"""Bounded real upstream calls through actual native Tool.invoke; no model call."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--payload', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
parser.add_argument('--quick', action='store_true')
args = parser.parse_args()
sys.dont_write_bytecode = True
payload = args.payload.resolve()
spec = importlib.util.spec_from_file_location('domain_research_live', payload / 'tools/domain_tools.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CASES = [
    ('search_prices', {'q': '.com,.org,.dev', 'sort': 'renewal', 'maxRenewalCents': 1500, 'limit': 3}),
    ('get_registrars', {}),
    ('check_availability_batch', {'name': 'example', 'tlds': 'com', 'cachedOnly': True}),
]
if not args.quick:
    CASES += [
        ('get_tld_prices', {'tld': 'com', 'registrar': 'porkbun', 'limit': 1}),
        ('estimate_cost', {'tld': 'com', 'registrar': 'porkbun', 'years': 3}),
        ('get_registrar_link', {'tld': 'com', 'registrar': 'porkbun', 'name': 'example'}),
        ('get_naming_guidance', {}),
        ('get_price_history', {'tld': 'com', 'registrar': 'porkbun'}),
        ('open_name_finder', {}),
        ('compare_domain_names', {'domains': 'example.com,example.org', 'maxRenewalCents': 1500}),
        ('check_availability', {'name': 'example', 'tld': 'com'}),
    ]


async def main():
    records = []
    by_name = {cls.remote_name: cls for cls in module.TOOL_TYPES}
    for name, arguments in CASES:
        started = datetime.now(timezone.utc).isoformat()
        result = await by_name[name]().invoke(arguments)
        record = {'tool': name, 'arguments': arguments, 'started_at_utc': started, 'result': result}
        data = result.get('data', {})
        if result.get('ok'):
            assert isinstance(data, dict), (name, type(data))
            if name == 'search_prices':
                assert 1 <= len(data['offers']) <= 3
                assert data['availability'] == 'not_checked'
                assert data['comparison']['url'].startswith('https://www.cheapest.domains/')
                assert all(offer.get('fetchedAt') and offer.get('sourceUrl') for offer in data['offers'])
            if name == 'open_name_finder':
                assert result['form_url'] == 'https://www.cheapest.domains/naming'
            record['functional_check'] = 'PASS'
        else:
            record['functional_check'] = 'REMOTE_OR_ADAPTER_FAILURE'
        records.append(record)
        print(json.dumps({'tool': name, 'ok': result.get('ok'), 'functional_check': record['functional_check'], 'error': result.get('error', {}).get('code'), 'api_version': data.get('apiVersion')}, ensure_ascii=False), flush=True)
        if not result.get('ok'):
            # Do not repeatedly probe an unavailable/rate-limited service.
            break
    report = {'payload': str(payload), 'manifest_sha256': hashlib.sha256((payload / 'manifest.json').read_bytes()).hexdigest(), 'actual_native_tools': True, 'model_calls': 0, 'credentials': 'none', 'records': records, 'passed': sum(r['functional_check'] == 'PASS' for r in records), 'planned': len(CASES), 'optional_radar': 'not called; independent noncommercial data terms', 'private_domain_names': 'none; only IANA example names used'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'report': str(args.report), 'passed': report['passed'], 'planned': report['planned'], 'model_calls': 0}))
    return 0 if report['passed'] == report['planned'] else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
