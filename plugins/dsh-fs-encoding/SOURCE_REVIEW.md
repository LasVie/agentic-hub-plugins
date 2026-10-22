# Source Review: dsh-fs-encoding

Candidate `CAND-DSH-153`; upstream https://github.com/MrWeiCodes/dsh-fs-encoding pinned to npm 1.5.2 git head `a4d31cc33bd6f0fab2bf6752f6e50e8301885b94`. Reviewed 2026-10-22. The complete root MIT license covers repository software; copyright is retained. No separate license, NOTICE, branded media, font or dataset is distributed.

This is a derivative Python port of encoding detection/normalization, BOM and line-ending fidelity, strict representability refusal, search and one-level undo behavior. It does not copy DSH/Cordis registration, UI cards, compiled JavaScript, icon, locales, Node dependencies or DSH peers. The Python standard library supplies codecs, so iconv-lite/chardet are not bundled.

The original replaces DSH `read`/`write`/`edit`/`grep` and relies on DSH filesystem, session, sandbox and observation services; unchanged installation is incompatible. The WorkSwarm port instead declares five distinct native `encoding_*` tools with explicit paths. It cannot transparently protect calls made through built-in tools. No connector, account, API key, Node runtime or network service is required.

Asset Ledger duplicate review found no full overlap. `xlsx` (45af6a728e8a476bafddfd6639946ff3), `code-analysis-toolbox` (5383b7c97dcf45e18805798365dd6c1f), `python-release-diff` (850431fa7351409f922e0fbd510d1b8a) and `doc-sensitive-redact` (eee9ffd49af44476adb85ec3b6faad9b) do not provide arbitrary legacy-encoded text round trips with BOM/line-ending preservation, strict rejection and guarded undo.


## Chinese packaging 1.0.2 (2026-10-22)

The Project Lead-side user explicitly requested Chinese packages for every currently delivered asset. This is local Build work based on merged 1.0.1. Marketplace/native display fields and README were localized without changing machine identifiers, license bytes, publishers or upstream provenance. Functional code, data, runtime instructions and templates remain byte-identical. No new third-party material is introduced. Original license copies and attribution remain; modified documentation carries a prominent dated notice. New user testing, screenshot and separate Hub confirmation remain pending. Automated checks do not substitute for these gates.


## Complete Chinese runtime edition (2026-10-22)

Localized the actual Skill instructions, ToolCard descriptions and human-readable errors while retaining machine parameter names, result/error keys, codes, codec IDs, protocol values, original MIT headers and full license bytes. Existing algorithms and standard exception details remain; Chinese prefixes explain external/Python diagnostics without rewriting third-party values. No new dependencies or source materials. Final hash and real WorkSwarm evidence are recorded after packaging.
