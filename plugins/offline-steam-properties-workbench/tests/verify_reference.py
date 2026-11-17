"""Cross-check the actual plugin adapter against public, pinned CoolProp APIs.

IF97 is a different water formulation in the SAME CoolProp binary, not an
independent engine, experimental measurement, or certification. No installation,
download, reference-state mutation, private upstream API, or host is needed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import stat
import sys
import tempfile
import time
import zipfile


ASSET = Path(__file__).resolve().parents[1]
EXPECTED_REVISION = "ae81610e7d23efc57f9d051c8e70a4d66e87537f"
PROPERTIES = {
    "density_kg_m3": "Dmass",
    "enthalpy_j_kg": "Hmass",
    "entropy_j_kg_k": "Smass",
}
PT_CASES = [(300, 100000), (500, 100000), (500, 5000000),
            (800, 5000000), (600, 20000000), (800, 20000000)]
SOURCES = [
    {
        "url": "https://coolprop.org/coolprop/HighLevelAPI.html",
        "sections": ["Versions", "Vapor, Liquid, and Saturation States", "Sample Code"],
        "reviewed_date": "2026-11-16",
        "documented_version": "8.0.0",
        "documented_gitrevision": EXPECTED_REVISION,
        "use": "Published atmospheric saturation values and public PropsSI interface.",
    },
    {
        "url": "https://coolprop.org/fluid_properties/IF97.html",
        "sections": ["IF97 Backend", "IF97 Water Property Examples"],
        "reviewed_date": "2026-11-16",
        "documented_version": "8.0.0",
        "use": "Public IF97::Water backend and published IF97 density example.",
    },
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(payload):
    return {str(path.relative_to(payload)): sha256(path)
            for path in sorted((payload / "runtime").glob("*.py"))}


def load_engine(payload):
    spec = importlib.util.spec_from_file_location("_steam_reference_engine", payload / "runtime/engine.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def extract_reviewed_wheel(wheel, destination):
    # Hash verification is owned by the production engine's wheel_path().
    with zipfile.ZipFile(wheel) as archive:
        members = archive.infolist()
        if len(members) > 1000 or sum(item.file_size for item in members) > 160 * 1024 * 1024:
            raise ValueError("Reviewed wheel exceeds extraction bounds")
        seen = set()
        for item in members:
            path = Path(item.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in item.filename
                    or stat.S_ISLNK(item.external_attr >> 16) or item.filename in seen):
                raise ValueError("Unsafe wheel member")
            seen.add(item.filename)
        archive.extractall(destination)


def project(state):
    return {"schema": "steam-properties/v1", "name": "水与蒸汽物性数值交叉验证", "state": state,
            "sweep": {"variable": "pressure_pa", "start": 10000, "end": 2000000, "points": 2}}


def run(payload, report):
    engine = load_engine(payload)
    wheel = engine.wheel_path()  # Includes exact recorded SHA-256 verification.
    hashes = source_hashes(payload)
    report["environment"] = {
        "python_executable": sys.executable, "python_version": sys.version,
        "platform": platform.platform(), "machine": platform.machine(),
        "isolated_mode": bool(sys.flags.isolated), "write_bytecode": not sys.dont_write_bytecode,
    }
    report["subject"] = {"payload": str(payload), "runtime_sha256_before": hashes,
                         "wheel_filename": wheel.name, "wheel_sha256": sha256(wheel)}
    report["checks"] = checks = []
    cache = {}

    def compare(label, actual, expected, *, rel_tol=0, abs_tol=0, context=None):
        finite = all(isinstance(v, (int, float)) and math.isfinite(v) for v in (actual, expected))
        difference = abs(actual - expected) if finite else None
        checks.append({"check": label, "context": context or {}, "actual": actual, "expected": expected,
                       "absolute_error": difference,
                       "relative_error": difference / abs(expected) if finite and expected else None,
                       "relative_tolerance": rel_tol, "absolute_tolerance": abs_tol,
                       "passed": finite and math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol)})

    def calculate(state):
        key = json.dumps(state, sort_keys=True)
        if key not in cache:
            request = project(state)
            result = engine.calculate(request)
            if result.get("ok") is not True:
                raise RuntimeError(f"Plugin calculation failed for {state}: {result}")
            if result["input"] != request or result["engine"] != {
                "name": "CoolProp", "version": "8.0.0", "backend": "HEOS", "fluid": "Water"
            }:
                raise RuntimeError("Plugin result identity differs from requested input/engine")
            cache[key] = result
        return cache[key]

    with tempfile.TemporaryDirectory(prefix="main3-steam-reference-") as directory:
        extracted = Path(directory)
        extract_reviewed_wheel(wheel, extracted)
        if "CoolProp" in sys.modules:
            raise RuntimeError("Reference process must not preload another CoolProp installation")
        sys.path.insert(0, directory)
        try:
            import numpy
            import CoolProp
            import CoolProp.CoolProp as CP

            binary = Path(CP.__file__).resolve()
            if not binary.is_relative_to(extracted.resolve()):
                raise RuntimeError("Reference binary did not load from the reviewed wheel")
            if CoolProp.__version__ != "8.0.0" or CoolProp.__gitrevision__ != EXPECTED_REVISION:
                raise RuntimeError("Unexpected CoolProp version/revision")
            report["environment"].update(numpy_version=numpy.__version__, coolprop_version=CoolProp.__version__,
                                          coolprop_gitrevision=CoolProp.__gitrevision__)
            report["subject"].update(native_binary_member=str(binary.relative_to(extracted.resolve())),
                                      native_binary_sha256=sha256(binary))

            # Six predeclared states span compressed liquid and gas, well away
            # from saturation. The 0.5% budget is a model-agreement regression
            # threshold, not a universal thermodynamic uncertainty guarantee.
            for temperature, pressure in PT_CASES:
                state = {"pair": "PT", "pressure_pa": pressure, "temperature_k": temperature}
                actual = calculate(state)["state"]
                for field, output in PROPERTIES.items():
                    reference = CP.PropsSI(output, "P", pressure, "T", temperature, "IF97::Water")
                    compare("HEOS versus IF97: " + field, actual[field], reference, rel_tol=0.005, context=state)

            # This one hard-coded public example confirms the comparison API's
            # identity as well; it is not used to calibrate the comparisons.
            compare("Published IF97 density at 500 K and 101325 Pa",
                    CP.PropsSI("Dmass", "T", 500, "P", 101325, "IF97::Water"),
                    0.4409206435977277, rel_tol=1e-10, abs_tol=1e-12)

            # Numeric reference values only, from the reviewed official 8.0.0
            # page above. These verify integration with the published model.
            atmospheric = calculate({"pair": "PQ", "pressure_pa": 101325, "quality": 0})["saturation"]
            for label, actual, expected, tolerance in [
                ("temperature_k", atmospheric["temperature_k"], 373.12429584766636, 0.02),
                ("liquid_enthalpy_j_kg", atmospheric["liquid"]["enthalpy_j_kg"], 419057.7330939922, 20),
                ("vapor_enthalpy_j_kg", atmospheric["vapor"]["enthalpy_j_kg"], 2675529.32550072, 20),
                ("latent_heat_j_kg", atmospheric["latent_heat_j_kg"], 2256471.592406728, 20),
            ]:
                compare("Published HEOS atmospheric saturation: " + label, actual, expected, abs_tol=tolerance)

            # Independent input paths through the actual subprocess adapter;
            # numerical inversion is expected to agree much more closely than
            # two different formulations. Include both saturation endpoints.
            for pressure, quality in [(10000, 0), (101325, 1), (1000000, 0), (10000000, 1)]:
                first = calculate({"pair": "PQ", "pressure_pa": pressure, "quality": quality})
                second = calculate({"pair": "TQ", "temperature_k": first["state"]["temperature_k"], "quality": quality})
                for field in ("pressure_pa", "temperature_k", *PROPERTIES):
                    compare("PQ to TQ inverse: " + field, second["state"][field], first["state"][field],
                            rel_tol=1e-8, abs_tol=1e-7, context={"pressure_pa": pressure, "quality": quality})

            # Endpoint values come from separate real adapter calls. Enthalpy,
            # entropy and specific volume are mass-weighted; density is not.
            for pressure in (101325, 2000000):
                liquid = calculate({"pair": "PQ", "pressure_pa": pressure, "quality": 0})
                vapor = calculate({"pair": "PQ", "pressure_pa": pressure, "quality": 1})
                a, b = liquid["state"], vapor["state"]
                for quality in (0.25, 0.75):
                    mixture = calculate({"pair": "PQ", "pressure_pa": pressure, "quality": quality})["state"]
                    context = {"pressure_pa": pressure, "quality": quality}
                    for field in ("enthalpy_j_kg", "entropy_j_kg_k"):
                        compare("Endpoint lever rule: " + field, mixture[field],
                                (1-quality)*a[field] + quality*b[field], rel_tol=1e-8, abs_tol=1e-7, context=context)
                    compare("Endpoint lever rule: specific_volume_m3_kg", 1/mixture["density_kg_m3"],
                            (1-quality)/a["density_kg_m3"] + quality/b["density_kg_m3"],
                            rel_tol=1e-8, abs_tol=1e-12, context=context)
                compare("Latent heat equals separately computed endpoint enthalpy difference",
                        liquid["saturation"]["latent_heat_j_kg"], b["enthalpy_j_kg"] - a["enthalpy_j_kg"],
                        rel_tol=1e-8, abs_tol=1e-6, context={"pressure_pa": pressure})
        finally:
            sys.path.remove(directory)

    report["subject"]["runtime_sha256_after"] = source_hashes(payload)
    report["subject"]["runtime_unchanged"] = hashes == report["subject"]["runtime_sha256_after"]
    report["plugin_calculation_count"] = len(cache)
    report["passed"] = all(item["passed"] for item in checks) and report["subject"]["runtime_unchanged"]
    report["summary"] = {"checks": len(checks), "passed": sum(item["passed"] for item in checks),
                         "max_heos_if97_relative_error": max(item["relative_error"] for item in checks
                                                              if item["check"].startswith("HEOS versus IF97:"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, default=ASSET / "offline-steam-properties-workbench")
    parser.add_argument("--output", type=Path, default=ASSET / "tests/records/reference-crosscheck.json")
    args = parser.parse_args()
    started = time.monotonic()
    report = {
        "record_schema": "steam-reference-crosscheck/v1", "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
        "test_script_sha256": sha256(Path(__file__).resolve()), "sources": SOURCES,
        "scope": "Actual plugin HEOS adapter versus alternative IF97 formulation in the same reviewed CoolProp binary; published examples and mathematical invariants.",
        "limitations": "Not an independent engine, measurement dataset, exhaustive range validation, engineering certification, or user manual test. No new dependencies or host changes.",
        "passed": False,
    }
    try:
        run(args.payload.resolve(), report)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "summary": report.get("summary"),
                      "error": report.get("error"), "record": str(args.output)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
