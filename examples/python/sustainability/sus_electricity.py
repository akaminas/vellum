"""sus_electricity.py: the energy transition in the world's electricity, 2000–2025, as a five-panel composite.

a  world electricity generation by source, stacked, 2000–2025, in six groups (coal, oil and gas, nuclear, hydro with
   bioenergy and other renewables, wind, solar); the line between fossil and low-carbon in ink
b  the change in generation from the year before, by source, 2011–2025, with the net change as a short ink bar
c  a world choropleth of the low-carbon share in 2024, on the shore gradient (cut at 15 % so zero stays visible)
d  the speed of change: the least-squares slope of the low-carbon share over 2015–2024, in percentage points per decade,
   for the twenty largest producers, each dot coloured by its 2024 share on the scale of c
e  the low-carbon share in the eight largest producers (the EU-27 as one), split by source with the colours of a,
   against the world share (dotted)

Data: data/sustainability/owid-energy.csv (Ember and the Energy Institute via Our World in Data, CC BY 4.0) and
data/ne_110m_admin_0_countries.geojson (Natural Earth). Run: python examples/python/sustainability/sus_electricity.py
"""
from _sus import *
from matplotlib.colors import LinearSegmentedColormap

NAME = "sus_electricity"
E, ISO = owid("owid-energy.csv")
YEARS = np.arange(2000, 2026)                  # from 2000 every source column is filled (bioenergy is missing before)
LAST = int(YEARS[-1])

# six groups, fossil first (warm hues) then low-carbon (cool hues, ochre for the sun); the stack runs in this order
GROUPS = [("coal", ["coal_electricity"], "terracotta"),
          ("oil and gas", ["gas_electricity", "oil_electricity"], "mauve"),
          ("nuclear", ["nuclear_electricity"], "indigo"),
          ("hydro and bio", ["hydro_electricity", "biofuel_electricity", "other_renewable_exc_biofuel_electricity"], "teal"),
          ("wind", ["wind_electricity"], "moss"),
          ("solar", ["solar_electricity"], "ochre")]
FOSSIL = 2                                     # the first two groups are fossil


def by_group(country, years):
    """TWh by group (rows) and year (columns); a missing component counts as zero once the total is known."""
    out = np.zeros((len(GROUPS), len(years)))
    for g, (_, cols, _) in enumerate(GROUPS):
        for c in cols:
            out[g] += np.nan_to_num(series(E, country, c, years))
    return out


# ---- a: the world
TWH = by_group("World", YEARS)
GEN = series(E, "World", "electricity_generation", YEARS)
assert np.allclose(TWH.sum(0), GEN, rtol=2e-3), "the six groups must add up to world generation"
LC = 100 * TWH[FOSSIL:].sum(0) / GEN
assert np.allclose(LC, series(E, "World", "low_carbon_share_elec", YEARS), atol=0.05), "our share must match OWID's"
LOW = int(np.argmin(LC))
d_fossil = TWH[:FOSSIL, -1].sum() - TWH[:FOSSIL, -2].sum()
d_low = TWH[FOSSIL:, -1].sum() - TWH[FOSSIL:, -2].sum()
d_gen = GEN[-1] - GEN[-2]
assert d_fossil < 0 < d_gen < d_low, "the claim: low-carbon growth exceeded the growth of demand, fossil generation fell"
assert TWH[5, -1] > TWH[4, -1] and (TWH[5, :-1] < TWH[4, :-1]).all(), "solar passed wind first in the last year"

# ---- b: change from the year before
BY = np.arange(2011, LAST + 1)
DT = np.diff(by_group("World", np.arange(2010, LAST + 1)), axis=1)
DNET = DT.sum(0)

# ---- c: the low-carbon share in 2024, the last year with near-complete coverage (2025 covers fewer than half the countries)
cs = [c for c in E if is_country(ISO[c])]
MAPYEAR = 2024
SHARE = {ISO[c]: E[c][MAPYEAR]["low_carbon_share_elec"] for c in cs if E[c].get(MAPYEAR, {}).get("low_carbon_share_elec") is not None}
G = geo()
over_half = sum(1 for v in SHARE.values() if v >= 50)

