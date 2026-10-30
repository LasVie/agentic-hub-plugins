# Copyright (C) Paul Falstad and Iain Sharp
# Modified 2026-10-28 for the bounded offline-circuit-lab Python runtime.
#
# Numerical companion models, MNA stamping and dense LU routines adapted from
# CircuitJS1, commit e952e788a4135a693bfd4cee7883f9b3314e3e76.
# See the bundled THIRD_PARTY_NOTICES.md.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 2 of the License, or (at your option) any later
# version. This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details. You should have received a copy of the GNU
# General Public License along with this program; see licenses/circuitjs/LICENSE.
"""有界理想 RLC 网络的修正节点分析；无联网或第三方运行时依赖。"""
from __future__ import annotations

import math
import re

VERSION = "1.0.0"
MAX_COMPONENTS = 24
MAX_NODES = 16  # 包含接地节点 0。
MAX_STEPS = 5000
VALUE_LIMITS = {"R": (1e-3, 1e9), "C": (1e-12, 1.0), "L": (1e-9, 1e3), "V": (-1e3, 1e3)}
LABEL = re.compile(r"[\w-]{1,24}\Z", re.UNICODE)
RESERVED = {"__proto__", "prototype", "constructor"}


class CircuitError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CircuitError("invalid_value", f"{name} 必须是有限数值。")
    try:
        value = float(value)
    except (OverflowError, ValueError):
        raise CircuitError("invalid_value", f"{name} 必须是有限数值。") from None
    if not math.isfinite(value) or not low <= value <= high:
        raise CircuitError("invalid_value", f"{name} 超出范围 [{low:g}, {high:g}]。")
    return value


def _label(value, name):
    if not isinstance(value, str) or not LABEL.fullmatch(value) or value in RESERVED:
        raise CircuitError("invalid_label", f"{name} 须为 1–24 个字母、数字、中文、下划线或连字符；不能使用保留名称。")
    return value


def _validate(raw):
    if not isinstance(raw, dict) or set(raw) - {"components", "duration_ms", "step_us", "probe", "mode"}:
        raise CircuitError("invalid_circuit", "电路须为对象，仅支持 components、duration_ms、step_us、probe、mode。")
    mode = raw.get("mode", "transient")
    if mode not in ("transient", "dc"):
        raise CircuitError("invalid_mode", "mode 只能是 transient（阶跃瞬态）或 dc（直流工作点）。")
    supplied = raw.get("components")
    if not isinstance(supplied, list) or not 1 <= len(supplied) <= MAX_COMPONENTS:
        raise CircuitError("component_limit", f"电路必须包含 1–{MAX_COMPONENTS} 个元件。")
    components, nodes, ids = [], set(), set()
    for item in supplied:
        if not isinstance(item, dict) or set(item) != {"id", "type", "a", "b", "value"}:
            raise CircuitError("invalid_component", "每个元件必须且只能包含 id、type、a、b、value。")
        ident = _label(item["id"], "元件编号")
        if ident in ids:
            raise CircuitError("duplicate_id", f"元件编号 {ident} 重复。")
        ids.add(ident)
        kind = item["type"]
        if not isinstance(kind, str) or kind not in VALUE_LIMITS:
            raise CircuitError("unsupported_component", "仅支持 R（电阻）、L（电感）、C（电容）、V（理想电压源）。")
        a, b = _label(item["a"], "节点 a"), _label(item["b"], "节点 b")
        if a == b:
            raise CircuitError("shorted_component", f"元件 {ident} 的两个端点相同；拒绝理想源短路及无意义自环。")
        value = _number(item["value"], f"元件 {ident} 的数值", *VALUE_LIMITS[kind])
        components.append({"id": ident, "type": kind, "a": a, "b": b, "value": value})
        nodes.update((a, b))
    if "0" not in nodes:
        raise CircuitError("missing_ground", "必须使用节点 0 作为接地参考。")
    if len(nodes) > MAX_NODES:
        raise CircuitError("node_limit", f"最多支持 {MAX_NODES} 个节点（包含接地 0）。")
    graph = {node: set() for node in nodes}
    for c in components:
        graph[c["a"]].add(c["b"])
        graph[c["b"]].add(c["a"])
    reached, pending = set(), ["0"]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(graph[node] - reached)
    if reached != nodes:
        raise CircuitError("floating_network", "存在未连接到接地网络的浮置节点；请检查连线。")
    probe = _label(raw.get("probe", sorted(nodes - {"0"})[0]), "探针节点")
    if probe not in nodes:
        raise CircuitError("unknown_probe", "探针必须选择电路中已有的节点。")
    duration = _number(raw.get("duration_ms", 5.0), "仿真时长（毫秒）", 1e-5, 1e3) / 1000
    step = _number(raw.get("step_us", 10.0), "步长（微秒）", 0.01, 1e4) / 1e6
    if mode == "transient":
        quotient = duration / step
        count = round(quotient)
        if count < 1 or count > MAX_STEPS:
            raise CircuitError("step_limit", f"时长除以步长必须在 1–{MAX_STEPS} 步之间。")
        if not math.isclose(quotient, count, rel_tol=1e-9, abs_tol=1e-9):
            raise CircuitError("nonintegral_steps", "时长必须为步长的整数倍；请调整时长或步长。")
    else:
        count = 0
    return components, sorted(nodes - {"0"}), probe, mode, step, count


