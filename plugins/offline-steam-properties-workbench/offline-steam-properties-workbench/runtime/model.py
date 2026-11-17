"""Strict declarative SI-only inputs for the fixed water/steam calculation."""
from __future__ import annotations

import copy
import hashlib
import json
import math

VERSION = "1.0.0"
MAX_INPUT = 256 * 1024


class InputError(ValueError):
    """Chinese diagnostic safe to expose to the user."""


def encode(value):
    try:
        data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise InputError("项目必须是有效 UTF-8 JSON，不能包含非有限数值。") from exc
    if len(data) > MAX_INPUT:
        raise InputError("项目超过 256 KiB 上限。")
    return data


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise InputError("JSON 含重复字段。")
            result[key] = value
        return result
    try:
        if len(data) > MAX_INPUT:
            raise InputError("项目超过 256 KiB 上限。")
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _v: (_ for _ in ()).throw(InputError("JSON 含非有限数值。")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InputError("项目 JSON 无效、含重复字段或非有限数值。") from exc


def keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise InputError(f"{label}字段必须恰好为：{'、'.join(expected)}；不接受脚本、后端配置或额外字段。")


def number(value, low, high, label):
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        raise InputError(f"{label}必须为 {low} 至 {high} 之间的有限数值。")
    return value


def validate(project):
    encode(project)
    keys(project, ("schema", "name", "state", "sweep"), "项目")
    if project["schema"] != "steam-properties/v1":
        raise InputError("仅支持 steam-properties/v1 项目格式。")
    name = project["name"]
    if not isinstance(name, str) or not name.strip() or not 1 <= len(name) <= 80 or any(not c.isprintable() for c in name):
        raise InputError("项目名称须为 1 至 80 个可显示字符，不能含控制字符。")
    state = project["state"]
    if not isinstance(state, dict) or not isinstance(state.get("pair"), str) or state["pair"] not in ("PT", "PQ", "TQ"):
        raise InputError("状态输入仅支持 PT、PQ 或 TQ。")
    pair = state["pair"]
    expected = {"PT": ("pair", "pressure_pa", "temperature_k"),
                "PQ": ("pair", "pressure_pa", "quality"),
                "TQ": ("pair", "temperature_k", "quality")}[pair]
    keys(state, expected, "状态")
    if "pressure_pa" in state:
        number(state["pressure_pa"], 1000, 20000000, "绝对压力（Pa）")
    if "temperature_k" in state:
        number(state["temperature_k"], 273.16, 800 if pair == "PT" else 640, "温度（K）")
    if "quality" in state:
        number(state["quality"], 0, 1, "蒸汽干度 Q")
    sweep = project["sweep"]
    keys(sweep, ("variable", "start", "end", "points"), "饱和扫描")
    if not isinstance(sweep["variable"], str) or sweep["variable"] not in ("pressure_pa", "temperature_k"):
        raise InputError("饱和扫描仅支持 pressure_pa 或 temperature_k。")
    lo, hi = (1000, 20000000) if sweep["variable"] == "pressure_pa" else (273.16, 640)
    number(sweep["start"], lo, hi, "扫描起点")
    number(sweep["end"], lo, hi, "扫描终点")
    if sweep["start"] >= sweep["end"]:
        raise InputError("扫描终点必须大于起点。")
    if type(sweep["points"]) is not int or not 2 <= sweep["points"] <= 100:
        raise InputError("扫描点数必须是 2 至 100 的整数。")
    return copy.deepcopy(project)


def fingerprint(project):
    return hashlib.sha256(json.dumps(project, ensure_ascii=False, allow_nan=False,
                                    sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def examples():
    default = {"schema": "steam-properties/v1", "name": "常压饱和水",
               "state": {"pair": "PQ", "pressure_pa": 101325, "quality": 0},
               "sweep": {"variable": "pressure_pa", "start": 10000, "end": 2000000, "points": 25}}
    result = {"常压饱和水": default}
    for name, state in (("过热蒸汽", {"pair": "PT", "pressure_pa": 101325, "temperature_k": 473.15}),
                        ("湿蒸汽", {"pair": "PQ", "pressure_pa": 101325, "quality": 0.5}),
                        ("温度扫描", {"pair": "TQ", "temperature_k": 373.15, "quality": 1})):
        project = copy.deepcopy(default)
        project.update(name=name, state=state)
        if name == "温度扫描":
            project["sweep"] = {"variable": "temperature_k", "start": 300, "end": 620, "points": 25}
        result[name] = project
    return result
