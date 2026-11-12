"""Live checks of the tools against the real public services. Writes a JSON evidence file; makes only small read-only requests.
Run from a scratch cwd:  python -I -B live_checks.py --payload <payload dir> --out <evidence.json>
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--payload', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.payload.resolve() / 'tools'))
import jma_tools as J  # noqa: E402

CASES = [
    ('locate', {'place': '100-0005'}),
    ('locate', {'place': '35.681,139.767'}),
    ('locate', {'place': '東京'}),
    ('locate', {'place': '东京'}),
    ('locate', {'place': '長野県松本市丸の内3'}),
    ('locate', {'place': '旭川'}),
    ('locate', {'place': '冲绳'}),
    ('locate', {'place': '神奈川県'}),
    ('locate', {'place': '山形'}),
    ('locate', {'place': '999-9999'}),
    ('locate', {'place': '51.5,-0.12'}),
    ('locate', {'place': '大'}),
    ('rainfall', {'place': '東京', 'days': 4}),
    ('rainfall', {'place': '100-0005', 'days': 2}),
    ('rainfall', {'station_code': '44132', 'days': 1}),
    ('warnings', {'place': '100-0005'}),
    ('warnings', {'place': '旭川'}),
    ('warnings', {'place': '那覇', 'include_outlook': False}),
    ('warnings', {'place': '冲绳县', 'include_outlook': False}),
    ('site_rain_risk', {'place': '35.681,139.767'}),
    ('site_rain_risk', {'place': '長野県松本市丸の内3'}),
    ('wbgt', {'place': '東京', 'days': 2}),
    ('wbgt', {'place': '35.681,139.767', 'days': 1, 'times': '9:00,12:00,15:00'}),
    ('rainfall', {'days': 3}),
    ('wbgt', {'place': '東京', 'times': '25:99'}),
]


async def main():
    report = []
    for name, arguments in CASES:
        started = time.perf_counter()
        result = await J.call_tool(name, arguments)
        report.append({'tool': J.TOOL_PREFIX + name, 'arguments': arguments, 'seconds': round(time.perf_counter() - started, 2), 'result': result})
        status = 'ok' if result.get('ok') else 'error:' + result['error']['code']
        time.sleep(1.5)  # 留出余量，避免触发本插件对国土地理院的每分钟限流
        print(f"{J.TOOL_PREFIX + name:20} {json.dumps(arguments, ensure_ascii=False):60} {status:28} {report[-1]['seconds']}s", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


asyncio.run(main())
