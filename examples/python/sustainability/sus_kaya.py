"""sus_kaya.py: what drove world CO2, 1970–2022, by the Kaya identity, as a five-panel composite.

    CO2 = population × (GDP / population) × (energy / GDP) × (CO2 / energy)

The change in CO2 between two years is split exactly into one term per factor by the additive log-mean Divisia index
(LMDI-I, Ang 2004): ΔC_k = L(C1, C0) · ln(x_k,1 / x_k,0), with L the logarithmic mean; the four terms sum to ΔC.

a  waterfall of the change in world CO2 from 1990 to 2022 into the four factors
b  the same decomposition for five periods, scaled to a change per decade, with the net change marked
c  the four factors and CO2 as an index (1970 = 1, log scale); GDP is published for the world in benchmark years only,
   so the two factors that use it are drawn through those years, each marked
d  carbon intensity of energy, 1965–2024, the world against the four largest emitting countries and the EU-27
e  energy intensity of GDP, 1990–2022, the world (benchmark years) against the same five

Data: data/sustainability/owid-co2.csv (Global Carbon Budget 2025; Energy Institute and U.S. EIA primary energy; Maddison
Project 2023 GDP; UN WPP population; via Our World in Data, CC BY 4.0).
Run: python examples/python/sustainability/sus_kaya.py
"""
from _sus import *
from matplotlib.ticker import FixedLocator, NullLocator

NAME = "sus_kaya"
C, ISO = owid("owid-co2.csv")
W = C["World"]
FACTORS = [("P", "population", "indigo"), ("A", "income per person", "terracotta"),
           ("I", "energy per dollar", "teal"), ("K", "CO₂ per unit of energy", "ochre")]
TAG = {"P": "people", "A": "income", "I": "energy/$", "K": "CO₂/energy"}      # the short names of b and c
HUEF = {k: h for k, _, h in FACTORS}
BENCH = [y for y in sorted(W) if W[y]["gdp"] is not None and y >= 1970]       # 1970, 1980, ... 2010, 2015–2022
B0, B1 = 1990, 2022
assert B1 == BENCH[-1] and all(y in BENCH for y in (1970, 1980, 1990, 2000, 2010))


def factors(y, d=W):
    r = d[y]
    return dict(P=r["population"], A=r["gdp"] / r["population"], I=r["primary_energy_consumption"] / r["gdp"],
                K=r["co2"] / r["primary_energy_consumption"]), r["co2"]


def decompose(a, b):
    f0, c0 = factors(a); f1, c1 = factors(b)
    d = lmdi(c0, c1, f0, f1)
    assert abs(sum(d.values()) - (c1 - c0)) < 1e-6 * c1, "LMDI must be exact"
    return {k: v / 1000 for k, v in d.items()}, c0 / 1000, c1 / 1000        # Gt


# ---- a: 1990 to 2022
DA, CA0, CA1 = decompose(B0, B1)
RISE = 100 * (CA1 / CA0 - 1)
ratio = DA["I"] / DA["K"]

# ---- b: by period, scaled to a change per decade
PERIODS = [(1970, 1980), (1980, 1990), (1990, 2000), (2000, 2010), (2010, 2022)]
DB = []
for a, b in PERIODS:
    d, c0, c1 = decompose(a, b)
    DB.append(({k: v * 10 / (b - a) for k, v in d.items()}, (c1 - c0) * 10 / (b - a)))
K_UP = [p for p, (d, _) in zip(PERIODS, DB) if d["K"] > 0]
assert K_UP == [(2000, 2010)], "carbon intensity rose only in the 2000s"

# ---- c: indices, 1970 = 1
YRS = np.arange(1970, 2025)
IDX = {}
f70, c70 = factors(1970)
for k in ("P", "K"):                                                             # annual: they need no GDP
    if k == "P": s = series(C, "World", "population", YRS)
    else: s = series(C, "World", "co2", YRS) / series(C, "World", "primary_energy_consumption", YRS)
    IDX[k] = (YRS, s / f70[k])
for k in ("A", "I"):
    IDX[k] = (np.array(BENCH), np.array([factors(y)[0][k] / f70[k] for y in BENCH]))
IDX["C"] = (YRS, series(C, "World", "co2", YRS) / c70)

# ---- d, e: the four largest emitting countries in 2024 and the EU-27 (summed from its members where GDP is needed)
EU = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany",
      "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
      "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"]
