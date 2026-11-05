"""离线力学实验室：仅使用支持的原生 Tool/ToolCard 接口。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime/lab.py"
_name = "mechanics_lab_runtime_" + str(abs(hash(str(_path))))
_spec = importlib.util.spec_from_file_location(_name, _path)
_lab = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _lab
_spec.loader.exec_module(_lab)


class LocalMechanicsLabTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="local_mechanics_lab", name="local_mechanics_lab",
            description="启动、查询或关闭只在本机监听的中文离线力学实验室。数值计算仅在用户浏览器运行，不返回模拟数值。启动/关闭须明确授权；只在指定专用目录保存实验场景与会话，不改宿主。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace","action"],"properties":{
                "workspace":{"type":"string","description":"已存在、无符号链接的专用工作目录绝对路径；不同安装不要共用。"},
                "action":{"type":"string","enum":["start","status","stop"]},
                "confirmed":{"type":"boolean","description":"用户明确授权启动/关闭服务时设置true；只读status不需要。"}}}))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_lab.local_lab, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
