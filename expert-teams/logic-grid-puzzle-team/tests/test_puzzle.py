"""Finite-model, independent-reconstruction and delivery regression tests."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = ASSET / "logic-grid-puzzle-team"
FIXTURES = Path(__file__).parent / "fixtures"


def load(role, filename):
    path = PAYLOAD / "agents" / role / "tools" / f"{filename}.py"
    spec = importlib.util.spec_from_file_location(f"puzzle_{filename}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


model = load("modeler", "model")
review = load("reviewer", "review")
deliver = load("leader", "deliver")


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class PuzzleTests(unittest.TestCase):
    def setUp(self):
        # Explicitly disposable asset-owned scratch, outside the runtime payload.
        test_tmp = ASSET / ".local" / "test-tmp"
        test_tmp.mkdir(parents=True, exist_ok=True)
        self.scratch = tempfile.TemporaryDirectory(prefix="logic-grid-test-", dir=test_tmp)
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def assertBoth(self, value, expected):
        modeled = model.analyze(value)
        reviewed = review.analyze(modeled["learner"])
        self.assertEqual(modeled["report"]["solution_count"], expected)
        self.assertEqual(reviewed["solution_count"], expected)
        if expected == 1:
            self.assertEqual(modeled["report"]["solution"], reviewed["solution"])
        self.assertEqual(modeled["report"]["input_sha256"], reviewed["model_sha256"])
        return modeled, reviewed

    def test_three_item_unique_and_complete_explanation(self):
        modeled, reviewed = self.assertBoth(fixture("unique-three"), 1)
        self.assertEqual(modeled["report"]["candidate_count"], 36)
        self.assertEqual(len(reviewed["explanation"]["steps"]), 6)
        self.assertEqual(reviewed["explanation"]["steps"][0]["premises"], [c["id"] for c in fixture("unique-three")["clues"]])

    def test_four_item_unique(self):
        modeled, reviewed = self.assertBoth(fixture("unique-four"), 1)
        self.assertEqual(modeled["report"]["candidate_count"], 576)
        self.assertEqual(len(reviewed["explanation"]["steps"]), 8)

    def test_ambiguity_reports_two_real_counterexamples(self):
        modeled, reviewed = self.assertBoth(fixture("ambiguous"), 24)
        self.assertNotEqual(modeled["report"]["counterexamples"][0], modeled["report"]["counterexamples"][1])
        self.assertEqual(reviewed["explanation"]["steps"], [])

    def test_inconsistent_clues_are_not_vacuously_explained(self):
        _, reviewed = self.assertBoth(fixture("inconsistent"), 0)
        self.assertIsNone(reviewed["solution"])
        self.assertEqual(reviewed["explanation"]["steps"], [])

    def test_algorithms_agree_on_every_nonempty_subset_of_five_clues(self):
        value = fixture("unique-three")
        original = value["clues"]
        for mask in range(1, 1 << len(original)):
            with self.subTest(mask=mask):
                current = copy.deepcopy(value)
                current["clues"] = [c for i, c in enumerate(original) if mask & (1 << i)]
                permutations = model.enumerate_models(model.validate(current))
                reconstructed = review.reconstruct(model.learner_source(current))
                depth_first, _ = review.dfs_solutions(reconstructed)
                self.assertEqual({model.canonical(v) for v in permutations}, {model.canonical(v) for v in depth_first})

    def test_reviewer_rejects_unsupported_chinese_wording(self):
        with self.assertRaises(review.PuzzleError):
            review.analyze(fixture("malformed-learner"))

    def test_changed_negation_changes_source_and_model(self):
        learner = model.analyze(fixture("unique-three"))["learner"]
        original = review.analyze(learner)
        learner["clues"][0]["text"] = learner["clues"][0]["text"].replace("不对应", "对应")
        modified = review.analyze(learner)
        self.assertNotEqual(original["source_sha256"], modified["source_sha256"])
        self.assertNotEqual(original["model_sha256"], modified["model_sha256"])
        self.assertNotEqual(modified["solution_count"], 1)

    def test_unknown_missing_invalid_fields_and_bounds(self):
        operations = [
            lambda v: v.update({"approved": True}),
            lambda v: v.pop("title"),
            lambda v: v.update({"schema_version": 1}),
            lambda v: v.update({"categories": v["categories"][:2]}),
            lambda v: v["categories"][0]["items"].append({"id": "p4", "label": "小李"}),
            lambda v: v["categories"][0]["items"][1].update({"id": "p1"}),
            lambda v: v["categories"][0]["items"][1].update({"label": "小林"}),
            lambda v: v["clues"][0].update({"op": "either"}),
            lambda v: v["clues"][0]["right"].update({"item": "unknown"}),
            lambda v: v["clues"][0].update({"left": v["clues"][0]["right"]}),
            lambda v: v["clues"][1].update({"id": "clue-01"}),
            lambda v: v["clues"].append({**v["clues"][0], "id": "duplicate"}),
            lambda v: v.update({"clues": []}),
            lambda v: v.update({"clues": v["clues"] * 7}),
            lambda v: v["categories"][0].update({"label": "【人物】"}),
            lambda v: v.update({"title": "恶意\u202e标题"}),
        ]
        for index, mutate in enumerate(operations):
            with self.subTest(index=index):
                value = fixture("unique-three")
                mutate(value)
                with self.assertRaises((model.PuzzleError, TypeError)):
                    model.analyze(value)

    def test_source_unknown_fields_and_changed_rules_rejected(self):
        for mutation in (lambda v: v.update({"solution": []}), lambda v: v.update({"rules": "可重复使用项目"}),
                         lambda v: v["clues"].pop(), lambda v: v["categories"][0].update({"label": "人物甲"})):
            learner = model.analyze(fixture("unique-three"))["learner"]
            mutation(learner)
            if len(learner["clues"]) == 4:
                # A valid clue omission is detectable by a new source hash and origin check, not syntax.
                self.assertNotEqual(model.digest(learner), model.digest(model.analyze(fixture("unique-three"))["learner"]))
            else:
                with self.assertRaises(review.PuzzleError):
                    review.analyze(learner)

    def test_certificate_recomputes_and_rejects_tampered_review(self):
        value = fixture("unique-three")
        expected = review.analyze(model.analyze(value)["learner"])
        self.assertEqual(deliver.certify(value, expected)["status"], "verified_unique")
        mutations = [lambda r: r.update({"source_sha256": "0" * 64}), lambda r: r.update({"solution_count": 2}),
                     lambda r: r.update({"approved": True}), lambda r: r["solution"][0].update({"drink": "d1"}),
                     lambda r: r["explanation"]["steps"].pop(),
                     lambda r: r["explanation"]["steps"][0].update({"premises": []}),
                     lambda r: r["explanation"]["steps"][0]["conclusion"].update({"op": "not_match"}),
                     lambda r: r["reconstructed_model"]["clues"].pop()]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                tampered = copy.deepcopy(expected)
                mutate(tampered)
                with self.assertRaises(deliver.PuzzleError):
                    deliver.certify(value, tampered)

    def test_stale_same_id_review_rejected(self):
        value = fixture("unique-three")
        stale = review.analyze(model.analyze(value)["learner"])
        value["title"] = "同编号新版本"
        with self.assertRaises(deliver.PuzzleError):
            deliver.certify(value, stale)

    def test_nonunique_or_inconsistent_delivery_refused(self):
        for name in ("ambiguous", "inconsistent"):
            value = fixture(name)
            checked = review.analyze(model.analyze(value)["learner"])
            with self.assertRaises(deliver.PuzzleError):
                deliver.certify(value, checked)

    def test_json_duplicate_keys_nonfinite_invalid_utf8_and_oversize(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b' ' * 65537):
            path = self.root / "invalid.json"
            path.write_bytes(raw)
            for module in (model, review, deliver):
                with self.subTest(raw=raw[:30], module=module.__name__):
                    with self.assertRaises((ValueError, UnicodeError)):
                        module.read_json(str(path))

    def test_controlled_text_collision_rejected_and_literal_conjunction_supported(self):
        value = fixture("unique-three")
        value["categories"][1]["items"][1]["label"] = "茶不"
        with self.assertRaises(model.PuzzleError):
            model.analyze(value)
        # Independent text dictionary also rejects the collision even if model validation was bypassed.
        with self.assertRaises(review.PuzzleError):
            review.analyze(model.learner_source(value))
        value["categories"][1]["items"][1]["label"] = "茶与咖啡"
        self.assertBoth(value, 1)

    def test_cli_nested_json_and_missing_arguments_are_chinese_json_errors(self):
        nested = self.root / "nested.json"
        nested.write_text("[" * 2000 + "0" + "]" * 2000)
        normal_review = self.root / "normal-review.json"
        normal_review.write_text("{}")
        commands = [("modeler", "model.py", ["--input", str(nested)]),
                    ("reviewer", "review.py", ["--input", str(nested)]),
                    ("leader", "deliver.py", ["--model", str(nested), "--review", str(normal_review), "--output", str(self.root / "unused")])]
        for role, filename, arguments in commands:
            script = PAYLOAD / "agents" / role / "tools" / filename
            for args in (arguments, []):
                result = subprocess.run([sys.executable, str(script), *args], capture_output=True, timeout=5,
                                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                self.assertEqual(result.returncode, 2)
                response = json.loads(result.stdout)
                self.assertFalse(response["ok"])
                self.assertNotIn("Traceback", result.stderr.decode())
                self.assertRegex(response["message"], "[一-龥]")

    def test_bundled_examples_match_original_fixtures(self):
        for sample, original in (("campus-model", "unique-three"), ("four-model", "unique-four")):
            self.assertEqual((PAYLOAD / "examples" / f"{sample}.json").read_bytes(),
                             (FIXTURES / f"{original}.json").read_bytes())

    def test_symlink_and_traversal_input_and_output_rejected(self):
        path = self.root / "input.json"
        path.write_text("{}")
        link = self.root / "link.json"
        link.symlink_to(path)
        folder_link = self.root / "link-dir"
        folder_link.symlink_to(self.root, target_is_directory=True)
        for module in (model, review, deliver):
            for candidate in (str(link), str(folder_link / "input.json"), str(self.root / ".." / "x")):
                with self.subTest(module=module.__name__, candidate=candidate):
                    with self.assertRaises(module.PuzzleError):
                        module.read_json(candidate)

    def test_fifo_input_rejected_without_blocking(self):
        path = self.root / "pipe"
        os.mkfifo(path)
        for module in (model, review, deliver):
            with self.assertRaises(module.PuzzleError):
                module.read_json(str(path))

    def test_delivery_html_is_escaped_and_contains_no_answer(self):
        value = fixture("unique-three")
        value["title"] = "<script>测试</script>"
        checked = review.analyze(model.analyze(value)["learner"])
        certified = deliver.certify(value, checked)
        result = deliver.export(certified, self.root / "delivered")
        page = (self.root / "delivered" / "puzzle.html").read_text()
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("教师答案", page)
        self.assertNotIn("简明验证依据", page)
        self.assertNotIn('"solution"', page)
        self.assertEqual(result["files"]["puzzle.html"], hashlib.sha256(page.encode()).hexdigest())
        audit = json.loads((self.root / "delivered" / "audit.json").read_text())
        self.assertEqual(audit["source_sha256"], review.digest(audit["learner_source"]))

    def test_existing_output_not_overwritten(self):
        directory = self.root / "existing"
        directory.mkdir()
        sentinel = directory / "keep.txt"
        sentinel.write_text("证据")
        with self.assertRaises(FileExistsError):
            model.write_bundle(directory, {"keep.txt": "改变"})
        self.assertEqual(sentinel.read_text(), "证据")

    def test_partial_output_failure_preserves_written_file_without_success_audit(self):
        value = fixture("unique-three")
        checked = review.analyze(model.analyze(value)["learner"])
        certified = deliver.certify(value, checked)
        original_open = Path.open
        def fail_answer(path, *args, **kwargs):
            if path.name == "answer.md":
                raise OSError("simulated disk failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", fail_answer):
            with self.assertRaises(OSError):
                deliver.export(certified, self.root / "partial")
        self.assertTrue((self.root / "partial" / "puzzle.html").is_file())
        self.assertFalse((self.root / "partial" / "audit.json").exists())
        with self.assertRaises(FileExistsError):
            deliver.export(certified, self.root / "partial")

    def test_real_cli_pipeline_and_chinese_failure(self):
        def run(role, file, *arguments):
            result = subprocess.run([sys.executable, str(PAYLOAD / "agents" / role / "tools" / file), *map(str, arguments)],
                                    capture_output=True, timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            return result, json.loads(result.stdout.decode("utf-8"))
        source = FIXTURES / "unique-three.json"
        before = source.read_bytes()
        status, response = run("modeler", "model.py", "--input", source, "--output", self.root / "modeled")
        self.assertEqual(status.returncode, 0, response)
        self.assertTrue((self.root / "modeled" / "model-report.json").is_file())
        status, response = run("reviewer", "review.py", "--input", self.root / "modeled" / "learner.json", "--output", self.root / "reviewed")
        self.assertEqual(status.returncode, 0, response)
        status, response = run("leader", "deliver.py", "--model", source, "--review", self.root / "reviewed" / "review.json", "--output", self.root / "final")
        self.assertEqual(status.returncode, 0, response)
        self.assertEqual(set(p.name for p in (self.root / "final").iterdir()), {"puzzle.html", "answer.md", "audit.json"})
        self.assertEqual(source.read_bytes(), before)
        status, response = run("leader", "deliver.py", "--model", source, "--review", self.root / "reviewed" / "review.json", "--output", self.root / "final")
        self.assertEqual(status.returncode, 2)
        self.assertIn("未完成交付", response["message"])


if __name__ == "__main__":
    unittest.main()
