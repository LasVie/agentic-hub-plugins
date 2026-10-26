# User test confirmation — Chinese 1.0.0 confirmed; originals collected

- Task ID: AH-20261026-domain-renewal-research; Candidate ID: CAND-CLD-138.
- Confirmed by: Nguyen Trung Dung, the member explicitly identified in this conversation.
- Package: 域名续费比价 / domain-renewal-research, version 1.0.0.
- Native ZIP SHA-256: `af6ef3967d0dcb88739abf6bf0df5e88e4eb39f98477b536386d0e93159b0d26`.
- Canonical ZIP SHA-256: `532fefbc5aa7a94fa08ad76270ad9d491e8f4ffe7fac12713a3e4b1c6945a82c`.
- Confirmation received: 2026-10-26, recorded at 15:08 Asia/Singapore; the message's exact send time is unavailable. Visible test screenshots show 15:02–15:04 on that date.
- Evidence/source: current conversation, the user's message immediately after the six Chinese test prompts; no permanent message URL is exposed.
- Actual user statement: “Confirmed for chinese version, can you port the English version too, if that is necessary”.
- User test confirmation: Chinese version testing confirmed complete by Nguyen Trung Dung for this task's previously supplied 1.0.0 package. The user did not independently restate a hash; association is to the unchanged package handed over immediately before these tests. Both ZIP hashes were rechecked unchanged on receipt. Preserve this confirmation; do not ask for it again.

## Seven screenshots received in this conversation

| Order | Visible evidence | Limits of the visible evidence |
| --- | --- | --- |
| 1 | `domain_get_registrars` completed; Chinese answer cites the MCP endpoint and service 1.12.0. | Full registrar list/raw response is below the crop. |
| 2 | Plugin selector has 域名续费比价 enabled; Exa and Windows Toolkit disabled. | Version/hash association comes from the preceding package handoff and confirmation. |
| 3 | `domain_search_prices` completed with requested suffixes, renewal sort, 1500-cent budget and limit 3. | Final price rows/raw response are below the crop. |
| 4 | `domain_estimate_cost` completed for OVHcloud/.org, `years=3`. | Final amounts/raw response are below the crop. |
| 5 | `domain_check_availability_batch` completed for example/com,org, `cachedOnly=true`. | Individual returned statuses are below the crop. |
| 6 | Invalid-Chinese-name prompt and completed calls; assistant admits substituting `12345`, then attempts correction. | Final raw `INVALID_ARGUMENTS` is not visible. This establishes agent argument substitution, not adapter acceptance of Chinese input or a passing manual rejection test. Independent exact-input SDK tests passed. |
| 7 | `domain_open_name_finder` completed, with Chinese form-entry heading. | Final URL/raw response is below the crop. |

The user supplied seven readable conversation images. On 2026-10-26 the matching seven originals were found in `C:/Users/ASUS/Pictures/Screenshots/`, viewed individually, and copied byte-for-byte into `evidence/1.0.0/`. `evidence.json` preserves original filenames, SHA-256, dimensions and byte counts. No recompression or image editing was performed. No credentials/private project material were observed. The earlier attachment-access blocker came from searching only Codex attachments; that search was too narrow and has been corrected. The user's follow-up “did I not send you just now ?” was correct.

Known blocking issues: none established in the plugin payload. The incomplete manual invalid-input screenshot is explicitly retained as an evidence limitation, not counted as a passing rejection test. The exact supplied Chinese-name rejection is independently covered by the passing real-SDK tests; agent argument substitution does not establish a plugin defect. User confirmation plus the original enabled-plugin/core-call screenshots are available for delivery. The Chinese package/version/ZIPs remain unchanged. GitHub upload/check/merge results must be recorded only after they occur. Hub and Project Lead acceptance remain separate later actions.

## English use

A separate port is unnecessary for language-neutral native tools. The packaged Skill explicitly follows a user's request for another response language. The same ZIP can be tried in an English-language host; this is an inference from the adapter/manifest, not an English-frontend test claim. Labels, bundled help and raw local errors remain Chinese; no fully English-localized edition is claimed. `MANUAL_TESTING_EN.md` supplies English prompts outside the payload. No packaged source, version, wrapper or ZIP changed; the Chinese confirmation remains applicable.
