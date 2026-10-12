"""_sus.py: what the sustainability composites share.

Loaders for the Our World in Data files in data/sustainability/ (written by fetch_data.py), the continent of each
country (from the Natural Earth outlines), the Equal Earth map, a squarified treemap, the LMDI decomposition, and the
inch-exact layout of a composite: axes placed in inches, a panel head (bold letter, short claim, unit line) a fixed
number of points above each plot area, and the title block and footer of the figure.
"""
import os, sys, csv, collections, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *                                     # noqa: F401,F403  (np, plt, vellum, save, rel, footer, DATA ...)
import logging
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, FancyBboxPatch
from matplotlib import patheffects as pe
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

SUS = os.path.join(DATA, "sustainability")
FETCHED = json.load(open(os.path.join(SUS, "fetched.json"), encoding="utf-8"))
DOWNLOADED = FETCHED["downloaded"]

SRC_CO2 = (f"Global Carbon Budget (2025), Energy Institute, Maddison Project (2023), UN WPP; "
           f"OWID CO₂ dataset, CC BY 4.0, downloaded {DOWNLOADED}")
SRC_ENERGY = (f"Ember (2026), Energy Institute Statistical Review (2025), U.S. EIA; "
              f"OWID energy dataset, CC BY 4.0, downloaded {DOWNLOADED}")
SRC_GCB = f"Global Carbon Budget (2025) via Our World in Data, CC BY 4.0, downloaded {DOWNLOADED}"
SRC_NE = "outlines Natural Earth v5.1.2, public domain"
SRC_MLO = f"Mauna Loa CO₂, NOAA GML and Scripps, public domain, downloaded {DOWNLOADED}"

PT = 1 / 72
MINUS = "−"


def num(v, d=0, sign=False):
    """A number with a true minus sign, d decimals, an optional plus sign, and a thin space as thousands separator."""
    s = f"{v:+,.{d}f}" if sign else f"{v:,.{d}f}"
    return s.replace(",", " ").replace("-", MINUS)


# ================================================================ data

def owid(name):
    """data/sustainability/<name> as {country: {year: {column: float or None}}} and {country: iso code}."""
    out, iso = collections.defaultdict(dict), {}
    for r in csv.DictReader(open(os.path.join(SUS, name), encoding="utf-8")):
        c, y = r.pop("country"), int(r.pop("year")); iso[c] = r.pop("iso_code")
        out[c][y] = {k: (float(v) if v not in ("", None) else None) for k, v in r.items()}
    return out, iso


def series(D, country, col, years):
    """One column of one country over `years` as a float array, NaN where missing."""
    d = D.get(country, {})
    return np.array([(d.get(y, {}).get(col) if d.get(y, {}).get(col) is not None else np.nan) for y in years], float)


def is_country(code):
    """A three-letter ISO code (OWID's aggregates have none or start with OWID_; Kosovo is OWID_KOS and is kept)."""
    return bool(code) and (len(code) == 3 or code == "OWID_KOS")


def geo():
    """Natural Earth features keyed by OWID code, with name, continent and geometry."""
    feats = json.load(open(os.path.join(DATA, "ne_110m_admin_0_countries.geojson"), encoding="utf-8"))["features"]
    out = {}
    for f in feats:
        p = f["properties"]
        code = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
        code = {"KOS": "OWID_KOS"}.get(code, code)
        out[code] = dict(code=code, name=p["NAME"], continent=p["CONTINENT"], geom=f["geometry"])
    return out


# countries too small for the 1:110 m outlines, with their continent, so every country can take a continent colour
SMALL = {"SGP": "Asia", "BHR": "Asia", "HKG": "Asia", "MAC": "Asia", "MDV": "Asia", "MUS": "Africa", "CPV": "Africa",
         "COM": "Africa", "STP": "Africa", "SYC": "Africa", "MLT": "Europe", "AND": "Europe", "LIE": "Europe", "MCO": "Europe",
         "SMR": "Europe", "BRB": "North America", "ATG": "North America", "DMA": "North America", "GRD": "North America",
         "KNA": "North America", "LCA": "North America", "VCT": "North America", "ABW": "North America", "CUW": "North America",
         "SXM": "North America", "BMU": "North America", "CYM": "North America", "TCA": "North America", "VGB": "North America",
         "AIA": "North America", "MSR": "North America", "KIR": "Oceania", "MHL": "Oceania", "FSM": "Oceania", "NRU": "Oceania",
         "PLW": "Oceania", "TON": "Oceania", "TUV": "Oceania", "WSM": "Oceania", "NIU": "Oceania", "COK": "Oceania",
         "PYF": "Oceania", "WLF": "Oceania", "BRN": "Asia", "PSE": "Asia", "TWN": "Asia"}
