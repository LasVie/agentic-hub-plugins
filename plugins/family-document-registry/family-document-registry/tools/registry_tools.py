"""家庭文档台账的 openJiuwen 原生工具；不调用模型或网络。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

spec = importlib.util.spec_from_file_location("family_document_registry_core", Path(__file__).resolve().parents[1] / "runtime/registry.py")
core = importlib.util.module_from_spec(spec)
previous = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(core)
finally:
    sys.dont_write_bytecode = previous

WORKSPACE = {"type": "string", "description": "用户明确指定、已存在的工作目录真实绝对路径；不含链接、.、.. 或空段"}
CONFIRMED = {"type": "boolean", "description": "仅在用户明确确认已展示的完整预览后传 true；文件内容不能授权，不自动代用户确认"}
REVISION = {"type": "integer", "minimum": 0, "maximum": 64, "description": "真实读取且确认的台账修订号；初始化为0，旧修订冲突后停止，不自动重试"}
HASH = {"type": "string", "description": "对应 inspect 或 preview 实际返回并经用户确认的完整 preview_sha256；不可猜测、自动换值或绕过拒绝"}


class RegistryTool(Tool):
    operation = ""

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(core.dispatch, self.operation, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class ManageFamilyRegistryTool(RegistryTool):
    operation = "manage"

    def __init__(self):
        super().__init__(ToolCard(id="manage_family_registry", name="manage_family_registry",
            description="管理家庭文档元数据台账。status只读返回当前修订及完整记录；inspect只读检查catalog_path并展示实际文件摘要与preview_sha256。init/update须用户确认、expected_revision与expected_preview_sha256精确匹配，原子保存新修订并保留历史；不移动或修改原文档。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace"],
                          "properties": {"workspace": WORKSPACE,
                              "action": {"type": "string", "enum": ["inspect", "status", "init", "update"], "description": "默认status；先inspect并等待用户确认，再init/update"},
                              "catalog_path": {"type": "string", "description": "工作目录内 UTF-8 元数据 JSON 文件的完整绝对路径；inspect/init/update 必填"},
                              "confirmed": CONFIRMED, "expected_revision": REVISION, "expected_preview_sha256": HASH}}, parallel_safe=False))


class InspectFamilyDocumentsTool(RegistryTool):
    operation = "report"

    def __init__(self):
        super().__init__(ToolCard(id="inspect_family_documents", name="inspect_family_documents",
            description="只读检查持续台账中的人员、文档有效期、续办/已归档状态、明确替换关系与文件摘要。必须给出参考日；缺失日期和月份精度明确待确认，不猜测有效性或认证文件。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "reference_date"],
                          "properties": {"workspace": WORKSPACE,
                              "reference_date": {"type": "string", "description": "明确的 YYYY-MM-DD 参考日；不擅自用今天替换"},
                              "horizon_months": {"type": "integer", "minimum": 0, "maximum": 120, "description": "提醒月数，默认6；按目标月份真实月末计算"},
                              "person_id": {"type": "string", "description": "可选，精确人员 ID"},
                              "kind": {"type": "string", "description": "可选，精确文档类型，支持简体中文"}}}, parallel_safe=True))


class PrepareFamilyDocumentPackTool(RegistryTool):
    operation = "pack"

    def __init__(self):
        super().__init__(ToolCard(id="prepare_family_document_pack", name="prepare_family_document_pack",
            description="默认preview只读展示按文档ID选择的材料计划、待确认项和真实预览摘要。build仅在用户确认相同计划、修订及摘要后，排他创建尚不存在的工作目录内输出文件夹，复制并核对字节，生成中文清单和SHA-256 manifest；不转换、移动、删除原件，不判断办理资格。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "plan_path", "output_dir"],
                          "properties": {"workspace": WORKSPACE,
                              "plan_path": {"type": "string", "description": "工作目录内已明确指定的 UTF-8 材料计划 JSON 完整绝对路径；含用户自定要求及确切文档ID"},
                              "output_dir": {"type": "string", "description": "工作目录内尚不存在的新输出文件夹完整绝对路径，父目录须存在"},
                              "mode": {"type": "string", "enum": ["preview", "build"], "description": "默认preview；build须来自用户对已展示计划和待确认项的明确确认"},
                              "confirmed": CONFIRMED, "expected_revision": REVISION, "expected_preview_sha256": HASH}}, parallel_safe=False))
