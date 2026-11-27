"""读取 SRT 和基于旧版时间的剪辑记录。"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import re


CLOCK = r"[0-9]{2,3}:[0-5][0-9]:[0-5][0-9][,.][0-9]{3}"
ARROW = re.compile(rf"({CLOCK})[ \t]+-->[ \t]+({CLOCK})")
MAX_TIME = 3_600_000_000


@dataclass(frozen=True)
class Cue:
    number: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    inserted: int

    @property
    def shift(self):
        return self.inserted - (self.end - self.start)


@dataclass(frozen=True)
class Scope:
    edits: tuple[Edit, ...]
    approved_end: int | None
    revised_end: int | None


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(CLOCK, value):
        raise ValueError("时间须写成 HH:MM:SS,mmm")
    hours, minutes, seconds, millis = map(int, re.split("[:,.]", value))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def clock(value):
    if value is None:
        return ""
    total, millis = divmod(value, 1000)
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def read_text(path: Path):
    with path.open("rb") as stream:
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError(f"{path.name} 超过 2 MB")
    try:
        return raw.decode("utf-8-sig"), sha256(raw).hexdigest()
    except UnicodeDecodeError:
        raise ValueError(f"{path.name} 须使用 UTF-8 编码") from None


def srt(path):
    data, digest = read_text(path)
    if path.suffix.lower() != ".srt":
        raise ValueError("字幕路径须为 .srt 文件")
    data = data.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    cues = []
    numbers = set()
    if not data.strip():
        return cues, digest
    for index, block in enumerate(re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", data), 1):
        if not block.strip():
            continue
        lines = block.split("\n")
        number = lines[0].strip()
        time = ARROW.fullmatch(lines[1].strip()) if len(lines) >= 3 else None
        body = "\n".join(lines[2:])
        if not re.fullmatch(r"[0-9]{1,12}", number) or time is None or not body.strip():
            raise ValueError(f"{path.name} 第 {index} 条须有数字编号、起止时间和正文")
        if number in numbers:
            raise ValueError(f"{path.name} 重复字幕编号 {number}")
        if any(ord(char) < 32 and char not in "\n\t" for char in body):
            raise ValueError(f"{path.name} 第 {index} 条含不支持的控制字符")
        start, end = map(timestamp, time.groups())
        if start >= end:
            raise ValueError(f"{path.name} 第 {index} 条的结束时间须晚于开始时间")
        numbers.add(number)
        cues.append(Cue(number, start, end, body))
    if len(cues) > 10000:
        raise ValueError("每份 SRT 最多支持 10000 条字幕")
    return cues, digest


def record(path):
    data, digest = read_text(path)
    try:
        value = json.loads(data)
    except (ValueError, RecursionError):
        raise ValueError(f"{path.name} 不是有效的 JSON") from None
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} 的顶层须为 JSON 对象")
    return value, digest


def edit_scope(path):
    if path is None:
        return None, None
    data, digest = record(path)
    if data.keys() - {"edits", "approved_duration", "revised_duration"}:
        raise ValueError("剪辑记录含未知字段")
    approved = timestamp(data["approved_duration"]) if "approved_duration" in data else None
    revised = timestamp(data["revised_duration"]) if "revised_duration" in data else None
    rows = data.get("edits")
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("剪辑记录须有 edits 列表，最多 100 段")
    edits = []
    for index, entry in enumerate(rows, 1):
        if not isinstance(entry, dict) or entry.keys() != {"start", "end", "new_duration_ms"}:
            raise ValueError(f"第 {index} 段须提供旧版 start、end 及新时长 new_duration_ms")
        start, end = timestamp(entry["start"]), timestamp(entry["end"])
        inserted = entry["new_duration_ms"]
        if type(inserted) is not int or not 0 <= inserted < MAX_TIME or end < start or start == end and inserted == 0:
            raise ValueError(f"第 {index} 段起止或新时长无效")
        if approved is not None and end > approved:
            raise ValueError(f"第 {index} 段超出已确认版本时长")
        edits.append(Edit(start, end, inserted))
    edits.sort(key=lambda edit: edit.start)
    if any(b.start < a.end or b.start == a.start for a, b in zip(edits, edits[1:])):
        raise ValueError("剪辑区间重叠或起点相同，请先合并为明确的区间")
    shift = sum(edit.shift for edit in edits)
    if approved is not None:
        expected = approved + shift
        if revised is not None and revised != expected:
            raise ValueError("按剪辑记录计算的成片时长与提供的改版时长不一致")
        revised = expected
    elapsed = 0
    for edit in edits:
        if revised is not None and edit.start + elapsed + edit.inserted > revised:
            raise ValueError("剪辑后的变化区间超出改版时长")
        elapsed += edit.shift
    if revised is not None and not 0 <= revised < MAX_TIME:
        raise ValueError("按剪辑计算的改版时长超出支持范围")
    return Scope(tuple(edits), approved, revised), digest


def load_inputs(approved_path, edits_path):
    approved, approved_sha = srt(approved_path)
    scope, edits_sha = edit_scope(edits_path)
    if scope is not None and scope.approved_end is not None and any(cue.end > scope.approved_end for cue in approved):
        raise ValueError("已确认字幕超出记录中的旧版时长")
    return approved, scope, {"approved_sha256": approved_sha, "edits_sha256": edits_sha}


def encode_srt(cues, times):
    blocks = []
    for cue in cues:
        start, end = times.get(cue.number, (cue.start, cue.end))
        blocks.append(f"{cue.number}\n{clock(start)} --> {clock(end)}\n{cue.text}")
    return "\n\n".join(blocks) + "\n" if blocks else ""
