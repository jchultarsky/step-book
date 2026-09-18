# orange-book, vendored

A copy of the `orange-book` Typst book format bundled with Quarto 1.10.18
(`share/extension-subtrees/orange-book`), kept here so the PDF can be fixed
in two places the format does not expose as options.  The sample images of
the upstream `template/` folder are left out.

Changes from upstream:

- `typst/packages/preview/orange-book/0.7.1/lib.typ`: chapters and parts
  start with `pagebreak(weak: true)` instead of `pagebreak(to: "odd")`.
  The book is read on screen, and starting every chapter on a right-hand
  page left sixteen blank pages.
- Same file: `book()` defaults to `outline-small-depth: 1`, so a part page
  lists its chapters but not their sections.  At the upstream default of 2,
  Part I's list was taller than the page and was drawn over the part title.
  (Quarto fills in its own copy of `typst-show.typ`, not this one, so the
  setting has to be the package's default rather than an argument there.)

- Same file: the part title box is 52% wide rather than 60%, so a wide
  numeral such as III does not run into it.

When upgrading Quarto, compare against the bundled copy and reapply these.
The licences of the extension (Posit, MIT), the orange-book package (MIT)
and marginalia (Unlicense) are kept alongside the files.
