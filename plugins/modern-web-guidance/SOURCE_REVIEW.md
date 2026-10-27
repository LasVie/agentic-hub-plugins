# Modern Web Guidance source and reuse review

Reviewed 2026-10-27, Gan Mingrui. Task `AH-20261027-modern-web-guidance`; candidate `CAND-CLD-076`; internal identity `repo:agent-plugin:modern-web-guidance`.

Name mapping: Modern Web Guidance → 现代网页技术指南 → `modern-web-guidance`, package 1.0.0.

## Purpose and overlap

The user explicitly selected this candidate and authorized Build. The live candidate/task claim was written and read back before implementation. This is a companion extension of frontend-design (`8fd546a8a97149a08029b24e9d3cd028@e7bda4f`): it supplies local modern-platform reference retrieval and fallback guidance, not aesthetic design generation. WCAG audit (`3fda724704c741a3b4b6d014753b0423@1.0.0`) and Chrome DevTools (`2f99a9222dce41f4bd5ac440bf4496f4@1.0.0`) address audit/live-debugging workflows. Current tracker conclusion: Partial Overlap - Extend Existing Capability. No existing asset was overwritten or prematurely entered in Asset Ledger.

## Pinned materials and coverage

| Material | Fixed source | Reuse and rights conclusion |
| --- | --- | --- |
| Prompt/instructions | npm `modern-web-guidance@0.0.196`, `skills/modern-web-guidance/SKILL.md` | Apache-2.0 root license; Chinese task-scoped adaptation in same named skill; replaces online npx/latest, broad mandatory triggering and full-corpus assumptions |
| Documentation/examples | Same package, 12 exact guide paths enumerated in provenance.json | Apache-2.0; translated and abridged with per-file modification notices, retained source links and snapshot caveats. Not a complete translation of the 192-entry upstream index |
| Index data | Same package, `skills/modern-web-guidance/guides.json` | Apache-2.0; 12 stable IDs/categories selected and Chinese metadata added. This generated file is present in the pinned npm tarball, not the distribution Git tree |
| Search implementation | [bm25.ts](https://github.com/GoogleChrome/modern-web-guidance-src/blob/8a0a736723558e9ae484e4b6bbf3cc6a8d6ba4ad/src/rag/bm25.ts) | Apache-2.0 source root license, no imports/dependencies in this module. Type erasure, Chinese comments/errors/tokenization; upstream BM25 and RRF scoring retained |
| Host adapter / CLI | Newly authored `tools/guidance_tool.py`, `runtime/cli.mjs` | Native Tool/ToolCard bridge, read-only bounded JSON protocol and relevance filtering; not copied from another team plugin. No claim of repository-wide relicensing |
| Icons / fonts / media | Not included | Google branding and upstream illustrations not reused |
| Model / vectors / third-party runtime bundles | Not included | TensorFlow, MiniLM, tokenizers, long, seedrandom, vectors and source maps excluded. No model-license inference required for distribution because these materials are absent |
| Online services / telemetry | Not included | Upstream default-on Clearcut/watchdog, npm install/update and environment detection are not imported or shipped. Native runtime imports only local BM25 and Node fs |

The npm tarball is [the exact registry artifact](https://registry.npmjs.org/modern-web-guidance/-/modern-web-guidance-0.0.196.tgz). Its SHA-256 is `c2728821e16071044bae353f74ec3cd6ced9d1c001a24a133e4c4ebd190798f8`; SHA-512 was verified against the registry integrity field (recorded in provenance.json). The 12 guide files and SKILL bytes also match Git blob hashes at [distribution commit 4f2b13e25c5815b3f080ca0d983e828d96561a0f](https://github.com/GoogleChrome/modern-web-guidance/tree/4f2b13e25c5815b3f080ca0d983e828d96561a0f). Per-source and per-target SHA-256 values are recorded for each guide. The standalone BM25 comes from a separately pinned implementation commit, not an assertion that it exactly equals the npm bundled revision.

Both fixed repository trees and npm contents were checked for root/subdirectory licenses and NOTICE files. Root Apache-2.0 applies to the selected code, skill and guides; no subdirectory override or per-file conflicting terms were found. Selected files have no separate copyright header. `GoogleChrome` is the actual npm publisher statement; no personal author, year or ownership statement was invented. The original license text includes its unchanged template appendix.

## Redistribution obligations and fulfillment

- Complete, unchanged Apache-2.0 texts at `licenses/modern-web-guidance/LICENSE` and `licenses/modern-web-guidance-src/LICENSE`. Each SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
- No standalone upstream NOTICE found. The npm `THIRD_PARTY_NOTICES` is preserved verbatim at `licenses/modern-web-guidance/THIRD_PARTY_NOTICES`, SHA-256 `6c15a79dd9fde68f3f175fa8a0ffbfd88dc25bfbfd07ce554286e432caad56f3`. Its dependency entries are preserved as original evidence; those dependencies themselves are absent.
- Payload `THIRD_PARTY_NOTICES.md` covers both upstreams, fixed versions, original attribution statements, covered paths and modifications. It does not replace the full license or change the license terms.
- Prominent modification notices appear in each of 12 guide files, the adapted SKILL, BM25 module and the catalog's `modification_notice` field. No original file-specific attribution was removed.
- No trademark endorsement or general trademark permission is claimed. External documentation links are citations, not runtime requests or bundled third-party media.

## Chinese adaptation and technical changes

All packaged user-facing instructions, descriptions, examples, help/errors and retrieval content use Simplified Chinese. API names, stable IDs, source URLs and legal text remain intact. Scope is explicitly a curated 12-guide edition; dense semantic search, Chrome-extension guidance and other upstream topics are excluded. Chinese keyword/bigram BM25 has narrower recall than full semantic search and may still need a focused query.

Technical corrections to selected examples: IME checks precede preventDefault; reduced/absent transitions must not leave hidden state waiting only for transitionend; selector fallbacks use separate supported rules; :has and :user-invalid support are separate; responsive tables retain a semantic scrolling default; snapshot versions are not asserted as current compatibility. These are documented changes, not attributed verbatim to upstream.

Requires the host's existing Python/openJiuwen SDK and Node.js 20+ on PATH. No extra npm package, external account/API key, model or service is needed. Host model availability remains a prerequisite for conversational use. Runtime does not write files, execute guide snippets or access project paths. The sole child process is a fixed local Node CLI with JSON stdin, never shell interpolation.

## Final archive review

Canonical archive: `releases/agent-plugin/modern-web-guidance/1.0.0/modern-web-guidance-1.0.0.zip`. Native-import transport is generated separately for the current host's manifest-root importer, without changing payload bytes. Final hashes, extraction audit and actual tests are recorded in TEST_REPORT.md and test-evidence.json. The automated suite checks every license evidence hash, every mapped guide hash, all declared paths and Chinese retrieval from the extracted payload. The release audit compares every source/native/marketplace payload byte and repeats deterministic packing.

Reuse conclusion: `ported / verified` for the explicitly enumerated materials. No unresolved distribution condition identified for this scope. This content review is not a claim of legal advice, Hub approval, actual browser behavior testing, human test completion or Project Lead acceptance. Gan Mingrui subsequently confirmed “1.0.0 测试通过” on 2026-10-27 after delegated host tests and original screenshots; see TEST_REPORT.md. The confirmed payload and ZIP hashes remain unchanged for GitHub delivery.
