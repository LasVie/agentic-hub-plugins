import { Chess, DEFAULT_POSITION } from '../vendor/chess/chess.js';

export { DEFAULT_POSITION };
export const MATE_FEN = '7k/8/5KQ1/8/8/8/8/8 w - - 0 1';
export const EXAMPLE_PGN = '[Event "本地教学示例"]\n[White "白方"]\n[Black "黑方"]\n[Result "*"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 *';

export class InputError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

/** The supported envelope protects the engine; this does not prove historical reachability. */
export function checkPosition(game, originalFen = game.fen()) {
  const fen = game.fen();
  const pieces = game.board().flat().filter(Boolean);
  const kings = Object.fromEntries(['w', 'b'].map(color => [color, pieces.filter(p => p.type === 'k' && p.color === color)]));
  if (kings.w.length !== 1 || kings.b.length !== 1) throw new InputError('invalid_kings', '每方必须恰有一个王。');
  for (const color of ['w', 'b']) {
    if (pieces.filter(p => p.color === color).length > 16 || pieces.filter(p => p.color === color && p.type === 'p').length > 8) throw new InputError('piece_limit', '每方最多 16 枚棋子，其中兵最多 8 枚。');
  }
  if (pieces.some(p => p.type === 'p' && /[18]$/.test(p.square))) throw new InputError('invalid_pawn', '兵不能位于第一行或第八行。');
  const [wk, bk] = [kings.w[0].square, kings.b[0].square];
  if (Math.abs(wk.charCodeAt(0) - bk.charCodeAt(0)) <= 1 && Math.abs(Number(wk[1]) - Number(bk[1])) <= 1) throw new InputError('adjacent_kings', '两个王不能相邻。');
  const inactive = game.turn() === 'w' ? 'b' : 'w';
  if (game.isAttacked(kings[inactive][0].square, game.turn())) throw new InputError('inactive_king_in_check', '非行棋方的王已被将军；该局面不在支持范围内。');
  const castling = originalFen.split(/\s+/)[2];
  for (const [right, king, rook, color] of [['K','e1','h1','w'],['Q','e1','a1','w'],['k','e8','h8','b'],['q','e8','a8','b']]) {
    if (castling.includes(right) && (game.get(king)?.type !== 'k' || game.get(king)?.color !== color || game.get(rook)?.type !== 'r' || game.get(rook)?.color !== color)) throw new InputError('invalid_castling', '王车易位权与王、车的位置不一致。');
  }
  return game;
}

export function parsePosition(kind, text) {
  if (typeof text !== 'string' || !text.trim()) throw new InputError('input_required', '请先输入 FEN 或 PGN。');
  if ((kind === 'pgn' ? new TextEncoder().encode(text).length : text.length) > (kind === 'pgn' ? 65536 : 256)) throw new InputError('input_too_large', kind === 'pgn' ? 'PGN 最多 64 KiB 文本。' : 'FEN 最多 256 个字符。');
  const game = new Chess();
  try {
    if (kind === 'pgn') {
      game.loadPgn(text, { strict: true });
      if (game.history().length > 512) throw new InputError('move_limit', 'PGN 主线最多 512 个半回合。');
      // Check the starting FEN as well, including any supplied SetUp position.
      const history = game.history({ verbose: true });
      parsePosition('fen', game.getHeaders().FEN ?? history[0]?.before ?? game.fen());
    } else {
      const tokens = text.trim().split(/\s+/);
      if (tokens.length !== 6) throw new InputError('invalid_fen', 'FEN 必须包含完整的六个字段。');
      if (!/^[wb]$/.test(tokens[1]) || !/^(?:-|K?Q?k?q?)$/.test(tokens[2]) || !/^(?:-|[a-h][36])$/.test(tokens[3]) || !/^\d+$/.test(tokens[4]) || !/^[1-9]\d*$/.test(tokens[5])) throw new InputError('invalid_fen', 'FEN 行棋方、易位权、吃过路兵或回合字段无效。');
      if (Number(tokens[4]) > 100000 || Number(tokens[5]) > 100000) throw new InputError('invalid_fen', 'FEN 回合计数超出支持范围。');
      game.load(tokens.join(' '));
      checkPosition(game, tokens.join(' '));
      if (tokens[3] !== '-') {
        const ep = tokens[3], rank = Number(ep[1]);
        const expectedRank = game.turn() === 'w' ? 6 : 3;
        const pawnSquare = ep[0] + (game.turn() === 'w' ? 5 : 4);
        const sourceSquare = ep[0] + (game.turn() === 'w' ? 7 : 2);
        const pawn = game.get(pawnSquare);
        if (rank !== expectedRank || game.get(ep) || game.get(sourceSquare) || pawn?.type !== 'p' || pawn?.color === game.turn() || tokens[4] !== '0') throw new InputError('invalid_en_passant', '吃过路兵目标与上一手兵的双步位置不一致。');
      }
    }
    return checkPosition(game);
  } catch (error) {
    if (error instanceof InputError) throw error;
    throw new InputError(kind === 'pgn' ? 'invalid_pgn' : 'invalid_fen', kind === 'pgn' ? 'PGN 无法按标准主线解析；请检查棋谱和 SAN 着法。' : 'FEN 无效；请检查棋子、行棋方与六个字段。');
  }
}

