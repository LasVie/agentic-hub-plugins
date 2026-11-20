"""Verify the actual source or exact extracted package command chain."""
from collections import Counter
import csv
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ASSET = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("MEETING_PAYLOAD", ASSET / ASSET.name)).resolve()
SAMPLE = ROOT / "examples/clock-change.json"
ROLES = {"intake": "analyst", "plan": "planner", "verify": "verifier", "deliver": "leader"}


class Meetings(unittest.TestCase):
    def setUp(self):
        scratch = ASSET / ".local/disposable-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="meeting-", dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original = self.root / "input.json"
        self.case = json.loads(SAMPLE.read_text())
        self.named = {key: self.root / name for key, name in {
            "intake": "intake.json", "plan": "plan.json", "baseline": "baseline.json",
            "review": "review.json", "delivery": "delivery"}.items()}

    def invoke(self, role, *extra, expected=0, **flags):
        exe = ROOT / "agents" / ROLES[role] / "tools" / (role + ".py")
        argv = [sys.executable, "-B", str(exe), *extra, "--input", str(self.original)]
        for key, val in flags.items():
            argv.extend(["--" + key, str(val)])
        result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def put(self, data=None):
        self.original.write_text(json.dumps(self.case if data is None else data, ensure_ascii=False) + "\n")

    def get(self, name):
        return json.loads(self.named[name].read_text())

    def prepare(self):
        self.put()
        self.invoke("intake", output=self.named["intake"])
        self.invoke("verify", "baseline", output=self.named["baseline"])
        self.invoke("plan", intake=self.named["intake"], output=self.named["plan"])

    def compare(self, expected=0):
        self.invoke("verify", "compare", expected=expected,
                    **{n: self.named[n] for n in ("intake", "baseline", "plan")}, output=self.named["review"])

    def deliver(self, expected=0):
        self.invoke("deliver", expected=expected,
                    **{n: self.named[n] for n in ("intake", "baseline", "plan", "review")}, output=self.named["delivery"])

    def audit(self):
        self.prepare()
        before = self.original.read_bytes()
        self.compare()
        self.deliver()
        self.assertEqual(before, self.original.read_bytes())
        return json.loads((self.named["delivery"] / "audit.json").read_text())

    def test_actual_chain_preserves_march_stagger_and_exceptions(self):
        audit = self.audit()
        self.assertEqual(audit["verification"], "consistent")
        rows = audit["rows"][:4]
        self.assertEqual([r["people"][1]["start"][11:16] for r in rows], ["15:00", "14:00", "14:00", "15:00"])
        self.assertEqual([r["status"] for r in rows], ["conflict", "ok", "conflict", "ok"])
        self.assertEqual(rows[2]["people"][1]["outside_minutes"], 10)
        self.assertEqual(rows[0]["people"][2]["outside_minutes"], 30)
        self.assertEqual({p for p in audit["zones"]}, {"America/New_York", "Europe/Berlin", "Asia/Singapore"})
        self.assertTrue(all(len(p["tzif_sha256"]) == 64 for p in audit["zones"].values()))
        with (self.named["delivery"] / "meetings.csv").open(encoding="utf-8-sig", newline="") as f:
            records = list(csv.DictReader(f))
        self.assertEqual(len(records), 24)
        self.assertEqual(Counter(r["候选"] for r in records), {"nine": 12, "eight": 12})
        report = (self.named["delivery"] / "review.md").read_text()
        self.assertIn("nine：2/4", report)
        self.assertIn("eight：4/4", report)

    def test_gap_is_reported_without_moving_start(self):
        self.case.update(start_date="2027-03-14", slots=[{"id": "gap", "start": "02:30"}])
        r = self.audit()["rows"][0]
        self.assertEqual(r["status"], "nonexistent")
        self.assertEqual(r["alternatives_utc"], [])
        self.assertNotIn("start_utc", r)

    def test_overlap_lists_both_instants(self):
        self.case.update(start_date="2027-11-07", slots=[{"id": "repeat", "start": "01:30"}])
        r = self.audit()["rows"][0]
        self.assertEqual(r["status"], "ambiguous")
        self.assertEqual(r["alternatives_utc"], ["2027-11-07T05:30+00:00", "2027-11-07T06:30+00:00"])

    def test_cross_midnight_local_and_equal_to_closing(self):
        self.case.update(organizer_zone="UTC", slots=[{"id": "night", "start": "15:45"}])
        target = self.case["participants"][2]
        target["weekly"].update(mon=[["23:45", "24:00"]], tue=[["00:00", "00:15"]])
        p = self.audit()["rows"][0]["people"][2]
        self.assertEqual((p["start"], p["end"], p["outside_minutes"]),
                         ("2027-03-08T23:45+08:00", "2027-03-09T00:15+08:00", 0))

    def test_actual_elapsed_minutes_cross_spring_transition(self):
        self.case.update(start_date="2027-03-14", duration_minutes=60, slots=[{"id": "jump", "start": "01:30"}])
        self.case["participants"][0]["weekly"]["sun"] = [["01:00", "04:00"]]
        r = self.audit()["rows"][0]
        self.assertEqual((r["start_utc"], r["end_utc"]), ("2027-03-14T06:30+00:00", "2027-03-14T07:30+00:00"))
        self.assertEqual((r["people"][0]["end"], r["people"][0]["outside_minutes"]), ("2027-03-14T03:30-04:00", 0))

    def test_non_hour_zone_and_full_date_closure(self):
        self.case["participants"][2].update(zone="Asia/Kathmandu", overrides={"2027-03-08": []})
        p = self.audit()["rows"][0]["people"][2]
        self.assertEqual(p["start"], "2027-03-08T19:45+05:45")
        self.assertEqual(p["outside_minutes"], 30)

    def test_duplicate_headers_and_nonfinite_json_rejected(self):
        for content in ('{"schema_version":1,"schema_version":1}', '{"schema_version": NaN}'):
            self.original.write_text(content)
            self.assertIn("核验中止", self.invoke("intake", output=self.named["intake"], expected=2).stderr)

    def test_missing_confirmed_availability_is_never_filled_in(self):
        del self.case["participants"][0]["weekly"]["mon"]
        self.put()
        self.assertIn("字段", self.invoke("intake", output=self.named["intake"], expected=2).stderr)

    def test_unknown_iana_zone_has_readable_chinese_failure(self):
        self.case["organizer_zone"] = "Unknown/Locality"
        self.put()
        self.assertIn("IANA 数据", self.invoke("intake", output=self.named["intake"], expected=2).stderr)

    def test_read_only_and_refuse_overwrite(self):
        self.audit()
        before = (self.named["delivery"] / "audit.json").read_bytes()
        self.deliver(expected=2)
        self.assertEqual((self.named["delivery"] / "audit.json").read_bytes(), before)
        self.invoke("intake", output=self.named["intake"], expected=2)

    def test_stale_or_tampered_plan_blocks_review_and_delivery(self):
        self.prepare()
        plan = self.get("plan")
        plan["rows"][0]["people"][0]["outside_minutes"] = True
        self.named["plan"].write_text(json.dumps(plan))
        self.compare(expected=1)
        self.assertEqual(self.get("review")["verdict"], "disagreement")
        self.deliver(expected=2)
        self.assertFalse(self.named["delivery"].exists())

    def test_rewritten_plan_after_review_blocks_delivery(self):
        self.prepare()
        self.compare()
        with self.named["plan"].open("a") as out:
            out.write("\n")
        self.deliver(expected=2)

    def test_changed_original_bytes_invalidate_receipts(self):
        self.prepare()
        self.compare()
        with self.original.open("a") as out:
            out.write("\n")
        self.deliver(expected=2)

    def test_tzif_fingerprint_mismatch_is_a_disagreement(self):
        self.prepare()
        baseline = self.get("baseline")
        baseline["zones"]["America/New_York"]["tzif_sha256"] = "0"*64
        self.named["baseline"].write_text(json.dumps(baseline))
        self.compare(expected=1)

    def test_csv_labels_are_not_executed_as_formulas(self):
        self.case["participants"][1]["label"] = " =SUM(1,2)"
        self.audit()
        with (self.named["delivery"] / "meetings.csv").open(encoding="utf-8-sig", newline="") as f:
            self.assertIn("' =SUM(1,2)", [row["参会者"] for row in csv.DictReader(f)])

    def test_maximum_review_stays_under_evidence_limits(self):
        self.case.update(weeks=12, duration_minutes=120)
        self.case["slots"].append({"id": "ten", "start": "10:00"})
        for i in range(5):
            self.case["participants"].append(dict(self.case["participants"][0], id=f"guest-{i}"))
        audit = self.audit()
        self.assertEqual(len(audit["rows"]), 36)
        self.assertEqual(sum(len(r["people"]) for r in audit["rows"]), 288)


if __name__ == "__main__":
    unittest.main()
