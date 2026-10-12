"""nl_text.py: type for the map. Labels set as glyph outlines, straight or bent along a curve, with tracking and kerning.

Everything is laid out in paper points: a label is built with TextPath glyph by glyph (so letter spacing can be opened,
as a cartographer spaces names of areas), then each outline vertex (u, v) is moved to the point at arc length u along
the guide curve, v points along its left normal. The result is a matplotlib Path in data coordinates, drawn as a
PathPatch with a halo stroke underneath.
"""
import numpy as np
from matplotlib.font_manager import FontProperties, findfont, get_font
from matplotlib.ft2font import Kerning, LoadFlags
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath
from matplotlib import patheffects as pe
from scipy.ndimage import gaussian_filter1d


def layout(text, prop, size, tracking=0.0):
    """Glyph outlines of `text` on a straight baseline from u = 0, in points. tracking in em.
    Returns (vertices, codes, width)."""
    font = get_font(findfont(prop))
    font.set_size(size, 72)                          # TextPath resizes this cached font object, so measure first
    xs, x, prev = [], 0.0, None
    for ch in text:
        gi = font.get_char_index(ord(ch))
        if prev is not None:
            x += font.get_kerning(prev, gi, Kerning.DEFAULT) / 64.0
        xs.append(x)
        x += font.load_char(ord(ch), flags=LoadFlags.NO_HINTING).linearHoriAdvance / 65536.0 + tracking * size
        prev = gi
    verts, codes = [], []
    for ch, x0 in zip(text, xs):
        if ch.strip():
            tp = TextPath((x0, 0), ch, size=size, prop=prop)
            if len(tp.vertices):
                verts.append(tp.vertices); codes.append(tp.codes)
    width = x - tracking * size
    if not verts:
        return np.zeros((0, 2)), np.zeros(0, np.uint8), width
    return np.concatenate(verts), np.concatenate(codes), width


class Paper:
    """Data <-> paper points for an axes with equal aspect: k points per data unit, origin at the data point (x0, y0)."""

    def __init__(self, x0, y0, pt_per_unit):
        self.x0, self.y0, self.k = x0, y0, pt_per_unit

    def to_pt(self, xy):
        xy = np.asarray(xy, float)
        return np.stack([(xy[:, 0] - self.x0) * self.k, (xy[:, 1] - self.y0) * self.k], 1)

    def to_data(self, p):
        return np.stack([p[:, 0] / self.k + self.x0, p[:, 1] / self.k + self.y0], 1)


def resample(P, step=1.0, smooth=0.0):
    """A polyline in points resampled every `step` points, optionally Gaussian-smoothed (sigma in points)."""
    d = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    keep = np.concatenate([[True], d > 1e-9])
    P, s = P[keep], s[keep]
    n = max(int(s[-1] / step), 2)
    t = np.linspace(0, s[-1], n)
    Q = np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1)
    if smooth > 0:
        sig = smooth / (s[-1] / (n - 1))
        Qs = np.stack([gaussian_filter1d(Q[:, 0], sig, mode="nearest"), gaussian_filter1d(Q[:, 1], sig, mode="nearest")], 1)
        Q = Qs
    return Q


def bend(verts, guide, start, offset=0.0):
    """Move outline vertices (u, v) onto the guide (a resampled polyline in points) from arc length `start`."""
    d = np.hypot(*np.diff(guide, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    tang = np.gradient(guide, axis=0); tang /= np.maximum(np.hypot(*tang.T)[:, None], 1e-9)
    u = start + verts[:, 0]
    px, py = np.interp(u, s, guide[:, 0]), np.interp(u, s, guide[:, 1])
    tx, ty = np.interp(u, s, tang[:, 0]), np.interp(u, s, tang[:, 1])
    nrm = np.hypot(tx, ty); tx, ty = tx / nrm, ty / nrm
    v = verts[:, 1] + offset
    return np.stack([px - ty * v, py + tx * v], 1)


def curved_label(ax, paper, text, guide_xy, prop, size, color, halo=None, halo_pt=2.0, tracking=0.0, offset=0.0,
                 smooth=6.0, at=0.5, valign="middle", zorder=20, alpha=1.0, halo_alpha=1.0, flip="auto"):
    """Set `text` along the curve guide_xy (data coordinates), centred at fraction `at` of the curve's length.
    offset moves the baseline along the left normal (points); valign "middle" centres the cap height on the curve.
    flip: "auto" reverses a guide that would make the text read upside down."""
    G = resample(paper.to_pt(guide_xy), 0.5, smooth)
    if flip == "auto" and G[-1, 0] < G[0, 0]:
        G = G[::-1]
    verts, codes, width = layout(text, prop, size, tracking)
    if valign == "middle":
        offset -= 0.35 * size                       # roughly half the cap height of these faces
    L = np.hypot(*np.diff(G, axis=0).T).sum()
    start = at * L - width / 2
    if start < 0 or start + width > L:              # the guide is too short; extend it straight at both ends
        ext = width
        t0 = G[1] - G[0]; t0 /= np.hypot(*t0); t1 = G[-1] - G[-2]; t1 /= np.hypot(*t1)
        G = np.concatenate([[G[0] - t0 * ext], G, [G[-1] + t1 * ext]])
        G = resample(G, 0.5, 0)
        start += ext
    P = bend(verts, G, start, offset)
    path = Path(paper.to_data(P), codes)
    effects = [pe.withStroke(linewidth=halo_pt, foreground=halo, alpha=halo_alpha)] if halo else []
    patch = PathPatch(path, facecolor=color, edgecolor="none", lw=0, alpha=alpha, zorder=zorder, path_effects=effects)
    ax.add_patch(patch)
    return patch


def straight_label(ax, paper, text, xy, prop, size, color, ha="center", va="baseline", halo=None, halo_pt=2.0,
                   tracking=0.0, angle=0.0, zorder=20, alpha=1.0, dx=0.0, dy=0.0, clip=True):
    """A straight label at data point xy, offset (dx, dy) points, rotated by angle degrees, as glyph outlines."""
    verts, codes, width = layout(text, prop, size, tracking)
    if not len(verts):
        return None
    u0 = {"left": 0.0, "center": -width / 2, "right": -width}[ha]
    v0 = {"baseline": 0.0, "center": -0.35 * size, "top": -0.72 * size, "bottom": 0.22 * size}[va]
    P = verts + [u0, v0]
    a = np.radians(angle)
    R = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])
    P = P @ R + paper.to_pt([xy])[0] + [dx, dy]
    effects = [pe.withStroke(linewidth=halo_pt, foreground=halo)] if halo else []
    patch = PathPatch(Path(paper.to_data(P), codes), facecolor=color, edgecolor="none", lw=0, alpha=alpha,
                      zorder=zorder, path_effects=effects, clip_on=clip)
    ax.add_patch(patch)
    return patch, width


def fp(family, weight="normal", style="normal"):
    return FontProperties(family=family, weight=weight, style=style)
