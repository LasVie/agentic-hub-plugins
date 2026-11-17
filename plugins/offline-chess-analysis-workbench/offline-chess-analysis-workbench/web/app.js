import { Chess } from '../vendor/chess/chess.js';
import { ChessEngine } from './engine.js';
import { DEFAULT_POSITION, MATE_FEN, EXAMPLE_PGN, InputError, parsePosition, positionStatus, formatScore } from './model.js';
import { PIECE_NAMES, pieceSVG, squareOrder, boardSVG } from './board.js';

const $ = id => document.getElementById(id);
const engine = new ChessEngine();
const exports = ['export-fen','export-pgn','export-json','export-svg'];
let game = parsePosition('fen', DEFAULT_POSITION), mode = 'fen', dirty = false, busy = false;
let generation = 0, result = null, selected = null, flipped = false, lastMove = null;
let replay = null, selectedLine = 0, replayStep = 0;
const EMPTY = '<div class="empty"><svg viewBox="0 0 120 70" aria-hidden="true"><path d="M8 35h34m0 0 22-22h40M42 35l22 22h40"/><circle cx="8" cy="35" r="5"/><circle cx="106" cy="13" r="5"/><circle cx="106" cy="57" r="5"/></svg><strong>等待真实引擎结果</strong><span>候选线会逐手通过规则校验后显示。</span></div>';

