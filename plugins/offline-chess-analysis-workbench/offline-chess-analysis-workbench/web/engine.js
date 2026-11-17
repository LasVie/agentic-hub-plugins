import { InputError, parseInfo, parsePosition, validateVariation } from './model.js';

export class ChessEngine {
  constructor(workerFactory = () => new Worker(new URL('../vendor/stockfish/stockfish-19-lite-single.js', import.meta.url))) {
    this.workerFactory = workerFactory;
    this.active = null;
  }
  cancel() {
    if (!this.active) return;
    this.active.fail(new InputError('cancelled', '搜索已取消；没有保留未完成结果。'));
  }
  search(fen, seconds, multipv, onProgress = () => {}) {
    const position = parsePosition('fen', fen);
    if (position.isGameOver()) return Promise.reject(new InputError('terminal_position', '局面已结束；不启动引擎搜索，也不生成候选线。'));
    if (!Number.isInteger(seconds) || seconds < 1 || seconds > 10 || !Number.isInteger(multipv) || multipv < 1 || multipv > 3) return Promise.reject(new InputError('invalid_limit', '搜索时长须为 1–10 秒，候选线须为 1–3 条。'));
    this.cancel();
    return new Promise((resolve, reject) => {
      let worker, timer, phase = 'uci', name = '', settled = false;
      const lines = new Map();
      const finish = (error, result) => {
        if (settled) return;
        settled = true; clearTimeout(timer);
        if (worker) { worker.onmessage = null; worker.onerror = null; worker.onmessageerror = null; worker.terminate(); }
        if (this.active?.fail === fail) this.active = null;
        error ? reject(error) : resolve(result);
      };
      const fail = error => finish(error);
      this.active = { fail };
      const timeout = milliseconds => {
        clearTimeout(timer);
        timer = setTimeout(() => fail(new InputError('engine_timeout', '引擎未在限定时间内完成，已释放工作线程；请重试。')), milliseconds);
      };
      try {
        worker = this.workerFactory();
        worker.onerror = event => { event.preventDefault?.(); fail(new InputError('engine_failed', '引擎工作线程失败，已释放；可重新运行。')); };
        worker.onmessageerror = () => fail(new InputError('engine_failed', '无法读取引擎消息；请重新运行。'));
        worker.onmessage = event => {
          if (settled || typeof event.data !== 'string') return;
          for (const line of event.data.split(/\r?\n/)) {
            if (settled) break;
            if (/CRITICALERROR|Aborted\(|RuntimeError|^Error:/.test(line)) { fail(new InputError('engine_failed', '引擎报告运行错误；结果未保留，请检查局面后重试。')); break; }
            if (line.startsWith('id name ')) name = line.slice(8);
            if (line === 'uciok' && phase === 'uci') {
              if (!name.startsWith('Stockfish 19')) { fail(new InputError('engine_version', '引擎版本与打包版本不符；请重新安装当前插件。')); break; }
              phase = 'ready';
              worker.postMessage('setoption name Hash value 32');
              worker.postMessage(`setoption name MultiPV value ${multipv}`);
              worker.postMessage('isready');
            } else if (line === 'readyok' && phase === 'ready') {
              phase = 'search'; timeout(seconds * 1000 + 1800);
              worker.postMessage('ucinewgame');
              worker.postMessage(`position fen ${fen}`);
              worker.postMessage(`go movetime ${seconds * 1000}`);
            } else if (phase === 'search') {
              const info = parseInfo(line);
              if (info && info.multipv <= multipv) {
                try {
                  info.variation = validateVariation(fen, info.pv);
                  lines.set(info.multipv, info);
                  onProgress({ name, depth: info.depth, nodes: info.nodes, time_ms: info.time_ms });
                } catch (error) { fail(error); break; }
              }
              if (line.startsWith('bestmove ')) {
                const bestmove = line.split(/\s+/)[1];
                try {
                  validateVariation(fen, [bestmove]);
                  const variants = [...lines.values()].sort((a,b) => a.multipv - b.multipv);
                  if (!variants.length || variants[0].pv[0] !== bestmove) throw new InputError('incomplete_result', '引擎没有返回与最佳着法一致的完整候选线；请重新运行。');
                  finish(null, { engine_name: name, engine_version: '19.0.1', variant: 'lite-single', fen, side_to_move: fen.split(' ')[1], limits: { movetime_ms: seconds * 1000, hash_mib: 32, threads: 1, multipv }, bestmove, variants });
                } catch(error) { fail(error); }
              }
            }
          }
        };
        timeout(10000);
        worker.postMessage('uci');
      } catch { fail(new InputError('worker_unavailable', '浏览器无法创建本地引擎工作线程；请使用支持 WebAssembly 的浏览器。')); }
    });
  }
}
