"""Real DeepAgent plugin bind/model-visible cards/Runner invocation/unload; no LLM."""
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
parser.add_argument('--live-price', action='store_true')
args = parser.parse_args()


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload = args.payload.resolve()
    before = hashes(payload)
    manifest = json.loads((payload / 'manifest.json').read_text(encoding='utf-8'))
    catalog = json.loads((payload / 'tools/tool_catalog.json').read_text(encoding='utf-8'))
    expected = {'domain_' + name for name in catalog}
    scratch = args.report.parent / ('agent-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch / 'host-skills'
    empty.mkdir()
    card = AgentCard(id='domain-port-test-' + uuid.uuid4().hex, name='域名比价注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    # Bind the real host rail explicitly; no mock agent, transport or loader.
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    infos = await agent.ability_manager.list_tool_info(names=sorted(expected))
    visible = {info.name for info in infos}
    assert visible == expected, (expected - visible, visible - expected)
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in expected)
    bound = agent.ability_manager.get('domain_search_prices')
    registered = Runner.resource_mgr.get_tool(tool_id=bound.id)
    assert registered is not None
    invalid = await registered.invoke({'private_project_brief': '中文私密内容'})
    assert invalid['error']['code'] == 'INVALID_ARGUMENTS'
    assert '中文私密内容' not in str(invalid)
    result = None
    if args.live_price:
        result = await registered.invoke({'q': '.com,.org,.dev', 'sort': 'renewal', 'maxRenewalCents': 1500, 'limit': 3})
        assert result['ok'], result
        assert 1 <= len(result['data']['offers']) <= 3
    unloaded = await agent.unload_extension(record)
    after_infos = await agent.ability_manager.list_tool_info(names=sorted(expected))
    assert after_infos == []
    assert hashes(payload) == before, 'Host test mutated packaged source bytes'
    versions = {}
    for package in ('openjiuwen', 'mcp', 'jsonschema', 'jiuwenswarm'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'editable module; distribution metadata unavailable'
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'manifest_version': manifest['version'], 'model_calls': 0, 'real_deepagent': True, 'real_runner_resource_manager': True, 'real_skill_rail': True, 'model_visible_native_tools': sorted(visible), 'all_twelve_direct': len(visible) == 12, 'invalid_chinese_input_rejected_before_network': True, 'live_price_via_registered_tool': bool(result and result['ok']), 'unloaded_refs': unloaded, 'all_tools_unloaded': True, 'payload_unchanged': True, 'versions': versions, 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
