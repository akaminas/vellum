"""sus_decoupling.py: economies that grew while their CO2 fell, 2005–2022, as a five-panel composite.

a  change in GDP against change in territorial CO2, 2005–2022, every country with both, on log-ratio axes; bubble area
   is population, colour the continent; the quadrant of absolute decoupling (GDP up, CO2 down) on the card colour
b  CO2 per person against GDP per person in 2022 (log–log), bubbles as in a, with lines of equal carbon intensity of GDP
   and arrows from 2005 for the eight largest emitters
c  GDP, territorial and consumption-based CO2 as an index (2005 = 100) for the six largest economies that decoupled and
   the two most populous countries, which did not
d  the trade gap: consumption-based minus territorial CO2, as a share of territorial, for the twenty largest economies
e  cumulative CO2 from fossil fuels and industry, 1850–2024, as a treemap nested by continent

Data: data/sustainability/owid-co2.csv (Global Carbon Budget 2025, Maddison Project 2023, UN WPP via Our World in Data,
CC BY 4.0); continents from data/ne_110m_admin_0_countries.geojson. Run: python examples/python/sustainability/sus_decoupling.py
"""
from _sus import *
from matplotlib.ticker import FixedLocator, NullLocator

NAME = "sus_decoupling"
C, ISO = owid("owid-co2.csv")
CONT = continent_of()
Y0, Y1 = 2005, 2022                       # 2022 is the last year of the Maddison GDP series
HUE = {"Asia": "teal", "Europe": "terracotta", "North America": "indigo", "Africa": "ochre", "South America": "mauve",
       "Oceania": "moss"}
cs = [c for c in C if is_country(ISO[c]) and ISO[c] in CONT]


def g(c, y, k):
    return C[c].get(y, {}).get(k)


# ---- a: every country with GDP and CO2 in both years
ROWS = []
for c in cs:
    v = [g(c, Y0, "gdp"), g(c, Y1, "gdp"), g(c, Y0, "co2"), g(c, Y1, "co2")]
    if None in v or 0 in v: continue
    k0, k1 = g(c, Y0, "consumption_co2"), g(c, Y1, "consumption_co2")
    ROWS.append(dict(c=c, cont=CONT[ISO[c]], gdp=v[1] / v[0], co2=v[3] / v[2], pop=g(c, Y1, "population"),
                     cons=(k1 / k0) if k0 and k1 else None))
N = len(ROWS)
DEC = [r for r in ROWS if r["gdp"] > 1 and r["co2"] < 1]
BOTH = [r for r in DEC if r["cons"] is not None and r["cons"] < 1]
N_CONS = sum(1 for r in ROWS if r["cons"] is not None)
POP_DEC = 100 * sum(r["pop"] for r in DEC) / sum(r["pop"] for r in ROWS)
assert (len(DEC), len(BOTH), N) == (45, 27, 164), (len(DEC), len(BOTH), N)   # the numbers of the title, as downloaded
ALL_DEC = {r["c"] for r in DEC}

# ---- b: per person in 2022, and the eight largest emitters' moves since 2005
PC = []
for c in cs:
    p, gd, co = g(c, Y1, "population"), g(c, Y1, "gdp"), g(c, Y1, "co2")
    if p and gd and co: PC.append(dict(c=c, cont=CONT[ISO[c]], x=gd / p, y=1e6 * co / p, pop=p))
MOVERS = sorted([c for c in cs if g(c, Y1, "co2")], key=lambda c: -g(c, Y1, "co2"))[:8]

# ---- c: index lines
SIX = [r["c"] for r in sorted(BOTH, key=lambda r: -g(r["c"], Y1, "gdp"))[:6]]
TWO = ["China", "India"]
YRS = np.arange(Y0, Y1 + 1)


def index(c, k):
    s = series(C, c, k, YRS); return 100 * s / s[0]


# ---- d: the trade gap in 2022 for the twenty largest economies
BIGGDP = sorted([c for c in cs if g(c, Y1, "gdp") and g(c, Y1, "trade_co2_share") is not None], key=lambda c: -g(c, Y1, "gdp"))[:20]
GAP = sorted([(c, g(c, Y1, "trade_co2_share")) for c in BIGGDP], key=lambda t: t[1])
for c, v in GAP:                                 # the column is (consumption − territorial) / territorial
    assert abs(100 * (g(c, Y1, "consumption_co2") - g(c, Y1, "co2")) / g(c, Y1, "co2") - v) < 0.2, c

