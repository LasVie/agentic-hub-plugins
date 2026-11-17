"""Real-engine reference, input, freshness and numerical consistency checks."""
import copy
import importlib.util
import math
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch

PAYLOAD = Path(os.environ.get("STEAM_PAYLOAD", Path(__file__).resolve().parents[1] / "offline-steam-properties-workbench"))
spec = importlib.util.spec_from_file_location("_steam_test_engine", PAYLOAD / "runtime/engine.py")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
model = engine.model


class InputTests(unittest.TestCase):
    def test_examples_are_independent_and_exact_si_roundtrip(self):
        for name, project in model.examples().items():
            with self.subTest(name=name):
                self.assertEqual(model.strict_json(model.encode(project)), model.validate(project))
                frozen = model.validate(project)
                project["name"] = "输入变化"
                self.assertNotEqual(project, frozen)
                self.assertNotEqual(model.fingerprint(project), model.fingerprint(frozen))

    def test_reject_unsafe_types_and_unknown_fields(self):
        default = model.examples()["常压饱和水"]
        bad = []
        for key, value in (("backend", "REFPROP"), ("script", "import os"), ("fluid", "Air")):
            p = copy.deepcopy(default); p[key] = value; bad.append(p)
        for key, value in (("pressure_pa", True), ("pressure_pa", 10**400), ("pressure_pa", -1),
                           ("pressure_pa", float("inf")), ("quality", -0.1), ("quality", 1.01),
                           ("pair", "constructor"), ("pair", "P|liquid")):
            p = copy.deepcopy(default); p["state"][key] = value; bad.append(p)
        for value in (True, 1, 101, 2.5):
            p = copy.deepcopy(default); p["sweep"]["points"] = value; bad.append(p)
        p = copy.deepcopy(default); p["sweep"]["start"] = p["sweep"]["end"]; bad.append(p)
        p = copy.deepcopy(default); p["name"] = "不允许\n换行"; bad.append(p)
        p = copy.deepcopy(default); p["name"] = " " * 100 + "水"; bad.append(p)
        for p in bad:
            with self.subTest(project=p), self.assertRaises(model.InputError): model.validate(p)

    def test_reject_ambiguous_and_non_json(self):
        for data in (b'{"schema":1,"schema":2}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'['*10000, b' '*262145):
            with self.subTest(data=data[:40]), self.assertRaises(model.InputError): model.strict_json(data)

    def test_actual_current_arch_wheel_is_hash_pinned(self):
        self.assertTrue(engine.wheel_path().is_file())
        path = engine.wheel_path()
        with patch.object(engine, "WHEELS", {(arch, abi): (filename, "0"*64) for (arch, abi), (filename, _sha) in engine.WHEELS.items()}):
            with self.assertRaises(model.InputError): engine.wheel_path()
        self.assertTrue(path.is_file())


class RealEngineTests(unittest.TestCase):
    def run_project(self, project):
        result = engine.calculate(project)
        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result["input"], project)
        self.assertEqual(result["engine"]["version"], "8.0.0")
        return result

    def test_published_atmospheric_saturation_reference(self):
        # Published CoolProp8 HighLevelAPI reference, not an independent engine:
        # https://coolprop.org/coolprop/HighLevelAPI.html
        result = self.run_project(model.examples()["常压饱和水"])
        sat = result["saturation"]
        self.assertAlmostEqual(sat["temperature_k"], 373.12429584766636, delta=0.02)
        self.assertAlmostEqual(sat["liquid"]["enthalpy_j_kg"], 419057.7330939922, delta=20)
        self.assertAlmostEqual(sat["vapor"]["enthalpy_j_kg"], 2675529.32550072, delta=20)
        self.assertAlmostEqual(sat["latent_heat_j_kg"], 2256471.592406728, delta=2000)
        self.assertEqual(result["state"]["phase"], "饱和液态")

    def test_endpoints_and_mass_weighted_mixture(self):
        p = model.examples()["常压饱和水"]
        p["sweep"]["points"] = 2
        results = []
        for q in (0, 0.5, 1):
            p["state"]["quality"] = q
            results.append(self.run_project(p))
        a, mid, b = [r["state"] for r in results]
        self.assertAlmostEqual(mid["enthalpy_j_kg"], (a["enthalpy_j_kg"] + b["enthalpy_j_kg"])/2, delta=1e-3)
        self.assertAlmostEqual(1/mid["density_kg_m3"], (1/a["density_kg_m3"]+1/b["density_kg_m3"])/2, delta=1e-8)
        self.assertEqual([s["phase"] for s in (a, mid, b)], ["饱和液态", "气液两相", "饱和蒸汽"])

    def test_pt_liquid_vapor_and_saturation_ambiguity(self):
        p = model.examples()["过热蒸汽"]
        p["sweep"]["points"] = 2
        vapor = self.run_project(p)
        self.assertEqual(vapor["state"]["phase"], "气态")
        self.assertIsNone(vapor["state"]["quality"])
        p["state"]["temperature_k"] = 300
        liquid = self.run_project(p)
        self.assertEqual(liquid["state"]["phase"], "液态")
        self.assertGreater(liquid["state"]["density_kg_m3"], 990)
        p["state"]["temperature_k"] = liquid["saturation"]["temperature_k"]
        rejected = engine.calculate(p)
        self.assertFalse(rejected["ok"])
        self.assertIn("P,Q", rejected["error"]["message"])
        self.assertNotIn("state", rejected)

    def test_tq_roundtrip_and_full_bounded_sweep(self):
        p = model.examples()["温度扫描"]
        p["sweep"] = {"variable": "temperature_k", "start":273.16, "end":640, "points":100}
        a = self.run_project(p)
        self.assertEqual(len(a["sweep"]), 100)
        self.assertEqual(a["sweep"][0]["temperature_k"], 273.16)
        self.assertEqual(a["sweep"][-1]["temperature_k"], 640)
        p["state"] = {"pair": "PQ", "pressure_pa": a["state"]["pressure_pa"], "quality": 1}
        p["sweep"]["points"] = 2
        b = self.run_project(p)
        for key in ("temperature_k", "density_kg_m3", "enthalpy_j_kg", "entropy_j_kg_k"):
            self.assertTrue(math.isclose(a["state"][key], b["state"][key], rel_tol=1e-7))

    def test_cancel_then_recovery_and_timeout_then_recovery(self):
        p = model.examples()["常压饱和水"]
        p["sweep"]["points"] = 2
        event = threading.Event(); event.set()
        self.assertEqual(engine.calculate(p, event)["error"]["code"], "cancelled")
        event.clear()
        self.run_project(p)
        with patch.object(engine, "WALL_SECONDS", 0):
            self.assertEqual(engine.calculate(p)["error"]["code"], "timeout")
        self.run_project(p)

    def test_result_association_cannot_be_replayed_for_changed_input(self):
        p = model.examples()["常压饱和水"]
        p["sweep"]["points"] = 2
        r = self.run_project(p)
        p["state"]["pressure_pa"] = 200000
        with self.assertRaises(ValueError): engine._verify(r, p)
        p = copy.deepcopy(r["input"])
        r["saturation"]["latent_heat_j_kg"] *= 2
        with self.assertRaises(ValueError): engine._verify(r, p)

    def test_owned_worker_crash_then_recovery(self):
        project = model.examples()["常压饱和水"]
        project["sweep"]["points"] = 2
        actual_popen = engine.subprocess.Popen
        def fail_owned_child(*args, **kwargs):
            child = actual_popen(*args, **kwargs)
            child.kill()
            return child
        with patch.object(engine.subprocess, "Popen", fail_owned_child):
            failed = engine.calculate(project)
        self.assertFalse(failed["ok"])
        self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in failed["error"]["message"]))
        self.run_project(project)

    def test_cancel_after_extraction_reaps_all_owned_files(self):
        project = model.examples()["常压饱和水"]
        project["sweep"]["points"] = 100
        original_popen = engine.subprocess.Popen
        captured = {}
        cancelled = threading.Event()
        finished = []
        def record_child(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            captured.update(child=child, directory=Path(kwargs["cwd"]))
            return child
        with patch.object(engine.subprocess, "Popen", record_child):
            worker = threading.Thread(target=lambda: finished.append(engine.calculate(project, cancelled)))
            worker.start()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if captured.get("directory") and any(
                        f.is_file() for d in captured["directory"].glob("steam-engine-*") for f in d.rglob("*")):
                    cancelled.set()
                    break
                if finished: break
                time.sleep(.002)
            worker.join(timeout=20)
        self.assertTrue(cancelled.is_set(), "An actual extracted wheel file must be observed before cancellation")
        self.assertFalse(worker.is_alive())
        self.assertEqual(finished[0]["error"]["code"], "cancelled")
        self.assertIsNotNone(captured["child"].poll())
        self.assertFalse(captured["directory"].exists(), "Parent must reap extraction after worker termination")


if __name__ == "__main__": unittest.main(verbosity=2)
