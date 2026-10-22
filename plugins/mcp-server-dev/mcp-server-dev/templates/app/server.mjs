// Derived from the Apache-2.0 mcp-server-dev registration examples (see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded read-only demo, stdio, SDK-built UI, absolute resource path and text fallback.
// 修改声明（2026-10-22）：将工具说明、界面名称与输入校验提示中文化，保留协议标识和计算行为。
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE } from '@modelcontextprotocol/ext-apps/server';
import { readFile } from 'node:fs/promises';
import { z } from 'zod';

const server = new McpServer({ name: '__PROJECT_NAME__', version: '0.1.0' });
const uri = 'ui://add/result.html';
const html = await readFile(new URL('widget.html', import.meta.url), 'utf8');
registerAppTool(server, 'add', {
  description: '将两个介于 -1000000 至 1000000 的有限数值相加；宿主支持时在结果组件中显示总和。',
  inputSchema: {
    a: z.number({ error: 'a 必须为数字' }).min(-1e6, 'a 不能小于 -1000000').max(1e6, 'a 不能大于 1000000'),
    b: z.number({ error: 'b 必须为数字' }).min(-1e6, 'b 不能小于 -1000000').max(1e6, 'b 不能大于 1000000'),
  },
  annotations: { title: '数值相加', readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  _meta: { ui: { resourceUri: uri } },
}, async ({ a, b }) => ({ content: [{ type: 'text', text: JSON.stringify({ sum: a + b }) }], structuredContent: { sum: a + b } }));
registerAppResource(server, '加法结果', uri, {}, async () => ({ contents: [{ uri, mimeType: RESOURCE_MIME_TYPE, text: html }] }));
await server.connect(new StdioServerTransport());
