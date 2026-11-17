"""Public WorkSwarm native Tool/ToolCard entries; no host modifications."""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime/runtime.py"
_name = "_offline_steam_runtime_" + str(abs(hash(str(_path))))
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
_runtime = sys.modules[_name]


class SteamWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="steam_workbench", name="steam_workbench",
            description="启动、查询或关闭离线水与蒸汽物性工作台；仅用本机专用目录和随机空闲端口。启动和停止须经用户授权。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"action": {"type": "string", "enum": ["start", "status", "stop"]},
                    "workspace": {"type": "string", "description": "已有专用工作目录的绝对路径，不含符号链接。"},
                    "confirmed": {"type": "boolean", "description": "用户明确授权启动或停止后设为 true。"}},
                "required": ["action", "workspace"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.lifecycle, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)


class CalculateWaterPropertiesTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="calculate_water_properties", name="calculate_water_properties",
            description="真实调用随包 CoolProp 8.0.0 的 HEOS::Water，计算水/蒸汽的密度、比焓、比熵、相态、饱和性质及有界饱和扫描。输入仅 SI，压力为绝对压力。不能用模型估值代替工具返回。",
            input_params={"type": "object", "additionalProperties": False,
                "properties": {"project": {"type": "object", "description": "steam-properties/v1：name、state(pair为PT/PQ/TQ，pressure_pa/temperature_k/quality)、sweep(variable为pressure_pa/temperature_k，start/end/points)。固定纯水，无代码/流体/后端/配置导入。"}},
                "required": ["project"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.engine_call, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)
