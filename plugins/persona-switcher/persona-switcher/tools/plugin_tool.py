"""会话人设切换的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute,InputError
DESC='管理工作目录内的角色库并切换当前人设与说话风格：status 查询、list 列出、use 切换、none 回到默认、default 设默认、create 新建或覆盖、delete 删除、init 添加示例角色。只改变说话的人设，不改变工具、技能、模型或权限；除 status/list 外仅在用户明确要求时调用。'
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='persona_switch',name='persona_switch',description=DESC,input_params={'type':'object','properties':{
   'workspace_dir':{'type':'string','description':'已存在工作目录的绝对路径（Windows 盘符路径在 WSL/Linux 上会自动映射到 /mnt/<盘符>）；角色库和状态保存在其中的 .persona-switcher/'},
   'action':{'type':'string','enum':['status','list','use','none','default','create','delete','init']},
   'role_id':{'type':'string','description':'角色 id：小写字母、数字、连字符，最多 64 字符；default 传空字符串或 none 表示清除默认'},
   'name':{'type':'string','description':'create 时的角色显示名'},
   'description':{'type':'string','description':'create 时的一句话描述'},
   'persona':{'type':'string','description':'create 时的人设正文（Markdown）'},
   'overwrite':{'type':'boolean','description':'create 时覆盖同 id 角色，需用户明确同意'},
   'confirm':{'type':'boolean','description':'delete 或覆盖时必填 true；只有在向用户确认且用户明确同意后才可传'}},
   'required':['action','workspace_dir'],'additionalProperties':False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except InputError as e:return {'ok':False,'message':str(e)}
  except (ValueError,TypeError,KeyError,UnicodeError):return {'ok':False,'message':'输入或本地数据格式不正确，请按中文说明检查。'}
  except OSError:return {'ok':False,'message':'本地文件读写失败，请检查工作目录权限；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
