"""文档数字核对：功能测试（标准库 unittest；需要 openjiuwen SDK，因为工具类继承它的 Tool）。

在仓库根目录运行（使用装有 openjiuwen 的 Python）：
    python -B -m unittest discover -s plugins/adds-up/tests -v

测试对象是插件载荷里的真实文件 plugins/adds-up/adds-up/tools/adds_up.py，不是模拟。
"""
import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = ASSET / "adds-up"
spec = importlib.util.spec_from_file_location("adds_up_under_test", PAYLOAD / "tools" / "adds_up.py")
au = importlib.util.module_from_spec(spec)
spec.loader.exec_module(au)


def leads_for(rows, conv="us", **kw):
    au.FMT["conv"] = conv
    au.FMT["group"] = True
    return au.check_table(au.Table("T1", rows, **kw), conv)


def kinds(leads, strength=None):
    return sorted(x["kind"] for x in leads if strength is None or x["strength"] == strength)


def has_cjk(text):
    return any("一" <= ch <= "鿿" for ch in text)


class Numbers(unittest.TestCase):
    def val(self, text, conv="us"):
        n = au.parse_cell(text, conv)
        return None if n is None else n.value

    def test_plain_grouped_and_chinese_units(self):
        self.assertEqual(self.val("1,234.56"), Decimal("1234.56"))
        self.assertEqual(self.val("1.234,56"), Decimal("1234.56"))
        self.assertEqual(self.val("¥ 1,200"), Decimal("1200"))
        self.assertEqual(self.val("￥1,200.50"), Decimal("1200.50"))
        self.assertEqual(self.val("1,200元"), Decimal("1200"))
        self.assertEqual(self.val("人民币 3,000"), Decimal("3000"))
        self.assertEqual(self.val("（700）"), Decimal("-700"))

    def test_fullwidth_percent(self):
        n = au.parse_cell("37.5％")
        self.assertTrue(n.pct)
        self.assertEqual(n.decimals, 1)

    def test_chinese_dates_and_labels_are_not_numbers(self):
        for text in ("2026年3月5日", "2026年3月", "3月5日", "3月", "12月份", "5日", "5号", "第一季度"):
            self.assertIsNone(au.parse_cell(text), text)

    def test_year_label_is_yearlike(self):
        for text in ("2025年", "2025年度"):
            n = au.parse_cell(text)
            self.assertIsNotNone(n, text)
            self.assertTrue(n.yearlike, text)
            self.assertEqual(n.value, Decimal(2025))


