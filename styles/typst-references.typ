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
