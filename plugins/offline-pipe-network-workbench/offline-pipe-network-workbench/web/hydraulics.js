// Fixed public EPANET C-API adapter. No generated expressions or arbitrary commands.
import EpanetEngine from './vendor/epanet/index.mjs';
import {VERSION, ModelError, validateModel} from './network.js';
const warningText = {
  1:'水力计算未收敛，结果仅供诊断，不能导出为有效方案。',
  2:'水力计算存在不稳定状态，结果仅供诊断。',
  3:'引擎报告网络不连通。', 4:'引擎报告供水条件不足。',
  5:'引擎报告控制条件异常。', 6:'存在负压力：固定需水模型仍强制满足需水量，不代表现实可供水。'
};
export async function solveNetwork(input, options = {}) {
  const model = validateModel(input), warnings = [];
  const engine = await EpanetEngine({...options, print:()=>{}, printErr:()=>{}});
  const ptr = engine._malloc(8); let ph = 0;
  const call = (fn, types, values) => {
    const code = engine.ccall(fn, 'number', types, values);
    if (code >= 100) throw new ModelError(`epanet_${code}`, code === 110 ? '水力计算未收敛；未生成有效结果，请检查管径、需水量和供水条件。' : `EPANET 拒绝此模型（代码 ${code}）；请检查参数。`);
    if (code > 0 && !warnings.some(w=>w.code === code)) warnings.push({code, message:warningText[code] || `引擎报告警告 ${code}；请独立核对。`});
    return code;
  };
  const api = (name, types, values) => call(name, ['number',...types], [ph,...values]);
  const get = (name, index, prop) => {
    api(name, ['number','number','number'], [index, prop, ptr]);
    const value = engine.getValue(ptr, 'double');
    if (!Number.isFinite(value)) throw new ModelError('invalid_result', '引擎返回非有限结果，不能导出。');
    return value;
  };
  try {
    call('EN_getversion', ['number'], [ptr]);
    const revision = engine.getValue(ptr, 'i32');
    if (revision !== 20305) throw new ModelError('engine_version', '引擎版本不符，未运行模型。');
    call('EN_createproject', ['number'], [ptr]); ph = engine.getValue(ptr, 'i32');
    api('EN_init', ['string','string','number','number'], ['report.txt','out.bin',5,0]);
    // LPS / metres / mm, H-W, demand-driven, no patterns or minor losses.
    api('EN_setdemandmodel', ['number','number','number','number'], [0,0,0,0]);
    api('EN_setoption', ['number','number'], [0,200]);
    api('EN_setoption', ['number','number'], [1,0.000001]);
    const nodeIndices = new Map();
    // EPANET inserts junctions before reservoir/tank entries and shifts indexes.
    for (const n of [...model.nodes].sort((a,b)=>(a.type==='reservoir')-(b.type==='reservoir'))) {
      api('EN_addnode', ['string','number','number'], [n.id,n.type === 'reservoir' ? 1 : 0,ptr]);
      const index = engine.getValue(ptr, 'i32'); nodeIndices.set(n.id,index);
      api('EN_setnodevalue', ['number','number','number'], [index,0,n.type === 'junction' ? n.elevation_m : n.head_m]);
      if (n.type === 'junction') api('EN_setnodevalue', ['number','number','number'], [index,1,n.demand_lps]);
    }
    const pipeIndices = new Map();
    for (const p of model.pipes) {
      api('EN_addlink', ['string','number','string','string','number'], [p.id,1,p.from,p.to,ptr]);
      const index = engine.getValue(ptr, 'i32'); pipeIndices.set(p.id,index);
      api('EN_setpipedata', ['number','number','number','number','number'], [index,p.length_m,p.diameter_mm,p.roughness,0]);
    }
    api('EN_solveH', [], []);
    const nodes = model.nodes.map(n=>({id:n.id,type:n.type,head_m:get('EN_getnodevalue',nodeIndices.get(n.id),10),pressure_m:n.type === 'junction' ? get('EN_getnodevalue',nodeIndices.get(n.id),11) : null,demand_lps:get('EN_getnodevalue',nodeIndices.get(n.id),9)}));
    const pipes = model.pipes.map(p=>({id:p.id,from:p.from,to:p.to,flow_lps:get('EN_getlinkvalue',pipeIndices.get(p.id),8),velocity_mps:get('EN_getlinkvalue',pipeIndices.get(p.id),9),headloss_m:Math.abs(nodes.find(n=>n.id===p.from).head_m-nodes.find(n=>n.id===p.to).head_m)}));
    const residuals = nodes.filter(n=>n.type === 'junction').map(n=>({id:n.id,residual_lps:pipes.reduce((sum,p)=>sum+(p.to===n.id?p.flow_lps:0)-(p.from===n.id?p.flow_lps:0),0)-n.demand_lps}));
    const maxResidual = Math.max(0,...residuals.map(n=>Math.abs(n.residual_lps)));
    if (nodes.some(n=>n.pressure_m !== null && n.pressure_m < 0) && !warnings.some(w=>w.code===6)) warnings.push({code:6,message:warningText[6]});
    if (maxResidual > 0.001) warnings.push({code:'continuity',message:'节点流量平衡残差超过 0.001 L/s，结果仅供诊断。'});
    const complete = !warnings.some(w=>[1,2,3,4,5,'continuity'].includes(w.code));
    return {version:VERSION,engine:'OWA-EPANET',engine_version:'2.3.5',analysis_complete:complete,model,nodes,pipes,warnings,max_continuity_residual_lps:maxResidual,units:{flow:'L/s',head:'m',pressure:'m water head',diameter:'mm',length:'m'},boundary:'仅对本次有限稳态固定需水模型求解；不证明实际供水能力、水质或工程安全。'};
  } finally {
    if (ph) engine.ccall('EN_deleteproject','number',['number'],[ph]);
    engine._free(ptr);
  }
}
