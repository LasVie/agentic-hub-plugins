"""视频频道日更流水线功能测试：经原生 Tool.invoke 调用，使用中文输入。

用法：python -B tests/video_channel_ops_functional.py [插件内层目录]
默认测试 plugins/video-channel-ops/video-channel-ops；可传解压后的 ZIP 内层目录。
找到 ffmpeg/ffprobe（PATH 或 FFMPEG_PATH/FFPROBE_PATH）时额外执行真实渲染与检查。
"""
import asyncio,importlib,json,os,shutil,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
pkg=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'plugins'/'video-channel-ops'/'video-channel-ops'
import importlib.util as u
spec=u.spec_from_file_location('video_channel_ops',pkg/'__init__.py',submodule_search_locations=[str(pkg)]);m=u.module_from_spec(spec);sys.modules['video_channel_ops']=m;spec.loader.exec_module(m)
tool=importlib.import_module('video_channel_ops.tools.plugin_tool')
media=importlib.import_module('video_channel_ops.runtime.media')
results=[]
def check(name,cond,detail=''):
 results.append((name,bool(cond)));print(('PASS' if cond else 'FAIL')+': '+name+('' if cond else ' — '+str(detail)))
def have_ff():
 try:media.tool('ffmpeg');media.tool('ffprobe');return True
 except media.MediaError:return False
