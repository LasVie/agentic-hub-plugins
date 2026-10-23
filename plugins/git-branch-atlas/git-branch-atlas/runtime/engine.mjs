/**
 * Apache-2.0 subset port from zhu1090093659/dsh-web packages/dsh-git-graph.
 * CHANGED 2026-10-23: native bounded read-only runner, revisioned snapshots,
 * canonical workspace restriction and ahead/behind comparison. No Git mutations.
 * Upstream parseGraph/computeLanes are bundled unchanged in vendor/types.ts.
 */
import { parseGraph, computeLanes, parseBranches, parseWorktrees } from '../vendor/types.ts';
import { graphLogArgv, forEachRefArgv, worktreeListArgv } from '../vendor/readonly-argv.mjs';
import { run, object, fail, within, integer, text, now } from './common.mjs';
function git(root, args, allowFail = false) {
  const r = run('/usr/bin/git', ['--no-optional-locks', '--no-pager', '-c', 'core.fsmonitor=false', ...args], root, 10000);
  if (!r.ok && !allowFail) fail('Git 只读命令未成功；请确认仓库状态、权限与本地对象是否齐全。未联网补取对象。');
  return r;
}
function repo(ctx, p) {
  const target = within(ctx.root, p.repo_dir || '.', true);
  const root = git(target, ['rev-parse', '--show-toplevel']).stdout.trim();
  if (root !== ctx.root && !root.startsWith(ctx.root + '/')) fail('Git 仓库根目录越出绑定工作区。');
  return root;
}
function resolve(root, value) {
  const ref = text(value, 'Git 引用', 200);
  if (ref.startsWith('-') || /[\x00-\x20]/.test(ref)) fail('Git 引用不能为选项或包含空白字符。');
  const r = git(root, ['rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], true);
  const oid = r.stdout.trim(); if (!r.ok || !/^[a-f0-9]{40,64}$/.test(oid)) fail('Git 引用不能解析为已有本地提交。');
  return oid;
}
export function execute(ctx, action, p) {
  if (!object(p)) fail('payload 须为对象。');
  if (action === 'status') return { ...ctx.read(), message: '只读分支拓扑快照；没有 checkout、fetch、blame 或提交操作。' };
  if (action === 'export_graph') return { export: ctx.read() };
  const root = repo(ctx, p);
  if (action === 'compare_branches') {
    const a = resolve(root, p.base), b = resolve(root, p.head);
    const counts = git(root, ['rev-list', '--left-right', '--count', `${a}...${b}`]).stdout.trim().split(/\s+/).map(Number);
    const merge = git(root, ['merge-base', '--all', a, b], true);
    const bases = merge.ok ? merge.stdout.trim().split('\n').filter(Boolean) : [];
    return { base_oid: a, head_oid: b, base_only: counts[0], head_only: counts[1], merge_bases: bases, related: bases.length > 0, message: bases.length ? '比较的是已存在的本地提交，不包含远端未拉取的更新。' : '两个引用没有共同祖先；不假设线性关系。' };
  }
  if (action !== 'scan') fail('操作不支持。');
  const limit = integer(p.limit ?? 80, '提交上限', 1, 200);
  const result = git(root, graphLogArgv(limit + 1), true);
  const head = git(root, ['rev-parse', '--verify', 'HEAD'], true);
  if (!result.ok && head.ok) fail('提交图读取失败；不会把错误当作空仓库。');
  const all = result.ok ? parseGraph(result.stdout) : [], commits = all.slice(0, limit);
  for (const c of commits) {
    if (!/^[a-f0-9]{40,64}$/.test(c.oid) || c.parents.some(p => !/^[a-f0-9]{40,64}$/.test(p))) fail('Git 图格式异常，已拒绝不完整数据。');
    c.subject = c.subject.replace(/[\x00-\x1f]/g, ' ').slice(0, 400); c.author = c.author.replace(/[\x00-\x1f]/g, ' ').slice(0, 120);
  }
  const branches = parseBranches(git(root, forEachRefArgv()).stdout);
  const worktrees = parseWorktrees(git(root, worktreeListArgv()).stdout);
  const snapshot = { observed_at: now(), repo: root === ctx.root ? '.' : root.slice(ctx.root.length + 1), head_oid: head.ok ? head.stdout.trim() : null, commits, lanes: computeLanes(commits), branches, worktrees, has_more: all.length > limit, limit, note: '拓扑顺序与边界外父提交保留；图形泳道为辅助视图，完整 parent OID 才是证据。只读，不拉取远端或改变工作树。' };
  ctx.mutate(p.expected_revision, s => { s.snapshot = snapshot; return {}; });
  return { revision: ctx.read().revision, snapshot, message: '分支拓扑已读取。' };
}
