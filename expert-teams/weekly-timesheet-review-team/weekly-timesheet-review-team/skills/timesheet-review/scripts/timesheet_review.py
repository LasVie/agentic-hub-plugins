"""按原始记录独立计算、复核并交付单人工时清单。"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from hashlib import sha256
from html import escape
from io import StringIO
from itertools import combinations
import json
from pathlib import Path
import re
import sys

VERSION = "1.0.0"
DAY = 1440
LIMIT = 300
INPUT_LIMIT = 512 * 1024
REQUIRED = {"project", "start", "end"}
BREAK = {"break_start", "break_end"}
MESSAGES = {
    "invalid_row": "字段数量与表头不一致",
    "invalid_project": "项目或班次标签缺失或无效",
    "invalid_time": "起止日期时间缺失或无效",
    "invalid_duration": "起止顺序无效或超过 24 小时",
    "invalid_break": "休息须提供有效的起止时间，且位于记录内",
    "outside_week": "周内没有工作分钟",
    "duplicate": "原始记录重复，请核对保留哪一行",
    "overlap": "工时重叠，请核对各行实际归属",
    "expected_day_unconfirmed": "预计日期没有可汇总工时，请核实记录",
}


class ReviewError(ValueError):
    pass


def read_bytes(path, limit=INPUT_LIMIT):
    if not path.is_file() or path.is_symlink():
        raise ReviewError("输入须为可读的普通文件")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ReviewError("输入文件超过体积上限")
    return raw


def load_json(raw):
    def unique(pairs):
        value = dict(pairs)
        if len(value) != len(pairs):
            raise ReviewError("JSON 有重复字段")
        return value

    try:
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ReviewError("JSON 必须是有效的 UTF-8 且字段唯一") from exc


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(raw):
    return sha256(raw).hexdigest()


def local_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError
    return date.fromisoformat(value)


def minute(value):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", value):
        raise ValueError
    clock = datetime.fromisoformat(value)
    return clock.toordinal() * DAY + clock.hour * 60 + clock.minute


def day_text(value):
    return date.fromordinal(value).isoformat()


def parse_settings(raw):
    settings = load_json(raw)
    if not isinstance(settings, dict) or not {"week_start", "utc_offset"} <= settings.keys() or settings.keys() - {"week_start", "utc_offset", "expected_days"}:
        raise ReviewError("周设置须明确 week_start 和 utc_offset，可填写 expected_days")
    try:
        first = local_day(settings["week_start"]).toordinal()
    except ValueError as exc:
        raise ReviewError("周起始日期须为 YYYY-MM-DD") from exc
    if first + 7 > date.max.toordinal():
        raise ReviewError("无法表示该周的结束日期")
    offset = settings["utc_offset"]
    if not isinstance(offset, str) or not re.fullmatch(r"[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00)", offset) or offset == "-00:00":
        raise ReviewError("请提供明确的固定 UTC 偏移，例如 +08:00")
    expected = settings.get("expected_days", [])
    try:
        days = [local_day(value).toordinal() for value in expected] if isinstance(expected, list) else []
    except ValueError as exc:
        raise ReviewError("预计日期须为周内的 YYYY-MM-DD 日期") from exc
    if not isinstance(expected, list) or len(days) != len(set(days)) or any(not first <= value < first + 7 for value in days):
        raise ReviewError("预计日期须为互不重复的周内日期")
    return first, offset, sorted(days)


def finding(code, rows=(), **details):
    return {"code": code, "rows": list(rows), "message": MESSAGES[code], **details}


def parse_entry(record, line):
    label = record["project"]
    if not label or len(label) > 100 or not label.isprintable():
        return finding("invalid_project", [line])
    try:
        start, end = minute(record["start"]), minute(record["end"])
    except ValueError:
        return finding("invalid_time", [line])
    if not 0 < end - start <= DAY:
        return finding("invalid_duration", [line])
    break_start, break_end = record.get("break_start", ""), record.get("break_end", "")
    if break_start or break_end:
        try:
            pause_start, pause_end = minute(break_start), minute(break_end)
        except ValueError:
            return finding("invalid_break", [line])
        if not start <= pause_start < pause_end <= end or pause_end - pause_start == end - start:
            return finding("invalid_break", [line])
        segments = [(a, b) for a, b in ((start, pause_start), (pause_end, end)) if a < b]
    else:
        segments = [(start, end)]
    return line, label, segments, (label, start, end, break_start, break_end)


def parse_entries(raw, first):
    low, high = first * DAY, (first + 7) * DAY
    entries, issues = [], []
    try:
        reader = csv.reader(StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        header = next(reader, [])
        fields = set(header)
        if len(header) != len(fields) or fields not in (REQUIRED, REQUIRED | BREAK):
            raise ReviewError("CSV 表头须为 project,start,end，另可同时提供 break_start,break_end")
        count = 0
        while True:
            line = reader.line_num + 1
            try:
                row = next(reader)
            except StopIteration:
                break
            if not row:
                continue
            count += 1
            if count > LIMIT:
                raise ReviewError("每周最多复核 300 条记录")
            if len(row) != len(header):
                issues.append(finding("invalid_row", [line]))
                continue
            entry = parse_entry(dict(zip(header, (value.strip() for value in row))), line)
            if isinstance(entry, dict):
                issues.append(entry)
                continue
            source, project, segments, identity = entry
            clipped = [(max(low, a), min(high, b)) for a, b in segments if max(low, a) < min(high, b)]
            if clipped:
                entries.append((source, project, clipped, identity))
            else:
                issues.append(finding("outside_week", [line]))
    except (UnicodeError, csv.Error) as exc:
        raise ReviewError("CSV 须为有效的 UTF-8，且引号与行格式正确") from exc
    if not count:
        raise ReviewError("CSV 没有工时记录")
    return entries, issues, count


def analyze_times(entries, first):
    totals, overlap = {}, Counter()
    segments = sorted((a, b, row) for row, _, parts, _ in entries for a, b in parts)
    active = []
    for start, end, row in segments:
        active = [(stop, number) for stop, number in active if stop > start]
        for stop, number in active:
            overlap[tuple(sorted((row, number)))] += min(stop, end) - start
        active.append((end, row))
        duration = totals.setdefault(row, Counter())
        while start < end:
            day = start // DAY
            boundary = min(end, (day + 1) * DAY)
            duration[day] += boundary - start
            start = boundary
    return totals, overlap


def review_times(entries, first):
    totals, overlap = {}, Counter()
    for row, _, parts, _ in entries:
        totals[row] = {day: span for day in range(first, first + 7)
                       if (span := sum(max(0, min(b, (day + 1) * DAY) - max(a, day * DAY))
                                       for a, b in parts))}
    for left, right in combinations(entries, 2):
        minutes = sum(max(0, min(b, d) - max(a, c))
                      for a, b in left[2] for c, d in right[2])
        if minutes:
            overlap[(left[0], right[0])] = minutes
    return totals, overlap


def evaluate(entries, issues, first, expected, method):
    totals, overlap = method(entries, first)
    identical = defaultdict(list)
    for row, _, _, identity in entries:
        identical[identity].append(row)
    repeated = [group for group in identical.values() if len(group) > 1]
    findings = [*issues, *(finding("duplicate", group) for group in repeated)]
    duplicate_pairs = {pair for group in repeated for pair in combinations(group, 2)}
    for pair, minutes in sorted(overlap.items()):
        if pair not in duplicate_pairs:
            findings.append(finding("overlap", pair, minutes=minutes))

    held = {row for issue in findings if issue["code"] != "outside_week" for row in issue["rows"]}
    days, projects, rows = Counter(), Counter(), []
    for row, project, _, _ in entries:
        per_day = totals[row]
        included = row not in held
        if included:
            days.update(per_day)
            projects[project] += sum(per_day.values())
        rows.append({"row": row, "project": project, "minutes": sum(per_day.values()),
                     "included": included,
                     "days": {day_text(day): value for day, value in sorted(per_day.items())}})
    findings.extend(finding("expected_day_unconfirmed", date=day_text(day)) for day in expected if not days[day])
    return {
        "status": "reviewed_with_holds" if held or any(issue["code"] == "expected_day_unconfirmed" for issue in findings) else "reviewed",
        "rows": rows,
        "held_rows": sorted(held),
        "days": {day_text(day): days[day] for day in range(first, first + 7)},
        "projects": dict(sorted(projects.items())),
        "included_minutes": sum(days.values()),
        "findings": findings,
    }


def report(kind, inputs, result):
    return {"version": VERSION, "kind": kind, "inputs": inputs, "result": result}


def require_report(path, expected, name):
    raw = read_bytes(path, 16 * 1024 * 1024)
    if raw != encoded(expected):
        raise ReviewError(f"{name}与当前原始输入、计算结果或报告格式不一致")
    return raw


def html_page(result, inputs):
    title = "每周工时记录复核"
    status = "部分记录或日期待核实" if result["status"] == "reviewed_with_holds" else "工时复核完成"
    daily = "".join(f"<tr><th>{day}</th><td>{value}</td></tr>" for day, value in result["days"].items())
    projects = "".join(f"<tr><th>{escape(project)}</th><td>{value}</td></tr>"
                       for project, value in result["projects"].items())
    findings = []
    for issue in result["findings"][:100]:
        source = "、".join(map(str, issue["rows"])) or issue.get("date", "")
        minutes = f"（{issue['minutes']} 分钟）" if "minutes" in issue else ""
        prefix = f"来源 {source} · " if source else ""
        findings.append(f"<li>{prefix}{issue['message']}{minutes}</li>")
    if len(result["findings"]) > 100:
        findings.append("<li>仅显示前 100 条，完整列表见逐行复核 JSON。</li>")
    issue_list = "".join(findings) or "<li>本周记录未发现需更正的项目。</li>"
    return f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
body{{margin:0;background:#f2f5f4;color:#163038;font:16px/1.5 system-ui,sans-serif}}
main{{max-width:820px;margin:auto;padding:28px}}h1{{font-size:2rem;margin:0}}
section{{background:white;border:1px solid #c9d9d7;border-radius:12px;padding:16px 20px;margin:18px 0}}
.status{{border-left:5px solid #286a61;background:#dcece7;padding:12px}}table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:6px;border-bottom:1px solid #d6dfde}}a{{color:#155a52}}
</style><main><h1>{title}</h1><p>{inputs['week_start']} 起七天 · UTC{inputs['utc_offset']} · v{VERSION}</p>
<p class="status">{status} · 已纳入 {result['included_minutes']} 分钟</p>
<section><h2>需核实的记录</h2><ul>{issue_list}</ul></section>
<section><h2>按日汇总（分钟）</h2><table>{daily}</table></section>
<section><h2>按项目汇总（分钟）</h2><table>{projects}</table></section>
<p>暂缓行未计入汇总。预计日期无记录时请核对来源。源文件更正及工时提交由用户办理。</p>
<p><a href="evaluation.json">逐行复核 JSON</a> · <a href="artifact.json">文件摘要清单</a></p></main></html>
""".encode()


