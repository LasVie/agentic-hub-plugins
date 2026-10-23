#!/usr/bin/env python3
"""不依赖宿主或模型的中文命令行入口。"""
import importlib.util
import json
from pathlib import Path
import sys

path=Path(__file__).resolve().parents[1]/"runtime/quota.py"
spec=importlib.util.spec_from_file_location("quota_cli_core",path)
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
if len(sys.argv)!=2 or sys.argv[1] not in ("policy","check","record","report"):
    print("消息配额与用量审计 1.0.1\n用法：python scripts/quota_cli.py policy|check|record|report < 请求.json\n--help 显示本说明。参数、示例及限制请参阅 README.md。")
    raise SystemExit(0 if sys.argv[1:]==["--help"] else 2)
try:
    request=core.strict_json(sys.stdin.read(512*1024+1))
    answer=core.dispatch(sys.argv[1],request)
except core.Failure as exc:
    answer={"ok":False,"version":core.VERSION,"error":{"code":exc.code,"message":exc.message}}
except (UnicodeError,RecursionError):
    answer={"ok":False,"version":core.VERSION,"error":{"code":"invalid_json","message":"请求编码或嵌套深度无效。"}}
print(json.dumps(answer,ensure_ascii=False,indent=2))
raise SystemExit(0 if answer["ok"] else 2)
