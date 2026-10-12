"""site_icons.py: the index of chart forms, one small circular icon per form, grouped by the job of the data.

After the R Graph Gallery's chart-type index, drawn in Vellum's own logic: each family of data job takes one colour
family, the disc is the tint (area) and the marks are the tone (line), with the surface colour as the spacer. Colours
are CSS variables, so the icons follow the theme. build_site.py writes the index into <!--#formsindex-->.
"""
import json, math, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
T, D, S, BG = "var(--ic)", "var(--ic-deep)", "var(--v-surface)", "var(--ic-tint)"   # tone, deep, surface, disc


def dot(x, y, r=4.2, fill=T):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" style="fill:{fill};stroke:{S};stroke-width:1.6"/>'


def line(pts, w=3.2, col=T, extra=""):
    return f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" style="fill:none;stroke:{col};stroke-width:{w};stroke-linecap:round;stroke-linejoin:round{extra}"/>'


def rect(x, y, w, h, fill=T, rx=0):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" style="fill:{fill}"/>'


def path(d, fill=T, stroke="none", w=0):
    return f'<path d="{d}" style="fill:{fill};stroke:{stroke};stroke-width:{w};stroke-linejoin:round"/>'


def curve(xs, f):
    return [(x, f(x)) for x in xs]


def gauss(x, m, s): return math.exp(-((x - m) / s) ** 2 / 2)


XS = [12 + i * 2 for i in range(39)]


# ---------------------------------------------------------------- distribution
def violin():
    up = [(50 + 26 * (0.25 * gauss(y, 34, 6) + gauss(y, 60, 10) * 0.9 + 0.08), y) for y in range(14, 88, 2)]
    lo = [(100 - x, y) for x, y in up][::-1]
    pts = up + lo
    return path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z") + rect(46, 52, 8, 16, S, 2)


