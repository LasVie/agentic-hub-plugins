"""Supported native Tool/ToolCard entries; no host path or dependency patches."""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime" / "runtime.py"
_name = "_offline_allocation_runtime_" + str(abs(hash(str(_path))))
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
_runtime = sys.modules[_name]


class AllocationWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="allocation_workbench", name="allocation_workbench",
            description="启动、查询或关闭离线资源配置优化台。本机专用工作目录与随机空闲端口；启动和关闭须经用户授权。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"action": {"type": "string", "enum": ["start", "status", "stop"]},
                    "workspace": {"type": "string", "description": "已有专用工作目录的绝对路径，不含符号链接。"},
                    "confirmed": {"type": "boolean", "description": "用户明确授权启动或停止后设为 true。"}},
                "required": ["action", "workspace"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.lifecycle, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)


class OptimizeAllocationTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="optimize_allocation", name="optimize_allocation",
            description="使用离线 HiGHS 1.16.0 真实选择整项作业，使资源预算内的总价值最大。返回独立复算的资源用量、目标值和真实求解状态。CSparse Copyright (c) 2006 Timothy A. Davis；LGPL-2.1-or-later，见随包许可。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"project": {"type": "object", "description": "offline-allocation/v1：name、resources(id/name/capacity)、jobs(id/name/value/uses)、min_jobs；仅有界非负整数数据。"}},
                "required": ["project"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.engine_call, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)
