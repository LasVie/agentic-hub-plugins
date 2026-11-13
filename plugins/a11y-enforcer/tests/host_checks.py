"""Real DeepAgent/SkillUseRail/Runner visibility, invocation and unload, without an LLM.

Run from a scratch directory (the SDK writes logs/ to the cwd):
    python -B -X utf8 host_checks.py --payload <extracted a11y-enforcer dir> --fixtures <tests/fixtures/manual> --report <host-report.json>
"""
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

EXPECTED = {'a11y_scan', 'a11y_contrast'}


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
    card = AgentCard(id='a11y-enforcer-test-' + uuid.uuid4().hex, name='网页无障碍检查工具注册验证')
    agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language='cn', auto_create_workspace=False, cwd=str(scratch), enable_tool_resilience_rail=False))
    await agent.register_rail(SkillUseRail(skills_dir=str(empty), skill_mode='all', include_tools=False, enable_cache=False))
    record = await agent.load_plugin(str(payload))
    info = await agent.ability_manager.list_tool_info(names=sorted(EXPECTED))
    assert {t.name for t in info} == EXPECTED
    assert all(agent.ability_manager.get(name).exposure.value == 'direct' for name in EXPECTED)
    assert all(any('一' <= ch <= '鿿' for ch in (t.description or '')) for t in info)

    def registered(name):
        return Runner.resource_mgr.get_tool(tool_id=agent.ability_manager.get(name).id)

    scan, contrast = registered('a11y_scan'), registered('a11y_contrast')
    rejected = await scan.invoke({})
    assert rejected['error']['code'] == 'INVALID_ARGUMENTS'
    rejected_unknown = await scan.invoke({'paths': [str(fixtures / '登录页.html')], 'json': str(scratch / 'x.json')})
    assert rejected_unknown['error']['code'] == 'INVALID_ARGUMENTS' and not (scratch / 'x.json').exists()
    missing = await scan.invoke({'paths': [str(fixtures / '不存在.html')]})
    assert missing['error']['code'] == 'ALL_PATHS_FAILED' and '找不到这个文件或文件夹' in missing['error']['skipped'][0]['reason']
    bad_contrast = await contrast.invoke({'pairs': [{'foreground': 'bogus', 'background': '#fff'}]})
    assert bad_contrast['error']['code'] == 'INVALID_COLOR' and '无法识别的颜色' in bad_contrast['error']['message']

    login = await scan.invoke({'paths': [str(fixtures / '登录页.html')], 'max_issues': 500})
    assert login['ok'] and login['summary']['errors'] == 8 and login['summary']['warnings'] == 2
    assert '[viewport-zoom] WCAG 1.4.4' in login['report_text'] and '没有 lang 属性' in login['report_text']
    card_jsx = await scan.invoke({'paths': [str(fixtures / '商品卡片.jsx')], 'max_issues': 500})
    assert card_jsx['ok'] and card_jsx['summary']['errors'] == 6 and card_jsx['summary']['warnings'] == 0
    vue = await scan.invoke({'paths': [str(fixtures / '订单表单.vue')], 'max_issues': 500})
    assert vue['ok'] and vue['summary']['errors'] == 7 and vue['summary']['warnings'] == 3
    clean = await scan.invoke({'paths': [str(fixtures / '正确示例.html')]})
    assert clean['ok'] and clean['summary']['errors'] == 0 and clean['summary']['warnings'] == 0
    folder = await scan.invoke({'paths': [str(fixtures)], 'max_issues': 500})
    assert folder['ok'] and folder['summary']['files_scanned'] == 4 and folder['summary']['errors'] == 21 and folder['summary']['warnings'] == 5
    errors_only = await scan.invoke({'paths': [str(fixtures)], 'errors_only': True, 'max_issues': 500})
    assert errors_only['summary']['warnings'] == 0 and errors_only['summary']['errors'] == 21
    ratio_black = await contrast.invoke({'pairs': [{'foreground': '#000000', 'background': '#ffffff'}]})
    assert ratio_black['ok'] and ratio_black['pairs'][0]['ratio'] == 21.0
    ratio_gray = await contrast.invoke({'pairs': [{'foreground': '#777777', 'background': '#ffffff'}, {'foreground': '#767676', 'background': '#ffffff'}]})
    assert ratio_gray['ok'] and [p['ratio'] for p in ratio_gray['pairs']] == [4.48, 4.54]
    assert [p['aa_normal'] for p in ratio_gray['pairs']] == [False, True] and '未达标' in ratio_gray['report_text']
    live = {'login_html': login['summary'], 'card_jsx': card_jsx['summary'], 'order_vue': vue['summary'], 'clean_html': clean['summary'],
            'folder_all_four': folder['summary'], 'contrast_black_white': ratio_black['pairs'][0]['ratio'],
            'contrast_777777_767676': [p['ratio'] for p in ratio_gray['pairs']]}
    unloaded = await agent.unload_extension(record)
    assert await agent.ability_manager.list_tool_info(names=sorted(EXPECTED)) == []
    assert hashes(payload) == before
    assert hashes(fixtures) == fixtures_before
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(payload), 'fixtures': str(fixtures), 'model_calls': 0,
              'real_deepagent': True, 'real_runner': True, 'real_skill_rail': True,
              'model_visible_direct_tools': sorted(EXPECTED), 'two_tools_loaded': True,
              'registered_invalid_input_rejected': True, 'registered_unknown_field_rejected': True,
              'registered_missing_path_refused': True, 'registered_invalid_color_refused': True, 'calls_via_runner': live,
              'all_tools_unloaded': True, 'unload_result': unloaded, 'payload_unchanged': True, 'fixtures_unchanged': True,
              'versions': {n: importlib.metadata.version(n) for n in ('openjiuwen', 'pydantic')},
              'sdk_source': str(Path(sys.modules['openjiuwen'].__file__).resolve()), 'frontend_conversation': 'not performed'}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tools': len(EXPECTED), 'live': live}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
