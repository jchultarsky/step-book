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
