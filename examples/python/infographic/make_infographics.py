"""make_infographics.py: three infographics on world life expectancy, 1950 to 2023, and the pandemic setback.

From data/owid-life-expectancy.csv (UN World Population Prospects 2024, processed by Our World in Data, CC BY 4.0) and
data/ne_110m_admin_0_countries.geojson (Natural Earth v5.1.2, public domain):
  story.html  -> story.png   1080 x 1920  portrait story in five numbered sections: the world and its regions since
                                          1950, a map of the pandemic fall, the six regions fall and recovery, a unit
                                          chart of every country, the eight most populous countries
  square.html -> square.png  1080 x 1080  one-glance summary: the world line inside the spread of all countries,
                                          three stat tiles, a mini map and the deepest falls
  sheet.html  -> sheet.png   1920 x 1080  landscape data sheet: a beeswarm of every mapped country by decade coloured by
                                          UN region, the fall against the level, and the narrowing spread
each with a dark twin (*_dark.png, the same page with data-theme="dark"), in docs/media/infographic/, rendered at 2x
with tools/render.py and recorded in docs/figures/infographic/. Every number is computed in story_kit.facts() and
vis_kit.atlas(); nothing is typed.
"""
import math, os, statistics
from html import escape
from story_kit import stamp, num, spell, fits, wrap, textw, page, box, words, render, record, rel, DOCS, SOURCE, SOURCE_FULL, AUTHOR, URL, REGIONS, f
from vis_kit import (atlas, Map, swarm, scale_css, T, halo, L, PL, AREA, DOT, RING, RECT, leader, lin, svgdoc, signed,
                     short, FAMILY, YEARS_SWARM, pct, vellum)

OUT = os.path.join(DOCS, "media", "infographic")
ISO = "2026-10-12"
G = 24                                            # gutter
NB = 6                                            # bins of the map scale: no fall, then five fall bins

THEME = '<script>if (location.hash === "#dark") document.documentElement.setAttribute("data-theme", "dark");</script>'


class Grid:
    def __init__(self, W, M=64, n=12):
        self.W, self.M, self.n = W, M, n
        self.colw = (W - 2 * M - (n - 1) * G) / n
    def x(self, c): return self.M + c * (self.colw + G)
    def w(self, span): return span * self.colw + (span - 1) * G


CSS = """
.sheet { position: relative; overflow: hidden; background: var(--v-surface); }
.kick { font-size: 15px; line-height: 20px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--v-muted);
        display: flex; justify-content: space-between; border-top: 2px solid var(--v-ink); padding-top: 10px; box-sizing: border-box; }
.num { display: flex; align-items: baseline; font-family: var(--v-font-title); color: var(--v-ink); white-space: nowrap; }
.num .u { font-size: 0.55em; margin-left: 0.12em; }
.num .lab { font: 20px/28px var(--v-font-body); color: var(--v-secondary); white-space: normal; margin-left: 28px; align-self: center; }
.head { font-family: var(--v-font-title); color: var(--v-ink); }
.deck { color: var(--v-secondary); }
.deck b, .lead b { color: var(--v-ink); font-weight: 400; }
.sec { border-top: 1px solid var(--v-rule); box-sizing: border-box; padding-top: 8px; display: grid; column-gap: 24px; }
.sec .n { font: 15px/38px var(--v-font-body); letter-spacing: 0.12em; color: var(--v-muted); }
.sec .t { font-family: var(--v-font-title); color: var(--v-ink); }
.sec .l { color: var(--v-secondary); grid-column: 2; }
.tile { background: var(--v-card); border-radius: 12px; box-sizing: border-box; }
.tile .v { font-family: var(--v-font-title); color: var(--v-ink); line-height: 1; white-space: nowrap; }
.tile .v .u { font-size: 0.5em; color: var(--v-secondary); margin-left: 0.15em; }
.tile .l { color: var(--v-secondary); }
.tile .k { color: var(--v-muted); }
.foot { font-size: 13px; line-height: 18px; color: var(--v-muted); border-top: 1px solid var(--v-rule); padding-top: 10px; box-sizing: border-box; }
.foot b { color: var(--v-secondary); font-weight: 400; }
"""


# ---- shared bits

def bx(cls, x, y, w, h, inner, style=""):
    """An absolutely placed block; its size is fixed so an overflow shows in the QA pass."""
    return f'<div class="box {cls}" style="left:{f(x)}px;top:{f(y)}px;width:{f(w)}px;height:{f(h)}px;{style}">{inner}</div>'


def kicker(g, y, left, right):
    return box("kick", g.x(0), y, g.w(12), 32, f"<span>{escape(left)}</span><span>{escape(right)}</span>")


def section(g, y, h, n, title, lead, c0=0, span=12, tsize=30, lsize=19, lh=27, nw=48):
    """A numbered section head: a rule, the number in muted small caps, a serif claim, one lead in secondary."""
    w = g.w(span) - nw - G
    fits(title, tsize, w, 1, "title"); fits(lead, lsize, w, 2)
    inner = (f'<div class="n">{n:02d}</div><div class="t" style="font-size:{tsize}px;line-height:38px">{escape(title)}</div>'
             + (f'<div class="l" style="font-size:{lsize}px;line-height:{lh}px">{escape(lead)}</div>' if lead else ""))
    return bx("sec", g.x(c0), y, g.w(span), h, inner, f"grid-template-columns:{nw}px 1fr")


def footer(g, y, h, F, method, c0=0, span=12):
    src = f"<b>Data</b> {escape(SOURCE_FULL)}; CC BY 4.0. Outlines and population: Natural Earth v5.1.2, public domain."
    meth = f"<b>Method</b> {escape(method)}"
    who = f"<b>Made</b> {ISO} · {AUTHOR} · Vellum example · {URL} · make_infographics.py · git {stamp()}"
    return box("foot", g.x(c0), y, g.w(span), h, f"<div>{src}</div><div>{meth}</div><div>{who}</div>")


def bins(F):
    """Map classes of the fall in years: 0 = no fall, then 0-1, 1-2, 2-3, 3-4, 4 and more."""
    edges = [0, 1, 2, 3, 4]
    def k(e):
        d = -F["dip"][e]
        if d <= 0: return 0
        return 1 + sum(d >= t for t in edges[1:])
    return k, edges


