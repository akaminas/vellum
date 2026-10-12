"""sus_carbon_budget.py: where the emitted CO2 went, and what it did, 1850–2026, as a five-panel composite.

a  monthly mean CO2 at Mauna Loa, March 1958 to the last month in the file, with the deseasonalised trend
b  the yearly rise of CO2 in the air (difference of complete calendar-year means) against the rise had every emitted
   tonne stayed there (emissions from fossil fuels, industry and land-use change / 7.782 Gt CO2 per ppm); the gap is
   what the ocean and the land took up
c  the airborne fraction, year by year and as a centred eleven-year mean, with the fraction over the whole period
d  global surface temperature (GISTEMP v4, against 1880–1900) against cumulative CO2 since 1850, with the least-squares
   line; the last ten years in terracotta
e  yearly CO2 emissions by source since 1850: coal, oil, gas, cement and other industry, land-use change

Data: data/sustainability/co2_mm_mlo.csv (NOAA GML and Scripps), gistemp_v4.csv (NASA GISS), owid-co2.csv (Global Carbon
Budget 2025 via Our World in Data, CC BY 4.0). Run: python examples/python/sustainability/sus_carbon_budget.py
"""
from _sus import *

NAME = "sus_carbon_budget"
C, ISO = owid("owid-co2.csv")
W = C["World"]
GT_PER_PPM = 2.124 * 3.664                        # GtC per ppm (Ballantyne et al. 2012, as in the Global Carbon Budget) × CO2/C

# ---- a: Mauna Loa, monthly
MM = [l.strip().split(",") for l in open(os.path.join(SUS, "co2_mm_mlo.csv"), encoding="utf-8") if l[:1].isdigit()]
T_M = np.array([float(r[2]) for r in MM]); CO2_M = np.array([float(r[3]) for r in MM]); CO2_D = np.array([float(r[4]) for r in MM])
LAST_M = f"{['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][int(MM[-1][1]) - 1]} {MM[-1][0]}"
BY = {}
for r in MM: BY.setdefault(int(r[0]), []).append(float(r[3]))
ANN = {y: float(np.mean(v)) for y, v in BY.items() if len(v) == 12}        # complete calendar years only

# ---- b, c: growth against emissions
EM_LAST = max(y for y in W if W[y]["co2_including_luc"] is not None)
GY = np.array([y for y in range(1960, EM_LAST + 1) if y in ANN and y - 1 in ANN])
GROW = np.array([ANN[y] - ANN[y - 1] for y in GY])
EMIT = np.array([W[y]["co2_including_luc"] / 1000 for y in GY])          # Gt CO2
EMIT_PPM = EMIT / GT_PER_PPM
AF = GROW / EMIT_PPM
AF_ALL = GROW.sum() / EMIT_PPM.sum()
TOTAL_EMIT = EMIT.sum()
AF_RUN = np.array([AF[max(0, i - 5): i + 6].mean() if 5 <= i < len(AF) - 5 else np.nan for i in range(len(AF))])
assert abs(AF_ALL - 0.433) < 0.005, AF_ALL

# ---- d: temperature against cumulative CO2
G = {}
for l in open(os.path.join(SUS, "gistemp_v4.csv"), encoding="utf-8"):
    p = l.strip().split(",")
    if p[0].isdigit() and p[13] != "***": G[int(p[0])] = float(p[13])
BASE = float(np.mean([G[y] for y in range(1880, 1901)]))
TY = np.array([y for y in range(1880, EM_LAST + 1) if y in G])
CUM = np.array([W[y]["cumulative_co2_including_luc"] / 1000 for y in TY])
TEMP = np.array([G[y] - BASE for y in TY])
SLOPE, ICPT = np.polyfit(CUM, TEMP, 1)
R = np.corrcoef(CUM, TEMP)[0, 1]
assert R > 0.9

