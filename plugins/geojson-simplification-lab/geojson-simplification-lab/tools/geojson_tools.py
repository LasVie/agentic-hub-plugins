"""离线地图简化工作台的 openJiuwen 原生工具。"""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_SPEC = importlib.util.spec_from_file_location("geojson_simplification_lab_runtime", Path(__file__).with_name("runtime.py"))
_RUNTIME = importlib.util.module_from_spec(_SPEC)
_PREVIOUS_BYTECODE = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _SPEC.loader.exec_module(_RUNTIME)
finally:
    sys.dont_write_bytecode = _PREVIOUS_BYTECODE


class GeojsonWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="geojson_workbench", name="geojson_workbench",
            description="管理离线地图简化工作台：start 在随机空闲端口启动或复用本插件的独立本机服务，status 只读查询，stop 仅关闭身份核实的本插件服务。启动和停止须经用户确认。浏览器中导入 GeoJSON、预览拓扑简化、查看属性并下载结果；不上传地图、不修改原件或宿主。空闲30分钟退出。",
            input_params={"type": "object", "additionalProperties": False,
                "required": ["workspace", "action"], "properties": {
                    "workspace": {"type": "string", "description": "用户指定的已存在专用目录绝对路径，目录及父级不能为符号链接；仅在其 .geojson-simplification-lab 子目录保存服务记录"},
                    "action": {"type": "string", "enum": ["status", "start", "stop"]},
                    "confirmed": {"type": "boolean", "description": "start/stop 须有用户对本插件服务操作的明确授权并设为 true；status 不需要"}}},
            parallel_safe=False))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_RUNTIME.workbench, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
