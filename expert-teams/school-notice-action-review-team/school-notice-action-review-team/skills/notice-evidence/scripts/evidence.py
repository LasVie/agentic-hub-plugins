"""读取审批范围内的通知，核验逐项原文引用与日期。"""

from datetime import date, datetime, timedelta
from hashlib import sha256
import json
import re


OPERATIONS = {"新增", "更正", "取消", "提醒", "待确认"}
REFERENCE = re.compile(r"[A-Za-z0-9_-]{1,32}:[1-9][0-9]*:[1-9][0-9]*")
ID = re.compile(r"[A-Za-z0-9_-]{1,32}")
DATES = "[0-9]{4}-[0-9]{2}-[0-9]{2}"
SIGNALS = {
    "更正": ("更正", "改为", "调整", "改到", "变更", "改期", "延期", "提前", "以此为准", "延至"),
    "取消": ("取消", "不再", "停办", "暂停"),
    "提醒": ("提醒", "仍按", "照常", "再次"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"JSON 重复字段：{key}")
        result[key] = value
    return result


def read_json(path):
    require(path and not path.is_symlink() and path.is_file(), "请提供普通 JSON 文件")
    with path.open("rb") as stream:
        data = stream.read(1_000_001)
    require(len(data) <= 1_000_000, "JSON 文件超过 1 MB")
    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=without_duplicates)
    except (UnicodeError, json.JSONDecodeError) as e:
        raise ValueError(f"{path.name} 须为 UTF-8 JSON") from e


def fingerprint(obj):
    bits = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(bits).hexdigest()


def day(value):
    require(isinstance(value, str) and re.fullmatch(DATES, value), "日期须为 YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"无效日期：{value}") from e


def sent_at(value):
    if value is None:
        return None
    require(isinstance(value, str) and re.fullmatch(DATES + r"(?:T[0-9]{2}:[0-9]{2})?", value),
            "发文日期须为 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM，也可为空")
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"无效发文日期：{value}") from e


def short(value, length=120):
    return (isinstance(value, str) and 0 < len(value) <= length and bool(value.strip())
            and not any(ord(c) < 32 for c in value))


def validate_bundle(bundle):
    require(isinstance(bundle, dict) and set(bundle) == {"start", "end", "children", "notices"}, "原始资料字段与模板不符")
    start, end = day(bundle["start"]), day(bundle["end"])
    require(0 <= (end - start).days <= 30, "核对范围须为 1 至 31 天")
    children = bundle["children"]
    require(isinstance(children, dict) and 1 <= len(children) <= 10, "请登记 1 至 10 个孩子或班级代号")
    for key, child in children.items():
        require(ID.fullmatch(key) and isinstance(child, dict) and set(child) == {"label", "caregiver"}
                and short(child["label"]) and (child["caregiver"] is None or short(child["caregiver"])),
                f"孩子或班级资料无效：{key}")

    notices = bundle["notices"]
    require(isinstance(notices, dict) and 1 <= len(notices) <= 40, "请提供 1 至 40 份通知")
    for key, notice in notices.items():
        require(ID.fullmatch(key) and isinstance(notice, dict)
                and set(notice) == {"sent", "issuer", "scope", "text"}, f"通知结构不符：{key}")
        sent_at(notice["sent"])
        require(notice["issuer"] is None or short(notice["issuer"]), f"发文方无效：{key}")
        scope = notice["scope"]
        require(scope is None or (isinstance(scope, list) and all(isinstance(c, str) and c in children for c in scope)
                                   and len(scope) == len(set(scope))), f"适用对象无效：{key}")
        body = notice["text"]
        require(isinstance(body, str) and body.strip() and len(body) <= 4000
                and len(body.splitlines()) <= 100 and not any(ord(c) < 32 and c not in "\r\n\t" for c in body),
                f"通知文本为空或超过限额：{key}")
    return bundle


def quote_location(notice, anchor, line, quote):
    lines = notice["text"].splitlines()
    require(type(line) is int and 1 <= line <= len(lines), f"原文行号无效：{anchor}")
    body = lines[line - 1]
    require(short(quote, 300) and body.count(quote) == 1, f"摘录须在原文该行唯一出现：{anchor}:{line}")
    return f"{anchor}:{line}:{body.index(quote) + 1}", body


