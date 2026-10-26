"""Read-only independent byte/tree comparison of the synthetic manual fixture."""
from pathlib import Path
import hashlib
import json
import sys

base=Path(__file__).resolve().parents[2]/'dist/offline-backup-recovery/1.0.0/manual-test'
source,target=base/'示例源目录',base/'人工测试恢复'
def inventory(root):
    if not root.is_dir() or root.is_symlink():raise ValueError('目录不存在或是链接')
    result={}
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('发现链接')
        result[p.relative_to(root).as_posix()]={'type':'directory'} if p.is_dir() else {'type':'file','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    return result
try:
    a,b=inventory(source),inventory(target)
    expected=json.loads((base/'expected-source.json').read_text())
    unchanged=all(a.get(k,{}).get('sha256')==v['sha256'] for k,v in expected.items()) and sum(v['type']=='file' for v in a.values())==len(expected)
    passed=a==b and unchanged
    result={'passed':passed,'source_unchanged':unchanged,'file_bytes_and_tree_match':a==b,'entries':len(a),'files':sum(v['type']=='file' for v in a.values()),'message':'源文件未变且恢复目录逐字节摘要与结构一致。' if passed else '对比不通过，请检查差异，不要确认人工测试通过。'}
except (OSError,ValueError) as e:
    result={'passed':False,'message':'无法完成对比，请先完成实际恢复并检查路径。','error_type':type(e).__name__}
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['passed'] else 2)
