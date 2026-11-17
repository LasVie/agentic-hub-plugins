import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Chess } from '../offline-chess-analysis-workbench/vendor/chess/chess.js';
import { DEFAULT_POSITION, MATE_FEN, EXAMPLE_PGN, parsePosition, parseInfo, validateVariation, positionStatus, formatScore } from '../offline-chess-analysis-workbench/web/model.js';
import { ChessEngine } from '../offline-chess-analysis-workbench/web/engine.js';
import { boardSVG, squareOrder, pieceSVG } from '../offline-chess-analysis-workbench/web/board.js';

test('FEN parsing requires six fields and preserves valid standard special-move positions', () => {
  assert.equal(parsePosition('fen',DEFAULT_POSITION).moves().length,20);
  assert.throws(() => parsePosition('fen','8/8/8/8/8/8/8/8 w - -'),/六个字段/);
  assert.throws(() => parsePosition('fen','8/8/8/8/8/8/4k3/4K3 w - - 0 1'),error=>error.code==='adjacent_kings');
  assert.throws(() => parsePosition('fen','4k3/8/8/8/8/8/4R3/4K3 w - - 0 1'),error=>error.code==='inactive_king_in_check');
  assert.throws(() => parsePosition('fen','4k3/8/8/8/8/8/8/4K3 w K - 0 1'),error=>error.code==='invalid_castling');
  assert.throws(() => parsePosition('fen','4k3/8/8/8/8/8/8/4K3 w - e6 0 1'),error=>error.code==='invalid_en_passant');
  assert.throws(() => parsePosition('fen','4k3/8/8/8/8/8/8/4K3 w - - 0 100001'),error=>error.code==='invalid_fen');
  const castle = parsePosition('fen','r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');
  assert.ok(castle.moves().includes('O-O')); assert.ok(castle.moves().includes('O-O-O'));
  const ep = parsePosition('fen','4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2');
  assert.equal(ep.move('exd6').isEnPassant(),true);
  const promotion = parsePosition('fen','7k/P7/8/8/8/8/8/7K w - - 0 1');
  promotion.move({from:'a7',to:'a8',promotion:'n'}); assert.equal(promotion.get('a8').type,'n');
});

test('PGN is strict, Unicode safe, byte bounded and rejects bad SetUp', () => {
  assert.equal(parsePosition('pgn',EXAMPLE_PGN).history().length,6);
  assert.throws(() => parsePosition('pgn','1. e4 e5 2. e2e5 *'),error=>error.code==='invalid_pgn');
  assert.throws(() => parsePosition('pgn','[Event "'+ '中'.repeat(22000)+'"]'),error=>error.code==='input_too_large');
  assert.throws(() => parsePosition('pgn','[SetUp "1"]\n[FEN "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1"]\n\n*'),error=>error.code==='inactive_king_in_check');
});

test('PV rule-checks each actual move, terminal mate and explicit length rejection', () => {
  const pv=validateVariation(MATE_FEN,['g6g7']); assert.equal(pv[0].san,'Qg7#');
  assert.equal(positionStatus(new Chess(pv[0].fen)),'黑方被将死');
  assert.throws(()=>validateVariation(DEFAULT_POSITION,['e2e5']),error=>error.code==='illegal_engine_move');
  assert.throws(()=>validateVariation(DEFAULT_POSITION,['e2e4','e7e5','bad']),error=>error.code==='invalid_engine_move');
  assert.throws(()=>validateVariation(DEFAULT_POSITION,Array(129).fill('e2e4')),error=>error.code==='variation_limit');
});

test('UCI score parser retains signed perspective, depth, bounds and actual moves', () => {
  assert.equal(parseInfo('info depth 10 nodes 123'),null);
  assert.deepEqual(parseInfo('info depth 12 multipv 1 score mate -3 nodes 123 time 12 pv g6g7').score,{type:'mate',value:-3,bound:null,perspective:'side_to_move'});
  assert.equal(parseInfo('info depth 5 multipv 3 score cp -45 upperbound nodes 789 time 42 pv e2e4').score.bound,'upperbound');
  assert.equal(parseInfo('info depth 5 multipv 4 score cp 0 pv e2e4'),null);
  assert.equal(formatScore({type:'mate',value:1,bound:'lowerbound'},'w'),'白方将死对方 1 步（评分下界）');
  assert.equal(formatScore({type:'cp',value:-45,bound:'upperbound'},'b'),'-0.45 兵（评分上界）');
});