def world_map(F, w, ox=0, oy=0, labels=(), small=False, tsize=15, lat0=-56, lat1=84):
    """Choropleth of the pandemic fall (lowest of the two pandemic years minus the last year before it), on ember."""
    m = Map(w, lat0, lat1, ox=ox, oy=oy)
    k, _ = bins(F)
    parts = [f'<path d="{m.outline(lat0, lat1)}" fill="none" stroke="{"var(--v-grid)"}" stroke-width="1"/>']
    for e, geom in F["shapes"]:
        fill = "var(--v-grid)" if e is None else "var(--v-teal-tint)" if k(e) == 0 else f"var(--fall-{k(e)})"
        parts.append(f'<path d="{m.path(geom)}" fill="{fill}" stroke="var(--v-surface)" stroke-width="{0.5 if small else 0.7}" stroke-linejoin="round"/>')
    return m, parts


def legend_bar(F, x, y, sw, h, tsize, title=True):
    """Six swatches with their edges below: no fall, then years of fall."""
    _, edges = bins(F)
    p = []
    if title: p.append(T(x, y - 0.9 * tsize, "fall in life expectancy, years", tsize, "muted"))
    for i in range(NB):
        xx = x + i * (sw + 2) + (8 if i else 0)
        p.append(RECT(xx, y, sw, h, "var(--v-teal-tint)" if i == 0 else f"var(--fall-{i})", raw=True))
    p.append(T(x + sw / 2, y + h + 0.85 * tsize, "none", tsize, "muted", "middle"))
    for j, t in enumerate(edges):
        xx = x + 8 + (j + 1) * (sw + 2) - 1
        p.append(T(xx, y + h + 0.85 * tsize, str(t) if j < len(edges) - 1 else f"{t}+", tsize, "muted", "middle"))
    return p


# ---- story: 1080 x 1920

def pan_low(F, series):
    """The lowest value of a series in the pandemic years, and its year."""
    y = min(range(F["base"] + 1, F["low"] + 1), key=lambda k: series[k])
    return series[y], y


def story_main_chart(F, w, h, sm=15):
    """01: the world line on top of the six UN regions, the pandemic fall in terracotta, milestones and the famine."""
    Wd, R = F["world"], F["regions"]
    yr0, yr1 = F["start"], F["last"]
    base, low = F["base"], F["low"]
    rows = [(short(r), R[r][yr1], False) for r in REGIONS] + [("World", Wd[yr1], True)]
    namew = max(textw(n, sm) for n, _, _ in rows) + 14
    valw = textw("00.0", sm)
    l, r, t, b = 26, w - namew - valw - 22, 30, h - 28
    X, Y = lin(yr0, yr1, l, r), lin(30, 88, b, t)
    p = []
    for v in (30, 40, 50, 60, 70, 80):
        p.append(L(l, Y(v), r, Y(v), "grid", 1)); p.append(T(l - 8, Y(v), str(v), sm, "muted", "end"))
    p.append(L(l, b, r, b, "rule", 1))
    for yy in range(1950, 2021, 10):
        p.append(L(X(yy), b, X(yy), b + 5, "rule", 1)); p.append(T(X(yy), b + 17, str(yy), sm, "muted", "middle"))
    p.append(T(0, 6, "life expectancy at birth, years", sm, "muted"))
    # the pandemic years as a faint band, named at its foot
    p.append(RECT(X(base), t - 4, X(low) - X(base), b - t + 4, "terracotta-tint", op=0.4))
    # regions, faint; end labels for regions and the world spread apart in one column
    ends = []
    for reg in REGIONS:
        ys = sorted(R[reg])
        p.append(PL([(X(y), Y(R[reg][y])) for y in ys], "rule", 1.5))
        ends.append([Y(R[reg][yr1]), short(reg), R[reg][yr1], False])
    ends.append([Y(Wd[yr1]), "World", Wd[yr1], True])
    ends.sort()
    lab = list(vellum.spread([e[0] for e in ends], sm * 1.18))
    for (y0, name, v, wd), yl in zip(ends, lab):
        p.append(leader([(X(yr1) + (8 if wd else 3), y0), (X(yr1) + 14, yl)], 0.8))
        p.append(T(X(yr1) + 18, yl, name, sm + (1 if wd else 0), "ink" if wd else "muted", weight=700 if wd else None))
        p.append(T(w, yl, num(v), sm + (1 if wd else 0), "ink" if wd else "muted", "end", weight=700 if wd else None))
    # the world
    pre = [y for y in F["years"] if y <= base]; post = [y for y in F["years"] if y >= low]
    pan = [y for y in F["years"] if base <= y <= low]
    p.append(PL([(X(y), Y(Wd[y])) for y in pre], "teal", 3.4))
    p.append(PL([(X(y), Y(Wd[y])) for y in post], "teal", 3.4))
    p.append(PL([(X(y), Y(Wd[y])) for y in pan], "terracotta", 3.4))
    # milestones: the first year at 50, 60 and 70 (70 below the line, where the plot is empty)
    for th, dy, a in ((50, -28, "start"), (60, -26, "end"), (70, 28, "start")):
        y = F["first"][th]; x0, y0 = X(y), Y(Wd[y])
        p.append(leader([(x0, y0 + (6 if dy > 0 else -6)), (x0, y0 + dy + (-9 if dy > 0 else 9))], 0.8))
        p.append(halo(x0 + (4 if a == "end" else -4), y0 + dy, f"{th} years in {y}", sm, "secondary", a))
        p.append(RING(x0, y0, 4.2, "teal", 2))
    # the famine dip
    q0, q1 = F["prior"][:2]; cf = F["china_famine"]
    fx, fy = X(q1), Y(Wd[q1]); ly = Y(34)
    p.append(leader([(fx, fy + 6), (fx, ly - 20)], 0.8))
    p.append(halo(fx - 4, ly - 10, f"{q0 + 1}–{str(q1)[2:]}: {num(-F['prior_drop'])} years", sm, "ink"))
    p.append(halo(fx - 4, ly + 8, f"famine in China, where it fell {num(cf[0])}", sm, "muted"))
    p.append(DOT(fx, fy, 4.6, "teal", 1.6))
    # the pandemic fall and the record
    lx, lyy = X(low), Y(Wd[low]); bx0 = X(base) - 8
    p.append(leader([(lx, lyy - 7), (lx, t + 2), (bx0 + 4, t + 2)], 0.8))
    p.append(f'<text x="{f(bx0)}" y="{f(t + 2)}" dy="0.32em" font-size="{sm}" text-anchor="end" fill="var(--v-secondary)">'
             f'<tspan font-weight="700" fill="var(--v-ink)">{base + 1}–{str(low)[2:]}: {num(-F["drop"])} years,</tspan> '
             f'the deepest fall since {F["since"]}</text>')
    p.append(T(bx0, t + 21, f"then {num(Wd[yr1])} in {yr1}, a record", sm, "secondary", "end"))
    p.append(DOT(lx, lyy, 5.6, "terracotta", 1.8))
    p.append(DOT(X(yr1), Y(Wd[yr1]), 5.6, "teal", 1.8))
    return svgdoc(w, h, p, "World and regional life expectancy, 1950 to the last year")


