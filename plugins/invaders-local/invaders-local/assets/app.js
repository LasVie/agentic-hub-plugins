// Browser adapter for the pinned MIT engine; no network or host APIs.
const byId = id => document.getElementById(id);
const board = byId('board');
const notice = byId('notice');
const storageKey = 'invaders-local:1.0.2:' + location.pathname + ':' + INITIAL_SEED;
let game = newGame(0, INITIAL_SEED);
let paused = true;
let started = false;
let storageEnabled = true;
try {
  const text = localStorage.getItem(storageKey);
  if (text !== null) {
    const saved = restoreSave(text, INITIAL_SEED);
    if (saved) { game = saved; started = true; notice.textContent = game.over ? '已恢复已结束的对局，点击重新开始可再次游玩。' : '已恢复本地进度，点击继续游戏。'; }
    else { localStorage.removeItem(storageKey); notice.textContent = '存档无效或版本不匹配，已安全忽略并新建游戏。'; }
  }
} catch { storageEnabled = false; notice.textContent = '浏览器未开放本地存储；本次仍可游玩，但不能续玩。'; }

function saveProgress(manual = false) {
  if (!storageEnabled) { if (manual) notice.textContent = '浏览器未开放本地存储，无法保存。'; return; }
  try {
    localStorage.setItem(storageKey, saveText(game, INITIAL_SEED));
    if (manual) notice.textContent = '进度已保存在当前浏览器。重新打开同一地址即可恢复，并保持暂停。';
  } catch { notice.textContent = '保存失败，当前游戏仍可继续；请勿依赖本次续玩。'; }
}

const colors = {'ansi256(2)':'#66ba80','ansi256(10)':'#8ce69e','ansi256(13)':'#e5a4db','ansi256(14)':'#8cdedc','ansi256(15)':'#f1f7fc'};
function render() {
  const fragment = document.createDocumentFragment();
  for (const row of draw(game)) {
    const line = document.createElement('span');
    for (const run of row) {
      const span = document.createElement('span');
      span.textContent = run.text;
      if (run.color) span.style.color = colors[run.color] || '#e3edf1';
      if (run.bold) span.style.fontWeight = '700';
      if (run.dim) span.style.opacity = '0.4';
      line.append(span);
    }
    fragment.append(line, document.createTextNode('\n'));
  }
  board.replaceChildren(fragment);
  for (const field of ['score','hi','level','lives']) byId(field).textContent = game[field];
  byId('position').textContent = `位置 ${game.px} · 步数 ${game.tick}`;
  byId('status').textContent = game.over ? '游戏结束' : paused ? (started ? '已暂停' : '待开始') : game.cleared > 0 ? '本波已清空，下一波准备中' : '游戏中';
  byId('toggle').textContent = game.over ? '游戏已结束' : paused ? (started ? '继续游戏' : '开始游戏') : '暂停游戏';
  byId('toggle').disabled = game.over;
  board.setAttribute('aria-label', `射击棋盘；位置 ${game.px}，生命 ${game.lives}，波次 ${game.level}，得分 ${game.score}`);
}

function pause() { paused = true; saveProgress(); render(); }
function toggle() {
  if (game.over) return;
  paused = !paused; started = true;
  if (paused) saveProgress();
  else board.focus({preventScroll:true});
  render();
}
byId('toggle').addEventListener('click', toggle);
byId('save').addEventListener('click', () => saveProgress(true));
byId('restart').addEventListener('click', () => {
  game = newGame(game.hi, INITIAL_SEED); paused = true; started = false;
  saveProgress(); notice.textContent = '已重新开局，最高分保留。点击开始游戏。'; render();
});
board.addEventListener('keydown', event => {
  const key = event.key.toLowerCase();
  if (!['arrowleft','arrowright','a','d',' ','p','escape'].includes(key)) return;
  event.preventDefault();
  if (key === 'p') { if (!event.repeat) toggle(); return; }
  if (key === 'escape') { pause(); return; }
  if (game.over || paused) return;
  if (key === 'arrowleft' || key === 'a') game = move(game, -1);
  if (key === 'arrowright' || key === 'd') game = move(game, 1);
  if (key === ' ') game = fire(game);
  render();
});
window.addEventListener('blur', pause);
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
window.addEventListener('pagehide', () => saveProgress());
setInterval(() => {
  if (paused || game.over) return;
  game = step(game);
  if (game.over) paused = true;
  if (game.tick % 10 === 0 || game.over) saveProgress();
  render();
}, TICK_MS);
render();
