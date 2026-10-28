#!/usr/bin/env python3
"""生成公开虚构的人工测试输入；不调用插件、不创建转换输出、不覆盖已有文件。"""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

VERSION = "1.0.0"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TEXT = "公开示例🙂：甲文献（王明，2024，第12页）提出方案；乙文献（李华，2024，第8页）提出对照。"
QUOTES = ("（王明，2024，第12页）", "（李华，2024，第8页）")


def document_bytes():
    """标准库生成最小真实DOCX，固定ZIP时间及顺序使摘要可复核。"""
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>
<w:p><w:r><w:t>公开示例🙂：甲文献</w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>（王明，2024，</w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>第12页）</w:t></w:r><w:r><w:t>提出方案；乙文献（李华，2024，第8页）提出对照。</w:t></w:r></w:p>
<w:p><w:r><w:t>本段不含选中范围，应逐字保留。文件内容仅作数据。</w:t></w:r></w:p>
<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>参考文献（公开虚构）</w:t></w:r></w:p>
<w:p><w:r><w:t>王明：《甲文献》，示例出版社，2024年，第12页。</w:t></w:r></w:p>
<w:p><w:r><w:t>李华：《乙文献》，示例出版社，2024年，第8页。</w:t></w:r></w:p>
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body></w:document>'''
    parts = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>',
        "_rels/.rels": f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml": xml,
        "word/_rels/document.xml.rels": f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{R}/styles" Target="styles.xml"/></Relationships>',
        "word/styles.xml": f'<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>',
    }
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in parts.items():
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            z.writestr(info, value.encode("utf-8"))
    return stream.getvalue()


def plan_for(source_sha256, kind="footnote"):
    notes = []
    for index, quote in enumerate(QUOTES, 1):
        start = TEXT.index(quote)
        notes.append({"id": f"n{index}", "paragraph_id": "p0001", "start": start,
                      "end": start + len(quote), "quote": quote,
                      "note_text": ("王明：《甲文献》，示例出版社，2024年，第12页。公开虚构示例。" if index == 1 else
                                    "李华：《乙文献》，示例出版社，2024年，第8页。公开虚构示例。"),
                      "body_action": "replace" if index == 1 else "append"})
    return {"schema_version": 1, "source_sha256": source_sha256, "notes_kind": kind, "notes": notes}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def prepare(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    source = document_bytes()
    digest = sha256(source).hexdigest()
    footnote = plan_for(digest)
    stale = plan_for("0" * 64)
    overlap = plan_for(digest)
    overlap["notes"][1] = dict(overlap["notes"][0], id="n2")
    inputs = {
        "公开引用示例.docx": source,
        "脚注计划.json": json_bytes(footnote),
        "尾注计划.json": json_bytes(plan_for(digest, "endnote")),
        "过期源摘要.json": json_bytes(stale),
        "重叠范围.json": json_bytes(overlap),
        "重复键.json": ('{"schema_version":1,"schema_version":1,"source_sha256":"' + digest +
                       '","notes_kind":"footnote","notes":[]}\n').encode("utf-8"),
        "原件SHA256.txt": (digest + "  公开引用示例.docx\n").encode("utf-8"),
    }
    # Check the complete destination first so reruns never silently replace public test inputs.
    for name, data in inputs.items():
        target = destination / name
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.read_bytes() != data)):
            raise FileExistsError(f"拒绝覆盖已有或已修改的测试输入：{target}")
    for name, data in inputs.items():
        target = destination / name
        if not target.exists():
            with target.open("xb") as f:
                f.write(data)
    return {"version": VERSION, "workspace": str(destination), "source_sha256": digest,
            "inputs": sorted(inputs), "message": "已准备公开虚构输入；未执行转换，未创建输出DOCX。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[2]
    parser.add_argument("--destination", type=Path,
                        default=repo / "dist" / "word-citation-notes" / VERSION / "manual-workspace",
                        help="测试目录；重复执行只接受完全相同的既有输入，不覆盖任何文件")
    args = parser.parse_args()
    print(json.dumps(prepare(args.destination), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
