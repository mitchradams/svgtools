import re
import math
import xml.etree.ElementTree as ET
from svgpathtools import svg2paths2, Path, wsvg, Line, Arc

# ---------------------------------------------------------------------------
# Unit parsing helpers
# ---------------------------------------------------------------------------

_MM_PER_UNIT = {
    "mm": 1.0,
    "cm": 10.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,
    "pc": 25.4 / 6.0,
    "px": 25.4 / 96.0,  # CSS reference pixel
    "":   25.4 / 96.0,  # bare numbers treated as px per SVG spec
}

def _parse_length_mm(value: str) -> float | None:
    """Parse an SVG length string (e.g. '210mm', '8.27in', '595.28') to mm.
    Returns None if the string cannot be parsed."""
    value = value.strip()
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)\s*([a-z]*)", value, re.IGNORECASE)
    if not m:
        return None
    number, unit = float(m.group(1)), m.group(2).lower()
    factor = _MM_PER_UNIT.get(unit)
    if factor is None:
        return None
    return number * factor

def _parse_viewbox(viewbox_str: str) -> tuple[float, float, float, float] | None:
    """Parse 'min-x min-y width height' from a viewBox attribute string."""
    parts = re.split(r"[\s,]+", viewbox_str.strip())
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)
    except ValueError:
        return None

def _read_svg_unit_transform(filename: str) -> float:
    """
    Return the scale factor (user-units → mm) for the given SVG file.

    Strategy:
      - Parse width and height attributes (e.g. '210mm', '8.27in').
      - Parse the viewBox to get the user-unit dimensions.
      - scale = physical_width_mm / viewBox_width_uu
      - If either is missing, fall back to 1.0 (no conversion — assume user
        units are already mm, which is Inkscape's default).
    """
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        # Strip namespace prefix if present
        attrib = {k.split("}")[-1]: v for k, v in root.attrib.items()}
        w_str = attrib.get("width", "")
        vb_str = attrib.get("viewBox", "")
        w_mm = _parse_length_mm(w_str)
        vb = _parse_viewbox(vb_str)
        if w_mm and vb and vb[2] > 0:
            return w_mm / vb[2]
    except Exception:
        pass
    return 1.0  # fallback: assume user-units == mm

# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_svg_paths_from_file(filename: str):
    """
    Load paths from an SVG file, converting coordinates to millimetres.

    Returns:
        paths      — list[Path] with coordinates in mm
        metadata   — dict with keys:
                       'attributes'     : per-path attribute dicts (from svgpathtools)
                       'svg_attributes' : top-level SVG attribute dict
                       'scale'          : user-unit → mm scale factor that was applied
                       'width_mm'       : physical canvas width in mm
                       'height_mm'      : physical canvas height in mm
    """
    scale = _read_svg_unit_transform(filename)

    paths, attributes, svg_attributes = svg2paths2(filename)

    if scale != 1.0:
        paths = [path.scaled(scale) for path in paths]

    # Determine canvas size in mm for use when saving
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        attrib = {k.split("}")[-1]: v for k, v in root.attrib.items()}
        width_mm  = _parse_length_mm(attrib.get("width",  "")) or 0.0
        height_mm = _parse_length_mm(attrib.get("height", "")) or 0.0
    except Exception:
        width_mm = height_mm = 0.0

    metadata = {
        "attributes":     attributes,
        "svg_attributes": svg_attributes,
        "scale":          scale,
        "width_mm":       width_mm,
        "height_mm":      height_mm,
    }
    return paths, metadata


def save_svg_paths_to_file(paths: list[Path], filename: str,
                           stroke_width_mm: float = 0.1,
                           margin_mm: float = 5.0):
    """
    Save paths (whose coordinates are in mm) to an SVG file with a physically
    correct `width` / `height` header in millimetres.

    The canvas is sized to the bounding box of all paths plus `margin_mm` on
    every side.  `stroke_width_mm` sets the stroke width in the same units.

    We bypass wsvg for the header and write the SVG by hand so that we have
    full control over the units; wsvg is still used to serialise the path `d`
    strings via Path.d().
    """
    if not paths:
        return

    # Bounding box of all paths (mm coordinates)
    min_x = min(path_min_x(p) for p in paths)
    min_y = min(path_min_y(p) for p in paths)
    max_x = max(path_max_x(p) for p in paths)
    max_y = max(path_max_y(p) for p in paths)

    canvas_w = (max_x - min_x) + 2 * margin_mm
    canvas_h = (max_y - min_y) + 2 * margin_mm

    # Shift all paths so (min_x, min_y) maps to (margin_mm, margin_mm)
    dx = margin_mm - min_x
    dy = margin_mm - min_y
    shifted = [p.translated(complex(dx, dy)) for p in paths]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{canvas_w:.6f}mm"',
        f'     height="{canvas_h:.6f}mm"',
        f'     viewBox="0 0 {canvas_w:.6f} {canvas_h:.6f}">',
        "  <defs/>",
    ]
    for path in shifted:
        d = path.d()
        lines.append(
            f'  <path d="{d}" fill="none" stroke="#000000"'
            f' stroke-width="{stroke_width_mm:.4f}"/>'
        )
    lines.append("</svg>")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------
# Arc-aware polygon conversion
# ---------------------------------------------------------------------------

