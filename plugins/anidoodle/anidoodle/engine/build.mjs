// 本地源码构建；运行前 npm install --ignore-scripts。依赖固定为 esbuild 0.25.12。
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
const root = dirname(fileURLToPath(import.meta.url));
const { build } = await import(process.env.ANIDOODLE_ESBUILD_URL || 'esbuild');
const text = name => readFileSync(resolve(root, '../licenses/anidoodle', name), 'utf8');
const notice = '/*! anidoodle\n' + text('LICENSE') + '\n' + text('NOTICE') + '\nModifications: Gan Mingrui, Chinese interactive adapter, 2026-10-27.\n*/';
const result = await build({ entryPoints: [resolve(root, 'src/entry.ts')], bundle: true, format: 'iife', target: 'es2020', minify: true, write: false, legalComments: 'inline', metafile: true, banner: { js: notice } });
writeFileSync(resolve(root, 'art.js'), result.outputFiles[0].text);
writeFileSync(resolve(root, 'build-inputs.json'), JSON.stringify(Object.keys(result.metafile.inputs).map(p => p.replaceAll('\\', '/').split('/engine/').pop()), null, 2)+'\n');
console.log('构建完成：engine/art.js。重新运行生成工具后，修改才会进入作品页面。');
