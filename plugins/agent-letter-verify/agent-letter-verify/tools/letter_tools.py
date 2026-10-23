"""代理信件完整性校验的 openJiuwen 原生工具；不接受或返回密钥。"""
import asyncio
import importlib.util
from pathlib import Path
from openjiuwen.core.foundation.tool import Tool, ToolCard

_PATH = Path(__file__).resolve().parents[1] / "runtime/verifier.py"
_SPEC = importlib.util.spec_from_file_location("agent_letter_verifier_core", _PATH)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


class LetterPolicyTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="agent_letter_policy", name="agent_letter_policy",
            description="初始化、读取或按明确请求修改工作目录内的信件校验策略。初始化默认关闭；配置开启须有非空发件人白名单和本地专用密钥。密钥只在本地内部读取，不接受或返回到对话。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "action"],
                "properties": {
                    "workspace": {"type": "string", "description": "已存在工作目录的绝对路径；策略只作用于此目录"},
                    "action": {"type": "string", "enum": ["init", "status", "configure"], "description": "init 初始化（关闭）、status 读取、configure 修改"},
                    "enabled": {"type": "boolean", "description": "configure 时可指定；必须遵循用户明确的开启或关闭要求"},
                    "allow": {"type": "array", "items": {"type": "string"}, "maxItems": 128, "description": "configure 时可指定发件人标识白名单；空名单不能开启校验"},
                    "expected_revision": {"type": "integer", "minimum": 0, "description": "configure 必填；使用最近 status 返回的 revision，防止覆盖并发修改"},
                }}))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_CORE.dispatch, "policy", inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class VerifyLetterTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="verify_agent_letter", name="verify_agent_letter",
            description="显式离线校验工作目录内的基础 v1 代理信封 JSON：结构、白名单、正文 SHA-256 和 HMAC。不发送或拦截消息，不证明唯一作者或防止重放。只看 verdict/verified；ok 不等于认证通过。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "letter_path"],
                "properties": {
                    "workspace": {"type": "string", "description": "已初始化信任策略的工作目录绝对路径"},
                    "letter_path": {"type": "string", "description": "此工作目录内 .json 信封文件的绝对路径；不跟随链接，不从私有信任目录读取"},
                }}))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_CORE.dispatch, "verify", inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
