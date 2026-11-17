// Original presentation helpers. Scientific values are supplied by CoolProp.
export const SCHEMA = 'steam-properties/v1';
export const MAX_PROJECT_BYTES = 256 * 1024;
export const exampleProject = () => ({schema:SCHEMA,name:'常压饱和水',state:{pair:'PQ',pressure_pa:101325,quality:0},sweep:{variable:'pressure_pa',start:10000,end:2000000,points:25}});
export const clone = value => JSON.parse(JSON.stringify(value));
export const displayNumber = value => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('zh-CN',{maximumSignificantDigits:8,notation:value!==0&&(Math.abs(value)<1e-5||Math.abs(value)>=1e10)?'scientific':'standard'}).format(value) : '—';
export const pressureKpa = value => value / 1000;
export const temperatureC = value => value - 273.15;
// Apply the decimal Celsius offset in hundredths for edited UI values. This
// keeps the supported 0.01 °C boundary exactly 273.16 K without rounding saved SI.
export const temperatureK = value => (value * 100 + 27315) / 100;
export const kiloEnergy = value => value / 1000;

function objectKeys(value, expected, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.getPrototypeOf(value) !== Object.prototype) throw new Error(`${label}必须是 JSON 对象。`);
  const keys=Object.keys(value);
  if (keys.length!==expected.length||keys.some(key=>!expected.includes(key))) throw new Error(`${label}包含未知字段或缺少必需字段；不接受脚本、样式或外部资源。`);
}
function finite(value,label) {if(typeof value!=='number'||!Number.isFinite(value))throw new Error(`${label}必须是有限数值。`);}
export function validateProject(value) {
  objectKeys(value,['schema','name','state','sweep'],'项目');
  if(value.schema!==SCHEMA)throw new Error('项目版本不受支持，需要 steam-properties/v1。');
  if(typeof value.name!=='string'||!value.name.trim()||value.name.length>80||/[\u0000-\u001f\u007f-\u009f]/.test(value.name))throw new Error('项目名称需要 1 至 80 个字符，不能包含控制字符。');
  const state=value.state,pair=state?.pair;
  if(!['PQ','PT','TQ'].includes(pair))throw new Error('状态组合只能是 PQ、PT 或 TQ。');
  const fields={PQ:['pair','pressure_pa','quality'],PT:['pair','pressure_pa','temperature_k'],TQ:['pair','temperature_k','quality']}[pair];
  if(!fields)throw new Error('状态组合只能是 PQ、PT 或 TQ。');
  objectKeys(state,fields,'状态输入');
  for(const key of fields.filter(key=>key!=='pair'))finite(state[key],{pressure_pa:'绝对压力',temperature_k:'绝对温度',quality:'干度'}[key]);
  if('pressure_pa'in state&&(state.pressure_pa<1000||state.pressure_pa>20000000))throw new Error('绝对压力需要在 1 至 20000 kPa 之间。');
  if('temperature_k'in state&&(state.temperature_k<273.16||state.temperature_k>(pair==='PT'?800:640)))throw new Error(pair==='PT'?'P–T 温度需要在 0.01 至 526.85 °C 之间。':'饱和温度需要在 0.01 至 366.85 °C 之间。');
  if('quality'in state&&(state.quality<0||state.quality>1))throw new Error('干度必须在 0 至 1 之间。');
  const sweep=value.sweep;objectKeys(sweep,['variable','start','end','points'],'扫描输入');
  if(!['pressure_pa','temperature_k'].includes(sweep.variable))throw new Error('扫描变量只能是 pressure_pa 或 temperature_k。');
  for(const key of ['start','end','points'])finite(sweep[key],'扫描参数');
  const low=sweep.variable==='pressure_pa'?1000:273.16,high=sweep.variable==='pressure_pa'?20000000:640;
  if(sweep.start<low||sweep.end>high||sweep.end<=sweep.start)throw new Error(sweep.variable==='pressure_pa'?'扫描需要满足 1 ≤ 起点 < 终点 ≤ 20000 kPa。':'扫描需要满足 0.01 ≤ 起点 < 终点 ≤ 366.85 °C。');
  if(!Number.isInteger(sweep.points)||sweep.points<2||sweep.points>100)throw new Error('采样点数必须是 2 至 100 的整数。');
  return value;
}
export function projectJson(value) {
  validateProject(value);
  const text=JSON.stringify(value,null,2)+'\n';
  if(new TextEncoder().encode(text).byteLength>MAX_PROJECT_BYTES)throw new Error('项目文件超过 256 KiB 限制。');
  return text;
}
export function parseProject(text) {
  if(typeof text!=='string'||new TextEncoder().encode(text).byteLength>MAX_PROJECT_BYTES)throw new Error('项目文件超过 256 KiB 限制。');
  let value;
  try {value=JSON.parse(text);}catch {throw new Error('项目不是有效 JSON，请检查文件内容。');}
  // JSON grammar is checked above; inspect its tokens for ambiguous duplicate
  // object keys before accepting the bounded declarative document.
  const tokens=text.match(/"(?:[^"\\]|\\.)*"|[{}\[\]:,]|[^\s{}\[\]:,]+/g)||[];
  let cursor=0;
  function visit(depth=0){
    if(depth>8)throw new Error('项目嵌套过深。');
    const token=tokens[cursor++];
    if(token==='{'){
      const keys=new Set();
      if(tokens[cursor]==='}'){cursor++;return;}
      do {const key=JSON.parse(tokens[cursor++]);if(keys.has(key))throw new Error('项目包含重复字段，无法确定其含义。');keys.add(key);cursor++;visit(depth+1);}while(tokens[cursor++]==',');
    }else if(token==='['){if(tokens[cursor]===']'){cursor++;return;}do{visit(depth+1);}while(tokens[cursor++]==',');}
  }
  visit();
  return validateProject(value);
}

