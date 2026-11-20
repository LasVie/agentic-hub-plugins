"""例会核验的输入、时区数据与文件交接契约。"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from importlib import metadata, resources
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata
from zoneinfo import TZPATH, ZoneInfo

UTC = timezone.utc
MINUTE = timedelta(minutes=1)
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
MAX_FILE = 512 * 1024
ID = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
ZONE = re.compile(r"[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+)*\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, keys, label):
    require(type(value) is dict and set(value) == set(keys.split()), f"{label}字段不完整或存在未知字段")


def count(value, low, high, label):
    require(type(value) is int and low <= value <= high, f"{label}应为{low}至{high}之间的整数")
    return value


def identifier(value):
    require(type(value) is str and ID.fullmatch(value), "编号须由小写字母开头，仅含小写字母、数字及连字符")
    return value


def local_date(value):
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value, flags=re.ASCII), "日期应为 YYYY-MM-DD")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise ValueError("日期不存在") from None
    require(2000 <= result.year <= 2099, "日期年份应在2000至2099之间")
    return result


def clock(value, closing=False):
    if closing and value == "24:00":
        return 1440
    require(type(value) is str and re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", value), "时刻应为 HH:MM，24:00仅作窗口终点")
    return int(value[:2]) * 60 + int(value[3:])


def windows(value):
    require(type(value) is list and len(value) <= 8, "每日最多八个可用窗口")
    intervals = []
    for pair in value:
        require(type(pair) is list and len(pair) == 2, "窗口应为两个时刻组成的列表")
        left, right = clock(pair[0]), clock(pair[1], closing=True)
        require(left < right, "窗口终点须晚于起点；跨午夜请拆成相邻两天")
        intervals.append((left, right))
    intervals.sort()
    require(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), "同一天的窗口不能重叠")
    return tuple(intervals)


@dataclass(frozen=True)
class Participant:
    id: str
    label: str
    zone: str
    weekly: tuple
    overrides: dict


@dataclass(frozen=True)
class Case:
    id: str
    organizer_zone: str
    start: date
    weeks: int
    length: int
    slots: tuple
    people: tuple


def zone_key(key):
    require(type(key) is str and len(key) <= 96 and ZONE.fullmatch(key), "时区应采用 IANA 编号")
    require(key == "UTC" or ("/" in key and key.split("/")[0] not in {"right", "posix"}), "请提供 IANA 地区时区或 UTC")
    return key


def validate(value):
    fields(value, "schema_version case_id organizer_zone start_date weeks duration_minutes slots participants", "案例")
    count(value["schema_version"], 1, 1, "结构版本")
    start = local_date(value["start_date"])
    weeks = count(value["weeks"], 4, 12, "周数")
    require((start + timedelta(weeks=weeks - 1)).year <= 2099, "最后一期超出支持年份")
    duration = count(value["duration_minutes"], 15, 120, "会议分钟数")
    require(type(value["slots"]) is list and 1 <= len(value["slots"]) <= 3, "候选时段应为1至3个")
    slots = []
    for slot in value["slots"]:
        fields(slot, "id start", "候选时段")
        slots.append((identifier(slot["id"]), clock(slot["start"])))
    require(len({s[0] for s in slots}) == len(slots) and len({s[1] for s in slots}) == len(slots), "候选编号及时刻不应重复")
    require(type(value["participants"]) is list and 2 <= len(value["participants"]) <= 8, "参会者应为2至8人")
    people = []
    for entry in value["participants"]:
        fields(entry, "id label zone weekly overrides", "参会者")
        label = entry["label"]
        require(type(label) is str and 1 <= len(label) <= 60 and label.strip() and
                not any(unicodedata.category(ch) in {"Cc", "Cf", "Cs"} for ch in label),
                "参会者标签应是1至60个可见字符")
        fields(entry["weekly"], " ".join(DAYS), "每周窗口")
        overrides = entry["overrides"]
        require(type(overrides) is dict and len(overrides) <= 32, "日期例外最多32条")
        people.append(Participant(identifier(entry["id"]), label, zone_key(entry["zone"]),
                                  tuple(windows(entry["weekly"][d]) for d in DAYS),
                                  {local_date(d): windows(w) for d, w in overrides.items()}))
    require(len({p.id for p in people}) == len(people), "参会者编号不能重复")
    return Case(identifier(value["case_id"]), zone_key(value["organizer_zone"]), start,
                weeks, duration, tuple(slots), tuple(people))


def load_zone(key):
    relative = key.split("/")
    for root in TZPATH:
        file = Path(root).joinpath(*relative)
        if file.is_file():
            raw = file.read_bytes()
            source = "系统 TZif"
            break
    else:
        try:
            file = resources.files("tzdata.zoneinfo")
            for segment in relative:
                file = file.joinpath(segment)
            raw = file.read_bytes()
            source = "已安装 tzdata " + metadata.version("tzdata")
        except (ModuleNotFoundError, FileNotFoundError, metadata.PackageNotFoundError):
            raise ValueError(f"宿主缺少 {key} 的 IANA 数据") from None
    try:
        zone = ZoneInfo.from_file(BytesIO(raw), key=key)
    except (ValueError, OSError):
        raise ValueError(f"宿主时区文件无法解析：{key}") from None
    return zone, {"source": source, "tzif_sha256": sha256(raw).hexdigest()}


def zone_snapshot(case):
    sources, zones = {}, {}
    for key in sorted({case.organizer_zone, *(p.zone for p in case.people)}):
        zones[key], sources[key] = load_zone(key)
    return zones, sources


def hex_bytes(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"JSON 字段重复：{key}")
        obj[key] = value
    return obj


def invalid_constant(value):
    raise ValueError(f"JSON 不允许非有限值：{value}")


def read(path):
    path = Path(path)
    require(path.is_absolute(), "输入须为绝对路径")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    require(not path.is_symlink(), "输入文件不能是符号链接")
    with os.fdopen(os.open(path, flags), "rb") as f:
        before = os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_FILE, "输入须为不超过512 KiB的非空普通文件")
        raw = f.read(MAX_FILE + 1)
        after = os.fstat(f.fileno())
        require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
                "读取期间文件发生变化")
    try:
        obj = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_pairs, parse_constant=invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("无法解析 UTF-8 JSON，请检查文件格式和嵌套深度") from None
    return obj, hex_bytes(raw)


def input_state(path):
    data, digest = read(path)
    case = validate(data)
    zones, provenance = zone_snapshot(case)
    identity = {"schema_version": 1, "case_id": case.id, "input_sha256": digest,
                "zones": provenance, "duration_minutes": case.length,
                "participants": [{"id": p.id, "label": p.label, "zone": p.zone} for p in case.people]}
    return case, zones, identity


def intake(identity):
    return {"kind": "meeting-intake/v1", **identity}


def wall_at(d, minute):
    return datetime.combine(d, time()) + minute * MINUTE


def wall_min(d):
    return d.hour * 60 + d.minute


def stamp(d):
    offset = d.utcoffset()
    require(offset is None or offset % MINUTE == timedelta(0), "本版不支持秒级时区偏移")
    return d.isoformat(timespec="minutes")


def output_path(path):
    path = Path(path)
    require(path.is_absolute() and path.parent.is_dir(), "输出须为已存在父目录下的新绝对路径")
    return path


def write(path, data):
    with output_path(path).open("xb") as stream:
        stream.write(canonical(data) + b"\n")


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("命令参数不完整或无效，请用 --help 查看用法")


def cli(main):
    try:
        main()
    except (ValueError, OSError) as error:
        reason = str(error) if isinstance(error, ValueError) else f"文件操作失败（错误号 {error.errno}）"
        print(f"核验中止：{reason}", file=sys.stderr)
        raise SystemExit(2) from None
