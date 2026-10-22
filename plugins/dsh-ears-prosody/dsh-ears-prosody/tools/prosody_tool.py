"""WorkSwarm/openJiuwen adapter for local, bounded WAV analysis."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from openjiuwen.core.foundation.tool import Tool, ToolCard


VERSION = "1.0.1"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze.mjs"


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


def run_prosody(inputs: dict[str, Any]) -> dict[str, Any]:
    """Invoke the fixed bundled CLI without shell expansion or network services."""
    if not isinstance(inputs, dict) or set(inputs) != {"path"}:
        return _error("invalid_input", "仅提供 path 参数，值为本地 WAV 文件的绝对路径。")
    path = inputs["path"]
    if not isinstance(path, str) or not path or len(path) > 4096 or "\x00" in path:
        return _error("invalid_input", "path 必须为非空字符串，最多 4096 个字符，且不能包含 NUL 字符。")
    if "://" in path or not Path(path).is_absolute():
        return _error("invalid_input", "请使用本地文件的绝对路径；不支持网址或相对路径。")
    node = shutil.which("node")
    if not node:
        return _error("missing_node", "请安装 Node.js 20 或更高版本，将其加入 WorkSwarm 后端的 PATH，然后重启该后端。")
    if not SCRIPT.is_file():
        return _error("missing_payload", "缺少随包分析程序，请重新安装完整插件。")
    try:
        result = subprocess.run(
            [node, str(SCRIPT), path], capture_output=True, text=True,
            encoding="utf-8", timeout=30, check=False, shell=False,
        )
    except subprocess.TimeoutExpired:
        return _error("timeout", "本地分析超过 30 秒时限，请尝试更短的 WAV 音频。")
    except (OSError, UnicodeError):
        return _error("execution_failed", "无法运行本地分析程序，请检查 Node.js 环境和插件文件。")
    try:
        output = json.loads(result.stdout)
    except (ValueError, TypeError):
        return _error("invalid_output", "分析程序返回了无效 JSON；请确认 Node.js 版本不低于 20，必要时重新安装插件。")
    if not isinstance(output, dict) or type(output.get("ok")) is not bool or output.get("version") != VERSION:
        return _error("invalid_output", "分析程序返回了非预期的结果或版本。")
    if result.returncode and output["ok"]:
        return _error("execution_failed", "分析程序异常退出。")
    return output


class ProsodyTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="analyze_wav_prosody", name="analyze_wav_prosody",
            description=(
                "测量本地 WAV 的音高走势、活动与停顿时序、能量和能量峰节奏代理指标。"
                "仅在本地读取音频；不转写、不识别说话人、不推断情绪或意图。"
                "需提供后端可访问的 WAV 绝对路径，文件不超过 12 MiB、时长不超过 60 秒。"
            ),
            input_params={
                "type": "object", "additionalProperties": False, "required": ["path"],
                "properties": {"path": {
                    "type": "string", "minLength": 1, "maxLength": 4096,
                    "description": "WorkSwarm 后端可访问的本地 WAV 绝对路径，不接受网址。",
                }},
            },
        ))

    async def invoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await asyncio.to_thread(run_prosody, inputs)

    async def stream(self, inputs: dict[str, Any], **kwargs: Any):
        yield await self.invoke(inputs, **kwargs)
