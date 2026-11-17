#!/usr/bin/env python3
"""原生命题模型检查：标准库、有限穷举、只写全新目录。"""
import argparse
import hashlib
import itertools
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
        raise PuzzleError(f"{where}须为不超过32字符的小写字母、数字或单连字符标识")


def label(value, where, maximum=40):
    if (not isinstance(value, str) or not 1 <= len(value) <= maximum or value != value.strip()
            or any(unicodedata.category(c).startswith("C") or c in "【】" for c in value)):
        raise PuzzleError(f"{where}须为有界非空文字，不得含控制字符、首尾空白或保留括号")


def validate(model):
    keys(model, ["schema_version", "puzzle_id", "title", "categories", "clues"], "模型")
    if model["schema_version"] != "1.0":
        raise PuzzleError("不支持的模型版本")
    identifier(model["puzzle_id"], "题目标识")
    label(model["title"], "标题", 80)
    categories = model["categories"]
    if not isinstance(categories, list) or len(categories) != 3:
        raise PuzzleError("仅支持三个类别")
    ids, labels, dimensions = set(), set(), []
    for category in categories:
        keys(category, ["id", "label", "items"], "类别")
        identifier(category["id"], "类别标识")
        label(category["label"], "类别名称")
        if category["id"] in ids or category["label"] in labels:
            raise PuzzleError("类别标识和名称不得重复")
        ids.add(category["id"])
        labels.add(category["label"])
        items = category["items"]
        if not isinstance(items, list) or len(items) not in (3, 4):
            raise PuzzleError("每个类别必须含三个或四个项目")
        item_ids, item_labels = set(), set()
        for item in items:
            keys(item, ["id", "label"], "项目")
            identifier(item["id"], "项目标识")
            label(item["label"], "项目名称")
            if item["id"] in item_ids or item["label"] in item_labels:
                raise PuzzleError("同类别项目标识和名称不得重复")
            item_ids.add(item["id"])
            item_labels.add(item["label"])
        if any(name + "不" in item_labels for name in item_labels):
            raise PuzzleError("项目名称不能仅相差末尾的不字，以免对应与不对应句式混淆")
        dimensions.append(len(items))
    if len(set(dimensions)) != 1:
        raise PuzzleError("三个类别的项目数量必须相同")
    clues = model["clues"]
    if not isinstance(clues, list) or not 1 <= len(clues) <= 32:
        raise PuzzleError("线索数量必须为1至32条")
    category_index = {c["id"]: n for n, c in enumerate(categories)}
    items_by_id = {c["id"]: {i["id"] for i in c["items"]} for c in categories}
    clue_ids, relations = set(), set()
    for clue in clues:
        keys(clue, ["id", "op", "left", "right"], "线索")
        identifier(clue["id"], "线索标识")
        if clue["id"] in clue_ids:
            raise PuzzleError("线索标识不得重复")
        clue_ids.add(clue["id"])
        if clue["op"] not in ("match", "not_match"):
            raise PuzzleError("仅支持对应和不对应关系")
        for ref in (clue["left"], clue["right"]):
            keys(ref, ["category", "item"], "线索引用")
            if (not isinstance(ref["category"], str) or not isinstance(ref["item"], str)
                    or ref["category"] not in items_by_id
                    or ref["item"] not in items_by_id[ref["category"]]):
                raise PuzzleError("线索引用了不存在的类别或项目")
        if category_index[clue["left"]["category"]] >= category_index[clue["right"]["category"]]:
            raise PuzzleError("线索必须按类别顺序引用不同类别")
        relation = canonical({k: v for k, v in clue.items() if k != "id"})
        if relation in relations:
            raise PuzzleError("同一关系不得重复列为多条线索")
        relations.add(relation)
    return model


def learner_source(model):
    categories = model["categories"]
    names = {c["id"]: (c["label"], {i["id"]: i["label"] for i in c["items"]}) for c in categories}
    clues = []
    for clue in model["clues"]:
        def ref_text(ref):
            category, items = names[ref["category"]]
            return f"【{category}】{items[ref['item']]}"
        verb = "对应" if clue["op"] == "match" else "不对应"
        clues.append({"id": clue["id"], "text": f"{ref_text(clue['left'])}与{ref_text(clue['right'])}{verb}。"})
    return {"schema_version": "1.0", "puzzle_id": model["puzzle_id"], "title": model["title"],
            "categories": categories, "rules": RULES, "clues": clues}