MAP_CALLOUTS = [  # country, label offset from its label point in px, anchor: layout only, every number is computed
    ("United States", (-92, -34), "end"), ("Mexico", (-96, 4), "end"), ("Peru", (-150, -10), "end"),
    ("Bolivia", (-160, 30), "end"), ("Brazil", (96, 46), "start"), ("Nigeria", (-104, -34), "end"),
    ("Russia", (-64, -36), "end"), ("India", (14, 92), "start"), ("China", (112, 20), "start")]


def fall_txt(F, e):
    d = F["dip"][e]
    return f"{e} {num(d)}" if d < 0 else f"{e}, no fall"


def story_map(F, w, top=20, sm=15):
    """02: the choropleth with callouts in the oceans, the legend in the South Pacific."""
    m, p = world_map(F, w, oy=top, lat1=80)
    for e, (dx, dy), a in MAP_CALLOUTS:
        x0, y0 = m.P(*F["labelpt"][e])
        tx, ty = x0 + dx, (y0 + dy if dy is not None else 8)
        p.append(leader([(x0, y0), (tx + (6 if a == "end" else -6), ty)], 0.8))
        p.append(DOT(x0, y0, 2.8, "ink", 1.2))
        p.append(halo(tx, ty, fall_txt(F, e), sm, "ink", a))
    p += legend_bar(F, 4, top + m.h - 40, 40, 12, sm)
    return svgdoc(w, top + m.h, p, "Map of the fall in life expectancy from 2019 to the pandemic low, by country"), top + m.h


def story_regions(F, w, sm=15):
    """03: for the world and six regions, the fall to the pandemic low (terracotta) and the net change by the last
    year (teal), both against the last year before the pandemic; the level then in a column on the left."""
    R = dict(F["regions"]); R["World"] = F["world"]
    base, last = F["base"], F["last"]
    fall = {r: pan_low(F, R[r])[0] - R[r][base] for r in R}
    net = {r: R[r][last] - R[r][base] for r in R}
    rows = ["World"] + sorted(REGIONS, key=lambda r: fall[r])
    namew = max(textw(short(r), sm + 1) for r in rows) + 10
    lvw = textw("00.0", sm) + 10
    lo = math.floor(min(fall.values())); hi = math.ceil(max(net.values()) + 0.6)
    X = lin(lo - 0.9, hi, namew + lvw + 18, w - 8)
    top, rh = 44, 26
    yb = top + rh * (len(rows) - 1) + 14
    p = []
    for v in range(lo, hi + 1):
        p.append(L(X(v), top - 18, X(v), yb, "rule" if v == 0 else "grid", 1))
    p.append(T(namew + lvw, top - 30, str(base), sm, "muted", "end"))
    p.append(T(X(lo - 0.9), top - 30, f"fall to the low, then net change by {last}, years", sm, "muted"))
    for i, reg in enumerate(rows):
        y = top + i * rh; wd = reg == "World"
        if wd: p.append(RECT(-6, y - rh / 2 + 2, w + 6, rh - 4, "card", rx=4))
        p.append(T(0, y, short(reg), sm + 1, "ink", weight=700 if wd else None))
        p.append(T(namew + lvw, y, num(R[reg][base]), sm, "secondary", "end"))
        p.append(RECT(X(fall[reg]), y - 5, X(0) - X(fall[reg]), 10, "terracotta-tint"))
        p.append(L(X(fall[reg]), y - 7, X(fall[reg]), y + 7, "terracotta", 2.4))
        p.append(T(X(fall[reg]) - 7, y, num(fall[reg]), sm, "ink", "end"))
        p.append(L(X(0), y, X(net[reg]), y, "teal", 1.6))
        p.append(DOT(X(net[reg]), y, 5.2, "teal", 1.6))
        p.append(T(X(net[reg]) + 10, y, signed(net[reg]), sm, "ink"))
    return svgdoc(w, yb, p, "Fall and recovery of life expectancy by region"), yb


