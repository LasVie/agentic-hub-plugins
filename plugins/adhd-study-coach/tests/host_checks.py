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

EXPECTED = {'adhd_card_inspect', 'adhd_card_review', 'adhd_card_log_session'}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload = args.payload.resolve()
    before = hashes(payload)
    scratch = args.report.parent / ('isolated-agent-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch / 'host-skills'
    empty.mkdir()
    card = AgentCard(id='adhd-coach-test-' + uuid.uuid4().hex, name='学习教练工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(EXPECTED))
    assert {t.name for t in info} == EXPECTED
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in EXPECTED)
    assert all(any('一' <= ch <= '鿿' for ch in (t.description or '')) for t in info)

    def registered(name):
        return Runner.resource_mgr.get_tool(tool_id=agent.ability_manager.get(name).id)

    rejected = await registered('adhd_card_review').invoke({'today': '2026-11-06'})
    assert rejected['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_unknown = await registered('adhd_card_inspect').invoke({'extra': True})
    assert rejected_unknown['error']['code'] == 'INVALID_ARGUMENTS'
    logged = await registered('adhd_card_log_session').invoke({'today': '2026-11-06', 'entries': [{'subject': '生物', 'topic': '光合作用：光反应', 'key_point': '叶绿素吸收红光和蓝光'}]})
    assert logged['ok'] and logged['data']['sessions'] == 1
    card_text = logged['data']['card_text']
    inspected = await registered('adhd_card_inspect').invoke({'card': card_text, 'today': '2026-11-07'})
    assert inspected['ok'] and inspected['data']['stage'] == 'warm_up' and inspected['data']['due_count'] == 1
    reviewed = await registered('adhd_card_review').invoke({'card': card_text, 'today': '2026-11-07', 'results': [{'subject': '生物', 'topic': '光合作用：光反应', 'grades': ['solid']}]})
    assert reviewed['ok'] and reviewed['data']['changes'][0]['after']['interval_days'] == 3
    live = {'stage_after_one_day': inspected['data']['stage'], 'interval_after_solid': reviewed['data']['changes'][0]['after']['interval_days'],
            'next_due': reviewed['data']['changes'][0]['after']['due']}
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(EXPECTED)) == []
    assert hashes(payload) == before
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'model_calls': 0,
              'real_deepagent': True, 'real_runner': True, 'real_skill_rail': True,
              'model_visible_direct_tools': sorted(EXPECTED), 'three_tools_loaded': True,
              'registered_tool_invalid_input_rejected': True, 'registered_unknown_field_rejected': True,
              'calls_via_runner': live, 'all_tools_unloaded': True, 'unload_result': unloaded, 'payload_unchanged': True,
              'versions': {n: importlib.metadata.version(n) for n in ('openjiuwen', 'pydantic')},
              'sdk_source': str(Path(sys.modules['openjiuwen'].__file__).resolve()), 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tools': len(EXPECTED), 'live': live}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
