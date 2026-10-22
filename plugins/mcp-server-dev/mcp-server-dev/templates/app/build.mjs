// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
import { build } from 'esbuild';
import './collect-licenses.mjs';
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const result = await build({ entryPoints: [fileURLToPath(new URL('widget.mjs', import.meta.url))],
  bundle: true, write: false, format: 'esm', platform: 'browser', legalComments: 'inline' });
const js = result.outputFiles[0].text.replace(/<\/script/gi, '<\\/script');
const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="color-scheme" content="light dark"><title>Add numbers</title>
<style>body{font:16px system-ui;color:var(--color-text-primary,CanvasText);background:transparent;margin:16px}output{font-size:32px}</style></head>
<body><p>Result</p><output id="sum" aria-live="polite">Waiting for a tool result</output><script type="module">${js}</script></body></html>`;
await writeFile(new URL('widget.html', import.meta.url), html);
console.log('Built widget.html with local SDK bundle');