def story_units(F, w, sm=15, ncol=30):
    """04: one square per country or territory, grouped: fell and recovered, fell and still below, did not fall."""
    st = F["status"]
    groups = [("back", "teal"), ("below", "terracotta"), ("nofall", "rule")]
    seq = [(g_, c) for g_, c in groups for e in F["countries"] if st[e] == g_]
    gap = 3; cell = (w - (ncol - 1) * gap) / ncol; nrow = -(-len(seq) // ncol)
    p = []
    for k, (g_, c) in enumerate(seq):
        ci, ri = divmod(k, nrow)                                       # column-major: the groups read left to right
        p.append(RECT(ci * (cell + gap), ri * (cell + gap), cell, cell, c, rx=1.5))
    gh = nrow * (cell + gap) - gap
    n = {g_: sum(st[e] == g_ for e in F["countries"]) for g_, _ in groups}
    base, last = F["base"], F["last"]
    texts = {"back": ("fell, then rose above", f"their {base} level"),
             "below": ("fell, and were still", f"below it in {last}"),
             "nofall": ("did not fall", f"in {base + 1} or {F['low']}")}
    cw_ = (w - 2 * 16) / 3
    for j, (g_, c) in enumerate(groups):
        x = j * (cw_ + 16); y = gh + 22
        p.append(RECT(x, y - 6, 12, 12, c, rx=1.5))
        p.append(T(x + 20, y, str(n[g_]), 24, "ink", face="title"))
        p.append(T(x, y + 26, texts[g_][0], sm, "secondary"))
        p.append(T(x, y + 45, texts[g_][1], sm, "secondary"))
    h = gh + 22 + 56
    return svgdoc(w, h, p, f"{len(seq)} squares, one per country or territory, by pandemic fall and recovery"), h


def story_multiples(F, w, h, cols=4, rows=2, y0=2015, sm=15):
    """05: the eight most populous mapped countries, from y0 to the last year; every panel spans the same number of
    years of life expectancy, so the slopes compare; the dotted ochre line is the level of the year before."""
    le = F["le"]; base, low, last = F["base"], F["low"], F["last"]
    yrs = list(range(y0, last + 1))
    cs = F["biggest"]
    span = max(max(le[e][y] for y in yrs) - min(le[e][y] for y in yrs) for e in cs) + 0.8
    rg = 20
    pw = (w - (cols - 1) * G) / cols; ph = (h - (rows - 1) * rg) / rows
    p = []
    for i, e in enumerate(cs):
        ox, oy = (i % cols) * (pw + G), (i // cols) * (ph + rg)
        vals = [le[e][y] for y in yrs]
        mid = (max(vals) + min(vals)) / 2
        X, Y = lin(yrs[0], yrs[-1], ox + 4, ox + pw - 44), lin(mid - span / 2, mid + span / 2, oy + ph - 6, oy + 26)
        p.append(L(ox, oy + ph, ox + pw, oy + ph, "rule", 1))
        p.append(T(ox, oy + 8, e, sm + 1, "ink", weight=700))
        d = F["dip"][e]
        p.append(T(ox + pw, oy + 8, f"{num(d)} years" if d < 0 else "no fall", sm, "secondary", "end"))
        b = le[e][base]
        p.append(L(X(yrs[0]), Y(b), X(last), Y(b), "ochre", 1.3, dash="1.3 3.9", cap="round"))
        pre = [y for y in yrs if y <= base]; pan = [y for y in yrs if base <= y <= low]; post = [y for y in yrs if y >= low]
        p.append(PL([(X(y), Y(le[e][y])) for y in pre], "teal", 2.6))
        p.append(PL([(X(y), Y(le[e][y])) for y in post], "teal", 2.6))
        p.append(PL([(X(y), Y(le[e][y])) for y in pan], "terracotta", 2.6))
        v, ylow = pan_low(F, le[e])
        if d < 0: p.append(DOT(X(ylow), Y(v), 4.2, "terracotta", 1.4))
        p.append(DOT(X(last), Y(le[e][last]), 4.2, "teal", 1.4))
        p.append(T(X(last) + 9, Y(le[e][last]), num(le[e][last]), sm, "ink"))
    return svgdoc(w, h, p, "Life expectancy in the eight most populous countries since 2015")


def story(F):
    g = Grid(1080)
    Wd, base, low, last, start = F["world"], F["base"], F["low"], F["last"], F["start"]
    B = []
    B.append(kicker(g, 32, "World life expectancy at birth", f"{start}–{last} · {F['n']} countries and territories"))
    lab = fits(f"world life expectancy at birth, {base} to {low}, after seven decades of gains", 20, g.w(6), 2)
    hero = f'<span>{num(-F["drop"])}<span class="u">years</span></span><span class="lab">{escape(lab)}</span>'
    B.append(bx("num", g.x(0), 70, g.w(12), 100, hero, "font-size:96px;line-height:100px"))
    B.append(bx("head", g.x(0), 176, g.w(12), 124, escape(fits(headline(F), 54, g.w(12), 2, "title")), "font-size:54px;line-height:62px"))
    deck = (f"From {num(Wd[start])} years in {start}, the world gained {num(Wd[base] - Wd[start])} years of life expectancy by "
            f"{base}. Two pandemic years took {num(F['drop'])} of them back, to the level of {F['level']}. By {last} the loss "
            f"was made up, at {num(Wd[last])} years, a record.")
    B.append(bx("deck", g.x(0), 302, g.w(11), 58, escape(fits(deck, 19, g.w(11), 2)), "font-size:19px;line-height:28px"))
    gap = 14
    # 01
    y = 376
    B.append(section(g, y, 82, 1, "Seven decades of gains, then two years of loss",
                     f"The world (teal) and the six UN regions (grey), {start} to {last}; the pandemic years shaded."))
    B.append(box("fig", g.x(0), y + 88, g.w(12), 292, story_main_chart(F, g.w(12), 292)))
    y += 88 + 292 + gap + 6
    # 02
    worst = min(F["reg_med_dip"], key=F["reg_med_dip"].get)
    B.append(section(g, y, 82, 2, f"The fall was deepest in {short(worst)}",
                     f"Fall from {base} to the lower of {base + 1} and {low}, by country; "
                     f"the median country in {short(worst)} lost {num(-F['reg_med_dip'][worst])} years."))
    msvg, mh = story_map(F, g.w(12))
    B.append(box("fig", g.x(0), y + 66, g.w(12), mh, msvg))
    y += 66 + mh + gap
    # 03 and 04 side by side
    B.append(section(g, y, 82, 3, "All six regions fell, all recovered",
                     f"Life expectancy in {base}; the fall and the net change.", 0, 6, 24, 17, 24, 36))
    rsvg, rh = story_regions(F, g.w(6))
    B.append(box("fig", g.x(0), y + 80, g.w(6), rh, rsvg))
    B.append(section(g, y, 82, 4, f"{F['pct_back']} % were at or above {base} by {last}",
                     f"One square for each of the {F['n']} countries and territories.", 6, 6, 24, 17, 24, 36))
    usvg, uh = story_units(F, g.w(6))
    B.append(box("fig", g.x(6), y + 88, g.w(6), uh, usvg))
    y += max(80 + rh, 88 + uh) + gap
    # 05
    B.append(section(g, y, 48, 5, f"The eight most populous countries, 2015–{last}", "", 0, 12, 24, 17, 24, 36))
    B.append(box("fig", g.x(0), y + 50, g.w(12), 168, story_multiples(F, g.w(12), 168)))
    y += 50 + 168 + gap
    B.append(footer(g, y, 1920 - 16 - y, F, f"fall = the lower of {base + 1} and {low} minus {base}; {F['n']} countries and "
                    f"territories with an ISO code, {len(F['mapped'])} of them on the map; most populous by Natural Earth estimates."))
    return f'<main class="sheet" style="width:1080px;height:1920px">{"".join(B)}</main>'


def headline(F):
    return f"The pandemic brought world life expectancy its deepest fall since {F['since']}"


def alt_story(F):
    Wd = F["world"]
    return (f"World life expectancy fell {num(F['drop'])} years in {F['base'] + 1}–{str(F['low'])[2:]}, from {num(Wd[F['base']])} "
            f"to {num(Wd[F['low']])} years, the deepest fall since {F['since']}; by {F['last']} it reached a record {num(Wd[F['last']])} years.")


# ---- square: 1080 x 1080

def spread_chart(F, w, h, sm=15, label_w=None):
    """The world line inside the spread of all countries: the middle 80 % and the middle half as tint bands."""
    Wd, S = F["world"], F["spread"]
    yrs = F["years"]; yr0, yr1 = yrs[0], yrs[-1]; base, low = F["base"], F["low"]
    lw = label_w or 178
    l, r, t, b = 26, w - lw, 30, h - 28
    X, Y = lin(yr0, yr1, l, r), lin(30, 90, b, t)
    p = []
    for v in range(30, 91, 10):
        p.append(L(l, Y(v), r, Y(v), "grid", 1)); p.append(T(l - 8, Y(v), str(v), sm, "muted", "end"))
    p.append(L(l, b, r, b, "rule", 1))
    for yy in range(1950, 2021, 10):
        p.append(L(X(yy), b, X(yy), b + 5, "rule", 1)); p.append(T(X(yy), b + 17, str(yy), sm, "muted", "middle"))
    p.append(T(0, 6, "life expectancy at birth, years", sm, "muted"))
    p.append(RECT(X(base), t, X(low) - X(base), b - t, "terracotta-tint", op=0.4))
    band = lambda i: [(X(y), Y(S[y][i])) for y in yrs]
    p.append(AREA(band(4), band(0), "teal-tint", op=0.45))
    p.append(AREA(band(3), band(1), "teal-tint", op=0.9))
    p.append(PL(band(2), "teal-deep", 1.2, dash="1.5 3.5"))
    pre = [y for y in yrs if y <= base]; post = [y for y in yrs if y >= low]; pan = [y for y in yrs if base <= y <= low]
    p.append(PL([(X(y), Y(Wd[y])) for y in pre], "teal", 3.4))
    p.append(PL([(X(y), Y(Wd[y])) for y in post], "teal", 3.4))
    p.append(PL([(X(y), Y(Wd[y])) for y in pan], "terracotta", 3.4))
    # direct labels at the right end, spread apart, each joined to its band or line
    q = S[yr1]
    labs = [(Y(q[4]), "90th percentile", num(q[4])), (Y((q[3] + q[1]) / 2), "middle half", f"{num(q[1], 0)}–{num(q[3], 0)}"),
            (Y(q[2]), "median country", num(q[2])), (Y(Wd[yr1]), "World", num(Wd[yr1])), (Y(q[0]), "10th percentile", num(q[0]))]
    order = sorted(range(len(labs)), key=lambda i: labs[i][0])
    ys = list(vellum.spread([labs[i][0] for i in order], sm * 1.2))
    for i, yl in zip(order, ys):
        y0, name, v = labs[i]; wd = name == "World"
        p.append(leader([(r + 3, y0), (r + 9, yl)], 0.8))
        p.append(T(r + 12, yl, name, sm, "ink" if wd else "secondary", weight=700 if wd else None))
        p.append(T(w, yl, v, sm, "ink" if wd else "secondary", "end", weight=700 if wd else None))
    # the extremes of the last year, under the labels
    le = F["le"]; cs = F["countries"]
    hi_, lo_ = max(cs, key=lambda e: le[e][yr1]), min(cs, key=lambda e: le[e][yr1])
    ky = Y(52)
    p.append(L(r + 12, ky - 20, w, ky - 20, "rule", 1))
    p.append(T(r + 12, ky, f"in {yr1}, highest", sm, "muted"))
    p.append(T(r + 12, ky + 20, hi_, sm, "ink")); p.append(T(w, ky + 20, num(le[hi_][yr1]), sm, "ink", "end"))
    p.append(T(r + 12, ky + 46, "lowest", sm, "muted"))
    p.append(T(r + 12, ky + 66, lo_, sm, "ink")); p.append(T(w, ky + 66, num(le[lo_][yr1]), sm, "ink", "end"))
    p.append(T(r + 12, ky + 92, "gap", sm, "muted")); p.append(T(w, ky + 92, f"{num(le[hi_][yr1] - le[lo_][yr1])} years", sm, "ink", "end"))
    # annotations: the pandemic fall and the famine
    lx, ly = X(low), Y(Wd[low])
    p.append(DOT(lx, ly, 5.4, "terracotta", 1.8)); p.append(DOT(X(yr1), Y(Wd[yr1]), 5.4, "teal", 1.8))
    tx = X(base) - 10
    p.append(leader([(lx, ly - 7), (lx, t + 4), (tx + 4, t + 4)], 0.8))
    p.append(T(tx, t + 4, f"{base + 1}–{str(low)[2:]}: {num(-F['drop'])} years", sm, "ink", "end", weight=700))
    p.append(T(tx, t + 22, f"deepest fall since {F['since']}", sm, "secondary", "end"))
    q1 = F["prior"][1]
    p.append(DOT(X(q1), Y(Wd[q1]), 4.4, "teal", 1.6))
    fy = Y(S[q1][0]) + 30
    p.append(leader([(X(q1), Y(Wd[q1]) + 6), (X(q1), fy - 10)], 0.8))
    p.append(halo(X(q1) - 4, fy, f"{q1}: famine in China; the world fell {num(F['prior_drop'])}", sm, "secondary"))
    return svgdoc(w, h, p, "World life expectancy within the spread of all countries, 1950 to the last year")


def tile(x, y, w, h, value, unit, label, key="", vs=56, pad=22):
    v = f'<div class="v" style="font-size:{vs}px">{escape(value)}<span class="u">{escape(unit)}</span></div>'
    fits(label, 17, w - 2 * pad, 2)
    l = f'<div class="l" style="font-size:17px;line-height:23px;margin-top:10px">{escape(label)}</div>'
    k = f'<div class="k" style="font-size:14px;line-height:19px;margin-top:6px">{escape(key)}</div>' if key else ""
    return bx("tile", x, y, w, h, v + l + k, f"padding:{pad}px {pad}px")


def falls_bars(F, w, n=8, sm=15):
    """The deepest falls by country: tint bar, tone end mark, value; the region in muted."""
    cs = [e for e in F["rank_fall"] if e in F["region"]][:n]
    namew = max(textw(e, sm + 1) for e in cs) + 12
    lo = F["dip"][cs[0]]
    X = lin(math.floor(lo), 0, namew + 34, w)
    top, rh = 12, 26; p = []
    for i, e in enumerate(cs):
        y = top + i * rh; d = F["dip"][e]
        p.append(T(0, y, e, sm + 1, "ink"))
        p.append(RECT(X(d), y - 6, X(0) - X(d), 12, "terracotta-tint"))
        p.append(L(X(d), y - 8, X(d), y + 8, "terracotta", 2.4))
        p.append(T(X(d) - 7, y, num(d), sm, "ink", "end"))
        p.append(T(X(0) - 8, y, short(F["region"][e]), 13, "terracotta-deep", "end"))
    p.append(L(X(0), top - 12, X(0), top + rh * (n - 1) + 12, "rule", 1))
    h = top + rh * (n - 1) + 14
    return svgdoc(w, h, p, "The deepest pandemic falls by country"), h


def square_title(F):
    Wd = F["world"]
    return (f"World life expectancy fell {num(F['drop'])} years in the pandemic, then rose to a record "
            f"{num(Wd[F['last']])}")


def square(F):
    g = Grid(1080)
    Wd, base, low, last, start = F["world"], F["base"], F["low"], F["last"], F["start"]
    B = [kicker(g, 32, "World life expectancy at birth", f"{start}–{last}")]
    B.append(bx("head", g.x(0), 76, g.w(12), 110, escape(fits(square_title(F), 44, g.w(12), 2, "title")), "font-size:44px;line-height:52px"))
    B.append(box("fig", g.x(0), 212, g.w(8), 460, spread_chart(F, g.w(8), 460)))
    tw, th, tg = g.w(4), 140, 20
    n_fell = len(F["fell"])
    B.append(tile(g.x(8), 212, tw, th, num(-F["drop"]), " years",
                  f"the world, {base} to {low}, after {num(Wd[base] - Wd[start])} years gained since {start}"))
    B.append(tile(g.x(8), 212 + th + tg, tw, th, f"{round(100 * n_fell / F['n'])}", " %",
                  f"of {F['n']} countries and territories fell in {base + 1} or {low}"))
    B.append(tile(g.x(8), 212 + 2 * (th + tg), tw, th, f"{F['pct_back']}", " %",
                  f"were back at or above their {base} level by {last}"))
    # bottom row: mini map and the deepest falls
    y = 700
    B.append(bx("sec", g.x(0), y, g.w(7), 34, f'<div class="t" style="font-size:22px;line-height:30px">Fall, {base} to the pandemic low</div>', "display:block"))
    m = Map(g.w(7), lat1=80)
    _, mp = world_map(F, g.w(7), small=True, lat1=80)
    mp += legend_bar(F, 2, m.h - 30, 26, 9, 13, title=False)
    B.append(box("fig", g.x(0), y + 44, g.w(7), m.h, svgdoc(g.w(7), m.h, mp, "Map of the pandemic fall by country")))
    B.append(bx("sec", g.x(7), y, g.w(5), 34, '<div class="t" style="font-size:22px;line-height:30px">The deepest falls</div>', "display:block"))
    fsvg, fh = falls_bars(F, g.w(5))
    B.append(box("fig", g.x(7), y + 50, g.w(5), fh, fsvg))
    fy = max(y + 44 + m.h, y + 50 + fh) + 14
    B.append(bx("foot", g.x(0), fy, g.w(12), 1080 - 20 - fy,
                f"<div><b>Data</b> {escape(SOURCE)} and others via Our World in Data, CC BY 4.0; Natural Earth v5.1.2. "
                f"Fall = the lower of {base + 1} and {low} minus {base}.</div>"
                f"<div><b>Made</b> {ISO} · {AUTHOR} · Vellum example · {URL} · make_infographics.py · git {stamp()}</div>"))
    return f'<main class="sheet" style="width:1080px;height:1080px">{"".join(B)}</main>'


def alt_square(F):
    return alt_story(F) + f" {F['pct_back']} % of {F['n']} countries and territories were at or above their {F['base']} level in {F['last']}."


# ---- sheet: 1920 x 1080

def sheet_title(F):
    S, y0, y1 = F["spread"], F["start"], F["last"]
    a, b = S[y0][4] - S[y0][0], S[y1][4] - S[y1][0]
    return (f"Countries have drawn together: the middle 80 % spanned {num(a, 0)} years of life expectancy in {y0}, "
            f"{num(b, 0)} in {y1}")


def beeswarm(F, w, h, r=3.25, sm=15):
    """Every mapped country in each decade year, one dot each, coloured by UN region; the median and the middle 80 %."""
    le, reg = F["le"], F["region"]
    cs = F["mapped"]; yrs = YEARS_SWARM
    l, rr, t, b = 34, w - 10, 64, h - 30
    Y = lin(10, 90, b, t)
    xs = lin(0, len(yrs) - 1, l + 156, rr - 62)
    p = []
    for v in range(10, 91, 10):
        p.append(L(l, Y(v), rr, Y(v), "grid", 1)); p.append(T(l - 8, Y(v), str(v), sm, "muted", "end"))
    p.append(T(0, t - 26, "life expectancy at birth, years; one dot per country", sm, "muted"))
    meds = []
    pos = {}
    for j, yr in enumerate(yrs):
        vals = [Y(le[e][yr]) for e in cs]
        off = swarm(vals, r, 0.8)
        cx = xs(j)
        p.append(T(cx, b + 16, str(yr), sm + 1, "secondary", "middle"))
        q10, q50, q90 = F['spread'][yr][0], F['spread'][yr][2], F['spread'][yr][4]
        meds.append((cx, Y(q50), q50, q10, q90))
        for e, o, v in zip(cs, off, vals):
            pos[(e, yr)] = (cx + o, v)
        # the middle 80 %: a bracket on the left of each swarm
        bxl = cx - max(abs(o) for o in off) - 10
        p.append(PL([(bxl + 4, Y(q90)), (bxl, Y(q90)), (bxl, Y(q10)), (bxl + 4, Y(q10))], "secondary", 1.2))
    for (e, yr), (x, y) in pos.items():
        p.append(DOT(x, y, r, FAMILY[reg[e]], 0.9))
    # medians joined across the years
    p.append(PL([(m[0], m[1]) for m in meds], "ink", 1.4, dash="5 4"))
    for cx, my, q50, q10, q90 in meds:
        p.append(f'<line x1="{f(cx - 22)}" y1="{f(my)}" x2="{f(cx + 22)}" y2="{f(my)}" stroke="var(--v-ink)" stroke-width="2.4"/>')
    # notes on the first and last columns: the spread, the median
    for j in (0, len(yrs) - 1):
        cx, my, q50, q10, q90 = meds[j]
        side = -1 if j == 0 else 1
        bxl = cx - 10 - max(abs(pos[(e, yrs[j])][0] - cx) for e in cs)
        if j == 0:
            p.append(halo(bxl - 6, Y(q90), f"90th percentile {num(q90)}", sm, "secondary", "end"))
            p.append(halo(bxl - 6, Y(q10), f"10th percentile {num(q10)}", sm, "secondary", "end"))
            p.append(halo(bxl - 6, my, f"median {num(q50)}", sm, "ink", "end", weight=700))
    # extremes named: lowest and highest dots of the first and last year, and the famine in China
    def name(e, yr, dx, dy, a="start"):
        x, y = pos[(e, yr)]
        p.append(leader([(x, y), (x + dx, y + dy)], 0.8))
        p.append(halo(x + dx + (4 if a == "start" else -4), y + dy, f"{e} {num(le[e][yr])}", sm, "ink", a))
    lo50 = min(cs, key=lambda e: le[e][1950]); hi50 = max(cs, key=lambda e: le[e][1950])
    lo23 = min(cs, key=lambda e: le[e][2023]); hi23 = max(cs, key=lambda e: le[e][2023])
    name(lo50, 1950, 30, 14); name(hi50, 1950, 40, -22)
    name(lo23, 2023, -40, 18, "end"); name(hi23, 2023, -40, -26, "end")
    name("China", 1960, 34, 18)
    return svgdoc(w, h, p, "Beeswarm of life expectancy by country and decade, coloured by UN region"), meds


def region_key(w, sm=15):
    p = []; x = 0
    for reg in REGIONS:
        p.append(DOT(x + 5, 10, 5, FAMILY[reg], 1)); p.append(T(x + 15, 10, short(reg), sm, "secondary"))
        x += 15 + textw(short(reg), sm) + 22
    return svgdoc(w, 20, p, "UN regions")


def bubble(F, w, h, sm=15):
    """Each mapped country: life expectancy before the pandemic against its fall; area by population."""
    cs = F["mapped"]; le, reg, pop, dip = F["le"], F["region"], F["pop"], F["dip"]
    base = F["base"]
    ylo, yhi = math.floor(min(dip[e] for e in cs)), 2
    l, r, t, b = 30, w - 8, 30, h - 30
    X = lin(50, 86, l, r); Y = lin(ylo, yhi, b, t)
    pmax = max(pop[e] for e in cs); R = lambda e: 2 + 30 * math.sqrt(pop[e] / pmax)
    p = []
    for v in range(ylo, yhi + 1):
        p.append(L(l, Y(v), r, Y(v), "rule" if v == 0 else "grid", 1))
        p.append(T(l - 8, Y(v), signed(v, 0) if v else "0", sm, "muted", "end"))
    for v in range(50, 87, 5):
        p.append(T(X(v), b + 16, str(v), sm, "muted", "middle"))
    p.append(T(0, 6, f"fall in years, {base} to the pandemic low; bubble area: population", sm, "muted"))
    p.append(T(r, b + 36, f"life expectancy in {base}, years →".replace(" →", ""), sm, "muted", "end"))
    off = [e for e in cs if dip[e] > yhi]
    for e in sorted(cs, key=lambda e: -pop[e]):
        if e in off: continue
        x, y = X(le[e][base]), Y(dip[e])
        p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(R(e))}" fill="var(--v-{FAMILY[reg[e]]}-tint)" fill-opacity="0.75" '
                 f'stroke="var(--v-{FAMILY[reg[e]]})" stroke-width="1.2"/>')
    def lab(e, dx, dy, a="start"):
        x, y = X(le[e][base]), Y(dip[e])
        p.append(leader([(x, y), (x + dx, y + dy)], 0.8))
        p.append(halo(x + dx + (3 if a == "start" else -3), y + dy, f"{e} {signed(dip[e])}", sm, "ink", a))
    for e, dx, dy, a in (("China", -40, -34, "end"), ("India", -30, 40, "end"), ("United States", 6, 52, "end"),
                         ("Bolivia", -20, -14, "end"), ("Mexico", 26, 26, "start"), ("Peru", 30, -6, "start"),
                         ("Nigeria", 20, -34, "start")):
        lab(e, dx, dy, a)
    for e in off:
        p.append(T(r, Y(ylo) - 14, f"off the scale: {e} {signed(dip[e])}", 13, "muted", "end"))
    return svgdoc(w, h, p, "Bubble chart of the pandemic fall against life expectancy before it")


