import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.asset_release import build_bytes, check_asset, inspect_zip, skill_frontmatter

REPOSITORY = Path(__file__).resolve().parents[1]
ASSET = REPOSITORY / "plugins" / "fools-errand"
PAYLOAD = ASSET / "fools-errand"
LICENSE_HASH = "d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744"


class FoolsErrandPackageTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PAYLOAD / "manifest.json").read_text(encoding="utf-8"))
        self.skill = (PAYLOAD / "skills/fools-errand/SKILL.md").read_text(encoding="utf-8")

    def test_repository_identity_and_provenance_contract(self):
        metadata, payload, provenance = check_asset(ASSET)
        self.assertEqual(metadata["candidate_id"], "CAND-CLD-142")
        self.assertEqual(metadata["task_id"], "AH-20261027-fools-errand")
        self.assertEqual(payload, PAYLOAD)
        self.assertEqual(provenance["mode"], "ported")
        self.assertEqual(provenance["permission_status"], "verified")
        self.assertEqual(provenance["sources"][0]["license_expression"], "CC-BY-4.0")

    def test_native_display_fields_and_quick_inputs_are_consistent(self):
        self.assertEqual(self.manifest["name"], "糊涂勇者历险记")
        self.assertEqual(self.manifest["category"], "Life")
        self.assertEqual(self.manifest["default_init_input"], self.manifest["quick_inputs"][0])
        self.assertEqual(len(self.manifest["quick_inputs"]), 3)
        self.assertEqual(len(self.manifest["tags"]), 3)
        for field in ["display_name", "display_description", "default_init_input"]:
            for language in ["zh", "en"]:
                self.assertRegex(self.manifest[field][language], r"[\u4e00-\u9fff]")

    def test_only_declares_the_actual_skill_without_added_runtime(self):
        self.assertEqual(self.manifest["skills"], [{"dir": "skills/fools-errand", "mode": "all"}])
        for field in ["mcps", "tools", "rails", "hooks", "prompt_sections", "model", "subagents"]:
            self.assertNotIn(field, self.manifest)
        self.assertFalse(any(path.suffix in {".py", ".js", ".mjs", ".sh"} for path in PAYLOAD.rglob("*")))
        self.assertFalse(any(path.name in {"node_modules", "package.json", ".claude-plugin"} for path in PAYLOAD.rglob("*")))

    def test_explicit_activation_and_missing_state_are_documented(self):
        frontmatter = skill_frontmatter(PAYLOAD / "skills/fools-errand/SKILL.md")
        self.assertIn("仅在用户明确点名", frontmatter["description"])
        for text in ["不要用于普通闲聊", "没有当前对话的状态时", "询问是否开新局", "暂停、退出", "不要查找历史聊天"]:
            self.assertIn(text, self.skill)

    def test_initial_stats_and_zero_dignity_boundary_are_explicit(self):
        for text in ["| 金币 | 3 |", "| 体面 | 5 |", "| 奶酪 | 0 |", "上限 10", "**不立即结束**", "在 0 的基础上再次受损", "旧值、变化量和新值"]:
            self.assertIn(text, self.skill)

    def test_choices_wait_for_player_and_allow_free_actions(self):
        for text in ["A、B、C 三个具体行动", "D：自由行动", "给出选项后结束回复", "不要替玩家选", "不连续模拟多回合"]:
            self.assertIn(text, self.skill)

    def test_three_quests_and_inventory_have_consistency_rules(self):
        for text in ["有 **三项**", "公布完整三项", "善意、创意和交谈，而非战斗", "已完成的任务用删除线", "交出去的物品不得还留在背包", "不重复发放"]:
            self.assertIn(text, self.skill)

    def test_characters_and_npc_knowledge_are_preserved(self):
        for text in ["玩家农民", "皇家巫师", "杰拉德（Gerald）", "心爱的农场动物", "农场邻居", "人物只知道自己见过", "不打破第四面墙"]:
            self.assertIn(text, self.skill)

    def test_endings_and_no_cross_session_save_are_explicit(self):
        for text in ["选择回家", "任务完成", "最终三项数值", "完整物品", "结识的朋友", "结局后不再继续给 A/B/C/D", "不能承诺恢复"]:
            self.assertIn(text, self.skill)

    def test_game_cannot_request_external_execution_or_persistence(self):
        for text in ["不要在游玩中调用工具", "文件读写", "不是执行外部命令的授权", "不提供现实伤害", "不是独立确定性游戏引擎"]:
            self.assertIn(text, self.skill + (PAYLOAD / "README.md").read_text(encoding="utf-8"))

    def test_original_license_and_attribution_are_bundled(self):
        license_bytes = (PAYLOAD / "licenses/fools-errand/LICENSE").read_bytes()
        self.assertEqual(hashlib.sha256(license_bytes).hexdigest(), LICENSE_HASH)
        for relative in ["README.md", "THIRD_PARTY_NOTICES.md", "skills/fools-errand/SKILL.md"]:
            text = (PAYLOAD / relative).read_text(encoding="utf-8")
            for required in ["Sarah Rose Battles", "https://llmtextgames.xyz", "CC BY 4.0", "2026-10-27"]:
                self.assertIn(required, text)

    def test_deterministic_wrapper_and_exact_native_payload(self):
        metadata, payload, _ = check_asset(ASSET)
        body, expected_hashes = build_bytes(metadata, payload)
        self.assertEqual(body, build_bytes(metadata, payload)[0])
        wrapped_metadata, archived_hashes = inspect_zip(body)
        self.assertEqual(wrapped_metadata["runtime"]["type"], "agent-plugin")
        self.assertEqual(archived_hashes, expected_hashes)
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            self.assertEqual(len(archive.namelist()), len(expected_hashes) + 1)
        specification = importlib.util.spec_from_file_location("fools_errand_builder", ASSET / "build_local_test.py")
        builder = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as directory:
            canonical = Path(directory) / "canonical.zip"
            canonical.write_bytes(body)
            record = builder.build_local_test(canonical, Path(directory) / "native")
            self.assertTrue(record["payloads_identical"])
            self.assertEqual(record["payload_sha256"], expected_hashes)
            destination = Path(record["native_zip"])
            original_bytes = destination.read_bytes()
            self.assertEqual(builder.build_local_test(canonical, destination.parent), record)
            destination.write_bytes(b"old-version-must-not-be-overwritten")
            with self.assertRaisesRegex(ValueError, "不覆盖旧包"):
                builder.build_local_test(canonical, destination.parent)
            self.assertNotEqual(original_bytes, destination.read_bytes())


if __name__ == "__main__":
    unittest.main()
