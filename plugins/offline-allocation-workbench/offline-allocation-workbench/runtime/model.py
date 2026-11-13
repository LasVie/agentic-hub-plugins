"""Bounded declarative allocation data; never accept program/model source."""
from __future__ import annotations

import copy
import hashlib
import json

VERSION = "1.0.0"
MAX_INPUT = 256 * 1024
SCHEMA = "offline-allocation/v1"


class InputError(ValueError):
    pass


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise InputError("JSON 含有重复字段，请检查原始文件。")
            result[key] = value
        return result

    def constant(_):
        raise InputError("JSON 不接受 NaN 或无穷大。")

    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if len(raw.encode("utf-8")) > MAX_INPUT:
            raise InputError("项目不得超过 256 KiB。")
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as exc:
        raise InputError("项目必须是有效的 UTF-8 JSON。") from exc


def encode(value):
    try:
        data = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise InputError("输入必须是有效的 JSON 数据。") from exc
    if len(data) > MAX_INPUT:
        raise InputError("项目不得超过 256 KiB。")
    return data


def keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise InputError(label + "字段不完整或含有不支持的字段；不接受脚本、HTML、路径或求解器选项。")


def text(value, limit, label):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 or 127 <= ord(c) < 160 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise InputError(f"{label}须为 1 至 {limit} 字的有效文本，不能含控制字符。")
    return value


def integer(value, maximum, label):
    if type(value) is not int or not 0 <= value <= maximum:
        raise InputError(f"{label}须为 0 至 {maximum} 的整数；布尔值、小数和字符串均不接受。")
    return value


def validate(project):
    # Encode first to bound nested/untrusted objects before walking the schema.
    encode(project)
    keys(project, ("schema", "name", "resources", "jobs", "min_jobs"), "项目")
    if project["schema"] != SCHEMA:
        raise InputError("仅支持 offline-allocation/v1 项目格式。")
    text(project["name"], 80, "项目名称")
    resources, jobs = project["resources"], project["jobs"]
    if not isinstance(resources, list) or not 1 <= len(resources) <= 8:
        raise InputError("须提供 1 至 8 种资源。")
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 100:
        raise InputError("须提供 1 至 100 项作业。")
    resource_ids = set()
    for r in resources:
        keys(r, ("id", "name", "capacity"), "资源")
        identifier = text(r["id"], 40, "资源标识")
        if identifier in resource_ids:
            raise InputError("资源标识不能重复。")
        resource_ids.add(identifier)
        text(r["name"], 80, "资源名称")
        integer(r["capacity"], 1000000, "资源容量")
    job_ids = set()
    for j in jobs:
        keys(j, ("id", "name", "value", "uses"), "作业")
        identifier = text(j["id"], 40, "作业标识")
        if identifier in job_ids:
            raise InputError("作业标识不能重复。")
        job_ids.add(identifier)
        text(j["name"], 80, "作业名称")
        integer(j["value"], 1000000, "作业价值")
        keys(j["uses"], resource_ids, "作业资源用量")
        for amount in j["uses"].values():
            integer(amount, 1000000, "资源用量")
    integer(project["min_jobs"], len(jobs), "最少选择作业数")
    return copy.deepcopy(project)


def project_hash(project):
    return hashlib.sha256(encode(project)).hexdigest()


def examples():
    p = {"schema": SCHEMA, "name": "资源选择 · 双预算", "min_jobs": 0,
         "resources": [{"id": "labour", "name": "人工", "capacity": 7},
                       {"id": "machine", "name": "机时", "capacity": 5}],
         "jobs": [{"id": ident, "name": "作业" + ident, "value": value,
                   "uses": {"labour": labour, "machine": machine}}
                  for ident, labour, machine, value in
                  [("A", 6, 2, 10), ("B", 4, 4, 9), ("C", 3, 2, 8), ("D", 2, 3, 6)]]}
    expanded = copy.deepcopy(p)
    expanded["name"] = "设备扩容 · 增加一单位机时"
    expanded["resources"][1]["capacity"] = 6
    impossible = copy.deepcopy(p)
    impossible["name"] = "不可行 · 至少选择三项"
    impossible["min_jobs"] = 3
    return {"资源选择": p, "设备扩容": expanded, "不可行示例": impossible}
