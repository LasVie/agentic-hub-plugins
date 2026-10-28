"""兴趣心跳主动分享功能测试：经原生 Tool.invoke 与引擎（固定时间）调用，使用中文输入。

用法：python -B tests/interest_heartbeat_functional.py [插件内层目录]
默认测试 plugins/interest-heartbeat/interest-heartbeat；可传解压后的 ZIP 内层目录。
"""
import asyncio,importlib,json,os,sys,tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[1]
pkg=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'plugins'/'interest-heartbeat'/'interest-heartbeat'
os.environ['INTEREST_HEARTBEAT_DATA_DIR']=tempfile.mkdtemp(prefix='心跳测试-')
import importlib.util as u
spec=u.spec_from_file_location('interest_heartbeat',pkg/'__init__.py',submodule_search_locations=[str(pkg)]);m=u.module_from_spec(spec);sys.modules['interest_heartbeat']=m;spec.loader.exec_module(m)
tool=importlib.import_module('interest_heartbeat.tools.plugin_tool')
eng=importlib.import_module('interest_heartbeat.runtime.engine')
TZ=ZoneInfo('Asia/Shanghai')
def at(day,hm):return datetime.fromisoformat(f'2026-10-{day:02d}T{hm}:00').replace(tzinfo=TZ).timestamp()
results=[]
def check(name,cond,detail=''):
 results.append((name,bool(cond)));print(('PASS' if cond else 'FAIL')+': '+name+('' if cond else ' — '+json.dumps(detail,ensure_ascii=False,default=str)[:400]))
E=lambda now,**q:eng.execute(q,now=now)
def err(now,**q):
 try:eng.execute(q,now=now);return None
 except eng.InputError as e:return str(e)
