"""离线卫星轨道工作台的 openJiuwen 原生工具。"""
import asyncio
from importlib.machinery import SourceFileLoader
import importlib.util
from pathlib import Path

from openjiuwen.core.foundation.tool import Tool, ToolCard


class _RuntimeLoader(SourceFileLoader):
    def set_data(self, path, data, **kwargs):
        """Keep installed plugin contents untouched during SDK loading."""


_NAME = "offline_satellite_orbit_workbench_runtime"
_PATH = Path(__file__).with_name("runtime.py")
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH, loader=_RuntimeLoader(_NAME, str(_PATH)))
_RUNTIME = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNTIME)


class SatelliteOrbitWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="satellite_orbit_workbench", name="satellite_orbit_workbench",
            description="管理离线卫星轨道工作台：status 只读查询；start 在随机空闲端口启动或复用本插件的独立本机服务；stop 仅关闭身份已核实的本插件服务。启动和停止须经用户确认。在同一电脑的普通浏览器中编辑 TLE 或 OMM，计算有限时间段的轨道、地面投影与几何仰角，并下载 SVG、CSV 或 JSON。轨道要素仅在浏览器中处理，原文件不受修改；几何结果不代表实际可见或航行安全。仅支持 macOS/Linux，空闲30分钟退出。",
            input_params={"type": "object", "additionalProperties": False,
                "required": ["workspace", "action"], "properties": {
                    "workspace": {"type": "string", "description": "用户指定的已存在专用目录绝对路径，目录及父级不能为符号链接；仅在其 .offline-satellite-orbit-workbench 子目录保存服务记录"},
                    "action": {"type": "string", "enum": ["status", "start", "stop"]},
                    "confirmed": {"type": "boolean", "description": "start/stop 须有用户对本插件服务操作的明确授权并设为 true；status 不需要"}}},
            parallel_safe=False))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_RUNTIME.workbench, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
