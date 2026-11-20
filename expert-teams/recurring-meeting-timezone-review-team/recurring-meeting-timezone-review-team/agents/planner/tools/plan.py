"""逐周展开本地例会时刻，沿 UTC 计算参会冲突。"""
from datetime import timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/meeting-evidence/scripts"))
from contract import (ChineseParser, MINUTE, UTC, canonical, cli, input_state,
                      intake, read, require, stamp, wall_at, wall_min, write)


def starts_for(wall, zone):
    result = set()
    for fold in (0, 1):
        utc = wall.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) == wall:
            result.add(utc)
    return sorted(result)


def attendance(person, zone, start, duration):
    outside = 0
    first = None
    for j in range(duration):
        local = (start + j * MINUTE).astimezone(zone)
        minute = wall_min(local)
        allowed = person.overrides.get(local.date(), person.weekly[local.weekday()])
        if not any(low <= minute < high for low, high in allowed):
            outside += 1
            if first is None:
                first = stamp(local)
    return {"id": person.id, "start": stamp(start.astimezone(zone)),
            "end": stamp((start + duration * MINUTE).astimezone(zone)),
            "outside_minutes": outside, "first_outside": first}


def plan(case, zones):
    rows = []
    for slot, minute in case.slots:
        for i in range(case.weeks):
            wall = wall_at(case.start + timedelta(weeks=i), minute)
            choices = starts_for(wall, zones[case.organizer_zone])
            row = {"slot": slot, "week": i + 1, "organizer_wall": stamp(wall)}
            if len(choices) != 1:
                rows.append({**row, "status": "ambiguous" if choices else "nonexistent",
                             "alternatives_utc": [stamp(x) for x in choices]})
                continue
            start = choices[0]
            people = [attendance(p, zones[p.zone], start, case.length) for p in case.people]
            rows.append({**row, "status": "conflict" if any(x["outside_minutes"] for x in people) else "ok",
                         "start_utc": stamp(start), "end_utc": stamp(start + case.length * MINUTE), "people": people})
    return rows


def main():
    p = ChineseParser(usage="plan.py --input 案例.json --intake 回执.json --output 新规划.json", description="计算原始例会各期时刻与冲突")
    for key in ("input", "intake", "output"):
        p.add_argument("--" + key, required=True)
    args = p.parse_args()
    case, zones, identity = input_state(args.input)
    receipt, digest = read(args.intake)
    require(canonical(receipt) == canonical(intake(identity)), "梳理回执与原始输入或时区数据不一致")
    rows = plan(case, zones)
    write(args.output, {"kind": "meeting-plan/v1", **identity, "intake_sha256": digest, "rows": rows})
    print(f"已计算{len(rows)}期候选记录；须交独立复核")


if __name__ == "__main__":
    cli(main)
