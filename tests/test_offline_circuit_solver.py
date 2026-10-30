"""Functional checks against analytic circuits and electrical conservation."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("offline_circuit_solver", ROOT / "plugins/offline-circuit-lab/offline-circuit-lab/runtime/solver.py")
SOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOLVER)


def component(ident, kind, a, b, value):
    return {"id": ident, "type": kind, "a": a, "b": b, "value": value}


def rc(resistance=1000, duration_ms=1, step_us=10):
    return {"components": [component("V1", "V", "1", "0", 5),
                           component("R1", "R", "1", "2", resistance),
                           component("C1", "C", "2", "0", 1e-6)],
            "duration_ms": duration_ms, "step_us": step_us, "probe": "2"}


class CircuitSolverTests(unittest.TestCase):
    def success(self, circuit):
        result = SOLVER.simulate(circuit)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["version"], "1.0.0")
        json.dumps(result, ensure_ascii=False, allow_nan=False)
        return result

    def failure(self, circuit, code):
        result = SOLVER.simulate(circuit)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], code, result)
        self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in result["error"]["message"]))
        self.assertNotIn("samples", result)
        return result

    def test_dc_voltage_divider_and_power_balance(self):
        circuit = {"mode": "dc", "probe": "2", "components": [
            component("V1", "V", "1", "0", 5), component("R1", "R", "1", "2", 1000),
            component("R2", "R", "2", "0", 1000)]}
        result = self.success(circuit)
        self.assertAlmostEqual(result["summary"]["final_voltage"], 2.5, places=10)
        sample = result["samples"][0]
        self.assertAlmostEqual(sample["currents"]["V1"], -0.0025, places=10)
        power = sum((sample["voltages"][c["a"]] - sample["voltages"][c["b"]]) * sample["currents"][c["id"]] for c in circuit["components"])
        self.assertAlmostEqual(power, 0, places=12)

    def test_rc_step_at_one_time_constant(self):
        result = self.success(rc())
        self.assertEqual(result["samples"][0]["voltages"], {"0": 0, "1": 0, "2": 0})
        self.assertAlmostEqual(result["summary"]["final_voltage"], 5 * (1 - math.exp(-1)), delta=0.001)
        self.assertEqual(len(result["samples"]), 101)
        self.assertAlmostEqual(result["samples"][-1]["t"], .001)
        self.assertAlmostEqual(result["samples"][1]["voltages"]["1"], 5)

    def test_edit_resistance_changes_actual_rc_response(self):
        slow = self.success(rc(resistance=2000))
        fast = self.success(rc())
        self.assertAlmostEqual(slow["summary"]["final_voltage"], 5 * (1 - math.exp(-.5)), delta=.001)
        self.assertGreater(fast["summary"]["final_voltage"] - slow["summary"]["final_voltage"], 1)

    def test_edit_topology_parallel_load_changes_response(self):
        circuit = rc()
        circuit["components"].append(component("R2", "R", "2", "0", 1000))
        result = self.success(circuit)
        # Thevenin: final 2.5V, Rth=500 ohm, tau=0.5ms.
        self.assertAlmostEqual(result["summary"]["final_voltage"], 2.5 * (1 - math.exp(-2)), delta=.001)

    def test_parallel_capacitors_are_supported(self):
        circuit = rc()
        circuit["components"].append(component("C2", "C", "2", "0", 1e-6))
        result = self.success(circuit)
        self.assertAlmostEqual(result["summary"]["final_voltage"], 5 * (1 - math.exp(-.5)), delta=.001)
        self.assertAlmostEqual(result["samples"][-1]["currents"]["C1"], result["samples"][-1]["currents"]["C2"], places=12)

    def test_rl_step(self):
        circuit = {"duration_ms": 1, "step_us": 10, "probe": "2", "components": [
            component("V1", "V", "1", "0", 5), component("R1", "R", "1", "2", 100),
            component("L1", "L", "2", "0", .1)]}
        result = self.success(circuit)
        sample = result["samples"][-1]
        self.assertAlmostEqual(sample["currents"]["L1"], .05 * (1 - math.exp(-1)), delta=1e-5)
        self.assertAlmostEqual(sample["voltages"]["2"], 5 * math.exp(-1), delta=.001)

    def test_rlc_underdamped_waveform_and_timestep_convergence(self):
        circuit = {"duration_ms": .3, "step_us": 2, "probe": "3", "components": [
            component("V1", "V", "1", "0", 5), component("R1", "R", "1", "2", 100),
            component("L1", "L", "2", "3", .01), component("C1", "C", "3", "0", 1e-6)]}
        coarse = self.success(circuit)
        circuit["step_us"] = 1
        fine = self.success(circuit)
        alpha, omega, t = 5000, math.sqrt(1e8 - 5000**2), .0003
        exact = 5 * (1 - math.exp(-alpha * t) * (math.cos(omega * t) + alpha / omega * math.sin(omega * t)))
        self.assertAlmostEqual(fine["summary"]["final_voltage"], exact, delta=.002)
        self.assertLess(abs(fine["summary"]["final_voltage"] - exact), abs(coarse["summary"]["final_voltage"] - exact))
        self.assertGreater(fine["summary"]["max_voltage"], 5)

    def test_arbitrary_bridge_with_multiple_sources_obeys_kcl(self):
        circuit = {"mode": "dc", "probe": "中点", "components": [
            component("源甲", "V", "左", "0", 5), component("源乙", "V", "右", "0", -2),
            component("R1", "R", "左", "中点", 1000), component("R2", "R", "右", "中点", 2000),
            component("R3", "R", "中点", "0", 3000), component("R4", "R", "左", "右", 4700)]}
        result = self.success(circuit)
        sample = result["samples"][0]
        expected = (5 / 1000 - 2 / 2000) / (1 / 1000 + 1 / 2000 + 1 / 3000)
        self.assertAlmostEqual(sample["voltages"]["中点"], expected, places=10)
        for node in sample["voltages"]:
            current = sum(sample["currents"][c["id"]] * ((c["a"] == node) - (c["b"] == node)) for c in circuit["components"])
            self.assertAlmostEqual(current, 0, places=10)

    def test_dc_capacitor_open_inductor_short(self):
        circuit = {"mode": "dc", "probe": "2", "components": [
            component("V1", "V", "1", "0", 5), component("R1", "R", "1", "2", 1000),
            component("L1", "L", "2", "0", .1), component("C1", "C", "1", "0", 1e-6)]}
        sample = self.success(circuit)["samples"][0]
        self.assertAlmostEqual(sample["voltages"]["2"], 0)
        self.assertAlmostEqual(sample["currents"]["L1"], .005)
        self.assertEqual(sample["currents"]["C1"], 0)

    def test_dc_floating_node_after_capacitor_opens_is_rejected(self):
        circuit = {"mode": "dc", "probe": "2", "components": [
            component("V1", "V", "1", "0", 5), component("C1", "C", "1", "2", 1e-6)]}
        self.failure(circuit, "singular_network")

    def test_incompatible_capacitor_initial_voltage_is_rejected(self):
        self.failure({"components": [component("V1", "V", "1", "0", 5), component("C1", "C", "1", "0", 1e-6)]}, "inconsistent_initial_state")

    def test_ideal_source_conflict_and_redundancy_are_rejected(self):
        circuit = {"components": [component("V1", "V", "1", "0", 5), component("V2", "V", "1", "0", 3)]}
        self.failure(circuit, "inconsistent_initial_state")
        circuit["components"][1]["value"] = 5
        self.failure(circuit, "singular_network")

    def test_disconnected_floating_component_is_rejected(self):
        circuit = rc()
        circuit["components"].append(component("R2", "R", "漂浮甲", "漂浮乙", 100))
        self.failure(circuit, "floating_network")

    def test_shorted_source_is_rejected(self):
        self.failure({"components": [component("V1", "V", "0", "0", 5)]}, "shorted_component")

    def test_ill_conditioned_network_is_rejected_without_fake_leakage(self):
        circuit = {"duration_ms": .00001, "step_us": .01, "components": [
            component("V1", "V", "1", "0", 5), component("C1", "C", "1", "2", 1),
            component("R1", "R", "2", "0", 1e9)]}
        self.failure(circuit, "numerical_residual")

    def test_step_and_topology_limits(self):
        self.failure(rc(duration_ms=50.01), "step_limit")
        self.failure(rc(duration_ms=.333, step_us=10), "nonintegral_steps")
        self.failure({"components": [component(f"R{i}", "R", "1", "0", 1000) for i in range(25)]}, "component_limit")
        self.failure({"components": [component(f"R{i}", "R", str(i), str(i + 1), 1000) for i in range(16)]}, "node_limit")

    def test_allowed_5000_steps_reach_steady_state(self):
        result = self.success(rc(duration_ms=50, step_us=10))
        self.assertEqual(len(result["samples"]), 5001)
        self.assertAlmostEqual(result["summary"]["final_voltage"], 5, delta=1e-9)

    def test_invalid_values_and_labels(self):
        for bad in (float("nan"), float("inf"), -1, 0, True, "1000", 10**1000):
            circuit = rc()
            circuit["components"][1]["value"] = bad
            self.failure(circuit, "invalid_value")
        circuit = rc()
        circuit["components"][0]["id"] = "__proto__"
        self.failure(circuit, "invalid_label")
        circuit = rc()
        circuit["components"][0]["type"] = "D"
        self.failure(circuit, "unsupported_component")

    def test_duplicate_missing_ground_unknown_probe_and_extra_fields(self):
        circuit = rc()
        circuit["components"][0]["id"] = "R1"
        self.failure(circuit, "duplicate_id")
        self.failure({"components": [component("R1", "R", "1", "2", 1000)]}, "missing_ground")
        circuit = rc()
        circuit["probe"] = "不存在"
        self.failure(circuit, "unknown_probe")
        circuit = rc()
        circuit["components"][0]["initial"] = 3
        self.failure(circuit, "invalid_component")

    def test_input_is_unchanged_and_warning_is_explicit(self):
        circuit = rc()
        before = copy.deepcopy(circuit)
        result = self.success(circuit)
        self.assertEqual(circuit, before)
        self.assertTrue(any("减半步长" in warning for warning in result["warnings"]))
        self.assertTrue(any("阶跃前零状态" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
