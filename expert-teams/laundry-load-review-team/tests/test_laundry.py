"""Run the actual CLI against the source or an extracted native package."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("LAUNDRY_PAYLOAD", ROOT / ROOT.name))
SCRIPT = PAYLOAD / "skills/laundry-review/scripts/laundry_review.py"
FIXTURE = ROOT / "tests/fixtures/mixed-basket.json"


class LaundryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="laundry-case-")
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.case = self.dir / "case.json"
        self.case.write_bytes(FIXTURE.read_bytes())

    def cmd(self, action, filename, *args, exit_code=0):
        call = subprocess.run([sys.executable, "-B", str(SCRIPT), action, "--case", str(self.case),
                               "--output", str(self.dir / filename), *map(str, args)],
                              text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(call.returncode, exit_code, call.stdout + call.stderr)
        return json.loads(call.stdout)

    def data(self, filename):
        return json.loads((self.dir / filename).read_bytes())

    def write(self, filename, value):
        (self.dir / filename).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def mutate(self, filename, change):
        value = self.data(filename)
        change(value)
        self.write(filename, value)

    def start(self):
        self.cmd("baseline", "baseline.json")
        self.assertFalse((self.dir / "plan.json").exists())
        self.cmd("plan", "plan.json")

    def check(self, **kwargs):
        return self.cmd("verify", "review.json", "--baseline", self.dir / "baseline.json",
                        "--plan", self.dir / "plan.json", **kwargs)

    def finish(self, **kwargs):
        return self.cmd("deliver", "delivery", "--baseline", self.dir / "baseline.json",
                        "--plan", self.dir / "plan.json", "--review", self.dir / "review.json", **kwargs)

    def audit_mutation(self, change):
        self.start()
        self.mutate("plan.json", lambda report: change(report["result"]))
        self.assertEqual(self.check()["status"], "blocked")
        return {x["code"] for x in self.data("review.json")["result"]["findings"]}

    def test_positive_three_usable_loads_two_wash_holds(self):
        self.start()
        self.assertEqual(self.check()["status"], "reviewed")
        self.assertEqual(self.finish()["status"], "reviewed_with_holds")
        data = self.data("delivery/evaluation.json")
        self.assertEqual(data["checked_pieces"], 11)
        self.assertFalse(data["human_testing_passed"])
        self.assertEqual([sum(y["count"] for y in x["items"]) for x in data["batches"]], [1, 5, 3])
        self.assertEqual({x["profile"]: x["reason"] for x in data["held"]},
                         {"scarf": "hand", "unknown": "unknown_wash"})
        gym = next(x for x in data["batches"] if any(y["profile"] == "gym_top" for y in x["items"]))
        self.assertEqual(gym["program"], "gentle30")
        self.assertEqual({i["dry"] for i in gym["items"]}, {"line", "tumble_low"})
        html = (self.dir / "delivery/checklist.html").read_text()
        for s in ("日常洗衣分批清单", "可用批次已复核", "悬挂晾干", "低温滚筒烘干", "标签不清的新衣"):
            self.assertIn(s, html)
        manifest = self.data("delivery/artifact.json")
        self.assertEqual(len(manifest["files_sha256"]), 6)
        for name, checksum in manifest["files_sha256"].items():
            self.assertEqual(sha256((self.dir / "delivery" / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual((self.dir / "delivery/inputs/case.json").read_bytes(), FIXTURE.read_bytes())

    def test_wrong_temperature_cycle_and_drying_are_blocked(self):
        def inject(plan):
            gym = plan["batches"][-1]
            gym["program"] = "normal40"
            gym["items"][0]["dry"] = "tumble_low"
        self.assertEqual(self.audit_mutation(inject), {"program_conflict", "dry_conflict"})
        self.assertEqual(self.finish()["status"], "blocked")
        result = self.data("delivery/evaluation.json")
        self.assertEqual(result["batches"], [])
        self.assertIn("暂不提供可执行批次", (self.dir / "delivery/checklist.html").read_text())

    def test_machine_without_compatible_program(self):
        self.mutate("case.json", lambda c: c.update(programs=c["programs"][:1]))
        self.start()
        self.assertEqual(self.check()["status"], "reviewed")
        self.finish()
        data = self.data("delivery/evaluation.json")
        self.assertEqual({x["profile"] for x in data["held"] if x["reason"] == "no_program"},
                         {"gym_top", "gym_shorts", "red"})
        self.assertEqual(len(data["batches"]), 1)

    def test_unknown_drying_preserves_verified_wash_assignment(self):
        self.mutate("case.json", lambda c: c["profiles"]["white_tee"].update(dry="unknown"))
        self.start()
        self.check()
        self.finish()
        self.assertEqual(self.data("delivery/evaluation.json")["dry_pending"], [{"profile": "white_tee", "count": 5}])

    def test_color_and_separate_restrictions(self):
        def mix(plan):
            red, _, gym = plan["batches"]
            gym["items"].extend(red["items"])
            del plan["batches"][0]
        self.assertEqual(self.audit_mutation(mix), {"color_conflict", "separate_conflict"})

    def test_capacity_split_and_repeated_separate_group(self):
        self.mutate("case.json", lambda c: c["basket"].update(white_tee=8, red=2))
        self.start()
        self.assertEqual(self.check()["status"], "reviewed")
        batches = self.data("plan.json")["result"]["batches"]
        white = [x["items"][0]["count"] for x in batches if x["program"] == "normal40"]
        red = [x["items"][0]["count"] for x in batches if x["items"][0]["profile"] == "red"]
        self.assertEqual(white, [6, 2])
        self.assertEqual(red, [1, 1])

    def test_count_overflow_duplicate_and_missing_coverage(self):
        def duplicate(plan):
            batch = plan["batches"][1]
            batch["items"].append(batch["items"][0].copy())
            del plan["batches"][-1]
        self.assertEqual(self.audit_mutation(duplicate), {"duplicate_in_load", "count_limit", "coverage"})

    def test_false_hold(self):
        def move(plan):
            white = plan["batches"].pop(1)["items"][0]
            plan["held"].append({"profile": white["profile"], "count": white["count"], "reason": "no_program"})
        self.assertEqual(self.audit_mutation(move), {"incorrect_hold"})

    def test_missing_color_and_separate_facts(self):
        def change(c):
            c["profiles"]["white_tee"]["color"] = None
            c["profiles"]["gym_top"]["separate"] = None
        self.mutate("case.json", change)
        self.start()
        self.check()
        holds = {x["profile"]: x["reason"] for x in self.data("plan.json")["result"]["held"]}
        self.assertEqual((holds["white_tee"], holds["gym_top"]), ("unknown_color", "unknown_separate"))

    def test_separate_with_unknown_color_is_valid_on_its_own(self):
        self.mutate("case.json", lambda c: c["profiles"]["red"].update(color=None))
        self.start()
        self.assertEqual(self.check()["status"], "reviewed")
        self.assertEqual(self.data("plan.json")["result"]["batches"][0]["items"][0]["profile"], "red")

    def test_duplicate_json_and_non_integer_count(self):
        self.case.write_text('{"schema":1,"schema":1}')
        self.assertIn("重复字段", self.cmd("plan", "plan.json", exit_code=2)["message"])
        self.case.write_bytes(FIXTURE.read_bytes())
        self.mutate("case.json", lambda c: c["basket"].update(red=True))
        self.assertIn("件数无效", self.cmd("plan", "plan.json", exit_code=2)["message"])

    def test_stale_case_and_tampered_review(self):
        self.start()
        self.case.write_bytes(self.case.read_bytes() + b"\n")
        self.assertIn("当前案例", self.check(exit_code=2)["message"])
        self.case.write_bytes(FIXTURE.read_bytes())
        self.check()
        self.mutate("review.json", lambda r: r["result"].update(status="blocked"))
        self.assertIn("已过期", self.finish(exit_code=2)["message"])
        self.assertFalse((self.dir / "delivery").exists())

    def test_review_is_bound_to_exact_candidate_bytes(self):
        self.start()
        self.check()
        path = self.dir / "plan.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertIn("已过期", self.finish(exit_code=2)["message"])

    def test_baseline_rejects_candidate_input(self):
        result = self.cmd("baseline", "baseline.json", "--plan", self.dir / "plan.json", exit_code=2)
        self.assertIn("交接参数", result["message"])

    def test_existing_output_and_symlink_are_rejected(self):
        self.start()
        result = self.cmd("plan", "plan.json", exit_code=2)
        self.assertIn("输出已存在", result["message"])
        self.case.unlink()
        self.case.symlink_to(FIXTURE)
        self.assertIn("符号链接", self.cmd("plan", "new.json", exit_code=2)["message"])

    def test_report_escapes_user_supplied_text(self):
        self.mutate("case.json", lambda c: c.update(title="<script>标题</script>"))
        self.start()
        self.check()
        self.finish()
        body = (self.dir / "delivery/checklist.html").read_text()
        self.assertIn("&lt;script&gt;标题&lt;/script&gt;", body)
        self.assertNotIn("<script>", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
