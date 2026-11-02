"""Offline comparisons with fixed, independent NASA/JPL and USNO numeric facts.

No network access is performed by these tests. See fixtures/README.md for
coordinate/time conventions, source captures, and the explicit 2100 Moon limit.
"""
import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).with_name("fixtures")
spec = importlib.util.spec_from_file_location(
    "observing_reference_engine", ROOT / "offline-observing-planner/runtime/engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
HORIZONS = json.loads((FIXTURES / "horizons.json").read_text())
USNO = json.loads((FIXTURES / "usno_events.json").read_text())


def separation_arcmin(actual, expected):
    """Great-circle separation; avoids meaningless raw azimuth error at zenith."""
    a1, a2 = map(math.radians, (actual["altitude_deg"], expected["altitude_deg"]))
    dz = math.radians(actual["azimuth_deg"] - expected["azimuth_deg"])
    hav = math.sin((a1 - a2) / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dz / 2) ** 2
    return math.degrees(2 * math.asin(math.sqrt(max(0, min(1, hav))))) * 60


def position(case, expected):
    result = engine.compute_plan({
        "latitude": case["latitude"], "longitude": case["longitude"],
        "elevation_m": case["elevation_m"], "start_utc": expected["utc"],
        "duration_hours": 1 / 60, "step_minutes": 5, "bodies": [case["body"]],
    })
    if not result["ok"]:
        raise AssertionError(result)
    return result["bodies"][0]["track"][0]


class IndependentReferenceTests(unittest.TestCase):
    def assert_group(self, prefix):
        count = 0
        for case in HORIZONS["cases"]:
            if not case["id"].startswith(prefix):
                continue
            for expected in case["expected"]:
                with self.subTest(case=case["id"], utc=expected["utc"]):
                    actual = position(case, expected)
                    self.assertEqual(actual["utc"], expected["utc"])
                    self.assertLessEqual(separation_arcmin(actual, expected),
                                         expected["separation_tolerance_arcmin"])
                    count += 1
        return count

    def test_all_seven_bodies_singapore_2000_2026_2100(self):
        # The one 2100 Moon case has a documented 2arcmin rather than1arcmin budget.
        self.assertEqual(self.assert_group("singapore_"), 28)

    def test_mercury_mars_reported_issue383_coordinates_time(self):
        # Independent JPL positions, not the contradictory numbers in the issue PDF.
        self.assertEqual(self.assert_group("issue383_"), 2)

    def test_polar_airless_positions_summer_and_winter(self):
        self.assertEqual(self.assert_group("polar_"), 8)

    def test_far_future_moon_time_scale_difference_is_explicit(self):
        case = next(c for c in HORIZONS["cases"] if c["id"] == "singapore_moon")
        expected = next(e for e in case["expected"] if e["utc"].startswith("2100-"))
        default_error = separation_arcmin(position(case, expected), expected)
        # Preserve the known >1arcmin discrepancy as an honest regression, not a
        # silently weakened blanket accuracy promise or production correction.
        self.assertGreater(default_error, 1)
        self.assertLess(default_error, 2)
        astro = engine._astronomy()
        default = astro.Time.Parse(expected["utc"])
        self.assertGreater((default.tt - default.ut) * 86400, 200)
        matched = astro.Time(default.ut, default.ut +
                             HORIZONS["future_moon_diagnostic"]["jpl_tdb_minus_utc_seconds"] / 86400)
        observer = astro.Observer(case["latitude"], case["longitude"], case["elevation_m"])
        eq = astro.Equator(astro.Body.Moon, matched, observer, True, True)
        hor = astro.Horizon(matched, observer, eq.ra, eq.dec, astro.Refraction.Airless)
        diagnostic_error = separation_arcmin({"altitude_deg": hor.altitude,
                                              "azimuth_deg": hor.azimuth}, expected)
        self.assertLess(diagnostic_error, 0.1)
        self.assertLess(diagnostic_error, default_error / 20)

    def test_usno_sun_moon_rise_set_and_civil_twilight(self):
        result = engine.compute_plan({"latitude": USNO["latitude"], "longitude": USNO["longitude"],
            "elevation_m": 0, "start_utc": USNO["start_utc"], "duration_hours": 24,
            "step_minutes": 60, "bodies": ["Sun", "Moon"]})
        self.assertTrue(result["ok"], result)
        bodies = {b["id"]: b for b in result["bodies"]}
        civil = next(t for t in result["twilight"] if t["kind"] == "civil")
        for event in USNO["events"]:
            with self.subTest(event=event):
                if event["kind"].startswith("civil_"):
                    values = civil[event["kind"].split("_")[1]]
                else:
                    values = bodies[event["body"]]["rise_set"][event["kind"]]
                self.assertEqual(len(values), 1)
                parsed = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
                self.assertLessEqual(abs((parsed(values[0]["utc"]) - parsed(event["utc"])).total_seconds()),
                                     USNO["tolerance_seconds"])


if __name__ == "__main__":
    unittest.main()
