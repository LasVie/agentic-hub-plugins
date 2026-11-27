import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'survey-skip-logic-review-team'
SCRIPT = ROOT / 'scripts' / 'routing.py'
STEPS = ('baseline', 'analyze', 'verify', 'report')


def cli(step, spec, out):
    return subprocess.run([sys.executable, '-B', str(SCRIPT), step, str(spec), str(out)],
                          capture_output=True, encoding='utf-8')


class RoutingTest(unittest.TestCase):
    def test_complete_path_is_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            spec = out / 'input.json'
            spec.write_text(json.dumps({'start': 'q1', 'questions': {'q1': {'yes': 'END'}}}), encoding='utf-8')
            for step in STEPS:
                proc = cli(step, spec, out)
                self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('未发现结构性缺陷', (out / '报告.md').read_text(encoding='utf-8'))

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.out = Path(directory.name)
        self.spec = ROOT / 'examples' / '演示问卷.json'

    def run_steps(self, *steps):
        for step in steps:
            proc = cli(step, self.spec, self.out)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_demo_has_three_defect_categories_and_paths(self):
        self.run_steps(*STEPS)
        result = json.loads((self.out / 'analysis.json').read_text(encoding='utf-8'))['result']
        self.assertEqual(result['unreachable'], ['Q3'])
        self.assertEqual(result['broken'], [['Q2', '缺失分支', 'Q99', ['继续', '缺失分支']]])
        self.assertEqual(result['loops'], [['Q1', [], ['继续', '返回']], ['Q2', ['继续'], ['返回', '继续']]])
        report = (self.out / '报告.md').read_text(encoding='utf-8')
        self.assertIn('`继续` → `缺失分支`', report)
        self.assertIn('不表示所有作答都会困在循环中', report)

    def test_unreachable_cycle_is_not_treated_as_a_reachable_cycle(self):
        self.spec = self.out / 'custom.json'
        self.spec.write_text('{"start":"Q1","questions":{"Q1":{"结束":"END"},"Q2":{"循环":"Q2"}}}', encoding='utf-8')
        self.run_steps(*STEPS)
        evidence = json.loads((self.out / 'analysis.json').read_text(encoding='utf-8'))['result']
        self.assertEqual(evidence, dict(unreachable=['Q2'], broken=[], loops=[]))

    def test_duplicate_keys_are_rejected_without_baseline(self):
        self.spec = self.out / 'invalid.json'
        self.spec.write_text('{"start":"Q1","questions":{"Q1":{"是":"END","是":"Q1"}}}', encoding='utf-8')
        result = cli('baseline', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('重复键', result.stderr)
        self.assertFalse((self.out / 'baseline.json').exists())

    def test_preflight_rejects_duplicate_keys_before_writing_any_output(self):
        spec = self.out / 'invalid.json'
        spec.write_text('{"start":"Q1","questions":{"Q1":{"是":"END","是":"Q1"}}}', encoding='utf-8')
        out = self.out / 'results'
        out.mkdir()
        result = cli('validate', spec, out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('重复键', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(list(out.iterdir()), [])

    def test_preflight_accepts_structural_findings_without_writing_output(self):
        result = cli('validate', self.spec, self.out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('输入校验通过', result.stdout)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_preflight_stops_when_output_directory_is_not_empty(self):
        existing = self.out / '已有结果.txt'
        existing.write_text('保留', encoding='utf-8')
        result = cli('validate', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('输出目录非空', result.stderr)
        self.assertEqual(list(self.out.iterdir()), [existing])
        self.assertEqual(existing.read_text(encoding='utf-8'), '保留')

    def test_omitted_handoff_prevents_report(self):
        self.run_steps('baseline', 'analyze')
        self.assertEqual(cli('report', self.spec, self.out).returncode, 2)
        self.assertFalse((self.out / '报告.md').exists())

    def test_analysis_waits_for_baseline(self):
        result = cli('analyze', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('尚未生成独立基线', result.stderr)
        self.assertFalse((self.out / 'analysis.json').exists())

    def test_analysis_rejects_baseline_from_different_input(self):
        original = self.spec
        self.spec = self.out / 'changed.json'
        self.spec.write_bytes(original.read_bytes())
        self.run_steps('baseline')
        self.spec.write_bytes(original.read_bytes() + b'\n')
        result = cli('analyze', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('发生变化', result.stderr)
        self.assertFalse((self.out / 'analysis.json').exists())

    def test_wrong_answer_trace_blocks_independent_verification(self):
        self.run_steps('baseline', 'analyze')
        path = self.out / 'analysis.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['result']['broken'][0][-1] = ['退出', '缺失分支']
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        result = cli('verify', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('断链证据路径回放不一致', result.stderr)
        self.assertFalse((self.out / 'verification.json').exists())

    def test_changed_input_blocks_reuse_of_old_handoffs(self):
        original = self.spec
        self.spec = self.out / 'snapshot.json'
        self.spec.write_bytes(original.read_bytes())
        self.run_steps('baseline', 'analyze', 'verify')
        self.spec.write_bytes(original.read_bytes() + b'\n')
        result = cli('report', self.spec, self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('发生变化', result.stderr)
        self.assertFalse((self.out / '报告.md').exists())

    def test_existing_report_is_not_overwritten(self):
        self.run_steps(*STEPS)
        path = self.out / '报告.md'
        previous = path.read_bytes()
        self.assertEqual(cli('report', self.spec, self.out).returncode, 2)
        self.assertEqual(path.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()
