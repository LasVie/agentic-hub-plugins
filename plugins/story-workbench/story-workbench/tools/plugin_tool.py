"""小说创作台：中文本机交互与原生工具适配。"""
import asyncio,json,subprocess,shutil
from pathlib import Path
from openjiuwen.core.foundation.tool import Tool,ToolCard
ROOT=Path(__file__).resolve().parents[1]
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='story_workbench',name='story_workbench',description='管理本地小说项目、人物、章节与修订历史；在中文编辑器中添加可重新定位的原文批注，不自动生成或改写正文。',input_params={'type': 'object', 'properties': {'workspace_dir': {'type': 'string', 'description': '已存在工作目录绝对路径；此目录内保存插件数据。'}, 'action': {'type': 'string', 'enum': ['help', 'open_ui', 'stop_ui', 'status', 'create_project', 'save_character', 'save_chapter', 'annotate', 'resolve_annotation', 'export_project'], 'description': '先用help获取各操作的payload字段；open_ui打开中文交互工作台。'}, 'payload': {'type': 'object', 'description': '各操作参数见help；写操作须先status并传expected_revision。', 'additionalProperties': True}}, 'required': ['workspace_dir', 'action'], 'additionalProperties': False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  if not isinstance(inputs,dict):return {'ok':False,'message':'输入须为对象。'}
  def call():
   candidates=['/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node',shutil.which('node')]
   executable=next((p for p in candidates if p and Path(p).is_file()),None)
   if not executable:return {'ok':False,'message':'没有找到Node.js，请使用支持SQLite与类型擦除的Node22.6+运行时。'}
   raw=json.dumps(inputs,ensure_ascii=False)
   if len(raw.encode())>256000:return {'ok':False,'message':'输入过大。'}
   r=subprocess.run([executable,'--no-warnings','--experimental-sqlite','--experimental-strip-types',str(ROOT/'runtime/cli.mjs')],input=raw,text=True,capture_output=True,timeout=50)
   if r.returncode or len(r.stdout)>16000000:return {'ok':False,'message':'本机运行时未成功返回结果，请核对Node版本与权限。'}
   result=json.loads(r.stdout)
   if not isinstance(result,dict):return {'ok':False,'message':'本机结果格式不正确。'}
   return result
  try:return await asyncio.to_thread(call)
  except subprocess.TimeoutExpired:return {'ok':False,'message':'操作超时，请读取当前记录后再重试，避免重复写入。'}
  except Exception:return {'ok':False,'message':'本机操作未确认成功，请检查工作目录、运行时与文件权限。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
