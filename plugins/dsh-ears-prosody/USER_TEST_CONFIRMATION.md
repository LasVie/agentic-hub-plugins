# User testing confirmation history

## Version 1.0.0 — confirmed 2026-10-22

Task `AH-20261022-dsh-ears-prosody`; candidate `CAND-DSH-189`; owner Cai Zhenze.

The requesting human user explicitly stated in the current Codex conversation:

> The attached image is my original testing screenshot. I confirm manual testing of **CAND-DSH-189 — DSH Ears Prosody v1.0.0** is complete and passed. Please proceed to Phase 3.

Recorded 2026-10-22, Asia/Singapore. The exact message timestamp and a shareable conversation URL are unavailable; neither is invented. The confirming user's identity is not inferred from the owner or GitHub account. This is explicit version-specific testing confirmation, separate from Song Haoran's final Project Lead acceptance.

- Canonical ZIP SHA-256: `819341f0c0000225beb197ef04dd0c96982187bbfec670c7658b45716f302008`.
- Native WorkSwarm ZIP SHA-256: `4e272217182ae9a8977ad5fec6958b4bd7638494a87d566f234707971c5aa7b4`.
- All nine runtime files were reverified identical across source, canonical ZIP and native companion. No unresolved functional issue was reported.
- Original attachment: `Screenshot 2026-10-22 at 5.05.12 PM.png`; 846 × 1628 pixels, 283,306 bytes; SHA-256 `ac05b63e9512fc44b7e19d262ea4b5935d13dd568cdd3e78a49e61b8cf6ba5c4`.
- An unchanged local copy is preserved at `/private/tmp/prosody-submission-20261022/original-test-screenshot.png`, outside the repository and runtime ZIP.

The screenshot visibly identifies version 1.0.0 and the demo/silence results: five seconds, three segments, two 365 ms pauses, 220.1 Hz mean pitch, and silence with zero activity/null pitch. These values match the separately recorded installed-tool test. The screenshot alone does not independently prove backend tool invocation. No original image has yet been uploaded to GitHub, and no evidence permalink is claimed.

## New delivery-language requirement

Submission preflight fetched main `e0f6b866649e82cbf37fbd082db9891ca977ae8e` (PR #20). Its new **Chinese Final Deliverables** policy requires actual packaged Chinese instructions, metadata, default output and errors. It explicitly states that localization changes a tested payload and requires a new version/ZIP and renewed user test-completion confirmation.

The confirmed English 1.0.0 package and original evidence remain preserved. The same task returns to Build for a Chinese 1.0.1 edition before a delivery PR. The 1.0.0 confirmation does not cover 1.0.1. No push, PR, merge, Release or Hub operation is authorized for an unconfirmed changed ZIP; Hub operations remain Song Haoran's responsibility.

Linked confirmation report: `RPT-20261022-dsh-ears-prosody-confirmed-100`.

The preserved 1.0.0 canonical ZIP/artifact are now stored at `dist/dsh-ears-prosody/history/1.0.0/`; the native companion remains at `dist/dsh-ears-prosody/1.0.0/`. Local commit `1f6f30c` preserves the original source and report. The superseded English release is excluded from the current delivery release tree, without changing its archived bytes.

## Version 1.0.1 Chinese edition — confirmed 2026-10-22

The requesting human user explicitly stated in this same conversation:

> The attached image is my new testing screenshot of the Chinese edition to be used. I confirm manual testing of **CAND-DSH-189 — DSH Ears Prosody v1.0.1 (Chinese edition)** is complete and passed. Please proceed to Phase 3.

Recorded 2026-10-22, Asia/Singapore. The original screenshot displays a test conversation at 17:34; the exact confirmation-message timestamp is unavailable. Source is the current conversation, with no invented message permalink. Owner Cai Zhenze is the user's explicit assignment. Final Project Lead acceptance remains separate and pending.

- Task `AH-20261022-dsh-ears-prosody`; candidate `CAND-DSH-189`.
- Naming: `chaoge762/dsh-ears-prosody` / DSH Ears Prosody → **DSH 韵律分析** → `dsh-ears-prosody`.
- Canonical ZIP SHA-256: `be6bddccd8fc5c42a5259d66cd9c2b8f474d0a174b0ac2a29c20ac97c6fcf9e8`.
- Native WorkSwarm ZIP SHA-256: `a68c0ba7687a98a274dfeb0102e641895084ccf516c3e703b19c0ba6a6e9afb2`.
- Original attachment `Screenshot 2026-10-22 at 5.35.53 PM.png`: 566 × 1256 pixels, 206,508 bytes; SHA-256 `6252eda92c0d96cbfdbb871cd929da14db72f593d629c9284935a3e4fd251751`.
- Unchanged original preserved locally at `/private/tmp/prosody-submit-101-20261022/original-test-screenshot-1.0.1.png`, outside source and runtime ZIPs.
- Linked confirmation report: `RPT-20261022-dsh-ears-prosody-confirmed-101`.

The original image is readable and shows the Chinese plugin name, `analyze_wav_prosody`, returned version 1.0.1, Chinese fixture paths and Chinese explanations. Demo results are five seconds, three activity segments, two 365 ms pauses and 220.1 Hz mean pitch; silence has one second, zero activity and unavailable pitch/pacing. These corroborate the independently recorded installed-tool results and unchanged package hashes. The screenshot alone does not independently prove backend invocation. It contains synthetic test measurements, not private audio or credentials, and was explicitly supplied for PR evidence.

All required delivery materials are present and no known blocking issue remains. This confirmation authorizes GitHub delivery of the unchanged Chinese package under the repository workflow; it does not authorize Hub operations or establish Song Haoran's acceptance. The verified PR evidence permalink will be recorded in the original Development Task when the PR exists.
