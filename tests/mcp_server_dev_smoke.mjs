// Run against a real generated server, including a relocated unpacked MCPB.
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const [projectArg, kind, modulesArg] = process.argv.slice(2);
assert(projectArg && ['app', 'mcpb'].includes(kind) && modulesArg, 'usage: node smoke.mjs PROJECT app|mcpb NODE_MODULES');
const project = resolve(projectArg);
const modules = resolve(modulesArg);
const { Client } = await import(pathToFileURL(resolve(modules, '@modelcontextprotocol/sdk/dist/esm/client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(resolve(modules, '@modelcontextprotocol/sdk/dist/esm/client/stdio.js')));
const client = new Client({ name: 'mcp-server-dev-functional-test', version: '1.0.0' });
const transport = new StdioClientTransport({ command: process.execPath, args: [resolve(project, 'server.mjs')], cwd: '/tmp', stderr: 'pipe' });
const deadline = setTimeout(() => { console.error('Protocol test timed out'); process.exit(1); }, 20000);
try {
  await client.connect(transport);
  assert.equal(client.getServerVersion().version, '0.1.0');
  const { tools } = await client.listTools();
  assert.equal(tools.length, 1);
  assert.equal(tools[0].name, 'add');
  assert.equal(tools[0].annotations.readOnlyHint, true);
  assert.equal(tools[0].annotations.title, '数值相加');
  assert(tools[0].description.includes('有限数值'));
  const result = await client.callTool({ name: 'add', arguments: { a: 2, b: 3 } });
  assert.equal(result.isError, undefined);
  assert.deepEqual(JSON.parse(result.content[0].text), { sum: 5 });
  const bad = await client.callTool({ name: 'add', arguments: { a: 1e20, b: 0 } });
  assert.equal(bad.isError, true);
  assert(bad.content.some(item => item.type === 'text' && item.text.includes('不能大于')));
  const typeError = await client.callTool({ name: 'add', arguments: { a: 'injected', b: 0 } });
  assert.equal(typeError.isError, true);
  assert(typeError.content.some(item => item.type === 'text' && item.text.includes('必须为数字')));
  let unknownFailed = false;
  try {
    const unknown = await client.callTool({ name: 'unknown_tool', arguments: {} });
    unknownFailed = unknown.isError === true;
  } catch { unknownFailed = true; }
  assert(unknownFailed);
  const recovery = await client.callTool({ name: 'add', arguments: { a: -2, b: 7 } });
  assert.deepEqual(JSON.parse(recovery.content[0].text), { sum: 5 });
  if (kind === 'app') {
    assert.equal(tools[0]._meta.ui.resourceUri, 'ui://add/result.html');
    const { resources } = await client.listResources();
    assert.equal(resources[0].uri, 'ui://add/result.html');
    const { contents } = await client.readResource({ uri: resources[0].uri });
    assert.equal(contents[0].mimeType, 'text/html;profile=mcp-app');
    assert(contents[0].text.includes('aria-live="polite"'));
    assert(contents[0].text.includes('lang="zh-CN"'));
    assert(contents[0].text.includes('计算结果'));
    assert(contents[0].text.includes('等待工具返回结果'));
    assert(contents[0].text.includes('无法读取结果，请查看工具的文本回复'));
    assert(contents[0].text.includes('textContent'));
    assert(!contents[0].text.includes('from "https://'));
  }
  console.log(JSON.stringify({ kind, project, initialize: 'passed', tools_list: 'passed', add_2_3: 5,
    invalid_inputs: 'rejected', unknown_tool: 'rejected', recovery: 'passed',
    resource: kind === 'app' ? 'UI URI/MIME/local HTML verified' : 'not applicable' }));
} finally {
  clearTimeout(deadline);
  await client.close();
  await transport.close();
}
