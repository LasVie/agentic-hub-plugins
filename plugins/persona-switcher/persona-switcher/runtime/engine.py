"""会话人设切换：角色库读写、当前角色状态与切换提示。

改编自 dsh-persona-switcher@5638544（MIT，Copyright (c) 2026 yupaoa）lib/index.js 中的
validateRoleId / rolePaths / serializeRole / splitFrontmatter / scalar / parseRole / scanRoles /
formatNotice。修改：由 JavaScript 改写为 Python；状态由每会话改为每工作目录；提示文本改为中文；
新增 init 示例角色与大小、符号链接边界。完整许可见 licenses/dsh-persona-switcher/LICENSE。
"""
from pathlib import Path
from datetime import datetime,timezone
import json,os,re,shutil,tempfile
class InputError(ValueError):pass
NO_ROLE='__none__'
ID_RE=re.compile(r'^[a-z0-9][a-z0-9-]*$')
MAX_ROLE=32*1024
# 在 WSL/Linux 上运行时把 Windows 盘符路径（D:\x）映射为 /mnt/d/x。
WIN_RE=re.compile(r'^([A-Za-z]):[\\/]*(.*)$')
CONFIRM='删除或覆盖角色不可恢复；请先向用户确认，用户明确同意后再以 confirm=true 重新调用。'
SAMPLES=Path(__file__).resolve().parents[1]/'skills'/'persona-switcher'/'references'/'sample-roles'
def workspace(q):
 raw=str(q.get('workspace_dir') or '').strip()
 m=WIN_RE.match(raw)
 if m and os.name!='nt':raw='/mnt/'+m.group(1).lower()+'/'+m.group(2).replace('\\','/')
 p=Path(raw).expanduser()
 if not p.is_absolute() or not p.is_dir():raise InputError('请提供已存在工作目录的绝对路径。')
 return p.resolve()
def base(root):
 b=root/'.persona-switcher'
 for c in (b,b/'roles'):
  if c.is_symlink():raise InputError('角色库路径不能是符号链接。')
 (b/'roles').mkdir(parents=True,exist_ok=True,mode=0o700)
 return b
def validate_id(v):
 if not isinstance(v,str) or not v.strip():raise InputError('角色 id 不能为空。')
 v=v.strip()
 if not ID_RE.match(v):raise InputError('角色 id 只能包含小写字母、数字和连字符，并以字母或数字开头。')
 if len(v)>64:raise InputError('角色 id 最多 64 个字符。')
 return v
def atomic(p,text):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 fd,t=tempfile.mkstemp(prefix='pending-',dir=p.parent)
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(text);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def split_front(text):
 t=text.lstrip('﻿')
 if not t.startswith('---'):return '',t
 end=t.find('\n---',3)
 if end<0:return '',t
 after=t.find('\n',end+1)
 return t[3:end],('' if after<0 else t[after+1:])
def scalar(front,key):
 m=re.search(r'^'+key+r'\s*:\s*(.*)$',front,re.M)
 if not m:return None
 v=m.group(1).strip()
 if len(v)>=2 and v[0]==v[-1] and v[0] in '"\'':v=v[1:-1]
 return v
def parse_role(text,fallback):
 # 只读取身份字段；tools / denyTools / skillsDir / model 等字段一律忽略，切换人设不改变能力。
 front,body=split_front(text);persona=body.strip()
 if not persona:return None
 rid=(scalar(front,'id') or fallback).strip()
 if not rid:return None
 return {'id':rid,'name':(scalar(front,'name') or rid).strip(),'description':(scalar(front,'description') or '').strip(),'persona':persona}
def serialize(r):
 return '\n'.join(['---','id: '+r['id'],'name: '+r['name'],'description: '+r['description'],'---','',r['persona'],''])
