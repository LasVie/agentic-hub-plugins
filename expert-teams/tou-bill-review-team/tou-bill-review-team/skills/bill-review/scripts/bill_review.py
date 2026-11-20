"""Create evidence-bound local time-of-use bill reports."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from html import escape
import io
import json
from pathlib import Path

from compute import candidate, independent_replay, meter_report
from inputs import InputError, decode_json, digest, json_bytes, load_case, read_bytes, require

VERSION = "1.0.0"


def bound(stage, case, result, **dependencies):
    return {"stage": stage, "inputs_sha256": case.hashes, "version": VERSION, **dependencies, "result": result}


def checked(data, expected, message):
    require(json_bytes(data) == json_bytes(expected), message)


def money(minor):
    return f"{Decimal(minor).scaleb(-2):.2f}"


def energy(micro):
    return f"{Decimal(micro).scaleb(-6):f}".rstrip("0").rstrip(".") or "0"


def comparison(case, totals):
    lines = []
    for band in case.rates:
        billed = case.billed[band]
        billed_minor = int(Decimal(billed["amount"]) * 100)
        billed_micro = int(Decimal(billed["kwh"]) * 1_000_000)
        amount = totals["amount_minor"][band]
        quantity = totals["energy_micro_kwh"][band]
        lines.append({"band": band, "billed_minor": billed_minor, "computed_minor": amount,
                      "difference_minor": billed_minor - amount, "billed_micro_kwh": billed_micro,
                      "computed_micro_kwh": quantity})
    return lines


def interval_csv(case, totals):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["区间起点", "UTC偏移", "原始CSV行", "原始读数", "单位", "分段", "电量kWh", "单价"])
    if totals is not None:
        for (time, line, raw, unit, micro), band in zip(case.readings, totals["interval_bands"], strict=True):
            writer.writerow([time.isoformat(timespec="minutes"), case.offset, line, raw, unit, band, energy(micro), case.rates[band]])
    return buffer.getvalue().encode("utf-8-sig")


def report_html(result):
    status = {"verified": "电量费用已独立复核", "blocked": "待澄清，未给出已验证金额"}[result["status"]]
    caption = "差额为账单数减复算数。原始账单只有分段汇总时，无法据此定位供电方处理了哪一行。"
    lines = result["lines"]
    rows = ""
    summary = ""
    if lines:
        rows = "".join(
            f"<tr><th>{escape(line['band'])}</th><td>{energy(line['billed_micro_kwh'])}</td>"
            f"<td>{energy(line['computed_micro_kwh'])}</td><td>{money(line['billed_minor'])}</td>"
            f"<td>{money(line['computed_minor'])}</td><td>{money(line['difference_minor'])}</td></tr>"
            for line in lines
        )
        summary = (
            f"<table><caption>{caption}</caption><thead><tr><th>费率分段</th><th>账单 kWh</th>"
            "<th>复算 kWh</th><th>账单金额</th><th>复算金额</th><th>差额</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            f"<p class='totals'>账单 {money(result['billed_minor'])}　复算 {money(result['computed_minor'])}"
            f"　差额 {money(result['difference_minor'])} {escape(result['currency'])}</p>"
        )
    warnings = "".join(f"<li>{escape(text)}</li>" for text in result["findings"])
    if warnings:
        warnings = f"<h2>需处理的问题</h2><ul>{warnings}</ul>"
    return f"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>分时用电账单复核</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f3ed;color:#162b2d;font:16px/1.65 system-ui,sans-serif}}
main{{max-width:920px;margin:auto;padding:clamp(20px,5vw,64px)}}h1{{margin:0;font-size:clamp(28px,5vw,44px)}}
.status{{background:#dcece1;border-left:5px solid #17664f;padding:14px 18px;font-weight:650}}
section{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
td,th{{text-align:right;padding:10px 14px;border-bottom:1px solid #c8d7cf}}th:first-child{{text-align:left}}
caption{{text-align:left;padding:6px 0 12px}}a{{color:#135c4e}}.totals{{font-weight:700;font-variant-numeric:tabular-nums}}
</style><main><h1>分时用电账单复核</h1>
<p>v{VERSION} · 费率 {escape(result["tariff_version"])} · UTC{escape(result["utc_offset"])}</p>
<p class="status">{status}</p>
<section>{summary}</section>{warnings}
<p><a href="intervals.csv">区间明细 CSV</a> · <a href="evaluation.json">复核结果 JSON</a> · <a href="artifact.json">证据摘要清单</a></p>
<p>适用范围为所列冻结输入与电量费。请核对源资料和真实成员交接。</p></main></html>
"""


