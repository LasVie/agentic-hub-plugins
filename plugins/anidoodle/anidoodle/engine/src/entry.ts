// JiuwenSwarm adapter by Gan Mingrui, 2026-10-27. Upstream notices are bundled in licenses/.
import { mount } from './hosts/interactive';
import { mascotHero } from './canvas-core/mascotHero';
import { formMascot } from './canvas-core/formMascot';
import { scrollHero } from './canvas-core/scrollHero';

const pieces = { mascot: mascotHero, form: formMascot, scroll: scrollHero };
const el = document.getElementById('art');
const scene = document.body.dataset.scene as keyof typeof pieces;
if (!el || !pieces[scene]) throw new Error('作品类型无效，请重新生成页面。');
const c = mount(el, pieces[scene], { maxScale: 1.5, scrollTrack: scene === 'scroll' ? '#track' : null });
(window as any).__artController = c;
const status = document.getElementById('status')!;
const png = document.getElementById('save-png') as HTMLButtonElement;
c.ready.then(() => { status.textContent = '画好了，试着与它互动吧。'; png.disabled = false; }).catch(() => { status.textContent = '绘制失败，请使用新版 Chrome 或 Edge 重新打开。'; });
png.addEventListener('click', () => {
  c.renderNow();
  c.canvas.toBlob(blob => {
    if (!blob) { status.textContent = '导出失败，请重试。'; return; }
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = '手绘作品.png'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 3000);
    status.textContent = '已导出当前画面。';
  }, 'image/png');
});
const form = document.querySelector('form');
form?.addEventListener('submit', event => {
  event.preventDefault();
  const name = document.getElementById('name') as HTMLInputElement;
  const password = document.getElementById('password') as HTMLInputElement;
  const valid = name.value.trim().length > 0 && password.value.length >= 4;
  c.setState(valid ? 'success' : 'error');
  status.textContent = valid ? '演示完成！没有注册账号，也没有发送任何信息。' : '请填写演示称呼，并输入至少 4 个字符的演示密码。';
});
form?.addEventListener('input', () => c.setState('idle'));
document.getElementById('reveal')?.addEventListener('change', event => {
  const visible = (event.target as HTMLInputElement).checked;
  (document.getElementById('password') as HTMLInputElement).type = visible ? 'text' : 'password';
  c.setState(visible ? 'peek' : 'idle');
});
