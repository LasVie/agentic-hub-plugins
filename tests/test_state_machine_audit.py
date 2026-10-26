"""Behavior, boundary and oracle tests for CAND-DSH-214's bounded port."""
import copy
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PAYLOAD = Path(os.environ.get("STATE_MACHINE_AUDIT_PAYLOAD", Path(__file__).resolve().parents[1] /
                             "plugins/state-machine-audit/state-machine-audit")).resolve()
SPEC = importlib.util.spec_from_file_location("test_bounded_model_core", PAYLOAD / "runtime/audit.py")
CORE = importlib.util.module_from_spec(SPEC)
_old = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(CORE)
finally:
    sys.dont_write_bytecode = _old


def simple():
    return {"schemaVersion": 1, "init": "初始", "states": [{"id": "初始"}, {"id": "结束", "terminal": True}],
            "transitions": [{"from": "初始", "event": "完成", "to": "结束"}]}


class StateMachineAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="state-machine-audit-test-")
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / "中文模型.json"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, model):
        self.path.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")

    def inspect(self):
        return CORE.dispatch("inspect", {"workspace": str(self.root), "path": str(self.path)})

    def audit(self, model=None, **opts):
        if model is not None:
            self.write(model)
        return CORE.dispatch("audit", {"workspace": str(self.root), "path": str(self.path), "confirmed": True,
                                      "expected_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(), **opts})

    def invalid(self, model, code="model_invalid"):
        self.write(model)
        result = self.inspect()
        self.assertFalse(result["ok"], result)
        self.assertFalse(result["ran"])
        self.assertEqual(result["error"]["code"], code)

    def fixture(self, name):
        return json.loads((PAYLOAD / "examples" / (name + ".json")).read_text())

    def test_inspect_exposes_initial_state_independent_of_state_order(self):
        for name in ("正常订单", "未支付发货", "守卫堵塞", "越域重试"):
            with self.subTest(model=name):
                model = self.fixture(name)
                model["states"].reverse()
                self.assertNotEqual(model["states"][0]["id"], model["init"])
                self.write(model)
                before = self.path.read_bytes()
                result = self.inspect()
                self.assertTrue(result["ok"])
                self.assertEqual(result["init"], model["init"])
                self.assertEqual(result["model_sha256"], hashlib.sha256(before).hexdigest())
                self.assertNotIn("verdict", result)
                self.assertEqual(self.path.read_bytes(), before)

    def test_normal_order_complete(self):
        result = self.audit(self.fixture("正常订单"))
        self.assertEqual(result["verdict"], "pass")
        self.assertTrue(result["analysis_complete"])
        self.assertEqual(result["summary"]["explored_configurations"], 12)
        self.assertEqual(result["summary"]["unreachable_states"], ["错误"])
        self.assertTrue(all(p["status"] == "pass" for p in result["properties"]))

    def test_unpaid_shipment_shortest(self):
        result = self.audit(self.fixture("未支付发货"))
        finding = next(f for f in result["findings"] if f.get("property_id") == "先付后发")
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(finding["trace_length"], 1)
        self.assertEqual(finding["trace"][0]["event"], "绕过支付")
        self.assertFalse(finding["trace"][0]["before"]["已付款"])

    def test_guard_blocked_is_dead_end(self):
        result = self.audit(self.fixture("守卫堵塞"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["findings"][0]["code"], "enabled_dead_end")
        self.assertEqual(result["findings"][0]["trace"], [])

    def test_terminal_with_no_edges_passes(self):
        m = {"schemaVersion": 1, "init": "结束", "states": [{"id": "结束", "terminal": True}], "transitions": []}
        result = self.audit(m)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["properties"], [])

    def test_no_properties_does_not_claim_safety(self):
        result = self.audit(simple())
        self.assertIn("无不变量", result["coverage_note"])

    def test_initial_forbidden_state_zero_trace(self):
        m = simple()
        m["invariants"] = [{"id": "禁入", "kind": "never-states", "description": "禁止初始", "states": ["初始"]}]
        r = self.audit(m)
        self.assertEqual(r["findings"][0]["trace_length"], 0)

    def test_initial_target_has_no_past_event(self):
        m = simple()
        m["invariants"] = [{"id": "先决", "kind": "event-before-state", "description": "须先完成", "event": "完成", "state": "初始"}]
        self.assertEqual(self.audit(m)["verdict"], "fail")

    def test_event_on_entering_edge_counts(self):
        m = simple()
        m["invariants"] = [{"id": "先决", "kind": "event-before-state", "description": "入边完成", "event": "完成", "state": "结束"}]
        self.assertEqual(self.audit(m)["verdict"], "pass")

    def test_history_is_part_of_configuration(self):
        m = {"schemaVersion": 1, "init": "开始", "states": [{"id": "开始"}, {"id": "汇合"}, {"id": "结束", "terminal": True}],
             "transitions": [{"from": "开始", "event": "许可", "to": "汇合"}, {"from": "开始", "event": "跳过", "to": "汇合"},
                             {"from": "汇合", "event": "提交", "to": "结束"}],
             "invariants": [{"id": "许可先决", "kind": "event-before-state", "description": "提交需要许可", "event": "许可", "state": "结束"}]}
        r = self.audit(m)
        self.assertEqual(r["verdict"], "fail")
        self.assertEqual([s["event"] for s in r["findings"][0]["trace"]], ["跳过", "提交"])

    def test_all_nondeterministic_outcomes_explored(self):
        m = simple()
        m["states"].append({"id": "危险", "terminal": True})
        m["transitions"].append({"from": "初始", "event": "完成", "to": "危险"})
        m["invariants"] = [{"id": "禁入", "kind": "never-states", "description": "不能危险", "states": ["危险"]}]
        self.assertEqual(self.audit(m)["verdict"], "fail")

    def test_guarded_match_overrides_fallback(self):
        m = simple()
        m["variables"] = [{"name": "许可", "kind": "boolean", "init": True}]
        m["states"].append({"id": "回退", "terminal": True})
        m["transitions"][0]["guard"] = {"variable": "许可", "op": "==", "value": True}
        m["transitions"].append({"from": "初始", "event": "完成", "to": "回退"})
        r = self.audit(m)
        self.assertEqual(r["summary"]["unreachable_states"], ["回退"])
        m["variables"][0]["init"] = False
        self.assertEqual(self.audit(m)["summary"]["unreachable_states"], ["结束"])

    def test_nested_boolean_guard(self):
        m = simple()
        m["variables"] = [{"name": "许可", "kind": "boolean", "init": False}]
        m["transitions"][0]["guard"] = {"all": [{"not": {"variable": "许可", "op": "==", "value": True}},
                                                 {"any": [{"variable": "许可", "op": "!=", "value": True}]}]}
        self.assertEqual(self.audit(m)["verdict"], "pass")

    def test_domain_escape_not_clamped_or_complete(self):
        r = self.audit(self.fixture("越域重试"))
        f = next(f for f in r["findings"] if f["code"] == "domain_escape")
        self.assertEqual(r["verdict"], "fail")
        self.assertFalse(r["analysis_complete"])
        self.assertIn("domain_escape", r["incomplete_reasons"])
        self.assertEqual(f["trace"][-1]["after"]["重试"], 3)

    def test_state_budget_never_silently_passes(self):
        r = self.audit(self.fixture("正常订单"), max_states=1)
        self.assertEqual(r["verdict"], "incomplete")
        self.assertFalse(r["analysis_complete"])
        self.assertEqual(r["summary"]["unreachable_states"], [])
        self.assertTrue(r["summary"]["unresolved_states"])
        self.assertTrue(all(p["status"] == "incomplete" for p in r["properties"]))

    def test_exact_state_budget_can_complete(self):
        self.assertEqual(self.audit(simple(), max_states=2)["verdict"], "pass")

    def test_found_violation_decisive_even_with_limit(self):
        r = self.audit(self.fixture("未支付发货"), max_states=1)
        self.assertEqual(r["verdict"], "fail")
        self.assertFalse(r["analysis_complete"])

    def test_edge_budget_is_incomplete(self):
        self.assertEqual(self.audit(self.fixture("正常订单"), max_edges=1)["verdict"], "incomplete")

    def test_depth_budget_is_incomplete(self):
        r = self.audit(self.fixture("正常订单"), max_steps=1)
        self.assertEqual(r["verdict"], "incomplete")
        self.assertIn("depth_limit", r["incomplete_reasons"])

    def test_revisited_cycle_does_not_exhaust_depth(self):
        m = {"schemaVersion": 1, "init": "环", "states": [{"id": "环"}], "transitions": [{"from": "环", "event": "循环", "to": "环"}]}
        self.assertEqual(self.audit(m, max_steps=1)["verdict"], "pass")

    def test_unknown_fields_rejected(self):
        self.invalid(self.fixture("未知字段"))

    def test_duplicate_keys_rejected(self):
        self.path.write_bytes((PAYLOAD / "examples/重复键.json").read_bytes())
        self.assertEqual(self.inspect()["error"]["code"], "duplicate_json_key")

    def test_null_state_rejected(self):
        m = simple(); m["states"].append(None); self.invalid(m)

    def test_duplicate_ids_rejected(self):
        m = simple(); m["states"].append({"id": "初始"}); self.invalid(m)

    def test_missing_endpoint_rejected(self):
        m = simple(); m["transitions"][0]["to"] = "不存在"; self.invalid(m)

    def test_unknown_property_reference_rejected(self):
        m = simple(); m["invariants"] = [{"id": "禁入", "kind": "never-states", "description": "不能遗漏", "states": ["不存在"]}]
        self.invalid(m)

    def test_unsupported_property_rejected(self):
        m = simple(); m["invariants"] = [{"id": "概率", "kind": "probability"}]; self.invalid(m)

    def test_terminal_outgoing_rejected(self):
        m = simple(); m["states"][0]["terminal"] = True; self.invalid(m)

    def test_unbounded_integer_rejected(self):
        m = simple(); m["variables"] = [{"name": "数", "kind": "integer", "init": 0}]; self.invalid(m)

    def test_float_and_bool_integer_rejected(self):
        for n in (True, 0.0, 1e30):
            with self.subTest(n=n):
                m = simple(); m["variables"] = [{"name": "数", "kind": "integer", "init": n, "min": 0, "max": 2}]
                self.invalid(m)

    def test_integer_domain_width_rejected(self):
        m = simple(); m["variables"] = [{"name": "数", "kind": "integer", "init": 0, "min": 0, "max": 64}]; self.invalid(m)

    def test_integer_initial_domain_rejected(self):
        m = simple(); m["variables"] = [{"name": "数", "kind": "integer", "init": 3, "min": 0, "max": 2}]; self.invalid(m)

    def test_theoretical_product_rejected(self):
        m = simple(); m["variables"] = [{"name": str(i), "kind": "integer", "init": 0, "min": 0, "max": 63} for i in range(3)]
        self.invalid(m, "model_too_large")

    def test_guard_code_string_rejected(self):
        m = simple(); m["transitions"][0]["guard"] = "__import__('os').system('echo forbidden')"; self.invalid(m)

    def test_guard_type_and_reference_rejected(self):
        for guard in ({"variable": "未知", "op": "==", "value": 1}, {"all": []}, {"not": {}, "any": []}):
            with self.subTest(guard=guard):
                m = simple(); m["transitions"][0]["guard"] = guard; self.invalid(m)

    def test_boolean_guard_does_not_accept_number(self):
        m = simple(); m["variables"] = [{"name": "开", "kind": "boolean", "init": True}]
        m["transitions"][0]["guard"] = {"variable": "开", "op": "==", "value": 1}; self.invalid(m)

    def test_duplicate_updates_rejected(self):
        m = simple(); m["variables"] = [{"name": "开", "kind": "boolean", "init": False}]
        m["transitions"][0]["updates"] = [{"variable": "开", "op": "set", "value": True}] * 2; self.invalid(m)

    def test_boolean_increment_rejected(self):
        m = simple(); m["variables"] = [{"name": "开", "kind": "boolean", "init": False}]
        m["transitions"][0]["updates"] = [{"variable": "开", "op": "inc", "value": 1}]; self.invalid(m)

    def test_nan_rejected(self):
        self.path.write_text('{"schemaVersion":NaN}')
        self.assertFalse(self.inspect()["ok"])

    def test_invalid_utf8_rejected(self):
        self.path.write_bytes(b'\xff')
        self.assertEqual(self.inspect()["error"]["code"], "invalid_json")

    def test_lone_surrogate_rejected(self):
        self.path.write_text(json.dumps({"schemaVersion": 1, "init": "x", "states": [{"id": "\ud800"}], "transitions": []}, ensure_ascii=True))
        self.assertEqual(self.inspect()["error"]["code"], "model_invalid")

    def test_depth_limit_refusal(self):
        self.path.write_text("[" * 25 + "0" + "]" * 25)
        self.assertEqual(self.inspect()["error"]["code"], "model_too_deep")

    def test_file_size_refusal(self):
        self.path.write_bytes(b" " * (CORE.MAX_BYTES + 1))
        self.assertEqual(self.inspect()["error"]["code"], "input_too_large")

    def test_symlink_rejected(self):
        real = self.root / "实际.json"; real.write_text(json.dumps(simple()))
        self.path.symlink_to(real)
        self.assertEqual(self.inspect()["error"]["code"], "unsafe_path")

    def test_parent_swap_cannot_redirect_open_file(self):
        workspace = self.root / "工作区"; workspace.mkdir()
        parent = workspace / "模型"; parent.mkdir()
        source = parent / "模型.json"; source.write_text(json.dumps(simple()))
        outside = self.root / "工作区外"; outside.mkdir()
        (outside / "模型.json").write_text('{"private":"不可读入"}')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        real_open, swapped = os.open, []
        def intercept(path, flags, *args, **kwargs):
            if path == "模型.json" and kwargs.get("dir_fd") is not None and not swapped:
                parent.rename(workspace / "原始模型")
                parent.symlink_to(outside, target_is_directory=True)
                swapped.append(True)
            return real_open(path, flags, *args, **kwargs)
        with patch.object(CORE.os, "open", intercept):
            result = CORE.dispatch("inspect", {"workspace": str(workspace), "path": str(source)})
        self.assertTrue(swapped)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["model_sha256"], digest)

    def test_report_omission_is_distinct_from_search_incomplete(self):
        states = [{"id": f"链{i}"} for i in range(60)] + [{"id": f"死端{i}"} for i in range(40)]
        transitions = [{"from": f"链{i}", "event": "前进", "to": f"链{i+1}"} for i in range(59)]
        transitions += [{"from": "链59", "event": "分支", "to": f"死端{i}"} for i in range(40)]
        model = {"schemaVersion": 1, "init": "链0", "states": states, "transitions": transitions,
                 "variables": [{"name": "长变量名称" * 6 + str(i), "kind": "boolean", "init": False} for i in range(6)]}
        result = self.audit(model)
        self.assertTrue(result["analysis_complete"], result)
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["summary"]["finding_count"], 40)
        self.assertEqual(len(result["findings"]) + result["findings_omitted"], 40)
        self.assertGreater(result["findings_omitted"], 20)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False).encode()), CORE.RESULT_BYTES)

    def test_cli_help_and_error_are_chinese(self):
        command = [sys.executable, "-B", str(PAYLOAD / "runtime/audit.py")]
        help_result = subprocess.run(command + ["--help"], capture_output=True, text=True)
        self.assertIn("用法：", help_result.stdout)
        self.assertIn("选项", help_result.stdout)
        invalid = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("参数无效", invalid.stderr)

    def test_outside_workspace_refused(self):
        self.write(simple())
        sub = self.root / "子目录"; sub.mkdir()
        r = CORE.dispatch("inspect", {"workspace": str(sub), "path": str(self.path)})
        self.assertEqual(r["error"]["code"], "outside_workspace")

    def test_directory_and_relative_path_refused(self):
        for path in (str(self.root), "模型.json"):
            with self.subTest(path=path):
                self.assertFalse(CORE.dispatch("inspect", {"workspace": str(self.root), "path": path})["ok"])

    def test_explicit_confirmation_required(self):
        self.write(simple())
        for value in (False, 1, "true"):
            with self.subTest(value=value):
                self.assertEqual(self.audit(confirmed=value)["error"]["code"], "confirmation_required")

    def test_changed_raw_bytes_refused(self):
        self.write(simple()); digest = self.inspect()["model_sha256"]
        self.path.write_text(self.path.read_text() + "\n")
        self.assertEqual(self.audit(expected_sha256=digest)["error"]["code"], "model_changed")

    def test_invalid_hash_and_limits_refused(self):
        self.write(simple())
        for opts in ({"expected_sha256": "ABC"}, {"max_states": True}, {"max_states": 2001}, {"max_steps": 65}, {"max_edges": 0}):
            with self.subTest(opts=opts): self.assertFalse(self.audit(**opts)["ok"])

    def test_no_input_writes_and_deterministic(self):
        self.write(self.fixture("正常订单")); original = self.path.read_bytes(); files = list(self.root.iterdir())
        first, second = self.audit(), self.audit()
        self.assertEqual(first, second)
        self.assertEqual(original, self.path.read_bytes())
        self.assertEqual(files, list(self.root.iterdir()))

    def test_independent_finite_graph_oracle(self):
        # Independently enumerate all 16 possible directed graphs on two nodes.
        # Node 1 is forbidden. Oracle uses set closure, not the port's BFS helpers.
        for mask in range(16):
            m = {"schemaVersion": 1, "init": "0", "states": [{"id": "0"}, {"id": "1"}], "transitions": [],
                 "invariants": [{"id": "禁入", "kind": "never-states", "description": "不能进入1", "states": ["1"]}]}
            pairs = list(itertools.product(("0", "1"), repeat=2))
            chosen = [edge for bit, edge in enumerate(pairs) if mask & (1 << bit)]
            m["transitions"] = [{"from": a, "event": "e", "to": b} for a, b in chosen]
            reachable = {"0"}
            while True:
                expanded = reachable | {b for a, b in chosen if a in reachable}
                if expanded == reachable: break
                reachable = expanded
            dead = any(not any(a == state for a, _ in chosen) for state in reachable)
            r = self.audit(m)
            with self.subTest(mask=mask):
                self.assertTrue(r["analysis_complete"])
                self.assertEqual(set(r["summary"]["reachable_states"]), reachable)
                self.assertEqual(r["verdict"], "fail" if "1" in reachable or dead else "pass")

    def test_cli_real_subprocess(self):
        self.write(simple()); args = {"workspace": str(self.root), "path": str(self.path)}
        p = subprocess.run([sys.executable, "-B", str(PAYLOAD / "runtime/audit.py"), "inspect", "--input-json", json.dumps(args)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        args.update(confirmed=True, expected_sha256=json.loads(p.stdout)["model_sha256"], max_states=1)
        p = subprocess.run([sys.executable, "-B", str(PAYLOAD / "runtime/audit.py"), "audit", "--input-json", json.dumps(args)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(json.loads(p.stdout)["verdict"], "incomplete")


if __name__ == "__main__":
    unittest.main()