# ---- e: cumulative CO2 to 2024
CUMY = 2024
WORLD_CUM = g("World", CUMY, "cumulative_co2")
CUM = {c: g(c, CUMY, "cumulative_co2") for c in cs if g(c, CUMY, "cumulative_co2")}
SHARE = {c: 100 * v / WORLD_CUM for c, v in CUM.items()}
BYCONT = {k: sum(SHARE[c] for c in SHARE if CONT[ISO[c]] == k) for k in HUE}
REST = 100 - sum(SHARE.values())                 # international aviation and shipping, and rounding of the regions

TITLE = (f"{len(DEC)} of {N} countries grew their economy while cutting CO₂ from {Y0} to {Y1}, "
         f"and {len(BOTH)} cut the emissions of what they consume too")
SUB = (f"CO₂ from fossil fuels and industry; GDP at 2011 prices; bubble area is population; "
       f"the {len(DEC)} are home to {POP_DEC:.0f} % of the people")
SHORT = {"United States": "US", "United Kingdom": "UK", "Saudi Arabia": "Saudi Ar.", "South Korea": "S. Korea",
         "Democratic Republic of Congo": "DR Congo"}


def pct_axis(ax, which, ticks):
    """A log-ratio axis labelled as a percentage change: 1 is 0 %, 2 is +100 %, 0.5 is −50 %."""
    lab = [("0" if t == 1 else num(100 * (t - 1), sign=True)) for t in ticks]
    axis = ax.xaxis if which == "x" else ax.yaxis
    axis.set_major_locator(FixedLocator(ticks)); axis.set_minor_locator(NullLocator()); axis.set_ticklabels(lab)


BUBBLE = 1.7e-7                                  # pt² per person: China, 1.4 billion, is a 240 pt² disc


def bubbles(V, ax, xs, ys, pops, hues, alpha=0.88):
    """Bubble area in proportion to population, largest first so the small ones sit on top, ringed in the surface."""
    order = np.argsort(pops)[::-1]
    ax.scatter(np.array(xs)[order], np.array(ys)[order], s=BUBBLE * np.array(pops)[order] + 4,
               color=[V.tone(HUE[h]) for h in np.array(hues)[order]], edgecolor=V.surface, linewidth=0.5, alpha=alpha, zorder=3)


def label(V, ax, x, y, text, dx, dy, ha="left", va="center", color=None):
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=V.sz["annotation"],
                color=color or V.ink, path_effects=halo(V), zorder=8,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.45, shrinkA=0, shrinkB=2) if abs(dx) + abs(dy) > 9 else None)


def panel_a(V, ax):
    ax.set_xscale("log"); ax.set_yscale("log")
    xl, yl = (0.5, 5.2), (0.38, 4.6)
    ax.fill_between([1, xl[1]], yl[0], 1, color=V.card, lw=0, zorder=0)
    ax.axhline(1, color=V.rule, lw=0.7, zorder=1); ax.axvline(1, color=V.rule, lw=0.7, zorder=1)
    ax.plot(xl, xl, color=V.rule, lw=0.7, ls=V.dotted, zorder=1)
    ax.annotate("CO₂ as fast as GDP", (0.56, 0.56), xytext=(3, -3), textcoords="offset points", rotation=37,
                rotation_mode="anchor", ha="left", va="top", fontsize=V.sz["unit_line"], color=V.muted)
    ax.text(4.9, 0.42, f"{len(DEC)} countries: GDP up, CO₂ down\n{len(BOTH)} of them cut consumption CO₂ too",
            ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.2, zorder=6)
    bubbles(V, ax, [r["gdp"] for r in ROWS], [r["co2"] for r in ROWS], [r["pop"] for r in ROWS], [r["cont"] for r in ROWS])
    at = {r["c"]: r for r in ROWS}
    for c, dx, dy, ha in (("China", 10, 6, "left"), ("India", -12, 8, "right"), ("United States", -14, 9, "right"),
                          ("United Kingdom", -10, -8, "right"), ("Germany", 11, -6, "left"), ("Nigeria", -10, 9, "right"),
                          ("Ethiopia", -6, 9, "right"), ("Ukraine", 8, -8, "left"), ("Romania", 9, -7, "left"),
                          ("Brazil", -11, 7, "right")):
        r = at[c]; label(V, ax, r["gdp"], r["co2"], SHORT.get(c, c), dx, dy, ha=ha)
    ax.set_xlim(*xl); ax.set_ylim(*yl)
    pct_axis(ax, "x", [0.5, 1, 2, 4]); pct_axis(ax, "y", [0.5, 1, 2, 4])
    ax.grid(False)
    ax.set_xlabel(f"change in GDP, {Y0}–{Y1}, %", fontsize=V.sz["unit_line"], labelpad=2)
    head(V, ax, "a", "Growth and emissions, every country", unit=f"change in territorial CO₂, {Y0}–{Y1}, %")


