"""Behavior and negative-control tests; all created workspaces are disposable.

ROTA_PAYLOAD selects an extracted, unchanged payload for the same real callers.
No network, host or model is used by these program-level checks.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("ROTA_PAYLOAD", BASE / "household-chore-rota-team")).resolve()
SCRIPTS = {
    "intake": PAYLOAD / "agents/analyst/tools/intake.py",
    "plan": PAYLOAD / "agents/planner/tools/plan.py",
    "verify": PAYLOAD / "agents/verifier/tools/verify.py",
    "deliver": PAYLOAD / "agents/leader/tools/deliver.py",
}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sys.path.insert(0, str(PAYLOAD / "skills/rota-evidence/scripts"))
import contract
planner = module("rota_planner_test", SCRIPTS["plan"])
independent = module("rota_independent_test", SCRIPTS["verify"])
leader = module("rota_leader_test", SCRIPTS["deliver"])


class RotaTests(unittest.TestCase):
    def setUp(self):
        scratch = BASE / ".local/disposable-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.work = Path(self.tmp.name)
        self.case = json.loads((BASE / "tests/fixtures/complete.json").read_text(encoding="utf-8"))
        self.input = self.put("case.json", self.case)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, obj):
        path = self.work / name
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def call(self, tool, *args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS[tool]), *map(str, args)],
                                capture_output=True, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=15)
        self.assertEqual(result.returncode, expected, (tool, result.stdout, result.stderr))
        self.assertNotIn("Traceback", result.stderr)
        obj = json.loads(result.stdout)
        return obj

    def prepared(self, case=None, node_limit=100000, status="feasible"):
        if case is not None:
            self.case = case
            self.put("case.json", case)
        self.call("intake", "--input", self.input, "--output", self.work / "intake")
        self.call("plan", "--input", self.input, "--intake", self.work / "intake/intake.json",
                  "--output", self.work / "plan", "--node-limit", node_limit, expected=0 if status == "feasible" else 1)
        return json.loads((self.work / "plan/plan.json").read_text())

    def reviewed(self, expected=0, conclusion="pass"):
        self.call("verify", "--input", self.input, "--plan", self.work / "plan/plan.json", "--output", self.work / "verification", expected=expected)
        self.review = json.loads((self.work / "verification/review.json").read_text())
        self.put("review-notes.json", {"schema_version": 1, "case_sha256": self.review["case_sha256"],
                                      "plan_sha256": self.review["plan_sha256"], "conclusion": conclusion,
                                      "reasons": ["确定性夹具说明：仅测试程序交接，不能当作真实成员内容审查。"]})
        return self.review

    def delivered(self, expected=0):
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json",
                  "--plan", self.work / "plan/plan.json", "--review", self.work / "verification/review.json",
                  "--notes", self.work / "review-notes.json", "--output", self.work / "delivery", expected=expected)
        return json.loads((self.work / "delivery/review.json").read_text())

    def test_complete_real_cli_handoffs_and_outputs(self):
        original = self.input.read_bytes()
        plan = self.prepared()
        review = self.reviewed()
        dossier = self.delivered()
        self.assertEqual(dossier["delivery_status"], "verified")
        self.assertEqual(sum(x["weekly_minutes"] for x in review["loads"].values()), 180)
        self.assertEqual(review["loads"], plan["loads"])
        self.assertEqual(self.input.read_bytes(), original)
        self.assertEqual({p.name for p in (self.work / "delivery").iterdir()}, {"rota.html", "assignments.csv", "review.json"})
        html = (self.work / "delivery/rota.html").read_text()
        self.assertEqual(html.count('class="day"'), 7)
        self.assertIn("合住小家", html)
        self.assertIn("约定检查通过", html)
        rows = list(csv.reader(io.StringIO((self.work / "delivery/assignments.csv").read_text(encoding="utf-8-sig"))))
        self.assertEqual(len(rows), 8)
        self.assertEqual(dossier["source_sha256"], hashlib.sha256(original).hexdigest())

    def test_full_twenty_one_occurrences_six_people(self):
        full = json.loads((PAYLOAD / "examples/full-week.json").read_text())
        self.prepared(full)
        review = self.reviewed()
        self.assertEqual(len(self.delivered()["result"]["assignments"]), 21)
        self.assertEqual(sum(p["weekly_minutes"] for p in review["loads"].values()), 315)

    def test_soft_preference_cannot_override_unavailability(self):
        plan = self.prepared()
        self.assertEqual(next(x["participant_id"] for x in plan["assignments"] if x["duty_id"] == "c04"), "wang")
        self.assertIn("c04", plan["preference_misses"])
        self.reviewed()
        self.delivered()
        self.assertIn("偏好未满足", (self.work / "delivery/rota.html").read_text())

    def test_impossible_is_not_a_verified_rota(self):
        bad = json.loads((BASE / "tests/fixtures/impossible.json").read_text())
        plan = self.prepared(bad, status="infeasible")
        self.assertTrue(plan["search"]["space_exhausted"])
        self.assertIsNone(plan["loads"])
        self.reviewed(expected=1, conclusion="block")
        dossier = self.delivered(expected=1)
        self.assertEqual(dossier["delivery_status"], "draft")
        self.assertIsNone(dossier["result"]["loads"])
        self.assertIn("未核验，不记为零", (self.work / "delivery/rota.html").read_text())

    def test_node_limit_is_unknown_not_infeasible(self):
        plan = self.prepared(node_limit=1, status="unknown")
        self.assertEqual(plan["status"], "unknown")
        self.assertFalse(plan["search"]["space_exhausted"])
        self.assertEqual(plan["assignments"], [])
        self.reviewed(expected=1, conclusion="block")
        self.assertEqual(self.delivered(expected=1)["delivery_status"], "draft")

    def test_independent_checker_rejects_dropped_and_duplicated_duties(self):
        plan = self.prepared()
        source = hashlib.sha256(self.input.read_bytes()).hexdigest()
        for assignments in (plan["assignments"][:-1], plan["assignments"][:-1] + [plan["assignments"][0]]):
            altered = copy.deepcopy(plan)
            altered["assignments"] = assignments
            review = independent.check(self.case, altered, source, contract.digest(altered))
            self.assertEqual(review["verdict"], "block")
            self.assertIsNone(review["loads"])

    def test_wrong_planner_totals_are_blocked(self):
        plan = self.prepared()
        plan["loads"]["lin"]["weekly_minutes"] += 1
        self.put("plan/plan.json", plan)
        review = self.reviewed(expected=1)
        self.assertTrue(any("独立复算不一致" in x for x in review["issues"]))

    def test_report_numeric_types_cannot_masquerade_as_integer_minutes(self):
        plan = self.prepared()
        plan["loads"]["lin"]["weekly_minutes"] = float(plan["loads"]["lin"]["weekly_minutes"])
        self.put("plan/plan.json", plan)
        self.reviewed(expected=1)
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json",
                  "--plan", self.work / "plan/plan.json", "--review", self.work / "verification/review.json",
                  "--notes", self.work / "review-notes.json", "--output", self.work / "delivery", expected=2)

    def test_intake_summary_cannot_change_count_representation(self):
        self.call("intake", "--input", self.input, "--output", self.work / "intake")
        report = json.loads((self.work / "intake/intake.json").read_text())
        report["summary"]["total_minutes"] = float(report["summary"]["total_minutes"])
        self.put("intake/intake.json", report)
        self.call("plan", "--input", self.input, "--intake", self.work / "intake/intake.json", "--output", self.work / "plan", expected=2)

    def test_forged_optimality_claim_does_not_pass_delivery(self):
        self.prepared()
        self.reviewed()
        plan = json.loads((self.work / "plan/plan.json").read_text())
        plan["search"]["optimality_claim"] = True
        self.put("plan/plan.json", plan)
        sha = hashlib.sha256((self.work / "plan/plan.json").read_bytes()).hexdigest()
        self.review["plan_sha256"] = sha
        self.put("verification/review.json", self.review)
        notes = json.loads((self.work / "review-notes.json").read_text())
        notes["plan_sha256"] = sha
        self.put("review-notes.json", notes)
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json",
                  "--plan", self.work / "plan/plan.json", "--review", self.work / "verification/review.json",
                  "--notes", self.work / "review-notes.json", "--output", self.work / "delivery", expected=2)
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json",
                  "--plan", self.work / "plan/plan.json", "--review", self.work / "verification/review.json",
                  "--notes", self.work / "review-notes.json", "--output", self.work / "delivery", expected=2)
        self.assertFalse((self.work / "delivery").exists())

    def test_eligibility_unavailable_daily_and_weekly_caps_are_independent_checks(self):
        plan = self.prepared()
        for kind in ("eligibility", "unavailable", "daily", "weekly"):
            case = copy.deepcopy(self.case)
            changed = copy.deepcopy(plan)
            target = changed["assignments"][0]
            pid, did = target["participant_id"], target["duty_id"]
            duty = next(d for d in case["duties"] if d["id"] == did)
            person = next(p for p in case["participants"] if p["id"] == pid)
            if kind == "eligibility":
                duty["eligible"] = [x for x in duty["eligible"] if x != pid]
                duty["preferred"] = [x for x in duty["preferred"] if x != pid]
            elif kind == "unavailable":
                person["unavailable_days"] = sorted(set(person["unavailable_days"]) | {duty["day"]})
            elif kind == "daily":
                person["daily_limits"][duty["day"]] = 0
            else:
                person["weekly_limit"] = 0
            changed["case_sha256"] = contract.digest(case)
            changed["source_sha256"] = "f" * 64
            with self.subTest(kind=kind):
                review = independent.check(case, changed, "f" * 64, contract.digest(changed))
                self.assertEqual(review["verdict"], "block")
                self.assertTrue(review["issues"])

    def test_leader_recomputes_even_if_review_is_forged_pass(self):
        self.prepared()
        self.reviewed()
        plan = json.loads((self.work / "plan/plan.json").read_text())
        next(x for x in plan["assignments"] if x["duty_id"] == "c04")["participant_id"] = "chen"
        loads, issues, misses = contract.loads_for(self.case, plan["assignments"])
        self.assertTrue(issues)
        plan["loads"], plan["preference_misses"] = loads, misses
        self.put("plan/plan.json", plan)
        sha = hashlib.sha256((self.work / "plan/plan.json").read_bytes()).hexdigest()
        self.review.update({"plan_sha256": sha, "loads": loads, "preference_misses": misses, "verdict": "pass", "issues": []})
        self.put("verification/review.json", self.review)
        notes = json.loads((self.work / "review-notes.json").read_text())
        notes["plan_sha256"] = sha
        self.put("review-notes.json", notes)
        self.assertEqual(self.delivered(expected=1)["delivery_status"], "draft")

    def test_content_review_block_survives_math_pass(self):
        self.prepared()
        self.reviewed(conclusion="block")
        dossier = self.delivered(expected=1)
        self.assertEqual(dossier["delivery_status"], "draft")
        self.assertTrue(any("内容复核阻塞" in x for x in dossier["result"]["blockers"]))

    def test_input_bytes_changed_invalidate_handoff(self):
        self.prepared()
        self.input.write_text(self.input.read_text() + "\n")
        self.call("verify", "--input", self.input, "--plan", self.work / "plan/plan.json", "--output", self.work / "verification", expected=2)

    def test_plan_bytes_changed_invalidate_independent_review(self):
        self.prepared()
        self.reviewed()
        p = self.work / "plan/plan.json"
        p.write_text(p.read_text() + "\n")
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json", "--plan", p,
                  "--review", self.work / "verification/review.json", "--notes", self.work / "review-notes.json",
                  "--output", self.work / "delivery", expected=2)

    def test_intake_case_tampering_cannot_reach_planning(self):
        self.call("intake", "--input", self.input, "--output", self.work / "intake")
        intake = json.loads((self.work / "intake/intake.json").read_text())
        intake["case"]["duties"][0]["minutes"] += 10
        self.put("intake/intake.json", intake)
        self.call("plan", "--input", self.input, "--intake", self.work / "intake/intake.json", "--output", self.work / "plan", expected=2)

    def test_existing_output_is_never_overwritten(self):
        self.prepared()
        old = (self.work / "plan/plan.json").read_bytes()
        self.call("plan", "--input", self.input, "--intake", self.work / "intake/intake.json", "--output", self.work / "plan", expected=2)
        self.assertEqual((self.work / "plan/plan.json").read_bytes(), old)
        self.reviewed()
        self.delivered()
        before = {p.name: p.read_bytes() for p in (self.work / "delivery").iterdir()}
        self.call("deliver", "--input", self.input, "--intake", self.work / "intake/intake.json", "--plan", self.work / "plan/plan.json", "--review", self.work / "verification/review.json", "--notes", self.work / "review-notes.json", "--output", self.work / "delivery", expected=2)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.work / "delivery").iterdir()})

    def test_html_and_csv_treat_names_as_data(self):
        self.case["household"] = '<script>alert("x")</script>'
        self.case["duties"][0]["name"] = '=HYPERLINK("x")<img src=x>'
        self.prepared(self.case)
        self.reviewed()
        self.delivered()
        html = (self.work / "delivery/rota.html").read_text()
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x>", html)
        self.assertIn("&lt;script&gt;", html)
        rows = list(csv.reader(io.StringIO((self.work / "delivery/assignments.csv").read_text(encoding="utf-8-sig"))))
        self.assertTrue(rows[1][1].startswith("'="))

    def test_input_edge_cases_rejected_by_both_parsers(self):
        changes = [
            lambda c: c.update(schema_version=True), lambda c: c.update(extra="无效"),
            lambda c: c.update(start_date="2026-02-30"), lambda c: c.update(start_date="9999-12-29"),
            lambda c: c["participants"].append(copy.deepcopy(c["participants"][0])),
            lambda c: c["participants"][0].update(daily_limits=[60]),
            lambda c: c["participants"][0].update(weekly_limit=True),
            lambda c: c["participants"][0].update(unavailable_days=[0, 0]),
            lambda c: c["duties"][0].update(minutes=True), lambda c: c["duties"][0].update(minutes=1.5),
            lambda c: c["duties"][0].update(day=7), lambda c: c["duties"][0].update(minutes=0),
            lambda c: c["duties"][0].update(eligible=["unknown"]),
            lambda c: c["duties"][0].update(preferred=["wang"]),
            lambda c: c["duties"][0].update(name="\t非法"),
            lambda c: c.update(duties=c["duties"] * 4),
        ]
        for i, change in enumerate(changes):
            bad = copy.deepcopy(self.case)
            change(bad)
            with self.subTest(variant=i):
                with self.assertRaises(ValueError):
                    contract.validate_case(bad)
                with self.assertRaises(ValueError):
                    independent.inspect_case(bad)

    def test_duplicate_json_keys_and_symlinks_are_refused(self):
        self.input.write_text('{"schema_version":1,"schema_version":1}')
        self.call("intake", "--input", self.input, "--output", self.work / "intake", expected=2)
        with self.assertRaises(ValueError):
            independent.load(self.input)
        link = self.work / "linked.json"
        link.symlink_to(self.input)
        self.call("intake", "--input", link, "--output", self.work / "intake", expected=2)
        with self.assertRaises(ValueError):
            independent.load(link)

    def test_unknown_assignment_reference_is_not_accepted(self):
        plan = self.prepared()
        plan["assignments"][0]["participant_id"] = "outsider"
        self.put("plan/plan.json", plan)
        self.call("verify", "--input", self.input, "--plan", self.work / "plan/plan.json", "--output", self.work / "verification", expected=2)

    def test_review_fields_are_strict_and_content_reasons_required(self):
        self.prepared()
        self.reviewed()
        intake = json.loads((self.work / "intake/intake.json").read_text())
        plan = json.loads((self.work / "plan/plan.json").read_text())
        source = hashlib.sha256(self.input.read_bytes()).hexdigest()
        intake_sha = hashlib.sha256((self.work / "intake/intake.json").read_bytes()).hexdigest()
        plan_sha = hashlib.sha256((self.work / "plan/plan.json").read_bytes()).hexdigest()
        for change in (lambda n: n.update(reasons=[]), lambda n: n.update(conclusion="maybe"), lambda n: n.update(schema_version=True), lambda n: n.update(case_sha256="0" * 64)):
            notes = json.loads((self.work / "review-notes.json").read_text())
            change(notes)
            with self.assertRaises(ValueError):
                leader.check_reports(self.case, source, intake, intake_sha, plan, plan_sha, self.review, notes)

    def test_readable_chinese_missing_input_error(self):
        self.call("intake", "--input", self.work / "missing.json", "--output", self.work / "intake", expected=2)
        result = self.call("plan", "--input", self.input, expected=2)
        self.assertIn("参数", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
