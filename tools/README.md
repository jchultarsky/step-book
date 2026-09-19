# Checking tools

These scripts keep the book honest.
They compare what the text claims against published EXPRESS schemas and against the example files the listings are drawn from, so an error in an entity name, an attribute order or a parameter count fails the build rather than reaching a reader.

All of them run in CI on every push and pull request.

## `check_book.py`

Three checks over every `.qmd` source:

1. Every simple Part 21 record in a `step` listing names an entity that exists in AP242, AP214 or AP203e2, and supplies a parameter count that at least one of those schemas declares for it. Complex records are checked for their component entity names, not their parameter counts.
2. Every entity name written in inline code in prose exists in one of those schemas, which catches typos and invented entities.
3. Every record in every file under `examples/` gets the same entity-name and parameter-count checks.

The script does not select a schema from `FILE_SCHEMA`, check scalar types or SELECT wrappers, evaluate WHERE or global rules, or validate geometry.
`check_references.py` separately checks reference targets and listing consistency; neither is a conformance validator.

```bash
python3 tools/check_book.py
```

## `check_appendix_b.py`

Appendix B lists each entity's attributes in the order a Part 21 record supplies them.
That is exactly what an EXPRESS schema settles, so every row's attribute names and order are checked against it, accepting either the flattened attributes or a complex block's own.
Parenthesised hints such as `(set)` are stripped before comparison and are not validated; rows the script cannot parse are skipped.

```bash
python3 tools/check_appendix_b.py
```

## `check_strings.py`

The book names literal strings constantly, and says of each whether a schema
rule fixes it or a recommended practice merely asks for it.
The first kind is checkable: an enforced string appears in the schema text.
This reports every quoted string in the prose and fails when a sentence claims
schema enforcement for one that no schema contains.

```bash
python3 tools/check_strings.py
```

Most conventional strings come from the CAx-IF recommended practices, which are
not machine-readable here, so a string absent from the schemas is not an error
by itself.
Claiming the schema enforces such a string is.
Exceptions, for sentences that name a string precisely to say the schema does
*not* fix it, are listed in the script with a reason.

## `check_availability.py`

The book says things like "AP242 adds this" and "that is in all three".
Those are decidable, and they have been one of its most error-prone kinds of
sentence.

```bash
python3 tools/check_availability.py
```

It fails on the two contradictions it can be sure of: a claim that an entity is
in all three protocols when a schema does not declare it, and a claim that one
is particular to AP242 when the older schemas declare it too.
Each claim is attributed to the entity nearest it, because a sentence often
names several and makes a claim about one.
Edition-qualified claims are skipped, since the vendored schemas are one
edition each.

## `check_listings.py`

Three separate errors came from one kind of drift: a record was removed from a
listing and its explanation still described it, or an explanation named a
record the listing never contained.

```bash
python3 tools/check_listings.py
```

For each Part 21 listing it collects the instance names defined, reads the
prose up to the next listing or heading, and checks every `#n` that prose
mentions against the listings above it and the example files.

## `check_references.py`

A listing shows a few records; what they refer to is printed beneath it at
render time by `filters/referenced-records.lua`, from the file the listing
names in `{.step source="…"}`.
This makes that promise hold.

```bash
python3 tools/check_references.py
```

It fails when a listing refers to a record it does not show and names no
source; when a record it shows differs from the same record in its source, so
excerpts cannot drift; when a record it refers to is in neither; and when any
reference, in a listing or anywhere in `examples/`, points at an instance of
an entity type its attribute does not admit in the file's schema.
That last check resolves SELECTs and aggregates through the schema, so a
`PCURVE` whose surface is a `DEFINITIONAL_REPRESENTATION`, or a usage record
pointing at an edge loop instead of a face, fails the build.

## `render_examples.py`

Draws the part figures in `figures/` from the example files: every edge
(lines, circles, B-splines), every vertex, and the outlines of cylinders,
cones, spheres and tori, which are not edges and are drawn in grey.
Assemblies are drawn by applying each component's
`ITEM_DEFINED_TRANSFORMATION`.

```bash
python3 tools/render_examples.py          # regenerate figures/*.svg
python3 tools/render_examples.py --check  # fail if a figure has drifted
```

## `express_schema.py`

The shared EXPRESS parser, also usable directly to look an entity up:

```bash
python3 tools/express_schema.py ap242 axis2_placement_3d
```

It recovers supertypes, explicit attributes with their types, and the underlying type of every TYPE declaration, and resolves inheritance into Part 21 order.
Multiple inheritance contributes every supertype's attributes even when the names repeat, which is why `DOCUMENT_FILE` takes six parameters and not four.

## `schemas/`

Published MIM long-form schemas, vendored from the [STEPcode](https://github.com/stepcode/stepcode) project so the checks are reproducible offline:

| File | Schema |
|------|--------|
| `ap242_mim_lf.exp` | AP242 managed model-based 3D engineering |
| `ap214e3.exp` | AP214 edition 3, `AUTOMOTIVE_DESIGN` |
| `ap203e2.exp` | AP203 edition 2 |
