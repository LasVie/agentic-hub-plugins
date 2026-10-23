"""Real native Tool/ToolCard + Node/SQLite/HTTP/Git outcome tests. No mocked tool results."""
from pathlib import Path
import asyncio, importlib.util, importlib, json, sys, tempfile, subprocess, os, urllib.request, urllib.error, hashlib

PLUGINS=['word-vault-local','story-workbench','process-workbench','environment-inspector','git-branch-atlas']
PAYLOADS=Path(os.environ.get('INTERACTIVE_PAYLOADS',str(Path(__file__).resolve().parents[1]/'plugins')))
NODE='/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node'
RESULTS=[]
def payload(slug):
 p=PAYLOADS/slug
 return p/slug if (p/slug/'manifest.json').exists() else p
def load_tool(slug):
 name='interactive_test_'+slug.replace('-','_')
 p=payload(slug)
 spec=importlib.util.spec_from_file_location(name,p/'__init__.py',submodule_search_locations=[str(p)])
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
 return importlib.import_module(name+'.tools.plugin_tool').PluginTool()
def check(slug,label,condition,detail=None):
 RESULTS.append({'plugin':slug,'test':label,'passed':bool(condition),'detail':detail})
 if not condition:raise AssertionError(f'{slug}: {label}: {detail}')
def req(url,data,token,origin=None,ctype='application/json'):
 headers={'Authorization':'Bearer '+token,'Content-Type':ctype}
 if origin:headers['Origin']=origin
 request=urllib.request.Request(url,data=json.dumps(data).encode(),headers=headers,method='POST')
 try:
  with urllib.request.urlopen(request,timeout=20) as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
def git(root,*args):
 env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
 return subprocess.check_output(['/usr/bin/git','-c','user.name=Plugin Test','-c','user.email=plugin-test@example.invalid',*args],cwd=root,env=env,stderr=subprocess.DEVNULL,text=True).strip()
def setup_git(root):
 repo=root/'repo';repo.mkdir();git(repo,'init','-b','main');(repo/'base.txt').write_text('base\n');git(repo,'add','base.txt');git(repo,'commit','-m','初始提交')
 git(repo,'switch','-c','feature');(repo/'feature.txt').write_text('feature\n');git(repo,'add','feature.txt');git(repo,'commit','-m','功能分支提交');git(repo,'switch','main');(repo/'main.txt').write_text('main\n');git(repo,'add','main.txt');git(repo,'commit','-m','主线提交');git(repo,'merge','--no-ff','feature','-m','合并功能分支')
 return repo