class ChineseTables(unittest.TestCase):
    def test_correct_table_is_silent(self):
        rows = [["区域", "一季度", "二季度", "合计"], ["华东", "100", "120", "220"], ["华南", "80", "90", "170"],
                ["合计", "180", "210", "390"]]
        self.assertEqual(leads_for(rows), [])

    def test_wrong_total_row(self):
        rows = [["区域", "一季度", "二季度"], ["华东", "100", "120"], ["华南", "80", "90"], ["合计", "180", "220"]]
        leads = leads_for(rows)
        self.assertEqual(kinds(leads), ["total-row"])
        self.assertEqual(leads[0]["where"], "T1 R4 C3")
        self.assertIn("210", leads[0]["message"])
        self.assertTrue(has_cjk(leads[0]["message"]))
        self.assertIn("显示 220", leads[0]["message"])

    def test_other_total_words(self):
        for word in ("总计", "共计", "总额", "汇总", "销售合计", "本月合计"):
            rows = [["项目", "金额"], ["设备", "100"], ["服务", "200"], [word, "310"]]
            self.assertEqual(kinds(leads_for(rows)), ["total-row"], word)

    def test_subtotals_and_grand_total(self):
        rows = [["项目", "费用"], ["电脑", "900"], ["显示器", "300"], ["硬件小计", "1,200"],
                ["软件许可", "250"], ["技术支持", "150"], ["软件小计", "400"], ["总计", "1,600"]]
        self.assertEqual(leads_for(rows), [])
        rows[-1][1] = "1,700"
        self.assertEqual(kinds(leads_for(rows)), ["total-row"])

    def test_of_which_rows_are_not_parts(self):
        rows = [["地区", "销售额"], ["欧洲", "500"], ["其中：德国", "200"], ["亚洲", "300"], ["合计", "800"]]
        self.assertEqual(leads_for(rows), [])

    def test_average_row(self):
        rows = [["班级", "分数"], ["一班", "80"], ["二班", "90"], ["三班", "100"], ["平均分", "95"]]
        self.assertEqual(kinds(leads_for(rows)), ["average-row"])
        rows[-1][1] = "90"
        self.assertEqual(leads_for(rows), [])

    def test_total_column(self):
        rows = [["门店", "一月", "二月", "三月", "合计"], ["甲", "10", "20", "30", "60"], ["乙", "15", "25", "35", "75"],
                ["丙", "20", "30", "40", "100"]]    # 只有“丙”的合计错了（应为 90）
        leads = leads_for(rows)
        self.assertEqual(kinds(leads), ["total-column"])
        self.assertEqual(leads[0]["where"], "T1 R4 C5")

    def test_total_planning_label_is_not_a_total(self):
        rows = [["项目", "金额"], ["设备", "100"], ["服务", "200"], ["总计划投入", "500"]]
        self.assertEqual(leads_for(rows), [])

    def test_year_headers_are_not_summed(self):
        rows = [["项目", "2024年", "2025年"], ["收入", "100", "120"], ["成本", "60", "70"], ["利润", "40", "50"]]
        self.assertEqual(leads_for(rows), [])

    def test_month_label_column_is_not_summed(self):
        rows = [["月份", "销售额"], ["1月", "100"], ["2月", "120"], ["3月", "130"], ["合计", "350"]]
        self.assertEqual(leads_for(rows), [])
        rows[-1][1] = "360"
        self.assertEqual(kinds(leads_for(rows)), ["total-row"])

    def test_tax_row_with_fullwidth_percent(self):
        rows = [["项目", "金额"], ["货物", "1,000.00"], ["服务", "500.00"], ["小计", "1,500.00"],
                ["增值税（13％）", "195.00"], ["合计", "1,695.00"]]
        self.assertEqual(leads_for(rows), [])
        rows[4][1] = "205.00"
        self.assertIn("rate-row", kinds(leads_for(rows)))

    def test_share_column(self):
        rows = [["区域", "人数", "占比"], ["甲", "50", "25%"], ["乙", "100", "50%"], ["丙", "25", "12.5%"], ["丁", "25", "20%"]]
        self.assertIn("share", kinds(leads_for(rows)))

    def test_english_and_german_labels_still_work(self):
        rows = [["Item", "Q1", "Q2"], ["A", "100", "200"], ["B", "300", "400"], ["Total", "400", "650"]]
        self.assertEqual(kinds(leads_for(rows)), ["total-row"])
        rows = [["Position", "Betrag"], ["A", "1.250,00 €"], ["B", "708,00 €"], ["C", "850,00 €"], ["Summe", "2.818,00 €"]]
        self.assertEqual(kinds(leads_for(rows, "eu")), ["total-row"])

    def test_messages_are_chinese(self):
        rows = [["项目", "单位", "金额"], ["甲", "10 mg", "5"], ["乙", "20 g", "6"], ["丙", "30 mg", "7"]]
        for ld in leads_for(rows):
            self.assertTrue(has_cjk(ld["message"]), ld["message"])


