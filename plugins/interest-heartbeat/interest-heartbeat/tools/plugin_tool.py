"""兴趣心跳主动分享的 WorkSwarm 原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool,ToolCard
from ..runtime.engine import execute,InputError
DESC=('兴趣心跳：按节律醒来、按兴趣闲逛找新东西、由代码闸门（暂停/静默时段/忙时窗口/每日上限/冷却）决定能否开口。'
 '一跳流程：beat → （闲逛到期时）web 搜索 + add_seed + browse_done → （闸门放行时）pick → 说一两句并 confirm_send，或 skip。'
 '不开口时只回复 （心跳：这次没有值得说的）。其他动作：status 查看状态与定时任务提示词、configure 修改节律与时段、interests 管理兴趣、'
 'profile 记录用户喜好（只记用户明确说过的）、carry 心事匣、seeds 素材池、ledger 账本与审计、reset 清空（需用户明确同意）。只读写本地插件数据目录。')
S={'type':'string'}
class PluginTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id='interest_heartbeat',name='interest_heartbeat',description=DESC,input_params={'type':'object','properties':{
   'action':{'type':'string','enum':['status','configure','interests','profile','beat','add_seed','browse_done','pick','confirm_send','skip','carry','seeds','ledger','reset']},
   'op':{'type':'string','description':'interests：list/add/remove/set；profile：list/add/remove；seeds：list/remove'},
   'items':{'type':'array','items':S,'description':'interests 的兴趣条目'},
   'kind':{'type':'string','enum':['like','dislike','fact','avoid'],'description':'画像分区：喜欢/不喜欢/近况事实/别提'},
   'text':{'type':'string','description':'add_seed 的素材一两句话；profile 的画像条目；carry 的心事（留空则清空）'},
   'source':{'type':'string','description':'add_seed：browse/chat/hand；profile：user（用户明确说的）/chat（从聊天推断）'},
   'topic':{'type':'string','description':'add_seed 的合并键，同话题素材合并为一条'},
   'tag':{'type':'string','enum':['news','fandom','scene','promise'],'description':'素材类别：资讯(3天)/圈内动态(14天)/日常话题(60天)/约定待办(90天)'},
   'url':{'type':'string','description':'素材来处链接'},
   'id':{'type':'string','description':'要删除的素材或画像条目 ID'},
   'focus':{'type':'string','description':'browse_done 的本次闲逛焦点'},'added':{'type':'integer'},
   'summary':{'type':'string','description':'confirm_send：本次说了什么（一句话）'},
   'seed_ids':{'type':'array','items':S,'description':'confirm_send：本次用到的素材 ID'},
   'clear_carry':{'type':'boolean','description':'confirm_send：说出心事匣内容后传 true 清空'},
   'reason':{'type':'string','description':'skip 的原因'},
   'limit':{'type':'integer'},
   'paused':{'type':'boolean'},'timezone':{'type':'string','description':'IANA 时区，如 Asia/Shanghai'},
   'interval_minutes':{'type':'number','description':'心跳间隔（供定时任务使用）'},
   'max_daily':{'type':'number'},'cooldown_minutes':{'type':'number'},
   'quiet_hours':{'type':'string','description':'静默时段，HH:MM-HH:MM，可跨午夜；空字符串表示取消'},
   'busy_windows':{'type':'array','items':S,'description':'忙时窗口列表，每项 HH:MM-HH:MM；空数组表示取消'},
   'browse_windows':{'type':'array','items':S,'description':'闲逛时段列表，每项 HH:MM-HH:MM'},
   'browse_min_interval_hours':{'type':'number'},'max_seeds_per_visit':{'type':'number'},'daily_browse_sessions':{'type':'number'},
   'scope':{'type':'string','enum':['seeds','ledger','profile','all']},
   'confirm':{'type':'boolean','description':'reset 必填 true；只有用户明确同意后才可传'}},
   'required':['action'],'additionalProperties':False},parallel_safe=False))
 async def invoke(self,inputs,**kwargs):
  try:return await asyncio.to_thread(execute,inputs)
  except InputError as e:return {'ok':False,'message':str(e)}
  except (ValueError,TypeError,KeyError,UnicodeError):return {'ok':False,'message':'输入或本地数据格式不正确，请按中文说明检查。'}
  except OSError:return {'ok':False,'message':'本地数据目录读写失败，请检查路径与权限；未确认操作成功。'}
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
