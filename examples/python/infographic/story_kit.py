"""story_kit.py: what make_infographics.py and make_pitch.py share.

1. `facts()`: every number of the life-expectancy story, computed from data/owid-life-expectancy.csv (Our World in
   Data, CC BY 4.0). Nothing printed in the pieces is typed by hand.
2. Inline-SVG primitives that draw by the Vellum rules: unit line above the y axis, hairline horizontal grid, bottom
   spine in grid colour, ringed dots, direct labels, callouts with leaders, a ten-by-ten waffle, a dot timeline and the
   world line chart that every format shares (infographics note 1332.16, one master, several formats). Colours are
   the CSS variables of docs/assets/css/vellum-tokens.css, which is generated from vellum.json; mark sizes are read
   from vellum.json and scaled per medium.
3. `page()`, the HTML template every piece is generated from, `render()` (tools/render.py), and `words()`.
"""
import math, os, re, sys
from html import escape
from string import Template
from PIL import ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import REPO, DOCS, load_csv, vellum, stamp, record, rel   # noqa: E402  (DOCS, record, rel, stamp re-exported)
sys.path.insert(0, os.path.join(REPO, "tools"))
import render as _render                                                 # noqa: E402

SOURCE = "UN World Population Prospects (2024)"                         # the source of every value from 1950 on
SOURCE_FULL = ("UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva "
               "(2015), Riley (2005); processed by Our World in Data, downloaded 2026-10-12")   # data/SOURCES.md, verbatim
DATE = "12 October 2026"
AUTHOR, URL = "A. Kaminas", "akaminas.github.io/vellum"
REGIONS = ["Africa", "Asia", "Europe", "Latin America and the Caribbean", "Northern America", "Oceania"]  # UN regions
MINUS = "\u2212"


def spell(n):
    """Small whole numbers in words, as running text wants them."""
    return ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"][n]


def num(x, nd=1, sign=False):
    """A number as printed: a true minus sign (U+2212), a plus only when asked for."""
    s = f"{abs(x):.{nd}f}"
    return (MINUS if x < 0 and float(s) != 0 else "+" if sign else "") + s


# ---- the facts

def facts():
    le, code = {}, {}
    for r in load_csv("owid-life-expectancy.csv"):
        le.setdefault(r["Entity"], {})[int(r["Year"])] = float(r["Life expectancy"])
        code[r["Entity"]] = r["Code"]
    w = {y: v for y, v in le["World"].items() if y >= 1950}
    years = sorted(w)
    # falls: runs of consecutive yearly declines, peak to trough, as (peak year, trough year, years lost)
    falls, run = [], None
    for a, b in zip(years, years[1:]):
        if w[b] < w[a]:
            run = (run[0] if run else a, b)
        elif run:
            falls.append((*run, w[run[0]] - w[run[1]])); run = None
    pan = next(f for f in falls if f[0] < 2020 <= f[1])                  # the run that holds 2020
    deeper = [f for f in falls if f[1] < pan[0] and f[2] > pan[2]]       # earlier falls deeper than the pandemic's
    prior = max(deeper, key=lambda f: f[1])
    base, low, last = pan[0], pan[1], years[-1]
    assert w[last] == max(w.values()), "the last year is no longer the record; rewrite the claims"
    level = min((y for y in years if y < base), key=lambda y: abs(w[y] - w[low]))   # the earlier year the low matches
    first = {t: min(y for y in years if w[y] >= t) for t in (50, 60, 70)}
    countries = [e for e, c in code.items() if c and not c.startswith("OWID")]
    fell = [e for e in countries if min(le[e][y] for y in range(base + 1, low + 1)) < le[e][base]]
    back = [e for e in countries if le[e][last] >= le[e][base]]
    reg = {r: {y: v for y, v in le[r].items() if y >= 1950} for r in REGIONS}
    rfall = {r: reg[r][base] - reg[r][low] for r in REGIONS}
    assert all(reg[r][last] > reg[r][base] for r in REGIONS), "a region is still below its pre-pandemic level"
    return dict(
        world=w, years=years, regions=reg, rfall=rfall, base=base, low=low, last=last, first=first, level=level,
        pan=pan, prior=prior, start=years[0],
        drop=pan[2], prior_drop=prior[2], since=prior[1],
        n=len(countries), n_fell=len(fell), n_back=len(back),
        pct_fell=round(100 * len(fell) / len(countries)), pct_back=round(100 * len(back) / len(countries)),
        n_years=len(years), country_years=sum(len([y for y in le[e] if y >= 1950]) for e in countries),
        worst=max(rfall, key=rfall.get), mildest=min(rfall, key=rfall.get),
    )


