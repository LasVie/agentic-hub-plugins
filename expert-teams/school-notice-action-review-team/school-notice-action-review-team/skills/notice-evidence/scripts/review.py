"""家校通知核对阶段入口。"""

import argparse
import csv
import json
from pathlib import Path
import sys

from checklist import compare, resolve
from evidence import fingerprint, observations, read_json, require, validate_bundle


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def seal(bundle, extraction, role):
    return {"version": 1, "role": role, "source_sha256": fingerprint(bundle),
            "extraction": extraction, "records": observations(bundle, extraction)}


def read_sealed(path, bundle, role):
    record = read_json(path)
    require(isinstance(record, dict) and "extraction" in record, f"缺少{role}回执")
    expected = seal(bundle, record["extraction"], role)
    require(fingerprint(record) == fingerprint(expected), f"{role}回执已改动或与当前通知不符")
    return record


def verification(bundle, draft, baseline):
    accepted, disagreements = compare(draft["records"], baseline["records"])
    result = resolve(bundle, accepted, disagreements)
    return {"source_sha256": fingerprint(bundle), "draft_sha256": fingerprint(draft),
            "baseline_sha256": fingerprint(baseline), "notice_count": len(bundle["notices"]),
            "agreed_observations": len(accepted), "disputed_observations": len(disagreements),
            **result}


def markdown(value):
    return "".join("\\" + char if char in r"\`*_{}[]()<>!|&" else char for char in str(value))


def render(out, bundle, receipt):
    kids = bundle["children"]

    def child_label(key):
        return kids[key]["label"] if key else "适用对象待确认"

    def when(day, time):
        if day:
            return day + " " + (time or "未给时刻")
        return "日期待确认"

    lines = ["# 家校待办清单", "", f"核对范围 {bundle['start']} 至 {bundle['end']}。"
             f"共核对 {receipt['notice_count']} 份通知。", "", "## 已核对事项", ""]
    if not receipt["actions"]:
        lines.append("给定通知内没有可列入本期的已核对事项。")
    for entry in receipt["actions"]:
        owner = f" · 照护人 {markdown(entry['caregiver'])}" if entry["caregiver"] else ""
        lines.append(f"- [ ] {when(entry['date'], entry['time'])} · {markdown(child_label(entry['child']))}{owner} · "
                     f"{markdown(entry['quote'])} · 来源 {entry['ref']}")
    lines += ["", "## 变更记录", ""]
    if not receipt["changes"]:
        lines.append("给定通知内无已核对变更。")
    for entry in receipt["changes"]:
        new = ("取消" if entry["op"] == "取消" else when(entry["new_date"], entry["new_time"]))
        lines.append(f"- {markdown(child_label(entry['child']))} · {when(entry['old_date'], entry['old_time'])} → {new} · "
                     f"{entry['old_ref']} → {entry['new_ref']}")
    lines += ["", "## 待确认", ""]
    if not receipt["pending"]:
        lines.append("给定通知内无待确认条目。")
    for entry in receipt["pending"]:
        lines.append(f"- {markdown(child_label(entry['child']))} · {markdown(entry['quote'])} · "
                     f"{entry['reason']} · 来源 {entry['ref']}")
    lines.extend(("", "日期用于排序；原文写明“之前”等条件时，行动仍按原文。出处格式为通知代号、行号和起始字符位置。", ""))

    out.mkdir(parents=True, exist_ok=False)
    (out / "checklist.md").write_text("\n".join(lines), encoding="utf-8")
    with (out / "changes.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["孩子代号", "操作", "旧出处", "新出处", "旧日期", "旧时刻", "新日期", "新时刻"])
        for e in receipt["changes"]:
            writer.writerow([e[name] for name in ("child", "op", "old_ref", "new_ref",
                                                   "old_date", "old_time", "new_date", "new_time")])
    write(out / "audit.json", receipt)


class ChineseParser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage:", "用法：", 1)

    def format_help(self):
        return (super().format_help().replace("usage:", "用法：", 1)
                .replace("positional arguments:", "阶段：").replace("options:", "选项：")
                .replace("show this help message and exit", "查看帮助并退出"))

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "核对停止：阶段或参数无效，请查看 --help。\n")


def parser():
    cli = ChineseParser(description="核对本地学校通知、适用对象、期限和更正")
    cli.add_argument("stage", choices=("baseline", "draft", "verify", "deliver"), help="本次执行的阶段")
    cli.add_argument("--source", type=Path, required=True, help="原始通知 JSON")
    cli.add_argument("--extraction", type=Path, help="本成员独立填写的摘录 JSON")
    cli.add_argument("--draft", type=Path, help="分析员的 draft.json")
    cli.add_argument("--baseline", type=Path, help="核验员的 baseline.json")
    cli.add_argument("--receipt", type=Path, help="核验员的 verification.json")
    cli.add_argument("--out", type=Path, required=True, help="此前不存在的阶段输出目录")
    return cli


def main():
    args = parser().parse_args()
    try:
        bundle = validate_bundle(read_json(args.source))
        if args.stage in {"baseline", "draft"}:
            require(args.extraction and not (args.baseline or args.draft or args.receipt),
                    "独立摘录阶段仅接收原始通知及本成员摘录")
            result = seal(bundle, read_json(args.extraction), args.stage)
        else:
            require(args.draft and args.baseline and not args.extraction, "核对阶段须同时接收两份独立回执")
            draft = read_sealed(args.draft, bundle, "draft")
            baseline = read_sealed(args.baseline, bundle, "baseline")
            result = verification(bundle, draft, baseline)
            if args.stage == "deliver":
                require(args.receipt and fingerprint(read_json(args.receipt)) == fingerprint(result),
                        "缺少当前资料对应的有效核验回执")
                render(args.out, bundle, result)
                print("中文清单、变更表与审计记录已生成")
                return 0
        args.out.mkdir(parents=True, exist_ok=False)
        target = "verification.json" if args.stage == "verify" else args.stage + ".json"
        write(args.out / target, result)
        print(f"阶段回执已生成 {args.out.resolve() / target}")
        return 0
    except FileExistsError:
        print("核对停止：输出目录或文件已存在，请使用新的目录", file=sys.stderr)
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        print(f"核对停止：{error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