# ---- e: emissions by source
EY = np.arange(1850, EM_LAST + 1)
SOURCES = [("coal", ["coal_co2"]), ("oil", ["oil_co2"]), ("gas", ["gas_co2"]),
           ("cement, other", ["cement_co2", "flaring_co2", "other_industry_co2"]), ("land-use change", ["land_use_change_co2"])]
SRC = np.array([sum(np.nan_to_num(series(C, "World", c, EY)) for c in cols) / 1000 for _, cols in SOURCES])
TOT = series(C, "World", "co2_including_luc", EY) / 1000
assert np.allclose(SRC.sum(0), TOT, rtol=0.01), "the five sources must add up to the total with land use"

TITLE = (f"The air kept {100 * AF_ALL:.0f} % of the {num(TOTAL_EMIT)} Gt of CO₂ emitted from {GY[0]} to {GY[-1]}, "
         f"and the world warmed about {1000 * SLOPE:.1f} °C for every {num(1000)} Gt")
SUB = (f"CO₂ at Mauna Loa rose from {ANN[1959]:.0f} ppm in 1959 to {ANN[max(ANN)]:.0f} ppm in {max(ANN)}; "
       f"ocean and land took up the other {100 - 100 * AF_ALL:.0f} %")


def panel_a(V, ax):
    ax.plot(T_M, CO2_M, color=V.tint(0), lw=0.6, zorder=2)
    ax.plot(T_M, CO2_D, color=V.tone(0), lw=1.5, zorder=3)
    y0, y1 = 1959, max(ANN)
    for y, dx, ha, va in ((y0, 7, "left", "top"), (y1, -6, "right", "bottom")):
        V.dot(ax, y + 0.5, ANN[y], V.ink, s=14, z=5, ring=0.9)
        ax.annotate(f"{y}: {ANN[y]:.0f} ppm", (y + 0.5, ANN[y]), xytext=(dx, -6 if va == "top" else 6), textcoords="offset points",
                    ha=ha, va=va, fontsize=V.sz["annotation"], color=V.ink)
    ax.annotate("monthly mean", (1990.5, CO2_M[np.argmin(np.abs(T_M - 1990.6))]), xytext=(1996, 336), textcoords="data",
                ha="left", va="center", fontsize=V.sz["unit_line"], color=V.muted,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=1, relpos=(0, 0.5)))
    ax.annotate("seasonal cycle removed", (2004, CO2_D[np.argmin(np.abs(T_M - 2004))]), xytext=(2008, 360), textcoords="data",
                ha="left", va="center", fontsize=V.sz["unit_line"], color=V.muted,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=1, relpos=(0, 0.5)))
    ax.set_xlim(1957, 2027.5); ax.set_xticks([1960, 1980, 2000, 2020])
    ax.set_ylim(298, 440); ax.set_yticks([320, 360, 400, 440])
    head(V, ax, "a", f"CO₂ in the air, March 1958 to {LAST_M}", unit="parts per million, Mauna Loa")


def panel_b(V, ax):
    ax.fill_between(GY, GROW, EMIT_PPM, color=V.card, lw=0, zorder=1, step="mid")
    ax.bar(GY, GROW, width=0.72, color=V.tone(0), lw=0, zorder=2)
    ax.step(GY, EMIT_PPM, where="mid", color=V.tone(1), lw=1.4, zorder=3)
    i = len(GY) - 1
    ax.annotate("if every tonne\nemitted had stayed", (GY[-12], EMIT_PPM[-12]), xytext=(1985, 5.15), textcoords="data",
                ha="center", va="bottom", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=2, relpos=(0.6, 0)))
    ax.annotate("taken up by\nocean and land", (2008, 3.0), ha="center", va="center", fontsize=V.sz["annotation"],
                color=V.secondary, linespacing=1.15, zorder=4)
    ax.annotate("what stayed\nin the air", (1966, 0.95), xytext=(1962, 2.6), textcoords="data", ha="left", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=2, relpos=(0.2, 0)))
    ax.set_xlim(GY[0] - 1, GY[-1] + 1); ax.set_xticks([1960, 1980, 2000, 2020])
    ax.set_ylim(0, 6.6); ax.set_yticks([0, 2, 4, 6])
    head(V, ax, "b", "Yearly rise, and what was emitted", unit="ppm a year · emissions at 7.78 Gt CO₂ per ppm")


