from .common import *
HERE=Path(__file__).resolve().parents[1]
TYPES={'architecture','workflow','sequence','dataflow','lifecycle','erd','tree','class','timeline','waterfall'}
def check_local(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('brand','repository','image','href','url'):raise InputError('离线版不接受品牌、外部资源或仓库证据路径；请改为普通文字节点。')
   check_local(v)
 elif isinstance(obj,list):
  for v in obj:check_local(v)
 elif isinstance(obj,str) and (re_match_url(obj)):raise InputError('离线版不接受外部 URL 或文件协议资源。')
def re_match_url(s):return any(x in s.lower() for x in ('http:','https:','file:','data:','javascript:'))
def example():
 return {'schema_version':2,'diagram_type':'workflow','meta':{'title':'插件交付流程','subtitle':'从选择到本地验证','locale':'zh-CN','output':'graph.html'},'lanes':[{'id':'team','label':'开发团队'}],'nodes':[{'id':'select','lane':'team','col':0,'type':'frontend','label':'选择候选'},{'id':'build','lane':'team','col':1,'type':'backend','label':'中文适配'},{'id':'test','lane':'team','col':2,'type':'backend','label':'桌面测试'}],'edges':[{'id':'a','from':'select','to':'build'},{'id':'b','from':'build','to':'test'}]}
def execute(q):
 root=workspace(q);action=q.get('action');f=safe(root,q.get('source_file','graph.json'));out=safe(root,q.get('output_file','graph.html'))
 if f.suffix!='.json' or out.suffix!='.html' or f==out:raise InputError('源文件必须是 .json，输出必须是不同的 .html 文件。')
 if action=='example':
  if f.exists():raise InputError('样例路径已存在，请使用新的 source_file 保留原文件。')
  save(f,example());return {'ok':True,'message':'已创建中文工作流 JSON；可继续 validate 和 deliver。','source':str(f)}
 if action not in ('validate','deliver'):raise InputError('请选择 example、validate 或 deliver。')
 diagram=json.loads(read(f));check_local(diagram)
 if not isinstance(diagram,dict) or diagram.get('diagram_type') not in TYPES:raise InputError('不支持该图谱类型，请检查 diagram_type。')
 if not isinstance(diagram.get('meta'),dict) or diagram['meta'].get('locale')!='zh-CN':raise InputError('请设置 meta.locale 为 zh-CN，并使用中文标题和节点标签。')
 if not isinstance(diagram['meta'].get('output'),str):raise InputError('请在 meta.output 中填写工作目录内的 HTML 相对路径。')
 authored=safe(root,diagram['meta']['output'])
 if authored.suffix!='.html':raise InputError('meta.output 必须是工作目录内的 HTML。')
 out.parent.mkdir(parents=True,exist_ok=True)
 args=[node(),str(HERE/'vendor/archify/bin/archify.mjs'),action,diagram['diagram_type'],str(f)]
 if action=='deliver':args+=[str(out)]
 args+=['--quality','standard','--json']
 r=subprocess.run(args,cwd=root,text=True,capture_output=True,timeout=60)
 try:receipt=json.loads(r.stdout)
 except ValueError:receipt={}
 diagnostics=receipt.get('diagnostics',[])
 issues=[{'code':d.get('code'),'subject':d.get('subject'),'message':'请检查该位置的结构、引用关系或布局约束；按图谱 schema 修正后重试。'} for d in diagnostics[:30] if isinstance(d,dict)]
 ok=r.returncode==0 and (action!='deliver' or out.is_file())
 result={'ok':ok,'message':('图谱校验通过。' if action=='validate' else '已交付中文离线交互图谱。') if ok else '图谱校验或交付失败，请先修复源 JSON；未确认新产物可用。','diagnostics':issues,'source':str(f)}
 if action=='deliver' and ok:result.update(output=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest())
 save(safe(root,'graph-validation.json'),result)
 return result
