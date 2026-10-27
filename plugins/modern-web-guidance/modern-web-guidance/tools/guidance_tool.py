"""JiuwenSwarm 原生工具：调用包内只读检索器，参数通过 stdin 传递。"""
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

from openjiuwen.core.foundation.tool import Tool, ToolCard

ROOT = Path(__file__).resolve().parents[1]


class ModernWebGuidanceTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="modern_web_guidance", name="modern_web_guidance",
            description="查询 12 篇中文现代 Web 精选指南，返回固定来源、实现建议与降级说明。离线只读，不运行示例、不更改项目。",
            input_params={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["help", "search", "list", "retrieve"], "description": "先搜索，再读取命中的指南。"},
                    "query": {"type": "string", "maxLength": 300, "description": "中文主题或 API 名称，每次聚焦一个能力。"},
                    "ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3, "description": "搜索或列表返回的指南 ID。"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 12, "description": "搜索最多返回几篇，默认 5。"},
                },
                "required": ["action"], "additionalProperties": False,
            }, parallel_safe=True,
        ))

    async def invoke(self, inputs, **kwargs):
        if not isinstance(inputs, dict):
            return {"ok": False, "message": "输入必须是对象。"}
        try:
            raw = json.dumps(inputs, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            return {"ok": False, "message": "参数须为有效的 JSON 数据。"}
        if len(raw.encode("utf-8")) > 16384:
            return {"ok": False, "message": "输入过大，请缩短查询。"}
        node = shutil.which("node")
        if not node:
            return {"ok": False, "message": "未找到 Node.js，请安装 Node.js 20 或更高版本并重启宿主，使 PATH 生效。无需 npm install。"}

        def call():
            result = subprocess.run(
                [node, str(ROOT / "runtime" / "cli.mjs")], input=raw,
                encoding="utf-8", capture_output=True, timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode not in (0, 2) or not result.stdout or len(result.stdout) > 200000:
                return {"ok": False, "message": "检索器启动失败，请核对 Node.js 版本和插件文件完整性。"}
            value = json.loads(result.stdout)
            if not isinstance(value, dict) or not isinstance(value.get("ok"), bool):
                return {"ok": False, "message": "检索结果格式异常，请重新安装插件。"}
            return value

        try:
            return await asyncio.to_thread(call)
        except subprocess.TimeoutExpired:
            return {"ok": False, "message": "本地检索超时，请重试或检查 Node.js 运行环境。"}
        except (OSError, ValueError):
            return {"ok": False, "message": "无法读取检索结果，请检查 Node.js 与插件文件。"}

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
