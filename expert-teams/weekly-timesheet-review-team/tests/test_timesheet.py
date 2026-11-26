"""Exercise the same CLI from the source and the extracted release."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT.parent / ROOT.parent.name
SCRIPT = Path(os.environ.get("TIMESHEET_TEST_PAYLOAD", PAYLOAD)) / "skills/timesheet-review/scripts/timesheet_review.py"
FIXTURE = ROOT / "fixtures/mixed-week.csv"
CASE = ROOT / "fixtures/mixed-week.json"


class TimesheetTest(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="timesheet-test-")
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.case = CASE
        self.csv = FIXTURE

    def stage(self, name, *args, output=None, ok=True):
        destination = self.root / (output or name)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), name, "--case", str(self.case),
                                 "--entries", str(self.csv), "--output", str(destination), *args],
                                capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        response = json.loads(result.stdout if ok else result.stderr)
        self.assertEqual(response["ok"], ok)
        return destination, response

    def entries(self, content):
        self.csv = self.root / "entries.csv"
        self.csv.write_text(content, encoding="utf-8")

    def compare(self):
        baseline, _ = self.stage("baseline")
        analysis, _ = self.stage("analyze")
        links = ["--baseline", str(baseline), "--analysis", str(analysis)]
        return baseline, analysis, links

    def test_delivered_week_and_source_hashes(self):
        baseline, analysis, links = self.compare()
        review, _ = self.stage("verify", *links)
        bundle, _ = self.stage("deliver", *links, "--review", str(review))
        review_record = json.loads(review.read_bytes())
        result = review_record["result"]
        self.assertEqual(result["status"], "reviewed_with_holds")
        self.assertEqual(result["included_minutes"], 260)
        self.assertEqual(result["days"]["2026-11-16"], 105)
        self.assertEqual(result["days"]["2026-11-17"], 155)
        self.assertEqual(result["held_rows"], [2, 3, 4, 5, 8])
        self.assertEqual(result["projects"], {"夜班支持": 210, "周报": 50})
        self.assertEqual(Counter(f["code"] for f in result["findings"]),
                         {"duplicate": 1, "overlap": 1, "invalid_time": 1,
                          "expected_day_unconfirmed": 1, "outside_week": 1})
        self.assertEqual(next(f["minutes"] for f in result["findings"] if f["code"] == "overlap"), 30)
        artifact = json.loads((bundle / "artifact.json").read_bytes())
        self.assertFalse(artifact["human_testing_passed"])
        self.assertEqual(len(artifact["files_sha256"]), 7)
        for name, checksum in artifact["files_sha256"].items():
            self.assertEqual(hashlib.sha256((bundle / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual((bundle / "inputs/entries.csv").read_bytes(), self.csv.read_bytes())
        self.assertEqual((bundle / "inputs/analysis.json").read_bytes(), analysis.read_bytes())
        self.assertEqual((bundle / "inputs/baseline.json").read_bytes(), baseline.read_bytes())
        self.assertIn("需核实的记录", (bundle / "checklist.html").read_text())
        _, failure = self.stage("deliver", *links, "--review", str(review), ok=False)
        self.assertIn("已存在", failure["message"])

    def test_altered_analysis_stops_review(self):
        _, analysis, links = self.compare()
        forged = json.loads(analysis.read_bytes())
        forged["result"]["findings"] = []
        analysis.write_text(json.dumps(forged, ensure_ascii=False))
        out, failure = self.stage("verify", *links, ok=False)
        self.assertIn("候选分析报告", failure["message"])
        self.assertFalse(out.exists())

    def test_reserialized_review_does_not_pass_the_byte_binding(self):
        _, _, links = self.compare()
        review, _ = self.stage("verify", *links)
        review.write_text(json.dumps(json.loads(review.read_bytes()), ensure_ascii=False))
        target, failure = self.stage("deliver", *links, "--review", str(review), ok=False)
        self.assertFalse(target.exists())
        self.assertIn("正式复核报告", failure["message"])

    def test_changed_source_bytes_invalidate_old_reports(self):
        _, _, links = self.compare()
        self.entries(FIXTURE.read_text() + "\n")
        _, failure = self.stage("verify", *links, ok=False)
        self.assertIn("独立初核报告", failure["message"])

    def test_clip_week_and_treat_touching_intervals_as_adjacent(self):
        self.case = self.root / "simple.json"
        self.case.write_text('{"week_start":"2026-11-16","utc_offset":"+08:00"}')
        self.entries("project,start,end\n"
                     "周初,2026-11-15 23:30,2026-11-16 00:30\n"
                     "相邻班次,2026-11-16 00:30,2026-11-16 01:00\n"
                     "周末,2026-11-22 23:15,2026-11-23 01:00\n")
        _, _, links = self.compare()
        result, _ = self.stage("verify", *links)
        summary = json.loads(result.read_bytes())["result"]
        self.assertEqual(summary["included_minutes"], 105)
        self.assertEqual(summary["status"], "reviewed")
        self.assertEqual(summary["findings"], [])

    def test_work_during_another_records_break_is_not_an_overlap(self):
        self.entries("project,start,end,break_start,break_end\n"
                     "白班,2026-11-16 09:00,2026-11-16 11:00,2026-11-16 10:00,2026-11-16 10:30\n"
                     "补记,2026-11-16 10:00,2026-11-16 10:30,,\n")
        _, _, links = self.compare()
        result, _ = self.stage("verify", *links)
        summary = json.loads(result.read_bytes())["result"]
        self.assertEqual(summary["included_minutes"], 120)
        self.assertNotIn("overlap", [f["code"] for f in summary["findings"]])

    def test_line_number_preserved_after_multiline_rejected_label(self):
        self.entries('project,start,end\n"跨\n行",2026-11-16 09:00,2026-11-16 10:00\n'
                     '例会,2026-11-16 11:00,2026-11-16 12:00\n')
        baseline, _, links = self.compare()
        self.stage("verify", *links)
        result = json.loads(baseline.read_bytes())["result"]
        self.assertEqual(result["rows"][0]["row"], 4)
        self.assertEqual(result["held_rows"], [2])

    def test_malformed_or_unknown_time_is_held(self):
        self.entries("project,start,end,break_start,break_end\n"
                     "日期错,2026-02-30 09:00,2026-11-16 12:00,,\n"
                     "休息时点缺失,2026-11-16 09:00,2026-11-16 12:00,2026-11-16 10:00,\n"
                     "逆序,2026-11-16 12:00,2026-11-16 09:00,,\n"
                     "字段缺失,2026-11-16 12:00\n")
        baseline, _, links = self.compare()
        self.stage("verify", *links)
        findings = json.loads(baseline.read_bytes())["result"]["findings"]
        self.assertEqual([f["code"] for f in findings[:4]],
                         ["invalid_time", "invalid_break", "invalid_duration", "invalid_row"])

    def test_unsafe_html_is_escaped(self):
        self.entries("project,start,end\n<script>有标签</script>,2026-11-16 09:00,2026-11-16 10:00\n")
        _, _, links = self.compare()
        review, _ = self.stage("verify", *links)
        bundle, _ = self.stage("deliver", *links, "--review", str(review))
        page = (bundle / "checklist.html").read_text()
        self.assertIn("&lt;script&gt;有标签&lt;/script&gt;", page)
        self.assertNotIn("<script>", page)

    def test_configuration_refuses_implicit_timezone(self):
        self.case = self.root / "bad.json"
        self.case.write_text('{"week_start":"2026-11-16","utc_offset":"Asia/Singapore"}')
        _, failure = self.stage("baseline", ok=False)
        self.assertIn("固定 UTC 偏移", failure["message"])

    def test_large_finding_set_survives_report_validation(self):
        csv = "project,start,end\n" + "".join(
            f"项目{n},2026-11-16 09:00,2026-11-16 10:00\n" for n in range(300))
        self.entries(csv)
        _, _, links = self.compare()
        review, _ = self.stage("verify", *links)
        result = json.loads(review.read_bytes())["result"]
        self.assertEqual(sum(f["code"] == "overlap" for f in result["findings"]), 44850)
        self.assertEqual(result["included_minutes"], 0)

    def test_help_and_malformed_csv(self):
        help_text = subprocess.check_output([sys.executable, "-B", str(SCRIPT), "--help"], text=True)
        self.assertIn("复核阶段", help_text)
        self.entries('project,start,end\n"未闭合,2026-11-16 09:00,2026-11-16 11:00\n')
        _, failure = self.stage("baseline", ok=False)
        self.assertIn("引号", failure["message"])


if __name__ == "__main__":
    unittest.main()
