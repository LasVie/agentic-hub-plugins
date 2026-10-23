"""Real offline integrity/policy tests; optional real host SDK, never a model call.

AGENT_LETTER_PAYLOAD selects an extracted payload. --write-demo-dir creates only
fictional public test keys and signed examples outside the package. Optional
AGENT_LETTER_UPSTREAM points to audited pinned index.js for actual interoperability.
"""
from __future__ import annotations
import asyncio
import copy
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("AGENT_LETTER_PAYLOAD", ROOT / "plugins/agent-letter-verify/agent-letter-verify"))
KEY = bytes(range(32))  # PUBLIC TEST KEY, NEVER for real communication.
ORDER = ["v", "kind", "id", "from", "to", "seq", "subject", "body", "sha256", "sentAtMs", "type", "mode", "re", "hop"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def signed(**changes):
    env = {"v": 1, "kind": "msg", "id": "demo-001", "from": "sender_demo", "to": "receiver_demo",
           "seq": 1, "subject": "虚构测试信件", "body": '你好😀\n第二行\u2028"反斜线\\',
           "sentAtMs": 1, "type": "direct", "mode": "offline", "hop": 0}
    env.update(changes)
    env["sha256"] = hashlib.sha256(env.get("body", "").encode()).hexdigest()
    canonical = json.dumps([[k, env[k]] for k in ORDER if k in env], ensure_ascii=False, separators=(",", ":"))
    env["mac"] = hmac.new(KEY, canonical.encode(), hashlib.sha256).hexdigest()
    return env


def private_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    path.chmod(0o600)


def make_demo(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    core = load("letter_demo_core", PAYLOAD / "runtime/verifier.py")
    result = core.dispatch("policy", {"workspace": str(root), "action": "init"})
    assert result["ok"], result
    key = root / ".agent-letter-verify/keys/sender_demo.key"
    key.write_text(KEY.hex() + "\n")
    key.chmod(0o600)
    good = signed()
    bad_body = {**good, "body": "正文已被改动"}
    bad_mac = {**good, "mac": "0" * 64}
    stranger = signed(**{"from": "unknown_demo"})
    extra = {**good, "unregistered": "新增未登记字段"}
    for name, env in (("有效信件.json", good), ("正文被改.json", bad_body), ("签名被改.json", bad_mac),
                      ("未知发件人.json", stranger), ("未知字段.json", extra)):
        private_json(root / name, env)
    (root / "重复字段.json").write_text('{"v":1,"v":1}\n')
    (root / "测试说明.txt").write_text("本目录只含公开虚构测试数据；sender_demo.key 不是秘密，不得用于真实通信。\n"
        "初始 revision=0、enabled=false。先校验应为 not_checked。\n"
        "用户明确要求后 configure：expected_revision=0，enabled=true，allow=[sender_demo]。\n"
        "有效信件应 verified；改正文/签名/未知发件人/未知字段/重复字段均 rejected。\n"
        "读取最新 revision 后关闭；再次有效信件应 not_checked。\n", encoding="utf-8")
    return {"workspace": str(root), "initial_revision": 0, "public_fixture_key": True}


class FixtureCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load("letter_core_tests", PAYLOAD / "runtime/verifier.py")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-letter-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = str(self.root)
        self.store = self.root / ".agent-letter-verify"
        self.policy("init")
        self.key = self.store / "keys/sender_demo.key"
        self.key.write_text(KEY.hex() + "\n")
        self.key.chmod(0o600)
        self.file = self.root / "测试信件.json"
        private_json(self.file, signed())

    def policy(self, action="status", **changes):
        return self.core.dispatch("policy", {"workspace": self.workspace, "action": action, **changes})

    def enable(self):
        rev = self.policy()["policy"]["revision"]
        result = self.policy("configure", enabled=True, allow=["sender_demo"], expected_revision=rev)
        self.assertTrue(result["ok"], result)
        return result

    def verify(self, env=None, path=None):
        if env is not None:
            private_json(self.file, env)
        return self.core.dispatch("verify", {"workspace": self.workspace, "letter_path": str(path or self.file)})

    def reason(self, result, expected):
        self.assertEqual(result.get("reason_code", result.get("error", {}).get("code")), expected, result)
        message = result.get("message", result.get("error", {}).get("message", ""))
        self.assertRegex(message, r"[\u4e00-\u9fff]")
        self.assertFalse(result.get("verified", False), result)


class IntegrityTests(FixtureCase):
    def test_init_default_disabled_and_idempotent_without_reset(self):
        initial = self.policy()
        self.assertEqual(initial["policy"], {"schema_version": 1, "enabled": False, "allow": [], "revision": 0})
        self.enable()
        before = (self.store / "policy.json").read_bytes()
        again = self.policy("init")
        self.assertFalse(again["created"])
        self.assertEqual((self.store / "policy.json").read_bytes(), before)

    def test_disabled_is_explicitly_unchecked_not_authentication(self):
        result = self.verify()
        self.reason(result, "verification_disabled")
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "not_checked")

    def test_valid_chinese_envelope_exact_input_hash_and_no_sensitive_echo(self):
        self.enable()
        before = self.file.read_bytes()
        result = self.verify()
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["verdict"], "verified")
        self.assertEqual(result["version"], "1.0.1")
        self.assertEqual(result["envelope_sha256"], hashlib.sha256(before).hexdigest())
        output = json.dumps(result, ensure_ascii=False)
        for value in (KEY.hex(), signed()["body"], signed()["mac"]):
            self.assertNotIn(value, output)
        self.assertEqual(before, self.file.read_bytes())

    def test_actual_node_canonical_and_pinned_upstream_interoperability(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Requires Node for independent JavaScript interoperability")
        env = signed()
        code = """const fs=require('node:fs'),c=require('node:crypto');
const e=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
const order=['v','kind','id','from','to','seq','subject','body','sha256','sentAtMs','type','mode','re','hop'];
const canonical=JSON.stringify(order.filter(k=>e[k]!==undefined).map(k=>[k,e[k]]));
console.log(JSON.stringify({canonical,mac:c.createHmac('sha256',Buffer.from(process.argv[2],'hex')).update(canonical).digest('hex')}));"""
        actual = json.loads(subprocess.check_output([node, "-e", code, str(self.file), KEY.hex()], text=True))
        self.assertEqual(actual["canonical"].encode(), self.core.canonical_bytes(env))
        self.assertEqual(actual["mac"], env["mac"])
        upstream = os.environ.get("AGENT_LETTER_UPSTREAM")
        if upstream:
            code = """import {pathToFileURL} from 'node:url';import fs from 'node:fs';
const {createVerify}=await import(pathToFileURL(process.argv[1]));
const v=createVerify({root:process.argv[2],enabled:true,allow:['sender_demo']});
console.log(JSON.stringify(v.verify(JSON.parse(fs.readFileSync(process.argv[3],'utf8')))));"""
            result = json.loads(subprocess.check_output([node, "--input-type=module", "-e", code,
                upstream, str(self.store), str(self.file)], text=True))
            self.assertEqual(result, {"ok": True})

    def test_changed_body_and_mac_are_separately_rejected(self):
        self.enable()
        self.reason(self.verify({**signed(), "body": "被篡改"}), "body_digest_mismatch")
        self.reason(self.verify({**signed(), "mac": "0" * 64}), "mac_mismatch")

    def test_sender_allowlist_checked_before_key_lookup(self):
        self.enable()
        self.reason(self.verify(signed(**{"from": "unknown_demo"})), "sender_not_allowed")

    def test_missing_key_does_not_use_shared_fallback(self):
        self.enable()
        self.key.unlink()
        (self.store / "signing.key").write_text(KEY.hex())
        self.reason(self.verify(), "file_unavailable")

    def test_empty_allowlist_cannot_enable_or_replace_enabled_policy(self):
        before = (self.store / "policy.json").read_bytes()
        self.reason(self.policy("configure", enabled=True, expected_revision=0), "empty_allowlist")
        self.assertEqual(before, (self.store / "policy.json").read_bytes())
        self.enable()
        self.reason(self.policy("configure", allow=[], expected_revision=1), "empty_allowlist")

    def test_disable_persists_and_stale_revision_is_preserved(self):
        self.enable()
        self.reason(self.policy("configure", enabled=False, expected_revision=0), "revision_conflict")
        self.assertTrue(self.policy()["policy"]["enabled"])
        off = self.policy("configure", enabled=False, expected_revision=1)
        self.assertTrue(off["ok"])
        self.assertFalse(self.policy()["policy"]["enabled"])
        self.reason(self.verify(), "verification_disabled")
        self.assertEqual(self.policy()["policy"]["revision"], 2)

    def test_failed_atomic_write_reports_failure_and_preserves_old_policy(self):
        before = (self.store / "policy.json").read_bytes()
        with patch.object(self.core.os, "replace", side_effect=OSError("injected write failure")):
            result = self.policy("configure", allow=["sender_demo"], expected_revision=0)
        self.assertFalse(result["ok"])
        self.assertEqual(before, (self.store / "policy.json").read_bytes())
        self.assertFalse(list(self.store.glob("*.tmp")))
        self.assertFalse((self.store / "policy.lock").exists())

    def test_existing_lock_is_not_removed(self):
        lock = self.store / "policy.lock"
        lock.write_text("existing lock")
        self.reason(self.policy("configure", enabled=False, expected_revision=0), "policy_busy")
        self.assertEqual(lock.read_text(), "existing lock")

    def test_invalid_policy_or_symlink_is_never_reinitialized(self):
        path = self.store / "policy.json"
        path.write_text("broken")
        self.assertFalse(self.policy("init")["ok"])
        self.assertEqual(path.read_text(), "broken")
        path.unlink()
        path.symlink_to(self.file)
        self.assertFalse(self.policy("init")["ok"])
        self.assertTrue(path.is_symlink())

    def test_unknown_missing_fields_and_protocol_versions(self):
        self.enable()
        for change, reason in (({"extra": 1}, "unknown_field"), ({"peerStateAtSend": {}}, "unknown_field"),
                               ({"v": 2}, "unsupported_version"), ({"kind": "other"}, "unsupported_kind"),
                               ({"v": True}, "unsupported_version")):
            self.reason(self.verify({**signed(), **change}), reason)
        for key in ("id", "from", "to", "mac", "seq", "body", "sha256"):
            env = signed();del env[key]
            self.reason(self.verify(env), "missing_field")

    def test_hello_ack_have_no_required_body_digest(self):
        self.enable()
        for kind in ("hello", "ack"):
            env = {"v": 1, "kind": kind, "id": "greeting", "from": "sender_demo", "to": "receiver_demo"}
            env["mac"] = hmac.new(KEY, self.core.canonical_bytes(env), hashlib.sha256).hexdigest()
            self.assertTrue(self.verify(env)["verified"])

    def test_invalid_types_unicode_numbers_and_identifiers(self):
        self.enable()
        for key, value, reason in (("from", "../../outside", "invalid_identifier"), ("id", "bad/id", "invalid_identifier"),
            ("to", "", "invalid_recipient"), ("subject", None, "invalid_field_type"), ("body", {}, "invalid_field_type"),
            ("seq", True, "invalid_integer"), ("seq", 1.0, "invalid_integer"), ("hop", -1, "invalid_integer"),
            ("sentAtMs", 9007199254740992, "invalid_integer"), ("subject", "\ud800", "invalid_unicode"),
            ("mac", "XYZ", "invalid_digest")):
            env = {**signed(), key: value}
            self.file.write_text(json.dumps(env, ensure_ascii=True))
            self.reason(self.verify(), reason)

    def test_duplicate_keys_nonfinite_and_broken_json(self):
        self.enable()
        for data, reason in ((b'{"v":1,"v":2}', "duplicate_json_key"), (b'{"v":NaN}', "invalid_json"),
                             (b'{"v":Infinity}', "invalid_json"), (b'\xff', "invalid_json"), (b'broken', "invalid_json")):
            self.file.write_bytes(data)
            self.reason(self.verify(), reason)

    def test_input_and_body_size_limits(self):
        self.enable()
        self.file.write_bytes(b" " * (self.core.MAX_LETTER + 1))
        self.reason(self.verify(), "file_too_large")
        self.reason(self.verify(signed(body="中" * 100000)), "field_too_large")

    def test_path_traversal_outside_private_store_and_links(self):
        self.enable()
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "outside.json";private_json(outside, signed())
            self.reason(self.verify(path=outside), "outside_workspace")
            link = self.root / "link.json";link.symlink_to(outside)
            self.reason(self.verify(path=link), "file_unavailable")
            directory = self.root / "linked";directory.symlink_to(Path(other), target_is_directory=True)
            self.reason(self.verify(path=directory / "outside.json"), "file_unavailable")
        self.reason(self.verify(path=self.store / "policy.json"), "outside_workspace")
        self.reason(self.verify(path=self.root / ".." / self.root.name / "测试信件.json"), "invalid_letter_path")
        hard = self.root / "hard.json";os.link(self.file, hard)
        self.reason(self.verify(path=hard), "unsafe_file")

    def test_sender_key_links_and_permissions_are_rejected(self):
        self.enable()
        self.key.chmod(0o644)
        self.reason(self.verify(), "unsafe_permissions")
        self.key.chmod(0o600)
        other = self.root / "other.key";other.write_text(KEY.hex());other.chmod(0o600)
        self.key.unlink();self.key.symlink_to(other)
        self.reason(self.verify(), "file_unavailable")

    def test_invalid_policy_requests_do_not_change_policy(self):
        before = (self.store / "policy.json").read_bytes()
        for args in ({"enabled": True}, {"expected_revision": True, "enabled": False},
                     {"expected_revision": 0}, {"expected_revision": 0, "allow": ["a", "a"]},
                     {"expected_revision": 0, "allow": ["../escape"]}, {"expected_revision": 0, "enabled": 1}):
            self.assertFalse(self.policy("configure", **args)["ok"])
            self.assertEqual(before, (self.store / "policy.json").read_bytes())
        self.assertFalse(self.core.dispatch("verify", {"workspace": self.workspace, "letter_path": str(self.file), "key": KEY.hex()})["ok"])

    def test_no_network_and_replay_limitation_are_honest(self):
        self.enable()
        with patch.object(socket.socket, "connect", side_effect=AssertionError("No network permitted")):
            first, second = self.verify(), self.verify()
        self.assertTrue(first["verified"] and second["verified"])
        self.assertTrue(any("重放" in x for x in first["limitations"]))

    def test_cli_chinese_help_exit_codes_and_single_json(self):
        cli = PAYLOAD / "scripts/letter_cli.py"
        help_text = subprocess.check_output([sys.executable, str(cli), "--help"], text=True)
        self.assertIn("未校验", help_text)
        args = {"workspace": self.workspace, "letter_path": str(self.file)}
        result = subprocess.run([sys.executable, str(cli), "verify"], input=json.dumps(args), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout)["verdict"], "not_checked")
        invalid = subprocess.run([sys.executable, str(cli), "verify"], input="broken", text=True, capture_output=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stderr, "")
        self.assertIn("JSON", json.loads(invalid.stdout)["error"]["message"])


