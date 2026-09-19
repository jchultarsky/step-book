# Inside the STEP File

[![Build and deploy book](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml/badge.svg)](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml)

*Products, shapes and tolerances, one record at a time.* An open-source reader's guide to the STEP file format (ISO 10303): what the records in a STEP file mean, how they fit together, and what real exporters actually write.

- **Read online:** <https://jchultarsky.github.io/step-book/>
- **Download PDF:** <https://jchultarsky.github.io/step-book/inside-the-step-file.pdf>
- **Download EPUB:** <https://jchultarsky.github.io/step-book/inside-the-step-file.epub>

## Building locally

The book is written in [Quarto](https://quarto.org/) Markdown. Install Quarto 1.10 or later, then:

```bash
quarto preview        # live-reloading HTML in your browser
quarto render         # full build: HTML site, PDF and EPUB into _book/
```

The PDF is produced with Typst, which ships inside Quarto, so no LaTeX installation is required.

## Repository layout

```
_quarto.yml          Book configuration: title, chapter order, output formats
index.qmd            Preface
chapters/            One .qmd file per chapter, numbered in reading order
appendices/          Complete block file, entity quick reference, sources, glossary
examples/            The STEP files every listing in the book is taken from
filters/             Quarto filter that shows the records each listing refers to
figures/             Part drawings generated from examples/ by tools/render_examples.py
syntax/              Syntax-highlighting definitions for Part 21 files and EXPRESS
styles/              Stylesheets for the HTML and EPUB editions and typography fixes for the PDF
tools/               Checks that validate the book against published EXPRESS schemas
docs/                The original PDF draft the book was converted from
.github/workflows/   CI: runs the checks, renders the book, deploys it to GitHub Pages
```

## Checking the book

CI checks entity names, simple-record parameter counts, reference targets, listing consistency and Appendix B attribute order against the AP242, AP214 and AP203 edition-2 schemas vendored under `tools/schemas/`, so a wrong entity name or parameter count fails the build instead of reaching a reader.
These are focused checks, not full EXPRESS or geometric validation: a passing build does not prove that every claim or example conforms to its declared schema and edition.

```bash
python3 tools/check_book.py
python3 tools/check_appendix_b.py
```

See [tools/README.md](tools/README.md) for what each check covers.

## Contributing

Corrections, clarifications, and new material are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
