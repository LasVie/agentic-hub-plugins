"""Real host SDK integration test; accepts an installed or extracted payload directory.

Run with the WorkSwarm venv Python; no model calls. All fixtures and state are
created in an explicit new evidence directory outside the installed plugin.
"""
import argparse,asyncio,hashlib,importlib.util,json,os,sys
from pathlib import Path
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OTEL_SDK_DISABLED='true',PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True
from openjiuwen.harness.resources.extension_loader import find_plugin_manifest,load_plugin_package
from openjiuwen.harness.resources.extension_resolver import resolve_plugin_parts
from openjiuwen.harness.schema.build_context import BuildContext
args=argparse.ArgumentParser()
args.add_argument('payload',type=Path)
args.add_argument('evidence_dir',type=Path)
a=args.parse_args()
R=Path(__file__).resolve().parents[1]
P=a.payload.resolve();OUT=a.evidence_dir.resolve();OUT.mkdir(parents=True,exist_ok=False)
F=OUT/'synthetic-inputs'
fsp=importlib.util.spec_from_file_location('ebook_fixtures',R/'plugins/offline-ebook-reader/prepare_manual_testing.py')
fixtures=importlib.util.module_from_spec(fsp);fsp.loader.exec_module(fixtures);fixtures.main(F)
W=OUT/'installed-workspace';W.mkdir()
def network_guard(event,args):
 if event=='socket.connect':
  address=args[1]
  if not isinstance(address,tuple) or address[0] not in ('127.0.0.1','::1'):
   raise RuntimeError('Integration test forbids external network connections')
sys.addaudithook(network_guard)
spec=load_plugin_package(find_plugin_manifest(str(P)))
parts=resolve_plugin_parts(spec,BuildContext(language='cn',extras={'source_root':str(P)}))
assert len(parts.tools)==3 and len(parts.skills)==1 and not parts.mcps and not parts.rails
lib,read,reader=parts.tools;records=[]
async def call(tool,expected=True,**kw):
 r=await tool.invoke({'workspace':str(W),**kw});assert r['ok']==expected,r
 assert r['version']=='1.0.0',r
 records.append({'inputs':kw,'result':r});return r
async def main():
 await call(lib,action='list')
 a=await call(lib,action='import',path=str(F/'中文三章示例.txt'),confirmed=True);bid=a['book']['book_id'];assert a['book']['chapter_count']==3
 await call(lib,action='toc',book_id=bid)
 d=await call(read,book_id=bid,chapter_index=1,max_chars=40);assert d['truncated'] and d['next_char']==40
 d2=await call(read,book_id=bid,chapter_index=1,start_char=d['next_char'],max_chars=40);assert d2['start_char']==40
 a=await call(lib,action='progress',book_id=bid,chapter_index=1,offset_ratio=.35,expected_revision=a['revision'],confirmed=True)
 b=await call(lib,action='import',path=str(F/'中文三章示例.txt'),confirmed=True);assert b['reused'] and b['book']['progress']['offset_ratio']==.35
 c=await call(lib,False,action='progress',book_id=bid,chapter_index=0,offset_ratio=0,expected_revision=0,confirmed=True);assert c['error']['code']=='revision_conflict'
 await call(lib,action='preferences',expected_revision=a['revision'],preferences={'font_size':24,'line_height':2,'width':800,'theme':'dark'},confirmed=True)
 e=await call(lib,action='import',path=str(F/'中文顺序示例.epub'),confirmed=True)
 toc=await call(lib,action='toc',book_id=e['book']['book_id']);assert toc['chapters'][0]['title']=='第一章 出发'
 await call(lib,False,action='import',path=str(F/'固定版式拒绝.epub'),confirmed=True)
 await call(lib,False,action='import',path=str(F/'损坏示例.epub'),confirmed=True)
 await call(lib,False,action='import',path=str(F/'旧编码示例.txt'),confirmed=True)
 await call(lib,action='import',path=str(F/'旧编码示例.txt'),encoding='gb18030',confirmed=True)
 r=await call(reader,action='start',confirmed=True);s=await call(reader,action='status');assert s['session_id']==r['session_id']
 await call(reader,action='stop',confirmed=True)
 result={'passed':True,'invocations':len(records),'registered_tools':3,'registered_skills':1,'installed_package':str(P),'model_requests':0,'records':records}
 (OUT/'installed-tools.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
asyncio.run(main())
