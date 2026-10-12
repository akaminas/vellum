"""make_pitch.py: a ten-slide pitch deck for an illustrative proposal, "an open observatory of mortality data".

The evidence slides use data/owid-life-expectancy.csv (UN World Population Prospects 2024, processed by Our World in
Data, CC BY 4.0) through story_kit.facts(); the pipeline, the plan, the budget and the ask are invented and every slide
that shows them says "illustrative" in its footer. The arc is the one of "Vellum - pitch decks" (1330.01): title,
problem as one stat tile, what exists as a dumbbell chart, the approach as five boxes, evidence as one figure with one
highlighted series, evidence as small multiples, three stat tiles, the plan as a dot timeline, the ask, contact.

Writes docs/media/pitch/pitch.html (all slides, each a 1600 x 900 section), slide-01.png ... slide-10.png at 2x
(each slide rendered alone through its #fragment), thumb-01.png ... at 480 px, and pitch.pdf with one slide per page.
Type sizes are points on a 13.333 x 7.5 in slide, so 1 pt = 1600 / 960 px.
"""
import os, sys
from html import escape
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "infographic"))
from story_kit import (facts, num, spell, textw, fits, wrap, Marks, Chart, svg, svg_text, col, f, world_chart, dot_timeline,  # noqa: E402
                       page, box, render, record, rel, stamp, DOCS, SOURCE, SOURCE_FULL, DATE, AUTHOR, URL, REGIONS)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import render as tools_render                                                                                          # noqa: E402

OUT = os.path.join(DOCS, "media", "pitch")
SW, SH = 1600, 900
PT = SW / 960                                      # px per point on a 13.333 x 7.5 in slide
TITLE, BODY, LABEL, FOOT = 28 * PT, 20 * PT, 16 * PT, 10 * PT      # 1329.02 and 1330.02
STAT, ASK, COVER = 56 * PT, 72 * PT, 40 * PT
MX = 80                                            # 8 mm of 160 mm
CW = SW - 2 * MX                                   # content width
TOP, BOTTOM = 192, 760                             # the content band under the title
MK = Marks(PT, 2.2, LABEL)                         # figure marks scaled by 2.2, figure text at 16 pt
SHORT = "Open mortality observatory"

# ---- the invented part of the proposal, in one place
BUDGET = {"staff": 0.84, "infrastructure": 0.24, "data partnerships": 0.12}   # million euros over 24 months, illustrative
PLAN = [(0, "Data audit", True), (3, "Prototype pipeline", True), (6, "First open release", False),
        (12, "Monthly estimates for 40 countries", False), (18, "All 236 countries and territories", False),
        (24, "Handover to a host institution", False)]                         # month, milestone, done; illustrative
FIRST_RELEASE = 6                                   # the milestone to remember
STEPS = [("Collect", "weekly death counts from national registers"),
         ("Harmonise", "ages, dates and definitions across countries"),
         ("Estimate", "monthly life expectancy with its uncertainty"),
         ("Publish", "open data and code under CC\u00a0BY\u00a04.0"),
         ("Flag", "any fall below a country’s 2019 level")]                      # illustrative
OPEN_STEP = 3                                       # the step to remember: publishing in the open

CSS = f"""
@page {{ size: {SW}px {SH}px; margin: 0; }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
section.slide {{ position: relative; width: {SW}px; height: {SH}px; overflow: hidden; background: var(--v-surface); break-after: page; }}
@media screen {{
  body {{ background: var(--v-grid); }}
  section.slide {{ margin: 0 auto 32px; }}
  body:has(section:target) {{ background: var(--v-surface); }}
  body:has(section:target) section.slide {{ margin: 0; }}
  body:has(section:target) section.slide:not(:target) {{ display: none; }}
}}
.rule {{ background: var(--v-teal); }}
.title {{ font: {TITLE:.2f}px/56px var(--v-font-title); color: var(--v-ink); white-space: nowrap; }}
.cover {{ font: {COVER:.2f}px/80px var(--v-font-title); color: var(--v-ink); }}
.body {{ font-size: {BODY:.2f}px; line-height: 44px; color: var(--v-secondary); }}
.body.ink {{ color: var(--v-ink); }}
.label {{ font-size: {LABEL:.2f}px; line-height: 36px; color: var(--v-muted); }}
.source {{ font-size: {LABEL:.2f}px; line-height: 32px; color: var(--v-muted); }}
.foot {{ display: flex; justify-content: space-between; font-size: {FOOT:.2f}px; line-height: 24px; color: var(--v-muted); }}
.tile {{ background: var(--v-card); border-radius: 12px; padding: 40px; box-sizing: border-box; }}
.tile .v {{ font: {STAT:.2f}px/96px var(--v-font-title); color: var(--v-ink); }}
.tile .v.ask {{ font-size: {ASK:.2f}px; line-height: 120px; color: var(--v-terracotta); }}
.tile .l {{ font-size: {LABEL:.2f}px; line-height: 36px; color: var(--v-muted); margin-top: 16px; }}
.tile .c {{ font-size: {LABEL:.2f}px; line-height: 36px; color: var(--v-secondary); margin-top: 8px; }}
"""


