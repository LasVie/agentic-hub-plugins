"""课表校验与导出的 WorkSwarm/openJiuwen 工具适配器。"""
from __future__ import annotations

import asyncio
from functools import lru_cache
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any

from openjiuwen.core.foundation.tool import Tool, ToolCard

VERSION = "1.0.0"
CORE = Path(__file__).resolve().parents[1] / "lib/fet_audit.py"


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


@lru_cache(maxsize=1)
def _core():
    name = "_fet_audit_" + hashlib.sha256(str(CORE).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, CORE)
    if spec is None or spec.loader is None:
        raise ImportError("缺少课表分析程序")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_export(path: str, content: str, fmt: str, sources: list[str]) -> dict[str, Any]:
    if not isinstance(path, str) or not path or len(path) > 4096 or "\x00" in path or "://" in path:
        return _error("invalid_output_path", "output_path 必须是本地导出文件的绝对路径。")
    target = Path(path)
    if not target.is_absolute() or target.suffix.lower() != "." + fmt:
        return _error("invalid_output_path", "导出路径必须是绝对路径，扩展名须与 csv 或 json 格式一致。")
    try:
        if target.parent.resolve(strict=True) != target.parent or not target.parent.is_dir():
            return _error("invalid_output_path", "导出目录必须已存在，且不能经过符号链接或含有 .. 路径段。")
        if any(target == Path(s).resolve() for s in sources):
            return _error("invalid_output_path", "不能使用输入文件作为导出路径。")
        body = content.encode("utf-8")
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        info = os.fstat(fd)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(body)
        except Exception:
            # Remove only the file created by this operation, not a replacement.
            try:
                current = target.lstat()
                if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
                    target.unlink()
            except OSError:
                pass
            raise
    except FileExistsError:
        return _error("output_exists", "导出文件已存在；请提供新的文件名，不会覆盖已有文件。")
    except (OSError, ValueError, UnicodeError):
        return _error("export_failed", "无法创建导出文件，请检查本地目录、权限和文件名。")
    return {"output_path": str(target), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def run_tool(operation: str, inputs: dict[str, Any]) -> dict[str, Any]:
    required = {"inspect": {"path"}, "verify": {"fet_path", "solution_path"},
                "export": {"fet_path", "solution_path", "format", "output_path"}}
    optional = {"teacher", "students"} if operation == "export" else set()
    if operation not in required or not isinstance(inputs, dict):
        return _error("invalid_input", "请提供受支持的操作及对象形式的参数。")
    if not required[operation] <= inputs.keys() or inputs.keys() - required[operation] - optional:
        return _error("invalid_input", "参数缺失或包含未支持的字段，请按工具参数说明调用。")
    if any(not isinstance(inputs[k], str) or not inputs[k] or len(inputs[k]) > 4096
           or "\x00" in inputs[k] for k in required[operation]):
        return _error("invalid_input", "必填参数必须是非空字符串，最多 4096 个字符，不能包含 NUL 字符。")
    if operation == "export":
        if inputs["format"] not in {"csv", "json"}:
            return _error("invalid_input", "format 仅支持 csv 或 json。")
        for field in optional:
            if field in inputs and (not isinstance(inputs[field], str) or not inputs[field].strip()
                                    or len(inputs[field]) > 256):
                return _error("invalid_input", "teacher 和 students 筛选值必须为非空名称，最多 256 个字符。")
    try:
        engine = _core()
        if operation == "inspect":
            return engine.inspect_fet(inputs["path"])
        if operation == "verify":
            return engine.verify_timetable(inputs["fet_path"], inputs["solution_path"])
        result = engine.export_timetable(inputs["fet_path"], inputs["solution_path"],
                                        format=inputs["format"], teacher=inputs.get("teacher"),
                                        students=inputs.get("students"))
        if not result.get("ok"):
            return result
        saved = _write_export(inputs["output_path"], result["content"], inputs["format"],
                              [inputs["fet_path"], inputs["solution_path"]])
        if saved.get("ok") is False:
            return saved
        return {**result, **saved}
    except (ImportError, OSError, ValueError, TypeError, KeyError):
        return _error("execution_failed", "本地分析程序无法完成操作，请检查输入和完整插件安装。")


PATH = {"type": "string", "minLength": 1, "maxLength": 4096,
        "description": "WorkSwarm 后端可访问的本地 UTF-8 XML 文件绝对路径。"}


class _TimetableTool(Tool):
    operation: str

    async def invoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await asyncio.to_thread(run_tool, self.operation, inputs)

    async def stream(self, inputs: dict[str, Any], **kwargs: Any):
        yield await self.invoke(inputs, **kwargs)


class InspectFetTool(_TimetableTool):
    operation = "inspect"

    def __init__(self):
        super().__init__(ToolCard(id="inspect_fet", name="inspect_fet",
            description="离线检查 .fet 的教师、学生、科目引用、时间网格和工作量，报告覆盖范围；不求解课表。",
            input_params={"type": "object", "additionalProperties": False,
                          "required": ["path"], "properties": {"path": PATH}}))


class VerifyTimetableTool(_TimetableTool):
    operation = "verify"

    def __init__(self):
        super().__init__(ToolCard(id="verify_fet_timetable", name="verify_fet_timetable",
            description="对照 .fet 检查已提供的课表 XML：教师/学生重叠、未安排活动、网格越界及已支持的不可用时段。不验证全部 FET 约束。",
            input_params={"type": "object", "additionalProperties": False,
                          "required": ["fet_path", "solution_path"],
                          "properties": {"fet_path": PATH, "solution_path": PATH}}))


class ExportTimetableTool(_TimetableTool):
    operation = "export"

    def __init__(self):
        super().__init__(ToolCard(id="export_fet_timetable", name="export_fet_timetable",
            description="校验并导出已有课表为 UTF-8 CSV/JSON，可按教师或学生组筛选；仅创建新文件，拒绝覆盖。保留冲突与覆盖范围说明。",
            input_params={"type": "object", "additionalProperties": False,
                "required": ["fet_path", "solution_path", "format", "output_path"],
                "properties": {"fet_path": PATH, "solution_path": PATH,
                    "format": {"type": "string", "enum": ["csv", "json"], "description": "导出格式。"},
                    "output_path": {"type": "string", "description": "已存在目录下的新文件绝对路径，扩展名为 .csv 或 .json，不覆盖文件。"},
                    "teacher": {"type": "string", "description": "可选：精确匹配的教师名称。"},
                    "students": {"type": "string", "description": "可选：年级、班级或学生小组名称。"}}}))
