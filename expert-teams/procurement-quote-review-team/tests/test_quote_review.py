"""Business, evidence and output regressions using original synthetic inputs.

The role reports constructed here are test fixtures. They do not demonstrate
independent model reasoning or runtime member participation.
"""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ASSET = HERE.parent
SCRIPT = ASSET / "procurement-quote-review-team/skills/quote-evaluation/scripts/quote_review.py"
FIXTURES = HERE / "fixtures"
ADAPTED_REPORTS = FIXTURES / "member-reports-v2"


def load_module():
    spec = importlib.util.spec_from_file_location("procurement_quote_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def synthetic_reports(case, case_hash):
    """Known fixture judgments and arithmetic; never described as live evidence."""
    assessments = []
    totals = []
    known = {"A": "5800", "B": "4400", "C": "1700"}
    for offer in case["offers"]:
        key = offer["source_ids"][0]
        text = (FIXTURES / {"a": "报价甲.md", "b": "报价乙.md", "c": "报价丙.md"}[key]).read_text(encoding="utf-8").splitlines()
        for criterion in case["criteria"]:
            mandatory = criterion["mandatory"]
            status = "fail" if mandatory and offer["id"] == "C" else "pass"
            if not mandatory and offer["id"] == "C":
                status = "unknown"
            assessments.append({
                "offer_id": offer["id"], "criterion_id": criterion["id"],
                "status": status, "score": None if mandatory or status == "unknown" else "4",
                "evidence": [{"source_id": key, "line": 2 if mandatory else 5, "quote": text[1 if mandatory else 4]}],
                "rationale": "合成夹具：逐字核对交货天数；丙质量保留人工运行中的未知，不补写基础档位证据。",
            })
        complete = all(cost.get(field) is not None for cost in offer["costs"]
                       for field in ("amount", "quantity", "occurrences"))
        total = known[offer["id"]] if complete and offer.get("currency") == case.get("currency") and case.get("currency") else None
        totals.append({"offer_id": offer["id"], "total": total})
    common = {"schema_version": 2, "case_sha256": case_hash}
    return (
        {**common, "role": "technical", "notes": [], "issues": [], "assessments": assessments},
        {**common, "role": "commercial", "notes": [], "issues": [], "totals": totals},
        {**common, "role": "verifier", "notes": [], "issues": [], "assessments": copy.deepcopy(assessments), "totals": copy.deepcopy(totals)},
    )


class QuoteReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="procurement-unit-")
        # macOS exposes its temporary directory through /var -> /private/var;
        # use the canonical parent so production's no-symlink rule is exercised.
        self.root = Path(self.temp.name).resolve()
        self.case_dir = self.root / "输入"
        shutil.copytree(FIXTURES, self.case_dir)
        self.case_path = self.case_dir / "case.json"
        self.case = json.loads(self.case_path.read_text(encoding="utf-8"))

    def tearDown(self):
        self.temp.cleanup()

    def save_case(self):
        write_json(self.case_path, self.case)

    def reports(self):
        self.save_case()
        inspection = self.module.inspect_case(self.case_path)
        reports = synthetic_reports(self.case, inspection["case_sha256"])
        paths = []
        for filename, report in zip(("technical.json", "commercial.json", "review.json"), reports):
            paths.append(write_json(self.root / filename, report))
        return paths, reports

    def evaluate(self, paths):
        return self.module.evaluate(self.case_path, *paths)

    def save_reports(self, paths, reports):
        for path, report in zip(paths, reports):
            write_json(path, report)

    @staticmethod
    def assessment(report, offer, criterion):
        return next(row for row in report["assessments"]
                    if row["offer_id"] == offer and row["criterion_id"] == criterion)

    def assert_reviewed_b_then_a(self, result):
        self.assertEqual(result["status"], "reviewed")
        self.assertEqual([row["offer_id"] for row in result["rankings"]], ["B", "A"])
        self.assertFalse(result["clarifications"])
        self.assertFalse(result["conflicts"])

    def eligibility(self, result, offer):
        return next(row for row in result["eligibility"] if row["offer_id"] == offer)

    def assert_rejected(self, function, *args):
        with self.assertRaises(self.module.QuoteError):
            function(*args)

    def test_exact_lifecycle_costs_and_price_reversal(self):
        inspection = self.module.inspect_case(self.case_path)
        self.assertEqual(inspection["version"], "1.0.1")
        totals = {row["offer_id"]: row["total"] for row in inspection["costs"]}
        self.assertEqual({k: float(v) for k, v in totals.items()}, {"A": 5800, "B": 4400, "C": 1700})
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "reviewed")
        self.assertEqual([r["offer_id"] for r in result["rankings"]], ["B", "A"])
        self.assertNotIn("C", [r["offer_id"] for r in result["rankings"]])

    def test_excluded_offer_unknown_quality_is_preserved_without_blocking(self):
        paths, reports = self.reports()
        self.assertEqual(self.assessment(reports[0], "C", "quality")["status"], "unknown")
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        self.assertEqual(self.eligibility(result, "C")["status"], "excluded")
        self.assertIn("delivery", self.eligibility(result, "C")["exclusion_criteria"])
        self.assertTrue(self.eligibility(result, "C")["reasons"])
        unknowns = [issue for issue in result["issues"]
                    if issue.get("offer_id") == "C" and issue["kind"] == "unknown"]
        self.assertTrue(unknowns)
        self.assertTrue(all(not issue["blocking"] for issue in unknowns))
        self.assertTrue(result["warnings"])

    def test_informational_notes_survive_delivery_without_becoming_blockers(self):
        paths, reports = self.reports()
        note = "已核对三份成本一致；不验证供应商真实性。"
        reports[2]["notes"] = [note]
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        self.assertTrue(any(note in value for value in result["notes"]))
        self.assertNotIn(note, result["notes"], "汇总信息必须保留来源角色前缀")
        output = self.root / "有信息记录的交付"
        self.module.deliver(self.case_path, *paths, output)
        for filename in ("comparison.html", "review.md", "evaluation.json"):
            self.assertIn(note, (output / filename).read_text(encoding="utf-8"))

    def test_global_issue_blocks_even_when_only_c_is_excluded(self):
        paths, reports = self.reports()
        reports[2]["issues"] = [{"scope": "global", "category": "evaluation", "message": "所有报价的税费口径未确定。"}]
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(any(issue["scope"] == "global" and issue["blocking"] for issue in result["issues"]))

    def test_eligible_offer_evaluation_issue_blocks_ranking(self):
        paths, reports = self.reports()
        reports[0]["issues"] = [{"scope": "offer", "offer_id": "A", "category": "evaluation", "message": "甲的费用口径待确认。"}]
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(any(issue.get("offer_id") == "A" and issue["blocking"] for issue in result["issues"]))

    def test_excluded_offer_evaluation_issue_remains_a_warning(self):
        paths, reports = self.reports()
        marker = "丙质量基础证据不足，保留未知。"
        reports[0]["issues"] = [{"scope": "offer", "offer_id": "C", "category": "evaluation", "message": marker}]
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        issues = [issue for issue in result["issues"] if issue["message"] == marker]
        self.assertEqual(len(issues), 1)
        self.assertFalse(issues[0]["blocking"])
        self.assertTrue(any(marker in value for value in result["warnings"]))
        output = self.root / "保留非阻断问题的交付"
        self.module.deliver(self.case_path, *paths, output)
        for filename in ("comparison.html", "review.md", "evaluation.json"):
            self.assertIn(marker, (output / filename).read_text(encoding="utf-8"))
        compliance = (output / "compliance.csv").read_text(encoding="utf-8-sig")
        self.assertIn(marker, compliance)
        self.assertIn("非阻断警示", compliance)
        self.assertIn("已排除", compliance)
        self.assertIn("已排除", (output / "costs.csv").read_text(encoding="utf-8-sig"))

    def test_excluded_offer_eligibility_issue_is_not_downgraded(self):
        paths, reports = self.reports()
        reports[2]["issues"] = [{"scope": "offer", "offer_id": "C", "category": "eligibility", "message": "丙所报交货期适用范围不明确。"}]
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertEqual(self.eligibility(result, "C")["status"], "uncertain")
        self.assertTrue(any(issue.get("offer_id") == "C" and issue["category"] == "eligibility" and issue["blocking"]
                            for issue in result["issues"]))

    def test_unilateral_mandatory_failure_cannot_establish_exclusion(self):
        for other_status in ("pass", "unknown"):
            with self.subTest(other_status=other_status):
                paths, reports = self.reports()
                self.assessment(reports[2], "C", "delivery")["status"] = other_status
                self.save_reports(paths, reports)
                result = self.evaluate(paths)
                self.assertEqual(result["status"], "clarification_required")
                self.assertEqual(result["rankings"], [])
                self.assertEqual(self.eligibility(result, "C")["status"], "uncertain")
                self.assertTrue(result["conflicts"])

    def test_other_mandatory_unknown_still_blocks_after_agreed_failure(self):
        self.case["criteria"].append({"id": "warranty", "text": "保修须有明确承诺", "mandatory": True,
                                      "weight": "0", "max_score": "1"})
        paths, reports = self.reports()
        for report in (reports[0], reports[2]):
            self.assessment(report, "C", "warranty").update(status="unknown", evidence=[], rationale="适用范围待澄清。")
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(self.eligibility(result, "C")["status"], "uncertain")
        self.assertEqual(result["rankings"], [])

    def test_other_mandatory_conflict_still_blocks_after_agreed_failure(self):
        self.case["criteria"].append({"id": "warranty", "text": "保修须有明确承诺", "mandatory": True,
                                      "weight": "0", "max_score": "1"})
        paths, reports = self.reports()
        self.assessment(reports[0], "C", "warranty")["status"] = "pass"
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(self.eligibility(result, "C")["status"], "uncertain")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(any(issue.get("criterion_id") == "warranty" and issue["kind"] == "conflict" and issue["blocking"]
                            for issue in result["issues"]))

    def test_eligible_offer_unknown_quality_remains_a_real_blocker(self):
        paths, reports = self.reports()
        for report in (reports[0], reports[2]):
            self.assessment(report, "B", "quality").update(status="unknown", score=None, evidence=[],
                                                            rationale="乙评分所需的材料尚未证实。")
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(any(issue.get("offer_id") == "B" and issue["kind"] == "unknown" and issue["blocking"]
                            for issue in result["issues"]))

    def test_excluded_nonmandatory_disagreement_is_retained_not_blocking(self):
        paths, reports = self.reports()
        self.assessment(reports[2], "C", "quality").update(status="pass", score="5")
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        disagreements = [issue for issue in result["issues"] if issue.get("offer_id") == "C" and issue["kind"] == "conflict"]
        self.assertTrue(disagreements)
        self.assertTrue(all(not issue["blocking"] for issue in disagreements))
        self.assertTrue(result["warnings"])

    def test_excluded_offer_missing_currency_does_not_convert_null_to_decimal(self):
        self.case["offers"][2]["currency"] = None
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        self.assertIsNone(next(row for row in result["costs"] if row["offer_id"] == "C")["total"])
        self.assertTrue(any(issue.get("offer_id") == "C" and not issue["blocking"] for issue in result["issues"]))

    def test_excluded_offer_missing_cost_does_not_prevent_eligible_ranking(self):
        self.case["offers"][2]["costs"][0]["amount"] = None
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        self.assertIsNone(next(row for row in result["costs"] if row["offer_id"] == "C")["total"])

    def test_excluded_commercial_disagreement_is_visible_warning(self):
        paths, reports = self.reports()
        reports[1]["totals"][2]["total"] = "1701"
        self.save_reports(paths, reports)
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        mismatches = [issue for issue in result["issues"] if issue.get("offer_id") == "C" and issue["kind"] == "conflict"]
        self.assertTrue(mismatches)
        self.assertTrue(all(not issue["blocking"] for issue in mismatches))

    def test_stale_excluded_offer_evidence_still_fails(self):
        paths, _ = self.reports()
        with (self.case_dir / "报价丙.md").open("a", encoding="utf-8") as stream:
            stream.write("修订后的原始材料。\n")
        self.assert_rejected(self.evaluate, paths)

    def test_invalid_excluded_offer_evidence_still_fails(self):
        paths, reports = self.reports()
        self.assessment(reports[2], "C", "quality")["evidence"][0]["quote"] = "不存在的证据"
        self.save_reports(paths, reports)
        self.assert_rejected(self.evaluate, paths)

    def test_member_report_v1_is_rejected_without_automatic_migration(self):
        for index in range(3):
            with self.subTest(role=index):
                paths, reports = self.reports()
                reports[index]["schema_version"] = 1
                self.save_reports(paths, reports)
                self.assert_rejected(self.evaluate, paths)

    def test_issue_scope_and_category_are_strict(self):
        malformed = [
            {"scope": "global", "category": "evaluation", "message": "不能伪装全局问题", "offer_id": "C"},
            {"scope": "offer", "category": "evaluation", "message": "缺少报价标识"},
            {"scope": "offer", "offer_id": "UNKNOWN", "category": "evaluation", "message": "未知报价"},
            {"scope": "offer", "offer_id": "C", "category": "informational", "message": "未知分类"},
            {"scope": "project", "category": "evaluation", "message": "未知范围"},
            "旧版问题字符串不能自动归类",
        ]
        for issue in malformed:
            with self.subTest(issue=issue):
                paths, reports = self.reports()
                reports[2]["issues"] = [issue]
                self.save_reports(paths, reports)
                self.assert_rejected(self.evaluate, paths)

    def test_unknown_nested_fields_cannot_override_excluded_issue_validation(self):
        for location in ("assessment", "total", "evidence"):
            with self.subTest(location=location):
                paths, reports = self.reports()
                if location == "assessment":
                    target = self.assessment(reports[2], "C", "quality")
                elif location == "total":
                    target = reports[2]["totals"][2]
                else:
                    target = self.assessment(reports[2], "C", "quality")["evidence"][0]
                target["blocking"] = False
                self.save_reports(paths, reports)
                self.assert_rejected(self.evaluate, paths)

    def test_notes_are_required_bounded_text_not_an_untyped_issue_escape(self):
        for notes in (None, [""], [True], ["x" * 2001]):
            with self.subTest(notes_type=type(notes).__name__):
                paths, reports = self.reports()
                if notes is None:
                    del reports[2]["notes"]
                else:
                    reports[2]["notes"] = notes
                self.save_reports(paths, reports)
                self.assert_rejected(self.evaluate, paths)

    def test_explained_v2_adaptation_of_saved_manual_reports(self):
        # Explicitly edited schema fixture, not a replay claim about new models.
        metadata = json.loads((ADAPTED_REPORTS / "adaptation.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["evidence_kind"], "explicit_schema_adaptation_not_new_model_test")
        for name, expected in metadata["adapted_reports_sha256"].items():
            self.assertEqual(hashlib.sha256((ADAPTED_REPORTS / name).read_bytes()).hexdigest(), expected)
        self.assertTrue(all(len(value) == 64 for value in metadata["original_reports_sha256"].values()))
        inspection = self.module.inspect_case(self.case_path)
        paths = []
        for name in ("technical.json", "commercial.json", "verifier.json"):
            report = json.loads((ADAPTED_REPORTS / name).read_text(encoding="utf-8"))
            self.assertEqual(report["case_sha256"], inspection["case_sha256"])
            paths.append(write_json(self.root / name, report))
        result = self.evaluate(paths)
        self.assert_reviewed_b_then_a(result)
        quality = next(row for row in result["compliance"] if row["offer_id"] == "C" and row["criterion_id"] == "quality")
        self.assertEqual(quality["technical"]["status"], "unknown")
        self.assertEqual(quality["verification"]["status"], "unknown")
        self.assertTrue(result["notes"])
        self.assertTrue(result["warnings"])
        self.assertFalse(result["participation_verified"])

    def test_no_eligible_offers_does_not_rank(self):
        paths, reports = self.reports()
        for report in (reports[0], reports[2]):
            for assessment in report["assessments"]:
                if assessment["criterion_id"] == "delivery":
                    assessment["status"] = "fail"
        write_json(paths[0], reports[0]); write_json(paths[2], reports[2])
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "no_eligible_offer")
        self.assertEqual(result["rankings"], [])

    def test_missing_currency_requires_clarification(self):
        self.case["offers"][1]["currency"] = None
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(result["clarifications"])

    def test_missing_project_currency_delivers_clarification_without_rank(self):
        del self.case["currency"]
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertIsNone(result["currency"])
        self.assertEqual(result["rankings"], [])
        self.assertTrue(result["clarifications"])
        output = self.root / "缺少项目币种的澄清档案"
        delivered = self.module.deliver(self.case_path, *paths, output)
        self.assertEqual(delivered["status"], "clarification_required")
        archived = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
        self.assertIsNone(archived["currency"])
        self.assertEqual(archived["rankings"], [])
        self.assertTrue((output / "comparison.html").is_file())

    def test_missing_ranking_method_is_not_silently_inferred(self):
        del self.case["ranking_method"]
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_unknown_ranking_method_is_not_silently_substituted(self):
        self.case["ranking_method"] = "arbitrary-user-formula"
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_mixed_currency_does_not_invent_conversion(self):
        self.case["offers"][1]["currency"] = "USD"
        paths, _ = self.reports()
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])

    def test_independent_disagreement_blocks_rank(self):
        paths, reports = self.reports()
        reports[2]["assessments"][0]["status"] = "fail"
        write_json(paths[2], reports[2])
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])
        self.assertTrue(result["conflicts"])

    def test_unknown_mandatory_condition_is_not_a_pass(self):
        paths, reports = self.reports()
        for report in (reports[0], reports[2]):
            report["assessments"][0].update(status="unknown", evidence=[], rationale="无法从材料确认。")
        write_json(paths[0], reports[0]); write_json(paths[2], reports[2])
        result = self.evaluate(paths)
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])

    def test_commercial_total_mismatch_cannot_silently_rank(self):
        paths, reports = self.reports()
        reports[1]["totals"][0]["total"] = "1000"
        write_json(paths[1], reports[1])
        try:
            result = self.evaluate(paths)
        except self.module.QuoteError:
            return
        self.assertEqual(result["status"], "clarification_required")
        self.assertEqual(result["rankings"], [])

    def test_changed_source_invalidates_previous_reports(self):
        paths, _ = self.reports()
        with (self.case_dir / "报价甲.md").open("a", encoding="utf-8") as stream:
            stream.write("新增说明：报价已修订。\n")
        self.assert_rejected(self.evaluate, paths)

    def test_changed_rubric_invalidates_previous_reports(self):
        paths, _ = self.reports()
        self.case["technical_weight"], self.case["cost_weight"] = "50", "50"
        self.save_case()
        self.assert_rejected(self.evaluate, paths)

    def test_false_evidence_is_rejected(self):
        paths, reports = self.reports()
        reports[0]["assessments"][0]["evidence"][0]["quote"] = "承诺 1 天内交货。"
        write_json(paths[0], reports[0])
        self.assert_rejected(self.evaluate, paths)

    def test_another_offer_source_is_not_own_evidence(self):
        paths, reports = self.reports()
        reports[0]["assessments"][0]["evidence"] = copy.deepcopy(reports[0]["assessments"][2]["evidence"])
        write_json(paths[0], reports[0])
        self.assert_rejected(self.evaluate, paths)

    def test_report_role_substitution_is_rejected(self):
        paths, reports = self.reports()
        reports[2]["role"] = "technical"
        write_json(paths[2], reports[2])
        self.assert_rejected(self.evaluate, paths)

    def test_missing_assessment_is_rejected(self):
        paths, reports = self.reports()
        reports[0]["assessments"].pop()
        write_json(paths[0], reports[0])
        self.assert_rejected(self.evaluate, paths)

    def test_duplicate_assessment_is_rejected(self):
        paths, reports = self.reports()
        reports[0]["assessments"].append(copy.deepcopy(reports[0]["assessments"][0]))
        write_json(paths[0], reports[0])
        self.assert_rejected(self.evaluate, paths)

    def test_missing_report_fails_without_output(self):
        paths, _ = self.reports()
        paths[2].unlink()
        output = self.root / "不存在的输出"
        self.assert_rejected(self.module.deliver, self.case_path, *paths, output)
        self.assertFalse(output.exists())

    def test_duplicate_offer_id_rejected(self):
        self.case["offers"][1]["id"] = "A"
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_source_traversal_is_rejected(self):
        (self.root / "outside.md").write_text("不能读取到这里。", encoding="utf-8")
        self.case["sources"][0]["path"] = "../outside.md"
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_snapshot_source_id_cannot_be_a_path(self):
        self.case["sources"][0]["id"] = "../../outside"
        self.case["offers"][0]["source_ids"] = ["../../outside"]
        for cost in self.case["offers"][0]["costs"]:
            cost["evidence"]["source_id"] = "../../outside"
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_aliased_source_paths_are_rejected(self):
        self.case["sources"].append({"id": "alias", "path": "./报价甲.md"})
        self.save_case()
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_source_symlink_is_rejected(self):
        source = self.case_dir / "报价甲.md"
        source.unlink()
        source.symlink_to(self.case_dir / "报价乙.md")
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_source_size_is_bounded(self):
        (self.case_dir / "报价甲.md").write_text("x" * (256 * 1024 + 1), encoding="utf-8")
        self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_numeric_rejections(self):
        for value in ("NaN", "Infinity", "-1", True):
            with self.subTest(value=value):
                self.case["offers"][0]["costs"][0]["amount"] = value
                self.save_case()
                self.assert_rejected(self.module.inspect_case, self.case_path)

    def test_existing_output_directory_is_preserved(self):
        paths, _ = self.reports()
        output = self.root / "已存在"
        output.mkdir()
        marker = output / "用户材料.txt"
        marker.write_text("保留", encoding="utf-8")
        self.assert_rejected(self.module.deliver, self.case_path, *paths, output)
        self.assertEqual(marker.read_text(encoding="utf-8"), "保留")
        self.assertEqual(list(output.iterdir()), [marker])

    def test_racing_empty_output_is_not_deleted_on_failed_claim(self):
        paths, _ = self.reports()
        output = self.root / "并发创建的目录"
        original_mkdir = Path.mkdir

        def competing_mkdir(path, *args, **kwargs):
            if path == output:
                original_mkdir(path, *args, **kwargs)
                raise FileExistsError("合成并发：用户刚刚创建了这个目录")
            return original_mkdir(path, *args, **kwargs)

        with mock.patch.object(Path, "mkdir", competing_mkdir):
            self.assert_rejected(self.module.deliver, self.case_path, *paths, output)
        self.assertTrue(output.is_dir(), "未获得目录所有权时，不得在回滚中删除它")
        self.assertEqual(list(output.iterdir()), [])

    def test_report_html_and_csv_escape_untrusted_values(self):
        self.case["title"] = "<script>alert('不能执行')</script>"
        # Criterion identities are actually included in the compliance CSV.
        self.case["criteria"][0]["id"] = "=HYPERLINK(\"https://invalid.example\")"
        paths, _ = self.reports()
        output = self.root / "安全输出"
        self.module.deliver(self.case_path, *paths, output)
        html = next(output.glob("*.html")).read_text(encoding="utf-8")
        self.assertNotIn("<script>", html.lower())
        self.assertIn("&lt;script&gt;", html)
        csvs = [p.read_text(encoding="utf-8-sig") for p in output.glob("*.csv")]
        self.assertTrue(csvs)
        self.assertTrue(any("'=HYPERLINK" in body for body in csvs))
        self.assertTrue(any(output.glob("*.json")))
        self.assertTrue(any(output.glob("*.md")))

    def test_delivered_snapshots_replay_with_identical_input_and_result(self):
        paths, _ = self.reports()
        original = self.evaluate(paths)
        output = self.root / "可复算交付"
        self.module.deliver(self.case_path, *paths, output)
        frozen_case = output / "inputs/case/case.json"
        frozen_reports = [output / "inputs/reports" / name for name in
                          ("technical.json", "commercial.json", "verifier.json")]
        frozen = self.module.evaluate(frozen_case, *frozen_reports)
        self.assertEqual(frozen, original)
        self.assertEqual(self.module.inspect_case(frozen_case)["case_sha256"], original["case_sha256"])

    def test_cli_inspection_and_error_are_json(self):
        command = [sys.executable, "-B", str(SCRIPT), "inspect", "--case", str(self.case_path)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["version"], "1.0.1")
        self.assertIn("case_sha256", response)
        result = subprocess.run(command[:-1] + [str(self.root / "missing.json")], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        error = json.loads(result.stdout)
        self.assertFalse(error["ok"])
        self.assertIn("error", error)


if __name__ == "__main__":
    unittest.main()
