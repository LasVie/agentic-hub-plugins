# LaTeX Guard test prompts

After uploading this folder to the agent workspace, replace `<folder>` below with its absolute workspace path.

## Citation audit

```text
Use cite_audit with bib_path `<folder>/main.bib` and tex_paths [`<folder>/main.tex`]. Return the raw tool result.
```

Expected: `missing_in_bib` contains `missing`, and `uncited` contains `unused`.

## BibTeX lint

```text
Use bib_lint on `<folder>/main.bib` with write=false. Return the raw tool result.
```

Expected: the `known` entry is reported as missing `author` and `journal`. The file is not modified.

## Crossref fill preview

```text
Use bib_fill on `<folder>/main.bib` with write=false. Return the raw tool result.
```

Expected: the tool queries Crossref where a DOI or title is available, reports filled/missing/failed keys, and does not modify the file.
