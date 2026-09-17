# Inside the STEP File

Open-source book on the STEP file format (ISO 10303), published as an HTML site on GitHub Pages plus a downloadable PDF. The text was converted from the PDF draft in `docs/`; the `.qmd` sources are now canonical.

## Toolchain

- Quarto book project (`_quarto.yml`). HTML via the `html` format, PDF via the `typst` format (Typst is bundled with Quarto; no LaTeX).
- `quarto preview` for live editing, `quarto render` for the full build into `_book/` (git-ignored).
- CI (`.github/workflows/publish.yml`) renders on every push and PR and deploys `_book/` to GitHub Pages from `main`.

## Conventions

- One sentence per line in `.qmd` sources.
- Chapters live in `chapters/` (numbered files) and `appendices/`, ordered in `_quarto.yml`. Each starts with a level-1 heading with a `{#sec-...}` id, followed by a `::: {.chapter-abstract}` div, and ends with a `::: {.callout-important title="In brief"}` summary.
- Boxed sections: `callout-note` titled "Engineering background: …" and `callout-warning` titled "In the wild: …".
- Part 21 listings use ```` ```step ````, EXPRESS uses ```` ```express ```` (definitions in `syntax/`). Entity names in prose are upper case in backticks.
- Appendix A embeds `examples/block.step` via the include-code-files extension; never paste the file into the chapter.
- There is no citation apparatus. Sources are named in the text by part and edition, and collected as prose in `appendices/c-sources.qmd`.
- Example STEP files live in `examples/`; listings in the text should be complete, valid files.
- Check both HTML and PDF output after structural changes; tables and callouts are the usual sources of divergence.
