"""Real-network checks through the actual native Tool.invoke path. Records field/count/digest
evidence only, not copied datasets. Needs the openjiuwen SDK; ~12 OpenF1 and ~8 Jolpica requests."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--payload', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()

spec = importlib.util.spec_from_file_location('pitwall_live', args.payload / 'tools/pitwall_tools.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

TIME = re.compile(r'^\d+:\d{2}\.\d{3}$')
checks = []


def digest(result):
    return hashlib.sha256(json.dumps(result.get('data'), sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


async def invoke(cls, inputs, name):
    tool = next(t for t in m.TOOL_TYPES if t.__name__ == cls)()
    result = await tool.invoke(inputs)
    assert result['ok'], (cls, result)
    assert result['summary_zh'] and result['warnings_zh'] and result['retrieved_at_utc']
    assert all(any('一' <= ch <= '鿿' for ch in w) for w in result['warnings_zh'])
    checks.append({'tool': tool.card.name, 'inputs': inputs, 'source': result['source'], 'data_sha256': digest(result), 'check': name})
    return result


async def main():
    r = await invoke('HistoricalResultsTool', {'year': 2024, 'race': '摩纳哥'}, 'classification top ten; 2024 Monaco winner is Charles Leclerc')
    top = r['data']['races'][0]['results']
    assert r['data']['mode'] == 'classification' and len(top) == 10 and top[0]['driver'] == 'Charles Leclerc'
    r = await invoke('HistoricalResultsTool', {'year': 2024, 'driver': 'hamilton'}, 'one result per 2024 round')
    assert r['data']['mode'] == 'driver_season' and 20 <= r['data']['returned_races'] <= 24
    assert all(len(x['results']) == 1 for x in r['data']['races'])
    r = await invoke('ChampionshipStandingsTool', {'year': 2024}, '2024 driver champion Max Verstappen 437 points')
    assert r['data']['entries'][0]['driver'] == 'Max Verstappen' and r['data']['entries'][0]['points'] == '437'
    r = await invoke('ChampionshipStandingsTool', {'year': 2024, 'standings_type': '车队'}, '2024 constructor champion McLaren 666 points')
    assert r['data']['entries'][0]['constructor'] == 'McLaren' and r['data']['entries'][0]['points'] == '666'
    r = await invoke('ChampionshipStandingsTool', {'year': 2024, 'standings_type': 'constructor', 'round': 10}, 'standings after round 10')
    assert r['data']['round'] == '10' and len(r['data']['entries']) >= 8
    r = await invoke('RaceWinnersHistoryTool', {'race': 'monaco', 'years': 3}, 'latest three Monaco winners include 2024 Leclerc')
    winners = {w['season']: w['winner'] for w in r['data']['winners']}
    assert len(winners) == 3 and winners.get('2024') == 'Charles Leclerc'
    r = await invoke('CircuitFastestLapTool', {'race': 'monza', 'year': 2024}, '2024 Monza fastest lap has a lap time and is not labelled a record')
    assert TIME.match(r['data']['fastest_lap']['time']) and any('不是该赛道的历史最快圈纪录' in w for w in r['warnings_zh'])
    r = await invoke('ListSessionsTool', {'year': 2024, 'country': '意大利', 'session_type': '正赛'}, 'Italy has Imola and Monza races')
    assert {s['location'] for s in r['data']['sessions']} == {'Imola', 'Monza'}
    key = next(s['session_key'] for s in r['data']['sessions'] if s['location'] == 'Monza')
    r = await invoke('SessionResultsTool', {'year': 2024, 'race': '蒙扎'}, 'Monza 2024 winner is Leclerc')
    assert r['data']['session']['session_key'] == key and r['data']['results'][0]['name_acronym'] == 'LEC' and len(r['data']['results']) >= 18
    r = await invoke('DriversTool', {'session_key': key}, 'grid includes VER and LEC')
    assert {'VER', 'LEC'} <= {d['name_acronym'] for d in r['data']['drivers']}
    r = await invoke('LapsTool', {'session_key': key, 'driver': 'VER', 'lap_from': 1, 'lap_to': 5}, 'five timed laps with a fastest lap')
    assert len(r['data']['laps']) == 5 and TIME.match(r['data']['statistics']['fastest_lap']['lap_time'])
    r = await invoke('PitStopsTool', {'session_key': key, 'driver': 'Leclerc'}, 'Leclerc has at least one stop on a positive lap number')
    assert r['data']['count'] >= 1 and all(isinstance(x['lap_number'], int) and x['lap_number'] >= 1 for x in r['data']['pit_stops'])
    r = await invoke('TyreStintsTool', {'session_key': key, 'driver': '16'}, 'Leclerc stints use known compounds and cover laps contiguously')
    stints = r['data']['stints']
    assert len(stints) >= 2 and {s['compound'] for s in stints} <= {'SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'}
    assert all(a['lap_end'] + 1 == b['lap_start'] for a, b in zip(stints, stints[1:]))
    r = await invoke('WeatherTool', {'session_key': key}, 'weather statistics are ordered and plausible')
    air = r['data']['statistics']['air_temperature']
    assert air['min'] <= air['mean'] <= air['max'] and -20 < air['min'] < 60
    r = await invoke('RaceControlTool', {'session_key': key, 'category': '旗语', 'limit': 5}, 'flag messages only, at most five')
    assert 1 <= len(r['data']['messages']) <= 5 and {x['category'] for x in r['data']['messages']} == {'Flag'}
    # failure paths through the real tool objects
    bad = await next(t for t in m.TOOL_TYPES if t.__name__ == 'SessionResultsTool')().invoke({'year': 2024, 'race': '意大利'})
    assert bad['error']['code'] == 'AMBIGUOUS_SESSION'
    old = await next(t for t in m.TOOL_TYPES if t.__name__ == 'SessionResultsTool')().invoke({'year': 2019, 'race': 'monza'})
    assert old['error']['code'] == 'INVALID_ARGUMENTS'
    checks.append({'check': 'ambiguous country and pre-2023 year are rejected with distinct codes'})
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': str(args.payload), 'model_calls': 0, 'tool_checks': len(checks),
              'checks': checks, 'sdk': importlib.metadata.version('openjiuwen'), 'python': sys.version.split()[0]}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'tool_checks': len(checks)}))

asyncio.run(main())