async def exercise(slug,root):
 t=load_tool(slug)
 async def call(action='status',**p):return await t.invoke({'workspace_dir':str(root),'action':action,'payload':p})
 r=await call();check(slug,'fresh native SDK invocation',r.get('ok') and r['revision']==0,r)
 h=await call('help');check(slug,'Chinese native help',h.get('ok') and 'open_ui' in h['actions'])
 bad=await call('not-supported');check(slug,'unknown operation rejected',bad.get('ok') is False)
 if slug=='word-vault-local':
  entries=[{'term':'apple','meaning':'苹果'},{'term':'river','meaning':'河流'},{'term':'mountain','meaning':'山峰'},{'term':'glasses','meaning':'眼镜'},{'term':'buses','meaning':'公交车'}]
  r=await call('add_words',expected_revision=0,entries=entries);check(slug,'five local words saved',r.get('ok') and r['summary']['total']==5,r)
  check(slug,'upstream protected plural stays distinct',any(w['lemma']=='glasses' for w in r['words']))
  check(slug,'upstream conservative morphology used',any(w['lemma']=='bus' for w in r['words']))
  revision=r['revision'];bad=await call('add_words',expected_revision=0,entries=entries);check(slug,'stale write is immutable',not bad['ok'] and (await call())['revision']==revision)
  r=await call('add_words',expected_revision=revision,entries=[entries[0]]);check(slug,'repeat counts without duplicate row',r.get('ok') and r['summary']['total']==5 and next(w for w in r['words'] if w['term']=='apple')['seen_count']==2)
  bad=await call('start_quiz',learner='other',expected_revision=r['revision']);check(slug,'learner isolation',not bad['ok'] and (await call(learner='other'))['summary']['total']==0)
  for round_no in range(3):
   s=await call();r=await call('start_quiz',expected_revision=s['revision'],size=5);check(slug,f'quiz {round_no} generated real options',r.get('ok') and len(r['quiz']['questions'])==5,r)
   check(slug,f'quiz {round_no} hides answer indices',all('answer_index' not in q and 'correct_meaning' not in q for q in r['quiz']['questions']))
   bank={w['term']:w['meaning'] for w in r['words']};qid=r['quiz']['id']
   for q in r['quiz']['questions']:
    r=await call('answer',expected_revision=r['revision'],quiz_id=qid,question_id=q['id'],option_index=q['options'].index(bank[q['term']]))
    check(slug,f'quiz {round_no} scores question {q["id"]}',r.get('ok') and r['is_correct'],r)
  check(slug,'three-consecutive mastery persisted',r['summary']['mastered']==5 and all(w['streak']==3 for w in r['words']))
  bad=await call('answer',expected_revision=r['revision'],quiz_id=qid,question_id=0,option_index=0);check(slug,'duplicate answer does not double score',not bad['ok'] and (await call())['revision']==r['revision'])
  r=await call('start_quiz',expected_revision=r['revision'],size=1);q=r['quiz']['questions'][0];bank={w['term']:w['meaning'] for w in r['words']};wrong=(q['options'].index(bank[q['term']])+1)%4
  r=await call('answer',expected_revision=r['revision'],quiz_id=r['quiz']['id'],question_id=0,option_index=wrong,correct=True)
  check(slug,'client cannot self-award a correct answer',r.get('ok') and not r['is_correct'] and r['summary']['mastered']==4)
  r=await call('start_quiz',expected_revision=r['revision'],wrong_only=True,size=4);check(slug,'wrong-answer review selects wrong word',len(r['quiz']['questions'])==1)
  for label,p in [('boolean revision',{'expected_revision':True}),('unsafe learner',{'expected_revision':r['revision'],'learner':'../x'}),('invalid term',{'expected_revision':r['revision'],'entries':[{'term':'123','meaning':'测试'}]})]:
   args={'expected_revision':r['revision'],'entries':[entries[0]],**p};bad=await call('add_words',**args);check(slug,label+' rejected',not bad['ok'])
  e=await call('export_bank');check(slug,'learner export excludes other banks',e.get('ok') and e['export']['summary']['total']==5)
 elif slug=='story-workbench':
  r=await call('create_project',expected_revision=0,name='城市边界');check(slug,'project created',r.get('ok') and r['project_name']=='城市边界',r)
  bad=await call('create_project',expected_revision=r['revision'],name='覆盖');check(slug,'existing project never overwritten',not bad['ok'])
  r=await call('save_character',expected_revision=r['revision'],id='hero',name='林夏',role='图书修复师',goal='找回失踪的手稿');check(slug,'character saved',r.get('ok') and r['characters'][0]['name']=='林夏')
  prose='清晨，林夏推开旧书店。\n\n街道尽头亮起一盏灯。';r=await call('save_chapter',expected_revision=r['revision'],id='chapter-1',title='第一章',content=prose,chapter_revision='');check(slug,'Chinese chapter saved',r.get('ok') and r['chapters'][0]['content']==prose,r)
  chapter=r['chapters'][0];check(slug,'original marker core measures prose',chapter['writing_units']==len(''.join(prose.split())))
  r=await call('annotate',expected_revision=r['revision'],chapter_id=chapter['id'],chapter_revision=chapter['hash'],quote='旧书店',note='补充空间细节');check(slug,'quote anchored',r.get('ok') and r['annotations'][0]['anchor']['state']=='relocated',r)
  r=await call('save_chapter',expected_revision=r['revision'],id='chapter-1',title='第一章',content='序：🌙\n'+prose,chapter_revision=chapter['hash']);check(slug,'UTF16 quote relocated after prefix',r.get('ok') and r['annotations'][0]['anchor']['state']=='relocated',r)
  check(slug,'prior revision immutable and hashed',r['history'][0]['content']==prose and r['history'][0]['hash']==hashlib.sha256(prose.encode()).hexdigest())
  chapter=r['chapters'][0];r=await call('save_chapter',expected_revision=r['revision'],id='chapter-1',title='第一章',content='旧书店在此。旧书店在彼处。',chapter_revision=chapter['hash']);check(slug,'ambiguous quote detached honestly',r.get('ok') and r['annotations'][0]['anchor']['state']=='detached')
  bad=await call('annotate',expected_revision=r['revision'],chapter_id='chapter-1',chapter_revision=r['chapters'][0]['hash'],quote='旧书店',note='错误绑定');check(slug,'ambiguous new annotation rejected',not bad['ok'])
  bad=await call('save_chapter',expected_revision=r['revision'],id='chapter-1',title='第一章',content='bad',chapter_revision='stale');check(slug,'stale chapter hash rejected',not bad['ok'])
  r=await call('resolve_annotation',expected_revision=r['revision'],annotation_id=r['annotations'][0]['id']);check(slug,'resolve preserves annotation',r.get('ok') and r['annotations'][0]['status']=='resolved')
  bad=await call('save_character',expected_revision=0,id='hero',name='过期');check(slug,'stale character update rejected',not bad['ok'])
  e=await call('export_project');check(slug,'complete project history export',e.get('ok') and len(e['export']['history'])==2)
 elif slug=='process-workbench':
  template={'process':{'name':'delivery','display_name':'交付流程'},'phases':[{'id':'prep','name':'准备','links':[{'id':'draft','name':'草案','prompt':'保存草案','on_success':'next'}]},{'id':'check','name':'检查','links':[{'id':'verify','name':'验收','prompt':'核对结果','on_success':'end'}]}]}
  v=await call('validate_template',template=template);check(slug,'real template metadata validation',v.get('ok') and v['valid'] and v['meta']['linkCount']==2,v)
  malformed=json.loads(json.dumps(template));malformed['phases'][1]['links'][0]['id']='draft';v=await call('validate_template',template=malformed);check(slug,'duplicate step id rejected',not v['valid'])
  malformed=json.loads(json.dumps(template));malformed['phases'][0]['links'][0]['on_success']='missing';v=await call('validate_template',template=malformed);check(slug,'dangling transition rejected',not v['valid'])
  r=await call('save_template',expected_revision=0,template=template);check(slug,'template saved',r.get('ok'),r)
  r=await call('start_run',expected_revision=r['revision'],run_id='run-1');check(slug,'run freezes template',r.get('ok') and r['runs'][0]['current']=='draft',r)
  changed=json.loads(json.dumps(template));changed['phases'][0]['links'][0]['prompt']='new';r=await call('save_template',expected_revision=r['revision'],template=changed);check(slug,'existing run unaffected by template edits',r['runs'][0]['snapshot']['phases'][0]['links'][0]['prompt']=='保存草案')
  (root/'proof.txt').write_text('已核对交付数据\n');before=r['revision']
  for label,args in [('skipping',{'step_id':'verify','evidence_files':['proof.txt']}),('missing proof',{'step_id':'draft','evidence_files':['missing.txt']}),('traversal',{'step_id':'draft','evidence_files':['../outside.txt']})]:
   bad=await call('complete_step',expected_revision=before,run_id='run-1',note='测试',**args);check(slug,label+' rejected without advancement',not bad['ok'] and (await call())['revision']==before)
  for step in ['draft','verify']:
   r=await call('complete_step',expected_revision=r['revision'],run_id='run-1',step_id=step,note='已完成实际核对',evidence_files=['proof.txt']);check(slug,step+' completion recorded',r.get('ok'),r)
  check(slug,'run completes with real evidence hash',r['runs'][0]['status']=='done' and r['runs'][0]['trail'][0]['evidence'][0]['sha256']==hashlib.sha256((root/'proof.txt').read_bytes()).hexdigest())
  bad=await call('complete_step',expected_revision=r['revision'],run_id='run-1',step_id='verify',note='duplicate',evidence_files=['proof.txt']);check(slug,'finished run cannot double-complete',not bad['ok'])
  template['phases'][0]['links'][0]['on_success']='break';r=await call('save_template',expected_revision=r['revision'],template=template);r=await call('start_run',expected_revision=r['revision'],run_id='run-2');r=await call('complete_step',expected_revision=r['revision'],run_id='run-2',step_id='draft',note='已核对',evidence_files=['proof.txt']);check(slug,'break pauses instead of pretending done',r['runs'][-1]['status']=='paused')
  r=await call('resume_run',expected_revision=r['revision'],run_id='run-2');check(slug,'explicit resume works',r['runs'][-1]['status']=='running')
  check(slug,'full run export',(await call('export_process'))['export']['runs'][0]['status']=='done')
 elif slug=='environment-inspector':
  r=await call('probe',expected_revision=0);check(slug,'real local environment probe',r.get('ok') and r['snapshot']['platform']==sys.platform.replace('darwin','darwin'),r)
  check(slug,'actual Node version observed',any(t['name']=='Node.js' and t['status']=='available' and t['version'].startswith('v22.') for t in r['snapshot']['tools']))
  check(slug,'port failure not represented as no service',r['snapshot']['port_status']=='observed' or ('未能观测' in r['snapshot']['port_note'] and r['snapshot']['port_status']=='unavailable'))
  flat=json.dumps(r);check(slug,'identity and key fields absent',not any('"'+k+'"' in flat for k in ['hostname','home','user','env','networkInterfaces','api_key','token']))
  bad=await call('probe',expected_revision=0);check(slug,'stale probe cannot overwrite snapshot',not bad['ok'] and (await call())['revision']==r['revision'])
  r=await call('probe',expected_revision=r['revision']);check(slug,'second observation retained',len(r['snapshots'])==2)
  c=await call('compare',before_id='snap-1',after_id='snap-2');check(slug,'actual snapshots compared',c.get('ok') and 'ports_available' in c['comparison'])
  c=await call('compare',before_id='missing',after_id='snap-2');check(slug,'unknown snapshot rejected',not c['ok'])
  c=await call('compare',before_id='snap-1',after_id='snap-1');check(slug,'same snapshot comparison rejected',not c['ok'])
  e=await call('export_snapshots');check(slug,'snapshot export preserves two observations',len(e['export']['state']['snapshots'])==2)
  script="import {parseListeningPorts} from '"+(payload(slug)/'vendor/ports.mjs').as_uri()+"';console.log(JSON.stringify(parseListeningPorts(process.argv[1])));"
  fixture='COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\nnode 123 user 8u IPv4 0x0 0t0 TCP 127.0.0.1:3000 (LISTEN)\nnode 456 user 9u IPv6 0x0 0t0 TCP *:4000 (LISTEN)\n';parsed=json.loads(subprocess.check_output([NODE,'--input-type=module','-e',script,fixture],text=True));check(slug,'upstream lsof parser real fixture',[x['port'] for x in parsed]==[3000,4000] and parsed[1]['isWildcard'])
 elif slug=='git-branch-atlas':
  repo=setup_git(root);head_before=git(repo,'rev-parse','HEAD');index_before=(repo/'.git/index').read_bytes();files_before={p.name:p.read_bytes() for p in repo.glob('*.txt')}
  r=await call('scan',expected_revision=0,repo_dir='repo',limit=80);check(slug,'real branched/merged repository scan',r.get('ok') and len(r['snapshot']['commits'])==4,r)
  check(slug,'merge parents and lane core preserved',sum(len(c['parents'])==2 for c in r['snapshot']['commits'])==1 and any(l['merge'] for l in r['snapshot']['lanes']))
  check(slug,'two branch refs parsed',len(r['snapshot']['branches'])==2,r['snapshot']['branches'])
  c=await call('compare_branches',repo_dir='repo',base='feature',head='main');check(slug,'ahead/behind real divergence',c.get('ok') and c['base_only']==0 and c['head_only']==2 and c['related'],c)
  r=await call('scan',expected_revision=r['revision'],repo_dir='repo',limit=2);check(slug,'bounded graph retains truncation signal',len(r['snapshot']['commits'])==2 and r['snapshot']['has_more'])
  for label,args in [('traversal',{'repo_dir':'../'}),('option ref',{'repo_dir':'repo','base':'--all','head':'HEAD'}),('unresolvable ref',{'repo_dir':'repo','base':'missing','head':'HEAD'})]:
   c=await call('scan' if label=='traversal' else 'compare_branches',**args);check(slug,label+' rejected',not c['ok'])
  check(slug,'repository tracked state and index immutable',git(repo,'rev-parse','HEAD')==head_before and (repo/'.git/index').read_bytes()==index_before and all((repo/f).read_bytes()==data for f,data in files_before.items()))
  e=await call('export_graph');check(slug,'graph export retains authoritative parent OIDs',len(e['export']['state']['snapshot']['commits'][0]['parents'])==2)
  empty=root/'empty';empty.mkdir();git(empty,'init','-b','main');r=await call('scan',expected_revision=r['revision'],repo_dir='empty');check(slug,'unborn repository reported honestly',r.get('ok') and r['snapshot']['head_oid'] is None and not r['snapshot']['commits'],r)

 # Exercise the actual packaged server, native CLI and SQLite continuity.
 before=await call();r=await call('open_ui');check(slug,'real loopback UI starts',r.get('ok') and r.get('ui_url','').startswith('http://127.0.0.1:'),{k:v for k,v in r.items() if k!='ui_url'})
 url,key=r['ui_url'].split('#');api=url+'api'
 try:
  with urllib.request.urlopen(url,timeout=10) as page:html=page.read().decode()
  check(slug,'Chinese UI shell and restrictive CSP', 'lang="zh-CN"' in html and 'unsafe-inline' not in page.headers.get('Content-Security-Policy',''))
  code,out=req(api,{'action':'status','payload':{}},key);check(slug,'UI uses same authoritative SQLite revision',code==200 and out['ok'] and out['revision']==before['revision'])
  code,out=req(api,{'action':'status','payload':{}},'bad');check(slug,'missing UI token denied',code==403)
  code,out=req(api,{'action':'status','payload':{}},key,'https://example.invalid');check(slug,'cross-origin mutation denied',code==403)
  code,out=req(api,{'workspace_dir':'/tmp','action':'status'},key);check(slug,'UI cannot switch workspace',not out['ok'])
  code,out=req(api,{'action':'status','payload':{}},key,ctype='text/plain');check(slug,'non-JSON CSRF request denied',code==403)
  try:urllib.request.urlopen(url+'../../etc/passwd',timeout=5);safe=False
  except urllib.error.HTTPError as e:safe=e.code==404
  check(slug,'not an arbitrary file server',safe)
  duplicate=await call('open_ui');check(slug,'reopening reuses current healthy version',duplicate.get('ui_url')==r['ui_url'])
 finally:
  end=await call('stop_ui');check(slug,'UI shutdown preserves state',end.get('ok') and (await call())['revision']==before['revision'])
 check(slug,'private SQLite permissions',(root/'.agentic-hub-plugins'/slug/'state.sqlite').stat().st_mode&0o777==0o600)
 check(slug,'native data persists across new Tool objects',(await load_tool(slug).invoke({'workspace_dir':str(root),'action':'status'}))['revision']==before['revision'])

async def main():
 try:
  with tempfile.TemporaryDirectory(prefix='interactive-five-') as d:
   for slug in PLUGINS:
    root=Path(d)/slug;root.mkdir();await exercise(slug,root)
    print(slug, sum(r['passed'] for r in RESULTS if r['plugin']==slug),'checks passed',flush=True)
 finally:
  target=os.environ.get('INTERACTIVE_TEST_RESULTS')
  if target:Path(target).write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
 print(json.dumps({'passed':all(r['passed'] for r in RESULTS),'checks':len(RESULTS)}))
if __name__=='__main__':asyncio.run(main())