def panel_b(V, ax):
    ax.set_xscale("log"); ax.set_yscale("log")
    xl, yl = (600, 160000), (0.03, 60)
    # lines of equal carbon intensity of GDP: CO2 per person / GDP per person = kg per dollar
    for kg in (0.1, 0.3, 1.0):
        xs = np.array(xl); ax.plot(xs, kg * xs / 1000, color=V.grid, lw=0.7, zorder=1)
        xe = min(xl[1] / 1.05, yl[1] / 1.15 * 1000 / kg)
        ax.annotate(f"{kg:g} kg/$", (xe, kg * xe / 1000), xytext=(-2, 2), textcoords="offset points", ha="right", va="bottom",
                    rotation=33, rotation_mode="anchor", fontsize=V.sz["unit_line"] - 0.5, color=V.muted)
    bubbles(V, ax, [r["x"] for r in PC], [r["y"] for r in PC], [r["pop"] for r in PC], [r["cont"] for r in PC], alpha=0.85)
    for c in MOVERS:                                               # where the eight largest emitters came from
        x0 = g(c, Y0, "gdp") / g(c, Y0, "population"); y0 = 1e6 * g(c, Y0, "co2") / g(c, Y0, "population")
        x1 = g(c, Y1, "gdp") / g(c, Y1, "population"); y1 = 1e6 * g(c, Y1, "co2") / g(c, Y1, "population")
        ax.annotate("", (x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.18",
                    color=V.ink, lw=0.8, shrinkA=0, shrinkB=2), zorder=6)
        ax.scatter([x0], [y0], s=6, color=V.ink, lw=0, zorder=6)
    place = {"China": (12, -13, "left"), "United States": (8, 4, "left"), "India": (-10, 5, "right"), "Russia": (-6, 12, "right"),
             "Japan": (-4, 13, "right"), "Iran": (-12, 9, "right"), "Indonesia": (9, -9, "left"), "Germany": (9, -12, "left")}
    for c in MOVERS:
        p = next(r for r in PC if r["c"] == c); dx, dy, ha = place.get(c, (6, 0, "left"))
        label(V, ax, p["x"], p["y"], SHORT.get(c, c), dx, dy, ha=ha)
    ax.set_xlim(*xl); ax.set_ylim(*yl)
    ax.xaxis.set_major_locator(FixedLocator([1000, 3000, 10000, 30000, 100000])); ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels(["1k", "3k", "10k", "30k", "100k"])
    ax.yaxis.set_major_locator(FixedLocator([0.1, 1, 10])); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels(["0.1", "1", "10"])
    ax.grid(False)
    ax.set_xlabel(f"GDP per person, {Y1}, int. $ (log)", fontsize=V.sz["unit_line"], labelpad=2)
    V.note(ax, 640, 45, f"arrows: {Y0} → {Y1},\nthe eight largest emitters", va="top", linespacing=1.15)
    head(V, ax, "b", f"Emissions and income per person, {Y1}", unit="tonnes of CO₂ per person (log)")