def density():
    c = curve(XS, lambda x: 82 - 58 * (0.75 * gauss(x, 38, 9) + 0.45 * gauss(x, 64, 8)))
    return path("M12,82 L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in c) + " L88,82Z")


def histogram():
    hs = [10, 22, 40, 52, 38, 30, 44, 26, 12]
    return "".join(rect(14 + i * 8, 82 - h, 6.6, h) for i, h in enumerate(hs))


def boxplot():
    return (line([(14, 50), (34, 50)], 2.4) + line([(66, 50), (86, 50)], 2.4) + rect(34, 34, 32, 32, T, 2)
            + line([(48, 34), (48, 66)], 3, S))


def ridgeline():
    out = ""
    for k, (m, y0) in enumerate(((40, 34), (56, 50), (46, 66), (62, 82))):
        c = curve(XS, lambda x, m=m, y0=y0: y0 - 20 * gauss(x, m, 7))
        out += path("M12," + str(y0) + " L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in c) + f" L88,{y0}Z", S) + line(c, 2.6)
    return out


def beeswarm():
    pts = []
    for i, x in enumerate(range(18, 84, 6)):
        n = [1, 2, 3, 4, 5, 5, 4, 3, 2, 2, 1][i]
        for j in range(n): pts.append((x, 50 + (j - (n - 1) / 2) * 7.5))
    return "".join(dot(x, y, 3.6) for x, y in pts)


# ---------------------------------------------------------------- relation
def axes_l():
    return line([(18, 18), (18, 82), (84, 82)], 1.6, D)


def scatter():
    pts = [(28, 70), (34, 62), (38, 66), (44, 54), (50, 56), (54, 44), (60, 48), (64, 38), (70, 34), (74, 26), (46, 64), (66, 44)]
    return axes_l() + "".join(dot(x, y) for x, y in pts)


def heatmap():
    v = [[2, 3, 4, 5, 6, 6], [1, 2, 4, 5, 5, 6], [1, 2, 3, 4, 5, 5], [0, 1, 2, 3, 4, 4], [0, 0, 1, 2, 3, 3], [0, 0, 0, 1, 2, 2]]
    fills = [S, "var(--ic-tint)", "color-mix(in oklab, var(--ic) 35%, var(--v-surface))", "color-mix(in oklab, var(--ic) 60%, var(--v-surface))",
             T, "color-mix(in oklab, var(--ic) 70%, var(--ic-deep))", D]
    return rect(0, 0, 100, 100, S) + "".join(rect(4 + j * 15.4, 4 + i * 15.4, 14.2, 14.2, fills[v[i][j]]) for i in range(6) for j in range(6))


def correlogram():
    out = ""
    for i in range(5):
        for j in range(i + 1):
            r = 3 + 4.5 * abs(math.cos(i * 1.3 + j * 0.7))
            out += f'<circle cx="{20 + j * 15}" cy="{20 + i * 15}" r="{r:.1f}" style="fill:{T if (i + j) % 3 else D}"/>'
    return out


def bubble():
    return axes_l() + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" style="fill:{T};stroke:{S};stroke-width:1.6;opacity:.9"/>'
                              for x, y, r in ((36, 64, 8), (56, 46, 13), (72, 30, 6), (44, 38, 5), (68, 62, 9)))


def connected():
    pts = [(24, 70), (36, 60), (34, 46), (48, 40), (60, 48), (58, 32), (72, 26)]
    return line(pts, 2.6) + "".join(dot(x, y, 3.6) for x, y in pts)


def hexbin():
    out = ""
    for i in range(6):
        for j in range(6):
            x = 16 + j * 13.5 + (6.75 if i % 2 else 0); y = 16 + i * 11.7
            d = math.hypot(x - 50, y - 50)
            if d > 40: continue
            f = T if d < 14 else ("color-mix(in oklab, var(--ic) 55%, var(--v-surface))" if d < 26 else S)
            pts = " ".join(f"{x + 7 * math.cos(math.radians(a + 30)):.1f},{y + 7 * math.sin(math.radians(a + 30)):.1f}" for a in range(0, 360, 60))
            out += f'<polygon points="{pts}" style="fill:{f}"/>'
    return out


# ---------------------------------------------------------------- comparison
def barh():
    return "".join(rect(18, 20 + i * 13, w, 9) for i, w in enumerate((62, 50, 42, 30, 20)))


def lollipop():
    out = ""
    for i, h in enumerate((44, 56, 30, 62, 38, 50)):
        x = 20 + i * 12
        out += line([(x, 82), (x, 82 - h)], 1.6, D) + dot(x, 82 - h, 4.4)
    return out


def dotplot():
    out = ""
    for i, v in enumerate((76, 66, 58, 50, 40, 32)):
        y = 22 + i * 11.5
        out += line([(16, y), (84, y)], 1, D, ";opacity:.35") + dot(v, y, 4)
    return out


def dumbbell():
    out = ""
    for i, (a, b) in enumerate(((24, 70), (30, 62), (40, 78), (22, 50), (34, 58))):
        y = 24 + i * 13
        out += line([(a, y), (b, y)], 2.2, D) + f'<circle cx="{a}" cy="{y}" r="3.6" style="fill:{S};stroke:{D};stroke-width:2"/>' + dot(b, y, 4.4)
    return out


def slope():
    out = line([(26, 16), (26, 84)], 1.2, D) + line([(74, 16), (74, 84)], 1.2, D)
    for a, b, c in ((70, 30, T), (52, 58, D), (38, 22, D), (60, 70, D)):
        out += line([(26, a), (74, b)], 3 if c == T else 1.8, c) + dot(26, a, 3.6, c) + dot(74, b, 3.6, c)
    return out


def bump():
    out = ""
    ranks = ((1, 2, 1, 3), (2, 1, 3, 1), (3, 3, 2, 2), (4, 4, 4, 4))
    for k, r in enumerate(ranks):
        pts = [(20 + i * 20, 18 + rr * 15) for i, rr in enumerate(r)]
        out += line(pts, 3 if k == 1 else 1.8, T if k == 1 else D) + "".join(dot(x, y, 3.4, T if k == 1 else D) for x, y in pts)
    return out


# ---------------------------------------------------------------- part of a whole
def stackedbar():
    cols = (T, D, S, "color-mix(in oklab, var(--ic) 45%, var(--v-surface))")
    out = ""
    for i, seg in enumerate(((30, 22, 14, 10), (22, 30, 16, 8), (36, 14, 18, 8))):
        x = 12
        for c, w in zip(cols, seg):
            out += rect(x, 26 + i * 18, w - 1.6, 13, c); x += w
    return out


def waffle():
    return "".join(rect(14 + (k % 10) * 7.4, 14 + (9 - k // 10) * 7.4, 6.2, 6.2, T if k < 37 else S) for k in range(100))


def treemap():
    return (rect(10, 10, 46, 80, T) + rect(58, 10, 32, 44, D) + rect(58, 56, 32, 34, S)
            + rect(58, 56, 15, 34, "color-mix(in oklab, var(--ic) 45%, var(--v-surface))"))


def pie(r0=0):
    out = ""; a = -90
    for frac, c in ((0.46, T), (0.30, D), (0.24, S)):
        b = a + frac * 360
        x1, y1 = 50 + 32 * math.cos(math.radians(a)), 50 + 32 * math.sin(math.radians(a))
        x2, y2 = 50 + 32 * math.cos(math.radians(b)), 50 + 32 * math.sin(math.radians(b))
        large = 1 if frac > 0.5 else 0
        out += path(f"M50,50 L{x1:.1f},{y1:.1f} A32,32 0 {large} 1 {x2:.1f},{y2:.1f}Z", c, S, 2)
        a = b
    if r0: out += f'<circle cx="50" cy="50" r="{r0}" style="fill:{BG}"/>'
    return out


def doughnut(): return pie(16)


# ---------------------------------------------------------------- change over time
def lines():
    a = [(14, 70), (30, 62), (46, 64), (62, 48), (80, 34)]
    b = [(14, 78), (30, 74), (46, 70), (62, 66), (80, 60)]
    return line(b, 3, D) + line(a, 3) + dot(80, 34, 4.6) + dot(80, 60, 4.6, D)


def band():
    c = curve(XS, lambda x: 72 - 0.5 * (x - 12) - 4 * math.sin(x / 6))
    hi = [(x, y - 6 - 0.12 * (x - 12)) for x, y in c]; lo = [(x, y + 6 + 0.12 * (x - 12)) for x, y in c]
    return (path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in hi + lo[::-1]) + "Z", S) + line(c, 3) + dot(88, c[-1][1], 4.4))


def area():
    c = curve(XS, lambda x: 66 - 0.45 * (x - 12) - 7 * math.sin(x / 7))
    return path("M12,84 L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in c) + " L88,84Z")


def stackedarea():
    out = ""; base = [84] * len(XS)
    layers = (lambda x: 14 + 4 * math.sin(x / 9), lambda x: 12 + 0.12 * x, lambda x: 10 + 6 * math.cos(x / 11))
    cols = (T, D, "color-mix(in oklab, var(--ic) 45%, var(--v-surface))")
    for f, c in zip(layers, cols):
        top = [b - f(x) for b, x in zip(base, XS)]
        out += path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(XS, top)) + " L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(XS[::-1], base[::-1])) + "Z", c, S, 1.4)
        base = top
    return out


def stream():
    out = ""; mid = [50 + 6 * math.sin(x / 10) for x in XS]
    widths = (lambda x: 6 + 6 * gauss(x, 40, 12), lambda x: 5 + 8 * gauss(x, 62, 10), lambda x: 4 + 5 * gauss(x, 30, 9))
    tot = [sum(w(x) for w in widths) for x in XS]
    base = [m - t for m, t in zip(mid, tot)]
    for w, c in zip(widths, (T, D, "color-mix(in oklab, var(--ic) 45%, var(--v-surface))")):
        top = [b + 2 * w(x) for b, x in zip(base, XS)]
        out += path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(XS, base)) + " L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(XS[::-1], top[::-1])) + "Z", c, S, 1.4)
        base = top
    return out


def multiples():
    out = ""
    for k, (ox, oy) in enumerate(((16, 18), (52, 18), (16, 54), (52, 54))):
        out += line([(ox - 2, oy + 30), (ox + 34, oy + 30)], 1.2, D, ";opacity:.5")
        for j in range(3):
            pts = [(ox + i * 8, oy + 24 - i * (2 + j) - (3 if (i + j) % 2 else 0)) for i in range(5)]
            out += line(pts, 1.2, D, ";opacity:.45")
        pts = [(ox + i * 8, oy + 26 - i * (3 + k) + (4 if i == 2 and k == 1 else 0)) for i in range(5)]
        out += line(pts, 2.6)
    return out


# ---------------------------------------------------------------- maps (Natural Earth outlines, simplified)
_LAND = None


def land():
    global _LAND
    if _LAND is None:
        ne = json.load(open(os.path.join(REPO, "data", "ne_110m_admin_0_countries.geojson"), encoding="utf-8"))
        polys = []
        for f in ne["features"]:
            cont = f["properties"]["CONTINENT"]
            if cont in ("Antarctica", "Seven seas (open ocean)"): continue
            g = f["geometry"]; rings = g["coordinates"] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
            if g["type"] == "Polygon": rings = [rings[0]]
            for r in rings:
                pts = []
                for lon, lat in r:
                    x, y = round(44 + lon / 180 * 74, 1), round(50 - lat / 90 * 46 + 12, 1)   # large: the disc crops the Pacific
                    if not pts or abs(pts[-1][0] - x) + abs(pts[-1][1] - y) > 1.6: pts.append((x, y))
                if len(pts) >= 4: polys.append((cont, pts))
        _LAND = polys
    return _LAND


CONT_FILL = {"Africa": T, "Europe": D, "Asia": "color-mix(in oklab, var(--ic) 55%, var(--v-surface))", "North America": D,
             "South America": "color-mix(in oklab, var(--ic) 55%, var(--v-surface))", "Oceania": T}


def choropleth():
    return "".join(f'<polygon points="{" ".join(f"{x},{y}" for x, y in pts)}" style="fill:{CONT_FILL[c]};stroke:{BG};stroke-width:.5"/>' for c, pts in land())


def bubblemap():
    base = "".join(f'<polygon points="{" ".join(f"{x},{y}" for x, y in pts)}" style="fill:{S}"/>' for c, pts in land())
    return base + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" style="fill:{T};stroke:{S};stroke-width:1.4;opacity:.9"/>'
                          for x, y, r in ((95, 36, 7), (88, 46, 5), (58, 58, 6), (18, 30, 6), (50, 26, 4), (28, 72, 4.5)))


