/** Derived from zhu1090093659/dsh-web dsh-git-graph, Apache-2.0.
 * CHANGED 2026-10-23: retain read-only argv only; append HEAD so detached
 * commits remain visible. No switch/worktree-add/remove/branch-delete API. */
export const forEachRefArgv = () => ['for-each-ref','refs/heads','--format=%(refname:short)%00%(HEAD)%00%(objectname)'];
export const worktreeListArgv = () => ['worktree','list','--porcelain'];
export const graphLogArgv = limit => ['log','--branches','--tags','--remotes','HEAD','--topo-order','--parents','--format=%H%x00%P%x00%an%x00%at%x00%D%x00%s%x1e','--max-count',String(limit)];
