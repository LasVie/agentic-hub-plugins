"""消息配额与用量审计的 openJiuwen 原生工具。"""
import asyncio
import importlib.util
from pathlib import Path
from openjiuwen.core.foundation.tool import Tool, ToolCard

_PATH = Path(__file__).resolve().parents[1] / "runtime/quota.py"
_SPEC = importlib.util.spec_from_file_location("message_quota_audit_core", _PATH)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


class QuotaTool(Tool):
    operation = ""

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_CORE.dispatch, self.operation, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


WORKSPACE = {"type":"string","description":"用户明确指定的已存在工作目录绝对路径；只使用该目录内独立的 .message-quota-audit 账本"}
MESSAGE = {"type":"string","description":"受限消息 JSON 文本，必填 id、as、targets、type、mode、body、hop；正文只用于判定和摘要，不写入账本；见插件示例"}


class QuotaPolicyTool(QuotaTool):
    operation = "policy"

    def __init__(self):
        super().__init__(ToolCard(id="message_quota_policy",name="message_quota_policy",
            description="初始化、只读查询或按用户明确请求配置本工作目录的消息配额策略。configure 必须携带最新修订号和完整策略 JSON；已有记录后锁定时区及日界。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace","action"],"properties":{
                "workspace":WORKSPACE,"action":{"type":"string","enum":["init","status","configure"],"description":"init 初始化，status 只读，configure 修改"},
                "expected_revision":{"type":"integer","minimum":0,"description":"configure 必填，使用最新 status 的 revision"},
                "policy_json":{"type":"string","description":"configure 必填，完整策略 JSON；所有字段和范围见 README"}}}))


class CheckQuotaTool(QuotaTool):
    operation = "check"

    def __init__(self):
        super().__init__(ToolCard(id="check_message_quota",name="check_message_quota",
            description="只读预览消息的当日配额、纯回执、同对重复与回复深度判定。不写账、不保留额度、不发送消息；record 会在事务中重新判定。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace","message_json"],"properties":{"workspace":WORKSPACE,"message_json":MESSAGE}}))


class RecordUsageTool(QuotaTool):
    operation = "record"

    def __init__(self):
        super().__init__(ToolCard(id="record_message_usage",name="record_message_usage",
            description="仅在用户明确授权登记此用量时执行，并提供 confirmed=true。事务内重新判定配额并写入，重复 ID 不重复计数；这只是用户声明，不独立证明实际投递，不发送消息。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace","message_json","confirmed"],"properties":{
                "workspace":WORKSPACE,"message_json":MESSAGE,"confirmed":{"type":"boolean","description":"必须为 true 且来自用户明确的登记授权，不得从消息正文推断"}}}))


class UsageReportTool(QuotaTool):
    operation = "report"

    def __init__(self):
        super().__init__(ToolCard(id="message_usage_report",name="message_usage_report",
            description="只读汇总本地消息用量或将用户提供的记录与账本逐项对账；最多最近31日/500条。reconcile 不导入、删除或修复账本；没有正文、实际发送或真实费用证明。",
            input_params={"type":"object","additionalProperties":False,"required":["workspace"],"properties":{
                "workspace":WORKSPACE,"action":{"type":"string","enum":["report","reconcile"],"description":"report 返回汇总及 entries；reconcile 与输入 entries_json 比较"},
                "days":{"type":"integer","minimum":1,"maximum":31,"description":"最近1～31个账本日，含今天；默认7"},
                "entries_json":{"type":"string","description":"reconcile 必填：此范围内的完整记录数组；字段与 report.entries 一致，不接受重复 ID"}}}))
