/** Reproduce only these three ports. Build dependency: esbuild 0.25.12 (MIT), development-only.
 * Run with `node tools/build_song_plugins.mjs /absolute/path/to/esbuild/lib/main.js`.
 * No packages are downloaded by this script; no third-party sample packs are used.
 */
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
const require=createRequire(import.meta.url);
const esbuild=require(process.argv[2]||'esbuild');
if(esbuild.version!=='0.25.12')throw Error('Expected esbuild 0.25.12');
for(const slug of ['dsh-vault','dsh-pianist','dsh-simulated-life']){
 const dir=resolve('plugins',slug,slug);
 await esbuild.build({entryPoints:[`${dir}/runtime/entry.ts`],outfile:`${dir}/runtime/engine.mjs`,bundle:true,platform:'node',format:'esm',target:'node22',legalComments:'inline',banner:{js:'// WorkSwarm port. Upstream MIT sources and notices are bundled in vendor/ and licenses/.'}});
 if(slug==='dsh-pianist')await esbuild.build({entryPoints:[`${dir}/runtime/player.ts`],outfile:`${dir}/runtime/player.js`,bundle:true,platform:'browser',format:'iife',target:'es2022',legalComments:'inline'});
}
