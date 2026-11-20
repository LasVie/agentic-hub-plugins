from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("REHEARSAL_PAYLOAD", ASSET / ASSET.name))
SCRIPTS = PAYLOAD / "skills/rehearsal-evidence/scripts"
CASE = PAYLOAD / "examples/repair-shop.json"
sys.path.insert(0, str(SCRIPTS))
from plan import fallback_rules, restart_rules
from simulate import exercise
from verify import independent


class Rehearsal(unittest.TestCase):
    def setUp(self):
        scratch = ASSET / ".local"
        scratch.mkdir(exist_ok=True)
        work = TemporaryDirectory(dir=scratch, prefix="functional-")
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.input = self.root / "input.json"
        self.input.write_bytes(CASE.read_bytes())
        self.files = {
            "map": "map/dependency-map.json", "fallback": "fallback/fallback-plan.json",
            "restart": "restart/restart-plan.json", "baseline": "baseline/review-baseline.json",
            "trace": "trace/exercise-trace.json", "review": "review/independent-review.json",
        }

    def execute(self, script, phase=None, *, output, inputs=(), expected=0):
        command = [sys.executable, "-B", str(SCRIPTS / (script + ".py"))]
        if phase:
            command.append(phase)
        command += ["--input", str(self.input), "--output", str(self.root / output)]
        for name in inputs:
            command += ["--" + name, str(self.root / self.files[name])]
        done = subprocess.run(command, capture_output=True, text=True, timeout=12)
        self.assertEqual(done.returncode, expected, done.stdout + done.stderr)
        return done

    def amend(self, callback, filename=None):
        path = self.root / filename if filename else self.input
        data = json.loads(path.read_text())
        callback(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def through_trace(self):
        self.execute("verify", "baseline", output="baseline")
        self.execute("plan", "map", output="map")
        self.execute("plan", "fallback", output="fallback", inputs=["map"])
        self.execute("plan", "restart", output="restart", inputs=["map", "fallback"])
        self.execute("simulate", output="trace", inputs=["map", "fallback", "restart"])

    def review(self, expected=0):
        return self.execute("verify", "compare", output="review", inputs=list(self.files)[:-1], expected=expected)

    def deliver(self, expected=0):
        return self.execute("deliver", output="delivery", inputs=self.files, expected=expected)

    def test_full_chinese_outputs_and_item_accounting(self):
        self.through_trace()
        self.review()
        self.deliver()
        folder = self.root / "delivery"
        audit = json.loads((folder / "audit.json").read_text())
        routine, readonly = audit["scenarios"]
        self.assertTrue(routine["met"])
        self.assertEqual(routine["ready"], {"intake": 30, "assign": 35, "close": 40})
        self.assertEqual(routine["items"]["job-b"]["intake"], "deferred")
        self.assertEqual(routine["items"]["job-d"]["intake"], "deferred")
        self.assertEqual(routine["items"]["job-c"]["disposition"], "present")
        self.assertEqual(routine["items"]["job-f"]["disposition"], "online")
        self.assertFalse(readonly["met"])
        self.assertEqual(readonly["ready"], {})
        self.assertTrue(all(v["disposition"] == "hold_closed" for v in readonly["items"].values()))
        self.assertIn("未满足情景目标", (folder / "playbook.md").read_text(encoding="utf-8"))
        self.assertIn("工位负责人", (folder / "actions.csv").read_text(encoding="utf-8-sig"))
        self.assertEqual(len(audit["evidence_sha256"]), 6)
        log = [json.loads(row) for row in (folder / "scenario-trace.jsonl").read_text().splitlines()]
        self.assertEqual(sum(r["event"] == "account" for r in log), 9)
        self.deliver(expected=2)

    def test_hold_conflicting_revision_and_missed_due(self):
        def edit(data):
            data["scenarios"][0]["snapshot"][0]["revision"] = 1
            data["scenarios"][0]["items"][0]["due"] = 29
        self.amend(edit)
        self.through_trace()
        self.review()
        self.deliver()
        routine = json.loads((self.root / "delivery/audit.json").read_text())["scenarios"][0]
        self.assertFalse(routine["met"])
        self.assertEqual(routine["items"]["job-c"]["disposition"], "hold_conflict")
        self.assertFalse(routine["items"]["job-a"]["met_due"])

    def test_tampered_trace_duplicate_is_named_and_blocks_delivery(self):
        self.through_trace()
        def duplicate(data):
            entries = data["data"][0]["events"]
            index = next(i for i, row in enumerate(entries) if row[1:3] == ["account", "job-c"])
            entries.insert(index, entries[index])
        self.amend(duplicate, self.files["trace"])
        done = self.review(expected=3)
        self.assertIn("job-c", done.stdout)
        self.deliver(expected=2)
        self.assertFalse((self.root / "delivery").exists())

    def test_missing_item_invalidates_review(self):
        self.through_trace()
        self.amend(lambda d: d["data"][0]["items"].pop("job-b"), self.files["trace"])
        self.assertIn("job-b", self.review(expected=3).stdout)

    def test_moved_audit_event_blocks_comparison(self):
        self.through_trace()
        def edit(data):
            row = next(row for row in data["data"][1]["events"] if row[1] == "account")
            row[0] = 0
        self.amend(edit, self.files["trace"])
        self.review(expected=3)

    def test_forged_review_cannot_release_results(self):
        self.through_trace()
        self.review()
        self.amend(lambda d: d["data"].update(items=500), self.files["review"])
        self.deliver(expected=2)
        self.assertFalse((self.root / "delivery").exists())

    def test_input_and_fallback_handoff_are_frozen(self):
        self.through_trace()
        self.amend(lambda d: d.update(title="新版本"))
        self.review(expected=2)

    def test_tampered_fallback_constraints_block_replay(self):
        self.through_trace()
        self.amend(lambda d: d["data"]["staff_limits"].update(desk=40), self.files["fallback"])
        self.execute("simulate", output="new-trace", inputs=["map", "fallback", "restart"], expected=2)

    def test_rewritten_plan_after_execution_blocks_release(self):
        self.through_trace()
        self.review()
        path = self.root / self.files["restart"]
        path.write_bytes(path.read_bytes() + b"\n")
        self.deliver(expected=2)

    def test_baseline_rejects_other_roles_inputs(self):
        done = self.execute("verify", "baseline", output="baseline", inputs=["restart"], expected=2)
        self.assertIn("只接受原始案例", done.stderr)

    def test_cycle_unknown_owner_and_boolean_limit_rejected(self):
        for mutate in (lambda d: d["workflows"][0].update(needs=["close"]),
                       lambda d: d["workflows"][0].update(owner="unknown"),
                       lambda d: d["staff"][0].update(capacity=True)):
            self.input.write_bytes(CASE.read_bytes())
            self.amend(mutate)
            self.assertIn("流程停止", self.execute("plan", "map", output="map", expected=2).stderr)

    def test_future_snapshot_item_rejected(self):
        self.amend(lambda d: d["scenarios"][0]["snapshot"].append({"id": "job-f", "revision": 1}))
        self.assertIn("尚未到达", self.execute("plan", "map", output="map", expected=2).stderr)

    def test_duplicate_json_and_missing_staff_rejected(self):
        self.input.write_text('{"schema":1,"schema":1}')
        self.assertIn("字段重复", self.execute("plan", "map", output="map", expected=2).stderr)
        self.input.write_bytes(CASE.read_bytes())
        self.amend(lambda d: d.pop("staff"))
        self.assertIn("字段不完整", self.execute("plan", "map", output="map", expected=2).stderr)

    def test_two_independent_algorithms_agree_bounded_variations(self):
        rng = random.Random(174)
        source = json.loads(CASE.read_text())
        for seed in range(40):
            with self.subTest(seed=seed):
                case = deepcopy(source)
                for flow in case["workflows"]:
                    flow["startup"] = rng.randint(0, 120)
                    flow["manual_limit"] = rng.randint(0, 4)
                for staff in case["staff"]:
                    staff["capacity"] = rng.randint(0, 5)
                scenario = case["scenarios"][0]
                for event in scenario["events"]:
                    if event["kind"] == "owner_approved":
                        event["minute"] = rng.randint(1, 120)
                for item in scenario["items"]:
                    item["due"] = rng.randint(item["arrival"], 120)
                self.assertEqual(exercise(case, fallback_rules(case), restart_rules(case)), independent(case))


if __name__ == "__main__":
    unittest.main()
