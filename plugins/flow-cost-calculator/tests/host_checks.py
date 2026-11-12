"""Real DeepAgent/SkillUseRail/Runner visibility, invocation and unload, without an LLM."""
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
parser.add_argument('--payload', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()

EXPECTED = {'flow_cost_flow_efficiency', 'flow_cost_business_case'}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload = args.payload.resolve()
    before = hashes(payload)
    scratch = args.report.parent / ('isolated-agent-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch / 'host-skills'
    empty.mkdir()
    card = AgentCard(id='flow-cost-test-' + uuid.uuid4().hex, name='流动效率与持续成本测算工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(EXPECTED))
    assert {t.name for t in info} == EXPECTED
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in EXPECTED)
    assert all(any('一' <= ch <= '鿿' for ch in (t.description or '')) for t in info)

    def registered(name):
        return Runner.resource_mgr.get_tool(tool_id=agent.ability_manager.get(name).id)

    rejected = await registered('flow_cost_flow_efficiency').invoke({'lead_time_days': 3})
    assert rejected['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_unknown = await registered('flow_cost_business_case').invoke({'one_time_cost': 1, 'running_cost_per_year': 1, 'benefit_per_year': 1, 'extra': True})
    assert rejected_unknown['error']['code'] == 'INVALID_ARGUMENTS'
    capacity = await registered('flow_cost_flow_efficiency').invoke({'lead_time_days': 3, 'day_type': 'working', 'touch_hours': 30})
    assert capacity['error']['code'] == 'CAPACITY_EXCEEDED'
    flow = await registered('flow_cost_flow_efficiency').invoke({'lead_time_days': 42, 'day_type': 'calendar', 'touch_hours': 16})
    assert flow['ok'] and flow['data']['flow_efficiency_percent'] == 6.7 and flow['data']['bigger_lever'] == 'B'
    case = await registered('flow_cost_business_case').invoke({'one_time_cost': 180000, 'running_cost_per_year': 24000, 'benefit_per_year': 150800, 'years': 3})
    assert case['ok'] and case['data']['result'] == 200400.0 and case['data']['payback_months'] == 17.0
    zero = await registered('flow_cost_business_case').invoke({'one_time_cost': 0, 'running_cost_per_year': 0, 'benefit_per_year': 100})
    assert zero['error']['code'] == 'ZERO_COST'
    live = {'flow_efficiency_percent_42_calendar_16h': flow['data']['flow_efficiency_percent'], 'bigger_lever': flow['data']['bigger_lever'],
            'business_case_result': case['data']['result'], 'payback_months': case['data']['payback_months'],
            'running_cost_share_percent': case['data']['running_cost_share_percent']}
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(EXPECTED)) == []
    assert hashes(payload) == before
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'model_calls': 0,
              'real_deepagent': True, 'real_runner': True, 'real_skill_rail': True,
              'model_visible_direct_tools': sorted(EXPECTED), 'two_tools_loaded': True,
              'registered_tool_invalid_input_rejected': True, 'registered_unknown_field_rejected': True,
              'registered_capacity_and_zero_cost_refusals': True,
              'calls_via_runner': live, 'all_tools_unloaded': True, 'unload_result': unloaded, 'payload_unchanged': True,
              'versions': {n: importlib.metadata.version(n) for n in ('openjiuwen', 'pydantic')},
              'sdk_source': str(Path(sys.modules['openjiuwen'].__file__).resolve()), 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tools': len(EXPECTED), 'live': live}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
