"""WorkSwarm 原生工具；不会启动浏览器、进程、网络连接或模型。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool, ToolCard
from ..runtime.export_game import InputError, VERSION, execute


class CreateInvadersGame(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="create_invaders_game", name="create_invaders_game",
            description="创建星际防线离线中文游戏网页：键盘射击、护盾、计分、波次和本地续玩。只写入指定新文件，不覆盖，不联网，不调用模型。",
            input_params={"type": "object", "properties": {
                "output_path": {"type": "string", "description": "已有目录内新建 .html 文件的绝对路径；不覆盖已有文件，不经过符号链接"},
                "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647, "description": "初始随机种子，默认 12345；相同种子和按键/步数产生相同进程"}},
                "required": ["output_path"], "additionalProperties": False}, parallel_safe=True))

    async def invoke(self, inputs, **kwargs):
        try:
            return await asyncio.to_thread(execute, inputs)
        except InputError as exc:
            return {"ok": False, "version": VERSION, "message": str(exc)}
        except Exception:
            return {"ok": False, "version": VERSION, "message": "导出失败，请检查输入、文件权限和插件完整性；未确认成功。"}

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
