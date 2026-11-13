

# ==========================================================================
# 原生工具封装（本团队独立编写）：两个只读工具，调用上面移植的函数
# ==========================================================================
import asyncio
from copy import deepcopy
import threading
from typing import Any, AsyncIterator

from openjiuwen.core.foundation.tool import Tool, ToolCard

TOOL_PREFIX = "adds_up_"
MAX_FILES = 10
MAX_ROWS_LIMIT = 500
MAX_PATH_CHARS = 1000
MAX_REPORT_CHARS = 80000
MAX_SAMPLE_N = 1000000
_LOCK = threading.Lock()   # 上面的规则用全局变量 STATS、FMT 记录当前文件，所以同一时刻只允许一个调用在运行

NOTE_ZH = ("请用简体中文向用户汇报。线索只是候选，必须对照文档内容逐条确认并自己重算后才能当作发现；"
           "只报告材料本身能支持的内容，不要用记忆里的外部事实去“纠正”文档里的数字；不要编造没有返回的数据。")

_GRIM_VALUE_RE = re.compile(r"^[+]?\d+(?:[.,]\d+)?$")

CATALOG = {
    "extract": {
        "description": "读取本机上的文档并核对其中的数字：从 .docx、.pptx、.xlsx/.xlsm、.csv/.tsv、.md/.txt、.pdf 里取出"
                       "文字、表格和公式（电子表格会给出每个单元格的公式和显示值），再按规则列出算术“线索”（合计与分项对不上、"
                       "占比与百分比对不上、公式范围漏行、星期与日期对不上、时长与起止日期对不上、单位混用等），并说明规则检验了多少、"
                       "多少相符。线索只是候选，需要对照内容确认。只读文件，不改文件、不联网。可一次传入最多 10 个文件，便于跨文件对照。"
                       "路径必须是本机能读到的文件路径（绝对路径最稳妥）。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["files"], "properties": {
            "files": {"type": "array", "minItems": 1, "maxItems": MAX_FILES,
                      "items": {"type": "string", "minLength": 1, "maxLength": MAX_PATH_CHARS},
                      "description": "要核对的文件路径列表（最多 10 个）。支持 docx、pptx、xlsx、xlsm、csv、tsv、md、txt、pdf；"
                                     "旧版 doc、xls、ppt 要先另存为新格式。"},
            "max_rows": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS_LIMIT,
                         "description": "超过这个行数的长表只打印开头、结尾和有线索的行（规则仍然检查每一行），默认 60。"},
            "all_rows": {"type": "boolean",
                         "description": "为 true 时打印每个表的每一行（输出会很长），默认 false。需要通读中间各行找异常值时才用。"},
        }},
    },
    "grim": {
        "description": "GRIM 检验：文档里报告的百分比或平均值，能不能由“整数个数据”得到。已知样本量 n 和报告的百分比"
                       "（占 n 的比例）或平均值（每个数据都是整数，例如计数、量表分值），判断是否存在整数总数使其四舍五入后等于报告值，"
                       "并给出最接近的可能值。只适用于“n 个整数数据的占比或平均”，不适用于增长率、金额占比，也不适用于已给出个数的情况；"
                       "n 很大且小数位很少时几乎没有判别力。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["n", "value", "kind"], "properties": {
            "n": {"type": "integer", "minimum": 1, "maximum": MAX_SAMPLE_N, "description": "样本量 n（正整数）。"},
            "value": {"type": "string", "minLength": 1, "maxLength": 20,
                      "description": "报告的数值，按文档里的写法填，保留小数位，例如 \"37.5\" 或 \"3.48\"；百分比可带 % 号。"},
            "kind": {"type": "string", "enum": ["percent", "mean"],
                     "description": "percent：value 是占 n 的百分比；mean：value 是 n 个整数数据的平均值。"},
        }},
    },
}


