"""Bounded Sheets reads and explicit range/row writes."""
import json
import math
import re
from urllib.parse import quote

SLUG = "google-sheets"
LABEL = "Google 表格连接器"
SCOPE = "https://www.googleapis.com/auth/spreadsheets"
BASE = "https://sheets.googleapis.com/v4"
CELLS = re.compile(r"([A-Z]{1,3})([1-9][0-9]{0,6})(?::([A-Z]{1,3})([1-9][0-9]{0,6}))?\Z")
METADATA = "spreadsheetId,spreadsheetUrl,properties(title),sheets(properties(sheetId,title,gridProperties(rowCount,columnCount),sheetType))"


def column(value):
    number = 0
    for letter in value:
        number = number * 26 + ord(letter) - ord("A") + 1
    return number


def area(tab, cells):
    from google_api import invalid, text

    text(tab, "工作表名", 100)
    match = CELLS.fullmatch(cells.upper())
    if not match:
        raise invalid("请传入有限的 A1 范围，例如 A2:C20。")
    left, top, right, bottom = match.groups()
    height = int(bottom or top) - int(top) + 1
    width = column(right or left) - column(left) + 1
    if height < 1 or width < 1 or height * width > 5000:
        raise invalid("读取或写入的矩形最多包含 5000 个单元格。")
    return "'" + tab.replace("'", "''") + "'!" + cells.upper(), height, width


def base(file):
    from google_api import file_id

    return f"/spreadsheets/{file_id(file, 'spreadsheets')}"


def info(api, args):
    return api.json("GET", base(args.file), params={"fields": METADATA})


def create(api, args):
    from google_api import text

    return api.json("POST", "/spreadsheets", params={"fields": METADATA},
                    body={"properties": {"title": text(args.title, "标题", 200)}})


def read(api, args):
    a1, _, _ = area(args.tab, args.range)
    return api.json("GET", base(args.file) + "/values/" + quote(a1, safe=""),
                    params={"valueRenderOption": args.render, "majorDimension": "ROWS"})


def matrix(args, height, width):
    from google_api import invalid, text

    def scalar(value):
        if type(value) is str:
            text(value, "单元格文本", 10000, multiline=True, allow_empty=True)
            if args.formulas:
                if value.startswith("="):
                    return {"formulaValue": value}
                return {"stringValue": value}
            return value
        if type(value) is int and abs(value) > 9007199254740991:
            raise ValueError
        if type(value) is float and not math.isfinite(value):
            raise ValueError
        if args.formulas:
            if type(value) is bool:
                return {"boolValue": value}
            return {"numberValue": value}
        return value

    try:
        raw = json.loads(args.values_json)
        if not isinstance(raw, list) or not raw or len(raw) > height:
            raise ValueError
        result = []
        for row in raw:
            if not isinstance(row, list) or len(row) != width:
                raise ValueError
            if any(type(value) not in {str, int, float, bool} for value in row):
                raise ValueError
            result.append([scalar(value) for value in row])
        return result
    except (TypeError, ValueError, OverflowError):
        raise invalid("值须为二维 JSON 数组，每行列数与目标范围一致，最多 5000 格。") from None


def write(api, args):
    from google_api import Error, invalid

    a1, height, width = area(args.tab, args.range)
    data = matrix(args, 5000 // width if args.action == "append" else height, width)
    route = base(args.file)
    value_route = route + "/values/" + quote(a1, safe="")
    if args.action == "append":
        return api.json("POST", value_route + ":append",
                        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS",
                                "includeValuesInResponse": "true"},
                        body={"majorDimension": "ROWS", "values": data})
    if len(data) != height:
        raise invalid("更新数据的行数必须与指定范围完全一致。")
    metadata = api.json("GET", route, params={
        "ranges": a1,
        "fields": "sheets(properties(sheetId,title),data(rowData(values(userEnteredValue(formulaValue)))))",
    })
    target = next((item for item in metadata.get("sheets", [])
                   if item["properties"]["title"] == args.tab), None)
    if target is None:
        raise invalid("找不到指定工作表。")
    if not args.replace_formulas and any(
        "formulaValue" in cell.get("userEnteredValue", {})
        for block in target.get("data", []) for row in block.get("rowData", [])
        for cell in row.get("values", [])
    ):
        raise Error("formula_protected", "目标范围含有公式。请缩小范围，或明确允许替换公式。")
    if not args.formulas:
        return api.json("PUT", value_route, params={"valueInputOption": "RAW", "includeValuesInResponse": "true"},
                        body={"majorDimension": "ROWS", "values": data})
    left, top, _, _ = CELLS.fullmatch(args.range.upper()).groups()
    rows = [{"values": [{"userEnteredValue": value} for value in row]} for row in data]
    batch = api.json("POST", route + ":batchUpdate", body={"requests": [{"updateCells": {
        "start": {"sheetId": target["properties"]["sheetId"], "rowIndex": int(top) - 1, "columnIndex": column(left) - 1},
        "rows": rows, "fields": "userEnteredValue",
    }}]})
    return {"spreadsheetId": batch.get("spreadsheetId"), "updatedRange": a1, "updatedRows": len(data)}


def register(commands):
    sheet_info = commands.add_parser("info", help="列出工作表名称和大小")
    sheet_info.set_defaults(operation=info)
    sheet_info.add_argument("--file", required=True, help="表格链接或标识")
    creation = commands.add_parser("create", help="新建表格")
    creation.set_defaults(operation=create)
    creation.add_argument("--title", required=True, help="表格标题")
    reader = commands.add_parser("read", help="读取指定工作表范围")
    update = commands.add_parser("update", help="更新指定矩形范围")
    append = commands.add_parser("append", help="在指定表格区域的逻辑表末尾追加行")
    for command in (reader, update, append):
        command.add_argument("--file", required=True, help="表格链接或标识")
        command.add_argument("--tab", required=True, help="准确的工作表名称")
        command.add_argument("--range", required=True, help="有限 A1 范围，例如 A2:C20")
    reader.set_defaults(operation=read)
    reader.add_argument("--render", choices=("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"),
                        default="FORMATTED_VALUE", help="读取显示值、原始值或公式")
    for command in (update, append):
        command.set_defaults(operation=write, formulas=False, replace_formulas=False)
        command.add_argument("--values-json", required=True, help="二维 JSON 数组")
    update.add_argument("--formulas", action="store_true", help="将以等号开头的字符串明确写为公式")
    update.add_argument("--replace-formulas", action="store_true", help="允许覆盖指定范围内的现有公式")
