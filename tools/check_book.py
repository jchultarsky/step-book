#!/usr/bin/env python3
"""Check the book's factual claims about STEP against published EXPRESS schemas.

Three checks run over the .qmd sources:

1.  Every Part 21 record in a ``step`` listing names an entity that exists in
    AP242, AP214 or AP203e2.  Simple records must also supply a parameter
    count that at least one of those schemas declares; complex records are
    checked for their component entity names only.
2.  Every entity name written in inline code in prose exists in one of those
    schemas.  This catches typos and invented entities.
3.  Every record in every file under ``examples/`` gets the same checks.

This is not full schema validation: FILE_SCHEMA selection, scalar types,
SELECT wrappers, WHERE and global rules and geometric validity are outside
this script.

Whether a listing matches its file, and whether the records it refers to exist
and are of the right type, is ``check_references.py``.

Exit status is non-zero if any check fails, so this can gate CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from express_schema import Schema, load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

#: A whole Part 21 record: ``#12 = ENTITY_NAME(params);``
RECORD = re.compile(r"#(\d+)\s*=\s*(.+?);\s*$", re.S)
#: A simple (non-complex) record's entity name and parameter text.
SIMPLE = re.compile(r"^([A-Z][A-Z0-9_]*)\s*\((.*)\)$", re.S)
#: A complex record is a parenthesised run of ``TYPE(params)`` groups.  Only
#: groups at the top level of that run are entity types; a name inside a
#: group's parameters is a typed value such as ``LENGTH_MEASURE(6.)``.
#: Inline code in prose that looks like an entity name.
INLINE_ENTITY = re.compile(r"`([A-Z][A-Z0-9_]{3,})`")

#: Names that appear in inline code but are not entities.
NOT_ENTITIES = {
    # Part 21 syntax and header keywords.
    "ISO", "HEADER", "DATA", "ENDSEC", "FILE_DESCRIPTION", "FILE_NAME",
    "FILE_SCHEMA", "FILE_POPULATION", "SECTION_LANGUAGE", "SECTION_CONTEXT",
    "ANCHOR", "REFERENCE", "SIGNATURE",
    # Schema names, not entity names.
    "AUTOMOTIVE_DESIGN", "CONFIG_CONTROL_DESIGN",
    "AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF",
    "AP203_CONFIGURATION_CONTROLLED_3D_DESIGN_OF_MECHANICAL_PARTS_AND_ASSEMBLIES",
    "AP203_CONFIGURATION_CONTROLLED_3D_DESIGN_OF_MECHANICAL_PARTS_AND_ASSEMBLIES_MIM_LF",
    "SCHEMA_POPULATION",
    # EXPRESS keywords.
    "ENTITY", "END_ENTITY", "SUBTYPE", "SUPERTYPE", "ABSTRACT", "OPTIONAL",
    "DERIVE", "INVERSE", "UNIQUE", "WHERE", "SELECT", "TYPE", "END_TYPE",
    "ONEOF", "ANDOR", "LIST", "SET", "BAG", "ARRAY", "STRING", "REAL",
    "SCHEMA", "END_SCHEMA", "RULE", "END_RULE", "FUNCTION", "END_FUNCTION",
    "INTEGER", "BOOLEAN", "LOGICAL", "BINARY", "NUMBER", "SELF",
    # Defined types and measures used as values, not entity instances.
    "LENGTH_MEASURE", "PLANE_ANGLE_MEASURE", "POSITIVE_LENGTH_MEASURE",
    "COUNT_MEASURE", "PARAMETER_VALUE", "AREA_MEASURE", "VOLUME_MEASURE",
    "MASS_MEASURE", "DESCRIPTIVE_MEASURE", "TEXT", "LABEL", "IDENTIFIER",
}


class Report:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.checked = 0

    def fail(self, where: str, message: str) -> None:
        self.problems.append(f"{where}: {message}")

    def ok(self) -> bool:
        return not self.problems


def complex_parts(record: str) -> list[str]:
    """Entity type names of a complex instance, ignoring typed values inside."""
    inner = record.strip()
    if not (inner.startswith("(") and inner.endswith(")")):
        return []
    inner = inner[1:-1]
    names, i, in_string = [], 0, False
    while i < len(inner):
        ch = inner[i]
        if in_string:
            if ch == "'":
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            i += 1
            continue
        match = re.match(r"([A-Z][A-Z0-9_]*)\s*\(", inner[i:])
        if match:
            names.append(match.group(1))
            # Skip the whole parameter list of this group.
            depth, j = 0, i + match.end() - 1
            while j < len(inner):
                if inner[j] == "'":
                    j += 1
                    while j < len(inner) and inner[j] != "'":
                        j += 1
                elif inner[j] == "(":
                    depth += 1
                elif inner[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            i = j + 1
            continue
        i += 1
    return names


def split_parameters(text: str) -> list[str]:
    """Split a Part 21 parameter list on top-level commas."""
    out, depth, current, in_string = [], 0, [], False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    current.append("''")
                    i += 2
                    continue
                in_string = False
            current.append(ch)
        elif ch == "'":
            in_string = True
            current.append(ch)
        elif ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail or out:
        out.append(tail)
    return out


def iter_listings(path: Path, language: str = "step"):
    """Yield (start_line, body) for each fenced block of the given language."""
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("```") and language in stripped[3:]:
            start = i + 1
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            yield start, "\n".join(body)
        i += 1


def records_in(text: str):
    """Yield (instance_number, record_text) for complete records in a listing."""
    # Drop comments, which the book uses to elide records.
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    buffer: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*(ISO-10303-21|END-ISO-10303-21|HEADER|DATA|ENDSEC)\b", line):
            continue
        if re.match(r"^\s*(FILE_DESCRIPTION|FILE_NAME|FILE_SCHEMA|FILE_POPULATION|SECTION_LANGUAGE|SECTION_CONTEXT)\b", line):
            buffer = []
            continue
        buffer.append(line)
        joined = " ".join(buffer)
        if joined.rstrip().endswith(";"):
            match = RECORD.match(joined.strip())
            if match:
                yield int(match.group(1)), match.group(2).strip()
            buffer = []


def check_record(name: str, params: str, schemas: dict[str, Schema]) -> str | None:
    """Return an error message if the record is inconsistent with every schema."""
    found_in = [k for k, s in schemas.items() if s.has(name)]
    if not found_in:
        return f"entity {name} is in no reference schema"
    counts = set()
    for key in found_in:
        counts.add(len(schemas[key].attribute_order(name)))
    actual = len(split_parameters(params)) if params.strip() else 0
    if actual not in counts:
        expected = " or ".join(str(c) for c in sorted(counts))
        return (
            f"{name} has {actual} parameters, schema declares {expected} "
            f"({', '.join(found_in)})"
        )
    return None


def check_listings(paths: list[Path], schemas: dict[str, Schema], report: Report) -> None:
    for path in paths:
        for start, body in iter_listings(path):
            for number, record in records_in(body):
                where = f"{path.relative_to(ROOT)}:~{start} #{number}"
                if record.startswith("("):
                    # Complex instance: check each type group exists.
                    for name in complex_parts(record):
                        if not any(s.has(name) for s in schemas.values()):
                            report.fail(where, f"entity {name} is in no reference schema")
                        report.checked += 1
                    continue
                simple = SIMPLE.match(record)
                if not simple:
                    continue
                report.checked += 1
                problem = check_record(simple.group(1), simple.group(2), schemas)
                if problem:
                    report.fail(where, problem)


def check_prose_entities(paths: list[Path], schemas: dict[str, Schema], report: Report) -> None:
    for path in paths:
        text = path.read_text()
        # Ignore fenced blocks; they are checked as listings.
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
        seen: set[str] = set()
        for name in INLINE_ENTITY.findall(text):
            if name in NOT_ENTITIES or name in seen:
                continue
            seen.add(name)
            report.checked += 1
            if not any(s.has(name) for s in schemas.values()):
                report.fail(
                    str(path.relative_to(ROOT)),
                    f"prose names `{name}`, which is in no reference schema",
                )


def check_examples(schemas: dict[str, Schema], report: Report) -> None:
    """Check bundled examples for entity names and simple-record parameter counts."""
    for path in sorted((ROOT / "examples").glob("*.step")):
        text = path.read_text()
        data = text.split("DATA;", 1)[-1]
        for number, record in records_in(data):
            where = f"{path.relative_to(ROOT)} #{number}"
            if record.startswith("("):
                for name in complex_parts(record):
                    if not any(s.has(name) for s in schemas.values()):
                        report.fail(where, f"entity {name} is in no reference schema")
                    report.checked += 1
                continue
            simple = SIMPLE.match(record)
            if not simple:
                report.fail(where, f"could not parse record: {record[:60]}")
                continue
            report.checked += 1
            problem = check_record(simple.group(1), simple.group(2), schemas)
            if problem:
                report.fail(where, problem)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    schemas = {name: load(name) for name in ("ap242", "ap214", "ap203")}
    sources = sorted((ROOT / "chapters").glob("*.qmd")) + sorted(
        (ROOT / "appendices").glob("*.qmd")
    ) + [ROOT / "index.qmd"]
    sources = [p for p in sources if p.exists()]

    report = Report()
    check_listings(sources, schemas, report)
    check_prose_entities(sources, schemas, report)
    check_examples(schemas, report)

    if report.ok():
        print(f"OK: {report.checked} checks passed across {len(sources)} sources.")
        return 0
    print(f"{len(report.problems)} problems ({report.checked} checks):\n")
    for problem in report.problems:
        print("  " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