def spread_line(F, w, h, sm=15):
    """The width of the middle 80 % and of the middle half of countries, every year."""
    S, yrs = F["spread"], F["years"]
    l, r, t, b = 30, w - 120, 30, h - 28
    X = lin(yrs[0], yrs[-1], l, r); top = math.ceil(max(S[y][4] - S[y][0] for y in yrs) / 5) * 5
    Y = lin(0, top, b, t)
    p = []
    for v in range(0, top + 1, 10):
        p.append(L(l, Y(v), r, Y(v), "grid", 1)); p.append(T(l - 8, Y(v), str(v), sm, "muted", "end"))
    for yy in range(1950, 2021, 20):
        p.append(T(X(yy), b + 16, str(yy), sm, "muted", "middle"))
    p.append(T(0, 6, "spread between countries, years", sm, "muted"))
    for i0, i1, c, name in ((0, 4, "teal", "middle 80 %"), (1, 3, "indigo", "middle half")):
        pts = [(X(y), Y(S[y][i1] - S[y][i0])) for y in yrs]
        p.append(PL(pts, c, 2.8))
        p.append(DOT(*pts[-1], 4.6, c, 1.4)); p.append(DOT(*pts[0], 4.6, c, 1.4))
        p.append(T(pts[-1][0] + 10, pts[-1][1], f"{name} {num(S[yrs[-1]][i1] - S[yrs[-1]][i0])}", sm, "ink"))
        p.append(halo(pts[0][0] + 8, pts[0][1] - 14, num(S[yrs[0]][i1] - S[yrs[0]][i0]), sm, "secondary"))
    return svgdoc(w, h, p, "The spread of life expectancy between countries, by year")