class ChineseProse(unittest.TestCase):
    def check(self, text):
        return au.check_prose([("L1", text)])

    def test_weekday_after_the_date(self):
        self.assertEqual(self.check("会议安排在2026年3月5日（星期四）举行。"), [])
        leads = self.check("会议安排在2026年3月5日（星期三）举行。")
        self.assertEqual(kinds(leads), ["weekday"])
        self.assertIn("星期四", leads[0]["message"])
        self.assertIn("不是星期三", leads[0]["message"])
        self.assertIn("）", leads[0]["message"].split("：")[0])    # 引文里带着右括号

    def test_weekday_before_the_date_and_short_forms(self):
        self.assertEqual(self.check("周四 2026年3月5日 开会"), [])
        self.assertEqual(kinds(self.check("星期三，2026年3月5日开会")), ["weekday"])
        self.assertEqual(kinds(self.check("2026年3月8日（周日）和2026年3月9日（周六）")), ["weekday"])     # 3月8日是周日，3月9日是周一
        self.assertEqual(self.check("2026年3月8日（星期天）"), [])

    def test_impossible_date(self):
        leads = self.check("会议定在2026年2月30日举行。")
        self.assertEqual(kinds(leads), ["date"])
        self.assertIn("不是日历上存在的日期", leads[0]["message"])
        self.assertEqual(self.check("会议定在2026年2月28日举行。"), [])

    def test_durations(self):
        self.assertEqual(self.check("为期2026年3月1日至2026年5月31日，共13周。"), [])
        leads = self.check("为期2026年3月1日至2026年5月31日，共14周。")
        self.assertEqual(kinds(leads), ["duration"])
        self.assertIn("91 天", leads[0]["message"])
        self.assertEqual(self.check("2026年3月1日到2026年3月31日，共30天"), [])
        self.assertEqual(kinds(self.check("2026年3月1日到2026年3月31日，共40天")), ["duration"])
        self.assertEqual(self.check("2026年3月1日至2026年5月31日，共3个月"), [])
        self.assertEqual(kinds(self.check("2026年5月31日至2026年3月1日，共13周")), ["duration"])    # 结束早于开始

    def test_a_day_of_month_after_the_end_date_is_not_a_duration(self):
        self.assertEqual(self.check("2026年3月1日至2026年3月31日，并在4月5日汇报。"), [])

    def test_n_of_N(self):
        self.assertEqual(self.check("240 人中有 156 人，占 65%"), [])
        leads = self.check("240 人中有 156 人，占 62%")
        self.assertEqual(kinds(leads), ["n-of-N"])
        self.assertIn("65.0%", leads[0]["message"])
        self.assertEqual(kinds(self.check("通过考核的有 156/240（62％）")), ["n-of-N"])
        self.assertEqual(self.check("通过考核的有 156/240（65％）"), [])

    def test_percentage_points(self):
        leads = self.check("满意度从 12% 升至 15%，增长 3%。")
        self.assertEqual(kinds(leads), ["percentage-points"])
        self.assertIn("3 个百分点", leads[0]["message"])
        self.assertEqual(self.check("满意度从 12% 升至 15%，增长 25%。"), [])
        self.assertEqual(self.check("满意度从 12％ 升至 15％，增长 3 个百分点。"), [])

    def test_english_prose_still_works(self):
        self.assertEqual(kinds(self.check("The meeting is on Wednesday, 5 March 2026.")), ["weekday"])
        self.assertEqual(kinds(self.check("12 of 40 (25%) agreed.")), ["n-of-N"])


class Grim(unittest.TestCase):
    def test_percent(self):
        matches, near, dec = au.grim(12, "37.5", True)
        self.assertEqual(matches, [])
        self.assertEqual(dec, 1)
        matches, _, _ = au.grim(12, "33.3", True)
        self.assertEqual(matches, [4])

    def test_mean(self):
        self.assertEqual(au.grim(25, "3.48", False)[0], [87])
        self.assertEqual(au.grim(25, "3.47", False)[0], [])

    def test_chinese_report(self):
        text = au.run_grim(25, "3.47", False)
        self.assertIn("不可能", text)
        self.assertIn("3.48", text)
        text = au.run_grim(12, "33.3", True)
        self.assertIn("相符", text)
        self.assertTrue(has_cjk(text))


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path


OOXML_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def make_docx(path, blocks):
    """blocks: ("p", 文字) 或 ("t", [[单元格, ...], ...])；最小但合法的 OOXML 文档。"""
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = []
    for kind, value in blocks:
        if kind == "p":
            body.append('<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % escape(value))
        else:
            rows = "".join("<w:tr>%s</w:tr>" % "".join(
                "<w:tc><w:p><w:r><w:t>%s</w:t></w:r></w:p></w:tc>" % escape(c) for c in row) for row in value)
            body.append("<w:tbl>%s</w:tbl>" % rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                   "</Types>")
        z.writestr("_rels/.rels", '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" '
                                  'Target="word/document.xml"/></Relationships>' % (PKG_REL, OOXML_REL))
        z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                                        "<w:document %s><w:body>%s</w:body></w:document>" % (w, "".join(body)))
    return path


