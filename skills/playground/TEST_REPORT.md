# Final delegated WorkSwarm test: playground 1.0.2

Date: 2026-10-22 (Asia/Singapore). Task `AH-20261022-playground`; candidate `CAND-ANT-014`; unchanged responsible member **Nguyen Trung Dung**.

Final package: marketplace SHA-256 `34ab10d8a3739412b6fb1b9a7a946ea024b27ed0809c7fc776988bbf80c59997`; native import SHA-256 `9bcfe4d8a3a09428f32afe164bdf7742e32765563977e1dc9bd2f6463dc62187`. Both transports, source, final extraction and actually installed payload match file for file and byte for byte.

Authority: The human user in the current conversation explicitly asked the agent to finish import and prompt testing in the user-open local WorkSwarm, preserve original screenshots, and update the existing content through a PR if successful, while keeping responsible member names unchanged. This authorizes delegated AI-operated host tests and conditional PR preparation; it is not a statement that the human personally performed the tests.

Environment: the user-open **WorkSwarm 0.2.7**, configured **Deepseek V4 Flash**, macOS. The controlling AI operated the real UI and submitted real Chinese prompts; tool results were not replaced by fabricated output. Recorded at 2026-10-22T17:31:24+08:00.

Delivery repository base `49acfa795cb6964f06a16cd30594efb7055272d0` (latest merged Smart Download baseline); the actual host tests used unchanged package bytes prepared from `e0f6b866649e82cbf37fbd082db9891ca977ae8e`. Full latest AGENTS.md was read and verified as Git blob `78a5b51285e322b38d81381d47aa9eef672bb62f`.

## Actual results

| Flow | Observed verification | Result |
| --- | --- | --- |
| Actual Skill import | Imported the native 1.0.2 Skill through the user-open WorkSwarm UI, selected it in the host conversation and independently verified all 10 installed files against final source/native/marketplace bytes. | Passed |
| Real generation | The host read the actual Chinese Skill/template and generated a standalone Chinese product-card HTML file in the bounded fixture directory, with inline CSS/JS and no external resource dependency. | Passed |
| Real browser interaction | The controlling agent opened the actual generated HTML in a browser, clicked 活力醒目, adjusted the radius slider by keyboard to 13, and observed linked preview/prompt updates. | Passed |
| Clipboard success | The browser copy action displayed 已复制. The real UI screenshot and accessibility snapshot were retained. | Passed |

## Final regression and package checks

57 repository unit tests passed with actual openJiuwen/Node.js and zero skipped. The independent package audit passed for exact source/native/marketplace/repository-release/extracted contents, pinned source records, unchanged original license bytes and publisher/manifest author identities. The actual openJiuwen loader passed eight checks on the final extracted Learning package. The initial final-package audit snapshot checked 7 source assets and 26 retained release ZIPs; an intermediate repository check passed for 8 source assets and 27 retained ZIPs. Other explicitly delegated repository work may proceed concurrently; the parent agent runs the final full-repository check in the fresh PR worktree. These six-asset results do not assert the completion state of that parallel work. These automated checks supplement the actual delegated host run; they are not labelled as human-performed testing.

Evidence is retained under `workswarm-host-tests-20261022/`: `final-audit/final-package-audit.json`, `final-audit/final-unit-suite.log`, `final-audit/final-learning-loader.json`, and `final-audit/final-repo-validation.log`. Each asset also has `installed-payload-verification.json`, real UI accessibility snapshots and original PNG files.

## Original screenshots and scope

- `playground/browser-interaction.png` — version 1.0.2; SHA-256 `c434c8e67375c736bad890893de77fa05b20bee91e50de8bbed0540a6f100e18`; Original actual host/browser screenshot.
- `playground/import-list.png` — version 1.0.2; SHA-256 `9d5159b63b21d375aa39cf5304d41dfe3e3cabfd76d9a7df8f80742aee5dde1f`; Original actual host/browser screenshot.
- `playground/import-selected.png` — version 1.0.2; SHA-256 `5d6cc833c79a908cf601ef8841b0093147b3d6811728407d61f800f07d6a13fe`; Original actual host/browser screenshot.
- `playground/prompt-result.png` — version 1.0.2; SHA-256 `799062df96cd79f446435c077b229f1063e0c35e340e838aeb7b9893900dfa34`; Original actual host/browser screenshot.

The final-version screenshots are local original evidence pending attachment to a real PR discussion. No PR image URL or evidence permalink has been invented. Screenshot tracker fields must receive only verified PR evidence links after upload; existing historical evidence remains valid for its stated version.

## Limits and delivery state

- Clipboard-denied fallback received static source review only; clipboard rejection was not forced in the browser. Narrow-screen and every keyboard interaction were not exhaustively exercised in this run.
- The generated HTML is test output. These checks do not establish all six possible workflows or every future model-generated page.

The delegated test scope passed. Current status is `Awaiting Acceptance` with the delivery PR pending creation. `current_version_user_test_confirmation` remains null because the agent ran the tests under explicit human delegation; the separate `delegated_ai_test_confirmation` records that authority and the exact tested hashes. No current-version PR merge, Hub submission, Hub approval/publication, human-performed test completion or final Project Lead acceptance is claimed. Owners, stable IDs and historical PR/evidence records are preserved.

## Historical reports (preserved; prior versions and pending snapshots are not current results)

# WorkSwarm Chinese runtime test candidate playground 1.0.2

2026-10-22. Final native import/prompt tests delegated by the Project Lead; results pending. Previous version 1.0.1 and prior reports/hashes are historical only. No current-version user-performed testing, merge or Hub submission is claimed.

## Historical reports

# Chinese package verification: playground 1.0.1

Date: 2026-10-22. Current package is a local Build candidate, not merged or submitted. All current-version user testing and screenshot confirmation are pending. Original owner, stable task/candidate IDs, prior PR #10 and historical evidence remain intact. Earlier confirmation below covers only its original bytes.

Source validation: 50 repository unit/functional tests passed with actual openJiuwen SDK and Node.js (zero skipped); file encoding and LaTeX real Tool API integrations passed. Final archive source/market/native/extracted equality and original-license checks passed; details are in LOCALIZATION_TEST.json and package-verification.json. Six Plugins passed actual isolated import/install/load/Chinese-card/uninstall checks; Playground passed actual relocated Skill resolver checks through a temporary test harness (not target-host Skill import). No paid model call is made. Crossref fill integration uses a deterministic mock, not a live service assertion.

Localization covers Chinese marketplace/native display fields, tags, README and user instructions. Playground SKILL body is Chinese; its six pinned templates remain unchanged. Original license texts, technical IDs and functional algorithms are preserved; MCP generator changes only its version literal and Skill version references.

All three provenance/template-reference tests passed; six templates remain byte-identical. The current browser fixture rerun could not launch because Chromium is absent. It is recorded as unavailable, not passed. Chinese SKILL generation with the user model and target-host import remain pending.

## Historical report (original version only)

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
