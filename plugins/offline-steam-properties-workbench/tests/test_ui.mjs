import test from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const helperUrl = process.env.STEAM_PAYLOAD
  ? pathToFileURL(resolve(process.env.STEAM_PAYLOAD, 'web/ui_helpers.mjs')).href
  : new URL('../offline-steam-properties-workbench/web/ui_helpers.mjs', import.meta.url).href;
const {exampleProject,clone,validateProject,projectJson,parseProject,pressureKpa,temperatureC,temperatureK,kiloEnergy,displayNumber,chartData,nearestIndex,phaseLabel,resultCsv,MAX_PROJECT_BYTES} = await import(helperUrl);

test('display units convert SI without modifying authoritative project values',()=>{
  const project=exampleProject(),original=clone(project);
  assert.equal(pressureKpa(project.state.pressure_pa),101.325);
  assert.equal(temperatureC(373.15),100);
  assert.ok(Math.abs(kiloEnergy(2256403.721)-2256.403721)<1e-10);
  assert.deepEqual(project,original);
  assert.equal(displayNumber(0),'0');assert.notEqual(displayNumber(1e-12),'0');assert.equal(displayNumber(null),'—');
});

test('project JSON preserves SI values and all three state pairs through a fresh parse',()=>{
  const project=exampleProject();project.name='精确输入与温度';
  for(const state of [{pair:'PQ',pressure_pa:101325.123456789,quality:.125},{pair:'PT',pressure_pa:500000,temperature_k:473.15123456789},{pair:'TQ',temperature_k:373.15,quality:1}]){
    project.state=state;assert.deepEqual(parseProject(projectJson(project)),project);
  }
});

test('bounded exact-key import rejects unknown code, malformed numbers, duplicate and prototype keys',()=>{
  for(const bad of [{...exampleProject(),script:'fetch("https://example.invalid")'},{...exampleProject(),state:{pair:'__proto__'}},{...exampleProject(),state:{pair:'PQ',pressure_pa:101325,quality:true}},{...exampleProject(),state:{pair:'PQ',pressure_pa:101325,quality:null}},{...exampleProject(),state:{pair:'PQ',pressure_pa:Infinity,quality:0}}])assert.throws(()=>validateProject(bad));
  assert.throws(()=>parseProject('{"schema":"steam-properties/v1","schema":"x"}'),/重复字段/);
  assert.throws(()=>parseProject('{"a":1,"\\u0061":2}'),/重复字段/);
  assert.throws(()=>parseProject('{"schema":"steam-properties/v1","__proto__":{"polluted":true}}'),/未知字段/);
  assert.equal({}.polluted,undefined);
  assert.throws(()=>parseProject('x'.repeat(MAX_PROJECT_BYTES+1)),/256 KiB/);
  assert.throws(()=>parseProject('{"name":NaN}'),/有效 JSON/);
  for(const pair of ['__proto__','constructor','toString'])assert.throws(()=>validateProject({...exampleProject(),state:{pair}}),/状态组合只能是/);
  assert.throws(()=>parseProject(JSON.stringify(exampleProject()).replace('101325','1e400')),/绝对压力必须是有限数值/);
});

test('physical input bounds distinguish PT from saturation input and cap scan size',()=>{
  const p=exampleProject();
  p.state={pair:'PT',pressure_pa:1000,temperature_k:800};assert.equal(validateProject(p),p);
  p.state={pair:'TQ',temperature_k:640,quality:1};p.sweep={variable:'temperature_k',start:273.16,end:640,points:100};validateProject(p);
  for(const mutate of [q=>q.state.temperature_k=640.001,q=>q.sweep.points=101,q=>q.sweep.points=2.1,q=>q.sweep.start=q.sweep.end,q=>q.sweep.start=273.15]){const q=clone(p);mutate(q);assert.throws(()=>validateProject(q));}
});

test('edited Celsius boundaries convert exactly while strict SI limits still reject lower input',()=>{
  assert.equal(temperatureK(0.01),273.16);
  assert.equal(temperatureK(366.85),640);
  assert.equal(temperatureK(526.85),800);
  for(const state of [
    {pair:'PT',pressure_pa:101325,temperature_k:temperatureK(0.01)},
    {pair:'TQ',temperature_k:temperatureK(0.01),quality:0},
  ]){
    const p={...exampleProject(),state,sweep:{variable:'temperature_k',start:temperatureK(0.01),end:temperatureK(366.85),points:2}};
    assert.equal(validateProject(p),p);
    assert.equal(parseProject(projectJson(p)).state.temperature_k,273.16);
    for(const temperature of [temperatureK(0.009),273.15999999999997]){
      const lowerState=clone(p);lowerState.state.temperature_k=temperature;
      assert.throws(()=>validateProject(lowerState),/温度/);
      const lowerSweep=clone(p);lowerSweep.sweep.start=temperature;
      assert.throws(()=>validateProject(lowerSweep),/扫描/);
    }
  }
});

