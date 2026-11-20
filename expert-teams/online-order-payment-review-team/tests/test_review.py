import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = Path(sys.argv.pop(1)) if sys.argv[1:] and not sys.argv[1].startswith("-") else ASSET / ASSET.name
SCRIPT = PAYLOAD / "skills/order-evidence/scripts/review.py"
DATE = "2026-11-20"


class OrderReviewTests(unittest.TestCase):
    def setUp(self):
        scratch = ASSET / ".local/test-runs"
        scratch.mkdir(parents=True, exist_ok=True)
        storage = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(storage.cleanup)
        self.cwd = Path(storage.name)
        self.source = self.cwd / "source"
        shutil.copytree(PAYLOAD / "examples/weekly", self.source)

    def call(self, stage, *args, out=None, success=True):
        source = [] if stage == "match" else ["--source", str(self.source), "--as-of", DATE]
        out = self.cwd / (out or stage)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), stage, *source,
                                 "--out", str(out), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8")
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("已生成", result.stdout)
        else:
            self.assertEqual(result.returncode, 2)
            self.assertIn("核对停止", result.stderr)
        return result

    def append(self, filename, row):
        with (self.source / filename).open("a", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(row)

    def prep(self):
        self.call("baseline")
        self.call("intake")
        self.call("match", "--register", self.cwd / "intake/register.json")
        return ("--baseline", self.cwd / "baseline/baseline.json",
                "--proposal", self.cwd / "match/matches.json")

    def deliver(self):
        args = self.prep()
        self.call("verify", *args)
        self.call("deliver", *args, "--verification", self.cwd / "verify/verification.json")
        output = self.cwd / "deliver"
        with (output / "reconciliation.csv").open(encoding="utf-8-sig", newline="") as stream:
            return {row["标识"]: row for row in csv.DictReader(stream)}

    def test_split_charge_partial_refund_and_ambiguous_twins(self):
        rows = self.deliver()
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows["A100"]["已入账金额"], "120")
        self.assertEqual(rows["A100"]["差额"], "0")
        self.assertIn("原记录金额 120", rows["P001"]["说明"])
        self.assertEqual(rows["P001"]["已入账金额"], "")
        self.assertEqual(rows["R01"]["已入账金额"], "12")
        self.assertEqual(rows["R01"]["差额"], "18")
        self.assertEqual(rows["P005"]["结论"], "扣款候选歧义")
        self.assertEqual(rows["P005"]["订单号或原引用"], "")
        self.assertEqual(rows["P006"]["订单号或原引用"], "A103")
        self.assertIn("payments.csv:7", rows["P006"]["来源"])
        self.assertIn("| CNY | 扣款 | 190 | 145 | 45 |",
                      (self.cwd / "deliver/review.md").read_text())

    def test_refund_notice_is_not_payment_and_cross_currency_credit_is_unallocated(self):
        self.append("refunds.csv", ["R02", "2026-11-19", "A103", "CNY", "5"])
        self.append("payments.csv", ["P007", DATE, "东岸文具", "USD", "退款", "已入账", "5", "A103", "R02"])
        rows = self.deliver()
        self.assertEqual(rows["R02"]["结论"], "未见退款入账")
        self.assertEqual(rows["P007"]["结论"], "退款引用冲突")
        self.assertIn("| USD | 退款 | 5 | 0 | 5 |",
                      (self.cwd / "deliver/review.md").read_text())

    def test_ambiguous_competing_payments_and_explicit_conflicts(self):
        self.append("payments.csv", ["P008", DATE, "东岸文具", "CNY", "扣款", "已入账", "25", "", ""])
        self.append("payments.csv", ["P009", DATE, "其他", "CNY", "扣款", "已入账", "45", "A101", ""])
        rows = self.deliver()
        for key in ("P006", "P008"):
            self.assertEqual(rows[key]["结论"], "扣款候选歧义")
        self.assertEqual(rows["P009"]["结论"], "订单引用冲突")
        self.assertEqual(rows["A103"]["已入账金额"], "0")

    def test_multi_credit_and_overage(self):
        self.append("payments.csv", ["P007", DATE, "春禾杂货", "CNY", "退款", "已入账", "18.125", "", "R01"])
        rows = self.deliver()
        self.assertEqual(rows["R01"]["结论"], "退款入账超额")
        self.assertEqual(rows["R01"]["差额"], "-0.125")

    def test_duplicate_payment_and_future_date_rejected(self):
        path = self.source / "payments.csv"
        saved = path.read_bytes()
        self.append("payments.csv", ["P006", DATE, "东岸文具", "CNY", "扣款", "已入账", "25", "", ""])
        self.assertIn("重复标识", self.call("intake", success=False).stderr)
        path.write_bytes(saved)
        self.append("payments.csv", ["P007", "2026-11-21", "东岸文具", "CNY", "扣款", "已入账", "25", "", ""])
        self.assertIn("晚于", self.call("intake", success=False).stderr)
        self.assertFalse((self.cwd / "intake").exists())

    def test_blind_baseline_rejects_proposal(self):
        result = self.call("baseline", "--proposal", self.cwd / "provided.json", success=False)
        self.assertIn("只接收原始资料", result.stderr)

    def test_tampered_match_and_stale_input_stop_before_output(self):
        args = self.prep()
        path = self.cwd / "match/matches.json"
        saved = path.read_bytes()
        record = json.loads(saved)
        record["流水去向"]["P005"] = ["扣款已关联", "A102", "", []]
        path.write_text(json.dumps(record, ensure_ascii=False))
        self.assertIn("P005", self.call("verify", *args, success=False).stderr)
        path.write_bytes(saved)
        self.append("orders.csv", ["A150", DATE, "新店", "CNY", "3"])
        self.assertIn("基线", self.call("verify", *args, success=False).stderr)
        self.assertFalse((self.cwd / "verify").exists())

    def test_requires_current_verification_preserves_existing_output(self):
        args = self.prep()
        self.assertIn("核验回执", self.call("deliver", *args, success=False).stderr)
        self.call("verify", *args)
        receipt = self.cwd / "verify/verification.json"
        end = (*args, "--verification", receipt)
        self.call("deliver", *end)
        original = (self.cwd / "deliver/audit.json").read_bytes()
        self.assertIn("已存在", self.call("deliver", *end, success=False).stderr)
        self.assertEqual((self.cwd / "deliver/audit.json").read_bytes(), original)

    def test_empty_payments_and_refunds_yield_useful_partial_report(self):
        for name in ("payments.csv", "refunds.csv"):
            path = self.source / name
            path.write_text(path.read_text().splitlines()[0] + "\n")
        rows = self.deliver()
        self.assertEqual(set(rows), {"A100", "A101", "A102", "A103"})
        self.assertEqual(rows["A100"]["结论"], "缺少足额扣款证据")
        self.assertIn("尚无已入账流水", (self.cwd / "deliver/review.md").read_text())

    def test_csv_formula_identifiers_are_escaped(self):
        self.append("orders.csv", ["=123", DATE, "文具", "CNY", "15"])
        rows = self.deliver()
        self.assertEqual(rows["'=123"]["订单号或原引用"], "'=123")

    def test_maximum_ambiguous_batch_and_over_limit(self):
        order_path = self.source / "orders.csv"
        payment_path = self.source / "payments.csv"
        refund_path = self.source / "refunds.csv"
        for path in (order_path, payment_path, refund_path):
            path.write_text(path.read_text().splitlines()[0] + "\n")
        for i in range(100):
            order_id = "𠮷" * 117 + f"{i:03}"
            self.append("orders.csv", [order_id, DATE, "同商户", "CNY", "45"])
            self.append("payments.csv", [f"P{i:03}", DATE, "同商户", "CNY", "扣款", "已入账", "45", "", ""])
        rows = self.deliver()
        self.assertEqual(len(rows), 200)
        self.assertEqual(rows["P099"]["结论"], "扣款候选歧义")
        self.append("payments.csv", ["P100", DATE, "同商户", "CNY", "扣款", "已入账", "45", "", ""])
        self.assertIn("最多 100 项", self.call("intake", out="above-limit", success=False).stderr)

    def test_chinese_help_and_cli_error(self):
        for args, code, phrase in [(["--help"], 0, "核对本地网购"), (["wrong"], 2, "参数无效")]:
            r = subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, code)
            self.assertIn(phrase, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
