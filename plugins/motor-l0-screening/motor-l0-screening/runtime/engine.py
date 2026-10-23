from .common import *
HERE=Path(__file__).resolve().parent
def execute(q):
 root=workspace(q)
 if q.get('action')!='screen':raise InputError('仅支持 screen 粗筛操作。')
 req={k:q.get(k,d) for k,d in [('power_kw',None),('speed_rpm',None),('voltage_v',380),('line_freq_hz',50),('count',20),('motor_type','induction')]}
 out=safe(root,q.get('report_file','motor-screening.json'))
 if out.suffix!='.json':raise InputError('报告必须使用 .json 扩展名。')
 r=run_node(HERE/'engine.mjs',req)
 if r.get('ok'):
  save(out,r)
  return {k:v for k,v in r.items() if k not in ('matrix','reports')}|{'report':str(out)}
 return r
