# Checking tools

These scripts keep the book honest.
They compare what the text claims against published EXPRESS schemas and against the example files the listings are drawn from, so an error in an entity name, an attribute order or a parameter count fails the build rather than reaching a reader.

Both run in CI on every push and pull request.

## `check_book.py`

Three checks over every `.qmd` source:

1. Every Part 21 record in a `step` listing names an entity that exists in AP242, AP214 or AP203e2, and supplies the number of parameters the schema declares for it.
2. Every entity name written in inline code in prose exists in one of those schemas, which catches typos and invented entities.
3. Every record in every file under `examples/` satisfies its schema.

```bash
python3 tools/check_book.py
```

## `check_appendix_b.py`

Appendix B lists each entity's attributes in the order a Part 21 record supplies them.
That is exactly what an EXPRESS schema settles, so every row is checked against it.

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

## `express_schema.py`

The shared EXPRESS parser, also usable directly to look an entity up:

```bash
python3 tools/express_schema.py ap242 axis2_placement_3d
```

It recovers supertypes and explicit attributes and resolves inheritance into Part 21 order.
Multiple inheritance contributes every supertype's attributes even when the names repeat, which is why `DOCUMENT_FILE` takes six parameters and not four.

## `schemas/`

Published MIM long-form schemas, vendored from the [STEPcode](https://github.com/stepcode/stepcode) project so the checks are reproducible offline:

| File | Schema |
|------|--------|
| `ap242_mim_lf.exp` | AP242 managed model-based 3D engineering |
| `ap214e3.exp` | AP214 edition 3, `AUTOMOTIVE_DESIGN` |
| `ap203e2.exp` | AP203 edition 2 |