TOP4 = sorted([c for c in C if is_country(ISO[c]) and C[c].get(2024, {}).get("co2")], key=lambda c: -C[c][2024]["co2"])[:4]
BIG = TOP4 + ["European Union (27)"]
DY = np.arange(1965, 2025)
CI = {c: series(C, c, "co2_per_unit_energy", DY) for c in BIG + ["World"]}
EY = np.arange(1990, 2023)


def energy_per_gdp(c):
    if c != "European Union (27)": return series(C, c, "energy_per_gdp", EY)
    e = sum(series(C, m, "primary_energy_consumption", EY) for m in EU); g = sum(series(C, m, "gdp", EY) for m in EU)
    return 1e9 * e / g                                                           # TWh / $ to kWh / $


EI = {c: energy_per_gdp(c) for c in BIG}
EIW = (np.array([y for y in BENCH if y >= 1990]), np.array([1e9 * W[y]["primary_energy_consumption"] / W[y]["gdp"] for y in BENCH if y >= 1990]))
assert abs(EIW[1][0] - W[1990]["energy_per_gdp"]) < 0.01
SHORT = {"United States": "US", "European Union (27)": "EU-27"}

TITLE = (f"Since {B0} rising incomes added {DA['A']:.1f} Gt to the world's yearly CO₂; using less energy per dollar took off "
         f"{-DA['I']:.1f} Gt, a cleaner energy mix only {-DA['K']:.1f} Gt")
SUB = (f"Fossil and industry CO₂ rose from {CA0:.1f} to {CA1:.1f} Gt a year, {B0}–{B1}, split exactly by the Kaya identity (LMDI)")


def panel_a(V, ax):
    steps = [("P", DA["P"]), ("A", DA["A"]), ("I", DA["I"]), ("K", DA["K"])]
    x = 0; run = CA0
    ax.bar(x, CA0, width=0.62, color=V.muted, lw=0, zorder=2)
    ax.annotate(f"{CA0:.1f}", (x, CA0), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink)
    for k, v in steps:
        x += 1; lo, hi = sorted((run, run + v))
        ax.plot([x - 1 + 0.31, x - 0.31], [run, run], color=V.muted, lw=0.5, zorder=1)      # the connector
        ax.bar(x, hi - lo, bottom=lo, width=0.62, color=V.tone(HUEF[k]), lw=0, zorder=2)
        ax.annotate(f"{v:+.1f}".replace("-", MINUS), (x, hi), xytext=(0, 3), textcoords="offset points", ha="center",
                    va="bottom", fontsize=V.sz["annotation"], color=V.ink)
        run += v
    x += 1
    ax.plot([x - 1 + 0.31, x - 0.31], [run, run], color=V.muted, lw=0.5, zorder=1)
    ax.bar(x, CA1, width=0.62, color=V.secondary, lw=0, zorder=2)
    ax.annotate(f"{CA1:.1f}", (x, CA1), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink)
    assert abs(run - CA1) < 1e-9
    ax.set_xticks(range(6))
    ax.set_xticklabels([str(B0), "population", "income\nper person", "energy\nper dollar", "CO₂ per unit\nof energy", str(B1)],
                       fontsize=V.sz["unit_line"], linespacing=1.1)
    ax.set_xlim(-0.55, 5.55); ax.set_ylim(0, 72); ax.set_yticks([0, 20, 40, 60])
    ax.text(3.0, 30.5, f"energy per dollar took off\n{ratio:.0f}× as much as cleaner energy", ha="center", va="top",
            fontsize=V.sz["annotation"], color=V.muted, linespacing=1.2)
    head(V, ax, "a", f"The rise of {CA1 - CA0:.1f} Gt from {B0} to {B1}, by factor", unit="gigatonnes of CO₂ a year")


