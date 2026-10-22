import {generatePianoTone} from '../vendor/audio/generated-piano.js';
declare global {interface Window {PIANO:any}}
const data=window.PIANO;
const audio=document.querySelector('audio')!;
const status=document.getElementById('status')!;
const keyboard=document.getElementById('keyboard')!;
const voices=new Map<number,{source:AudioBufferSourceNode,gain:GainNode}>();
let ctx:AudioContext|undefined;
const label=(n:number)=>['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'][n%12]+(Math.floor(n/12)-1);
for(let n=21;n<=108;n++){
 const b=document.createElement('button');b.type='button';b.textContent=label(n);b.title=`演奏 ${label(n)}`;b.dataset.midi=String(n);b.className=[1,3,6,8,10].includes(n%12)?'key black':'key';
 b.addEventListener('click',async()=>{ctx??=new AudioContext();await ctx.resume();const old=voices.get(n);if(old){old.source.stop();voices.delete(n);}
 const tone=generatePianoTone({sampleRate:ctx.sampleRate,midi:n,velocity:.65,durationSeconds:1});const buffer=ctx.createBuffer(1,tone.length,ctx.sampleRate);buffer.copyToChannel(tone as Float32Array<ArrayBuffer>,0);const source=ctx.createBufferSource();const gain=ctx.createGain();gain.gain.value=.35;source.buffer=buffer;source.connect(gain).connect(ctx.destination);voices.set(n,{source,gain});source.onended=()=>voices.delete(n);source.start();b.classList.add('active');window.setTimeout(()=>b.classList.remove('active'),350);status.textContent=`正在试听：${label(n)} · 本地合成音色`;});
 keyboard.append(b);
}
function highlight(){
 const t=audio.currentTime;const active=new Set<number>();
 for(const e of data.timeline){if(e.time>t)break;if(e.type==='noteOn')active.add(e.midi);if(e.type==='noteOff')active.delete(e.midi);}
 for(const b of keyboard.children)(b as HTMLElement).classList.toggle('active',active.has(Number((b as HTMLElement).dataset.midi)));
 (document.getElementById('time')!).textContent=`${t.toFixed(1)} / ${Number(data.duration_seconds).toFixed(1)} 秒`;
 if(!audio.paused)requestAnimationFrame(highlight);
}
document.getElementById('play')!.addEventListener('click',async()=>{try{await audio.play();status.textContent='正在播放 · 点击琴键也可试听';highlight();}catch{status.textContent='播放未启动，请点击音频控件重试。';}});
document.getElementById('pause')!.addEventListener('click',()=>{audio.pause();status.textContent='已暂停，可继续播放。';});
document.getElementById('restart')!.addEventListener('click',async()=>{audio.currentTime=0;await audio.play();status.textContent='已从头播放';highlight();});
audio.addEventListener('play',highlight);audio.addEventListener('ended',()=>{status.textContent='演奏结束，可重新播放或试听琴键。';highlight();});