def tilemap():
    out = ""
    shape = ["..xx.....", ".xxxx..x.", "xxxxxxxx.", ".xxxxxxx.", "..xxxxx..", "...xxx...", "....x...."]
    for i, row in enumerate(shape):
        for j, ch in enumerate(row):
            if ch != "x": continue
            f = (T, D, "color-mix(in oklab, var(--ic) 55%, var(--v-surface))", S)[(i * 3 + j * 5) % 4]
            out += rect(10 + j * 9, 20 + i * 9, 8, 8, f, 1.5)
    return out


# ---------------------------------------------------------------- flow, trees, networks
def tree():
    tips = [22, 34, 46, 58, 70, 80]
    out = line([(18, 28), (18, 75)], 2, D)
    out += line([(18, 28), (40, 28)], 2, D) + line([(40, 22), (40, 34)], 2, D) + line([(40, 22), (78, 22)], 2) + line([(40, 34), (78, 34)], 2)
    out += line([(18, 75), (32, 75)], 2, D) + line([(32, 58), (32, 86)], 2, D) + line([(32, 58), (52, 58)], 2, D) + line([(52, 46), (52, 70)], 2, D)
    out += line([(52, 46), (78, 46)], 2, D) + line([(52, 70), (78, 70)], 2, D) + line([(32, 86), (78, 86)], 2, D)
    for y, c in ((22, T), (34, T), (46, D), (70, D), (86, D)): out += dot(78, y, 4, c)
    return out


