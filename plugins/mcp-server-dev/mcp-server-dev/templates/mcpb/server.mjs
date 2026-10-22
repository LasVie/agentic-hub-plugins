// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
// 修改声明（2026-10-22）：将工具说明与输入校验提示中文化，保留协议标识和计算行为。
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({ name: '__PROJECT_NAME__', version: '0.1.0' });
server.registerTool('add', {
  description: '将两个介于 -1000000 至 1000000 的有限数值相加，返回总和。',
  inputSchema: {
    a: z.number({ error: 'a 必须为数字' }).min(-1e6, 'a 不能小于 -1000000').max(1e6, 'a 不能大于 1000000'),
    b: z.number({ error: 'b 必须为数字' }).min(-1e6, 'b 不能小于 -1000000').max(1e6, 'b 不能大于 1000000'),
  },
  annotations: { title: '数值相加', readOnlyHint: true, destructiveHint: false, openWorldHint: false },
}, async ({ a, b }) => ({ content: [{ type: 'text', text: JSON.stringify({ sum: a + b }) }] }));
await server.connect(new StdioServerTransport());