def sheet(F):
    g = Grid(1920)
    base, low, last, start = F["base"], F["low"], F["last"], F["start"]
    S = F["spread"]
    B = [kicker(g, 32, "Life expectancy at birth, country by country", f"{start}–{last} · {len(F['mapped'])} countries on the map")]
    B.append(bx("head", g.x(0), 74, g.w(8), 116, escape(fits(sheet_title(F), 46, g.w(8), 2, "title")), "font-size:46px;line-height:56px"))
    d50 = S[start][2]; d23 = S[last][2]
    deck = (f"In {start} the median country could expect {num(d50)} years of life at birth; in {last}, {num(d23)}. The countries "
            f"that started lowest gained most, so the dots crowd upward. The pandemic dented almost every country at once: "
            f"{len(F['fell'])} of {F['n']} fell in {base + 1} or {low}, most of all in {short(min(F['reg_med_dip'], key=F['reg_med_dip'].get))}.")
    B.append(bx("deck", g.x(8), 80, g.w(4), 116, escape(fits(deck, 17, g.w(4), 5)), "font-size:17px;line-height:23px"))
    # left: beeswarm
    y = 214
    B.append(section(g, y, 48, 1, "Every country, every decade", "", 0, 8, 24, 17, 24, 36))
    B.append(box("fig", g.x(3) + 40, y + 16, g.w(5) - 40, 20, region_key(g.w(5) - 40)))
    bsvg, meds = beeswarm(F, g.w(8), 740)
    B.append(box("fig", g.x(0), y + 50, g.w(8), 740, bsvg))
    # right: the fall against the level, the spread
    B.append(section(g, y, 48, 2, f"Who fell furthest in {base + 1}–{str(low)[2:]}", "", 8, 4, 24, 17, 24, 36))
    B.append(box("fig", g.x(8), y + 62, g.w(4), 400, bubble(F, g.w(4), 400)))
    y2 = y + 62 + 400 + 34
    B.append(section(g, y2, 48, 3, "The spread has narrowed", "", 8, 4, 24, 17, 24, 36))
    B.append(box("fig", g.x(8), y2 + 60, g.w(4), 230, spread_line(F, g.w(4), 230)))
    fy = 1006
    B.append(bx("foot", g.x(0), fy, g.w(12), 60,
                f"<div><b>Data</b> {escape(SOURCE_FULL)}; CC BY 4.0. Outlines, UN regions and population (bubble area): "
                f"Natural Earth v5.1.2, public domain.</div>"
                f"<div><b>Method</b> {len(F['mapped'])} countries joined to the Natural Earth 1:110m map; percentiles over all "
                f"{F['n']} countries and territories; fall = the lower of {base + 1} and {low} minus {base}. "
                f"<b>Made</b> {ISO} · {AUTHOR} · Vellum example · {URL} · make_infographics.py · git {stamp()}</div>"))
    return f'<main class="sheet" style="width:1920px;height:1080px">{"".join(B)}</main>'


