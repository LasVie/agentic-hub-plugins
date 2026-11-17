export const PIECE_NAMES = { p: '兵', n: '马', b: '象', r: '车', q: '后', k: '王' };
const silhouettes = {
  p: '<circle cx="30" cy="16" r="8"/><path d="M25 24h10l2 14 7 9H16l7-9z"/>',
  r: '<path d="M15 10h8v7h4v-7h6v7h4v-7h8v17l-6 5 2 15H19l2-15-6-5z"/><path d="M19 27h22" fill="none"/>',
  n: '<path d="M17 47l4-13 14-12-13 4-9-6 8-9 2-8 9 6 10 6 4 16-4 16z"/><path d="M23 12l11 4" fill="none"/><circle cx="27" cy="16" r="1.7" fill="#a87b46" stroke="none"/>',
  b: '<path d="M30 6c-6 6-11 13-11 20 0 5 5 8 7 9l-6 12h20l-6-12c3-2 7-5 7-10 0-7-5-13-11-19z"/><path d="M25 16l10 12" fill="none"/>',
  q: '<path d="M13 18l6 25h22l6-25-13 14-4-18-5 18z"/><circle cx="12" cy="15" r="4"/><circle cx="30" cy="10" r="4"/><circle cx="48" cy="15" r="4"/>',
  k: '<path d="M27 4h6v6h6v6h-6v7h-6v-7h-6v-6h6z"/><path d="M17 24c0-9 13-4 13 1 0-5 13-10 13-1 0 7-7 9-7 13l5 10H19l5-10c0-4-7-6-7-13z"/>',
};

export function pieceSVG(piece, size = 60) {
  if (!piece || !silhouettes[piece.type] || !['w','b'].includes(piece.color)) return '';
  const fill = piece.color === 'w' ? '#fff9e9' : '#253b42';
  const stroke = piece.color === 'w' ? '#253b42' : '#d8e5dc';
  return `<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" viewBox="0 0 60 60" width="${size}" height="${size}"><g fill="${fill}" stroke="${stroke}" stroke-width="2.1" stroke-linejoin="round" stroke-linecap="round">${silhouettes[piece.type]}<path d="M17 48h26l3 6H14z"/></g></svg>`;
}

export function squareOrder(flipped = false) {
  const files = [...'abcdefgh']; const ranks = [8,7,6,5,4,3,2,1];
  if (flipped) { files.reverse(); ranks.reverse(); }
  return ranks.flatMap(rank => files.map(file => file + rank));
}

export function boardSVG(game, { flipped = false, lastMove = null } = {}) {
  const files = flipped ? [...'hgfedcba'] : [...'abcdefgh'];
  const ranks = flipped ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1];
  let output = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720" width="720" height="720" role="img" aria-label="国际象棋局面"><title>当前国际象棋局面</title><rect width="720" height="720" fill="#f7f7ed"/>';
  for (let row = 0; row < 8; row++) for (let column = 0; column < 8; column++) {
    const square = files[column] + ranks[row], x = 40 + 80 * column, y = 40 + 80 * row;
    output += `<rect x="${x}" y="${y}" width="80" height="80" fill="${(column+row)%2 ? '#739890' : '#e8eddf'}"/>`;
    if (lastMove && [lastMove.from,lastMove.to].includes(square)) output += `<rect x="${x+2}" y="${y+2}" width="76" height="76" fill="none" stroke="#b37829" stroke-width="4"/>`;
    const piece = game.get(square);
    if (piece) output += `<g transform="translate(${x+8} ${y+8}) scale(1.0666667)">${pieceSVG(piece).replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'')}</g>`;
  }
  for (let i=0;i<8;i++) output += `<text x="${80+i*80}" y="700" fill="#334e50" text-anchor="middle" font-family="sans-serif" font-size="20">${files[i]}</text><text x="20" y="${86+i*80}" fill="#334e50" text-anchor="middle" font-family="sans-serif" font-size="20">${ranks[i]}</text>`;
  return output + '</svg>';
}
