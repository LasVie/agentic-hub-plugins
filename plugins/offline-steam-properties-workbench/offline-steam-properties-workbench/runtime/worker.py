"""Fixed HEOS::Water public API adapter. No network, user code or configuration."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import resource
import stat
import sys
import tempfile
import zipfile

resource.setrlimit(resource.RLIMIT_CPU, (12, 13))
resource.setrlimit(resource.RLIMIT_FSIZE, (96 * 1024 * 1024, 96 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("_steam_worker_engine", ROOT / "runtime/engine.py")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
model = engine.model


def compute(CP, project):
    def prop(output, key, value, other, number):
        result = float(CP.PropsSI(output, key, value, other, number, "HEOS::Water"))
        if not math.isfinite(result): raise ValueError("nonfinite")
        return result
    def saturation(key, value):
        def side(q):
            return {"density_kg_m3": prop("Dmass", key, value, "Q", q),
                    "enthalpy_j_kg": prop("Hmass", key, value, "Q", q),
                    "entropy_j_kg_k": prop("Smass", key, value, "Q", q)}
        liquid, vapor = side(0), side(1)
        return {"pressure_pa": value if key == "P" else prop("P", key, value, "Q", 0),
                "temperature_k": value if key == "T" else prop("T", key, value, "Q", 0),
                "liquid": liquid, "vapor": vapor,
                "latent_heat_j_kg": vapor["enthalpy_j_kg"] - liquid["enthalpy_j_kg"]}
    requested = project["state"]
    pair = requested["pair"]
    key, val = ("T", requested["temperature_k"]) if pair == "TQ" else ("P", requested["pressure_pa"])
    other, num = ("T", requested["temperature_k"]) if pair == "PT" else ("Q", requested["quality"])
    phase_raw = CP.PhaseSI(key, val, other, num, "HEOS::Water")
    if phase_raw.startswith("unknown") or phase_raw not in {"liquid", "gas", "twophase", "supercritical", "supercritical_liquid", "supercritical_gas", "critical_point"}:
        raise ValueError("unknown phase")
    q = prop("Q", key, val, other, num)
    q = q if 0 <= q <= 1 else None
    labels = {"liquid": "液态", "gas": "气态", "twophase": "气液两相",
              "supercritical": "超临界流体", "supercritical_liquid": "超临界液态区",
              "supercritical_gas": "超临界气态区", "critical_point": "临界点"}
    phase = "饱和液态" if q == 0 else "饱和蒸汽" if q == 1 else labels[phase_raw]
    state = {"pressure_pa": prop("P", key, val, other, num),
             "temperature_k": prop("T", key, val, other, num),
             "density_kg_m3": prop("Dmass", key, val, other, num),
             "enthalpy_j_kg": prop("Hmass", key, val, other, num),
             "entropy_j_kg_k": prop("Smass", key, val, other, num), "phase": phase, "quality": q}
    sat = saturation(key, val)
    sweep = project["sweep"]
    points = []
    for i in range(sweep["points"]):
        value = sweep["start"] + (sweep["end"] - sweep["start"]) * i / (sweep["points"] - 1)
        data = saturation("P" if sweep["variable"] == "pressure_pa" else "T", value)
        points.append({"pressure_pa": data["pressure_pa"], "temperature_k": data["temperature_k"],
                       "liquid_density_kg_m3": data["liquid"]["density_kg_m3"],
                       "vapor_density_kg_m3": data["vapor"]["density_kg_m3"],
                       "liquid_enthalpy_j_kg": data["liquid"]["enthalpy_j_kg"],
                       "vapor_enthalpy_j_kg": data["vapor"]["enthalpy_j_kg"],
                       "latent_heat_j_kg": data["latent_heat_j_kg"]})
    return {"ok": True, "version": model.VERSION,
            "engine": {"name": "CoolProp", "version": "8.0.0", "backend": "HEOS", "fluid": "Water"},
            "input": project, "input_sha256": model.fingerprint(project), "state": state,
            "saturation": sat, "sweep": points}


def main():
    data = sys.stdin.buffer.read(model.MAX_INPUT + 1)
    if len(data) > model.MAX_INPUT: raise ValueError("input limit")
    project = model.validate(model.strict_json(data))
    wheel = engine.wheel_path()
    # The parent owns cwd and reaps its complete tree even when this worker is
    # killed before its Python finally handlers can run (cancel/crash/timeout).
    with tempfile.TemporaryDirectory(prefix="steam-engine-", dir=Path.cwd()) as directory:
        dest = Path(directory)
        # The entire immutable official wheel is retained and hashed; extract
        # only in this process's private disposable directory, never site-packages.
        with zipfile.ZipFile(wheel) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(i.file_size for i in entries) > 160 * 1024 * 1024:
                raise ValueError("wheel limits")
            for item in entries:
                path = Path(item.filename)
                if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError("wheel path")
            archive.extractall(dest)
        sys.path.insert(0, str(dest))
        import numpy
        if tuple(int(x) for x in numpy.__version__.split(".")[:2]) < (1, 20):
            raise ImportError("numpy version")
        import CoolProp
        import CoolProp.CoolProp as CP
        if CoolProp.__version__ != "8.0.0" or CoolProp.__gitrevision__ != "ae81610e7d23efc57f9d051c8e70a4d66e87537f":
            raise ImportError("engine revision")
        result = compute(CP, project)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print(json.dumps(engine.failure("无法加载随包引擎或 NumPy。", "engine_unavailable"), ensure_ascii=False))
    except Exception:
        print(json.dumps(engine.failure("该状态无法计算，请核对数值或改用饱和输入对。", "state_unavailable"), ensure_ascii=False))
