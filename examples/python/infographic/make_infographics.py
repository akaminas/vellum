"""make_infographics.py: two social graphics on world life expectancy since 1950 and the pandemic setback.

From data/owid-life-expectancy.csv (UN World Population Prospects 2024, processed by Our World in Data, CC BY 4.0):
  square.html -> square.png   1080 x 1080, number, headline, three stat tiles, the world line chart, meaning, source
  story.html  -> story.png    1080 x 1920, a stack of cards: number and headline, the same line chart, a waffle of
                              the countries back at their pre-pandemic level, a dot timeline of milestones, meaning
both in docs/media/infographic/, rendered at 2x with tools/render.py, and recorded in docs/figures/infographic/.
Every number is computed in story_kit.facts() and printed by this script; the layout is the 12-column grid of
1332.10 (64 px margin, 24 px gutters, 8 px base unit) and the four text sizes of 1332.11 (96, 56, 24, 18 px).
"""
import os
from html import escape
from story_kit import (facts, num, spell, fits, Marks, svg, world_chart, waffle, dot_timeline, page, box, words, render,
                       record, rel, DOCS, SOURCE, SOURCE_FULL, AUTHOR, URL)

OUT = os.path.join(DOCS, "media", "infographic")
W = 1080
M, G = 64, 24                                     # outer margin and gutter (1332.10)
COLW = (W - 2 * M - 11 * G) / 12                  # twelve columns
NUM, HEAD, BODY, FOOT = 96, 56, 24, 18            # the four text sizes (1332.11)
ISO = "2026-10-12"                                # the date the sheets were made
MK = Marks(100 / 72, 2.2, BODY)                   # drawn as at dpi=100, marks scaled like a slide figure


def cx(c): return M + c * (COLW + G)
def cw(span): return span * COLW + (span - 1) * G


CSS = f"""
.sheet {{ position: relative; overflow: hidden; background: var(--v-surface); }}
.num {{ display: flex; align-items: baseline; font: {NUM}px/{NUM}px var(--v-font-title); color: var(--v-ink); white-space: nowrap; }}
.num .u {{ font-size: {HEAD}px; line-height: {HEAD}px; }}
.lab {{ font: {BODY}px/32px var(--v-font-body); color: var(--v-secondary); }}
.head {{ font: {HEAD}px/64px var(--v-font-title); color: var(--v-ink); }}
.lead {{ font-size: {BODY}px; line-height: 32px; color: var(--v-ink); }}
.tile {{ background: var(--v-card); border-radius: 12px; padding: 24px; box-sizing: border-box; }}
.tile .v, .share .v {{ font: {HEAD}px/56px var(--v-font-title); color: var(--v-ink); }}
.tile .v.hi {{ color: var(--v-terracotta); }}
.tile .l {{ font-size: {BODY}px; line-height: 32px; color: var(--v-muted); margin-top: 8px; }}
.share .l {{ font-size: {BODY}px; line-height: 32px; color: var(--v-secondary); margin-top: 8px; }}
.share .k {{ font-size: {BODY}px; line-height: 32px; color: var(--v-muted); margin-top: 24px; }}
.say {{ display: flex; align-items: flex-end; font-size: {BODY}px; line-height: 32px; color: var(--v-secondary); }}
.foot {{ display: flex; align-items: flex-end; font-size: {FOOT}px; line-height: 24px; color: var(--v-muted); }}
"""


def hero(F, y):
    """The number first (96 px), its unit at the headline size, and what it is, on one baseline."""
    pan = F["pan"]
    inner = (f'<span style="width:{cw(5) + G:.1f}px">{num(-F["drop"])}<span class="u"> years</span></span>'
             f'<span class="lab">world life expectancy, {pan[0]} to {pan[1]}</span>')
    return box("num", cx(0), y, cw(12), NUM, inner)


def headline(F):
    return fits(f"The pandemic brought world life expectancy its deepest fall since {F['since']}", HEAD, cw(12), 2, "title")


def footer(y, h=72):
    """Source with its year, the date, the author and the address, in muted 18 px (1332.15)."""
    return box("foot", cx(0), y, cw(6), h,
               f"<div>{SOURCE.replace(' (', ', ').rstrip(')')},<br>via Our World in Data · {ISO}<br>{AUTHOR} · Vellum example · {URL}</div>")


def square(F):
    Wd = F["world"]; base, low = F["base"], F["low"]
    tiles = [(num(Wd[F["start"]]), f"years in {F['start']}", ""),
             (num(Wd[base]), f"years in {base}", ""),
             (num(Wd[low]), f"years in {low}, the low", " hi")]                   # the point, in terracotta
    body = [hero(F, 64), box("head", cx(0), 176, cw(12), 128, escape(headline(F)))]
    for k, (v, l, hi) in enumerate(tiles):
        body.append(box("tile", cx(4 * k), 336, cw(4), 144, f'<div class="v{hi}">{v}</div><div class="l">{escape(fits(l, BODY, cw(4) - 48, 1))}</div>'))
    body.append(box("fig", cx(0), 512, cw(12), 400, world_chart(F, cw(12), 400, MK).svg(alt_square(F))))
    body.append(footer(944))
    say = fits(f"By {F['last']} the loss was made up, and more.", BODY, cw(6), 2)
    body.append(box("say", cx(6), 952, cw(6), 64, f"<div>{say}</div>"))
    return f'<main class="sheet" style="width:{W}px;height:1080px">' + "".join(body) + "</main>"


