// Ported 2026-10-23 from dsh-process src/validate.js (MIT, weibaohui).
// JSON-object validation and explicit evidence journal replace YAML/host agents.
import { flowTarget, extractMeta } from '../vendor/process-core.mjs';
import { text, id, fail, object, now, within, hash } from './common.mjs';
import fs from 'node:fs';
function validate(template) {
  const errors = [], add = (path, message) => errors.push({ path, message });
  if (!object(template)) return { valid: false, errors: [{ path: '', message: '模板须为 JSON 对象。' }] };
  if (!object(template.process) || typeof template.process.name !== 'string' || !/^[a-z][a-z0-9-]{0,47}$/.test(template.process.name)) add('process.name', '流程名须为小写字母、数字和短横线。');
  if (!Array.isArray(template.phases) || !template.phases.length || template.phases.length > 20) add('phases', '须包含 1 至 20 个阶段。');
  const steps = [], phaseIds = new Set(), stepIds = new Set();
  for (const [pi, phase] of (Array.isArray(template.phases) ? template.phases : []).entries()) {
    if (!object(phase) || typeof phase.id !== 'string' || !/^[a-z][a-z0-9-]{0,47}$/.test(phase.id) || phaseIds.has(phase.id)) { add(`phases.${pi}.id`, '阶段编号无效或重复。'); continue; }
    phaseIds.add(phase.id);
    if (!Array.isArray(phase.links) || !phase.links.length || phase.links.length > 30) { add(`phases.${pi}.links`, '每阶段须含 1 至 30 个环节。'); continue; }
    for (const [li, link] of phase.links.entries()) {
      const loc = `phases.${pi}.links.${li}`;
      if (!object(link) || typeof link.id !== 'string' || !/^[a-z][a-z0-9-]{0,47}$/.test(link.id) || stepIds.has(link.id)) { add(loc + '.id', '环节编号无效或重复。'); continue; }
      stepIds.add(link.id); steps.push({ ...link, phase_id: phase.id, phase_name: phase.name || phase.id });
      if (typeof link.prompt !== 'string' || !link.prompt.trim() || link.prompt.length > 4000) add(loc + '.prompt', '须填写最多 4000 字的执行说明。');
      if (link.gates !== undefined && (!Array.isArray(link.gates) || link.gates.length > 10 || link.gates.some(g => !object(g) || g.type !== 'file_sha256'))) add(loc + '.gates', '此适配版仅支持 file_sha256 文件证据门禁；不执行 AI 评分。');
      for (const key of ['on_gate_fail', 'on_rating_fail']) if (link[key] && link[key] !== 'break') add(loc + '.' + key, '失败时须暂停，不自动重试或跳转。');
    }
  }
  for (const link of steps) {
    const flow = link.on_success ?? 'next'; const target = flowTarget(flow);
    if (typeof flow !== 'string' || (target && !stepIds.has(target)) || !flow.trim()) add(link.id + '.on_success', '成功流转须为 next/end/break 或存在的环节编号。');
  }
  if (steps.length > 120) add('phases', '总环节数不能超过 120。');
  return { valid: !errors.length, errors, meta: extractMeta(template), steps };
}
function view(ctx) { const { state, revision } = ctx.read(); return { revision, ...state }; }
export function execute(ctx, action, p) {
  if (!object(p)) fail('payload 须为对象。');
  if (action === 'status') return view(ctx);
  if (action === 'validate_template') return validate(p.template);
  if (action === 'export_process') return { export: view(ctx), message: '已导出模板快照与证据记录。' };
  const result = ctx.mutate(p.expected_revision, s => {
    if (action === 'save_template') {
      const check = validate(p.template); if (!check.valid) fail(check.errors.map(e => e.path + '：' + e.message).join('\n'));
      if (JSON.stringify(p.template).length > 100000) fail('模板过大。');
      s.template = p.template; return { message: '模板已校验并保存；既有运行保留原快照。' };
    }
    if (action === 'start_run') {
      if (!s.template) fail('请先保存有效模板。');
      const key = id(p.run_id, '运行编号'); if (s.runs.some(r => r.id === key)) fail('运行编号已存在，不会覆盖。');
      if (s.runs.length >= 100) fail('运行记录已达 100 条。');
      const checked = validate(s.template); if (!checked.valid) fail('模板校验未通过。');
      s.runs.push({ id: key, snapshot: structuredClone(s.template), steps: checked.steps, current: checked.steps[0].id, status: 'running', trail: [], started_at: now(), snapshot_hash: hash(JSON.stringify(s.template)) });
      return { message: '运行已开始；需明确完成当前环节，不会自动执行外部操作。' };
    }
    const r = s.runs.find(r => r.id === p.run_id); if (!r) fail('运行不存在。');
    if (action === 'resume_run') { if (r.status !== 'paused') fail('只能恢复已暂停的运行。'); r.status = 'running'; return { message: '运行已恢复。' }; }
    if (action !== 'complete_step') fail('操作不支持。');
    if (r.status !== 'running') fail('运行已结束或暂停，不能完成环节。');
    if (r.current !== p.step_id) fail('只能完成当前环节，不能跳过前置步骤。');
    if (r.trail.length >= 200) fail('已达到 200 次环节执行上限。');
    const note = text(p.note, '执行说明', 2000);
    if (!Array.isArray(p.evidence_files) || !p.evidence_files.length || p.evidence_files.length > 10) fail('须提供工作目录内 1 至 10 份实际证据文件。');
    const evidence = p.evidence_files.map(f => { const loc = within(ctx.root, f); if (fs.statSync(loc).size > 5 * 1024 * 1024) fail('单份证据文件不能超过 5 MiB。'); return { path: f, bytes: fs.statSync(loc).size, sha256: hash(fs.readFileSync(loc)) }; });
    const step = r.steps.find(x => x.id === r.current), index = r.steps.indexOf(step), route = step.on_success || 'next';
    r.trail.push({ step_id: r.current, note, evidence, completed_at: now() });
    const target = flowTarget(route);
    if (route === 'end' || (route === 'next' && !r.steps[index + 1])) { r.current = null; r.status = 'done'; }
    else if (route === 'break') { r.current = r.steps[index + 1]?.id || null; r.status = r.current ? 'paused' : 'done'; }
    else r.current = target || r.steps[index + 1].id;
    return { message: r.status === 'done' ? '所有已走到的环节完成，文件证据已记录。' : '当前环节已记录，流转到下一环节。', run_status: r.status };
  });
  return { ...result, ...view(ctx) };
}
export { validate };
