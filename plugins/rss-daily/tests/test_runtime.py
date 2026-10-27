import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
PAYLOAD = Path(os.environ.get("RSS_DAILY_PAYLOAD", Path(__file__).resolve().parents[1] / "rss-daily"))
sys.path.insert(0, str(PAYLOAD / "runtime"))
from engine import Engine, fingerprint, markdown_text, similar
from network import FeedError, canonical_url, download, parse_feed, plain, public_url, timestamp
from server import ProtocolError, Server


def wait(engine, mode="demo"):
    for attempt in range(100):
        result = engine.status(mode)
        if result["phase"] != "RUNNING":
            return result
        time.sleep(0.05)
    raise AssertionError("演示抓取未按时结束")


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="rss-daily-tests-")
        self.engine = Engine(self.temporary.name)

    def tearDown(self):
        for process in self.engine.processes:
            process.wait(timeout=5)
        self.temporary.cleanup()

    def draft(self):
        self.assertEqual(self.engine.fetch("demo")["phase"], "RUNNING")
        result = wait(self.engine)
        self.assertEqual(result["phase"], "DRAFT")
        return result

    def final(self):
        draft = self.draft()
        items = [{"id": item["id"], "title": item["title"], "summary": item["excerpt"]} for item in draft["items"]]
        return self.engine.finalize(draft["batch_id"], items, "demo")

    def test_initial_state_is_chinese(self):
        result = self.engine.status("demo")
        self.assertEqual(result["phase"], "IDLE")
        self.assertIn("演示", result["data_kind"])
        self.assertIn("尚未", result["message"])

    def test_demo_rss_atom_time_filter_and_dedup(self):
        result = self.draft()
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(sum(item["entries"] for item in result["source_results"]), 5)
        self.assertEqual(sum(item["skipped"] for item in result["source_results"]), 1)
        self.assertEqual(len({item["url"] for item in result["items"]}), 3)

    def test_pending_draft_reused(self):
        draft = self.draft()
        self.assertEqual(self.engine.fetch("demo")["batch_id"], draft["batch_id"])

    def test_finalize_binds_sources_and_waits_for_confirmation(self):
        result = self.final()
        self.assertEqual(result["phase"], "FINALIZED")
        self.assertEqual(result["history_count"], 0)
        self.assertIn("待用户确认", result["markdown"])
        self.assertIn("非实时新闻", result["markdown"])
        for item in result["items"]:
            self.assertIn(item["url"], result["markdown"])
            self.assertIn(item["published_at"], result["markdown"])

    def test_finalized_is_reused(self):
        result = self.final()
        self.assertEqual(self.engine.fetch("demo")["markdown"], result["markdown"])

    def test_explicit_confirmation_idempotent(self):
        result = self.final()
        first = self.engine.confirm(result["batch_id"], "demo")
        second = self.engine.confirm(result["batch_id"], "demo")
        self.assertEqual(first["confirmed_at"], second["confirmed_at"])
        self.assertEqual(second["history_count"], 3)

    def test_confirmed_items_suppressed_after_restart(self):
        result = self.final()
        self.engine.confirm(result["batch_id"], "demo")
        other = Engine(self.temporary.name)
        self.assertEqual(other.status("demo")["phase"], "CONFIRMED")
        other.fetch("demo", force=True)
        refreshed = wait(other)
        for process in other.processes:
            process.wait(timeout=5)
        self.assertEqual(refreshed["phase"], "EMPTY")
        self.assertEqual(refreshed["items"], [])
        self.assertEqual(refreshed["history_count"], 3)

    def test_demo_history_does_not_touch_live(self):
        result = self.final()
        self.engine.confirm(result["batch_id"], "demo")
        self.assertEqual(self.engine.status("live")["history_count"], 0)
        self.assertEqual(self.engine.status("live")["phase"], "IDLE")

    def test_force_does_not_clear_history(self):
        result = self.final()
        self.engine.confirm(result["batch_id"], "demo")
        started = self.engine.fetch("demo", force=True)
        self.assertEqual(started["history_count"], 3)
        wait(self.engine)

    def test_unknown_id_and_duplicate_id_rejected(self):
        result = self.draft()
        item = {"id": "不存在", "title": "中文标题", "summary": "中文摘要"}
        with self.assertRaisesRegex(ValueError, "唯一"):
            self.engine.finalize(result["batch_id"], [item], "demo")
        item["id"] = result["items"][0]["id"]
        with self.assertRaisesRegex(ValueError, "唯一"):
            self.engine.finalize(result["batch_id"], [item, item], "demo")

    def test_forged_link_rejected(self):
        result = self.draft()
        item = {"id": result["items"][0]["id"], "title": "中文标题", "summary": "中文摘要", "url": "https://example.com/forged"}
        with self.assertRaises(ValueError):
            self.engine.finalize(result["batch_id"], [item], "demo")

    def test_english_only_summary_rejected(self):
        result = self.draft()
        item = {"id": result["items"][0]["id"], "title": "中文标题", "summary": "English only"}
        with self.assertRaisesRegex(ValueError, "中文"):
            self.engine.finalize(result["batch_id"], [item], "demo")

    def test_stale_batch_rejected(self):
        self.final()
        with self.assertRaisesRegex(ValueError, "当前"):
            self.engine.confirm("旧批次", "demo")

    def test_unfinalized_confirm_rejected(self):
        result = self.draft()
        with self.assertRaises(ValueError):
            self.engine.confirm(result["batch_id"], "demo")

    def test_invalid_arguments_do_not_start_worker(self):
        for hours in (True, 0, 169, "24"):
            with self.assertRaises(ValueError):
                self.engine.fetch("demo", hours)
        with self.assertRaises(ValueError):
            self.engine.status("../live")
        self.assertEqual(self.engine.processes, [])

    def test_state_corruption_preserved(self):
        path = self.engine.directory("demo") / "state.json"
        path.write_text("损坏内容", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "保留原文件"):
            self.engine.status("demo")
        self.assertEqual(path.read_text(encoding="utf-8"), "损坏内容")

    def test_private_file_permissions(self):
        self.final()
        directory = self.engine.directory("demo")
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        for filename in ("state.json", "state.lock"):
            self.assertEqual((directory / filename).stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(directory.glob(".state-*")), [])

    def test_concurrent_fetch_reuses_one_batch(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda unused: self.engine.fetch("demo"), range(4)))
        self.assertEqual(len({result["batch_id"] for result in results}), 1)
        self.assertEqual(len(self.engine.processes), 1)
        wait(self.engine)

    def test_concurrent_confirm_is_atomic(self):
        result = self.final()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda unused: Engine(self.temporary.name).confirm(result["batch_id"], "demo"), range(4)))
        self.assertEqual({item["history_count"] for item in results}, {3})
        self.assertEqual(len({item["confirmed_at"] for item in results}), 1)

    def test_source_configuration_persists(self):
        sources = [{"name": "测试公开源", "url": "https://example.com/feed"}]
        self.engine.sources("set", sources)
        self.assertEqual(Engine(self.temporary.name).sources()["sources"], sources)

    def test_source_validation(self):
        for sources in ([], [{"name": "内网", "url": "http://127.0.0.1/feed"}], [{"url": "https://example.com/feed"}]):
            with self.assertRaises(ValueError):
                self.engine.sources("set", sources)

    def test_partial_failure_is_visible_in_final_report(self):
        result = self.draft()
        with self.engine.locked("demo") as directory:
            state = self.engine.load(directory)
            state["source_results"].append({"name": "失败演示源", "error": "模拟证书失败"})
            self.engine.save(directory, state)
        item = result["items"][0]
        finalized = self.engine.finalize(result["batch_id"], [{"id": item["id"], "title": "中文标题", "summary": item["excerpt"]}], "demo")
        self.assertIn("模拟证书失败", finalized["markdown"])
        self.assertEqual(finalized["history_count"], 0)

    def test_only_selected_items_are_confirmed(self):
        result = self.draft()
        item = result["items"][0]
        self.engine.finalize(result["batch_id"], [{"id": item["id"], "title": item["title"], "summary": item["excerpt"]}], "demo")
        self.assertEqual(self.engine.confirm(result["batch_id"], "demo")["history_count"], 1)
        self.engine.fetch("demo")
        self.assertEqual(len(wait(self.engine)["items"]), 2)

    def test_expired_history_is_pruned(self):
        with self.engine.locked("demo") as directory:
            state = self.engine.load(directory)
            state["history"] = [{"url": "https://example.com/demo/notes", "title": "演示：团队发布开源笔记工具", "confirmed_at": time.time() - 15 * 86400}]
            self.engine.save(directory, state)
        result = self.draft()
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(result["history_count"], 0)

    def test_pending_live_batch_blocks_source_replacement(self):
        with self.engine.locked("live") as directory:
            state = self.engine.load(directory)
            state["phase"] = "DRAFT"
            self.engine.save(directory, state)
        with self.assertRaisesRegex(ValueError, "未处理"):
            self.engine.sources("set", [{"name": "公开源", "url": "https://example.com/feed"}])

    def test_all_failed_is_not_empty(self):
        with self.engine.locked("live") as directory:
            state = self.engine.load(directory)
            state.update(phase="RUNNING", batch_id="failed", hours=24, started_at=time.time())
            self.engine.save(directory, state)
        with patch("engine.fetch_source", return_value=([], {"error": "模拟网络失败", "name": "测试源"})):
            self.engine.collect("live", "failed")
        result = self.engine.status("live")
        self.assertFalse(result["ok"])
        self.assertEqual(result["phase"], "FAILED")
        self.assertEqual(result["history_count"], 0)

    def test_worker_launch_failure_is_retryable(self):
        with patch("engine.subprocess.Popen", side_effect=OSError("测试拒绝启动")):
            result = self.engine.fetch("demo")
        self.assertEqual(result["phase"], "FAILED")
        self.assertEqual(self.engine.fetch("demo")["phase"], "RUNNING")
        self.assertEqual(wait(self.engine)["phase"], "DRAFT")

    def test_expired_worker_becomes_failure(self):
        with self.engine.locked("demo") as directory:
            state = self.engine.load(directory)
            state.update(phase="RUNNING", started_at=time.time() - 70)
            self.engine.save(directory, state)
        self.assertEqual(self.engine.status("demo")["phase"], "FAILED")

    def test_markdown_is_escaped(self):
        self.assertEqual(markdown_text("<script> **标题** [链接](a)"), "&lt;script&gt; \\*\\*标题\\*\\* \\[链接\\]\\(a\\)")

    def test_title_fingerprints_and_similarity(self):
        self.assertEqual(fingerprint("标题 A"), fingerprint("标题a"))
        self.assertTrue(similar("开源团队发布笔记工具", "开源团队发布笔记工具"))
        self.assertFalse(similar("笔记工具", "传感器节能研究"))

    def test_private_urls_rejected(self):
        for url in ("http://example.com/rss", "file:///etc/passwd", "https://127.0.0.1/rss", "https://169.254.169.254/rss", "https://[::1]/", "https://user:pw@example.com/rss", "https://example.com:8080/rss", "https://localhost/rss"):
            with self.subTest(url=url), self.assertRaises(FeedError):
                public_url(url)

    def test_dns_private_addresses_rejected_before_connection(self):
        with patch("network.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaisesRegex(FeedError, "解析包含非公网"):
                download("https://example.com/feed")

    def test_canonical_tracking_url(self):
        self.assertEqual(canonical_url("https://example.com/a?utm_source=x&topic=ai#fragment"), "https://example.com/a?topic=ai")

    def test_html_is_plain_data(self):
        self.assertEqual(plain("<p>文本</p><script>秘密()</script><style>隐藏</style><b>后续</b>"), "文本 后续")

    def test_bad_xml_entities_and_html_rejected(self):
        for content in (b"<html>not feed</html>", b"<rss><", b'<!DOCTYPE rss [<!ENTITY secret SYSTEM "file:///etc/passwd">]><rss/>' ):
            with self.assertRaises(FeedError):
                parse_feed(content, {"name": "坏源", "url": "https://example.com"}, time.time(), 24)

    def test_utf16_entity_declaration_rejected(self):
        content = '<!DOCTYPE rss [<!ENTITY secret SYSTEM "file:///etc/passwd">]><rss/>'.encode("utf-16")
        with self.assertRaises(FeedError):
            parse_feed(content, {"name": "坏源", "url": "https://example.com"}, time.time(), 24)

    def test_oversized_feed_rejected(self):
        with self.assertRaisesRegex(FeedError, "过大"):
            parse_feed(b" " * 524289, {"name": "坏源", "url": "https://example.com"}, time.time(), 24)

    def test_https_connection_keeps_certificate_validation(self):
        import ssl
        context = ssl.create_default_context()
        with patch("network.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]), patch("network.socket.create_connection") as connect, patch("network.ssl.create_default_context", return_value=context) as contexts:
            connect.side_effect = OSError("模拟断网")
            with self.assertRaises(OSError):
                download("https://example.com/feed")
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            contexts.assert_called_once_with()

    def test_redirect_to_private_address_rejected(self):
        from unittest.mock import MagicMock
        response = MagicMock(status=302)
        response.getheader.return_value = "https://127.0.0.1/feed"
        with patch("network.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]), patch("network.socket.create_connection"), patch("network.ssl.create_default_context"), patch("network.http.client.HTTPSConnection") as connection:
            connection.return_value.getresponse.return_value = response
            with self.assertRaises(FeedError):
                download("https://example.com/feed")
            self.assertEqual(connection.call_count, 1)

    def test_missing_timezone_not_made_current(self):
        self.assertIsNone(timestamp("2026-10-27T08:00:00"))
        self.assertIsNone(timestamp("not a date"))

    def test_protocol_initialization_and_schema(self):
        server = Server(self.temporary.name)
        with self.assertRaises(ProtocolError):
            server.handle({"jsonrpc": "2.0", "method": "tools/list"})
        result = server.handle({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
        self.assertEqual(result["protocolVersion"], "2025-03-26")
        self.assertEqual(len(server.handle({"jsonrpc": "2.0", "method": "tools/list"})["tools"]), 5)
        result = server.handle({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "rss_status", "arguments": {"mode": "demo"}}})
        self.assertFalse(result["isError"])
        self.assertEqual(json.loads(result["content"][0]["text"])["phase"], "IDLE")

    def test_stdio_is_utf8_json_only_and_recovers_after_bad_input(self):
        environment = dict(os.environ, RSS_DAILY_STATE_DIR=self.temporary.name)
        requests = ["broken", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "rss_status", "arguments": {"mode": "demo"}}})]
        result = subprocess.run([sys.executable, "-B", str(PAYLOAD / "runtime/server.py")], input="\n".join(requests) + "\n", capture_output=True, text=True, env=environment, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0]["error"]["code"], -32700)
        self.assertIn("演示", lines[-1]["result"]["content"][0]["text"])
        self.assertEqual(result.stderr, "")

    def test_payload_is_not_written_during_calls(self):
        before = {str(path.relative_to(PAYLOAD)): hashlib.sha256(path.read_bytes()).hexdigest() for path in PAYLOAD.rglob("*") if path.is_file()}
        self.final()
        after = {str(path.relative_to(PAYLOAD)): hashlib.sha256(path.read_bytes()).hexdigest() for path in PAYLOAD.rglob("*") if path.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