def scan(d):
 roles,warn,seen=[],[],set()
 for e in sorted(d.iterdir(),key=lambda x:x.name):
  if e.is_symlink():warn.append(f'已跳过符号链接 {e.name}');continue
  if e.is_dir():f,fb=e/'ROLE.md',e.name
  elif e.is_file() and e.name.lower().endswith('.md'):f,fb=e,e.name[:-3]
  else:continue
  if not f.is_file() or f.is_symlink():continue
  if f.stat().st_size>MAX_ROLE:warn.append(f'角色文件 {f.name} 超过 32 KiB，已跳过');continue
  try:r=parse_role(f.read_text(encoding='utf-8'),fb)
  except (OSError,UnicodeError):warn.append(f'角色文件 {f} 无法以 UTF-8 读取，已跳过');continue
  if r is None:warn.append(f'角色文件 {f} 没有人设正文，已跳过');continue
  if r['id'] in seen:warn.append(f'重复的角色 id "{r["id"]}" 已跳过');continue
  seen.add(r['id']);roles.append(r)
 return roles,warn
def notice(frm,to,names):
 n=lambda i:f'「{names.get(i,i)}」（{i}）'
 if frm==to:return ''
 close='你的下一条回复就属于这里指明的人设，而不是被替换的那个。'
 if to is None:lines=[f'人设变更：本工作目录已从角色{n(frm)}回到宿主默认人设，不再绑定任何角色。',f'角色{n(frm)}的人设、语气和口头习惯已失效。','不要继续模仿本对话中之前的回复：它们是以该角色写的，不是风格指南。']
 elif frm is None:lines=[f'人设变更：本工作目录已从宿主默认人设切换到角色{n(to)}。','此前的人设与说话风格已失效。','无论本对话更早的系统文本如何描述你的身份，都按当前角色说话。']
 else:lines=[f'人设变更：本工作目录已从角色{n(frm)}切换到角色{n(to)}。','上一个角色的人设与说话风格已失效。','无论本对话更早的系统文本如何描述你的身份，都按当前角色说话。']
 return '\n'.join(['<system-reminder>',*lines,close,'</system-reminder>'])
def load_state(p):
 if not p.exists():return {'current':None,'default':None,'revision':0}
 try:s=json.loads(p.read_text(encoding='utf-8'))
 except (ValueError,UnicodeError):
  p.replace(p.with_name('state.json.corrupt'));return {'current':None,'default':None,'revision':0,'recovered':True}
 if not isinstance(s,dict):raise InputError('状态文件格式不正确；请检查 .persona-switcher/state.json。')
 return {'current':s.get('current'),'default':s.get('default'),'revision':int(s.get('revision') or 0)}
def effective(s,ids):
 # current 为 NO_ROLE 表示用户明确选择 none，此时即使配置了默认角色也不重新装回。
 c=s.get('current')
 if c==NO_ROLE:return None
 if c in ids:return c
 return s.get('default') if s.get('default') in ids else None
