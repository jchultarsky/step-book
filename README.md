# The STEP Book

[![Build and deploy book](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml/badge.svg)](https://github.com/jchultarsky/step-book/actions/workflows/publish.yml)

A practical, open-source guide to the STEP file format (ISO 10303): what a STEP file contains, how it is structured, and how to work with it.

- **Read online:** <https://jchultarsky.github.io/step-book/>
- **Download PDF:** <https://jchultarsky.github.io/step-book/The-STEP-Book.pdf>

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
chapters/            One .qmd file per chapter
examples/            STEP files referenced in the text
references.bib       Bibliography (BibTeX)
.github/workflows/   CI: renders the book and deploys it to GitHub Pages
```

## Contributing

Corrections, clarifications, and new material are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
