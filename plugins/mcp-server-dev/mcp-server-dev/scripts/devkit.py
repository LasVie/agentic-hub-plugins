#!/usr/bin/env python3
"""MCP 开发助手：显式选择开发路径，生成工程时不覆盖已有文件。"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

VERSION = "1.0.4"
ROOT = Path(__file__).resolve().parents[1]
BUILDER_ID = "4c94938898ed4d3580593e5535f2315b"
BUILDER_URL = "https://agentichub.openjiuwen.com/assets/" + BUILDER_ID
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def plan(spec: dict) -> dict:
    keys = {"local_access", "interactive_ui", "prototype"}
    if not isinstance(spec, dict) or set(spec) != keys:
        raise ValueError("spec 必须且只能包含 local_access、interactive_ui、prototype 三个键")
    if any(type(spec[key]) is not bool for key in keys):
        raise ValueError("spec 中的值必须全部为 JSON 布尔值 true 或 false")
    local, ui, prototype = (spec[k] for k in ("local_access", "interactive_ui", "prototype"))
    skills = ["build-mcp-app"] if ui else []
    if local and not prototype:
        skills.append("build-mcpb")
    return {
        "plugin_version": VERSION,
        "transport": "stdio" if local or prototype else "streamable-http",
        "distribution": "mcpb" if local and not prototype else "prototype" if prototype else "remote",
        "skills": skills,
        "base_development_asset": {"id": BUILDER_ID, "url": BUILDER_URL},
        "next": "使用 MCP Builder 完成基础服务与认证；使用配套 Skill 添加界面和本地打包流程。",
        "limits": ["生成的示例使用 stdio；远程部署和认证请通过 MCP Builder 另外实现并测试。",
                   "MCPB 示例要求 Node.js >=20，包内不包含 Node 运行时。",
                   "界面渲染需要支持 MCP Apps 的宿主，并须单独完成宿主实测。"]
    }


def scaffold(kind: str, output: Path, name: str, author: str) -> dict:
    if not SLUG.fullmatch(name) or len(name) > 64:
        raise ValueError("name 必须为不超过 64 个字符的小写 slug，只能使用小写字母、数字和单个连字符")
    if not author.strip() or len(author) > 128:
        raise ValueError("author 必须包含 1 至 128 个字符，且不能全部为空白")
    if kind not in {"app", "mcpb"}:
        raise ValueError("kind 必须为 app 或 mcpb")
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("output 不能已存在；已有工程不会被覆盖")
    if not output.parent.is_dir():
        raise ValueError("output 的父目录必须已存在")
    with tempfile.TemporaryDirectory(prefix="mcp-dev-", dir=output.parent) as tmp:
        stage = Path(tmp) / "project"
        shutil.copytree(ROOT / "templates" / kind, stage)
        shutil.copy2(ROOT / "templates/collect-licenses.mjs", stage / "collect-licenses.mjs")
        for path in stage.rglob("*"):
            if path.is_file():
                path.write_text(path.read_text(encoding="utf-8").replace("__PROJECT_NAME__", name), encoding="utf-8")
        if kind == "mcpb":
            manifest = {
                "manifest_version": "0.4", "name": name, "version": "0.1.0",
                "description": "只读有界加法示例；用于生产环境前须按业务需求修改并测试。",
                "author": {"name": author},
                "server": {"type": "node", "entry_point": "server.mjs", "mcp_config": {
                    "command": "node", "args": ["${__dirname}/server.mjs"]}},
                "compatibility": {"runtimes": {"node": ">=20"}}
            }
            (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(ROOT / "licenses", stage / "licenses")
        shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.md")
        if output.exists() or output.is_symlink():
            raise ValueError("生成过程中出现同名 output，已停止以避免覆盖")
        stage.rename(output)
    return {"plugin_version": VERSION, "kind": kind, "project": str(output),
            "name": name, "generated_version": "0.1.0", "runtime": "Node.js >=20",
            "commands": ["npm ci --ignore-scripts", "npm run build", "node server.mjs"] if kind == "app"
                        else ["npm ci --ignore-scripts --omit=dev", "node collect-licenses.mjs", "mcpb validate manifest.json", "mcpb pack"],
            "license_note": "分发前请审查生成代码和已安装依赖的实际许可及适用范围。"}


class ChineseHelpFormatter(argparse.HelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups, prefix or "用法：")


class ChineseArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("add_help", False)
        kwargs.setdefault("formatter_class", ChineseHelpFormatter)
        super().__init__(*args, **kwargs)
        self._positionals.title = "位置参数"
        self._optionals.title = "可选参数"
        self.add_argument("-h", "--help", action="help", help="显示此帮助信息并退出")

    def error(self, message):
        # argparse's diagnostic sentences are English; keep option names in the
        # usage and give an actionable Chinese message rather than translating
        # protocol/argument identifiers or relying on the system locale.
        self.print_usage(sys.stderr)
        self.exit(2, "错误：命令行参数无效或不完整，请运行 --help 查看参数和子命令用法。\n")


def main() -> None:
    p = ChineseArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION, help="显示插件版本并退出")
    sub = p.add_subparsers(dest="command", required=True, title="子命令", metavar="{plan,scaffold}")
    route = sub.add_parser("plan", help="根据 JSON 需求生成开发路径规划", description="读取 JSON 需求，输出规划；不生成或部署服务。")
    route.add_argument("spec", type=Path, help="包含三个布尔键的 JSON 文件路径")
    new = sub.add_parser("scaffold", help="生成 MCP App 或 MCPB 示例工程", description="在新的输出目录中生成示例工程。")
    new.add_argument("--kind", choices=["app", "mcpb"], required=True, help="示例类型")
    new.add_argument("--output", type=Path, required=True, help="尚不存在的工程目录，父目录必须已存在")
    new.add_argument("--name", required=True, help="工程小写 slug，最多 64 个字符")
    new.add_argument("--author", required=True, help="实际作者姓名，1 至 128 个字符")
    args = p.parse_args()
    try:
        if args.command == "plan":
            if args.spec.stat().st_size > 16_384:
                raise ValueError("spec 文件不能超过 16 KiB")
            result = plan(json.loads(args.spec.read_text(encoding="utf-8")))
        else:
            result = scaffold(args.kind, args.output, args.name, args.author)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as exc:
        print(f"错误：spec 不是有效的 JSON（第 {exc.lineno} 行，第 {exc.colno} 列）。", file=sys.stderr)
        raise SystemExit(2)
    except UnicodeError:
        print("错误：spec 必须为有效的 UTF-8 文本。", file=sys.stderr)
        raise SystemExit(2)
    except OSError as exc:
        print(f"错误：无法读取文件或创建工程，请检查路径、访问权限和剩余空间（系统错误码 {exc.errno}）。", file=sys.stderr)
        raise SystemExit(2)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
