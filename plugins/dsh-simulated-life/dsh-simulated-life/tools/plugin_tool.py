"""模拟生活原生工具。"""
import asyncio
from openjiuwen.core.foundation.tool import Tool, ToolCard
from ..runtime.bridge import workspace, failure, PluginError
from ..runtime.life import context, react, seed_demo

class PluginTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id='dsh_simulated_life',name='dsh_simulated_life',description='本地虚构生活事件：seed_demo 建立专用测试事件；context 读取24小时窗口并按会话去重通知；react 回写感受、思考、行动。无需账号或网络。',input_params={'type':'object','properties':{'action':{'type':'string','enum':['seed_demo','context','react']},'workspace_dir':{'type':'string'},'session_id':{'type':'string','description':'手工查询的会话标识；宿主会话存在时优先使用宿主标识'},'force_full':{'type':'boolean'},'event_id':{'type':'string'},'feeling':{'type':'string'},'thought':{'type':'string'},'action_text':{'type':'string'}},'required':['action','workspace_dir'],'additionalProperties':False},parallel_safe=False))
    def _run(self,q,session):
        root=workspace(q.get('workspace_dir'));action=q.get('action')
        if action=='seed_demo':return seed_demo(root)
        if action=='react':return react(root,q)
        if action=='context':
            sid=session.get_session_id() if session and hasattr(session,'get_session_id') else q.get('session_id','manual')
            return context(root,sid,q.get('force_full',False))
        raise PluginError('不支持该模拟生活操作。')
    async def invoke(self,inputs,**kwargs):
        try:return await asyncio.to_thread(self._run,inputs,kwargs.get('session'))
        except Exception as exc:return failure(exc)
    async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
