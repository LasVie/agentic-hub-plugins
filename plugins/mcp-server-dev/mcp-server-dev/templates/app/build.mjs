// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
// 修改声明（2026-10-22）：生成带有简体中文语言声明、标题、结果标签和等待提示的 HTML。
import { build } from 'esbuild';
import './collect-licenses.mjs';
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const result = await build({ entryPoints: [fileURLToPath(new URL('widget.mjs', import.meta.url))],
  bundle: true, write: false, format: 'esm', platform: 'browser', charset: 'utf8', legalComments: 'inline' });
const js = result.outputFiles[0].text.replace(/<\/script/gi, '<\\/script');
const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="color-scheme" content="light dark"><title>数值相加</title>
<style>body{font:16px system-ui;color:var(--color-text-primary,CanvasText);background:transparent;margin:16px}output{font-size:32px}</style></head>
<body><p>计算结果</p><output id="sum" aria-live="polite">等待工具返回结果</output><script type="module">${js}</script></body></html>`;
await writeFile(new URL('widget.html', import.meta.url), html);
console.log('已生成 widget.html，并内联本地 SDK 构建产物');
