/*
 * Copyright 2024 The Ray Optics Simulation authors and contributors
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Modified 2026-10-30 for 离线光学实验室: selected numerical methods from
 * Ray Optics v5.4.0 are adapted to a strict, bounded, dependency-free module.
 * Class/UI/color/GRIN/arc/surface-merging branches are removed. Validation,
 * deterministic polygon handling, trace recording and limits are added.
 * Exact original files and source mapping: ../licenses/ray-optics and
 * ../THIRD_PARTY_NOTICES.md. This is not the full upstream application.
 */
import geometry from './geometry.mjs';

export const VERSION = '1.0.0';
export const LIMITS = Object.freeze({objects:32, vertices:16, emittedRays:256, segments:5000, depth:80, minPower:1e-6, elapsedMs:3000});
const EPS = 1e-7;
const TYPES = new Set(['SingleRay','Beam','Mirror','IdealLens','PlaneGlass','Glass','Detector']);
const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y});
const add=(a,b)=>({x:a.x+b.x,y:a.y+b.y});
const mul=(a,k)=>({x:a.x*k,y:a.y*k});
const cross=geometry.cross;
const dot=geometry.dot;
const len=v=>Math.hypot(v.x,v.y);
const unit=v=>mul(v,1/len(v));
const point=p=>({x:p.x,y:p.y});
function fail(code,message){const e=new Error(message);e.code=code;throw e;}
function object(v,name){if(!v||typeof v!=='object'||Array.isArray(v))fail('invalid_scene',`${name}必须是对象。`);}
function keys(v,allowed,name){for(const k of Object.keys(v))if(!allowed.includes(k))fail('unsupported_field',`${name}含不支持的字段：${k}。`);}
function number(v,lo,hi,name){if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)fail('invalid_number',`${name}必须是${lo}至${hi}之间的有限数值。`);return v;}
function integer(v,lo,hi,name){number(v,lo,hi,name);if(!Number.isInteger(v))fail('invalid_number',`${name}必须是整数。`);return v;}
function checkPoint(v,name){object(v,name);keys(v,['x','y'],name);return {x:number(v.x,-2000,2000,name+'.x'),y:number(v.y,-2000,2000,name+'.y')};}
function edges(path){return path.map((p,i)=>({p1:p,p2:path[(i+1)%path.length]}));}
function signedArea(path){return path.reduce((s,p,i)=>s+cross(p,path[(i+1)%path.length]),0)/2;}
function orientation(a,b,c){return cross(sub(b,a),sub(c,a));}
function onSegment(p,a,b){return Math.abs(orientation(a,b,p))<EPS&&dot(sub(p,a),sub(p,b))<=EPS;}
function segmentsTouch(a,b){const x=orientation(a.p1,a.p2,b.p1),y=orientation(a.p1,a.p2,b.p2),z=orientation(b.p1,b.p2,a.p1),w=orientation(b.p1,b.p2,a.p2);return (x*y<0&&z*w<0)||onSegment(b.p1,a.p1,a.p2)||onSegment(b.p2,a.p1,a.p2)||onSegment(a.p1,b.p1,b.p2)||onSegment(a.p2,b.p1,b.p2);}
function contains(path,p){let inside=false;for(const e of edges(path)){if(onSegment(p,e.p1,e.p2))return true;if((e.p1.y>p.y)!==(e.p2.y>p.y)&&p.x<(e.p2.x-e.p1.x)*(p.y-e.p1.y)/(e.p2.y-e.p1.y)+e.p1.x)inside=!inside;}return inside;}

