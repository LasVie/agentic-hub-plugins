// Derived from the Apache-2.0 mcp-server-dev registration examples (see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded read-only demo, stdio, SDK-built UI, absolute resource path and text fallback.
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE } from '@modelcontextprotocol/ext-apps/server';
import { readFile } from 'node:fs/promises';
import { z } from 'zod';

const server = new McpServer({ name: '__PROJECT_NAME__', version: '0.1.0' });
const uri = 'ui://add/result.html';
const html = await readFile(new URL('widget.html', import.meta.url), 'utf8');
registerAppTool(server, 'add', {
  description: 'Add two finite numbers between -1000000 and 1000000; display the sum in a result widget when supported.',
  inputSchema: { a: z.number().min(-1e6).max(1e6), b: z.number().min(-1e6).max(1e6) },
  annotations: { title: 'Add numbers', readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  _meta: { ui: { resourceUri: uri } },
}, async ({ a, b }) => ({ content: [{ type: 'text', text: JSON.stringify({ sum: a + b }) }], structuredContent: { sum: a + b } }));
registerAppResource(server, 'Addition result', uri, {}, async () => ({ contents: [{ uri, mimeType: RESOURCE_MIME_TYPE, text: html }] }));
await server.connect(new StdioServerTransport());
