"""vis_kit.py: the country-level data and the drawing primitives of the three life-expectancy infographics.

Beyond story_kit.facts() (the world series and its falls), `atlas()` reads, for every country and territory:
  - period life expectancy at birth by year, data/owid-life-expectancy.csv (UN WPP 2024 via Our World in Data, CC BY 4.0)
  - its outline, UN region and estimated population, data/ne_110m_admin_0_countries.geojson (Natural Earth v5.1.2,
    public domain); POP_EST is Natural Earth's own estimate (2019), used only to rank and size countries
and derives the pandemic fall (lowest of 2020 and 2021 minus 2019), the recovery (2023 minus 2019), the spread of
countries by year and the six UN regions of the mapped countries. Nothing printed in the pieces is typed by hand.

Drawing: an Equal Earth projection, a binned colour scale sampled from a Vellum gradient (as CSS variables for both
twins), a beeswarm layout, and small SVG helpers that follow the Vellum rules (hairline grid, unit line, ringed dots,
direct labels, leaders without arrowheads).
"""
import json, math, os, statistics
from html import escape
from story_kit import (facts, num, col, f, textw, wrap, load_csv, vellum, REGIONS, MINUS)
from _common import DATA

YEARS_SWARM = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2023]
FAMILY = dict(zip(REGIONS, vellum.SPEC["order"]))          # UN regions in Vellum slot order: teal, terracotta, ...
SHORT = {"Latin America and the Caribbean": "Latin America", "Northern America": "Northern America"}
GEO_FIX = {"SAH": "ESH", "PSX": "PSE", "SDS": "SSD", "SOL": "SOM", "CYN": "CYP"}   # Natural Earth units -> ISO codes


def short(r): return SHORT.get(r, r)


def pct(vals, q):
    """The q-th percentile (0..100) by linear interpolation between order statistics."""
    v = sorted(vals); k = (len(v) - 1) * q / 100; lo = math.floor(k); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


# ---- data

def atlas():
    F = facts()
    le, code = {}, {}
    for r in load_csv("owid-life-expectancy.csv"):
        le.setdefault(r["Entity"], {})[int(r["Year"])] = float(r["Life expectancy"])
        code[r["Entity"]] = r["Code"]
    countries = sorted(e for e, c in code.items() if c and not c.startswith("OWID"))
    by_code = {code[e]: e for e in countries}
    base, low, last = F["base"], F["low"], F["last"]
    pan = range(base + 1, low + 1)
    dip = {e: min(le[e][y] for y in pan) - le[e][base] for e in countries}          # negative: a fall
    rec = {e: le[e][last] - le[e][base] for e in countries}
    fell = [e for e in countries if dip[e] < 0]
    status = {e: ("back" if rec[e] >= 0 else "below") if dip[e] < 0 else "nofall" for e in countries}

    geo = json.load(open(os.path.join(DATA, "ne_110m_admin_0_countries.geojson"), encoding="utf-8"))
    shapes, region, pop, labelpt = [], {}, {}, {}
    for ft in geo["features"]:
        p = ft["properties"]
        if p["CONTINENT"] == "Antarctica": continue
        iso = GEO_FIX.get(p["ADM0_A3"], p["ADM0_A3"])
        e = by_code.get(iso)
        shapes.append((e, ft["geometry"]))
        if e:
            r = p["REGION_UN"]
            if r == "Americas": r = "Northern America" if p["SUBREGION"] == "Northern America" else "Latin America and the Caribbean"
            region.setdefault(e, r); labelpt.setdefault(e, (p["LABEL_X"], p["LABEL_Y"]))
            if p["ADM0_A3"] not in ("SOL", "CYN"): pop[e] = pop.get(e, 0) + p["POP_EST"]   # breakaway units: outline only
    mapped = sorted(region)
    assert set(region.values()) == set(REGIONS), set(region.values())

    spread = {y: (pct([le[e][y] for e in countries], 10), pct([le[e][y] for e in countries], 25),
                  statistics.median([le[e][y] for e in countries]),
                  pct([le[e][y] for e in countries], 75), pct([le[e][y] for e in countries], 90))
              for y in F["years"]}
    biggest = sorted(mapped, key=lambda e: -pop[e])[:8]
    rank_fall = sorted(countries, key=lambda e: dip[e])
    F.update(le=le, countries=countries, dip=dip, rec=rec, fell=fell, status=status, shapes=shapes, region=region,
             pop=pop, labelpt=labelpt, mapped=mapped, spread=spread, biggest=biggest, rank_fall=rank_fall)
    # the region of each mapped country's own deepest fall, for the map's words
    F["reg_med_dip"] = {r: statistics.median([dip[e] for e in mapped if region[e] == r]) for r in REGIONS}
    F["china_famine"] = max((le["China"][a] - le["China"][b], a, b) for a in range(1955, 1962) for b in range(a, 1963))
    return F


# ---- colour scales: a Vellum gradient sampled into bins, written as CSS variables for both twins

