import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = Path(sys.argv.pop(1)) if sys.argv[1:] and not sys.argv[1].startswith("-") else ASSET / ASSET.name
SCRIPT = PAYLOAD / "skills/notice-evidence/scripts/review.py"


class NoticeReviewTest(unittest.TestCase):
    def setUp(self):
        local = ASSET / ".local/test-runs"
        local.mkdir(parents=True, exist_ok=True)
        storage = tempfile.TemporaryDirectory(dir=local)
        self.addCleanup(storage.cleanup)
        self.cwd = Path(storage.name)
        self.source = json.loads((PAYLOAD / "examples/weekly-notices.json").read_text())
        self.rows = json.loads((ASSET / "tests/fixtures/weekly-extraction.json").read_text())

    def write(self, name, content):
        out = self.cwd / name
        out.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        return out

    def run_cli(self, stage, *args, destination=None, ok=True):
        source = self.write("source.json", self.source)
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), stage, "--source", str(source),
             "--out", str(self.cwd / (destination or stage)), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        if not ok:
            self.assertIn("核对停止", result.stderr)
        return result

    def seal(self, baseline=None):
        reviewer = self.write("reviewer-input.json", self.rows if baseline is None else baseline)
        analyst = self.write("analyst-input.json", self.rows)
        self.run_cli("baseline", "--extraction", reviewer)
        self.run_cli("draft", "--extraction", analyst)
        return ("--baseline", self.cwd / "baseline/baseline.json", "--draft", self.cwd / "draft/draft.json")

    def deliver(self, baseline=None):
        args = self.seal(baseline)
        self.run_cli("verify", *args)
        args += ("--receipt", self.cwd / "verify/verification.json")
        self.run_cli("deliver", *args)
        out = self.cwd / "deliver"
        return json.loads((out / "audit.json").read_text()), args

    def assert_pickup(self, receipt, a, b):
        found = {(v["child"], v["time"]) for v in receipt["actions"] if v["ref"].split(":")[0] in {"N2", "N3", "N9"}}
        self.assertEqual(found, {(key, val) for key, val in (("A", a), ("B", b)) if val})

    def test_weekly_changes_audience_and_missing_date(self):
        receipt, _ = self.deliver()
        self.assertEqual(receipt["notice_count"], 8)
        self.assertEqual(len(receipt["actions"]), 4)
        self.assertEqual(receipt["agreed_observations"], 8)
        self.assertEqual(receipt["disputed_observations"], 0)
        self.assert_pickup(receipt, "17:00", "16:30")
        self.assertEqual({v["ref"] for v in receipt["pending"]}, {"N6:1:1"})
        self.assertEqual({v["op"] for v in receipt["changes"]}, {"更正", "取消"})
        self.assertEqual(sorted(v["ref"] for v in receipt["actions"]), ["N1:1:1", "N1:2:1", "N2:1:1", "N3:1:1"])
        self.assertIn("2026-11-26 17:00", (self.cwd / "deliver/checklist.md").read_text())
        self.assertIn("照护人甲", (self.cwd / "deliver/checklist.md").read_text())
        with (self.cwd / "deliver/changes.csv").open(encoding="utf-8-sig", newline="") as f:
            changes = list(csv.DictReader(f))
        self.assertEqual(changes[0]["旧时刻"], "16:30")
        self.assertEqual(changes[0]["新时刻"], "17:00")

    def test_disputed_correction_leaves_other_class_usable(self):
        baseline = json.loads(json.dumps(self.rows))
        baseline["N3"] = []
        receipt, _ = self.deliver(baseline)
        self.assertEqual(receipt["disputed_observations"], 1)
        self.assert_pickup(receipt, None, "16:30")
        self.assertIn("N3:1:1", {r["ref"] for r in receipt["pending"]})

    def test_unknown_scope_blocks_previous_without_guessing_class(self):
        self.source["notices"]["N3"]["scope"] = None
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, None)
        self.assertTrue(any("适用对象" in p["reason"] for p in receipt["pending"]))

    def test_same_day_only_date_does_not_override(self):
        self.source["notices"]["N3"]["sent"] = "2026-11-23"
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, "16:30")
        self.assertTrue(any("发布先后" in p["reason"] for p in receipt["pending"]))

    def test_same_day_order_known_does_override(self):
        self.source["notices"]["N3"]["sent"] = "2026-11-23T09:01"
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, "17:00", "16:30")

    def test_competing_edits_on_same_parent_do_not_choose_a_winner(self):
        self.source["notices"]["N9"] = dict(self.source["notices"]["N3"], sent="2026-11-25")
        self.rows["N9"] = [dict(self.rows["N3"][0])]
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, "16:30")
        self.assertTrue(any("多份更正" in p["reason"] for p in receipt["pending"]))

    def test_missing_link_flags_potential_stale_item(self):
        self.rows["N3"][0]["previous"] = None
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, "16:30")
        self.assertTrue(any("此前有效" in p["reason"] for p in receipt["pending"]))

    def test_baseline_rejects_draft_input_and_incomplete_notice_coverage(self):
        path = self.write("evidence.json", self.rows)
        error = self.run_cli("baseline", "--extraction", path, "--draft", path, ok=False)
        self.assertIn("仅接收", error.stderr)
        del self.rows["N8"]
        error = self.run_cli("baseline", "--extraction", self.write("incomplete.json", self.rows), ok=False)
        self.assertIn("逐份覆盖通知", error.stderr)
        self.assertFalse((self.cwd / "baseline").exists())

    def test_substring_must_not_change_time(self):
        self.rows["N2"][0]["clock"] = "6:30"
        error = self.run_cli("draft", "--extraction", self.write("bad.json", self.rows), ok=False)
        self.assertIn("时间信息须取自原文", error.stderr)

    def test_half_hour_cannot_be_shortened_but_full_phrase_is_supported(self):
        notice = self.source["notices"]["N3"]
        notice["text"] = notice["text"].replace("下午5点", "下午5点一起")
        self.rows["N3"][0]["quote"] = notice["text"]
        self.run_cli("draft", "--extraction", self.write("hour.json", self.rows), destination="whole-hour")
        notice["text"] = notice["text"].replace("下午5点一起", "下午5点半")
        self.rows["N3"][0]["quote"] = notice["text"]
        short = self.write("truncated-time.json", self.rows)
        result = self.run_cli("draft", "--extraction", short, destination="shorten", ok=False)
        self.assertIn("时间信息须取自原文", result.stderr)
        self.rows["N3"][0]["clock"] = "下午5点半"
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, "17:30", "16:30")

    def test_unclear_twelve_hour_phrase_stays_pending(self):
        notice = self.source["notices"]["N3"]
        notice["text"] = notice["text"].replace("下午5点", "晚上12点")
        self.rows["N3"][0]["quote"] = notice["text"]
        self.rows["N3"][0]["clock"] = "晚上12点"
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, "16:30")
        self.assertIn("N3:1:1", {r["ref"] for r in receipt["pending"]})

    def test_fake_quote_stops_sealing(self):
        self.rows["N1"][0]["quote"] = "这段通知没有写"
        error = self.run_cli("draft", "--extraction", self.write("bad.json", self.rows), ok=False)
        self.assertIn("摘录须在原文", error.stderr)

    def test_earlier_or_different_issuer_cannot_replace(self):
        self.source["notices"]["N3"]["issuer"] = "来源未核实的转发"
        receipt, _ = self.deliver()
        self.assert_pickup(receipt, None, "16:30")
        self.assertTrue(any("发文方不同" in p["reason"] for p in receipt["pending"]))

    def test_raw_source_changes_invalidate_baseline(self):
        args = self.seal()
        self.source["notices"]["N8"]["text"] += " 后续以原文为准。"
        error = self.run_cli("verify", *args, ok=False)
        self.assertIn("回执已改动或与当前通知不符", error.stderr)
        self.assertFalse((self.cwd / "verify").exists())

    def test_forged_receipt_fails_and_existing_output_is_preserved(self):
        receipt, args = self.deliver()
        path = self.cwd / "deliver/audit.json"
        before = path.read_bytes()
        result = self.run_cli("deliver", *args, ok=False)
        self.assertIn("已存在", result.stderr)
        self.assertEqual(path.read_bytes(), before)
        receipt["actions"] = []
        self.write("verify/verification.json", receipt)
        result = self.run_cli("deliver", *args, destination="copy", ok=False)
        self.assertIn("有效核验回执", result.stderr)
        self.assertFalse((self.cwd / "copy").exists())

    def test_chinese_help(self):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"],
                           text=True, capture_output=True, check=True)
        self.assertIn("核对本地学校通知", r.stdout)
        self.assertIn("选项：", r.stdout)


if __name__ == "__main__":
    unittest.main()
