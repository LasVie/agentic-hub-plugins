"""物理解题审校的 openJiuwen 本地题图工具适配器。"""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

from openjiuwen.core.foundation.tool import Tool, ToolCard

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_figure.py"
_SPEC = importlib.util.spec_from_file_location("physics_assumption_check_figure", _SCRIPT)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


class PhysicsFigureTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="prepare_physics_figure", name="prepare_physics_figure",
            description="在本地裁剪并放大静态 PNG/JPEG 物理题图，输出新的 PNG 和尺寸/哈希。默认不锐化，不覆盖文件，不识别物理关系。输入最多 25 MiB / 2000 万像素，输出最多 3200 万像素。",
            input_params={
                "type": "object", "additionalProperties": False, "required": ["path", "output"],
                "properties": {
                    "path": {"type": "string", "description": "后端可读取的输入图片绝对路径"},
                    "output": {"type": "string", "description": "已存在目录中新的 .png 绝对路径，不得覆盖"},
                    "width": {"type": "integer", "minimum": 64, "maximum": 4096, "default": 1600,
                              "description": "目标宽度（像素），只放大不缩小"},
                    "crop": {"type": "array", "minItems": 4, "maxItems": 4,
                             "items": {"type": "integer"}, "description": "旋转校正后的 [左, 上, 右, 下] 像素区域"},
                    "enhance": {"type": "boolean", "default": False, "description": "是否开启锐化和对比度增强；默认关闭"},
                },
            },
        ))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_CORE.prepare_figure, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
