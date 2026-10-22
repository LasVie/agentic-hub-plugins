// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({ name: '__PROJECT_NAME__', version: '0.1.0' });
server.registerTool('add', {
  description: 'Add two finite numbers between -1000000 and 1000000. Returns the sum.',
  inputSchema: { a: z.number().min(-1e6).max(1e6), b: z.number().min(-1e6).max(1e6) },
  annotations: { title: 'Add numbers', readOnlyHint: true, destructiveHint: false, openWorldHint: false },
}, async ({ a, b }) => ({ content: [{ type: 'text', text: JSON.stringify({ sum: a + b }) }] }));
await server.connect(new StdioServerTransport());
