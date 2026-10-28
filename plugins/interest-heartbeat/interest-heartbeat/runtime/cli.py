"""命令行入口：定时任务会话里没有插件工具时，用 bash 调用同一引擎。

用法：python3 cli.py '<JSON 参数>'，例如 python3 cli.py '{"action": "beat"}'
输出与 interest_heartbeat 工具相同的 JSON 结果。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import InputError, execute  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        inputs = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"action": "status"}
        result = execute(inputs)
    except json.JSONDecodeError:
        result = {"ok": False, "message": "参数必须是一个 JSON 对象，例如 '{\"action\": \"beat\"}'。"}
    except InputError as e:
        result = {"ok": False, "message": str(e)}
    except (ValueError, TypeError, KeyError, UnicodeError):
        result = {"ok": False, "message": "输入或本地数据格式不正确，请按中文说明检查。"}
    except OSError:
        result = {"ok": False, "message": "本地数据目录读写失败，请检查路径与权限；未确认操作成功。"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
