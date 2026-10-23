// Build-time only: Node >=24; no packages/network. Browser has no Node dependency.
import {stripTypeScriptTypes} from 'node:module';
import {readFileSync, writeFileSync} from 'node:fs';
const source = new URL('./invaders-local/vendor/engine-source.ts', import.meta.url);
const output = new URL('./invaders-local/assets/engine.mjs', import.meta.url);
writeFileSync(output, stripTypeScriptTypes(readFileSync(source, 'utf8'), {mode: 'strip'}));
