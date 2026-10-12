"""_eco.py: what the ecology composites share on top of _common.

Tables exported by export_data.R from data/ecology/, axes placed in inches from the top left of the figure (so that a
composite's margins and gutters are exact, whatever its height), panel heads, and halos for labels over data.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *                                       # noqa: F401,F403
from matplotlib import patheffects as pe
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

ECO = os.path.join(DATA, "ecology")


def table(name):
    """A CSV of data/ecology as a dict of columns: numpy float arrays where every value parses, string arrays otherwise."""
    rows = list(csv.DictReader(open(os.path.join(ECO, name), encoding="utf-8")))
    out = {}
    for k in rows[0]:
        col = [r[k] for r in rows]
        try:
            out[k] = np.array([float(v) if v not in ("NA", "") else np.nan for v in col])
        except ValueError:
            out[k] = np.array(col)
    return out


def axes_in(fig, left, top, width, height, **kw):
    """Axes placed in inches: `left` and `top` from the top-left corner of the figure."""
    W, H = fig.get_size_inches()
    return fig.add_axes([left / W, 1 - (top + height) / H, width / W, height / H], **kw)


def halo(V, w=2.4):
    return [pe.withStroke(linewidth=w * V.scale, foreground=V.surface)]


def minus(s):
    """Typographic minus for negative numbers in text."""
    return str(s).replace("-", "−")


def head(V, ax, letter, claim, unit=None, pad=None, dx_in=0.0):
    """Panel head: bold letter and short claim, the unit line under it (V.panel). dx_in moves both left by that many
    inches, so a panel whose tick labels are long (species names) starts its head where its labels start."""
    n = len(ax.texts)
    V.panel(ax, letter, claim, unit=unit)
    t = ax._left_title                                         # V.panel sets the left-located title
    if pad is not None:
        t.set_y(1 + pad)
    if dx_in:
        x = -dx_in / (ax.get_position().width * ax.figure.get_size_inches()[0])
        t.set_x(x)
        for t in ax.texts[n:]: t.set_x(x)


def text(V, ax, x, y, s, size="annotation", color=None, ha="left", va="center", halo_w=None, **kw):
    """Annotation text in ink (or the given neutral) with an optional surface halo."""
    kw.setdefault("path_effects", halo(V, halo_w) if halo_w else None)
    return ax.text(x, y, s, fontsize=V.sz[size] if isinstance(size, str) else size, color=color or V.ink, ha=ha, va=va, **kw)


def clean(ax, grid=True):
    """No spines at all; keep the hairline y grid unless asked not to."""
    for s in ax.spines.values(): s.set_visible(False)
    if not grid: ax.grid(False)


def lens(r1, r2, d):
    """Area of the intersection of two circles of radii r1, r2 whose centres are d apart."""
    if d >= r1 + r2: return 0.0
    if d <= abs(r1 - r2): return np.pi * min(r1, r2) ** 2
    a = r1 ** 2 * np.arccos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1)) + r2 ** 2 * np.arccos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    return a - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def euler_geometry(total1, total2, shared):
    """Radii and centre distance of two circles with areas total1, total2 (shares of a unit square) overlapping by `shared`."""
    from scipy.optimize import brentq
    r1, r2 = np.sqrt(total1 / np.pi), np.sqrt(total2 / np.pi)
    d = brentq(lambda d: lens(r1, r2, d) - shared, abs(r1 - r2) + 1e-9, r1 + r2 - 1e-9)
    assert abs(lens(r1, r2, d) - shared) < 1e-9
    return r1, r2, d
