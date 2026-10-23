"""本地五子棋的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute
from ..runtime.common import InputError
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='gomoku_local',name='gomoku_local',description='15×15 自由五子棋的本地状态、合法落子、胜负判定和中文棋盘导出；用当前会话模型对弈，无需额外账号。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录的绝对路径'}, 'action': {'type': 'string', 'enum': ['new', 'state', 'move', 'export']}, 'game_id': {'type': 'string', 'description': '字母数字和短横线组成的对局编号，默认 game-1'}, 'row': {'type': 'integer', 'description': '从0开始的行，范围0至14'}, 'col': {'type': 'integer', 'description': '从0开始的列，范围0至14'}, 'expected_revision': {'type': 'integer', 'description': 'move 必填；必须与 state 的 revision 相同，防止旧局面落子'}, 'side': {'type': 'string', 'enum': ['black', 'white'], 'description': 'move 必填；必须与当前 turn 相同'}}, 'required': ['action', 'workspace_dir'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except (InputError,ValueError,TypeError,KeyError,UnicodeError) as e:return {'ok':False,'message':str(e) if isinstance(e,InputError) else '输入或本地数据格式不正确，请按中文说明检查。'}
  except Exception:return {'ok':False,'message':'本地执行失败，请检查文件权限、运行环境和输入；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