export function uciMove(game, uci) {
  if (!/^[a-h][1-8][a-h][1-8][qrbn]?$/.test(uci)) throw new InputError('invalid_engine_move', '引擎返回了无法识别的着法。');
  try { return game.move({ from: uci.slice(0, 2), to: uci.slice(2, 4), promotion: uci[4] }); }
  catch { throw new InputError('illegal_engine_move', '引擎主变化包含非法着法；结果已拒绝。'); }
}

export function validateVariation(fen, moves) {
  if (moves.length > 128) throw new InputError('variation_limit', '引擎候选线超过 128 个半回合；该结果未保留。');
  const game = parsePosition('fen', fen);
  const result = [];
  for (const uci of moves) {
    const move = uciMove(game, uci);
    result.push({ uci, san: move.san, fen: game.fen() });
  }
  return result;
}

export function positionStatus(game) {
  if (game.isCheckmate()) return `${game.turn() === 'w' ? '白方' : '黑方'}被将死`;
  if (game.isStalemate()) return '逼和';
  if (game.isInsufficientMaterial()) return '子力不足和棋';
  if (game.isThreefoldRepetition()) return '三次重复局面和棋';
  if (game.isDrawByFiftyMoves()) return '五十回合规则和棋';
  return `${game.turn() === 'w' ? '白方' : '黑方'}行棋${game.inCheck() ? ' · 被将军' : ''}`;
}

export function parseInfo(line) {
  if (!line.startsWith('info ') || !/\spv\s/.test(line)) return null;
  const value = key => { const m = line.match(new RegExp(`(?:^| )${key} (-?\\d+)(?: |$)`)); return m ? Number(m[1]) : null; };
  const score = line.match(/\bscore (cp|mate) (-?\d+)(?: (lowerbound|upperbound))?/);
  const pv = line.match(/\bpv ((?:[a-h][1-8][a-h][1-8][qrbn]?(?: |$))+)/);
  if (!score || !pv || !Number.isFinite(value('depth'))) return null;
  const multipv = value('multipv') ?? 1;
  if (multipv < 1 || multipv > 3) return null;
  return { depth: value('depth'), seldepth: value('seldepth'), nodes: value('nodes'), time_ms: value('time'), multipv, score: { type: score[1], value: Number(score[2]), bound: score[3] ?? null, perspective: 'side_to_move' }, pv: pv[1].trim().split(/\s+/) };
}

export function formatScore(score, color) {
  const side = color === 'w' ? '白方' : '黑方';
  const suffix = score.bound === 'lowerbound' ? '（评分下界）' : score.bound === 'upperbound' ? '（评分上界）' : '';
  if (score.type === 'mate') return `${side}${score.value > 0 ? '将死对方' : '将被将死'} ${Math.abs(score.value)} 步${suffix}`;
  return `${score.value >= 0 ? '+' : ''}${(score.value / 100).toFixed(2)} 兵${suffix}`;
}
