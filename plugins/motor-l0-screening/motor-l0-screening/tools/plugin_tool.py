"""电机方案粗筛的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute
from ..runtime.common import InputError
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='motor_l0_screening',name='motor_l0_screening',description='本地生成电机方案矩阵、执行物理规则校验并按公式估算排序；仅用于相对粗筛，不是工程认证或仿真结论。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录的绝对路径'}, 'action': {'type': 'string', 'enum': ['screen']}, 'power_kw': {'type': 'number'}, 'speed_rpm': {'type': 'number'}, 'voltage_v': {'type': 'number'}, 'line_freq_hz': {'type': 'number'}, 'count': {'type': 'integer', 'minimum': 1, 'maximum': 120}, 'motor_type': {'type': 'string', 'enum': ['induction', 'pmsm']}, 'report_file': {'type': 'string'}}, 'required': ['action', 'workspace_dir', 'power_kw', 'speed_rpm'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except (InputError,ValueError,TypeError,KeyError,UnicodeError) as e:return {'ok':False,'message':str(e) if isinstance(e,InputError) else '输入或本地数据格式不正确，请按中文说明检查。'}
  except Exception:return {'ok':False,'message':'本地执行失败，请检查文件权限、运行环境和输入；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
