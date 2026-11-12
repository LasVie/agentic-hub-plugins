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
parser.add_argument('--live', action='store_true')
args = parser.parse_args()

EXPECTED = {'jma_' + k for k in ('locate', 'rainfall', 'warnings', 'site_rain_risk', 'wbgt')}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload = args.payload.resolve()
    before = hashes(payload)
    scratch = args.report.parent / ('isolated-agent-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch / 'host-skills'
    empty.mkdir()
    card = AgentCard(id='jma-test-' + uuid.uuid4().hex, name='日本雨量工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(EXPECTED))
    assert {t.name for t in info} == EXPECTED
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in EXPECTED)
    assert all(any('一' <= ch <= '鿿' for ch in (t.description or '')) for t in info)

    def registered(name):
        return Runner.resource_mgr.get_tool(tool_id=agent.ability_manager.get(name).id)

    rejected = await registered('jma_rainfall').invoke({'days': 3})
    assert rejected['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_unknown = await registered('jma_warnings').invoke({'place': '東京', 'extra': True})
    assert rejected_unknown['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_range = await registered('jma_rainfall').invoke({'place': '東京', 'days': 30})
    assert rejected_range['error']['code'] == 'INVALID_ARGUMENTS'
    live = {}
    if args.live:
        located = await registered('jma_locate').invoke({'place': '100-0005'})
        assert located['ok'] and located['data']['rain_station']['code'] == '44132' and located['data']['forecast_office_code'] == '130000'
        rain = await registered('jma_rainfall').invoke({'place': '東京', 'days': 2})
        assert rain['ok'] and len(rain['data']['daily']) == 2 and rain['data']['station']['code'] == '44132'
        warn = await registered('jma_warnings').invoke({'place': '100-0005'})
        assert warn['ok'] and warn['data']['areas'] == ['千代田区']
        site = await registered('jma_site_rain_risk').invoke({'place': '35.681,139.767'})
        assert site['ok'] and len(site['data']['kikikuru']['layers']) == 3
        heat = await registered('jma_wbgt').invoke({'place': '東京', 'days': 1})
        assert heat['ok'] and heat['data']['station']['code'] == '44132'
        outside = await registered('jma_locate').invoke({'place': '51.5,-0.12'})
        assert outside['error']['code'] == 'OUT_OF_COVERAGE'
        live = {'locate_station': located['data']['rain_station']['code'], 'rain_days': len(rain['data']['daily']),
                'warning_areas': warn['data']['areas'], 'active_warnings': len(warn['data']['active_warnings']),
                'site_layers': len(site['data']['kikikuru']['layers']), 'wbgt_values': sum(len(d['values']) for d in heat['data']['days']),
                'outside_japan_rejected': True}
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(EXPECTED)) == []
    assert hashes(payload) == before, 'payload changed (a file was written into the plugin folder)'
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'model_calls': 0,
              'real_deepagent': True, 'real_runner': True, 'real_skill_rail': True,
              'model_visible_direct_tools': sorted(EXPECTED), 'five_tools_loaded': True,
              'registered_tool_invalid_input_rejected': True, 'registered_unknown_field_rejected': True,
              'live_calls_via_runner': live, 'all_tools_unloaded': True, 'unload_result': unloaded, 'payload_unchanged_no_files_written': True,
              'versions': {n: importlib.metadata.version(n) for n in ('openjiuwen', 'pydantic')},
              'sdk_source': str(Path(sys.modules['openjiuwen'].__file__).resolve()), 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tools': len(EXPECTED), 'live': live}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
