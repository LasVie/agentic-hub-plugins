# math-olympiad 1.0.0 test report

Task `AH-20261027-math-olympiad`; candidate `CAND-ANT-038`; owner Vannes Wijaya. Date 2026-10-27.
Environment: WSL2 Linux 6.18, Python 3.14, PyYAML 6.0.3; no LaTeX installed; no JiuwenSwarm/openJiuwen
host libraries installed and no local host running, so host import/load is left to manual testing.

## Packages

| Archive | Use | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `releases/agent-plugin/math-olympiad/1.0.0/math-olympiad-1.0.0.zip` | Repository / Hub format (plugin.yaml + inner payload) | `f401d739852e5549445d0929154a9aaca53958e46ae752a66521c15afcff52f0` | 92319 |
| `dist/math-olympiad-1.0.0-native.zip` (local test only, not committed) | Host “Create from file” import (manifest at root) | `4bade8c6a6eb65de21d6ecedcf2c45d6ec88a2d21b9e2767a54dd550397d2872` | 44335 |

The 14 payload files are byte-identical between the two archives (checked by script).

## Automated checks

| Command | Result |
| --- | --- |
| `python tools/asset_release.py check plugins/math-olympiad` | format_ok |
| `python tests/math_olympiad_package_test.py <zip>` | 69 PASS lines, ALL PASS (re-counted after fix) |
| `python -m unittest discover -s tests` | 404 run, OK (66 skipped) — before this asset's release existed |
| `python tools/asset_release.py check-repo` | run after final pack (see RELEASE section of the PR) |

`math_olympiad_package_test.py` extracts the ZIP and verifies: single outer dir with only `plugin.yaml`
and payload; exact 14-file inventory; manifest identity/version, no forbidden keys, Chinese display
name, declared skill exists; both LICENSE copies match the upstream hash; UTF-8 without BOM and
Chinese content in every text file; Apache change notice at the top of all 9 adapted files; skill
frontmatter; every `references/` / `scripts/` path cited in SKILL.md resolves; key Chinese
instructions present (Chinese default, abstention, staged-verification disclosure, no web, 4-HOLDS
threshold); no Claude-only tool names; bash syntax; `check_latex.sh` exits 1 without xelatex;
`compile_pdf.sh` prints Chinese errors, exits 2 on missing args, and writes a complete `ctexart`
document containing the Chinese body.

## Model-level trial (AI self-test, not user testing)

A separate Claude agent with no other context extracted the draft ZIP, followed SKILL.md as its
instructions without tools, and handled two Chinese requests (快速 preset):

1. 求解 “a+b+c=3 ⇒ a²+b²+c² ≥ 3”: 已证明 via Σ(a−1)² ≥ 0, cross-checked by Cauchy–Schwarz;
   all format sections present; disclosed “由同一智能体分阶段验证”.
2. 检查 “n²+n+41 恒为质数” 的枚举“证明”: HOLE FOUND, early exit after 2 rounds; counterexample
   n=40 → 1681 = 41²; patterns #17 and refutation categories 1/3/7 used.

Issues it reported, and fixes applied before the final package:
- 快速 preset (3 rounds) could never reach the 4-HOLDS threshold → explicit 3/3 rule added.
- CORRECT/INCORRECT/GAP vs HOLDS mapping ambiguous for GAP → explicit rule added.
- SKILL.md pattern table incomplete → pointer to full 13-pattern list added.
- Reference prompts assume blind verifiers → single-agent reading rule added.
- Step 6d with no code tools unclear → reasoning-only deep mode stated.
- Final format lacked “proof wrong / claim false” outcomes → four-way conclusion added.
- Dangling `shared/verifier_patterns_source.md` → marked as upstream internal, not shipped.

The trial ran on the pre-fix draft; the final package was not re-trialled by model. It is evidence
of instruction usability only — not of host loading, nor of mathematical reliability.

## Not tested / known limitations

