"""离线观星规划台：仅使用支持的原生 Tool/ToolCard 接口。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_path = Path(__file__).resolve().parents[1] / "runtime/lab.py"
_name = "observing_planner_runtime_" + str(abs(hash(str(_path))))
_spec = importlib.util.spec_from_file_location(_name, _path)
_lab = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _lab
_spec.loader.exec_module(_lab)


class ComputeObservingPlanTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="compute_observing_plan", name="compute_observing_plan",
            description="只读计算真实离线星历：太阳、月亮、水金火木土行星的无大气折射地平坐标、最长24小时高度轨迹、升落与暮光。明确UTC输入；不是天气或可见性预测。不会联网、调用模型或写文件。",
            input_params={"type":"object","additionalProperties":False,"required":["request"],"properties":{
                "request":{"type":"object","description":"latitude/longitude为纬度/东经度；start_utc格式YYYY-MM-DDTHH:MM:SSZ，2000–2100年；可选elevation_m、duration_hours(0,24]、step_minutes[5,60]、bodies数组Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn、display_offset_minutes固定显示偏移。详见随包SKILL。"}}}))

    async def invoke(self, inputs, **kwargs):
        result = await asyncio.to_thread(_lab.engine_call, inputs)
        if result.get("ok"):
            # Keep exact sampled endpoints/events while avoiding huge model context.
            for body in result.get("bodies", []):
                track = body.pop("track", [])
                body["sample_count"] = len(track)
                body["track_preview"] = track[:3]
                body["last_sample"] = track[-1] if track else None
            result.pop("sun_track", None)
            result["sample_count"] = len(result.pop("times", []))
            result["preview_truncated"] = result["sample_count"] > 4
            result["preview_note"] = "工具每个天体仅展示前3个和最后1个采样点；事件来自完整有界计算。完整轨迹与CSV请在本机界面查看。采样高度不是精确极值。"
        return result

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class LocalObservingPlannerTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="local_observing_planner", name="local_observing_planner",
            description="启动、查询或关闭只在本机监听的中文离线观星规划台。启动/关闭须明确授权；只在指定专用目录保存计划与会话，不改宿主。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace","action"],"properties":{
                "workspace":{"type":"string","description":"已存在、无符号链接的专用工作目录绝对路径；不同安装不要共用。"},
                "action":{"type":"string","enum":["start","status","stop"]},
                "confirmed":{"type":"boolean","description":"用户明确授权启动/关闭服务时设置true；只读status不需要。"}}}))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_lab.local_lab, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
