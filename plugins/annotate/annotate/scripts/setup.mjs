import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const majorVersion = Number(process.versions.node.split('.')[0]);
if (majorVersion < 20) throw new Error('需要 Node.js >=20。');
const payload = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const runtime = path.join(payload, 'runtime');
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const result = spawnSync(npm, ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], {
  cwd: runtime,
  env: { ...process.env, PATH: `${path.dirname(process.execPath)}${path.delimiter}${process.env.PATH || ''}` },
  stdio: ['ignore', 'inherit', 'inherit'],
  timeout: 140000,
  killSignal: 'SIGKILL'
});
if (result.error || result.status !== 0) throw new Error(`依赖安装失败： ${result.error?.message || result.status}`);
const cache = process.env.ANNOTATE_DATA_DIR || path.join(os.homedir(), '.cache', 'agentic-hub-annotate');
fs.mkdirSync(cache, { recursive: true });
fs.writeFileSync(path.join(cache, 'runtime.json'), JSON.stringify({ node: process.execPath }, null, 2) + '\n', { mode: 0o600 });
console.log(`批注插件依赖已安装到 ${runtime}`);
console.log(`已记录 Node 运行路径： ${process.execPath}`);
console.log('批注插件运行环境已就绪，启动器将自动继续。');