- Real host import, skill discovery and chat run: passed in manual test round 3 (below).
- PDF compilation with xelatex + ctex: passed in manual test round 3 on the tester's host (`/usr/bin/xelatex`); not exercised by the automated package test, which only checks script behaviour without xelatex.
- The host UI does not display plugin versions; the tested build is identified by ZIP SHA-256 and install time.
- Single-agent procedural isolation is weaker than upstream subagent isolation (disclosed in package).
- Mathematical correctness depends on the host model; no success-rate claim is made.

## Manual test round 1 (2026-10-27, Vannes Wijaya) — fixed, retest required

- Host: local JiuwenSwarm (`make start-debug`), native ZIP `83675ac2…e1ec` imported via Create from file.
- Solve prompt: the model loaded SKILL.md from
  `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/math-olympiad/skills/math-olympiad/SKILL.md`
  but then called `read_file` on `~/.jiuwenswarm/agent/workspace/skills/math-olympiad/references/attempt_agent.md`
  (File not found). SKILL.md did not state that `references/` / `scripts/` are relative to its own directory.
- Fix: SKILL.md now states paths are relative to the SKILL.md directory, derives the base from the loaded path,
  and continues without retrying if a reference still cannot be read. The package test asserts this rule.
- Both ZIPs rebuilt (hashes above); version unchanged at 1.0.0 because 1.0.0 was never delivered.
  The earlier hashes are superseded and must not be used.

## Manual test round 2 (2026-10-27, Vannes Wijaya) — fixed, retest required

- Package: native ZIP `019c00d1…a1ca` (round-1 fix). First run with host `preferred_language: en`: replies came back in
  English, so the Chinese edition was not exercised; host switched to `preferred_language: zh` and steps re-run.
- In Chinese the UI showed 奥数竞赛证明与对抗验证 and the replies were in Chinese; step 3 found the n=40 → 41² counterexample;
  step 4 identified the twin-prime conjecture as open. But step 2 again called `read_file` on
  `~/.jiuwenswarm/agent/workspace/skills/math-olympiad/references/*.md` (4 × File not found) and continued without references.
- Cause: the host system prompt states “已安装的 Skill 根目录：…/workspace/skills/{skill_name}”, which the model applied to
  this plugin-bundled skill, overriding the relative-path rule.
- Fix: SKILL.md now says the skill is not under that root, gives the plugin_packages location pattern and a full
  worked example path. Package test asserts it. Both ZIPs rebuilt (hashes above); earlier hashes superseded.
- Round-2 screenshots are kept as history only; they do not show the current package.

## Manual test round 3 (2026-10-27, Vannes Wijaya) — passed

- Host: local JiuwenSwarm (`make start-debug`), `preferred_language: zh`, model deepseek/deepseek-v4-pro, single-agent mode.
  Native ZIP `4bade8c6a6eb65de21d6ecedcf2c45d6ec88a2d21b9e2767a54dd550397d2872` imported (installed 11:23).
- Reference loading: host log shows all 6 `references/*.md` read from
  `…/plugins/plugin_packages/local/math-olympiad/skills/math-olympiad/` (6 reads each, 11:24–11:27); no File not found in this round.
- Step 2 (a²+b²+c² ≥ 3): Chinese staged workflow; 5/5 HOLDS, 确认; same-agent staged disclosure; `check_latex.sh` returned 0 and
  `compile_pdf.sh` produced a Chinese `proof.pdf` (ctexart) shown in the host artifact panel.
- Step 3 (n²+n+41): 证明有漏洞，且命题本身不成立; counterexamples n=40 (41²) and n=41 (41×43); early exit after 2 HOLE FOUND.
- Step 4 (twin primes): identified as open problem; no proof claimed; honest abstention with verification note.
- Plugin list and detail page show 奥数竞赛证明与对抗验证 with Chinese tags, description and quick prompts.
- Screenshots: `evidence/user-test-1.0.0-01.png` … `-08.png`, mapping in `evidence/originals.json`.
- User confirmation: see USER_TEST_CONFIRMATION.md.