def panel_c(V, axes):
    for k, (ax, c) in enumerate(zip(axes, SIX + TWO)):
        hue = HUE[CONT[ISO[c]]]
        gd, co, cn = index(c, "gdp"), index(c, "co2"), index(c, "consumption_co2")
        ax.set_yscale("log")
        ax.axhline(100, color=V.rule, lw=0.6, zorder=1)
        ax.plot(YRS, gd, color=V.secondary, lw=0.9, zorder=3)
        ax.plot(YRS, cn, color=V.tone(hue), lw=0.9, ls=(0, (2.2, 1.4)), zorder=3)
        ax.plot(YRS, co, color=V.tone(hue), lw=1.6, zorder=4)
        ly = 10 ** vellum.spread([np.log10(gd[-1]), np.log10(co[-1])], 0.11)          # the two end values, never on top of each other
        for s, t, yy in ((gd, "GDP", ly[0]), (co, "CO₂", ly[1])):
            ax.annotate(f"{s[-1]:.0f}", (YRS[-1], yy), xytext=(2, 0), textcoords="offset points", ha="left", va="center",
                        fontsize=V.sz["unit_line"] - 0.5, color=V.ink if t == "CO₂" else V.muted, annotation_clip=False)
        ax.set_xlim(Y0, Y1); ax.set_ylim(45, 380)
        ax.yaxis.set_major_locator(FixedLocator([50, 100, 200])); ax.yaxis.set_minor_locator(NullLocator())
        ax.set_yticklabels(["50", "100", "200"] if k == 0 else [])
        ax.set_xticks([Y0, Y1] if k == 0 else []); ax.tick_params(labelsize=V.sz["tick"] - 1, pad=2)
        ax.set_title(SHORT.get(c, c) if c not in ("United States", "United Kingdom") else c, loc="left",
                     fontsize=V.sz["annotation"], fontweight="normal", color=V.ink if c in SIX else V.muted, pad=2)
    # a key, in the first panel: what each line is
    ax = axes[0]
    ax.annotate("GDP", (2009, index(SIX[0], "gdp")[4]), xytext=(0, 5), textcoords="offset points", ha="center", va="bottom",
                fontsize=V.sz["unit_line"] - 0.5, color=V.muted)


def panel_e(V, ax):
    n = len(GAP)
    for i, (c, v) in enumerate(GAP):
        hue = HUE[CONT[ISO[c]]]
        ax.barh(i, v, height=0.68, color=V.tone(hue), lw=0, zorder=2)
        ax.annotate("0" if round(v) == 0 else f"{v:+.0f}".replace("-", MINUS), (v, i), xytext=(3 if v >= 0 else -3, 0), textcoords="offset points",
                    ha="left" if v >= 0 else "right", va="center", fontsize=V.sz["unit_line"] - 0.5, color=V.muted)
    ax.axvline(0, color=V.secondary, lw=0.6, zorder=3)
    ax.set_yticks(range(n)); ax.set_yticklabels([SHORT.get(c, c) for c, _ in GAP], fontsize=V.sz["unit_line"] - 0.5)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(-48, 76); ax.set_xticks([-25, 0, 25, 50]); ax.tick_params(axis="x", labelsize=V.sz["tick"] - 0.5, pad=2)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v, sign=v != 0) if v else "0"))
    ax.grid(False); ax.xaxis.grid(True); ax.spines["bottom"].set_visible(False)
    ax.set_xlabel("← net exporter · net importer →", fontsize=V.sz["unit_line"] - 0.5, labelpad=2)
    head(V, ax, "e", f"Trade gap, {Y1}", unit="consumption over territorial CO₂, %")


def panel_d(V, ax, W, H):
    """The treemap, laid out in inches (W × H) so its cells are as square as the algorithm makes them."""
    ax.set_axis_off()
    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    conts = sorted(HUE, key=lambda k: -BYCONT[k])
    blocks = squarify([BYCONT[k] for k in conts], 0, 0, W, H)
    for k, (x, y, w, h) in zip(conts, blocks):
        hue = HUE[k]
        members = sorted([c for c in SHARE if CONT[ISO[c]] == k], key=lambda c: -SHARE[c])
        small = BYCONT[k] < 5                                            # a small continent is one block, named, no countries
        big = [] if small else [c for c in members if SHARE[c] >= 0.35]
        vals = [SHARE[c] for c in big] + [sum(SHARE[c] for c in members if c not in big)]
        cells = squarify(vals, x, y, w, h)
        for j, (cx, cy, cw, ch) in enumerate(cells):
            other = j == len(big)
            ax.add_patch(Rectangle((cx, cy), cw, ch, facecolor=V.tint(hue) if (not other or small) else V.card,
                                   edgecolor=V.surface, lw=0.8))
            if small:
                nm = {"South America": "S. America"}.get(k, k)
                if cw > 0.30 and ch > 0.22:
                    ax.text(cx + 0.03, cy + 0.03, f"{nm}\n{BYCONT[k]:.1f} %", ha="left", va="top", fontsize=V.sz["unit_line"] - 0.5,
                            color=V.ink, linespacing=1.1, fontweight="bold")
                continue
            name = "other" if other else SHORT.get(big[j], big[j])
            val = vals[j]
            # a label when the cell is wide and tall enough, in ink; the value under the name in the large cells
            fw, fh = cw, ch                                                    # cell size in inches
            if fw > 0.40 and fh > 0.15:
                txt = f"{name}\n{val:.1f} %" if fh > 0.28 else f"{name} {val:.1f}"
                ax.text(cx + 0.03, cy + 0.03, txt, ha="left", va="top", fontsize=V.sz["unit_line"] - (0 if val > 3 else 0.5),
                        color=V.ink if not other else V.muted, linespacing=1.1, clip_on=True)
        ax.add_patch(Rectangle((x, y), w, h, facecolor="none", edgecolor=V.surface, lw=2.2, zorder=4))
    for k, (x, y, w, h) in zip(conts, blocks):                         # continent totals, bottom right of each block
        if BYCONT[k] >= 5:
            top_right = k == "North America"                             # its bottom right holds Canada and Mexico
            ax.text(x + w - 0.04, (y + 0.05) if top_right else (y + h - 0.04), f"{k} {BYCONT[k]:.0f} %", ha="right",
                    va="top" if top_right else "bottom", fontsize=V.sz["annotation"],
                    fontweight="bold", color=V.deep(HUE[k]) if V.mode == "light" else V.ink, zorder=6)
    head(V, ax, "d", f"Cumulative CO₂, 1850–{CUMY}", unit="share of the world's fossil and industry CO₂, by continent and country")