def slide(n, title, body, foot, cover=False):
    """The frame of every slide: the teal heading rule, the claim as the title, the content, the footer."""
    head = "" if cover else box("title", MX, 88, CW, 56, escape(fits(title, TITLE, CW, 1, "title")))
    right = f"{SHORT} · {n} / 10 · git {stamp()}"
    return (f'<section class="slide" id="s{n}">' + box("rule", MX, 64, 64, 4, "") + head + "".join(body)
            + box("foot", MX, 848, CW, 24, f"<span>{escape(foot)}</span><span>{escape(right)}</span>") + "</section>")


def source_line(text, y=784):
    """The line under the figure that says where the number comes from (1330.05)."""
    return box("source", MX, y, CW, 32, escape(fits(text, LABEL, CW, 1)))


DATA_FOOT = f"Data: {SOURCE}, processed by Our World in Data, CC BY 4.0 · values to {{last}} · {DATE}"
ILLUS_FOOT = f"Illustrative: the proposal, plan and budget are invented for this Vellum example · {DATE}"


# ---- the slides

def s1(F):
    body = [box("cover", MX, 232, 1240, 240, escape(fits(
                "An open observatory of mortality data would show the next fall in life expectancy as it happens", COVER, 1240, 3, "title"))),
            box("body", MX, 520, CW, 44, f"A proposal for two years of funding, with the evidence of {F['n_years']} years of data"),
            box("label", MX, 600, CW, 36, f"Vellum example deck · illustrative proposal · {AUTHOR} · {DATE}")]
    return slide(1, "", body, ILLUS_FOOT, cover=True)


def s2(F):
    W, base, low = F["world"], F["base"], F["low"]
    tile = (f'<div class="v">{num(-F["drop"])} years</div>'
            f'<div class="l">world life expectancy at birth, {base} to {low}</div>'
            f'<div class="c">the deepest fall since {F["prior"][0] + 1}–{str(F["since"])[2:]}, which cost {num(F["prior_drop"])} years</div>')
    say = (f"It took the world back to about its {F['level']} level: {spell(low - F['level'])} years of gains, "
           f"lost in {spell(low - base)}.")
    body = [box("tile", MX, 296, 704, 304, tile),
            box("body ink", MX + 784, 336, CW - 784, 176, escape(fits(say, BODY, CW - 784, 4)))]
    body.append(source_line(f"Period life expectancy at birth, world, {base} and {low} · {SOURCE}"))
    return slide(2, f"World life expectancy fell {num(F['drop'])} years in {base + 1} and {low}", body, DATA_FOOT.format(**F))


