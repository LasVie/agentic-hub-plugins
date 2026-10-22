---
name: latex-guard
description: Use native tools to lint or enrich BibTeX and audit LaTeX citation keys safely.
---

# LaTeX Guard

Use the narrowest tool that answers the request:

- `bib_lint` finds duplicate keys and missing fields. Keep `write` false unless the user explicitly asks to modify the file. A write removes later duplicate entries and normalizes formatting.
- `bib_fill` queries Crossref by DOI or title and fills only blank fields. Keep `write` false for preview; disclose that this tool sends DOI/title metadata to Crossref.
- `cite_audit` compares citation commands in one or more explicit TeX files with an explicit `.bib` file.

This Plugin does not compile LaTeX. Never claim that linting proves scholarly correctness. Before a write, preserve the original or ensure the file is version-controlled. The tools refuse writes when the BibTeX parser cannot account for every entry marker.