# ---- type and marks

FONTS = {"body": "C:/Windows/Fonts/corbel.ttf", "title": "C:/Windows/Fonts/pala.ttf"}
_cache = {}


def textw(s, size, face="body"):
    """Advance width of a string in px, measured with the face the page uses (Corbel or Palatino Linotype)."""
    key = (face, round(size * 4))
    if key not in _cache: _cache[key] = ImageFont.truetype(FONTS[face], size=round(size * 4))
    return _cache[key].getlength(s) / 4


class Marks:
    """Mark sizes of one medium: the print sizes of vellum.json times `scale`, in px at `px_pt` pixels per point."""
    def __init__(self, px_pt, scale, text):
        mk, k = vellum.SPEC["marks"], px_pt * scale
        self.line, self.thin, self.grid, self.ring = mk["line_pt"] * k, mk["thin_line_pt"] * k, mk["grid_pt"] * k, mk["ring_pt"] * k
        self.spine, self.leader = 0.8 * k, 0.5 * k
        self.r = math.sqrt(mk["marker_pt2"]) / 2 * k                     # marker 28 pt², radius in px
        self.dots = [d * self.thin for d in mk["dotted"]]                 # dotted 1 on 3, in line widths
        self.text = text                                                  # px size of figure text


def col(name):
    """A colour by its token name in vellum-tokens.css: 'ink', 'rule', 'teal', 'teal-tint', 'terracotta-deep' ..."""
    return f"var(--v-{name})"


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def svg_text(x, y, s, size, color="ink", anchor="start", face="body", extra=""):
    """Text centred vertically on y (dy 0.32 em puts the middle of the lower case on y)."""
    fam = ' font-family="var(--v-font-title)"' if face == "title" else ""
    return (f'<text x="{f(x)}" y="{f(y)}" dy="0.32em" font-size="{f(size)}" fill="{col(color)}" '
            f'text-anchor="{anchor}"{fam}{extra}>{escape(s)}</text>')