# ---- d: the speed of change, 2015–2024, for the twenty largest producers in 2024
gen24 = {c: E[c].get(2024, {}).get("electricity_generation") for c in cs}
SPAN = np.arange(2015, 2025)
TOP = sorted([c for c in cs if gen24[c]], key=lambda c: -gen24[c])[:20]


def slope(c):
    s = series(E, c, "low_carbon_share_elec", SPAN); m = ~np.isnan(s)
    assert m.sum() == len(SPAN), c
    return 10 * np.polyfit(SPAN[m], s[m], 1)[0]


SPEED = sorted([(c, slope(c), E[c][2024]["low_carbon_share_elec"]) for c in TOP], key=lambda t: -t[1])
W_SPEED = slope("World")
faster = sum(1 for _, v, _ in SPEED if v > W_SPEED)

# ---- e: the eight largest producers in 2024, with the EU-27 as one
EU = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany",
      "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
      "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"]
pool = {c: v for c, v in gen24.items() if v and c not in EU}
pool["European Union (27)"] = E["European Union (27)"][2024]["electricity_generation"]
BIG = sorted(pool, key=lambda c: -pool[c])[:8]
MINI = {}
for c in BIG:
    t = by_group(c, YEARS); g = series(E, c, "electricity_generation", YEARS)
    MINI[c] = dict(share=100 * t[FOSSIL:] / g, last=LAST if not np.isnan(g[-1]) else LAST - 1)
SHORT = {"European Union (27)": "EU-27", "United States": "United States", "United Arab Emirates": "UAE"}

TITLE = (f"Low-carbon sources made {LC[-1]:.1f} % of the world's electricity in {LAST}, up from {LC[0]:.1f} % in 2000, "
         f"and outgrew demand, so fossil generation fell")
SUB = (f"In {LAST} world generation rose by {num(d_gen)} TWh: low-carbon sources added {num(d_low)} TWh, fossil fuels "
       f"{num(d_fossil, sign=True)} TWh, and solar passed wind")


def shore(V):
    """The shore gradient from 15 % of its length, so a country or a dot at zero stays visible on the surface."""
    return LinearSegmentedColormap.from_list("shore_cut", V.gradient("shore", 256)[38:], N=256)


def ink_on(V, hue):
    """Labels of the stack take the deep step (light) or the tone (dark) of their layer, as in population_stacked."""
    return V.deep(hue) if V.mode == "light" else V.tone(hue)


def panel_a(V, ax):
    top = np.cumsum(TWH, axis=0) / 1000; base = np.vstack([np.zeros(len(YEARS)), top[:-1]])
    for g, (name, _, hue) in enumerate(GROUPS):
        ax.fill_between(YEARS, base[g], top[g], color=V.tint(hue), lw=0, zorder=2)
        ax.plot(YEARS, top[g], color=V.surface, lw=0.9, zorder=3)
    line = top[FOSSIL - 1]
    ax.plot(YEARS, line, color=V.ink, lw=1.1, zorder=4)              # the fossil / low-carbon boundary the claim is about
    ax.annotate("low-carbon ↑", (2001.6, line[1]), xytext=(0, 4), textcoords="offset points", ha="left", va="bottom",
                fontsize=V.sz["unit_line"], color=V.ink, zorder=5, rotation=9, rotation_mode="anchor")
    ax.annotate("fossil ↓", (2001.6, line[1]), xytext=(0, -4), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["unit_line"], color=V.ink, zorder=5, rotation=9, rotation_mode="anchor")
    # layer labels at the right edge: name and share in the last year, spread so the thin layers stay legible
    mids = [(base[g, -1] + top[g, -1]) / 2 for g in range(len(GROUPS))]
    ys = vellum.spread(mids, 2.2)
    for g, (name, _, hue) in enumerate(GROUPS):
        ax.annotate(f"{name}  {100 * TWH[g, -1] / GEN[-1]:.1f} %", (LAST, mids[g]), xytext=(LAST + 1.1, ys[g]), textcoords="data",
                    ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.rule, lw=0.5, shrinkA=1, shrinkB=0, relpos=(0, 0.5)))
    # the low-carbon share at three dates, in the empty sky above the stack
    ax.text(2000.6, 29.2, f"low-carbon share of the total: {LC[0]:.1f} % in 2000,\n"
            f"a low of {LC[LOW]:.1f} % in {2000 + LOW}, {LC[-1]:.1f} % in {LAST}", ha="left", va="top",
            fontsize=V.sz["annotation"], color=V.ink, linespacing=1.25, zorder=6)
    for i in (0, LOW, len(YEARS) - 1):
        ax.scatter(YEARS[i], line[i], s=14, color=V.ink, edgecolor=V.surface, linewidth=0.9, zorder=6, clip_on=False)
    ax.set_xlim(2000, LAST); ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2025])
    ax.set_ylim(0, 34); ax.set_yticks([0, 10, 20, 30])
    head(V, ax, "a", f"World electricity by source, 2000–{LAST}", unit="thousand terawatt-hours a year")