def make_xlsx(path, sheets, hidden=()):
    """sheets: {名称: [行, ...]}，单元格是文字、数字或 ("=公式", 值)；最小但合法的 OOXML 工作簿。"""
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        tags, rels, overrides = [], [], []
        for i, (title, rows) in enumerate(sheets.items(), 1):
            xml = []
            for r, row in enumerate(rows, 1):
                cells = []
                for c, v in enumerate(row):
                    ref = "%s%d" % (au.num_to_col(c + 1), r)
                    if v is None:
                        continue
                    if isinstance(v, tuple):
                        cells.append('<c r="%s"><f>%s</f><v>%s</v></c>' % (ref, escape(v[0].lstrip("=")), v[1]))
                    elif isinstance(v, str):
                        cells.append('<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (ref, escape(v)))
                    else:
                        cells.append('<c r="%s"><v>%s</v></c>' % (ref, v))
                xml.append('<row r="%d">%s</row>' % (r, "".join(cells)))
            z.writestr("xl/worksheets/sheet%d.xml" % i, "<worksheet %s><sheetData>%s</sheetData></worksheet>" % (ns, "".join(xml)))
            state = ' state="hidden"' if title in hidden else ""
            tags.append('<sheet name="%s" sheetId="%d"%s r:id="rId%d"/>' % (escape(title), i, state, i))
            rels.append('<Relationship Id="rId%d" Type="%s/worksheet" Target="worksheets/sheet%d.xml"/>' % (i, OOXML_REL, i))
            overrides.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % i)
        z.writestr("[Content_Types].xml",
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   "%s</Types>" % "".join(overrides))
        z.writestr("_rels/.rels", '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" '
                                  'Target="xl/workbook.xml"/></Relationships>' % (PKG_REL, OOXML_REL))
        z.writestr("xl/workbook.xml", '<workbook %s xmlns:r="%s"><sheets>%s</sheets></workbook>' % (ns, OOXML_REL, "".join(tags)))
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="%s">%s</Relationships>' % (PKG_REL, "".join(rels)))
    return path


def make_pptx(path, slides):
    """slides: [[文字, ...], ...]，每张幻灯片只有文本框；最小但合法的 OOXML 演示文稿。"""
    p = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        ids, rels = [], []
        for i, texts in enumerate(slides, 1):
            shapes = "".join('<p:sp><p:txBody><a:p><a:r><a:t>%s</a:t></a:r></a:p></p:txBody></p:sp>' % escape(t) for t in texts)
            z.writestr("ppt/slides/slide%d.xml" % i,
                       "<p:sld %s><p:cSld><p:spTree>%s</p:spTree></p:cSld></p:sld>" % (p, shapes))
            ids.append('<p:sldId id="%d" r:id="rId%d"/>' % (255 + i, i))
            rels.append('<Relationship Id="rId%d" Type="%s/slide" Target="slides/slide%d.xml"/>' % (i, OOXML_REL, i))
        z.writestr("ppt/presentation.xml", '<p:presentation %s xmlns:r="%s"><p:sldIdLst>%s</p:sldIdLst></p:presentation>' % (p, OOXML_REL, "".join(ids)))
        z.writestr("ppt/_rels/presentation.xml.rels", '<Relationships xmlns="%s">%s</Relationships>' % (PKG_REL, "".join(rels)))
        z.writestr("[Content_Types].xml",
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/></Types>')
        z.writestr("_rels/.rels", '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" '
                                  'Target="ppt/presentation.xml"/></Relationships>' % (PKG_REL, OOXML_REL))
    return path


def make_pdf(path, lines):
    """手工写一个最小的单页 PDF：中文字体用 STSong-Light + UniGB-UCS2-H（不嵌入字体），文字以 UTF-16BE 十六进制写入。"""
    stream, y = [], 780
    for line in lines:
        stream.append("BT /F1 12 Tf 1 0 0 1 72 %d Tm <%s> Tj ET" % (y, line.encode("utf-16-be").hex().upper()))
        y -= 20
    content = "\n".join(stream).encode("ascii")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Encoding /UniGB-UCS2-H /DescendantFonts [6 0 R] >>",
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 2 >> /DW 1000 >>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path, "wb") as fh:
        fh.write(bytes(out))
    return path


