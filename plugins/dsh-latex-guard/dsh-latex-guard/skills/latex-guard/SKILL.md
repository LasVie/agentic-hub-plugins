---
name: latex-guard
description: Use native tools to compile-check LaTeX, lint or enrich BibTeX, and audit citation keys safely.
---

# LaTeX Guard

Use the narrowest tool that answers the request:

- `latex_check` takes an explicit project directory and entry filename. It runs `latexmk` when available; otherwise it reports `skipped` and still audits a same-stem `.bib` file when present.
- `bib_lint` finds duplicate keys and missing fields. Keep `write` false unless the user explicitly asks to modify the file. A write removes later duplicate entries and normalizes formatting.
- `bib_fill` queries Crossref by DOI or title and fills only blank fields. Keep `write` false for preview; disclose that this tool sends DOI/title metadata to Crossref.
- `cite_audit` compares citation commands in one or more explicit TeX files with an explicit `.bib` file.

Treat a skipped compile as inconclusive, not a passing build. Never claim that linting proves scholarly correctness. Before a write, preserve the original or ensure the file is version-controlled. The tools refuse writes when the BibTeX parser cannot account for every entry marker.