def deliver(case, meter_body, plan_body, review_body, output):
    checked(decode_json(meter_body), meter_report(case), "读数核查报告与当前原始文件不一致。")
    expected_review = bound("replay", case, independent_replay(case))
    checked(decode_json(review_body), expected_review, "独立复算报告与当前原始文件不一致。")
    observed_plan = decode_json(plan_body)
    require(isinstance(observed_plan, dict), "候选报告必须为对象。")
    expected_plan = bound("calculate", case, candidate(case), meter_sha256=digest(meter_body))
    checked({k: v for k, v in observed_plan.items() if k != "result"},
            {k: v for k, v in expected_plan.items() if k != "result"},
            "候选报告的输入或上游交接摘要不一致。")
    verified = (
        json_bytes(observed_plan.get("result")) == json_bytes(expected_plan["result"])
        == json_bytes(expected_review["result"])
    )
    totals = expected_review["result"] if verified else None
    lines = comparison(case, totals) if verified else []
    result = {"status": "verified" if verified else "blocked", "version": VERSION, "human_testing_passed": False,
              "currency": case.currency, "utc_offset": case.offset, "tariff_version": case.tariff_version,
              "billing_start": case.start.isoformat(timespec="minutes"), "billing_end": case.end.isoformat(timespec="minutes"),
              "lines": lines, "findings": [] if verified else ["候选分段、电量或金额与独立复算不一致。"]}
    if verified:
        for column in ("billed_minor", "computed_minor", "difference_minor"):
            result[column] = sum(line[column] for line in lines)
    files = {"inputs/" + name: body for name, body in case.snapshots.items()}
    files.update({"handoffs/meter.json": meter_body, "handoffs/candidate.json": plan_body,
                  "handoffs/independent.json": review_body, "intervals.csv": interval_csv(case, totals),
                  "evaluation.json": json_bytes(result), "review.html": report_html(result).encode("utf-8")})
    manifest = {"version": VERSION, "status": result["status"], "files_sha256": {k: digest(v) for k, v in files.items()}}
    files["artifact.json"] = json_bytes(manifest)
    # Exclusive creation preserves previous runs. The manifest is written last; interruption cannot
    # leave a partial dossier with a completion manifest.
    output.mkdir()
    for name, body in files.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        with path.open("xb") as stream:
            stream.write(body)
    return result


def main():
    parser = argparse.ArgumentParser(description="离线核查分时电量费用，输出可追溯证据。",
                                     usage="bill_review.py {inspect,calculate,replay,deliver} --case 目录 --output 路径")
    parser.add_argument("stage", choices=("inspect", "calculate", "replay", "deliver"), help="核查、候选计算、独立复算或交付")
    parser.add_argument("--case", required=True, type=Path, help="原始三文件所在目录")
    parser.add_argument("--output", required=True, type=Path, help="全新报告文件或交付目录")
    parser.add_argument("--meter", type=Path, help="读数核查报告")
    parser.add_argument("--candidate", type=Path, help="候选报告")
    parser.add_argument("--independent", type=Path, help="独立复算报告")
    args = parser.parse_args()
    try:
        require(not args.output.exists() and not args.output.is_symlink(), "输出路径已存在，请使用新的路径。")
        case = load_case(args.case)
        required = {"inspect": set(), "calculate": {"meter"}, "replay": set(),
                    "deliver": {"meter", "candidate", "independent"}}[args.stage]
        provided = {name for name in ("meter", "candidate", "independent") if getattr(args, name) is not None}
        require(provided == required, "当前步骤的交接报告参数不正确。")
        if args.stage == "deliver":
            result = deliver(case, read_bytes(args.meter), read_bytes(args.candidate),
                             read_bytes(args.independent), args.output)
        else:
            if args.stage == "inspect":
                result = meter_report(case)
            elif args.stage == "calculate":
                body = read_bytes(args.meter)
                checked(decode_json(body), meter_report(case), "读数核查报告与当前原始文件不一致。")
                result = bound("calculate", case, candidate(case), meter_sha256=digest(body))
            else:
                result = bound("replay", case, independent_replay(case))
            with args.output.open("xb") as stream:
                stream.write(json_bytes(result))
        print(json.dumps({"ok": True, "status": result.get("status", "recorded"), "version": VERSION,
                          "output": str(args.output)}, ensure_ascii=False))
        return 0
    except InputError as error:
        message = str(error)
    except (ValueError, csv.Error):
        message = "文件编码或 CSV／JSON 格式无效。"
    except OSError:
        message = "文件不可读或输出不可写。请确认文件存在、权限正确且输出路径为新路径。"
    print(json.dumps({"ok": False, "status": "blocked", "message": message, "version": VERSION}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
