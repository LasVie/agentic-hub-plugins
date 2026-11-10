// Fixed SVG and CSV serializers. User values never become markup or code.
export const fmt = n => n === null ? '—' : Number(n).toLocaleString('zh-CN',{maximumFractionDigits:5});
const escape = v => String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
export function networkSVG(r) {
  const ns=r.model.nodes, xs=ns.map(n=>n.x), ys=ns.map(n=>n.y);
  const minX=Math.min(...xs), minY=Math.min(...ys), dx=Math.max(1,Math.max(...xs)-minX),dy=Math.max(1,Math.max(...ys)-minY);
  const scale=Math.min(640/dx,240/dy), points=new Map(ns.map(n=>[n.id,{x:80+(n.x-minX)*scale+(640-dx*scale)/2,y:60+(n.y-minY)*scale+(240-dy*scale)/2}]));
  let body='';
  for(const p of r.pipes){const a=points.get(p.flow_lps>=0?p.from:p.to),b=points.get(p.flow_lps>=0?p.to:p.from); const L=Math.hypot(b.x-a.x,b.y-a.y)||1,ux=(b.x-a.x)/L,uy=(b.y-a.y)/L;
    body+=`<g role="button" tabindex="0" data-pipe="${escape(p.id)}" aria-label="管道 ${escape(p.id)}"><path d="M${a.x} ${a.y}L${b.x} ${b.y}" stroke="#2b8294" stroke-width="${Math.min(8,2+Math.sqrt(Math.abs(p.flow_lps)))}"/><path d="M${(a.x+b.x)/2} ${(a.y+b.y)/2}l${-ux*9-uy*5} ${-uy*9+ux*5}l${uy*10} ${-ux*10}Z" fill="#185b6c"/><text x="${(a.x+b.x)/2+7}" y="${(a.y+b.y)/2-12}" font-size="12" fill="#2b5f70">${escape(p.id)} · ${fmt(Math.abs(p.flow_lps))}</text></g>`;
  }
  for(const n of r.nodes){const p=points.get(n.id),bad=n.pressure_m!==null&&n.pressure_m<0,color=bad?'#c34b39':n.type==='reservoir'?'#305a80':'#258d8b';
    body+=`<g role="button" tabindex="0" data-node="${escape(n.id)}" aria-label="节点 ${escape(n.id)}">${n.type==='reservoir'?`<rect x="${p.x-13}" y="${p.y-13}" width="26" height="26" rx="4" fill="${color}"/>`:`<circle cx="${p.x}" cy="${p.y}" r="12" fill="${color}"/>`}<text x="${p.x}" y="${p.y+33}" text-anchor="middle" font-size="13" fill="#244b59">${escape(n.id)} · ${fmt(n.type==='reservoir'?n.head_m:n.pressure_m)} m</text></g>`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 380" font-family="sans-serif"><title>${escape(r.model.name)} — EPANET 2.3.5 · 插件 ${r.version}</title><rect width="800" height="380" fill="#f9fcfd"/>${body}<text x="20" y="365" fill="#728a93" font-size="11">箭头为实际流向；节点值为压力水头（水库为总水头）；非实际供水认证</text></svg>`;
}
export function resultsCSV(r) {
  const rows=[['插件版本',r.version,'引擎版本',r.engine_version],['模型',r.model.name],['分析完成',r.analysis_complete],['警告',r.warnings.map(w=>`${w.code}: ${w.message}`).join('；')],[],['节点ID','类型','水头_m','压力_m水头','需水_出水_Lps'],...r.nodes.map(n=>[n.id,n.type==='reservoir'?'水库':'需水节点',n.head_m,n.pressure_m??'',n.demand_lps]),[],['管道ID','from','to','流量_Lps','流速_mps','两端水头差_m'],...r.pipes.map(p=>[p.id,p.from,p.to,p.flow_lps,p.velocity_mps,p.headloss_m])];
  return '\ufeff'+rows.map(row=>row.map(v=>{let s=String(v);if(typeof v==='string'&&/^[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}).join(',')).join('\r\n');
}
