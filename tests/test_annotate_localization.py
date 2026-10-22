import json
from pathlib import Path
import re
import unittest


PAYLOAD = Path(__file__).parents[1] / "plugins/annotate/annotate"


class AnnotateChinesePackageTests(unittest.TestCase):
    def test_localization_preserves_reviewed_dependency_versions(self):
        inventory = json.loads((PAYLOAD.parent / "DEPENDENCIES.json").read_text(encoding="utf-8"))
        lock = json.loads((PAYLOAD / "runtime/package-lock.json").read_text(encoding="utf-8"))
        expected = [(dependency["package"], dependency["version"]) for dependency in inventory["dependencies"]]
        actual = [(name[len("node_modules/"):], metadata["version"]) for name, metadata in lock["packages"].items() if name.startswith("node_modules/")]
        self.assertCountEqual(actual, expected)

    def test_manifest_displays_chinese_without_changing_identifiers(self):
        manifest = json.loads((PAYLOAD / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "annotate")
        self.assertEqual(manifest["version"], "1.0.3")
        self.assertEqual(manifest["package_type"], "plugin")
        self.assertEqual(manifest["display_name"]["zh"], "网页圈选与批注")
        for field in ("display_name", "display_description", "default_init_input"):
            for value in manifest[field].values():
                self.assertRegex(value, r"[\u4e00-\u9fff]")
        for suggestion in manifest["quick_inputs"]:
            for value in suggestion.values():
                self.assertRegex(value, r"[\u4e00-\u9fff]")

    def test_skill_instructions_default_to_chinese(self):
        skill = (PAYLOAD / "skills/annotate-feedback/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认用简体中文", skill)
        self.assertIn("发送给智能体", skill)
        self.assertIn("不要读取示例源码冒充看到了图片", skill)
        self.assertIn("name: annotate-feedback", skill)
        self.assertIn("version: 1.0.3", skill)

    def test_overlay_localizes_visible_controls_and_retains_wire_keys(self):
        overlay = (PAYLOAD / "runtime/server/overlay.js").read_text(encoding="utf-8")
        for label in ("发送给智能体", "智能体处理中", "全部完成", "矩形", "保存", "确认清空？", "粉色"):
            self.assertIn(label, overlay)
        for untranslated in ('label: "Send to Agent"', 'label: "Agent is on it"', 'title="Delete note"', 'aria-label="Undo"'):
            self.assertNotIn(untranslated, overlay)
        self.assertIn('id: "pink"', overlay)
        self.assertIn('data-act="send"', overlay)

    def test_server_human_descriptions_are_chinese(self):
        server = (PAYLOAD / "runtime/server/index.mjs").read_text(encoding="utf-8")
        descriptions = re.findall(r'description: "([^"\n]+)"', server)
        self.assertGreaterEqual(len(descriptions), 9)
        for description in descriptions:
            self.assertRegex(description, r"[\u4e00-\u9fff]")
        self.assertIn("默认使用简体中文", server)
        self.assertIn("网页批注 · 批次", server)
        self.assertIn('status: "empty"', server)
        self.assertIn('["working", "done", "skipped"]', server)

    def test_launcher_errors_are_chinese_and_license_is_unchanged(self):
        launcher = (PAYLOAD / "scripts/launch.py").read_text(encoding="utf-8")
        self.assertIn("首次使用正在初始化", launcher)
        self.assertIn("自动安装依赖失败", launcher)
        license_text = (PAYLOAD / "licenses/claude-annotate/LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Angelo Dini", license_text)
        self.assertIn("Permission is hereby granted", license_text)


if __name__ == "__main__":
    unittest.main()
