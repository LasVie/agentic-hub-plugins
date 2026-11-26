"""Verify the CLI workflow and its stop conditions against the extracted payload."""
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ASSET = Path(__file__).resolve().parents[1]
PACKAGE = Path(os.environ.get("RESTOCK_PACKAGE", ASSET / ASSET.name))
SCRIPT = PACKAGE / "skills/restock-evidence/scripts/restock.py"
SOURCE = PACKAGE / "examples/weekly-restock.json"


class RestockTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(dir=ASSET / ".local")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.data = json.loads(SOURCE.read_text(encoding="utf-8"))

    def run_stage(self, name, *, out=None, success=True, **options):
        command = [sys.executable, "-B", str(SCRIPT), name]
        for key, value in options.items():
            command.extend(["--" + key, str(value)])
        result = subprocess.run(command + ["--out", str(out or self.work / name)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0 if success else 2, result.stderr)
        return result.stderr if not success else result.stdout

    def read(self, relative):
        return json.loads((self.work / relative).read_text(encoding="utf-8"))

    def write(self, name, data):
        file = self.work / name
        file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return file

    def proposal(self, source):
        self.run_stage("intake", source=source)
        self.run_stage("baseline", source=source)
        self.run_stage("plan", intake=self.work / "intake/intake.json")
        return self.read("plan/proposal.json")

    def check_options(self, source=SOURCE):
        return {"source": source, "baseline": self.work / "baseline/baseline.json",
                "proposal": self.work / "plan/proposal.json"}

    def test_complete_weekly_case(self):
        proposal = self.proposal(SOURCE)
        liners, paper, bags, tablets = proposal["items"]
        self.assertEqual(liners["first_shortage"], "2026-11-27")
        self.assertEqual(liners["purchase"], {"total": 10000, "count": 1, "size": 10000})
        self.assertEqual(paper["first_shortage"], "2026-11-25")
        self.assertEqual(paper["shortfall"], 2000)
        self.assertEqual(paper["purchase"], {"total": 2000, "count": 1, "size": 2000})
        self.assertEqual(bags["reason"], "missing_pack")
        self.assertEqual(bags["shortfall"], 1400)
        self.assertEqual(tablets["status"], "wait")
        self.assertIn("待定", tablets["notes"][0])
        self.run_stage("verify", **self.check_options())
        self.run_stage("deliver", **self.check_options(), verification=self.work / "verify/verification.json")
        audit = self.read("deliver/audit.json")
        self.assertEqual((audit["status"], audit["matched_items"], audit["issues"]), ("matched", 4, []))
        for name, digest in audit["files_sha256"].items():
            self.assertEqual(hashlib.sha256((self.work / "deliver" / name).read_bytes()).hexdigest(), digest)
        with (self.work / "deliver/restock.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[1]["建议合计"], "2")
        text = (self.work / "deliver/shopping-list.md").read_text(encoding="utf-8")
        self.assertIn("买 1 包，每包 2 卷", text)
        self.assertIn("待确认", text)

    def test_same_day_supply_and_next_shop_boundary(self):
        self.data["items"][0].update(stock=[], arrivals=[
            {"date": "2026-11-22", "qty": 99, "status": "confirmed"},
            {"date": "2026-11-23", "qty": 1, "status": "confirmed"},
            {"date": "2026-11-24", "qty": 30, "status": "pending"},
            {"date": "2026-11-30", "qty": 1, "status": "confirmed"},
        ])
        source = self.write("dates.json", self.data)
        row = self.proposal(source)["items"][0]
        self.assertEqual((row["first_shortage"], row["shortfall"]), ("2026-11-24", 6000))
        self.run_stage("verify", **self.check_options(source))

    def test_uncertainty_and_pack_constraints(self):
        self.data["items"][0]["daily_use"] = None
        self.data["items"][1]["packs"] = [{"qty": 6}]
        self.data["items"][2]["stock"] = [{"qty": 3}]
        self.data["items"][3]["capacity"] = 6
        source = self.write("changes.json", self.data)
        rows = self.proposal(source)["items"]
        self.assertEqual([row["reason"] for row in rows],
                         ["missing_use", "pack_capacity", "uncertain_stock", "existing_capacity"])
        self.assertTrue(all(row["purchase"] is None and row["status"] == "check" for row in rows))
        self.run_stage("verify", **self.check_options(source))

    def test_exact_fit_and_fewer_packages_breaks_tie(self):
        self.data["items"][2]["packs"] = [{"qty": "0.7", "variant": "V12"}, {"qty": "1.4", "variant": "V12"}]
        self.data["items"][2]["capacity"] = "1.4"
        source = self.write("tie.json", self.data)
        row = self.proposal(source)["items"][2]
        self.assertEqual(row["purchase"], {"total": 1400, "count": 1, "size": 1400})
        self.run_stage("verify", **self.check_options(source))

    def test_invalid_inputs_do_not_create_intake(self):
        cases = [("daily_use", True), ("daily_use", "1.2345"), ("stock", [{"qty": -1}]),
                 ("arrivals", [{"date": "2026-02-30", "qty": 1, "status": "confirmed"}]),
                 ("packs", [{"qty": 0}]), ("unit", "")]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(self.data)
                data["items"][0][key] = value
                error = self.run_stage("intake", source=self.write("invalid.json", data), success=False)
                self.assertIn("处理失败", error)
        self.data["items"].append(self.data["items"][0])
        error = self.run_stage("intake", source=self.write("duplicate.json", self.data), success=False)
        self.assertIn("出现多次", error)
        self.assertFalse((self.work / "intake").exists())

    def test_stale_and_altered_evidence_blocks_delivery(self):
        proposal = self.proposal(SOURCE)
        self.run_stage("verify", **self.check_options())
        options = self.check_options()
        changed = copy.deepcopy(proposal)
        changed["items"][1]["purchase"]["count"] = True
        options["proposal"] = self.write("altered.json", changed)
        error = self.run_stage("verify", success=False, out=self.work / "wrong", **options)
        self.assertIn("卷纸", error)
        self.assertFalse((self.work / "wrong").exists())
        stale = self.write("equivalent-source.json", self.data)
        error = self.run_stage("deliver", success=False, **self.check_options(stale),
                               verification=self.work / "verify/verification.json")
        self.assertIn("基线", error)
        self.assertFalse((self.work / "deliver").exists())
        receipt = self.read("verify/verification.json")
        receipt["matched_items"] = 1
        error = self.run_stage("deliver", success=False, **self.check_options(),
                               verification=self.write("fake.json", receipt))
        self.assertIn("核验回执", error)
        self.assertFalse((self.work / "deliver").exists())

    def test_existing_output_is_preserved(self):
        self.run_stage("intake", source=SOURCE)
        receipt = self.work / "intake/intake.json"
        snapshot = receipt.read_bytes()
        self.assertIn("已存在", self.run_stage("intake", source=SOURCE, success=False))
        self.assertEqual(receipt.read_bytes(), snapshot)

    def test_chinese_help_and_missing_argument(self):
        help_result = subprocess.run([sys.executable, "-B", str(SCRIPT), "verify", "--help"],
                                     capture_output=True, text=True, check=True, timeout=10)
        self.assertIn("复核补货方案", help_result.stdout)
        self.assertIn("独立基线路径", help_result.stdout)
        self.assertIn("参数错误", self.run_stage("verify", success=False))


if __name__ == "__main__":
    unittest.main()
