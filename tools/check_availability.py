#!/usr/bin/env python3
"""Check the book's claims about which application protocol has which entity.

The book says things like "AP242 adds X", "X is in all three" and "X is absent
from AP214".  Those are decidable: either a schema declares the entity or it
does not.  This has been one of the book's most error-prone kinds of sentence,
so it is worth failing the build over.

The check is deliberately narrow, because a false positive here would push an
author to "correct" a sentence that is already right.  It fails only on two
contradictions it can be sure of:

*   a sentence says an entity is in all three protocols when some schema does
    not declare it; and
*   a sentence says an entity is particular to AP242, or absent from an older
    protocol, when that older schema declares it after all.

Everything else is reported as context rather than failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILES = {
    "AP242": ROOT / "tools" / "schemas" / "ap242_mim_lf.exp",
    "AP214": ROOT / "tools" / "schemas" / "ap214e3.exp",
    "AP203": ROOT / "tools" / "schemas" / "ap203e2.exp",
}

ENTITY = re.compile(r"`([A-Z][A-Z0-9_]{3,})`")
#: "in all three", "all three protocols define", "all three schemas"
ALL_THREE = re.compile(r"\ball three\b", re.I)
#: A claim that something is peculiar to AP242, or missing from an older AP.
AP242_ONLY = re.compile(
    r"\bAP242 adds\b|\bAP242[- ]only\b|\bonly in AP242\b"
    r"|\babsent from AP(?:203|214)\b|\bnot in AP(?:203|214)\b"
    r"|\bdoes not exist in AP(?:203|214)\b",
    re.I,
)
#: An edition-qualified claim ("not in AP203 first edition") cannot be checked
#: against the vendored schemas, which are one edition each.
EDITION_QUALIFIED = re.compile(
    r"\b(?:first|second|third|fourth) edition\b|\bedition [1-4]\b", re.I)


def nearest(line: str, claim: re.Match, entities: list[str]) -> str | None:
    """The entity a claim is about: the one closest to the claim's words.

    A sentence often names several entities and makes a claim about one of
    them -- "X does not exist in AP214, where a plain Y does the job" -- so
    attributing the claim to every name on the line invents contradictions.
    """
    mid = (claim.start() + claim.end()) // 2
    best, best_distance = None, None
    for entity in entities:
        for hit in re.finditer(re.escape(f"`{entity}`"), line):
            distance = abs((hit.start() + hit.end()) // 2 - mid)
            if best_distance is None or distance < best_distance:
                best, best_distance = entity, distance
    return best


#: Names that are not entities, or are entities the schemas spell differently.
SKIP = {
    "FILE_DESCRIPTION", "FILE_NAME", "FILE_SCHEMA", "FILE_POPULATION",
    "SECTION_LANGUAGE", "SECTION_CONTEXT", "SCHEMA_POPULATION", "ANCHOR",
    "REFERENCE", "SIGNATURE", "HEADER", "DATA", "ENDSEC", "BOOLEAN", "LOGICAL",
    "INTEGER", "STRING", "REAL", "BINARY", "SELECT", "ENTITY", "TYPE", "LIST",
    "SET", "BAG", "ARRAY", "WHERE", "DERIVE", "INVERSE", "UNIQUE", "ONEOF",
    "ANDOR", "SUBTYPE", "SUPERTYPE", "ABSTRACT", "OPTIONAL", "SCHEMA",
    "AUTOMOTIVE_DESIGN", "CONFIG_CONTROL_DESIGN", "NULL_STYLE",
}


def declares(text: str, entity: str) -> bool:
    return re.search(rf"^\s*ENTITY\s+{entity.lower()}\b", text, re.M | re.I) is not None


def main() -> int:
    schemas = {ap: p.read_text(errors="replace") for ap, p in SCHEMA_FILES.items()}
    sources = sorted((ROOT / "chapters").glob("*.qmd"))
    sources += sorted((ROOT / "appendices").glob("*.qmd"))
    sources += [ROOT / "index.qmd"]

    problems: list[str] = []
    context: list[str] = []
    checked = 0

    for path in [p for p in sources if p.exists()]:
        text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"),
                      path.read_text(), flags=re.S)
        for lineno, line in enumerate(text.splitlines(), 1):
            entities = [e for e in dict.fromkeys(ENTITY.findall(line)) if e not in SKIP]
            if not entities:
                continue
            for claim, kind in ((ALL_THREE.search(line), "all"),
                                (AP242_ONLY.search(line), "242")):
                if claim is None:
                    continue
                # An edition-qualified claim ("not in AP203 first edition")
                # cannot be settled against schemas that are one edition each.
                # Skip only that claim, not everything else on the line.
                window = line[max(0, claim.start() - 60):claim.end() + 60]
                if EDITION_QUALIFIED.search(window):
                    continue
                entity = nearest(line, claim, entities)
                if entity is None:
                    continue
                where = [ap for ap, t in schemas.items() if declares(t, entity)]
                if not where:
                    continue  # check_book.py already covers unknown entities
                checked += 1
                where_text = ", ".join(sorted(where))
                if kind == "all" and len(where) < 3:
                    problems.append(
                        f"{path.relative_to(ROOT)}:{lineno}: says all three have "
                        f"`{entity}`, but only {where_text} declares it\n"
                        f"      {line.strip()[:150]}"
                    )
                elif kind == "242" and len(where) == 3:
                    problems.append(
                        f"{path.relative_to(ROOT)}:{lineno}: treats `{entity}` as "
                        f"particular to AP242, but all three declare it\n"
                        f"      {line.strip()[:150]}"
                    )
                else:
                    context.append(f"  {path.relative_to(ROOT)}:{lineno} `{entity}` -> {where_text}")

    if not problems:
        print(f"OK: {checked} availability claims checked against the three schemas.")
        for line in context[:12]:
            print(line)
        return 0
    print(f"{len(problems)} availability claims contradicted by the schemas:\n")
    for problem in problems:
        print("  " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