def _check_initial_constraints(components):
    """阶跃后理想电压源不能强制零初值电容瞬时跳变。"""
    edges = {}
    for c in components:
        if c["type"] not in ("C", "V"):
            continue
        value = c["value"] if c["type"] == "V" else 0.0
        # Va - Vb = value; all capacitors initially have zero voltage.
        edges.setdefault(c["a"], []).append((c["b"], -value))
        edges.setdefault(c["b"], []).append((c["a"], value))
    potential = {}
    for root in edges:
        if root in potential:
            continue
        potential[root] = 0.0
        pending = [root]
        while pending:
            node = pending.pop()
            for other, delta in edges[node]:
                expected = potential[node] + delta
                if other in potential:
                    if not math.isclose(potential[other], expected, rel_tol=1e-10, abs_tol=1e-10):
                        raise CircuitError("inconsistent_initial_state", "理想电压源与零初值电容形成不相容回路，要求瞬时无限电流；请加入实际串联电阻或修改拓扑。")
                else:
                    potential[other] = expected
                    pending.append(other)


def _conductance(matrix, index, a, b, g):
    # Adapted CircuitJS1 SimulationManager.stampResistor/stampConductance.
    ia, ib = index.get(a), index.get(b)
    if ia is not None:
        matrix[ia][ia] += g
    if ib is not None:
        matrix[ib][ib] += g
    if ia is not None and ib is not None:
        matrix[ia][ib] -= g
        matrix[ib][ia] -= g


def _current(rhs, index, a, b, value):
    # Adapted CircuitJS1 SimulationManager.stampCurrentSource.
    if a in index:
        rhs[index[a]] -= value
    if b in index:
        rhs[index[b]] += value


def _factor(matrix):
    """带行归一化的稠密 Crout LU；不通过虚构漏电或扰动对角线掩盖奇异网络。"""
    size = len(matrix)
    scales = [max(abs(value) for value in row) for row in matrix]
    if any(scale == 0 for scale in scales):
        raise CircuitError("singular_network", "电路方程无唯一解；检查浮置节点、理想源回路及直流开路。")
    lu = [[value / scales[i] for value in row] for i, row in enumerate(matrix)]
    pivots = []
    # Adapted CircuitJS1 SimulationManager.lu_factor_dense (Crout, partial pivot).
    for j in range(size):
        for i in range(j):
            lu[i][j] -= sum(lu[i][k] * lu[k][j] for k in range(i))
        for i in range(j, size):
            lu[i][j] -= sum(lu[i][k] * lu[k][j] for k in range(j))
        pivot = max(range(j, size), key=lambda i: abs(lu[i][j]))
        if abs(lu[pivot][j]) < 1e-12:
            raise CircuitError("singular_network", "电路方程奇异或病态；理想源可能冲突、支路电流不唯一或参数比例过大。")
        if pivot != j:
            lu[j], lu[pivot] = lu[pivot], lu[j]
        pivots.append(pivot)
        for i in range(j + 1, size):
            lu[i][j] /= lu[j][j]
    return lu, pivots, scales


