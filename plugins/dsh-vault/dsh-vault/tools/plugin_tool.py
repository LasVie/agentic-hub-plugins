"""本地凭据保险库：秘密来自本地受限文件，不接受对话中的密码。"""
import asyncio, json, os, stat
from openjiuwen.core.foundation.tool import Tool, ToolCard
from ..runtime.bridge import PluginError, workspace, safe_path, read_json, locked, run_node, failure

class PluginTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id='dsh_vault',name='dsh_vault',description='本地加密凭据保险库。demo 只测试虚构凭据；真实凭据通过受限本地文件导入，get/list 始终掩码。无需服务账号。',input_params={'type':'object','properties':{'action':{'type':'string','enum':['demo','init','put','list','get','totp','remove']},'workspace_dir':{'type':'string','description':'已有工作目录的绝对路径'},'id':{'type':'string'},'key_file':{'type':'string','description':'工作目录内主口令文件的相对路径，权限必须为600；不要把口令发到对话中'},'credential_file':{'type':'string','description':'工作目录内虚构或用户指定凭据 JSON 的相对路径'},'query':{'type':'string'},'overwrite':{'type':'boolean'},'confirm':{'type':'boolean'}},'required':['action','workspace_dir'],'additionalProperties':False},parallel_safe=False))
    def _run(self,q):
        root=workspace(q.get('workspace_dir'));action=q.get('action')
        if action=='demo':
            directory=safe_path(root,'dsh-vault-demo')
            with locked(root,'vault-demo'):
                req={'directory':str(directory),'master_password':'DEMO-ONLY-not-a-real-master-password'}
                if not (directory/'vault.json').exists():
                    result=run_node({**req,'action':'init'})
                    if not result['ok']:return result
                put=run_node({**req,'action':'put','id':'demo-account','overwrite':True,'credential':{'label':'虚构演示账户','username':'demo@example.invalid','secret':'DEMO-SECRET-DO-NOT-USE','totp_secret':'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'}})
                if not put['ok']:return put
                listing=run_node({**req,'action':'list'});code=run_node({**req,'action':'totp','id':'demo-account','now_ms':59000})
                wrong=run_node({**req,'action':'list','master_password':'wrong-demo-password'})
                encrypted=(directory/'vault.json').read_text(encoding='utf-8')
                checks={'encrypted_at_rest':'DEMO-SECRET-DO-NOT-USE' not in encrypted,'masked_query':listing.get('entries',[{}])[0].get('secret')=='********','totp_known_vector':code.get('code')=='287082','wrong_password_rejected':wrong.get('ok') is False}
                return {'ok':all(checks.values()),'message':'虚构凭据演示完成。演示保险库使用公开测试口令，不能保存真实秘密。','checks':checks,'entries':listing.get('entries',[]),'directory':str(directory)}
        if action not in ('init','put','list','get','totp','remove'):raise PluginError('不支持该保险库操作。')
        key=safe_path(root,q.get('key_file') or 'vault-master-password.txt')
        if key.is_symlink() or not key.is_file() or key.stat().st_size>4096:raise PluginError('请先在本地创建主口令文件，长度至少12字符；不要在对话中提供口令。')
        if os.name!='nt' and stat.S_IMODE(key.stat().st_mode)&0o077:raise PluginError('主口令文件权限必须为600，请在本地执行 chmod 600。')
        password=key.read_text(encoding='utf-8').rstrip('\r\n')
        req={k:v for k,v in q.items() if k in ('action','id','query','overwrite','confirm')}
        req.update(directory=str(safe_path(root,'dsh-vault-data')),master_password=password)
        if action=='put':req['credential']=read_json(safe_path(root,q.get('credential_file') or 'credential.json'),32768)
        with locked(root,'vault-data'):return run_node(req)
    async def invoke(self,inputs,**kwargs):
        try:return await asyncio.to_thread(self._run,inputs)
        except Exception as exc:return failure(exc)
    async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
