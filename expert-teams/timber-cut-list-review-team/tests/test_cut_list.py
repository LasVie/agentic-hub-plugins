"""Boundary and handoff tests for the native cut-list workflow."""
import csv
from itertools import product
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("TIMBER_TEST_PAYLOAD", BASE / BASE.name)).resolve()
SCRIPTS = ROOT / "skills/cut-workflow/scripts"
sys.path.insert(0, str(SCRIPTS))
from audit import audit_cut
from contract import Board, Case, Part, case_from, digest, encoded
from planner import plan_cut


class Workflow(unittest.TestCase):
    def setUp(self):
        local = BASE / ".local"
        local.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=local)
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)
        self.case = self.path / "case.json"
        self.case.write_bytes((BASE / "tests/fixtures/verified-pairing.json").read_bytes())
        self.stock, self.plan, self.review = (self.path / name for name in ("stock.json", "plan.json", "review.json"))
        self.delivery = self.path / "delivery"

    def write(self, path, value):
        path.write_bytes(encoded(value))

    def mutate(self, path, change):
        d = json.loads(path.read_bytes())
        change(d)
        self.write(path, d)

    def invoke(self, stage, output, *extra, expected=0):
        cmd = [sys.executable, "-B", str(SCRIPTS / "cut_list.py"), stage, "--case", str(self.case), "--output", str(output)]
        if stage != "inspect":
            cmd += ["--stock", str(self.stock)]
        if stage in ("verify", "deliver"):
            cmd += ["--plan", str(self.plan)]
        if stage == "deliver":
            cmd += ["--review", str(self.review)]
        result = subprocess.run(cmd + list(extra), check=False, text=True, capture_output=True, cwd=self.path)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["ok"], expected == 0)
        self.assertEqual(value["version"], "1.0.0")
        return value

    def prep(self, *args):
        self.invoke("inspect", self.stock)
        return self.invoke("plan", self.plan, *args)

    def audit(self):
        return self.invoke("verify", self.review)

    def deliver(self):
        self.invoke("deliver", self.delivery)
        return json.loads((self.delivery / "artifact.json").read_bytes())

    def short_stock(self):
        self.case.write_bytes((BASE / "tests/fixtures/one-mm-over.json").read_bytes())

    def test_verified_handoff_dossier(self):
        self.assertEqual(self.prep()["status"], "candidate")
        review = self.audit()
        self.assertEqual(review["verdict"], "verified")
        self.assertEqual(sorted(b["remaining_mm"] for b in review["boards"]), [9, 9])
        manifest = self.deliver()
        self.assertEqual(manifest["status"], "verified")
        self.assertFalse(manifest["human_testing_passed"])
        for name, sha in manifest["files_sha256"].items():
            self.assertEqual(digest((self.delivery / name).read_bytes()), sha)
        for path in (self.case, self.stock, self.plan, self.review):
            self.assertEqual((self.delivery / "inputs" / path.name).read_bytes(), path.read_bytes())
        with (self.delivery / "cuts.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["库存编号"] for row in rows}, {"B1", "B2"})
        self.assertIn("<details open>", (self.delivery / "layout.html").read_text())

    def test_one_mm_shortfall_proof(self):
        self.short_stock()
        self.assertEqual(self.prep()["status"], "no_plan")
        review = self.audit()
        self.assertEqual(review["verdict"], "confirmed_no_plan")
        self.assertEqual(len(review["findings"]), 2)
        self.assertTrue(all("超出 1 毫米" in f["message"] for f in review["findings"]))
        self.deliver()
        self.assertEqual(len((self.delivery / "cuts.csv").read_text().splitlines()), 1)

    def test_injected_candidate_omits_kerf(self):
        self.short_stock()
        self.prep()
        def bogus(plan):
            plan["status"] = "candidate"
            plan["assignments"] = [{"stock_id": board, "pieces": [["Long", idx], ["Short", idx]]}
                                   for idx, board in enumerate(("B1", "B2"), start=1)]
        self.mutate(self.plan, bogus)
        review = self.audit()
        self.assertEqual(review["verdict"], "blocked")
        self.assertEqual({f["code"] for f in review["findings"]}, {"over_capacity"})
        self.deliver()
        self.assertNotIn('href="cuts.csv"', (self.delivery / "layout.html").read_text())

    def test_search_has_an_explicit_limit_result(self):
        self.assertEqual(self.prep("--max-states", "1")["status"], "search_limit")
        self.assertEqual(self.audit()["verdict"], "inconclusive")
        self.assertEqual(self.deliver()["status"], "inconclusive")

    def test_no_plan_claim_rejected_by_counterexample(self):
        self.prep()
        self.mutate(self.plan, lambda d: d.update(status="no_plan", assignments=[]))
        review = self.audit()
        self.assertEqual(review["verdict"], "blocked")
        self.assertEqual(review["findings"][0]["code"], "counterexample")

    def test_exhaustive_budget_distinct_from_no_plan(self):
        board = Board("B", "A", 1, 0, 0)
        boards = tuple(Board("B"+str(i), board.material, board.length, 0, 0) for i in range(10))
        case = Case("bounded", 1, boards, tuple(Part("P", i, "A", 1) for i in range(1, 10)), "case")
        plan = plan_cut(case, b"stock", 50)
        self.assertEqual(plan["status"], "no_plan")
        review = audit_cut(case, b"stock", encoded(plan), plan)
        self.assertEqual(review["findings"][0]["code"], "verification_limit")

    def test_duplicate_and_missing_parts(self):
        self.prep()
        self.mutate(self.plan, lambda d: d["assignments"][1]["pieces"].__setitem__(0, d["assignments"][0]["pieces"][0]))
        self.assertEqual({"missing_piece", "duplicate_piece"},
                         {f["code"] for f in self.audit()["findings"]})

    def test_duplicate_stock(self):
        self.prep()
        self.mutate(self.plan, lambda d: d["assignments"][1].update(stock_id=d["assignments"][0]["stock_id"]))
        self.assertEqual(self.audit()["findings"][0]["code"], "duplicate_stock")

    def test_unknown_piece(self):
        self.prep()
        self.mutate(self.plan, lambda d: d["assignments"][0]["pieces"].__setitem__(0, ["Missing", 1]))
        self.assertIn("unknown_piece", {f["code"] for f in self.audit()["findings"]})

    def test_unknown_stock(self):
        self.prep()
        self.mutate(self.plan, lambda d: d["assignments"][0].update(stock_id="Unknown"))
        self.assertIn("unknown_stock", {f["code"] for f in self.audit()["findings"]})

    def test_material_mismatch(self):
        self.mutate(self.case, lambda d: d["stock"][0].update(material="橡木"))
        self.prep()
        self.mutate(self.plan, lambda d: d.update(status="candidate", assignments=[{"stock_id": "B1", "pieces": [["Long", 1]]}]))
        self.assertIn("material", {f["code"] for f in self.audit()["findings"]})

    def test_unresolved_vs_informational(self):
        self.invoke("inspect", self.stock, "--note", "登记 2 块库存", "--issue", "未确认材质规格")
        value = self.invoke("plan", self.plan, expected=2)
        self.assertIn("待澄清", value["error"])
        self.assertFalse(self.plan.exists())

    def test_stale_case_bytes(self):
        self.prep()
        self.case.write_bytes(self.case.read_bytes() + b"\n")
        self.assertIn("摘要", self.invoke("verify", self.review, expected=2)["error"])

    def test_stale_plan_bytes(self):
        self.prep()
        self.audit()
        self.plan.write_bytes(self.plan.read_bytes() + b"\n")
        self.assertIn("复核记录", self.invoke("deliver", self.delivery, expected=2)["error"])
        self.assertFalse(self.delivery.exists())

    def test_tampered_review(self):
        self.prep()
        self.audit()
        before = self.review.read_bytes()
        self.mutate(self.review, lambda d: d["boards"][0].update(remaining_mm=1000))
        self.assertIn("独立验算", self.invoke("deliver", self.delivery, expected=2)["error"])
        self.assertNotEqual(self.review.read_bytes(), before)

    def test_no_overwrite(self):
        self.prep()
        self.audit()
        self.deliver()
        preserved = (self.delivery / "artifact.json").read_bytes()
        self.invoke("deliver", self.delivery, expected=2)
        self.assertEqual((self.delivery / "artifact.json").read_bytes(), preserved)
        stock = self.stock.read_bytes()
        self.invoke("inspect", self.stock, expected=2)
        self.assertEqual(self.stock.read_bytes(), stock)

    def test_invalid_integer_and_missing_key(self):
        self.mutate(self.case, lambda d: d.update(kerf_mm=True))
        self.assertIn("整数", self.invoke("inspect", self.stock, expected=2)["error"])
        self.mutate(self.case, lambda d: d.pop("kerf_mm"))
        self.assertIn("缺失", self.invoke("inspect", self.stock, expected=2)["error"])

    def test_duplicate_json_and_oversized_file(self):
        self.case.write_bytes(b'{"schema_version":1,"schema_version":1}')
        self.assertIn("重复", self.invoke("inspect", self.stock, expected=2)["error"])
        self.case.write_bytes(b" " * (128 * 1024 + 1))
        self.assertIn("128 KiB", self.invoke("inspect", self.stock, expected=2)["error"])

    def test_symlink_input(self):
        saved = self.case.rename(self.path / "other-case.json")
        self.case.symlink_to(saved)
        self.assertIn("文件", self.invoke("inspect", self.stock, expected=2)["error"])

    def test_html_escapes_labels(self):
        self.mutate(self.case, lambda d: d.update(title="<script>仅是文本</script> ![任意标签](任意目标)"))
        self.prep()
        self.audit()
        self.deliver()
        html = (self.delivery / "layout.html").read_text()
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        markdown = (self.delivery / "review.md").read_text()
        self.assertNotIn("<script>", markdown)
        self.assertIn("\\!\\[任意标签\\]\\(任意目标\\)", markdown)

    def test_matches_independent_small_oracle(self):
        rng = random.Random(20261119)
        for trial in range(48):
            boards = tuple(Board(f"B{i}", rng.choice("ab"), rng.randrange(4, 13), 1, 0) for i in range(3))
            parts = tuple(Part("P", i + 1, rng.choice("ab"), rng.randrange(1, 6)) for i in range(5))
            case = Case(str(trial), rng.randrange(3), boards, parts, str(trial))
            feasible = any(all(
                boards[board].material == part.material for board, part in zip(assignments, parts)
            ) and all(
                sum(part.length + case.kerf for board, part in zip(assignments, parts) if board == index) <= stock.capacity
                for index, stock in enumerate(boards)
            ) for assignments in product(range(3), repeat=len(parts)))
            candidate = plan_cut(case, b"stock", 1000)
            self.assertEqual(candidate["status"], "candidate" if feasible else "no_plan", trial)
            audited = audit_cut(case, b"stock", encoded(candidate), candidate)
            self.assertEqual(audited["verdict"], "verified" if feasible else "confirmed_no_plan", trial)


if __name__ == "__main__":
    unittest.main()
