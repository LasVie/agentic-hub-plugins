"""Read and bind the bounded local input contract."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import stat

INPUTS = ("readings.csv", "tariff.json", "bill.json")
MAX_BYTES = 2_000_000
MAX_INTERVALS = 31 * 48
DECIMAL_PATTERN = r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,6})?"
CODE_PATTERN = r"[a-z][a-z0-9_-]{0,23}"
TIME_PATTERN = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}"


class InputError(ValueError):
    """An input or handoff that requires clarification."""


def require(condition, message):
    if not condition:
        raise InputError(message)


def read_bytes(path: Path, limit=MAX_BYTES):
    require(not path.is_symlink(), f"不接受符号链接：{path.name}")
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as stream:
        meta = os.fstat(stream.fileno())
        require(stat.S_ISREG(meta.st_mode) and meta.st_size <= limit, f"文件类型或大小超出范围：{path.name}")
        body = stream.read(limit + 1)
    require(len(body) <= limit, f"文件超出大小限制：{path.name}")
    return body


def digest(body):
    return sha256(body).hexdigest()


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def decode_json(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "JSON 不允许重复字段。")
            result[key] = value
        return result
    return json.loads(body.decode("utf-8-sig"), object_pairs_hook=unique)


def fields(data, names, label):
    require(isinstance(data, dict) and data.keys() == set(names.split()), f"{label}的字段不完整或包含额外字段。")
    return data


def match(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def decimal_value(text, label, places=6):
    require(match(DECIMAL_PATTERN, text) and len(text.partition(".")[2]) <= places, f"{label}须为非负十进制定点数字符串。")
    return Decimal(text)


def minute_value(text):
    require(match(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00", text), "费率边界须使用 HH:MM。")
    hour, minute = map(int, text.split(":"))
    return hour * 60 + minute


def timestamp(text):
    require(match(TIME_PATTERN, text), "区间时间须使用本地 YYYY-MM-DDTHH:MM。")
    try:
        return datetime.fromisoformat(text)
    except ValueError as error:
        raise InputError("区间时间不是有效的日历日期。") from error


@dataclass(frozen=True)
class Case:
    snapshots: dict
    hashes: dict
    start: datetime
    end: datetime
    interval_minutes: int
    offset: str
    tariff_version: str
    currency: str
    rounding: str
    rates: dict
    windows: tuple
    billed: dict
    readings: tuple


def parse_tariff(body):
    tariff = fields(decode_json(body), "version utc_offset interval_minutes currency rounding rates windows", "费率")
    require(match(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", tariff["version"]), "缺少有效的费率版本标识。")
    offset = tariff["utc_offset"]
    require(match(r"[+-](?:0[0-9]|1[0-3]):[0-5][0-9]|[+-]14:00", offset) and offset != "-00:00", "须明确提供固定 UTC 偏移。")
    interval = tariff["interval_minutes"]
    require(type(interval) is int and interval in (30, 60), "读数间隔仅支持 30 或 60 分钟。")
    require(match(r"[A-Z]{3}", tariff["currency"]), "币种须使用三位大写代码。")
    require(tariff["rounding"] in ("half_up", "half_even"), "须明确选择 half_up 或 half_even 舍入。")
    rates = tariff["rates"]
    require(isinstance(rates, dict) and 1 <= len(rates) <= 48, "须提供 1 至 48 个分时单价。")
    for band, rate in rates.items():
        require(match(CODE_PATTERN, band), "费率分段编号无效。")
        decimal_value(rate, "每千瓦时单价")
    windows = tariff["windows"]
    require(isinstance(windows, list) and 1 <= len(windows) <= 48, "须提供全天费率时段。")
    normalized = []
    for rule in windows:
        fields(rule, "start end band", "时段")
        start, end = minute_value(rule["start"]), minute_value(rule["end"])
        band = rule["band"]
        require(match(CODE_PATTERN, band) and band in rates, "时段引用了未知费率。")
        require(start < end and start % interval == end % interval == 0, "时段必须顺序排列在读数边界；跨日时段须拆为两段。")
        normalized.append((start, end, band))
    normalized.sort()
    previous_end = 0
    for start, end, _ in normalized:
        require(start == previous_end, "全天费率时段存在缺口或重叠。")
        previous_end = end
    require(previous_end == 1440 and {band for _, _, band in normalized} == set(rates), "费率时段须覆盖全天并使用所有费率分段。")
    return tariff, tuple(normalized)


def parse_bill(body, tariff):
    bill = fields(decode_json(body), "start end currency lines", "账单")
    require(bill["currency"] == tariff["currency"], "账单币种与费率不一致。")
    start, end = timestamp(bill["start"]), timestamp(bill["end"])
    interval = tariff["interval_minutes"]
    require(start < end and end - start <= timedelta(days=31), "账单窗口须为非空且不超过 31 天。")
    require(all((t.hour * 60 + t.minute) % interval == 0 for t in (start, end)), "账单边界须与读数对齐。")
    lines = bill["lines"]
    require(isinstance(lines, dict) and lines.keys() == tariff["rates"].keys(), "须逐项列出每个费率分段的账单电量及金额（含零值）。")
    for line in lines.values():
        fields(line, "kwh amount", "账单费用项")
        decimal_value(line["kwh"], "账单电量")
        decimal_value(line["amount"], "账单金额", places=2)
    return start, end, lines


def parse_readings(body, start, end, minutes):
    reader = csv.reader(io.StringIO(body.decode("utf-8-sig"), newline=""), strict=True)
    require(next(reader, None) == ["start", "energy", "unit"], "读数 CSV 表头须为 start,energy,unit。")
    step = timedelta(minutes=minutes)
    readings = {}
    for row in reader:
        line = reader.line_num
        require(len(row) == 3 and len(readings) < MAX_INTERVALS, f"第 {line} 行读数列数或总行数无效。")
        when = timestamp(row[0])
        require(start <= when < end and (when - start) % step == timedelta(), f"第 {line} 行读数不在账单区间边界。")
        require(when not in readings, f"读数重复：{row[0]}。")
        require(row[2] in ("Wh", "kWh"), f"第 {line} 行读数单位须为 Wh 或 kWh。")
        value = decimal_value(row[1], f"第 {line} 行读数", places=3 if row[2] == "Wh" else 6)
        micro_kwh = int(value * (1_000 if row[2] == "Wh" else 1_000_000))
        readings[when] = (when, line, row[1], row[2], micro_kwh)
    count = (end - start) // step
    for index in range(count):
        when = start + index * step
        require(when in readings, f"缺少读数：{when.isoformat(timespec='minutes')}。")
    return tuple(readings[when] for when in sorted(readings))


def load_case(folder):
    require(folder.is_dir() and not folder.is_symlink(), "案例须为包含三个指定文件的本地目录。")
    # Read the authoritative bytes once. Every consumer uses these same bytes for parsing and hashing.
    snapshots = {name: read_bytes(folder / name) for name in INPUTS}
    tariff, windows = parse_tariff(snapshots["tariff.json"])
    start, end, billed = parse_bill(snapshots["bill.json"], tariff)
    readings = parse_readings(snapshots["readings.csv"], start, end, tariff["interval_minutes"])
    hashes = {name: digest(body) for name, body in snapshots.items()}
    return Case(snapshots, hashes, start, end, tariff["interval_minutes"], tariff["utc_offset"],
                tariff["version"], tariff["currency"], tariff["rounding"], tariff["rates"], windows, billed, readings)
