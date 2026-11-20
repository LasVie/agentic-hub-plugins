import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PAYLOAD = BASE / BASE.name


class StocktakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / '输入'
        self.data.mkdir()
        self.out = self.root / '输出'
        self.out.mkdir()
        self.write('book', 'sku,location,unit,at,quantity\n甲,A,件,2026-11-20T08:00:00+08:00,10\n乙,A,件,2026-11-20T08:00:00+08:00,15\n丙,B,件,2026-11-20T08:00:00+08:00,6\n')
        self.write('count', 'sku,location,unit,at,quantity\n甲,A,件,2026-11-20T10:00:00+08:00,13\n乙,A,件,2026-11-20T10:00:00+08:00,11\n丙,B,件,2026-11-20T10:00:00+08:00,6\n')
        self.write('moves', 'id,sku,location,unit,at,delta\nold,甲,A,件,2026-11-20T00:00:00Z,7\nin,甲,A,件,2026-11-20T02:00:00Z,3\nlate,甲,A,件,2026-11-20T02:00:01Z,9\nout,乙,A,件,2026-11-20T01:00:00Z,-2\n')

    def write(self, name, text):
        (self.data / f'{name}.csv').write_text(text, encoding='utf-8')

    def run_stage(self, stage, *, success=True, confirm=True):
        cmd = [sys.executable, str(PAYLOAD / 'scripts' / 'stocktake.py'), stage, str(self.data), str(self.out)]
        if confirm:
            cmd.append('--confirmed')
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', env={**__import__('os').environ, 'PYTHONUTF8':'1'})
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def stages(self):
        for stage in ('inspect', 'baseline', 'reconcile'):
            self.run_stage(stage)

    def test_delivers_exceptions_and_checks_both_cutoffs(self):
        self.stages()
        self.run_stage('deliver')
        with (self.out / 'exceptions.csv').open(encoding='utf-8-sig', newline='') as fh:
            rows = {r['商品编码']: r for r in csv.DictReader(fh)}
        self.assertEqual(set(rows), {'甲', '乙'})
        self.assertEqual((rows['甲']['分类'], rows['甲']['纳入流水编号']), ('时点差异已解释', 'in'))
        self.assertEqual((rows['乙']['分类'], rows['乙']['剩余差异']), ('建议复盘', '-2'))
        self.assertIn('独立复核', (self.out / 'review.md').read_text(encoding='utf-8'))

    def test_requires_confirmed_coverage(self):
        self.assertIn('完整', self.run_stage('inspect', success=False, confirm=False).stderr)

    def test_rejects_duplicate_movement_id(self):
        with (self.data / 'moves.csv').open('a', encoding='utf-8') as fh:
            fh.write('in,乙,A,件,2026-11-20T01:00:00Z,1\n')
        self.assertIn('重复', self.run_stage('inspect', success=False).stderr)

    def test_rejects_unit_mismatch(self):
        path = self.data / 'count.csv'
        self.write('count', path.read_text(encoding='utf-8').replace('甲,A,件', '甲,A,箱'))
        self.assertIn('单位', self.run_stage('inspect', success=False).stderr)

    def test_rejects_missing_count(self):
        path = self.data / 'count.csv'
        self.write('count', '\n'.join(path.read_text(encoding='utf-8').splitlines()[:-1])+'\n')
        self.assertIn('缺少', self.run_stage('inspect', success=False).stderr)

    def test_rejects_naive_timestamp(self):
        path = self.data / 'count.csv'
        self.write('count', path.read_text(encoding='utf-8').replace('+08:00', ''))
        self.assertIn('时区', self.run_stage('inspect', success=False).stderr)

    def test_refuses_altered_intermediate(self):
        self.stages()
        path = self.out / 'reconcile.json'
        report = json.loads(path.read_text(encoding='utf-8'))
        report['rows'][0]['residual'] += 1
        path.write_text(json.dumps(report), encoding='utf-8')
        self.assertIn('不一致', self.run_stage('deliver', success=False).stderr)
        self.assertFalse((self.out / 'exceptions.csv').exists())

    def test_refuses_changed_sources(self):
        self.stages()
        with (self.data / 'moves.csv').open('a', encoding='utf-8') as fh:
            fh.write('more,乙,A,件,2026-11-20T01:00:00Z,1\n')
        self.assertIn('源文件', self.run_stage('deliver', success=False).stderr)
        self.assertFalse((self.out / 'review.md').exists())

    def test_refuses_duplicate_stage_output(self):
        self.run_stage('inspect')
        self.assertIn('已存在', self.run_stage('inspect', success=False).stderr)


if __name__ == '__main__':
    unittest.main()
