"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const form = $("plan-form");
  const names = {Sun:"太阳",Moon:"月球",Mercury:"水星",Venus:"金星",Mars:"火星",Jupiter:"木星",Saturn:"土星"};
  const colors = {Sun:"#d6ac4f",Moon:"#d9e5e8",Mercury:"#a6b0bd",Venus:"#ecc793",Mars:"#e38e74",Jupiter:"#9bc3b8",Saturn:"#b6a1d5"};
  const keys = ["latitude","longitude","elevation_m","start_utc","duration_hours","step_minutes","bodies","display_offset_minutes"];
  let result = null, revision = 0, controller = null;
  Object.entries(colors).forEach(([id,color]) => {
    const dot = document.querySelector(`[data-body="${id}"]`);
    if(dot) dot.style.backgroundColor = color;
  });
  // Fixed precision makes readouts comparable without implying more accuracy.
  const deg = n => Number.isFinite(n) ? `${n.toFixed(3)}°` : "—";
  function notice(text, kind="") { $("notice").textContent=text; $("notice").className=`notice ${kind}`; }
  function clearSvg(svg) { svg.replaceChildren(); }
  function invalidate(text="输入已改变，旧结果已清除。请重新计算。") {
    revision++; result=null;
    if(controller) {controller.abort(); controller=null;}
    $("calculate").disabled=false; $("calculate").textContent="计算观测计划 ↗";
    $("export-csv").disabled=true; $("time-index").disabled=true; $("time-index").value=0;
    $("selected-time").textContent="尚无当前结果"; $("selected-utc").textContent="UTC 为计算基准";
    $("above-count").textContent="—"; $("sample-info").textContent="—"; $("result-version").textContent="等待计算";
    $("sky-empty").hidden=false; $("timeline-empty").hidden=false;
    $("legend").replaceChildren(); $("twilight-events").replaceChildren();
    $("readings").replaceChildren(); const row=document.createElement("tr"),cell=document.createElement("td");cell.colSpan=6;cell.className="empty-cell";cell.textContent="没有当前结果；请计算后查看。";row.append(cell);$("readings").append(row);
    drawSkyGrid();drawTimelineGrid();notice(text);
  }
  function requestFromForm() {
    if(!form.reportValidity()) throw Error("请先修正标出的输入项。");
    if(form.elements.display_offset_minutes.value==="custom"&&!$("custom-offset").value.trim()) throw Error("请填写自定义固定时差。");
    const r={};
    for(const key of keys) {
      if(key==="bodies") r.bodies=[...form.querySelectorAll('input[name="bodies"]:checked')].map(e=>e.value);
      else if(key==="start_utc") r[key]=form.elements[key].value.trim();
      else if(key==="display_offset_minutes") r[key]=Number(form.elements[key].value==="custom"?$("custom-offset").value:form.elements[key].value);
      else r[key]=Number(form.elements[key].value);
    }
    validateRequest(r); return r;
  }
  function validateRequest(r) {
    if(!r||typeof r!=="object"||Array.isArray(r)) throw Error("计划必须是一个 JSON 对象。");
    if(Object.keys(r).some(k=>!keys.includes(k))) throw Error("计划含不支持的字段；请导入本工具导出的输入 JSON。");
    const limits={latitude:[-80,80],longitude:[-180,180],elevation_m:[-500,10000],duration_hours:[1/3600,24],step_minutes:[5,60],display_offset_minutes:[-840,840]};
    for(const [key,[lo,hi]] of Object.entries(limits)) {
      if(typeof r[key]!=="number"||!Number.isFinite(r[key])||r[key]<lo||r[key]>hi) throw Error(`${key} 必须为 ${lo} 至 ${hi} 范围内的有限数值。`);
    }
    if(!Number.isInteger(r.step_minutes)||!Number.isInteger(r.display_offset_minutes)) throw Error("采样间隔和显示时差必须为整数分钟。");
    if(Math.abs(r.duration_hours*3600-Math.round(r.duration_hours*3600))>0.000001) throw Error("计划时长必须对应整数秒，且至少为 1 秒。");
    if(!Array.isArray(r.bodies)||!r.bodies.length||r.bodies.length>7||new Set(r.bodies).size!==r.bodies.length||r.bodies.some(b=>!Object.hasOwn(names,b))) throw Error("请选择至少一个支持的天体，且不要重复。");
    if(typeof r.start_utc!=="string"||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(r.start_utc)) throw Error("UTC 时间格式应为 YYYY-MM-DDTHH:MM:SSZ。");
    const date=new Date(r.start_utc);
    if(!Number.isFinite(date.getTime())||date.toISOString().replace(".000Z","Z")!==r.start_utc||date.getUTCFullYear()<2000||date.getUTCFullYear()>2100) throw Error("请输入 2000–2100 年内真实有效的 UTC 日期和时间。");
    const end=new Date(date.getTime()+r.duration_hours*3600000);
    if(end.getUTCFullYear()>2100) throw Error("计划结束时间不能超出 2100 年。");
  }
  function fillForm(r) {
    validateRequest(r);
    for(const key of keys) {
      if(key==="bodies") form.querySelectorAll('input[name="bodies"]').forEach(e=>e.checked=r.bodies.includes(e.value));
      else if(key==="display_offset_minutes") {
        form.elements[key].value=[0,480].includes(r[key])?String(r[key]):"custom";$("custom-offset").value=r[key];
      } else form.elements[key].value=r[key];
    }
    $("custom-offset-label").hidden=form.elements.display_offset_minutes.value!=="custom";
  }
  async function api(path, data, signal) {
    const options={method:data===undefined?"GET":"POST",credentials:"same-origin",cache:"no-store",signal};
    if(data!==undefined) {options.headers={"Content-Type":"application/json"};options.body=JSON.stringify(data);}
    const response=await fetch(`api/${path}`,options);
    let body;
    try{body=await response.json();}catch{throw Error("本机服务返回了不可读取的响应，请检查服务状态。");}
    if(!response.ok||body.ok!==true){const e=Error(body.error?.message||"本机计算或文件操作未完成。");e.code=body.error?.code||String(response.status);throw e;}
    return body;
  }
  form.addEventListener("input",()=>{ $("custom-offset-label").hidden=form.elements.display_offset_minutes.value!=="custom";invalidate(); });
  form.addEventListener("change",()=>{ $("custom-offset-label").hidden=form.elements.display_offset_minutes.value!=="custom";invalidate(); });
  form.addEventListener("submit",async event=>{
    event.preventDefault();let request;
    try{request=requestFromForm();}catch(e){invalidate(e.message);notice(e.message,"error");return;}
    invalidate("正在本机计算位置与区间事件……");const current=revision;
    controller=new AbortController();const activeController=controller;
    $("calculate").disabled=true;$("calculate").textContent="计算中……";notice("正在本机计算位置与区间事件……","busy");
    try {
      const data=await api("plan",{request},activeController.signal);
      if(current!==revision) return;
      if(data.version!=="1.0.0"||!Array.isArray(data.times)||!data.times.length||!Array.isArray(data.bodies)) throw Error("结果版本或结构不符合当前插件，未显示该结果。");
      result=data;
      $("sky-empty").hidden=true;$("timeline-empty").hidden=true;
      $("export-csv").disabled=false;$("time-index").disabled=false;$("time-index").max=data.times.length-1;$("time-index").value=0;
      $("result-version").textContent=`v${data.version} · 引擎 ${data.engine_version}`;
      $("sample-info").textContent=`${data.times.length} 个时刻 · ${data.bodies.length} 个天体`;
      renderLegend();drawTimeline();renderAt(0);renderTwilight();renderConventions();
      notice(`计算完成。${data.times.length} 个采样时刻；拖动时间滑块查看真实读数。`);
    } catch(e) {if(current===revision&&e.name!=="AbortError") {invalidate(e.message);notice(e.message,"error");}}
    finally {if(current===revision){controller=null;$("calculate").disabled=false;$("calculate").textContent="计算观测计划 ↗";}}
  });
  const presets={singapore:{latitude:1.3521,longitude:103.8198,elevation_m:15,display_offset_minutes:480},beijing:{latitude:39.9042,longitude:116.4074,elevation_m:44,display_offset_minutes:480},north:{latitude:70,longitude:20,elevation_m:0,display_offset_minutes:0}};
  document.querySelectorAll("[data-place]").forEach(button=>button.addEventListener("click",()=>{for(const[k,v]of Object.entries(presets[button.dataset.place]))form.elements[k].value=v;$("custom-offset-label").hidden=true;invalidate("已载入示例地点。时间保持不变，请重新计算。");}));
  $("time-index").addEventListener("input",()=>{if(result)renderAt(Number($("time-index").value));});

  function svgNode(tag,attrs={},text){const n=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
  function append(svg,tag,attrs,text){const n=svgNode(tag,attrs,text);svg.append(n);return n;}
  function drawSkyGrid(){
    const svg=$("sky-chart");clearSvg(svg);const cx=300,cy=238,R=185;
    append(svg,"circle",{cx,cy,r:R,fill:"#17323a",stroke:"#4c676d","stroke-width":1.4});
    for(const altitude of [30,60])append(svg,"circle",{cx,cy,r:R*(90-altitude)/90,fill:"none",class:"chart-grid","stroke-dasharray":"3 5"});
    append(svg,"line",{x1:cx-R,y1:cy,x2:cx+R,y2:cy,class:"chart-grid"});append(svg,"line",{x1:cx,y1:cy-R,x2:cx,y2:cy+R,class:"chart-grid"});
    [["北 · 0°",300,31],["东 · 90°",535,242],["南 · 180°",300,454],["西 · 270°",65,242]].forEach(([t,x,y])=>append(svg,"text",{x,y,"text-anchor":"middle",class:"chart-text"},t));
    append(svg,"text",{x:cx+5,y:cy-5,class:"chart-label"},"天顶");
    for(const alt of [0,30,60])append(svg,"text",{x:cx+5,y:cy-R*(90-alt)/90-5,class:"chart-label"},`${alt}°`);
  }
  function renderAt(index){
    if(!result)return;drawSkyGrid();drawTimeCursor(index);
    const t=result.times[index];$("selected-time").textContent=t.display.replace("T"," ");$("selected-utc").textContent=`计算时刻 ${t.utc}`;
    let above=0;const svg=$("sky-chart"),rows=[];
    for(const body of result.bodies){
      const p=body.track[index],color=colors[body.id]||"#fff",isAbove=p.altitude_deg>=0;
      if(isAbove){above++;const r=185*(90-p.altitude_deg)/90,angle=p.azimuth_deg*Math.PI/180,x=300+r*Math.sin(angle),y=238-r*Math.cos(angle);const g=append(svg,"g",{});append(g,"title",{},`${body.name}：高度 ${deg(p.altitude_deg)}，方位 ${deg(p.azimuth_deg)}`);append(g,"circle",{cx:x,cy:y,r:6,fill:color,stroke:"#112630","stroke-width":2});append(g,"text",{x:x+10,y:y-8,fill:color,class:"body-label"},body.name);}
      const tr=document.createElement("tr");const label=document.createElement("td");label.textContent=body.name;tr.append(label);
      for(const value of [deg(p.altitude_deg),deg(p.azimuth_deg)]){const td=document.createElement("td");td.textContent=value;tr.append(td);}
      const state=document.createElement("td"),pill=document.createElement("span");pill.className=`state-pill${isAbove?"":" below"}`;pill.textContent=isAbove?"以上":"以下";state.append(pill);tr.append(state);
      for(const kind of ["rise","set"]){const td=document.createElement("td");const events=body.rise_set[kind]||[];if(events.length){events.forEach(event=>{const line=document.createElement("small");line.textContent=event.display.replace("T"," ");line.title=event.utc;td.append(line);});}else{td.textContent="区间内无事件";}tr.append(td);}rows.push(tr);
    }
    $("above-count").textContent=`${above} / ${result.bodies.length} 位于几何地平线以上`;
    $("readings").replaceChildren(...rows);
  }
  function drawTimelineGrid(){const svg=$("timeline-chart");clearSvg(svg);for(const a of [-90,-60,-30,0,30,60,90]){const y=chartY(a);append(svg,"line",{x1:60,y1:y,x2:1070,y2:y,stroke:a===0?"#77928e":"#304650","stroke-width":a===0?1.3:1,"stroke-dasharray":a===0?"5 4":""});append(svg,"text",{x:47,y:y+4,"text-anchor":"end",class:"chart-label"},`${a}°`);}}
  const chartY=alt=>25+(90-alt)/180*252;
  function chartX(index){if(!result||result.times.length<2)return 60;const start=Date.parse(result.times[0].utc),end=Date.parse(result.times.at(-1).utc);return 60+1010*(Date.parse(result.times[index].utc)-start)/(end-start);}
  function drawTimeline(){
    if(!result)return;const svg=$("timeline-chart");clearSvg(svg);
    const sun=result.sun_track||result.bodies.find(b=>b.id==="Sun")?.track;
    if(sun){for(let i=0;i<result.times.length-1;i++){const a=sun[i].altitude_deg,color=a>=0?"#73827a":a>=-6?"#576d70":a>=-12?"#334f62":a>=-18?"#233a53":"#152b40";append(svg,"rect",{x:chartX(i),y:25,width:Math.max(0,chartX(i+1)-chartX(i)),height:252,fill:color,opacity:.58});}}
    for(const a of [-90,-60,-30,0,30,60,90]){const y=chartY(a);append(svg,"line",{x1:60,y1:y,x2:1070,y2:y,stroke:a===0?"#adc0ad":"#4a5b62","stroke-width":a===0?1.3:1,"stroke-dasharray":a===0?"5 4":"",opacity:a===0?1:.5});append(svg,"text",{x:47,y:y+4,"text-anchor":"end",class:"chart-label"},`${a}°`);}
    const ticks=new Set([0,Math.round((result.times.length-1)/4),Math.round((result.times.length-1)/2),Math.round((result.times.length-1)*3/4),result.times.length-1]);
    for(const i of ticks){const t=result.times[i].display,x=chartX(i);append(svg,"text",{x,y:299,"text-anchor":"middle",class:"chart-label"},`${t.slice(5,10)} ${t.slice(11,16)}`);}
    for(const b of result.bodies){append(svg,"polyline",{points:b.track.map((p,i)=>`${chartX(i)},${chartY(p.altitude_deg)}`).join(" "),fill:"none",stroke:colors[b.id]||"#fff","stroke-width":2,"stroke-linejoin":"round","stroke-linecap":"round"});}
    append(svg,"text",{x:1070,y:321,"text-anchor":"end",class:"chart-label"},"时间为所选固定时差；高度角不含折射");
    append(svg,"line",{id:"time-cursor",x1:60,y1:20,x2:60,y2:282,stroke:"#efeee0","stroke-width":1.2,"stroke-dasharray":"4 4"});
  }
  function drawTimeCursor(index){const line=$("time-cursor");if(line){line.setAttribute("x1",chartX(index));line.setAttribute("x2",chartX(index));}}
  $("timeline-chart").addEventListener("click",event=>{if(!result)return;const svg=$("timeline-chart"),point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;const transform=svg.getScreenCTM();if(!transform)return;const local=point.matrixTransform(transform.inverse());if(local.x<60||local.x>1070)return;let best=0;for(let i=1;i<result.times.length;i++)if(Math.abs(chartX(i)-local.x)<Math.abs(chartX(best)-local.x))best=i;$("time-index").value=best;renderAt(best);});
  function renderLegend(){const items=result.bodies.map(body=>{const span=document.createElement("span"),swatch=document.createElement("i");swatch.style.backgroundColor=colors[body.id];span.append(swatch,document.createTextNode(body.name));return span;});$("legend").replaceChildren(...items);}
  function renderTwilight(){const cards=result.twilight.map(t=>{const div=document.createElement("div");div.className="event-card";const h=document.createElement("h3");h.textContent=`${t.name||t.kind} · 太阳中心 ${t.altitude_deg}°`;div.append(h);for(const[k,label]of[["dawn","晨光"],["dusk","暮光"]]){const p=document.createElement("p");p.textContent=`${label}：`;(t[k]||[]).forEach((event,i)=>{const strong=document.createElement("strong");strong.textContent=(i?"；":"")+event.display.replace("T"," ");strong.title=event.utc;p.append(strong);});if(!t[k]?.length)p.append(document.createTextNode("区间内无事件"));div.append(p);}return div;});$("twilight-events").replaceChildren(...cards);}
  function renderConventions(){const container=$("conventions");container.replaceChildren();for(const value of [...Object.values(result.conventions||{}),...(result.warnings||[])]){const p=document.createElement("p");p.textContent=value;container.append(p);}}

  function download(filename,content,type){const blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  const csvCell=value=>`"${String(value).replaceAll('"','""')}"`;
  $("export-csv").addEventListener("click",()=>{if(!result)return;const rows=[["插件版本","引擎版本","UTC时刻","固定时差显示时刻","天体","高度角_度_无折射","方位角_度_北零向东","赤经_小时_当日","赤纬_度_当日","纬度_度","经度_度","海拔_米"]];for(const b of result.bodies)for(const p of b.track)rows.push([result.version,result.engine_version,p.utc,p.display,b.name,p.altitude_deg,p.azimuth_deg,p.ra_hours,p.dec_deg,result.request.latitude,result.request.longitude,result.request.elevation_m]);download("观星计划-实际读数.csv","\uFEFF"+rows.map(r=>r.map(csvCell).join(",")).join("\r\n"),"text/csv;charset=utf-8");notice(`已导出 ${rows.length-1} 行实际计算读数；事件与天气不在此 CSV 中。`);});
  $("export-json").addEventListener("click",()=>{try{const request=requestFromForm();download("观星计划-输入.json",JSON.stringify(request,null,2)+"\n","application/json;charset=utf-8");notice("已导出输入条件 JSON，不包含旧计算结果。");}catch(e){notice(e.message,"error");}});
  $("import-json").addEventListener("click",()=>$("import-file").click());
  $("import-file").addEventListener("change",async event=>{const file=event.target.files[0];if(!file)return;try{if(file.size>16384)throw Error("计划 JSON 不得超过 16 KiB。");const request=JSON.parse(await file.text());validateRequest(request);fillForm(request);invalidate("已导入输入条件。请重新计算，核对本次结果。");}catch(e){notice(e instanceof SyntaxError?"无法解析 JSON；当前输入未替换。":e.message,"error");}finally{event.target.value="";}});
  $("save-plan").addEventListener("click",async()=>{let request;try{request=requestFromForm();}catch(e){notice(e.message,"error");return;}const current=revision;$("save-plan").disabled=true;try{try{await api("save",{request,overwrite:false});}catch(e){if(current!==revision){notice("保存前输入已改变；已有计划未覆盖，请核对后重新保存。");return;}if(["overwrite_confirmation","output_exists","save_exists","already_exists","conflict","409"].includes(e.code)){if(!window.confirm("工作目录中已有保存的计划。是否用当前输入条件替换它？")){notice("已保留原计划，未覆盖。");return;}await api("save",{request,overwrite:true});}else throw e;}notice(current===revision?"输入条件已保存到本次专用工作目录；计算结果不保存。":"已保存点击时的输入；当前输入随后已改变，请核对后另行保存。");}catch(e){notice(e.message,"error");}finally{$("save-plan").disabled=false;}});
  $("load-plan").addEventListener("click",async()=>{const current=revision;$("load-plan").disabled=true;try{const data=await api("saved");if(current!==revision)return;if(data.request===null){notice("本次工作目录还没有保存的计划。当前输入保持不变。");return;}fillForm(data.request);invalidate("已读取保存的输入条件。请重新计算；未恢复旧结果。");}catch(e){if(current===revision)notice(e.message,"error");}finally{$("load-plan").disabled=false;}});
  drawSkyGrid();drawTimelineGrid();
})();