def alt_sheet(F):
    S, a, b = F["spread"], F["start"], F["last"]
    return (f"Beeswarm of {len(F['mapped'])} countries' life expectancy every decade from {a} to {b}: the median rose from "
            f"{num(S[a][2])} to {num(S[b][2])} years and the middle 80 % narrowed from {num(S[a][4] - S[a][0])} to "
            f"{num(S[b][4] - S[b][0])} years. A bubble chart shows the pandemic fall against life expectancy in {F['base']}.")


def build(name, w, h, title, desc, body, css):
    html_path = os.path.join(OUT, f"{name}.html")
    html = page(html_path, title, desc, THEME + body, css, w, __file__)
    for mode, frag in (("light", ""), ("dark", "#dark")):
        render(html_path, os.path.join(OUT, f"{name}{'' if mode == 'light' else '_dark'}.png"), w, h, 2, frag)
    return html


SUBTITLES = {
    "story": ("Portrait story, 1080 × 1920 px: five numbered sections, a line chart of the world and its regions, a "
              "choropleth map, a fall-and-recovery bar chart, a unit chart of 236 countries and eight small multiples", "portrait story"),
    "square": ("Social square, 1080 × 1080 px: the world line inside the spread of all countries, three stat tiles, "
               "a mini map and the deepest falls", "social square"),
    "sheet": ("Landscape data sheet, 1920 × 1080 px: a beeswarm of every mapped country by decade, a bubble chart of "
              "the pandemic fall and the narrowing spread", "landscape data sheet"),
}


