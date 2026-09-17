# Contributing

Thank you for helping improve The STEP Book. Small fixes and large chapters are equally welcome.

## Quick fixes

Every page of the published book has an **Edit this page** link that opens the source file on GitHub. For typos and small clarifications, editing there and opening a pull request is enough.

## Larger changes

1. Open an issue first to describe what you want to add or change, so we can agree on scope before you invest time.
2. Fork the repository and create a branch.
3. Run `quarto preview` while writing; run `quarto render` before opening the pull request to confirm both the HTML and the PDF build.
4. Open a pull request. CI renders the book for every pull request.

## Writing guidelines

- **One sentence per line.** Start each sentence on a new line in the source. Paragraphs are still separated by blank lines. This keeps diffs readable and reviews focused.
- **Cite the standard.** Add sources to `references.bib` and cite them with `[@key]`. Prefer the current edition of each ISO 10303 part.
- **Use the standard's terminology.** Write entity names exactly as they appear in a Part 21 file, in backticks: `AXIS2_PLACEMENT_3D`.
- **Keep examples real.** Listings should be complete, valid files unless the text says otherwise. Put reusable files in `examples/`.
- **Cross-reference, don't repeat.** Give sections, figures, tables, and listings an identifier (`{#sec-...}`, `{#tbl-...}`, `{#lst-...}`) and refer to them with `@sec-...`.
- **Check both outputs.** Some Markdown renders differently in HTML and in the PDF. Look at both before submitting.

## License

By contributing you agree that your contributions are licensed under the repository's [MIT license](LICENSE).
