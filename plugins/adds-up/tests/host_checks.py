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
parser.add_argument('--fixtures', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()

EXPECTED = {'adds_up_extract', 'adds_up_grim'}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


async def main():
    payload = args.payload.resolve()
    fixtures = args.fixtures.resolve()
    before = hashes(payload)
    fixtures_before = hashes(fixtures)
    scratch = args.report.parent / ('isolated-agent-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    empty = scratch / 'host-skills'
    empty.mkdir()
    card = AgentCard(id='adds-up-test-' + uuid.uuid4().hex, name='文档数字核对工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(EXPECTED))
    assert {t.name for t in info} == EXPECTED
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in EXPECTED)
    assert all(any('一' <= ch <= '鿿' for ch in (t.description or '')) for t in info)

    def registered(name):
        return Runner.resource_mgr.get_tool(tool_id=agent.ability_manager.get(name).id)

    extract, grim = registered('adds_up_extract'), registered('adds_up_grim')
    rejected = await extract.invoke({})
    assert rejected['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_unknown = await extract.invoke({'files': [str(fixtures / '销售明细.csv')], 'extra': True})
    assert rejected_unknown['error']['code'] == 'INVALID_ARGUMENTS'
    missing = await extract.invoke({'files': [str(fixtures / '不存在.xlsx')]})
    assert missing['error']['code'] == 'ALL_FILES_FAILED' and '找不到这个文件' in missing['error']['message']
    bad_grim = await grim.invoke({'n': 0, 'value': '1', 'kind': 'mean'})
    assert bad_grim['error']['code'] == 'INVALID_ARGUMENTS'

    sales = await extract.invoke({'files': [str(fixtures / '销售明细.csv')]})
    assert sales['ok'] and sales['lead_count'] == 1 and '830' in sales['report_text'] and '显示 840' in sales['report_text']
    clean = await extract.invoke({'files': [str(fixtures / '正确的预算.csv')]})
    assert clean['ok'] and clean['lead_count'] == 0
    budget = await extract.invoke({'files': [str(fixtures / '预算表.xlsx')]})
    assert budget['ok'] and budget['lead_count'] == 6 and '只算到第 4 行' in budget['report_text']
    report = await extract.invoke({'files': [str(fixtures / '项目报告.docx')]})
    assert report['ok'] and report['lead_count'] == 6
    for word in ('星期四', '13 周', '65.0%', '25%', '不是日历上存在的日期', '7,200'):
        assert word in report['report_text'], word
    deck = await extract.invoke({'files': [str(fixtures / '季度汇报.pptx')]})
    assert deck['ok'] and deck['lead_count'] == 1
    many = await extract.invoke({'files': [str(fixtures / '销售明细.csv'), str(fixtures / '汇总说明.md'), str(fixtures / '不存在.xlsx')]})
    assert many['ok'] and [bool(f['error']) for f in many['files']] == [False, False, True]
    g_bad = await grim.invoke({'n': 25, 'value': '3.47', 'kind': 'mean'})
    assert g_bad['ok'] and g_bad['consistent'] is False and g_bad['nearest'][0]['gives'] == '3.48'
    g_ok = await grim.invoke({'n': 12, 'value': '33.3', 'kind': 'percent'})
    assert g_ok['ok'] and g_ok['consistent'] is True and g_ok['matching_counts_or_totals'] == [4]
    live = {'sales_csv_leads': sales['lead_count'], 'clean_csv_leads': clean['lead_count'], 'budget_xlsx_leads': budget['lead_count'],
            'report_docx_leads': report['lead_count'], 'deck_pptx_leads': deck['lead_count'],
            'multi_file_error_flags': [bool(f['error']) for f in many['files']],
            'grim_mean_25_3.47_consistent': g_bad['consistent'], 'grim_percent_12_33.3_consistent': g_ok['consistent']}
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(EXPECTED)) == []
    assert hashes(payload) == before
    assert hashes(fixtures) == fixtures_before
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'fixtures': str(fixtures), 'model_calls': 0,
              'real_deepagent': True, 'real_runner': True, 'real_skill_rail': True,
              'model_visible_direct_tools': sorted(EXPECTED), 'two_tools_loaded': True,
              'registered_invalid_input_rejected': True, 'registered_unknown_field_rejected': True,
              'registered_missing_file_refused': True, 'calls_via_runner': live, 'all_tools_unloaded': True,
              'unload_result': unloaded, 'payload_unchanged': True, 'fixtures_unchanged': True,
              'versions': {n: importlib.metadata.version(n) for n in ('openjiuwen', 'pydantic')},
              'sdk_source': str(Path(sys.modules['openjiuwen'].__file__).resolve()), 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tools': len(EXPECTED), 'live': live}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