export function validateScene(input){
  object(input,'场景');keys(input,['schema_version','title','objects'],'场景');
  if(input.schema_version!==1)fail('unsupported_schema','仅支持schema_version=1的本插件场景。');
  if(typeof input.title!=='string'||!input.title.trim()||input.title.length>100)fail('invalid_title','标题必须是1至100字符的文本。');
  if(!Array.isArray(input.objects)||input.objects.length<1||input.objects.length>LIMITS.objects)fail('invalid_objects','场景须包含1至32个对象。');
  const ids=new Set();let rays=0;
  const objects=input.objects.map((o,i)=>{
    object(o,`对象${i+1}`);if(!TYPES.has(o.type))fail('unsupported_type',`不支持的对象类型：${String(o.type)}。`);
    if(typeof o.id!=='string'||!/^\p{L}[\p{L}\p{N}_-]{0,31}$/u.test(o.id)||ids.has(o.id))fail('invalid_id','对象ID须唯一，以字母开头，最多32个字母、数字、下划线或连字符。');ids.add(o.id);
    const allowed=['id','type',...(o.type==='Glass'?['path']:['p1','p2'])];
    if(['SingleRay','Beam'].includes(o.type))allowed.push('brightness');
    if(o.type==='Beam')allowed.push('rayCount');
    if(['Glass','PlaneGlass'].includes(o.type))allowed.push('refIndex');
    if(o.type==='IdealLens')allowed.push('focalLength');
    if(o.type==='Detector')allowed.push('bins','twoSided');
    keys(o,allowed,o.id);const r={id:o.id,type:o.type};
    if(o.type==='Glass'){
      if(!Array.isArray(o.path)||o.path.length<3||o.path.length>LIMITS.vertices)fail('invalid_polygon','玻璃多边形须有3至16个顶点，首尾不重复。');
      r.path=o.path.map((p,j)=>checkPoint(p,`${o.id}.path[${j}]`));const es=edges(r.path);
      if(es.some(e=>geometry.distance(e.p1,e.p2)<1)||Math.abs(signedArea(r.path))<1)fail('invalid_polygon','玻璃边长与面积不能退化。');
      for(let j=0;j<r.path.length;j++){const previous=r.path[(j+r.path.length-1)%r.path.length],current=r.path[j],next=r.path[(j+1)%r.path.length];if(Math.abs(orientation(previous,current,next))<EPS)fail('invalid_polygon','玻璃相邻边不能共线或折返；请移除冗余顶点。');}
      for(let a=0;a<es.length;a++)for(let b=a+1;b<es.length;b++)if(b!==a+1&&!(a===0&&b===es.length-1)&&segmentsTouch(es[a],es[b]))fail('invalid_polygon','不支持自相交或自接触的玻璃多边形。');
    }else{r.p1=checkPoint(o.p1,o.id+'.p1');r.p2=checkPoint(o.p2,o.id+'.p2');if(geometry.distance(r.p1,r.p2)<1)fail('invalid_geometry','对象两点间距不能小于1个坐标单位。');}
    if(['SingleRay','Beam'].includes(o.type))r.brightness=number((o.brightness===undefined?1:o.brightness),0.001,10,o.id+'.brightness');
    if(o.type==='SingleRay')rays++;
    if(o.type==='Beam'){r.rayCount=integer((o.rayCount===undefined?9:o.rayCount),1,64,o.id+'.rayCount');rays+=r.rayCount;}
    if(['Glass','PlaneGlass'].includes(o.type))r.refIndex=number((o.refIndex===undefined?1.5:o.refIndex),1,3,o.id+'.refIndex');
    if(o.type==='IdealLens'){r.focalLength=number((o.focalLength===undefined?100:o.focalLength),-2000,2000,o.id+'.focalLength');if(Math.abs(r.focalLength)<1)fail('invalid_number','焦距绝对值须至少为1。');}
    if(o.type==='Detector'){r.bins=integer((o.bins===undefined?20:o.bins),1,100,o.id+'.bins');r.twoSided=(o.twoSided===undefined?true:o.twoSided);if(typeof r.twoSided!=='boolean')fail('invalid_boolean','twoSided须是布尔值。');}
    return r;
  });
  if(rays<1||rays>LIMITS.emittedRays)fail('ray_limit','须有光源，发射光线总数不能超过256。');
  const glass=objects.filter(o=>['Glass','PlaneGlass'].includes(o.type));
  if(glass.some(o=>o.type==='PlaneGlass')&&glass.length>1)fail('overlapping_glass','半平面玻璃不能与其他玻璃同时使用；请使用互不接触的多边形玻璃。');
  for(let a=0;a<glass.length;a++)for(let b=a+1;b<glass.length;b++){
    if(edges(glass[a].path).some(e=>edges(glass[b].path).some(f=>segmentsTouch(e,f)))||contains(glass[a].path,glass[b].path[0])||contains(glass[b].path,glass[a].path[0]))fail('overlapping_glass','不支持相交、嵌套或接触的玻璃；请留出空气间隔。');
  }
  // Starting exactly on a surface has no unique incident medium/direction.
  // Reject it instead of silently skipping the first interaction.
  for(const source of objects.filter(o=>['SingleRay','Beam'].includes(o.type))){
    const origins=source.type==='SingleRay'?[source.p1]:Array.from({length:source.rayCount},(_,i)=>add(source.p1,mul(sub(source.p2,source.p1),(i+0.5)/source.rayCount)));
    for(const optical of objects.filter(o=>!['SingleRay','Beam'].includes(o.type)))for(const edge of optical.type==='Glass'?edges(optical.path):[optical])for(const p of origins){
      const onLine=Math.abs(orientation(edge.p1,edge.p2,p))/geometry.distance(edge.p1,edge.p2)<EPS;
      if(onLine&&(optical.type==='PlaneGlass'||onSegment(p,edge.p1,edge.p2)))fail('source_on_surface','光源采样点不能位于光学边界或探测器上；请移动光源。');
    }
  }
  return {schema_version:1,title:input.title.trim(),objects};
}

