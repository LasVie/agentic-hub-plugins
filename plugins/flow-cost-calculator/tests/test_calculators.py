"""Offline business-boundary checks for 流动效率与持续成本测算: argument validation, exact arithmetic,
the upstream control examples, refusal rules, scenario maths, flag logic, safety of the source and
Chinese output. No network, no model, no files written."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

PAYLOAD = Path(os.environ.get('FLOWCOST_TEST_PAYLOAD') or Path(__file__).resolve().parents[1] / 'flow-cost-calculator')
spec = importlib.util.spec_from_file_location('flow_cost_under_test', PAYLOAD / 'tools/flow_cost.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HAN = re.compile('[一-鿿]')


def call(name, args):
    return asyncio.run(m.call_tool(name, args))


def fe(days=3, day_type='working', hours=20, **extra):
    return call('flow_efficiency', dict({'lead_time_days': days, 'day_type': day_type, 'touch_hours': hours}, **extra))


def bc(p=180000, l=24000, n=150800, **extra):
    return call('business_case', dict({'one_time_cost': p, 'running_cost_per_year': l, 'benefit_per_year': n}, **extra))


def code(result):
    return result['error']['code']


class RegistrationTests(unittest.TestCase):
    def test_two_tool_cards_with_closed_schemas_and_chinese_descriptions(self):
        tools = {'flow_cost_flow_efficiency': m.FlowEfficiencyTool(), 'flow_cost_business_case': m.BusinessCaseTool()}
        for name, tool in tools.items():
            self.assertEqual(tool.card.name, name)
            self.assertFalse(tool.card.input_params['additionalProperties'])
            self.assertTrue(HAN.search(tool.card.description))
            for prop in tool.card.input_params['properties'].values():
                self.assertTrue(HAN.search(prop['description']), prop)

    def test_stream_equals_invoke(self):
        tool = m.FlowEfficiencyTool()
        args = {'lead_time_days': 3, 'day_type': 'working', 'touch_hours': 20}

        async def both():
            invoked = await tool.invoke(args)
            streamed = [chunk async for chunk in tool.stream(args)]
            return invoked, streamed
        invoked, streamed = asyncio.run(both())
        self.assertEqual(streamed, [invoked])
        self.assertTrue(invoked['ok'])


class FlowValidationTests(unittest.TestCase):
    def test_bad_inputs_are_rejected_with_invalid_arguments(self):
        good = {'lead_time_days': 3, 'day_type': 'working', 'touch_hours': 20}
        bad = [
            'text', None, [], 5, {},
            dict(good, extra=1),
            {k: v for k, v in good.items() if k != 'touch_hours'},
            dict(good, lead_time_days=None),
            dict(good, lead_time_days=True), dict(good, lead_time_days='3'), dict(good, lead_time_days=0), dict(good, lead_time_days=-1),
            dict(good, lead_time_days=5000.01), dict(good, lead_time_days=float('nan')), dict(good, lead_time_days=float('inf')),
            dict(good, day_type='weekly'), dict(good, day_type=''), dict(good, day_type=3),
            dict(good, touch_hours=0), dict(good, touch_hours=-2), dict(good, touch_hours='20'), dict(good, touch_hours=False),
            dict(good, items_per_year=-1), dict(good, items_per_year=100001), dict(good, items_per_year=2.5), dict(good, items_per_year=True),
            dict(good, speedup_factor=1), dict(good, speedup_factor=0.5), dict(good, speedup_factor=101),
            dict(good, wait_reduction_ratio=0), dict(good, wait_reduction_ratio=1.01), dict(good, wait_reduction_ratio=-0.1),
        ]
        for arguments in bad:
            result = call('flow_efficiency', arguments)
            self.assertFalse(result['ok'], arguments)
            self.assertEqual(code(result), 'INVALID_ARGUMENTS', arguments)
            self.assertTrue(HAN.search(result['error']['message']), arguments)

    def test_upper_boundaries_are_accepted(self):
        self.assertTrue(fe(days=5000, hours=1, items_per_year=100000)['ok'])
        self.assertTrue(fe(items_per_year=0)['ok'])


class FlowResultTests(unittest.TestCase):
    def test_upstream_control_example_working_days(self):
        d = fe(3, 'working', 20)['data']
        self.assertEqual((d['lead_time_hours'], d['wait_hours'], d['flow_efficiency_percent']), (24.0, 4.0, 83.3))

    def test_upstream_control_example_calendar_days_and_levers(self):
        r = fe(42, 'calendar', 16)
        d = r['data']
        self.assertEqual((d['working_days'], d['lead_time_hours'], d['wait_hours'], d['wait_working_days']), (30.0, 240.0, 224.0, 28.0))
        self.assertEqual(d['flow_efficiency_percent'], 6.7)
        self.assertEqual((d['lever_a']['new_lead_time_working_days'], d['lever_a']['saved_working_days']), (29.0, 1.0))
        self.assertEqual((d['lever_b']['new_lead_time_working_days'], d['lever_b']['saved_working_days']), (16.0, 14.0))
        self.assertEqual(d['bigger_lever'], 'B')
        self.assertTrue(any('5/7' in c for c in d['caveats_zh']))
        self.assertFalse(any('低于 5%' in w for w in r['warnings_zh']))  # 6.7% is not below 5%

    def test_below_five_percent_is_flagged_for_checking_the_estimate(self):
        r = fe(100, 'working', 10)  # 10 / 800 = 1.25 %
        self.assertEqual(r['data']['flow_efficiency_percent'], 1.3)
        self.assertTrue(any('低于 5%' in w for w in r['warnings_zh']))
        self.assertFalse(any('低于 5%' in w for w in fe(3, 'working', 20)['warnings_zh']))
        self.assertFalse(any('低于 5%' in w for w in fe(20, 'working', 8)['warnings_zh']))  # exactly 5 %

    def test_custom_lever_parameters_and_bigger_lever_flips(self):
        d = fe(10, 'working', 70, speedup_factor=10, wait_reduction_ratio=0.1)['data']
        self.assertEqual(d['bigger_lever'], 'A')
        self.assertEqual(d['lever_a']['saved_working_days'], 7.88)
        self.assertEqual(d['lever_b']['saved_working_days'], 0.13)  # 10 h wait x 0.1 = 1 h = 0.125 days, half-up

    def test_equal_levers(self):
        # wait 4h, touch 4h; A saves 4*(1-1/2)=2h; B saves 4*0.5=2h
        r = fe(1, 'working', 4)
        self.assertEqual(r['data']['bigger_lever'], 'equal')
        self.assertTrue(any('相同' in w for w in r['warnings_zh']))

    def test_yearly_projection_is_item_days_and_labelled(self):
        r = fe(42, 'calendar', 16, items_per_year=120)
        self.assertEqual(r['data']['yearly_wait_item_days'], 3360.0)
        self.assertTrue(any('事项·天' in f for f in r['data']['formulas_zh']))
        self.assertTrue(any('日历时间' in c for c in r['data']['caveats_zh']))
        self.assertIsNone(fe()['data']['yearly_wait_item_days'])
        self.assertTrue(any('没有做年度推算' in c for c in fe()['data']['caveats_zh']))

    def test_touch_equal_to_capacity_is_one_hundred_percent_with_flag(self):
        r = fe(3, 'working', 24)
        self.assertEqual(r['data']['flow_efficiency_percent'], 100.0)
        self.assertEqual(r['data']['wait_hours'], 0.0)
        self.assertTrue(any('100%' in w for w in r['warnings_zh']))

    def test_capacity_exceeded_is_refused_with_the_capacity_maths(self):
        r = fe(3, 'working', 24.5)
        self.assertEqual(code(r), 'CAPACITY_EXCEEDED')
        self.assertEqual(r['error']['lead_time_hours'], 24.0)
        self.assertIn('24.00', r['error']['message'])
        self.assertEqual(code(fe(7, 'calendar', 41)), 'CAPACITY_EXCEEDED')  # 7 calendar days = 5 working days = 40 h

    def test_fractional_inputs_are_exact(self):
        d = fe(0.5, 'working', 1)['data']  # 4 h lead time
        self.assertEqual((d['lead_time_hours'], d['flow_efficiency_percent']), (4.0, 25.0))
        d = fe(0.1, 'working', 0.4)['data']  # 0.8 h: float arithmetic would not be exact
        self.assertEqual(d['flow_efficiency_percent'], 50.0)

    def test_equals_sign_only_when_exact(self):
        formulas = fe(3, 'working', 20)['data']['formulas_zh']
        self.assertTrue(any('= 24.00 小时' in f for f in formulas))
        self.assertTrue(any('≈ 83.3%' in f for f in formulas))
        self.assertFalse(any('= 83.3%' in f for f in formulas))

    def test_every_formula_shows_substituted_numbers(self):
        for line in fe(42, 'calendar', 16, items_per_year=10)['data']['formulas_zh']:
            self.assertRegex(line, r'\d')
            self.assertIn('=', line.replace('≈', '=') if '≈' in line else line)


class BusinessValidationTests(unittest.TestCase):
    def test_bad_inputs_are_rejected_with_invalid_arguments(self):
        good = {'one_time_cost': 180000, 'running_cost_per_year': 24000, 'benefit_per_year': 150800}
        bad = [
            'text', None, [], {},
            dict(good, extra=1),
            {k: v for k, v in good.items() if k != 'benefit_per_year'},
            dict(good, one_time_cost=-1), dict(good, running_cost_per_year=-0.01), dict(good, benefit_per_year=0), dict(good, benefit_per_year=-5),
            dict(good, one_time_cost='180000'), dict(good, one_time_cost=True), dict(good, one_time_cost=None),
            dict(good, one_time_cost=float('nan')), dict(good, benefit_per_year=float('inf')),
            dict(good, one_time_cost=m.MAX_AMOUNT + 1), dict(good, running_cost_per_year=1e10), dict(good, benefit_per_year=2_000_000_000),
            dict(good, years=4), dict(good, years=3.0), dict(good, years='3'), dict(good, years=0),
            dict(good, usage_ratio=0), dict(good, usage_ratio=1), dict(good, usage_ratio=1.5),
            dict(good, running_cost_overrun_ratio=0), dict(good, running_cost_overrun_ratio=11),
            dict(good, currency=''), dict(good, currency='   '), dict(good, currency='x' * 9), dict(good, currency='a\nb'), dict(good, currency=5),
        ]
        for arguments in bad:
            result = call('business_case', arguments)
            self.assertFalse(result['ok'], arguments)
            self.assertEqual(code(result), 'INVALID_ARGUMENTS', arguments)
            self.assertTrue(HAN.search(result['error']['message']), arguments)

    def test_boundary_values_are_accepted(self):
        self.assertTrue(bc(p=m.MAX_AMOUNT, l=m.MAX_AMOUNT, n=m.MAX_AMOUNT)['ok'])
        self.assertTrue(bc(years=5, usage_ratio=0.01, running_cost_overrun_ratio=10, currency='USD')['ok'])

    def test_all_zero_cost_is_refused(self):
        r = bc(p=0, l=0)
        self.assertEqual(code(r), 'ZERO_COST')
        self.assertTrue(bc(p=0, l=100)['ok'] and bc(p=100, l=0)['ok'])


class BusinessResultTests(unittest.TestCase):
    def test_upstream_control_example(self):
        r = bc()
        d = r['data']
        self.assertEqual((d['running_cost_total'], d['total_cost'], d['total_benefit'], d['result']), (72000.0, 252000.0, 452400.0, 200400.0))
        self.assertEqual((d['running_cost_share_percent'], d['monthly_surplus'], d['payback_months'], d['roi_percent']), (28.6, 10566.67, 17.0, 79.5))
        self.assertEqual((d['break_even_usage_percent'], d['break_even_cost_overrun_percent']), (55.7, 278.0))
        self.assertEqual((d['usage_scenario']['result'], d['usage_scenario']['share_of_base_result_percent']), (64680.0, 32.0))
        self.assertEqual(d['payback_status'], 'ok')
        self.assertEqual(d['running_cost_share_band'], 'mid')

    def test_cost_scenario_and_dials(self):
        d = bc()['data']
        self.assertEqual(d['cost_scenario']['effective_running_cost_per_year'], 36000.0)
        self.assertEqual(d['cost_scenario']['result'], 164400.0)
        self.assertEqual(d['dials'], {'usage_to_40_percent_loss': 271440.0, 'running_cost_plus_100_percent_loss': 72000.0, 'bigger': 'usage'})
        self.assertEqual(bc(p=10, l=100, n=50)['data']['dials']['bigger'], 'running_cost')
        self.assertEqual(bc(p=10, l=3, n=5)['data']['dials']['bigger'], 'equal')  # 0.6*5 == 3

    def test_five_year_horizon_and_currency_label(self):
        r = bc(years=5, currency='USD')
        self.assertEqual(r['data']['total_cost'], 300000.0)
        self.assertEqual(r['data']['total_benefit'], 754000.0)
        self.assertTrue(all('元' not in f for f in r['data']['formulas_zh']))
        self.assertTrue(any('USD' in f for f in r['data']['formulas_zh']))
        self.assertTrue(any('元' in f for f in bc()['data']['formulas_zh']))

    def test_share_bands_and_boundaries(self):
        # share = l*3 / (p + l*3)
        self.assertEqual(bc(p=300, l=33.33333333, n=500)['data']['running_cost_share_band'], 'low')   # 24.99...%
        self.assertEqual(bc(p=300, l=100, n=500)['data']['running_cost_share_band'], 'mid')            # exactly 50%
        self.assertEqual(bc(p=30, l=5, n=500)['data']['running_cost_share_percent'], 33.3)
        self.assertEqual(bc(p=3, l=1, n=500)['data']['running_cost_share_band'], 'mid')               # exactly 50%
        self.assertEqual(bc(p=2, l=1, n=500)['data']['running_cost_share_band'], 'mid')               # 60% exactly
        self.assertEqual(bc(p=1, l=1, n=500)['data']['running_cost_share_band'], 'high')              # 75%
        self.assertEqual(bc(p=9, l=1, n=500)['data']['running_cost_share_band'], 'mid')               # 25% exactly
        self.assertEqual(bc(p=10, l=1, n=500)['data']['running_cost_share_band'], 'low')
        r = bc(p=1, l=1, n=500)
        self.assertTrue(any('60%' in w for w in r['warnings_zh']))

    def test_payback_never_when_benefit_does_not_exceed_running_cost(self):
        for n in (100, 90):
            r = bc(p=1000, l=100, n=n)
            self.assertEqual(r['data']['payback_status'], 'never')
            self.assertIsNone(r['data']['payback_months'])
            self.assertTrue(any('永远收不回来' in w for w in r['warnings_zh']))
            self.assertTrue(any('永不' in f for f in r['data']['formulas_zh']))

    def test_payback_over_fifty_years(self):
        r = bc(p=100000, l=100, n=101)
        self.assertEqual(r['data']['payback_status'], 'over_50_years')
        self.assertGreater(r['data']['payback_months'], 600)
        self.assertTrue(any('超过 50 年' in w for w in r['warnings_zh']))

    def test_no_one_time_cost_pays_back_immediately(self):
        r = bc(p=0, l=100, n=500)
        self.assertEqual((r['data']['payback_months'], r['data']['payback_status']), (0.0, 'ok'))

    def test_zero_running_cost_flags_and_skips_break_even_overrun(self):
        r = bc(p=1000, l=0, n=500)
        self.assertIsNone(r['data']['break_even_cost_overrun_percent'])
        self.assertEqual(r['data']['running_cost_share_percent'], 0.0)
        self.assertTrue(any('上线后不产生任何成本' in w for w in r['warnings_zh']))
        self.assertEqual(r['data']['dials']['bigger'], 'usage')

    def test_negative_result_has_no_share_of_base_and_is_flagged(self):
        r = bc(p=500000, l=24000, n=100000)
        d = r['data']
        self.assertLess(d['result'], 0)
        self.assertIsNone(d['usage_scenario']['share_of_base_result_percent'])
        self.assertIsNone(d['cost_scenario']['share_of_base_result_percent'])
        self.assertLess(d['break_even_cost_overrun_percent'], 0)
        self.assertGreater(d['break_even_usage_percent'], 100)
        self.assertTrue(any('已经为负' in w for w in r['warnings_zh']))

    def test_custom_scenarios(self):
        d = bc(usage_ratio=0.5, running_cost_overrun_ratio=1)['data']
        self.assertEqual(d['usage_scenario']['effective_benefit_per_year'], 75400.0)
        self.assertEqual(d['cost_scenario']['effective_running_cost_per_year'], 48000.0)
        self.assertEqual(d['cost_scenario']['result'], 128400.0)

    def test_exact_arithmetic_has_no_float_noise(self):
        r = bc(p=0.1, l=0.1, n=0.2)
        self.assertEqual(r['data']['result'], 0.2)  # 0.6 - 0.1 - 0.3 in floats is 0.20000000000000004
        self.assertTrue(any('= 0.20 元' in f for f in r['data']['formulas_zh']))

    def test_every_formula_shows_substituted_numbers(self):
        for line in bc()['data']['formulas_zh']:
            self.assertRegex(line, r'\d')


class SafetyAndShapeTests(unittest.TestCase):
    def test_arguments_are_not_mutated_and_results_are_deterministic(self):
        args = {'lead_time_days': 42, 'day_type': 'calendar', 'touch_hours': 16, 'items_per_year': 12}
        before = json.dumps(args, sort_keys=True)
        first, second = call('flow_efficiency', args), call('flow_efficiency', args)
        self.assertEqual(json.dumps(args, sort_keys=True), before)
        self.assertEqual(first, second)

    def test_internal_errors_do_not_leak_details(self):
        def boom(values):
            raise RuntimeError('secret path C:/hidden')
        with patch.dict(m.RUNNERS, {'business_case': boom}):
            r = bc()
        self.assertEqual(code(r), 'INTERNAL_ERROR')
        self.assertNotIn('secret', json.dumps(r, ensure_ascii=False))
        self.assertIn('RuntimeError', r['error']['message'])

    def test_output_is_json_serialisable_and_chinese(self):
        for r in (fe(42, 'calendar', 16, items_per_year=5), bc()):
            json.dumps(r, ensure_ascii=False)
            self.assertTrue(HAN.search(r['message']))
            self.assertTrue(all(HAN.search(s) for s in r['summary_zh']))
            self.assertTrue(all(HAN.search(s) for s in r['data']['formulas_zh']))
            self.assertEqual(r['tool'][:10], 'flow_cost_')

    def test_message_forbids_benchmarks(self):
        self.assertIn('不要给出行业正常值', m.NOTE_ZH)

    def test_source_has_no_network_file_environment_process_clock_or_dynamic_execution(self):
        source = (PAYLOAD / 'tools/flow_cost.py').read_text(encoding='utf-8')
        forbidden = r'\b(socket|urllib|requests|httpx|http\.client|aiohttp|subprocess|ctypes|pickle|marshal|shutil|tempfile|datetime|time|random|os|sys|pathlib)\b|\bopen\(|\beval\(|\bexec\(|__import__|compile\('
        imports = [line for line in source.splitlines() if re.match(r'\s*(import|from)\s', line)]
        for line in imports:
            self.assertNotRegex(line, forbidden, line)
        body = '\n'.join(line for line in source.splitlines() if not re.match(r'\s*(import|from)\s', line) and not line.strip().startswith('#'))
        self.assertNotRegex(re.sub(r'"[^"\n]*"', '""', body), r'\bopen\(|\beval\(|\bexec\(|__import__|compile\(|\bos\.|\bsubprocess\b|\bsocket\b')

    def test_manifest_skills_tools_and_module_agree(self):
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual((manifest['package_type'], manifest['id'], manifest['version']), ('plugin', 'flow-cost-calculator', '1.0.0'))
        self.assertEqual({t['class'] for t in manifest['tools']}, {'FlowEfficiencyTool', 'BusinessCaseTool'})
        for item in manifest['tools']:
            self.assertTrue((PAYLOAD / item['file']).is_file())
            self.assertTrue(issubclass(getattr(m, item['class']), m.Tool))
        for item in manifest['skills']:
            skill = (PAYLOAD / item['dir'] / 'SKILL.md').read_text(encoding='utf-8')
            front = re.match(r'---\nname: ([^\n]+)\ndescription: [^\n]+\nversion: 1\.0\.0\n---\n', skill)
            self.assertIsNotNone(front, item)
            self.assertEqual(front.group(1), Path(item['dir']).name)
        skills = {Path(i['dir']).name: (PAYLOAD / i['dir'] / 'SKILL.md').read_text(encoding='utf-8') for i in manifest['skills']}
        self.assertIn('flow_cost_flow_efficiency', skills['flow-efficiency'])
        self.assertIn('flow_cost_business_case', skills['business-case-running-costs'])
        for text in skills.values():
            self.assertIn('不要给出', text)  # the "no normal values / rules of thumb" rule is stated

    def test_user_facing_files_are_utf8_without_bom_and_chinese(self):
        for path in PAYLOAD.rglob('*'):
            if not path.is_file():
                continue
            data = path.read_bytes()
            self.assertFalse(data.startswith(b'\xef\xbb\xbf'), path)
            text = data.decode('utf-8')
            self.assertNotIn('�', text, path)
            if path.name in ('README.md', 'SKILL.md', 'THIRD_PARTY_NOTICES.md', 'manifest.json'):
                self.assertTrue(HAN.search(text), path)
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        for key in ('name', 'description'):
            self.assertTrue(HAN.search(manifest[key]))
        for tag in manifest['tags']:
            self.assertTrue(HAN.search(tag['zh']) and tag['en'])
        for quick in manifest['quick_inputs']:
            self.assertTrue(HAN.search(quick['zh']))


class ControlExamplesInSkillsTests(unittest.TestCase):
    def test_the_check_examples_written_in_the_skills_match_the_tools(self):
        flow = (PAYLOAD / 'skills/flow-efficiency/SKILL.md').read_text(encoding='utf-8')
        case = (PAYLOAD / 'skills/business-case-running-costs/SKILL.md').read_text(encoding='utf-8')
        for fragment in ('83.3%', '6.7%', '232 小时', '128 小时'):
            self.assertIn(fragment, flow)
        for fragment in ('28.6%', '17.0 个月', '79.5%', '55.7%', '+278%', '64,680', '32%'):
            self.assertIn(fragment, case)
        d = fe(42, 'calendar', 16)['data']
        self.assertEqual((d['lever_a']['new_lead_time_working_days'] * 8, d['lever_b']['new_lead_time_working_days'] * 8), (232.0, 128.0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