def _solve(matrix, factored, rhs):
    lu, pivots, scales = factored
    x = [value / scale for value, scale in zip(rhs, scales)]
    # Adapted CircuitJS1 SimulationManager.lu_solve_dense.
    for i, pivot in enumerate(pivots):
        value = x[pivot]
        x[pivot] = x[i]
        x[i] = value - sum(lu[i][j] * x[j] for j in range(i))
    for i in range(len(x) - 1, -1, -1):
        x[i] = (x[i] - sum(lu[i][j] * x[j] for j in range(i + 1, len(x)))) / lu[i][i]
    if any(not math.isfinite(value) or abs(value) > 1e6 for value in x):
        raise CircuitError("numerical_range", "数值结果非有限或超出本版 ±10⁶ V/A 的计算范围；请检查拓扑、参数及步长。")
    for row, expected in zip(matrix, rhs):
        residual = abs(sum(a * value for a, value in zip(row, x)) - expected)
        scale = sum(abs(a * value) for a, value in zip(row, x)) + abs(expected) + 1e-12
        if residual > 1e-8 * scale:
            raise CircuitError("numerical_residual", "线性方程残差过大，结果不可信；请调整参数比例或步长。")
    return x


def _matrix(components, nodes, mode, step, trapezoidal):
    index = {node: i for i, node in enumerate(nodes)}
    branches = [c for c in components if c["type"] == "V" or (mode == "dc" and c["type"] == "L")]
    branch_index = {c["id"]: len(nodes) + i for i, c in enumerate(branches)}
    size = len(nodes) + len(branches)
    matrix = [[0.0] * size for _ in range(size)]
    rhs = [0.0] * size
    conductances = {}
    for c in components:
        kind, value, a, b, ident = c["type"], c["value"], c["a"], c["b"], c["id"]
        if ident in branch_index:
            branch = branch_index[ident]
            # Interface convention: Va - Vb = value, current positive a -> b.
            for node, sign in ((a, 1), (b, -1)):
                if node in index:
                    matrix[index[node]][branch] += sign
                    matrix[branch][index[node]] += sign
            rhs[branch] = value if kind == "V" else 0.0
        elif kind == "R":
            conductances[ident] = 1 / value
        elif mode == "transient":
            # CircuitJS1 Norton companions, with SI units.
            conductances[ident] = ((2 if trapezoidal else 1) * value / step if kind == "C"
                                   else step / ((2 if trapezoidal else 1) * value))
        if ident in conductances:
            _conductance(matrix, index, a, b, conductances[ident])
    return matrix, rhs, index, branch_index, conductances, _factor(matrix)