async def main():
 call=lambda **q:tool.PluginTool().invoke(q)
 r=await call(action='status');check('status 默认设置与 cron 提示词',r['ok'] and r['设置']['每日上限']==10 and 'HEARTBEAT_OK' in r['cron_prompt'],r)
 r=await call(action='configure',timezone='Asia/Shanghai',busy_windows=['09:00-10:00']);check('configure 时区与忙时窗口',r['ok'] and r['config']['忙时窗口']==['09:00-10:00'],r)
 r=await call(action='configure',quiet_hours='25:00-08:00');check('非法时段中文报错',not r['ok'] and 'HH:MM' in r['message'],r)
 r=await call(action='configure',max_daily=-1);check('非法数值中文报错',not r['ok'] and 'max_daily' in r['message'],r)
 r=await call(action='configure',timezone='火星/基地');check('非法时区中文报错',not r['ok'] and '无法识别的时区' in r['message'],r)
 r=await call(action='interests',op='set',items=['咖啡','独立游戏','AI 工具']);check('兴趣 set',r['interests']==['咖啡','独立游戏','AI 工具'],r)
 r=await call(action='interests',op='remove',items=['不存在']);check('删除不存在兴趣报错',not r['ok'] and '没有' in r['message'],r)
 r=await call(action='profile',op='add',kind='avoid',text='剧透',source='user');check('画像 别提',r['ok'] and r['profile']['别提']==['剧透'],r)
 r=await call(action='profile',op='add',kind='like',text='手冲咖啡');pid=r['id'];check('画像 推断条目置信度上限 0.6',r['ok'],r)
 r=await call(action='profile',op='list');check('画像列表',any(x['id']==pid and x['confidence']==0.6 for x in r['entries']),r)
 r=await call(action='profile',op='add',kind='bogus',text='x');check('画像非法分区报错',not r['ok'] and 'kind' in r['message'],r)
 # 静默时段（默认 01:00-08:00）
 r=E(at(28,'03:00'),action='beat');check('静默时段 SILENT',r['闸门']['verdict']=='SILENT' and '静默时段' in r['闸门']['reason'] and 'HEARTBEAT_OK' in r['下一步'],r)
 r=E(at(28,'09:30'),action='beat');check('忙时窗口 SILENT',r['闸门']['verdict']=='SILENT' and '忙时窗口' in r['闸门']['reason'],r)
 r=E(at(28,'10:30'),action='beat');check('10:30 可开口、未到闲逛时段',r['闸门']['verdict']=='SPEAK' and not r['闲逛']['due'] and '不在闲逛时段' in r['闲逛']['reason'],r)
 r=E(at(28,'10:30'),action='pick');check('空素材池 pick',r['可以开口'] and r['素材']==[] and r['画像']['别提']==['剧透'],r)
 # 闲逛焦点轮换
 r=E(at(28,'11:10'),action='beat');check('11:10 闲逛到期、焦点为第一个兴趣',r['闲逛']['due'] and r['闲逛']['focus']=='咖啡' and r['闲逛']['max_seeds']==2,r)
 a=E(at(28,'11:12'),action='add_seed',text='某烘焙商发布了新的浅烘埃塞豆',topic='浅烘新豆',tag='news',url='https://example.com/a')
 b=E(at(28,'11:12'),action='add_seed',text='某烘焙商发布了新的浅烘埃塞豆',topic='浅烘新豆',tag='news')
 c=E(at(28,'11:13'),action='add_seed',text='同一款豆子加了限量版',topic='浅烘新豆',tag='news')
 check('素材新增 / 完全重复 / 同话题合并',a['kind']=='added' and b['kind']=='duplicate' and c['kind']=='merged' and c['id']==a['id'],[a,b,c])
 check('空素材报错','不能为空' in (err(at(28,'11:13'),action='add_seed',text='  ') or ''))
 E(at(28,'11:14'),action='browse_done',focus='咖啡',added=1)
 r=E(at(28,'12:00'),action='beat');check('同日间隔不足 4 小时不再闲逛',not r['闲逛']['due'] and '不足' in r['闲逛']['reason'],r)
 r=E(at(28,'17:30'),action='beat');check('下一次焦点轮换到下一个兴趣',r['闲逛']['due'] and r['闲逛']['focus']=='独立游戏',r)
 E(at(28,'17:31'),action='browse_done',focus='独立游戏',added=0)
 r=E(at(28,'20:30'),action='beat');check('每天最多闲逛 2 次',not r['闲逛']['due'] and '2 次' in r['闲逛']['reason'],r)
 r=E(at(29,'11:30'),action='beat');check('次日焦点轮换到 AI 工具（3 天冷却）',r['闲逛']['focus']=='AI 工具',r)
 # 开口、冷却、记账
 r=E(at(28,'12:00'),action='pick');sid=r['素材'][0]['id'] if r['素材'] else None
 check('pick 返回素材与来处',r['可以开口'] and sid==a['id'] and r['素材'][0]['url']=='https://example.com/a' and r['素材'][0]['类别']=='资讯',r)
 r=E(at(28,'12:01'),action='confirm_send',summary='分享了浅烘新豆',seed_ids=[sid]);check('confirm_send 记账',r['ok'] and r['今日次数']=='1/10' and r['已计用素材']==[sid],r)
 r=E(at(28,'12:10'),action='beat');check('冷却中 SILENT',r['闸门']['verdict']=='SILENT' and '冷却中' in r['闸门']['reason'],r)
 r=E(at(28,'12:10'),action='pick');check('冷却中 pick 拒绝',not r['可以开口'] and '冷却' in r['原因'],r)
 r=E(at(28,'12:40'),action='pick');check('冷却结束可再开口',r['可以开口'] and r['今天已说']==['分享了浅烘新豆'],r)
 E(at(28,'12:41'),action='confirm_send',summary='第二次',seed_ids=[sid])
 r=E(at(28,'13:20'),action='seeds');check('用满 2 次的素材退役',all(x['id']!=sid for x in r['活跃']) and r['已归档数']>=1,r)
 E(at(28,'13:20'),action='configure',max_daily=2)
 r=E(at(28,'14:00'),action='beat');check('每日上限 SILENT',r['闸门']['verdict']=='SILENT' and '上限' in r['闸门']['reason'],r)
 r=E(at(28,'14:00'),action='confirm_send',summary='迟到的一句');check('闸门变化后记账仍入账并提示',r['ok'] and '提示' in r and r['今日次数']=='3/2',r)
 r=E(at(29,'10:30'),action='beat');check('跨天重置每日计数',r['闸门']['verdict']=='SPEAK',r)
 # 聊天素材用一次即退役、TTL 过期、心事匣
 s=E(at(29,'10:31'),action='add_seed',text='用户说周末想去看展',source='chat',tag='promise')
 E(at(29,'10:32'),action='confirm_send',summary='问了看展',seed_ids=[s['id']])
 r=E(at(29,'10:33'),action='seeds');check('聊天素材用一次退役',all(x['id']!=s['id'] for x in r['活跃']),r)
 n=E(at(29,'10:34'),action='add_seed',text='短期资讯',tag='news')
 r=E(at(29,'10:34')+4*86400,action='beat');check('资讯 3 天后过期',r['维护']['expired']>=1,r['维护'])
 E(at(29,'11:00'),action='carry',text='上次没说完：那家店周三休息')
 r=E(at(29,'11:00')+3600,action='pick');check('心事匣进入素材包',r.get('心事匣')=='上次没说完：那家店周三休息',r)
 E(at(29,'12:30'),action='confirm_send',summary='说了店休',clear_carry=True)
 r=E(at(29,'12:31'),action='status');check('说出后清空心事匣',r['心事匣']=='',r)
 # 素材池上限淘汰
 for i in range(20):E(at(29,'13:00'),action='add_seed',text=f'闲逛素材 {i}',topic=f'话题{i}',source='browse')
 r=E(at(29,'13:01'),action='seeds');check('topic 类最多 16 条',len([x for x in r['活跃'] if x['来源']=='闲逛'])<=16,len(r['活跃']))
 h=E(at(29,'13:02'),action='add_seed',text='手动置顶素材',source='hand')
 r=E(at(29,'13:03'),action='seeds');check('手动素材受保护保留',any(x['id']==h['id'] for x in r['活跃']),r)
 # 暂停、skip、账本、跨午夜窗口、reset
 E(at(29,'13:04'),action='configure',paused=True)
 r=E(at(29,'13:05'),action='beat');check('暂停后 SILENT 且不闲逛',r['闸门']['reason']=='心跳已暂停' and not r['闲逛']['due'],r)
 E(at(29,'13:06'),action='configure',paused=False,quiet_hours='22:00-02:00')
 r=E(at(29,'23:30'),action='beat');r2=E(at(30,'01:59'),action='beat');r3=E(at(30,'02:00'),action='beat')
 check('跨午夜静默时段左闭右开',r['闸门']['verdict']=='SILENT' and r2['闸门']['verdict']=='SILENT' and '静默' not in r3['闸门'].get('reason',''),[r['闸门'],r2['闸门'],r3['闸门']])
 r=E(at(30,'10:30'),action='skip',reason='素材都不新鲜');check('skip 记录原因',r['ok'] and 'HEARTBEAT_OK' in r['message'],r)
 r=E(at(30,'10:31'),action='ledger',limit=200);events=[x['event'] for x in r['审计']]
 check('审计含各类事件',{'beat','sent','skip','seed_added','browse_done','pick_refused'}<=set(events),sorted(set(events)))
 raw=(Path(os.environ['INTEREST_HEARTBEAT_DATA_DIR'])/'audit.jsonl').read_text(encoding='utf-8')
 check('审计不含素材正文',('浅烘埃塞豆' not in raw) and ('看展' not in raw),'')
 check('数据文件为 UTF-8 中文',('浅烘' in (Path(os.environ['INTEREST_HEARTBEAT_DATA_DIR'])/'seeds.json').read_text(encoding='utf-8')),'')
 r=await call(action='reset',scope='all');check('reset 缺 confirm 被拒',not r['ok'] and '明确同意' in r['message'],r)
 r=await call(action='reset',scope='seeds',confirm=True);r2=await call(action='seeds');check('reset seeds',r['ok'] and r2['活跃']==[],r2)
 r=await call(action='nope');check('未知动作中文报错',not r['ok'],r)
 # 并发调用不丢账
 E(at(30,'10:40'),action='configure',max_daily=100,cooldown_minutes=0)
 base_n=len(E(at(30,'10:41'),action='ledger')['今天已说'])
 await asyncio.gather(*[tool.PluginTool().invoke({'action':'confirm_send','summary':f'并发{i}'}) for i in range(8)])
 r=await call(action='ledger');check('并发 confirm_send 不丢账',len(r['今天已说'])-base_n==8,len(r['今天已说']))
 # 技能与清单
 skill=(pkg/'skills'/'interest-heartbeat'/'SKILL.md').read_text(encoding='utf-8')
 check('技能 frontmatter 与中文流程','name: interest-heartbeat' in skill and '一跳流程' in skill and 'HEARTBEAT_OK' in skill,'')
 man=json.loads((pkg/'manifest.json').read_text(encoding='utf-8'));check('清单中文名称',man['name']=='兴趣心跳主动分享' and man['display_name']['zh']=='兴趣心跳主动分享',man['name'])
 card=tool.PluginTool().card;check('工具卡 id 与中文描述',card.name=='interest_heartbeat' and '闸门' in card.description,card.name)
 bad=[n for n,ok in results if not ok];print(f'\n{len(results)-len(bad)}/{len(results)} passed');sys.exit(1 if bad else 0)
asyncio.run(main())