def panel_b(V, ax):
    xs = np.arange(len(PERIODS))
    pos = np.zeros(len(xs)); neg = np.zeros(len(xs))
    for k, _, hue in FACTORS:
        v = np.array([d[k] for d, _ in DB]); up = np.where(v > 0, v, 0); dn = np.where(v < 0, v, 0)
        ax.bar(xs, up, bottom=pos, width=0.6, color=V.tone(hue), edgecolor=V.surface, lw=0.6, zorder=2)
        ax.bar(xs, dn, bottom=neg, width=0.6, color=V.tone(hue), edgecolor=V.surface, lw=0.6, zorder=2)
        pos += up; neg += dn
    net = np.array([n for _, n in DB])
    ax.axhline(0, color=V.secondary, lw=0.6, zorder=3)
    ax.scatter(xs, net, marker="_", s=110, color=V.ink, linewidths=1.6, zorder=5)
    for x, n, p in zip(xs, net, pos):
        ax.annotate(f"net {n:+.1f}".replace("-", MINUS), (x, p), xytext=(0, 3), textcoords="offset points", ha="center",
                    va="bottom", fontsize=V.sz["unit_line"] - 0.5, color=V.ink)
    # direct labels on the first column, in place of a legend, pushed apart where the segments are thin
    d0 = DB[0][0]; ys = [d0["P"] / 2, d0["P"] + d0["A"] / 2, d0["I"] / 2, d0["I"] + d0["K"] / 2]
    for (k, name, hue), yy, y0 in zip(FACTORS, vellum.spread(ys, 1.25), ys):
        ax.annotate(TAG[k], (-0.31, y0), xytext=(-0.45, yy), textcoords="data", ha="right", va="center",
                    fontsize=V.sz["unit_line"] - 0.5, color=V.ink,
                    arrowprops=dict(arrowstyle="-", color=V.rule, lw=0.5, shrinkA=1, shrinkB=0, relpos=(1, 0.5)))
    i = PERIODS.index((2000, 2010)); dK = DB[i][0]["K"]
    ax.annotate("2000s, the coal boom:\nCO₂/energy rose", (i - 0.3, pos[i] - dK / 2), xytext=(0.0, 13.9), textcoords="data",
                ha="center", va="top", fontsize=V.sz["unit_line"] - 0.5, color=V.muted, linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=1, relpos=(1, 0.5)))
    ax.set_xticks(xs); ax.set_xticklabels(["1970s", "1980s", "1990s", "2000s", "2010–22"])
    ax.set_xlim(-1.75, len(xs) - 0.4); ax.set_ylim(-8.2, 14.6); ax.set_yticks([-5, 0, 5, 10])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v, sign=v != 0) if v else "0"))
    head(V, ax, "b", "Each decade: growth against efficiency", unit="change in yearly CO₂, Gt per decade")


def panel_c(V, ax):
    ax.set_yscale("log")
    ends = []
    for k, name, hue in FACTORS:
        x, y = IDX[k]
        ax.plot(x, y, color=V.tone(hue), lw=1.4, zorder=3)
        if k in ("A", "I"):                                              # benchmark years only: every point marked
            ax.scatter(x, y, s=9, color=V.tone(hue), edgecolor=V.surface, linewidth=0.6, zorder=4)
        ends.append((x[-1], y[-1], f"{TAG[k]} {y[-1]:.2f}×", k))
    x, y = IDX["C"]; m = ~np.isnan(y)
    ax.plot(x[m], y[m], color=V.ink, lw=1.8, zorder=5)
    ends.append((x[m][-1], y[m][-1], f"CO₂ {y[m][-1]:.2f}×", "C"))
    ax.axhline(1, color=V.rule, lw=0.6, zorder=1)
    ly = 10 ** vellum.spread([np.log10(e[1]) for e in ends], 0.062)
    for (xe, ye, t, k), yy in zip(ends, ly):
        ax.annotate(t, (xe, ye), xytext=(2026.5, yy), textcoords="data", ha="left", va="center", fontsize=V.sz["unit_line"] - 0.5,
                    color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.rule, lw=0.5, shrinkA=1, shrinkB=1, relpos=(0, 0.5)))
    ax.set_xlim(1970, 2024.5); ax.set_xticks([1970, 1990, 2010])
    ax.set_ylim(0.45, 3.4)
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 3])); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels(["0.5", "1", "2", "3"])
    head(V, ax, "c", "The four factors", unit="index, 1970 = 1 (log) · dots: GDP years")


