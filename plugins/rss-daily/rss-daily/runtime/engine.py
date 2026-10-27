import concurrent.futures
import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from network import fetch_source, parse_feed, public_url


PAYLOAD = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"


def title_tokens(text):
    normalized = re.sub(r"[^\u4e00-\u9fff\w]", " ", text.lower())
    tokens = {token for token in normalized.split() if len(token) > 1}
    chinese = re.findall(r"[\u4e00-\u9fff]", normalized)
    tokens.update(chinese[index] + chinese[index + 1] for index in range(len(chinese) - 1))
    return tokens


def similar(left, right):
    first, second = title_tokens(left), title_tokens(right)
    return bool(first and second) and len(first & second) / len(first | second) >= 0.85


def fingerprint(title):
    return hashlib.sha256(re.sub(r"\s+", "", title.lower()).encode("utf-8")).hexdigest()[:24]


def markdown_text(value):
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#+!|])", r"\\\1", value.replace("\n", " "))


class Engine:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("RSS_DAILY_STATE_DIR") or Path.home() / ".cache/agentic-hub-rss-daily")
        self.processes = []

    def directory(self, mode):
        if mode not in ("demo", "live"):
            raise ValueError("mode 只能是 demo（演示）或 live（真实订阅）")
        directory = self.root / mode
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        return directory

    @contextlib.contextmanager
    def locked(self, mode):
        directory = self.directory(mode)
        with (directory / "state.lock").open("a+") as stream:
            os.chmod(stream.name, 0o600)
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield directory
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def load(self, directory):
        path = directory / "state.json"
        if not path.exists():
            return {"phase": "IDLE", "history": [], "sources": json.loads((PAYLOAD / "data/sources.json").read_text(encoding="utf-8"))}
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(state, dict) or not isinstance(state.get("history"), list) or not isinstance(state.get("sources"), list) or state.get("phase") not in ("IDLE", "RUNNING", "DRAFT", "FINALIZED", "CONFIRMED", "EMPTY", "FAILED"):
                raise ValueError("状态结构不完整")
            return state
        except (ValueError, OSError) as error:
            raise ValueError("状态文件损坏或无法读取；已保留原文件，请勿自动重置：" + str(error)) from error

    def save(self, directory, state):
        descriptor, temporary = tempfile.mkstemp(prefix=".state-", dir=directory)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(state, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, directory / "state.json")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def view(self, mode, state):
        messages = {
            "IDLE": "尚未生成日报", "RUNNING": "正在读取订阅源，请稍后调用 rss_status；不要重复发起抓取",
            "DRAFT": "候选素材已就绪，请基于原始素材编写中文标题和摘要，再调用 rss_finalize",
            "FINALIZED": "日报已生成，尚未确认；请展示全文并等待用户明确表示已阅读后再调用 rss_confirm",
            "CONFIRMED": "用户已确认阅读，已写入去重历史；这不代表已发送邮件或发布到外部平台",
            "EMPTY": "当前时间窗口内没有未确认的新条目；不要编造日报",
            "FAILED": "抓取失败；没有生成日报，也没有确认任何条目",
        }
        phase = state["phase"]
        result = {key: state[key] for key in ("batch_id", "hours", "items", "source_results", "selected", "markdown", "confirmed_at", "error", "started_at", "finished_at") if key in state}
        result.update({"ok": phase != "FAILED", "phase": phase, "message": messages[phase], "mode": mode,
                       "version": VERSION, "data_kind": "演示材料，非实时新闻" if mode == "demo" else "真实公开订阅源",
                       "history_count": len(state["history"]), "state_directory": str(self.directory(mode))})
        return result

    def status(self, mode="live"):
        self.processes = [process for process in self.processes if process.poll() is None]
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state["phase"] == "RUNNING" and time.time() - state["started_at"] > 65:
                state.update(phase="FAILED", error="后台抓取超过时限；请检查网络后明确重试")
                self.save(directory, state)
            return self.view(mode, state)

    def fetch(self, mode="live", hours=24, force=False):
        if type(hours) is not int or not 1 <= hours <= 168 or type(force) is not bool:
            raise ValueError("hours 必须是 1 至 168 的整数，force 必须是布尔值")
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state["phase"] == "RUNNING" or (state["phase"] in ("DRAFT", "FINALIZED") and not force):
                return self.view(mode, state)
            state = {"phase": "RUNNING", "history": state["history"], "sources": state["sources"],
                     "batch_id": uuid.uuid4().hex, "hours": hours, "started_at": time.time()}
            self.save(directory, state)
            try:
                environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
                process = subprocess.Popen([sys.executable, "-B", str(PAYLOAD / "runtime/worker.py"), str(self.root.resolve()), mode, state["batch_id"]],
                                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=environment, start_new_session=True)
                self.processes.append(process)
            except OSError as error:
                state.update(phase="FAILED", error="无法启动抓取进程：" + str(error))
                self.save(directory, state)
            return self.view(mode, state)

    def collect(self, mode, batch_id):
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state.get("batch_id") != batch_id or state["phase"] != "RUNNING":
                return
            hours, now, sources = state["hours"], state["started_at"], state["sources"]
        results = []
        if mode == "demo":
            for filename in ("demo-rss.xml", "demo-atom.xml"):
                content = (PAYLOAD / "data" / filename).read_text(encoding="utf-8")
                recent = datetime.fromtimestamp(now - 3600, timezone.utc).isoformat()
                old = datetime.fromtimestamp(now - 30 * 86400, timezone.utc).isoformat()
                content = content.replace("@RECENT@", recent).replace("@OLD@", old).encode("utf-8")
                results.append(parse_feed(content, {"name": "演示 " + filename, "url": "https://example.com/" + filename}, now, hours))
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                results = list(executor.map(lambda source: fetch_source(source, now, hours), sources))
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state.get("batch_id") != batch_id or state["phase"] != "RUNNING":
                return
            state["source_results"] = [result[1] for result in results]
            history = [item for item in state["history"] if item["confirmed_at"] >= now - 14 * 86400][-1000:]
            state["history"] = history
            candidates = sorted((item for result in results for item in result[0]), key=lambda item: (-item["timestamp"], item["source"], item["url"]))
            selected = []
            counts = {}
            for candidate in candidates:
                if counts.get(candidate["source"], 0) >= 2:
                    continue
                if any(candidate["url"] == known["url"] or fingerprint(candidate["title"]) == fingerprint(known["title"]) or similar(candidate["title"], known["title"]) for known in history + selected):
                    continue
                candidate["id"] = hashlib.sha256((batch_id + candidate["url"]).encode()).hexdigest()[:16]
                selected.append(candidate)
                counts[candidate["source"]] = counts.get(candidate["source"], 0) + 1
                if len(selected) == 12:
                    break
            state["items"] = selected
            state["phase"] = "DRAFT" if selected else "EMPTY"
            if all("error" in result[1] for result in results):
                state.update(phase="FAILED", error="全部订阅源读取失败；请查看 source_results 中的原始原因")
            state["finished_at"] = time.time()
            self.save(directory, state)

    def finalize(self, batch_id, items, mode="live"):
        if not isinstance(items, list) or not 1 <= len(items) <= 12:
            raise ValueError("items 必须包含 1 至 12 条摘要")
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state.get("batch_id") != batch_id or state["phase"] != "DRAFT":
                raise ValueError("批次不匹配或不是可编辑草稿；请先读取 rss_status")
            source_items = {item["id"]: item for item in state["items"]}
            selected = []
            seen = set()
            for item in items:
                if not isinstance(item, dict) or set(item) != {"id", "title", "summary"} or not isinstance(item["id"], str) or item["id"] not in source_items or item["id"] in seen:
                    raise ValueError("每条摘要必须使用当前批次唯一的 id、title、summary；不得自行提供网址")
                for field, limit in (("title", 160), ("summary", 600)):
                    value = item[field]
                    if not isinstance(value, str) or not 2 <= len(value.strip()) <= limit or not re.search(r"[\u4e00-\u9fff]", value) or any(ord(char) < 32 and char not in "\n\t" for char in value):
                        raise ValueError("标题和摘要必须是长度合适、不含控制符的中文文字")
                selected.append(dict(source_items[item["id"]], edited_title=item["title"].strip(), summary=item["summary"].strip()))
                seen.add(item["id"])
            generated = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M UTC+8")
            lines = ["# 资讯晨报", "", "生成时间：" + generated, "", "演示材料，非实时新闻。" if mode == "demo" else "根据公开订阅源编排；摘要由智能体整理，未独立核实报道中的事实。", "", "状态：待用户确认阅读；尚未写入去重历史。", ""]
            for index, item in enumerate(selected, 1):
                lines.extend(["## " + str(index) + ". " + markdown_text(item["edited_title"]), "", markdown_text(item["summary"]), "",
                              "来源：" + markdown_text(item["source"]) + "｜发布时间：" + item["published_at"],
                              "原文：<" + item["url"].replace("<", "%3C").replace(">", "%3E") + ">", ""])
            failures = [result for result in state.get("source_results", []) if "error" in result]
            if failures:
                lines.extend(["## 未能读取的订阅源", ""] + [markdown_text(result["name"] + "：" + result["error"]) for result in failures])
            state.update(phase="FINALIZED", selected=selected, markdown="\n".join(lines))
            self.save(directory, state)
            return self.view(mode, state)

    def confirm(self, batch_id, mode="live"):
        with self.locked(mode) as directory:
            state = self.load(directory)
            if state.get("batch_id") != batch_id or state["phase"] not in ("FINALIZED", "CONFIRMED"):
                raise ValueError("只能确认当前已经生成的日报；请先读取 rss_status")
            if state["phase"] == "CONFIRMED":
                return self.view(mode, state)
            confirmed_at = time.time()
            state["history"].extend({"url": item["url"], "title": item["title"], "confirmed_at": confirmed_at} for item in state["selected"])
            state["history"] = state["history"][-1000:]
            state.update(phase="CONFIRMED", confirmed_at=confirmed_at)
            state["markdown"] = state["markdown"].replace("状态：待用户确认阅读；尚未写入去重历史。", "状态：用户已确认阅读，已写入去重历史。", 1)
            self.save(directory, state)
            return self.view(mode, state)

    def sources(self, action="list", sources=None, mode="live"):
        if mode != "live" or action not in ("list", "set"):
            raise ValueError("订阅源管理仅支持 live 模式，action 为 list 或 set")
        with self.locked(mode) as directory:
            state = self.load(directory)
            if action == "set":
                if state["phase"] in ("RUNNING", "DRAFT", "FINALIZED"):
                    raise ValueError("当前有未处理批次；请先完成确认，再修改订阅源")
                if not isinstance(sources, list) or not 1 <= len(sources) <= 6:
                    raise ValueError("请提供 1 至 6 个公开 HTTPS 订阅源")
                validated = []
                for source in sources:
                    if not isinstance(source, dict) or set(source) != {"name", "url"} or not isinstance(source["name"], str) or not 1 <= len(source["name"].strip()) <= 60:
                        raise ValueError("每个订阅源需要 name 和 url，名称长度为 1 至 60 字符")
                    public_url(source["url"])
                    if source["url"] in [item["url"] for item in validated]:
                        raise ValueError("订阅源地址不能重复")
                    validated.append({"name": source["name"].strip(), "url": source["url"]})
                state["sources"] = validated
                self.save(directory, state)
            return {"ok": True, "sources": state["sources"], "message": "已保存订阅源" if action == "set" else "当前真实订阅源；演示材料使用独立内置文件"}