def network():
    nodes = [(50, 50), (28, 34), (30, 66), (70, 30), (74, 64), (48, 22), (52, 80), (20, 50), (84, 46)]
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 7), (2, 7), (3, 8), (4, 8), (1, 5), (2, 6), (3, 5)]
    out = "".join(line([nodes[a], nodes[b]], 1.2, D, ";opacity:.6") for a, b in edges)
    return out + "".join(dot(x, y, 6 if k == 0 else 4, T if k in (0, 1, 2, 5) else D) for k, (x, y) in enumerate(nodes))


def sankey():
    out = ""
    for (y0, h0, y1, h1) in ((18, 22, 16, 14), (40, 14, 32, 22), (54, 26, 56, 26)):
        out += path(f"M22,{y0} C50,{y0} 50,{y1} 78,{y1} L78,{y1 + h1} C50,{y1 + h1} 50,{y0 + h0} 22,{y0 + h0}Z",
                    "color-mix(in oklab, var(--ic) 45%, var(--v-surface))")
    return out + rect(14, 16, 8, 66, T, 1) + rect(78, 14, 8, 14, D, 1) + rect(78, 32, 8, 22, T, 1) + rect(78, 56, 8, 28, D, 1)


def chord():
    out = f'<circle cx="50" cy="50" r="34" style="fill:none;stroke:{T};stroke-width:6"/>'
    for a, b in ((20, 160), (60, 250), (120, 300), (200, 340)):
        x1, y1 = 50 + 30 * math.cos(math.radians(a)), 50 + 30 * math.sin(math.radians(a))
        x2, y2 = 50 + 30 * math.cos(math.radians(b)), 50 + 30 * math.sin(math.radians(b))
        out += f'<path d="M{x1:.1f},{y1:.1f} Q50,50 {x2:.1f},{y2:.1f}" style="fill:none;stroke:{D};stroke-width:2.4;opacity:.8"/>'
    return out


