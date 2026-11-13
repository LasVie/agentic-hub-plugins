import asyncio
from copy import deepcopy
from typing import Any, AsyncIterator

from openjiuwen.core.foundation.tool import Tool, ToolCard

TOOL_PREFIX = "a11y_"
MAX_PATHS = 10
MAX_PATH_CHARS = 1000
MAX_FILES = 3000                 # 一次调用最多扫描的文件数
MAX_TOTAL_BYTES = 200 * 1024 * 1024
MAX_ISSUES_LIMIT = 500
DEFAULT_MAX_ISSUES = 100
MAX_PAIRS = 50
MAX_COLOR_CHARS = 64
SUPPORTED_EXTS = EXTS            # 上游支持的扩展名

NOTE_ZH = ("请用简体中文向用户汇报。这是静态扫描：只能看到标记里直接写出来的问题，看不到运行时生成的内容、"
           "传给自定义组件的属性和样式表里的 CSS；没有发现问题不等于符合 WCAG，仍需键盘和读屏软件的人工检查。"
           "每条发现都要结合上下文确认后再当作问题；修改代码要尽量小，并说明改了什么。")

CATALOG = {
    "scan": {
        "description": "静态扫描网页界面代码里的无障碍问题（对照 WCAG 2.2 AA）：读取 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro "
                       "文件或文件夹，只读不改，报告缺 alt 的图片、没有名称的按钮和链接、没有标签的表单项、只能点击不能用键盘操作的元素、"
                       "正数 tabindex、缺少 lang、禁止缩放、自动播放、标题层级跳跃、去掉焦点轮廓等，每条带文件、行号、规则名、"
                       "WCAG 成功标准编号和中文说明。这是静态扫描，看不到运行时生成的内容、传给自定义组件的属性和样式表里的 CSS；"
                       "没有发现问题不等于符合 WCAG。文件夹里会跳过 node_modules、dist、build 等目录和符号链接。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["paths"], "properties": {
            "paths": {"type": "array", "minItems": 1, "maxItems": MAX_PATHS, "items": {"type": "string", "minLength": 1, "maxLength": MAX_PATH_CHARS},
                      "description": "要扫描的文件或文件夹路径列表（最多 10 个，建议用完整路径）。文件只支持 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro。"},
            "errors_only": {"type": "boolean", "description": "为 true 时只报告错误，不报告警告，默认 false。"},
            "max_issues": {"type": "integer", "minimum": 1, "maximum": MAX_ISSUES_LIMIT,
                           "description": "最多列出多少条问题，默认 100（统计数字始终覆盖全部问题）。"},
        }},
    },
    "contrast": {
        "description": "计算文字色和背景色的 WCAG 对比度，并判断是否达标：AA 正文 4.5:1、AA 大字 3:1（24px，或加粗 18.66px 以上）、"
                       "界面组件和图标 3:1，AAA 正文 7:1、AAA 大字 4.5:1。颜色可写 #rgb、#rrggbb、#rrggbbaa、rgb()、rgba() 或 20 个基本英文颜色名；"
                       "带透明度的前景色按背景色混合后计算，背景色的透明度被忽略（按不透明处理）。不会读取主题或样式文件，颜色需要先从代码里找出来。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["pairs"], "properties": {
            "pairs": {"type": "array", "minItems": 1, "maxItems": MAX_PAIRS, "items": {
                "type": "object", "additionalProperties": False, "required": ["foreground", "background"], "properties": {
                    "foreground": {"type": "string", "minLength": 1, "maxLength": MAX_COLOR_CHARS, "description": "文字（或图标、边框）的颜色，例如 \"#6b7280\"。"},
                    "background": {"type": "string", "minLength": 1, "maxLength": MAX_COLOR_CHARS, "description": "背景颜色，例如 \"#ffffff\"。"}}},
                "description": "要检查的颜色对列表（最多 50 对）。"},
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
    if tool == "scan":
        paths = arguments.get("paths")
        if not isinstance(paths, list) or not paths:
            return None, "paths 必须是至少含一个路径的列表。"
        if len(paths) > MAX_PATHS:
            return None, "一次最多扫描 %d 个路径。" % MAX_PATHS
        cleaned = []
        for item in paths:
            if not isinstance(item, str) or not item.strip():
                return None, "paths 里的每一项都必须是非空字符串。"
            if len(item) > MAX_PATH_CHARS or "\x00" in item:
                return None, "路径过长或含有非法字符。"
            cleaned.append(item.strip())
        errors_only = arguments.get("errors_only", False)
        if not isinstance(errors_only, bool):
            return None, "errors_only 必须是 true 或 false。"
        max_issues = arguments.get("max_issues", DEFAULT_MAX_ISSUES)
        if isinstance(max_issues, bool) or not isinstance(max_issues, int) or not 1 <= max_issues <= MAX_ISSUES_LIMIT:
            return None, "max_issues 必须是 1 到 %d 之间的整数。" % MAX_ISSUES_LIMIT
        return {"paths": cleaned, "errors_only": errors_only, "max_issues": max_issues}, None
    pairs = arguments.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return None, "pairs 必须是至少含一对颜色的列表。"
    if len(pairs) > MAX_PAIRS:
        return None, "一次最多检查 %d 对颜色。" % MAX_PAIRS
    cleaned_pairs = []
    for item in pairs:
        if not isinstance(item, dict) or set(item) != {"foreground", "background"}:
            return None, "pairs 里的每一项都必须是只含 foreground 和 background 两个字段的对象。"
        for key in ("foreground", "background"):
            value = item[key]
            if not isinstance(value, str) or not value.strip():
                return None, "%s 必须是非空字符串，例如 \"#6b7280\"。" % key
            if len(value) > MAX_COLOR_CHARS or "\x00" in value:
                return None, "%s 太长或含有非法字符。" % key
        cleaned_pairs.append({"foreground": item["foreground"].strip(), "background": item["background"].strip()})
    return {"pairs": cleaned_pairs}, None


def _size_text(size: int) -> str:
    return "%.1f MB" % (size / 1024 / 1024)


def collect_files(paths: list) -> tuple[list, list]:
    """把用户给的路径展开成文件列表；返回 (文件, 跳过原因)。文件夹按字典序遍历，跳过符号链接。"""
    files, skipped = [], []
    for given in paths:
        if os.path.islink(given):
            skipped.append({"path": given, "reason": "是符号链接，没有读取。"})
        elif os.path.isfile(given):
            if not given.lower().endswith(SUPPORTED_EXTS):
                skipped.append({"path": given, "reason": "不支持这种文件类型（只支持 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro）。"})
            else:
                files.append(given)
        elif os.path.isdir(given):
            found = list(iter_files([given]))
            files.extend(found)
        else:
            skipped.append({"path": given, "reason": "找不到这个文件或文件夹。"})
    return files, skipped


def run_scan(values: dict) -> dict:
    deadline = time.monotonic() + SCAN_BUDGET_SECONDS
    files, skipped = collect_files(values["paths"])
    if not files:
        if skipped and all(item["reason"].startswith("找不到") for item in skipped) and len(skipped) == len(values["paths"]):
            return error("ALL_PATHS_FAILED", "所有路径都找不到：" + "；".join(item["path"] for item in skipped), skipped=skipped)
        return error("NO_FILES", "没有找到 HTML、JSX、TSX、Vue、Svelte 或 Astro 文件。", skipped=skipped)
    issues, scanned, total_bytes, complete = [], 0, 0, True
    not_scanned = 0
    for index, path in enumerate(files):
        if scanned >= MAX_FILES or total_bytes >= MAX_TOTAL_BYTES or time.monotonic() > deadline:
            not_scanned = len(files) - index
            complete = False
            break
        try:
            found = scan_file(path, min(deadline, time.monotonic() + FILE_BUDGET_SECONDS))
        except FileTooLarge as exc:
            size = exc.args[0] if exc.args else 0
            skipped.append({"path": path, "reason": "文件超过 %s 的上限（%s），没有扫描。" % (_size_text(MAX_FILE_BYTES), _size_text(size))})
            continue
        except ScanTimeout:
            skipped.append({"path": path, "reason": "扫描超过时间预算（单个文件 %d 秒），这个文件的结果不完整，已丢弃。" % int(FILE_BUDGET_SECONDS)})
            complete = False
            continue
        except OSError as exc:
            skipped.append({"path": path, "reason": "读不了这个文件（%s）。" % type(exc).__name__})
            continue
        scanned += 1
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        issues.extend(found)
    if not scanned and not issues:
        return error("NO_FILES_SCANNED", "找到了文件，但都没能扫描：" + "；".join("%s：%s" % (s["path"], s["reason"]) for s in skipped[:5]), skipped=skipped)
    if values["errors_only"]:
        issues = [i for i in issues if i["level"] == "error"]
    errors = sum(1 for i in issues if i["level"] == "error")
    warnings = len(issues) - errors
    by_rule: dict = {}
    for item in issues:
        by_rule[item["rule"]] = by_rule.get(item["rule"], 0) + 1
    shown = issues[:values["max_issues"]]
    level_zh = {"error": "错误", "warning": "警告"}
    lines = ["%s:%d: %s [%s] WCAG %s: %s" % (i["file"], i["line"], level_zh[i["level"]], i["rule"], i["wcag"], i["message"]) for i in shown]
    if len(issues) > len(shown):
        lines.append("（只列出前 %d 条，共 %d 条；统计数字覆盖全部。）" % (len(shown), len(issues)))
    lines.append("")
    lines.append("共扫描 %d 个文件：%d 个错误，%d 个警告" % (scanned, errors, warnings))
    for rule, count in sorted(by_rule.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append("  %4d  %s" % (count, rule))
    if skipped:
        lines.append("")
        lines.append("没有扫描的路径：")
        for item in skipped:
            lines.append("  %s：%s" % (item["path"], item["reason"]))
    if not complete:
        lines.append("")
        lines.append("（扫描没有跑完：%s 结果不完整，请缩小范围后重扫。）" % (
            "有 %d 个文件因文件数、总大小或时间上限没有扫描；" % not_scanned if not_scanned else "有文件超时；"))
    return {"ok": True, "tool": TOOL_PREFIX + "scan", "message": NOTE_ZH, "report_text": "\n".join(lines),
            "summary": {"files_scanned": scanned, "errors": errors, "warnings": warnings, "by_rule": by_rule},
            "issues": shown, "issues_truncated": len(issues) > len(shown), "skipped": skipped, "scan_complete": complete}



def run_contrast(values: dict) -> dict:
    results, problems = [], []
    for pair in values["pairs"]:
        fg, bg = pair["foreground"], pair["background"]
        try:
            (_, fg_alpha), (_, bg_alpha) = parse_color(fg), parse_color(bg)
            value = ratio(fg, bg)
        except ValueError as exc:
            problems.append({"foreground": fg, "background": bg, "error": str(exc)})
            results.append({"foreground": fg, "background": bg, "error": str(exc)})
            continue
        shown = "%.2f" % value
        text = "%s 在 %s 上：%s:1  %s" % (fg, bg, shown, verdict(value))
        notes = []
        if fg_alpha < 1:
            notes.append("前景色带透明度，已按背景色混合后计算。")
        if bg_alpha < 1:
            notes.append("背景色的透明度被忽略，按不透明处理；实际背景以叠加后的颜色为准。")
        for threshold in (3, 4.5, 7):
            if value < threshold and float(shown) >= threshold:
                notes.append("四舍五入后显示 %s，但精确值 %.4f 低于 %s:1，按未达标处理。" % (shown, value, ("%g" % threshold)))
        results.append({"foreground": fg, "background": bg, "ratio": float(shown), "ratio_exact": round(value, 4),
                        "aa_normal": value >= 4.5, "aa_large": value >= 3, "aaa_normal": value >= 7, "aaa_large": value >= 4.5,
                        "ui_components": value >= 3, "result_zh": text, "notes": notes})
    if len(problems) == len(results):
        return error("INVALID_COLOR", "所有颜色都无法识别：" + "；".join(p["error"] for p in problems), pairs=results)
    lines = []
    for item in results:
        if "error" in item:
            lines.append("%s 在 %s 上：%s" % (item["foreground"], item["background"], item["error"]))
        else:
            lines.append(item["result_zh"])
            lines.extend("  注：" + n for n in item["notes"])
    return {"ok": True, "tool": TOOL_PREFIX + "contrast", "message": NOTE_ZH, "report_text": "\n".join(lines), "pairs": results,
            "all_aa_normal": all(item.get("aa_normal") for item in results)}


RUNNERS = {"scan": run_scan, "contrast": run_contrast}


async def call_tool(name: str, arguments: Any) -> dict:
    values, message = validate(name, arguments)
    if message:
        return error("INVALID_ARGUMENTS", message, tool=TOOL_PREFIX + name)
    try:
        return await asyncio.to_thread(RUNNERS[name], values)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # 不向用户暴露内部堆栈，也不伪造结果
        return error("INTERNAL_ERROR", "工具内部出错（%s）；本次没有返回结果。" % type(exc).__name__, tool=TOOL_PREFIX + name)


class A11yTool(Tool):
    key = ""

    def __init__(self) -> None:
        entry = CATALOG[self.key]
        super().__init__(ToolCard(id=TOOL_PREFIX + self.key, name=TOOL_PREFIX + self.key,
                                  description=entry["description"], input_params=deepcopy(entry["schema"])))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_tool(self.key, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class A11yScanTool(A11yTool):
    key = "scan"


class A11yContrastTool(A11yTool):
    key = "contrast"
