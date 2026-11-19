"""Business regressions; the oracle is a separate joint-state Dijkstra search."""
from __future__ import annotations

import copy
import heapq
import importlib.util
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("ROBOT_TEST_PAYLOAD", BASE / "robot-route-review-team"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "skills/route-workflow/scripts"))
import protocol


def module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj


planner = module("bounded_planner", "agents/planner/skills/route-search/scripts/planner.py")
replay = module("linear_replay", "agents/verifier/skills/route-replay/scripts/replay.py")
dossier = module("route_dossier", "skills/route-workflow/scripts/dossier.py")


def joint_oracle(case):
    """Independent tiny-instance optimum, no calls into either runtime algorithm."""
    goals = tuple(tuple(r["goal"]) for r in case["robots"])
    start = tuple(tuple(r["start"]) for r in case["robots"])
    walls = set(map(tuple, case["grid"]["obstacles"]))
    queue, seen, serial = [(0, 0, 0, start)], {}, itertools.count(1)
    while queue:
        cost, tick, _, state = heapq.heappop(queue)
        if seen.get((state, tick), cost) < cost:
            continue
        if state == goals:
            return cost
        if tick == case["horizon"]:
            continue
        choices = []
        for index, (x, y) in enumerate(state):
            choices.append([(x, y)] if (x, y) == goals[index] else
                           [(x + dx, y + dy) for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1))
                            if 0 <= x + dx < case["grid"]["width"] and 0 <= y + dy < case["grid"]["height"] and (x + dx, y + dy) not in walls])
        for nxt in itertools.product(*choices):
            if len(set(nxt)) != len(nxt) or any(state[a] == nxt[b] and state[b] == nxt[a]
                                               for a in range(len(nxt)) for b in range(a + 1, len(nxt))):
                continue
            new_cost = cost + sum(pos != goals[i] for i, pos in enumerate(state))
            key = (nxt, tick + 1)
            if new_cost < seen.get(key, float("inf")):
                seen[key] = new_cost; heapq.heappush(queue, (new_cost, tick + 1, next(serial), nxt))
    return None


