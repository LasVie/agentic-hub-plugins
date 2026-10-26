"""WorkSwarm原生工具，不调用模型；启动需要用户明确授权。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool, ToolCard
from ..runtime.control import safe_execute


class MusicLibrary(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="local_music_library", name="local_music_library",
            description="本地音乐库：为用户指定音频目录启动、查询或关闭离线回环播放器；保存独立歌单，支持浏览器播放和续播。启动/关闭需明确授权；不调用外网或模型。",
            input_params={"type": "object", "properties": {
                "action": {"type": "string", "enum": ["start", "status", "stop"], "description": "start启动，status查询，stop关闭本插件会话"},
                "library_dir": {"type": "string", "description": "用户明确选择的已有音频目录，真实绝对路径，不经过符号链接"},
                "workspace": {"type": "string", "description": "库目录之外的已有独立工作目录；在此保存私有状态"},
                "confirmed": {"type": "boolean", "description": "用户明确授权启动/关闭服务后才设为true；查询不需要"}},
                "required": ["action", "library_dir", "workspace"], "additionalProperties": False}, parallel_safe=False))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(safe_execute, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
