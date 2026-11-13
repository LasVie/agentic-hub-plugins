"""HiGHS CLI adapter: generated numeric LP, bounded owned child, verified output."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
_name = "_offline_allocation_model_" + str(abs(hash(str(ROOT))))
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, ROOT / "runtime" / "model.py")
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
model = sys.modules[_name]
ENGINE_VERSION = "HiGHS 1.16.0"
WALL_SECONDS = 8
MAX_OUTPUT = 1024 * 1024
BINARY = ROOT / "vendor" / "highs" / "bin" / "highs"
BINARY_SHA256 = "c2f3c6d27708eac52d9c16b9306996c2511780e49c87b292d8617572593eb109"


def failure(message, code="invalid_input", **extra):
    return {"ok": False, "version": model.VERSION,
            "error": {"code": code, "message": message}, **extra}


def lp_text(project):
    # Original names are data only. Generated identifiers and bounded integers
    # make LP directives, file paths and command-line option injection impossible.
    jobs = project["jobs"]
    term = lambda values: " + ".join(f"{n} x{i}" for i, n in enumerate(values))
    lines = ["Maximize", " value: " + term([j["value"] for j in jobs]), "Subject To"]
    for index, resource in enumerate(project["resources"]):
        lines.append(f" r{index}: " + term([j["uses"][resource["id"]] for j in jobs])
                     + f" <= {resource['capacity']}")
    lines.append(" count: " + term([1] * len(jobs)) + f" >= {project['min_jobs']}")
    lines.extend(["Binary", " " + " ".join(f"x{i}" for i in range(len(jobs))), "End", ""])
    return "\n".join(lines)


def binary_check():
    if platform.system() != "Darwin":
        raise model.InputError("当前安装包仅支持 macOS 26+（Intel 或 Apple Silicon），不支持此系统。")
    try:
        if int(platform.mac_ver()[0].split(".")[0]) < 26:
            raise model.InputError("当前 HiGHS 二进制需要 macOS 26 或更高版本。")
        if any(p.is_symlink() for p in (BINARY, *BINARY.parents)) or not BINARY.is_file():
            raise model.InputError("HiGHS 引擎缺失或不是插件内的真实文件。")
        if hashlib.sha256(BINARY.read_bytes()).hexdigest() != BINARY_SHA256:
            raise model.InputError("HiGHS 引擎校验失败；请重新安装原始包，不会运行已变化的文件。")
        if not Path("/usr/bin/sandbox-exec").is_file():
            raise model.InputError("系统缺少本地求解进程所需的网络隔离组件。")
        # Supported ZIP importers may not retain executable bits. Change only
        # this hash-verified plugin-owned file, never a system installation.
        if not os.access(BINARY, os.X_OK):
            BINARY.chmod(0o755)
    except (OSError, KeyError, ValueError) as exc:
        if isinstance(exc, model.InputError):
            raise
        raise model.InputError("无法验证本地 HiGHS 引擎和平台要求。") from exc


def parse_solution(raw, project):
    lines = raw.splitlines()
    if not lines or lines[0] != "Model status" or len(lines) < 2:
        raise model.InputError("求解器没有返回可核验的模型状态。")
    status = lines[1].strip()
    known = {"Optimal", "Infeasible", "Time limit reached", "Iteration limit reached",
             "Solution limit reached", "Unknown", "Unbounded or infeasible", "Interrupted",
             "Objective bound reached", "Objective target reached", "Memory limit reached"}
    if status not in known:
        raise model.InputError("求解器返回了不支持的状态；本次不提供分配结论。")
    try:
        primal_index = lines.index("# Primal solution values")
        primal = lines[primal_index + 1].strip()
    except (ValueError, IndexError):
        primal = "None"
    selected = None
    objective = None
    if primal == "Feasible":
        matches = [i for i, line in enumerate(lines) if line == f"# Columns {len(project['jobs'])}"]
        if len(matches) != 1:
            raise model.InputError("求解器作业变量数量与输入不一致。")
        values = {}
        for line in lines[matches[0] + 1:matches[0] + 1 + len(project["jobs"])]:
            fields = line.split()
            if len(fields) != 2 or not re.fullmatch(r"x[0-9]+", fields[0]) or fields[0] in values:
                raise model.InputError("求解器作业变量格式无效。")
            try:
                value = float(fields[1])
            except ValueError as exc:
                raise model.InputError("求解器返回了无效数值。") from exc
            if not math.isfinite(value) or min(abs(value), abs(value - 1)) > 1e-6:
                raise model.InputError("求解结果未满足作业必须整项选择的约束。")
            values[fields[0]] = int(value >= 0.5)
        if set(values) != {f"x{i}" for i in range(len(project["jobs"]))}:
            raise model.InputError("求解结果缺少作业变量。")
        selected = [j["id"] for i, j in enumerate(project["jobs"]) if values[f"x{i}"]]
        if len(selected) < project["min_jobs"]:
            raise model.InputError("求解结果不满足最少作业数。")
        for resource in project["resources"]:
            used = sum(j["uses"][resource["id"]] for j in project["jobs"] if j["id"] in selected)
            if used > resource["capacity"]:
                raise model.InputError("求解结果超过资源容量，已拒绝显示。")
        objective = sum(j["value"] for j in project["jobs"] if j["id"] in selected)
        objective_lines = [line for line in lines if line.startswith("Objective ")]
        if len(objective_lines) != 1:
            raise model.InputError("求解结果缺少唯一目标值。")
        try:
            reported = float(objective_lines[0].split()[1])
        except (ValueError, IndexError) as exc:
            raise model.InputError("求解器目标值无效。") from exc
        if not math.isfinite(reported) or abs(reported - objective) > 1e-5:
            raise model.InputError("求解器目标值与独立复算不一致。")
    if status == "Optimal" and selected is None:
        raise model.InputError("求解器声称最优但没有可行解，已拒绝此结论。")
    if status in {"Infeasible", "Unbounded or infeasible"} and selected is not None:
        raise model.InputError("求解器状态与可行解互相矛盾。")
    bound = gap = None
    if status == "Optimal":
        for prefix in ("Objective_bound ", "MIP_rel_gap "):
            found = [line[len(prefix):].strip() for line in lines if line.startswith(prefix)]
            if len(found) != 1:
                raise model.InputError("最优结果缺少目标界或间隙。")
            value = float(found[0])
            if not math.isfinite(value):
                raise model.InputError("最优结果的目标界或间隙无效。")
            if prefix.startswith("Objective_bound"):
                bound = value
            else:
                gap = value
        if abs(bound - objective) > 1e-5 or gap != 0:
            raise model.InputError("尚未得到零间隙最优结果，不能标记为最优。")
    state = "optimal" if status == "Optimal" else "infeasible" if status == "Infeasible" else "feasible" if selected is not None else "limit"
    messages = {"optimal": "求解完成：求解器报告零间隙最优解，作业与资源约束已独立复算。",
                "infeasible": "当前容量与最少作业数无法同时满足，求解器报告不可行。",
                "feasible": "已找到可行方案，但尚未证明最优；请勿当作最优结果。",
                "limit": "未得到可用的可行解或确定结论；请减少作业或修改容量后重试。"}
    return {"status": state, "message": messages[state], "selected_ids": selected or [],
            "objective": objective, "optimality_proven": state == "optimal", "dual_bound": bound,
            "mip_gap": gap, "solver_status": status, "constraints_verified": selected is not None,
            "engine_version": ENGINE_VERSION,
            "usage": [{"resource_id": r["id"], "name": r["name"], "capacity": r["capacity"],
                       "used": sum(j["uses"][r["id"]] for j in project["jobs"] if selected is not None and j["id"] in selected) if selected is not None else None}
                      for r in project["resources"]],
            "jobs": [{**j, "selected": j["id"] in selected if selected is not None else False} for j in project["jobs"]]}


def csv_result(result):
    def safe(value):
        return "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["作业标识", "作业名称", "已选择", "价值", "求解结论"] + [safe(r["name"]) for r in result["usage"]])
    label = "求解器报告最优" if result["status"] == "optimal" else "可行但未证明最优"
    for j in result["jobs"]:
        writer.writerow([safe(j["id"]), safe(j["name"]), "是" if j["selected"] else "否", j["value"], label]
                        + [j["uses"][r["resource_id"]] for r in result["usage"]])
    return stream.getvalue()


def calculate(project, cancelled=None):
    try:
        project = model.validate(project)
        if cancelled is not None and cancelled.is_set():
            return failure("计算已取消。", "cancelled", cancelled=True)
        binary_check()
    except model.InputError as exc:
        return failure(str(exc))
    if cancelled is not None and cancelled.is_set():
        return failure("计算已取消。", "cancelled", cancelled=True)
    started = time.monotonic()
    environment = {key: os.environ[key] for key in ("LANG", "LC_ALL", "LC_CTYPE", "TMPDIR") if key in os.environ}
    environment.update(PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    with tempfile.TemporaryDirectory(prefix="allocation-solve-") as directory:
        path = Path(directory)
        (path / "model.lp").write_text(lp_text(project), encoding="ascii")
        (path / "options.txt").write_text("threads = 1\nparallel = off\nrandom_seed = 0\ntime_limit = 5\nmip_rel_gap = 0\nmip_abs_gap = 0\nwrite_solution_to_file = true\nwrite_solution_style = 0\n", encoding="ascii")
        try:
            process = subprocess.Popen([sys.executable, "-I", "-B", str(ROOT / "runtime" / "solver_exec.py")],
                                       cwd=directory, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError:
            return failure("无法启动本机 HiGHS 求解进程。", "engine_unavailable")
        output = bytearray()
        overflow = threading.Event()
        def drain():
            try:
                while block := process.stdout.read(8192):
                    if len(output) + len(block) > MAX_OUTPUT:
                        overflow.set()
                        return
                    output.extend(block)
            except (OSError, ValueError):
                pass
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        reason = None
        try:
            while process.poll() is None:
                if cancelled is not None and cancelled.is_set():
                    reason = failure("计算已取消，未保留本次结果。", "cancelled", cancelled=True)
                    break
                if time.monotonic() - started >= WALL_SECONDS or overflow.is_set():
                    reason = failure("求解进程达到资源上限，未生成最优结论。", "resource_limit", timed_out=True)
                    break
                time.sleep(0.015)
            if reason:
                process.terminate()
                try:
                    process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    process.kill()
            process.wait(timeout=2)
            reader.join(timeout=1)
            if reason:
                return reason
            if overflow.is_set():
                return failure("求解器输出超过上限。", "resource_limit")
            solution = path / "solution.sol"
            if process.returncode != 0 or not solution.is_file() or solution.stat().st_size > MAX_OUTPUT:
                return failure("HiGHS 未生成有效解文件；请检查平台要求、安装完整性和系统隔离支持。", "engine_failed")
            if ENGINE_VERSION not in output.decode("utf-8", "replace"):
                return failure("求解器实际版本与固定版本不一致。", "engine_version")
            result = parse_solution(solution.read_text(encoding="utf-8"), project)
            if cancelled is not None and cancelled.is_set():
                return failure("计算已取消，未保留本次结果。", "cancelled", cancelled=True)
            result.update(elapsed_seconds=round(time.monotonic() - started, 6), input_sha256=model.project_hash(project))
            data = {"ok": True, "version": model.VERSION, "project": project, "result": result, "warnings": [],
                    "license_notice": "CSparse：Copyright (c) 2006 Timothy A. Davis；LGPL-2.1-or-later，见 licenses/highs/csparse/LICENSE。"}
            if result["status"] in {"optimal", "feasible"}:
                data["csv"] = csv_result(result)
            return data
        except (OSError, ValueError, subprocess.SubprocessError):
            return failure("本次求解结果无法通过独立校验，未提供分配结论。", "invalid_result")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=2)
            process.stdout.close()
