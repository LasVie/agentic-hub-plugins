// Browser save files are untrusted. Never use upstream's shallow restore().
const MAX_SCORE = 1e12;
const integer = (v, min, max) => Number.isSafeInteger(v) && v >= min && v <= max;
const record = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const keys = (v, names) => record(v) && Object.keys(v).every(k => names.includes(k));
const list = (v, max, valid) => Array.isArray(v) && v.length <= max && v.every(valid);

export function validGame(g) {
  if (!keys(g, ['v','h','level','score','hi','lives','nextLife','px','invaders','total','shields','ufo','dir','anim','shots','reload','vx','glide','lastMove','bombs','booms','tick','invuln','cleared','over','seed'])) return false;
  if (g.v !== 2 || !integer(g.h, 12, 16) || !integer(g.level, 1, 1000000) ||
      !integer(g.score, 0, MAX_SCORE) || !integer(g.hi, g.score, MAX_SCORE) ||
      !integer(g.lives, 0, 5) || !integer(g.nextLife, 1500, MAX_SCORE) || g.nextLife % 1500 !== 0 ||
      !integer(g.px, 0, 30) || !integer(g.total, 1, 24) || ![-1,1].includes(g.dir) ||
      ![0,1].includes(g.anim) || !integer(g.reload, 0, 3) || ![-1,0,1].includes(g.vx) ||
      !integer(g.glide, 0, 3) || !integer(g.tick, 0, 1e9) || !integer(g.lastMove, -99, g.tick) ||
      !integer(g.invuln, 0, 30) || !integer(g.cleared, 0, 30) || typeof g.over !== 'boolean' ||
      !integer(g.seed, 0, 2147483647) || (g.lives === 0) !== g.over) return false;
  const pos = p => keys(p, ['x','y']) && integer(p.x, 0, 32) && integer(p.y, 0, g.h - 1);
  if (!list(g.shots, 3, pos) || !list(g.bombs, 4, pos) ||
      !list(g.invaders, g.total, i => keys(i,['x','y','row']) && integer(i.x,0,30) && integer(i.y,0,g.h-1) && integer(i.row,0,3)) ||
      !list(g.shields, 40, b => keys(b,['x','y','ch','hp']) && integer(b.x,0,32) && integer(b.y,0,g.h-1) && ['▟','█','▙'].includes(b.ch) && integer(b.hp,1,2)) ||
      !list(g.booms, 64, b => keys(b,['x','y','t','text']) && integer(b.x,-5,33) && integer(b.y,0,g.h-1) && integer(b.t,1,20) && (b.text === undefined || (typeof b.text === 'string' && /^(?:\+1|\d{1,12})$/.test(b.text))))) return false;
  return g.ufo === null || (keys(g.ufo,['x','y','dir']) && integer(g.ufo.x,-5,33) && g.ufo.y === 0 && [-1,1].includes(g.ufo.dir));
}

export function restoreSave(text, initialSeed) {
  if (typeof text !== 'string' || text.length > 65536) return null;
  try {
    const value = JSON.parse(text);
    if (!keys(value,['schema','version','initialSeed','game']) || value.schema !== 1 ||
        value.version !== '1.0.2' || value.initialSeed !== initialSeed || !validGame(value.game)) return null;
    return value.game;
  } catch { return null; }
}

export function saveText(game, initialSeed) {
  if (!validGame(game)) throw new Error('当前游戏状态无效，未保存。');
  return JSON.stringify({schema:1, version:'1.0.2', initialSeed, game});
}
