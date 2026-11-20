"""逐件验算与小规模无解复核；独立于规划器。"""
from collections import Counter
from itertools import product
from math import prod

from contract import Case, InputError, digest, fields, identifier, integer, same_value, stamp

EXHAUSTIVE_LIMIT = 60_000


def independent_exhaustion(case: Case) -> tuple[bool | None, list[str]]:
    """直接枚举原始输入的所有材料兼容指派并记录最小缺口。"""
    choices = [[index for index, board in enumerate(case.boards) if part.material == board.material]
               for part in case.parts]
    if any(not candidates for candidates in choices):
        return False, ["至少一件零件找不到材质及规格相同的库存。"]
    if prod(map(len, choices)) > EXHAUSTIVE_LIMIT:
        return None, []
    best_total = sum(part.length + case.kerf for part in case.parts) + 1
    closest = []
    for placement in product(*choices):
        used = Counter()
        for part, index in zip(case.parts, placement):
            used[index] += part.length + case.kerf
        deficits = [(case.boards[index], amount) for index, amount in used.items()
                    if amount > case.boards[index].capacity]
        if not deficits:
            return True, []
        total = sum(amount - board.capacity for board, amount in deficits)
        if total < best_total:
            best_total, closest = total, deficits
    return False, [f"总超长最小的一种分配中，库存 {board.id} 需 {used} 毫米，可用 {board.capacity} 毫米，超出 {used - board.capacity} 毫米。"
                   for board, used in closest]


def audit_cut(case: Case, stock_raw: bytes, plan_raw: bytes, candidate: dict) -> dict:
    expected = {**stamp(case, "planner"), "stock_report_sha256": digest(stock_raw)}
    fields(candidate, set(expected) | {"status", "visited", "limit", "assignments"}, "候选方案")
    if not same_value({key: candidate[key] for key in expected}, expected):
        raise InputError("候选方案与原始案例或库存报告摘要不一致。")
    limit = integer(candidate["limit"], 1, 100_000, "规划上限")
    integer(candidate["visited"], 1, limit, "规划已访问状态数")
    status = candidate["status"]
    if status not in ("candidate", "no_plan", "search_limit"):
        raise InputError("候选状态未知。")
    assignments = candidate["assignments"]
    if not isinstance(assignments, list) or len(assignments) > len(case.boards) or (status != "candidate" and assignments):
        raise InputError("候选分配列表错误。")

    findings = []
    audited = []

    def finding(code: str, message: str) -> None:
        findings.append({"code": code, "message": message})

    if status == "search_limit":
        verdict = "inconclusive"
        finding("search_limit", "规划达到搜索上限，可行性未确认。")
    elif status == "no_plan":
        result, reasons = independent_exhaustion(case)
        if result is False:
            verdict = "confirmed_no_plan"
            for reason in reasons:
                finding("no_plan_reason", reason)
        else:
            verdict = "blocked"
            if result is True:
                finding("counterexample", "独立穷举发现可行分配，与规划结论冲突。")
            else:
                finding("verification_limit", "候选称无解，独立穷举超出复核上限。")
    else:
        boards = {board.id: board for board in case.boards}
        parts = {part.key: part for part in case.parts}
        counts = Counter()
        used_boards = set()
        for assignment in assignments:
            fields(assignment, {"stock_id", "pieces"}, "单块分配")
            board_id = identifier(assignment["stock_id"])
            refs = assignment["pieces"]
            if not isinstance(refs, list) or not 1 <= len(refs) <= len(parts):
                raise InputError("单块分配必须包含有限数量的零件引用。")
            if board_id in used_boards:
                finding("duplicate_stock", f"库存 {board_id} 被重复占用。")
            used_boards.add(board_id)
            board = boards.get(board_id)
            if board is None:
                finding("unknown_stock", f"库存 {board_id} 不在原始清单。")
            pieces = []
            for ref in refs:
                if not isinstance(ref, list) or len(ref) != 2:
                    raise InputError("零件引用须包含编号和序号。")
                key = identifier(ref[0]), integer(ref[1], 1, 24, "零件序号")
                counts[key] += 1
                piece = parts.get(key)
                if piece is None:
                    finding("unknown_piece", f"零件 {key[0]} 第 {key[1]} 件不在原始需求。")
                    continue
                if board and piece.material != board.material:
                    finding("material", f"库存 {board_id} 与零件 {piece.id} 的材质及规格不一致。")
                pieces.append({"id": piece.id, "ordinal": piece.ordinal, "length_mm": piece.length})
            if board:
                use = sum(piece["length_mm"] for piece in pieces) + len(pieces) * case.kerf
                if use > board.capacity:
                    finding("over_capacity", f"库存 {board.id} 需 {use} 毫米，可用 {board.capacity} 毫米，超出 {use - board.capacity} 毫米。")
                audited.append({"stock_id": board.id, "material": board.material, "length_mm": board.length,
                                "trim_start_mm": board.left, "trim_end_mm": board.right, "used_mm": use,
                                "kerf_mm": case.kerf, "remaining_mm": board.capacity - use, "pieces": pieces})
        for key in parts:
            if counts[key] == 0:
                finding("missing_piece", f"遗漏零件 {key[0]} 第 {key[1]} 件。")
            elif counts[key] > 1:
                finding("duplicate_piece", f"零件 {key[0]} 第 {key[1]} 件被重复分配。")
        verdict = "blocked" if findings else "verified"

    return {
        **stamp(case, "verifier"),
        "stock_report_sha256": digest(stock_raw),
        "plan_sha256": digest(plan_raw),
        "verdict": verdict,
        "findings": findings,
        "boards": audited if verdict == "verified" else [],
    }
