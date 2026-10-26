"""Actual DeepAgent, SkillUseRail and Runner registration; no model or loader stubs."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode=True
from openjiuwen.core.runner import Runner
from openjiuwen.core.single_agent.schema.agent_card import AgentCard
from openjiuwen.harness.deep_agent import DeepAgent
from openjiuwen.harness.rails import SkillUseRail
from openjiuwen.harness.schema.config import DeepAgentConfig

parser=argparse.ArgumentParser()
parser.add_argument('--payload',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--live-catalog',action='store_true')
args=parser.parse_args()


def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload=args.payload.resolve()
    before=hashes(payload)
    catalog=json.loads((payload/'tools/tool_catalog.json').read_text(encoding='utf-8'))
    expected={'coffee_'+name for name in catalog}
    scratch=args.report.parent/('agent-'+uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty=scratch/'host-skills'
    empty.mkdir()
    card=AgentCard(id='coffee-port-'+uuid.uuid4().hex,name='咖啡原生工具注册验证')
    agent=DeepAgent(card).configure(DeepAgentConfig(card=card,language='cn',auto_create_workspace=False,cwd=str(scratch),enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty),skill_mode='all',include_tools=False,enable_cache=False))
    record=await agent.load_plugin(str(payload))
    infos=await agent.ability_manager.list_tool_info(names=sorted(expected))
    assert {x.name for x in infos}==expected
    assert all(agent.ability_manager.get(n).exposure.value=='direct' for n in expected)
    tool=agent.ability_manager.get('coffee_search_coffees')
    registered=Runner.resource_mgr.get_tool(tool_id=tool.id)
    assert registered is not None
    invalid=await registered.invoke({'private_notes':'中文私密内容'})
    assert invalid['error']['code']=='INVALID_ARGUMENTS' and '中文私密内容' not in str(invalid)
    result=None
    if args.live_catalog:
        result=await registered.invoke({'category':'espresso','price_max':30,'limit':2})
        assert result['ok'] and 1<=len(result['data']['coffees'])<=2
    unloaded=await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(expected))==[]
    assert hashes(payload)==before
    versions={}
    for name in ('openjiuwen','mcp','httpx','jsonschema'):
        versions[name]=importlib.metadata.version(name)
    report={'at_utc':datetime.now(timezone.utc).isoformat(),'payload':str(payload),'model_calls':0,
      'real_deepagent':True,'real_skill_rail':True,'real_runner':True,'model_visible_tools':sorted(expected),
      'all_eight_direct':len(expected)==8,'extra_private_field_rejected_before_network':True,
      'registered_live_catalog_call':bool(result and result['ok']),'unloaded_refs':unloaded,
      'all_tools_unloaded':True,'payload_unchanged':True,'versions':versions,'frontend_conversation':'not performed'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,ensure_ascii=False))


asyncio.run(main())
