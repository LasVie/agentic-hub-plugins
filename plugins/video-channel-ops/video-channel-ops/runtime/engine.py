"""视频频道日更流水线：频道目录、每日栏位状态、生成任务与指标记录。

频道目录结构与 channel.json / state.json / OPERATIONS.md 模板改编自 channelroom-studio/ai-youtube-os@a4eb2f9
（MIT，Copyright (c) 2026 Channelroom Studio）的 templates/ 与 commands/new-channel.md、daily.md 中的约定。
修改：模板译为简体中文并改用 {{TIMEZONE}}；由提示词约定改为工具强制的防重复、job ID 记录、
“上传尝试不等于完成”和授权确认。完整许可见 licenses/ai-youtube-os/LICENSE。
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,os,re,secrets,tempfile,threading,time
from . import media
class InputError(ValueError):pass
WIN_RE=re.compile(r'^([A-Za-z]):[\\/]*(.*)$')
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
TEMPLATES=Path(__file__).resolve().parent/'templates'
SLOTS={'long':'长视频','short':'短视频'}
STEPS=['调研','脚本','配音','画面','渲染','字幕与检查','上传']
STEP_STATUS=['完成','进行中','待人工','跳过','失败']
PUBLISHED=['已预约','已公开']
CHECKPOINTS=['24h','72h','7d']
DIRS=('research','content','production','runs')
FIELDS={'name':'CHANNEL_NAME','handle':'HANDLE','language':'LANGUAGE','timezone':'TIMEZONE','topic':'TOPIC','tone':'TONE',
 'long_format':'LONG_FORMAT','short_format':'SHORT_FORMAT','voice_provider':'VOICE_PROVIDER','voice_id':'VOICE_ID',
 'visual_provider':'VISUAL_PROVIDER','visual_style':'VISUAL_STYLE'}
CONFIRM='该操作会改变授权或覆盖已记录的发布结果；请先向用户说明并取得明确同意，再以 confirm=true 重新调用。'
def to_path(raw):
 raw=str(raw or '').strip()
 m=WIN_RE.match(raw)
 if m and os.name!='nt':raw='/mnt/'+m.group(1).lower()+'/'+m.group(2).replace('\\','/')
 return Path(raw).expanduser()
def channel_path(q,must_exist=True):
 p=to_path(q.get('channel_dir'))
 if not str(q.get('channel_dir') or '').strip() or not p.is_absolute():raise InputError('请提供频道目录的绝对路径（channel_dir）。')
 if must_exist and not (p/'channel.json').is_file():raise InputError(f'{p} 不是频道目录（缺少 channel.json）；请先用 new_channel 创建。')
 return p.resolve() if p.exists() else p
def load(p,default=None):
 if not p.exists():
  if default is not None:return default
  raise InputError(f'缺少文件：{p.name}')
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except json.JSONDecodeError:raise InputError(f'{p.name} 不是有效的 JSON，请先手动修复；未做任何修改。')
def save(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 fd,t=tempfile.mkstemp(prefix='.pending-',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def now_iso():return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def today(ch,q,warn):
 d=str(q.get('date') or '').strip()
 if d:
  if not DATE_RE.match(d):raise InputError('date 格式应为 YYYY-MM-DD。')
  return d
 tz=ch.get('timezone') or ''
 try:
  from zoneinfo import ZoneInfo
  return datetime.now(ZoneInfo(tz)).strftime('%Y-%m-%d')
 except Exception:
  warn.append(f'无法识别时区「{tz}」，已按本机时间计算日期。')
  return datetime.now().strftime('%Y-%m-%d')
def slot_of(q):
 s=q.get('slot')
 if s not in SLOTS:raise InputError('slot 只能是 long（长视频）或 short（短视频）。')
 return s
def text(q,k,limit=500):
 v=q.get(k)
 if v is None:return ''
 if not isinstance(v,str):raise InputError(f'{k} 必须是文本。')
 v=v.strip()
 if len(v)>limit:raise InputError(f'{k} 最多 {limit} 个字符。')
 return v
def ctx(q):
 c=channel_path(q);warn=[]
 ch=load(c/'channel.json');st=load(c/'state.json',{'last_run_date':None,'slots':{},'pending_jobs':[],'metrics_due':[]})
 return c,ch,st,today(ch,q,warn),warn
def summary(c,ch,st,day,warn):
 slots=st.get('slots',{}).get(day,{})
 man=load(c/'runs'/day/'manifest.json',{'date':day,'steps':[]})
 jobs=[j for j in load(c/'production'/'jobs.json',[]) if j.get('status')=='进行中']
 done=[k for k in SLOTS if slots.get(k,{}).get('video_id')]
 due=[m for m in st.get('metrics_due',[]) if m.get('due_date','9999')<=day]
 msg=f'频道「{ch.get("name")}」{day}：'+('、'.join(SLOTS[k] for k in done)+' 已发布/预约，' if done else '')+ \
  (('待制作：'+'、'.join(SLOTS[k] for k in SLOTS if k not in done)) if len(done)<len(SLOTS) else '今天的栏位都已完成，不要再新建。')
 if jobs:msg+=f'；有 {len(jobs)} 个进行中的生成任务，请用原 job ID 继续取回结果，不要重新提交'
 r={'ok':True,'channel_dir':str(c),'date':day,'slots':slots,'done_slots':done,'steps':man.get('steps',[]),'pending_jobs':jobs,
  'metrics_due':due,'authorization':ch.get('authorization',{}),'last_run_date':st.get('last_run_date'),'message':msg+'。'}
 if warn:r['warnings']=warn
 return r
def a_new_channel(q):
 c=channel_path(q,must_exist=False)
 if (c/'channel.json').exists():raise InputError(f'{c} 已有 channel.json，未覆盖任何文件。')
 if c.exists() and not c.is_dir():raise InputError(f'{c} 已存在且不是目录。')
 vals={v:text(q,k,200) for k,v in FIELDS.items()}
 vals['LANGUAGE']=vals['LANGUAGE'] or '简体中文';vals['TIMEZONE']=vals['TIMEZONE'] or 'Asia/Shanghai'
 if not vals['CHANNEL_NAME']:raise InputError('请提供频道名称（name）。')
 c.mkdir(parents=True,exist_ok=True)
 for d in DIRS:(c/d).mkdir(exist_ok=True)
 for f in ('channel.json','OPERATIONS.md','state.json'):
  t=(TEMPLATES/f).read_text(encoding='utf-8')
  for k,v in vals.items():t=t.replace('{{'+k+'}}',json.dumps(v,ensure_ascii=False)[1:-1] if f.endswith('.json') else v)
  (c/f).write_text(t,encoding='utf-8')
 save(c/'production'/'jobs.json',[])
 blank=[k for k,v in FIELDS.items() if not vals[v]]
 r={'ok':True,'channel_dir':str(c),'created':['channel.json','OPERATIONS.md','state.json','production/jobs.json']+[d+'/' for d in DIRS],
  'authorization':{'daily_upload':False,'additional_payments':False},
  'message':'已创建频道目录。下一步：按频道实际情况修改 OPERATIONS.md；第一期先在不上传的情况下试做。'}
 if blank:r['blank_fields']=blank;r['message']+=' 未填写的项目：'+'、'.join(blank)+'，可稍后在 channel.json 中补充。'
 return r
def a_status(q):return summary(*ctx(q))
def a_log_step(q):
 c,ch,st,day,warn=ctx(q);slot=slot_of(q)
 step=q.get('step')
 if step not in STEPS:raise InputError('step 只能是：'+'、'.join(STEPS)+'。')
 status=q.get('status')
 if status not in STEP_STATUS:raise InputError('status 只能是：'+'、'.join(STEP_STATUS)+'。')
 if step=='上传' and status=='完成':raise InputError('上传尝试不等于完成：请在平台确认预约/公开状态和视频 ID 后用 publish 记录。')
 if st.get('slots',{}).get(day,{}).get(slot,{}).get('video_id') and status in ('进行中','完成') and step!='上传':
  raise InputError(f'{day} 的{SLOTS[slot]}已有视频 ID，不要重复制作。')
 files=q.get('files') or []
 if not isinstance(files,list) or not all(isinstance(f,str) for f in files):raise InputError('files 必须是文本路径数组。')
 missing=[f for f in files if not (to_path(f) if to_path(f).is_absolute() else c/f).exists()]
 if missing and status=='完成':raise InputError('以下文件不存在，不能记为完成：'+'、'.join(missing))
 mp=c/'runs'/day/'manifest.json';man=load(mp,{'date':day,'steps':[]})
 man['steps']=[s for s in man['steps'] if not (s.get('slot')==slot and s.get('step')==step)]
 man['steps'].append({'slot':slot,'step':step,'status':status,'files':files,'note':text(q,'note'),'at':now_iso()})
 man['steps'].sort(key=lambda s:(s['slot'],STEPS.index(s['step'])))
 save(mp,man)
 r={'ok':True,'date':day,'manifest':str(mp),'message':f'已记录 {day} {SLOTS[slot]}「{step}」：{status}。'}
 if missing:r['warnings']=warn+['以下文件尚不存在：'+'、'.join(missing)]
 elif warn:r['warnings']=warn
 return r
def a_log_job(q):
 c,ch,st,day,warn=ctx(q);slot=slot_of(q)
 jid=text(q,'job_id',200);tl=text(q,'tool',100)
 if not jid or not tl:raise InputError('请提供 job_id 和 tool（生成工具名称）。')
 jp=c/'production'/'jobs.json';jobs=load(jp,[])
 old=next((j for j in jobs if j.get('job_id')==jid and j.get('tool')==tl),None)
 if old:return {'ok':True,'duplicate':True,'job':old,'message':f'job {jid} 已记录过（{old.get("status")}），不要重新提交，请用同一 job ID 查询结果。'}
 cr=q.get('credits')
 if cr is not None and (isinstance(cr,bool) or not isinstance(cr,(int,float)) or cr<0):raise InputError('credits 必须是非负数。')
 job={'job_id':jid,'tool':tl,'date':day,'slot':slot,'purpose':text(q,'purpose',200),'credits':cr,'status':'进行中','submitted_at':now_iso()}
 jobs.append(job);save(jp,jobs)
 st.setdefault('pending_jobs',[]);st['pending_jobs']=[x for x in st['pending_jobs'] if x!=jid]+[jid];save(c/'state.json',st)
 return {'ok':True,'job':job,'message':f'已记录生成任务 {jid}（{tl}）。拿不到结果时用同一 job ID 再查询，不要重新提交。'}
def a_job_done(q):
 c,ch,st,day,warn=ctx(q)
 jid=text(q,'job_id',200);status=q.get('status') or '已完成'
 if status not in ('已完成','失败'):raise InputError('status 只能是 已完成 或 失败。')
 jp=c/'production'/'jobs.json';jobs=load(jp,[])
 hit=[j for j in jobs if j.get('job_id')==jid]
 if not hit:raise InputError(f'jobs.json 中没有 job {jid}。')
 for j in hit:j.update(status=status,result=text(q,'result'),finished_at=now_iso())
 save(jp,jobs);st['pending_jobs']=[x for x in st.get('pending_jobs',[]) if x!=jid];save(c/'state.json',st)
 return {'ok':True,'job':hit[-1],'message':f'job {jid} 已标记为{status}。'}
def a_publish(q):
 c,ch,st,day,warn=ctx(q);slot=slot_of(q)
 vid=text(q,'video_id',100);status=q.get('status')
 if status not in PUBLISHED:raise InputError('status 只能是 已预约 或 已公开；用户没说明时先问用户，不要猜。')
 if not vid:raise InputError('上传尝试不等于完成：需要平台上的视频 ID 才能记录。')
 cur=st.setdefault('slots',{}).setdefault(day,{})
 if cur.get(slot,{}).get('video_id') and cur[slot]['video_id']!=vid and q.get('confirm') is not True:
  raise InputError(f'{day} 的{SLOTS[slot]}已记录视频 {cur[slot]["video_id"]}。'+CONFIRM)
 key=[day,slot,vid,status];pend=st.get('pending_publish') or {}
 tok=text(q,'confirm_token',100)
 if not tok or tok!=pend.get('token') or pend.get('key')!=key:
  pend={'token':secrets.token_hex(4),'key':key,'created_at':now_iso()};st['pending_publish']=pend;save(c/'state.json',st)
  qn=f'请问你是否已在平台后台亲眼看到视频 {vid} 处于「{status}」状态？'
  return {'ok':True,'recorded':False,'needs_user_confirmation':True,'question':qn,'confirm_token':pend['token'],
   'message':'尚未记录。先把 question 原样问用户并结束本轮回复；只有用户在下一条消息中明确确认后，才用同样参数加 confirm_token 再调用一次。不要在同一轮中自行确认。'}
 st.pop('pending_publish',None)
 cur[slot]={'video_id':vid,'status':status,'title':text(q,'title',200),'recorded_at':now_iso()}
 due=st.setdefault('metrics_due',[])
 base=datetime.strptime(day,'%Y-%m-%d')
 for cp,days in (('24h',1),('72h',3),('7d',7)):
  if not any(m.get('video_id')==vid and m.get('checkpoint')==cp for m in due):
   due.append({'video_id':vid,'slot':slot,'checkpoint':cp,'due_date':(base+timedelta(days=days)).strftime('%Y-%m-%d')})
 save(c/'state.json',st)
 r={'ok':True,'recorded':True,'date':day,'slot':cur[slot],'message':f'已记录 {day} {SLOTS[slot]}：{status}，视频 ID {vid}。已排好 24 小时 / 72 小时 / 7 天指标记录。'}
 if not ch.get('authorization',{}).get('daily_upload'):r['warnings']=warn+['channel.json 未授权自动上传（daily_upload=false）；此记录应来自用户本人完成的上传。请把这条提醒告诉用户。']
 return r
def a_log_metric(q):
 c,ch,st,day,warn=ctx(q);slot=slot_of(q)
 vid=text(q,'video_id',100);cp=q.get('checkpoint')
 if not vid or cp not in CHECKPOINTS:raise InputError('请提供 video_id 和 checkpoint（24h / 72h / 7d）。')
 h=q.get('elapsed_hours')
 if isinstance(h,bool) or not isinstance(h,(int,float)) or h<=0:raise InputError('elapsed_hours 必须是实际经过的小时数（正数）。')
 vals={}
 for k in ('views','likes','comments','watch_minutes','subscribers_gained'):
  v=q.get(k)
  if v is None:continue
  if isinstance(v,bool) or not isinstance(v,(int,float)) or v<0:raise InputError(f'{k} 必须是非负数；平台仍在处理的数值请留空，不要填 0。')
  vals[k]=v
 mp=c/'production'/'metrics.json';ms=load(mp,[])
 ms.append({'video_id':vid,'slot':slot,'checkpoint':cp,'elapsed_hours':h,**vals,'note':text(q,'note'),'recorded_at':now_iso()});save(mp,ms)
 st['metrics_due']=[m for m in st.get('metrics_due',[]) if not (m.get('video_id')==vid and m.get('checkpoint')==cp)];save(c/'state.json',st)
 same=[m for m in ms if m['slot']==slot and m['checkpoint']==cp]
 note=f'同类（{SLOTS[slot]}、{cp}）样本 {len(same)} 条'+('，少于 3 条，不要下结论。' if len(same)<3 else '。')
 return {'ok':True,'message':f'已记录视频 {vid} 的 {cp} 指标（实际经过 {h} 小时）。'+note}
def a_finish_day(q):
 c,ch,st,day,warn=ctx(q)
 st['last_run_date']=day;save(c/'state.json',st)
 r=summary(c,ch,st,day,warn);r['message']=f'已更新 last_run_date={day}。'+r['message'];return r
def a_authorize(q):
 c=channel_path(q);ch=load(c/'channel.json')
 changes={k:q[k] for k in ('daily_upload','additional_payments') if k in q}
 if not changes or not all(isinstance(v,bool) for v in changes.values()):raise InputError('请提供 daily_upload 和/或 additional_payments 的布尔值。')
 if q.get('confirm') is not True:raise InputError(CONFIRM)
 ch.setdefault('authorization',{}).update(changes);save(c/'channel.json',ch)
 return {'ok':True,'authorization':ch['authorization'],'message':'已更新授权：'+'，'.join(f'{k}={"true" if v else "false"}' for k,v in changes.items())+'。'}
def a_render(q):
 c=channel_path(q);rd=text(q,'run_dir',300)
 if not rd:raise InputError('请提供运行目录 run_dir（相对于频道目录，例如 runs/2026-10-27/short）。')
 p=to_path(rd);p=(p if p.is_absolute() else c/p).resolve()
 if c not in p.parents:raise InputError('run_dir 必须位于频道目录内。')
 if not p.is_dir():raise InputError(f'运行目录不存在：{rd}')
 r=media.render(p,bool(q.get('long_form')))
 return {'ok':True,**r,'message':f'已渲染 {r["size"]} 视频：{r["video"]}。渲染完成不等于完成，请接着运行 preflight。'}
def a_preflight(q):
 c=channel_path(q)
 def res(k):
  v=text(q,k,500)
  if not v:return None
  p=to_path(v);return p if p.is_absolute() else c/p
 v=res('video')
 if v is None:raise InputError('请提供要检查的视频路径 video。')
 rows=media.preflight(v,res('srt'))
 fail=any(r[0]=='FAIL' for r in rows)
 return {'ok':True,'passed':not fail,'checks':[{'status':a,'item':b,'detail':d} for a,b,d in rows],
  'human_checklist':['前 3 秒是否以问题或具体画面开场','字幕是否会被手机底部界面遮挡','每个事实句是否在 sources.json 中有来源',
   '外部图片 / 片段的使用授权是否记录在 rights.json','是否已确定平台“经过修改或合成的内容”披露项'],
  'message':('存在 FAIL 项，不要上传。' if fail else '机器检查无 FAIL。')+'人工检查项未经确认前一律记为“未确认”。'}
ACTIONS={k[2:]:v for k,v in globals().items() if k.startswith('a_')}
READ_ONLY={'status','render','preflight'}
_LOCK=threading.Lock()
class channel_lock:
 """同一频道的写操作串行执行：进程内线程锁 + 跨进程锁文件（超过 60 秒视为残留）。"""
 def __init__(self,q):
  self.ro=q.get('action') in READ_ONLY
  self.p=None if self.ro or q.get('action')=='new_channel' else channel_path(q)/'.channel.lock'
 def __enter__(self):
  if self.ro:return
  _LOCK.acquire()
  if not self.p:return
  end=time.monotonic()+30
  while True:
   try:os.close(os.open(self.p,os.O_CREAT|os.O_EXCL|os.O_WRONLY));return
   except FileExistsError:
    try:
     if time.time()-self.p.stat().st_mtime>60:self.p.unlink();continue
    except FileNotFoundError:continue
    if time.monotonic()>end:_LOCK.release();raise InputError('频道正被另一个操作占用，请稍后重试；未做任何修改。')
    time.sleep(0.05)
 def __exit__(self,*a):
  if self.ro:return
  try:
   if self.p:
    try:self.p.unlink()
    except FileNotFoundError:pass
  finally:_LOCK.release()
def execute(q):
 if not isinstance(q,dict):raise InputError('参数必须是对象。')
 f=ACTIONS.get(q.get('action'))
 if not f:raise InputError('未知操作；可用：'+'、'.join(ACTIONS)+'。')
 try:
  with channel_lock(q):return f(q)
 except media.MediaError as e:raise InputError(str(e))
