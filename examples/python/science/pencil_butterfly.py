"""pencil_butterfly.py: butterflies drawn the way an old natural-history textbook drew them, in graphite: wings spread, a
sketched double outline, the veins and the discal cell, hatching that darkens the wing bases and borders, and each group's
marks (eyespots, bands, spots, dark veins, tails, hooked antennae).

Every butterfly is built from a few numbers: where the forewing apex and tornus sit, how round the hindwing is, which tails
and marks it carries. One function draws every group in the same hand. Used by butterfly_tree.py; run on its own it writes a
proof sheet of every group to the path given on the command line.
"""
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse, PathPatch, Polygon
from matplotlib.path import Path
from shapely.geometry import Point, Polygon as SPoly

# wing geometry in units of the wingspan (x to the right of the body, y up), and the marks of each group
BASE = dict(ax=0.47, ay=0.25, mx=0.40, my=0.07, tx=0.29, ty=-0.03, h1=(0.33, -0.05), h2=(0.29, -0.22), h3=(0.12, -0.31), tails=[],
            scallop=0.0, body=1.0, antenna="club", marks=[])
STYLES = {
    "Papilionidae":   dict(ay=0.27, h1=(0.33, -0.04), h2=(0.27, -0.24), h3=(0.12, -0.30), tails=[(0.22, -0.27, 0.18, -0.46)], scallop=0.012,
                           marks=[("bands", 4), ("margin", 0.05), ("eyespot_anal",)]),
    "Hedylidae":      dict(ax=0.48, ay=0.20, mx=0.41, my=0.06, tx=0.27, ty=0.0, h1=(0.27, -0.03), h2=(0.24, -0.16), h3=(0.10, -0.22), body=0.7,
                           antenna="thread", marks=[("lines", 3)]),
    "Hesperiidae":    dict(ax=0.42, ay=0.24, mx=0.36, my=0.05, tx=0.25, ty=-0.03, h1=(0.25, -0.04), h2=(0.22, -0.16), h3=(0.09, -0.22), body=1.6,
                           antenna="hook", marks=[("base", 0.55), ("glass", 5)]),
    "Pieridae":       dict(ax=0.46, ay=0.25, mx=0.42, my=0.08, tx=0.30, ty=-0.03, h1=(0.33, -0.05), h2=(0.30, -0.22), h3=(0.12, -0.30),
                           marks=[("apex",), ("spots", 2)]),
    "Riodinidae":     dict(ax=0.42, ay=0.22, mx=0.38, my=0.06, tx=0.27, ty=-0.03, h1=(0.29, -0.04), h2=(0.27, -0.18), h3=(0.11, -0.25),
                           marks=[("checks",), ("margin", 0.04)]),
    "Lycaenidae":     dict(ax=0.43, ay=0.22, mx=0.40, my=0.06, tx=0.29, ty=-0.03, h1=(0.30, -0.04), h2=(0.28, -0.19), h3=(0.12, -0.24),
                           tails=[(0.20, -0.235, 0.20, -0.33)], marks=[("margin", 0.03), ("eyespot_anal",), ("spots", 4)]),
    "Libytheinae":    dict(ax=0.46, ay=0.27, mx=0.43, my=0.16, tx=0.30, ty=-0.03, h1=(0.31, -0.06), h2=(0.27, -0.21), h3=(0.11, -0.27),
                           scallop=0.008, marks=[("base", 0.6), ("spots", 3)]),
    "Danainae":       dict(ax=0.48, ay=0.26, mx=0.41, my=0.06, tx=0.29, ty=-0.04, h1=(0.32, -0.06), h2=(0.29, -0.22), h3=(0.12, -0.29),
                           marks=[("veins_dark",), ("margin", 0.05), ("dots",)]),
    "Satyrinae":      dict(ax=0.45, ay=0.24, mx=0.40, my=0.06, tx=0.29, ty=-0.03, h1=(0.31, -0.05), h2=(0.29, -0.21), h3=(0.12, -0.29),
                           marks=[("margin", 0.03), ("eyespots", 2, 4)]),
    "Charaxinae":     dict(ax=0.48, ay=0.27, mx=0.40, my=0.09, tx=0.29, ty=-0.03, h1=(0.33, -0.05), h2=(0.28, -0.22), h3=(0.12, -0.29),
                           tails=[(0.25, -0.22, 0.24, -0.32), (0.19, -0.26, 0.18, -0.36)], scallop=0.01, marks=[("base", 0.5), ("margin", 0.06)]),
    "Calinaginae":    dict(ax=0.45, ay=0.25, mx=0.41, my=0.07, tx=0.30, ty=-0.03, h1=(0.32, -0.05), h2=(0.29, -0.22), h3=(0.12, -0.29),
                           marks=[("base", 0.45), ("veins_dark",)]),
    "Heliconiinae":   dict(ax=0.49, ay=0.22, mx=0.43, my=0.07, tx=0.24, ty=0.0, h1=(0.30, -0.04), h2=(0.26, -0.18), h3=(0.11, -0.23),
                           marks=[("dark",), ("fwband",), ("hwrays",)]),
    "Limenitidinae":  dict(ax=0.46, ay=0.25, mx=0.40, my=0.07, tx=0.29, ty=-0.03, h1=(0.32, -0.05), h2=(0.29, -0.21), h3=(0.12, -0.28),
                           scallop=0.006, marks=[("dark",), ("whiteband",)]),
    "Nymphalinae":    dict(ax=0.47, ay=0.27, mx=0.39, my=0.10, tx=0.30, ty=-0.03, h1=(0.33, -0.05), h2=(0.28, -0.22), h3=(0.12, -0.29),
                           scallop=0.02, tails=[(0.27, -0.16, 0.30, -0.20)], marks=[("margin", 0.04), ("blotches",)]),
    "Biblidinae":     dict(ax=0.45, ay=0.24, mx=0.41, my=0.07, tx=0.30, ty=-0.03, h1=(0.32, -0.05), h2=(0.29, -0.21), h3=(0.12, -0.28),
                           marks=[("dark",), ("fwband",), ("rings",)]),
    "Apaturinae":     dict(ax=0.47, ay=0.26, mx=0.41, my=0.09, tx=0.30, ty=-0.03, h1=(0.33, -0.05), h2=(0.29, -0.22), h3=(0.12, -0.29),
                           scallop=0.008, marks=[("dark",), ("whiteband",), ("eyespots", 1, 1)]),
    "Cyrestinae":     dict(ax=0.47, ay=0.25, mx=0.42, my=0.07, tx=0.29, ty=-0.03, h1=(0.33, -0.05), h2=(0.29, -0.21), h3=(0.12, -0.27),
                           tails=[(0.21, -0.25, 0.22, -0.44)], marks=[("lines", 6)]),
    "Pseudergolinae": dict(ax=0.46, ay=0.25, mx=0.41, my=0.08, tx=0.30, ty=-0.03, h1=(0.32, -0.05), h2=(0.29, -0.21), h3=(0.12, -0.28),
                           scallop=0.006, marks=[("base", 0.4), ("lines", 4)]),
}
STEP = 0.0085                       # hatching pitch, inches