class Files(TempDirCase):
    @unittest.skipUnless(importlib.util.find_spec("pdfplumber"), "环境里没有 pdfplumber")
    def test_pdf_chinese_text_with_pdfplumber(self):
        path = make_pdf(os.path.join(self.dir, "报告.pdf"), ["项目 金额", "设备 1,200", "合计 2,100", "会议在2026年3月5日（星期三）举行。"])
        res = au.process(path)
        self.assertIsNone(res["error"])
        text = " ".join(b[2] for b in res["blocks"] if b[0] == "text")
        self.assertIn("会议在2026年3月5日（星期三）举行。", text)
        self.assertEqual(kinds(res["leads"]), ["weekday"])

    def test_csv_with_chinese_labels(self):
        path = self.write("sales.csv", "区域,一季度,二季度,合计\n华东,100,120,220\n华南,80,90,170\n合计,180,210,400\n")
        res = au.process(path)
        self.assertIsNone(res["error"])
        self.assertEqual(kinds(res["leads"]), ["total-row"])
        self.assertEqual(res["leads"][0]["where"], "D4")
        self.assertIn("390", res["leads"][0]["message"])
        self.assertTrue(has_cjk(res["held"]))

    def test_markdown_prose_and_table(self):
        path = self.write("r.md", "培训安排在2026年3月5日（星期三）。\n\n| 项目 | 金额 |\n|---|---|\n| 设备 | 100 |\n| 服务 | 200 |\n| 合计 | 310 |\n")
        res = au.process(path)
        self.assertEqual(kinds(res["leads"]), ["total-row", "weekday"])

    def test_unsupported_and_missing(self):
        path = self.write("old.doc", "x")
        self.assertIn("不支持的文件类型", au.process(path)["error"])
        text, results = au.run_extract([os.path.join(self.dir, "none.xlsx")])
        self.assertEqual(results[0]["error"], "找不到这个文件。")
        self.assertIn("错误：找不到这个文件。", text)

    def test_docx_table_and_text(self):
        path = make_docx(os.path.join(self.dir, "报价.docx"), [
            ("p", "报价单：培训安排在2026年3月5日（星期三）。"),
            ("t", [["项目", "数量", "单价", "金额"], ["培训费", "15", "480", "7,400"], ["教材费", "10", "20", "200"], ["合计", "", "", "7,600"]]),
        ])
        res = au.process(path)
        self.assertIsNone(res["error"])
        found = kinds(res["leads"])
        self.assertIn("weekday", found)
        self.assertTrue(any(n.startswith("已读取：") for n in res["notes"]))

    def test_docx_sum_mismatch(self):
        path = make_docx(os.path.join(self.dir, "预算.docx"), [
            ("t", [["科目", "金额"], ["设备", "1,200"], ["服务", "800"], ["差旅", "500"], ["合计", "2,600"]]),
        ])
        res = au.process(path)
        self.assertEqual(kinds(res["leads"]), ["total-row"])
        self.assertIn("2,500", res["leads"][0]["message"])

    def test_xlsx_sum_stops_short(self):
        path = make_xlsx(os.path.join(self.dir, "成本.xlsx"), {"成本": [
            ["项目", "一月"], ["房租", 100], ["电费", 50], ["水费", 25], ["合计", ("=SUM(B2:B3)", 150)]]})
        res = au.process(path)
        self.assertIsNone(res["error"])
        self.assertEqual(kinds(res["leads"]), ["sum-range", "total-row"])
        self.assertEqual(res["leads"][0]["where"], "成本!B5")
        self.assertTrue(has_cjk(res["leads"][0]["message"]))
        self.assertIn("只算到第 3 行", res["leads"][0]["message"])

    def test_xlsx_hidden_sheet_note(self):
        path = make_xlsx(os.path.join(self.dir, "h.xlsx"), {
            "汇总": [["项目", "值"], ["收入", ("=基础!B2", 10)]], "基础": [["项目", "值"], ["收入", 10]]}, hidden=("基础",))
        res = au.process(path)
        self.assertTrue(any("是隐藏的" in n for n in res["notes"]), res["notes"])

    def test_xlsx_text_number_is_named_as_the_cause(self):
        path = make_xlsx(os.path.join(self.dir, "t.xlsx"), {"成本": [
            ["中心", "一月", "二月", "三月", "一季度"],
            ["甲", 100, 110, 120, ("=SUM(B2:D2)", 330)],
            ["乙", 200, "210", 220, ("=SUM(B3:D3)", 420)],
            ["丙", 300, 310, 320, ("=SUM(B4:D4)", 930)],
            ["合计", ("=SUM(B2:B4)", 600), ("=SUM(C2:C4)", 420), ("=SUM(D2:D4)", 660), ("=SUM(E2:E4)", 1680)]]})
        res = au.process(path)
        by_cell = dict((x["where"], x) for x in res["leads"] if x["kind"] != "number-as-text")
        self.assertIn("原因在这个文本单元格", by_cell["成本!E3"]["message"])
        self.assertIn("number-as-text", kinds(res["leads"]))

    def test_pptx_text(self):
        path = make_pptx(os.path.join(self.dir, "汇报.pptx"), [["季度汇报"], ["会议在2026年2月30日举行"]])
        res = au.process(path)
        self.assertIsNone(res["error"])
        self.assertEqual(kinds(res["leads"]), ["date"])
        self.assertTrue(any(n.startswith("已读取：2 张幻灯片") for n in res["notes"]), res["notes"])

    def test_pdf_without_library_says_so(self):
        path = self.write("x.pdf", "%PDF-1.4\n")
        res = au.process(path)
        if res["error"] is None:       # 环境里没有 PDF 库时，应明说；有库时只要不崩溃
            self.assertTrue(res["notes"])

    def test_render_is_chinese(self):
        path = self.write("a.csv", "项目,金额\n甲,1\n乙,2\n合计,4\n")
        text, _ = au.run_extract([path])
        for heading in ("# 文档数字核对：提取结果", "## 文件 1：a.csv", "### 内容", "### 线索（1 条，按阅读顺序）", "### 规则覆盖了什么"):
            self.assertIn(heading, text)


