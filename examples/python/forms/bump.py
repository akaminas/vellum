"""bump.py: the rank of today's eight largest CO2 emitters among themselves, 1990 to 2022, as a bump chart: one line per country,
ringed dots at each year, the country that moved most in colour and the rest in rule grey. Data: data/sustainability/owid-co2.csv
(Global Carbon Project via Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Global Carbon Project (2023), Our World in Data CO2 dataset; fossil CO2 and cement, territorial"
ROWS = [r for r in load_csv("sustainability/owid-co2.csv") if r["iso_code"] and not r["iso_code"].startswith("OWID") and r["co2"]]
CO2 = {(r["country"], int(r["year"])): float(r["co2"]) for r in ROWS}
LAST = 2022
TOP = [c for c, _ in sorted(((c, v) for (c, y), v in CO2.items() if y == LAST), key=lambda t: -t[1])[:8]]
YEARS = list(range(1990, LAST + 1, 4)) + ([LAST] if (LAST - 1990) % 4 else [])
RANK = {c: [1 + sum(CO2[(d, y)] > CO2[(c, y)] for d in TOP) for y in YEARS] for c in TOP}
MOVE = {c: RANK[c][0] - RANK[c][-1] for c in TOP}
STAR = max(TOP, key=lambda c: abs(MOVE[c]))
ordinal = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"

TITLE = f"{STAR} rose from {ordinal(RANK[STAR][0])} to {ordinal(RANK[STAR][-1])} among the eight largest emitters since {YEARS[0]}"
SUB = f"Rank of today's eight largest emitters of fossil CO₂ among themselves, {YEARS[0]}–{LAST}, by total annual emissions"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.16, right=0.84, top=0.80, bottom=0.10)
    for c in sorted(TOP, key=lambda c: c == STAR):
        hot = c == STAR; col = V.tone(1) if hot else V.rule
        ax.plot(YEARS, RANK[c], color=col, lw=V.lw * (2.0 if hot else 1.2), zorder=3 if hot else 2, solid_capstyle="round")
        V.dot(ax, YEARS, RANK[c], col, s=48 if hot else 30, z=4 if hot else 3)
        for x, r, side in ((YEARS[0], RANK[c][0], -1), (YEARS[-1], RANK[c][-1], 1)):
            ax.annotate(c, (x, r), xytext=(side * 9, 0), textcoords="offset points", ha="right" if side < 0 else "left", va="center",
                        fontsize=V.sz["annotation"], color=V.ink if hot else V.muted, fontweight="bold" if hot else "normal")
    ax.set_ylim(8.6, 0.4); ax.set_xlim(YEARS[0] - 1, YEARS[-1] + 1)
    ax.set_yticks([]); ax.set_xticks(YEARS[::2] + ([YEARS[-1]] if len(YEARS) % 2 == 0 else []))
    ax.grid(False); ax.spines["bottom"].set_visible(False)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="bump chart", medium="screen", tool="matplotlib",
            data="Fossil CO2 by country, Global Carbon Project via Our World in Data, 1990–2022", script=rel(__file__),
            alt=(f"Bump chart of the ranks of the eight largest CO2 emitters, {YEARS[0]}–{LAST}. {STAR} moved from "
                 f"{ordinal(RANK[STAR][0])} to {ordinal(RANK[STAR][-1])}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "bump", mode, meta=META)
