"""build_checker 功能测试：python -B tests/test_build_checker.py [tool-file] [pdf-dir]"""
import asyncio
import copy
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tool_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "src" / "build_checker.py"
spec = importlib.util.spec_from_file_location("build_checker", tool_file)
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)
tool = bc.BuildCheckerTool()
TODAY = "2026-11-03"
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS:", name)
    else:
        failed += 1
        print("FAIL:", name, "—", str(detail)[:600])


def call(**q):
    if q.get("action") == "export":
        q.setdefault("user_budget", 2200)
    return asyncio.run(tool.invoke({"today": TODAY, **q}))


def part(slot, model, price, **specs):
    return {"slot": slot, "model": model, "price": price, "currency": "SGD", "shop": "Example Shop",
            "url": f"https://shop.example.com/{slot}", "checked_date": "2026-11-02", "specs": specs}


MAIN = {"key": "main", "name": {"zh": "2K 游戏主机", "en": "1440p gaming PC"}, "budget": 2200, "currency": "SGD", "parts": [
    part("cpu", "AMD Ryzen 7 7700", 349, socket="AM5", tdp_w=88, memory_types=["DDR5"], has_igpu=True, boxed_cooler=True),
    part("motherboard", "B650M board", 199, socket="AM5", chipset="B650", form_factor="mATX", memory_type="DDR5",
         ram_slots=4, m2_slots=2, m2_slot_names=["M2_1", "M2_2"], eps8_required=1),
    part("ram", "32GB DDR5-6000 (2×16GB)", 139, memory_type="DDR5", modules=2, capacity_gb_per_module=16, speed_mts=6000),
    part("gpu", "RTX 5070 12GB", 899, length_mm=300, board_power_w=250, power_connectors={"12v-2x6": 1}),
    part("storage", "2TB NVMe SSD", 169, interface="m2_nvme"),
    part("psu", "750W Gold ATX", 129, wattage_w=750, form_factor="ATX", connectors={"12v-2x6": 1, "pcie8": 2, "eps8": 2}),
    part("case", "mATX mesh case", 99, supported_form_factors=["mATX", "ITX"], max_gpu_length_mm=338, max_cooler_height_mm=165,
         radiator_mounts=[240, 280], psu_form_factors=["ATX"], depth_mm=410, width_mm=215, height_mm=430),
    part("cooler", "Dual-tower air cooler", 69, cooler_type="air", height_mm=155, sockets=["AM5", "AM4", "LGA1700"]),
]}
BUDGET = copy.deepcopy(MAIN)
BUDGET.update(key="budget", name={"zh": "省钱版", "en": "Budget variant"}, budget=1800)
BUDGET["parts"][3] = part("gpu", "RX 9060 XT 16GB", 579, length_mm=280, board_power_w=180, power_connectors={"pcie8": 2})
PERF = copy.deepcopy(MAIN)
PERF.update(key="performance", name={"zh": "性能版", "en": "Performance variant"}, budget=2800)
PERF["parts"][3] = part("gpu", "RTX 5070 Ti 16GB", 1299, length_mm=330, board_power_w=300, power_connectors={"12v-2x6": 1})
PERF["parts"][5] = part("psu", "850W Gold ATX", 159, wattage_w=850, form_factor="ATX", connectors={"12v-2x6": 1, "pcie8": 2, "eps8": 2})

MD_DIR = Path(tempfile.mkdtemp(prefix="pc_md_"))
REPORT_MD = """# 2K 游戏主机方案 · 1440p Gaming PC Plan

{{kpis}}

## 一、方案摘要 · 1. Summary

一台均衡的 2K 游戏主机，预算内并留有升级空间。
A balanced 1440p gaming PC within budget, with room to upgrade.

{{budget_chart}}

## 二、配件清单 · 2. Parts list

{{parts:main}}

## 三、兼容性报告 · 3. Compatibility report

{{compat}}

{{power_chart}}

## 五、装机指南 · 5. Assembly guide

{{board_map}}

1. 在主板盒上安装处理器。 Install the CPU on the board, on top of its box.
2. 把内存插到 A2 和 B2。 Fit the RAM in A2 and B2.
3. 把系统盘装到 M2_1。 Install the boot drive in M2_1.

<script>document.title='pwned'</script>

## 六、资料来源 · 6. Sources and notes

- Example spec page: https://example.com/spec
"""
REPORT = MD_DIR / "report.md"
REPORT.write_text(REPORT_MD, encoding="utf-8")
SLOTS = {"ram_slots_to_use": ["A2", "B2"], "m2_boot_slot": "M2_1"}


def md_file(text, name):
    f = MD_DIR / name
    f.write_text(text, encoding="utf-8")
    return str(f)


r = call(action="validate", builds=[MAIN, BUDGET, PERF])
check("good builds validate with no hard fail", r["success"] and r["can_export"], r)
main = r["builds"][0]
rules = {x["rule"]: x["status"] for x in main["results"]}
check("socket, memory, board, GPU, cooler, PSU all pass", all(rules.get(k) == "pass" for k in (
    "cpu_socket", "memory_type", "ram_slots", "board_fit", "gpu_length", "cooler_height", "cooler_socket", "psu_wattage",
    "psu_gpu_connectors", "psu_eps", "psu_fit", "m2_slots")), rules)