def execute(q):
 root=workspace(q);b=base(root);rd=b/'roles';sp=b/'state.json'
 action=q.get('action')
 if action not in ('status','list','use','none','default','create','delete','init'):raise InputError('不支持的操作；可用 status、list、use、none、default、create、delete、init。')
 if action=='init':
  added=[]
  for f in sorted(SAMPLES.glob('*.md')):
   d=rd/f.stem
   if not (d/'ROLE.md').exists() and not (rd/f.name).exists():d.mkdir(mode=0o700,exist_ok=True);atomic(d/'ROLE.md',f.read_text(encoding='utf-8'));added.append(f.stem)
  q={**q,'action':'list'};out=execute(q);out['message']=('已添加示例角色：'+'、'.join(added)) if added else '示例角色均已存在，未覆盖。';out['added']=added;return out
 roles,warn=scan(rd);by={r['id']:r for r in roles};names={i:r['name'] for i,r in by.items()}
 s=load_state(sp);before=effective(s,by);msg='';changed=False
 if action=='use':
  rid=validate_id(q.get('role_id'))
  if rid not in by:raise InputError(f'角色库中没有 id 为 {rid} 的角色；先用 list 查看。')
  s['current']=rid;changed=True
 elif action=='none':s['current']=NO_ROLE;changed=True
 elif action=='default':
  v=q.get('role_id')
  if v in (None,'','none'):s['default']=None;msg='已清除新工作目录会话的默认角色。'
  else:
   rid=validate_id(v)
   if rid not in by:raise InputError(f'角色库中没有 id 为 {rid} 的角色。')
   s['default']=rid;msg=f'默认角色已设为「{names[rid]}」。'
  changed=True
 elif action=='create':
  rid=validate_id(q.get('role_id'));persona=str(q.get('persona') or '').strip()
  if not persona:raise InputError('请提供人设正文 persona。')
  name=re.sub(r'[\r\n]+',' ',str(q.get('name') or rid)).strip() or rid;desc=re.sub(r'[\r\n]+',' ',str(q.get('description') or '')).strip()
  text=serialize({'id':rid,'name':name,'description':desc,'persona':persona})
  if len(text.encode())>MAX_ROLE:raise InputError('角色文件超过 32 KiB 上限。')
  if rid in by and not q.get('overwrite'):raise InputError(f'角色 {rid} 已存在；如需覆盖请明确 overwrite=true。')
  if rid in by and q.get('confirm') is not True:raise InputError(CONFIRM)
  d=rd/rid
  if d.is_symlink():raise InputError('角色目录不能是符号链接。')
  d.mkdir(mode=0o700,exist_ok=True);atomic(d/'ROLE.md',text)
  flat=rd/(rid+'.md')
  if flat.is_file() and not flat.is_symlink():flat.unlink()
  msg=f'已保存角色「{name}」（{rid}）。'
 elif action=='delete':
  rid=validate_id(q.get('role_id'))
  if rid not in by:raise InputError(f'角色库中没有 id 为 {rid} 的角色。')
  if q.get('confirm') is not True:raise InputError(CONFIRM)
  d,flat=rd/rid,rd/(rid+'.md')
  if (d/'ROLE.md').is_file():(d/'ROLE.md').unlink()
  if d.is_dir() and not d.is_symlink():shutil.rmtree(d)
  if flat.is_file() and not flat.is_symlink():flat.unlink()
  if s.get('default')==rid:s['default']=None
  if s.get('current')==rid:s['current']=None
  changed=True;msg=f'已删除角色「{names[rid]}」（{rid}），不可恢复。'
 if action in ('create','delete'):roles,w2=scan(rd);warn=w2;by={r['id']:r for r in roles};names.update({i:r['name'] for i,r in by.items()})
 if changed:
  s['revision']=s.get('revision',0)+1;s['updated_at']=datetime.now(timezone.utc).isoformat()
  atomic(sp,json.dumps({k:s.get(k) for k in ('current','default','revision','updated_at')},ensure_ascii=False,indent=2)+'\n')
 now=effective(s,by);cur=by.get(now)
 out={'ok':True,'action':action,'workspace':str(root),'roles_dir':str(rd),
  'current_role':None if cur is None else {k:cur[k] for k in ('id','name','description')},
  'persona':'' if cur is None else cur['persona'],
  'default_role':s.get('default'),'cleared_by_user':s.get('current')==NO_ROLE,'revision':s.get('revision',0),'warnings':warn}
 if action in ('list','init'):out['roles']=[{k:r[k] for k in ('id','name','description')} for r in roles]
 nt=notice(before,now,names) if action in ('use','none','delete') else ''
 if nt:out['notice']=nt
 if not msg:
  if action=='use':msg=f'已切换到角色「{cur["name"]}」（{now}）。' if before!=now else f'当前已是角色「{cur["name"]}」，无变化。'
  elif action=='none':msg='已回到宿主默认人设。本工作目录在你再次 use 之前不会使用任何角色，默认角色也不会自动装回（新会话同样如此）。' if before is not None else '当前已是宿主默认人设。'
  elif action=='list':msg=f'角色库共有 {len(roles)} 个角色。' if roles else '角色库为空；可用 init 添加示例角色，或用 create 新建。'
  else:msg=f'当前角色：「{cur["name"]}」（{now}）。' if cur else '当前使用宿主默认人设（未绑定角色）。'
 out['message']=msg
 return out
