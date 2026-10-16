"""area.py: petroleum products supplied in the United States each year since 1949 as an area chart: one filled series with
its line on top, the peak marked. The baseline is zero, so the area is the quantity. Data: data/eia_petroleum.csv (EIA
Monthly Energy Review, table 3.5)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "US EIA, Monthly Energy Review, table 3.5 (public domain)"
ROWS = [r for r in load_csv("eia_petroleum.csv") if r["description"] == "Total Petroleum Products Supplied"]
YR = np.array([int(r["year"]) for r in ROWS]); VAL = np.array([float(r["value"]) / 1000 for r in ROWS])      # million barrels a day
PK = int(VAL.argmax())
assert PK < len(YR) - 1 and VAL[PK + 1:].max() < VAL[PK]

TITLE = f"US petroleum use peaked in {YR[PK]} and has not passed {VAL[PK]:.1f} million barrels a day since"
SUB = f"Petroleum products supplied in the United States, {YR[0]}–{YR[-1]}, million barrels a day · {VAL[-1]:.1f} in {YR[-1]}"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.10)
    ax.fill_between(YR, VAL, color=V.tint(0), alpha=0.9, lw=0, zorder=2)
    ax.plot(YR, VAL, color=V.tone(0), lw=V.lw * 1.3, zorder=3)
    V.dot(ax, [YR[PK], YR[-1]], [VAL[PK], VAL[-1]], V.tone(1), z=5)
    ax.annotate(f"{YR[PK]}: {VAL[PK]:.1f}", (YR[PK], VAL[PK]), xytext=(-8, 8), textcoords="offset points", ha="right", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink)
    ax.annotate(f"{YR[-1]}: {VAL[-1]:.1f}", (YR[-1], VAL[-1]), xytext=(0, 12), textcoords="offset points", ha="right", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink)
    ax.annotate(f"{YR[0]}: {VAL[0]:.1f}", (YR[0], VAL[0]), xytext=(8, -14), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["annotation"], color=V.ink)
    ax.set_xlim(YR[0], YR[-1] + 1); ax.set_ylim(0, 24); ax.set_xticks(range(1950, 2021, 10)); ax.set_yticks([0, 5, 10, 15, 20])
    V.panel(ax, unit="million barrels a day")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="area chart", medium="screen", tool="matplotlib",
            data="EIA Monthly Energy Review, total petroleum products supplied, 1949–2025", script=rel(__file__),
            alt=(f"Area chart of US petroleum products supplied, {YR[0]}–{YR[-1]}. Use rose from {VAL[0]:.1f} to a peak of "
                 f"{VAL[PK]:.1f} million barrels a day in {YR[PK]} and was {VAL[-1]:.1f} in {YR[-1]}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "area", mode, meta=META)