def enumerate_models(model):
    """穷举两个非锚定类别的所有排列，最多576种完整候选。"""
    categories = model["categories"]
    vectors = [[item["id"] for item in c["items"]] for c in categories]
    solutions = []
    for second in itertools.permutations(vectors[1]):
        for third in itertools.permutations(vectors[2]):
            positions = {c["id"]: {item: n for n, item in enumerate(values)}
                         for c, values in zip(categories, (vectors[0], second, third))}
            def holds(clue):
                left, right = clue["left"], clue["right"]
                equal = positions[left["category"]][left["item"]] == positions[right["category"]][right["item"]]
                return equal if clue["op"] == "match" else not equal
            if all(holds(clue) for clue in model["clues"]):
                solutions.append([{c["id"]: values[n] for c, values in zip(categories, (vectors[0], second, third))}
                                  for n in range(len(vectors[0]))])
    return solutions


def analyze(model):
    validate(model)
    learner = learner_source(model)
    solutions = enumerate_models(model)
    size = len(model["categories"][0]["items"])
    candidates = 36 if size == 3 else 576
    report = {"schema_version": "1.0", "puzzle_id": model["puzzle_id"], "input_sha256": digest(model),
              "source_sha256": digest(learner), "algorithm": "permutations", "candidate_count": candidates,
              "solution_count": len(solutions), "status": "unique_model" if len(solutions) == 1 else
              "inconsistent" if not solutions else "ambiguous", "solution": solutions[0] if len(solutions) == 1 else None,
              "counterexamples": solutions[:2] if len(solutions) > 1 else []}
    return {"learner": learner, "report": report}


def no_symlinks(path):
    if ".." in Path(path).parts:
        raise PuzzleError("路径不得含上级目录跳转")
    absolute = Path(os.path.abspath(path))
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            raise PuzzleError("输入输出路径不得包含符号链接")
    return absolute


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PuzzleError("JSON不得含重复字段")
            result[key] = value
        return result
    def reject_constant(_):
        raise PuzzleError("JSON不得含非有限数值")
    if path == "-":
        raw = sys.stdin.buffer.read(LIMIT + 1)
    else:
        source = no_symlinks(path)
        fd = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise PuzzleError("输入必须为普通JSON文件")
            raw = handle.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise PuzzleError("输入超过64KiB限制")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def write_bundle(destination, values):
    path = no_symlinks(destination)
    if not path.parent.is_dir():
        raise PuzzleError("输出父目录必须已存在")
    encoded = {name: (canonical(value) + "\n").encode("utf-8") if not isinstance(value, str)
               else value.encode("utf-8") for name, value in values.items()}
    path.mkdir(mode=0o700)
    for name, content in encoded.items():
        with (path / name).open("xb") as handle:
            handle.write(content)
    return [str(path / name) for name in encoded]


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        print(canonical({"ok": False, "error": "ARGUMENT_INVALID", "message": "命令参数不完整或不受支持，请使用--help查看中文说明。"}))
        raise SystemExit(2)

    def format_help(self):
        return super().format_help().replace("usage: ", "用法：", 1).replace("options:\n", "参数：\n", 1)


def main():
    parser = ChineseParser(add_help=False, description="检查三类别逻辑谜题，穷举解数并生成中文题面")
    parser.add_argument("--input", required=True, help="模型JSON路径；-表示标准输入")
    parser.add_argument("--output", help="尚不存在的输出目录；省略则仅输出JSON")
    parser.add_argument("-h", "--help", action="help", help="显示中文用法后退出")
    args = parser.parse_args()
    try:
        result = analyze(read_json(args.input))
        if args.output:
            result["files"] = write_bundle(args.output, {"learner.json": result["learner"], "model-report.json": result["report"]})
        print(canonical({"ok": True, **result}))
        return 0
    except (PuzzleError, OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        detail = str(error) if isinstance(error, PuzzleError) else "文件或JSON无效、目录已存在或无法安全完成写入"
        print(canonical({"ok": False, "error": "MODEL_INVALID", "message": f"模型检查未完成：{detail}。已存在或部分写入的输出目录不会被覆盖，请检查后使用全新目录。"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
