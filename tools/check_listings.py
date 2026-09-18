#!/usr/bin/env python3
"""Check that a listing and the prose around it agree about which records exist.

Three separate errors in this book came from the same drift: a record was
removed from a listing and the explanation still described it, or an
explanation named a record the listing never contained.  Both are decidable.

For each fenced ``step`` listing, this collects the instance names it defines,
then reads the prose that follows it up to the next listing or heading and
checks every ``#n`` that prose mentions.  A mention is satisfied if the record
is defined in that listing, in an earlier listing of the same chapter, or in
one of the example files, since chapters often refer back to records the
reader has already met.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFINES = re.compile(r"^\s*#(\d+)\s*=", re.M)
MENTIONS = re.compile(r"`#(\d+)`")
FENCE = re.compile(r"^```")
HEADING = re.compile(r"^#{1,6}\s")


def example_instances() -> set[str]:
    out: set[str] = set()
    for path in (ROOT / "examples").glob("*.step"):
        out |= set(DEFINES.findall(path.read_text(errors="replace")))
    return out


def main() -> int:
    known_examples = example_instances()
    problems: list[str] = []
    checked = 0

    for path in sorted((ROOT / "chapters").glob("*.qmd")) + sorted(
        (ROOT / "appendices").glob("*.qmd")
    ):
        lines = path.read_text().splitlines()
        defined_so_far: set[str] = set()
        i = 0
        while i < len(lines):
            if not (FENCE.match(lines[i]) and "step" in lines[i]):
                i += 1
                continue
            # Collect the listing.
            start, body = i + 1, []
            i += 1
            while i < len(lines) and not FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1
            here = set(DEFINES.findall("\n".join(body)))
            defined_so_far |= here
            # Read the prose that explains it.
            prose = []
            j = i
            while j < len(lines) and not FENCE.match(lines[j]) and not HEADING.match(lines[j]):
                prose.append(lines[j])
                j += 1
            for number in dict.fromkeys(MENTIONS.findall("\n".join(prose))):
                checked += 1
                if number in defined_so_far or number in known_examples:
                    continue
                problems.append(
                    f"{path.relative_to(ROOT)}: prose after the listing at line "
                    f"{start} names `#{number}`, which no listing above it "
                    f"defines and no example file contains"
                )

    if not problems:
        print(f"OK: {checked} record references in prose all resolve to a listing or an example file.")
        return 0
    print(f"{len(problems)} record references with nothing behind them:\n")
    for problem in dict.fromkeys(problems):
        print("  " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
