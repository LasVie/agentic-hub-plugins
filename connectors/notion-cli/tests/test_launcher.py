import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "notion_launcher", Path(__file__).resolve().parents[1] / "notion-cli" / "launcher.py"
)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)

PAGE = "624cc1d0-d0c0-4b57-87ba-8b3d263ebb1d"
PAGE_URL = "https://www.notion.so/Test-624cc1d0d0c04b5787ba8b3d263ebb1d"
LOGIN = "https://app.notion.com/workers/cli-login?challenge=example"


class LauncherTest(unittest.TestCase):
    def test_browser_login_output_requires_expected_origin_and_code(self):
        output = f"Open this URL:\n  {LOGIN}\nVerification code:\n  AZ9-38B\n"
        self.assertEqual(launcher.login_details(output), (LOGIN, "AZ9-38B"))
        with self.assertRaises(launcher.ConnectorError):
            launcher.login_details(output.replace("app.notion.com", "example.net"))
        with self.assertRaises(launcher.ConnectorError):
            launcher.login_details(output.replace("AZ9-38B", ""))

    def test_cli_does_not_inherit_notion_profile_or_token(self):
        with patch.dict(os.environ, {"NOTION_TOKEN": "example", "NTN_TOKEN": "example"}):
            env = launcher.ntn_environment(Path("connector-session"))
        self.assertEqual(env["NOTION_HOME"], "connector-session")
        self.assertEqual(env["NOTION_KEYRING"], "0")
        self.assertNotIn("NOTION_TOKEN", env)
        self.assertNotIn("NTN_TOKEN", env)

    def test_page_id_from_url_and_id(self):
        self.assertEqual(launcher.page_id(PAGE_URL + "?pvs=4"), PAGE)
        self.assertEqual(launcher.page_id(PAGE), PAGE)
        with self.assertRaises(launcher.ConnectorError):
            launcher.page_id(PAGE_URL.replace("www.notion.so", "example.net"))

    def test_title_search_returns_page_matches(self):
        page = {
            "id": PAGE, "url": PAGE_URL,
            "properties": {"title": {"type": "title", "title": [{"plain_text": "测试"}, {"plain_text": "页面"}]}},
        }
        with patch.object(launcher, "api", return_value={"results": [page], "has_more": True}) as api:
            found = launcher.search(None, None, "测试", 2)
        self.assertEqual(found, {"pages": [{"id": PAGE, "url": PAGE_URL, "title": "测试页面"}], "has_more": True})
        api.assert_called_once_with(None, None, "POST", "v1/search", {
            "query": "测试", "filter": {"property": "object", "value": "page"}, "page_size": 2,
        })

    def test_read_preserves_truncation(self):
        cases = [("text", True, True), ("x" * 20001, False, True), ("text", False, False)]
        for content, remote_truncated, expected in cases:
            with self.subTest(length=len(content), remote_truncated=remote_truncated):
                with patch.object(launcher, "api", return_value={"markdown": content, "truncated": remote_truncated}):
                    result = launcher.read(None, None, PAGE)
                self.assertEqual(result, {"page_id": PAGE, "markdown": content[:20000], "truncated": expected})

    def test_append_is_one_paragraph_and_reports_the_created_block(self):
        with patch.object(launcher, "api", return_value={"results": [{"id": "new-block"}]}) as api:
            self.assertEqual(launcher.append(None, None, PAGE, "回读标记"), {"page_id": PAGE, "block_id": "new-block"})
        api.assert_called_once_with(None, None, "PATCH", f"v1/blocks/{PAGE}/children", {
            "children": [{"type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "回读标记"}}],
            }}],
        })
        with self.assertRaises(launcher.ConnectorError):
            launcher.append(None, None, PAGE, "🧪" * 1001)
        with patch.object(launcher, "api", return_value={"results": []}):
            with self.assertRaises(launcher.ConnectorError):
                launcher.append(None, None, PAGE, "回读标记")


if __name__ == "__main__":
    unittest.main()
