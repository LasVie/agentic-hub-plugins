from .common import *
import re,html
HERE=Path(__file__).resolve().parent
def validate(s):
 if not isinstance(s,dict) or not isinstance(s.get('board'),list) or len(s['board'])!=225 or any(type(x)is not int or x not in (0,1,2) for x in s['board']):raise InputError('棋盘数据损坏，请保留文件检查。')
 b=s['board'];black=b.count(1);white=b.count(2)
 if black not in (white,white+1) or type(s.get('revision'))is not int or s['revision']!=black+white:raise InputError('落子次数或版本数据不一致。')
 if s.get('turn')!=('black' if black==white else 'white') or s.get('status')not in ('playing','black_won','white_won','draw'):raise InputError('当前回合或胜负状态数据不一致。')
 if not isinstance(s.get('moves'),list) or len(s['moves'])!=s['revision']:raise InputError('落子记录不完整。')
 rebuilt=[0]*225
 for i,m in enumerate(s['moves']):
  r,c=m.get('row'),m.get('col')
  if type(r)is not int or type(c)is not int or not 0<=r<15 or not 0<=c<15 or m.get('side')!=('black' if i%2==0 else 'white') or rebuilt[r*15+c]:raise InputError('落子记录损坏。')
  rebuilt[r*15+c]=1 if i%2==0 else 2
 if rebuilt!=b:raise InputError('落子记录和棋盘不一致。')
def snapshot(s,title):
 moves={(m['row'],m['col']):i+1 for i,m in enumerate(s['moves'])}
 rows=[]
 for r in range(15):
  cells=[]
  for c in range(15):
   v=s['board'][r*15+c];label=('黑' if v==1 else '白')+str(moves[(r,c)]) if v else '·'
   cells.append(f'<td class="s{v}" title="第{r+1}行，第{c+1}列">{label}</td>')
  rows.append('<tr><th>'+str(r+1)+'</th>'+''.join(cells)+'</tr>')
 status={'playing':'进行中','black_won':'黑方获胜','white_won':'白方获胜','draw':'和棋'}[s['status']]
 return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>本地五子棋</title><style>body{font-family:system-ui;background:#f6f0df;color:#28312b;padding:24px}table{border-collapse:collapse;background:#dbb773}td,th{border:1px solid #ab8a51;width:30px;height:30px;text-align:center}td.s1{background:#252525;color:white;border-radius:50%}td.s2{background:white;color:#333;border-radius:50%}h1{font-size:28px}</style><h1>本地五子棋 · '+html.escape(title)+'</h1><p>'+status+'；版本 '+str(s['revision'])+'；下一手 '+('黑方' if s['turn']=='black' else '白方')+'。五颗或以上连线获胜，无禁手。</p><table><tr><th>行/列</th>'+''.join('<th>'+str(c+1)+'</th>' for c in range(15))+'</tr>'+''.join(rows)+'</table><p>只读棋盘快照。继续对弈请在 WorkSwarm 对话中告诉智能体行列；界面坐标从1开始，工具坐标从0开始。数字是落子顺序。</p></html>'
def execute(q):
 root=workspace(q);action=q.get('action');gid=q.get('game_id','game-1')
 if not isinstance(gid,str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9-]{0,47}',gid):raise InputError('对局编号只能含字母、数字和短横线，最多48字符。')
 path=safe(root,'gomoku-'+gid+'.json')
 with locked(root,'gomoku-'+gid):
  if action=='new':
   if path.exists():raise InputError('对局已存在，请继续此局或选新 game_id，不能覆盖旧局。')
   s={'board':[0]*225,'moves':[],'revision':0,'turn':'black','status':'playing'};save(path,s)
  else:
   if not path.exists():raise InputError('尚无此对局，请先 new 新建。')
   s=json.loads(read(path,65536));validate(s)
   if action=='move':
    if s['status']!='playing':raise InputError('对局已结束，不能继续落子。')
    if type(q.get('expected_revision'))is not int or q['expected_revision']!=s['revision']:raise InputError('局面版本已变化，请先读取 state 再落子。')
    if q.get('side')!=s['turn']:raise InputError('落子方和当前回合不一致。')
    r,c=q.get('row'),q.get('col')
    if type(r)is not int or type(c)is not int or not 0<=r<15 or not 0<=c<15:raise InputError('行列必须是0至14的整数。')
    if s['board'][r*15+c]:raise InputError('该位置已有棋子，请选择空位。')
    side=s['turn'];s['board'][r*15+c]=1 if side=='black' else 2
    check=run_node(HERE/'engine.mjs',{'board':s['board'],'row':r,'col':c})
    s['moves'].append({'row':r,'col':c,'side':side});s['revision']+=1;s['turn']='white' if side=='black' else 'black'
    s['status']=side+'_won' if check['win'] else ('draw' if not check['has_empty'] else 'playing');save(path,s)
   elif action not in ('state','export'):raise InputError('请选择 new、state、move 或 export。')
  out=safe(root,'gomoku-'+gid+'.html');atomic(out,snapshot(s,gid))
  return {'ok':True,'message':{'playing':'棋局进行中。','black_won':'黑方连成五子，获胜。','white_won':'白方连成五子，获胜。','draw':'棋盘已满，和棋。'}[s['status']],**s,'state_file':str(path),'board_html':str(out),'coordinates':'工具行列从0开始；HTML显示从1开始。'}
