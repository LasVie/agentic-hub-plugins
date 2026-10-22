# LaTeX Guard

This WorkSwarm Plugin exposes three native tools: `bib_lint`, `bib_fill`, and `cite_audit`. It does not use an MCP connector and does not require DeepSeek Harness, Cordis, Node.js, npm, `latexmk`, or a TeX distribution.

`bib_fill` is the only network operation; it sends a DOI or title to the public Crossref API. The other tools work on local files only. This Plugin does not compile LaTeX.

All paths are explicit tool inputs. `bib_lint` and `bib_fill` preview changes by default and write only when `write` is true. An incomplete BibTeX parse blocks a write.

This is a modified Python port of `dsh-latex-guard` 0.1.3. See `THIRD_PARTY_NOTICES.md` and `licenses/dsh-latex-guard/LICENSE`.
