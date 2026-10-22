"""用户在本地运行的口令配置；不接受命令行口令，不经过聊天。"""
import getpass, os, sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('用法：python setup_vault.py /已有工作目录')
root=Path(sys.argv[1]).expanduser()
if not root.is_absolute() or not root.is_dir():raise SystemExit('请提供已存在的绝对工作目录。')
path=root.resolve()/'vault-master-password.txt'
if path.exists() or path.is_symlink():raise SystemExit('口令文件已存在，拒绝覆盖。')
password=getpass.getpass('在本地输入主口令（至少12字符，不会显示）：')
if len(password)<12:raise SystemExit('主口令长度不足。')
if getpass.getpass('再次输入确认：')!=password:raise SystemExit('两次输入不一致。')
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(password+'\n')
print('主口令仅写入本地受限文件。可让 dsh_vault 执行 init；请勿上传该文件。')