class Safety(TempDirCase):
    def setUp(self):
        super().setUp()
        self.saved = (au.MAX_FILE_BYTES, au.MAX_ZIP_ENTRIES, au.MAX_ZIP_MEMBER_BYTES, au.MAX_ZIP_TOTAL_BYTES)
        self.addCleanup(self.restore)

    def restore(self):
        au.MAX_FILE_BYTES, au.MAX_ZIP_ENTRIES, au.MAX_ZIP_MEMBER_BYTES, au.MAX_ZIP_TOTAL_BYTES = self.saved

    def test_oversize_file_is_refused(self):
        path = self.write("big.csv", "a,b\n" + "1,2\n" * 100)
        au.MAX_FILE_BYTES = 50
        res = au.process(path)
        self.assertIn("上限", res["error"])
        self.assertEqual(res["blocks"], [])

    def test_too_many_zip_entries_are_refused(self):
        path = make_docx(os.path.join(self.dir, "a.docx"), [("p", "x")])
        au.MAX_ZIP_ENTRIES = 2
        self.assertIn("条目过多", au.process(path)["error"])

    def test_oversized_zip_member_is_refused(self):
        path = make_docx(os.path.join(self.dir, "a.docx"), [("p", "x" * 5000)])
        au.MAX_ZIP_MEMBER_BYTES = 1000
        self.assertIn("解压后过大", au.process(path)["error"])

    def test_zip_total_is_capped(self):
        path = make_docx(os.path.join(self.dir, "a.docx"), [("p", "x" * 500)])
        au.MAX_ZIP_TOTAL_BYTES = 800
        self.assertIn("总大小超过上限", au.process(path)["error"])

    def test_xml_with_doctype_or_entity_is_refused(self):
        path = make_docx(os.path.join(self.dir, "evil.docx"), [("p", "x")])
        for payload in ('<!DOCTYPE lolz [<!ENTITY a "aaaa">]>', '<!ENTITY a "aaaa">'):
            evil = os.path.join(self.dir, "evil2.docx")
            with zipfile.ZipFile(path) as src, zipfile.ZipFile(evil, "w") as dst:
                for info in src.infolist():
                    data = src.read(info.filename)
                    if info.filename == "word/document.xml":
                        data = data.replace(b"<w:document", payload.encode() + b"<w:document", 1)
                    dst.writestr(info.filename, data)
            res = au.process(evil)
            self.assertIn("DOCTYPE 或 ENTITY", res["error"], payload)
            os.remove(evil)

    def test_bad_zip_is_reported_without_crash(self):
        path = self.write("broken.docx", "not a zip")
        self.assertIn("不是有效的 Office 文件", au.process(path)["error"])

    def test_tool_never_writes(self):
        path = self.write("a.csv", "项目,金额\n甲,1\n乙,2\n合计,3\n")
        before = sorted(os.listdir(self.dir))
        au.run_extract([path])
        self.assertEqual(sorted(os.listdir(self.dir)), before)