check("power estimate", main["power"]["estimated_w"] == 88 + 250 + 60 + 8 and main["power"]["recommended_psu_w"] == round(406 * 1.3), main["power"])
check("total and budget", main["total"] == 2052 and rules["budget"] == "pass", main["total"])
check("Chinese and English in every result", all(x["zh"] and x["en"] for x in main["results"]))

bad = copy.deepcopy(MAIN)
bad["parts"][0]["specs"]["socket"] = "LGA1851"
bad["parts"][2]["specs"]["memory_type"] = "DDR4"
bad["parts"][3]["specs"]["length_mm"] = 350
bad["parts"][5]["specs"]["wattage_w"] = 350
bad["parts"][5]["specs"]["connectors"] = {"pcie8": 2, "eps8": 1}
bad["parts"][6]["specs"]["supported_form_factors"] = ["ITX"]
bad["parts"][7]["specs"]["height_mm"] = 170
bad["parts"][1]["checked_date"] = "2026-10-01"
r = call(action="validate", builds=[bad])
fails = {x["rule"] for x in r["builds"][0]["results"] if x["status"] == "fail"}
want = {"cpu_socket", "memory_type", "gpu_length", "psu_wattage", "psu_gpu_connectors", "board_fit", "cooler_height", "price_age"}
check("each injected fault is a hard fail", want <= fails, fails)
check("bad build cannot export", r["success"] and not r["can_export"])
out = Path(tempfile.mkdtemp()) / "bad.pdf"
r = call(action="export", builds=[bad], markdown_path=str(REPORT), output_path=str(out))
check("export refuses a failing build", not r["success"] and "失败" in r["error"] and not out.exists(), r)

aio = copy.deepcopy(MAIN)
aio["parts"][7] = part("cooler", "360mm AIO", 159, cooler_type="aio", radiator_mm=360, sockets=["AM5"])
r = call(action="validate", builds=[aio])
check("unsupported radiator size fails", any(x["rule"] == "radiator_fit" and x["status"] == "fail" for x in r["builds"][0]["results"]))
nocool = copy.deepcopy(MAIN)
nocool["parts"].pop(7)
r = call(action="validate", builds=[nocool])
check("boxed cooler is a warning, not a fail", r["can_export"] and any(x["rule"] == "cooler" and x["status"] == "warn" for x in r["builds"][0]["results"]))
unk = copy.deepcopy(MAIN)
unk["parts"][3]["specs"].pop("length_mm")
r = call(action="validate", builds=[unk])
check("missing spec is unknown, not pass", any(x["rule"] == "gpu_length" and x["status"] == "unknown" for x in r["builds"][0]["results"]))
low = copy.deepcopy(MAIN)
low["parts"][5]["specs"]["wattage_w"] = 450
r = call(action="validate", builds=[low])
check("thin PSU headroom warns", any(x["rule"] == "psu_wattage" and x["status"] == "warn" for x in r["builds"][0]["results"]))
cur = copy.deepcopy(MAIN)
cur["parts"][4]["currency"] = "USD"
r = call(action="validate", builds=[cur])
check("mixed currency fails", any(x["rule"] == "currency" and x["status"] == "fail" for x in r["builds"][0]["results"]))
r = call(action="validate", builds=[{**MAIN, "parts": [{**MAIN["parts"][0], "url": "not a link"}]}])
check("price without a real link is rejected", not r["success"], r)
r = call(action="validate", builds=[{**MAIN, "name": {"zh": "只有中文"}}])
check("missing English text is rejected", not r["success"], r)
r = call(action="validate", builds=[MAIN, {**BUDGET, "key": "main"}])
check("duplicate build keys rejected", not r["success"])

tmp_pdf = lambda: str(Path(tempfile.mkdtemp()) / "x.pdf")
r = call(action="export", builds=[MAIN], user_budget=None, markdown_path=str(REPORT), output_path=tmp_pdf())
check("export needs user_budget", not r["success"] and "user_budget" in r["error"], r)
inflated = copy.deepcopy(MAIN)
inflated["budget"] = 5000
r = call(action="validate", builds=[inflated], user_budget=2000)
b0 = r["builds"][0]
check("user_budget overrides a build's own budget", b0["budget"] == 2000 and any(
    x["rule"] == "budget" and x["status"] == "warn" for x in b0["results"]) and r["notes"], r)