async def main():
 root=tempfile.mkdtemp(prefix='频道测试-');ch=str(Path(root,'世界新闻解说'))
 call=lambda **q:tool.PluginTool().invoke({'channel_dir':ch,**q})
 r=await call(action='status');check('未建频道时中文报错',not r['ok'] and 'new_channel' in r['message'],r)
 r=await call(action='new_channel',name='世界新闻解说',topic='国际新闻解读',tone='冷静、重证据',short_format='60 秒，每天 1 条')
 check('新建频道',r['ok'] and 'channel.json' in r['created'] and 'voice_id' in r['blank_fields'],r)
 cj=json.loads(Path(ch,'channel.json').read_text(encoding='utf-8'))
 check('channel.json 中文与默认值',cj['name']=='世界新闻解说' and cj['language']=='简体中文' and cj['timezone']=='Asia/Shanghai' and cj['authorization']=={'daily_upload':False,'additional_payments':False} and cj['banned_expressions'][0]=='保证收益',cj)
 ops=Path(ch,'OPERATIONS.md').read_text(encoding='utf-8')
 check('OPERATIONS.md 中文模板已填充',ops.startswith('# 世界新闻解说 运营规范') and '{{' not in ops and '每日制作 7 步' in ops)
 check('目录结构',all(Path(ch,d).is_dir() for d in ('research','content','production','runs')) and json.loads(Path(ch,'production','jobs.json').read_text())==[])
 r=await call(action='new_channel',name='重复');check('已有频道不覆盖',not r['ok'] and '未覆盖' in r['message'],r)
 r=await call(action='new_channel',name='带"引号"的频道',channel_dir=str(Path(root,'q')))
 check('JSON 特殊字符安全',r['ok'] and json.loads(Path(root,'q','channel.json').read_text(encoding='utf-8'))['name']=='带"引号"的频道',r)
 D='2026-10-27'
 r=await call(action='status',date=D);check('status 显示待制作',r['ok'] and r['done_slots']==[] and '待制作：长视频、短视频' in r['message'],r)
 run=Path(ch,'runs',D,'short');run.mkdir(parents=True);(run/'script.md').write_text('# 今日短视频脚本\n为什么油价又涨了？',encoding='utf-8')
 r=await call(action='log_step',date=D,slot='short',step='脚本',status='完成',files=[f'runs/{D}/short/script.md'],note='前 3 秒提问开场')
 check('记录步骤',r['ok'] and '「脚本」：完成' in r['message'],r)
 r=await call(action='log_step',date=D,slot='short',step='画面',status='完成',files=['不存在.png'])
 check('文件不存在不能记完成',not r['ok'] and '不存在.png' in r['message'],r)
 r=await call(action='log_step',date=D,slot='short',step='配音',status='待人工',note='未连接配音工具')
 man=json.loads(Path(ch,'runs',D,'manifest.json').read_text(encoding='utf-8'))
 check('manifest 按步骤排序',[s['step'] for s in man['steps']]==['脚本','配音'] and man['steps'][1]['status']=='待人工',man)
 r=await call(action='log_step',date=D,slot='short',step='上传',status='完成')
 check('上传尝试不能记为完成',not r['ok'] and '上传尝试不等于完成' in r['message'],r)
 r=await call(action='log_step',date=D,slot='short',step='剪辑',status='完成');check('非法步骤中文报错',not r['ok'] and '调研' in r['message'],r)
 r=await call(action='log_job',date=D,slot='short',job_id='el-001',tool='ElevenLabs',purpose='短视频旁白',credits=120)
 check('记录生成任务',r['ok'] and r['job']['status']=='进行中',r)
 r=await call(action='log_job',date=D,slot='short',job_id='el-001',tool='ElevenLabs')
 check('重复 job 提示勿重提',r['ok'] and r.get('duplicate') and '不要重新提交' in r['message'],r)
 r=await call(action='status',date=D);check('status 显示进行中任务',len(r['pending_jobs'])==1 and '不要重新提交' in r['message'],r)
 r=await call(action='log_job',date=D,slot='short',job_id='x',tool='y',credits=-1);check('负 credits 拒绝',not r['ok'],r)
 r=await call(action='job_done',job_id='el-001',result=f'runs/{D}/short/narration.mp3')
 check('任务完成',r['ok'] and r['job']['status']=='已完成' and json.loads(Path(ch,'state.json').read_text())['pending_jobs']==[],r)
 r=await call(action='publish',date=D,slot='short',status='已预约');check('无视频 ID 不能记发布',not r['ok'] and '视频 ID' in r['message'],r)
 r=await call(action='publish',date=D,slot='short',status='已预约',video_id='abc123',title='油价为何又涨？')
 tok=r.get('confirm_token')
 check('发布第一步只提问不记录',r['ok'] and r['recorded'] is False and r['needs_user_confirmation'] and 'abc123' in r['question'] and '已预约' in r['question'] and tok and 'abc123' not in json.dumps(json.loads(Path(ch,'state.json').read_text(encoding='utf-8')).get('slots',{})),r)
 r=await call(action='publish',date=D,slot='short',status='已预约',video_id='abc123',confirm_token='wrong');check('错误 token 不记录',r['recorded'] is False and r['confirm_token']!=tok,r)
 tok=r['confirm_token']
 r=await call(action='publish',date=D,slot='short',status='已公开',video_id='abc123',confirm_token=tok);check('参数变化后旧 token 失效',r['recorded'] is False,r)
 tok=r['confirm_token']
 r=await call(action='publish',date=D,slot='short',status='已公开',video_id='abc123',confirm_token=tok,title='油价为何又涨？')
 check('第二步带 token 记录并提示未授权自动上传',r['ok'] and r['recorded'] and 'daily_upload=false' in ' '.join(r.get('warnings',[])),r)
 r=await call(action='publish',date=D,slot='short',status='已预约',video_id='zzz');check('发布缺 status 时中文提示先问',not (await call(action='publish',date=D,slot='short',video_id='zzz'))['ok'],r)
 st=json.loads(Path(ch,'state.json').read_text(encoding='utf-8'))
 check('排好 24h/72h/7d 指标',[x['due_date'] for x in st['metrics_due']]==['2026-10-28','2026-10-30','2026-11-03'],st['metrics_due'])
 r=await call(action='log_step',date=D,slot='short',step='渲染',status='进行中');check('已发布栏位拒绝重复制作',not r['ok'] and '不要重复制作' in r['message'],r)
 r=await call(action='publish',date=D,slot='short',status='已公开',video_id='zzz');check('覆盖视频 ID 需确认',not r['ok'] and 'confirm=true' in r['message'],r)
 r=await call(action='status',date=D);check('status 显示短视频已完成',r['done_slots']==['short'] and '短视频 已发布/预约' in r['message'] and '待制作：长视频' in r['message'],r)
 r=await call(action='status',date='2026-10-28');check('指标到期提醒',[x['checkpoint'] for x in r['metrics_due']]==['24h'],r['metrics_due'])
 r=await call(action='log_metric',date='2026-10-28',slot='short',video_id='abc123',checkpoint='24h',elapsed_hours=26,views=0)
 check('指标记录（0 允许，处理中留空）',r['ok'] and '实际经过 26 小时' in r['message'] and '少于 3 条' in r['message'],r)
 r=await call(action='log_metric',slot='short',video_id='abc123',checkpoint='24h',elapsed_hours=0);check('经过时间必须为正',not r['ok'],r)
 r=await call(action='status',date='2026-10-28');check('已记录指标不再提醒',r['metrics_due']==[],r['metrics_due'])
 r=await call(action='authorize',daily_upload=True);check('授权需 confirm',not r['ok'] and '明确同意' in r['message'],r)
 r=await call(action='authorize',daily_upload=True,confirm=True);check('授权修改',r['ok'] and json.loads(Path(ch,'channel.json').read_text(encoding='utf-8'))['authorization']['daily_upload'] is True,r)
 r=await call(action='finish_day',date=D);check('收尾更新 last_run_date',r['ok'] and r['last_run_date']==D,r)
 r=await asyncio.gather(*[call(action='log_step',date='2026-10-29',slot='long',step=st_,status='待人工') for st_ in ['调研','脚本','配音','画面','渲染','字幕与检查','上传']])
 man=json.loads(Path(ch,'runs','2026-10-29','manifest.json').read_text(encoding='utf-8'))
 check('并行记录 7 步不丢失',all(x['ok'] for x in r) and [x['step'] for x in man['steps']]==['调研','脚本','配音','画面','渲染','字幕与检查','上传'] and not Path(ch,'.channel.lock').exists(),man)
 r=await call(action='render',run_dir='../..');check('render 拒绝越出频道目录',not r['ok'] and '频道目录内' in r['message'],r)
 r=await call(action='render',run_dir=f'runs/{D}/short');check('render 缺 scenes.json 中文报错',not r['ok'] and 'scenes.json' in r['message'],r)
 r=await call(action='preflight',video='没有.mp4');check('preflight 缺文件中文报错',not r['ok'] and '找不到视频文件' in r['message'],r)
 # 纯逻辑（不需要 FFmpeg）
 check('最后场景拉长覆盖旁白',media.plan_durations([2.0,3.0],7.5)==[2.0,5.5])
 check('旁白较短不改时长',media.plan_durations([2.0,3.0],4.0)==[2.0,3.0])
 try:media.plan_durations([1,0],3);check('零时长拒绝',False)
 except media.MediaError as e:check('零时长拒绝','正数' in str(e))
 try:media.inside(Path(root),'../x.png');check('场景路径越界拒绝',False)
 except media.MediaError as e:check('场景路径越界拒绝','越出' in str(e))
 check('SRT 结束时间',media.last_caption_end('1\n00:00:00,000 --> 00:00:02,500\n你好\n\n2\n00:00:02,500 --> 00:00:58,200\n再见\n')==58.2)
 V=lambda w,h,d,a=True:{'streams':[{'codec_type':'video','width':w,'height':h}]+([{'codec_type':'audio'}] if a else []),'format':{'duration':str(d)}}
 rows=media.checks(V(1080,1920,200),-20,-3,190.0)
 check('竖屏超 180 秒警告',('WARN','时长') in [(a,b) for a,b,_ in rows] and '竖屏/Shorts' in rows[0][2],rows)
 check('字幕结尾偏差警告',rows[-1][0]=='WARN' and rows[-1][1]=='字幕',rows)
 check('无声判 FAIL',any(a=='FAIL' and b=='音频' for a,b,_ in media.checks(V(1920,1080,60),-80,-50,None)))
 check('无音轨判 FAIL',any(a=='FAIL' and '没有音频轨' in d for a,_,d in media.checks(V(1920,1080,60,False),None,None,None)))
 check('削波警告',any(a=='WARN' and '削波' in d for a,_,d in media.checks(V(1920,1080,60),-20,-0.1,None)))
 check('音量未读出时标未确认',any(a=='WARN' and '未确认' in d for a,_,d in media.checks(V(1920,1080,60),None,None,None,has_volume=False)))
 old=os.environ.get('PATH');os.environ['PATH']='';fp=os.environ.pop('FFMPEG_PATH',None);fq=os.environ.pop('FFPROBE_PATH',None)
 try:
  (run/'scenes.json').write_text('[{"image":"a.png","duration":1}]',encoding='utf-8');(run/'narration.mp3').write_bytes(b'')
  r=await call(action='render',run_dir=f'runs/{D}/short');check('缺 FFmpeg 时中文安装提示',not r['ok'] and '未找到 ffprobe' in r['message'] and 'FFPROBE_PATH' in r['message'],r)
 finally:
  os.environ['PATH']=old or ''
  if fp:os.environ['FFMPEG_PATH']=fp
  if fq:os.environ['FFPROBE_PATH']=fq
 if have_ff():
  import subprocess
  ff=media.tool('ffmpeg')
  for i,c in enumerate(('red','blue')):subprocess.run([ff,'-y','-loglevel','error','-f','lavfi','-i',f'color={c}:s=640x480','-frames:v','1',str(run/f's{i}.png')],check=True)
  subprocess.run([ff,'-y','-loglevel','error','-f','lavfi','-i','sine=frequency=440:duration=4','-filter:a','volume=0.3',str(run/'narration.mp3')],check=True)
  (run/'scenes.json').write_text(json.dumps([{'image':'s0.png','duration':1},{'image':'s1.png','duration':1}]),encoding='utf-8')
  r=await call(action='render',run_dir=f'runs/{D}/short');check('真实渲染竖屏 MP4',r['ok'] and r['size']=='1080x1920' and r['scene_seconds'][-1]>=2.9 and (run/'final.mp4').is_file(),r)
  (run/'final.srt').write_text('1\n00:00:00,000 --> 00:00:03,900\n为什么油价又涨了？\n',encoding='utf-8')
  r=await call(action='preflight',video=f'runs/{D}/short/final.mp4',srt=f'runs/{D}/short/final.srt')
  check('真实检查通过',r['ok'] and r['passed'] and [c['item'] for c in r['checks']]==['分辨率','时长','音频','字幕'] and len(r['human_checklist'])==5,r)
  subprocess.run([ff,'-y','-loglevel','error','-f','lavfi','-i','color=black:s=1920x1080:d=2','-f','lavfi','-i','anullsrc','-shortest',str(run/'silent.mp4')],check=True)
  r=await call(action='preflight',video=f'runs/{D}/short/silent.mp4');check('真实检查无声 FAIL',r['ok'] and not r['passed'] and '不要上传' in r['message'],r)
 else:print('SKIP: 未找到 FFmpeg，跳过真实渲染与检查')
 shutil.rmtree(root,ignore_errors=True)
asyncio.run(main())
ok=sum(p for _,p in results);print(f'\n{ok}/{len(results)} passed');sys.exit(0 if ok==len(results) else 1)
