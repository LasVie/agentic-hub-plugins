/** Actual pinned engine/rules tests; no model calls or host replacement. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { Chess } from '../offline-chess-analysis-workbench/vendor/chess/chess.js';
import { ChessEngine } from '../offline-chess-analysis-workbench/web/engine.js';
import { MATE_FEN, parsePosition, validateVariation } from '../offline-chess-analysis-workbench/web/model.js';

const enginePath = process.env.CHESS_TEST_ENGINE ?? fileURLToPath(new URL('../offline-chess-analysis-workbench/vendor/stockfish/stockfish-19-lite-single.js', import.meta.url));
const started = new Set();
const records = [];
async function test(name, fn) {
  const start = Date.now();
  await fn();
  records.push({ name, passed: true, elapsed_ms: Date.now() - start });
  console.log('PASS', name);
}
class EngineProcess {
  constructor() {
    this.proc = spawn(process.execPath, [enginePath], { stdio: ['pipe','pipe','pipe'] });
    this.lines = [];
    this.waiters = [];
    this.stderr = '';
    started.add(this);
    readline.createInterface({input:this.proc.stdout}).on('line', line => {
      this.lines.push(line);
      for (const w of [...this.waiters]) if (w.predicate(line)) { this.waiters.splice(this.waiters.indexOf(w),1); clearTimeout(w.timer); w.resolve(line); }
      this.onmessage?.({data:line});
    });
    this.proc.stderr.on('data', d => { this.stderr += d; });
    this.proc.on('error', error => { this.onerror?.({error,preventDefault(){}}); });
  }
  postMessage(command) { this.proc.stdin.write(command + '\n'); }
  wait(predicate, timeout=15000) {
    return new Promise((resolve,reject) => {
      const w={predicate,resolve};
      w.timer=setTimeout(()=>{this.waiters=this.waiters.filter(x=>x!==w); reject(new Error('Engine timeout '+this.lines.slice(-5).join('\n')+' stderr='+this.stderr));},timeout);
      this.waiters.push(w);
    });
  }
  terminate() {
    this.proc.kill('SIGTERM');
    for (const w of this.waiters) clearTimeout(w.timer);
    this.waiters=[]; started.delete(this);
  }
  async ready() {
    const uci=this.wait(s=>s==='uciok'); this.postMessage('uci'); await uci;
    const r=this.wait(s=>s==='readyok'); this.postMessage('isready'); await r;
  }
}
function perft(game, depth) {
  if (!depth) return 1;
  let nodes=0;
  for(const move of game.moves({verbose:true})) { game.move(move); nodes+=perft(game,depth-1); game.undo(); }
  return nodes;
}
try {
  await test('rules starting-position perft 20 / 400 / 8902', () => {
    assert.deepEqual([1,2,3].map(d=>perft(new Chess(),d)),[20,400,8902]);
  });
  await test('castling moves both rooks and kings; no castle through attack', () => {
    const c=new Chess('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');
    assert(c.moves().includes('O-O')); assert(c.moves().includes('O-O-O'));
    c.move('O-O'); assert.equal(c.get('g1').type,'k'); assert.equal(c.get('f1').type,'r'); assert.equal(c.get('h1'),undefined);
    const attacked=new Chess('4kr2/8/8/8/8/8/8/4K2R w K - 0 1');
    assert(!attacked.moves().includes('O-O'));
  });
  await test('en-passant removes the passed pawn', () => {
    const c=parsePosition('fen','4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2');
    const m=c.move({from:'e5',to:'d6'}); assert(m.isEnPassant()); assert.equal(c.get('d5'),undefined); assert.equal(c.get('d6').type,'p');
  });
  await test('promotion supports all four choices and requires a legal move', () => {
    const c=parsePosition('fen','4k3/P7/8/8/8/8/8/4K3 w - - 0 1');
    assert.equal(c.moves({verbose:true}).filter(m=>m.from==='a7'&&m.to==='a8').length,4);
    c.move({from:'a7',to:'a8',promotion:'n'}); assert.equal(c.get('a8').type,'n');
    assert.throws(()=>new Chess().move({from:'e2',to:'e5'}));
  });
  await test('actual UCI initialization/version and engine perft 8902', async () => {
    const p=new EngineProcess(); try {
      await p.ready(); assert(p.lines.some(s=>s.startsWith('id name Stockfish 19')));
      p.postMessage('position startpos'); const done=p.wait(s=>/^Nodes searched:\s+8902/.test(s));
      p.postMessage('go perft 3'); await done;
    } finally {p.terminate();}
  });
  await test('actual engine search finds and independently verifies Qg7 mate', async () => {
    const e=new ChessEngine(()=>new EngineProcess());
    const result=await e.search(MATE_FEN,1,1);
    assert.equal(result.bestmove,'g6g7'); assert.equal(result.engine_version,'19.0.1');
    assert.equal(result.variants[0].score.type,'mate'); assert.equal(result.variants[0].score.value,1);
    const replay=validateVariation(MATE_FEN,result.variants[0].pv); const c=new Chess(replay.at(-1).fen);
    assert(c.isCheckmate()); assert.equal(replay[0].san,'Qg7#');
  });
  await test('actual three-line search yields legal PVs and finite metadata', async () => {
    const e=new ChessEngine(()=>new EngineProcess()); const r=await e.search(new Chess().fen(),1,3);
    assert.equal(r.variants.length,3);
    for(const line of r.variants) { assert(line.depth>0); assert(line.nodes>0); assert(line.time_ms>=0); assert(line.pv.length>0); validateVariation(r.fen,line.pv); }
  });
  await test('actual search cancellation releases worker and next search recovers', async () => {
    const e=new ChessEngine(()=>new EngineProcess()); let cancelled=false;
    const pending=e.search(new Chess().fen(),10,1,()=>{if(!cancelled){cancelled=true;e.cancel();}});
    await assert.rejects(pending,error=>error.code==='cancelled');
    assert.equal(e.active,null);
    assert.equal((await e.search(MATE_FEN,1,1)).bestmove,'g6g7');
  });
  await test('worker failure releases state and next real worker recovers', async () => {
    let failFirst=true;
    const e=new ChessEngine(()=>{
      if(failFirst){failFirst=false; const w={postMessage(){queueMicrotask(()=>w.onerror({preventDefault(){}}));},terminate(){}};return w;}
      return new EngineProcess();
    });
    await assert.rejects(e.search(MATE_FEN,1,1),error=>error.code==='engine_failed');
    assert.equal(e.active,null); assert.equal((await e.search(MATE_FEN,1,1)).bestmove,'g6g7');
  });
  console.log(JSON.stringify({node:process.version,tests:records.length,records},null,2));
} finally { for(const p of started) p.terminate(); }