def _catmull(pts, n=24):
    """A closed Catmull-Rom curve through the points."""
    P = np.asarray(pts, float); P = np.r_[P[-1:], P, P[:2]]
    t = np.linspace(0, 1, n, endpoint=False)[:, None]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.vstack(out)


def _jitter(xy, amp, rng):
    """A pencil line wobbles: smooth noise across the line."""
    n = len(xy)
    if n < 3: return xy
    t = np.linspace(0, 1, n)
    w = amp * (np.sin(2 * np.pi * rng.uniform(2, 5) * t + rng.uniform(0, 6.3)) * 0.6 + rng.normal(0, 0.25, n).cumsum() / np.sqrt(n))
    d = np.gradient(xy, axis=0); nrm = np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9
    return xy + np.c_[-d[:, 1], d[:, 0]] / nrm * w[:, None]


def _stroke(ax, xy, ink, lw, rng, z, passes=2, amp=0.0025, alpha=0.8):
    for _ in range(passes):
        j = _jitter(np.asarray(xy, float), amp, rng)
        ax.plot(j[:, 0], j[:, 1], color=ink, lw=lw * rng.uniform(0.8, 1.1), alpha=alpha * rng.uniform(0.8, 1.0),
                solid_capstyle="round", solid_joinstyle="round", zorder=z)


