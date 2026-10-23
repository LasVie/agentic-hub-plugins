"""Outcome tests against the actual Tool SDK. No host sessions or UI mocked."""
import asyncio,importlib.util,sys,json,hashlib,subprocess,os,tempfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('PORT_TEST_OUTPUT',tempfile.mkdtemp(prefix='five-ports-tests-')))
(BASE/'test-workspaces').mkdir(parents=True,exist_ok=True)
ROOT=Path(os.environ.get('PORT_PAYLOAD_ROOT',str(REPO/'plugins')))
RUN=os.environ.get('PORT_TEST_RUN','self')
RESULTS=[]
def payload(slug):return ROOT/slug/slug if (ROOT/slug/slug/'manifest.json').exists() else ROOT/slug
def tool(slug):
 name=slug.replace('-','_')+'_testpkg'
 s=importlib.util.spec_from_file_location(name,payload(slug)/'__init__.py',submodule_search_locations=[str(payload(slug))])
 m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m)
 return importlib.import_module(name+'.tools.plugin_tool').PluginTool()
def record(slug,label,ok,detail=''):
 RESULTS.append({'plugin':slug,'test':label,'passed':bool(ok),'detail':detail})
 if not ok:print('FAIL',slug,label,detail)
async def main():
 for slug in ['qt-dev-review','archify-graph-tools','motor-l0-screening','action-first-mode','gomoku-local']:
  t=tool(slug);root=BASE/'test-workspaces'/(RUN+'-'+slug);root.mkdir(exist_ok=True)
  async def call(**q):return await t.invoke({'workspace_dir':str(root),**q})
  if slug=='qt-dev-review':
   (root/'bad.cpp').write_text('#include <QScopedPointer>\nvoid f() { QScopedPointer<int> p(new int(3)); }\n')
   (root/'good.qml').write_text('import QtQuick\nItem {\n id: root\n}\n')
   (root/'bad.qml').write_text('import QtQuick\nItem {\n property var x: 42\n width: parent.width\n anchors.fill: parent\n}\n')
   r=await call(action='review',files=['bad.cpp','bad.qml']);record(slug,'C++ and QML findings located',r.get('ok') and r['count']>=2,json.dumps(r,ensure_ascii=False)[:400])
   record(slug,'code not modified','QScopedPointer' in (root/'bad.cpp').read_text())
   r=await call(action='review',files=['good.qml']);record(slug,'clean file accepts',r.get('ok') and r['count']==0,str(r)[:200])
   for label,files in [('traversal',['../outside.cpp']),('missing',['absent.cpp']),('empty',[])]:
    r=await call(action='review',files=files);record(slug,label+' rejected',r.get('ok') is False)
  elif slug=='archify-graph-tools':
   f=root/'sample.json'
   if f.exists():f.unlink()
   r=await call(action='example',source_file='sample.json');record(slug,'Chinese example created',r.get('ok'),str(r))
   r=await call(action='validate',source_file='sample.json');record(slug,'valid source accepted',r.get('ok'),str(r))
   r=await call(action='deliver',source_file='sample.json',output_file='sample.html');record(slug,'real renderer delivered',r.get('ok'),str(r))
   if (root/'sample.html').exists():
    h=(root/'sample.html').read_text();record(slug,'Chinese content and interactive controls','插件交付流程' in h and 'zh-CN' in h and '<script' in h)
   d=json.loads(f.read_text());d['edges'][0]['to']='missing';(root/'bad.json').write_text(json.dumps(d))
   before=(root/'sample.html').read_bytes() if (root/'sample.html').exists() else b''
   r=await call(action='deliver',source_file='bad.json',output_file='sample.html');record(slug,'broken node reference rejected',r.get('ok') is False,str(r))
   record(slug,'failed delivery preserves prior output',(root/'sample.html').exists() and (root/'sample.html').read_bytes()==before)
   d=json.loads(f.read_text());d['nodes'][0]['brand']={'url':'https://example.com/a.svg','sha256':'a'*64};(root/'remote.json').write_text(json.dumps(d))
   r=await call(action='deliver',source_file='remote.json');record(slug,'remote resource rejected before renderer',r.get('ok') is False and '离线' in r.get('message',''))
   r=await call(action='validate',source_file='../outside.json');record(slug,'unsafe path rejected',r.get('ok') is False)
  elif slug=='motor-l0-screening':
   r=await call(action='screen',power_kw=7.5,speed_rpm=1450,count=30)
   record(slug,'matrix and validation produced',r.get('ok') and r.get('summary',{}).get('total',0)>0,str(r)[:800])
   if r.get('ok'):
    original=json.loads((root/'motor-screening.json').read_text());record(slug,'full matrix saved',len(original['matrix'])==original['summary']['total'])
    record(slug,'ranking excludes failed and infeasible',all(x['report']['status']!='failed' and x['estimate']['feasible'] for x in original['ranked']))
    record(slug,'finite efficiency sorted descending',all(original['ranked'][i]['estimate']['efficiency']>=original['ranked'][i+1]['estimate']['efficiency'] for i in range(len(original['ranked'])-1)))
    r2=await call(action='screen',power_kw=7.5,speed_rpm=1450,count=30);record(slug,'deterministic matrix',original['matrix']==json.loads((root/'motor-screening.json').read_text())['matrix'])
   for k,v in [('power_kw',-1),('speed_rpm',0),('count',121),('power_kw',True),('motor_type','unsupported')]:
    q=dict(action='screen',power_kw=7.5,speed_rpm=1450);q[k]=v;r=await call(**q);record(slug,k+' invalid '+str(v)+' rejected',r.get('ok') is False,str(r)[:200])
   r=await call(action='screen',power_kw=7.5,speed_rpm=1450,line_freq_hz=60,motor_type='pmsm');record(slug,'explicit PMSM and 60Hz passed through',r.get('ok') and r['spec']['motor_type']=='pmsm' and r['spec']['line_freq_hz']==60,str(r)[:200])
  elif slug=='action-first-mode':
   p=root/'action-first-state.json'
   if p.exists():p.unlink()
   r=await call(action='status');record(slug,'default off',r.get('ok') and not r['enabled'])
   r=await call(action='on');record(slug,'explicit on',r.get('ok') and r['enabled'])
   t=tool(slug);r=await call(action='status');record(slug,'fresh tool instance persists state',r.get('ok') and r['enabled'])
   record(slug,'state file permissions private',oct(p.stat().st_mode&0o777)=='0o600')
   r=await call(action='off');record(slug,'explicit off',r.get('ok') and not r['enabled'])
   r=await call(action='auto');record(slug,'implicit command rejected',r.get('ok') is False)
  elif slug=='gomoku-local':
   async def game(gid,moves):
    for ext in ('json','html'):
     p=root/f'gomoku-{gid}.{ext}'
     if p.exists():p.unlink()
    r=await call(action='new',game_id=gid)
    for rev,(row,col) in enumerate(moves):
     r=await call(action='move',game_id=gid,row=row,col=col,side='black' if rev%2==0 else 'white',expected_revision=rev)
     if not r.get('ok'):return r
    return r
   for label,line in [('horizontal',[(7,c) for c in range(5)]),('vertical',[(r,7) for r in range(5)]),('diagonal',[(r,r) for r in range(5)]),('reverse-diagonal',[(r,14-r) for r in range(5)])]:
    moves=[]
    for i,x in enumerate(line):
     moves.append(x)
     if i<4:moves.append((14,i*2))
    r=await game(label,moves);record(slug,label+' win detected',r.get('ok') and r['status']=='black_won',str(r)[:160])
    before=(root/f'gomoku-{label}.json').read_bytes()
    r=await call(action='move',game_id=label,row=10,col=10,side='white',expected_revision=9)
    record(slug,label+' finished game immutable',not r['ok'] and (root/f'gomoku-{label}.json').read_bytes()==before)
   r=await game('boundary',[(7,7)]);p=root/'gomoku-boundary.json';before=p.read_bytes()
   bad=[dict(row=7,col=7,side='white',expected_revision=1),dict(row=-1,col=0,side='white',expected_revision=1),dict(row=7.5,col=8,side='white',expected_revision=1),dict(row=True,col=8,side='white',expected_revision=1),dict(row=8,col=8,side='black',expected_revision=1),dict(row=8,col=8,side='white',expected_revision=0)]
   for i,q in enumerate(bad):
    r=await call(action='move',game_id='boundary',**q);record(slug,'invalid move '+str(i)+' rejected without mutation',not r['ok'] and p.read_bytes()==before)
   r=await call(action='new',game_id='boundary');record(slug,'existing game preserved',not r['ok'] and p.read_bytes()==before)
   r=await call(action='export',game_id='boundary');record(slug,'Chinese board snapshot exported',r['ok'] and '只读棋盘快照' in Path(r['board_html']).read_text())
   # Overline directly exercises the bundled rule core via its bounded bridge.
   m=importlib.import_module('gomoku_local_testpkg.runtime.common');b=[0]*225
   for c in range(6):b[7*15+c]=1
   rr=m.run_node(payload(slug)/'runtime/engine.mjs',{'board':b,'row':7,'col':2});record(slug,'overline counts as win',rr['win'])
  print(slug, sum(x['passed'] for x in RESULTS if x['plugin']==slug),'/',sum(x['plugin']==slug for x in RESULTS))
 (BASE/('functional-results.json' if RUN=='self' else RUN+'-functional-results.json')).write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
 if any(not x['passed'] for x in RESULTS):raise SystemExit(1)
asyncio.run(main())
