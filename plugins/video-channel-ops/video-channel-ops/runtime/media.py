"""视频频道日更流水线：FFmpeg 渲染与上传前机器检查。

改编自 channelroom-studio/ai-youtube-os@a4eb2f9（MIT，Copyright (c) 2026 Channelroom Studio）
plugins/ai-youtube-os/scripts/render.py 与 scripts/preflight.py。修改：由命令行脚本改为可调用函数并返回
结构化结果；检查结果与报错改为中文；FFmpeg 路径可由环境变量指定；限制场景路径不得越出运行目录；
音量解析失败时报告“未确认”而不是崩溃。完整许可见 licenses/ai-youtube-os/LICENSE。
"""
from pathlib import Path
import json,os,re,shutil,subprocess
FPS=30
AUDIO_EXTS=('.mp3','.wav','.m4a','.aac')
SILENT_DB=-60.0       # 平均音量低于此值视为几乎无声
LOUD_PEAK_DB=-0.5     # 峰值高于此值可能削波
SHORTS_MAX_SEC=180.0  # YouTube Shorts 时长上限
CAPTION_GAP_SEC=3.0   # 字幕结束时间与视频结尾相差超过此值，可能被截断
class MediaError(ValueError):pass
def tool(name):
 p=os.environ.get(name.upper()+'_PATH') or shutil.which(name)
 if not p:raise MediaError(f'未找到 {name}。请先安装 FFmpeg 并加入 PATH，或用环境变量 {name.upper()}_PATH 指定可执行文件路径。')
 return p
def run(cmd,**kw):
 try:return subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1800,**kw)
 except subprocess.TimeoutExpired:raise MediaError('FFmpeg 运行超过 30 分钟未结束，已停止；未生成可信结果。')
