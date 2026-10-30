"""离线光学实验室原生工具；使用现有 Tool/ToolCard 接口。"""
import asyncio
import importlib.util
from pathlib import Path
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime/lab.py"
_name = "offline_optics_runtime_" + str(abs(hash(str(_path))))
_spec = importlib.util.spec_from_file_location(_name, _path)
_lab = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _lab
_spec.loader.exec_module(_lab)

NODE = {"type": "string", "description": "可选：用户已安装 Node.js 18+ 的绝对路径。默认查找现有 PATH、常见安装路径或已有 Codex Node 运行时；不会下载或安装。"}


class LocalOpticsLabTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="local_optics_lab", name="local_optics_lab",
            description="启动、查询或关闭仅本机可访问的中文离线光学实验室。真实编辑镜面、透镜、玻璃和探测器，计算光路、保存或导出；启动/关闭须用户明确授权。使用当前安装专用目录，不修改宿主或其他插件。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "action"], "properties": {
                "workspace": {"type": "string", "description": "已存在、无符号链接的专用目录绝对路径。此安装仅在其 .offline-optics-lab 子目录保存场景/会话；不同安装不要共用目录。"},
                "action": {"type": "string", "enum": ["start", "status", "stop"]},
                "confirmed": {"type": "boolean", "description": "只有用户明确授权启动或关闭本机服务时才设true；status无需确认。"},
                "node_path": NODE}}))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_lab.local_lab, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class SimulateOpticalSceneTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="simulate_optical_scene", name="simulate_optical_scene",
            description="只读执行真实的有界二维几何光线追迹，返回探测器数值、光线段预览和截断信息。不联网、不写文件、不猜测结果。支持单光线/光束、直镜、理想薄透镜、均匀玻璃和探测器；不是全波、三维或硬件认证。请先读随包SKILL取得scene结构。",
            input_params={"type": "object", "additionalProperties": False, "required": ["scene"], "properties": {
                "scene": {"type": "object", "description": "{schema_version:1,title:中文标题,objects:[...]};对象id唯一，type为SingleRay/Beam/Mirror/IdealLens/PlaneGlass/Glass/Detector。除Glass使用path顶点外，使用p1/p2坐标。具体字段、方向、边界见SKILL和engine/README。禁止URL、脚本或上游模块。"},
                "node_path": NODE}}))

    async def invoke(self, inputs, **kwargs):
        result = await asyncio.to_thread(_lab.engine_call, inputs)
        if result.get("ok"):
            segments = result.pop("segments", [])
            result["segment_count"] = len(segments)
            result["segments_preview"] = segments[:12]
            result["preview_truncated"] = len(segments) > 12
            result["preview_note"] = "工具仅显示前12段光路；数值统计与探测器结果来自完整的本次有界计算。完整光路请在本机界面查看；请同时检查引擎截断标志。"
        return result

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
