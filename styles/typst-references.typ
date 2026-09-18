// Chapter references in the PDF edition.
//
// The book template numbers a level-1 heading as "3." so that the chapter
// title reads "3. The Header".  Typst reuses that same numbering when it
// renders a reference, which makes a cross-reference read "Chapter 3." in the
// middle of a sentence.  This rule drops the trailing separator for references
// to chapters and appendices, leaving sub-section references untouched.
#show ref: it => {
  let el = it.element
  if el != none and el.func() == heading and el.level == 1 and el.numbering != none {
    let nums = counter(heading).at(el.location())
    let shown = if type(el.numbering) == function {
      (el.numbering)(..nums)
    } else {
      numbering(el.numbering, ..nums)
    }
    let label = if type(shown) == str { shown.trim(".", at: end) } else { shown }
    let supplement = if it.supplement == auto { el.supplement } else { it.supplement }
    link(el.location())[#supplement #label]
  } else {
    it
  }
}

// Names in tables.
//
// Entity and attribute names like SURFACE_OF_LINEAR_EXTRUSION or
// application_interpreted_model_schema_name are single unbreakable words, so
// in a narrow column they run into the next one.  Give every underscore in a
// table a break opportunity after it.  Code listings are not tables and are
// untouched.
#show table: it => {
  show "_": "_" + "\u{200B}"
  it
}

// Table cells are narrow; justifying them opens wide gaps between words.
#show table: set par(justify: false)

// Definition lists (the glossary).  The default layout hangs the term into the
// margin and sets the description beside it, where a long term overprints it.
// Put the term on its own line and indent the description beneath it.
#show terms.item: it => block(below: 0.9em, breakable: false)[
  #strong(it.term)
  #block(above: 0.3em, inset: (left: 1.2em), it.description)
]
