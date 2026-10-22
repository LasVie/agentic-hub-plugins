"""本地事件与会话状态；所有写入均加锁、原子替换。"""
import hashlib, json, re
from datetime import datetime, timedelta, timezone
from .bridge import PluginError, workspace, safe_path, read_json, atomic_json, locked, run_node

def context(root,session_id,force_full=False,now_ms=None):
    session_id=str(session_id or 'manual')
    if len(session_id)>256:raise PluginError('会话标识过长。')
    rel='.life-state/'+hashlib.sha256(session_id.encode()).hexdigest()+'.json'
    statefile=safe_path(root,rel)
    with locked(root,'life-state-'+session_id):
        previous=read_json(statefile) if statefile.exists() else None
        req={'workspace_dir':str(root),'state':previous,'force_full':force_full}
        if now_ms is not None:req['now_ms']=now_ms
        result=run_node(req)
        if result.get('ok'):
            state=result.pop('next_state');atomic_json(statefile,state)
        return result

def react(root,q):
    event_id=q.get('event_id')
    if not isinstance(event_id,str) or not event_id or len(event_id)>128:raise PluginError('需要有效的 event_id。')
    updates={k:q[k] for k in ('feeling','thought','action_text') if isinstance(q.get(k),str) and q[k].strip()}
    if not updates or any(len(v)>4000 for v in updates.values()):raise PluginError('请提供不超过4000字符的感受、思考或行动。')
    life=safe_path(root,'.life')
    if not life.is_dir():raise PluginError('没有本地生活事件目录。')
    with locked(root,'life-events'):
        for day in sorted(life.iterdir(),key=lambda p:p.name,reverse=True):
            if not re.fullmatch(r'\d{6}',day.name):continue
            path=safe_path(root,'.life/'+day.name+'/events.json')
            if not path.exists():continue
            data=read_json(path)
            if not isinstance(data,dict) or not isinstance(data.get('events'),list):continue
            for event in data['events']:
                if not isinstance(event,dict) or event.get('id')!=event_id:continue
                old=event.get('react') or {}
                if not isinstance(old,dict):raise PluginError('原事件的 react 格式不正确。')
                revised=dict(old)
                for k,v in updates.items():revised['action' if k=='action_text' else k]=v.strip()
                revised['updated_at']=datetime.now(timezone.utc).isoformat()
                event['react']=revised;atomic_json(path,data)
                return {'ok':True,'message':'已原子更新该虚构生活事件的反应，原事件其他字段保留。','event_id':event_id,'react':revised}
    raise PluginError('未找到该事件，请先读取当前事件列表。')

def seed_demo(root):
    now=datetime.now(timezone(timedelta(hours=8)));day=now.strftime('%y%m%d')
    path=safe_path(root,'.life/'+day+'/events.json')
    with locked(root,'life-events'):
        if path.exists():raise PluginError('今天的事件文件已存在，演示不会覆盖；请使用新的专用测试目录。')
        data={'date':day,'timezone':'Asia/Singapore','world_summary':'虚构的安静小城，以下仅为功能测试。','events':[
        {'id':'demo-library','time':(now-timedelta(hours=2)).isoformat(),'type':'encounter','title':'图书馆偶遇','description':'虚构角色在图书馆遇到热心读者，获赠一本星空手册。','actors':['虚构读者'],'location':'城南图书馆','importance':3,'impact':'对天文观察产生兴趣。'},
        {'id':'demo-walk','time':(now-timedelta(minutes=40)).isoformat(),'type':'routine','title':'雨后散步','description':'虚构角色在雨后公园散步，观察水洼倒影。','importance':1},
        {'id':'demo-expired','time':(now-timedelta(hours=26)).isoformat(),'type':'routine','title':'已过期的早餐','description':'这条超过24小时窗口，不应注入。'}]}
        atomic_json(path,data)
    return {'ok':True,'message':'已建立3条虚构测试事件，其中1条已过期；未接入外部世界服务。','path':str(path)}
