import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const payload = path.resolve(process.argv[2]);
const root = path.resolve(process.argv[3]);
const output = path.resolve(process.argv[4]);
const state = await fs.mkdtemp('/private/tmp/change-verification-real-source-');
process.env.CHANGE_VERIFICATION_STATE_DIR = state;
const { analyze } = await import(pathToFileURL(path.join(payload, 'runtime/engine.mjs')));
const { git } = await import(pathToFileURL(path.join(payload, 'runtime/git.mjs')));
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
try {
  const before = await git(root, ['status', '--porcelain']);
  const config = await fs.readFile(path.join(root, '.git/config'));
  const report = await analyze({ root, base: '24a6540', head: 'b4f3c8e3be2b756ad9966463a65331e69fdee5f8', depth: 2 });
  assert.equal(report.base.slice(0, 7), '24a6540');
  assert(report.changes.length > 0);
  assert(report.scan.head.indexed_count > 100);
  assert(report.items.every(item => item.status === 'pending'));
  assert.deepEqual(await git(root, ['status', '--porcelain']), before);
  assert.deepEqual(await fs.readFile(path.join(root, '.git/config')), config);
  const result = { pinned_head: report.head, base: report.base, changed: report.changes,
    scan: report.scan, direct: report.items.filter(item => item.kind === 'direct').length,
    ripple: report.items.filter(item => item.kind === 'ripple').length, all_pending: true,
    config_sha256_before_and_after: hash(config), worktree_status_sha256_before_and_after: hash(before),
    statement: '只读分析已下载上游的两个实际 release 提交；没有执行项目功能，不是业务功能回归通过。' };
  await fs.writeFile(output, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
} finally { await fs.rm(state, { recursive: true, force: true }); }