class HostTests(FixtureCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load("letter_host_core", PAYLOAD / "runtime/verifier.py")
        try:
            from openjiuwen.core.common.logging.log_config import configure_log_config, get_log_config_snapshot
            config = get_log_config_snapshot()
            config["log_path"] = "/private/tmp/agent-letter-sdk-test-logs"
            configure_log_config(config)
            from openjiuwen.core.foundation.tool import Tool
        except ModuleNotFoundError as exc:
            if not exc.name.startswith("openjiuwen"):
                raise
            raise unittest.SkipTest("Requires actual host openJiuwen SDK") from exc
        cls.tool_type = Tool
        cls.adapter = load("letter_host_adapter", PAYLOAD / "tools/letter_tools.py")

    def test_actual_sdk_policy_invoke_and_verify_stream(self):
        tool = self.adapter.LetterPolicyTool()
        self.assertIsInstance(tool, self.tool_type)
        self.assertIn("策略", tool.card.description)
        result = asyncio.run(tool.invoke({"workspace": self.workspace, "action": "status"}))
        self.assertTrue(result["ok"])
        self.enable()
        verify = self.adapter.VerifyLetterTool()
        self.assertIsInstance(verify, self.tool_type)
        async def collect():
            return [r async for r in verify.stream({"workspace": self.workspace, "letter_path": str(self.file)})]
        values = asyncio.run(collect())
        self.assertEqual(len(values), 1)
        self.assertTrue(values[0]["verified"], values)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-demo-dir":
        print(json.dumps(make_demo(sys.argv[2]), ensure_ascii=False))
    else:
        unittest.main()