def panel_c(V, ax):
    V.reference(ax, y=AF_ALL)
    ax.scatter(GY, AF, s=9, color=V.tint(0), edgecolor="none", zorder=2)
    ax.plot(GY, AF_RUN, color=V.tone(0), lw=1.5, zorder=3)
    ax.annotate("11-year mean", (GY[6], AF_RUN[6]), xytext=(1961, 0.05), textcoords="data", ha="left", va="bottom",
                fontsize=V.sz["unit_line"], color=V.muted,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=2, relpos=(0.4, 1)))
    hi = int(np.argmax(AF)); lo = int(np.argmin(AF))
    for k, txt in ((hi, f"{GY[hi]}"), (lo, f"{GY[lo]}")):
        ax.annotate(txt, (GY[k], AF[k]), xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=V.sz["unit_line"] - 0.5, color=V.muted)
    ax.set_xlim(GY[0] - 1, GY[-1] + 1); ax.set_xticks([1960, 1990, 2020])
    ax.set_ylim(0, 0.98); ax.set_yticks([0, 0.25, 0.5, 0.75])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}"))
    V.note(ax, GY[0], 0.97, f"dotted: all years, {100 * AF_ALL:.0f} %", va="top")
    head(V, ax, "c", "Airborne fraction", unit="per cent of the year's emissions")


def panel_d(V, ax):
    recent = TY > TY[-1] - 10
    ax.scatter(CUM[~recent], TEMP[~recent], s=10, color=V.rule, edgecolor="none", zorder=2)
    V.dot(ax, CUM[recent], TEMP[recent], V.tone(1), s=16, z=4, ring=0.7)
    xs = np.array([0, 2900]); ax.plot(xs, ICPT + SLOPE * xs, color=V.ink, lw=1.0, zorder=3)
    ax.annotate(f"{1000 * SLOPE:.2f} °C per {num(1000)} Gt\nr = {R:.2f}", (2900, ICPT + SLOPE * 2900), xytext=(-2, 10),
                textcoords="offset points", ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15)
    ax.annotate(f"{TY[-1] - 9}–{TY[-1]}", (CUM[-6], TEMP[-6]), xytext=(-30, 8), textcoords="offset points", ha="right",
                va="bottom", fontsize=V.sz["unit_line"], color=V.ink,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=3))
    ax.annotate("1880–1900:\nthe baseline", (60, -0.05), xytext=(380, -0.36), textcoords="data", ha="left", va="center",
                fontsize=V.sz["unit_line"] - 0.5, color=V.muted, linespacing=1.1,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=2, relpos=(0, 0.5)))
    ax.axhline(0, color=V.rule, lw=0.6, zorder=1)
    ax.set_xlim(0, 3000); ax.set_xticks([0, 1000, 2000, 3000])
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v)))
    ax.set_ylim(-0.45, 1.7); ax.set_yticks([0, 0.5, 1.0, 1.5])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v, 1) if v else "0"))
    ax.set_xlabel("cumulative CO₂ since 1850, Gt", fontsize=V.sz["unit_line"], labelpad=2)
    head(V, ax, "d", "Warming tracks the total", unit="°C above 1880–1900, GISTEMP")


