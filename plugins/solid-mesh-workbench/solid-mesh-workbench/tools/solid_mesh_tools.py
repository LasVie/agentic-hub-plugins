"""Public native OpenJiuwen tool declarations for the solid mesh workbench."""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime" / "runtime.py"
_name = "_solid_mesh_runtime_" + str(abs(hash(str(_path))))
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
_runtime = sys.modules[_name]


class SolidMeshWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="solid_mesh_workbench", name="solid_mesh_workbench",
            description="启动、查询或停止立体网格布尔工坊。工作台仅监听本机，提供真实网格运算与三维预览。启动或停止必须获得用户明确授权；不得修改宿主、模型或其他插件。",
            input_params={"type": "object", "additionalProperties": False,
                          "properties": {"action": {"type": "string", "enum": ["start", "status", "stop"]},
                                         "workspace": {"type": "string", "description": "已有专用工作目录的绝对路径；目录及父目录不得为符号链接。"},
                                         "confirmed": {"type": "boolean", "description": "仅在用户明确授权启动或停止后设置 true。"},
                                         "node_path": {"type": "string", "description": "可选：已有 Node.js 22+ 可执行文件的绝对路径；不会安装软件。"}},
                          "required": ["action", "workspace"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.lifecycle, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)


class CalculateSolidMeshTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="calculate_solid_mesh", name="calculate_solid_mesh",
            description="调用随插件离线提供的 Manifold 引擎，对两个有界封闭三角网格或基础实体执行并集、差集、交集，并返回体积、面积、边界、网格与 OBJ。输入为 solid-mesh-workbench/v1 项目，单位毫米；不是猜测或生成替代代码。",
            input_params={"type": "object", "additionalProperties": False,
                          "properties": {"project": {"type": "object", "description": "schema=solid-mesh-workbench/v1，units=mm，operation=union/difference/intersection，a 与 b 为 box/cylinder/obj/mesh 操作数；详见插件说明。"},
                                         "node_path": {"type": "string", "description": "可选：已有 Node.js 22+ 的绝对路径。"}},
                          "required": ["project"]}, parallel_safe=False))

    async def invoke(self, inputs, session=None, **kwargs):
        return await asyncio.to_thread(_runtime.engine_call, inputs)

    async def stream(self, inputs, session=None, **kwargs):
        yield await self.invoke(inputs, session=session, **kwargs)
