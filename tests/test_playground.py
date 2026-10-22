"""Source provenance and shipped-reference checks for the Playground port."""
from pathlib import Path
import hashlib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'skills/playground'
PAYLOAD = ASSET / 'playground'


class PlaygroundSourceTests(unittest.TestCase):
    def test_translated_templates_preserve_source_hashes_and_match_payload_records(self):
        record = json.loads((ASSET / 'UPSTREAM_FILES.json').read_text(encoding='utf-8'))
        for item in record['files']:
            actual = hashlib.sha256((PAYLOAD / item['payload_path']).read_bytes()).hexdigest()
            self.assertEqual(actual, item['payload_sha256'], item['payload_path'])
            if item['payload_path'].startswith('templates/'):
                self.assertTrue(item['modified'])
                self.assertRegex(item['upstream_sha256'], r'^[0-9a-f]{64}$')
                self.assertNotEqual(actual, item['upstream_sha256'])
                text = (PAYLOAD / item['payload_path']).read_text(encoding='utf-8')
                self.assertIn('修改说明：2026-10-22', text)
                self.assertIn('Anthropic', text)
                self.assertIn('Apache-2.0', text)
                self.assertIn('中文', text)

    def test_instruction_examples_use_safe_text_and_chinese_failure_fallbacks(self):
        for name in ['data-explorer.md', 'diff-review.md', 'document-critique.md']:
            text = (PAYLOAD / 'templates' / name).read_text(encoding='utf-8')
            self.assertIn('textContent', text, name)
            self.assertNotRegex(text, r'\.innerHTML\s*=', name)
            self.assertIn('复制失败', text, name)
        critique = (PAYLOAD / 'templates/document-critique.md').read_text(encoding='utf-8')
        self.assertIn('已拒绝（仅供背景，不得执行）', critique)
        self.assertIn("s.status !== 'rejected'", critique)

    def test_template_references_resolve_from_the_skill_directory(self):
        skill = (PAYLOAD / 'SKILL.md').read_text(encoding='utf-8')
        references = set(re.findall(r'`(templates/[^`]+\.md)`', skill))
        shipped = {p.relative_to(PAYLOAD).as_posix() for p in (PAYLOAD / 'templates').glob('*.md')}
        self.assertEqual(references, shipped)
        self.assertTrue(references)
        for relative in references:
            self.assertTrue((PAYLOAD / relative).is_file())

    def test_license_evidence_and_modified_file_notice_are_present(self):
        provenance = json.loads((ASSET / 'provenance.json').read_text(encoding='utf-8'))
        self.assertEqual(provenance['mode'], 'ported')
        for source in provenance['sources']:
            for item in source['license_evidence']:
                self.assertEqual(hashlib.sha256((PAYLOAD / item['path']).read_bytes()).hexdigest(), item['sha256'])
        self.assertIn('Modified for Agentic Hub on 2026-10-22', (PAYLOAD / 'SKILL.md').read_text(encoding='utf-8'))
        self.assertTrue((PAYLOAD / 'THIRD_PARTY_NOTICES.md').is_file())


if __name__ == '__main__':
    unittest.main()