def panel_e(V, ax):
    seq = V.sequential["terracotta"]
    cols = [seq[5], seq[4], seq[2], seq[1]] if V.mode == "light" else [seq[1], seq[2], seq[4], seq[5]]
    cols = cols + [V.tint("moss")]
    base = np.zeros(len(EY))
    tops = []
    for (name, _), col, v in zip(SOURCES, cols, SRC):
        ax.fill_between(EY, base, base + v, color=col, lw=0, zorder=2)
        ax.plot(EY, base + v, color=V.surface, lw=0.5, zorder=3)
        tops.append((base[-1], base[-1] + v[-1])); base = base + v
    mids = [(a + b) / 2 for a, b in tops]
    ys = vellum.spread(mids, 4.2)
    for (name, _), m, yy, v in zip(SOURCES, mids, ys, SRC):
        ax.annotate(f"{name} {v[-1]:.1f}", (EY[-1], m), xytext=(EY[-1] + 8, yy), textcoords="data", ha="left", va="center",
                    fontsize=V.sz["unit_line"] - 0.5, color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.rule, lw=0.5, shrinkA=1, shrinkB=0, relpos=(0, 0.5)))
    ax.set_xlim(1850, EY[-1]); ax.set_xticks([1850, 1900, 1950, 2000])
    ax.set_ylim(0, 46); ax.set_yticks([0, 10, 20, 30, 40])
    head(V, ax, "e", f"Emissions by source, 1850–{EY[-1]}", unit="Gt of CO₂ a year")


def draw(V):
    plt.rcParams["lines.linewidth"] = 1.2
    Wd, H = 7.2, 7.0
    S = Sheet(V, Wd, H); fig = S.fig
    top = S.header(TITLE, SUB) + 0.50
    h1 = 2.05
    a = S.at(0.40, top, 3.0, h1); b = S.at(4.15, top, 2.90, h1)
    panel_a(V, a); panel_b(V, b)
    top2 = top + h1 + 0.72
    h2 = H - top2 - 0.62
    c = S.at(0.40, top2, 1.55, h2); d = S.at(2.55, top2, 1.80, h2); e = S.at(4.92, top2, 1.28, h2)
    panel_c(V, c); panel_d(V, d); panel_e(V, e)
    S.footer(footer(f"{SRC_MLO} (Maunakea, Dec 2022 to Jul 2023); GISTEMP v4, NASA GISS, public domain; {SRC_GCB}", __file__))
    return fig


ALT = (f"Five panels. a: CO2 at Mauna Loa from {ANN[1959]:.0f} ppm in 1959 to {ANN[max(ANN)]:.0f} ppm in {max(ANN)}. "
       f"b: the yearly rise against what emissions would have added; c: the airborne fraction, {100 * AF_ALL:.0f} per cent over "
       f"{GY[0]}–{GY[-1]}. d: global temperature against cumulative CO2, {1000 * SLOPE:.2f} °C per 1,000 Gt (r = {R:.2f}). "
       f"e: yearly emissions by source since 1850; {SRC[-1, -1]:.1f} Gt from land-use change and {SRC[:4, -1].sum():.1f} Gt from "
       f"fossil fuels and industry in {EY[-1]}.")
META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="five-panel composite: line, bars against a step line, dots with running mean, scatter with fit, stacked area",
            medium="paper", tool="matplotlib",
            data=(f"Mauna Loa monthly CO2 (NOAA GML and Scripps) to {LAST_M}; GISTEMP v4 (NASA GISS); Global Carbon Budget (2025) "
                  f"via Our World in Data (CC BY 4.0); all downloaded {DOWNLOADED}"),
            script=rel(__file__), alt=ALT,
            note=("Mauna Loa was shut by its eruption from 29 November 2022 to July 2023; NOAA fills those months from Maunakea. "
                  "Growth is the difference of calendar-year means of complete years. Observed warming includes the effect of "
                  "gases other than CO2 and of aerosols, so the slope in d is an empirical ratio, not the TCRE of CO2 alone."))

if __name__ == "__main__":
    print(TITLE); print(SUB); print("slope", SLOPE * 1000, "r", R, "AF", AF_ALL, "last", LAST_M)
    for mode in MODES:
        save(draw(vellum.use(mode)), "sustainability", NAME, mode, meta=META)
