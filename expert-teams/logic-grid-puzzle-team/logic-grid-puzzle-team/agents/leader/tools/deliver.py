#!/usr/bin/env python3
"""重新执行双算法检查；只在来源、独立重建和解释一致时交付。"""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

LIMIT = 65536


class PuzzleError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def no_symlinks(path):
    if ".." in Path(path).parts:
        raise PuzzleError("路径不得含上级目录跳转")
    result = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (result, *result.parents)):
        raise PuzzleError("路径不得包含符号链接")
    return result


def decode_json(raw):
    if len(raw) > LIMIT:
        raise PuzzleError("输入超过64KiB限制")
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise PuzzleError("JSON字段重复")
            result[key] = value
        return result
    def invalid_constant(_):
        raise PuzzleError("不支持非有限数值")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)


def read_json(path):
    fd = os.open(no_symlinks(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise PuzzleError("输入必须是普通JSON文件")
        return decode_json(handle.read(LIMIT + 1))


def peer(role, filename, value):
    script = no_symlinks(Path(__file__).absolute().parents[2] / role / "tools" / filename)
    result = subprocess.run([sys.executable, str(script), "--input", "-"], input=canonical(value).encode("utf-8"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, check=False,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    # 同一包内固定脚本、禁用shell；从冻结的内存输入重算，避免二次读取输入文件。
    response = decode_json(result.stdout)
    if result.returncode != 0 or not isinstance(response, dict) or response.get("ok") is not True:
        raise PuzzleError("包内独立检查未成功，不能交付")
    return response


def certify(model, supplied_review):
    modeled = peer("modeler", "model.py", model)
    learner, report = modeled["learner"], modeled["report"]
    expected_review = peer("reviewer", "review.py", learner)["review"]
    if canonical(supplied_review) != canonical(expected_review):
        raise PuzzleError("独立复核记录与当前题面重算不一致；来源、线索、答案或解释可能已变化")
    if (report["solution_count"] != 1 or expected_review["solution_count"] != 1
            or report["solution"] != expected_review["solution"]):
        raise PuzzleError("两个算法尚未对同一个唯一解达成一致")
    if (report["source_sha256"] != digest(learner)
            or expected_review["source_sha256"] != digest(learner)
            or report["input_sha256"] != expected_review["model_sha256"]
            or canonical(model) != canonical(expected_review["reconstructed_model"])):
        raise PuzzleError("题面与线索重建的来源绑定不一致")
    # expected_review的每个结论已在非空完整解集中逐项验证，全部线索是明确的前提。
    steps = expected_review["explanation"]["steps"]
    if len(steps) != 2 * len(report["solution"]):
        raise PuzzleError("解释未覆盖全部非锚定答案关系")
    return {"learner": learner, "model_report": report, "review": expected_review,
            "status": "verified_unique", "model_sha256": digest(model),
            "source_sha256": digest(learner), "review_sha256": digest(supplied_review)}


def learner_html(learner):
    esc = html.escape
    categories = learner["categories"]
    category_text = "".join(f"<li><strong>{esc(c['label'])}</strong>：{esc('、'.join(i['label'] for i in c['items']))}</li>" for c in categories)
    clues = "".join(f"<li><span class='id'>{esc(c['id'])}</span> {esc(c['text'])}</li>" for c in learner["clues"])
    headers = "".join(f"<th>{esc(c['label'])}</th>" for c in categories)
    rows = "".join(f"<tr><th>{esc(item['label'])}</th><td>　</td><td>　</td></tr>" for item in categories[0]["items"])
    return f"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(learner['title'])}</title>
<style>body{{font-family:system-ui,'PingFang SC',sans-serif;max-width:850px;margin:2rem auto;padding:0 1rem;line-height:1.8;color:#182534}}h1{{font-size:1.8rem}}table{{border-collapse:collapse;width:100%;margin:1.5rem 0}}th,td{{border:1px solid #8795a2;padding:.65rem;text-align:left}}.id{{color:#536477;font-size:.85em}}@media print{{body{{margin:0;max-width:none}}}}</style>
<h1>{esc(learner['title'])}</h1><p>逻辑网格谜题 · 学生题面</p>
<h2>类别与项目</h2><ul>{category_text}</ul><p>{esc(learner['rules'])}</p>
<h2>线索</h2><ol>{clues}</ol><h2>填写答案</h2><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>
<p>请根据编号线索与一一对应规则填写空格。本页不含答案。</p></html>
"""


def answer_markdown(certified):
    learner = certified["learner"]
    categories = learner["categories"]
    names = {c["id"]: {i["id"]: i["label"] for i in c["items"]} for c in categories}
    def md(value):
        return html.escape(value).replace("|", "\\|").replace("`", "&#96;").replace("*", "&#42;").replace("_", "&#95;")
    headings = " | ".join(md(c["label"]) for c in categories)
    lines = [f"# {md(learner['title'])}：教师答案", "", "唯一解已通过排列穷举、中文题面重建与逐变量深搜的一致性检查。", "",
             f"| {headings} |", "| " + " | ".join("---" for _ in categories) + " |"]
    for row in certified["model_report"]["solution"]:
        lines.append("| " + " | ".join(md(names[c["id"]][row[c["id"]]]) for c in categories) + " |")
    lines.extend(["", "## 简明验证依据", "", "以下每一关系均由全部编号线索和一一对应规则蕴含。程序已穷举全部候选并检查前提有解；这不是最短的人类推理链。", ""])
    for step in certified["review"]["explanation"]["steps"]:
        relation = step["conclusion"]
        left, right = relation["left"], relation["right"]
        lines.append(f"- {md(names[left['category']][left['item']])}与{md(names[right['category']][right['item']])}对应；依据：" + "、".join(step["premises"]) + "。")
    lines.extend(["", "## 边界", "", "只证明当前受控题面与有限模型的一致性及唯一解，不保证人类难度、最少线索或无需试探即可解题。", "证书不能代替真实专家团运行记录；成员参与及交接须由宿主运行证据另行确认。", ""])
    return "\n".join(lines)


def export(certified, destination):
    path = no_symlinks(destination)
    if not path.parent.is_dir():
        raise PuzzleError("输出父目录必须已存在")
    puzzle = learner_html(certified["learner"]).encode("utf-8")
    answer = answer_markdown(certified).encode("utf-8")
    audit = {"schema_version": "1.0", "status": certified["status"], "puzzle_id": certified["learner"]["puzzle_id"],
             "model_sha256": certified["model_sha256"], "source_sha256": certified["source_sha256"],
             "review_sha256": certified["review_sha256"], "learner_source": certified["learner"],
             "model_report": certified["model_report"], "explanation": certified["review"]["explanation"],
             "files": {"puzzle.html": hashlib.sha256(puzzle).hexdigest(), "answer.md": hashlib.sha256(answer).hexdigest()},
             "limitations": "证书只验证当前有限题面的语义重建、唯一解与答案关系蕴含；不证明难度、最少线索或多智能体实际参与。"}
    contents = {"puzzle.html": puzzle, "answer.md": answer, "audit.json": (canonical(audit) + "\n").encode("utf-8")}
    path.mkdir(mode=0o700)
    # 审计记录最后写入；部分写入时不返回成功、不清理未知文件、不覆盖原目录。
    for name, raw in contents.items():
        with (path / name).open("xb") as handle:
            handle.write(raw)
    return {"directory": str(path), "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()},
            "status": "verified_unique", "source_sha256": certified["source_sha256"]}


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        print(canonical({"ok": False, "error": "ARGUMENT_INVALID", "message": "命令参数不完整或不受支持，请使用--help查看中文说明。"}))
        raise SystemExit(2)

    def format_help(self):
        return super().format_help().replace("usage: ", "用法：", 1).replace("options:\n", "参数：\n", 1)


def main():
    parser = ChineseParser(add_help=False, description="重新检查双算法与独立复核记录，生成中文谜题交付包")
    parser.add_argument("--model", required=True, help="当前原始模型JSON路径")
    parser.add_argument("--review", required=True, help="独立复核产生的review.json路径")
    parser.add_argument("--output", required=True, help="尚不存在的交付目录")
    parser.add_argument("-h", "--help", action="help", help="显示中文用法后退出")
    args = parser.parse_args()
    try:
        certified = certify(read_json(args.model), read_json(args.review))
        print(canonical({"ok": True, **export(certified, args.output)}))
        return 0
    except (PuzzleError, OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError, subprocess.SubprocessError) as error:
        detail = str(error) if isinstance(error, PuzzleError) else "文件、JSON或包内检查无法完成"
        print(canonical({"ok": False, "error": "DELIVERY_REFUSED", "message": f"未完成交付：{detail}。不会覆盖已存在目录；部分写入目录请保留检查并另选全新目录。"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
