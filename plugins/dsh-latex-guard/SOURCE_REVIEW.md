# Source Review: dsh-latex-guard

## Identity and fixed source

- Candidate: `CAND-DSH-204`
- Upstream: https://github.com/Flan246/dsh-latex-guard
- Fixed revision: `8046f75141ddcf70a6eae4e61f20525d892e0176`
- Published version: `0.1.3`; the npm package records the same git head.
- Upstream license: complete MIT text at repository root, copyright `(c) 2026 Flan246`.
- Review date: 2026-10-22.

The upstream root license covers the repository software at the fixed revision. No separate subdirectory license, NOTICE, file-header exception, logo, font, dataset, or third-party media was found. The port retains the full MIT text, copyright, disclaimer, a prominent source header, and a modification summary.

## Reuse and modifications

This is a derivative Python port of the core algorithms and behavior in `src/core/`, plus adapted operating guidance. The DSH/Cordis plugin registration, compiled JavaScript, Node CLI, npm dependencies, tests, and distribution assets are not included.

The port exposes three native WorkSwarm `Tool` classes, uses explicit file-path inputs, previews BibTeX changes by default, blocks writes after incomplete parsing, and uses Python's standard library for Crossref. The upstream `latex_check` capability was deliberately omitted after host testing showed that a real compile requires a separately installed TeX distribution; the Plugin does not advertise or return a skipped compilation tool. Because no upstream or npm dependency code is bundled, Commander, Undici, Cordis, DSH Tools, and development dependency licenses are not distribution obligations for this ZIP.

The latest upstream commit on review date was `45b326bf9f5dfab8884c0fa9580cb90298bc85d5`, which only adds evaluation fixtures/reporting after 0.1.3. It was inspected for version context but is not the reused revision.

## Compatibility conclusion

Compatible as a real Agentic Hub Plugin after replacing the host-specific registration layer and narrowing the shipped scope to capabilities that work without an unavailable system dependency. No MCP connector, DSH UI, Cordis service, Node.js, npm install, TeX distribution, account, or secret is required.

- `bib_lint`: local read and optional explicit write.
- `bib_fill`: local read, optional explicit write, and HTTPS calls to Crossref using DOI/title metadata.
- `cite_audit`: local reads only.

## Functional duplicate review

Asset Ledger was searched by purpose and terms, not name alone. Partial overlaps:

- `Citation Management` (`1f4e4a2df62a40879bbbd77580973b99`) searches/validates academic references and generates BibTeX.
- `academic-citation-manager` (`0b3aefa276af49bc863c42001a77e695`) adds real references and standardizes paper citations.
- `blind-submission-audit` (`0829fbe48b0940c7967c61cc444f0d2c`) reads LaTeX/BibTeX for identity leaks.
- `Peer Review` (`1f53f98b3e4348d69a42b25b6c6ce459`) annotates `.tex` as part of academic review.

None exposes duplicate-key/missing-field BibTeX linting, Crossref gap filling, and unresolved/uncited key auditing as one three-tool Plugin. Conclusion: partial overlap, extend with a distinct executable capability; do not replace the citation research Skills. LaTeX compilation is explicitly outside the delivered scope.

## Distribution review

The final ZIP must include `THIRD_PARTY_NOTICES.md`, `licenses/dsh-latex-guard/LICENSE`, the modified tool header, and only the Python port/Plugin documentation. Before release, unpack the ZIP and verify these exact paths and the license SHA-256 recorded in `provenance.json`.
