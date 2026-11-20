"""Exercise source or an exact extracted native package via its public CLI."""
import csv
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("TOU_PAYLOAD", ASSET / ASSET.name))
SCRIPT = PAYLOAD / "skills/bill-review/scripts/bill_review.py"
FIXTURE = ASSET / "tests/fixtures/two-hour"


class BillReviewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="tou-review-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.case = self.root / "case"
        shutil.copytree(FIXTURE, self.case)

    def cli(self, stage, dest, options=(), expected=0):
        run = subprocess.run([sys.executable, "-B", str(SCRIPT), stage, "--case", str(self.case),
                              "--output", str(self.root / dest), *options], capture_output=True,
                             text=True, encoding="utf-8", timeout=10)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def saved(self, name):
        return json.loads((self.root / name).read_bytes())

    def write(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def change(self, file, callback):
        path = self.case / file
        data = json.loads(path.read_bytes())
        callback(data)
        self.write(path, data)

    def prepare(self):
        self.cli("inspect", "meter.json")
        self.cli("replay", "independent.json")
        self.assertFalse((self.root / "candidate.json").exists())
        self.cli("calculate", "candidate.json", ("--meter", str(self.root / "meter.json")))

    def deliver(self, dest="delivery", expected=0):
        flags = ("--meter", str(self.root / "meter.json"), "--candidate", str(self.root / "candidate.json"),
                 "--independent", str(self.root / "independent.json"))
        return self.cli("deliver", dest, flags, expected)

    def assert_block(self, keyword):
        report = self.cli("inspect", "meter.json", expected=2)
        self.assertIn(keyword, report["message"])
        self.assertFalse((self.root / "meter.json").exists())

    def drop_last(self):
        path = self.case / "readings.csv"
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    def test_exact_positive_dossier_and_chinese_outputs(self):
        self.prepare()
        self.assertEqual(self.deliver()["status"], "verified")
        result = self.saved("delivery/evaluation.json")
        self.assertEqual((result["billed_minor"], result["computed_minor"], result["difference_minor"]), (100, 80, 20))
        self.assertFalse(result["human_testing_passed"])
        with (self.root / "delivery/intervals.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["分段"] for row in rows], ["off_peak", "peak", "peak", "off_peak"])
        self.assertEqual([row["原始CSV行"] for row in rows], ["2", "3", "4", "5"])
        self.assertEqual([row["电量kWh"] for row in rows], ["1"] * 4)
        html = (self.root / "delivery/review.html").read_text()
        for literal in ("账单 1.00", "复算 0.80", "差额 0.20", "电量费用已独立复核"):
            self.assertIn(literal, html)
        manifest = self.saved("delivery/artifact.json")
        self.assertEqual(len(manifest["files_sha256"]), 9)
        for path, digest in manifest["files_sha256"].items():
            self.assertEqual(sha256((self.root / "delivery" / path).read_bytes()).hexdigest(), digest)
        for source in self.case.iterdir():
            self.assertEqual(source.read_bytes(), (self.root / "delivery/inputs" / source.name).read_bytes())

    def test_internally_consistent_bad_candidate_is_blocked(self):
        self.prepare()
        original = (self.root / "independent.json").read_bytes()
        candidate = self.saved("candidate.json")
        candidate["result"] = {
            "interval_bands": ["off_peak", "peak", "peak", "peak"],
            "energy_micro_kwh": {"off_peak": 1_000_000, "peak": 3_000_000},
            "amount_minor": {"off_peak": 10, "peak": 90},
        }
        self.write(self.root / "candidate.json", candidate)
        self.assertEqual(self.deliver()["status"], "blocked")
        dossier = self.saved("delivery/evaluation.json")
        self.assertNotIn("computed_minor", dossier)
        self.assertEqual(dossier["lines"], [])
        self.assertEqual(len((self.root / "delivery/intervals.csv").read_text().splitlines()), 1)
        self.assertIn("待澄清", (self.root / "delivery/review.html").read_text())
        self.assertEqual((self.root / "independent.json").read_bytes(), original)

    def test_missing_reading(self):
        self.drop_last()
        self.assert_block("缺少读数")

    def test_duplicate_reading(self):
        path = self.case / "readings.csv"
        with path.open("a") as stream:
            stream.write("2026-11-20T18:00,1,kWh\n")
        self.assert_block("读数重复")

    def test_unknown_unit_and_sub_wh_precision(self):
        path = self.case / "readings.csv"
        source = path.read_text()
        path.write_text(source.replace("1000,Wh", "1000,kW"))
        self.assert_block("读数单位")
        path.write_text(source.replace("1000,Wh", "1000.0001,Wh"))
        self.assert_block("十进制定点")

    def test_ambiguous_missing_and_unaligned_tariffs(self):
        for start, message in [("17:30", "缺口"), ("16:30", "重叠"), ("17:15", "边界")]:
            shutil.copyfile(FIXTURE / "tariff.json", self.case / "tariff.json")
            self.change("tariff.json", lambda d: d["windows"][1].update(start=start))
            self.assert_block(message)

    def test_unknown_offset(self):
        self.change("tariff.json", lambda d: d.update(utc_offset="-00:00"))
        self.assert_block("固定 UTC 偏移")

    def test_currency_and_missing_bill_band(self):
        self.change("bill.json", lambda d: d.update(currency="USD"))
        self.assert_block("币种")
        self.change("bill.json", lambda d: (d.update(currency="CNY"), d["lines"].pop("peak")))
        self.assert_block("逐项列出")

    def test_stale_evidence_with_same_arithmetic(self):
        self.prepare()
        path = self.case / "bill.json"
        with path.open("ab") as stream:
            stream.write(b"\n")
        report = self.deliver(expected=2)
        self.assertIn("当前原始文件不一致", report["message"])
        self.assertFalse((self.root / "delivery").exists())

    def test_review_alone_rejects_candidate_parameter(self):
        bad = self.cli("replay", "independent.json", ("--candidate", str(self.root / "candidate.json")), expected=2)
        self.assertIn("交接报告参数", bad["message"])

    def test_tampered_independent_evidence(self):
        self.prepare()
        path = self.root / "independent.json"
        report = json.loads(path.read_bytes())
        report["result"]["amount_minor"]["peak"] = 0
        self.write(path, report)
        self.assertIn("独立复算报告", self.deliver(expected=2)["message"])

    def test_existing_dossier_preserved(self):
        self.prepare()
        self.deliver()
        before = (self.root / "delivery/artifact.json").read_bytes()
        self.assertIn("输出路径已存在", self.deliver(expected=2)["message"])
        self.assertEqual((self.root / "delivery/artifact.json").read_bytes(), before)

    def test_round_half_up_and_even_per_band(self):
        for mode, amount in (("half_up", 1), ("half_even", 0)):
            with self.subTest(rounding=mode):
                self.change("tariff.json", lambda d: (d.update(rounding=mode), d["rates"].update(peak="0.0025")))
                self.cli("replay", mode + ".json")
                self.assertEqual(self.saved(mode + ".json")["result"]["amount_minor"]["peak"], amount)
        self.prepare()
        self.assertEqual(self.deliver()["status"], "verified")

    def test_exact_with_large_values_and_rates(self):
        path = self.case / "readings.csv"
        path.write_text(path.read_text().replace("1.000000,kWh", "999999999.999999,kWh"))
        self.change("tariff.json", lambda d: d["rates"].update(peak="999999999.999999"))
        self.prepare()
        self.assertEqual(self.deliver()["status"], "verified")
        with localcontext() as ctx:
            ctx.prec = 40
            exact = (Decimal("1000000000.999999") * Decimal("999999999.999999")).quantize(
                Decimal("0.01"), rounding="ROUND_HALF_UP"
            )
        self.assertEqual(self.saved("candidate.json")["result"]["amount_minor"]["peak"], int(exact * 100))

    def test_hourly_window_spanning_midnight(self):
        self.change("tariff.json", lambda d: d.update(interval_minutes=60))
        self.change("bill.json", lambda d: d.update(start="2026-11-20T23:00", end="2026-11-21T01:00"))
        (self.case / "readings.csv").write_text("start,energy,unit\n2026-11-21T00:00,2,kWh\n2026-11-20T23:00,1,kWh\n")
        self.prepare()
        self.assertEqual(self.deliver()["status"], "verified")
        self.assertEqual(self.saved("candidate.json")["result"]["energy_micro_kwh"]["off_peak"], 3_000_000)

    def test_duplicate_json_key_and_symlink(self):
        path = self.case / "bill.json"
        path.write_bytes(b'{"start":"a","start":"b"}')
        self.assert_block("重复字段")
        path.unlink()
        path.symlink_to(FIXTURE / "bill.json")
        self.assert_block("符号链接")


if __name__ == "__main__":
    unittest.main(verbosity=2)