// Line intersection and forward-ray/finite-segment checks follow geometry.js
// and LineObjMixin.checkRayIntersectsShape. Guards reject degeneracy explicitly.
function intersection(ray,edge,infinite=false){
  const d=sub(ray.p2,ray.p1),e=sub(edge.p2,edge.p1);
  if(Math.abs(cross(unit(d),unit(e)))<1e-12)return null;
  const p=geometry.linesIntersection(ray,edge);
  if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||dot(sub(p,ray.p1),unit(d))<=EPS)return null;
  if(!infinite&&!geometry.intersectionIsOnSegment(p,edge))return null;
  return p;
}

// Adapted directly from Mirror.onRayIncident.
function mirror(ray,obj,p){const rx=ray.p1.x-p.x,ry=ray.p1.y-p.y,mx=obj.p2.x-obj.p1.x,my=obj.p2.y-obj.p1.y;ray.p1=point(p);ray.p2={x:p.x+rx*(my*my-mx*mx)-2*ry*mx*my,y:p.y+ry*(mx*mx-my*my)-2*rx*mx*my};}

// Adapted directly from IdealLens.onRayIncident; no fixed-scene formulas.
function lens(ray,obj,p){
  const length=geometry.segmentLength(obj),ux=(-obj.p1.y+obj.p2.y)/length,uy=(obj.p1.x-obj.p2.x)/length,mid=geometry.segmentMidpoint(obj);
  const a={x:mid.x+ux*2*obj.focalLength,y:mid.y+uy*2*obj.focalLength},b={x:mid.x-ux*2*obj.focalLength,y:mid.y-uy*2*obj.focalLength};
  let near,far;if(geometry.distanceSquared(ray.p1,a)<geometry.distanceSquared(ray.p1,b)){near=geometry.parallelLineThroughPoint(obj,a);far=geometry.parallelLineThroughPoint(obj,b);}else{near=geometry.parallelLineThroughPoint(obj,b);far=geometry.parallelLineThroughPoint(obj,a);}
  if(obj.focalLength>0)ray.p2=geometry.linesIntersection(far,geometry.line(mid,geometry.linesIntersection(near,ray)));
  else ray.p2=geometry.linesIntersection(far,geometry.line(p,geometry.linesIntersection(near,geometry.line(mid,geometry.linesIntersection(far,ray)))));
  ray.p1=point(p);
}

