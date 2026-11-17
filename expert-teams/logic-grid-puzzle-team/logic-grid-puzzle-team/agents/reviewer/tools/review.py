#!/usr/bin/env python3
"""从学生可见中文题面独立重建关系，并以逐变量深搜复核。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
import stat
import sys

LIMIT = 65536
RULES = "每个类别内的项目各使用一次；同一行的项目相互对应。仅以下编号线索构成题目条件。"
IDENT = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


class PuzzleError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise PuzzleError(f"{where}字段必须完整且不得增加未知字段")


def identifier(value, where):
    if not isinstance(value, str) or len(value) > 32 or not IDENT.fullmatch(value):
        raise PuzzleError(f"{where}标识不符合小写字母、数字和单连字符约定")


def label(value, where, maximum=40):
    if (not isinstance(value, str) or not 1 <= len(value) <= maximum or value != value.strip()
            or any(unicodedata.category(c).startswith("C") or c in "【】" for c in value)):
        raise PuzzleError(f"{where}不是有效的有界文字，或含控制字符及保留括号")


def reconstruct(learner):
    keys(learner, ["schema_version", "puzzle_id", "title", "categories", "rules", "clues"], "题面")
    if learner["schema_version"] != "1.0" or learner["rules"] != RULES:
        raise PuzzleError("题面版本或一一对应规则已变化")
    identifier(learner["puzzle_id"], "题目")
    label(learner["title"], "标题", 80)
    categories = learner["categories"]
    if not isinstance(categories, list) or len(categories) != 3:
        raise PuzzleError("题面必须含三个类别")
    seen_ids, seen_labels, sizes = set(), set(), []
    for category in categories:
        keys(category, ["id", "label", "items"], "类别")
        identifier(category["id"], "类别")
        label(category["label"], "类别名称")
        if category["id"] in seen_ids or category["label"] in seen_labels:
            raise PuzzleError("类别标识或名称重复")
        seen_ids.add(category["id"])
        seen_labels.add(category["label"])
        items = category["items"]
        if not isinstance(items, list) or len(items) not in (3, 4):
            raise PuzzleError("每类须有三个或四个项目")
        ids, labels = set(), set()
        for item in items:
            keys(item, ["id", "label"], "项目")
            identifier(item["id"], "项目")
            label(item["label"], "项目名称")
            if item["id"] in ids or item["label"] in labels:
                raise PuzzleError("同类项目标识或名称重复")
            ids.add(item["id"])
            labels.add(item["label"])
        sizes.append(len(items))
    if len(set(sizes)) != 1:
        raise PuzzleError("类别规模必须一致")
    # 以完整类别与项目字面值建立受控句式词典；不接受自由文本猜测或改写。
    vocabulary = {}
    for left_index, left_category in enumerate(categories):
        for right_category in categories[left_index + 1:]:
            for left in left_category["items"]:
                for right in right_category["items"]:
                    for op, verb in (("match", "对应"), ("not_match", "不对应")):
                        text = f"【{left_category['label']}】{left['label']}与【{right_category['label']}】{right['label']}{verb}。"
                        if text in vocabulary:
                            raise PuzzleError("项目文字造成线索句式歧义")
                        vocabulary[text] = {"op": op, "left": {"category": left_category["id"], "item": left["id"]},
                                            "right": {"category": right_category["id"], "item": right["id"]}}
    visible_clues = learner["clues"]
    if not isinstance(visible_clues, list) or not 1 <= len(visible_clues) <= 32:
        raise PuzzleError("线索数量必须为1至32条")
    clues, ids, relations = [], set(), set()
    for visible in visible_clues:
        keys(visible, ["id", "text"], "中文线索")
        identifier(visible["id"], "线索")
        if visible["id"] in ids:
            raise PuzzleError("线索标识重复")
        ids.add(visible["id"])
        if not isinstance(visible["text"], str) or visible["text"] not in vocabulary:
            raise PuzzleError("中文线索不符合受支持的对应／不对应完整句式")
        relation = vocabulary[visible["text"]]
        if canonical(relation) in relations:
            raise PuzzleError("题面重复描述同一关系")
        relations.add(canonical(relation))
        clues.append({"id": visible["id"], **relation})
    return {"schema_version": "1.0", "puzzle_id": learner["puzzle_id"], "title": learner["title"],
            "categories": categories, "clues": clues}


def dfs_solutions(model):
    """不使用排列枚举：逐项目分配行位置，以已可求值的线索剪枝。"""
    categories = model["categories"]
    size = len(categories[0]["items"])
    assignment = {(categories[0]["id"], item["id"]): row for row, item in enumerate(categories[0]["items"])}
    variables = [(c["id"], item["id"]) for c in categories[1:] for item in c["items"]]
    used = {c["id"]: set() for c in categories[1:]}
    solutions, nodes = [], 0

    def consistent():
        for clue in model["clues"]:
            left = (clue["left"]["category"], clue["left"]["item"])
            right = (clue["right"]["category"], clue["right"]["item"])
            if left in assignment and right in assignment:
                equal = assignment[left] == assignment[right]
                if equal != (clue["op"] == "match"):
                    return False
        return True

    def search(index):
        nonlocal nodes
        nodes += 1
        if index == len(variables):
            solutions.append([{c["id"]: next(i["id"] for i in c["items"] if assignment[(c["id"], i["id"])] == row)
                               for c in categories} for row in range(size)])
            return
        variable = variables[index]
        for row in range(size):
            if row in used[variable[0]]:
                continue
            assignment[variable] = row
            used[variable[0]].add(row)
            if consistent():
                search(index + 1)
            used[variable[0]].remove(row)
            del assignment[variable]
    search(0)
    return solutions, nodes


def explanation(model, solutions):
    steps = []
    if len(solutions) == 1:
        categories = model["categories"]
        anchor = categories[0]["id"]
        for row in solutions[0]:
            for category in categories[1:]:
                conclusion = {"op": "match", "left": {"category": anchor, "item": row[anchor]},
                              "right": {"category": category["id"], "item": row[category["id"]]}}
                # 全部线索有解且所有解均含此关系，故结论非空地被全部线索蕴含。
                if not all(any(other[anchor] == row[anchor] and other[category["id"]] == row[category["id"]]
                               for other in solution) for solution in solutions):
                    raise PuzzleError("答案关系不被线索蕴含")
                steps.append({"id": f"step-{len(steps) + 1:02d}", "premises": [c["id"] for c in model["clues"]],
                              "conclusion": conclusion})
    return {"method": "all_clues_entailment", "steps": steps}


def analyze(learner):
    model = reconstruct(learner)
    solutions, nodes = dfs_solutions(model)
    return {"schema_version": "1.0", "puzzle_id": learner["puzzle_id"], "source_sha256": digest(learner),
            "model_sha256": digest(model), "algorithm": "depth-first", "search_nodes": nodes,
            "solution_count": len(solutions), "status": "unique_review_model" if len(solutions) == 1 else
            "inconsistent" if not solutions else "ambiguous", "reconstructed_model": model,
            "solution": solutions[0] if len(solutions) == 1 else None,
            "counterexamples": solutions[:2] if len(solutions) > 1 else [], "explanation": explanation(model, solutions)}


def no_symlinks(path):
    if ".." in Path(path).parts:
        raise PuzzleError("路径不得含上级目录跳转")
    result = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (result, *result.parents)):
        raise PuzzleError("路径不得包含符号链接")
    return result


def read_json(path):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise PuzzleError("JSON字段重复")
            result[key] = value
        return result
    def invalid_constant(_):
        raise PuzzleError("不支持非有限数值")
    if path == "-":
        raw = sys.stdin.buffer.read(LIMIT + 1)
    else:
        fd = os.open(no_symlinks(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise PuzzleError("输入必须是普通JSON文件")
            raw = handle.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise PuzzleError("输入超过64KiB限制")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        print(canonical({"ok": False, "error": "ARGUMENT_INVALID", "message": "命令参数不完整或不受支持，请使用--help查看中文说明。"}))
        raise SystemExit(2)

    def format_help(self):
        return super().format_help().replace("usage: ", "用法：", 1).replace("options:\n", "参数：\n", 1)


def main():
    parser = ChineseParser(add_help=False, description="仅从中文题面独立重建模型并深搜验解")
    parser.add_argument("--input", required=True, help="learner.json路径；-表示标准输入")
    parser.add_argument("--output", help="尚不存在的目录；省略则仅输出JSON")
    parser.add_argument("-h", "--help", action="help", help="显示中文用法后退出")
    args = parser.parse_args()
    try:
        review = analyze(read_json(args.input))
        result = {"ok": True, "review": review}
        if args.output:
            output = no_symlinks(args.output)
            if not output.parent.is_dir():
                raise PuzzleError("输出父目录不存在")
            encoded = (canonical(review) + "\n").encode("utf-8")
            output.mkdir(mode=0o700)
            with (output / "review.json").open("xb") as handle:
                handle.write(encoded)
            result["files"] = [str(output / "review.json")]
        print(canonical(result))
        return 0
    except (PuzzleError, OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        detail = str(error) if isinstance(error, PuzzleError) else "文件或JSON无效、目录已存在或无法安全完成写入"
        print(canonical({"ok": False, "error": "REVIEW_INVALID", "message": f"独立复核未完成：{detail}。请保留现有文件并检查输入，重试须使用全新目录。"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