def publish(F, name, w, h, title, alt, body, css):
    html = build(name, w, h, title, alt, body, css)
    n = len(words(html))
    print(f"{name}: {n} words")
    sub, form = SUBTITLES[name]
    record("infographic", name, dict(
        title=title, subtitle=sub, kind="infographic", form=form, medium="infographic", tool="HTML + SVG",
        data=f"{SOURCE_FULL}; CC BY 4.0. Natural Earth v5.1.2 (outlines, UN regions, population estimates), public domain",
        script=rel(__file__), alt=alt, words=n,
        note="One story, three formats: every number is computed from the data files by the script, nothing typed.",
        files={"light": f"media/infographic/{name}.png", "dark": f"media/infographic/{name}_dark.png",
               "html": f"media/infographic/{name}.html"}))


if __name__ == "__main__":
    import sys
    F = atlas()
    css = CSS + scale_css("fall", "ember", NB - 1, 0.14, 0.92, first=1)
    only = sys.argv[1:] or ["story", "square", "sheet"]
    if "story" in only: publish(F, "story", 1080, 1920, headline(F), alt_story(F), story(F), css)
    if "square" in only: publish(F, "square", 1080, 1080, square_title(F), alt_square(F), square(F), css)
    if "sheet" in only: publish(F, "sheet", 1920, 1080, sheet_title(F), alt_sheet(F), sheet(F), css)
