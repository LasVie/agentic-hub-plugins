// Adapted from Anthropic mcp-server-dev d4226d0 (Apache-2.0; see THIRD_PARTY_NOTICES.md).
// Modified 2026-10-22: bounded demo, tested SDK pins, safe text rendering and local build.
// 修改声明（2026-10-22）：将无数值结果与解析失败时的界面回退提示中文化。
import { App, applyHostStyleVariables } from '@modelcontextprotocol/ext-apps';
const app = new App({ name: '__PROJECT_NAME__', version: '0.1.0' });
app.ontoolresult = (result) => {
  const target = document.getElementById('sum');
  try {
    const data = result.structuredContent ?? JSON.parse(result.content.find(c => c.type === 'text').text);
    target.textContent = typeof data.sum === 'number' ? String(data.sum) : '结果中没有数值总和';
  } catch {
    target.textContent = '无法读取结果，请查看工具的文本回复';
  }
};
app.onhostcontextchanged = (ctx) => {
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
};
await app.connect();
