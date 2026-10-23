#!/usr/bin/env python3
"""无需宿主 SDK 或模型的本地课表检查入口。"""
import importlib.util
import json
from pathlib import Path
import sys

HELP = """课表校验与导出 1.0.0 — 离线检查
用法：
  python audit_cli.py inspect /绝对路径/学校.fet
  python audit_cli.py verify /绝对路径/学校.fet /绝对路径/活动安排.xml
结果以 UTF-8 JSON 输出；不修改文件、不调用模型。
退出码：0 已检查范围无问题；1 发现问题；2 输入或运行错误。
完整 CSV/JSON 文件导出请使用宿主 export_fet_timetable 工具。
"""


def main(args):
    if args in ([], ["--help"], ["-h"]):
        print(HELP)
        return 0
    if not ((args[0] == "inspect" and len(args) == 2) or
            (args[0] == "verify" and len(args) == 3)):
        print(json.dumps({"ok": False, "version": "1.0.0", "error": {
            "code": "invalid_arguments", "message": "参数无效；使用 --help 查看中文用法。"}}, ensure_ascii=False))
        return 2
    source = Path(__file__).resolve().parents[1] / "lib/fet_audit.py"
    spec = importlib.util.spec_from_file_location("_fet_audit_cli", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.inspect_fet(args[1]) if args[0] == "inspect" else module.verify_timetable(*args[1:])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if not result["ok"] else (0 if result["passed"] else 1)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