// Vector Snell/Fresnel equations ported from BaseGlass.refract. Unlike the
// upstream display sampling heuristic, every retained branch carries its actual
// fractional power; discarded power is accumulated and disclosed.
function refract(ray,edge,p,ratio){
  const d=unit(sub(ray.p2,ray.p1)),s=sub(edge.p2,edge.p1);
  const n=unit(sub(mul(s,dot(d,s)),mul(d,dot(s,s))));
  const cos1=Math.max(0,Math.min(1,-dot(n,d))),sq=1-ratio*ratio*(1-cos1*cos1);
  const reflected=add(d,mul(n,2*cos1));
  if(sq<0){ray.p1=point(p);ray.p2=add(p,reflected);return {kind:'total_internal_reflection'};}
  const cos2=Math.sqrt(sq),rs=((ratio*cos1-cos2)/(ratio*cos1+cos2))**2,rp=((ratio*cos2-cos1)/(ratio*cos2+cos1))**2;
  const branch={...ray,p1:point(p),p2:add(p,reflected),s:ray.s*rs,p:ray.p*rp};
  ray.p1=point(p);ray.p2=add(p,add(mul(d,ratio),mul(n,ratio*cos1-cos2)));ray.s*=1-rs;ray.p*=1-rp;
  return {kind:'refraction',branch};
}

// Signed detector power/momentum/irradiance follows Detector.onRayIncident.
function detect(ray,obj,p,out){
  const d=unit(sub(ray.p2,ray.p1)),e=unit(sub(obj.p2,obj.p1)),c=cross(d,e),v=ray.s+ray.p,sign=Math.sign(c);
  out.power+=sign*v;out.normal+=sign*c*v;out.shear-=sign*dot(d,e)*v;out.hits++;
  const index=Math.min(obj.bins-1,Math.floor(geometry.distance(p,obj.p1)/out.binSize));out.binData[index]+=sign*v;
  ray.p1=point(p);ray.p2=add(p,d);
}

function terminal(ray){const d=unit(sub(ray.p2,ray.p1));return add(ray.p1,mul(d,6000));}
function goodRay(ray){const d=sub(ray.p2,ray.p1);return [ray.p1.x,ray.p1.y,ray.p2.x,ray.p2.y,ray.s,ray.p].every(Number.isFinite)&&len(d)>EPS&&ray.s>=0&&ray.p>=0;}