export function phaseLabel(value) {
  const labels={liquid:'液相',gas:'气相',twophase:'液汽两相',two_phase:'液汽两相',supercritical:'超临界流体',supercritical_liquid:'超临界液相',supercritical_gas:'超临界气相',critical_point:'临界状态',unknown:'相态未确定'};
  return Object.hasOwn(labels,value)?labels[value]:(typeof value==='string'&&/[\u4e00-\u9fff]/.test(value)?value:'相态未确定');
}
export const CURVES = {
  temperature:{label:'饱和温度',unit:'°C',series:[{key:'temperature_k',label:'饱和温度',convert:temperatureC,color:'#176b8a'}]},
  pressure:{label:'饱和压力',unit:'kPa（绝对压力）',series:[{key:'pressure_pa',label:'饱和压力',convert:pressureKpa,color:'#176b8a'}]},
  enthalpy:{label:'比焓',unit:'kJ/kg',series:[{key:'liquid_enthalpy_j_kg',label:'饱和液体',convert:kiloEnergy,color:'#176b8a'},{key:'vapor_enthalpy_j_kg',label:'饱和蒸汽',convert:kiloEnergy,color:'#bd692c'}]},
  density:{label:'密度',unit:'kg/m³',series:[{key:'liquid_density_kg_m3',label:'饱和液体',convert:value=>value,color:'#176b8a'},{key:'vapor_density_kg_m3',label:'饱和蒸汽',convert:value=>value,color:'#bd692c'}]},
  latent:{label:'汽化潜热',unit:'kJ/kg',series:[{key:'latent_heat_j_kg',label:'汽化潜热',convert:kiloEnergy,color:'#176b8a'}]},
};
export function chartData(rows,variable,curve) {
  if(!Array.isArray(rows)||rows.length<2||!Object.hasOwn(CURVES,curve))throw new Error('扫描数据不足，无法绘制曲线。');
  const isPressure=variable==='pressure_pa';
  const x=rows.map(row=>isPressure?pressureKpa(row.pressure_pa):temperatureC(row.temperature_k));
  const series=CURVES[curve].series.map(item=>({...item,values:rows.map(row=>item.convert(row[item.key]))}));
  if([...x,...series.flatMap(item=>item.values)].some(value=>!Number.isFinite(value)))throw new Error('扫描结果包含无效数值。');
  if(x.some((value,index)=>index>0&&value<=x[index-1]))throw new Error('扫描结果的自变量必须严格递增。');
  const values=series.flatMap(item=>item.values),low=Math.min(...values),high=Math.max(...values);
  const pad=high===low?Math.max(Math.abs(high)*.05,1e-6):(high-low)*.08;
  return {x,series,xMin:x[0],xMax:x.at(-1),yMin:low-pad,yMax:high+pad,xLabel:isPressure?'绝对压力 / kPa':'温度 / °C',yLabel:`${CURVES[curve].label} / ${CURVES[curve].unit}`};
}
export function nearestIndex(values,target) {
  let index=0;for(let i=1;i<values.length;i++)if(Math.abs(values[i]-target)<Math.abs(values[index]-target))index=i;
  return index;
}
export function resultCsv(result) {
  if(!result?.state||!result?.saturation||!Array.isArray(result.sweep))throw new Error('当前没有完整结果可导出。');
  const headers=['部分','序号','压力_Pa','温度_K','密度_kg_m3','比焓_J_kg','比熵_J_kg_K','相态','干度','液体密度_kg_m3','蒸汽密度_kg_m3','液体比焓_J_kg','蒸汽比焓_J_kg','汽化潜热_J_kg'];
  const s=result.state,t=result.saturation;
  const rows=[headers,['单点状态','',s.pressure_pa,s.temperature_k,s.density_kg_m3,s.enthalpy_j_kg,s.entropy_j_kg_k,phaseLabel(s.phase),s.quality??'','','','','',''],
    ['饱和液体','',t.pressure_pa,t.temperature_k,t.liquid.density_kg_m3,t.liquid.enthalpy_j_kg,t.liquid.entropy_j_kg_k,'饱和液体',0,'','','','',t.latent_heat_j_kg],
    ['饱和蒸汽','',t.pressure_pa,t.temperature_k,t.vapor.density_kg_m3,t.vapor.enthalpy_j_kg,t.vapor.entropy_j_kg_k,'饱和蒸汽',1,'','','','',t.latent_heat_j_kg],
    ...result.sweep.map((row,index)=>['饱和扫描',index+1,row.pressure_pa,row.temperature_k,'','','','','',row.liquid_density_kg_m3,row.vapor_density_kg_m3,row.liquid_enthalpy_j_kg,row.vapor_enthalpy_j_kg,row.latent_heat_j_kg])];
  const cell=value=>{const text=String(value);return /[",\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;};
  return '\ufeff'+rows.map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
}
