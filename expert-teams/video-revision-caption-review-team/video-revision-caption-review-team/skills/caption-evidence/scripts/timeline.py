"""按旧版剪辑记录核算时间，逐条核对改版字幕。"""
from collections import Counter, defaultdict, deque
from itertools import pairwise

from inputs import MAX_TIME


def project_cue(cue, edits):
    offset = 0
    for edit in edits:
        if cue.end <= edit.start:
            break
        if cue.start >= edit.end:
            offset += edit.shift
        elif edit.inserted == 0 and edit.start <= cue.start and cue.end <= edit.end:
            return "removed", None, None
        else:
            return "changed", None, None
    return "retained", cue.start + offset, cue.end + offset


def planner(approved, scope):
    edits = scope.edits if scope is not None else ()
    return [projection(cue.number, project_cue(cue, edits)) for cue in approved]


def verifier(approved, scope):
    """按保留区间覆盖得到独立基线，直接对照原址与新址。"""
    retained, removed = [], []
    old_cursor = new_cursor = 0
    for edit in scope.edits if scope is not None else ():
        span = edit.start - old_cursor
        if span:
            retained.append((old_cursor, edit.start, new_cursor))
        new_cursor += span + edit.inserted
        old_cursor = edit.end
        if edit.inserted == 0:
            removed.append((edit.start, edit.end))
    retained.append((old_cursor, MAX_TIME, new_cursor))
    result = []
    for cue in approved:
        covering = next(((old, new) for old, end, new in retained if old <= cue.start < cue.end <= end), None)
        if covering is not None:
            old, new = covering
            expected = ("retained", new + cue.start - old, new + cue.end - old)
        elif any(start <= cue.start < cue.end <= end for start, end in removed):
            expected = ("removed", None, None)
        else:
            expected = ("changed", None, None)
        result.append(projection(cue.number, expected))
    return result


def projection(number, expected):
    kind, start, end = expected
    return {"approved": number, "kind": kind, "start": start, "end": end}


def regions(scope):
    offset = 0
    changes = []
    for edit in scope.edits if scope is not None else ():
        begin = edit.start + offset
        changes.append((begin, begin + edit.inserted, edit))
        offset += edit.shift
    return changes


def crosses_changed(cue, changes):
    return any(cue.start < end and start < cue.end for start, end, _ in changes)


def audit_row(kind, old=None, new=None, target=None, area=None):
    return {
        "kind": kind, "approved": old.number if old else None, "revised": new.number if new else None,
        "approved_time": [old.start, old.end] if old else None, "revised_time": [new.start, new.end] if new else None,
        "suggested_time": target, "playback": area,
        "approved_text": old.text if old else None, "revised_text": new.text if new else None,
    }


def reconcile(approved, revised, scope, expected):
    revised_by_tuple = defaultdict(deque)
    revised_by_text = defaultdict(list)
    old_counts = Counter(cue.text for cue in approved)
    for cue in revised:
        revised_by_tuple[(cue.text, cue.start, cue.end)].append(cue)
        revised_by_text[cue.text].append(cue)
    changes = regions(scope)
    used, exact = set(), {}
    rows, repairs = [], {}
    for old, slot in zip(approved, expected):
        if slot["kind"] == "retained":
            available = revised_by_tuple[(old.text, slot["start"], slot["end"])]
            if available:
                new = available.popleft()
                used.add(new.number)
                exact[old.number] = new

    deleted_text = set()
    for old, slot in zip(approved, expected):
        if slot["kind"] == "removed":
            deleted_text.add(old.text)
            rows.append(audit_row("removed", old=old))
            continue
        if slot["kind"] == "changed":
            rows.append(audit_row("crosses_edit", old=old))
            continue
        if old.number in exact:
            rows.append(audit_row("same" if scope is not None else "same_without_edits", old, exact[old.number]))
            continue
        choices = revised_by_text[old.text]
        matching = choices[0] if len(choices) == old_counts[old.text] == 1 else None
        if matching is None or matching.number in used:
            status = "ambiguous" if any(c.number not in used for c in choices) else "missing"
            target = [slot["start"], slot["end"]] if scope is not None else None
            rows.append(audit_row(status, old=old, target=target))
        else:
            used.add(matching.number)
            target = [slot["start"], slot["end"]]
            if scope is None or crosses_changed(matching, changes):
                rows.append(audit_row("timing_unconfirmed", old, matching))
            else:
                repairs[matching.number] = target
                rows.append(audit_row("timing_fix", old, matching, target))

    for cue in revised:
        if cue.number not in used:
            if crosses_changed(cue, changes):
                status = "new_material"
            elif cue.text in deleted_text:
                status = "deleted_text_present"
            else:
                status = "revised_unlinked"
            rows.append(audit_row(status, new=cue))
    for start, end, edit in changes:
        if edit.inserted:
            rows.append(audit_row("check_new_span", area=[start, end]))

    # Validate the actual candidate order and bounds before producing a new SRT.
    timings = [(cue, *repairs.get(cue.number, (cue.start, cue.end))) for cue in revised]
    limit = scope.revised_end if scope is not None and scope.revised_end is not None else MAX_TIME - 1
    latest_end = -1
    for cue, start, end in timings:
        if start < latest_end:
            rows.append(audit_row("overlap", new=cue, target=[start, end]))
        if end > limit:
            rows.append(audit_row("out_of_bounds", new=cue, target=[start, end]))
        latest_end = max(latest_end, end)
    for (_, previous_start, _), (cue, start, end) in pairwise(timings):
        if start < previous_start:
            rows.append(audit_row("order", new=cue, target=[start, end]))

    unresolved = sum(row["kind"] not in {"same", "same_without_edits", "removed", "timing_fix"} for row in rows)
    return {"mode": "mapped" if scope is not None else "comparison_only",
            "status": "review_required" if unresolved or scope is None else "verified_track",
            "unresolved": unresolved, "approved_count": len(approved), "revised_count": len(revised),
            "rows": rows, "repairs": repairs}
