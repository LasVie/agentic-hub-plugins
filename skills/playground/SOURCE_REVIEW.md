# Playground source and duplicate review

Reviewed: 2026-10-22. Candidate: `CAND-ANT-014`. Task: `AH-20261022-playground`.
Owner/publisher: Nguyen Trung Dung, following the user's selected task and confirmed tracker member name.

## Scope and related assets

The port generates local interactive HTML explorers with live state, presets, previews, and a prompt the user copies into an agent session. It retains the six upstream workflows. It does not implement native host page/TUI integration, automatic browser-to-agent callbacks, hosting, or model access.

The live tracker was re-read at kickoff: the candidate was `To Evaluate`, `Unassigned`, with no linked task; `AH-20261022-playground` did not exist. The Asset Ledger still contained 593 records. The following relevant existing assets were compared by inputs, actions, outputs, and scope:

| Asset ID | Asset / version | Comparison |
| --- | --- | --- |
| `8fd546a8a97149a08029b24e9d3cd028` | frontend-design / e7bda4f | Generates polished frontend interfaces from a brief. Playground adds a user-operated stateful explorer with live preview and a contextual prompt output; it does not replace the general frontend design asset. |
| `fb9e53d490ed4f62af6151509c3bb1ba` | ui-design / 1.0.0 | Implements interfaces with visual direction and craft checks. Its ledger entry does not describe interactive configuration and feedback-to-prompt workflows. |
| `585e9662a0604f6f97c4a710abe05034` | vcp-visual-output / 1.0.0 | Produces self-contained visual HTML cards through VCP. Playground adds controls, selection/review state, and prompt generation; it does not depend on or replace VCP. |
| `7d1e144cfda141a8ac7d5cec8f21f556` | Landing Page Generator / 1.0.0 | Generates a deployable product landing page; the primary output is a finished page, rather than an interactive explorer used to give an agent further instructions. |

Conclusion: distinct interactive exploration capability within the scope described above. This is not a claim that all generic HTML-generation capability is new. Candidate review/claim and task updates are saved in `tracking/pending/AH-20261022-playground-start.json`; no cloud claim or synchronization is asserted while the write connection is unavailable. Live ownership must be rechecked before synchronization or remote delivery.

## Pinned materials and permission

Source: https://github.com/anthropics/claude-plugins-official/tree/d4226d062928f8d9505dbdeadd10217d23361052/plugins/playground

Pinned full commit: `d4226d062928f8d9505dbdeadd10217d23361052`. Upstream does not declare a Playground version; this port uses its own release version `1.0.0` and does not invent an upstream version.

The pinned tree, root license, plugin license, plugin author metadata, main skill, and all six templates were inspected. The full root and plugin Apache-2.0 texts match (SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`). No more-specific license or NOTICE appears in the copied subtree. The plugin-level license covers these packaged skill instructions and templates. No external assets, executable upstream scripts, fonts, data, or runtime dependencies are copied. No API-service authorization is needed for the copied instruction material. This is a permitted port, recorded as `mode: ported`, `permission_status: verified`, not as independent/original upstream work.

| Actual material | Pinned upstream path | License / evidence | Reuse |
| --- | --- | --- | --- |
| `playground/SKILL.md` | `plugins/playground/skills/playground/SKILL.md` | Apache-2.0; `playground/licenses/claude-plugins-official/LICENSE` | Modified, with prominent in-file notice |
| `playground/templates/*.md` (six files) | `plugins/playground/skills/playground/templates/*.md` | Same Apache-2.0 evidence | Copied byte for byte |
| `playground/licenses/claude-plugins-official/LICENSE` | `plugins/playground/LICENSE` | Complete Apache-2.0 text, SHA-256 above | Copied byte for byte |

`UPSTREAM_FILES.json` records exact upstream/payload paths, SHA-256 hashes, and modified status per reused file. Existing attribution is retained; the upstream plugin identifies Anthropic as author but supplies no file-level copyright statement. No new copyright ownership is invented. The license appendix's placeholders remain part of the unchanged license text. The local installation guide, notices, release metadata, and test material are additions; no license is selected for the repository as a whole.

## Changes and execution boundaries

Only `SKILL.md` is modified among copied implementation files. It adds version `1.0.0`, a prominent modification notice, provider-neutral language, skill-relative template resolution, portable browser handoff, headless output, safe source-text handling, clipboard failure behavior, and truthful verification instructions. The six templates retain their original sample snippets; the shared skill explicitly requires safe text rendering when adapting those examples to user data.

The human-readable installation instructions cover the Hub inner directory, workspace-local Codex skills, and the active Hermes profile. Automated package checks cannot establish target-host discovery or model behavior. Representative HTML workflows are exercised separately; target-host and user acceptance remain pending as described in `TEST_REPORT.md`.

## Final ZIP content review

Expected release: `releases/skill/playground/1.0.0/playground-1.0.0.zip`.

- Full upstream license: `playground/playground/licenses/claude-plugins-official/LICENSE`; exact SHA-256 is recorded in `provenance.json` and checked against the extracted ZIP.
- Source/author/modification summary: `playground/playground/THIRD_PARTY_NOTICES.md`.
- Modified-file declaration: `playground/playground/SKILL.md`, immediately after the title. A centralized summary is not being used as its replacement.
- All six `playground/playground/templates/*.md` files must match their pinned upstream hashes.
- Upstream NOTICE: none at the inspected scopes; none fabricated.
- Branding, fonts, images, external data, runtime dependencies: none bundled.
- Developer tests, tracker records, caches, and downloaded research materials stay outside the ZIP.
- The final archive is extracted and every member is compared against `artifact.json` payload hashes; this review result is recorded in `TEST_REPORT.md` and `RELEASE_TEST.log` after packaging. A mismatched or missing license, copied path, or change notice prevents a successful release check.

License evidence is sufficient for this stated reuse. Cloud tracker synchronization, target-host user testing, PR delivery, and Hub submission remain separate workflow conditions and are not claimed by this source review.


## Chinese packaging 1.0.1 (2026-10-22)

The Project Lead-side user explicitly requested Chinese packages for every currently delivered asset. This is local Build work based on merged 1.0.0. Marketplace/native display fields and README were localized without changing machine identifiers, license bytes, publishers or upstream provenance. Playground SKILL.md frontmatter and instructions are translated, including the existing safety and browser handoff rules; six upstream templates are byte-identical. UPSTREAM_FILES.json retains the original source hash and records the changed payload hash. Functional code, data, runtime instructions and templates remain byte-identical. No new third-party material is introduced. Original license copies and attribution remain; modified documentation carries a prominent dated notice. New user testing, screenshot and separate Hub confirmation remain pending. Automated checks do not substitute for these gates.


## Complete Chinese template edition (2026-10-22)

All six `playground/templates/*.md` files are now modified derivatives, translated into Simplified Chinese together with their sample labels, help, prompts and comments. Original machine identifiers, code syntax, source paths and full Apache-2.0 license text remain intact. Every template carries a prominent dated modification notice and source/license pointer. `UPSTREAM_FILES.json` preserves each original upstream hash, records the actual translated payload hash, and marks all seven instruction/template files modified. Historical statements above about byte-identical templates apply only to earlier editions. Data/diff/document examples now construct text-safe DOM content instead of interpolating untrusted text into executable HTML; clipboard success, failure fallback, keyboard controls, real source evidence, comment preservation and rejected-suggestion boundaries are explicit. No new library, remote resource, media, dataset or dependency is bundled. Nguyen Trung Dung remains the owner. Translation and packaging checks do not establish target-host model behavior; actual import/prompt/browser tests are separate evidence.
