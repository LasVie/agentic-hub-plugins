"""Real DeepAgent/SkillUseRail/Runner visibility and unload, without an LLM."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode = True
from openjiuwen.core.runner import Runner
from openjiuwen.core.single_agent.schema.agent_card import AgentCard
from openjiuwen.harness.deep_agent import DeepAgent
from openjiuwen.harness.rails import SkillUseRail
from openjiuwen.harness.schema.config import DeepAgentConfig

parser = argparse.ArgumentParser()
parser.add_argument('--payload',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--live',action='store_true')
args = parser.parse_args()

def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

async def main():
    payload = args.payload.resolve()
    before = hashes(payload)
    expected = {'biorxiv_'+name for name in json.loads((payload/'tools/tool_catalog.json').read_text(encoding='utf-8'))}
    scratch = args.report.parent / ('isolated-agent-'+uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch/'host-skills'
    empty.mkdir()
    card = AgentCard(id='biorxiv-test-'+uuid.uuid4().hex,name='预印本工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card,language='cn',auto_create_workspace=False,cwd=str(scratch),enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty),skill_mode='all',include_tools=False,enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(expected))
    assert {t.name for t in info} == expected
    assert all(agent.ability_manager.get(name).exposure.value=='direct' for name in expected)
    bound = agent.ability_manager.get('biorxiv_search_preprints')
    registered = Runner.resource_mgr.get_tool(tool_id=bound.id)
    rejected = await registered.invoke({'date_from':'2024-01-08','date_to':'2024-01-01'})
    assert rejected['error']['code']=='INVALID_ARGUMENTS'
    live = None
    med = None
    if args.live:
        bound = agent.ability_manager.get('biorxiv_get_categories')
        live = await Runner.resource_mgr.get_tool(tool_id=bound.id).invoke({})
        assert live['ok'] and 'bioinformatics' in json.dumps(live['data'])
        bound = agent.ability_manager.get('biorxiv_search_preprints')
        med = await Runner.resource_mgr.get_tool(tool_id=bound.id).invoke({'date_from':'2024-01-01','date_to':'2024-01-07','server':'medrxiv','limit':1})
        assert med['ok'] and med['received_count']==1
        assert med['data']['results'][0].get('doi')
        assert '2024-01-01'<=med['data']['results'][0]['date']<='2024-01-07'
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(expected)) == []
    assert hashes(payload)==before
    report = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'payload':str(payload),'model_calls':0,
              'real_deepagent':True,'real_runner':True,'real_skill_rail':True,
              'model_visible_direct_tools':sorted(expected),'seven_tools_loaded':True,
              'registered_tool_invalid_input_rejected':True,'live_categories_via_runner':bool(live and live['ok']),
              'live_medrxiv_via_runner':bool(med and med['ok']),
              'all_tools_unloaded':True,'unload_result':unloaded,'payload_unchanged':True,
              'versions':{n:importlib.metadata.version(n) for n in ('mcp','jsonschema','httpx','pydantic')},
              'sdk_source':str(Path(sys.modules['openjiuwen'].__file__).resolve()),'frontend_conversation':'not performed'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    asyncio.run(main())
