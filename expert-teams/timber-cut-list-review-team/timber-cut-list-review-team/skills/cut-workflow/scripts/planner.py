"""查找一个满足约束的方案。搜索状态用尽才判定无可行分配。"""
from contract import Case, digest, stamp

MAX_STATES = 100_000
DEFAULT_STATES = 50_000


def plan_cut(case: Case, stock_raw: bytes, limit: int) -> dict:
    boards = case.boards
    pieces = sorted(case.parts, key=lambda item: (-item.length, item.id, item.ordinal))
    available = [board.capacity for board in boards]
    assigned = [[] for _ in boards]
    dead_ends = set()
    visited = 0

    def place(depth: int) -> bool | None:
        nonlocal visited
        if depth == len(pieces):
            return True
        state = depth, tuple(available)
        if state in dead_ends:
            return False
        if visited >= limit:
            return None
        visited += 1
        piece = pieces[depth]
        required = piece.length + case.kerf
        tried = set()
        order = sorted(range(len(boards)), key=lambda i: (not assigned[i], available[i], boards[i].id))
        for index in order:
            remaining = available[index]
            if boards[index].material != piece.material or remaining < required or remaining in tried:
                continue
            tried.add(remaining)
            available[index] -= required
            assigned[index].append(piece.key)
            result = place(depth + 1)
            if result is True:
                return True
            assigned[index].pop()
            available[index] += required
            if result is None:
                return None
        dead_ends.add(state)
        return False

    found = place(0)
    status = {True: "candidate", False: "no_plan", None: "search_limit"}[found]
    return {
        **stamp(case, "planner"),
        "stock_report_sha256": digest(stock_raw),
        "status": status,
        "visited": visited,
        "limit": limit,
        "assignments": [
            {"stock_id": board.id, "pieces": [list(key) for key in group]}
            for board, group in zip(boards, assigned) if group
        ],
    }