def run(coro):
    return asyncio.run(coro)


class ToolWrapper(TempDirCase):
    def test_tool_cards(self):
        extract, grim = au.AddsUpExtractTool(), au.AddsUpGrimTool()
        self.assertEqual(extract.card.name, "adds_up_extract")
        self.assertEqual(grim.card.name, "adds_up_grim")
        for tool in (extract, grim):
            self.assertTrue(has_cjk(tool.card.description))
            self.assertFalse(tool.card.input_params["additionalProperties"])
        self.assertEqual(extract.card.input_params["required"], ["files"])
        self.assertEqual(sorted(grim.card.input_params["required"]), ["kind", "n", "value"])

    def test_invalid_arguments(self):
        tool = au.AddsUpExtractTool()
        for bad in ({}, {"files": []}, {"files": "a.csv"}, {"files": [1]}, {"files": [""]}, {"files": ["a.csv"], "extra": 1},
                    {"files": ["a.csv"], "max_rows": 0}, {"files": ["a.csv"], "max_rows": True},
                    {"files": ["a.csv"], "all_rows": "yes"}, {"files": ["x"] * 11}, {"files": ["a\x00b"]}):
            out = run(tool.invoke(bad))
            self.assertFalse(out["ok"], bad)
            self.assertEqual(out["error"]["code"], "INVALID_ARGUMENTS", bad)
            self.assertTrue(has_cjk(out["error"]["message"]), bad)
        grim = au.AddsUpGrimTool()
        for bad in ({"n": 0, "value": "1", "kind": "mean"}, {"n": 5, "value": "x", "kind": "mean"},
                    {"n": 5, "value": "120", "kind": "percent"}, {"n": 5, "value": "1", "kind": "other"},
                    {"n": 5.5, "value": "1", "kind": "mean"}, {"n": 5, "value": "-1", "kind": "mean"},
                    {"n": 5, "value": "1", "kind": "mean", "x": 1}, {"n": 2000000, "value": "1", "kind": "mean"}, "text"):
            out = run(grim.invoke(bad))
            self.assertEqual(out["error"]["code"], "INVALID_ARGUMENTS", bad)

    def test_extract_invoke(self):
        path = self.write("销售.csv", "区域,一季度,二季度\n华东,100,120\n华南,80,90\n合计,180,220\n")
        out = run(au.AddsUpExtractTool().invoke({"files": [path]}))
        self.assertTrue(out["ok"])
        self.assertEqual(out["tool"], "adds_up_extract")
        self.assertEqual(out["lead_count"], 1)
        self.assertFalse(out["truncated"])
        self.assertEqual(out["files"][0]["file"], "销售.csv")
        self.assertIn("210", out["report_text"])
        self.assertTrue(has_cjk(out["message"]))

    def test_all_files_failed(self):
        out = run(au.AddsUpExtractTool().invoke({"files": [os.path.join(self.dir, "none.csv"), self.write("x.doc", "x")]}))
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"]["code"], "ALL_FILES_FAILED")
        self.assertEqual(len(out["error"]["files"]), 2)

    def test_partial_failure_still_returns_the_good_file(self):
        good = self.write("a.csv", "项目,金额\n甲,1\n乙,2\n合计,3\n")
        out = run(au.AddsUpExtractTool().invoke({"files": [good, os.path.join(self.dir, "none.csv")]}))
        self.assertTrue(out["ok"])
        self.assertEqual([bool(f["error"]) for f in out["files"]], [False, True])

    def test_report_is_truncated_with_a_notice(self):
        path = self.write("a.csv", "项目,金额\n" + "".join("项%d,%d\n" % (i, i) for i in range(200)))
        saved = au.MAX_REPORT_CHARS
        au.MAX_REPORT_CHARS = 500
        try:
            out = run(au.AddsUpExtractTool().invoke({"files": [path], "all_rows": True}))
        finally:
            au.MAX_REPORT_CHARS = saved
        self.assertTrue(out["truncated"])
        self.assertIn("已在 500 个字符处截断", out["report_text"])

    def test_max_rows_and_all_rows(self):
        path = self.write("long.csv", "项目,金额\n" + "".join("项%d,%d\n" % (i, i) for i in range(1, 101)))
        short = run(au.AddsUpExtractTool().invoke({"files": [path], "max_rows": 10}))
        self.assertIn("没有打印", short["report_text"])
        full = run(au.AddsUpExtractTool().invoke({"files": [path], "all_rows": True}))
        self.assertNotIn("没有打印", full["report_text"])
        self.assertGreater(len(full["report_text"]), len(short["report_text"]))

    def test_grim_invoke(self):
        out = run(au.AddsUpGrimTool().invoke({"n": 25, "value": "3.47", "kind": "mean"}))
        self.assertTrue(out["ok"])
        self.assertFalse(out["consistent"])
        self.assertEqual(out["nearest"][0], {"count_or_total": 87, "gives": "3.48"})
        self.assertIn("不可能", "".join(out["result_zh"]))
        out = run(au.AddsUpGrimTool().invoke({"n": 12, "value": "33.3%", "kind": "percent"}))
        self.assertTrue(out["consistent"])
        self.assertEqual(out["matching_counts_or_totals"], [4])
        out = run(au.AddsUpGrimTool().invoke({"n": 12, "value": "33.3％", "kind": "percent"}))
        self.assertTrue(out["consistent"])

    def test_concurrent_calls_do_not_mix_state(self):
        a = self.write("eu.csv", "Position;Betrag\nA;1.250,00\nB;708,00\nSumme;1.960,00\n")
        b = self.write("us.csv", "项目,金额\n甲,1,250.00\n乙,708.00\n合计,1,960.00\n")

        async def both():
            tool = au.AddsUpExtractTool()
            return await asyncio.gather(*[tool.invoke({"files": [p]}) for p in (a, b, a, b)])

        outs = run(both())
        self.assertEqual([o["lead_count"] for o in outs], [o["lead_count"] for o in (outs[0], outs[1], outs[0], outs[1])])
        self.assertEqual(outs[0]["report_text"], outs[2]["report_text"])
        self.assertEqual(outs[1]["report_text"], outs[3]["report_text"])


