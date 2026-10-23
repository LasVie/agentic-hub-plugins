from .common import *
from datetime import datetime,timezone
def execute(q):
 root=workspace(q);action=q.get('action')
 if action not in ('on','off','status'):raise InputError('请选择 on 开启、off 关闭或 status 查询。')
 p=safe(root,'action-first-state.json')
 with locked(root,'action-first'):
  state=json.loads(read(p,8192)) if p.exists() else {'enabled':False,'revision':0}
  if not isinstance(state,dict) or type(state.get('enabled')) is not bool or type(state.get('revision')) is not int:raise InputError('状态文件损坏；请保留文件并检查，不自动覆盖。')
  if action!='status':
   state={'enabled':action=='on','revision':state['revision']+1,'updated_at':datetime.now(timezone.utc).isoformat()};save(p,state)
  return {'ok':True,**state,'message':'行动优先表达已开启。' if state['enabled'] else '行动优先表达已关闭。','workspace':str(root),'state_file':str(p)}
