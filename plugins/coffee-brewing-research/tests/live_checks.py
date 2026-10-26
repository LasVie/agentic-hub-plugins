"""Bounded actual public native calls; results remain in ignored local research."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--payload',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--quick',action='store_true')
args=parser.parse_args()
sys.dont_write_bytecode=True
payload=args.payload.resolve()
spec=importlib.util.spec_from_file_location('coffee_live',payload/'tools/coffee_tools.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def hashes():
    return {p.relative_to(payload).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in payload.rglob('*') if p.is_file()}


async def main():
    before=hashes()
    records=[]
    by_name={cls.remote_name:cls for cls in module.TOOL_TYPES}
    async def call(name,inputs):
        result=await by_name[name]().invoke(inputs)
        records.append({'tool':name,'arguments':inputs,'result':result})
        args.report.write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'model_calls':0,'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'tool':name,'ok':result.get('ok'),'server_version':result.get('server_version'),'error':result.get('error',{}).get('code')},ensure_ascii=False),flush=True)
        assert result['ok'],result.get('error')
        return result['data']
    data=await call('search_coffees',{'category':'espresso','price_max':30,'limit':3})
    assert isinstance(data,dict) and len(data.get('coffees',[]))>=2
    first,second=[x['id'] for x in data['coffees'][:2]]
    await call('get_coffee',{'id_or_name':first})
    if not args.quick:
        await call('find_similar',{'coffee':first,'limit':2})
        await call('get_recommendations',{'preferences':['chocolate','caramel'],'budget':20,'brew_method':'espresso','limit':2})
        # The service returned an ID it could not resolve in comparison. Exact
        # returned names work; do not hide that failed diagnostic or auto-retry.
        await call('compare_coffees',{'coffee_a':data['coffees'][0]['name'],'coffee_b':data['coffees'][1]['name']})
        await call('trending_coffees',{'limit':2})
        await call('what_to_brew',{'time_of_day':'evening','brew_method':'pourover'})
    await call('dial_in_suggestion',{'coffee':first,'brew_method':'espresso'})
    assert hashes()==before,'Runtime bytes changed during live invocation'
    print(json.dumps({'passed':len(records),'model_calls':0,'payload_unchanged':True}))


asyncio.run(main())
