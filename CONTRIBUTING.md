# Contributing

Thank you for helping improve *Inside the STEP File*. Small fixes and large chapters are equally welcome.

## Quick fixes

Every page of the published book has an **Edit this page** link that opens the source file on GitHub. For typos and small clarifications, editing there and opening a pull request is enough.

## Larger changes

1. Open an issue first to describe what you want to add or change, so we can agree on scope before you invest time.
2. Fork the repository and create a branch.
3. Run `quarto preview` while writing; run `quarto render` before opening the pull request to confirm both the HTML and the PDF build.
4. Open a pull request. CI renders the book for every pull request.

## Writing guidelines

- **One sentence per line.** Start each sentence on a new line in the source. Paragraphs are still separated by blank lines. This keeps diffs readable and reviews focused.
- **Cite the standard by part and edition.** Write "ISO 10303-21" or "Part 21" in the text and name the edition where it matters. New sources go in Appendix C, which is prose rather than a citation list.
- **Use the standard's terminology.** Write entity names exactly as they appear in a Part 21 file, in backticks: `AXIS2_PLACEMENT_3D`.
- **Keep examples real.** Listings are excerpts of the files in `examples/`, which were exported by Open CASCADE. If a listing is written to a published pattern rather than exported, the text must say so.
- **Name each listing's file.** Open a Part 21 listing with ```` ```{.step source="bracket.step"} ````. The records it refers to but does not show are then printed beneath it from that file, and `tools/check_references.py` fails if one is missing, of the wrong type, or if the listing no longer matches the file. A record written for the book must use a number the file does not.
- **Cross-reference, don't repeat.** Give sections, figures, tables, and listings an identifier (`{#sec-...}`, `{#tbl-...}`, `{#lst-...}`) and refer to them with `@sec-...`.
- **Check both outputs.** Some Markdown renders differently in HTML and in the PDF. Look at both before submitting.

## License

By contributing you agree that your contributions are licensed under the repository's [MIT license](LICENSE).
