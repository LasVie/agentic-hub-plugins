# Playground 1.0.0 test report

Date: 2026-10-22 (Asia/Singapore). Candidate: `CAND-ANT-014`.
Task: `AH-20261022-playground`. Owner: Nguyen Trung Dung.

## Environment and scope

- Windows; Python 3.12.6; PyYAML 6.0.3.
- Node.js v24.19.0; Playwright 1.62.1; installed Google Chrome 155.0.8059.85, running headless in an isolated test context.
- Source pinned to `anthropics/claude-plugins-official@d4226d062928f8d9505dbdeadd10217d23361052`.
- The ported skill and matching templates were read in this Codex session. The design, data-explorer, and document-critique workflows were followed to produce the three local HTML fixtures under `tests/fixtures/playground/`. Tests operate on those real outputs. This is not a claim that a separate Codex/Hermes/Hub installation discovered or invoked the skill automatically.
- No Claude Code process, upstream installation script, external model call, remote data service, or repository research sample ZIP was executed for these tests.

## Functional browser tests: passed

Command, using the task host's installed Playwright package and browser:

```powershell
$env:PLAYGROUND_PLAYWRIGHT_MODULE = '<installed-playwright-package-directory>'
$env:PLAYGROUND_BROWSER_CHANNEL = 'chrome'
node tests/playground_browser_smoke.mjs
```

An installed Playwright package is a development/test dependency only. The generated pages and shipped Skill do not require Node.js or Playwright. Without `PLAYGROUND_BROWSER_CHANNEL`, the runner uses Playwright's own installed Chromium.

The final browser run completed at `2026-10-22T04:13:07.056Z` with 14 passing checks, no page JavaScript errors, and no external network requests:

1. Design defaults render correctly and produce a contextual initial prompt.
2. A radius change immediately updates computed preview styles and prompt text.
3. Quiet, Bright, and Compact presets synchronize the controls and preview.
4. HTML-looking product input remains literal text and cannot create an image/event handler.
5. Clipboard success passes the exact displayed prompt to a stubbed clipboard API and displays success afterward.
6. At 390px width, the design page has no horizontal overflow and keyboard changes work.
7. The design page works over a `file:` URL with networking offline.
8. Clipboard rejection selects the prompt for manual copying and never displays success.
9. SQL filters/presets update the query and a self-contained request with schema context.
10. An invalid minimum total disables copying and removes misleading output; resetting restores a valid query.
11. HTML-looking source in the document critique remains literal and cannot execute.
12. Approved suggestions appear as changes; rejected suggestions appear only under an explicit do-not-apply context heading.
13. Changing document filters preserves decisions and literal user comments.
14. Across the three workflows, no external resources or browser JavaScript errors occur.

Clipboard success/rejection were tested using API stubs so the user's OS clipboard was not overwritten. Actual clipboard permission behavior remains a manual check in the user's chosen browser. A successful syntax or source check alone was not treated as a rendered-page test.

The browser-results JSON is retained verbatim in `FUNCTIONAL_TEST.log`. Screenshots of the design desktop/mobile views and document review mobile view were visually inspected. They show readable controls, prompt text, and no clipped page content. These are automated test artifacts, not user test screenshots or Hub submission evidence.

## Source and repository checks

- `python tools/asset_release.py audit-upstream .research/upstream`: found identical root/plugin Apache-2.0 evidence; manual content review is in `SOURCE_REVIEW.md`.
- `python tools/asset_release.py check skills/playground`: passed.
- Three new `test_playground.py` tests passed: pinned template/payload hashes, skill-relative template references, and license evidence/modification notices.
- `python -X utf8 -m unittest discover -s tests -v`: 21 passed, 2 existing tests errored before their assertions because this Windows process cannot create symlinks (`WinError 1314`). They are `test_payload_symlinks_are_rejected` and `test_generation_preserves_existing_files_and_rejects_symlinks`. No production code or checked-in test was weakened to bypass them.
- A local, untracked runner `.research/run_tests_windows.py` explicitly skipped those two unavailable privilege checks: 23 tests total, 21 passed, 2 skipped. The unmodified full suite still requires a symlink-capable environment before claiming full CI parity. WSL is not installed on this host.
- The initial default-codepage run also encountered one existing UTF-8 decoding error. Running Python with `-X utf8` resolved it.
- `git diff --check`: passed before final packaging.
- The fresh Windows clone initially converted existing tracked text files to CRLF, causing the existing MCP asset's license hash check to fail. Only checkout line-ending differences were restored to the exact HEAD blob bytes in this separate clone; no existing tracked content was changed. `python tools/asset_release.py check-repo` then passed for both source assets and both release ZIPs.

## Packaging and final archive review

The package uses `runtime.type: skill`, one outer `plugin.yaml`, and an inner `playground/` payload containing the skill, six templates, local installation guide, notices, and complete upstream license. Test fixtures, browser tools, tracker records, and downloaded research files are outside the runtime payload.

Final packaging, archive extraction, license/notice checks, per-file hash comparisons, deterministic-byte verification, and repository package validation are recorded in `RELEASE_TEST.log`. `artifact.json` records the exact ZIP SHA-256, payload hashes, and source-review/test-report hashes. Do not claim a successful release check without the corresponding final log.

Final archive review passed: 10 payload files, 54,356 ZIP bytes, all extracted payload hashes matched, all six templates matched their pinned upstream bytes, the complete license matched its evidence hash, the modified skill's change notice was present, no development files were included, and rebuilding produced identical ZIP bytes. ZIP SHA-256: `bb296a3e6cfb809952bf524b6c1c86543481c5ee4b9729089b3899ca6841a69c`.

## Outstanding user/host checks

- Install the inner skill in the intended Hub/JiuwenSwarm, Codex, or Hermes environment and generate a fresh page with the model used there.
- Exercise the six workflows as relevant to the intended use; only the three representative workflows above were generated and browser-tested here.
- Check the real clipboard in the chosen browser, particularly local-file, remote, or restricted contexts.
- Capture a real user test screenshot showing version and key behavior, and report any blocking issues. No user test-completion confirmation has been recorded.
- Tracker registration and progress updates are pending because no write connector or browser route is available. No online claim, Ready for Testing status, task completion, project-lead acceptance, merged PR, or Hub submission is asserted by this local report.
