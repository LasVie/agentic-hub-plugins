"""中文档案、独立验算摘要与可离线展开的排样图。"""
import csv
from html import escape
from io import StringIO
from pathlib import Path
import re

from contract import Case, VERSION, digest, encoded, write_new

STATUS_ZH = {
    "verified": "候选分配已通过逐件复核",
    "confirmed_no_plan": "独立穷举确认现有库存无可行分配",
    "inconclusive": "搜索达到上限，未确认可行性",
    "blocked": "有待解决的复核问题",
}
STYLE = """
:root{color-scheme:light;font-family:system-ui,"PingFang SC",sans-serif;color:#173235;background:#f4f1e9}
body{max-width:1100px;margin:0 auto;padding:clamp(16px,4vw,48px);line-height:1.55}
header{border-bottom:1px solid #c8d5ca;padding-bottom:20px} h1,h2,h3,p{margin:.4em 0 .6em}
h1{font-size:clamp(24px,4vw,40px)} .intro{color:#455e5d}
.status{border-left:4px solid #236550;padding:12px 16px;background:#e2ecd9;margin:20px 0}
details,.panel{background:#fefcf5;border:1px solid #c8d5ca;border-radius:10px;margin:14px 0;padding:14px 18px}
summary{font-weight:650;cursor:pointer} summary:focus-visible,a:focus-visible{outline:2px solid #1c6451;outline-offset:3px}
.strip{display:flex;overflow:hidden;min-height:34px;margin:12px 0;border:1px solid #203945;border-radius:6px;background:#e1e7df}
.segment{display:block;flex:0 0 auto}.part0{background:#75b5ad}.part1{background:#eaca7d}
.trim{background:#5c7075}.kerf{background:#a24232}.leftover{background:#dbe1d1}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;text-align:left}
th,td{border-bottom:1px solid #d7e0d6;padding:6px 12px 6px 0}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}a{color:#145c4e}
small{display:block;overflow-wrap:anywhere;color:#455e5d}
"""


def csv_rows(review: dict) -> bytes:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["库存编号", "零件编号", "件序号", "成品长度毫米", "每件锯缝毫米", "该库存总余料毫米"])
    for board in review["boards"]:
        for part in board["pieces"]:
            writer.writerow([board["stock_id"], part["id"], part["ordinal"], part["length_mm"],
                             board["kerf_mm"], board["remaining_mm"]])
    return buffer.getvalue().encode("utf-8-sig")


def board_view(board: dict) -> str:
    length = board["length_mm"]

    def segment(amount: int, category: str) -> str:
        return f'<span class="segment {category}" style="width:{amount / length * 100:.6f}%"></span>'

    pieces_html = []
    strip = [segment(board["trim_start_mm"], "trim")]
    for index, piece in enumerate(board["pieces"]):
        strip.append(segment(piece["length_mm"], f"part{index % 2}"))
        strip.append(segment(board["kerf_mm"], "kerf"))
        pieces_html.append(f'<tr><td>{escape(piece["id"])}</td><td>{piece["ordinal"]}</td>'
                           f'<td>{piece["length_mm"]}</td><td>{board["kerf_mm"]}</td></tr>')
    strip.append(segment(board["remaining_mm"], "leftover"))
    strip.append(segment(board["trim_end_mm"], "trim"))
    return (f'<details open><summary>{escape(board["stock_id"])} · 余料 {board["remaining_mm"]} mm</summary>'
            f'<p>{escape(board["material"])} · 原长 {length} mm · 首尾修边 '
            f'{board["trim_start_mm"]} / {board["trim_end_mm"]} mm · 零件及锯缝 {board["used_mm"]} mm</p>'
            f'<div class="strip" aria-hidden="true">{"".join(strip)}</div>'
            '<div class="table"><table><thead><tr><th>零件编号</th><th>第几件</th><th>成品 mm</th><th>锯缝 mm</th>'
            f'</tr></thead><tbody>{"".join(pieces_html)}</tbody></table></div></details>')


def report_html(case: Case, review: dict) -> bytes:
    boards = "".join(board_view(board) for board in review["boards"])
    issues = "".join("<li>" + escape(item["message"]) + "</li>" for item in review["findings"])
    reviews = f"<section class='panel'><h2>复核发现</h2><ul>{issues}</ul></section>" if issues else ""
    exports = '<a href="cuts.csv">下料清单 CSV</a>' if review["verdict"] == "verified" else ""
    return (f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            f'<title>木料定尺下料复核</title><style>{STYLE}</style><body><header><h1>木料定尺下料复核</h1>'
            f'<p class="intro">{escape(case.title)} · v{VERSION} · 整数毫米</p></header>'
            f'<p class="status">{STATUS_ZH[review["verdict"]]}</p>'
            f'<p>{len(case.boards)} 件库存 · {len(case.parts)} 件需求 · 每件锯缝占量 {case.kerf} mm</p>'
            f'{reviews}{boards}'
            '<p>图中深灰为修边，青色或黄色为零件，红色为锯缝，浅灰为余料。点击库存编号可折叠明细。</p>'
            f'<nav>{exports}<a href="evaluation.json">复核数据 JSON</a><a href="review.md">复核说明</a></nav>'
            f'<small>原始案例 SHA-256 {case.sha}</small>'
            '<small>本页用于尺寸与数量核对。现场测量、切削方式和安全条件由用户确认。</small></body></html>').encode("utf-8")


def dossier(case: Case, review: dict, inputs: dict[str, bytes], output: Path) -> dict:
    evaluation = {"version": VERSION, "case_sha256": case.sha, "status": review["verdict"], "review": review,
                  "human_testing_passed": False}
    # Escape Markdown link/image syntax as well as embedded HTML.
    title = re.sub(r"([\\\[\]()`*_!])", r"\\\1", escape(case.title))
    summary = f"# {title}\n\n{STATUS_ZH[review['verdict']]}。\n"
    if review["findings"]:
        summary += "\n" + "".join("- " + item["message"] + "\n" for item in review["findings"])
    summary += f"\n- 原始案例 SHA-256：`{case.sha}`。\n- 锯缝按每件占量计算。人工仍需核对原始测量和现场条件。\n"
    files = {
        "layout.html": report_html(case, review),
        "cuts.csv": csv_rows(review),
        "evaluation.json": encoded(evaluation),
        "review.md": summary.encode("utf-8"),
        **{f"inputs/{name}": raw for name, raw in inputs.items()},
    }
    manifest = {"version": VERSION, "status": review["verdict"], "case_sha256": case.sha,
                "files_sha256": {name: digest(raw) for name, raw in sorted(files.items())},
                "human_testing_passed": False}
    output.mkdir(exist_ok=False)
    (output / "inputs").mkdir()
    for name, raw in files.items():
        write_new(output / name, raw)
    write_new(output / "artifact.json", encoded(manifest))
    return {"status": manifest["status"], "case_sha256": case.sha, "html": str((output / "layout.html").absolute())}
