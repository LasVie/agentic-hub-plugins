"""Run both delivery outcomes and exercise the exact-package review gates."""
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ASSET = Path(__file__).resolve().parents[1]
PACKAGE = Path(os.environ.get("CAPTION_PACKAGE", ASSET / ASSET.name))
SCRIPTS = PACKAGE / "skills/caption-evidence/scripts"
EXAMPLE = PACKAGE / "examples"
sys.path.insert(0, str(SCRIPTS))
from inputs import Cue, Edit, Scope
from timeline import planner, verifier


class CaptionReviewTests(unittest.TestCase):
    def setUp(self):
        trial = TemporaryDirectory(dir=ASSET / ".local")
        self.addCleanup(trial.cleanup)
        self.work = Path(trial.name)
        self.approved = EXAMPLE / "approved.srt"
        self.revised = EXAMPLE / "revised.srt"
        self.edits = EXAMPLE / "edits.json"

    def stage(self, stage, *, expect=0, out=None, **inputs):
        args = [sys.executable, "-B", str(SCRIPTS / "captions.py"), stage]
        for key, value in inputs.items():
            if value is not None:
                args.extend(["--" + key, str(value)])
        dest = self.work / (out or stage)
        result = subprocess.run(args + ["--out", str(dest)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def save(self, name, value):
        path = self.work / name
        path.write_text(json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value, encoding="utf-8")
        return path

    def read(self, name):
        return json.loads((self.work / name).read_text(encoding="utf-8"))

    def baseline_and_proposal(self):
        self.stage("baseline", approved=self.approved, edits=self.edits)
        self.stage("propose", approved=self.approved, revised=self.revised, edits=self.edits)
        return self.read("propose/proposal.json")

    def verify_args(self):
        return {"approved": self.approved, "revised": self.revised, "edits": self.edits,
                "baseline": self.work / "baseline/baseline.json", "proposal": self.work / "propose/proposal.json"}

    def deliver(self):
        self.stage("verify", **self.verify_args())
        self.stage("deliver", **self.verify_args(), verification=self.work / "verify/verification.json")
        audit = self.read("deliver/audit.json")
        for name, expected in audit["files_sha256"].items():
            self.assertEqual(sha256((self.work / "deliver" / name).read_bytes()).hexdigest(), expected)
        return audit

    def test_weekly_revision_stays_on_playback_list(self):
        plan = self.baseline_and_proposal()
        self.assertEqual(plan["repairs"], {"3": [2500, 3500]})
        self.assertEqual([row["approved"] for row in plan["rows"] if row["kind"] == "removed"], ["1", "4"])
        self.assertEqual([row["approved"] for row in plan["rows"] if row["kind"] == "crosses_edit"], ["3", "6"])
        self.assertTrue(any(row["playback"] == [4000, 5000] for row in plan["rows"]))
        audit = self.deliver()
        self.assertEqual((audit["result"], audit["track_status"], audit["unresolved"]), ("matched", "review_required", 5))
        self.assertFalse((self.work / "deliver/reviewed.srt").exists())
        with (self.work / "deliver/cue-review.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(any(row["旧编号"] == "5" and row["新编号"] == "3" for row in rows))
        baseline = self.read("baseline/baseline.json")
        self.assertNotIn("revised_sha256", baseline["evidence"])

    def test_intro_only_reimports_with_same_text_and_fix(self):
        self.revised = EXAMPLE / "intro-only.srt"
        self.edits = EXAMPLE / "intro-only-edits.json"
        plan = self.baseline_and_proposal()
        self.assertEqual(plan["repairs"], {"1": [0, 1500]})
        audit = self.deliver()
        self.assertEqual(audit["track_status"], "verified_track")
        revised = self.revised.read_text()
        expected = revised.replace("00:00:00,250 --> 00:00:01,750", "00:00:00,000 --> 00:00:01,500")
        self.assertEqual((self.work / "deliver/reviewed.srt").read_text(), expected)

    def test_no_edit_record_does_not_authorize_timing(self):
        self.edits = None
        self.revised = self.approved
        plan = self.baseline_and_proposal()
        self.assertEqual((plan["mode"], plan["status"], plan["repairs"]), ("comparison_only", "review_required", {}))
        self.assertEqual(self.deliver()["result"], "matched")
        self.assertIn("缺少剪辑记录", (self.work / "deliver/review.md").read_text())
        self.assertFalse((self.work / "deliver/reviewed.srt").exists())

    def test_repeated_text_is_not_guessed_and_stale_intro_is_reported(self):
        self.approved = self.save("repeat-before.srt",
            "1\n00:00:00,000 --> 00:00:01,000\n片头\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\n下一步\n\n"
            "3\n00:00:05,000 --> 00:00:06,000\n下一步\n")
        self.revised = self.save("repeat-after.srt",
            "8\n00:00:00,100 --> 00:00:00,300\n片头\n\n"
            "9\n00:00:01,100 --> 00:00:02,100\n下一步\n\n"
            "10\n00:00:02,400 --> 00:00:03,400\n下一步\n")
        self.edits = self.save("cut.json", {"edits": [
            {"start": "00:00:00,000", "end": "00:00:03,000", "new_duration_ms": 0}]})
        plan = self.baseline_and_proposal()
        self.assertEqual(plan["repairs"], {})
        self.assertEqual(sum(row["kind"] == "ambiguous" for row in plan["rows"]), 2)
        self.assertTrue(any(row["kind"] == "deleted_text_present" for row in plan["rows"]))
        self.deliver()

    def test_no_caption_in_new_span_still_requires_playback(self):
        self.approved = self.save("prior.srt",
            "1\n00:00:01,000 --> 00:00:02,000\n在前\n\n2\n00:00:02,000 --> 00:00:03,000\n在后\n")
        self.revised = self.save("after.srt",
            "1\n00:00:01,000 --> 00:00:02,000\n在前\n\n2\n00:00:03,000 --> 00:00:04,000\n在后\n")
        self.edits = self.save("insert.json", {"edits": [
            {"start": "00:00:02,000", "end": "00:00:02,000", "new_duration_ms": 1000}]})
        plan = self.baseline_and_proposal()
        self.assertEqual([r["kind"] for r in plan["rows"]], ["same", "same", "check_new_span"])
        self.assertEqual(plan["rows"][-1]["playback"], [2000, 3000])
        self.assertEqual(self.deliver()["track_status"], "review_required")

    def test_bad_inputs_do_not_create_stage_output(self):
        invalid_edits = [
            {"edits": [{"start": "00:00:02,000", "end": "00:00:02,000", "new_duration_ms": True}]},
            {"edits": [
                {"start": "00:00:02,000", "end": "00:00:04,000", "new_duration_ms": 0},
                {"start": "00:00:03,000", "end": "00:00:05,000", "new_duration_ms": 0}]},
            {"edits": [], "approved_duration": "00:00:12,000", "revised_duration": "00:00:11,000"},
        ]
        for edit in invalid_edits:
            with self.subTest(edit=edit):
                self.stage("baseline", expect=2, approved=self.approved, edits=self.save("bad.json", edit))
        duplicate = self.save("duplicate.srt", self.approved.read_text() + "\n" + self.approved.read_text())
        result = self.stage("baseline", expect=2, approved=duplicate, edits=self.edits)
        self.assertIn("重复字幕编号", result.stderr)
        malformed = self.save("bad.srt", "1\n00:00:12,000 --> 00:00:11,000\n错误。\n")
        result = self.stage("baseline", expect=2, approved=malformed)
        self.assertIn("结束时间须晚于开始时间", result.stderr)
        self.assertFalse((self.work / "baseline").exists())

    def test_wrong_source_or_receipt_cannot_deliver(self):
        plan = self.baseline_and_proposal()
        self.stage("verify", **self.verify_args())
        self.stage("verify", out="stale", expect=2, **{
            **self.verify_args(), "approved": self.save("edited.srt", self.approved.read_text() + "\n")
        })
        plan["rows"].pop()
        err = self.stage("verify", out="tampered", expect=2, **{
            **self.verify_args(), "proposal": self.save("tampered.json", plan)
        })
        self.assertIn("方案与独立核验不一致", err.stderr)
        bad_receipt = self.read("verify/verification.json")
        bad_receipt["unresolved"] = 0
        self.stage("deliver", expect=2, **self.verify_args(), verification=self.save("bogus.json", bad_receipt))
        self.assertFalse((self.work / "deliver").exists())
        self.assertFalse((self.work / "tampered").exists())

    def test_reject_order_overlap_and_clip_duration_on_candidate(self):
        self.edits = self.save("empty.json", {"edits": [], "revised_duration": "00:00:03,000"})
        original = ("1\n00:00:02,000 --> 00:00:04,000\n第二条\n\n"
                    "2\n00:00:01,000 --> 00:00:03,000\n第一条\n")
        self.approved = self.save("before.srt", original)
        self.revised = self.save("after.srt", original)
        plan = self.baseline_and_proposal()
        problems = {row["kind"] for row in plan["rows"]}
        self.assertTrue({"out_of_bounds", "order", "overlap"} <= problems)
        self.assertEqual(self.deliver()["track_status"], "review_required")

    def test_preserves_existing_stage_and_localized_help(self):
        self.stage("baseline", approved=self.approved)
        artifact = self.work / "baseline/baseline.json"
        snapshot = artifact.read_bytes()
        retry = self.stage("baseline", expect=2, approved=self.approved)
        self.assertIn("输出目录已存在", retry.stderr)
        self.assertEqual(artifact.read_bytes(), snapshot)
        help_result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "captions.py"), "verify", "--help"],
                                     capture_output=True, text=True, check=True, timeout=10)
        self.assertIn("独立复核方案", help_result.stdout)
        self.assertIn("改版 SRT 文件", help_result.stdout)

    def test_timeline_calculations_agree_at_boundaries(self):
        cues = [Cue(str(a * 40 + b), 1000 * a, 1000 * b, "字幕")
                for a in range(14) for b in range(a + 1, 15)]
        for edits in ((), (Edit(0, 3000, 0),), (Edit(3000, 3000, 1000),),
                      (Edit(1000, 3000, 0), Edit(3000, 4000, 0)),
                      (Edit(3000, 4000, 1000), Edit(5000, 6000, 3500), Edit(9000, 9000, 600))):
            with self.subTest(edits=edits):
                scope = Scope(edits, None, None)
                self.assertEqual(planner(cues, scope), verifier(cues, scope))


if __name__ == "__main__":
    unittest.main()
