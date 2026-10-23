#!/usr/bin/env python3
"""本地命令行：标准输入接收 JSON 请求，标准输出只返回中文结构化结果。"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
path = Path(__file__).resolve().parents[1] / "runtime/verifier.py"
spec = importlib.util.spec_from_file_location("agent_letter_cli_core", path)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def main():
    if sys.argv[1:] in (["--help"], ["-h"]):
        print("代理信件完整性校验 1.0.1\n用法：python letter_cli.py policy|verify < 请求.json\n"
              "policy 参数：workspace、action（init/status/configure）；configure 还须 expected_revision 及 enabled/allow。\n"
              "verify 参数：workspace、letter_path。密钥只放在本地私有目录，不要粘贴到对话或请求。\n"
              "退出码：0 请求成功（仍须检查 verdict）；2 请求未完成。not_checked（未校验）不能当作通过。")
        return 0
    if len(sys.argv) != 2 or sys.argv[1] not in ("policy", "verify"):
        result = {"version": core.VERSION, "ok": False, "error": {"code": "invalid_operation", "message": "请指定 policy 或 verify；使用 --help 查看说明。"}}
    else:
        try:
            data = sys.stdin.buffer.read(core.MAX_LETTER + 1)
            core.require(len(data) <= core.MAX_LETTER, "request_too_large", "请求超过 1 MiB 上限。")
            result = core.dispatch(sys.argv[1], core.decode_json(data))
        except core.Refusal as err:
            result = {"version": core.VERSION, "ok": False, "error": {"code": err.code, "message": err.message}}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
