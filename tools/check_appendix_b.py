#!/usr/bin/env python3
"""Check Appendix B's attribute-order table against the published schemas.

Appendix B lists, for each entity, its attributes in the order a Part 21 record
supplies them.  That claim is exactly what an EXPRESS schema settles, so every
row can be checked.  Rows whose entity is a header entity (defined by Part 21,
not by a schema) or that carry the "and subtypes" wording are reported as
skipped rather than failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from express_schema import load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APPENDIX = ROOT / "appendices" / "b-entity-reference.qmd"

#: Entities defined by Part 21 itself, which no MIM schema declares.
HEADER_ENTITIES = {"FILE_DESCRIPTION", "FILE_NAME", "FILE_SCHEMA"}
#: Parenthesised hints in the attribute column -- "(list)", "(set)",
#: "(list of lists)", "(in precedence order)" -- and a trailing derived marker.
HINT = re.compile(r"\s*\([^)]*\)|\s*\*$")
ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")
ENTITY_CELL = re.compile(r"`([A-Z][A-Z0-9_]*)`")


#: A row that defers to another entity rather than listing attributes.
DEFERS = re.compile(r"^\s*(as|same as)\b", re.I)


def normalise(cell: str) -> list[str] | None:
    """Attribute names claimed by a table cell, or None if it makes no claim."""
    cell = cell.strip()
    if cell in {"—", "-", ""} or DEFERS.match(cell):
        return None
    # Strip parenthesised hints from the whole cell before splitting, so that
    # a hint containing a comma does not look like two attributes.
    cell = HINT.sub("", cell)
    names = []
    for part in cell.split(","):
        part = part.strip().strip("*`_ ")
        if not part:
            continue
        # A trailing prose annotation such as "dimensions `*` or explicit".
        part = re.split(r"\s+(?:or|and)\s+", part)[0].strip().strip("*`_ ")
        if part and re.fullmatch(r"[a-z][a-z0-9_]*", part):
            names.append(part)
    return names or None


def main() -> int:
    schemas = {name: load(name) for name in ("ap242", "ap214", "ap203")}
    checked = skipped = 0
    problems: list[str] = []

    for lineno, line in enumerate(APPENDIX.read_text().splitlines(), 1):
        row = ROW.match(line)
        if not row:
            continue
        entity_cell, attrs_cell, _ = row.groups()
        if entity_cell.strip() in {"Entity", "---"} or set(entity_cell.strip()) <= {"-", " "}:
            continue
        match = ENTITY_CELL.search(entity_cell)
        if not match:
            continue
        name = match.group(1)
        where = f"{APPENDIX.relative_to(ROOT)}:{lineno} {name}"
        if name in HEADER_ENTITIES:
            skipped += 1
            continue
        claimed = normalise(attrs_cell)
        if claimed is None:
            skipped += 1
            continue
        found = [k for k, s in schemas.items() if s.has(name)]
        if not found:
            problems.append(f"{where}: in no reference schema")
            continue
        checked += 1
        actual_variants = {k: list(schemas[k].attribute_order(name)) for k in found}
        if any(claimed == v for v in actual_variants.values()):
            continue
        # A type that appears only inside a complex instance carries just the
        # attributes it declares itself; the appendix lists those.
        own = {
            k: [a.name for a in schemas[k].get(name).attributes] for k in found
        }
        if any(claimed == v for v in own.values()):
            continue
        # "and subtypes" rows list only the supertype's own attributes.
        if "and subtypes" in entity_cell:
            skipped += 1
            checked -= 1
            continue
        detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in actual_variants.items())
        problems.append(
            f"{where}\n      claims: {', '.join(claimed)}\n      schema: {detail}"
        )

    if not problems:
        print(f"OK: {checked} entity rows match the schemas ({skipped} skipped).")
        return 0
    print(f"{len(problems)} mismatched rows ({checked} checked, {skipped} skipped):\n")
    for problem in problems:
        print("  " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
