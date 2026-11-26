"""把盘点数据转成统一单位的可核对事实。"""
from datetime import date
from hashlib import sha256
import json
import re


def read_json(path):
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError("文件超过 1 MB")
    try:
        result = json.loads(raw)
    except (ValueError, RecursionError):
        raise ValueError("需要有效的 UTF-8 JSON") from None
    if not isinstance(result, dict):
        raise ValueError("JSON 顶层必须是对象")
    return result, sha256(raw).hexdigest()


def day(value, label):
    try:
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value)
    except ValueError:
        pass
    raise ValueError(f"{label}：日期须为有效的 YYYY-MM-DD")


def quantity(value, label, *, optional=False, positive=False):
    """以千分之一单位计数，保持包装和消耗量比较精确。"""
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{label}：缺少有效数量")
    match = re.fullmatch(r"([0-9]{1,6})(?:\.([0-9]{1,3}))?", str(value))
    if not match:
        raise ValueError(f"{label}：数量应为非负数，最多保留三位小数")
    result = int(match[1]) * 1000 + int((match[2] or "").ljust(3, "0"))
    if result == 0 and positive:
        raise ValueError(f"{label}：包装量须大于零")
    return result


def label(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 120:
        raise ValueError(f"{field}：须提供非空文字（最多 120 字）")
    if not value.isprintable():
        raise ValueError(f"{field}：不能包含换行或其他控制字符")
    return value.strip()


def entries(value, field, limit=60):
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{field}：须为最多 {limit} 项的对象列表")
    return value


def compatible(row, variant):
    actual = row.get("variant")
    if actual is not None:
        actual = label(actual, "规格")
    if variant is None or actual == variant:
        return "compatible"
    return "unknown" if actual is None else "incompatible"


def normalize_item(item, start, horizon):
    name = label(item.get("name"), "品名")
    unit = label(item.get("unit"), f"{name}的单位")
    variant = item.get("variant")
    if variant is not None:
        variant = label(variant, f"{name}的所需规格")
    stock, stock_uncertain = 0, False
    notes = []
    for row in entries(item.get("stock"), f"{name}的盘点"):
        amount = quantity(row.get("qty"), f"{name}的存量", optional=True)
        fit = compatible(row, variant)
        if fit == "incompatible":
            notes.append("盘点含不适配规格，已排除")
        elif fit == "unknown" or amount is None:
            if amount != 0:
                stock_uncertain = True
                notes.append("盘点量或适配待确认")
        else:
            stock += amount
    arriving = []
    for row in entries(item.get("arrivals", []), f"{name}的到货"):
        status = row.get("status")
        if status not in ("confirmed", "pending"):
            raise ValueError(f"{name}：到货状态须为已确认或待定")
        when = row.get("date")
        offset = (day(when, f"{name}的到货").toordinal() - start) if when is not None else None
        amount = quantity(row.get("qty"), f"{name}的到货量", optional=True)
        if status == "pending" or offset is None or amount is None:
            notes.append("待定或缺少日期或数量的到货未计入")
        elif not 0 <= offset < horizon:
            notes.append("覆盖期外到货未计入")
        elif compatible(row, variant) != "compatible":
            notes.append("到货规格待确认或不适配，未计入")
        else:
            arriving.append((offset, amount))
    packs = set()
    for row in entries(item.get("packs", []), f"{name}的包装"):
        amount = quantity(row.get("qty"), f"{name}的包装量", positive=True)
        if compatible(row, variant) == "compatible":
            packs.add(amount)
        else:
            notes.append("存在规格待确认或不适配的包装")
    return {
        "name": name, "unit": unit, "variant": variant, "on_hand": stock,
        "stock_uncertain": stock_uncertain,
        "daily": quantity(item.get("daily_use"), f"{name}的日耗", optional=True),
        "capacity": quantity(item.get("capacity"), f"{name}的存放上限", optional=True),
        "arrivals": sorted([offset, amount] for offset, amount in arriving),
        "packs": sorted(packs), "notes": sorted(set(notes)),
    }


def intake(source):
    original, digest = read_json(source)
    start = day(original.get("as_of"), "盘点日")
    end = day(original.get("next_shop"), "下次采购日")
    horizon = (end - start).days
    if not 1 <= horizon <= 90:
        raise ValueError("下次采购须在盘点后的 1 至 90 天内")
    rows = entries(original.get("items"), "日用品", limit=100)
    if not rows:
        raise ValueError("至少需要一种日用品")
    items = [normalize_item(item, start.toordinal(), horizon) for item in rows]
    keys = [(item["name"], item["variant"]) for item in items]
    if len(set(keys)) != len(keys):
        raise ValueError("同一品名和规格出现多次，请先合并盘点")
    return {
        "type": "intake", "schema": 1, "source_sha256": digest,
        "as_of": start.isoformat(), "next_shop": end.isoformat(),
        "horizon": horizon, "items": items,
    }
