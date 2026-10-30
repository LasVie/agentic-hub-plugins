/* 固定 stdin/stdout JSON 桥；只装载随包分发的本地引擎。 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const core = require('./core.js');
globalThis.fetch = () => { throw new Error('网络请求已禁用'); };
async function main() {
  let chunks = [], size = 0;
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > 10000) throw new Error('输入过大');
    chunks.push(chunk);
  }
  const request = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  const vendor = path.resolve(__dirname, '../vendor/rdkit');
  const init = require(path.join(vendor, 'RDKit_minimal.js'));
  const rdkit = await init({wasmBinary: fs.readFileSync(path.join(vendor, 'RDKit_minimal.wasm')),
    print: () => {}, printErr: () => {}, locateFile: () => path.join(vendor, 'RDKit_minimal.wasm')});
  const result = JSON.stringify(core.analyze(rdkit, request));
  if (Buffer.byteLength(result) > 1500000) throw new Error('输出过大');
  process.stdout.write(result + '\n');
}
main().catch(() => { process.stdout.write(JSON.stringify(core.failure('engine_failed', '无法装载或执行随包的离线 RDKit 引擎。')) + '\n'); process.exitCode = 1; });
