"""导出自包含离线游戏；只使用 Python 标准库。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

VERSION = "1.0.2"
PAYLOAD = Path(__file__).resolve().parents[1]


class InputError(ValueError):
    """可以直接展示给用户的中文输入错误。"""


def render_game(seed):
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise InputError("seed 必须是 0 至 2147483647 的整数。")
    parts = {"SEED": str(seed), "VERSION": VERSION}
    for name, filename in (("ENGINE", "engine.mjs"), ("STATE", "state.mjs"), ("APP", "app.js")):
        source = (PAYLOAD / "assets" / filename).read_text(encoding="utf-8")
        # Modules have no imports. Inline module avoids file:// import/CORS failures.
        if name != "APP":
            source = source.replace("export ", "")
        parts[name] = source.replace("</script", "<\\/script")
    # Propagate the complete MIT notice to every exported derivative, too.
    license_text = (PAYLOAD / "licenses/invaders/LICENSE").read_text(encoding="utf-8")
    parts["LICENSE"] = license_text
    template = (PAYLOAD / "assets" / "page.html").read_text(encoding="utf-8")
    for key, value in parts.items():
        template = template.replace("@@" + key + "@@", value)
    return template


def execute(inputs):
    if not isinstance(inputs, dict) or set(inputs) - {"output_path", "seed"}:
        raise InputError("请仅提供 output_path 和可选的 seed。")
    seed = inputs.get("seed", 12345)
    html = render_game(seed).encode("utf-8")
    value = inputs.get("output_path")
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or "\x00" in value:
        raise InputError("output_path 必须是已有目录内新建 .html 文件的绝对路径。")
    path = Path(value)
    if not path.is_absolute() or path.suffix.lower() != ".html" or ".." in path.parts:
        raise InputError("请使用无 .. 的绝对路径，并以 .html 结尾。")
    if not path.parent.is_dir():
        raise InputError("输出目录不存在；请先创建目录，工具不会创建目录。")
    if path.parent.resolve() != path.parent or path.is_symlink():
        raise InputError("输出路径不能经过符号链接。")
    if path.exists():
        raise InputError("目标文件已存在，未覆盖；请换一个文件名。")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(html)
    except FileExistsError as exc:
        raise InputError("目标文件已存在，未覆盖；请换一个文件名。") from exc
    except OSError as exc:
        raise InputError("写入网页失败，请检查目录权限和可用空间；未确认导出成功。") from exc
    return {"ok": True, "version": VERSION, "display_name": "星际防线", "seed": seed,
            "output_path": str(path), "sha256": hashlib.sha256(html).hexdigest(), "bytes": len(html),
            "message": "已导出离线游戏网页。请用桌面浏览器打开；点击开始，左右方向键或 A/D 移动，空格射击，P 暂停。失去窗口焦点会自动暂停。"}


class ChineseFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix="用法：")


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage()
        self.exit(2, "参数无效；请提供输出文件绝对路径及整数 seed，使用 --help 查看中文帮助。\n")


def main():
    parser = ChineseParser(description="星际防线：导出无需联网的中文游戏网页。", formatter_class=ChineseFormatter, add_help=False)
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示帮助并退出")
    parser.add_argument("output_path", help="已有目录中新建 .html 文件的绝对路径（不覆盖）")
    parser.add_argument("--seed", type=int, default=12345, help="0 至 2147483647 的整数，默认 12345")
    args = parser.parse_args()
    try:
        result = execute(vars(args))
    except InputError as exc:
        result = {"ok": False, "version": VERSION, "message": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
