"""Validate a small, frozen user-confirmed basket."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat

VERSION = "1.0.0"
SCHEMA = 1
ACTION = {"very_gentle": "非常轻柔", "gentle": "轻柔", "normal": "标准"}
COLOR = {"light": "浅色", "dark": "深色", "bright": "亮色"}
DRY = {
    "line": "悬挂晾干",
    "flat": "平摊晾干",
    "line_shade": "阴凉处悬挂晾干",
    "flat_shade": "阴凉处平摊晾干",
    "tumble_low": "低温滚筒烘干",
    "tumble_normal": "按标签选普通热度滚筒烘干",
    "unknown": "先确认干燥标签",
}
HOLD = {
    "unknown_wash": "机洗条件未确认",
    "hand": "标签要求手洗，移出机洗批次",
    "no_machine": "标签未许可机洗",
    "unknown_color": "颜色分组未确认",
    "unknown_separate": "是否须分洗未确认",
    "no_program": "当前机器无已确认相容程序",
}


class InputError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InputError(message)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_file(path: Path):
    require(not path.is_symlink(), "不接受符号链接文件。")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= 512_000, "文件类型或大小超出范围。")
        data = stream.read(512_001)
    require(len(data) <= 512_000, "文件超过大小限制。")
    return data


def decoded(data):
    def checked_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "JSON 中存在重复字段。")
            result[key] = value
        return result
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=checked_pairs)


def fields(data, names, label):
    require(isinstance(data, dict) and data.keys() == set(names.split()), f"{label}的字段缺失或多余。")


def text(value, limit, key):
    require(isinstance(value, str) and value == value.strip() and 0 < len(value) <= limit
            and all(c.isprintable() for c in value), f"{key}须提供简短的单行原文。")


def key(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,23}", value) is not None


def integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def choice(value, allowed):
    return isinstance(value, str) and value in allowed


@dataclass(frozen=True)
class Case:
    data: bytes
    title: str
    profiles: dict
    programs: dict
    basket: dict

    @property
    def sha256(self):
        return digest(self.data)


def load_case(path):
    data = read_file(path)
    case = decoded(data)
    fields(case, "schema title profiles programs basket", "案例")
    require(type(case["schema"]) is int and case["schema"] == SCHEMA, "不支持的输入版本。")
    text(case["title"], 80, "标题")
    profiles, programs, basket = case["profiles"], case["programs"], case["basket"]
    require(isinstance(profiles, dict) and 1 <= len(profiles) <= 80, "请提供 1 至 80 个可复用组别。")
    for profile_id, profile in profiles.items():
        require(key(profile_id), "衣物组别编号无效。")
        fields(profile, "name label color wash separate dry", "衣物组别")
        text(profile["name"], 60, "衣物名称")
        text(profile["label"], 180, "标签记录")
        require(profile["color"] is None or choice(profile["color"], COLOR), "颜色组无效。")
        require(profile["separate"] is None or type(profile["separate"]) is bool, "分洗应为是、否或待确认。")
        require(choice(profile["dry"], DRY), "干燥条件无效。")
        wash = profile["wash"]
        fields(wash, "method max_celsius max_action", "洗涤条件")
        require(choice(wash["method"], ("machine", "hand", "no_machine", "unknown")), "洗涤方式无效。")
        require(wash["max_celsius"] is None or integer(wash["max_celsius"], 0, 95), "温度上限须为 0 至 95 的整数摄氏度。")
        require(wash["max_action"] is None or choice(wash["max_action"], ACTION), "动作强度无效。")
        if wash["method"] != "machine":
            require(wash["max_celsius"] is None and wash["max_action"] is None, "待确认或非机洗组不应填写机洗条件。")
    require(isinstance(programs, list) and len(programs) <= 12, "最多列出 12 个机洗程序。")
    known = {}
    for program in programs:
        fields(program, "id name celsius action max_items", "洗衣程序")
        ident = program["id"]
        require(key(ident) and ident not in known, "洗衣程序编号无效或重复。")
        text(program["name"], 48, "面板程序名")
        require(integer(program["celsius"], 0, 95), "程序须有已确认的整数摄氏度。")
        require(choice(program["action"], ACTION), "程序须有已确认的动作强度。")
        require(program["max_items"] is None or integer(program["max_items"], 1, 80), "件数上限须为 1 至 80 或待确认。")
        known[ident] = program
    require(isinstance(basket, dict) and 1 <= len(basket) <= 40, "衣篮须含 1 至 40 个组别。")
    for ident, count in basket.items():
        require(ident in profiles and integer(count, 1, 80), "衣篮中有未知组别或件数无效。")
    require(sum(basket.values()) <= 80, "每次最多核查 80 件衣物。")
    return Case(data, case["title"], profiles, known, basket)
