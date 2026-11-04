/**
 * Web3D 1.0.5 source-level geometry subset build, 2026-11-04.
 * Upstream glTF Transform 4.5.1 remains MIT licensed; original terms are in licenses/.
 * This derivative exposes only the already-supported dedup/weld/prune transforms.
 * It removes unused ndarray/lanczos imports, rather than disguising code generation.
 * Build dependencies are external and pinned by ../build-evidence/npm-build.lock.json.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const outer=path.resolve(fileURLToPath(new URL('..',import.meta.url)));
const deps=path.resolve(process.env.WEB3D_BUILD_DEPS||'');
if(!process.env.WEB3D_BUILD_DEPS)throw Error('Set WEB3D_BUILD_DEPS to the isolated pinned build directory');
const {build}=await import(path.join(deps,'node_modules/esbuild/lib/main.js'));
const ts=(await import(path.join(deps,'node_modules/typescript/lib/typescript.js'))).default;
const upstream=path.join(deps,'node_modules/@gltf-transform/functions/dist/index.js');
const original=fs.readFileSync(upstream,'utf8');
const digest=s=>crypto.createHash('sha256').update(s).digest('hex');
const source=ts.createSourceFile('functions-4.5.1.mjs',original,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);
if(source.parseDiagnostics.length)throw Error('Upstream ESM parse failed');
const removed=[];const edits=[];let narrowed=false;
for(const node of source.statements){
 if(ts.isImportDeclaration(node)&&['ndarray','ndarray-lanczos'].includes(node.moduleSpecifier.text)){
  removed.push({module:node.moduleSpecifier.text,source:node.getText(source)});
  edits.push([node.getStart(source),node.end,'']);
 }
 if(ts.isExportDeclaration(node)&&node.exportClause&&ts.isNamedExports(node.exportClause)){
  const names=node.exportClause.elements.map(x=>x.name.text);
  if(!['dedup','weld','prune'].every(x=>names.includes(x)))throw Error('Unexpected upstream transform exports');
  edits.push([node.getStart(source),node.end,'export {dedup, weld, prune};']);narrowed=true;
 }
}
if(removed.length!==2||!narrowed)throw Error('Expected exactly the two unused image-array imports and transform exports');
let derivative=original;
for(const [start,end,replacement]of edits.sort((a,b)=>b[0]-a[0]))derivative=derivative.slice(0,start)+replacement+derivative.slice(end);
derivative='/* Modified 2026-11-04: geometry-only exports; unused ndarray/lanczos imports removed. Original MIT terms retained. */\n'+derivative;
// Non-exported palette/texture-compression bodies in this intermediate source are
// discarded by the compiler. No public transform in this subset calls ndarray.
// The emitted-code audit below rejects any surviving reference, not just calls.
const noNativePixels={name:'existing-bounded-image-io',setup(b){
 b.onResolve({filter:/^ndarray-pixels$/},()=>({path:'bounded-pixels',namespace:'web3d-bounded'}));
 b.onLoad({filter:/.*/,namespace:'web3d-bounded'},()=>({contents:"export async function getPixels(){throw Error('Native image codecs are outside this bounded geometry build');} export async function savePixels(){throw Error('Native image codecs are outside this bounded geometry build');}",loader:'js'}));
 b.onLoad({filter:/[\\/]@gltf-transform[\\/]functions[\\/]dist[\\/]index\.js$/},()=>({contents:derivative,loader:'js',resolveDir:path.dirname(upstream)}));
}};
const root=path.join(outer,'web3d-asset-lab');
const entry=fs.readFileSync(path.join(outer,'build/gltf-engine.mjs'),'utf8');
const banner="/* Modified geometry subset 2026-11-04: unused ndarray code generation is not included. glTF Transform and retained dependencies keep their original MIT terms. */\nimport {createRequire as __dfRequire} from 'node:module'; import {fileURLToPath as __dfURL} from 'node:url'; const require=__dfRequire(import.meta.url); const __dirname=__dfURL(new URL('.',import.meta.url));";
const result=await build({absWorkingDir:deps,stdin:{contents:entry,sourcefile:'web3d-geometry-entry.mjs',resolveDir:deps},outfile:path.join(root,'vendor/engine.mjs'),bundle:true,format:'esm',platform:'node',target:'node22',metafile:true,minify:false,treeShaking:true,legalComments:'eof',nodePaths:[path.join(deps,'node_modules')],plugins:[noNativePixels],banner:{js:banner},define:{'import.meta.dirname':'__dirname'}});
const emitted=fs.readFileSync(path.join(root,'vendor/engine.mjs'),'utf8');
const ast=ts.createSourceFile('engine.mjs',emitted,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);
const violations=[];
function visit(node){
 if(ts.isIdentifier(node)&&/ndarray|lanczos|compileConstructor|CACHED_CONSTRUCTORS/.test(node.text))violations.push({kind:'removed-array-capability',name:node.text});
 if((ts.isCallExpression(node)||ts.isNewExpression(node))){
  const name=node.expression.getText(ast);
  if(/^(?:(?:globalThis|global|window|self)\.)?(?:eval|Function|AsyncFunction|GeneratorFunction)$/.test(name))violations.push({kind:'string-compilation',name});
  if(/^(?:setTimeout|setInterval)$/.test(name)&&node.arguments?.[0]&&ts.isStringLiteralLike(node.arguments[0]))violations.push({kind:'string-timer',name});
 }
 ts.forEachChild(node,visit);
}
visit(ast);
if(ast.parseDiagnostics.length||violations.length)throw Error('Emitted-code audit failed: '+JSON.stringify(violations));
if(Object.keys(result.metafile.inputs).some(x=>/[\\/]ndarray(?:[\\/-]|$)|[\\/]iota-array[\\/]|[\\/]is-buffer[\\/]/.test(x)))throw Error('Removed array dependency remains in build graph');
const evidence=path.join(outer,'build-evidence');
fs.writeFileSync(path.join(evidence,'engine.mjs.inputs.json'),JSON.stringify(result.metafile.inputs,null,2)+'\n');
fs.writeFileSync(path.join(evidence,'geometry-subset-build.json'),JSON.stringify({date:'2026-11-04',upstream:'@gltf-transform/functions@4.5.1',upstream_commit:'41156dfa2324ac6c44ddf0a40ec0da194c4731d6',upstream_dist_sha256:digest(original),derived_dist_sha256:digest(derivative),removed_imports:removed,exports:['dedup','weld','prune'],native_image_io:'Existing explicit unsupported-codec error retained; prune catches it and skips decoded texture analysis',emitted_sha256:digest(emitted),emitted_bytes:Buffer.byteLength(emitted),ast_string_compilation_violations:violations,removed_array_modules_absent:true,inputs:Object.keys(result.metafile.inputs),not_changed:['vendor/model-view.mjs','vendor/texture-resize.mjs','runtime/handler.cjs','web/app.js']},null,2)+'\n');
console.log(JSON.stringify({emitted_sha256:digest(emitted),bytes:Buffer.byteLength(emitted),inputs:Object.keys(result.metafile.inputs),violations}));
