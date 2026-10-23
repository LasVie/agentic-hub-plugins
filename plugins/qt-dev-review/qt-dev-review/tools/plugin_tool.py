"""Qt 开发审校的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute
from ..runtime.common import InputError
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='qt_dev_review',name='qt_dev_review',description='只读审查指定的 Qt C++/QML 文件，输出中文规则定位和审校报告；无需 Qt 安装，不替代编译和人工审查。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录的绝对路径'}, 'action': {'type': 'string', 'enum': ['review']}, 'files': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 20, 'description': '工作目录内 C++/QML 文件相对路径'}, 'report_file': {'type': 'string', 'description': '中文报告的相对路径，默认 qt-review.md'}}, 'required': ['action', 'workspace_dir', 'files'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except (InputError,ValueError,TypeError,KeyError,UnicodeError) as e:return {'ok':False,'message':str(e) if isinstance(e,InputError) else '输入或本地数据格式不正确，请按中文说明检查。'}
  except Exception:return {'ok':False,'message':'本地执行失败，请检查文件权限、运行环境和输入；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
