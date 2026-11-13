"""Focused contract regressions for the four Google Workspace packages."""
from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

CONNECTORS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CONNECTORS / "google-drive/google-drive"))
import google_api
import oauth


def service(name):
    slug = "google-" + name
    spec = spec_from_file_location(name, CONNECTORS / slug / slug / "service.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Fixture:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return next(self.responses)

    @contextmanager
    def response(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        yield SimpleNamespace(iter_content=lambda **_: iter(next(self.responses)))


class WorkspaceTest(unittest.TestCase):
    def test_google_links_never_fetch_external_urls(self):
        self.assertEqual(google_api.file_id("https://docs.google.com/presentation/d/abc/edit#slide=id.x", "presentations"), "abc")
        for bad in ["https://docs.google.com@other.example/document/d/abc/edit",
                    "https://docs.google.com/document/d/e/published/pub", "x/y", "https://drive.google.com:999/file/d/test/view"]:
            with self.assertRaises(oauth.Error):
                google_api.file_id(bad, "documents")

    def test_drive_search_escapes_chinese_filters_and_paginates(self):
        api = Fixture({"files": [{"name": "项目说明"}], "nextPageToken": "next", "incompleteSearch": True})
        result = service("drive").search(api, SimpleNamespace(name="张三'\\文档", kind="docs", folder="folder123",
            drive="shared123", modified_since="2026-11-12", page_token="page", limit=12))
        params = api.calls[0][2]["params"]
        self.assertIn("name contains '张三\\'\\\\文档'", params["q"])
        self.assertIn("'folder123' in parents", params["q"])
        self.assertEqual((params["corpora"], params["driveId"], params["pageToken"]), ("drive", "shared123", "page"))
        self.assertEqual(result["next_page_token"], "next")
        self.assertTrue(result["incomplete_search"])

    def test_download_keeps_existing_file_and_exports_native_doc(self):
        drive = service("drive")
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "周报.pdf"
            args = SimpleNamespace(file="test", output=file, format="pdf")
            api = Fixture({"mimeType": drive.MIMES["docs"]}, [b"%PDF-", b"mock"])
            self.assertEqual(drive.download(api, args)["bytes"], 9)
            self.assertEqual(file.read_bytes(), b"%PDF-mock")
            self.assertEqual(api.calls[-1], ("GET", "/files/test/export", {"params": {"mimeType": "application/pdf"}}))
            with self.assertRaises(oauth.Error):
                drive.download(api, args)
            self.assertEqual(file.read_bytes(), b"%PDF-mock")
            self.assertEqual(list(file.parent.iterdir()), [file])

    def test_slides_reads_and_restricts_edits_to_page_and_revision(self):
        slides = service("slides")
        shape = {"objectId": "title_id", "shape": {"placeholder": {"type": "TITLE"},
                 "text": {"textElements": [{"textRun": {"content": "中文幻灯片初稿\n"}}]}}}
        deck = {"title": "项目", "revisionId": "r1", "slides": [{"objectId": "page1", "pageElements": [shape]},
                {"objectId": "page:2", "pageElements": [shape]}]}
        read = slides.read(Fixture(deck), SimpleNamespace(file="deck", page="page:2", max_chars=120))
        self.assertEqual(read["content"][0]["elements"][0]["text"], "中文幻灯片初稿\n")
        args = SimpleNamespace(file="deck", page="page:2", old="初稿", new="完成", revision="r0")
        api = Fixture(deck)
        with self.assertRaisesRegex(oauth.Error, "版本"):
            slides.replace(api, args)
        self.assertEqual(len(api.calls), 1)
        args.revision = "r1"
        api = Fixture(deck, {"replies": [{"replaceAllText": {"occurrencesChanged": 1}}]})
        self.assertEqual(slides.replace(api, args)["replacements"], 1)
        request = api.calls[-1][2]["body"]
        self.assertEqual(request["writeControl"], {"requiredRevisionId": "r1"})
        self.assertEqual(request["requests"][0]["replaceAllText"]["pageObjectIds"], ["page:2"])

    def test_slides_append_writes_new_page_and_only_new_placeholders(self):
        api = Fixture({"revisionId": "r1"}, {})
        out = service("slides").append_page(api, SimpleNamespace(file="deck", revision="r1", title="标题", body="内容"))
        commands = api.calls[1][2]["body"]["requests"]
        self.assertEqual(commands[0]["createSlide"]["objectId"], out["page_id"])
        self.assertEqual([x["objectId"] for x in commands[0]["createSlide"]["placeholderIdMappings"]],
                         [x["insertText"]["objectId"] for x in commands[1:]])

    def test_docs_edits_unique_text_by_utf16_offsets_in_target_tab(self):
        docs = service("docs")
        tab = {"tabProperties": {"title": "中文子页", "tabId": "t.0"},
               "documentTab": {"body": {"content": [{"paragraph": {"elements": [
                   {"startIndex": 1, "endIndex": 5, "textRun": {"content": "🗒️旧"}},
                   {"startIndex": 5, "endIndex": 7, "textRun": {"content": "日期"}},
               ]}}]}}}
        doc = {"title": "文档", "revisionId": "r1", "tabs": [{"tabProperties": {"tabId": "parent", "title": "主"},
                "childTabs": [tab]}]}
        result = docs.read(Fixture(doc), SimpleNamespace(file="doc", tab="t.0", max_chars=120))
        self.assertEqual(result["text"], "🗒️旧日期")
        api = Fixture(doc, {})
        docs.edit(api, SimpleNamespace(action="replace", file="doc", tab="t.0", revision="r1", old="旧日期", new="新日期"))
        request = api.calls[-1][2]["body"]
        self.assertEqual(request["writeControl"]["requiredRevisionId"], "r1")
        self.assertEqual(request["requests"][0]["deleteContentRange"]["range"],
                         {"tabId": "t.0", "startIndex": 4, "endIndex": 7})
        self.assertEqual(request["requests"][1]["insertText"]["text"], "新日期")

    def test_sheets_protects_formulas_and_writes_raw_ranges(self):
        sheets = service("sheets")
        self.assertEqual(sheets.area("项目'统计", "b2:c2"), ("'项目''统计'!B2:C2", 1, 2))
        for name in ["A:A", "B2:A4", "A1:A5001", "A10:A1"]:
            with self.assertRaises(oauth.Error):
                sheets.area("项目", name)
        props = {"title": "项目", "sheetId": 8}
        formula = {"sheets": [{"properties": props, "data": [{"rowData": [{"values": [{"userEnteredValue": {"formulaValue": "=1+2"}}]}]}]}]}
        args = SimpleNamespace(file="sheet", tab="项目", range="A2:B2", values_json='[["=字面文本",7]]',
                               formulas=False, replace_formulas=False, action="update")
        api = Fixture(formula)
        with self.assertRaisesRegex(oauth.Error, "公式"):
            sheets.write(api, args)
        self.assertEqual(len(api.calls), 1)
        api = Fixture({"sheets": [{"properties": props}]}, {"updatedCells": 2})
        self.assertEqual(sheets.write(api, args)["updatedCells"], 2)
        self.assertEqual(api.calls[-1][2]["params"]["valueInputOption"], "RAW")
        args.formulas = True
        args.values_json = '[["=SUM(A1:A2)",7]]'
        api = Fixture({"sheets": [{"properties": props}]}, {"spreadsheetId": "sheet"})
        sheets.write(api, args)
        cell = api.calls[-1][2]["body"]["requests"][0]["updateCells"]
        self.assertEqual(cell["rows"][0]["values"], [{"userEnteredValue": {"formulaValue": "=SUM(A1:A2)"}},
                                                    {"userEnteredValue": {"numberValue": 7}}])

    def test_sheets_append_inserts_rows_without_parsing_text(self):
        args = SimpleNamespace(file="sheet", tab="项目", range="A1:B20", values_json='[["中文",4]]',
                               formulas=False, replace_formulas=False, action="append")
        api = Fixture({"updates": {"updatedRange": "'项目'!A5:B5"}})
        self.assertEqual(service("sheets").write(api, args)["updates"]["updatedRange"], "'项目'!A5:B5")
        self.assertEqual(api.calls[0][2]["params"]["insertDataOption"], "INSERT_ROWS")
        self.assertEqual(api.calls[0][2]["params"]["valueInputOption"], "RAW")

    def test_shared_client_keeps_card_authorizations_separate(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"WORKSWARM_GOOGLE_WORKSPACE_HOME": directory}):
            root = Path(directory)
            config = root / "desktop.json"
            client = {"installed": {"client_id": "fixture.apps.googleusercontent.com", "client_secret": "fixture-only",
                                   "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": oauth.TOKEN_URI}}
            config.write_text(json.dumps(client))
            oauth.configure(config)
            for slug in ("google-drive", "google-slides"):
                oauth.write(root / f"{slug}.token.json", {"session_id": slug, "client_id": client["installed"]["client_id"],
                    "token": "fixture-access", "refresh_token": "fixture-refresh", "scopes": [service(slug.split("-")[-1]).SCOPE]})
            self.assertTrue(oauth.status("google-drive", service("drive").SCOPE)["signed_in_local"])
            oauth.configure(config)
            oauth.sign_out("google-drive")
            self.assertTrue(oauth.status("google-slides", service("slides").SCOPE)["signed_in_local"])
            with self.assertRaises(oauth.Error):
                oauth.status("google-drive", service("drive").SCOPE)

    def test_rejects_non_desktop_and_redirected_credentials(self):
        for client in ({"web": {"client_id": "fixture"}}, {"installed": {"client_id": "fixture.apps.googleusercontent.com",
                    "client_secret": "fixture", "auth_uri": "https://other.example/auth", "token_uri": oauth.TOKEN_URI}}):
            with self.assertRaises(oauth.Error):
                oauth.validate_client(client)


if __name__ == "__main__":
    unittest.main()
