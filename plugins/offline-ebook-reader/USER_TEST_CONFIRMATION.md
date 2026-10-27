# User test confirmation — 离线书架阅读器 1.0.0

Task `AH-20261027-offline-ebook-reader`; Candidate `CAND-DSH-329`; Owner Cai Zhenze.

User test confirmation: "I confirm manual testing of CAND-DSH-329 — 离线书架阅读器 v1.0.0 passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md. GitHub delivery only; no Release or Hub actions."

Confirmed by Cai Zhenze in the current conversation on 2026-10-27 Asia/Singapore; the message has no available permanent link or exact receipt timestamp. Original screenshots are dated10:39:11/29/40/50. Receipt time is not inferred from screenshot timestamps. No known blocking issue reported. This is user completion, not Project Lead acceptance.

- Tested native ZIP SHA-256: `0da0b30a9961bc6ea1fd66b18b8085f1f10446eb14526ca013e6edfaa9669222`.
- Canonical ZIP SHA-256: `f6b38c5e1f05055c041971609a6669f5aefcb45d37563722d55e7e12c55b6cf4`.
- Confirmed source/canonical/native ten-file payload remains byte-identical. No runtime/localization/wrapper/version change after testing.
- Confirmation report: `RPT-20261027-offline-ebook-reader-confirmed-100`.

## Original screenshot receipt

Four original PNGs were copied byte-for-byte into ignored `dist/offline-ebook-reader/1.0.0/user-evidence/` for PR upload. The originals are not in either plugin ZIP. Images are uploaded directly to the GitHub PR comment, with their verified permalink subsequently recorded in the original task. No image is reconstructed or recompressed.

| Original filename | Dimensions | Bytes | SHA-256 |
| --- | --- | --- | --- |
| Screenshot 2026-10-27 at 10.39.11 AM.png | 1270×1778 | 401917 | `0ecf3e9294fd384ec3e29e76b53c1d89abb223119b5a2f2c7f02ff112d5bf7b0` |
| Screenshot 2026-10-27 at 10.39.29 AM.png | 1162×1838 | 500691 | `11e0e0d710efd15e92892cfdde5568f8135647e74ce99d587f99d8dab96da781` |
| Screenshot 2026-10-27 at 10.39.40 AM.png | 3448×2080 | 608869 | `f872315ceabfcfe8906dfe5c365192d77e335affec45f0e451b224000a2b2043` |
| Screenshot 2026-10-27 at 10.39.50 AM.png | 3452×2078 | 753683 | `56163fdb3b88d6ccfeaa6c838fa469258c957c85b27e218e33f62e8e6b136f19` |

First image shows the Chinese requested tool workflow and version1.0.0 response introduction. Second shows reported import reuse, fixed-layout/malformed/encoding refusals, chapter snippets, omission warnings and matching start/status session. It is a conversation summary, not independent backend invocation proof. Third/fourth show actual v1.0.0 TXT/EPUB reader UI, corresponding book names/chapter order and saved-position banners. Neither static UI image alone proves a before/after refresh, service restart, or changed-settings persistence. User explicit pass is retained; independent automated evidence is separately described in TEST_REPORT.md.

The local reader URL/session in the screenshots matches the prepared installed-tool session `18d9d0eb87d106271a0f81cc` and synthetic fixture records. That task-owned reader was stopped and its port confirmed closed before public upload, retiring the temporary capability. Original images are unchanged. No model request, Release or Hub operation is made during GitHub delivery. Project Lead acceptance remains pending.
