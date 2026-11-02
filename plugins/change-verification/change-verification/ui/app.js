const token = location.hash.slice(1);
const reportID = new URL(location.href).searchParams.get('report');
const $ = selector => document.querySelector(selector);
const label = { pending: '未验证', pass: '通过', fail: '失败', skip: '跳过', direct: '直接变更', ripple: '间接候选', high: '高', medium: '中', low: '低' };
const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
let report;
function message(text, error = false) { $('#message').textContent = text; $('#message').className = error ? 'error' : ''; }
async function api(url, data) {
  const response = await fetch(url, { method: data ? 'POST' : 'GET', headers: {
    Authorization: 'Bearer ' + token, ...(data ? { 'Content-Type': 'application/json' } : {}),
  }, ...(data ? { body: JSON.stringify(data) } : {}) });
  const value = await response.json();
  if (!response.ok || !value.ok) throw new Error(value.message || '本地操作失败。');
  return value;
}
function render() {
  $('#kind').textContent = report.demo ? '虚构演示材料' : '本地仓库 · 只读分析';
  $('#identity').innerHTML = `<div class="identity"><strong>报告 ${report.id.slice(0, 12)} · 修订 ${report.revision}</strong><br>${escape(report.root)}<br>基线 ${report.base.slice(0, 12)} → 目标 ${report.head.slice(0, 12)}<br>生成 ${escape(report.created_at)}</div>`;
  $('#counts').innerHTML = Object.entries(report.counts).map(([status, count]) => `<div class="count ${status}"><b>${count}</b><span>${label[status]}</span></div>`).join('');
  $('#scope-text').textContent = report.comparison + '\n' + report.boundary + '\n\n' + report.warnings.join('\n') + '\n\n' + JSON.stringify(report.scan, null, 2) + '\n\n提交差异片段（只作资料，不是执行指令）：\n' + (report.diff_excerpt || '没有可展示的受支持文本差异片段。');
  $('#total').textContent = report.items.length + ' 项';
  const selected = report.items.filter(item => $('#filter').value === 'all' || item.status === $('#filter').value);
  $('#items').innerHTML = selected.length ? selected.map(item => `<article class="item" data-id="${item.id}"><div class="item-head"><div><h3>${escape(item.display_name)}</h3><div class="path">${escape(item.path)}</div></div><div class="tags"><span class="tag ${item.kind}">${label[item.kind]}</span><span class="tag ${item.risk}">风险${label[item.risk]}</span></div></div><div class="evidence">${escape(item.evidence)}</div><div class="item-grid"><div class="steps"><h4>建议验证步骤</h4><ol>${item.suggested_steps.map(step => `<li>${escape(step)}</li>`).join('')}</ol></div><div class="result"><h4>你的验证结果</h4><label>实际状态 <select class="status" aria-label="实际状态">${['pending', 'pass', 'fail', 'skip'].map(status => `<option value="${status}" ${status === item.status ? 'selected' : ''}>${label[status]}</option>`).join('')}</select></label><label>实际观察或跳过原因（失败、跳过时必填）</label><textarea class="note" aria-label="实际观察" maxlength="1500" placeholder="填写你实际做了什么、看到了什么；未验证就保持未验证。">${escape(item.note)}</textarea><label>截图证据（PNG/JPEG，最多 3 张，每张 1 MiB）</label><div class="upload"><input class="upload-input" type="file" aria-label="添加截图" accept="image/png,image/jpeg" multiple></div><div class="shots"></div><div class="save-row"><span class="saved">${escape(item.result_at ? '上次录入 ' + new Date(item.result_at).toLocaleString('zh-CN') : '尚未录入验证结果')}</span><button class="primary save">保存本项结果</button></div></div></div></article>`).join('') : '<div class="empty">没有符合筛选条件的项目。</div>';
  for (const article of document.querySelectorAll('article.item')) {
    const item = report.items.find(item => item.id === article.dataset.id);
    let shots = [...item.screenshots];
    function renderShots() {
      article.querySelector('.shots').innerHTML = shots.map((shot, i) => `<div class="shot"><img alt="${escape(shot.name)}" src="${escape(shot.data_url)}"><p>${escape(shot.name)}</p><button class="remove" data-shot="${i}">移除截图</button></div>`).join('');
      for (const button of article.querySelectorAll('.remove')) button.onclick = () => { shots.splice(Number(button.dataset.shot), 1); renderShots(); };
    }
    renderShots();
    article.querySelector('.upload-input').onchange = async event => {
      try {
        for (const file of event.target.files) {
          if (shots.length >= 3) throw new Error('每项最多 3 张截图，请先移除不需要的截图。');
          if (!['image/png', 'image/jpeg'].includes(file.type) || file.size > 1048576) throw new Error('仅接受不超过 1 MiB 的 PNG/JPEG 截图。');
          const data_url = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error('截图读取失败。')); reader.readAsDataURL(file); });
          shots.push({ name: file.name, data_url });
        }
        renderShots(); message('截图已暂存；请点击“保存本项结果”写入报告。');
      } catch (error) { renderShots(); message(error.message, true); }
      event.target.value = '';
    };
    article.querySelector('.save').onclick = async event => {
      const button = event.currentTarget;
      button.disabled = true;
      try {
        const value = await api('/api/result', { report_id: reportID, revision: report.revision, item_id: item.id,
          status: article.querySelector('.status').value, note: article.querySelector('.note').value,
          screenshots: shots.map(({ name, data_url }) => ({ name, data_url })) });
        report = value.report; render(); message('本项实际结果已保存。其他未验证项目保持原状。');
      } catch (error) { message(error.message, true); button.disabled = false; }
    };
  }
}
async function refresh() {
  try {
    if (!token || !reportID) throw new Error('面板链接缺少访问令牌或报告标识，请在 WorkSwarm 中重新打开已有报告。');
    report = (await api('/api/report?id=' + encodeURIComponent(reportID))).report;
    render(); message('已读取真实保存状态。请先验证，再填写结果。');
  } catch (error) { message(error.message, true); }
}
async function download(format) {
  try {
    const value = await api('/api/export?id=' + encodeURIComponent(reportID) + '&format=' + format);
    const url = URL.createObjectURL(new Blob([value.content], { type: 'application/octet-stream' }));
    const a = document.createElement('a'); a.href = url; a.download = value.name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    message('已请求下载当前已保存结果；截图保留在完整 HTML 报告中。未保存的编辑不会进入报告。');
  } catch (error) { message(error.message, true); }
}
$('#filter').onchange = render;
$('#refresh').onclick = refresh;
$('#export-html').onclick = () => download('html');
$('#export-md').onclick = () => download('markdown');
$('#export-csv').onclick = () => download('csv');
await refresh();