def _hatch(bounds, step, angle):
    """Parallel lines covering a box, at an angle in degrees."""
    x0, y0, x1, y1 = bounds
    a = np.deg2rad(angle); d = np.array([np.cos(a), np.sin(a)]); nv = np.array([-d[1], d[0]])
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); R = np.hypot(x1 - x0, y1 - y0)
    return [[tuple(c + nv * s - d * R), tuple(c + nv * s + d * R)] for s in np.arange(-R, R, step)]


def _path(geom):
    """A shapely (multi)polygon as a matplotlib Path, holes included."""
    polys = [geom] if geom.geom_type == "Polygon" else [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    verts, codes = [], []
    for pg in polys:
        for ring in [pg.exterior, *pg.interiors]:
            c = np.asarray(ring.coords)
            verts += c.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes) if verts else None


def _hatch_region(ax, geom, ink, angles, alpha, z, lw=0.24):
    """Hatch a region: parallel lines at each (angle, pitch factor), clipped to it."""
    if geom.is_empty: return
    path = _path(geom)
    if path is None: return
    segs = [s for ang, k in angles for s in _hatch(geom.bounds, STEP * k, ang)]
    lc = LineCollection(segs, colors=ink, linewidths=lw, alpha=alpha, zorder=z, capstyle="round")
    ax.add_collection(lc); lc.set_clip_path(path, ax.transData)


def _paper(ax, geom, paper, z):
    """Lay bare paper over a region (a pale band or spot on a dark wing)."""
    path = None if geom.is_empty else _path(geom)
    if path is not None: ax.add_patch(PathPatch(path, fc=paper, ec="none", zorder=z))


def _clipped_line(ax, xy, wing, z, **kw):
    ln, = ax.plot(*np.asarray(xy).T, zorder=z, **kw)
    ln.set_clip_path(_path(wing), ax.transData)


def _eyespot(ax, xy, r, ink, paper, z):
    ax.add_patch(Ellipse(xy, 2 * r, 2 * r, fc=paper, ec=ink, lw=0.5, zorder=z + 0.3))
    ax.add_patch(Ellipse(xy, 1.3 * r, 1.3 * r, fc="none", ec=ink, lw=0.35, alpha=0.7, zorder=z + 0.31))
    ax.add_patch(Ellipse(xy, 0.8 * r, 0.8 * r, fc=ink, ec="none", alpha=0.9, zorder=z + 0.32))
    ax.add_patch(Ellipse((xy[0] - 0.15 * r, xy[1] + 0.15 * r), 0.25 * r, 0.25 * r, fc=paper, ec="none", zorder=z + 0.33))


def _wing_outline(p, fore):
    if fore:
        pts = [(0.035, 0.03), (0.17, 0.14), (0.32, 0.22), (p["ax"], p["ay"]), (p["mx"], p["my"]), (p["tx"], p["ty"]),
               (0.15, -0.035), (0.045, -0.005)]
    else:
        pts = [(0.035, -0.005), (0.18, 0.0), p["h1"], p["h2"], p["h3"], (0.06, -0.12), (0.035, -0.04)]
    out = _catmull(pts)
    if p["scallop"] and not fore:                                  # a scalloped outer margin: ripple the points facing out
        k = np.arange(len(out)); outer = np.hypot(out[:, 0], out[:, 1] + 0.05) > 0.22
        out[outer] *= (1 + p["scallop"] / 0.3 * np.cos(k[outer] * 2 * np.pi / 9))[:, None]
    for tx, ty, ex, ey in ([] if fore else p["tails"]):            # tails: a narrow spur from the hindwing margin
        i = int(np.argmin(np.hypot(out[:, 0] - tx, out[:, 1] - ty))); w = 0.018
        spur = np.array([[tx + w, ty], [ex + w * 0.6, ey + 0.02], [ex, ey], [ex - w * 0.6, ey + 0.02], [tx - w, ty]])
        out = np.r_[out[:i], spur, out[i + 1:]]
    return out


