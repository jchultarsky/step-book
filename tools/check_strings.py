#!/usr/bin/env python3
"""Check the book's quoted magic strings against the published schemas.

The book repeatedly names a literal string and says whether a schema rule
fixes it or a recommended practice merely asks for it.  The first kind is
checkable: if a string is enforced by an EXPRESS schema, it appears in that
schema's text, almost always inside a WHERE clause or a global RULE.

This reports every single-quoted string the prose puts in inline code,
classified by whether the schemas contain it.  A string that appears in no
schema is not necessarily wrong -- most of the conventional strings come from
the CAx-IF recommended practices, which are not machine-readable here -- but
the book must not claim a schema enforces one of those.  The check therefore
fails only when a sentence claims schema enforcement for a string no schema
contains.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = sorted((ROOT / "tools" / "schemas").glob("*.exp"))

#: A single-quoted literal inside inline code: `'part definition'`
QUOTED = re.compile(r"`'([^'`\n]{2,60})'`")
#: Wording that claims a schema, rather than a practice, fixes the value.
CLAIMS_SCHEMA = re.compile(
    r"\bschema (?:enforces|requires|fixes|says|constrains)\b"
    r"|\b(?:global )?rule (?:enforces|requires|fixes|says|forbids|constrains)\b"
    r"|\benforce[sd] (?:with|by) a (?:global )?rule\b"
    r"|\ba rule on\b|\brule requires\b|\bfixed by the schema\b",
    re.I,
)


#: Strings that appear on a sentence claiming schema enforcement but are
#: deliberately named as the thing the schema does *not* fix.  Each needs a
#: reason; anything else on such a sentence is a defect.
CONTRASTED = {
    # Named as what edition 1 files wrote, in contrast to the edition 3 rule
    # requiring 'AUTOMOTIVE_DESIGN_LF' in the same sentence.
    "automotive_design",
}


def load_schema_text() -> str:
    return "\n".join(p.read_text(errors="replace") for p in SCHEMAS)


def sources() -> list[Path]:
    out = sorted((ROOT / "chapters").glob("*.qmd"))
    out += sorted((ROOT / "appendices").glob("*.qmd"))
    out += [ROOT / "index.qmd"]
    return [p for p in out if p.exists()]


def main() -> int:
    schema_text = load_schema_text().lower()
    problems: list[str] = []
    in_schema = absent = 0

    for path in sources():
        text = path.read_text()
        # Prose only; listings are checked by check_book.py.
        text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
        for lineno, line in enumerate(text.splitlines(), 1):
            claims = bool(CLAIMS_SCHEMA.search(line))
            for value in QUOTED.findall(line):
                if f"'{value}'".lower() in schema_text:
                    in_schema += 1
                    continue
                absent += 1
                if claims and value not in CONTRASTED:
                    problems.append(
                        f"{path.relative_to(ROOT)}:{lineno}: the sentence claims a "
                        f"schema fixes a string, and '{value}' is in no vendored "
                        f"schema\n      {line.strip()[:150]}"
                    )

    total = in_schema + absent
    if not problems:
        print(
            f"OK: {total} quoted strings checked; {in_schema} appear in a schema, "
            f"{absent} do not and none of those is claimed as schema-enforced."
        )
        return 0
    print(f"{len(problems)} strings claimed as schema-enforced but absent from every schema:\n")
    for problem in problems:
        print("  " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