def error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def validate(tool: str, arguments: Any) -> tuple[dict | None, str | None]:
    """返回 (规整后的参数, 错误信息)。"""
    if not isinstance(arguments, dict):
        return None, "参数必须是一个对象。"
    allowed = set(CATALOG[tool]["schema"]["properties"])
    extra = sorted(set(arguments) - allowed)
    if extra:
        return None, "不认识的参数：%s。" % "、".join(extra)
    if tool == "extract":
        files = arguments.get("files")
        if not isinstance(files, list) or not files:
            return None, "files 必须是至少含一个路径的列表。"
        if len(files) > MAX_FILES:
            return None, "一次最多核对 %d 个文件。" % MAX_FILES
        cleaned = []
        for f in files:
            if not isinstance(f, str) or not f.strip():
                return None, "files 里的每一项都必须是非空字符串。"
            if len(f) > MAX_PATH_CHARS or "\x00" in f:
                return None, "文件路径过长或含有非法字符。"
            cleaned.append(f.strip())
        max_rows = arguments.get("max_rows", 60)
        if isinstance(max_rows, bool) or not isinstance(max_rows, int) or not 1 <= max_rows <= MAX_ROWS_LIMIT:
            return None, "max_rows 必须是 1 到 %d 之间的整数。" % MAX_ROWS_LIMIT
        all_rows = arguments.get("all_rows", False)
        if not isinstance(all_rows, bool):
            return None, "all_rows 必须是 true 或 false。"
        return {"files": cleaned, "max_rows": max_rows, "all_rows": all_rows}, None
    n = arguments.get("n")
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MAX_SAMPLE_N:
        return None, "n 必须是 1 到 %d 之间的整数。" % MAX_SAMPLE_N
    kind = arguments.get("kind")
    if kind not in ("percent", "mean"):
        return None, "kind 必须是 percent 或 mean。"
    value = arguments.get("value")
    if not isinstance(value, str) or not value.strip():
        return None, "value 必须是字符串，例如 \"37.5\"。"
    text = value.strip().rstrip("%％").strip()
    if not _GRIM_VALUE_RE.match(text):
        return None, "value 必须是一个非负数（可带小数，百分比可带 % 号），例如 \"37.5\"。"
    if kind == "percent" and Decimal(text.replace(",", ".")) > 100:
        return None, "百分比不能超过 100。"
    return {"n": n, "value": text, "kind": kind}, None


def run_extract_tool(values: dict) -> dict:
    with _LOCK:
        text, results = run_extract(values["files"], values["max_rows"], values["all_rows"])
    files = []
    for res in results:
        files.append({"file": res["file"], "type": res.get("type", ""), "error": res.get("error"),
                      "lead_count": len(res.get("leads") or []), "note_count": len(res.get("notes") or []),
                      "rules_covered": res.get("held", "")})
    if all(item["error"] for item in files):
        return error("ALL_FILES_FAILED", "所有文件都没有读成：" + "；".join(
            "%s：%s" % (item["file"], item["error"]) for item in files), files=files)
    truncated = len(text) > MAX_REPORT_CHARS
    if truncated:
        text = text[:MAX_REPORT_CHARS] + ("\n\n（输出过长，已在 %d 个字符处截断。请减少文件数、调小 max_rows，"
                                          "或分批核对。线索和“规则覆盖了什么”可能不完整。）\n" % MAX_REPORT_CHARS)
    return {"ok": True, "tool": TOOL_PREFIX + "extract", "message": NOTE_ZH, "report_text": text, "files": files,
            "lead_count": sum(item["lead_count"] for item in files), "truncated": truncated}


def run_grim_tool(values: dict) -> dict:
    is_pct = values["kind"] == "percent"
    matches, near, decimals = grim(values["n"], values["value"], is_pct)
    lines = grim_report(values["n"], values["value"], is_pct)
    return {"ok": True, "tool": TOOL_PREFIX + "grim", "arguments": dict(values), "message": NOTE_ZH,
            "consistent": bool(matches), "decimals": decimals,
            "matching_counts_or_totals": [int(k) for k in matches[:20]],
            "nearest": [{"count_or_total": int(k), "gives": str(v)} for k, v in near],
            "result_zh": lines}


RUNNERS = {"extract": run_extract_tool, "grim": run_grim_tool}


async def call_tool(name: str, arguments: Any) -> dict:
    values, message = validate(name, arguments)
    if message:
        return error("INVALID_ARGUMENTS", message, tool=TOOL_PREFIX + name)
    try:
        return await asyncio.to_thread(RUNNERS[name], values)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # 不向用户暴露内部堆栈，也不伪造结果
        return error("INTERNAL_ERROR", "工具内部出错（%s）；本次没有返回结果。" % type(exc).__name__,
                     tool=TOOL_PREFIX + name)


class AddsUpTool(Tool):
    key = ""

    def __init__(self) -> None:
        entry = CATALOG[self.key]
        super().__init__(ToolCard(id=TOOL_PREFIX + self.key, name=TOOL_PREFIX + self.key,
                                  description=entry["description"], input_params=deepcopy(entry["schema"])))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_tool(self.key, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class AddsUpExtractTool(AddsUpTool):
    key = "extract"


class AddsUpGrimTool(AddsUpTool):
    key = "grim"
