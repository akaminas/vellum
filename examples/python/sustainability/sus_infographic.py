"""sus_infographic.py: "The world's electricity in 2025", a portrait infographic, 1080 × 1920 px, drawn in matplotlib.

A stack of sections on the 12-column grid of the Vellum infographics (64 px margin, 24 px gutters) and their four text
sizes (96, 56, 24, 18 px), plus one hero size:
  1  kicker, hero number (the low-carbon share), headline
  2  three stat tiles on the card colour: low-carbon growth, the fall in fossil generation (terracotta: the point), solar
  3  two waffles of 100 units, 2000 and 2025, by source, with the labels between them
  4  the world map of the low-carbon share in 2024 with its gradient bar
  5  the ten largest producers, low-carbon share 2015 → 2025, and wind and solar in four economies as small multiples
  6  what it means, the source and the stamp
Every number comes from sus_electricity.py, which reads data/sustainability/owid-energy.csv.
Run: python examples/python/sustainability/sus_infographic.py
"""
from sus_electricity import *                     # the data, the groups, the numbers and the map helpers
from matplotlib.patches import FancyBboxPatch

NAME = "sus_world_electricity"
WPX, HPX, DPI = 1080, 1920, 200                   # 5.4 × 9.6 in at 200 dpi
M, GUT = 64, 24
COLW = (WPX - 2 * M - 11 * GUT) / 12
NUM, HEAD, BODY, FOOT, HERO = 96, 56, 24, 18, 168


def pt(px):
    return px * 72 / DPI


def cx(c): return M + c * (COLW + GUT)
def cw(span): return span * COLW + (span - 1) * GUT


# ---- numbers
SH00 = 100 * TWH[:, 0] / GEN[0]; SH25 = 100 * TWH[:, -1] / GEN[-1]


def units(shares):
    """100 units by the largest remainder, so the waffle adds up to exactly 100."""
    fl = np.floor(shares).astype(int); rest = 100 - fl.sum()
    for i in np.argsort(-(shares - fl))[:rest]: fl[i] += 1
    return fl


U00, U25 = units(SH00), units(SH25)
assert U00.sum() == 100 == U25.sum()
SOLAR_X = TWH[5, -1] / TWH[5, 15]
TEN = sorted([c for c in cs if gen24[c]], key=lambda c: -gen24[c])[:10]
DUMB = sorted([(c, E[c][2015]["low_carbon_share_elec"], E[c][LAST]["low_carbon_share_elec"]) for c in TEN], key=lambda t: -t[2])
assert all(not np.isnan(t[2]) for t in DUMB)
up10 = sum(1 for _, a, b in DUMB if b > a)
FOUR = ["China", "United States", "European Union (27)", "India"]
SW = {c: series(E, c, "solar_share_elec", np.arange(2010, LAST + 1)) + series(E, c, "wind_share_elec", np.arange(2010, LAST + 1))
      for c in FOUR}
CI = series(E, "World", "carbon_intensity_elec", np.array([2000, LAST]))

HEADLINE = "Clean power grew faster than demand, and fossil generation fell"
assert d_fossil < 0 < d_gen < d_low


class Px:
    """The sheet in pixels from the top-left corner."""

    def __init__(self, V):
        self.V = V
        self.fig = plt.figure(figsize=(WPX / DPI, HPX / DPI), dpi=DPI)

    def ax(self, x, y, w, h, **kw):
        return self.fig.add_axes([x / WPX, 1 - (y + h) / HPX, w / WPX, h / HPX], **kw)

    def text(self, x, y, s, px, **kw):
        kw.setdefault("color", self.V.ink); kw.setdefault("va", "top"); kw.setdefault("ha", "left")
        return self.fig.text(x / WPX, 1 - y / HPX, s, fontsize=pt(px), **kw)

    def box(self, x, y, w, h, color, r=12):
        a = self.ax(x, y, w, h); a.set_axis_off(); a.set_xlim(0, w); a.set_ylim(h, 0)
        a.add_patch(FancyBboxPatch((0, 0), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=color, edgecolor="none"))
        return a

    def rule(self, y):
        self.fig.add_artist(plt.Line2D([M / WPX, (WPX - M) / WPX], [1 - y / HPX] * 2, color=self.V.grid, lw=0.8))


def section(P, y, title, sub):
    """A section head: the title in bold body type, the subtitle in muted text under it. Returns the y below it."""
    P.text(M, y, title, 30, fontweight="bold")
    P.text(M, y + 40, sub, 21, color=P.V.muted)
    return y + 80


def width_px(P, s, px, **kw):
    """The rendered width of a text in pixels."""
    t = P.fig.text(0, 0, s, fontsize=pt(px), **kw); w = t.get_window_extent(P.fig.canvas.get_renderer()).width; t.remove()
    return w * WPX / (P.fig.get_size_inches()[0] * P.fig.dpi)


