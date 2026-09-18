#!/usr/bin/env python3
"""Check that every record a listing refers to exists, and is the right kind.

A listing in the book shows a few records of a file.  The records they refer to
are shown beneath it at render time (``filters/referenced-records.lua``), taken
from the example file the listing names in its ``source`` attribute:

    ```{.step source="bracket.step"}

This check makes that promise hold:

1.  A listing that refers to a record it does not show must name a source.
2.  Every record a listing shows is either the same record as in its source
    (whitespace aside), or a record written for the book whose number the
    source does not use.  So an excerpt cannot drift from its file, and a
    hand-written record cannot collide with one the reader will be shown.
3.  Every record a listing refers to is in the listing or in its source.
4.  Every reference, in a listing or in any file in ``examples/``, points at an
    instance of an entity type its attribute admits in the file's schema: a
    ``PCURVE``'s surface is a surface, a ``GEOMETRIC_ITEM_SPECIFIC_USAGE``'s
    item is a representation item.  A reference to the wrong record usually
    lands on the wrong kind of record, so this catches renumbering slips.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_book import records_in, split_parameters  # noqa: E402
from express_schema import Schema, load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
FENCE = re.compile(r"^```\s*(\{[^}]*\}|step)\s*$")
ATTRIBUTE = re.compile(r'(\w+)="([^"]*)"')
STRING = re.compile(r"'(?:[^']|'')*'")
REF = re.compile(r"#(\d+)")
GROUP = re.compile(r"([A-Z][A-Z0-9_]*)\s*\(")
TYPED_VALUE = re.compile(r"^[A-Z][A-Z0-9_]*\s*\(")


def normalise(record: str) -> str:
    """A record with whitespace outside strings removed, for comparison."""
    out, last = [], 0
    for match in STRING.finditer(record):
        out.append(re.sub(r"\s+", "", record[last:match.start()]))
        out.append(match.group(0))
        last = match.end()
    out.append(re.sub(r"\s+", "", record[last:]))
    return "".join(out)


def references(text: str) -> list[int]:
    return [int(n) for n in REF.findall(STRING.sub("''", text))]


def groups(record: str) -> list[tuple[str, str]]:
    """(entity, parameter text) for a simple record, or for each part of a complex one."""
    text = record.strip()
    if not text.startswith("("):
        match = GROUP.match(text)
        return [(match.group(1), text[match.end():-1])] if match else []
    out, i, inner = [], 0, text[1:-1]
    while i < len(inner):
        match = GROUP.match(inner, i)
        if not match:
            i += 1
            continue
        depth, j = 1, match.end()
        while j < len(inner) and depth:
            if inner[j] == "'":
                j = inner.index("'", j + 1)
                while inner[j + 1: j + 2] == "'":
                    j = inner.index("'", j + 2)
            elif inner[j] == "(":
                depth += 1
            elif inner[j] == ")":
                depth -= 1
            j += 1
        out.append((match.group(1), inner[match.end(): j - 1]))
        i = j
    return out


def schema_key(file_text: str) -> str:
    declared = re.search(r"FILE_SCHEMA\s*\(\s*\((.*?)\)\s*\)", file_text, re.S)
    name = declared.group(1).upper() if declared else ""
    if "AP242" in name:
        return "ap242"
    if "CONFIG_CONTROL" in name or "AP203" in name:
        return "ap203"
    return "ap214"


class Source:
    def __init__(self, path: Path):
        text = path.read_text(errors="replace")
        self.name = path.name
        self.schema = schema_key(text)
        self.records = {n: body for n, body in records_in(text.split("DATA;", 1)[1])}


def check_types(where: str, shown: dict[int, str], known: dict[int, str],
                schema: Schema, problems: list[str]) -> int:
    """Check each reference in ``shown`` against the attribute that holds it."""
    checked = 0
    for number, body in shown.items():
        parts = groups(body)
        complex_record = body.strip().startswith("(")
        for entity, parameter_text in parts:
            if complex_record:
                declared = schema.get(entity)
                attributes = declared.attributes if declared else []
            else:
                attributes = schema.attributes(entity)
            parameters = split_parameters(parameter_text) if parameter_text.strip() else []
            if len(parameters) != len(attributes):
                continue  # check_book.py reports parameter counts
            for parameter, attribute in zip(parameters, attributes):
                targets = references(parameter)
                if not targets or TYPED_VALUE.match(parameter):
                    continue
                admitted = schema.admits(attribute.type_text)
                if admitted is None:
                    continue
                for target in targets:
                    if target not in known:
                        continue
                    checked += 1
                    target_types = [e for e, _ in groups(known[target])]
                    if not admitted:
                        problems.append(
                            f"{where} #{number}: {entity}.{attribute.name} is "
                            f"{attribute.type_text}, but holds a reference #{target}"
                        )
                    elif not schema.is_a(target_types, admitted):
                        kind = " ".join(target_types)
                        article = "an" if kind[:1] in "AEIOU" else "a"
                        problems.append(
                            f"{where} #{number}: {entity}.{attribute.name} "
                            f"({attribute.type_text}) refers to #{target}, {article} {kind}"
                        )
    return checked


def iter_listings(path: Path):
    """Yield (line, attributes, body) for each Part 21 listing in a source file."""
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        fence = FENCE.match(lines[i].strip())
        if not fence or "step" not in fence.group(1):
            i += 1
            continue
        attributes = dict(ATTRIBUTE.findall(fence.group(1)))
        start, body = i + 1, []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"):
            body.append(lines[i])
            i += 1
        i += 1
        yield start, attributes, "\n".join(body)


def main() -> int:
    schemas = {key: load(key) for key in ("ap242", "ap214", "ap203")}
    sources = {p.name: Source(p) for p in sorted(EXAMPLES.glob("*.step"))}
    problems: list[str] = []
    listings = resolved = typed = 0

    for path in sorted((ROOT / "chapters").glob("*.qmd")) + sorted((ROOT / "appendices").glob("*.qmd")):
        for line, attributes, body in iter_listings(path):
            if "include" in attributes:
                continue
            shown = dict(records_in(body))
            if not shown:
                continue
            listings += 1
            where = f"{path.relative_to(ROOT)}:{line}"
            referred = {r for text in shown.values() for r in references(text)}
            missing = sorted(referred - set(shown))
            name = attributes.get("source")
            if name is None:
                if missing:
                    problems.append(
                        f"{where}: refers to {', '.join(f'#{n}' for n in missing)} "
                        f"without showing them; give the listing a source=\"…\""
                    )
                typed += check_types(where, shown, shown, schemas["ap242"], problems)
                continue
            source = sources.get(name)
            if source is None:
                problems.append(f"{where}: source=\"{name}\" is not a file in examples/")
                continue
            for number, text in shown.items():
                if number in source.records and normalise(text) != normalise(source.records[number]):
                    problems.append(
                        f"{where}: #{number} differs from #{number} in {name}\n"
                        f"      listing: {normalise(text)[:110]}\n"
                        f"      {name}: {normalise(source.records[number])[:110]}"
                    )
            for number in missing:
                if number in source.records:
                    resolved += 1
                else:
                    problems.append(f"{where}: refers to #{number}, which neither the listing nor {name} contains")
            known = {**source.records, **shown}
            typed += check_types(where, shown, known, schemas[source.schema], problems)

    for source in sources.values():
        typed += check_types(f"examples/{source.name}", source.records, source.records,
                             schemas[source.schema], problems)

    if problems:
        print(f"{len(problems)} problems:\n")
        for problem in problems:
            print("  " + problem)
        return 1
    print(
        f"OK: {listings} listings; {resolved} records they refer to found in their "
        f"sources; {typed} references of the right entity type."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