def write_new(path, raw):
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as exc:
        raise ReviewError("输出路径已存在，请换一个新路径") from exc


def deliver(directory, raw_case, raw_entries, baseline, candidate, review, inputs, result):
    try:
        directory.mkdir()
    except FileExistsError as exc:
        raise ReviewError("交付目录已存在，请换一个新目录") from exc
    snapshot = {
        "checklist.html": html_page(result, inputs), "evaluation.json": encoded(report("evaluation", inputs, result)),
        "inputs/week.json": raw_case, "inputs/entries.csv": raw_entries,
        "inputs/baseline.json": baseline, "inputs/analysis.json": candidate, "inputs/review.json": review,
    }
    (directory / "inputs").mkdir()
    for name, raw in snapshot.items():
        write_new(directory / name, raw)
    manifest = {"version": VERSION, "status": result["status"], "human_testing_passed": False,
                "files_sha256": {name: digest(raw) for name, raw in snapshot.items()}}
    write_new(directory / "artifact.json", encoded(manifest))


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "参数不完整或无效。运行 --help 查看用法。\n")


def run():
    parser = ChineseParser(add_help=False, usage="%(prog)s 阶段 --case 周设置.json --entries 原始记录.csv --output 新路径",
                           description="单人工时复核。阶段：baseline 独立初核、analyze 计算、verify 复核、deliver 交付。")
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示用法")
    parser.add_argument("stage", choices=["baseline", "analyze", "verify", "deliver"], help="复核阶段")
    for name, label in {"case": "周设置 JSON", "entries": "原始 CSV", "output": "尚不存在的输出路径"}.items():
        parser.add_argument(f"--{name}", required=True, type=Path, metavar=label, help=label)
    for name, label in {"baseline": "初核 JSON", "analysis": "分析 JSON", "review": "正式复核 JSON"}.items():
        parser.add_argument(f"--{name}", type=Path, metavar=label, help=label)
    args = parser.parse_args()
    raw_case, raw_entries = read_bytes(args.case), read_bytes(args.entries)
    first, offset, expected = parse_settings(raw_case)
    entries, issues, count = parse_entries(raw_entries, first)
    inputs = {"week_start": day_text(first), "utc_offset": offset, "source_rows": count,
              "case_sha256": digest(raw_case), "entries_sha256": digest(raw_entries)}
    method = analyze_times if args.stage == "analyze" else review_times
    result = evaluate(entries, issues, first, expected, method)
    if args.stage in {"baseline", "analyze"}:
        write_new(args.output, encoded(report(args.stage, inputs, result)))
    else:
        if args.baseline is None or args.analysis is None:
            raise ReviewError("复核和交付均须提供初核及分析报告")
        baseline = require_report(args.baseline, report("baseline", inputs, result), "独立初核报告")
        analysis = require_report(args.analysis, report("analyze", inputs, result), "候选分析报告")
        verdict = report("review", inputs, result)
        verdict["reports_sha256"] = {"baseline": digest(baseline), "analysis": digest(analysis)}
        if args.stage == "verify":
            write_new(args.output, encoded(verdict))
        else:
            if args.review is None:
                raise ReviewError("交付须提供正式复核报告")
            review = require_report(args.review, verdict, "正式复核报告")
            deliver(args.output, raw_case, raw_entries, baseline, analysis, review, inputs, result)
    print(json.dumps({"ok": True, "status": result["status"], "minutes": result["included_minutes"],
                      "message": "本阶段已完成", "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        run()
    except ReviewError as error:
        print(json.dumps({"ok": False, "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except OSError:
        print('{"ok":false,"message":"读写失败，请检查权限与父目录；保留现有文件并换新路径重试"}', file=sys.stderr)
        sys.exit(1)
