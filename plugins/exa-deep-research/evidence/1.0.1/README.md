# Original user test screenshots — Exa 深度研究 1.0.1

Task `AH-20261022-exa-deep-research`; candidate `CAND-CLD-017`.
Owner: Nguyen Trung Dung. Received 2026-10-23 at 14:57:13 Asia/Singapore.
These five original PNG attachments accompany the user's explicit confirmation
of the Chinese package. No image was resized, recompressed, annotated or recreated.
File hashes, dimensions and archive fingerprints are in [index.json](index.json).

1. [Fetch](01-fetch.png): Chinese prompt and page-content summary with source URL.
2. [Advanced search](02-advanced-search.png): domain-filtered query and response.
3. [Paid approval guard](03-paid-approval-guard.png): Chinese error message with
   `PAID_ACTION_REQUIRES_APPROVAL` for `allow_paid=false`.
4. [Search summary](04-search-summary.png): Chinese summaries and source links,
   with an English introductory paragraph.
5. [Expanded search event](05-search-tool-event.png): actual `exa_search`
   arguments and `ok=True` result routed through `web_search_exa`.

None shows the plugin version/hash. The user's reply to the precise 1.0.1
handoff establishes version association; the Chinese guard text also matches
this payload. Only image 5 displays an expanded raw tool result. The others
document frontend responses. See [TEST_REPORT.md](../../TEST_REPORT.md) for
independent runtime verification and limits. Do not infer paid-research execution
or complete Chinese wording in every model response.

The delivery PR embeds these original files through immutable commit URLs.
The shared task's Test Screenshot field points to the dedicated PR evidence
comment, which survives temporary branch deletion.
