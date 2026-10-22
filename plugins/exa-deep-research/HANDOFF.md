# Local test handoff

Task: AH-20261022-exa-deep-research; candidate: CAND-CLD-017.
Version: 1.0.0; branch: port/exa-deep-research-20261022.

For native JiuwenSwarm/WorkSwarm local Plugin import, use:
`.research/test-packages/exa-deep-research-1.0.0-workswarm.zip`

SHA-256: `589ebbf999a42f0c15e9d98afe47b11d1b4747211c82becebca0ea1cf7f7f548`

Canonical repository marketplace ZIP:
`releases/agent-plugin/exa-deep-research/1.0.0/exa-deep-research-1.0.0.zip`

SHA-256: `f61bc3d94d3fdb48db5e1f41139cd9450c9f5902cfc992ccf730ea32b27cc8ac`

Both contain exactly the same native runtime files. Follow MANUAL_TESTING.md.
Python 3.11+ and requirements.txt must be available in the native host. Search
and fetch use Exa's anonymous quota; optional managed research needs EXA_API_KEY
and explicit authorization. The original Hermes MCP trial is separate.

After testing, confirm whether this exact package/version passed and supply
original screenshots of the version and key operations. AGENTS.md requires
current-package user test completion before push or a delivery PR. Ownership
remains Unassigned because no contributor identity was supplied. Song Haoran
handles any later Hub submission personally.

The shared tracker was updated and read back on 2026-10-22: candidate
CAND-CLD-017 remains Planned with Verified Reusable license review; task
AH-20261022-exa-deep-research is Ready for Testing. Progress report
RPT-20261022-exa-deep-research-ready records the tests, dependencies and limits.
The report is inside the native table and its linked filter. PR, screenshot
and completion fields remain blank; Project Lead acceptance is pending.

Validation: nine port regressions and the real extracted-package host/live
service smoke test passed. Authenticated paid research remains untested.
The supported repository suite had 31 passes and 26 dependency-based skips;
two existing symlink cases require unavailable Windows privileges. See
TEST_REPORT.md for commands and details.