export function simulate(input){
  const started=Date.now(),scene=validateScene(input),queue=[],segments=[],detectors=[];
  let nextId=0,lostPower=0,truncated=false,emittedPower=0;
  const optical=scene.objects.filter(o=>!['SingleRay','Beam'].includes(o.type));
  for(const obj of scene.objects){
    if(obj.type==='Detector'){const size=geometry.segmentLength(obj)/obj.bins;detectors.push({id:obj.id,power:0,normal:0,shear:0,hits:0,binSize:size,binData:Array(obj.bins).fill(0),binPositions:Array.from({length:obj.bins},(_,i)=>i*size)});}
    if(obj.type==='SingleRay'){queue.push({p1:point(obj.p1),p2:point(obj.p2),s:obj.brightness/2,p:obj.brightness/2,id:nextId++,depth:0,source:obj.id});emittedPower+=obj.brightness;}
    if(obj.type==='Beam'){
      // Upstream evenly spaced midpoint emission; fixed explicit count and
      // total beam power replace viewport-dependent rayDensity scaling.
      const edge=sub(obj.p2,obj.p1),dir=unit({x:edge.y,y:-edge.x});
      for(let i=0;i<obj.rayCount;i++){const p=add(obj.p1,mul(edge,(i+0.5)/obj.rayCount));queue.push({p1:p,p2:add(p,dir),s:obj.brightness/(2*obj.rayCount),p:obj.brightness/(2*obj.rayCount),id:nextId++,depth:0,source:obj.id});}emittedPower+=obj.brightness;
    }
  }
  const emittedRays=queue.length;
  // Every segment is selected by nearest positive intersection across all
  // current objects, as in Simulator.processRays. Queue bounds are explicit.
  for(let q=0;q<queue.length;q++){
    const ray=queue[q];
    if(segments.length>=LIMITS.segments||Date.now()-started>LIMITS.elapsedMs){truncated=true;for(let k=q;k<queue.length;k++)lostPower+=queue[k].s+queue[k].p;break;}
    if(ray.depth>=LIMITS.depth||ray.s+ray.p<LIMITS.minPower){truncated=true;lostPower+=ray.s+ray.p;continue;}
    if(!goodRay(ray))fail('numerical_error','光线产生非有限或退化数值；未保留结果。');
    let best=null,nearestTied=false;
    for(const obj of optical){
      const es=obj.type==='Glass'?edges(obj.path):[obj];
      for(const edge of es){
        const p=intersection(ray,edge,obj.type==='PlaneGlass');if(!p)continue;
        if(obj.type==='Detector'&&!obj.twoSided&&cross(sub(ray.p2,ray.p1),sub(obj.p2,obj.p1))<=0)continue;
        const distance=geometry.distance(ray.p1,p);
        if(!best||distance<best.distance-EPS){best={obj,edge,p,distance};nearestTied=false;}
        else if(Math.abs(distance-best.distance)<EPS)nearestTied=true;
      }
    }
    if(nearestTied)fail('ambiguous_intersection','光线命中重合边界或多边形顶点，方向不唯一；请移动对象或光源。');
    if(best&&Math.max(Math.abs(best.p.x),Math.abs(best.p.y))>1000000)fail('geometry_limit','交点距离超出数值范围；请避免近乎平行的远距离边界。');
    const seg={from:point(ray.p1),to:best?point(best.p):terminal(ray),brightness:ray.s+ray.p,ray_id:ray.id,source_id:ray.source,object_id:best?.obj.id??null,type:best?.obj.type??'escape'};segments.push(seg);
    if(!best)continue;
    const {obj,edge,p}=best;
    if(['Glass','PlaneGlass'].includes(obj.type)){
      if(obj.type==='Glass'&&(geometry.distance(p,edge.p1)<EPS||geometry.distance(p,edge.p2)<EPS))fail('ambiguous_intersection','光线命中玻璃顶点，法线不唯一；请调整光源。');
      const incidentCross=cross(sub(ray.p2,ray.p1),sub(edge.p2,edge.p1));
      const exiting=obj.type==='PlaneGlass'?incidentCross>0:incidentCross*Math.sign(signedArea(obj.path))>0;
      const result=refract(ray,edge,p,exiting?obj.refIndex:1/obj.refIndex);seg.interaction=result.kind;
      if(result.branch){result.branch.id=nextId++;result.branch.depth++;if(result.branch.s+result.branch.p>=LIMITS.minPower)queue.push(result.branch);else lostPower+=result.branch.s+result.branch.p;}
    }else if(obj.type==='Mirror'){mirror(ray,obj,p);seg.interaction='reflection';}
    else if(obj.type==='IdealLens'){lens(ray,obj,p);seg.interaction='ideal_lens';}
    else detect(ray,obj,p,detectors.find(d=>d.id===obj.id));
    ray.depth++;queue.push(ray);
  }
  if(segments.some(s=>![s.from.x,s.from.y,s.to.x,s.to.y,s.brightness].every(Number.isFinite))||detectors.some(d=>![d.power,d.normal,d.shear,...d.binData].every(Number.isFinite)))fail('numerical_error','检测到非有限计算结果；未保留结果。');
  const warnings=['理想二维几何光学；坐标和光强为相对单位，不是实际功率、波动光学或工程认证。','探测器读数带方向符号；光束brightness是总相对功率，rayCount仅改变离散采样。'];
  if(truncated||lostPower>0)warnings.push(`部分低功率或达到边界的光线已截断；累计未继续传播的相对功率为${lostPower.toPrecision(6)}。`);
  return {ok:true,version:VERSION,scene,segments,detectors,stats:{emitted_rays:emittedRays,emitted_power:emittedPower,processed_segments:segments.length,truncated:truncated||lostPower>0,lost_power:lostPower},warnings};
}

export function run(request){try{object(request,'请求');keys(request,['action','scene'],'请求');const action=request.action??'simulate';if(action==='validate')return {ok:true,version:VERSION,scene:validateScene(request.scene)};if(action!=='simulate')fail('invalid_action','仅支持simulate或validate操作。');return simulate(request.scene);}catch(e){return {ok:false,version:VERSION,error:{code:e.code||'calculation_error',message:e.code?e.message:'计算失败；未生成替代结果。'}};}}
