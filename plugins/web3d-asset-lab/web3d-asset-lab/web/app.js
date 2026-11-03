import{$,api,action,display,download,init,message,metric,fileBytes,to64,from64,prettyBytes}from'./common.js';
import{showModel}from'../vendor/model-view.mjs';
import{resizeColorTextures}from'../vendor/texture-resize.mjs';
let destroyBefore,destroyAfter;
async function show(r){if(r.original){destroyBefore?.();destroyBefore=await showModel($('#before-view'),from64(r.original));}if(r.optimized){destroyAfter?.();destroyAfter=await showModel($('#after-view'),from64(r.optimized));}$('#metrics').replaceChildren(metric('原始文件',prettyBytes(r.before.bytes)),metric('优化文件',r.after?prettyBytes(r.after.bytes):'尚未优化'),metric('网格资源',r.after?r.before.meshes+' → '+r.after.meshes:r.before.meshes),metric('节省字节',r.after?String(r.before.bytes-r.after.bytes):'—'));display($('#report'),r.after?{优化前:r.before,优化后:r.after,说明:r.note}:r.before);}
$('#demo').onclick=()=>action(async()=>{await show(await api('demo'));message('16个展品组成的真实GLB演示模型已载入；这是插件自建测试素材');});
$('#import').onclick=()=>action(async()=>{await show(await api('import',{data:to64(await fileBytes($('#model-file')))}));message('本地GLB已解析，未加载任何外部资源');});
$('#optimize').onclick=()=>action(async()=>{const r=await api('optimize');await show(r);message('真实引擎处理完成；请旋转两侧模型检查效果，再导出成品');});
$('#resize-textures').onclick=()=>action(async()=>{const current=await api('load');if(!current.original)throw Error('请先导入模型');const r=await resizeColorTextures(from64(current.optimized||current.original),128);if(!r.resized)return message('没有需要缩放的彩色贴图；数据贴图和已足够小的图像保持原样');const result=await api('save-textures',{data:to64(r.bytes)});await show(result);message('已将'+r.resized+'张彩色贴图缩小至最长边128像素；这是主动选择的有损分辨率调整');});
$('#load').onclick=()=>action(async()=>{const r=await api('load');if(!r.original)throw Error('当前工作目录尚无模型');await show(r);message('已从专用工作目录恢复实际文件和报告');});
$('#export').onclick=()=>download('optimized.glb');$('#export-report').onclick=()=>download('model-report.json');
await action(async()=>{const s=await init();if(s.before)await show(await api('load'));});
