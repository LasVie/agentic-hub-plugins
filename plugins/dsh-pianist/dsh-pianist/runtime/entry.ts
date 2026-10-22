// WorkSwarm 中文离线合成音色适配；原始 MIT 核心保存在 vendor/。
import { normalizeScore } from '../vendor/core/normalizer.js';
import { buildTimeline } from '../vendor/core/timeline.js';
import { transposeScore } from '../vendor/core/transpose.js';
import { generatePianoTone } from '../vendor/audio/generated-piano.js';
let text='';for await(const chunk of process.stdin)text+=chunk;
async function main(q:any){
 const notes=q.notes;
 if(!Array.isArray(notes)||notes.length<1||notes.length>256)throw Error('notes 必须包含1至256个音符。');
 const bpm=q.bpm??100;if(!Number.isFinite(bpm)||bpm<30||bpm>240)throw Error('速度必须为30至240 BPM。');
 const transpose=q.transpose??0;if(!Number.isInteger(transpose)||Math.abs(transpose)>24)throw Error('移调必须为-24至24的整数。');
 const events=notes.map((n:any,i:number)=>{
  if(!n||!Number.isInteger(n.midi)||n.midi<21||n.midi>108||!Number.isFinite(n.start_beat)||n.start_beat<0||n.start_beat>96||!Number.isFinite(n.beats)||n.beats<=0||n.beats>16||!Number.isFinite(n.velocity??0.65)||(n.velocity??0.65)<=0||(n.velocity??0.65)>1)throw Error('音符需要 MIDI 21–108、非负 start_beat、正 beats 和0至1的力度。');
  if(Math.round(n.beats*960)<1)throw Error('音符时值过短。');
  return {id:`n${i}`,type:'note',midi:n.midi,startTick:Math.round(n.start_beat*960),durationTicks:Math.round(n.beats*960),velocity:n.velocity??0.65,voiceId:'v1',trackId:'piano'};
 });
 let score=normalizeScore({id:'piano-local',title:String(q.title??'离线钢琴练习').slice(0,100),ppq:960,tempoMap:[{tick:0,bpm}],timeSignatureMap:[{tick:0,numerator:4,denominator:4}],tracks:[{id:'piano',instrument:{id:'generated-piano'},voices:[{id:'v1',events}]}]});
 if(transpose)score=transposeScore(score,transpose);
 const timeline=buildTimeline(score);const duration=timeline.durationSeconds+0.35;
 if(duration>60)throw Error('单次演奏最长60秒，请缩短乐谱。');
 const sampleRate=22050;const mixed=new Float32Array(Math.ceil(duration*sampleRate));
 const ons=new Map();
 for(const e of timeline.events){
  if(e.type==='noteOn')ons.set(e.noteId,e);
  if(e.type==='noteOff'){
   const on:any=ons.get(e.noteId);if(!on)continue;
   const tone=generatePianoTone({sampleRate,midi:on.midi,velocity:on.velocity,durationSeconds:e.time-on.time+0.2});
   const start=Math.round(on.time*sampleRate);const release=Math.max(1,Math.round(.2*sampleRate));
   for(let i=0;i<tone.length&&start+i<mixed.length;i++){const fade=i>=tone.length-release?(tone.length-i)/release:1;mixed[start+i]+=tone[i]*fade;}
  }
 }
 let peak=0;for(const n of mixed)peak=Math.max(peak,Math.abs(n));
 const gain=peak>0?0.9/Math.max(1,peak):1;
 const wav=Buffer.alloc(44+mixed.length*2);wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(sampleRate,24);wav.writeUInt32LE(sampleRate*2,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(mixed.length*2,40);
 for(let i=0;i<mixed.length;i++)wav.writeInt16LE(Math.round(Math.max(-1,Math.min(1,mixed[i]*gain))*32767),44+i*2);
 return {ok:true,message:'本地钢琴音频已生成，使用合成音色，无需账号或音色下载。',title:score.title,bpm,transpose,duration_seconds:duration,sample_rate:sampleRate,note_count:notes.length,wav_base64:wav.toString('base64'),score:JSON.parse(JSON.stringify(score,(_,v)=>typeof v==='bigint'?v.toString():v)),timeline:JSON.parse(JSON.stringify(timeline.events,(_,v)=>typeof v==='bigint'?v.toString():v))};
}
try{process.stdout.write(JSON.stringify(await main(JSON.parse(text))));}
catch(e:any){const msg=String(e.message);process.stdout.write(JSON.stringify({ok:false,message:/[\u4e00-\u9fff]/.test(msg)?msg:'乐谱校验失败，请检查音高范围、节拍与移调。'}));}
