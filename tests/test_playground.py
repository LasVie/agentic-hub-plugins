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
    def test_pinned_templates_are_unmodified_and_every_record_matches(self):
        record = json.loads((ASSET / 'UPSTREAM_FILES.json').read_text(encoding='utf-8'))
        for item in record['files']:
            actual = hashlib.sha256((PAYLOAD / item['payload_path']).read_bytes()).hexdigest()
            self.assertEqual(actual, item['payload_sha256'], item['payload_path'])
            if item['payload_path'].startswith('templates/'):
                self.assertFalse(item['modified'])
                self.assertEqual(actual, item['upstream_sha256'])

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