def panel_b(V, ax):
    pos = np.zeros(len(BY)); neg = np.zeros(len(BY))
    for g, (name, _, hue) in enumerate(GROUPS):
        d = DT[g]; up = np.where(d > 0, d, 0); dn = np.where(d < 0, d, 0)
        for h, b0 in ((up, pos), (dn, neg)):
            ax.bar(BY, h, bottom=b0, width=0.74, color=V.tint(hue), edgecolor=V.surface, lw=0.35, zorder=2)
        pos += up; neg += dn
    ax.axhline(0, color=V.secondary, lw=0.6, zorder=3)
    ax.scatter(BY, DNET, marker="_", s=34, color=V.ink, linewidths=1.5, zorder=5)    # the net change in total generation
    fy = DT[:FOSSIL, -1].sum()
    ax.annotate(f"{LAST}: fossil {num(fy, sign=True)},\nlow-carbon {num(DT[FOSSIL:, -1].sum(), sign=True)}",
                (LAST, neg[-1] - 12), xytext=(LAST + 0.5, -330), textcoords="data",
                ha="right", va="top", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.2,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=1, relpos=(0.93, 1)))
    i18 = 2018 - 2011
    ax.annotate("net change", (2018 - 0.3, DNET[i18]), xytext=(-2, 0), textcoords="offset points", ha="right", va="center",
                fontsize=V.sz["annotation"], color=V.ink)
    ax.annotate("pandemic", (2020 - 0.42, neg[2020 - 2011] + 60), xytext=(-2, 0), textcoords="offset points", ha="right",
                va="center", fontsize=V.sz["annotation"], color=V.muted)
    ax.set_xlim(2010.4, LAST + 0.6); ax.set_xticks([2011, 2015, 2020, 2025])
    ax.set_ylim(-640, 1360); ax.set_yticks([-400, 0, 400, 800, 1200])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v)))
    head(V, ax, "b", "Change from the year before", unit="terawatt-hours · colours as in a")