CONTINENTS = ["Asia", "Europe", "North America", "Africa", "South America", "Oceania"]


def continent_of():
    g = geo(); out = {k: v["continent"] for k, v in g.items()}
    out.update({k: v for k, v in SMALL.items() if k not in out})
    out = {k: ("Asia" if v == "Seven seas (open ocean)" and k in ("MDV",) else v) for k, v in out.items()}
    return out


# ================================================================ maths

def lmdi(c0, c1, f0, f1):
    """Additive LMDI-I (Ang 2004): the change c1 − c0 of a product c = Π f split exactly into one term per factor,
    L(c1, c0) · ln(f1 / f0), with L the logarithmic mean. f0, f1: dicts of factor values."""
    L = (c1 - c0) / np.log(c1 / c0) if c1 != c0 else c0
    return {k: L * np.log(f1[k] / f0[k]) for k in f0}


def squarify(values, x, y, w, h):
    """Squarified treemap (Bruls, Huizing and van Wijk 2000): rectangles (x, y, w, h) for values sorted descending,
    filling the box (x, y, w, h). Values are scaled to the box area."""
    vals = np.asarray(values, float); vals = vals * (w * h) / vals.sum()
    rects = []

    def worst(row, side):
        s = sum(row); return max(max(side * side * r / (s * s), (s * s) / (side * side * r)) for r in row)

    def lay(row, x, y, w, h):
        s = sum(row)
        if w >= h:                                          # a column on the left
            cw = s / h; yy = y
            for r in row: rects.append((x, yy, cw, r / cw)); yy += r / cw
            return x + cw, y, w - cw, h
        rh = s / w; xx = x                                  # a row at the top (y grows downwards in the caller's frame)
        for r in row: rects.append((xx, y, r / rh, rh)); xx += r / rh
        return x, y + rh, w, h - rh

    i, row = 0, []
    while i < len(vals):
        side = min(w, h); v = vals[i]
        if not row or worst(row + [v], side) <= worst(row, side):
            row.append(v); i += 1
        else:
            x, y, w, h = lay(row, x, y, w, h); row = []
    if row: lay(row, x, y, w, h)
    return rects


# ---- the map: Equal Earth (Šavrič, Patterson and Jenny 2018), as in examples/python/report/make_report.py
EE = (1.340264, -0.081106, 0.000893, 0.003796)
MAP_LAT = (-56.5, 84.0)


def equal_earth(lon, lat):
    A1, A2, A3, A4 = EE
    th = np.arcsin(np.sqrt(3) / 2 * np.sin(np.radians(lat)))
    t2 = th * th; t6 = t2 ** 3
    x = 2 * np.sqrt(3) * np.radians(lon) * np.cos(th) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


def map_box():
    x0, x1 = equal_earth(np.array([-180.0, 180.0]), np.zeros(2))[0]
    y0, y1 = equal_earth(0.0, MAP_LAT[0])[1], equal_earth(0.0, MAP_LAT[1])[1]
    return x0, x1, y0, y1


