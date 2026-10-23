import fs from 'node:fs';
import {buildParamMatrix} from '../vendor/param-matrix.mjs';
import {validateDesignBatch} from '../vendor/core/design-rules.mjs';
import {quickL0Estimate} from '../vendor/core/formula-engine.mjs';
const q=JSON.parse(fs.readFileSync(0,'utf8'));
try{
 for(const [k,lo,hi] of [['power_kw',0.01,10000],['speed_rpm',1,100000],['voltage_v',1,100000],['line_freq_hz',1,2000]]){
  const v=q[k];if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw Error(k+' 超出有效范围。');
 }
 if(!Number.isInteger(q.count)||q.count<1||q.count>120)throw Error('count 必须是1至120的整数。');
 if(!['induction','pmsm'].includes(q.motor_type))throw Error('motor_type 请选择 induction 或 pmsm。');
 const m=buildParamMatrix(q,{maxMatrixSize:120,strictMaxMatrixSize:true});
 const v=validateDesignBatch(m.matrix,{bgCaliber:'actual',engSlotFill:true,pfEtaBins:true});
 const ranked=[...v.passed,...v.warning].map(x=>({...x,estimate:quickL0Estimate(x.params,{bgCaliber:'actual',engSlotFill:true,pfEtaBins:true})})).filter(x=>x.estimate.feasible&&Number.isFinite(x.estimate.efficiency)).sort((a,b)=>b.estimate.efficiency-a.estimate.efficiency||a.index-b.index);
 console.log(JSON.stringify({ok:true,message:'本地粗筛计算完成；仅用于未标定的相对比较，不代表仿真或投产结论。',spec:m.spec,matrix:m.matrix,summary:v.summary,warnings:m.warnings,ranked:ranked.slice(0,10),rankable_count:ranked.length,reports:v.reports,confidence_note:'0.5 为上游公式通道标记，不是准确率或概率。'}));
}catch(e){console.log(JSON.stringify({ok:false,message:e.message}));}
