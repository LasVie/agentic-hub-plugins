"""Behavioral regressions for the bounded observing adapter; no network/model."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ENGINE = Path(__file__).resolve().parents[1] / "offline-observing-planner/runtime/engine.py"
SPEC = importlib.util.spec_from_file_location("observing_engine_test", ENGINE)
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
BASE = {"latitude": 1.3521, "longitude": 103.8198, "start_utc": "2026-10-30T12:00:00Z"}


class EngineTests(unittest.TestCase):
    def calculate(self, **updates):
        result = engine.compute_plan({**BASE, **updates})
        self.assertTrue(result["ok"], result)
        return result

    def test_default_plan_has_finite_tracks_and_ordered_events(self):
        result = self.calculate(step_minutes=5)
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(len(result["times"]), 289)
        self.assertEqual(len(result["bodies"]), 7)
        for body in result["bodies"]:
            self.assertEqual(len(body["track"]), 289)
            for point in body["track"]:
                self.assertTrue(-90 <= point["altitude_deg"] <= 90)
                self.assertTrue(0 <= point["azimuth_deg"] < 360)
                self.assertTrue(0 <= point["ra_hours"] < 24)
                self.assertTrue(-90 <= point["dec_deg"] <= 90)
            for direction in ("rise", "set"):
                stamps = [x["utc"] for x in body["rise_set"][direction]]
                self.assertEqual(stamps, sorted(set(stamps)))
                for stamp in stamps:
                    self.assertGreaterEqual(stamp, BASE["start_utc"])
                    self.assertLess(stamp, "2026-10-31T12:00:00Z")
        json.dumps(result, allow_nan=False)

    def test_fixed_offset_changes_labels_not_computation(self):
        a = self.calculate(bodies=["Moon"], duration_hours=1)
        b = self.calculate(bodies=["Moon"], duration_hours=1, display_offset_minutes=840)
        for x, y in zip(a["bodies"][0]["track"], b["bodies"][0]["track"]):
            self.assertEqual(x["altitude_deg"], y["altitude_deg"])
            self.assertEqual(x["azimuth_deg"], y["azimuth_deg"])
            self.assertEqual(x["utc"], y["utc"])
            self.assertNotEqual(x["display"], y["display"])
        self.assertEqual(b["times"][0]["display"], "2026-10-31T02:00:00+14:00")

    def test_shifted_plan_agrees_at_shared_moment(self):
        a = self.calculate(bodies=["Mars", "Mercury"], duration_hours=6, step_minutes=60)
        b = self.calculate(bodies=["Mars", "Mercury"], duration_hours=1, start_utc="2026-10-30T18:00:00Z")
        for x, y in zip(a["bodies"], b["bodies"]):
            self.assertEqual(x["track"][-1], y["track"][0])
            self.assertNotAlmostEqual(x["track"][0]["altitude_deg"], y["track"][0]["altitude_deg"], places=3)

    def test_nonmultiple_interval_keeps_exact_endpoint(self):
        result = self.calculate(bodies=["Venus"], duration_hours=0.75, step_minutes=30)
        self.assertEqual([p["utc"] for p in result["times"]],
                         ["2026-10-30T12:00:00Z", "2026-10-30T12:30:00Z", "2026-10-30T12:45:00Z"])
        self.assertEqual(len(result["sun_track"]), 3)
        self.assertEqual([b["id"] for b in result["bodies"]], ["Venus"])

    def test_one_second_plan_is_supported(self):
        result = self.calculate(bodies=["Sun"], duration_hours=1 / 3600)
        self.assertEqual(result["times"][-1]["utc"], "2026-10-30T12:00:01Z")
        self.assertEqual(len(result["times"]), 2)

    def test_polar_noevent_is_not_fabricated_as_zero_or_infinite(self):
        summer = self.calculate(latitude=80, longitude=0, bodies=["Sun"], start_utc="2026-06-21T00:00:00Z")
        winter = self.calculate(latitude=80, longitude=0, bodies=["Sun"], start_utc="2026-12-21T00:00:00Z")
        for plan in (summer, winter):
            rs = plan["bodies"][0]["rise_set"]
            self.assertEqual(rs["rise"], [])
            self.assertEqual(rs["set"], [])
            self.assertEqual(rs["status"], "no_event_in_interval")
            self.assertIn("本区间", rs["message"])
        self.assertTrue(all(x["altitude_deg"] > 0 for x in summer["sun_track"]))
        self.assertTrue(all(x["altitude_deg"] < 0 for x in winter["sun_track"]))

    def test_twilight_search_roots_match_airless_solar_center(self):
        result = self.calculate(bodies=["Sun"])
        astro = engine._astronomy()
        observer = astro.Observer(BASE["latitude"], BASE["longitude"], 0)
        for twilight in result["twilight"]:
            self.assertEqual(len(twilight["dawn"]), 1)
            self.assertEqual(len(twilight["dusk"]), 1)
            for direction in ("dawn", "dusk"):
                time = astro.Time.Parse(twilight[direction][0]["utc"])
                eq = astro.Equator(astro.Body.Sun, time, observer, True, True)
                hor = astro.Horizon(time, observer, eq.ra, eq.dec, astro.Refraction.Airless)
                self.assertAlmostEqual(hor.altitude, twilight["altitude_deg"], delta=0.001)

    def test_rise_set_is_distinct_from_airless_zero_crossing(self):
        result = self.calculate(bodies=["Sun"])
        astro = engine._astronomy()
        observer = astro.Observer(BASE["latitude"], BASE["longitude"], 0)
        for name in ("rise", "set"):
            time = astro.Time.Parse(result["bodies"][0]["rise_set"][name][0]["utc"])
            eq = astro.Equator(astro.Body.Sun, time, observer, True, True)
            altitude = astro.Horizon(time, observer, eq.ra, eq.dec, astro.Refraction.Airless).altitude
            self.assertTrue(-1.0 < altitude < -0.6, altitude)

    def test_range_edges_complete_and_end_is_checked(self):
        for start in ("2000-01-01T00:00:00Z", "2100-12-31T22:59:59Z"):
            self.calculate(latitude=-80, longitude=180, elevation_m=-500, start_utc=start,
                           duration_hours=1, bodies=["Mercury", "Mars"])
        invalid = engine.compute_plan({**BASE, "start_utc": "2100-12-31T23:59:59Z"})
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["error"]["code"], "out_of_range")

    def test_invalid_values_are_rejected_without_coercion(self):
        cases = [
            {"latitude": True}, {"latitude": "1"}, {"latitude": float("nan")}, {"latitude": 81},
            {"longitude": float("inf")}, {"longitude": 181}, {"longitude": 10**1000},
            {"elevation_m": -501}, {"elevation_m": 10001}, {"step_minutes": 4}, {"step_minutes": 5.1},
            {"duration_hours": 25}, {"duration_hours": 0}, {"duration_hours": 0.0003},
            {"display_offset_minutes": 841}, {"display_offset_minutes": 1.5},
            {"bodies": []}, {"bodies": ["Earth"]}, {"bodies": ["Moon", "Moon"]},
            {"bodies": "Sun"}, {"bodies": [{}]}, {"timezone": "Asia/Singapore"},
            {"start_utc": "2026-10-30T12:00:00+08:00"}, {"start_utc": "2026-02-30T00:00:00Z"},
            {"start_utc": "1999-12-31T23:59:59Z"}, {"start_utc": "9999-12-31T23:59:59Z"},
            {"start_utc": "2026-12-31T23:59:60Z"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                result = engine.compute_plan({**BASE, **changes})
                self.assertFalse(result["ok"])
                self.assertNotEqual(result["error"]["code"], "numerical_error", result)
                self.assertRegex(result["error"]["message"], "[\u4e00-\u9fff]")
                self.assertNotIn("bodies", result)
        for request in (None, [], {}, {"latitude": 1}):
            self.assertFalse(engine.compute_plan(request)["ok"])

    def test_validation_cli_returns_normalized_request_without_computation(self):
        process = subprocess.run([sys.executable, str(ENGINE)],
            input=json.dumps({"action": "validate", "request": BASE}), text=True,
            capture_output=True, check=True, timeout=5)
        result = json.loads(process.stdout)
        self.assertTrue(result["ok"])
        self.assertEqual(result["request"]["duration_hours"], 24)
        self.assertNotIn("times", result)

    def test_cli_rejects_invalid_json_and_input_size(self):
        for payload, code in (("{broken}", "invalid_json"), (" " * 32769, "input_too_large")):
            process = subprocess.run([sys.executable, str(ENGINE)], input=payload, text=True,
                                     capture_output=True, check=True, timeout=5)
            result = json.loads(process.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], code)
        process = subprocess.run([sys.executable, str(ENGINE)],
            input=json.dumps(BASE).encode("utf-16"), capture_output=True, check=True, timeout=5)
        self.assertEqual(json.loads(process.stdout)["error"]["code"], "invalid_json")


if __name__ == "__main__":
    unittest.main()
