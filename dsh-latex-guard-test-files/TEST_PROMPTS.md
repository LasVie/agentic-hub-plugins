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

## LaTeX compilation

```text
Use latex_check with project_dir `<folder>`, entry `main.tex`, and engine `auto`. Return the raw tool result.
```

Expected: `passed` or `failed` when `latexmk` is installed. Otherwise, `skipped` with a notice explaining that `latexmk` is unavailable.
