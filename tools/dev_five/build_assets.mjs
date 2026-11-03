import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const repo=path.resolve(fileURLToPath(new URL('../..',import.meta.url))),build=path.join(repo,'.research/dev-five/build'),source=path.join(repo,'tools/dev_five');
const {build:bundle}=await import(path.join(build,'node_modules/esbuild/lib/main.js'));
const defs=JSON.parse(fs.readFileSync(path.join(repo,'tools/dev_five_config.json')));
const banner="import {createRequire as __dfRequire} from 'node:module'; import {fileURLToPath as __dfURL} from 'node:url'; const require=__dfRequire(import.meta.url); const __dirname=__dfURL(new URL('.',import.meta.url));";
async function make(entry,outfile,platform='node',extra={}){
 const result=await bundle({absWorkingDir:build,entryPoints:[entry],outfile,bundle:true,format:platform==='browser'?'esm':outfile.endsWith('.cjs')?'cjs':'esm',platform,target:platform==='browser'?'es2022':'node22',metafile:true,minify:false,legalComments:'eof',nodePaths:[path.join(build,'node_modules')],...(platform==='node'&&!outfile.endsWith('.cjs')?{banner:{js:banner},define:{'import.meta.dirname':'__dirname'}}:{}),...extra});
 fs.writeFileSync(outfile+'.inputs.json',JSON.stringify(result.metafile.inputs,null,2));
}
for(const d of defs.filter(d=>!process.env.DEV_FIVE_ONLY||d.slug===process.env.DEV_FIVE_ONLY)){
 const root=path.join(repo,'plugins',d.slug,d.slug);fs.mkdirSync(path.join(root,'vendor'),{recursive:true});
 if(d.slug==='api-mock-lab'){
  const entry=path.join(build,'mock-entry.mjs');fs.writeFileSync(entry,"export {MockoonServer} from '@mockoon/commons-server'; export {BuildEnvironment,BuildHTTPRoute,OpenApiConverter} from '@mockoon/commons'; export {parse as parseYaml} from 'yaml';");await make(entry,path.join(root,'vendor/engine.cjs'));
 }
 if(d.slug==='visual-web-studio'){
  const ts=(await import(path.join(build,'node_modules/typescript/lib/typescript.js'))).default;
  const legacyClasses={name:'upstream-es5-class-semantics',setup(b){b.onLoad({filter:/\.tsx?$/},async a=>({contents:ts.transpileModule(fs.readFileSync(a.path,'utf8'),{fileName:a.path,compilerOptions:{target:ts.ScriptTarget.ES5,module:ts.ModuleKind.ESNext,esModuleInterop:true,isolatedModules:true}}).outputText,loader:'js',resolveDir:path.dirname(a.path)}));}};
  const empty=path.join(build,'empty-formatter.cjs');fs.writeFileSync(empty,'/* Formatting addon intentionally excluded; visual editing/export remain supported. */');
  await make(path.join(repo,'.research/dev-five/grapesjs-source/packages/core/src/index.ts'),path.join(root,'vendor/grapes.mjs'),'browser',{plugins:[legacyClasses],alias:{'codemirror-formatting':empty},define:{__GJS_VERSION__:JSON.stringify('0.23.8')}});
  fs.copyFileSync(path.join(build,'node_modules/grapesjs/dist/css/grapes.min.css'),path.join(root,'vendor/grapes.css'));
  fs.copyFileSync(path.join(build,'node_modules/grapesjs/locale/zh.mjs'),path.join(root,'vendor/zh.mjs'));
 }
 if(d.slug==='postgres-local-lab'){
  const src=path.join(build,'node_modules/@electric-sql/pglite'),dest=path.join(root,'vendor/pglite');fs.mkdirSync(path.join(dest,'dist'),{recursive:true});
  for(const name of fs.readdirSync(path.join(src,'dist'))){if(/\.(cjs|js|wasm|data)$/.test(name))fs.copyFileSync(path.join(src,'dist',name),path.join(dest,'dist',name));}
  fs.copyFileSync(path.join(src,'LICENSE'),path.join(dest,'LICENSE'));
 }
 if(d.slug==='bundle-insight'){
  const dest=path.join(root,'vendor/visualizer/plugin/render-template/engine.mjs');fs.mkdirSync(path.dirname(dest),{recursive:true});await make(path.join(source,'bundle-engine.mjs'),dest,'node',{external:['fsevents']});
  fs.copyFileSync(path.join(build,'node_modules/@rollup/wasm-node/dist/wasm-node/bindings_wasm_bg.wasm'),path.join(path.dirname(dest),'bindings_wasm_bg.wasm'));
 }
 if(d.slug==='web3d-asset-lab'){
  const pixelStub=path.join(build,'bounded-pixels.mjs');fs.writeFileSync(pixelStub,"export async function getPixels(){throw Error('Native image codecs are outside this bounded geometry build');} export async function savePixels(){throw Error('Native image codecs are outside this bounded geometry build');}");
  await make(path.join(source,'gltf-engine.mjs'),path.join(root,'vendor/engine.mjs'),'node',{alias:{'ndarray-pixels':pixelStub}});
  await make(path.join(source,'model-view.mjs'),path.join(root,'vendor/model-view.mjs'),'browser');
  await make(path.join(source,'texture-resize.mjs'),path.join(root,'vendor/texture-resize.mjs'),'browser',{external:['node:fs','node:path']});
 }
 console.log('Built',d.slug);
}