def _adaptive_arc_points(arc: Arc, chord_error: float) -> list[tuple[float, float]]:
    """
    Sample an svgpathtools Arc into a polyline using adaptive step sizing.

    The step size in parameter space is chosen so that the maximum deviation
    of the chord from the true arc (the sagitta) is at most `chord_error`.

    For a circular arc of radius R, the sagitta for a subtended half-angle θ is:
        sagitta = R * (1 - cos θ)
    Setting sagitta = chord_error and solving gives the maximum allowed half-angle:
        θ_max = arccos(1 - chord_error / R)
    which maps to a maximum parameter-space step of θ_max / (π/2) for a
    quarter-circle arc (rough approximation — good enough for laser-cut tolerances).

    For non-circular (elliptical) arcs we use the geometric mean of the two
    radii as a conservative radius estimate.
    """
    arc_len = arc.length()
    if arc_len < 1e-9:
        return []

    rx, ry = abs(arc.radius.real), abs(arc.radius.imag)
    if rx < 1e-9 or ry < 1e-9:
        # Degenerate arc — treat as a line
        return [(arc.start.real, arc.start.imag), (arc.end.real, arc.end.imag)]

    # Conservative radius for sagitta calculation
    r_eff = math.sqrt(rx * ry)
    ratio = max(0.0, min(1.0, 1.0 - chord_error / r_eff))
    theta_max = math.acos(ratio)           # max half-angle per chord (radians)

    # Map to a minimum number of segments.  Each full 2π of arc needs
    # at least ceil(π / theta_max) segments.  We scale by the arc's own
    # angular span (approximated via arc_len / r_eff).
    angular_span = arc_len / r_eff        # approximate angular span in radians
    n_segs = max(2, math.ceil(angular_span / (2.0 * theta_max)))

    t_values = [i / n_segs for i in range(n_segs + 1)]
    return [(arc.point(t).real, arc.point(t).imag) for t in t_values]


def svg_path_to_polygon(svg_path: Path,
                        arc_chord_error: float = 0.01) -> list[tuple[float, float]]:
    """
    Convert an svgpathtools Path to a list of (x, y) points.

    Lines contribute their start point.  Arcs are sampled adaptively so that
    the chord error (deviation from the true arc) does not exceed
    `arc_chord_error` (in the same units as the path coordinates — mm after
    load_svg_paths_from_file has been used).

    The default 0.01 mm chord error gives smooth curves for laser cutting
    while keeping point counts reasonable.
    """
    points: list[tuple[float, float]] = []

    for segment in svg_path:
        if isinstance(segment, Line):
            points.append((segment.start.real, segment.start.imag))
        elif isinstance(segment, Arc):
            arc_pts = _adaptive_arc_points(segment, arc_chord_error)
            if arc_pts:
                # Drop the last point — it's the start of the next segment
                points.extend(arc_pts[:-1])
        # Other segment types (CubicBezier, QuadraticBezier) could be added here

    # Close the polygon if needed
    if points and points[0] != points[-1]:
        points.append(points[0])

    return points


def polygon_to_svg_path(polygon: list[tuple[float, float]]) -> Path:
    """Convert a list of (x, y) points to a closed svgpathtools Path of Lines."""
    pts = list(polygon)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    segments = [
        Line(start=complex(pts[i][0], pts[i][1]),
             end=complex(pts[i + 1][0], pts[i + 1][1]))
        for i in range(len(pts) - 1)
    ]
    return Path(*segments)

# ---------------------------------------------------------------------------
# Bounding-box helpers (unchanged API)
# ---------------------------------------------------------------------------

def path_width(path: Path) -> float:
    return path_max_x(path) - path_min_x(path)

def path_height(path: Path) -> float:
    return path_max_y(path) - path_min_y(path)

def path_min_x(path: Path) -> float:
    return path.bbox()[0]

def path_max_x(path: Path) -> float:
    return path.bbox()[1]

def path_min_y(path: Path) -> float:
    return path.bbox()[2]

def path_max_y(path: Path) -> float:
    return path.bbox()[3]

def paths_width(paths: list[Path]) -> float:
    return paths_max_x(paths) - paths_min_x(paths)

def paths_height(paths: list[Path]) -> float:
    return paths_max_y(paths) - paths_min_y(paths)

def paths_min_x(paths: list[Path]) -> float:
    return min(path_min_x(p) for p in paths)

def paths_max_x(paths: list[Path]) -> float:
    return max(path_max_x(p) for p in paths)

def paths_min_y(paths: list[Path]) -> float:
    return min(path_min_y(p) for p in paths)

def paths_max_y(paths: list[Path]) -> float:
    return max(path_max_y(p) for p in paths)

# ---------------------------------------------------------------------------
# Layout helper (unchanged API)
# ---------------------------------------------------------------------------

def distribute_svg_path_group_layout(path_groups: list[list[Path]],
                                     space_between_each: float) -> list[list[Path]]:
    """Lay out groups of paths in a horizontal row, left-aligned, with a fixed gap."""
    distributed: list[list[Path]] = []
    if not path_groups:
        return distributed

    # Anchor: x/y of the first non-empty group
    current_x = y = None
    for group in path_groups:
        if group:
            current_x = paths_min_x(group)
            y = paths_min_y(group)
            break

    if current_x is None:
        return distributed

    for group in path_groups:
        if group:
            tx = current_x - paths_min_x(group)
            ty = y - paths_min_y(group)
            translated = [p.translated(complex(tx, ty)) for p in group]
            distributed.append(translated)
            current_x += paths_width(group) + space_between_each

    return distributed