def key(V, S, x, y):
    """The continent colours, once for the figure, as ringed dots with names in ink."""
    for k in HUE:
        ax = S.at(x, y - 0.05, 0.1, 0.1); ax.set_axis_off(); ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
        ax.scatter([0], [0], s=30, color=V.tone(HUE[k]), edgecolor=V.surface, linewidth=0.8)
        t = S.text(x + 0.12, y, k, fontsize=V.sz["annotation"], color=V.ink, va="center", ha="left")
        S.fig.canvas.draw(); x += 0.12 + t.get_window_extent().width / S.fig.dpi + 0.20


def draw(V):
    plt.rcParams["lines.linewidth"] = 1.2
    W, H = 7.2, 8.0
    S = Sheet(V, W, H); fig = S.fig
    y = S.header(TITLE, SUB)
    key(V, S, 0.20, y + 0.12)
    top = y + 0.66
    hs = 1.95
    a = S.at(0.40, top, 3.0, hs); b = S.at(4.10, top, 2.95, hs)
    panel_a(V, a); panel_b(V, b)
    # row 2: the eight index panels of c
    top2 = top + hs + 0.86
    mw, gx = 0.655, 0.204
    axes = [S.at(0.40 + k * (mw + gx), top2, mw, 0.66) for k in range(8)]
    panel_c(V, axes)
    head(V, axes[0], "c", f"Decoupled, and not: six large economies against China and India",
         unit=f"index, {Y0} = 100 (log) · grey: GDP · solid: territorial CO₂ · dashed: consumption-based CO₂", gap=14)
    # row 3: d, the treemap, and e, the trade gap
    top3 = top2 + 0.66 + 0.66
    hd = H - top3 - 0.66
    d = S.at(0.40, top3, 4.55, hd); panel_d(V, d, 4.55, hd)
    e = S.at(5.72, top3, 1.33, hd); panel_e(V, e)
    S.footer(footer(f"{SRC_CO2} · continents from {SRC_NE}", __file__))
    return fig


ALT = (f"Five panels on decoupling. a: change in GDP against change in territorial CO2, {Y0}–{Y1}, for {N} countries; "
       f"{len(DEC)} grew while cutting CO2, {len(BOTH)} of which also cut consumption-based CO2. b: CO2 per person against GDP "
       f"per person in {Y1}, with arrows from {Y0} for the eight largest emitters. c: index lines for {', '.join(SIX)}, China and "
       f"India. d: consumption-based minus territorial CO2 for the twenty largest economies. e: treemap of cumulative CO2 since "
       f"1850; the United States {SHARE['United States']:.1f} per cent, China {SHARE['China']:.1f}.")
META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="five-panel composite: log-ratio bubble scatter, log-log bubble scatter with arrows, small multiples, diverging bars, nested treemap",
            medium="paper", tool="matplotlib",
            data=(f"Global Carbon Budget (2025), Maddison Project Database (2023) and UN WPP, via Our World in Data "
                  f"(CC BY 4.0, downloaded {DOWNLOADED}), {Y0}–{Y1} and 1850–{CUMY}; Natural Earth v5.1.2"),
            script=rel(__file__), alt=ALT)

if __name__ == "__main__":
    print(TITLE); print(SUB); print("six:", SIX, "movers:", MOVERS, "rest", round(REST, 1))
    for mode in MODES:
        save(draw(vellum.use(mode)), "sustainability", NAME, mode, meta=META)
