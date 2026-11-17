"""Run only the bundled, hash-pinned CoolProp wheel in an owned bounded child."""
from __future__ import annotations

import hashlib
import importlib.util
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
_name = "_steam_model_" + str(abs(hash(str(ROOT))))
if _name not in sys.modules:
    spec = importlib.util.spec_from_file_location(_name, ROOT / "runtime/model.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_name] = module
    spec.loader.exec_module(module)
model = sys.modules[_name]
WALL_SECONDS = 15
MAX_OUTPUT = 512 * 1024
WHEELS = {
    ("arm64", "cp311"): ("coolprop-8.0.0-cp311-cp311-macosx_11_0_arm64.whl", "ad8bca80518c9777e81dd861fc274e4a56115712b54af7413504249e8fe83078"),
    ("x86_64", "cp311"): ("coolprop-8.0.0-cp311-cp311-macosx_11_0_x86_64.whl", "7b8e17dd611b6e1a0b91bec887c84056c4492dcb033fda4b3e93a6b77dc9e074"),
    ("arm64", "abi3"): ("coolprop-8.0.0-cp312-abi3-macosx_11_0_arm64.whl", "46de36f51330ce8c7f8384a7360e1058739d20604736158aac6bd2abf6ae26bd"),
    ("x86_64", "abi3"): ("coolprop-8.0.0-cp312-abi3-macosx_11_0_x86_64.whl", "939803aa9d849961e76512d4c3d60b15c25802c75cbecc801892edb3b023f200"),
}


def failure(message, code="invalid_input", **extra):
    return {"ok": False, "version": model.VERSION, "error": {"code": code, "message": message}, **extra}


def wheel_path():
    if platform.system() != "Darwin" or platform.machine() not in {"arm64", "x86_64"}:
        raise model.InputError("此包仅支持 macOS 11+ 的 Intel 或 Apple Silicon；当前系统不受支持。")
    if (sys.implementation.name != "cpython" or sys.version_info[:2] < (3, 11)
            or sys.version_info[0] != 3 or sysconfig.get_config_var("Py_GIL_DISABLED")):
        raise model.InputError("此包需要 WorkSwarm 使用 CPython 3.11+，并预先安装 NumPy 1.20 或更高版本；插件不会修改宿主依赖。")
    if int(platform.mac_ver()[0].split(".")[0]) < 11:
        raise model.InputError("此包需要 macOS 11 或更高版本。")
    filename, expected = WHEELS[(platform.machine(), "cp311" if sys.version_info[:2] == (3, 11) else "abi3")]
    path = ROOT / "vendor/coolprop" / filename
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise model.InputError("随包 CoolProp 引擎缺失或路径不安全，请重新安装原始包。")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise model.InputError("随包 CoolProp 引擎校验失败，不会执行变化后的文件。")
    if not Path("/usr/bin/sandbox-exec").is_file():
        raise model.InputError("系统缺少计算子进程所需的网络隔离组件。")
    return path


def _verify(result, project):
    if not isinstance(result, dict) or result.get("ok") is not True:
        if isinstance(result, dict) and result.get("error", {}).get("code") == "engine_unavailable":
            raise model.InputError("无法加载随包 CoolProp 8.0.0。请检查 CPython 3.11+、NumPy 1.20+ 与插件完整性。")
        raise model.InputError("引擎未能计算该状态。饱和线附近的 P,T 状态请改用 P,Q 或 T,Q；请核对输入范围。")
    if result.get("input") != project or result.get("input_sha256") != model.fingerprint(project):
        raise ValueError("input association")
    if result.get("engine") != {"name": "CoolProp", "version": "8.0.0", "backend": "HEOS", "fluid": "Water"}:
        raise ValueError("engine identity")
    def finite(value):
        if isinstance(value, dict):
            for v in value.values(): finite(v)
        elif isinstance(value, list):
            for v in value: finite(v)
        elif isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
            raise ValueError("nonfinite result")
    finite(result)
    points = result["sweep"]
    if len(points) != project["sweep"]["points"]:
        raise ValueError("point count")
    for saturation in [result["saturation"], *points]:
        if "liquid" in saturation:
            liquid, vapor = saturation["liquid"], saturation["vapor"]
            hl, hv = liquid["enthalpy_j_kg"], vapor["enthalpy_j_kg"]
            rl, rv = liquid["density_kg_m3"], vapor["density_kg_m3"]
        else:
            hl, hv = saturation["liquid_enthalpy_j_kg"], saturation["vapor_enthalpy_j_kg"]
            rl, rv = saturation["liquid_density_kg_m3"], saturation["vapor_density_kg_m3"]
        latent = saturation["latent_heat_j_kg"]
        if not (hv > hl and rl > rv > 0 and latent > 0 and abs((hv - hl) - latent) < 1e-6):
            raise ValueError("saturation consistency")
    var = project["sweep"]["variable"]
    start, end = project["sweep"]["start"], project["sweep"]["end"]
    for i, point in enumerate(points):
        expected = start + (end - start) * i / (len(points) - 1)
        if not math.isclose(point[var], expected, rel_tol=1e-8, abs_tol=1e-6):
            raise ValueError("sweep association")
        if i and not (point["pressure_pa"] > points[i-1]["pressure_pa"] and point["temperature_k"] > points[i-1]["temperature_k"]):
            raise ValueError("saturation monotonicity")
    state = result["state"]
    for key in ("pressure_pa", "temperature_k", "density_kg_m3"):
        if state[key] <= 0: raise ValueError("positive state")
    for key, value in project["state"].items():
        if key != "pair" and not math.isclose(state[key], value, rel_tol=1e-8, abs_tol=1e-6):
            raise ValueError("state association")
    q = state["quality"]
    if q is not None:
        sat = result["saturation"]
        predicted_h = (1-q) * sat["liquid"]["enthalpy_j_kg"] + q * sat["vapor"]["enthalpy_j_kg"]
        predicted_rho = 1 / ((1-q) / sat["liquid"]["density_kg_m3"] + q / sat["vapor"]["density_kg_m3"])
        if not math.isclose(state["enthalpy_j_kg"], predicted_h, rel_tol=1e-7, abs_tol=1e-3) or not math.isclose(state["density_kg_m3"], predicted_rho, rel_tol=1e-7):
            raise ValueError("mixture consistency")
    return result


def calculate(project, cancelled=None):
    try:
        project = model.validate(project)
        if cancelled is not None and cancelled.is_set():
            return failure("计算已取消。", "cancelled", cancelled=True)
        wheel_path()
    except (model.InputError, OSError, ValueError) as exc:
        return failure(str(exc) if isinstance(exc, model.InputError) else "无法验证随包引擎。", "engine_unavailable" if not isinstance(exc, model.InputError) else "invalid_input")
    env = {k: os.environ[k] for k in ("LANG", "LC_ALL", "LC_CTYPE", "TMPDIR") if k in os.environ}
    env.update(PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with tempfile.TemporaryDirectory(prefix="steam-properties-") as directory:
        command = ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)",
                   sys.executable, "-I", "-B", str(ROOT / "runtime/worker.py")]
        try:
            process = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            return failure("无法启动本地物性计算子进程。", "engine_unavailable")
        output = bytearray()
        overflow = threading.Event()
        def read_output():
            while True:
                chunk = process.stdout.read(4096)
                if not chunk: break
                if len(output) + len(chunk) > MAX_OUTPUT:
                    overflow.set()
                    break
                output.extend(chunk)
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        started = time.monotonic()
        try:
            process.stdin.write(model.encode(project))
            process.stdin.close()
            while process.poll() is None:
                if cancelled is not None and cancelled.is_set():
                    return failure("计算已取消。", "cancelled", cancelled=True)
                if overflow.is_set():
                    return failure("引擎输出超过安全上限，已停止本次计算。", "invalid_result")
                if time.monotonic() - started > WALL_SECONDS:
                    return failure("物性计算超时，已停止本次子进程；可以减少扫描点后重试。", "timeout")
                time.sleep(0.02)
            reader.join(timeout=1)
            if cancelled is not None and cancelled.is_set():
                return failure("计算已取消。", "cancelled", cancelled=True)
            if process.returncode != 0 or reader.is_alive() or overflow.is_set():
                return failure("物性计算子进程未正常完成；请检查安装或减少扫描点后重试。", "engine_failed")
            result = _verify(model.strict_json(bytes(output)), project)
            return result
        except model.InputError as exc:
            return failure(str(exc), "state_unavailable")
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            return failure("本次物性结果未通过输入、有限数值及饱和关系校验，未显示结果。", "invalid_result")
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=0.6)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            reader.join(timeout=1)
            process.stdout.close()
            if not process.stdin.closed: process.stdin.close()