def audio_duration(path):
 r=run([tool('ffprobe'),'-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)])
 try:return float(r.stdout.strip())
 except ValueError:raise MediaError(f'无法读取音频时长：{path.name}')
def plan_durations(durations,audio_len):
 """拉长最后一个场景，使视频总长不短于旁白。"""
 if not durations:raise MediaError('scenes.json 中没有场景。')
 if any(d<=0 for d in durations):raise MediaError('场景时长必须为正数。')
 short=audio_len-sum(durations)
 if short>0:durations=durations[:-1]+[durations[-1]+short]
 return durations
def inside(base,rel):
 p=(base/rel).resolve()
 if base.resolve() not in p.parents and p!=base.resolve():raise MediaError(f'场景路径不能越出运行目录：{rel}')
 return p
def render(run_dir,long_form=False):
 sf=run_dir/'scenes.json'
 if not sf.is_file():raise MediaError(f'运行目录中缺少 scenes.json：{run_dir}')
 scenes=json.loads(sf.read_text(encoding='utf-8'))
 if not isinstance(scenes,list):raise MediaError('scenes.json 必须是数组，例如 [{"image": "scene01.png", "duration": 3.5}]。')
 audio=next((p for p in sorted(run_dir.glob('narration.*')) if p.suffix.lower() in AUDIO_EXTS),None)
 if audio is None:raise MediaError(f'运行目录中没有旁白音频 narration.mp3/.wav/.m4a/.aac：{run_dir}')
 w,h=(1920,1080) if long_form else (1080,1920)
 durations=plan_durations([float(s['duration']) for s in scenes],audio_duration(audio))
 inputs,chains=[],[]
 for i,(s,d) in enumerate(zip(scenes,durations)):
  img=inside(run_dir,s['image'])
  if not img.is_file():raise MediaError(f'找不到场景图片：{s["image"]}')
  inputs+=['-loop','1','-t',f'{d:.3f}','-i',str(img)]
  chains.append(f'[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p[v{i}]')
 concat=''.join(f'[v{i}]' for i in range(len(scenes)))+f'concat=n={len(scenes)}:v=1:a=0[vout]'
 out=run_dir/'final.mp4'
 r=run([tool('ffmpeg'),'-y','-hide_banner','-loglevel','error',*inputs,'-i',str(audio),'-filter_complex',';'.join(chains+[concat]),
  '-map','[vout]','-map',f'{len(scenes)}:a','-c:v','libx264','-crf','20','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)])
 if r.returncode!=0 or not out.is_file():raise MediaError('FFmpeg 渲染失败：'+(r.stderr.strip()[-600:] or '无错误输出'))
 return {'video':str(out),'size':f'{w}x{h}','scene_seconds':[round(d,3) for d in durations]}
def probe(path):
 r=run([tool('ffprobe'),'-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)])
 if r.returncode!=0:raise MediaError(f'ffprobe 无法读取该视频：{path.name}')
 return json.loads(r.stdout)
def volume(path):
 err=run([tool('ffmpeg'),'-hide_banner','-i',str(path),'-af','volumedetect','-f','null','-']).stderr
 m=re.search(r'mean_volume: (-?[\d.]+|-inf) dB',err);p=re.search(r'max_volume: (-?[\d.]+|-inf) dB',err)
 if not m or not p:return None,None
 return float(m.group(1).replace('-inf','-999')),float(p.group(1).replace('-inf','-999'))
def last_caption_end(srt):
 ends=re.findall(r'--> (\d+):(\d+):(\d+)[,.](\d+)',srt)
 if not ends:return 0.0
 h,m,s,ms=map(int,ends[-1])
 return h*3600+m*60+s+ms/1000
def checks(info,mean_db,peak_db,caption_end,has_volume=True):
 """纯判定逻辑：返回 (状态, 项目, 说明) 行；状态为 PASS/WARN/FAIL。"""
 rows=[]
 streams=info.get('streams',[])
 video=next((s for s in streams if s.get('codec_type')=='video'),None)
 has_audio=any(s.get('codec_type')=='audio' for s in streams)
 dur=float(info['format']['duration'])
 if video is None:rows.append(('FAIL','画面','没有视频轨'))
 else:
  w,h=video['width'],video['height'];vertical=h>w
  rows.append(('PASS','分辨率',f'{w}x{h}（{"竖屏/Shorts" if vertical else "横屏"}）'))
  if vertical and dur>SHORTS_MAX_SEC:rows.append(('WARN','时长',f'{dur:.1f} 秒，超过 Shorts {SHORTS_MAX_SEC:.0f} 秒上限'))
 rows.append(('PASS','时长',f'{dur:.1f} 秒'))
 if not has_audio:rows.append(('FAIL','音频','没有音频轨'))
 elif not has_volume:rows.append(('WARN','音频','未能读取音量，音量未确认'))
 elif mean_db<SILENT_DB:rows.append(('FAIL','音频',f'平均 {mean_db:.1f} dB，几乎无声'))
 elif peak_db>LOUD_PEAK_DB:rows.append(('WARN','音频',f'峰值 {peak_db:.1f} dB，可能削波'))
 else:rows.append(('PASS','音频',f'平均 {mean_db:.1f} dB，峰值 {peak_db:.1f} dB'))
 if caption_end is not None:
  gap=dur-caption_end
  rows.append(('PASS' if abs(gap)<=CAPTION_GAP_SEC else 'WARN','字幕',f'最后一条字幕结束于 {caption_end:.1f} 秒，视频 {dur:.1f} 秒'))
 return rows
def preflight(video,srt=None):
 if not video.is_file():raise MediaError(f'找不到视频文件：{video}')
 info=probe(video)
 has_audio=any(s.get('codec_type')=='audio' for s in info.get('streams',[]))
 mean,peak=volume(video) if has_audio else (None,None)
 cap=None
 if srt is not None:
  if not srt.is_file():raise MediaError(f'找不到字幕文件：{srt}')
  cap=last_caption_end(srt.read_text(encoding='utf-8-sig'))
 rows=checks(info,mean,peak,cap,has_volume=mean is not None)
 return rows
