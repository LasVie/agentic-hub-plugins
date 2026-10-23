# User testing confirmation: 课表校验与导出 1.0.0

Candidate `CAND-CLD-219`; task `AH-20261023-fet-timetable-audit`; explicitly assigned owner Cai Zhenze. Mapping: upstream `fet` → Chinese package **课表校验与导出** → `fet-timetable-audit`.

## Explicit current-package confirmation

The current conversation user supplied the original image and stated:

> I confirm manual testing of CAND-CLD-219 — 课表校验与导出 v1.0.0 is complete and passed. Use my attached original screenshot and proceed to Phase 3 under the latest AGENTS.md.

Recorded 2026-10-23, Asia/Singapore. The exact confirmation-message timestamp is unavailable; the screenshot displays the test conversation at 11:02–11:03. Source is this current conversation, with no invented message URL. This is explicit user confirmation of the current package, separate from automated tests and final Project Lead acceptance.

- Canonical ZIP: `releases/agent-plugin/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0.zip`; 52,504 bytes; SHA-256 `20ce4ca8188428a8d8abd957be6158f83d76337322cf70ba78c9b3ba1b80c911`.
- WorkSwarm testing ZIP: `dist/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0-workswarm.zip`; 51,390 bytes; SHA-256 `1340355e0dd10218bf0853b23f2323895661f793f3fc3bf321675e4de455cfbf`.
- All eight runtime files are byte-identical across source, canonical ZIP, native companion and installed plugin. No packaged source, metadata, wrapper or ZIP changed after testing. Subsequent confirmation/report updates are repository documentation only.
- Known blocking issues: none identified. The bounded checks and exclusions remain documented; passing supported checks is not complete FET feasibility proof.
- Linked confirmation Progress Report: `RPT-20261023-fet-timetable-audit-confirmed-100`.

## Original screenshot and corroboration

Original supplied file: `ChatGPT Image 23 Oct 2026, 11_04_39.png`; **568 × 1596 pixels**, **248,247 bytes**; SHA-256 `f7a9fadae503f9c88c8c4d1e4938eb42133954199205c16f3565329d1206f301`. Preserve these exact bytes for attachment to the GitHub delivery PR; do not crop, resize, recompress or put the image in the runtime ZIP.

The image is readable and identifies the Chinese plugin, actual tool names and returned version **1.0.0**. It shows three activities/four slots, teacher workloads 3 and 1, zero findings in the valid schedule and three findings in the conflicting schedule. The teacher-filtered CSV has two data rows, 234 bytes, SHA-256 `9a3f69ccc2e7ecad6904736b0c13e7b09be3e1c20caa3b6f81d15598be961140`. The fixture content and those results match the separately recorded installed-tool tests. Its `fet_version=6.28.0` identifies the FET input format and is not the plugin version.

The screenshot alone does not independently prove backend tool invocation. The actual SDK/installed-host evidence in `TEST_REPORT.md` supports that separately. The screenshot contains fictional school data and a local test path, with no observed credential or real student record. The user expressly supplied it for Phase 3 evidence. A verified permanent PR evidence link is recorded in the task's `Test Screenshot` field after attachment.

Read-only submission preflight also corroborated the user's actual saved WorkSwarm run: request `req_mvkdx4ua_53`, session `web_1a16693be05_b6177568805b`, recorded 2026-10-23 11:02:55–11:03:08 Asia/Singapore. Its raw results contain one `inspect_fet`, two `verify_fet_timetable` and one `export_fet_timetable` call, all reporting 1.0.0 and matching the displayed results. The physical exported CSV also matches 234 bytes and the SHA-256 above. These records corroborate the screenshot separately; no additional agent/model call was made for this check.

## Delivery boundary

Proceed with the unchanged Chinese canonical package through the repository's checked GitHub PR and merge workflow. Attach and verify the original image before merge. Do not create a GitHub Release or perform Agentic Hub operations. Song Haoran owns Hub submission/publication and Project Lead acceptance. Keep the candidate `Planned`, task awaiting acceptance and completion date blank until the applicable acceptance gates pass.