def dumbbell(F, w, h):
    """Each region in the pandemic's first and last year: a rule-grey stem from the later to the earlier value, the
    earlier dot in rule grey, the later in the teal tone, the worst-hit region's in terracotta. The fall at the right."""
    base, low, R, s = F["base"], F["low"], F["regions"], MK.text
    rows = [("World", F["world"])] + [(r, R[r]) for r in sorted(REGIONS, key=lambda r: F["rfall"][r])]
    name_w = max(textw(r, s) for r, _ in rows) + 1.5 * s
    c = Chart(w, h, (60, 80), (0, 1), MK, (name_w, 0, w - 4.5 * s, h - 3.4 * s))
    first, last = 1.9 * s, c.b - 1.1 * s           # the world row first, set apart from the regions by 0.6 em
    step = (last - first - 0.6 * s) / (len(rows) - 1)
    ys = [first + k * step + (0.6 * s if k else 0) for k in range(len(rows))]
    c.spine()
    c.xaxis([60, 65, 70, 75, 80])
    c.p.append(svg_text((c.l + c.r) / 2, c.b + 2.6 * s, "life expectancy at birth, years", s, "muted", "middle"))
    c.text(w, 0.6 * s, f"{base} to {low}", "muted", "end", px=True)
    for k, ((name, v), y) in enumerate(zip(rows, ys)):
        hi = name == F["worst"]
        x0, x1 = c.X(v[base]), c.X(v[low])
        c.p.append(f'<line x1="{f(x1)}" y1="{f(y)}" x2="{f(x0)}" y2="{f(y)}" stroke="{col("rule")}" stroke-width="{f(MK.thin)}"/>')
        c.dot(x0, y, "rule", px=True); c.dot(x1, y, "terracotta" if hi else "teal", px=True)
        c.text(0, y, "World average" if name == "World" else name, px=True)
        c.text(w, y, num(v[low] - v[base]), anchor="end", px=True)
        if k == 0:                                  # the key, written on the first row
            c.text(x1, y - 1.1 * s, str(low), "muted", "middle", px=True); c.text(x0, y - 1.1 * s, str(base), "muted", "middle", px=True)
    return c


def s3(F):
    lo, hi = F["rfall"][F["mildest"]], F["rfall"][F["worst"]]
    title = f"The world average hides falls of {num(lo)} to {num(hi)} years across regions"
    c = dumbbell(F, CW, 568)
    body = [box("fig", MX, TOP, CW, 568, c.svg(title)),
            source_line(f"Period life expectancy at birth in the six UN regions, {F['base']} and {F['low']} · {SOURCE}")]
    return slide(3, title, body, DATA_FOOT.format(**F))


def diagram(w, h):
    """Five boxes in reading order, numbered in teal-toned circles, joined by secondary arrows with stealth heads.
    The step to remember sits in the terracotta tint with its text in the deep step."""
    gap, n = 56, len(STEPS)
    bw = (w - (n - 1) * gap) / n; s = LABEL; p = []
    by, bh = 40, h - 40
    for k, (verb, phrase) in enumerate(STEPS):
        x = k * (bw + gap); hi = k == OPEN_STEP
        p.append(f'<rect x="{f(x)}" y="{f(by)}" width="{f(bw)}" height="{f(bh)}" rx="12" fill="{col("terracotta-tint" if hi else "card")}"/>')
        p.append(f'<circle cx="{f(x + 32 + 22)}" cy="{f(by)}" r="22" fill="{col("teal")}" stroke="{col("surface")}" stroke-width="{f(MK.ring)}"/>')
        p.append(svg_text(x + 54, by, str(k + 1), s, "surface", "middle", extra=' style="font-variant-numeric: lining-nums"'))
        p.append(svg_text(x + 28, by + 80, verb, BODY, "terracotta-deep" if hi else "ink"))
        for j, line in enumerate(wrap(phrase, s, bw - 56)):
            p.append(svg_text(x + 28, by + 132 + j * 36, line, s, "terracotta-deep" if hi else "secondary"))
        if k < n - 1:                               # arrow to the next box, 1.6 pt, stealth head
            ax0, ax1, ay = x + bw + 12, x + bw + gap - 12, by + bh / 2
            p.append(f'<line x1="{f(ax0)}" y1="{f(ay)}" x2="{f(ax1 - 8)}" y2="{f(ay)}" stroke="{col("secondary")}" stroke-width="{f(1.6 * PT)}"/>')
            p.append(f'<path d="M{f(ax1)},{f(ay)} L{f(ax1 - 16)},{f(ay - 7)} L{f(ax1 - 11)},{f(ay)} L{f(ax1 - 16)},{f(ay + 7)} Z" fill="{col("secondary")}"/>')
    return svg(w, h, p, "Five steps: " + ", ".join(v for v, _ in STEPS))


def s4(F):
    body = [box("fig", MX, 248, CW, 360, diagram(CW, 360)),
            source_line("Illustrative: the pipeline is invented for this example deck; the steps are those of a mortality nowcast")]
    return slide(4, "Five steps would turn death registers into open monthly estimates", body, ILLUS_FOOT)


def s5(F):
    title = f"In {F['base'] + 1}–{str(F['low'])[2:]} world life expectancy had its deepest fall since {F['since']}"
    body = [box("fig", MX, TOP, CW, 568, world_chart(F, CW, 568, MK).svg(title)),
            source_line(f"Period life expectancy at birth, world, {F['start']}–{F['last']} · {SOURCE}")]
    return slide(5, title, body, DATA_FOOT.format(**F))


