"""冻结的库存模型与阶段间文件合约。"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat

VERSION = "1.0.0"
MAX_JSON = 128 * 1024
ID_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}")


class InputError(ValueError):
    """用户可修正的输入或证据错误。"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def same_value(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def unique_pairs(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("JSON 字段重复。")
        result[key] = value
    return result


def reject_constant(_: str) -> None:
    raise InputError("JSON 必须使用有限数值。")


def document(path: Path) -> tuple[bytes, dict]:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise InputError("输入必须是普通 JSON 文件。")
        raw = stream.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise InputError("JSON 文件超过 128 KiB。")
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except InputError:
        raise
    except (ValueError, RecursionError, OverflowError) as error:
        raise InputError("输入必须是有效的 UTF-8 JSON。") from error
    if not isinstance(value, dict):
        raise InputError("JSON 根必须是对象。")
    return raw, value


def write_new(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(raw)


def fields(obj: object, expected: set[str], label: str) -> None:
    if not isinstance(obj, dict) or obj.keys() != expected:
        raise InputError(f"{label}字段缺失、未知或格式错误。")


def integer(value: object, lo: int, hi: int, label: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise InputError(f"{label}须为 {lo}–{hi} 的整数。")
    return value


def label(value: object, context: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 80 or not value.isprintable() or value.strip() != value:
        raise InputError(f"{context}须为 1–80 个非控制字符，首尾不能有空格。")
    return value


def identifier(value: object) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise InputError("编号须以英文字母开头，限 32 个字母、数字、下划线或连字符。")
    return value


def collection(value: object, cap: int, context: str) -> list:
    if not isinstance(value, list) or not 1 <= len(value) <= cap:
        raise InputError(f"{context}须包含 1–{cap} 条记录。")
    return value


@dataclass(frozen=True)
class Board:
    id: str
    material: str
    length: int
    left: int
    right: int

    @property
    def capacity(self) -> int:
        return self.length - self.left - self.right


@dataclass(frozen=True)
class Part:
    id: str
    ordinal: int
    material: str
    length: int

    @property
    def key(self) -> tuple[str, int]:
        return self.id, self.ordinal


@dataclass(frozen=True)
class Case:
    title: str
    kerf: int
    boards: tuple[Board, ...]
    parts: tuple[Part, ...]
    sha: str


def case_from(path: Path) -> tuple[bytes, Case]:
    raw, data = document(path)
    fields(data, {"schema_version", "title", "kerf_mm", "stock", "parts"}, "案例")
    integer(data["schema_version"], 1, 1, "案例格式版本")
    title = label(data["title"], "案例标题")
    kerf = integer(data["kerf_mm"], 0, 100, "每件锯缝占量")
    boards = []
    for row in collection(data["stock"], 12, "库存"):
        fields(row, {"id", "material", "length_mm", "trim_start_mm", "trim_end_mm"}, "库存")
        board = Board(identifier(row["id"]), label(row["material"], "材质及规格"),
                      integer(row["length_mm"], 1, 20000, "库存长度"),
                      integer(row["trim_start_mm"], 0, 19999, "首端修边"),
                      integer(row["trim_end_mm"], 0, 19999, "尾端修边"))
        if board.capacity <= 0:
            raise InputError(f"库存 {board.id} 两端修边后必须有正的可用长度。")
        boards.append(board)
    if len({board.id for board in boards}) != len(boards):
        raise InputError("库存编号重复。")
    parts = []
    seen = set()
    for row in collection(data["parts"], 24, "零件"):
        fields(row, {"id", "material", "length_mm", "quantity"}, "零件")
        part_id = identifier(row["id"])
        if part_id in seen:
            raise InputError("零件编号重复。")
        seen.add(part_id)
        material = label(row["material"], "材质及规格")
        length = integer(row["length_mm"], 1, 20000, "成品长度")
        amount = integer(row["quantity"], 1, 24, "数量")
        if len(parts) + amount > 24:
            raise InputError("合计最多 24 件零件。")
        parts.extend(Part(part_id, index, material, length) for index in range(1, amount + 1))
    return raw, Case(title, kerf, tuple(boards), tuple(parts), digest(raw))


def stamp(case: Case, role: str) -> dict:
    return {"schema_version": 1, "version": VERSION, "role": role, "case_sha256": case.sha}


def text_items(values: object, context: str) -> list:
    if not isinstance(values, list) or len(values) > 12:
        raise InputError(f"{context}最多 12 条。")
    return [label(item, context) for item in values]


def stock_report(case: Case, notes: list, issues: list) -> dict:
    return {
        **stamp(case, "stock-analyst"),
        "notes": text_items(notes, "库存说明"),
        "issues": text_items(issues, "库存待澄清项"),
        "usable_mm": {board.id: board.capacity for board in case.boards},
        "requested_pieces": len(case.parts),
    }


def accept_stock(case: Case, report: dict) -> None:
    if not same_value(report, stock_report(case, report.get("notes"), report.get("issues"))):
        raise InputError("库存报告与输入摘要或重算结果不一致。")
    if report["issues"]:
        raise InputError("库存待澄清项尚未解决。")
