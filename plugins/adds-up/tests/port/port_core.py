"""Port upstream adds_up.py (pinned) to the Chinese edition used by the plugin.

Every replacement must match the pinned upstream exactly `count` times, otherwise the script stops.
Run:  python -B -I port_core.py <upstream adds_up.py> <output adds_up_core.py>
"""
import sys

src_path, out_path = sys.argv[1], sys.argv[2]
raw = open(src_path, "rb").read()
assert b"\r" not in raw, "upstream file has CR characters"
s = raw.decode("utf-8")
log = []


def R(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit("MISMATCH (found %d, expected %d):\n%s" % (n, count, old[:300]))
    s = s.replace(old, new)
    log.append(count)


# ---------------------------------------------------------------- header
head_end = s.index("import argparse")
HEADER = '''"""文档数字核对（核心）：从 Word、PowerPoint、Excel、CSV、Markdown、纯文本和 PDF 里取出文字、
表格和公式，并按规则列出“算术线索”，供复核人逐条确认。

来源与改动
- 本文件移植自上游 Adds Up 的 skills/check/scripts/adds_up.py（作者 Murat Matur，MIT 许可，
  固定提交 501af9e40e709780849cbedfd73af45d1eb7c6bd）。上游版权声明与 MIT 许可全文见同一插件内的
  THIRD_PARTY_NOTICES.md 和 licenses/adds-up/LICENSE。
- 本团队的改动（修改摘要，详见 SOURCE_REVIEW.md）：
  1. 增加中文支持：合计/小计/平均/其中等标签，“2026年3月5日”日期和“星期三/周三”星期，
     “共 14 周”之类的时长，全角百分号“％”，“N 人中有 n 人，占 p%”之类的占比说法，年份、月份表头。
  2. 把全部输出文字（线索、说明、错误、报告标题）改成简体中文。
  3. 增加安全上限：文件大小、压缩包条目数和解压后大小，并拒绝含 DOCTYPE / ENTITY 声明的 XML。
  4. 把命令行入口拆成可直接调用的函数 run_extract()、run_grim()，不再依赖命令行与标准输出；
     规则本身、数字解析和各类文件的提取逻辑保持上游原样。

只用 Python 标准库；不联网、不写任何文件。PDF 文字提取需要环境里已装 pdfplumber 或 pypdf，没有就会
明确说明，由使用者直接阅读 PDF。

“线索”只是候选，不是结论；每一条都必须对照文档确认后才能报告。
"""

from __future__ import annotations

'''
s = HEADER + s[head_end:]

# ---------------------------------------------------------------- safety helpers (after imports)
R('''from decimal import Decimal, InvalidOperation
''', '''from decimal import Decimal, InvalidOperation

# 安全上限（本团队新增）：防止超大文件、压缩炸弹和 XML 实体展开。
MAX_FILE_BYTES = 50 * 1024 * 1024          # 单个文件
MAX_ZIP_ENTRIES = 5000                     # Office 压缩包条目数
MAX_ZIP_MEMBER_BYTES = 80 * 1024 * 1024    # 压缩包内单个条目解压后大小
MAX_ZIP_TOTAL_BYTES = 300 * 1024 * 1024    # 压缩包内全部条目解压后总大小


def _open_zip(path):
    """打开 Office 压缩包，并先检查条目数和解压后大小。"""
    z = zipfile.ZipFile(path)
    infos = z.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        z.close()
        raise ValueError("压缩包条目过多（%d 个，上限 %d 个），不予读取。" % (len(infos), MAX_ZIP_ENTRIES))
    total = 0
    for info in infos:
        if info.file_size > MAX_ZIP_MEMBER_BYTES:
            z.close()
            raise ValueError("压缩包里有解压后过大的条目（%s），不予读取。" % info.filename)
        total += info.file_size
    if total > MAX_ZIP_TOTAL_BYTES:
        z.close()
        raise ValueError("压缩包解压后总大小超过上限，不予读取。")
    return z


def _safe_xml(data):
    """拒绝带 DOCTYPE 或 ENTITY 声明的 XML（实体展开攻击）；Office 文档的正常 XML 不含这两种声明。"""
    head = data[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in data.upper():
        raise ValueError("XML 含有 DOCTYPE 或 ENTITY 声明，不予读取。")
    return data
''')
R('''        return ET.fromstring(z.read(name))''', '''        return ET.fromstring(_safe_xml(z.read(name)))''')
R('''    with zipfile.ZipFile(path) as z:''', '''    with _open_zip(path) as z:''', count=3)

# ---------------------------------------------------------------- number parsing: Chinese units, dates, years
R('''CURRENCY_CHARS = "€$£¥₺₹₽₩"''', '''CURRENCY_CHARS = "€$£¥￥₺₹₽₩"''')
R('''"KRW|BRL|MXN|ZAR|AED|SAR|ILS|RUB|UAH|TL")''', '''"KRW|BRL|MXN|ZAR|AED|SAR|ILS|RUB|UAH|TL|人民币")''')
R('''    re.compile(r"^\\d{1,2}[./]\\d{1,2}\\.$"),
]''', '''    re.compile(r"^\\d{1,2}[./]\\d{1,2}\\.$"),
    # 中文日期、月份和日号单元格（本团队新增）：它们是标签，不是要参与求和的数。
    re.compile(r"^(?:19|20)\\d{2}\\s*年\\s*\\d{1,2}\\s*月\\s*\\d{1,2}\\s*[日号]$"),
    re.compile(r"^(?:19|20)\\d{2}\\s*年\\s*\\d{1,2}\\s*月(?:份)?$"),
    re.compile(r"^\\d{1,2}\\s*月\\s*\\d{1,2}\\s*[日号]$"),
    re.compile(r"^\\d{1,2}\\s*月(?:份)?$"),
    re.compile(r"^\\d{1,2}\\s*[日号]$"),
]''')
R('''    r"(%|‰|[" + re.escape(CURRENCY_CHARS) + r"]|(?:[^\\W\\d_]|[°µ])[^\\s\\d]{0,7})?$"''',
  '''    r"(%|％|‰|[" + re.escape(CURRENCY_CHARS) + r"]|(?:[^\\W\\d_]|[°µ])[^\\s\\d]{0,7})?$"''')
R('''    raw = s
    neg = False
    if s.startswith("(") and s.endswith(")"):''', '''    raw = s
    ym = re.fullmatch(r"((?:19|20)\\d{2})\\s*年(?:度)?", s)
    if ym:      # “2025年”“2025年度”是年份标签（本团队新增）
        return Num(Decimal(ym.group(1)), 0, False, "", raw, "plain", True)
    neg = False
    if s.startswith(("(", "（")) and s.endswith((")", "）")):''')
R('''    pct = tail == "%"''', '''    pct = tail in ("%", "％")''')

# ---------------------------------------------------------------- label regexes: add Chinese (Either wrapper)
R('''SUBTOTAL_RE = re.compile(''', '''_SUBTOTAL_EN = re.compile(''')
R('''TOTAL_RE = re.compile(
    r"\\b(grand''', '''_TOTAL_EN = re.compile(
    r"\\b(grand''')
R('''RATE_RE = re.compile(r"(?<![\\d.,])(\\d{1,2}(?:[.,]\\d{1,2})?)\\s?%")''',
  '''RATE_RE = re.compile(r"(?<![\\d.,])(\\d{1,2}(?:[.,]\\d{1,2})?)\\s?[%％]")''')
R('''AVG_RE = re.compile(
    r"(\\b(average''', '''_AVG_EN = re.compile(
    r"(\\b(average''')
R('''BARE_TOTAL_RE = re.compile(''', '''_BARE_TOTAL_EN = re.compile(''')
R('''BARE_AVG_RE = re.compile(''', '''_BARE_AVG_EN = re.compile(''')
R('''MEMO_RE = re.compile(''', '''_MEMO_EN = re.compile(''')
R('''SKIP_HEADER_RE = re.compile(
    r"^\\s*(id|no\\.?|nr\\.?|#|pos\\.?|item\\s*no\\.?|date|datum|tarih|code|kod|sku|ref\\.?)\\s*$", re.I)''',
  '''SKIP_HEADER_RE = re.compile(
    r"^\\s*(id|no\\.?|nr\\.?|#|pos\\.?|item\\s*no\\.?|date|datum|tarih|code|kod|sku|ref\\.?|"
    r"序号|编号|代码|代号|日期|行号|名次|排名|货号|订单号)\\s*$", re.I)''')
R('''SMALL_INT_HEADER_RE = re.compile(
    r"^\\s*(year|jahr|yıl|week|kw|month|monat|ay|age|alter|yaş|day|tag|gün)\\s*$", re.I)''',
  '''SMALL_INT_HEADER_RE = re.compile(
    r"^\\s*(year|jahr|yıl|week|kw|month|monat|ay|age|alter|yaş|day|tag|gün|"
    r"年|年份|年度|月|月份|周|周次|年龄|日)\\s*$", re.I)


class _Either(object):
    """把英文等原有规则和中文规则合成一个，保持 .search() / .match() 的用法不变。"""

    def __init__(self, *rxs):
        self.rxs = rxs

    def search(self, text):
        for rx in self.rxs:
            m = rx.search(text)
            if m:
                return m
        return None

    def match(self, text):
        for rx in self.rxs:
            m = rx.match(text)
            if m:
                return m
        return None


# 中文标签（本团队新增）。中文没有词边界，所以不用 \\b；“总计”后面不能紧跟“划/算/量”（避开“总计划”“总计算”）。
_SUBTOTAL_CN = re.compile(r"小\\s?计|分\\s?项\\s?合\\s?计")
_TOTAL_CN = re.compile(r"合\\s?计|总\\s?计(?![划算量])|总\\s?金?\\s?额|总\\s?和|共\\s?计|总\\s?数|汇\\s?总")
_AVG_CN = re.compile(r"平均\\s?(?:值|数)?|均\\s?值")
_BARE_TOTAL_CN = re.compile(
    r"^\\W*(?:合\\s?计|总\\s?计|总\\s?金?\\s?额|总\\s?和|共\\s?计|汇\\s?总|小\\s?计)"
    r"(?:\\s*[（(].*[）)]|\\s*(?:含税|不含税|税前|税后|金额|元|万元))?\\W*$")
_BARE_AVG_CN = re.compile(r"^\\W*(?:平均\\s?(?:值|数|分|成绩|得分|水平)?|均\\s?值|均\\s?分)(?:\\s*[（(].*[）)])?\\W*$")
_MEMO_CN = re.compile(r"^\\W*(?:其中|其\\s?中|内含|含|包括|包含)")
SUBTOTAL_RE = _Either(_SUBTOTAL_EN, _SUBTOTAL_CN)
TOTAL_RE = _Either(_TOTAL_EN, _TOTAL_CN)
AVG_RE = _Either(_AVG_EN, _AVG_CN)
BARE_TOTAL_RE = _Either(_BARE_TOTAL_EN, _BARE_TOTAL_CN)
BARE_AVG_RE = _Either(_BARE_AVG_EN, _BARE_AVG_CN)
MEMO_RE = _Either(_MEMO_EN, _MEMO_CN)

DESC_ZH = {
    "all detail rows above": "上面所有明细行",
    "detail rows since the previous total": "上一个合计行之后的明细行",
    "the subtotals": "各小计行",
    "the rows below": "下面的明细行",
}
AXIS_ZH = {"row": "行", "column": "列"}


def colref(t, c):
    """整列的位置标签（线索的 where 与阅读顺序共用同一写法）。"""
    return "%s %s" % (t.name, t.col_ids[c]) if t.joiner else "%s列 %s" % (t.name, t.col_ids[c])''')
R('''"%s %s" % (t.name, t.col_ids[c]) if t.joiner else "%scolumn %s" % (t.name, t.col_ids[c])''', '''colref(t, c)''', count=4)

# ---------------------------------------------------------------- Table helpers
R('''            return "%srow %s" % (self.name, self.row_ids[r])''', '''            return "%s第%s行" % (self.name, self.row_ids[r])''')
R('''        """Describe a set of row indexes compactly: 'R2 to R5', 'rows 2 to 12, 14, 17 to 30'."""
        if not rs:
            return "no rows"''', '''        """用简短的话描述一组行：“R2 至 R5”“第2 至 12、14、17 至 30行”。"""
        if not rs:
            return "没有行"''')
R('''        parts = [self.row_ids[x] if x == y else "%s to %s" % (self.row_ids[x], self.row_ids[y]) for x, y in runs]
        if len(parts) > 6:
            parts = parts[:5] + ["... %s" % parts[-1]]
        return ("rows " if self.joiner == "" else "") + ", ".join(parts)''',
  '''        parts = [self.row_ids[x] if x == y else "%s 至 %s" % (self.row_ids[x], self.row_ids[y]) for x, y in runs]
        if len(parts) > 6:
            parts = parts[:5] + ["…… %s" % parts[-1]]
        body = "、".join(parts)
        return ("第 " + body + " 行") if self.joiner == "" else body''')

# ---------------------------------------------------------------- check_table messages
R('''            return (" The gap equals %s, held as text, which SUM skips. The formula is right and the text "
                    "cell is the cause." % ", ".join("%s (%s)" % (t.ref(*rc), n.raw) for rc, n in hits))''',
  '''            return (" 差额等于以文本形式存放的 %s，而 SUM 会跳过文本。公式没有错，原因在这个文本单元格。"
                    % "、".join("%s（%s）" % (t.ref(*rc), n.raw) for rc, n in hits))''')
R('''    def gap_words(state, diff, n_parts, subject="The stated figure", ref="its parts give"):
        """(strength, sentence) for a figure that differs from what its parts give."""
        gap = "%s %s than %s" % (fmt(abs(diff)), "higher" if diff > 0 else "lower", ref)
        if state == "rounding":
            return "weak", ("%s is %s. Rounded parts commonly produce a gap this small; "
                            "it is an error only if the figures are exact." % (subject, gap))
        if state == "stretch":
            return "normal", ("%s is %s. Rounding could produce this only if nearly all %d parts "
                              "were rounded the same way, which is unlikely." % (subject, gap, n_parts))
        return "normal", "%s is %s, more than rounding can produce." % (subject, gap)''',
  '''    def gap_words(state, diff, n_parts, subject="所列数字", ref="各分项之和"):
        """(strength, sentence) for a figure that differs from what its parts give."""
        gap = "比%s%s %s" % (ref, "高" if diff > 0 else "低", fmt(abs(diff)))
        if state == "rounding":
            return "weak", ("%s%s。四舍五入的分项常常产生这么小的差额；"
                            "只有这些数字是精确值时才算错误。" % (subject, gap))
        if state == "stretch":
            return "normal", ("%s%s。只有几乎全部 %d 个分项都按同一方向四舍五入才会出现这种差额，"
                              "可能性不大。" % (subject, gap, n_parts))
        return "normal", "%s%s，超出了四舍五入能造成的范围。" % (subject, gap)''')
R('''        return ' ("%s")' % headers[c] if headers[c] else ""''', '''        return '（“%s”列）' % headers[c] if headers[c] else ""''')
R('''            return " The cell holds a formula: %s." % m["formula"]
        return " The cell holds a typed number, not a formula."''',
  '''            return " 该单元格是公式：%s。" % m["formula"]
        return " 该单元格是手工输入的数字，不是公式。"''')
# rate rows
R('''base, base_desc = nums[x][c].value, '"%s" (%s)' % (labels[x], nums[x][c].raw)''',
  '''base, base_desc = nums[x][c].value, '“%s”（%s）' % (labels[x], nums[x][c].raw)''')
R('''base_desc = "the sum of %s (%s)" % (t.span(rs), fmt(base))''', '''base_desc = "%s之和（%s）" % (t.span(rs), fmt(base))''')
R('''            options = [("%s%% of the base" % fmt(rate), part), ("base plus %s%%" % fmt(rate), base + part),
                       ("base minus %s%%" % fmt(rate), base - part),
                       ("the %s%% contained in a gross base" % fmt(rate), base - base / (1 + rate / 100)),
                       ("a gross base less %s%%" % fmt(rate), base / (1 + rate / 100))]''',
  '''            options = [("基数的 %s%%" % fmt(rate), part), ("基数加 %s%%" % fmt(rate), base + part),
                       ("基数减 %s%%" % fmt(rate), base - part),
                       ("含税基数里包含的 %s%%" % fmt(rate), base - base / (1 + rate / 100)),
                       ("含税基数换算成不含税额（%s%%）" % fmt(rate), base / (1 + rate / 100))]''')
R('''                    for d, v in (("%s%% of it" % fmt(rate), tp), ("it plus %s%%" % fmt(rate), true_base + tp),
                                 ("it minus %s%%" % fmt(rate), true_base - tp)):''',
  '''                    for d, v in (("它的 %s%%" % fmt(rate), tp), ("它加 %s%%" % fmt(rate), true_base + tp),
                                 ("它减 %s%%" % fmt(rate), true_base - tp)):''')
R('''                            alt = (" It does match the sum of the detail rows %s (%s): %s = %s. So this row was "
                                   "worked out from the detail rows and the stated base is the figure to check."
                                   % (t.span(rs), fmt(true_base, stated.decimals), d, fmt(v, stated.decimals)))''',
  '''                            alt = (" 它与明细行 %s 之和（%s）对得上：%s = %s。可见这一行是按明细行算出来的，"
                                   "要核对的是所列的基数。"
                                   % (t.span(rs), fmt(true_base, stated.decimals), d, fmt(v, stated.decimals)))''')
R('''                'Row "%s" states %s. With %s as the base: %s. None matches.%s' % (''',
  '''                '“%s”行显示 %s。以 %s 为基数：%s。都对不上。%s' % (''')
R('''                    "; ".join("%s = %s" % (d, fmt(v, stated.decimals)) for d, v in options[:3]), alt),''',
  '''                    "；".join("%s = %s" % (d, fmt(v, stated.decimals)) for d, v in options[:3]), alt),''')
# total rows
R('''                    inner_note = " The detail cells of the table sum to %s." % fmt(inner, dec)''',
  '''                    inner_note = " 表中明细单元格之和为 %s。" % fmt(inner, dec)''')
R('''                    tail = ("The stated figure is %s %s than its parts give. An error if these are exact "
                            "counts; rounding explains it only if the figures are rounded." % (
                                fmt(abs(diff)), "higher" if diff > 0 else "lower"))''',
  '''                    tail = ("所列数字比各分项之和%s %s。如果这些是精确的计数，就是错误；"
                            "只有数字经过四舍五入时，才能用四舍五入解释。" % (
                                "高" if diff > 0 else "低", fmt(abs(diff))))''')
R('''                    '"%s"%s states %s, which is %s (%s%%) %s the subtotal in %s (%s). Check that tax, '
                    "a discount or another line accounts for exactly that gap." % (
                        labels[r], col_name(c), stated.raw, fmt(abs(diff), stated.decimals),
                        fmt(abs(diff) / abs(total) * 100, 2), "above" if diff > 0 else "below",
                        t.span(rs), nums[rs[0]][c].raw),''',
  '''                    '“%s”%s显示 %s，比 %s 的小计（%s）%s %s（%s%%）。请确认税费、折扣或其他项目是否正好解释了这个差额。' % (
                        labels[r], col_name(c), stated.raw, t.span(rs), nums[rs[0]][c].raw,
                        "高" if diff > 0 else "低", fmt(abs(diff), stated.decimals),
                        fmt(abs(diff) / abs(total) * 100, 2)),''')
R('''                '"%s"%s states %s. %s (%s) sum to %s%s. %s%s%s%s' % (
                    labels[r], col_name(c), stated.raw, desc.capitalize(), t.span(rs),''',
  '''                '“%s”%s显示 %s。%s（%s）之和为 %s%s。%s%s%s%s' % (
                    labels[r], col_name(c), stated.raw, DESC_ZH.get(desc, desc), t.span(rs),''')
R('''                    'Last row "%s" equals the sum of the rows above in %d other column(s), but%s '
                    "states %s where %s sum to %s. %s" % (''',
  '''                    '最后一行“%s”在另外 %d 列里等于上面各行之和，但%s显示 %s，而 %s 之和为 %s。%s' % (''')
R('''                '"%s"%s states %s. The plain mean of %s is %s. A weighted mean would differ; '
                "check which one is meant." % (''',
  '''                '“%s”%s显示 %s。%s 的简单平均是 %s。加权平均会不同，请确认指的是哪一种。' % (''')
R('''                    inner_note = (" The detail cells of the table sum to %s, so the totals around this cell "
                                  "do not agree with each other; find the faulty total before changing this one."
                                  % fmt(inner))''',
  '''                    inner_note = (" 表中明细单元格之和为 %s，所以这个单元格周围的合计互相对不上；"
                                  "改这个之前，先找出有问题的那个合计。"
                                  % fmt(inner))''')
R('''                'Row "%s": column "%s" states %s. The %d cells %s it sum to %s. %s%s%s%s' % (
                    labels[r], headers[c] or t.col_ids[c], nums[r][c].raw, n_parts,
                    side, fmt(total), tail, inner_note, typed_note(r, c),''',
  '''                '“%s”行：“%s”列显示 %s。它%s的 %d 个单元格之和为 %s。%s%s%s%s' % (
                    labels[r], headers[c] or t.col_ids[c], nums[r][c].raw,
                    "左边" if side == "before" else "右边", n_parts, fmt(total), tail, inner_note, typed_note(r, c),''')
R('''                        'Row "%s": %s states %s. %s / %s gives %s%%. The share matches in %d other row(s).' % (
                            labels[r], col_name(k).strip() or "share column", nums[r][k].raw,''',
  '''                        '“%s”行：%s显示 %s。%s / %s = %s%%。其他 %d 行的占比都对得上。' % (
                            labels[r], col_name(k).strip() or "占比列", nums[r][k].raw,''')
R('''            "Percentages%s over %s sum to %s%%, not 100%%. %s This matters only if they are shares of one whole." % (
                col_name(c), t.span(rs), fmt(total), tail),''',
  '''            "%s 的百分比%s之和是 %s%%，不是 100%%。%s只有当它们是同一个整体的各部分占比时，这才算问题。" % (
                t.span(rs), col_name(c), fmt(total), tail),''')
R('''gap_words(state, total - 100, len(rs), "The sum", "100%")''', '''gap_words(state, total - 100, len(rs), "合计", "100%")''')
R('''gap_words(state, total - 1, len(vals), "The sum", "1")''', '''gap_words(state, total - 1, len(vals), "合计", "1")''')
R('''            "Shares%s over %s sum to %s (%s%%), not 1 (100%%). %s This matters only if they are shares of one whole." % (
                col_name(c), t.span(rs), fmt(total), fmt(total * 100), tail),''',
  '''            "%s 的占比%s之和是 %s（%s%%），不是 1（100%%）。%s只有当它们是同一个整体的各部分占比时，这才算问题。" % (
                t.span(rs), col_name(c), fmt(total), fmt(total * 100), tail),''')
R('''"change%": "change from %s to %s in %%",''', '''"change%": "从 %s 到 %s 的变化百分比",''')
R('''            'Row "%s": "%s" states %s. In %d other row(s) this column equals %s; here that gives %s '
            "(from %s and %s).%s" % (''',
  '''            '“%s”行：“%s”显示 %s。其他 %d 行里这一列都等于 %s；这一行按此算是 %s（由 %s 和 %s 算出）。%s' % (''')
R('''            ld["message"] += (" Knock-on: with the value the lead on %s points to, the parts sum to %s%s, which "
                              "agrees. This total is then correct and should not be changed." % (
                                  ", ".join(t.ref(*rc) for rc in hit), fmt(adjusted, dec), unit))''',
  '''            ld["message"] += (" 连带影响：按 %s 处线索所指的数值，各分项之和为 %s%s，与之相符。"
                              "这个合计本身是对的，不应修改。" % (
                                  "、".join(t.ref(*rc) for rc in hit), fmt(adjusted, dec), unit))''')
R('''            desc = ", ".join("%s in %s" % (u, t.span(rs)) for u, rs in sorted(units.items()))''',
  '''            desc = "；".join("%s（%s）" % (u, t.span(rs)) for u, rs in sorted(units.items()))''')
R('''                "Column%s mixes units: %s. Totals and comparisons across these rows need one unit." % (
                    col_name(c), desc),''',
  '''                "这一列%s混用了单位：%s。跨这些行求和或比较之前，需要统一单位。" % (
                    col_name(c), desc),''')

# ---------------------------------------------------------------- prose rules
R('''WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]''',
  '''WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]''')
R('''_WD_ALT = "|".join(sorted((re.escape(w) for w in WEEKDAYS), key=len, reverse=True))
''', '''_WD_ALT = "|".join(sorted((re.escape(w) for w in WEEKDAYS), key=len, reverse=True))

# 中文星期（本团队新增）：星期一～星期日、星期天、周一～周日、周天、礼拜一～礼拜日。
_CN_DIGITS = "一二三四五六日天"
for _prefix in ("星期", "周", "礼拜"):
    for _i, _ch in enumerate(_CN_DIGITS):
        WEEKDAYS[_prefix + _ch] = min(_i, 6)      # “日”和“天”都是星期日（下标 6）
_WD_CN = r"(?:星期|周|礼拜)[" + _CN_DIGITS + r"]"
''')
R('''    ("iso", r"(?P<y>\\d{4})-(?P<m>\\d{2})-(?P<d>\\d{2})"),''',
  '''    ("iso", r"(?P<y>\\d{4})-(?P<m>\\d{2})-(?P<d>\\d{2})"),
    ("cn_ymd", r"(?P<y>\\d{4})\\s*年\\s*(?P<m>\\d{1,2})\\s*月\\s*(?P<d>\\d{1,2})\\s*[日号]"),''')
R('''        elif kind in ("dmy_dot", "iso"):''', '''        elif kind in ("dmy_dot", "iso", "cn_ymd"):''')
R('''_PCT = r"(\\d{1,3}(?:[.,]\\d+)?)\\s?%"''', '''_PCT = r"(\\d{1,3}(?:[.,]\\d+)?)\\s?[%％]"''')
R('''               r"(?!\\s*-?\\s?Punkt)", re.I),
]''', '''               r"(?!\\s*-?\\s?Punkt)", re.I),
    # 中文：“从 12% 升至 15%，增长 25%”（本团队新增）
    re.compile(r"从\\s*" + _PCT + r"\\s*(?:上升|提高|增长|增加|下降|降低|减少|升|降|涨|变)?\\s*(?:至|到|为)\\s*" + _PCT +
               r"[^。；;\\n]{0,40}?(?:增长|增加|上升|提高|下降|降低|减少|增幅|降幅|变化)\\s*(?:了|为|达)?\\s*" + _PCT +
               r"(?!\\s*个?百分点)"),
]''')
R('''SPAN_LINK_RE = re.compile(r"^\\s*(?:to|until|till|through|and|bis|bis\\s+zum|bis\\s+einschlie\\u00dflich|und|"
                          r"[-\\u2013\\u2014]|ile|ve)(?:\\s+the)?\\s*$", re.I)''',
  '''SPAN_LINK_RE = re.compile(r"^\\s*(?:to|until|till|through|and|bis|bis\\s+zum|bis\\s+einschlie\\u00dflich|und|"
                          r"[-\\u2013\\u2014]|ile|ve|至|到|直至|直到|截至|～|~|－)(?:\\s+the)?\\s*$", re.I)
# 中文时长（本团队新增）：只认“天、周、星期、个月”；单独的“月”“日”可能是日期的一部分，不当作时长。
SPAN_UNIT_CN_RE = re.compile(r"(?<![\\d.,])(\\d{1,4})\\s*(个星期|星期|周|个月|天)(?!\\d)")
SPAN_CN_UNITS = {"个星期": "week", "星期": "week", "周": "week", "个月": "month", "天": "day"}''')
R('''            leads.append(lead(where, "duration", '"%s ... %s": the end date is before the start date.' % (t1, t2)))''',
  '''            leads.append(lead(where, "duration", '“%s …… %s”：结束日期早于开始日期。' % (t1, t2)))''')
R('''        m = SPAN_UNIT_RE.search(text[e2:e2 + 60])
        if not m:
            continue
        n, unit = int(m.group(1)), m.group(2).lower()''',
  '''        tail_txt = text[e2:e2 + 60]
        m = SPAN_UNIT_RE.search(tail_txt)
        cn_m = SPAN_UNIT_CN_RE.search(tail_txt)
        if cn_m and (not m or cn_m.start() < m.start()):
            m = cn_m
            n, unit = int(m.group(1)), SPAN_CN_UNITS[m.group(2)]
        elif m:
            n, unit = int(m.group(1)), m.group(2).lower()
        else:
            continue''')
R('''            actual = "%d days (%d counting both end days), which is %s weeks" % (''',
  '''            actual = "%d 天（含首尾两天为 %d 天），约合 %s 周" % (''')
R('''            actual = "%d days, or %d counting both the first and the last day" % (days, days + 1)''',
  '''            actual = "%d 天，含首尾两天为 %d 天" % (days, days + 1)''')
R('''            actual = "%d days, about %d months" % (days, whole + (1 if d2.day >= d1.day else 0))''',
  '''            actual = "%d 天，约 %d 个月" % (days, whole + (1 if d2.day >= d1.day else 0))''')
R('''        leads.append(lead(where, "duration", '"%s ... %s ... %s": from %s to %s is %s.' % (''',
  '''        leads.append(lead(where, "duration", '“%s …… %s …… %s”：从 %s 到 %s 是 %s。' % (''')
R('''                                      '"%s": %s%% to %s%% is %s percentage points. As a percentage change it is %s%%. '
                                      "Written as a plain percent, the figure reads as the relative change." % (''',
  '''                                      '“%s”：%s%% 到 %s%% 是 %s 个百分点；按相对变化算是 %s%%。'
                                      "直接写成百分号时，读者会把它理解成相对变化。" % (''')
R('''                                      '"%s": %s%% to %s%% is %s percentage points, or %s%% as a percentage change. '
                                      "The stated %s%% is neither." % (''',
  '''                                      '“%s”：%s%% 到 %s%% 是 %s 个百分点，按相对变化算是 %s%%；'
                                      "所列的 %s%% 两者都不是。" % (''')
R('''            before = re.compile(r"\\b(?P<wd>" + _WD_ALT + r")\\b\\.?,?\\s+(?:the\\s+|den\\s+|dem\\s+|le\\s+|el\\s+)?" + expr, re.I)
            after = re.compile(expr + r"\\s*,?\\s*\\(?(?P<wd>" + _WD_ALT + r")\\b", re.I)''',
  '''            if kind == "cn_ymd":      # 中文没有词边界，星期可以在日期前，也可以在日期后（常带括号）
                before = re.compile(r"(?P<wd>" + _WD_CN + r")\\s*[，,、]?\\s*" + expr)
                after = re.compile(expr + r"\\s*[，,、]?\\s*[（(]?\\s*(?P<wd>" + _WD_CN + r")[）)]?")
            else:
                before = re.compile(r"\\b(?P<wd>" + _WD_ALT + r")\\b\\.?,?\\s+(?:the\\s+|den\\s+|dem\\s+|le\\s+|el\\s+)?" + expr, re.I)
                after = re.compile(expr + r"\\s*,?\\s*\\(?(?P<wd>" + _WD_ALT + r")\\b", re.I)''')
R('''                    actual = " or ".join(sorted(set(
                        "%s (%s)" % (WEEKDAY_NAMES[d.weekday()], d.isoformat()) for d in dates)))''',
  '''                    actual = "或".join(sorted(set(
                        "%s（%s）" % (WEEKDAY_NAMES[d.weekday()], d.isoformat()) for d in dates)))''')
R('''                        '"%s": that date is a %s, not a %s.' % (''', '''                        '“%s”：这个日期是%s，不是%s。' % (''')
R('''leads.append(lead(where, "date", '"%s" is not a calendar date.' % m.group(0).strip()))''',
  '''leads.append(lead(where, "date", '“%s”不是日历上存在的日期。' % m.group(0).strip()))''')
# n-of-N: accept full-width brackets/slash/percent and the Chinese "N 人中有 n 人，占 p%"
R('''        pats = [
            (r"(?<![\\d.,/])(?P<n>\\d{1,7})\\s*(?:of|out\\s+of|von|/)\\s*(?P<N>\\d{1,7})(?![\\d/.,]\\d)"
             r"[^.%\\n()]{0,40}?\\(\\s*(?P<p>\\d{1,3}(?:[.,]\\d+)?)\\s*%\\s*\\)"),
            (r"(?P<p>\\d{1,3}(?:[.,]\\d+)?)\\s*%\\s*\\(\\s*(?:n\\s*=\\s*)?(?P<n>\\d{1,7})\\s*/\\s*(?P<N>\\d{1,7})\\s*\\)"),
        ]''', '''        pats = [
            (r"(?<![\\d.,/])(?P<n>\\d{1,7})\\s*(?:of|out\\s+of|von|/|／)\\s*(?P<N>\\d{1,7})(?![\\d/.,]\\d)"
             r"[^.%％\\n()（）]{0,40}?[(（]\\s*(?P<p>\\d{1,3}(?:[.,]\\d+)?)\\s*[%％]\\s*[)）]"),
            (r"(?P<p>\\d{1,3}(?:[.,]\\d+)?)\\s*[%％]\\s*[(（]\\s*(?:n\\s*=\\s*)?(?P<n>\\d{1,7})\\s*[/／]\\s*(?P<N>\\d{1,7})\\s*[)）]"),
            # 中文：“240 人中有 156 人，占 65%”“240 人中的 156 人（占 65%）”
            (r"(?<![\\d.,/])(?P<N>\\d{1,7})\\s*[^\\d\\s，。；,.;（）()]{0,3}中\\s*(?:有|的)?\\s*(?P<n>\\d{1,7})\\s*"
             r"[^\\d，。；,.;（）()]{0,3}[，,（(]?\\s*(?:占|占比|约占|即|比例为)\\s*(?:总数的|全部的)?\\s*(?:约)?\\s*"
             r"(?P<p>\\d{1,3}(?:[.,]\\d+)?)\\s*[%％]"),
        ]''')
R('''                    note = " The stated figure looks truncated instead of rounded."''',
  '''                    note = " 所列数字像是截断而不是四舍五入得到的。"''')
R('''                    '"%s": %d / %d = %s%%, not %s%%.%s' % (''', '''                    '“%s”：%d / %d = %s%%，不是 %s%%。%s' % (''')

# ---------------------------------------------------------------- office-file notes and where-labels
R('''                 where="%s, %s%s, values as stored in the chart (the workbook embedded behind it is not read)" % (
                     where, ctype, ' titled "%s"' % title if title else ""))''',
  '''                 where="%s，%s%s，图表里存储的数值（不读取图表背后嵌入的工作簿）" % (
                     where, ctype, '（标题“%s”）' % title if title else ""))''')
R('''                   "(page %s) %s" % (m.group(1), text)))''', '''                   "（页%s）%s" % ("眉" if m.group(1) == "header" else "脚", text)))''')
R('''        read = ["%d paragraph(s)" % counters["p"], "%d table(s)" % counters["t"]]
        if n:
            read.append("the stored data of %d chart(s)" % n)
        read.append("footnotes, page headers and footers, and text boxes where present")
        skipped = []
        if n_img:
            skipped.append("%d image(s), so figures shown only inside a picture are missing" % n_img)
        if n_com:
            skipped.append("%d comment(s)" % n_com)
        if n_del:
            skipped.append("%d tracked deletion(s), the text is read as if all changes were accepted" % n_del)
        notes.append("Read: %s. Not read: %s." % (
            ", ".join(read), "; ".join(skipped) if skipped else "nothing, the file has no images, comments or tracked deletions"))''',
  '''        read = ["%d 个段落" % counters["p"], "%d 个表格" % counters["t"]]
        if n:
            read.append("%d 个图表里存储的数据" % n)
        read.append("脚注、页眉页脚和文本框（有则读取）")
        skipped = []
        if n_img:
            skipped.append("%d 张图片（只出现在图片里的数字读不到）" % n_img)
        if n_com:
            skipped.append("%d 条批注" % n_com)
        if n_del:
            skipped.append("%d 处修订删除（按“全部接受修订”后的文字读取）" % n_del)
        notes.append("已读取：%s。未读取：%s。" % (
            "、".join(read), "；".join(skipped) if skipped else "无，文件里没有图片、批注或修订删除"))''')
R('''where="slide %d" % idx''', '''where="第 %d 张幻灯片" % idx''')
R('''                pics.append("slide %d (%d)" % (idx, counts["pic"]))''', '''                pics.append("第 %d 张幻灯片（%d 张）" % (idx, counts["pic"]))''')
R('''        notes.append("Read: %d slide(s) with their text, tables, speaker notes and the stored data of their charts. "
                     "Not read: %s." % (
                         len(order),
                         "pictures on " + ", ".join(pics) + ", so figures shown only inside a picture are missing"
                         if pics else "nothing, the deck has no pictures"))''',
  '''        notes.append("已读取：%d 张幻灯片的文字、表格、演讲者备注和图表里存储的数据。"
                     "未读取：%s。" % (
                         len(order),
                         "图片（" + "、".join(pics) + "），只出现在图片里的数字读不到"
                         if pics else "无，幻灯片里没有图片"))''')
R('''                        names.append('row %d "%s"' % (hr, texts[0][:40]))
                notes.append('Sheet "%s" has hidden rows: %s%s. Hidden rows still count in every SUM range that '
                             "spans them, so the visible rows will not add up to the totals shown." % (
                                 name, _compress(hidden_rows), " (%s)" % ", ".join(names) if names else ""))
            if hidden_cols:
                notes.append('Sheet "%s" has hidden columns: %s.' % (name, ", ".join(hidden_cols)))''',
  '''                        names.append('第 %d 行“%s”' % (hr, texts[0][:40]))
                notes.append('工作表“%s”有隐藏行：%s%s。隐藏行仍会计入所有跨过它们的 SUM 区域，'
                             "所以可见的行加起来不会等于显示的合计。" % (
                                 name, _compress(hidden_rows), "（%s）" % "、".join(names) if names else ""))
            if hidden_cols:
                notes.append('工作表“%s”有隐藏列：%s。' % (name, "、".join(hidden_cols)))''')
R('''                                      "Cell shows %s%s." % (info["text"], " from " + info["formula"] if info["formula"] else "")))''',
  '''                                      "单元格显示 %s%s。" % (info["text"], "，来自公式 " + info["formula"] if info["formula"] else "")))''')
R('''                                      'Cell holds "%s" as text, between numeric cells. SUM and similar functions skip text.'
                                      % info["text"]))''',
  '''                                      '单元格里的“%s”是文本，夹在数值单元格之间。SUM 等函数会跳过文本。'
                                      % info["text"]))''')
R('''                            where_gap = ("%s%d (%s)" % (cl, gap[0], cells[(gap[0], c)]["text"]) if len(gap) == 1 else
                                         "%d cells between %s%d and %s%d" % (len(gap), cl, gap[0], cl, gap[-1]))
                            leads.append(lead(ref_of(r, c), "sum-range",
                                              "%s stops at row %d, but %s %s left out." % (
                                                  ftxt, r2, where_gap,
                                                  "holds a number and is" if len(gap) == 1 else "hold numbers and are")))''',
  '''                            where_gap = ("%s%d（%s）" % (cl, gap[0], cells[(gap[0], c)]["text"]) if len(gap) == 1 else
                                         "%s%d 与 %s%d 之间的 %d 个单元格" % (cl, gap[0], cl, gap[-1], len(gap)))
                            leads.append(lead(ref_of(r, c), "sum-range",
                                              "%s 只算到第 %d 行，但%s里的数字被漏掉了。" % (
                                                  ftxt, r2, where_gap)))''')
R('''                                              "%s starts at row %d, but %s%d directly above holds the number %s and is left out." % (''',
  '''                                              "%s 从第 %d 行开始，但紧邻上方的 %s%d 里有数字 %s，被漏掉了。" % (''')
R('''                            where_gap = ("%s%d (%s)" % (num_to_col(gap[0]), r, cells[(r, gap[0])]["text"])
                                         if len(gap) == 1 else
                                         "%d cells between %s%d and %s%d" % (
                                             len(gap), num_to_col(gap[0]), r, num_to_col(gap[-1]), r))
                            leads.append(lead(ref_of(r, c), "sum-range",
                                              "%s stops at column %s, but %s %s left out." % (
                                                  ftxt, num_to_col(c2), where_gap,
                                                  "holds a number and is" if len(gap) == 1 else "hold numbers and are")))''',
  '''                            where_gap = ("%s%d（%s）" % (num_to_col(gap[0]), r, cells[(r, gap[0])]["text"])
                                         if len(gap) == 1 else
                                         "%s%d 与 %s%d 之间的 %d 个单元格" % (
                                             num_to_col(gap[0]), r, num_to_col(gap[-1]), r, len(gap)))
                            leads.append(lead(ref_of(r, c), "sum-range",
                                              "%s 只算到 %s 列，但%s里的数字被漏掉了。" % (
                                                  ftxt, num_to_col(c2), where_gap)))''')
R('''                                              "SUM covers rows %d to %d, while %d sibling totals in row %d cover rows %d to %d." % (
                                                  span[0], span[1], len(common[1]), r, common[0][0], common[0][1])))''',
  '''                                              "SUM 覆盖第 %d 到 %d 行，而第 %d 行里另外 %d 个同类合计覆盖第 %d 到 %d 行。" % (
                                                  span[0], span[1], r, len(common[1]), common[0][0], common[0][1])))''')
R('''                                          "Typed number %s sits between two cells that share one formula pattern in its %s. "
                                          "By that pattern this cell would hold =%s. A typed number does not update "
                                          "with its inputs." % (info["text"], axis, from_r1c1(prev["r1c1"], r, c))))''',
  '''                                          "手工输入的数字 %s 夹在同一%s里两个公式规律相同的单元格之间。"
                                          "按这个规律，这个单元格应该是 =%s。手工输入的数字不会随输入数据更新。"
                                          % (info["text"], AXIS_ZH[axis], from_r1c1(prev["r1c1"], r, c))))''')
R('''                                          "Formula %s differs from its neighbours in the same %s. By their pattern "
                                          "this cell would hold =%s." % (
                                              info["formula"], axis, from_r1c1(prev["r1c1"], r, c)),''',
  '''                                          "公式 %s 和同一%s里相邻的公式不一致。按相邻公式的规律，"
                                          "这个单元格应该是 =%s。" % (
                                              info["formula"], AXIS_ZH[axis], from_r1c1(prev["r1c1"], r, c)),''')
R('''                                          '%s is a typed number (%s) in a column where %d other cells are formulas. '
                                          "If it can be counted or calculated from the workbook, recalculate it." % (
                                              '"%s"' % label if label else "This cell", info["text"], len(forms)),''',
  '''                                          '%s是手工输入的数字（%s），而这一列里另外有 %d 个单元格是公式。'
                                          "如果它能从工作簿里数出来或算出来，请重新计算。" % (
                                              '“%s”' % label if label else "这个单元格", info["text"], len(forms)),''')
R('''                                      'The label "%s" names "%s" as the base, but %s divides by %s%d, the row labelled '
                                      '"%s". A row labelled "%s" exists.' % (''',
  '''                                      '标签“%s”把“%s”当作基数，但 %s 除以的是 %s%d，也就是标为“%s”的那一行。'
                                      '表里存在标为“%s”的行。' % (''')
R('''where='sheet "%s", rows %d to %d' % (name, g[0], g[-1])''', '''where='工作表“%s”，第 %d 到 %d 行' % (name, g[0], g[-1])''')
R('''        notes.append("Read: %d sheet(s)%s, %d formula(s)%s." % (
            n_sheets, ", none hidden" if not hidden_sheets else ", %d of them hidden" % len(hidden_sheets),
            len(all_formulas) + shared_copies[0],
            "" if uncalculated else ", all with stored results"))
        if not any("hidden rows" in x or "hidden columns" in x for x in notes):
            notes.append("No hidden rows or columns.")''',
  '''        notes.append("已读取：%d 个工作表%s，%d 个公式%s。" % (
            n_sheets, "，没有隐藏的" if not hidden_sheets else "，其中 %d 个隐藏" % len(hidden_sheets),
            len(all_formulas) + shared_copies[0],
            "" if uncalculated else "，都有已存储的结果"))
        if not any("隐藏行" in x or "隐藏列" in x for x in notes):
            notes.append("没有隐藏的行或列。")''')
R('''                notes.append('Sheet "%s" is hidden and formulas on %s read from it. Its figures feed the visible '
                             "sheets and were checked like the others." % (hs, ", ".join('"%s"' % u for u in users)))
            else:
                notes.append('Sheet "%s" is hidden. No formula on another sheet refers to it.' % hs)''',
  '''                notes.append('工作表“%s”是隐藏的，%s 上的公式读取了它。它的数据会流入可见的工作表，已和其他数据一样检查。'
                             % (hs, "、".join('“%s”' % u for u in users)))
            else:
                notes.append('工作表“%s”是隐藏的，其他工作表上没有公式引用它。' % hs)''')
R('''                "whole file", "uncalculated",
                "%d formula cell(s) have no stored result (%s%s). The file was saved by a program that does not "
                "calculate, so formula values are unknown here and totals built on them cannot be checked. "
                "Open it in a spreadsheet program, save it and run the check again." % (
                    len(uncalculated), ", ".join(uncalculated[:5]), ", ..." if len(uncalculated) > 5 else "")))''',
  '''                "整个文件", "uncalculated",
                "有 %d 个公式单元格没有存储结果（%s%s）。这个文件是由不做计算的程序保存的，所以这里不知道公式的值，"
                "建立在它们之上的合计也无法核对。请先用电子表格软件打开、保存，再重新核对。" % (
                    len(uncalculated), "、".join(uncalculated[:5]), "……" if len(uncalculated) > 5 else "")))''')
R('''where="%slines %d to %d" % (prefix, i + 1, j)''', '''where="%s第 %d 到 %d 行" % (prefix, i + 1, j)''')
R('''    t = Table("", rows, where="the whole file",''', '''    t = Table("", rows, where="整个文件",''')
R('''"notes": ["Delimiter read as %r." % delim]''', '''"notes": ["分隔符识别为 %r。" % delim]''')
R('''                where="%s, text lines %d to %d, columns inferred from the position of the numbers"''',
  '''                where="%s，第 %d 到 %d 行文字，列是按数字的位置推断的"''')
R('''                    notes.append("Page %d has no text layer (scanned or image only)." % pno)''',
  '''                    notes.append("第 %d 页没有文字层（扫描件或纯图片）。" % pno)''')
R('''                notes.append("Page %d has no text layer (scanned or image only)." % pno)''',
  '''                notes.append("第 %d 页没有文字层（扫描件或纯图片）。" % pno)''')
R('''Table("p%d T%d" % (pno, tno), clean, where="page %d" % pno)''', '''Table("p%d T%d" % (pno, tno), clean, where="第 %d 页" % pno)''')
R('''infer_tables(loose, "p%d %s" % (pno, "I"), "page %d" % pno)''', '''infer_tables(loose, "p%d %s" % (pno, "I"), "第 %d 页" % pno)''')
R('''            notes.append("Tables named I1, I2, ... have no ruling lines in the PDF. Their columns were inferred from "
                         "where the numbers sit, so check a row against the page before reporting a lead from them.")''',
  '''            notes.append("名为 I1、I2…… 的表格在 PDF 里没有表格线，它们的列是按数字所在位置推断的，"
                         "所以报告这些表格里的线索之前，请先对照页面核对那一行。")''')
R('''        notes.append("Tables were read as plain lines (pypdf). Check table arithmetic from the text.")''',
  '''        notes.append("表格是按普通文字行读取的（pypdf），请根据文字核对表格里的算术。")''')
R('''    notes.append("No PDF text library is installed (pdfplumber or pypdf). Read this PDF directly and "
                 "apply the checks by hand, or convert it to text first.")''',
  '''    notes.append("环境里没有安装 PDF 文字库（pdfplumber 或 pypdf）。请直接阅读这个 PDF 并手工核对，"
                 "或者先把它转换成文字。")''')

# ---------------------------------------------------------------- process / render / grim / entry points
R('''    for key, name in (("totals", "totals"), ("calcs", "row calculations"),
                      ("nofn", "counts with a percentage"), ("weekdays", "weekdays"),
                      ("spans", "durations"), ("points", "percentage-point statements")):
        if STATS[key]:
            parts.append("%s: %d of %d agree" % (name, STATS[key + "_ok"], STATS[key]))
    if not parts:
        return "The rules found nothing they could test in this file. Everything has to be checked by reading."
    return ("Tested by rule: " + "; ".join(parts) + ". Anything else was not tested by rule, for example "
            "figures in sentences, growth rates and text against tables.")''',
  '''    for key, name in (("totals", "合计"), ("calcs", "行内计算"),
                      ("nofn", "带百分比的计数"), ("weekdays", "星期"),
                      ("spans", "时长"), ("points", "百分点说法")):
        if STATS[key]:
            parts.append("%s：%d/%d 相符" % (name, STATS[key + "_ok"], STATS[key]))
    if not parts:
        return "规则在这个文件里没有找到可以检验的内容，一切都要靠阅读来核对。"
    return ("按规则检验过：" + "；".join(parts) + "。其余内容没有按规则检验，例如句子里的数字、增长率，"
            "以及正文与表格之间的对照。")''')
R('''        result["error"] = ("Unsupported file type %s. Supported: %s. Old .doc, .xls and .ppt files "
                           "must be saved in the current format first." % (ext or "(none)", " ".join(sorted(EXTRACTORS))))
        return result
    try:
        data = EXTRACTORS[ext](path)
    except zipfile.BadZipFile:
        result["error"] = "The file is not a valid Office file (it may be password protected or damaged)."
        return result
    except Exception as exc:   # report and carry on with the other files
        result["error"] = "Could not read the file: %s: %s" % (type(exc).__name__, exc)
        return result''',
  '''        result["error"] = ("不支持的文件类型 %s。支持：%s。旧版 .doc、.xls、.ppt 文件需要先另存为当前格式。"
                           % (ext or "（无扩展名）", " ".join(sorted(EXTRACTORS))))
        return result
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            result["error"] = "文件超过 %d MB 的上限，不予读取。" % (MAX_FILE_BYTES // (1024 * 1024))
            return result
        data = EXTRACTORS[ext](path)
    except zipfile.BadZipFile:
        result["error"] = "这不是有效的 Office 文件（可能有密码保护或已损坏）。"
        return result
    except ValueError as exc:   # 安全上限或 XML 声明被拒绝（消息本身已是中文）
        result["error"] = str(exc)
        return result
    except Exception as exc:   # report and carry on with the other files
        result["error"] = "无法读取文件：%s：%s" % (type(exc).__name__, exc)
        return result''')
R('''        names = ("a decimal comma", "a decimal point")''', '''        names = ("小数逗号", "小数点")''')
R('''            "whole file", "number-format",
            "Two number formats in one file: %d figure(s) are written with %s and %d with %s, for example %s. "
            "Confirm each is intended." % (
                len(major), names[0], len(minor), names[1],
                "; ".join('%s "%s"' % (w, x) for w, x in minor[:4])),''',
  '''            "整个文件", "number-format",
            "同一个文件里有两种数字写法：%d 个数字用%s，%d 个用%s，例如 %s。请确认都是有意为之。" % (
                len(major), names[0], len(minor), names[1],
                "；".join('%s “%s”' % (w, x) for w, x in minor[:4])),''')
R('''        mark = "decimal comma" if conv == "eu" else "decimal point"
        if amb and eu and us:
            notes.append("%d figure(s) such as %s can be read two ways, and the file mixes both number formats. "
                         "They were read with a %s, the more frequent one. Check each against its context." % (
                             len(amb), "; ".join('%s "%s"' % a for a in amb[:3]), mark))
        elif amb and not (eu or us):
            notes.append("%d figure(s) such as %s can be read two ways and nothing in the file settles it. "
                         "They were read with a %s (so 1,234 is one thousand two hundred and thirty-four). "
                         "Say so in the report if a finding depends on it." % (
                             len(amb), "; ".join('%s "%s"' % a for a in amb[:3]), mark))''',
  '''        mark = "小数逗号" if conv == "eu" else "小数点"
        if amb and eu and us:
            notes.append("有 %d 个数字（如 %s）可以有两种读法，而且文件里两种数字写法混用。"
                         "它们按出现更多的那一种（%s）读取，请结合上下文逐个核对。" % (
                             len(amb), "；".join('%s “%s”' % a for a in amb[:3]), mark))
        elif amb and not (eu or us):
            notes.append("有 %d 个数字（如 %s）可以有两种读法，而文件里没有任何线索能判断。"
                         "它们按%s读取（所以 1,234 读作一千二百三十四）。如果某条结论取决于这一点，请在报告里说明。" % (
                             len(amb), "；".join('%s “%s”' % a for a in amb[:3]), mark))''')
R('''        held += " No rule applied to %s%s: check %s by reading." % (
            ", ".join(names[:10]), " and %d more" % (len(names) - 10) if len(names) > 10 else "",
            "it" if len(names) == 1 else "them")''',
  '''        held += " 没有规则适用于 %s%s：请靠阅读核对。" % (
            "、".join(names[:10]), " 等另外 %d 个" % (len(names) - 10) if len(names) > 10 else "")''')
R('''    out.append("# Adds Up extraction")
    out.append("")
    out.append("Leads are candidates produced by rule. Confirm each one against the content before reporting it,")
    out.append("and read the content yourself for everything the rules cannot see.")
    for idx, res in enumerate(results, 1):
        out.append("")
        out.append("## File %d: %s" % (idx, res["file"]))
        if res["error"]:
            out.append("")
            out.append("ERROR: " + res["error"])
            continue
        out.append("")
        out.append("### Content")''',
  '''    out.append("# 文档数字核对：提取结果")
    out.append("")
    out.append("“线索”是规则产生的候选项。报告之前必须逐条对照内容确认，")
    out.append("规则看不到的部分，请自己通读内容。")
    for idx, res in enumerate(results, 1):
        out.append("")
        out.append("## 文件 %d：%s" % (idx, res["file"]))
        if res["error"]:
            out.append("")
            out.append("错误：" + res["error"])
            continue
        out.append("")
        out.append("### 内容")''')
R('''            label = t.name.rstrip("!") if t.joiner == "" and t.name else (t.name or "table")
            out.append("")
            out.append("[%s] table, %d rows x %d columns, %s" % (label, len(t.rows), t.width, t.where))''',
  '''            label = t.name.rstrip("!") if t.joiner == "" and t.name else (t.name or "表格")
            out.append("")
            out.append("[%s] %d 行 x %d 列，%s" % (label, len(t.rows), t.width, t.where))''')
R('''                    out.append("  ... %d row(s) not printed (%s to %s). They were checked by the rules." % (
                        r - prev - 1, t.row_ids[prev + 1], t.row_ids[r - 1]))''',
  '''                    out.append("  …… 有 %d 行没有打印（%s 到 %s），规则已检查过它们。" % (
                        r - prev - 1, t.row_ids[prev + 1], t.row_ids[r - 1]))''')
R('''                            s += " (shown as %s)" % m["shown"]''', '''                            s += "（显示为 %s）" % m["shown"]''')
R('''                out.append("  (%d of %d rows printed. Run again with --all-rows to print every row.)" % (len(keep), n))''',
  '''                out.append("  （共 %d 行，已打印 %d 行。需要全部行时，请把 all_rows 设为 true 再运行。）" % (n, len(keep)))''')
R('''        out.append("### Leads (%d), in reading order" % len(res["leads"]))
        if not res["leads"]:
            out.append("None from the automatic rules.")
        for n, ld in enumerate(res["leads"], 1):
            out.append("%d. [%s] (%s%s) %s" % (
                n, ld["where"], ld["kind"], ", weak" if ld["strength"] == "weak" else "", ld["message"]))
        out.append("")
        out.append("### What the rules covered")
        out.append(res.get("held", ""))
        if res["notes"]:
            out.append("")
            out.append("### Notes")''',
  '''        out.append("### 线索（%d 条，按阅读顺序）" % len(res["leads"]))
        if not res["leads"]:
            out.append("自动规则没有产生线索。")
        for n, ld in enumerate(res["leads"], 1):
            out.append("%d. [%s]（%s%s）%s" % (
                n, ld["where"], ld["kind"], "，弱" if ld["strength"] == "weak" else "", ld["message"]))
        out.append("")
        out.append("### 规则覆盖了什么")
        out.append(res.get("held", ""))
        if res["notes"]:
            out.append("")
            out.append("### 说明")''')
# grim: return the report text instead of printing
R('''def cmd_grim(args):
    if (args.percent is None) == (args.mean is None):
        print("Give exactly one of --percent or --mean.")
        return 2
    is_pct = args.percent is not None
    value = args.percent if is_pct else args.mean
    matches, near, decimals = grim(args.n, value, is_pct)
    span = ""
    if matches:
        span = str(matches[0]) if len(matches) == 1 else "%d to %d" % (matches[0], matches[-1])
    if is_pct:
        what = "%s%% of n=%d" % (value.rstrip("%"), args.n)
        if matches:
            print("CONSISTENT: %s corresponds to a whole count (%s of %d)." % (what, span, args.n))
            if len(matches) > 1:
                print("Several counts display as this percentage, so the test cannot tell them apart. "
                      "If the count is stated, divide it by n instead.")
        else:
            print("NOT POSSIBLE: %s does not correspond to a whole count. Nearest: %s." % (
                what, "; ".join("%d/%d = %s%%" % (k, args.n, v) for k, v in near)))
            print("Check first that n is the right denominator and that the figure is a simple proportion.")
    else:
        what = "mean %s with n=%d" % (value, args.n)
        if matches:
            print("CONSISTENT: %s can come from whole-number values (total %s)." % (what, span))
        else:
            print("NOT POSSIBLE for whole-number data: %s. Nearest: %s." % (
                what, "; ".join("total %d gives %s" % (k, v) for k, v in near)))
            print("This only applies if every single value is a whole number (counts, scale points). "
                  "Check also that n is right.")
    return 0''',
  '''def grim_report(n, value, is_pct):
    """GRIM 检验的中文结论（返回字符串列表，每个元素一行）。value 按文档里的写法传入，如 "37.5"。"""
    out = []
    matches, near, decimals = grim(n, value, is_pct)
    span = ""
    if matches:
        span = str(matches[0]) if len(matches) == 1 else "%d 到 %d" % (matches[0], matches[-1])
    if is_pct:
        what = "n=%d 时的 %s%%" % (n, value.strip().rstrip("%％"))
        if matches:
            out.append("相符：%s 对应整数个数（%d 个，共 %d 个）。" % (what, matches[0], n) if len(matches) == 1 else
                       "相符：%s 对应整数个数（%s 个，共 %d 个）。" % (what, span, n))
            if len(matches) > 1:
                out.append("有好几个个数都显示成这个百分比，所以这项检验分辨不出它们。如果文档给了个数，请直接用个数除以 n。")
        else:
            out.append("不可能：%s 不对应任何整数个数。最接近的是：%s。" % (
                what, "；".join("%d/%d = %s%%" % (k, n, v) for k, v in near)))
            out.append("请先确认 n 是不是正确的分母，以及这个数字是不是简单的占比。")
    else:
        what = "n=%d 时的平均值 %s" % (n, value.strip())
        if matches:
            out.append("相符：%s 可以由整数数据得到（总和 %s）。" % (what, span))
        else:
            out.append("对整数数据来说不可能：%s。最接近的是：%s。" % (
                what, "；".join("总和 %d 得到 %s" % (k, v) for k, v in near)))
            out.append("这只适用于每个数据本身都是整数的情况（计数、量表分值）。也请确认 n 是对的。")
    return out''')
# entry points: replace argparse main with callable functions
main_start = s.index("# --------------------------------------------------------------------------\n# Command line")
s = s[:main_start] + '''# --------------------------------------------------------------------------
# 调用入口（本团队新增，替代上游的命令行入口）
# --------------------------------------------------------------------------

def run_extract(paths, max_rows=60, all_rows=False):
    """读取若干文件，返回 (中文文本报告, 每个文件的结果列表)。调用方负责保证同一时刻只有一个调用在运行
    （本模块用全局变量 STATS、FMT 记录当前文件的统计和数字写法）。"""
    results = []
    for path in paths:
        if not os.path.isfile(path):
            results.append({"file": os.path.basename(str(path)) or str(path), "type": "", "blocks": [], "notes": [],
                            "leads": [], "error": "找不到这个文件。"})
            continue
        results.append(process(path))
    return render(results, max_rows, all_rows), results


def run_grim(n, value, is_pct):
    """GRIM：这个百分比或平均值能不能由整数得到。n 为样本量，value 为文档里的写法（字符串）。"""
    return "\\n".join(grim_report(n, value, is_pct)) + "\\n"
'''

open(out_path, "w", encoding="utf-8", newline="\n").write(s)
print("replacements applied:", sum(log), "in", len(log), "steps; output bytes", len(s.encode("utf-8")))
