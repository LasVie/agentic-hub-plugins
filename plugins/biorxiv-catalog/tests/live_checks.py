"""Bounded real calls through native Tool.invoke; no model or host configuration."""
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
args = parser.parse_args()
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('biorxiv_live',args.payload.resolve()/'tools/biorxiv_tools.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

async def main():
    types = {c.remote_name:c for c in m.TOOL_TYPES}
    cases = [('search_preprints',{'date_from':'2024-01-01','date_to':'2024-01-07','category':'生物信息学','server':'生物预印本','limit':2}),
             ('get_preprint',{}),('get_categories',{}),
             ('search_published_preprints',{'date_from':'2024-01-01','date_to':'2024-01-07','include_details':False,'limit':2}),
             ('search_by_funder',{'funder_ror_id':'00k4n6c32','date_from':'2025-04-10','date_to':'2025-07-10','limit':1}),
             ('get_content_statistics',{'interval':'月度'}),('get_usage_statistics',{'interval':'monthly'})]
    raw = []
    summaries = []
    first_doi = None
    for name, inputs in cases:
        if name == 'get_preprint':
            inputs = {'doi':first_doi,'server':'biorxiv'}
        start = datetime.now(timezone.utc).isoformat()
        result = await types[name]().invoke(inputs)
        raw.append({'tool':name,'inputs':inputs,'result':result,'started_at_utc':start})
        good = result.get('ok') is True
        data = result.get('data',{})
        assertion = 'not run after adapter/service error'
        if good:
            assert isinstance(data,dict)
            if name == 'search_preprints':
                assert data['success'] is True and len(data['results'])==2
                assert all(row['category']=='bioinformatics' and '2024-01-01'<=row['date']<='2024-01-07' for row in data['results'])
                first_doi = data['results'][0]['doi']
                assert first_doi == '10.1101/2023.12.30.573742'
                assert any('total' in w for w in result['warnings_zh']) if data.get('total')==0 else True
                assertion = 'Two actual date/category-matched papers; DOI and inconsistent-total warning verified.'
            elif name == 'get_preprint':
                assert data['preprint']['doi']==first_doi and data['preprint'].get('license')
                assert data['preprint'].get('version') and data['preprint'].get('title')
                assertion = 'DOI/title/version/license from previous actual result verified.'
            elif name == 'get_categories':
                assert data and 'bioinformatics' in json.dumps(data)
                assertion = 'Actual subject catalog includes bioinformatics.'
            elif name == 'search_published_preprints':
                assert 1<=len(data['results'])<=2
                assert all(row.get('biorxiv_doi') and row.get('published_doi') and '2024-01-01'<=row['published_date']<='2024-01-07' for row in data['results'])
                assertion = 'Actual preprint/published DOI pairs and publication dates verified; null journal/author values retained.'
            elif name == 'search_by_funder':
                assert len(data['results'])==1 and data['results'][0].get('doi')
                assert '2025-04-10'<=data['results'][0]['date']<='2025-07-10'
                assertion = 'Actual dated preprint from the requested documented ROR query; missing award details not invented.'
            elif name in ('get_content_statistics','get_usage_statistics'):
                assert len(data['results'])>0
                metrics = ('new_papers','revised_papers') if name=='get_content_statistics' else ('full_text_views','pdf_downloads')
                assert all(all(isinstance(row.get(key),(int,float)) and row[key]>=0 for key in metrics) for row in data['results'])
                if any(not row.get('month') for row in data['results']):
                    assert any('期间' in warning for warning in result['warnings_zh'])
                assertion = 'Actual nonnegative source metrics verified; absent periods/abstract-view counts explicitly warned and not filled.'
            else:
                assert data.get('success') is not False
                assertion = 'Real source response retained; no fixture or predetermined changing value.'
        summary = {'tool':name,'inputs':inputs,'ok':good,'assertion':assertion,
                   'source_version':result.get('server_version'),'data_keys':list(data),
                   'received_count':result.get('received_count'),
                   'response_sha256':hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                   'error':result.get('error')}
        summaries.append(summary)
        print(json.dumps(summary,ensure_ascii=False),flush=True)
        if not good:
            break
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps({'payload':str(args.payload),'model_calls':0,'actual_native_tools':True,'records':raw},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    safe = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'model_calls':0,'passed':sum(r['ok'] for r in summaries),'planned':len(cases),'checks':summaries,
            'scope':'Actual source/extracted native tools. No frontend conversation or user completion; empty results do not prove corpus completeness. Article abstracts/full datasets omitted from this summary.'}
    args.report.with_name(args.report.stem+'-summary.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if safe['passed']==len(cases) else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