def dated(expression, issued, start, end):
    if expression is None:
        return None
    try:
        if re.fullmatch(DATES, expression):
            return day(expression).isoformat()
        match = re.fullmatch(r"(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日", expression)
        if match:
            year, month, number = match.groups()
            if year:
                return date(int(year), int(month), int(number)).isoformat()
            candidates = []
            for y in range(start.year, end.year + 1):
                try:
                    value = date(y, int(month), int(number))
                except ValueError:
                    continue
                if start <= value <= end:
                    candidates.append(value)
            return candidates[0].isoformat() if len(candidates) == 1 else None
        if issued:
            relative = {"今天": 0, "今日": 0, "明天": 1, "明日": 1, "后天": 2}
            if expression in relative:
                return (issued.date() + timedelta(days=relative[expression])).isoformat()
            week = re.fullmatch(r"(本|下)(?:周|星期)([一二三四五六日天])", expression)
            if week:
                weekday = "一二三四五六日".index(week[2].replace("天", "日"))
                return (issued.date() + timedelta(days=weekday - issued.weekday()
                                                 + (7 if week[1] == "下" else 0))).isoformat()
    except (ValueError, OverflowError):
        return None
    return None


def clock(expression):
    if expression is None:
        return None
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", expression)
    if match:
        hour, minute = map(int, match.groups())
        if hour < 24 and minute < 60:
            return f"{hour:02d}:{minute:02d}"
    match = re.fullmatch(r"(上午|下午|晚上)(\d{1,2})点(?:(\d{1,2})分|(半))?", expression)
    if match:
        hour, minute = int(match[2]), 30 if match[4] else int(match[3] or 0)
        unambiguous = hour < 12 or match[1] == "下午"
        if 1 <= hour <= 12 and minute < 60 and unambiguous:
            hour = hour % 12 + (0 if match[1] == "上午" else 12)
            return f"{hour:02d}:{minute:02d}"
    return None


def precedes(first, second):
    before, after = sent_at(first), sent_at(second)
    if before is None or after is None:
        return False
    if before.date() != after.date():
        return before.date() < after.date()
    return "T" in first and "T" in second and before < after


def quoted_time(value, line):
    if value is None:
        return True
    if not short(value, 40):
        return False
    before = r"(?<![0-9])" if value[0].isascii() and value[0].isdigit() else ""
    after = r"(?![0-9])" if value[-1].isascii() and value[-1].isdigit() else ""
    if value.endswith("点"):
        after = r"(?!(?:[0-9０-９半]|一刻|三刻))"
    return re.search(before + re.escape(value) + after, line) is not None


def observations(bundle, rows):
    require(isinstance(rows, dict) and set(rows) == set(bundle["notices"]),
            "两份摘录均须逐份覆盖通知；无事项写空数组")
    result = {}
    start, end = day(bundle["start"]), day(bundle["end"])
    for anchor, items in rows.items():
        require(isinstance(items, list) and len(items) <= 30, f"每份通知最多 30 条摘录：{anchor}")
        notice = bundle["notices"][anchor]
        for item in items:
            require(isinstance(item, dict) and set(item) == {"line", "quote", "op", "when", "clock", "previous"},
                    f"摘录字段不符：{anchor}")
            ref, line_text = quote_location(notice, anchor, item["line"], item["quote"])
            op, previous = item["op"], item["previous"]
            require(isinstance(op, str) and op in OPERATIONS and ref not in result, f"重复摘录或操作无效：{ref}")
            if op in SIGNALS:
                require(any(phrase in line_text for phrase in SIGNALS[op]), f"原文缺少明确的{op}依据：{ref}")
                require(previous is None or (isinstance(previous, str) and REFERENCE.fullmatch(previous)
                                              and previous != ref), f"此前条目的出处无效：{ref}")
            elif op == "新增":
                require(previous is None, f"新增条目无需此前出处：{ref}")
            else:
                require(previous is None or (isinstance(previous, str) and REFERENCE.fullmatch(previous)
                                              and previous != ref), f"待确认条目的出处无效：{ref}")
            for key in ("when", "clock"):
                value = item[key]
                require(quoted_time(value, line_text), f"时间信息须取自原文同一行：{ref}")
            result[ref] = {**item, "notice": anchor,
                           "date_iso": dated(item["when"], sent_at(notice["sent"]), start, end),
                           "time_iso": clock(item["clock"])}
            require(len(result) <= 200, "每轮最多 200 条摘录")
    return result
