"""Read and edit the body of a specific Docs tab."""
import re
SLUG = "google-docs"
LABEL = "Google 文档连接器"
SCOPE = "https://www.googleapis.com/auth/documents"
BASE = "https://docs.googleapis.com/v1"


def all_tabs(tabs):
    for tab in tabs:
        yield tab
        yield from all_tabs(tab.get("childTabs", []))


def paragraphs(content):
    for entry in content:
        if paragraph := entry.get("paragraph"):
            yield paragraph
        if table := entry.get("table"):
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    yield from paragraphs(cell.get("content", []))
        if toc := entry.get("tableOfContents"):
            yield from paragraphs(toc.get("content", []))


def tab_body(tab):
    return tab.get("documentTab", {}).get("body", {}).get("content", [])


def get(api, value):
    from google_api import file_id

    ident = file_id(value, "documents")
    doc = api.json("GET", f"/documents/{ident}", params={"includeTabsContent": "true",
                   "suggestionsViewMode": "PREVIEW_WITHOUT_SUGGESTIONS", "fields": "documentId,title,revisionId,tabs"})
    return ident, doc, list(all_tabs(doc.get("tabs", [])))


def select(tabs, tab_id):
    from google_api import invalid

    # Docs supplies identifiers such as t.0; use the ID only in a JSON body.
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", tab_id):
        raise invalid("标签页标识无效。")
    ident = tab_id
    for tab in tabs:
        if tab["tabProperties"]["tabId"] == ident:
            return tab
    raise invalid("此文档没有指定标签页。")


def read(api, args):
    from google_api import max_chars

    limit = max_chars(args.max_chars)
    ident, doc, tabs = get(api, args.file)
    selected = [select(tabs, args.tab)] if args.tab else tabs[:1]
    collected = []
    truncated = False
    for tab in selected:
        for paragraph in paragraphs(tab_body(tab)):
            for element in paragraph.get("elements", []):
                content = element.get("textRun", {}).get("content", "")
                if len(content) > limit:
                    collected.append(content[:limit])
                    truncated = True
                    break
                collected.append(content)
                limit -= len(content)
            if truncated:
                break
    return {"document_id": ident, "title": doc["title"], "revision_id": doc.get("revisionId"),
            "tabs": [{"tab_id": t["tabProperties"]["tabId"], "title": t["tabProperties"]["title"]} for t in tabs],
            "tab_id": selected[0]["tabProperties"]["tabId"] if selected else None,
            "text": "".join(collected), "truncated": truncated}


def create(api, args):
    from google_api import text

    result = api.json("POST", "/documents", body={"title": text(args.title, "标题", 200)})
    return {"document_id": result["documentId"], "title": result["title"],
            "url": f"https://docs.google.com/document/d/{result['documentId']}/edit"}


def utf16(value):
    return len(value.encode("utf-16-le")) // 2


def edit(api, args):
    from google_api import Error, invalid, text

    ident, doc, tabs = get(api, args.file)
    tab = select(tabs, args.tab)
    current = doc.get("revisionId")
    if not current:
        raise Error("write_access_required", "需要此文档的编辑权限。")
    if current != args.revision:
        raise Error("revision_changed", "文档版本已变化，请重新读取指定标签页。")
    if args.action == "append":
        payload = [{"insertText": {"endOfSegmentLocation": {"tabId": args.tab},
                                   "text": "\n" + text(args.text, "追加段落", 8000, multiline=True)}}]
    else:
        old = text(args.old, "查找文字", 4000)
        new = text(args.new, "替换文字", 4000, allow_empty=True)
        matches = []
        for paragraph in paragraphs(tab_body(tab)):
            contiguous = ""
            start = end = None
            for item in paragraph.get("elements", []) + [{}]:
                run = item.get("textRun", {})
                position = item.get("startIndex")
                if run and position == end and end is not None:
                    contiguous += run["content"]
                    end = item["endIndex"]
                    continue
                if start is not None:
                    index = contiguous.find(old)
                    while index >= 0:
                        matches.append(start + utf16(contiguous[:index]))
                        index = contiguous.find(old, index + 1)
                contiguous = run.get("content", "")
                start, end = (position, item.get("endIndex")) if run else (None, None)
        if len(matches) != 1:
            raise invalid("请提供在该标签页正文中恰好出现一次的文字。")
        start = matches[0]
        payload = [{"deleteContentRange": {"range": {"tabId": args.tab, "startIndex": start,
                                                    "endIndex": start + utf16(old)}}}]
        if new:
            payload.append({"insertText": {"location": {"tabId": args.tab, "index": start}, "text": new}})
    result = api.json("POST", f"/documents/{ident}:batchUpdate",
                      body={"writeControl": {"requiredRevisionId": current}, "requests": payload})
    return {"document_id": ident, "tab_id": args.tab, "revision_id": result.get("writeControl", {}).get("requiredRevisionId"),
            "message": "指定标签页的写入已提交。请回读核对内容。"}


def register(commands):
    reader = commands.add_parser("read", help="列出标签页并读取正文")
    reader.set_defaults(operation=read)
    reader.add_argument("--file", required=True, help="文档编辑链接或标识")
    reader.add_argument("--tab", help="标签页标识，省略时读取第一个标签页")
    reader.add_argument("--max-chars", type=int, default=12000, help="正文字符上限")
    creation = commands.add_parser("create", help="新建文档")
    creation.set_defaults(operation=create)
    creation.add_argument("--title", required=True, help="文档标题")
    append = commands.add_parser("append", help="向指定标签页追加段落")
    replace = commands.add_parser("replace", help="替换标签页正文内唯一匹配的一处文字")
    for command in (append, replace):
        command.set_defaults(operation=edit)
        command.add_argument("--file", required=True, help="文档编辑链接或标识")
        command.add_argument("--tab", required=True, help="指定标签页标识")
        command.add_argument("--revision", required=True, help="最近读取的文档版本")
    append.add_argument("--text", required=True, help="要追加的段落")
    replace.add_argument("--old", required=True, help="唯一匹配的原文字")
    replace.add_argument("--new", required=True, help="替换文字")