def lead(text, y):
    """The one sentence that opens a card: ink, body size, at most two lines of about 40 characters."""
    return box("lead", cx(0), y, cw(6), 64, escape(fits(text, BODY, cw(6), 2)))


def story(F):
    Wd = F["world"]; base, low, last, start = F["base"], F["low"], F["last"], F["start"]
    body = [hero(F, 64), box("head", cx(0), 176, cw(12), 128, escape(headline(F)))]
    # card 1: the master figure, the same as the square's
    body.append(lead(f"Life expectancy at birth rose from {num(Wd[start])} years in {start} to {num(Wd[base])} in {base}, "
                     f"then fell for two years.", 368))
    body.append(box("fig", cx(0), 448, cw(12), 400, world_chart(F, cw(12), 400, MK).svg(alt_story(F))))
    # card 2: a share the reader should count, as a waffle (1332.09), with its key in words
    body.append(lead(f"By {last} the loss had been made up across most of the world.", 912))
    parts, size = waffle(F["pct_back"], "teal", 34)
    body.append(box("fig", cx(0), 1000, size, size, svg(size, size, parts, f"{F['pct_back']} of 100 squares filled")))
    label = (f"of {F['n']} countries and territories had life expectancy at or above their {base} level in {last}; "
             f"{F['pct_fell']} % had fallen below it in {base + 1} or {low}")
    share = (f'<div class="v">{F["pct_back"]} %</div><div class="l">{fits(label, BODY, cw(6), 4)}</div>'
             f'<div class="k">1 square = 1 % of the {F["n"]}</div>')
    body.append(box("share", cx(6), 1000, cw(6), size, share))
    # card 3: milestones as a dot timeline (1332.12), the pandemic low in terracotta with its callout
    ev = [dict(x=F["first"][t], color="teal-deep", above=[f"{t} years"], below=str(F["first"][t])) for t in (50, 60, 70)]
    ev.append(dict(x=low, color="terracotta", above=[f"{num(Wd[low])} in {low}, about the level of {F['level']}"],
                   below=str(low), tier=2, anchor="end"))
    body.append(lead("The first years the world reached 50, 60 and 70 years, and the pandemic low", 1422))
    tl = dot_timeline(cw(12), 176, (start, last), ev, MK)
    body.append(box("fig", cx(0), 1502, cw(12), 176, tl.svg("Milestones of world life expectancy")))
    # the meaning, last, bottom right; the source bottom left
    decades = spell(round((base - start) / 10))
    say = f"The gains of {decades} decades held: by {last} the world had made up the loss and set a record of {num(Wd[last])} years."
    body.append(footer(1784))
    body.append(box("say", cx(6), 1760, cw(6), 96, f"<div>{fits(say, BODY, cw(6), 3)}</div>"))
    return f'<main class="sheet" style="width:{W}px;height:1920px">' + "".join(body) + "</main>"


def alt_square(F):
    Wd = F["world"]
    return (f"World life expectancy fell {num(F['drop'])} years in {F['base'] + 1}–{str(F['low'])[2:]}, from {num(Wd[F['base']])} "
            f"to {num(Wd[F['low']])} years, the deepest fall since {F['since']}; by {F['last']} it reached a record {num(Wd[F['last']])} years.")


def alt_story(F):
    return alt_square(F) + (f" {F['pct_back']} % of {F['n']} countries and territories were at or above their {F['base']} "
                            f"level in {F['last']}.")


if __name__ == "__main__":
    F = facts()
    data = f"{SOURCE_FULL}; CC BY 4.0"
    for name, h, make, alt in (("square", 1080, square, alt_square), ("story", 1920, story, alt_story)):
        html_path = os.path.join(OUT, f"{name}.html")
        html = page(html_path, headline(F), alt(F), make(F), CSS, W, __file__)
        png = render(html_path, os.path.join(OUT, f"{name}.png"), W, h, 2)
        n = len(words(html))
        print(f"{name}: {n} words -> {png}")
        record("infographic", name, dict(
            title=headline(F),
            subtitle=("Social square, 1080 × 1080 px: number, headline, three stat tiles, one figure" if name == "square" else
                      "Portrait story, 1080 × 1920 px: a stack of cards, line chart, waffle and dot timeline"),
            kind="infographic", form="social square" if name == "square" else "portrait story", medium="infographic",
            tool="HTML + SVG", data=data, script=rel(__file__), alt=alt(F), words=n,
            note="One master, several formats: the same numbers and line chart as the story and the A4 report, all computed from the data file.",
            files={"light": f"media/infographic/{name}.png", "html": f"media/infographic/{name}.html"}))