class FakeWorker {
  static instances=[];
  constructor() {this.commands=[];this.stopped=false;FakeWorker.instances.push(this);}
  postMessage(command){this.commands.push(command);}
  emit(line){this.onmessage?.({data:line});}
  terminate(){this.stopped=true;}
}
const handshake = worker => {worker.emit('id name Stockfish 19 Lite');worker.emit('uciok');worker.emit('readyok');};
test('controller enforces UCI setup, only accepts legal consistent output and terminates completed worker',async()=>{
  const controller=new ChessEngine(()=>new FakeWorker());
  const pending=controller.search(MATE_FEN,1,3);const worker=FakeWorker.instances.at(-1);handshake(worker);
  assert.deepEqual(worker.commands,['uci','setoption name Hash value 32','setoption name MultiPV value 3','isready','ucinewgame',`position fen ${MATE_FEN}`,'go movetime 1000']);
  worker.emit('info depth 1 multipv 1 score mate 1 nodes 30 time 1 pv g6g7');worker.emit('bestmove g6g7');
  const result=await pending;assert.equal(result.variants[0].variation[0].san,'Qg7#');assert.equal(worker.stopped,true);assert.equal(controller.active,null);
});
test('controller rejects illegal variation, failure and cancellation, then recovers with a fresh worker',async()=>{
  const controller=new ChessEngine(()=>new FakeWorker());
  const illegal=controller.search(DEFAULT_POSITION,1,1);let worker=FakeWorker.instances.at(-1);handshake(worker);
  worker.emit('info depth 1 score cp 0 nodes 1 time 1 pv e2e5');await assert.rejects(illegal,error=>error.code==='illegal_engine_move');assert.equal(worker.stopped,true);
  const failed=controller.search(DEFAULT_POSITION,1,1);worker=FakeWorker.instances.at(-1);worker.onerror({preventDefault(){}});await assert.rejects(failed,error=>error.code==='engine_failed');
  const cancelled=controller.search(DEFAULT_POSITION,1,1);worker=FakeWorker.instances.at(-1);controller.cancel();await assert.rejects(cancelled,error=>error.code==='cancelled');assert.equal(worker.stopped,true);
  const recovered=controller.search(MATE_FEN,1,1);worker=FakeWorker.instances.at(-1);handshake(worker);worker.emit('info depth 1 score mate 1 nodes 20 time 2 pv g6g7');worker.emit('bestmove g6g7');assert.equal((await recovered).bestmove,'g6g7');
});
test('controller refuses terminal positions without starting a worker',async()=>{
  let created=false; const engine=new ChessEngine(()=>{created=true;return new FakeWorker();});
  await assert.rejects(engine.search('7k/6Q1/5K2/8/8/8/8/8 b - - 1 1',1,1),error=>error.code==='terminal_position');
  await assert.rejects(engine.search('7k/5Q2/5K2/8/8/8/8/8 b - - 1 1',1,1),error=>error.code==='terminal_position');
  assert.equal(created,false);
});
test('real initialization watchdog expires a nonresponsive injected fake worker and permits fresh-worker recovery',async()=>{
  // This exercises the unchanged production 10-second watchdog with real time.
  // The worker is deliberately nonresponsive; it is not an actual engine hang.
  const controller=new ChessEngine(()=>new FakeWorker());
  const pending=controller.search(MATE_FEN,1,1);const hung=FakeWorker.instances.at(-1);
  const began=performance.now();
  await assert.rejects(pending,error=>error.code==='engine_timeout');
  assert.ok(performance.now()-began>=9900,'production initialization watchdog must not fire early');
  assert.equal(hung.stopped,true);assert.equal(hung.onmessage,null);assert.equal(controller.active,null);
  const recovered=controller.search(MATE_FEN,1,1);const fresh=FakeWorker.instances.at(-1);
  assert.notEqual(fresh,hung);handshake(fresh);
  fresh.emit('info depth 1 score mate 1 nodes 20 time 2 pv g6g7');fresh.emit('bestmove g6g7');
  assert.equal((await recovered).bestmove,'g6g7');assert.equal(fresh.stopped,true);
});
test('board SVG is self-contained, has original vector pieces and supports flipped coordinates',()=>{
  const game=parsePosition('fen',DEFAULT_POSITION),svg=boardSVG(game);
  assert.equal((svg.match(/xmlns=/g)??[]).length,1);assert.ok(!/<script|<foreignObject|https?:\/\/(?!www\.w3\.org)/.test(svg));
  assert.equal((svg.match(/<g transform=/g)??[]).length,32);assert.ok(svg.includes('<title>当前国际象棋局面</title>'));
  assert.equal(squareOrder(false)[0],'a8');assert.equal(squareOrder(true)[0],'h1');assert.equal(pieceSVG({type:'<script>',color:'w'}),'');
});