function notify(text, error = false) { $('message').textContent = text; $('message').classList.toggle('error', error); }
function setState(text, status = '') { $('state').textContent = text; $('state').className = 'state' + (status ? ` ${status}` : ''); }
function setBusy(value) { busy = value; $('analyze').disabled = value; $('cancel').disabled = !value; }
function invalidate(text = '输入已更改；请载入局面并重新分析。', inputDirty = true) {
  generation++; engine.cancel(); setBusy(false); result = null; replay = null; replayStep = 0; selectedLine = 0; selected = null;
  if (inputDirty) dirty = true;
  exports.forEach(id => { $(id).disabled = true; });
  $('best-move').textContent = '—'; $('depth').textContent = '—'; $('nodes').textContent = '—'; $('elapsed').textContent = '—';
  $('engine-name').textContent = '等待运行'; $('variations').innerHTML = EMPTY; $('replay').hidden = true;
  $('score-note').textContent = '分值以分析起点的行棋方为视角；正数有利于该方。100 厘兵 = 1 兵。有限搜索不等于最优性或胜负保证。';
  setState(inputDirty ? '输入待检查' : '尚未分析'); notify(text); renderBoard();
}
function setMode(value, invalidateInput = true) {
  mode = value;
  $('fen-mode').setAttribute('aria-pressed', String(mode === 'fen')); $('pgn-mode').setAttribute('aria-pressed', String(mode === 'pgn'));
  $('fen-field').hidden = mode !== 'fen'; $('pgn-field').hidden = mode !== 'pgn';
  if (invalidateInput) invalidate();
}
function syncText() { $('fen').value = game.fen(); $('pgn').value = game.pgn({ maxWidth: 76 }); }
function setGame(next, text = '局面已载入；可在棋盘落子或运行分析。') {
  invalidate(text, false); game = next; dirty = false; lastMove = null; syncText(); renderBoard(); notify(text);
}
function loadCurrent() {
  try { setGame(parsePosition(mode, $(mode).value)); return true; }
  catch(error) { invalidate('输入未通过检查。', true); setState('输入错误', 'error'); notify(`${error.message}（${error.code ?? 'invalid_input'}）`, true); return false; }
}
function viewGame() { return replay ? new Chess(replayStep ? replay[replayStep - 1].fen : result.fen) : game; }
function viewLastMove() {
  if (replay && replayStep) { const uci = replay[replayStep - 1].uci; return { from: uci.slice(0,2), to: uci.slice(2,4) }; }
  return replay ? null : lastMove;
}
function renderBoard() {
  const display = viewGame(), order = squareOrder(flipped), last = viewLastMove();
  const targets = !dirty && !replay && selected ? game.moves({ square: selected, verbose: true }).map(move => move.to) : [];
  $('board').replaceChildren(); $('board').classList.toggle('pending', dirty);
  for (let i=0;i<order.length;i++) {
    const square = order[i], piece = display.get(square), button = document.createElement('button');
    button.type = 'button'; button.dataset.square = square; button.className = 'square' + ((Math.floor(i/8)+i%8)%2 ? ' dark' : '');
    button.classList.toggle('selected', selected === square); button.classList.toggle('target', targets.includes(square));
    button.classList.toggle('last', !!last && [last.from,last.to].includes(square));
    button.setAttribute('aria-label', `${square} ${piece ? (piece.color === 'w' ? '白' : '黑') + PIECE_NAMES[piece.type] : '空格'}${targets.includes(square) ? '，合法目标' : ''}`);
    button.disabled = dirty; button.innerHTML = pieceSVG(piece); $('board').append(button);
  }
  $('file-labels').replaceChildren(...[...(flipped ? 'hgfedcba' : 'abcdefgh')].map(text => { const label = document.createElement('span'); label.textContent = text; return label; }));
  $('rank-labels').replaceChildren(...(flipped ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1]).map(text => { const label = document.createElement('span'); label.textContent = text; return label; }));
  $('position-status').textContent = dirty ? '输入待检查 · 棋盘仅保留上次局面' : (replay ? `主变化回放 · ${positionStatus(display)}` : positionStatus(display));
  $('undo').disabled = dirty || busy || !!replay || game.history().length === 0;
  $('history').textContent = game.history().length ? game.history().join(' ') : '尚无棋谱着法';
}
function squareClick(square) {
  if (dirty) return;
  if (replay) { notify('当前为主变化预览；请返回分析起点或点击“以此局面继续”。'); return; }
  const piece = game.get(square);
  if (!selected || piece?.color === game.turn()) { selected = piece?.color === game.turn() && selected !== square ? square : null; renderBoard(); return; }
  const from = selected;
  try {
    if (game.history().length >= 512) throw new InputError('move_limit', '本次棋谱已达到 512 个半回合；请从新 FEN 开始。');
    // Validate before invalidation, so an accidental illegal target preserves completed analysis.
    const check = new Chess(game.fen()); check.move({ from, to: square, promotion: $('promotion').value });
    invalidate('着法已应用；旧分析已失效。', false);
    game.move({ from, to: square, promotion: $('promotion').value }); lastMove = { from, to: square };
    syncText(); renderBoard();
  } catch(error) { selected = null; renderBoard(); notify(error instanceof InputError ? `${error.message}（${error.code}）` : '该着法不合法；局面未改变。', true); }
}
function renderAnalysis() {
  if (!result) return;
  const primary = result.variants[0];
  $('engine-name').textContent = `${result.engine_name} · lite-single`;
  $('best-move').textContent = primary.variation[0]?.san ?? result.bestmove;
  $('depth').textContent = String(primary.depth); $('nodes').textContent = primary.nodes?.toLocaleString('zh-CN') ?? '未提供';
  $('elapsed').textContent = primary.time_ms === null ? '未提供' : `${(primary.time_ms / 1000).toFixed(2)} s`;
  $('variations').replaceChildren();
  result.variants.forEach((line,index) => {
    const section = document.createElement('div'); section.className = 'variation' + (replay && selectedLine === index ? ' active' : '');
    const head = document.createElement('div'); head.className = 'variation-head';
    const label = document.createElement('span'); label.textContent = `候选 ${line.multipv} · 深度 ${line.depth}`;
    const score = document.createElement('strong'); score.textContent = formatScore(line.score, result.side_to_move); head.append(label,score);
    const moves = document.createElement('div'); moves.className = 'pv-moves';
    line.variation.forEach((move,step) => { const button = document.createElement('button'); button.type = 'button'; button.textContent = `${step+1}. ${move.san}`; button.setAttribute('aria-label', `回放候选 ${line.multipv} 第 ${step+1} 步 ${move.san}`); button.classList.toggle('current', !!replay && selectedLine === index && replayStep === step+1); button.addEventListener('click', () => showReplay(index,step+1)); moves.append(button); });
    section.append(head,moves); $('variations').append(section);
  });
  $('score-note').textContent = `评分视角：${result.side_to_move === 'w' ? '白方' : '黑方'}（分析起点的行棋方）；正分有利于该方。100 厘兵 = 1 兵。每条候选线独立标注最后返回的深度；有限搜索不保证最优着法或实际胜负。`;
}
function showReplay(lineIndex, step) {
  if (!result) return;
  selected = null; selectedLine = lineIndex; replay = result.variants[lineIndex].variation; replayStep = Math.min(Math.max(0,step),replay.length);
  $('replay').hidden = false; $('replay-step').textContent = `${replayStep} / ${replay.length}`;
  $('replay-prev').disabled = replayStep === 0; $('replay-next').disabled = replayStep === replay.length;
  $('replay-caption').textContent = `候选 ${lineIndex+1} · ${replayStep ? replay[replayStep-1].san : '分析起点'} · 仅预览；尚未改写分析局面。`;
  renderBoard(); renderAnalysis();
}
async function analyze() {
  if (dirty && !loadCurrent()) return;
  invalidate('正在初始化本地引擎…', false);
  if (game.isGameOver()) { const terminal = positionStatus(game); notify(`此局面已结束：${terminal}；没有启动引擎，也没有生成候选线。`); setState(terminal); return; }
  const seconds = Number($('seconds').value), multipv = Number($('multipv').value);
  const fen = game.fen(), pgn = game.pgn(), token = generation;
  setBusy(true); setState('本地搜索中');
  try {
    const data = await engine.search(fen,seconds,multipv,progress => {
      if (token !== generation) return;
      $('engine-name').textContent = progress.name; $('depth').textContent = String(progress.depth);
      $('nodes').textContent = progress.nodes?.toLocaleString('zh-CN') ?? '未提供'; $('elapsed').textContent = progress.time_ms === null ? '未提供' : `${(progress.time_ms/1000).toFixed(2)} s`;
      notify('本地引擎搜索中；完成前不可导出。');
    });
    if (token !== generation || dirty || game.fen() !== fen) return;
    result = { plugin_version: '1.0.1', rules_version: '1.4.0', generated_at: new Date().toISOString(), pgn, ...data };
    setBusy(false); setState('分析完成', 'complete'); renderAnalysis(); renderBoard(); exports.forEach(id => { $(id).disabled = false; });
    notify('分析完成；结果对应当前局面和搜索设置，可回放并导出。');
  } catch(error) {
    if (token !== generation) return;
    setBusy(false); setState(error.code === 'cancelled' ? '搜索已取消' : '分析失败', error.code === 'cancelled' ? '' : 'error');
    notify(error instanceof InputError ? `${error.message}（${error.code}）` : '分析未能完成；结果未保留，请重新运行。（analysis_failed）', error.code !== 'cancelled');
    $('depth').textContent = '—'; $('nodes').textContent = '—'; $('elapsed').textContent = '—'; renderBoard();
  }
}
function download(kind) {
  if (!result || dirty || busy || result.fen !== game.fen()) { notify('当前没有可导出的有效分析，请重新运行。',true); return; }
  let content, type;
  if (kind === 'fen') { content = result.fen + '\n'; type = 'text/plain;charset=utf-8'; }
  else if (kind === 'pgn') { content = result.pgn + '\n'; type = 'application/x-chess-pgn;charset=utf-8'; }
  else if (kind === 'json') { content = JSON.stringify({ ...result, boundary: '有限深度和时间的局面分析；评分视角为分析起点行棋方；不证明最优性或保证胜负。', replay: { line: replay ? selectedLine+1 : null, step: replay ? replayStep : 0, displayed_fen: viewGame().fen() } },null,2) + '\n'; type = 'application/json;charset=utf-8'; }
  else { content = boardSVG(viewGame(),{flipped,lastMove:viewLastMove()}); type = 'image/svg+xml;charset=utf-8'; }
  const url = URL.createObjectURL(new Blob([content],{type})); const link = document.createElement('a');
  link.href = url; link.download = `国际象棋-${kind === 'svg' ? '棋盘预览' : '局面分析'}.${kind}`; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url),1000);
}