def draw(V):
    plt.rcParams["savefig.bbox"] = None; plt.rcParams["savefig.pad_inches"] = 0
    P = Px(V); fig = P.fig
    ink, muted, sec = V.ink, V.muted, V.secondary

    # ---- 1. kicker, hero, headline
    P.text(M, 50, f"THE WORLD'S ELECTRICITY IN {LAST}", 22, color=muted, fontweight="bold")
    hero = f"{LC[-1]:.1f}"
    P.text(M - 6, 70, hero, HERO, fontfamily=V.title_font, color=ink)
    hw = width_px(P, hero, HERO, fontfamily=V.title_font)
    P.text(M - 6 + hw + 6, 104, "%", NUM, fontfamily=V.title_font, color=ink)
    P.text(cx(6) + 30, 100, "of it came from low-carbon\nsources: wind, solar, hydro,\nnuclear and bioenergy",
           BODY, color=sec, linespacing=1.35)
    P.text(cx(6) + 30, 214, f"up from {LC[0]:.1f} % in 2000", BODY, color=muted)
    P.text(M, 266, "Clean power grew faster than\ndemand, and fossil generation fell", 50, fontfamily=V.title_font,
           linespacing=1.12)

    # ---- 2. three stat tiles
    y = 398; th = 128
    tiles = [(num(d_low, sign=True), f"TWh more from low-carbon\nsources than in {LAST - 1}", V.ink),
             (num(d_fossil, sign=True), f"TWh from fossil fuels, while\ndemand rose {num(d_gen)} TWh", V.tone(1)),
             (f"{SOLAR_X:.0f}×", f"solar since 2015; in {LAST}\nit passed wind", V.ink)]
    for k, (v, lab, col) in enumerate(tiles):
        P.box(cx(4 * k), y, cw(4), th, V.card)
        P.text(cx(4 * k) + 22, y + 14, v, HEAD, fontfamily=V.title_font, color=col)
        P.text(cx(4 * k) + 22, y + 78, lab, 19, color=muted, linespacing=1.25)

    # ---- 3. two waffles
    y = section(P, 560, "Where every 100 units came from", "each square is 1 % of world generation, by source")
    cell, gap = 21, 4; side = 10 * cell + 9 * gap
    xl, xr = M, WPX - M - side
    for x0, u, yr in ((xl, U00, 2000), (xr, U25, LAST)):
        a = P.ax(x0, y + 36, side, side); a.set_axis_off(); a.set_xlim(0, side); a.set_ylim(side, 0)
        cols = [V.tone(GROUPS[g][2]) for g in range(len(GROUPS)) for _ in range(u[g])]
        for i, col in enumerate(cols):                                # column by column from the top left, fossil first
            cxi, ryi = divmod(i, 10)
            a.add_patch(Rectangle((cxi * (cell + gap), ryi * (cell + gap)), cell, cell, facecolor=col, edgecolor="none"))
        P.text(x0, y - 2, str(yr), 28, fontfamily=V.title_font, color=ink)
        P.text(x0 + side, y + 4, f"{u[FOSSIL:].sum()} low-carbon", 19, color=sec, ha="right")
    # between the waffles: each source with its units in 2000 and in the last year
    mx, mr = xl + side + 40, xr - 40
    P.text(mx, y + 36, "source", 17, color=muted)
    P.text(mr, y + 36, f"2000 → {LAST}", 17, color=muted, ha="right")
    for g, (name, _, hue) in enumerate(GROUPS):
        yy = y + 70 + g * 31
        a = P.ax(mx, yy, 15, 15); a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
        a.add_patch(Rectangle((0, 0), 1, 1, facecolor=V.tone(hue), edgecolor="none"))
        P.text(mx + 25, yy - 4, name, 20, color=ink)
        P.text(mr, yy - 4, f"{U00[g]} → {U25[g]}", 20, color=ink, ha="right", fontweight="bold" if g >= 4 else "normal")
    P.text(mx, y + 70 + 6 * 31 + 6, f"wind and solar: {U00[4] + U00[5]} → {U25[4] + U25[5]}", 19, color=sec)

    # ---- 4. map
    y = section(P, 958, f"{over_half} of {len(SHARE)} countries got over half their power from low-carbon sources",
                f"low-carbon share of electricity by country, {MAPYEAR}")
    x0, x1, y0, y1 = map_box(); mw = WPX - 2 * M; mh = mw * (y1 - y0) / (x1 - x0)
    a = P.ax(M, y - 4, mw, mh)
    cax = P.ax(M + 0.60 * mw, y - 4 + mh - 24, 210, 11)
    panel_c(V, a, cax)
    for t in cax.get_xticklabels(): t.set_fontsize(pt(16))
    for t in cax.texts: t.set_fontsize(pt(16))
    ymap = y - 4 + mh

    # ---- 5. the ten largest producers, and wind and solar in four economies
    y = ymap + 22
    P.text(M, y, "The ten largest producers", 28, fontweight="bold")
    P.text(M, y + 36, f"low-carbon share, %, 2015 ○ and {LAST} ●", 19, color=muted)
    yb, hb = y + 84, 1796 - (y + 84) - 30
    a = P.ax(M + 128, yb, cw(6) - 128 - 52, hb)
    n = len(DUMB)
    for i, (c, s0, s1) in enumerate(DUMB):
        a.plot([s0, s1], [i, i], color=V.rule, lw=1.4, solid_capstyle="butt", zorder=1)
        a.scatter([s0], [i], s=22, facecolor=V.surface, edgecolor=V.muted, linewidth=1.0, zorder=2)
        a.scatter([s1], [i], s=30, color=V.tone(0) if s1 > s0 else V.tone(1), edgecolor=V.surface, linewidth=1.0, zorder=3)
        a.annotate(f"{s1:.0f}", (1, i), xycoords=("axes fraction", "data"), xytext=(12, 0), textcoords="offset points",
                   ha="right", va="center", fontsize=pt(17), color=ink, annotation_clip=False)
    a.axvline(LC[-1], color=V.tone("ochre"), lw=1.0, ls=V.dotted, zorder=0)
    a.annotate(f"world {LC[-1]:.0f}", (LC[-1], -0.6), xytext=(4, 2), textcoords="offset points", ha="left", va="bottom",
               fontsize=pt(16), color=muted, annotation_clip=False)
    a.set_yticks(range(n)); a.set_yticklabels([SHORT.get(c, c) for c, _, _ in DUMB], fontsize=pt(18), color=ink)
    a.set_ylim(n - 0.5, -0.6); a.set_xlim(0, 100); a.set_xticks([0, 50, 100]); a.tick_params(labelsize=pt(16), pad=2)
    a.grid(False); a.xaxis.grid(True); a.spines["bottom"].set_visible(False)

    xr0 = cx(6) + 20
    P.text(xr0, y, "Wind and solar", 28, fontweight="bold")
    P.text(xr0, y + 36, f"share of generation, 2010–{LAST}, %", 19, color=muted)
    gx4 = 28; mw4 = (WPX - M - xr0 - gx4) / 2; mh4 = (1796 - (y + 84) - 40 - 2 * 34) / 2
    for k, c in enumerate(FOUR):
        r, q = divmod(k, 2)
        a = P.ax(xr0 + q * (mw4 + gx4), y + 84 + 34 + r * (mh4 + 34 + 34), mw4, mh4)
        s = SW[c]; xs = np.arange(2010, LAST + 1); m = ~np.isnan(s)
        a.fill_between(xs[m], 0, s[m], color=V.tint("moss"), lw=0, zorder=1)
        a.plot(xs[m], s[m], color=V.tone("moss"), lw=1.6, zorder=2)
        a.scatter([xs[m][-1]], [s[m][-1]], s=18, color=V.tone("moss"), edgecolor=V.surface, linewidth=0.9, zorder=3, clip_on=False)
        a.set_xlim(2010, LAST); a.set_ylim(0, 35); a.set_yticks([0, 15, 30]); a.set_xticks([])
        a.tick_params(labelsize=pt(15), pad=2)
        if q: a.set_yticklabels([])
        a.spines["bottom"].set_color(V.rule)
        a.set_title(f"{SHORT.get(c, c)}  {s[m][0]:.0f} → {s[m][-1]:.0f}", loc="left", fontsize=pt(19), color=ink,
                    fontweight="normal", pad=5)

    # ---- 6. meaning and source
    P.rule(1808)
    P.text(M, 1822, f"Each kilowatt-hour now carries {CI[1]:.0f} g of CO₂, against {CI[0]:.0f} g in 2000.", 21, color=sec)
    P.text(M, 1858, f"Ember (2026) and Energy Institute (2025) via Our World in Data, CC BY 4.0, downloaded {DOWNLOADED} · "
           f"Natural Earth v5.1.2", 15, color=muted)
    P.text(M, 1882, f"{os.path.basename(__file__)} · git {stamp()} · Vellum", 15, color=muted)
    return fig