class Routes(unittest.TestCase):
    def setUp(self):
        scratch = BASE / ".local/test-scratch"; scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch); self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.case = json.loads((ROOT / "examples/passing-bay.json").read_text())
        self.case_path = self.work / "case.json"

    def save(self, name, data):
        path = self.work / name; path.write_bytes(protocol.encoded(data)); return path

    def prepare(self, case=None):
        self.save("case.json", case or self.case)
        self.map_path = self.save("map.json", protocol.inspect(self.case_path))
        self.model_path = self.save("model.json", replay.audit(self.case_path))
        self.plan = planner.solve(self.case_path, self.map_path)
        self.plan_path = self.save("plan.json", self.plan)
        self.review = replay.review(self.case_path, self.model_path, self.plan_path)
        self.review_path = self.save("review.json", self.review)
        return self.plan

    def deliver(self, name="delivery"):
        return dossier.deliver(self.case_path, self.map_path, self.model_path, self.plan_path, self.review_path, self.work / name)

    def check_paths(self, paths):
        p = copy.deepcopy(self.plan); p["paths"] = paths
        return replay.check_plan(self.case, protocol.sha(self.case_path.read_bytes()), p)

    def test_passing_bay_computed_not_hardcoded(self):
        plan = self.prepare()
        self.assertEqual(plan["status"], "found")
        self.assertEqual(self.review["verdict"], "route_valid")
        self.assertEqual(plan["metrics"]["sum_of_costs"], joint_oracle(self.case))
        self.assertEqual(plan["metrics"], {"sum_of_costs": 7, "makespan": 4})
        self.assertTrue(any([1, 1] in p for p in plan["paths"].values()))

    def test_oracle_random_tiny_instances(self):
        rng = random.Random(214)
        for index in range(14):
            cells = list(itertools.product(range(3), range(2)))
            starts, goals = rng.sample(cells, 2), rng.sample(cells, 2)
            case = copy.deepcopy(self.case); case["grid"]["obstacles"] = []
            case["horizon"] = 4
            for robot, start, goal in zip(case["robots"], starts, goals):
                robot.update(start=list(start), goal=list(goal))
            with self.subTest(index=index):
                plan = self.prepare(case); optimum = joint_oracle(case)
                self.assertEqual(plan["status"], "found" if optimum is not None else "infeasible_within_horizon")
                if optimum is not None:
                    self.assertEqual(plan["metrics"]["sum_of_costs"], optimum)
                    self.assertEqual(self.review["verdict"], "route_valid")

    def test_four_robot_rotation(self):
        case = copy.deepcopy(self.case); case["grid"] = {"width": 2, "height": 2, "obstacles": []}
        ring = [[0, 0], [1, 0], [1, 1], [0, 1]]
        case["robots"] = [{"id": chr(65 + i), "start": p, "goal": ring[(i + 1) % 4]} for i, p in enumerate(ring)]
        plan = self.prepare(case)
        self.assertEqual(plan["metrics"]["sum_of_costs"], 4)
        self.assertEqual(self.review["verdict"], "route_valid")

    def test_three_robots_and_stationary_goal(self):
        case = copy.deepcopy(self.case); case["grid"]["obstacles"] = []
        case["robots"].append({"id": "C", "start": [0, 1], "goal": [0, 1]})
        self.prepare(case)
        self.assertEqual(self.review["verdict"], "route_valid")
        self.assertEqual(self.plan["paths"]["C"], [[0, 1]])

    def test_no_bay_finite_no_solution(self):
        case = json.loads((ROOT / "examples/no-bay.json").read_text()); case["horizon"] = 4
        self.prepare(case)
        self.assertIsNone(joint_oracle(case))
        self.assertEqual(self.plan["status"], "infeasible_within_horizon")
        self.assertEqual(self.review["verdict"], "no_route_to_verify")
        self.assertEqual(self.deliver()["status"], "infeasible_within_horizon")

    def test_horizon_too_short_is_not_global_no_solution(self):
        case = copy.deepcopy(self.case); case["horizon"] = 1
        self.prepare(case); self.assertEqual(self.plan["status"], "infeasible_within_horizon")
        self.assertIn("时域", self.plan["reason"])

    def test_search_budget_is_unknown(self):
        case = copy.deepcopy(self.case); case["limits"] = {"high_level_nodes": 1}
        self.prepare(case); self.assertEqual(self.plan["status"], "search_limit")
        self.assertFalse(self.plan["search"]["complete"])
        self.assertEqual(self.deliver()["status"], "search_limit")

    def test_low_search_budget_is_unknown(self):
        case = copy.deepcopy(self.case); case["limits"] = {"low_level_nodes": 1}
        self.prepare(case); self.assertEqual(self.plan["status"], "search_limit")

    def test_vertex_collision(self):
        self.prepare()
        result = self.check_paths({"A": [[0, 0], [1, 0], [2, 0]], "B": [[2, 0], [1, 0], [0, 0]]})
        self.assertTrue(any(f["code"] == "vertex" and f["tick"] == 1 for f in result["findings"]))

    def test_edge_swap(self):
        self.prepare()
        result = self.check_paths({"A": [[0, 0], [1, 0], [2, 0]], "B": [[2, 0], [2, 0], [1, 0], [0, 0]]})
        self.assertTrue(any(f["code"] == "edge_swap" and f["tick"] == 2 for f in result["findings"]))

    def test_wall_and_jump(self):
        self.prepare(); paths = copy.deepcopy(self.plan["paths"])
        paths["A"] = [[0, 0], [0, 1], [2, 0]]
        codes = {f["code"] for f in self.check_paths(paths)["findings"]}
        self.assertTrue({"obstacle", "illegal_move"} <= codes)

    def test_wrong_start_and_goal(self):
        self.prepare(); paths = copy.deepcopy(self.plan["paths"]); paths["A"] = [[1, 0], [1, 1]]
        codes = {f["code"] for f in self.check_paths(paths)["findings"]}
        self.assertTrue({"wrong_start", "wrong_goal"} <= codes)

    def test_leave_goal_after_arrival(self):
        self.prepare(); paths = copy.deepcopy(self.plan["paths"])
        paths["A"] = [[0, 0], [1, 0], [2, 0], [1, 0], [2, 0]]
        self.assertIn("left_goal", {f["code"] for f in self.check_paths(paths)["findings"]})

    def test_goal_occupation_not_disappearance(self):
        self.prepare(); paths = {"A": [[0, 0], [1, 0], [2, 0]], "B": [[2, 0], [1, 0], [1, 1], [1, 0], [2, 0], [1, 0], [0, 0]]}
        self.assertTrue(any(f["code"] == "vertex" and f["tick"] == 4 for f in self.check_paths(paths)["findings"]))

    def test_missing_robot(self):
        self.prepare()
        with self.assertRaises(protocol.ContractError): self.check_paths({"A": self.plan["paths"]["A"]})

    def test_boolean_coordinate_rejected(self):
        self.prepare(); paths = copy.deepcopy(self.plan["paths"]); paths["A"][0] = [False, 0]
        with self.assertRaises(protocol.ContractError): self.check_paths(paths)

    def test_tampered_metric(self):
        self.prepare(); self.plan["metrics"]["sum_of_costs"] = 0
        result = replay.check_plan(self.case, protocol.sha(self.case_path.read_bytes()), self.plan)
        self.assertIn("metrics_mismatch", {f["code"] for f in result["findings"]})

    def test_stale_case_even_when_only_whitespace_changes(self):
        self.prepare(); self.case_path.write_text(json.dumps(self.case))
        with self.assertRaises(protocol.ContractError): replay.review(self.case_path, self.model_path, self.plan_path)

    def test_stale_plan_bytes(self):
        self.prepare(); self.plan["notes"].append("新的说明也改变字节绑定")
        self.save("plan.json", self.plan)
        with self.assertRaises(protocol.ContractError): self.deliver()

    def test_stale_map_report(self):
        self.prepare(); m = json.loads(self.map_path.read_text()); m["notes"].append("追加说明")
        self.save("map.json", m)
        with self.assertRaises(protocol.ContractError): self.deliver()

    def test_stale_model_review(self):
        self.prepare(); m = json.loads(self.model_path.read_text()); m["notes"].append("追加说明")
        self.save("model.json", m)
        with self.assertRaises(protocol.ContractError): self.deliver()

    def test_disagreement_cannot_be_silently_accepted(self):
        self.prepare(); self.review["verdict"] = "route_invalid"; self.save("review.json", self.review)
        with self.assertRaises(protocol.ContractError): self.deliver()

    def test_real_model_issue_blocks(self):
        self.prepare(); m = json.loads(self.model_path.read_text()); m["issues"] = ["用户是否允许跟随尚未明确；须澄清。"]
        self.save("model.json", m); self.save("review.json", replay.review(self.case_path, self.model_path, self.plan_path))
        self.assertEqual(self.deliver()["status"], "blocked")

    def test_map_issue_prevents_search(self):
        self.prepare(); m = json.loads(self.map_path.read_text()); m["issues"] = ["目标含义不明确。"]
        self.save("map.json", m)
        with self.assertRaises(protocol.ContractError): planner.solve(self.case_path, self.map_path)

    def test_informational_note_does_not_block(self):
        self.prepare(); self.review["notes"].append("本轮仅作离散检查，不验证真实安全。")
        self.save("review.json", self.review)
        self.assertEqual(self.deliver()["status"], "reviewed")

    def test_no_overwrite_results(self):
        self.prepare(); self.deliver(); before = (self.work / "delivery/artifact.json").read_bytes()
        with self.assertRaises(protocol.ContractError): self.deliver()
        self.assertEqual(before, (self.work / "delivery/artifact.json").read_bytes())

    def test_no_overwrite_single_report(self):
        path = self.save("old.json", {"protected": True}); before = path.read_bytes()
        with self.assertRaises(protocol.ContractError): protocol.write_new(path, b"replace")
        self.assertEqual(path.read_bytes(), before)

    def test_symlink_report_rejected(self):
        self.prepare(); link = self.work / "link.json"; link.symlink_to(self.case_path)
        with self.assertRaises(protocol.ContractError): protocol.load_case(link)

    def test_invalid_input_variants(self):
        mutations = [lambda c:c.update(horizon=41), lambda c:c.update(model="continuous"),
                     lambda c:c.update(unknown="unsupported"), lambda c:c["robots"][0].update(start=[True, 0]),
                     lambda c:c["robots"][0].update(goal=[0, 1]), lambda c:c["robots"][1].update(goal=[2, 0]),
                     lambda c:c["grid"]["obstacles"].append([0, 1]), lambda c:c.update(limits={"seconds": 0.5})]
        for change in mutations:
            c = copy.deepcopy(self.case); change(c)
            with self.subTest(case=c), self.assertRaises(protocol.ContractError): protocol.validate_case(c)

    def test_duplicate_json_key_rejected(self):
        self.case_path.write_text('{"a":1,"a":2}')
        with self.assertRaises(protocol.ContractError): protocol.read_json(self.case_path)

    def test_oversized_case_rejected(self):
        self.case_path.write_bytes(b" " * 65537)
        with self.assertRaises(protocol.ContractError): protocol.load_case(self.case_path)

    def test_bounded_record_type_validation(self):
        self.prepare()
        for mutation in (lambda p:p["search"].update(complete=False), lambda p:p["search"].update(high_level_expanded=True),
                         lambda p:p.update(status="invented"), lambda p:p.update(horizon=9)):
            p = copy.deepcopy(self.plan); mutation(p)
            with self.assertRaises(protocol.ContractError): replay.check_plan(self.case, protocol.sha(self.case_path.read_bytes()), p)

    def test_artifact_hashes_chinese_csv_html_escaping(self):
        self.case["title"] = '合成 <script>unsafe</script> & 中文'; self.prepare(); self.deliver()
        out = self.work / "delivery"; artifact = json.loads((out / "artifact.json").read_text())
        for name, digest in artifact["files_sha256"].items(): self.assertEqual(protocol.sha((out / name).read_bytes()), digest)
        html = (out / "routes.html").read_text()
        self.assertNotIn(self.case["title"], html); self.assertIn('\\u003cscript', html)
        self.assertNotIn("__DOSSIER_JSON__", html)
        self.assertEqual(len((out / "timesteps.csv").read_text().splitlines()), 1 + (self.case["horizon"] + 1) * 2)
        self.assertIn("等待人工检查", html)

    def test_cli_actual_handoff_and_outputs(self):
        self.save("case.json", self.case)
        commands = [
            ["skills/route-workflow/scripts/protocol.py", "--case", "case.json", "--output", "map.json"],
            ["agents/verifier/skills/route-replay/scripts/replay.py", "audit-model", "--case", "case.json", "--output", "model.json"],
            ["agents/planner/skills/route-search/scripts/planner.py", "--case", "case.json", "--map-report", "map.json", "--output", "plan.json"],
            ["agents/verifier/skills/route-replay/scripts/replay.py", "review", "--case", "case.json", "--model-report", "model.json", "--plan", "plan.json", "--output", "review.json"],
            ["skills/route-workflow/scripts/dossier.py", "--case", "case.json", "--map-report", "map.json", "--model-report", "model.json", "--plan", "plan.json", "--review", "review.json", "--output", "delivery"]]
        for relative, *args in commands:
            result = subprocess.run([sys.executable, "-B", str(ROOT / relative), *args], cwd=self.work, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertEqual(json.loads((self.work / "delivery/evaluation.json").read_text())["status"], "reviewed")
        self.assertLessEqual((self.work / "model.json").stat().st_mtime_ns, (self.work / "plan.json").stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
