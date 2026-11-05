import { calculate, LIMITS } from './core.mjs';

let response;
try {
  const chunks = []; let count = 0;
  for await (const chunk of process.stdin) {
    count += chunk.length;
    if (count > LIMITS.inputBytes) throw new Error('size');
    chunks.push(chunk);
  }
  const text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
  response = await calculate(JSON.parse(text));
} catch {
  response = { ok: false, error: '输入必须是有效 UTF-8 JSON，且不超过 2 MiB。' };
}
process.stdout.write(`${JSON.stringify(response)}\n`);