class Package(unittest.TestCase):
    def test_manifest_matches_files(self):
        manifest = json.loads((PAYLOAD / "manifest.json").read_text(encoding="utf-8"))
        asset = json.loads((ASSET / "asset.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], asset["name"], "adds-up")
        self.assertEqual(manifest["version"], asset["version"])
        self.assertEqual(manifest["package_type"], "plugin")
        for entry in manifest["tools"]:
            self.assertTrue((PAYLOAD / entry["file"]).is_file())
            self.assertTrue(hasattr(au, entry["class"]))
        for entry in manifest["skills"]:
            self.assertTrue((PAYLOAD / entry["dir"] / "SKILL.md").is_file())
        for field in ("name", "description"):
            self.assertTrue(has_cjk(manifest[field]))

    def test_skill_frontmatter(self):
        text = (PAYLOAD / "skills" / "document-number-check" / "SKILL.md").read_text(encoding="utf-8")
        head = text.split("---")[1]
        self.assertIn("name: document-number-check", head)
        self.assertIn("adds_up_extract", head)
        self.assertIn("adds_up_grim", head)
        self.assertIn("adds_up_extract", text)
        self.assertIn("adds_up_grim", text)

    def test_license_evidence_matches_provenance(self):
        import hashlib
        provenance = json.loads((ASSET / "provenance.json").read_text(encoding="utf-8"))
        evidence = provenance["sources"][0]["license_evidence"][0]
        data = (PAYLOAD / evidence["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), evidence["sha256"])
        self.assertNotIn(b"\r", data)
        self.assertIn(b"Copyright (c) 2026 Murat Matur", data)

    def test_no_forbidden_files_in_payload(self):
        for path in PAYLOAD.rglob("*"):
            rel = path.relative_to(PAYLOAD).parts
            self.assertFalse(any(p in ("__pycache__", ".git", "venv", "node_modules") or p.endswith(".pyc") for p in rel), path)


if __name__ == "__main__":
    unittest.main()