$('initial').addEventListener('click', () => { setMode('fen',false); setGame(parsePosition('fen',DEFAULT_POSITION)); });
$('mate-example').addEventListener('click', () => { setMode('fen',false); setGame(parsePosition('fen',MATE_FEN),'一步将死局面已载入；请运行引擎，核对并回放真实结果。'); });
$('pgn-example').addEventListener('click', () => { setMode('pgn',false); setGame(parsePosition('pgn',EXAMPLE_PGN),'公开教学棋谱已载入；当前为其主线末尾局面。'); });
$('fen-mode').addEventListener('click', () => { if (mode !== 'fen') setMode('fen'); });
$('pgn-mode').addEventListener('click', () => { if (mode !== 'pgn') setMode('pgn'); });
for (const id of ['fen','pgn']) $(id).addEventListener('input', () => invalidate());
for (const id of ['seconds','multipv']) $(id).addEventListener('input', () => invalidate('搜索设置已更改；旧结果与导出已失效。',false));
$('load').addEventListener('click',loadCurrent); $('analyze').addEventListener('click',analyze);
$('cancel').addEventListener('click', () => { invalidate('搜索已取消；工作线程已释放，请重新运行。',false); setState('搜索已取消'); });
$('flip').addEventListener('click', () => { flipped = !flipped; renderBoard(); });
$('undo').addEventListener('click', () => { if (dirty || busy || replay) return; invalidate('已撤回一手；旧分析已失效。',false); game.undo(); lastMove = null; syncText(); renderBoard(); });
$('board').addEventListener('click',event => { const square = event.target.closest('button[data-square]')?.dataset.square; if(square) squareClick(square); });
$('board').addEventListener('keydown',event => { const button = event.target.closest('button[data-square]'); if(!button) return; const delta = {ArrowLeft:-1,ArrowRight:1,ArrowUp:-8,ArrowDown:8}[event.key]; if(delta === undefined) return; event.preventDefault(); const buttons=[...$('board').children], next=buttons.indexOf(button)+delta; buttons[next]?.focus(); });
$('replay-home').addEventListener('click', () => { replay = null; replayStep = 0; $('replay').hidden = true; renderBoard(); renderAnalysis(); });
$('replay-prev').addEventListener('click', () => showReplay(selectedLine,replayStep-1)); $('replay-next').addEventListener('click', () => showReplay(selectedLine,replayStep+1));
$('use-replay').addEventListener('click', () => { if (!replay) return; const next = parsePosition('fen',viewGame().fen()); setMode('fen',false); setGame(next,'已将预览局面设为新的分析起点；请重新运行。'); });
exports.forEach(id => $(id).addEventListener('click', () => download(id.slice(7))));
$('pgn-file').addEventListener('change',async () => {
  const file = $('pgn-file').files[0]; if (!file) return;
  invalidate('正在读取 PGN 文件…'); const token = generation;
  try {
    if (file.size > 65536) throw new InputError('input_too_large','PGN 文件最多 64 KiB。');
    const bytes = await file.arrayBuffer(), text = new TextDecoder('utf-8',{fatal:true}).decode(bytes);
    if (token !== generation) return;
    const next = parsePosition('pgn',text); setMode('pgn',false); setGame(next,'PGN 文件已载入并检查；没有执行文件中的任何指令。');
  } catch(error) { if (token === generation) notify(`${error instanceof InputError ? error.message : '文件无法作为 UTF-8 PGN 读取。'}（${error.code ?? 'invalid_utf8'}）`,true); }
  finally { $('pgn-file').value = ''; }
});
window.addEventListener('pagehide', () => engine.cancel());
syncText(); renderBoard();