def _veins(out, fore, S, side):
    """The discal cell and the veins that fan from it to the margin, as polylines."""
    cell_end = np.array([0.21, 0.075]) if fore else np.array([0.15, -0.10])
    base = np.array([0.04, 0.012]) if fore else np.array([0.04, -0.02])
    fr = np.linspace(0.16, 0.58, 8) if fore else np.linspace(0.18, 0.62, 7)
    n = len(out); vs = []
    t = np.linspace(0, 1, 12)[:, None]
    for k, f in enumerate(fr):
        end = out[int(f * n) % n]
        start = cell_end + (np.array([0.0, 0.035]) if fore else np.array([0.02, 0.03])) * (0.5 - k / len(fr))
        mid = (start + end) / 2 + (base - (start + end) / 2) * 0.08
        vs.append(S((1 - t) ** 2 * start + 2 * (1 - t) * t * mid + t ** 2 * end, side))
    vs.append(S(np.array([base, cell_end + [0, 0.03], cell_end + [0.0, -0.025], base]), side))
    return vs


def _marks(ax, p, out, S, side, fore, span, ink, paper, rng, z, wing, body):
    n = len(out); circ = lambda c, r: Point(*c).buffer(r)
    dense = [(35 * side, 0.6), (-40 * side, 0.9)]
    for m in p["marks"]:
        kind = m[0]
        if kind == "base":
            continue
        if kind == "dark":
            _hatch_region(ax, wing, ink, dense, 0.7, z + 0.15)
        elif kind == "margin":
            band = wing.difference(wing.buffer(-m[1] * span)).difference(circ(body, 0.2 * span))
            _hatch_region(ax, band, ink, dense, 0.7, z + 0.15)
            for f in np.linspace(0.3 if fore else 0.22, 0.68 if fore else 0.8, 6 if fore else 5):
                q = S([out[int(f * n)] * 0.965], side)[0]
                if wing.contains(Point(*q)): _paper(ax, circ(q, 0.008 * span), paper, z + 0.18)
        elif kind == "apex" and fore:
            _hatch_region(ax, wing.intersection(circ(S([out[int(0.32 * n)]], side)[0], 0.13 * span)), ink, dense, 0.75, z + 0.15)
        elif kind == "bands":
            for k in range(m[1]):
                c = 0.12 + 0.09 * k
                band = SPoly(S(np.array([[c, 0.5], [c + 0.035, 0.5], [c + 0.035 - 0.07, -0.5], [c - 0.07, -0.5]]), side))
                _hatch_region(ax, wing.intersection(band), ink, [(30 * side, 0.55), (-45 * side, 0.8)], 0.75, z + 0.16)
        elif kind == "eyespots":
            spots = ([0.36, 0.15], [0.33, 0.04])[:m[1]] if fore else ([0.24, -0.08], [0.24, -0.13], [0.22, -0.18], [0.18, -0.22])[:m[2]]
            for q in spots: _eyespot(ax, S([q], side)[0], (0.028 if fore else 0.022) * span, ink, paper, z)
        elif kind == "eyespot_anal" and not fore:
            _eyespot(ax, S([out[int(0.66 * n)] * 0.9], side)[0], 0.018 * span, ink, paper, z)
        elif kind == "spots" and fore:
            for k in range(m[1]):
                ax.add_patch(Ellipse(S([[0.28 + 0.03 * k, 0.15 - 0.025 * k]], side)[0], 0.03 * span, 0.026 * span, fc=ink, ec="none",
                                     alpha=0.75, zorder=z + 0.3))
        elif kind == "glass" and fore:                              # the glassy windows of a skipper's forewing
            for k in range(m[1]):
                q = np.array([0.26 + 0.025 * (k % 3), 0.11 + 0.02 * (k // 3) - 0.02 * (k % 3)])
                quad = [q + d for d in ([-0.012, -0.008], [0.012, -0.006], [0.01, 0.009], [-0.01, 0.008])]
                ax.add_patch(Polygon(S(np.array(quad), side), closed=True, fc=paper, ec=ink, lw=0.35, zorder=z + 0.3))
        elif kind == "checks":
            for k in range(14):
                q = S([[rng.uniform(0.08, 0.36 if fore else 0.26), rng.uniform(0.0, 0.2) if fore else rng.uniform(-0.22, -0.03)]], side)[0]
                if wing.contains(Point(*q)):
                    ax.add_patch(Ellipse(q, 0.022 * span, 0.016 * span, fc=ink, ec="none", alpha=0.6, zorder=z + 0.25))
        elif kind == "dots":
            for f in np.linspace(0.3 if fore else 0.22, 0.65 if fore else 0.78, 7):
                q = S([out[int(f * n)] * 0.93], side)[0]
                if wing.contains(Point(*q)): _paper(ax, circ(q, 0.0055 * span), paper, z + 0.2)
        elif kind == "fwband" and fore:                            # a pale band across a dark forewing
            band = SPoly(S(np.array([[0.24, 0.25], [0.33, 0.25], [0.30, -0.1], [0.21, -0.1]]), side))
            _paper(ax, wing.intersection(band), paper, z + 0.18)
        elif kind == "whiteband":
            pts = [[0.20, 0.12], [0.26, 0.12], [0.20, -0.25], [0.13, -0.25]] if fore else [[0.13, 0.0], [0.20, 0.0], [0.13, -0.3], [0.07, -0.3]]
            _paper(ax, wing.intersection(SPoly(S(np.array(pts), side))), paper, z + 0.18)
        elif kind == "hwrays" and not fore:
            for f in np.linspace(0.2, 0.6, 6):
                _clipped_line(ax, S(np.array([[0.1, -0.06], out[int(f * n)] * 0.92]), side), wing, z + 0.25, color=ink, lw=0.9, alpha=0.6)
        elif kind == "rings" and not fore:
            for r in (0.12, 0.16):
                tt = np.linspace(0.2, 1.5, 30)
                _clipped_line(ax, S(np.c_[0.06 + r * np.cos(tt - 1.4), -0.02 + r * np.sin(tt - 1.4) * 0.9], side), wing, z + 0.25,
                              color=paper, lw=1.0)
        elif kind == "blotches":
            for q in ([0.14, 0.1], [0.24, 0.12], [0.2, 0.02]) if fore else ([0.12, -0.08], [0.2, -0.12]):
                ax.add_patch(Ellipse(S([q], side)[0], 0.04 * span, 0.03 * span, fc=ink, ec="none", alpha=0.55, zorder=z + 0.25))
        elif kind == "lines":
            for k in range(m[1]):
                c = 0.1 + 0.055 * k
                _clipped_line(ax, S(np.array([[c, 0.4], [c - 0.12, -0.4]]), side), wing, z + 0.25, color=ink, lw=0.5, alpha=0.6)


def draw_butterfly(ax, cx, cy, span, group, ink, paper, seed=0, z=5):
    """Draw the group's butterfly, wings spread, body centred at (cx, cy), wingtip to wingtip `span` (data units)."""
    p = dict(BASE); p.update(STYLES[group]); rng = np.random.default_rng(seed)
    S = lambda xy, side: np.c_[cx + side * np.asarray(xy)[:, 0] * span, cy + np.asarray(xy)[:, 1] * span]
    dark_veins = any(m[0] == "veins_dark" for m in p["marks"])
    reach = next((m[1] for m in p["marks"] if m[0] == "base"), 0.28) * span
    for side in (1, -1):
        for fore in (False, True):
            zz = z + (0.2 if fore else 0)
            out = _wing_outline(p, fore); W = S(out, side)
            ax.add_patch(Polygon(W, closed=True, fc=paper, ec="none", zorder=zz))
            wing = SPoly(W).buffer(0)
            lc = LineCollection(_veins(out, fore, S, side), colors=ink, linewidths=0.55 if dark_veins else 0.28,
                                alpha=0.75 if dark_veins else 0.55, zorder=zz + 0.2)
            ax.add_collection(lc); lc.set_clip_path(_path(wing), ax.transData)
            _hatch_region(ax, wing.intersection(Point(cx, cy).buffer(reach)), ink, [(55 * side, 1.0)], 0.45, zz + 0.1, lw=0.22)
            _marks(ax, p, out, S, side, fore, span, ink, paper, rng, zz, wing, (cx, cy))
            _stroke(ax, np.r_[W, W[:1]], ink, 0.5, rng, zz + 0.4, passes=2)
    # body: abdomen with its rings, thorax, head, antennae
    b = p["body"]; t = np.linspace(0, 2 * np.pi, 40)
    ax.add_patch(Ellipse((cx, cy - 0.12 * span), 0.035 * span * b, 0.26 * span, fc=paper, ec="none", zorder=z + 0.6))
    _stroke(ax, np.c_[cx + 0.0175 * span * b * np.cos(t), cy - 0.12 * span + 0.13 * span * np.sin(t)], ink, 0.45, rng, z + 0.7, amp=0.001)
    for k in np.linspace(-0.22, -0.02, 6):
        ax.plot([cx - 0.016 * span * b, cx + 0.016 * span * b], [cy + k * span] * 2, color=ink, lw=0.25, alpha=0.6, zorder=z + 0.7)
    ax.add_patch(Ellipse((cx, cy + 0.03 * span), 0.05 * span * b, 0.10 * span, fc=ink, ec="none", alpha=0.55, zorder=z + 0.7))
    ax.add_patch(Ellipse((cx, cy + 0.095 * span), 0.04 * span * b, 0.035 * span, fc=ink, ec="none", alpha=0.75, zorder=z + 0.7))
    for side in (1, -1):
        s = np.linspace(0, 1, 20)
        x, y = cx + side * (0.01 + 0.09 * s) * span, cy + (0.1 + 0.22 * s) * span
        if p["antenna"] == "hook":                                  # a skipper's antenna ends in a hook
            a = np.linspace(0, 1.6, 8)
            x, y = np.r_[x, x[-1] + side * 0.03 * span * np.sin(a)], np.r_[y, y[-1] - 0.025 * span * (1 - np.cos(a))]
        if p["antenna"] == "thread":
            x, y = cx + side * (0.01 + 0.15 * s) * span, cy + (0.1 + 0.16 * s) * span
        _stroke(ax, np.c_[x, y], ink, 0.35, rng, z + 0.7, passes=1, amp=0.0008)
        if p["antenna"] == "club":
            ax.add_patch(Ellipse((x[-1], y[-1]), 0.018 * span, 0.03 * span, angle=-side * 25, fc=ink, ec="none", alpha=0.85, zorder=z + 0.75))


if __name__ == "__main__":
    import sys, matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for mode, ink, paper in (("light", "#3C3A36", "#FFFFFF"), ("dark", "#D9D3C8", "#2A2622")):
        fig = plt.figure(figsize=(8, 10)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 8); ax.set_ylim(0, 10); ax.axis("off")
        fig.patch.set_facecolor(paper)
        for i, g in enumerate(STYLES):
            cx, cy = 1.0 + (i % 4) * 2.0, 9.0 - (i // 4) * 1.75
            draw_butterfly(ax, cx, cy, 1.5, g, ink, paper, seed=i)
            ax.text(cx, cy - 0.85, g, fontsize=8, color=ink, ha="center")
        fig.savefig(sys.argv[1].replace(".png", f"_{mode}.png"), dpi=150, facecolor=paper)
