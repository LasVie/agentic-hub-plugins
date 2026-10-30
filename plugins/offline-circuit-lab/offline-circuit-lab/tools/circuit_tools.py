"""离线电路实验室原生工具；不修改宿主，不联网或调用模型。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_spec = importlib.util.spec_from_file_location("offline_circuit_lab_runtime", Path(__file__).resolve().parents[1] / "runtime/lab.py")
_lab = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _lab
_spec.loader.exec_module(_lab)

COMPONENT = {"type":"object","additionalProperties":False,"required":["id","type","a","b","value"],"properties":{
    "id":{"type":"string","description":"唯一的ASCII元件标识，例如R1。"},
    "type":{"type":"string","enum":["R","L","C","V"]},
    "a":{"type":"string","description":"起点节点；0代表地。"},
    "b":{"type":"string","description":"终点节点；0代表地。"},
    "value":{"type":"number","description":"SI单位：R欧姆、L亨利、C法拉、V伏特；电源满足Va-Vb=value。"}}}
CIRCUIT = {"type":"object","additionalProperties":False,"required":["components","duration_ms","step_us","probe"],"properties":{
    "components":{"type":"array","items":COMPONENT,"minItems":1,"maxItems":24},
    "duration_ms":{"type":"number","description":"有界仿真时长，毫秒；步数不得超过5000。"},
    "step_us":{"type":"number","description":"固定时间步长，微秒；应明显小于电路时间常数。"},
    "probe":{"type":"string","description":"要观察的实际节点标识。"},
    "mode":{"type":"string","enum":["transient","dc"],"description":"默认transient：零初始储能，电源在t=0阶跃。dc为理想直流稳态。"}}}


class LocalCircuitLabTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="local_circuit_lab", name="local_circuit_lab", description="为用户选择的专用目录启动、查询或关闭离线电路实验室。仅监听127.0.0.1，在独立浏览器编辑RLC拓扑、仿真、保存和导出；启动/关闭须明确授权。不会修改宿主或其他插件。", input_params={"type":"object","additionalProperties":False,"required":["workspace","action"],"properties":{
            "workspace":{"type":"string","description":"用户选择的已存在专用工作目录绝对路径，不能是符号链接；本插件仅在其.offline-circuit-lab子目录保存状态。"},
            "action":{"type":"string","enum":["start","status","stop"]},
            "confirmed":{"type":"boolean","description":"仅在用户明确授权启动或关闭本机服务时设为true；status无需确认。"}}}))
    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_lab.local_lab, inputs)
    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class SimulateRlcCircuitTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="simulate_rlc_circuit", name="simulate_rlc_circuit", description="执行真实的有界离线RLC数值仿真，输入元件与节点拓扑，返回测量摘要和首尾样本预览。不会生成或猜测结果，不写文件。完整波形/CSV请在本机实验室查看。理想元件教学模型，不是硬件安全、SPICE兼容或工程认证。", input_params={"type":"object","additionalProperties":False,"required":["circuit"],"properties":{"circuit":CIRCUIT}}))
    async def invoke(self, inputs, **kwargs):
        result = await asyncio.to_thread(_lab.simulate, inputs)
        if result.get("ok"):
            samples = result.pop("samples", [])
            result["sample_count"] = len(samples)
            result["trace_preview"] = samples if len(samples) <= 12 else samples[:6] + samples[-6:]
            result["trace_truncated"] = len(samples) > 12
            result["trace_note"] = "这里只返回首尾样本预览；完整数值波形与CSV由本机实验室提供。"
        return result
    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