def svg(w, h, parts, label):
    return (f'<svg width="{f(w)}" height="{f(h)}" viewBox="0 0 {f(w)} {f(h)}" role="img" aria-label="{escape(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>")


class Chart:
    """A plot in inline SVG. box = (left, top, right, bottom) of the plot area in px; data limits map onto it."""
    def __init__(self, w, h, xlim, ylim, m, box):
        self.w, self.h, self.m, self.xlim, self.ylim = w, h, m, xlim, ylim
        self.l, self.t, self.r, self.b = box
        self.p = []

    def X(self, x): return self.l + (x - self.xlim[0]) / (self.xlim[1] - self.xlim[0]) * (self.r - self.l)
    def Y(self, y): return self.b - (y - self.ylim[0]) / (self.ylim[1] - self.ylim[0]) * (self.b - self.t)

    def ygrid(self, ticks, fmt=str, labels=True):
        """Horizontal hairlines in the grid colour behind the data, tick labels in muted, no tick marks."""
        for t in ticks:
            y = self.Y(t)
            self.p.append(f'<line x1="{f(self.l)}" y1="{f(y)}" x2="{f(self.r)}" y2="{f(y)}" stroke="{col("grid")}" stroke-width="{f(self.m.grid)}"/>')
            if labels: self.p.append(svg_text(self.l - 0.5 * self.m.text, y, fmt(t), self.m.text, "muted", "end"))

    def spine(self):
        """The bottom spine, in the grid colour; there is no left, top or right spine."""
        self.p.append(f'<line x1="{f(self.l)}" y1="{f(self.b)}" x2="{f(self.r)}" y2="{f(self.b)}" stroke="{col("grid")}" stroke-width="{f(self.m.spine)}"/>')

    def xaxis(self, ticks, fmt=str, anchors=None):
        for i, t in enumerate(ticks):
            self.p.append(svg_text(self.X(t), self.b + 1.25 * self.m.text, fmt(t), self.m.text, "muted", (anchors or {}).get(i, "middle")))

    def unit(self, s, x=0):
        """The unit line: a noun phrase in muted, above the y axis, never rotated."""
        self.p.append(svg_text(x, self.t - 1.1 * self.m.text, s, self.m.text, "muted"))

    def line(self, xs, ys, color, width=None, extra=""):
        pts = " ".join(f"{f(self.X(x))},{f(self.Y(y))}" for x, y in zip(xs, ys))
        self.p.append(f'<polyline points="{pts}" fill="none" stroke="{col(color)}" stroke-width="{f(width or self.m.line)}" '
                      f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')

    def hline(self, y, color="ochre"):
        """A reference line: thin and dotted, 1 on 3."""
        Y = self.Y(y); d = self.m.dots
        self.p.append(f'<line x1="{f(self.l)}" y1="{f(Y)}" x2="{f(self.r)}" y2="{f(Y)}" stroke="{col(color)}" '
                      f'stroke-width="{f(self.m.thin)}" stroke-dasharray="{f(d[0])} {f(d[1])}"/>')

    def dot(self, x, y, color, px=False):
        cx, cy = (x, y) if px else (self.X(x), self.Y(y))
        self.p.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(self.m.r)}" fill="{col(color)}" stroke="{col("surface")}" stroke-width="{f(self.m.ring)}"/>')

    def text(self, x, y, s, color="ink", anchor="start", px=False, size=None):
        cx, cy = (x, y) if px else (self.X(x), self.Y(y))
        self.p.append(svg_text(cx, cy, s, size or self.m.text, color, anchor))

    def leader(self, x1, y1, x2, y2):
        """A thin muted leader, no arrowhead; coordinates in px."""
        self.p.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{col("muted")}" stroke-width="{f(self.m.leader)}"/>')

    def svg(self, label):
        return svg(self.w, self.h, self.p, label)


def spread(ys, gap):
    """Push label positions apart to at least `gap`, order kept (vellum.spread)."""
    return list(vellum.spread(ys, gap))


# ---- the shared figures

def world_chart(F, w, h, m, tick_w=None):
    """World life expectancy 1950 to the last year: the long rise in rule grey, the pandemic fall in terracotta,
    the earlier deeper fall named in a quiet note, a ringed end dot with its direct label. The master figure."""
    W, Y0, Y1 = F["world"], F["start"], F["last"]
    s = m.text
    yt = [40, 50, 60, 70]
    tick_w = tick_w or max(textw(str(t), s) for t in yt) + 0.5 * s
    end = f"{num(W[Y1])} in {Y1}"
    c = Chart(w, h, (Y0, Y1), (40, 76), m, (tick_w, 2.2 * s, w - textw(end, s) - m.r - 0.6 * s, h - 2.0 * s))
    c.ygrid(yt); c.spine()
    c.xaxis([1950, 1970, 1990, 2010])
    c.unit("life expectancy at birth, years")
    pre = [y for y in F["years"] if y <= F["base"]]; post = [y for y in F["years"] if y >= F["low"]]
    pan = [y for y in F["years"] if F["base"] <= y <= F["low"]]
    c.line(pre, [W[y] for y in pre], "rule"); c.line(post, [W[y] for y in post], "rule")
    c.line(pan, [W[y] for y in pan], "terracotta")                        # the one thing: terracotta, the rest rule grey
    c.dot(F["low"], W[F["low"]], "terracotta")
    c.dot(Y1, W[Y1], "rule")
    c.text(c.X(Y1) + m.r + 0.4 * s, c.Y(W[Y1]), end, px=True)
    # callout for the pandemic fall: below the line where the plot is empty, joined by a leader
    p0, p1 = F["pan"][:2]
    lx, ly = c.X(F["low"]), c.Y(W[F["low"]]) + 2.6 * s
    c.leader(lx, c.Y(W[F["low"]]) + m.r + 2, lx, ly - 0.7 * s)
    c.text(lx, ly, f"{p0 + 1}–{str(p1)[2:]}: {num(-F['drop'])}", anchor="middle", px=True)
    # quiet note on the earlier, deeper fall, which is what "since 1960" is measured against
    q0, q1 = F["prior"][:2]
    c.text(c.X(q1), c.Y(W[q1]) + 1.25 * s, f"{q0 + 1}–{str(q1)[2:]}: {num(-F['prior_drop'])}", "muted", "middle", px=True)
    return c


def dot_timeline(w, h, xlim, events, m, line="rule", lw=None):
    """A horizontal dot plot of events: ringed dots on a line, labels above in ink (tier 2 sits higher, joined to its
    dot by a leader, for an event too close to its neighbour), the date below in muted. Each event is a dict with
    x, color, above (lines), below (text) and optionally tier and anchor ('middle', 'start', 'end')."""
    s = m.text; y0 = h - 1.75 * s
    c = Chart(w, h, xlim, (0, 1), m, (0, 0, w, y0))
    c.p.append(f'<line x1="0" y1="{f(y0)}" x2="{f(w)}" y2="{f(y0)}" stroke="{col(line)}" stroke-width="{f(lw or m.line)}" stroke-linecap="round"/>')
    for e in events:
        x, a = c.X(e["x"]), e.get("anchor", "middle")
        top = y0 - m.r - 0.9 * s - (e.get("tier", 1) - 1) * 2.4 * s
        if e.get("tier", 1) > 1: c.leader(x, top + 0.75 * s, x, y0 - m.r - 2)
        for k, t in enumerate(reversed(e["above"])):
            c.text(x, top - k * 1.3 * s, t, e.get("ink", "ink"), a, px=True)
        bx = min(max(x, textw(e["below"], s) / 2), w - textw(e["below"], s) / 2)   # centred under the dot, kept on the sheet
        c.text(bx, y0 + m.r + 0.75 * s, e["below"], "muted", "middle", px=True)
        c.dot(x, y0, e["color"], px=True)
    return c


def waffle(n, color, cell, gap=2):
    """Ten by ten squares with a surface gap, the counted ones in the tone and the rest in the grid colour,
    filled from the bottom left in reading order. Returns (svg parts, size in px)."""
    size = 10 * cell + 9 * gap; parts = []
    for k in range(100):
        row, c = divmod(k, 10)
        x, y = c * (cell + gap), size - (row + 1) * cell - row * gap
        parts.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(cell)}" height="{f(cell)}" fill="{col(color if k < n else "grid")}"/>')
    return parts, size


