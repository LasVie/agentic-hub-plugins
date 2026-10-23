"""受限本地文件和进程适配，不调用 shell。"""
from pathlib import Path
import os,json,tempfile,subprocess,shutil,contextlib,hashlib
class InputError(ValueError):pass
def workspace(q):
 p=Path(q.get('workspace_dir','')).expanduser()
 if not p.is_absolute() or not p.is_dir():raise InputError('请提供已存在工作目录的绝对路径。')
 return p.resolve()
def safe(root,rel):
 if not isinstance(rel,str) or not rel or len(rel)>400:raise InputError('请提供有效的相对路径。')
 p=Path(rel)
 if p.is_absolute() or '..' in p.parts or p==Path('.'):raise InputError('路径必须在工作目录内。')
 c=root
 for a in p.parts:
  c=c/a
  if c.is_symlink():raise InputError('路径不能经过符号链接。')
 return c
def read(p,limit=1024*1024):
 if not p.is_file() or p.stat().st_size>limit:raise InputError('文件不存在或超过大小限制。')
 return p.read_text(encoding='utf-8')
def atomic(p,text):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 fd,t=tempfile.mkstemp(prefix='pending-',dir=p.parent)
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(text);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def save(p,obj):atomic(p,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
@contextlib.contextmanager
def locked(root,label):
 p=safe(root,'plugin-lock-'+hashlib.sha256(label.encode()).hexdigest()[:20])
 fd=os.open(p,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
 try:
  if os.name=='nt':
   import msvcrt
   os.write(fd,b'0');os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_LOCK,1)
  else:
   import fcntl
   fcntl.flock(fd,fcntl.LOCK_EX)
  yield
 finally:os.close(fd)
def node():
 p=shutil.which('node') or '/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node'
 if not Path(p).is_file():raise InputError('未找到 Node.js 22，请先安装 Node.js。')
 return p
def run_node(script,q):
 p=subprocess.run([node(),str(script)],input=json.dumps(q,ensure_ascii=False),text=True,capture_output=True,timeout=45)
 if p.returncode:raise InputError('本地计算未完成，请检查输入和 Node.js 版本。')
 try:return json.loads(p.stdout)
 except ValueError:raise InputError('本地计算返回了无效的数据。')
