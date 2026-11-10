"""Public native OpenJiuwen tool declarations for the queue capacity workbench."""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime" / "runtime.py"
_name = "_queue_capacity_runtime_" + str(abs(hash(str(_path))))
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
_runtime = sys.modules[_name]


class QueueCapacityWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="queue_capacity_workbench", name="queue_capacity_workbench",
            description="启动、查询或关闭离线排队容量实验台。仅使用插件专用本机服务；启动和关闭须得到用户明确授权。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"action": {"type": "string", "enum": ["start", "status", "stop"]},
                    "workspace": {"type": "string", "description": "已有专用工作目录的绝对路径，不含符号链接。"},
                    "confirmed": {"type": "boolean", "description": "用户明确授权启动或停止后设为 true。"}},
                "required": ["action", "workspace"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.lifecycle, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)


class SimulateQueueCapacityTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="simulate_queue_capacity", name="simulate_queue_capacity",
            description="使用随插件离线提供的 SimPy 4.1.2 引擎运行有界单阶段 FIFO 排队场景，比较容量并返回真实事件轨迹、等待时间、利用率及 CSV。不是模型估算。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"project": {"type": "object", "description": "queue-capacity-workbench/v1 场景：name、units=minutes、capacities 整数列表、jobs 列表；每作业 id、arrival、service。"}},
                "required": ["project"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.engine_call, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)
