// dsh-env-inspector MIT subset adaptation, 2026-10-23, original author webkubor.
// Uses its pure lsof parser; excludes key/config/host identity reads and termination.
import os from 'node:os';
import fs from 'node:fs';
import { parseListeningPorts } from '../vendor/ports.mjs';
import { run, object, fail, now } from './common.mjs';
const commands = [
  ['Node.js', process.execPath, ['--version']],
  ['Python', '/usr/bin/python3', ['--version']],
  ['Git', '/usr/bin/git', ['--version']],
  ['编译器', '/usr/bin/cc', ['--version']],
];
function probe(root) {
  const tools = commands.map(([name, cmd, args]) => {
    if (!fs.existsSync(cmd)) return { name, status: 'missing', version: null, note: '系统标准位置未找到；不代表其他路径未安装。' };
    const r = run(cmd, args, root, 2500), line = r.stdout.trim().split('\n')[0] || '';
    return { name, status: r.ok && line ? 'available' : 'unavailable', version: r.ok && line ? line.slice(0, 180) : null, note: r.ok ? '' : r.reason };
  });
  const lsof = ['/usr/sbin/lsof', '/usr/bin/lsof'].find(x => fs.existsSync(x));
  const ports = lsof ? run(lsof, ['-iTCP', '-sTCP:LISTEN', '-n', '-P'], root, 5000) : { ok: false, reason: '系统没有 lsof。' };
  return {
    observed_at: now(), platform: os.platform(), architecture: os.arch(), release: os.release(), cpu_count: os.cpus().length,
    memory_total_gib: Math.round(os.totalmem() / 1024 ** 3 * 100) / 100,
    tools,
    ports: ports.ok ? parseListeningPorts(ports.stdout).slice(0, 200).map(({ port, command, pid, host, isWildcard, category }) => ({ port, command, pid, bind: isWildcard ? 'all-interfaces' : host.includes('127.0.0.1') || host === '[::1]' ? 'loopback' : 'other-interface', category })) : [],
    port_status: ports.ok ? 'observed' : 'unavailable',
    port_note: ports.ok ? 'lsof 权限范围内的 TCP 监听事实；每端口保留一条代表记录，不是完整进程清单。扫描瞬间以后可能变化。' : `监听端口未能观测：${ports.reason}；不能据此断言没有监听端口。`,
    limits: '只读本机事实，未评估系统安全性；未读取密钥、配置文件、用户名、设备名称或网卡地址；不结束任何进程。仅验证当前 macOS；其他平台须另测。',
  };
}
function compare(a, b) {
  const toolChanges = b.tools.filter(t => { const before = a.tools.find(x => x.name === t.name); return !before || before.status !== t.status || before.version !== t.version; }).map(t => ({ name: t.name, before: a.tools.find(x => x.name === t.name) || null, after: t }));
  if (a.port_status !== 'observed' || b.port_status !== 'observed') return { tools: toolChanges, ports_available: false, note: '至少一份快照未能观测端口，不能判断端口增减。' };
  const key = p => `${p.port}:${p.pid}:${p.bind}`;
  return { tools: toolChanges, ports_available: true, opened: b.ports.filter(p => !a.ports.some(x => key(x) === key(p))), closed: a.ports.filter(p => !b.ports.some(x => key(x) === key(p))), note: '仅比较两次瞬时观测，不是持续监控。' };
}
export function execute(ctx, action, p) {
  if (!object(p)) fail('payload 须为对象。');
  if (action === 'status') { const { state, revision } = ctx.read(); return { revision, snapshots: state.snapshots }; }
  if (action === 'probe') {
    if (os.platform() !== 'darwin' && os.platform() !== 'linux') fail('当前适配版仅支持 macOS/Linux 只读探测；此平台未实现。');
    const observation = probe(ctx.root);
    ctx.mutate(p.expected_revision, s => { if (s.snapshots.length >= 100) fail('快照已达 100 份，请导出后另建工作目录。'); observation.id = 'snap-' + (s.snapshots.length + 1); s.snapshots.push(observation); return {}; });
    const { state, revision } = ctx.read(); return { message: '已完成本次只读观测；不可用项保持明确标记。', revision, snapshot: observation, snapshots: state.snapshots };
  }
  if (action === 'compare') {
    const { state, revision } = ctx.read(), a = state.snapshots.find(x => x.id === p.before_id), b = state.snapshots.find(x => x.id === p.after_id);
    if (!a || !b || a.id === b.id) fail('请选择两份不同且存在的快照。');
    return { revision, before_id: a.id, after_id: b.id, comparison: compare(a, b) };
  }
  if (action === 'export_snapshots') return { message: '导出仅包含已观测事实。', export: ctx.read() };
  fail('操作不支持；此插件没有释放端口或结束进程的功能。');
}