def lines(V, ax, x, data, world, hue, fmt, gap, xw=None, log=False):
    ends = []
    for c in BIG:
        y = data[c]; m = ~np.isnan(y)
        ax.plot(x[m], y[m], color=V.rule, lw=1.0, zorder=2)
        ends.append((x[m][-1], y[m][-1], SHORT.get(c, c)))
    xw_, yw = world
    ax.plot(xw_, yw, color=V.tone(hue), lw=2.0, zorder=4)
    if xw is not None: ax.scatter(xw_, yw, s=10, color=V.tone(hue), edgecolor=V.surface, linewidth=0.6, zorder=5)
    ends.append((xw_[-1], yw[-1], "world"))
    ly = 10 ** vellum.spread([np.log10(e[1]) for e in ends], gap) if log else vellum.spread([e[1] for e in ends], gap)
    for (xe, ye, t), yy in zip(ends, ly):
        ax.annotate(f"{t} {fmt(ye)}", (xe, ye), xytext=(x[-1] + (x[-1] - x[0]) * 0.035, yy), textcoords="data", ha="left",
                    va="center", fontsize=V.sz["unit_line"] - 0.5, color=V.ink if t == "world" else V.muted, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.rule, lw=0.5, shrinkA=1, shrinkB=1, relpos=(0, 0.5)))


def panel_d(V, ax):
    w = CI["World"]; m = ~np.isnan(w)
    lines(V, ax, DY, CI, (DY[m], w[m]), "ochre", lambda v: f"{v:.0f}", 13)
    ax.set_xlim(1965, 2024); ax.set_xticks([1970, 1990, 2010])
    ax.set_ylim(120, 340); ax.set_yticks([150, 200, 250, 300])
    head(V, ax, "d", "CO₂ per unit of energy", unit="grams of CO₂ per kWh of primary energy")


def panel_e(V, ax):
    ax.set_yscale("log")
    lines(V, ax, EY, EI, EIW, "teal", lambda v: f"{v:.2f}", 0.062, xw=True, log=True)
    ax.set_xlim(1990, 2022); ax.set_xticks([1990, 2000, 2010, 2020])
    ax.set_ylim(0.75, 8.5)
    ax.yaxis.set_major_locator(FixedLocator([1, 2, 4, 8])); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels(["1", "2", "4", "8"])
    head(V, ax, "e", "Energy per dollar", unit="kWh of primary energy per dollar of GDP (log)")


def draw(V):
    plt.rcParams["lines.linewidth"] = 1.2
    Wd, H = 7.2, 7.1
    S = Sheet(V, Wd, H); fig = S.fig
    top = S.header(TITLE, SUB) + 0.50
    h1 = 2.15
    a = S.at(0.40, top, 3.05, h1); b = S.at(4.62, top, 2.45, h1)
    panel_a(V, a); panel_b(V, b)
    top2 = top + h1 + 0.95
    h2 = H - top2 - 0.62
    c = S.at(0.40, top2, 1.45, h2); d = S.at(2.86, top2, 1.38, h2); e = S.at(5.28, top2, 1.20, h2)
    panel_c(V, c); panel_d(V, d); panel_e(V, e)
    S.footer(footer(SRC_CO2 + "; Kaya (1990), LMDI after Ang (2004)", __file__))
    return fig


ALT = (f"Five panels on the drivers of world CO2. a: waterfall from {CA0:.1f} Gt in {B0} to {CA1:.1f} Gt in {B1}: population "
       f"{DA['P']:+.1f}, income per person {DA['A']:+.1f}, energy per dollar {DA['I']:+.1f}, CO2 per unit of energy {DA['K']:+.1f} Gt. "
       f"b: the same split for five periods; carbon intensity rose only in the 2000s. c: the four factors as indices since 1970. "
       f"d: CO2 per unit of energy for the world, the four largest emitting countries and the EU-27, 1965–2024. e: energy per dollar of GDP, 1990–2022.")
META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="five-panel composite: waterfall, stacked decomposition bars, index lines (log), highlighted line charts",
            medium="paper", tool="matplotlib",
            data=(f"Global Carbon Budget (2025), Energy Institute and U.S. EIA primary energy, Maddison Project Database (2023), "
                  f"UN WPP; via Our World in Data (CC BY 4.0, downloaded {DOWNLOADED}), 1965–2024"),
            script=rel(__file__), alt=ALT)

if __name__ == "__main__":
    print(TITLE); print(SUB); print("big:", BIG, "ratio", round(ratio, 1))
    for mode in MODES:
        save(draw(vellum.use(mode)), "sustainability", NAME, mode, meta=META)