# ---------------------------------------------------------------- the third axis
def surface():
    out = ""
    stops = ("var(--v-lagoon-1)", "var(--v-lagoon-3)", "var(--v-lagoon-5)", "var(--v-lagoon-7)", "var(--v-lagoon-9)")
    for k, s in enumerate(stops):
        r = 36 - k * 7
        out += f'<ellipse cx="{50 + k * 2}" cy="{58 - k * 6}" rx="{r}" ry="{r * 0.42:.1f}" style="fill:{s};stroke:var(--v-surface);stroke-width:1"/>'
    return out


def scatter3d():
    box = line([(20, 70), (50, 84), (82, 70)], 1.4, D) + line([(20, 70), (20, 26)], 1.4, D) + line([(50, 84), (50, 40)], 1, D, ";opacity:.4")
    pts = [(36, 52), (44, 44), (40, 60), (58, 38), (64, 50), (70, 34), (54, 58), (30, 46)]
    drops = "".join(line([(x, y), (x, y + 18)], 1, D, ";opacity:.45;stroke-dasharray:1 3") for x, y in pts[:4])
    return box + drops + "".join(dot(x, y, 4, T if i < 5 else D) for i, (x, y) in enumerate(pts))


def twin():
    out = ""
    for k, r in enumerate((32, 24, 16, 8)):
        out += f'<circle cx="46" cy="54" r="{r}" style="fill:var(--v-lagoon-{3 + 2 * k});stroke:var(--v-surface);stroke-width:1.2"/>'
    return out + dot(46, 54, 3.6, "var(--v-terracotta)")


def dualaxis():
    # two lines on one hairline grid, each axis marked by a short key in its series colour
    grid = "".join(line([(18, y), (82, y)], 1.2, S) for y in (30, 50, 70))
    return (grid + line([(18, 86), (82, 86)], 1.4, D) + line([(10, 18), (16, 18)], 3, T) + line([(84, 18), (90, 18)], 3, D)
            + line([(20, 72), (36, 58), (52, 62), (68, 42), (80, 30)], 2.6) + line([(20, 40), (36, 46), (52, 34), (68, 56), (80, 64)], 2.6, D))


