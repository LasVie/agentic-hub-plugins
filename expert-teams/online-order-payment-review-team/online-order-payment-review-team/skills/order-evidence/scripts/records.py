"""读三张原始表，保留逐行出处，金额以千分之一单位的整数表示。"""

import csv
from datetime import date
from decimal import Decimal
from hashlib import sha256
import io
import json
import re


FIELDS = {
    "orders": {
        "订单号": "id", "下单日期": "date", "商户": "merchant",
        "币种": "currency", "实付应扣": "amount",
    },
    "payments": {
        "流水号": "id", "记录日期": "date", "商户": "merchant", "币种": "currency",
        "方向": "kind", "状态": "state", "金额": "amount", "订单号": "order", "退款单号": "notice",
    },
    "refunds": {
        "退款单号": "id", "确认日期": "date", "订单号": "order",
        "币种": "currency", "确认金额": "amount",
    },
}


def parse_day(text):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        raise ValueError("日期必须采用 YYYY-MM-DD 格式")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("日期不存在") from exc


def parse_row(row, through):
    optional = {"order", "notice"} if "state" in row else set()
    if any(not value for key, value in row.items() if key not in optional):
        raise ValueError("必填字段为空")
    if any(len(value) > 120 or any(ord(c) < 32 for c in value) for value in row.values()):
        raise ValueError("字段包含控制字符或超过 120 字符")
    if parse_day(row["date"]) > through:
        raise ValueError("日期晚于核对截至日期")
    if not re.fullmatch(r"[A-Z]{3}", row["currency"]):
        raise ValueError("币种应为三个大写字母")
    amount = row["amount"]
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,3})?", amount):
        raise ValueError("金额应为正数，最多九位整数和三位小数")
    row["amount"] = int(Decimal(amount) * 1000)
    if row["amount"] <= 0:
        raise ValueError("金额须大于零")
    if "state" in row:
        if row["state"] not in {"已入账", "待入账"} or row["kind"] not in {"扣款", "退款"}:
            raise ValueError("方向或状态不在允许值内")
        if row["kind"] == "扣款" and row["notice"]:
            raise ValueError("扣款流水不可填写退款单号")
    return row


def read_register(source, as_of):
    through = parse_day(as_of)
    register = {"截至日期": as_of, "文件摘要": {}}
    for table, fields in FIELDS.items():
        name = f"{table}.csv"
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{name} 须为普通文件")
        with path.open("rb") as stream:
            data = stream.read(512_001)
        if len(data) > 512_000:
            raise ValueError(f"{name} 超过 512 KB")
        register["文件摘要"][name] = sha256(data).hexdigest()
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        try:
            header = next(reader, [])
            if len(header) != len(fields) or set(header) != set(fields):
                raise ValueError("表头与模板不符")
            rows = {}
            while True:
                line = reader.line_num + 1
                values = next(reader, None)
                if values is None:
                    break
                if not values:
                    continue
                if len(values) != len(header):
                    raise ValueError("列数与表头不符")
                row = parse_row({fields[k]: v.strip() for k, v in zip(header, values)}, through)
                if row["id"] in rows:
                    raise ValueError(f"重复标识 {row['id']}")
                if len(rows) == 100:
                    raise ValueError("每张表最多 100 项")
                row["source"] = f"{name}:{line}"
                rows[row["id"]] = row
            register[table] = rows
        except (ValueError, csv.Error) as exc:
            raise ValueError(f"{name}:{reader.line_num} {exc}") from exc

    if not register["orders"]:
        raise ValueError("订单表至少需要一项")
    for notice in register["refunds"].values():
        order = register["orders"].get(notice["order"])
        if order is None or order["currency"] != notice["currency"] or notice["date"] < order["date"]:
            raise ValueError(f"{notice['source']} 退款通知的订单、币种或日期冲突")
    return register


def json_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def money(amount):
    return f"{Decimal(amount) / 1000:.3f}".rstrip("0").rstrip(".") or "0"
