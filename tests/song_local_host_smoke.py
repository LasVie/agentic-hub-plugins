"""Requires the real openJiuwen SDK. Tool invocation is separate from model/UI evidence."""
import asyncio, importlib.util, json, os, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
from test_song_local_plugins import module, package
from openjiuwen.harness.resources.extension_loader import load_plugin_package
from openjiuwen.core.foundation.tool import Tool
from openjiuwen.core.single_agent.prompts.builder import SystemPromptBuilder

async def main():
    results={}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for slug in ['dsh-vault','dsh-pianist','dsh-simulated-life']:
            _,p=package(slug);spec=load_plugin_package(p/'manifest.json')
            obj=module(slug,'tools.plugin_tool').PluginTool();assert isinstance(obj,Tool)
            folder=root/slug;folder.mkdir()
            if slug=='dsh-vault':
                result=await obj.invoke({'action':'demo','workspace_dir':str(folder)});assert result['ok'],result
                bridge=module(slug,'runtime.bridge');(folder/'vault-master-password.txt').write_text('Synthetic-private-password');os.chmod(folder/'vault-master-password.txt',0o644)
                assert not (await obj.invoke({'action':'init','workspace_dir':str(folder)}))['ok']
                os.chmod(folder/'vault-master-password.txt',0o600)
                assert (await obj.invoke({'action':'init','workspace_dir':str(folder)}))['ok']
            elif slug=='dsh-pianist':
                result=await obj.invoke({'workspace_dir':str(folder),'title':'中文测试 <script>unsafe()</script>','bpm':120,'notes':[{'midi':60,'start_beat':0,'beats':1}]});assert result['ok'],result
                markup=Path(result['artifacts']['player.html']).read_text();assert '<script>unsafe()</script>' not in markup;assert '播放' in markup;assert not any(x in markup for x in ['src="https://','src="http://'])
                assert all(Path(p).is_file() for p in result['artifacts'].values())
            else:
                result=await obj.invoke({'action':'seed_demo','workspace_dir':str(folder)});assert result['ok'],result
                result=await obj.invoke({'action':'context','workspace_dir':str(folder),'session_id':'sdk-demo'});assert result['ok'] and result['event_count']==2,result
                rail=module(slug,'rails.life_rail').LifeRail();assert rail.get_callbacks()
                builder=SystemPromptBuilder();rail.init(SimpleNamespace(system_prompt_builder=builder));rail.workspace=SimpleNamespace(root_path=folder)
                ctx=SimpleNamespace(session=SimpleNamespace(get_session_id=lambda:'rail-sdk-test'))
                await rail.before_model_call(ctx);assert 'dsh_simulated_life_context' in builder._sections
                assert '图书馆' in builder._sections['dsh_simulated_life_context'].render('cn')
                await rail.before_model_call(ctx);assert len(builder._sections)==1
                rail.uninit(None);assert not builder._sections
            results[slug]={'real_sdk_manifest_loaded':True,'real_tool_invoked':True,'ok':True}
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':asyncio.run(main())