def _hex(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def sample(stops, t):
    t = min(max(t, 0), 1) * (len(stops) - 1); i = min(int(t), len(stops) - 2); u = t - i
    a, b = _hex(stops[i]), _hex(stops[i + 1])
    return "#" + "".join(f"{round(x + (y - x) * u):02X}" for x, y in zip(a, b))


def scale_css(name, grad, n, t0=0.1, t1=0.95, first=0):
    """CSS variables --name-<first> .. --name-<first+n-1>, sampled evenly from t0 to t1 of the gradient, both twins."""
    g = vellum.SPEC["gradients"][grad]
    out = []
    for sel, mode in ((":root", "light"), (':root[data-theme="dark"]', "dark")):
        v = "; ".join(f"--{name}-{k + first}: {sample(g[mode], t0 + (t1 - t0) * k / (n - 1))}" for k in range(n))
        out.append(f"{sel} {{ {v}; }}")
    return "\n".join(out)


# ---- projection

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
SQ3 = math.sqrt(3)


def equal_earth(lon, lat):
    l, p = math.radians(lon), math.radians(lat)
    th = math.asin(SQ3 / 2 * math.sin(p)); t2 = th * th; t6 = t2 * t2 * t2
    x = 2 * SQ3 * l * math.cos(th) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, -y


class Map:
    """Equal Earth fitted to width w, latitudes lat0..lat1 shown; X(lon, lat) -> px."""
    def __init__(self, w, lat0=-56, lat1=84, ox=0, oy=0):
        x0, _ = equal_earth(-180, 0); x1, _ = equal_earth(180, 0)
        _, ytop = equal_earth(0, lat1); _, ybot = equal_earth(0, lat0)
        self.k = w / (x1 - x0); self.x0, self.y0 = x0, ytop
        self.w, self.h = w, (ybot - ytop) * self.k; self.ox, self.oy = ox, oy

    def P(self, lon, lat):
        x, y = equal_earth(lon, lat)
        return self.ox + (x - self.x0) * self.k, self.oy + (y - self.y0) * self.k

    def path(self, geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        d = []
        for poly in polys:
            for ring in poly:
                pts = [self.P(lo, max(la, -89)) for lo, la in ring]
                d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        return "".join(d)

    def outline(self, lat0=-56, lat1=84):
        """The graticule frame of the shown band: left and right meridians, flat top and bottom."""
        left = [self.P(-180, la) for la in range(lat1, lat0 - 1, -2)]
        right = [self.P(180, la) for la in range(lat0, lat1 + 1, 2)]
        return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in left + right) + "Z"


# ---- beeswarm

def swarm(vals, r, gap=0.6):
    """x offsets (px) for dots at y positions `vals` (px), packed as close to 0 as they go without overlap."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    placed, out, d = [], [0.0] * len(vals), 2 * r + gap
    for i in order:
        y = vals[i]
        near = [(px, py) for px, py in placed if abs(py - y) < d]
        bad = []
        for px, py in near:
            dx = math.sqrt(max(d * d - (py - y) ** 2, 0)); bad.append((px - dx, px + dx))
        cands = [0.0] + [b for a, b2 in bad for b in (a, b2)]
        cands.sort(key=abs)
        for c in cands:
            if all(not (a + 1e-6 < c < b - 1e-6) for a, b in bad):
                out[i] = c; break
        placed.append((out[i], y))
    return out


# ---- svg helpers

def T(x, y, s, size, color="ink", anchor="start", face="body", weight=None, ls=None, italic=False, extra=""):
    """Text centred vertically on y."""
    fam = ' font-family="var(--v-font-title)"' if face == "title" else ""
    w = f' font-weight="{weight}"' if weight else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{f(x)}" y="{f(y)}" dy="0.32em" font-size="{f(size)}" fill="{col(color)}" '
            f'text-anchor="{anchor}"{fam}{w}{l}{it}{extra}>{escape(s)}</text>')


def halo(x, y, s, size, color="ink", anchor="start", **kw):
    """Text with a surface-coloured halo, for labels that sit over lines or shapes."""
    return (T(x, y, s, size, "surface", anchor, extra=f' stroke="{col("surface")}" stroke-width="{f(size * 0.28)}" '
              f'stroke-linejoin="round"', **kw) + T(x, y, s, size, color, anchor, **kw))


def L(x1, y1, x2, y2, color="grid", w=1, dash=None, cap="butt", op=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' stroke-opacity="{op}"' if op is not None else ""
    return (f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{col(color)}" stroke-width="{f(w)}" '
            f'stroke-linecap="{cap}"{da}{o}/>')


def PL(pts, color, w, op=None, dash=None, fill="none"):
    o = f' stroke-opacity="{op}"' if op is not None else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" fill="{fill}" stroke="{col(color)}" '
            f'stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"{o}{da}/>')


def AREA(top, bot, color, op=None):
    pts = top + list(reversed(bot))
    o = f' fill-opacity="{op}"' if op is not None else ""
    return f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" fill="{col(color)}"{o}/>'


def DOT(x, y, r, color, ring=1.2, stroke="surface", op=None):
    o = f' fill-opacity="{op}"' if op is not None else ""
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col(color)}"{o} stroke="{col(stroke)}" stroke-width="{f(ring)}"/>'


def RING(x, y, r, color, w=1.4, fill="surface"):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col(fill)}" stroke="{col(color)}" stroke-width="{f(w)}"/>'


def RECT(x, y, w, h, color, rx=0, op=None, raw=False):
    fill = color if raw else col(color)
    o = f' fill-opacity="{op}"' if op is not None else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(max(w, 0))}" height="{f(max(h, 0))}" rx="{f(rx)}" fill="{fill}"{o}/>'


def leader(pts, w=0.9):
    """A thin muted leader through points, no arrowhead."""
    return PL(pts, "muted", w)


def lin(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def svgdoc(w, h, parts, label):
    return (f'<svg width="{f(w)}" height="{f(h)}" viewBox="0 0 {f(w)} {f(h)}" role="img" aria-label="{escape(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>")


def signed(x, nd=1):
    return num(x, nd, sign=True)