def panel_c(V, ax, cax):
    ax.set_axis_off()
    x0, x1, y0, y1 = map_box()
    cm = shore(V)
    with plt.rc_context({"hatch.linewidth": 0.4, "hatch.color": V.rule}):
        for code, f in G.items():
            if f["continent"] == "Antarctica": continue
            v = SHARE.get(code)
            fill = dict(facecolor=V.card, hatch="//////") if v is None else dict(facecolor=cm(v / 100))
            ax.add_patch(PathPatch(country_path(f["geom"]), lw=0.3, edgecolor=V.surface, **fill))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    # the legend: the gradient as a thin bar with five ticks and its unit
    cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=cm, extent=(0, 100, 0, 1))
    cax.set_yticks([]); cax.set_xticks([0, 25, 50, 75, 100]); cax.tick_params(labelsize=V.sz["unit_line"], pad=2)
    for s_ in cax.spines.values(): s_.set_visible(False)
    cax.grid(False)
    cax.annotate(f"per cent, {MAPYEAR}", (0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points",
                 ha="left", va="bottom", fontsize=V.sz["unit_line"], color=V.muted)
    cax.annotate("hatched: no data", (0, 0.5), xycoords="axes fraction", xytext=(-10, 0), textcoords="offset points",
                 ha="right", va="center", fontsize=V.sz["unit_line"], color=V.muted, annotation_clip=False, linespacing=1.1)


def panel_d(V, ax):
    cm = shore(V)
    n = len(SPEED)
    for i, (c, v, s) in enumerate(SPEED):
        ax.plot([0, v], [i, i], color=V.grid, lw=1.0, zorder=1, solid_capstyle="butt")
        ax.scatter([v], [i], s=22, color=cm(s / 100), edgecolor=V.surface, linewidth=0.9, zorder=3)
        lab = "0.0" if abs(v) < 0.05 else f"{v:.1f}".replace("-", MINUS)
        ax.annotate(lab, (1, i), xycoords=("axes fraction", "data"), xytext=(22, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=V.sz["unit_line"] - 0.5, color=V.ink if v > W_SPEED else V.muted, annotation_clip=False)
    ax.axvline(W_SPEED, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=0)
    ax.annotate(f"world {W_SPEED:.1f}", (W_SPEED, n - 0.2), xytext=(3, 0), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["unit_line"] - 0.5, color=V.muted, annotation_clip=False)
    ax.axvline(0, color=V.rule, lw=0.6, zorder=0)
    ax.set_yticks(range(n)); ax.set_yticklabels([SHORT.get(c, c) for c, _, _ in SPEED], fontsize=V.sz["unit_line"] - 0.5)
    for lab, (c, v, s) in zip(ax.get_yticklabels(), SPEED):
        lab.set_color(V.ink if v > W_SPEED else V.muted)
    ax.set_ylim(n + 0.5, -0.6)
    ax.set_xlim(-2, 28); ax.set_xticks([0, 10, 20]); ax.tick_params(axis="x", labelsize=V.sz["tick"] - 0.5, pad=2)
    ax.tick_params(axis="y", pad=3)
    ax.grid(False); ax.spines["bottom"].set_visible(False)
    head(V, ax, "d", "Speed of change, 2015–24", unit="points a decade · colour as in c")


def panel_e(V, axes):
    lw = series(E, "World", "low_carbon_share_elec", YEARS)
    for k, (ax, c) in enumerate(zip(axes, BIG)):
        m = MINI[c]; sh = m["share"]; last = m["last"]; n = last - 2000 + 1
        base = np.zeros(n)
        for j in range(len(GROUPS) - FOSSIL):
            ax.fill_between(YEARS[:n], base, base + sh[j, :n], color=V.tint(GROUPS[FOSSIL + j][2]), lw=0, zorder=2)
            base = base + sh[j, :n]
            if j < len(GROUPS) - FOSSIL - 1: ax.plot(YEARS[:n], base, color=V.surface, lw=0.5, zorder=3)
        ax.plot(YEARS[:n], base, color=V.ink, lw=1.0, zorder=4)
        ax.plot(YEARS, lw, color=V.secondary, lw=0.8, ls=(0, (0.6, 1.5)), zorder=5, dash_capstyle="round")
        V.dot(ax, last, base[-1], V.ink, s=11, z=6, ring=0.8)
        ax.annotate(f"{base[-1]:.0f}", (last, base[-1]), xytext=(-1, 4), textcoords="offset points", ha="right", va="bottom",
                    fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False, path_effects=halo(V), zorder=7)
        ax.set_xlim(2000, LAST); ax.set_ylim(0, 100); ax.set_yticks([0, 50, 100])
        ax.set_xticks([2000, 2025] if k == 0 else [])
        ax.tick_params(labelsize=V.sz["tick"] - 1, pad=2)
        if k: ax.set_yticklabels([])
        ax.spines["bottom"].set_color(V.rule)
        ax.set_title(SHORT.get(c, c), loc="left", fontsize=V.sz["annotation"], fontweight="normal", color=V.ink, pad=3)


def draw(V):
    plt.rcParams["lines.linewidth"] = 1.2
    W, H = 7.2, 8.0
    S = Sheet(V, W, H); fig = S.fig
    top = S.header(TITLE, SUB) + 0.50
    # row 1: a (with its layer labels to the right) and b
    ha = 1.80
    a = S.at(0.36, top, 2.86, ha); b = S.at(4.78, top, 2.30, ha)
    panel_a(V, a); panel_b(V, b)
    # row 2: c, the map, and d, the speed of change
    top2 = top + ha + 0.66
    x0, x1, y0, y1 = map_box(); mw = 4.72; mh = mw * (y1 - y0) / (x1 - x0)
    c = S.at(0.06, top2 + 0.14, mw, mh)                      # top level with d, so the two heads share a line
    cax = S.at(2.92, top2 + 0.14 + mh - 0.20, 0.86, 0.055)       # in the Southern Ocean, between Africa and Australia
    panel_c(V, c, cax)
    head(V, c, "c", f"Low-carbon share by country, {MAPYEAR}: {over_half} of {len(SHARE)} above half", gap=4,
         unit="per cent of generation from nuclear and renewables", dx=(0.36 - 0.06) * 72)
    d = S.at(5.70, top2 + 0.14, 1.10, 2.10)
    panel_d(V, d)
    # row 3: the small multiples of e, one row of eight
    top3 = top2 + 0.14 + 2.10 + 0.70
    mw3, gx = 0.70, 0.152
    axes = [S.at(0.36 + k * (mw3 + gx), top3, mw3, 0.74) for k in range(8)]
    panel_e(V, axes)
    head(V, axes[0], "e", "Low-carbon share in the eight largest producers, by source as in a",
         unit="per cent of generation · dotted: world", gap=15)
    S.footer(footer(f"{SRC_ENERGY} · {SRC_NE}, Equal Earth projection", __file__))
    return fig


ALT = (f"Five panels on the world's electricity. a: stacked area of generation by source, 2000–{LAST}; the low-carbon share "
       f"goes from {LC[0]:.1f} per cent in 2000 to a low of {LC[LOW]:.1f} in {2000 + LOW} and {LC[-1]:.1f} in {LAST}. "
       f"b: yearly change by source; in {LAST} fossil generation fell by {num(-d_fossil)} TWh while total generation rose by "
       f"{num(d_gen)} TWh. c: world map of the low-carbon share in {MAPYEAR}; {over_half} of {len(SHARE)} countries are above half. "
       f"d: among the twenty largest producers the share rose fastest in {SPEED[0][0]}, {SPEED[0][1]:.0f} points a decade; "
       f"{faster} moved faster than the world's {W_SPEED:.1f}. e: the low-carbon share in the eight largest producers, by source.")
META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="five-panel composite: stacked area, diverging stacked bars, choropleth, ranked dot plot, small multiples",
            medium="paper", tool="matplotlib",
            data=(f"Ember yearly electricity data (2026) and Energy Institute Statistical Review of World Energy (2025), via Our World "
                  f"in Data (CC BY 4.0, downloaded {DOWNLOADED}), 2000–{LAST}; Natural Earth v5.1.2"),
            script=rel(__file__), alt=ALT)

if __name__ == "__main__":
    print(TITLE); print(SUB)
    print("speed:", [(c, round(v, 1)) for c, v, _ in SPEED][:6], "world", round(W_SPEED, 1), "faster", faster)
    for mode in MODES:
        save(draw(vellum.use(mode)), "sustainability", NAME, mode, meta=META)
