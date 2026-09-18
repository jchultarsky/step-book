#!/usr/bin/env python3
"""Draw the example parts as wireframes, straight from their STEP files.

Each figure shows three things, drawn so they cannot be confused:

*   every edge in the file, as a dark line: lines, circles and B-splines
    evaluated from the records the chapters quote;
*   every vertex, as a dot;
*   the outline of each curved face, as a thin grey line.  An outline is where
    a cylinder, cone, sphere or torus turns away from the viewer.  It is not an
    edge and nothing in the file records it, which is exactly why it is drawn
    differently: a sphere with no edges would otherwise be an empty picture.

Assemblies are drawn by applying each component's placement, as a reader
would, from the ``ITEM_DEFINED_TRANSFORMATION`` records.

The figures in ``figures/`` are generated, not drawn.  Run this after changing
an example file; CI runs it with ``--check`` and fails if a committed figure no
longer matches the file it was drawn from.

    python3 tools/render_examples.py          # write figures/*.svg
    python3 tools/render_examples.py --check  # fail on drift
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_book import records_in, split_parameters  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "figures"

#: (example file, figure name, draw as assembly)
FIGURE_LIST = [
    ("block.step", "block", False),
    ("pin.step", "pin", False),
    ("bracket.step", "bracket", False),
    ("sphere.step", "sphere", False),
    ("torus.step", "torus", False),
    ("cone.step", "cone", False),
    ("clamp.step", "clamp", True),
]

AZIMUTH = math.radians(35)
ELEVATION = math.radians(25)
WIDTH, MAX_HEIGHT, PAD = 760, 420, 24
EDGE_COLOUR, OUTLINE_COLOUR = "#1f2328", "#8c959f"

Vec = tuple[float, float, float]


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a: Vec) -> Vec:
    return scale(a, 1 / math.sqrt(dot(a, a)))


# Screen axes of the view, and the direction it looks along.
SCREEN_U: Vec = (math.cos(AZIMUTH), -math.sin(AZIMUTH), 0.0)
SCREEN_V: Vec = (math.sin(AZIMUTH) * math.sin(ELEVATION),
                 math.cos(AZIMUTH) * math.sin(ELEVATION), -math.cos(ELEVATION))
VIEW: Vec = unit(cross(SCREEN_U, SCREEN_V))


class Frame:
    """An AXIS2_PLACEMENT_3D: origin and orthonormal axes."""

    def __init__(self, origin: Vec, x: Vec, y: Vec, z: Vec):
        self.o, self.x, self.y, self.z = origin, x, y, z

    def point(self, local: Vec) -> Vec:
        return add(self.o, add(scale(self.x, local[0]), add(scale(self.y, local[1]), scale(self.z, local[2]))))

    def vector(self, local: Vec) -> Vec:
        return add(scale(self.x, local[0]), add(scale(self.y, local[1]), scale(self.z, local[2])))

    def local(self, p: Vec) -> Vec:
        d = add(p, scale(self.o, -1))
        return (dot(d, self.x), dot(d, self.y), dot(d, self.z))


class Placement:
    """Maps a component's coordinates into the assembly's: from frame a to frame b."""

    def __init__(self, source: Frame, target: Frame):
        self.source, self.target = source, target

    def point(self, p: Vec) -> Vec:
        return self.target.point(self.source.local(p))

    def vector(self, v: Vec) -> Vec:
        return self.target.vector((dot(v, self.source.x), dot(v, self.source.y), dot(v, self.source.z)))


IDENTITY = Placement(Frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                     Frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)))


def refs(text: str) -> list[int]:
    return [int(n) for n in re.findall(r"#(\d+)", re.sub(r"'(?:[^']|'')*'", "''", text))]


def numbers(text: str) -> list[float]:
    return [float(n) for n in re.findall(r"[-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?", text)]


class Model:
    def __init__(self, path: Path):
        text = path.read_text(errors="replace")
        self.records = {n: " ".join(body.split()) for n, body in records_in(text.split("DATA;", 1)[1])}

    def entity(self, n: int) -> str:
        return re.match(r"\(?\s*([A-Z_0-9]+)", self.records[n]).group(1)

    def params(self, n: int) -> list[str]:
        body = self.records[n]
        return split_parameters(body[body.index("(") + 1: body.rindex(")")])

    def point(self, n: int) -> Vec:
        return tuple(numbers(self.params(n)[1]))  # type: ignore[return-value]

    def direction(self, n: int) -> Vec:
        return unit(tuple(numbers(self.params(n)[1])))  # type: ignore[arg-type]

    def frame(self, n: int) -> Frame:
        _, location, axis, ref = self.params(n)
        origin = self.point(refs(location)[0])
        z = self.direction(refs(axis)[0]) if axis != "$" else (0.0, 0.0, 1.0)
        x = self.direction(refs(ref)[0]) if ref != "$" else (1.0, 0.0, 0.0)
        x = unit(add(x, scale(z, -dot(x, z))))
        return Frame(origin, x, cross(z, x), z)

    def vertex(self, n: int) -> Vec:
        return self.point(refs(self.records[n])[0])

    def reachable(self, start: list[int]) -> set[int]:
        seen, stack = set(), list(start)
        while stack:
            n = stack.pop()
            if n not in seen and n in self.records:
                seen.add(n)
                stack.extend(refs(self.records[n]))
        return seen


# -- edges ----------------------------------------------------------------


def bspline(model: Model, n: int, samples: int = 32) -> list[Vec]:
    """Points along a non-rational B_SPLINE_CURVE_WITH_KNOTS, by de Boor."""
    p = model.params(n)
    degree = int(p[1])
    control = [model.point(r) for r in refs(p[2])]
    multiplicities = [int(m) for m in numbers(p[6])]
    knots = [k for k, m in zip(numbers(p[7]), multiplicities) for _ in range(m)]
    lo, hi = knots[degree], knots[len(control)]

    def at(t: float) -> Vec:
        k = max(i for i in range(degree, len(control)) if knots[i] <= t) if t < hi else len(control) - 1
        d = [control[j + k - degree] for j in range(degree + 1)]
        for r in range(1, degree + 1):
            for j in range(degree, r - 1, -1):
                i = j + k - degree
                span = knots[i + degree + 1 - r] - knots[i]
                a = 0.0 if span == 0 else (t - knots[i]) / span
                d[j] = add(scale(d[j - 1], 1 - a), scale(d[j], a))
        return d[degree]

    steps = samples if degree > 1 else len(control) - 1
    return [at(lo + (hi - lo) * i / steps) for i in range(steps + 1)]


def edge_polyline(model: Model, n: int) -> list[Vec]:
    p = model.params(n)
    start, end = model.vertex(refs(p[1])[0]), model.vertex(refs(p[2])[0])
    curve = refs(p[3])[0]
    kind = model.entity(curve)
    if kind == "LINE":
        return [start, end]
    if kind == "CIRCLE":
        c = model.params(curve)
        frame, radius = model.frame(refs(c[1])[0]), float(c[2])

        def angle(q: Vec) -> float:
            local = frame.local(q)
            return math.atan2(local[1], local[0])

        a1, a2 = angle(start), angle(end)
        if p[4] == ".F.":
            a1, a2 = a2, a1
        if abs(a2 - a1) < 1e-9:
            a2 = a1 + 2 * math.pi
        while a2 < a1:
            a2 += 2 * math.pi
        steps = max(8, round(96 * (a2 - a1) / (2 * math.pi)))
        return [frame.point((radius * math.cos(a1 + (a2 - a1) * i / steps),
                             radius * math.sin(a1 + (a2 - a1) * i / steps), 0.0)) for i in range(steps + 1)]
    if kind == "B_SPLINE_CURVE_WITH_KNOTS":
        return bspline(model, curve)
    raise SystemExit(f"render_examples: #{n} uses a {kind}, which this renderer does not draw")


# -- outlines of curved faces ----------------------------------------------


def outline(model: Model, face: int, edges: list[list[Vec]], place: Placement) -> list[list[Vec]]:
    """Silhouette curves of one face's surface, in assembly coordinates."""
    surface = refs(model.params(face)[2])[0]
    kind = model.entity(surface)
    if kind == "PLANE":
        return []
    s = model.params(surface)
    # Work in the surface's own frame, in the component's coordinates, and
    # place the result; only the view direction needs the assembly's axes.
    frame = model.frame(refs(s[1])[0])
    a, b, c = (dot(place.vector(axis), VIEW) for axis in (frame.x, frame.y, frame.z))
    heights = [frame.local(q)[2] for poly in edges for q in poly]

    def at(local: Vec) -> Vec:
        return place.point(frame.point(local))

    if kind in ("CYLINDRICAL_SURFACE", "CONICAL_SURFACE"):
        radius = float(s[2])
        slope = math.tan(float(s[3])) if kind == "CONICAL_SURFACE" else 0.0
        amplitude, phase = math.hypot(a, b), math.atan2(b, a)
        if amplitude < 1e-12 or abs(slope * c) > amplitude:
            return []
        spread = math.acos(slope * c / amplitude)
        v0, v1 = min(heights), max(heights)
        return [[at(((radius + slope * v) * math.cos(u), (radius + slope * v) * math.sin(u), v)) for v in (v0, v1)]
                for u in (phase - spread, phase + spread)]
    if kind == "SPHERICAL_SURFACE":
        radius = float(s[2])
        e1 = unit(cross(VIEW, (0.0, 0.0, 1.0) if abs(VIEW[2]) < 0.9 else (1.0, 0.0, 0.0)))
        e2 = cross(VIEW, e1)
        centre = place.point(frame.o)
        return [[add(centre, add(scale(e1, radius * math.cos(t)), scale(e2, radius * math.sin(t))))
                 for t in (2 * math.pi * i / 96 for i in range(97))]]
    if kind == "TOROIDAL_SURFACE":
        major, minor = float(s[2]), float(s[3])
        curves = []
        for offset in (0.0, math.pi):
            curve = []
            for i in range(145):
                u = 2 * math.pi * i / 144
                v = math.atan2(-(a * math.cos(u) + b * math.sin(u)), c) + offset
                local = add(scale((math.cos(u), math.sin(u), 0.0), major + minor * math.cos(v)),
                            (0.0, 0.0, minor * math.sin(v)))
                curve.append(at(local))
            curves.append(curve)
        return curves
    raise SystemExit(f"render_examples: face #{face} lies on a {kind}, which this renderer does not outline")


