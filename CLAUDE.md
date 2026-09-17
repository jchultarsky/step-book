# The STEP Book

Open-source book on the STEP file format (ISO 10303), published as an HTML site on GitHub Pages plus a downloadable PDF.

## Toolchain

- Quarto book project (`_quarto.yml`). HTML via the `html` format, PDF via the `typst` format (Typst is bundled with Quarto; no LaTeX).
- `quarto preview` for live editing, `quarto render` for the full build into `_book/` (git-ignored).
- CI (`.github/workflows/publish.yml`) renders on every push and PR and deploys `_book/` to GitHub Pages from `main`.

## Conventions

- One sentence per line in `.qmd` sources.
- Chapters live in `chapters/`, ordered in `_quarto.yml`. Each chapter starts with a level-1 heading with a `{#sec-...}` id.
- Citations go in `references.bib` (IEEE style via `ieee.csl`); cite with `[@key]`.
- Example STEP files live in `examples/`; listings in the text should be complete, valid files.
- Check both HTML and PDF output after structural changes; tables and callouts are the usual sources of divergence.