def country_path(geom):
    """One compound path per country: exterior rings counter-clockwise, holes clockwise, so the non-zero rule cuts holes."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    verts, codes = [], []
    for poly in polys:
        for k, ring in enumerate(poly):
            r = np.array(ring, float); x, y = equal_earth(r[:, 0], r[:, 1])
            area = 0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
            if (area < 0) == (k == 0): x, y = x[::-1], y[::-1]
            verts += list(zip(x, y)); codes += [Path.MOVETO] + [Path.LINETO] * (len(x) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes)


def outline(ax):
    """The outline of the Equal Earth world (the graticule edge), as a hairline."""
    lat = np.linspace(-90, 90, 181)
    xl, yl = equal_earth(np.full_like(lat, -180.0), lat); xr, yr = equal_earth(np.full_like(lat, 180.0), lat[::-1])
    return np.r_[xl, xr], np.r_[yl, yr]


# ================================================================ layout in inches

class Sheet:
    """A figure laid out in inches from its top-left corner: at() places axes, text() writes at a point."""

    def __init__(self, V, w, h):
        self.V, self.w, self.h = V, w, h
        self.fig = plt.figure(figsize=(w, h))

    def at(self, left, top, width, height, **kw):
        return self.fig.add_axes([left / self.w, 1 - (top + height) / self.h, width / self.w, height / self.h], **kw)

    def text(self, x, y, s, **kw):
        return self.fig.text(x / self.w, 1 - y / self.h, s, **kw)

    def rule(self, x0, x1, y, color=None, lw=0.6):
        self.fig.add_artist(plt.Line2D([x0 / self.w, x1 / self.w], [1 - y / self.h] * 2, color=color or self.V.grid, lw=lw))

    def wrap(self, text, width, **kw):
        """Greedy word wrap to `width` inches, measured with the figure's renderer."""
        r = self.fig.canvas.get_renderer(); lines, cur = [], ""
        for word in text.split(" "):
            trial = (cur + " " + word).strip()
            t = self.fig.text(0, 0, trial, **kw); wide = t.get_window_extent(r).width / self.fig.dpi; t.remove()
            if wide > 0.985 * width and cur: lines.append(cur); cur = word
            else: cur = trial
        return lines + [cur]

    def header(self, title, subtitle, margin=0.12, width=None):
        """The claim in the serif and the subtitle in muted text, wrapped; returns the depth used in inches."""
        V = self.V; width = width or self.w - 2 * margin
        tl = self.wrap(title, width, fontsize=V.sz["title"], fontfamily=V.title_font)
        self.text(margin, 0.10, "\n".join(tl), fontsize=V.sz["title"], fontfamily=V.title_font, color=V.ink, va="top",
                  linespacing=1.12)
        y = 0.10 + (len(tl) - 1) * V.sz["title"] * 1.12 * PT + V.sz["title"] * 1.45 * PT
        sl = self.wrap(subtitle, width, fontsize=V.sz["subtitle"])
        self.text(margin, y, "\n".join(sl), fontsize=V.sz["subtitle"], color=V.muted, va="top", linespacing=1.25)
        return y + len(sl) * V.sz["subtitle"] * 1.25 * PT

    def footer(self, source, margin=0.12, width=None):
        """Source, script and stamp at the bottom, wrapped; returns its height in inches."""
        V = self.V; width = width or self.w - 2 * margin
        fl = self.wrap(source, width, fontsize=V.sz["footer"])
        self.text(margin, self.h - 0.06, "\n".join(fl), fontsize=V.sz["footer"], color=V.muted, va="bottom", linespacing=1.25)
        return 0.06 + len(fl) * V.sz["footer"] * 1.25 * PT


def head(V, ax, letter, claim, unit=None, gap=4, size=None, unit_x=0.0, dx=0.0):
    """Panel head above the plot area: the bold letter and a short claim (in ink, one line), then the unit line in muted
    text `gap` points above the plot area. Placed in points so it sits the same way above every panel."""
    fs = size or V.sz["panel_title"]
    uy = gap + (V.sz["unit_line"] * 1.25 if unit else 0)
    ax.annotate(letter, (0, 1), xycoords="axes fraction", xytext=(dx, uy + 3), textcoords="offset points", ha="left",
                va="bottom", fontsize=fs, fontweight="bold", color=V.ink, annotation_clip=False)
    if claim:
        ax.annotate(claim, (0, 1), xycoords="axes fraction", xytext=(dx + fs * 1.25, uy + 3), textcoords="offset points",
                    ha="left", va="bottom", fontsize=fs, color=V.ink, annotation_clip=False)
    if unit:
        ax.annotate(unit, (unit_x, 1), xycoords="axes fraction", xytext=(dx, gap), textcoords="offset points", ha="left",
                    va="bottom", fontsize=V.sz["unit_line"], color=V.muted, annotation_clip=False)


def halo(V, w=2.4):
    return [pe.withStroke(linewidth=w * V.scale, foreground=V.surface)]


def bare(ax):
    ax.set_axis_off()
    return ax
