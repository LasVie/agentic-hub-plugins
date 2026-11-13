"""Bounded native Slides reads and revision-checked writes."""
import re
import uuid

SLUG = "google-slides"
LABEL = "Google 幻灯片连接器"
SCOPE = "https://www.googleapis.com/auth/presentations"
BASE = "https://slides.googleapis.com/v1"
FIELDS = "presentationId,title,revisionId,slides(objectId,pageElements)"


def shapes(elements):
    for element in elements:
        if shape := element.get("shape"):
            content = "".join(run.get("textRun", {}).get("content", "") for run in shape.get("text", {}).get("textElements", []))
            if content.strip():
                yield {"object_id": element["objectId"], "placeholder": shape.get("placeholder", {}).get("type"), "text": content}
        if group := element.get("elementGroup"):
            yield from shapes(group.get("children", []))
        if table := element.get("table"):
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    content = "".join(run.get("textRun", {}).get("content", "") for run in cell.get("text", {}).get("textElements", []))
                    if content.strip():
                        yield {"object_id": element["objectId"], "row": cell.get("location", {}).get("rowIndex", 0),
                               "column": cell.get("location", {}).get("columnIndex", 0), "text": content}


def get(api, value, fields=FIELDS):
    from google_api import file_id

    ident = file_id(value, "presentations")
    return ident, api.json("GET", f"/presentations/{ident}", params={"fields": fields})


def page_id(value):
    from google_api import invalid

    # Slides object IDs may contain a colon. IDs go in the JSON body.
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_:-]{0,49}", value):
        raise invalid("页面标识无效。")
    return value


def read(api, args):
    from google_api import invalid, max_chars

    limit = max_chars(args.max_chars)
    ident, deck = get(api, args.file)
    pages = [{"page_id": page["objectId"], "number": i} for i, page in enumerate(deck.get("slides", []), 1)]
    selected = deck.get("slides", [])
    if args.page:
        selected = [page for page in selected if page["objectId"] == page_id(args.page)]
        if not selected:
            raise invalid("此演示文稿没有指定页面。")
    results = []
    truncated = False
    for page in selected:
        entries = []
        for item in shapes(page.get("pageElements", [])):
            if not limit:
                truncated = True
                break
            content = item["text"]
            entries.append({**item, "text": content[:limit]})
            truncated |= len(content) > limit
            limit -= len(content[:limit])
        results.append({"page_id": page["objectId"], "elements": entries})
        if not limit:
            truncated |= len(results) < len(selected)
            break
    return {"presentation_id": ident, "title": deck["title"], "revision_id": deck.get("revisionId"),
            "pages": pages, "content": results, "truncated": truncated}


def create(api, args):
    from google_api import text

    result = api.json("POST", "/presentations", body={"title": text(args.title, "标题", 200)},
                      params={"fields": "presentationId,title,revisionId"})
    ident = result["presentationId"]
    return {**result, "url": f"https://docs.google.com/presentation/d/{ident}/edit"}


def revision(deck, expected):
    from google_api import Error

    current = deck.get("revisionId")
    if not current:
        raise Error("write_access_required", "需要此演示文稿的编辑权限。")
    if current != expected:
        raise Error("revision_changed", "演示文稿版本已变化，请重新读取页面。")
    return current


def append_page(api, args):
    from google_api import text

    title = text(args.title, "页面标题", 300)
    body = text(args.body, "页面正文", 4000, multiline=True)
    ident, deck = get(api, args.file, "presentationId,revisionId")
    current = revision(deck, args.revision)
    page = "slide_" + uuid.uuid4().hex
    title_id = "title_" + uuid.uuid4().hex
    body_id = "body_" + uuid.uuid4().hex
    requests = [{"createSlide": {
        "objectId": page,
        "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
        "placeholderIdMappings": [{"layoutPlaceholder": {"type": "TITLE", "index": 0}, "objectId": title_id},
                                  {"layoutPlaceholder": {"type": "BODY", "index": 0}, "objectId": body_id}],
    }}, {"insertText": {"objectId": title_id, "text": title}}, {"insertText": {"objectId": body_id, "text": body}}]
    result = api.json("POST", f"/presentations/{ident}:batchUpdate",
                      body={"requests": requests, "writeControl": {"requiredRevisionId": current}})
    return {"presentation_id": ident, "page_id": page, "revision_id": result.get("writeControl", {}).get("requiredRevisionId")}


def replace(api, args):
    from google_api import invalid, text

    old = text(args.old, "查找文字", 4000)
    new = text(args.new, "替换文字", 4000, allow_empty=True)
    page = page_id(args.page)
    ident, deck = get(api, args.file)
    current = revision(deck, args.revision)
    target = next((item for item in deck.get("slides", []) if item["objectId"] == page), None)
    if target is None:
        raise invalid("此演示文稿没有指定页面。")
    if not any(old in item["text"] for item in shapes(target.get("pageElements", []))):
        raise invalid("指定页没有要替换的文字。")
    request = {"replaceAllText": {"containsText": {"text": old, "matchCase": True},
                                  "replaceText": new, "pageObjectIds": [page]}}
    result = api.json("POST", f"/presentations/{ident}:batchUpdate",
                      body={"requests": [request], "writeControl": {"requiredRevisionId": current}})
    count = result.get("replies", [{}])[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    return {"presentation_id": ident, "page_id": page, "replacements": count}


def register(commands):
    reader = commands.add_parser("read", help="读取演示文稿或指定页面")
    reader.set_defaults(operation=read)
    reader.add_argument("--file", required=True, help="演示文稿链接或标识")
    reader.add_argument("--page", help="指定页面标识")
    reader.add_argument("--max-chars", type=int, default=12000, help="正文字符上限")
    creation = commands.add_parser("create", help="新建演示文稿")
    creation.set_defaults(operation=create)
    creation.add_argument("--title", required=True, help="演示文稿标题")
    add = commands.add_parser("append-page", help="新增一页标题和正文")
    add.set_defaults(operation=append_page)
    add.add_argument("--file", required=True, help="演示文稿链接或标识")
    add.add_argument("--revision", required=True, help="最近读取的演示文稿版本")
    add.add_argument("--title", required=True, help="页面标题")
    add.add_argument("--body", required=True, help="页面正文")
    change = commands.add_parser("replace", help="仅在指定页面替换匹配文字")
    change.set_defaults(operation=replace)
    change.add_argument("--file", required=True, help="演示文稿链接或标识")
    change.add_argument("--revision", required=True, help="最近读取的演示文稿版本")
    change.add_argument("--page", required=True, help="页面标识")
    change.add_argument("--old", required=True, help="原文字，区分大小写")
    change.add_argument("--new", required=True, help="替换文字")
