// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
import { App, applyHostStyleVariables } from '@modelcontextprotocol/ext-apps';
const app = new App({ name: '__PROJECT_NAME__', version: '0.1.0' });
app.ontoolresult = (result) => {
  const target = document.getElementById('sum');
  try {
    const data = result.structuredContent ?? JSON.parse(result.content.find(c => c.type === 'text').text);
    target.textContent = typeof data.sum === 'number' ? String(data.sum) : 'Result has no numeric sum';
  } catch {
    target.textContent = 'Result could not be read; see the tool text response';
  }
};
app.onhostcontextchanged = (ctx) => {
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
};
await app.connect();
