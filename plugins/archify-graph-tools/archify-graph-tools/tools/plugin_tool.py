"""交互图谱校验与交付的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute
from ..runtime.common import InputError
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='archify_graph_tools',name='archify_graph_tools',description='为 Playground 补充结构化图谱校验与离线交付；从中文 JSON 生成可交互 HTML，保留源文件和校验结果。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录的绝对路径'}, 'action': {'type': 'string', 'enum': ['example', 'validate', 'deliver']}, 'source_file': {'type': 'string', 'description': '工作目录内结构化图谱 JSON，默认 graph.json'}, 'output_file': {'type': 'string', 'description': '交付 HTML 相对路径，默认 graph.html'}}, 'required': ['action', 'workspace_dir'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except (InputError,ValueError,TypeError,KeyError,UnicodeError) as e:return {'ok':False,'message':str(e) if isinstance(e,InputError) else '输入或本地数据格式不正确，请按中文说明检查。'}
  except Exception:return {'ok':False,'message':'本地执行失败，请检查文件权限、运行环境和输入；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
