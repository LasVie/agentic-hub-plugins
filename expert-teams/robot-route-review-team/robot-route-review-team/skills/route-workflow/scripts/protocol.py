"""Bounded input/evidence contract; contains no path search or conflict detector."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

VERSION = "1.0.0"
MODEL = "grid-4-wait-stay-v1"
MAX_JSON = 1024 * 1024
DEFAULT_LIMITS = {"high_level_nodes": 2000, "low_level_nodes": 100000, "seconds": 5}


class ContractError(ValueError):
    pass


def fail(message: str) -> None:
    raise ContractError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("JSON 包含重复键：" + key)
        result[key] = value
    return result


def read_json(path: Path, max_bytes: int = MAX_JSON):
    if path.is_symlink() or not path.is_file():
        fail("输入必须是实际的普通文件，不能是符号链接。")
    with path.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        fail("JSON 文件超过大小限制。")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates,
                          parse_constant=lambda value: fail("不允许非有限数字。"))
    except (ValueError, UnicodeError) as error:
        fail("无法读取严格 UTF-8 JSON：" + str(error))
    return data, raw


def object_keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        fail("对象字段缺失或存在不支持的字段；请检查案例/报告格式。")


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        fail(f"{label}必须是 {low}–{high} 的整数。")
    return value


def cell(value, width, height):
    if not isinstance(value, list) or len(value) != 2:
        fail("坐标必须是 [x,y] 整数数组。")
    return [integer(value[0], 0, width - 1, "横坐标"), integer(value[1], 0, height - 1, "纵坐标")]


def validate_case(case):
    object_keys(case, ("schema_version", "title", "grid", "robots", "horizon", "model"), ("limits",))
    if type(case["schema_version"]) is not int or case["schema_version"] != 1 or case["model"] != MODEL:
        fail("案例版本或运动规则不受支持；不能自动改用其他碰撞模型。")
    if not isinstance(case["title"], str) or not 1 <= len(case["title"]) <= 100:
        fail("案例名称须为 1–100 个字符。")
    grid = case["grid"]
    object_keys(grid, ("width", "height", "obstacles"))
    width = integer(grid["width"], 2, 12, "网格宽度")
    height = integer(grid["height"], 2, 12, "网格高度")
    if not isinstance(grid["obstacles"], list) or len(grid["obstacles"]) > width * height:
        fail("障碍列表无效。")
    obstacles = [tuple(cell(item, width, height)) for item in grid["obstacles"]]
    if len(set(obstacles)) != len(obstacles):
        fail("障碍坐标重复。")
    if not isinstance(case["robots"], list) or not 2 <= len(case["robots"]) <= 4:
        fail("每次只支持 2–4 个模拟机器人。")
    ids, starts, goals = set(), set(), set()
    for robot in case["robots"]:
        object_keys(robot, ("id", "start", "goal"))
        identifier = robot["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,23}", identifier) or identifier in ids:
            fail("机器人 id 须唯一、以英文字母开头，最多 24 位。")
        start, goal = tuple(cell(robot["start"], width, height)), tuple(cell(robot["goal"], width, height))
        if start in starts or goal in goals or start in obstacles or goal in obstacles:
            fail("起点/终点不能落在障碍中，且起点、终点各自不得重复。")
        ids.add(identifier); starts.add(start); goals.add(goal)
    integer(case["horizon"], 1, 40, "搜索时域")
    limits = case.get("limits", {})
    object_keys(limits, (), tuple(DEFAULT_LIMITS))
    for name, maximum in DEFAULT_LIMITS.items():
        integer(limits.get(name, maximum), 1, maximum, "搜索限额 " + name)
    return case


def load_case(path: Path):
    case, raw = read_json(path, 65536)
    return validate_case(case), sha(raw), raw


def packet(role, case_sha256, **fields):
    return {"schema_version": 1, "version": VERSION, "role": role,
            "case_sha256": case_sha256, "model": MODEL, **fields}


def bind(record, role, case_sha256):
    if (not isinstance(record, dict) or record.get("schema_version") != 1 or
        type(record.get("schema_version")) is not int or record.get("version") != VERSION or
        record.get("role") != role or record.get("case_sha256") != case_sha256 or record.get("model") != MODEL):
        fail("报告角色、版本、运动模型或案例摘要不匹配；请保留旧证据并重新运行。")


def comments(record):
    if not isinstance(record.get("notes"), list) or not isinstance(record.get("issues"), list):
        fail("报告必须明确区分 notes 说明与 issues 未解决问题。")
    for name in ("notes", "issues"):
        if len(record[name]) > 20 or any(not isinstance(s, str) or not 1 <= len(s) <= 1000 for s in record[name]):
            fail("说明/问题列表格式无效或超过边界。")


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_new(path: Path, data: bytes):
    # Existing ancestors may be user-selected workspaces; the final object must
    # be created exclusively. Never resolve a symlink at the output leaf.
    if path.is_symlink():
        fail("输出不能是符号链接。")
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        fail("输出已存在；不覆盖，请指定新的文件名。")


def inspect(case_path: Path):
    case, digest, _ = load_case(case_path)
    return packet("map-analyst", digest, status="inspected", case=case,
                  notes=["已检查结构与离散规则；仍须成员核对用户意图。", "同格与反向换边被禁止；允许跟随与三方以上轮换，终点永久停留。"], issues=[])


def main():
    parser = argparse.ArgumentParser(description="冻结并检查模拟网格案例，不规划路径、不操作真实设备。")
    parser.add_argument("--case", type=Path, required=True, help="用户提供的案例 JSON")
    parser.add_argument("--output", type=Path, required=True, help="新的地图约束报告 JSON，不覆盖")
    args = parser.parse_args()
    try:
        result = inspect(args.case)
        write_new(args.output, encoded(result))
        print(json.dumps({"ok": True, "version": VERSION, "case_sha256": result["case_sha256"], "report": str(args.output.absolute())}, ensure_ascii=False))
    except (ContractError, OSError) as error:
        print(json.dumps({"ok": False, "version": VERSION, "error": str(error)}, ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