# ---- pages

PAGE = Template("""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=$w">
<title>$title</title>
<meta name="description" content="$desc">
<meta name="generator" content="$script · git $stamp">
<link rel="stylesheet" href="../../assets/css/vellum-tokens.css">
<link rel="stylesheet" href="../../assets/fonts/fonts.css">
<link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body { margin: 0; background: var(--v-surface); }
body { font-family: var(--v-font-body); color: var(--v-ink); font-kerning: normal; }
svg { display: block; overflow: visible; }
svg text { font-family: var(--v-font-body); }
.box { position: absolute; margin: 0; }
$css
</style>
</head>
<body>
$body
</body>
</html>
""")


def page(path, title, desc, body, css, w, script):
    html = PAGE.substitute(w=w, title=escape(title), desc=escape(desc), body=body, css=css, script=rel(script), stamp=stamp())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    return html


def box(cls, x, y, w, h, inner, extra=""):
    """An absolutely placed block on the sheet's grid; its size is fixed so an overflow shows in the QA pass."""
    return f'<div class="box {cls}" style="left:{f(x)}px;top:{f(y)}px;width:{f(w)}px;height:{f(h)}px"{extra}>{inner}</div>'


def wrap(text, size, width, face="body", slack=0.97):
    """Greedy line breaks as the browser makes them, with a little slack for hinting; returns the lines."""
    lines, cur = [], ""
    for w in text.split(" "):                      # plain spaces only, so a no-break space holds its words together
        t = (cur + " " + w).strip(" ")
        if cur and textw(t, size, face) > slack * width: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur]


def fits(text, size, width, n, face="body"):
    """Assert that a text block wraps to at most n lines in its box, so no box overflows."""
    k = len(wrap(text, size, width, face))
    assert k <= n, f"{text!r} needs {k} lines at {size}px in {width:.0f}px, the box has {n}"
    return text


def words(html):
    """Words a reader meets on the sheet: every token of visible text with a letter or a digit in it."""
    body = re.sub(r"(?s)<head>.*?</head>", " ", html)
    text = re.sub(r"<[^>]+>", " ", body)
    return [t for t in text.split() if re.search(r"\w", t)]


def render(html, png, w, h, scale=2, fragment=""):
    """PNG of a page (or of one #fragment of it) at `scale` device pixels per CSS pixel, via tools/render.py."""
    url = _render.url(html) + fragment
    _render.run([f"--window-size={w},{h}", f"--force-device-scale-factor={scale}", f"--screenshot={os.path.abspath(png)}", url])
    return png
