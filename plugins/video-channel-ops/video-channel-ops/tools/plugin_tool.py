"""视频频道日更流水线的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute,InputError
DESC='管理视频频道的每日制作：new_channel 创建频道目录（只需频道名称，其余可留空；只问用户一次，不逐项追问）、status 查看今天栏位与进行中任务、log_step 记录 7 步进度、log_job / job_done 记录付费生成任务 job ID、publish 记录经平台确认的视频 ID（两步：首次调用只返回要问用户的问题和 confirm_token，用户下一条消息确认后再带 token 调用）、log_metric 记录 24h/72h/7d 指标、finish_day 收尾、authorize 修改上传/付费授权、render 用 FFmpeg 渲染、preflight 上传前机器检查。只写频道目录内文件，不联网、不上传、不付费。'
S={'type':'string'}
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='video_channel',name='video_channel',description=DESC,input_params={'type':'object','properties':{
   'action':{'type':'string','enum':['status','new_channel','log_step','log_job','job_done','publish','log_metric','finish_day','authorize','render','preflight']},
   'channel_dir':{'type':'string','description':'频道目录绝对路径（Windows 盘符路径在 WSL/Linux 上会映射到 /mnt/<盘符>）'},
   'date':{'type':'string','description':'YYYY-MM-DD；留空则按 channel.json 时区取今天'},
   'slot':{'type':'string','enum':['long','short'],'description':'long=长视频，short=短视频'},
   'name':S,'handle':S,'language':S,'timezone':{'type':'string','description':'IANA 时区，默认 Asia/Shanghai'},'topic':S,'tone':S,
   'long_format':S,'short_format':S,'voice_provider':S,'voice_id':S,'visual_provider':S,'visual_style':S,
   'step':{'type':'string','enum':['调研','脚本','配音','画面','渲染','字幕与检查','上传']},
   'status':{'type':'string','description':'log_step：完成/进行中/待人工/跳过/失败；job_done：已完成/失败；publish：已预约/已公开'},
   'files':{'type':'array','items':S,'description':'相对频道目录的结果文件路径'},'note':S,
   'job_id':S,'tool':{'type':'string','description':'生成工具名称，如 ElevenLabs'},'purpose':S,'credits':{'type':'number'},'result':S,
   'video_id':S,'title':S,'confirm_token':{'type':'string','description':'publish 第二步：仅在用户于下一条消息中明确确认已在平台看到后，传入第一步返回的 confirm_token'},
   'checkpoint':{'type':'string','enum':['24h','72h','7d']},'elapsed_hours':{'type':'number'},
   'views':{'type':'number'},'likes':{'type':'number'},'comments':{'type':'number'},'watch_minutes':{'type':'number'},'subscribers_gained':{'type':'number'},
   'daily_upload':{'type':'boolean'},'additional_payments':{'type':'boolean'},
   'confirm':{'type':'boolean','description':'authorize 或覆盖已记录视频 ID 时必填 true；只有用户明确同意后才可传'},
   'run_dir':{'type':'string','description':'render 的运行目录（相对频道目录），内含 scenes.json 与 narration.*'},'long_form':{'type':'boolean','description':'true 输出 1920x1080 横屏，默认 1080x1920 竖屏'},
   'video':{'type':'string','description':'preflight 的视频路径'},'srt':{'type':'string','description':'preflight 的字幕路径（可选）'}},
   'required':['action','channel_dir'],'additionalProperties':False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except InputError as e:return {'ok':False,'message':str(e)}
  except (ValueError,TypeError,KeyError,UnicodeError):return {'ok':False,'message':'输入或本地数据格式不正确，请按中文说明检查。'}
  except OSError:return {'ok':False,'message':'本地文件读写或 FFmpeg 调用失败，请检查路径与权限；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