# -- collecting a drawing ---------------------------------------------------


class Drawing:
    def __init__(self) -> None:
        self.edges: list[list[Vec]] = []
        self.outlines: list[list[Vec]] = []
        self.vertices: list[Vec] = []

    def add_solids(self, model: Model, solids: list[int], place: Placement) -> None:
        for solid in solids:
            ids = model.reachable([solid])
            polylines = {n: edge_polyline(model, n) for n in sorted(ids) if model.entity(n) == "EDGE_CURVE"}
            for poly in polylines.values():
                self.edges.append([place.point(q) for q in poly])
            for n in sorted(ids):
                if model.entity(n) == "VERTEX_POINT":
                    self.vertices.append(place.point(model.vertex(n)))
                if model.entity(n) == "ADVANCED_FACE":
                    face_edges = [polylines[e] for e in sorted(model.reachable([n])) if e in polylines]
                    self.outlines.extend(outline(model, n, face_edges, place))


def solids_in(model: Model, representation: int) -> list[int]:
    items = refs(model.params(representation)[1])
    return [i for i in items if model.entity(i) in ("MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS")]


def draw(path: Path, assembly: bool) -> Drawing:
    model = Model(path)
    drawing = Drawing()
    if not assembly:
        solids = sorted(n for n in model.records if model.entity(n) in ("MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS"))
        drawing.add_solids(model, solids, IDENTITY)
        return drawing
    for n, body in sorted(model.records.items()):
        relation = re.search(r"REPRESENTATION_RELATIONSHIP\('[^']*','[^']*',#(\d+),#(\d+)\)", body)
        transform = re.search(r"REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION\(#(\d+)\)", body)
        if not (relation and transform):
            continue
        item = refs(model.records[int(transform.group(1))])
        place = Placement(model.frame(item[0]), model.frame(item[1]))
        drawing.add_solids(model, solids_in(model, int(relation.group(1))), place)
    return drawing


