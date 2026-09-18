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
- Example STEP files live in `examples/`. A listing is an excerpt: open it with ```` ```{.step source="file.step"} ```` naming the file it comes from or builds on. `filters/referenced-records.lua` prints the records it refers to beneath it (all of them in HTML, the nearest 40 in the PDF), and `tools/check_references.py` checks that each exists, has an entity type its attribute admits, and that shown records match the file. Records written for the book take numbers the source file does not use.
- `bracket-pmi.step` is the AP242 bracket from OCCT 7.9 plus hand-written PMI (#600 on) following the CAx-IF PMI practice v4.0. `pin-with-pcurves.step` is the pin re-exported with pcurves. Both were built with OCCT 7.9 (`cadquery-ocp` 7.9.3), not FreeCAD's bundled 7.8.
- Check both HTML and PDF output after structural changes; tables and callouts are the usual sources of divergence.
