"""本地运行桥；不使用 shell，不把密码放入命令行。"""
from __future__ import annotations
import contextlib, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

class PluginError(ValueError):
    pass

def workspace(raw):
    if not isinstance(raw,str) or not raw.strip():
        raise PluginError('请提供已有工作目录的绝对路径 workspace_dir。')
    root=Path(raw).expanduser()
    if not root.is_absolute() or not root.is_dir():
        raise PluginError('工作目录必须是已存在的绝对路径。')
    return root.resolve()

def safe_path(root, relative):
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise PluginError('相对路径不能越出工作目录。')
    cursor=root
    for part in rel.parts:
        cursor=cursor/part
        if cursor.is_symlink():
            raise PluginError('数据路径不能经过符号链接。')
    return cursor

def read_json(path,limit=1024*1024):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:
        raise PluginError('文件不存在、不是普通文件或超过大小限制。')
    with path.open(encoding='utf-8') as f:return json.load(f)

def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd, tmp=tempfile.mkstemp(prefix='pending-',dir=str(path.parent))
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextlib.contextmanager
def locked(root, label):
    directory=safe_path(root,'.song-plugins-locks')
    directory.mkdir(mode=0o700,exist_ok=True)
    target=safe_path(root,'.song-plugins-locks/'+hashlib.sha256(label.encode()).hexdigest()+'.lock')
    fd=os.open(target,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    try:
        if os.name=='nt':
            import msvcrt
            os.write(fd,b'0');os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally:os.close(fd)

def node_binary():
    configured=os.environ.get('DSH_NODE_BINARY')
    if configured:
        path=Path(configured).expanduser()
        if path.is_file() and os.access(path,os.X_OK):return str(path)
        raise PluginError('DSH_NODE_BINARY 不是可执行的 Node.js 文件。')
    found=shutil.which('node')
    if found:return found
    if sys.platform=='darwin':
        bundled=Path('/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node')
        if bundled.is_file():return str(bundled)
    raise PluginError('未找到 Node.js。请安装 Node.js 22 或以上，或设置 DSH_NODE_BINARY。')

def run_node(request):
    runtime=Path(__file__).with_name('engine.mjs')
    try:
        proc=subprocess.run([node_binary(),str(runtime)],input=json.dumps(request,ensure_ascii=False),text=True,encoding='utf-8',capture_output=True,timeout=60,check=False)
        result=json.loads(proc.stdout)
        if not isinstance(result,dict):raise ValueError()
        return result
    except subprocess.TimeoutExpired:
        raise PluginError('本地计算超时；未报告成功，请检查输入规模。') from None
    except (ValueError,OSError):
        raise PluginError('本地运行引擎未能完成，请检查 Node.js 与输入；详细内部异常未回传对话。') from None

def failure(exc):
    message=str(exc) if isinstance(exc,PluginError) else '输入或文件格式不正确，操作未完成。'
    return {'ok':False,'message':message}