ALT = (f"Portrait infographic on the world's electricity in {LAST}. {LC[-1]:.1f} per cent came from low-carbon sources, up from "
       f"{LC[0]:.1f} in 2000; low-carbon generation grew {num(d_low)} TWh in {LAST} while fossil generation fell {num(-d_fossil)} TWh "
       f"and solar, up {SOLAR_X:.0f}-fold since 2015, passed wind. Two waffles compare 2000 and {LAST}; a map shows the low-carbon "
       f"share by country in {MAPYEAR}; the ten largest producers' shares and wind and solar in China, the US, the EU and India follow.")
META = dict(title=f"The world's electricity in {LAST}: {LC[-1]:.1f} % low-carbon, and fossil generation fell",
            subtitle="Portrait infographic, 1080 × 1920 px: hero number, stat tiles, two waffles, map, dumbbell ranking, small multiples",
            kind="composite", form="portrait infographic (1080 × 1920 px)", medium="infographic", tool="matplotlib",
            data=(f"Ember yearly electricity data (2026) and Energy Institute Statistical Review (2025), via Our World in Data "
                  f"(CC BY 4.0, downloaded {DOWNLOADED}); Natural Earth v5.1.2"),
            script=rel(__file__), alt=ALT)

if __name__ == "__main__":
    for mode in MODES:
        save(draw(vellum.use(mode)), "sustainability", NAME, mode, meta=META, dpi=DPI)
