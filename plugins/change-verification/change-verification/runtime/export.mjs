import fs from 'node:fs/promises';
import path from 'node:path';
import { counts, cacheRoot, directory, publicReport, digest } from './store.mjs';

export const labels = { pending: '未验证', pass: '通过（用户录入）', fail: '失败（用户录入）', skip: '跳过（用户录入）',
  direct: '直接变更', ripple: '间接候选', high: '高', medium: '中', low: '低' };
export const htmlEscape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const md = value => String(value).replace(/[\\`*_{}\[\]<>()#+.!|~]/g, '\\$&');
function overview(report) {
  const c = counts(report);
  return `未验证 ${c.pending}，通过 ${c.pass}，失败 ${c.fail}，跳过 ${c.skip}。`;
}
export function markdown(report) {
  const lines = ['# 变更影响与回归检查报告', '', `插件版本：${report.version}；报告：${report.id}；修订：${report.revision}`, '',
    report.demo ? '**演示材料，不是真实项目验收。**' : '**本地仓库静态分析与人工结果记录。**', '', md(report.boundary), '',
    `仓库：${md(report.root)}`, `基线：${report.base}`, `目标：${report.head}`, `生成时间：${report.created_at}`, '',
    report.comparison, overview(report), '', '## 分析范围', '',
    `基线索引 ${report.scan.base.indexed_count}/${report.scan.base.tree_count}，目标索引 ${report.scan.head.indexed_count}/${report.scan.head.tree_count}；扩散深度 ${report.depth}。`,
    `扫描统计：${md(JSON.stringify(report.scan))}`, '', ...report.warnings.map(value => '- ' + md(value)), '', '## 回归清单', ''];
  if (!report.items.length) lines.push('没有可展示的清单项；不表示所有功能通过。', '');
  for (const [i, item] of report.items.entries()) {
    lines.push(`### ${i + 1}．${md(item.display_name)}`, '', `文件：${md(item.path)}`, `类型：${labels[item.kind]}；风险：${labels[item.risk]}；状态：${labels[item.status]}`,
      `证据：${md(item.evidence)}`, '', ...item.suggested_steps.map((step, n) => `${n + 1}. ${md(step)}`), '',
      `实际观察：${md(item.note || '未填写')}`, `结果来源：${md(item.result_source || '尚未录入')}`, `记录时间：${item.result_at || '尚未录入'}`, '');
    for (const shot of item.screenshots) lines.push(`- 截图：${md(shot.name)}；${shot.bytes} 字节；SHA-256：${shot.sha256}（图片见同目录完整 HTML 或 JSON 报告）。`);
    lines.push('');
  }
  return lines.join('\n');
}
export function html(report) {
  const e = htmlEscape;
  const cards = report.items.map(item => `<section><h2>${e(item.display_name)}</h2><p>${e(item.path)}</p><p>${labels[item.kind]} · 风险${labels[item.risk]} · ${labels[item.status]}</p><p>${e(item.evidence)}</p><ol>${item.suggested_steps.map(step => `<li>${e(step)}</li>`).join('')}</ol><h3>实际观察</h3><p class="note">${e(item.note || '未填写')}</p><p>${e(item.result_source || '尚未录入')} · ${e(item.result_at || '')}</p>${item.screenshots.map(shot => `<figure><img alt="${e(shot.name)}" src="${e(shot.data_url)}"><figcaption>${e(shot.name)} · SHA-256：${shot.sha256}</figcaption></figure>`).join('')}</section>`).join('');
  return `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><meta name="viewport" content="width=device-width, initial-scale=1"><title>变更影响与回归检查报告</title><style>body{font:16px/1.7 system-ui;max-width:1040px;margin:40px auto;padding:0 24px;background:#f5f7fb;color:#18253b}section,header{background:white;padding:24px;margin:20px 0;border:1px solid #dbe2ee;border-radius:16px}p,li,pre,figcaption{overflow-wrap:anywhere;white-space:pre-wrap}img{max-width:100%;height:auto}.note{border-left:4px solid #2563eb;padding-left:15px}h1{font-size:30px}pre{font-size:13px}</style><header><h1>变更影响与回归检查报告</h1><p>版本 ${report.version} · 报告 ${report.id} · 修订 ${report.revision}</p><p>${report.demo ? '演示材料，不是真实项目验收。' : '本地仓库静态分析与人工结果记录。'}</p><p>${e(report.boundary)}</p><p>仓库：${e(report.root)}<br>基线：${report.base}<br>目标：${report.head}</p><p>${overview(report)}</p><p>${e(report.comparison)}</p><ul>${report.warnings.map(value => `<li>${e(value)}</li>`).join('')}</ul><details><summary>扫描统计</summary><pre>${e(JSON.stringify(report.scan, null, 2))}</pre></details></header>${cards || '<section>没有可展示的清单项；不表示所有功能通过。</section>'}</html>`;
}
export function csv(report) {
  const cell = value => '"' + String(/^[=+\-@\t\r]/.test(String(value)) ? "'" + value : value).replaceAll('"', '""') + '"';
  const rows = [['文件', '名称', '类型', '风险', '状态', '实际观察', '建议验证', '证据', '截图数量', '结果来源']];
  for (const item of report.items) rows.push([item.path, item.display_name, labels[item.kind], labels[item.risk], labels[item.status], item.note,
    item.suggested_steps.join('；'), item.evidence, item.screenshots.length, item.result_source || '尚未录入']);
  return '\ufeff' + rows.map(row => row.map(cell).join(',')).join('\r\n') + '\r\n';
}
export async function exportFiles(report) {
  const dir = await directory(path.join(cacheRoot, 'exports', report.id + '-r' + report.revision));
  const artifacts = { 'report.md': markdown(report), 'report.html': html(report), 'report.csv': csv(report), 'report.json': JSON.stringify(publicReport(report, true), null, 2) + '\n' };
  const files = [];
  for (const [name, text] of Object.entries(artifacts)) {
    const target = path.join(dir, name);
    try { await fs.writeFile(target, text, { flag: 'wx', mode: 0o600 }); }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      const stat = await fs.lstat(target);
      if (!stat.isFile() || stat.isSymbolicLink() || digest(await fs.readFile(target)) !== digest(text)) throw new Error('导出位置存在不同内容或不安全文件，未覆盖。');
    }
    files.push({ path: target, sha256: digest(text), bytes: Buffer.byteLength(text) });
  }
  return { files, markdown: artifacts['report.md'], counts: counts(report), revision: report.revision,
    message: '报告已导出到插件私有缓存。完整 HTML 内嵌用户截图，可单文件离线查看；未提交或发布。' };
}
