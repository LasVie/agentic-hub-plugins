"""由 UTC 枚举和分钟掩码独立复算例会；不导入规划器。"""
from datetime import timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/meeting-evidence/scripts"))
from contract import (ChineseParser, MINUTE, UTC, canonical, cli, input_state,
                      intake, read, require, stamp, wall_at, write)


def possible_utc(target, zone):
    # datetime 保证有效偏移的绝对值小于24小时。枚举该边界内的UTC分钟。
    pivot = target.replace(tzinfo=UTC)
    return [x for minute in range(-1439, 1440)
            if (x := pivot + minute * MINUTE).astimezone(zone).replace(tzinfo=None) == target]


def mask(intervals):
    bits = 0
    for start, end in intervals:
        bits |= ((1 << (end - start)) - 1) << start
    return bits


def rebuild(case, zones):
    bounds = {p.id: (tuple(map(mask, p.weekly)), {d: mask(w) for d, w in p.overrides.items()}) for p in case.people}
    rows = []
    for slot, minute in case.slots:
        day = case.start
        for week in range(1, case.weeks + 1):
            target = wall_at(day, minute)
            day += timedelta(days=7)
            row = {"slot": slot, "week": week, "organizer_wall": stamp(target)}
            matches = possible_utc(target, zones[case.organizer_zone])
            if len(matches) != 1:
                rows.append(dict(row, status="ambiguous" if matches else "nonexistent",
                                 alternatives_utc=list(map(stamp, matches))))
                continue
            start = matches[0]
            end = start + timedelta(minutes=case.length)
            identities = []
            for who in case.people:
                zone = zones[who.zone]
                weekdays, overrides = bounds[who.id]
                misses = []
                instant = start
                while instant < end:
                    local = instant.astimezone(zone)
                    allowed = overrides.get(local.date(), weekdays[local.weekday()])
                    if not ((allowed >> (60 * local.hour + local.minute)) & 1):
                        misses.append(local)
                    instant += MINUTE
                identities.append({"id": who.id, "start": stamp(start.astimezone(zone)),
                                   "end": stamp(end.astimezone(zone)), "outside_minutes": len(misses),
                                   "first_outside": stamp(misses[0]) if misses else None})
            rows.append(dict(row, status="conflict" if any(x["first_outside"] for x in identities) else "ok",
                             start_utc=stamp(start), end_utc=stamp(end), people=identities))
    return rows


def baseline(identity, rows):
    return {"kind": "meeting-baseline/v1", **identity, "rows": rows}


def main():
    p = ChineseParser(usage="verify.py {baseline,compare} --input 案例.json --output 新报告.json", description="独立复算并核验规划交接")
    p.add_argument("action", choices=["baseline", "compare"])
    for key in ("input", "output"):
        p.add_argument("--" + key, required=True)
    for key in ("intake", "baseline", "plan"):
        p.add_argument("--" + key)
    args = p.parse_args()
    case, zones, identity = input_state(args.input)
    rows = rebuild(case, zones)
    if args.action == "baseline":
        require(not any((args.intake, args.baseline, args.plan)), "建立基线时只接收原始输入")
        write(args.output, baseline(identity, rows))
        print(f"独立基线已写入，共{len(rows)}期")
        return
    require(all((args.intake, args.baseline, args.plan)), "比对需提供梳理回执、独立基线及规划")
    receipt, intake_sha = read(args.intake)
    own, base_sha = read(args.baseline)
    proposed, plan_sha = read(args.plan)
    expected = {"kind": "meeting-plan/v1", **identity, "intake_sha256": intake_sha, "rows": rows}
    equal = canonical(proposed) == canonical(expected) and canonical(own) == canonical(baseline(identity, rows))
    equal = equal and canonical(receipt) == canonical(intake(identity))
    write(args.output, {"kind": "meeting-review/v1", **identity, "intake_sha256": intake_sha,
                        "baseline_sha256": base_sha, "plan_sha256": plan_sha,
                        "checked_rows": len(rows), "verdict": "pass" if equal else "disagreement"})
    print("逐期复算一致" if equal else "原始输入、时区凭证或逐期结果不一致，禁止通过")
    if not equal:
        raise SystemExit(1)


if __name__ == "__main__":
    cli(main)
