# Inside the STEP File

[![Build and deploy book](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml/badge.svg)](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml)

*Products, shapes and tolerances, one record at a time.* An open-source reader's guide to the STEP file format (ISO 10303): what the records in a STEP file mean, how they fit together, and what real exporters actually write.

- **Read online:** <https://jchultarsky.github.io/step-book/>
- **Download PDF:** <https://jchultarsky.github.io/step-book/inside-the-step-file.pdf>

## Building locally

The book is written in [Quarto](https://quarto.org/) Markdown. Install Quarto 1.10 or later, then:

```bash
quarto preview        # live-reloading HTML in your browser
quarto render         # full build: HTML site and PDF into _book/
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
syntax/              Syntax-highlighting definitions for Part 21 files and EXPRESS
styles/              Stylesheet for the HTML edition and typography fixes for the PDF
tools/               Checks that validate the book against published EXPRESS schemas
docs/                The original PDF draft the book was converted from
.github/workflows/   CI: runs the checks, renders the book, deploys it to GitHub Pages
```

## Checking the book

Every entity name, listing and attribute claim is verified against the published AP242, AP214 and AP203 schemas, which are vendored under `tools/schemas/`.
CI runs these before rendering, so a wrong entity name or parameter count fails the build instead of reaching a reader.

```bash
python3 tools/check_book.py
python3 tools/check_appendix_b.py
```

See [tools/README.md](tools/README.md) for what each check covers.

## Contributing

Corrections, clarifications, and new material are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