# -- SVG --------------------------------------------------------------------


def project(p: Vec) -> tuple[float, float]:
    return dot(p, SCREEN_U), dot(p, SCREEN_V)


def svg(drawing: Drawing, title: str) -> str:
    everything = [project(q) for poly in drawing.edges + drawing.outlines for q in poly]
    everything += [project(q) for q in drawing.vertices]
    us, vs = [u for u, _ in everything], [v for _, v in everything]
    span_u, span_v = max(us) - min(us), max(vs) - min(vs)
    k = min((WIDTH - 2 * PAD) / span_u, (MAX_HEIGHT - 2 * PAD) / span_v)
    width, height = round(span_u * k + 2 * PAD), round(span_v * k + 2 * PAD)

    def xy(p: Vec) -> str:
        u, v = project(p)
        return f"{PAD + (u - min(us)) * k:.2f},{PAD + (v - min(vs)) * k:.2f}"

    def path(poly: list[Vec]) -> str:
        return '<path d="M' + " L".join(xy(q) for q in poly) + '"/>'

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">',
        f"<title>{title}</title>",
        # An opaque background: e-readers' night modes put transparent
        # drawings on black, where dark lines vanish.
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<g fill="none" stroke="{OUTLINE_COLOUR}" stroke-width="1" stroke-linecap="round">',
        *(path(poly) for poly in drawing.outlines),
        "</g>",
        f'<g fill="none" stroke="{EDGE_COLOUR}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">',
        *(path(poly) for poly in drawing.edges),
        "</g>",
        f'<g fill="{EDGE_COLOUR}">',
        *(f'<circle cx="{xy(q).split(",")[0]}" cy="{xy(q).split(",")[1]}" r="3.2"/>' for q in drawing.vertices),
        "</g>",
        "</svg>",
        "",
    ]
    return "\n".join(out)


NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def same_drawing(committed: str, fresh: str) -> bool:
    """Equal apart from last-digit differences between platforms' maths libraries."""
    if NUMBER.sub("#", committed) != NUMBER.sub("#", fresh):
        return False
    return all(abs(float(a) - float(b)) <= 0.02
               for a, b in zip(NUMBER.findall(committed), NUMBER.findall(fresh)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if a committed figure differs")
    args = parser.parse_args()

    drifted = []
    for source, name, assembly in FIGURE_LIST:
        drawing = draw(ROOT / "examples" / source, assembly)
        text = svg(drawing, f"{source}: {len(drawing.edges)} edges, {len(drawing.vertices)} vertices")
        target = FIGURES / f"{name}.svg"
        if args.check:
            if not target.exists() or not same_drawing(target.read_text(), text):
                drifted.append(f"figures/{name}.svg no longer matches examples/{source}")
        else:
            FIGURES.mkdir(exist_ok=True)
            target.write_text(text)
            print(f"figures/{name}.svg: {len(drawing.edges)} edges, {len(drawing.vertices)} vertices, "
                  f"{len(drawing.outlines)} outlines, from examples/{source}")
    if drifted:
        print("Figures out of date; run python3 tools/render_examples.py:\n")
        for line in drifted:
            print("  " + line)
        return 1
    if args.check:
        print(f"OK: {len(FIGURE_LIST)} figures match the example files they are drawn from.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