def _simulate(raw):
    components, nodes, probe, mode, step, count = _validate(raw)
    if mode == "transient":
        _check_initial_constraints(components)
    zero_v = {node: 0.0 for node in ["0", *nodes]}
    zero_i = {c["id"]: 0.0 for c in components}
    samples = [{"t": 0.0, "voltages": zero_v, "currents": zero_i}] if mode == "transient" else []
    previous_v, previous_i = zero_v, zero_i
    assembled = {}
    for iteration in range(1, count + 1) if mode == "transient" else (0,):
        trapezoidal = iteration > 1
        if trapezoidal not in assembled:
            assembled[trapezoidal] = _matrix(components, nodes, mode, step, trapezoidal)
        matrix, base_rhs, index, branch_index, conductances, factored = assembled[trapezoidal]
        rhs = base_rhs[:]
        history = {}
        if mode == "transient":
            for c in components:
                ident, kind, a, b = c["id"], c["type"], c["a"], c["b"]
                if kind == "C":
                    history[ident] = -conductances[ident] * (previous_v[a] - previous_v[b])
                    if trapezoidal:
                        history[ident] -= previous_i[ident]
                elif kind == "L":
                    history[ident] = previous_i[ident]
                    if trapezoidal:
                        history[ident] += conductances[ident] * (previous_v[a] - previous_v[b])
                if ident in history:
                    _current(rhs, index, a, b, history[ident])
        solved = _solve(matrix, factored, rhs)
        voltages = {"0": 0.0, **{node: solved[i] for node, i in index.items()}}
        currents = {}
        for c in components:
            ident = c["id"]
            if ident in branch_index:
                currents[ident] = solved[branch_index[ident]]
            else:
                currents[ident] = conductances.get(ident, 0.0) * (voltages[c["a"]] - voltages[c["b"]]) + history.get(ident, 0.0)
            if not math.isfinite(currents[ident]) or abs(currents[ident]) > 1e6:
                raise CircuitError("numerical_range", "支路电流非有限或超出本版 ±10⁶ A 的计算范围。")
        # The matrix residual alone may hide loss of tiny conductances next to
        # huge companion conductances. Verify the reconstructed physical KCL too.
        for node in voltages:
            terms = [currents[c["id"]] * ((c["a"] == node) - (c["b"] == node)) for c in components]
            if abs(sum(terms)) > 1e-12 + 1e-7 * sum(abs(value) for value in terms):
                raise CircuitError("numerical_residual", "支路电流未满足节点电流守恒，参数比例可能超出数值精度；请调整参数或步长。")
        samples.append({"t": iteration * step if mode == "transient" else 0.0, "voltages": voltages, "currents": currents})
        previous_v, previous_i = voltages, currents
    trace = [sample["voltages"][probe] for sample in samples]
    warnings = ["仅计算理想线性 R/L/C 与理想电压源；不含寄生、饱和、温度、损耗模型或真实硬件安全验证。"]
    if mode == "transient":
        warnings += ["t=0 为阶跃前零状态；所有电压源在其后同时阶跃至设定值。电容初始电压和电感初始电流均为零。",
                     "首步使用后向欧拉，其后使用梯形积分。步长过大会遗漏快速动态或引起数值振铃；请减半步长复核收敛性。"]
    else:
        warnings.append("直流分析将电容视为开路、电感视为理想短路；无唯一解时拒绝返回结果，不添加虚构漏电。")
    return {"ok": True, "version": VERSION, "mode": mode,
            "method": "修正节点分析；首步后向欧拉 + 梯形积分" if mode == "transient" else "修正节点分析；直流工作点",
            "units": {"t": "s", "voltages": "V", "currents": "A"},
            "current_direction": "支路电流正方向为 a → b；电压源约束为 Va − Vb = value。",
            "samples": samples,
            "summary": {"probe": probe, "final_voltage": trace[-1], "min_voltage": min(trace), "max_voltage": max(trace),
                        "steps": count, "duration_ms": count * step * 1000, "step_us": step * 1e6 if mode == "transient" else None,
                        "component_count": len(components), "node_count": len(nodes) + 1},
            "warnings": warnings}


def simulate(circuit):
    """返回 JSON 可序列化结果；所有可预期的输入/拓扑失败均使用中文错误。"""
    try:
        return _simulate(circuit)
    except CircuitError as exc:
        return {"ok": False, "version": VERSION, "error": {"code": exc.code, "message": str(exc)}}
    except (ArithmeticError, ValueError, TypeError):
        return {"ok": False, "version": VERSION, "error": {"code": "numerical_error", "message": "数值计算失败；请检查参数、拓扑及步长，未生成可信结果。"}}
