"""Parse EXPRESS schemas (ISO 10303-11) far enough to answer questions about entities.

This is not a general EXPRESS implementation.  It recovers, for every ENTITY
declaration, the supertypes it inherits from and the explicit attributes it
declares, in order, so that the book's claims about entity names and attribute
order can be checked mechanically against a published schema.

Only the parts of the grammar the book depends on are handled: ENTITY headers
with SUBTYPE OF, the explicit-attribute list, and enough of DERIVE / INVERSE /
UNIQUE / WHERE to know where the explicit list ends.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

#: Sections that terminate the explicit-attribute list of an ENTITY.
_END_OF_EXPLICIT = re.compile(r"^\s*(DERIVE|INVERSE|UNIQUE|WHERE|END_ENTITY)\b", re.I)
_ENTITY_START = re.compile(r"^\s*ENTITY\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
_SUBTYPE_OF = re.compile(r"SUBTYPE\s+OF\s*\((.*?)\)", re.I | re.S)
_ATTRIBUTE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s*:\s*(.+?)\s*;\s*$",
    re.S,
)
_COMMENT_BLOCK = re.compile(r"\(\*.*?\*\)", re.S)
_COMMENT_LINE = re.compile(r"--[^\n]*")


@dataclass
class Attribute:
    name: str
    type_text: str
    optional: bool

    def __str__(self) -> str:
        return self.name


@dataclass
class Entity:
    name: str
    supertypes: list[str] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    abstract: bool = False


class Schema:
    """An EXPRESS schema, indexed by entity name (lower case)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.entities: dict[str, Entity] = {}
        self.types: set[str] = set()
        self._parse(self.path.read_text(errors="replace"))

    # -- parsing ---------------------------------------------------------

    def _parse(self, text: str) -> None:
        text = _COMMENT_BLOCK.sub(" ", text)
        text = _COMMENT_LINE.sub(" ", text)
        for match in re.finditer(r"\bTYPE\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.I):
            self.types.add(match.group(1).lower())

        lines = text.splitlines()
        i = 0
        while i < len(lines):
            start = _ENTITY_START.match(lines[i])
            if not start:
                i += 1
                continue
            name = start.group(1)
            # The ENTITY header runs until the first semicolon.
            header, i = self._collect_until_semicolon(lines, i)
            entity = Entity(name=name, abstract=bool(re.search(r"\bABSTRACT\b", header, re.I)))
            subtype = _SUBTYPE_OF.search(header)
            if subtype:
                entity.supertypes = [
                    s.strip() for s in subtype.group(1).split(",") if s.strip()
                ]
            # Explicit attributes follow, one statement per semicolon, until a
            # DERIVE / INVERSE / UNIQUE / WHERE / END_ENTITY line.
            while i < len(lines) and not _END_OF_EXPLICIT.match(lines[i]):
                if not lines[i].strip():
                    i += 1
                    continue
                statement, i = self._collect_until_semicolon(lines, i)
                attr = _ATTRIBUTE.match(statement)
                if not attr:
                    continue
                type_text = " ".join(attr.group(2).split())
                optional = bool(re.match(r"OPTIONAL\b", type_text, re.I))
                for nm in attr.group(1).split(","):
                    entity.attributes.append(
                        Attribute(nm.strip(), type_text, optional)
                    )
            while i < len(lines) and not re.match(r"^\s*END_ENTITY", lines[i], re.I):
                i += 1
            self.entities[name.lower()] = entity
            i += 1

    @staticmethod
    def _collect_until_semicolon(lines: list[str], i: int) -> tuple[str, int]:
        parts = []
        while i < len(lines):
            parts.append(lines[i])
            if ";" in lines[i]:
                i += 1
                break
            i += 1
        return " ".join(parts), i

    # -- queries ---------------------------------------------------------

    def has(self, name: str) -> bool:
        return name.lower() in self.entities

    def get(self, name: str) -> Entity | None:
        return self.entities.get(name.lower())

    def attribute_order(self, name: str) -> tuple[str, ...]:
        """Full attribute list of an entity, supertypes first, in Part 21 order.

        A Part 21 record lists inherited attributes before the entity's own,
        depth first through the supertype list.  Under multiple inheritance
        every supertype contributes its attributes even when two supertypes
        declare the same attribute name: ``DOCUMENT_FILE`` inherits ``name``
        and ``description`` from both ``DOCUMENT`` and ``CHARACTERIZED_OBJECT``
        and so takes six parameters, not four.  Only a diamond -- the same
        supertype reached by two paths -- contributes once.
        """
        names: list[str] = []
        self._collect_attributes(name, set(), names)
        return tuple(names)

    def _collect_attributes(
        self, name: str, visited: set[str], out: list[str]
    ) -> None:
        key = name.lower()
        if key in visited:
            return
        visited.add(key)
        entity = self.get(name)
        if entity is None:
            return
        for sup in entity.supertypes:
            self._collect_attributes(sup, visited, out)
        for attr in entity.attributes:
            out.append(attr.name)

    @lru_cache(maxsize=None)
    def ancestors(self, name: str) -> frozenset[str]:
        entity = self.get(name)
        if entity is None:
            return frozenset()
        out = set()
        for sup in entity.supertypes:
            out.add(sup.lower())
            out |= self.ancestors(sup)
        return frozenset(out)

    def subtypes_of(self, name: str) -> list[str]:
        target = name.lower()
        return sorted(
            e.name for e in self.entities.values() if target in self.ancestors(e.name)
        )


def load(which: str = "ap242") -> Schema:
    """Load one of the bundled reference schemas by short name."""
    here = Path(__file__).resolve().parent
    candidates = {
        "ap242": "ap242_mim_lf.exp",
        "ap214": "ap214e3.exp",
        "ap203": "ap203e2.exp",
    }
    return Schema(here / "schemas" / candidates[which])


if __name__ == "__main__":
    import sys

    schema = load(sys.argv[1] if len(sys.argv) > 2 else "ap242")
    name = sys.argv[-1]
    entity = schema.get(name)
    if entity is None:
        print(f"{name}: not in schema")
        raise SystemExit(1)
    print(f"ENTITY {entity.name}" + (" (ABSTRACT)" if entity.abstract else ""))
    if entity.supertypes:
        print("  SUBTYPE OF " + ", ".join(entity.supertypes))
    print("  attributes, in order:")
    for i, attr in enumerate(schema.attribute_order(entity.name), 1):
        print(f"    {i:2}. {attr}")