def multiples(F, w, h):
    """Six panels, one region each, on the same axes: change since the pre-pandemic year, the region in the teal tone
    (the worst hit in terracotta) over the other five in rule grey, the pre-pandemic level as a dotted reference."""
    base, last, R, s = F["base"], F["last"], F["regions"], MK.text
    yrs = list(range(base - 4, last + 1)); gx, gy = 64, 40
    pw, ph = (w - 2 * gx) / 3, (h - gy) / 2
    tick_w = textw(num(-4, 0), s) + 0.5 * s
    parts = []
    for k, r in enumerate(REGIONS):
        i, j = divmod(k, 3); x0, y0 = j * (pw + gx), i * (ph + gy)
        left = tick_w if j == 0 else 0
        c = Chart(pw, ph, (yrs[0], last), (-4, 2), MK, (left, 2.9 * s, pw - textw("+0.0", s) - MK.r - 0.6 * s, ph - (1.9 * s if i == 1 else 0.6 * s)))
        c.ygrid([-4, -2, 2], lambda t: num(t, 0, True), labels=j == 0)
        c.hline(0); c.spine()
        if i == 1: c.xaxis([yrs[0], base, last])
        c.text(0, 0.6 * s, r, px=True)
        if j == 0: c.unit(f"change since {base}, years")
        for o in REGIONS:                           # the other members, thin, in rule grey behind
            if o != r: c.line(yrs, [R[o][y] - R[o][base] for y in yrs], "rule", MK.thin)
        tone = "terracotta" if r == F["worst"] else "teal"
        d = [R[r][y] - R[r][base] for y in yrs]
        c.line(yrs, d, tone); c.dot(last, d[-1], tone)
        c.text(c.X(last) + MK.r + 0.4 * s, c.Y(d[-1]), num(d[-1], 1, True), px=True)
        if r == F["worst"]:                         # the trough of the one series that matters, labelled
            t = min(range(len(yrs)), key=lambda q: d[q])
            c.dot(yrs[t], d[t], tone); c.text(c.X(yrs[t]) - MK.r - 0.4 * s, c.Y(d[t]) - 0.4 * s, num(d[t]), anchor="end", px=True)
        parts.append(f'<g transform="translate({f(x0)},{f(y0)})">' + "".join(c.p) + "</g>")
    return svg(w, h, parts, "Small multiples of life expectancy change by region")


def s6(F):
    title = f"Every region was back above its {F['base']} level by {F['last']}"
    body = [box("fig", MX, TOP - 8, CW, 568, multiples(F, CW, 568)),
            source_line(f"Change from each UN region’s {F['base']} level (dotted) in life expectancy at birth · {SOURCE}")]
    return slide(6, title, body, DATA_FOOT.format(**F))


def s7(F):
    tiles = [(str(F["n"]), "countries and territories", f"{F['country_years']:,} country-years in all"),
             (str(F["n_years"]), "years of annual estimates", f"{F['start']} to {F['last']}, one value a year"),
             ("12", "open releases a year, one a month", "illustrative target")]
    body = [box("tile", MX + k * (CW + 48) / 3, 280, (CW - 96) / 3, 320,
                f'<div class="v">{v}</div><div class="l">{escape(fits(l, LABEL, (CW - 96) / 3 - 80, 2))}</div>'
                f'<div class="c">{escape(fits(c, LABEL, (CW - 96) / 3 - 80, 2))}</div>') for k, (v, l, c) in enumerate(tiles)]
    body.append(source_line(f"{F['n']} and {F['n_years']}: counted in the {SOURCE} series · 12: illustrative"))
    return slide(7, f"Every release would cover {F['n']} countries and territories since {F['start']}", body,
                 f"Data: {SOURCE} via Our World in Data, CC BY 4.0 · releases a year: illustrative · {DATE}")