// Synthetic presentation fixtures, not independent thermodynamic reference data.
const rows=[
  {pressure_pa:10000,temperature_k:318.956,liquid_density_kg_m3:989.8,vapor_density_kg_m3:.068,liquid_enthalpy_j_kg:191800,vapor_enthalpy_j_kg:2584000,latent_heat_j_kg:2392200},
  {pressure_pa:101325,temperature_k:373.1243,liquid_density_kg_m3:958.4,vapor_density_kg_m3:.598,liquid_enthalpy_j_kg:419100,vapor_enthalpy_j_kg:2675500,latent_heat_j_kg:2256400},
  {pressure_pa:2000000,temperature_k:485.527,liquid_density_kg_m3:849.8,vapor_density_kg_m3:10.0,liquid_enthalpy_j_kg:908600,vapor_enthalpy_j_kg:2798000,latent_heat_j_kg:1889400},
];

test('chart coordinates and hover indexes refer to actual irregular SI sample positions',()=>{
  const plot=chartData(rows,'pressure_pa','enthalpy');
  assert.deepEqual(plot.x,[10,101.325,2000]);
  assert.deepEqual(plot.series[0].values,[191.8,419.1,908.6]);
  assert.deepEqual(plot.series[1].values,[2584,2675.5,2798]);
  assert.equal(nearestIndex(plot.x,100),1);assert.equal(nearestIndex(plot.x,-100),0);assert.equal(nearestIndex(plot.x,9000),2);
  const temperaturePlot=chartData(rows,'temperature_k','pressure');
  assert.ok(Math.abs(temperaturePlot.x[1]-99.9743)<1e-10);
  assert.equal(temperaturePlot.series[0].values[1],101.325);
  assert.match(temperaturePlot.xLabel,/°C/);assert.match(temperaturePlot.yLabel,/绝对压力/);
});

test('chart bounds contain both phases and handle equal values without invented samples',()=>{
  const plot=chartData(rows,'pressure_pa','density');
  assert.ok(plot.yMin<.068&&plot.yMax>989.8);
  const flat=chartData(rows.map(row=>({...row,latent_heat_j_kg:1000})),'pressure_pa','latent');
  assert.ok(flat.yMin<1&&flat.yMax>1);assert.equal(flat.x.length,rows.length);
  assert.throws(()=>chartData([...rows].reverse(),'pressure_pa','density'),/严格递增/);
  assert.throws(()=>chartData(rows.map(row=>({...row,temperature_k:NaN})),'pressure_pa','temperature'),/无效数值/);
  assert.throws(()=>chartData(rows,'pressure_pa','constructor'),/数据不足/);
});

test('CSV contains full SI precision, state and both saturation phases with consistent columns',()=>{
  const sample={state:{pressure_pa:101325,temperature_k:373.124300000123,density_kg_m3:958.4,enthalpy_j_kg:419100.123456,entropy_j_kg_k:1306.9,phase:'液态',quality:0},saturation:{pressure_pa:101325,temperature_k:373.1243,liquid:{density_kg_m3:958.4,enthalpy_j_kg:419100,entropy_j_kg_k:1306.9},vapor:{density_kg_m3:.598,enthalpy_j_kg:2675500,entropy_j_kg_k:7354.8},latent_heat_j_kg:2256400},sweep:rows};
  const csv=resultCsv(sample),lines=csv.slice(1).trimEnd().split('\r\n');
  assert.equal(csv.charCodeAt(0),0xfeff);assert.equal(lines.length,7);
  assert.ok(lines.every(line=>line.split(',').length===14));
  assert.match(csv,/373\.124300000123/);assert.match(csv,/419100\.123456/);assert.match(csv,/饱和液体/);assert.match(csv,/饱和蒸汽/);
  assert.equal(phaseLabel('气液两相'),'气液两相');assert.equal(phaseLabel('constructor'),'相态未确定');
});
