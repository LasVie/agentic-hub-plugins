"""生成手工测试用的示例文件（确定性输出）：tests/fixtures/manual/ 下的 xlsx、docx、pptx、csv、md。

这些文件故意埋了错误，用来在 WorkSwarm 里手工验证插件；预期结果见 MANUAL_TESTING.md。
在仓库根目录运行：python -B plugins/adds-up/tests/make_fixtures.py
"""
import os
import sys
import zipfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_adds_up import make_docx, make_pptx, make_xlsx  # noqa: E402

OUT = os.path.join(HERE, "fixtures", "manual")
os.makedirs(OUT, exist_ok=True)


def normalize(path):
    """把压缩包里每个条目的时间改成固定值，让输出字节可重现。"""
    with zipfile.ZipFile(path) as src:
        items = [(i.filename, src.read(i.filename)) for i in src.infolist()]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as dst:
        for name, data in items:
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            dst.writestr(info, data)


def text(name, body):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


# 1. 预算表：SUM 少算一行、文本形式的数字、被它连带的合计；有一个隐藏工作表
path = os.path.join(OUT, "预算表.xlsx")
make_xlsx(path, {
    "2026预算": [
        ["科目", "一月", "二月", "三月", "一季度合计"],
        ["办公租金", 12000, 12000, 12000, ("=SUM(B2:D2)", 36000)],
        ["人员工资", 80000, 80000, 82000, ("=SUM(B3:D3)", 242000)],
        ["差旅费", 6500, 4200, 7800, ("=SUM(B4:D4)", 18500)],
        ["市场推广", 15000, "18000", 20000, ("=SUM(B5:D5)", 35000)],
        ["合计", ("=SUM(B2:B4)", 98500), ("=SUM(C2:C5)", 96200), ("=SUM(D2:D5)", 121800), ("=SUM(E2:E5)", 331500)],
    ],
    "参数": [["项目", "值"], ["增值税率", 0.13]],
}, hidden=("参数",))
normalize(path)

# 2. 项目报告：星期、时长、占比、百分点、不存在的日期、金额与合计
path = os.path.join(OUT, "项目报告.docx")
make_docx(path, [
    ("p", "项目报告（2026年第一季度）"),
    ("p", "启动会安排在2026年3月5日（星期三）。"),
    ("p", "项目周期为2026年3月1日至2026年5月31日，共14周。"),
    ("p", "共 240 名学员参加，240 人中有 156 人，占 62%，通过了考核。"),
    ("p", "客户满意度从 12% 升至 15%，增长 3%。"),
    ("p", "验收会定在2026年2月30日举行。"),
    ("t", [["项目", "数量", "单价（元）", "金额（元）"],
           ["培训费", "15", "480", "7,400"],
           ["教材费", "10", "20", "200"],
           ["场地费", "1", "3,000", "3,000"],
           ["资料费", "20", "15", "300"],
           ["合计", "", "", "10,900"]]),
])
normalize(path)

# 3. 季度汇报：句子里的增长率（规则不算，要靠技能通读）和不存在的日期
path = os.path.join(OUT, "季度汇报.pptx")
make_pptx(path, [
    ["季度汇报", "三季度收入 1,480 万元，比二季度 1,350 万元增长 12%。"],
    ["下一步", "验收时间：2026年2月30日", "预计新增客户 30 家，其中 18 家来自华东，占 60%。"],
])
normalize(path)

# 4. 销售明细：合计行写错（应为 830）
text("销售明细.csv", "区域,一季度,二季度,三季度,合计\n华东,100,120,130,350\n华南,80,90,100,270\n华北,60,70,80,210\n合计,240,280,310,840\n")

# 5. 全部正确的对照文件：应当报“没有发现”
text("正确的预算.csv", "科目,一月,二月,合计\n租金,100,100,200\n工资,500,520,1020\n合计,600,620,1220\n")

# 6. 与销售明细对照用的汇总说明（跨文件对照：说明里的合计和明细对不上）
text("汇总说明.md",
     "# 销售汇总说明\n\n全年三个季度的销售合计为 860 万元，其中华东 350 万元，华南 270 万元，华北 210 万元。\n\n"
     "| 区域 | 销售额（万元） |\n|---|---|\n| 华东 | 350 |\n| 华南 | 270 |\n| 华北 | 210 |\n| 合计 | 830 |\n")
print("fixtures written to", OUT)