def s8(F):
    s = MK.text
    xlim = (-2.2, 26.2); ppm = CW / (xlim[1] - xlim[0])            # px per month
    months = [m for m, _, _ in PLAN]
    room = [min(abs(m - o) for o in months if o != m) * ppm - 0.9 * s for m in months]   # space to the nearest neighbour
    ev = [dict(x=m, color="terracotta" if m == FIRST_RELEASE else "teal-deep" if done else "teal-tint",
               above=wrap(t, s, min(r, 240)), below=f"month {m}") for (m, t, done), r in zip(PLAN, room)]
    tl = dot_timeline(CW, 208, xlim, ev, MK, line="teal", lw=MK.thin)
    # key: done in the deep step, planned in the tint
    for k, (c, t) in enumerate((("teal-deep", "done"), ("teal-tint", "planned"))):
        x = k * 200
        tl.dot(x + MK.r, 0.6 * s, c, px=True); tl.text(x + 2 * MK.r + 0.4 * s, 0.6 * s, t, "muted", px=True)
    body = [box("fig", MX, 376, CW, 208, tl.svg("Plan: " + "; ".join(f"month {m}, {t}" for m, t, _ in PLAN))),
            source_line("Illustrative: milestones invented for this example deck; months counted from the start of funding")]
    return slide(8, f"The first open release would come {spell(FIRST_RELEASE)} months after funding", body, ILLUS_FOOT)


def s9(F):
    ask = sum(BUDGET.values())
    split = " · ".join(f"{k} €{v:.2f} million" for k, v in BUDGET.items())
    tile = (f'<div class="v ask">€{ask:.1f} million</div>'
            f'<div class="l">over 24 months, the whole ask</div><div class="c">{escape(split)}</div>')
    body = [box("tile", MX, 296, 960, 304, tile),
            source_line("Illustrative: the budget is invented for this example deck")]
    return slide(9, "Two years of funding would build and open the observatory", body, ILLUS_FOOT)


def s10(F):
    body = [box("body ink", MX, 248, CW, 44, AUTHOR),
            box("body", MX, 300, CW, 44, URL),
            box("label", MX, 408, 1240, 144, escape(fits(
                f"Data: {SOURCE_FULL}; CC BY 4.0. Every number on the evidence slides is computed by the script from that file.",
                LABEL, 1240, 4))),
            box("label", MX, 584, CW, 36, f"Drawn by {rel(__file__)} · git {stamp()} · {DATE} · Vellum example deck · illustrative proposal")]
    return slide(10, "Every number in this deck is computed from one open data file", body,
                 f"Data: {SOURCE}, processed by Our World in Data, CC BY 4.0 · {DATE}")


if __name__ == "__main__":
    F = facts()
    html_path = os.path.join(OUT, "pitch.html")
    slides = [s(F) for s in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10)]
    page(html_path, "An open observatory of mortality data", "Vellum example pitch deck, illustrative proposal, ten slides",
         "\n".join(slides), CSS, SW, __file__)
    pages, thumbs = [], []
    for n in range(1, 11):
        png = render(html_path, os.path.join(OUT, f"slide-{n:02d}.png"), SW, SH, 2, f"#s{n}")
        Image.open(png).convert("RGB").resize((480, 270), Image.LANCZOS).save(os.path.join(OUT, f"thumb-{n:02d}.png"))
        pages.append(f"media/pitch/slide-{n:02d}.png"); thumbs.append(f"media/pitch/thumb-{n:02d}.png")
    tools_render.pdf(html_path, os.path.join(OUT, "pitch.pdf"))
    print("wrote", OUT)
    record("pitch", "pitch", dict(
        title="An open observatory of mortality data would show the next fall in life expectancy as it happens",
        subtitle="Vellum example deck · illustrative proposal: ten slides in light mode, 1600 × 900 px",
        kind="slides", form="pitch deck, 10 slides", medium="pitch deck", tool="HTML + SVG",
        data=f"{SOURCE_FULL}; CC BY 4.0", script=rel(__file__),
        alt=(f"Ten-slide pitch deck. Evidence: world life expectancy fell {num(F['drop'])} years in {F['base'] + 1}–{str(F['low'])[2:]}, "
             f"the deepest fall since {F['since']}; regional falls ranged from {num(F['rfall'][F['mildest']])} to "
             f"{num(F['rfall'][F['worst']])} years; every region was back above its {F['base']} level by {F['last']}. "
             f"The ask, illustrative: €{sum(BUDGET.values()):.1f} million over two years."),
        note="Illustrative proposal: the pipeline, plan, budget and ask are invented; the evidence slides use real data.",
        files={"light": pages[0], "pages": pages, "thumbs": thumbs, "pdf": "media/pitch/pitch.pdf", "html": "media/pitch/pitch.html"}))