r = call(action="validate", builds=[inflated])
check("without user_budget the build's budget is used", r["builds"][0]["budget"] == 5000)
r = call(action="export", builds=[MAIN], output_path=tmp_pdf())
check("export needs markdown_path", not r["success"] and "markdown_path" in r["error"], r)
r = call(action="export", builds=[MAIN], markdown_path=md_file("Only English text here https://example.com", "en.md"), output_path=tmp_pdf())
check("export needs bilingual markdown", not r["success"] and "双语" in r["error"], r)
r = call(action="export", builds=[MAIN], markdown_path=md_file("中文 and English, no links", "nolink.md"), output_path=tmp_pdf())
check("export needs source links", not r["success"] and "链接" in r["error"], r)
r = call(action="export", builds=[MAIN], markdown_path=md_file("中文 English https://a.b\n\n{{nope}}\n", "bad.md"), output_path=tmp_pdf())
check("unknown placeholder is rejected", not r["success"] and "nope" in r["error"], r)
r = call(action="export", builds=[MAIN], markdown_path=md_file("中文 English https://a.b see {{board_map}} inline", "inl.md"), output_path=tmp_pdf())
check("inline placeholder is rejected", not r["success"] and "单独占一行" in r["error"], r)
r = call(action="export", builds=[MAIN], markdown_path=str(REPORT), output_path="relative.pdf")
check("export needs an absolute .pdf path", not r["success"])

pdf_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp())
for order in ("zh-en", "en-zh"):
    out = pdf_dir / f"sample-{order}.pdf"
    out.unlink(missing_ok=True)
    r = call(action="export", builds=[MAIN, BUDGET, PERF], markdown_path=str(REPORT), output_path=str(out), language_order=order, **SLOTS)
    check(f"export writes a PDF ({order})", r["success"] and out.exists() and out.read_bytes()[:4] == b"%PDF", r)
r = call(action="export", builds=[MAIN, BUDGET, PERF], markdown_path=str(REPORT), output_path=str(pdf_dir / "sample-zh-en.pdf"))
check("export never overwrites", not r["success"] and "已存在" in r["error"], r)

inp = bc.Input.model_validate({"action": "export", "builds": [MAIN, BUDGET, PERF], "today": TODAY, **SLOTS})
html = bc.render_html(inp, [bc.check_build(b, bc.date(2026, 11, 3)) for b in inp.builds], bc.date(2026, 11, 3), REPORT_MD)
check("raw HTML in markdown is not executed", "<script>" not in html and "&lt;script&gt;" in html)
check("missing required blocks go to the appendix", "Appendix" in html and html.index("Appendix") < html.rindex("<svg"))
check("placeholders are all replaced", "{{" not in html and "PCBLOCK" not in html)
for frag in ("一、方案摘要", "1. Summary", "Compatibility report", "Assembly guide", "Sources and notes",
             "示意图，非实物比例", "<svg", "A2", "M2_1", "<table"):
    check(f"report contains {frag!r}", frag in html)

check("slot names match loosely", bc._match_slots(["DDR5_A", "DDR5_B"], ["DDR5_A1", "DDR5_B1"]) == ({0, 1}, True)
      and bc._match_slots(["A2", "B2"], ["DDR5_A1", "DDR5_A2", "DDR5_B1", "DDR5_B2"]) == ({1, 3}, True))
check("ambiguous slot name is not guessed", bc._match_slots(["A"], ["A1", "A2", "B1", "B2"]) == (set(), False))

# 每个图表元素都必须在自身 viewBox 内（用无头浏览器量 getBBox）
browser = bc._browser()
if browser and any(k in browser.lower() for k in ("chrome", "chromium", "edge")):
    import json
    import re
    import subprocess
    long = copy.deepcopy([MAIN, BUDGET, PERF])
    for b in long:
        b["name"] = {"zh": b["name"]["zh"] + "（超长名称测试：高刷新率电竞版本）", "en": b["name"]["en"] + " — extra long stress-test name"}
    long[2]["parts"][0]["price"] *= 9
    js = ("<script>window.onload=()=>{const bad=[];document.querySelectorAll('svg').forEach((g,gi)=>{const v=g.viewBox.baseVal;"
          "g.querySelectorAll('text,rect,circle,line,path').forEach(t=>{const b=t.getBBox();if(b.x<v.x-1||b.y<v.y-1||"
          "b.x+b.width>v.x+v.width+1||b.y+b.height>v.y+v.height+1)bad.push(gi+': '+(t.textContent||t.tagName).slice(0,40))})});"
          "document.body.setAttribute('data-bad',JSON.stringify(bad))}</script>")
    for label, builds in (("sample", [MAIN, BUDGET, PERF]), ("long names", long)):
        inp = bc.Input.model_validate({"action": "export", "builds": builds, "today": TODAY, **SLOTS})
        page = bc.render_html(inp, [bc.check_build(b, bc.date(2026, 11, 3)) for b in inp.builds], bc.date(2026, 11, 3), REPORT_MD)
        f = pdf_dir / f"overflow-{label.replace(' ', '-')}.html"
        f.write_text(re.sub(r"<meta http-equiv='Content-Security-Policy'[^>]*>", "", page).replace("</body>", js + "</body>"), encoding="utf-8")
        dom = subprocess.run([browser, "--headless=new", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom", f.as_uri()],
                             capture_output=True, text=True, timeout=120).stdout
        m = re.search(r'data-bad="([^"]*)"', dom)
        bad = json.loads(m.group(1).replace("&quot;", '"')) if m else ["no result"]
        check(f"no diagram element outside its frame ({label})", not bad, bad)
else:
    print("SKIP: overflow check needs Chrome/Chromium")

print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