def wordcloud():
    words = (("Valjean", 19, 50, 50, T), ("Javert", 12, 30, 30, D), ("Marius", 12, 72, 30, D), ("Cosette", 11, 30, 71, D),
             ("Fantine", 11, 70, 71, D), ("Myriel", 8, 50, 86, D))
    return "".join(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" style="fill:{c};font-size:{s}px;font-family:var(--v-font-body);font-weight:700">{w}</text>' for w, s, x, y, c in words)


# family, colour family, anchor on forms.html, [(label, icon, href or None)]
ROWS = [
    ("Distribution", "ochre", "distribution", [("Violin", violin, None), ("Density", density, None), ("Histogram", histogram, None),
        ("Box plot", boxplot, None), ("Ridgeline", ridgeline, "science/penguins_distributions"), ("Beeswarm", beeswarm, None)]),
    ("Relation", "grey", "relation", [("Scatter", scatter, "science/penguins_scatter"), ("Heat map", heatmap, "science/disasters_heat"),
        ("Correlogram", correlogram, "science/cars_correlogram"), ("Bubble", bubble, None), ("Connected scatter", connected, "science/driving_connected"),
        ("2D density", hexbin, None)]),
    ("Comparison and ranking", "moss", "compare", [("Bar", barh, None), ("Lollipop", lollipop, None), ("Dot plot", dotplot, "report/report_dotplot"),
        ("Dumbbell", dumbbell, "report/report_dotplot"), ("Slope", slope, "science/life_slope"), ("Bump", bump, None),
        ("Word cloud", wordcloud, "science/miserables_wordcloud")]),
    ("Part of a whole", "terracotta", "whole", [("Stacked bar", stackedbar, None), ("Waffle", waffle, "infographic/story"),
        ("Treemap", treemap, None), ("Pie, six slices at most", pie, None), ("Doughnut", doughnut, None)]),
    ("Change over time", "indigo", "time", [("Line", lines, "science/co2_keeling"), ("Line with a band", band, "report/report_projection"),
        ("Area", area, None), ("Stacked area", stackedarea, "science/population_stacked"), ("Streamgraph", stream, None),
        ("Small multiples", multiples, "science/life_small_multiples"),
        ("Second y axis", dualaxis, "science/driving_dual_axis")]),
    ("Maps", "mauve", "maps", [("Choropleth", choropleth, "report/report_choropleth"), ("Bubble map", bubblemap, None),
        ("Tile map", tilemap, None)]),
    ("Flow, trees and networks", "teal", "networks", [("Tree", tree, "science/primates_tree"), ("Network", network, "science/miserables_network"),
        ("Sankey", sankey, None), ("Chord", chord, None)]),
    ("The third axis, with its twin", "lagoon", "threed", [("Surface", surface, "threed/landscape_surface"), ("3D scatter", scatter3d, "threed/penguins_scatter3d"),
        ("The flat twin", twin, "threed/landscape_surface")]),
]


TOOLS = [("vellum.json", "teal", "{ }", "source"), ("vellum.py", "indigo", "py", "matplotlib"),
         ("vellum.R", "moss", "R", "ggplot2"), ("vellum-colors.sty", "ochre", "TeX", "LaTeX"),
         ("vellum.css", "mauve", "css", "web"), ("vellum-web.js", "terracotta", "js", "SVG"),
         ("vellum-office.tsv", "grey", "tsv", "Office")]


def family_vars(fam):
    if fam == "grey":
        return "--ic:var(--v-secondary);--ic-tint:var(--v-grid);--ic-deep:var(--v-ink)"
    if fam == "lagoon":
        return "--ic:var(--v-teal);--ic-tint:var(--v-card);--ic-deep:var(--v-indigo)"
    return f"--ic:var(--v-{fam});--ic-tint:var(--v-{fam}-tint);--ic-deep:var(--v-{fam}-deep)"


def disc(fn, label):
    return (f'<span class="ic-disc"><svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
            f'<rect width="100" height="100" style="fill:{BG}"/>{fn()}</svg></span>')


def index(by_id=None, link_prefix=""):
    """The forms index as HTML. by_id: the gallery items, so an icon links to its example when there is one."""
    by_id = by_id or {}
    out = ['<div class="forms-index">']
    for name, fam, anchor, items in ROWS:
        out.append(f'<section class="fi-row" style="{family_vars(fam)}"><h3 class="fi-name"><span class="fi-key"></span>{name}</h3><ul class="fi-items">')
        for label, fn, key in items:
            if key and key in by_id:
                g, i = key.split("/")
                href = f"{link_prefix}gallery.html#g-{g}-{i}"
            else:
                href = f"{link_prefix}forms.html#{anchor}"
            out.append(f'<li><a class="fi-item" href="{href}">{disc(fn, label)}<span class="fi-label">{label}</span></a></li>')
        out.append("</ul></section>")
    out.append(f'<section class="fi-row" style="{family_vars("teal")}"><h3 class="fi-name"><span class="fi-key"></span>The style files</h3><ul class="fi-items fi-hexes">')
    for fn, fam, glyph, use in TOOLS:
        out.append(f'<li><a class="fi-item" href="{link_prefix}downloads/{fn}" style="{family_vars(fam)}">'
                   f'<span class="ic-hex"><svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
                   f'<polygon points="50,4 90,27 90,73 50,96 10,73 10,27" style="fill:var(--ic-tint);stroke:var(--ic);stroke-width:4"/>'
                   f'<text x="50" y="47" text-anchor="middle" style="fill:var(--ic-deep);font-family:Consolas,monospace;font-size:22px;font-weight:700">{glyph}</text>'
                   f'<text x="50" y="69" text-anchor="middle" style="fill:var(--ic-deep);font-family:var(--v-font-body);font-size:13px">{use}</text></svg></span>'
                   f'<span class="fi-label"><code>{fn}</code></span></a></li>')
    out.append("</ul></section></div>")
    return "\n".join(out)
