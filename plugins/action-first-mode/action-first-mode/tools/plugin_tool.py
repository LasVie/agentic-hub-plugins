"""行动优先表达的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute
from ..runtime.common import InputError
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='action_first_mode',name='action_first_mode',description='明确开启、关闭和查询行动优先表达模式，状态保存在用户指定的工作目录内；不作医疗效果承诺。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录的绝对路径'}, 'action': {'type': 'string', 'enum': ['on', 'off', 'status']}}, 'required': ['action', 'workspace_dir'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except (InputError,ValueError,TypeError,KeyError,UnicodeError) as e:return {'ok':False,'message':str(e) if isinstance(e,InputError) else '输入或本地数据格式不正确，请按中文说明检查。'}
  except Exception:return {'ok':False,'message':'本地执行失败，请检查文件权限、运行环境和输入；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
