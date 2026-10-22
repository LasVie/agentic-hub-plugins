"""WorkSwarm 钢琴 Tool：复用上游时间线与合成音色，导出独立中文播放器。"""
import asyncio, base64, html, json, uuid
from pathlib import Path
from openjiuwen.core.foundation.tool import Tool, ToolCard
from ..runtime.bridge import PluginError, workspace, safe_path, run_node, failure

class PluginTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id='dsh_pianist',name='dsh_pianist',description='离线生成钢琴演奏 WAV、乐谱 JSON 和含88键可试听键盘的中文 HTML 播放器。输入音符用 MIDI、start_beat、beats、velocity。无需账号、音色下载或网络。',input_params={'type':'object','properties':{'workspace_dir':{'type':'string'},'title':{'type':'string'},'bpm':{'type':'number'},'transpose':{'type':'integer'},'notes':{'type':'array','items':{'type':'object','properties':{'midi':{'type':'integer'},'start_beat':{'type':'number'},'beats':{'type':'number'},'velocity':{'type':'number'}},'required':['midi','start_beat','beats'],'additionalProperties':False}}},'required':['workspace_dir','notes'],'additionalProperties':False},parallel_safe=False))
    def _run(self,q):
        root=workspace(q.get('workspace_dir'));result=run_node(q)
        if not result.get('ok'):return result
        folder=safe_path(root,'piano-'+uuid.uuid4().hex[:12]);folder.mkdir(mode=0o700)
        wav=base64.b64decode(result.pop('wav_base64'));(folder/'performance.wav').write_bytes(wav)
        (folder/'score.json').write_text(json.dumps(result['score'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        player=Path(__file__).resolve().parents[1]/'runtime/player.js'
        payload=json.dumps(result,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
        markup='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>离线钢琴演奏</title><style>body{font:16px system-ui;margin:0;background:#eef2f8;color:#172540}main{max-width:1100px;margin:45px auto;padding:32px;background:white;border-radius:22px;box-shadow:0 20px 60px #173b6814}h1{font-size:32px;margin:10px 0}.tag{display:inline-block;padding:7px 12px;border-radius:20px;background:#e6f4f0;color:#166b52}button,a{font:inherit}nav{display:flex;gap:12px;margin:22px 0}nav button,a.download{border:0;border-radius:10px;padding:12px 22px;background:#284c9b;color:white;text-decoration:none}audio{width:100%;margin:12px 0}#keyboard{display:flex;overflow:auto;border:1px solid #bdc8db;padding:14px;background:#1e2a40;border-radius:12px}.key{min-width:34px;height:148px;padding:110px 0 0;border:1px solid #9da7b8;border-radius:0 0 7px 7px;background:#fafafa;font-size:11px;color:#304058}.key.black{height:100px;min-width:25px;padding-top:60px;background:#172238;color:#fff}.key.active{background:#e0a547;color:#14223c}#status{padding:16px;background:#f2f5fb;border-radius:10px}.muted{color:#5d6c83;line-height:1.8}#time{font-variant-numeric:tabular-nums}</style><main><span class="tag">无需账号 · 完全离线 · 中文版 1.0.0</span><h1>__TITLE__</h1><p class="muted">__META__ · 上游生成式备用音色（不包含录音音色包）</p><audio controls src="data:audio/wav;base64,__AUDIO__"></audio><nav><button id="play">播放</button><button id="pause">暂停</button><button id="restart">从头播放</button><a class="download" href="data:audio/wav;base64,__AUDIO__" download="performance.wav">下载 WAV</a></nav><p id="time">0.0 秒</p><p id="status">已就绪：点击播放，或点击下面的琴键试听。</p><div id="keyboard" aria-label="88键钢琴"></div><p class="muted">键盘可左右滚动；MIDI 范围 A0–C8。播放需手动点击。文件不连接外部服务。<br>来源：dsh-pianist，保留 MIT 许可，修改与版权说明随插件提供。</p></main><script>window.PIANO=__DATA__;</script><script>__PLAYER__</script></html>'''
        markup=markup.replace('__TITLE__',html.escape(result['title'])).replace('__META__',f"{result['bpm']} BPM · {result['note_count']} 个音符 · {result['duration_seconds']:.1f} 秒").replace('__AUDIO__',base64.b64encode(wav).decode()).replace('__DATA__',payload).replace('__PLAYER__',player.read_text(encoding='utf-8'))
        (folder/'player.html').write_text(markup,encoding='utf-8')
        return {k:v for k,v in result.items() if k not in ('score','timeline')}|{'artifacts':{n:str(folder/n) for n in ('performance.wav','score.json','player.html')}}
    async def invoke(self,inputs,**kwargs):
        try:return await asyncio.to_thread(self._run,inputs)
        except Exception as exc:return failure(exc)
    async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
