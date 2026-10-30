"""离线分子结构工作台的 openJiuwen 原生工具。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_SPEC = importlib.util.spec_from_file_location("molecule_structure_lab_runtime", Path(__file__).with_name("runtime.py"))
_RUNTIME = importlib.util.module_from_spec(_SPEC)
_PREVIOUS_BYTECODE = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _SPEC.loader.exec_module(_RUNTIME)
finally:
    sys.dont_write_bytecode = _PREVIOUS_BYTECODE


class AnalyzeMoleculeTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="analyze_molecule", name="analyze_molecule",
            description="调用随包 RDKit 离线解析 SMILES，返回规范 SMILES、八项数值描述符、600×400 SVG 与可选 SMARTS 的第一个匹配。索引从0开始，不声称全部匹配数或药效安全。需要本地 Node.js≥18；不联网、不保存分子、不修改文件。",
            input_params={"type": "object", "additionalProperties": False, "required": ["smiles"], "properties": {
                "smiles": {"type": "string", "maxLength": 1024, "description": "用户提供的单行普通 SMILES；最多256个显式原子、512条键，不接受名称或CX扩展"},
                "smarts": {"type": "string", "maxLength": 512, "description": "可选单行 SMARTS；最多128个显式原子、256条键，空串表示不查询"}}}, parallel_safe=True))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_RUNTIME.analyze, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class MoleculeWorkbenchTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id="molecule_workbench", name="molecule_workbench",
            description="管理本插件独立的本机浏览器工作台。start启动或复用仅监听127.0.0.1的随机端口，status只读查询，stop只停止经过令牌身份核实的本插件服务。启动/停止需用户确认；浏览器本地编辑SMILES、计算、查询和下载SVG/JSON，无需Node。空闲30分钟退出。",
            input_params={"type": "object", "additionalProperties": False, "required": ["workspace", "action"], "properties": {
                "workspace": {"type": "string", "description": "用户明确指定的已存在工作目录绝对路径，不能含符号链接；启动仅在其.molecule-structure-lab目录保存服务记录"},
                "action": {"type": "string", "enum": ["start", "status", "stop"]},
                "confirmed": {"type": "boolean", "description": "start/stop必须为true且来自用户对本插件服务操作的明确授权；status不需要"}}}, parallel_safe=False))

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_RUNTIME.workbench, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
