import readline from 'node:readline';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { analyze, demo, plan } from './engine.mjs';
import { load, list, publicReport, cacheRoot } from './store.mjs';
import { panelURL, closePanel } from './panel.mjs';
import { exportFiles } from './export.mjs';

const text = description => ({ type: 'string', description });
const id = text('实际工具返回的报告标识。');
const revision = { type: 'integer', minimum: 0, description: '实际查询返回的报告修订号，不能猜测。' };
const definitions = [
  ['verification_demo', '创建包含两个真实本地 Git 提交的虚构演示仓库，不执行演示代码，不修改用户项目。', {}, []],
  ['verification_analyze', '只读比较明确授权的本地 Git 仓库两个提交，生成中文静态影响候选和未验证的人工回归清单。', {
    root: text('用户明确授权的 Git 仓库顶层绝对路径；或 verification_demo 刚返回的独立演示路径。'),
    base: text('本地已有基线引用。'), head: text('本地已有目标引用。'),
    depth: { type: 'integer', minimum: 0, maximum: 3, description: '静态反向依赖扩散深度，默认 2。' },
    modules: { type: 'array', maxItems: 30, description: '可选用户模块命名；不读取配置或执行项目。', items: {
      type: 'object', additionalProperties: false, required: ['prefix', 'name'], properties: { prefix: text('相对路径或目录前缀，不带结尾斜线。'), name: text('准确中文模块名称。') } } },
  }, ['root', 'base', 'head']],
  ['verification_status', '读取磁盘上的真实报告、结果、截图摘要和修订号；不更改结果。无标识时列最近 50 份。', { report_id: id }, []],
  ['verification_open', '打开已有报告的中文本地回归面板，供用户人工填写状态、备注和截图。不代替用户验证。', { report_id: id }, ['report_id']],
  ['verification_plan', '仅为尚未录入结果的真实清单项补充中文建议步骤，不能修改状态、文件或影响证据。', {
    report_id: id, revision, item_id: text('报告中真实清单项标识。'),
    steps: { type: 'array', minItems: 1, maxItems: 8, items: text('简短可验证步骤，不声称已经执行。') },
  }, ['report_id', 'revision', 'item_id', 'steps']],
  ['verification_export', '将已有报告快照导出为中文 Markdown、CSV、JSON 和内嵌截图的独立 HTML，仅保存插件私有缓存。', { report_id: id }, ['report_id']],
].map(([name, description, properties, required]) => ({ name, description, inputSchema: { type: 'object', additionalProperties: false, properties, required } }));
function validate(value, schema) {
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('工具参数必须是对象。');
    for (const key of schema.required || []) if (!(key in value)) throw new Error(`缺少参数：${key}`);
    for (const [key, item] of Object.entries(value)) {
      if (!schema.properties[key]) throw new Error(`不支持的参数：${key}`);
      validate(item, schema.properties[key]);
    }
  } else if (schema.type === 'array') {
    if (!Array.isArray(value) || value.length < (schema.minItems || 0) || value.length > schema.maxItems) throw new Error('列表参数数量无效。');
    for (const item of value) validate(item, schema.items);
  } else if (schema.type === 'integer') {
    if (!Number.isInteger(value) || value < schema.minimum || value > (schema.maximum ?? Number.MAX_SAFE_INTEGER)) throw new Error('整数参数超出允许范围。');
  } else if (typeof value !== schema.type || (typeof value === 'string' && value.length > 1500)) throw new Error('工具参数类型或长度无效。');
}
async function invoke(name, args) {
  const definition = definitions.find(tool => tool.name === name);
  if (!definition) throw new Error('没有该工具。');
  validate(args, definition.inputSchema);
  if (name === 'verification_demo') return { ok: true, version: '1.0.0', ...await demo() };
  if (name === 'verification_analyze') {
    const report = await analyze(args);
    return { ok: true, report: publicReport(report), panel_url: await panelURL(report.id), message: '已生成未验证清单。请打开面板让用户自行填写，不能自动标记通过。' };
  }
  if (name === 'verification_status') return { ok: true, version: '1.0.0', state_directory: cacheRoot,
    ...(args.report_id ? { report: publicReport(await load(args.report_id)) } : await list()) };
  const report = await load(args.report_id);
  if (name === 'verification_export') return { ok: true, report_id: report.id, version: report.version, ...await exportFiles(report) };
  if (name === 'verification_plan') return { ok: true, report: publicReport(await plan(args)) };
  const url = await panelURL(report.id);
  let opened = false;
  try {
    if (process.platform === 'darwin') await promisify(execFile)('/usr/bin/open', [url], { timeout: 10000 });
    else if (process.platform === 'linux') await promisify(execFile)('xdg-open', [url], { timeout: 10000 });
    else throw new Error('当前系统未验证自动打开。');
    opened = true;
  } catch {}
  return { ok: true, version: '1.0.0', report_id: report.id, panel_url: url, browser_open_requested: opened,
    message: opened ? '已请求系统打开面板；请由用户确认页面可见。此结果不证明回归测试通过。' : '未能自动打开浏览器，请点击本地面板链接。MCP 已连接，无需安装依赖。' };
}
const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
let queue = Promise.resolve();
let initialized = false;
const send = value => process.stdout.write(JSON.stringify(value) + '\n');
async function dispatch(line) {
  let request;
  try {
    if (Buffer.byteLength(line) > 100000) throw new Error('请求超限。');
    request = JSON.parse(line);
    if (request.jsonrpc !== '2.0' || typeof request.method !== 'string') throw new Error('协议格式无效。');
  } catch {
    return send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: '无法解析请求或请求超限。' } });
  }
  if (!('id' in request)) return;
  const respond = result => send({ jsonrpc: '2.0', id: request.id, result });
  if (request.method === 'initialize') {
    initialized = true;
    return respond({ protocolVersion: ['2025-06-18', '2025-03-26', '2024-11-05'].includes(request.params?.protocolVersion) ? request.params.protocolVersion : '2024-11-05',
      capabilities: { tools: {} }, serverInfo: { name: 'change-verification', version: '1.0.0' },
      instructions: '请用中文。只分析明确授权仓库，静态候选不等于功能通过。人工结果由用户在面板录入。' });
  }
  if (request.method === 'ping') return respond({});
  if (!initialized) return send({ jsonrpc: '2.0', id: request.id, error: { code: -32002, message: '请先初始化连接。' } });
  if (request.method === 'tools/list') return respond({ tools: definitions });
  if (request.method === 'tools/call') {
    try {
      const value = await invoke(request.params?.name, request.params?.arguments ?? {});
      return respond({ content: [{ type: 'text', text: JSON.stringify(value) }] });
    } catch (error) {
      const message = error.code ? '本地文件或运行环境操作失败，请检查路径与权限；未尝试安装依赖或绕过检查。' : error.message || '本地操作失败。';
      return respond({ isError: true, content: [{ type: 'text', text: JSON.stringify({ ok: false, message }) }] });
    }
  }
  return send({ jsonrpc: '2.0', id: request.id, error: { code: -32601, message: '未实现该协议方法。' } });
}
input.on('line', line => { queue = queue.then(() => dispatch(line)).catch(error => process.stderr.write('请求处理失败。\n')); });
input.on('close', () => { void queue.then(closePanel); });
process.on('SIGTERM', () => { void closePanel().finally(() => process.exit(0)); });
