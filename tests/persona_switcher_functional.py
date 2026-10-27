"""会话人设切换功能测试：经原生 Tool.invoke 调用，使用中文输入。

用法：python -B tests/persona_switcher_functional.py [插件内层目录]
默认测试 plugins/persona-switcher/persona-switcher；可传解压后的 ZIP 内层目录。
"""
import asyncio,importlib,json,os,shutil,stat,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
pkg=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'plugins'/'persona-switcher'/'persona-switcher'
import importlib.util as u
spec=u.spec_from_file_location('persona_switcher',pkg/'__init__.py',submodule_search_locations=[str(pkg)]);m=u.module_from_spec(spec);sys.modules['persona_switcher']=m;spec.loader.exec_module(m)
tool=importlib.import_module('persona_switcher.tools.plugin_tool')
results=[]
def check(name,cond,detail=''):
 results.append((name,bool(cond)));print(('PASS' if cond else 'FAIL')+': '+name+('' if cond else ' — '+str(detail)))
async def main():
 ws=tempfile.mkdtemp(prefix='人设测试-')
 call=lambda **q:tool.PluginTool().invoke({'workspace_dir':ws,**q})
 r=await call(action='status');check('默认无角色',r['ok'] and r['current_role'] is None and r['persona']=='',r)
 r=await call(action='list');check('空角色库提示',r['ok'] and r['roles']==[] and '为空' in r['message'],r)
 r=await call(action='init');check('init 添加两个中文示例',sorted(r['added'])==['strict-reviewer','tea-master'] and len(r['roles'])==2,r)
 r=await call(action='init');check('init 不覆盖已有',r['added']==[] and '未覆盖' in r['message'],r)
 r=await call(action='use',role_id='tea-master');check('切换到茶馆掌柜',r['ok'] and r['current_role']['name']=='茶馆掌柜' and '客官' in r['persona'],r)
 check('切换提示含中文 notice',r.get('notice','').startswith('<system-reminder>') and '宿主默认人设切换到角色「茶馆掌柜」' in r['notice'],r.get('notice'))
 r=await call(action='status');check('新工具实例保持状态',r['current_role']['id']=='tea-master',r)
 r=await call(action='use',role_id='strict-reviewer');check('角色间切换 notice',r['ok'] and '从角色「茶馆掌柜」（tea-master）切换到角色「严谨评审官」' in r.get('notice',''),r)
 r=await call(action='use',role_id='strict-reviewer');check('重复切换无 notice',r['ok'] and 'notice' not in r and '无变化' in r['message'],r)
 r=await call(action='use',role_id='不存在');check('非法 id 中文报错',not r['ok'] and '小写字母' in r['message'],r)
 r=await call(action='use',role_id='ghost');check('不存在角色中文报错',not r['ok'] and '没有 id 为 ghost' in r['message'],r)
 persona='你是一位说话押韵的古风诗人。\n每句话尽量七字一句。'
 r=await call(action='create',role_id='poet',name='古风诗人',description='句句押韵',persona=persona)
 check('中文新建角色',r['ok'] and '古风诗人' in r['message'],r)
 f=Path(ws,'.persona-switcher','roles','poet','ROLE.md');txt=f.read_text(encoding='utf-8')
 check('ROLE.md UTF-8 与 frontmatter',txt.startswith('---\nid: poet\nname: 古风诗人\n') and persona in txt,txt)
 check('文件权限私有',stat.S_IMODE(f.stat().st_mode)==0o600,oct(f.stat().st_mode))
 r=await call(action='create',role_id='poet',persona='新内容');check('覆盖需 overwrite',not r['ok'] and 'overwrite' in r['message'],r)
 r=await call(action='create',role_id='poet',persona='新内容',overwrite=True);check('覆盖缺 confirm 被拒',not r['ok'] and '确认' in r['message'] and persona in f.read_text(encoding='utf-8'),r)
 r=await call(action='create',role_id='poet',persona='新内容',overwrite=True,confirm=True);check('overwrite+confirm 覆盖',r['ok'] and '新内容' in f.read_text(encoding='utf-8'),r)
 Path(ws,'.persona-switcher','roles','flat.md').write_text('---\nid: flat\nname: 扁平角色\ntools: [bash]\nmodel: x\n---\n扁平正文',encoding='utf-8')
 Path(ws,'.persona-switcher','roles','empty.md').write_text('---\nid: empty\n---\n',encoding='utf-8')
 r=await call(action='list');ids=[x['id'] for x in r['roles']]
 check('扁平文件可读、能力字段忽略',ids==['flat','poet','strict-reviewer','tea-master'] and set(r['roles'][0])=={'id','name','description'},r['roles'])
 check('空正文跳过并警告',any('没有人设正文' in w for w in r['warnings']),r['warnings'])
 r=await call(action='default',role_id='tea-master');check('设默认角色',r['ok'] and r['default_role']=='tea-master',r)
 r=await call(action='none');check('none 回到默认人设',r['ok'] and r['current_role'] is None and '回到宿主默认人设' in r.get('notice',''),r)
 check('退出提示无多余空格',' 回到' not in r['notice'] and '） 的' not in r['notice'],r['notice'])
 r=await call(action='status');check('none 后默认角色不自动装回',r['current_role'] is None and r['cleared_by_user'] and r['default_role']=='tea-master',r)
 r=await call(action='use',role_id='poet');r=await call(action='delete',role_id='poet')
 check('删除缺 confirm 被拒',not r['ok'] and 'confirm=true' in r['message'] and f.exists(),r)
 r=await call(action='delete',role_id='poet',confirm=True)
 check('删除当前角色并回落到默认',r['ok'] and not f.parent.exists() and r['current_role']['id']=='tea-master' and 'notice' in r,r)
 r=await call(action='delete',role_id='tea-master',confirm=True);check('删除默认角色清除 default',r['ok'] and r['default_role'] is None and r['current_role'] is None,r)
 Path(ws,'.persona-switcher','state.json').write_text('{坏',encoding='utf-8')
 r=await call(action='status');check('损坏状态改名保留',r['ok'] and Path(ws,'.persona-switcher','state.json.corrupt').exists(),r)
 r=await tool.PluginTool().invoke({'workspace_dir':'相对路径','action':'status'});check('相对路径拒绝',not r['ok'] and '绝对路径' in r['message'],r)
 eng=sys.modules['persona_switcher.runtime.engine']
 if os.name!='nt':check('Windows 盘符路径映射',str(eng.Path('/mnt/d/Job/x'))==str(eng.Path('/mnt/d/Job/x')) and eng.WIN_RE.match('D:\\Job\\x') and (lambda m:'/mnt/'+m.group(1).lower()+'/'+m.group(2).replace('\\','/'))(eng.WIN_RE.match('D:\\Job\\x'))=='/mnt/d/Job/x')
 if os.name!='nt' and Path('/mnt/c/Users/Public').is_dir():
  r=await tool.PluginTool().invoke({'workspace_dir':'C:\\Users\\Public','action':'status'});check('Windows 路径实际解析到 /mnt/c',r['ok'] and r['workspace']=='/mnt/c/Users/Public',r)
  shutil.rmtree('/mnt/c/Users/Public/.persona-switcher',ignore_errors=True)
 r=await call(action='切换');check('未知操作中文报错',not r['ok'] and '不支持的操作' in r['message'],r)
 os.symlink('/tmp',Path(ws,'.persona-switcher','roles','link'))
 r=await call(action='list');check('符号链接跳过',all(x['id']!='link' for x in r['roles']) and any('符号链接' in w for w in r['warnings']),r)
 json.dumps(r,ensure_ascii=False)
asyncio.run(main())
ok=sum(p for _,p in results);print(f'{ok}/{len(results)} passed');sys.exit(0 if ok==len(results) else 1)
