"""streamgraph.py: Germany's electricity by source, 1990–2023, as a streamgraph: the layers stacked around a centre
line, fossil fuels in the warm hues, low-carbon sources in the cool ones, each stream labelled where it is widest. Data:
data/sustainability/owid-energy.csv (Ember and the Energy Institute, via Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Ember and Energy Institute Statistical Review of World Energy, via Our World in Data energy dataset"
COUNTRY = "Germany"
ROWS = {int(r["year"]): r for r in load_csv("sustainability/owid-energy.csv") if r["country"] == COUNTRY and r["coal_electricity"]}
YEARS = np.array([y for y in range(1990, 2024) if y in ROWS])
num = lambda y, k: float(ROWS[y][k] or 0)
# bottom to top: fossil, then nuclear and hydro, then biomass and the rest, then wind and sun; (label, columns, slot)
LAYERS = [("Coal", ("coal_electricity",), 3), ("Oil and gas", ("oil_electricity", "gas_electricity"), 1), ("Nuclear", ("nuclear_electricity",), 4),
          ("Hydro", ("hydro_electricity",), 2), ("Biomass and other", ("biofuel_electricity", "other_renewable_exc_biofuel_electricity"), None),
          ("Wind", ("wind_electricity",), 0), ("Solar", ("solar_electricity",), 5)]
Y = np.array([[sum(num(y, k) for k in cols) for y in YEARS] for _, cols, _ in LAYERS])
TOT = Y.sum(0)
WS = (Y[5] + Y[6]) / TOT
assert WS[-1] > 0.35 and WS[0] < 0.01

TITLE = f"Wind and sun grew to {WS[-1] * 100:.0f} % of German electricity as coal and nuclear shrank"
SUB = f"Electricity generation by source, {COUNTRY}, {YEARS[0]}–{YEARS[-1]}, TWh · stream width: generation, centred on the middle"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.80, bottom=0.10)
    n = len(LAYERS)
    base = -TOT / 2; lo = []; hi = []                                                   # the silhouette baseline: centred
    for i in range(n):
        lo.append(base.copy()); base = base + Y[i]; hi.append(base.copy())
        ax.fill_between(YEARS, lo[i], hi[i], color=V.rule if LAYERS[i][2] is None else V.tone(LAYERS[i][2]), edgecolor=V.surface, linewidth=0.8, zorder=3)
    lim = TOT.max() * 0.56
    mids = [(lo[i][-1] + hi[i][-1]) / 2 for i in range(n)]
    pos = vellum.spread(mids, 0.07 * lim)                                                 # labels pushed apart by one line
    for i, (name, _, slot) in enumerate(LAYERS):
        ax.annotate(name, (YEARS[-1], mids[i]), xytext=(YEARS[-1] + 0.9, pos[i]), textcoords="data", ha="left", va="center",
                    fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=2))
    ax.set_xlim(YEARS[0], YEARS[-1]); ax.set_xticks(range(1990, 2021, 10)); ax.set_xticks(list(range(1990, 2021, 10)) + [2023])
    ax.set_ylim(-lim, lim); ax.set_yticks([-300, -150, 0, 150, 300]); ax.set_yticklabels(["300", "150", "0", "150", "300"])
    ax.grid(False, axis="x"); ax.axhline(0, color=V.rule, lw=V.thin, zorder=1)
    V.panel(ax, unit="TWh a year, either side of the centre line")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="streamgraph", medium="screen", tool="matplotlib",
            data=f"Electricity generation by source, {COUNTRY}, 1990–2023, Ember and Energy Institute via Our World in Data", script=rel(__file__),
            alt=(f"Streamgraph of German electricity by source, {YEARS[0]}–{YEARS[-1]}. Wind and solar grew from {WS[0] * 100:.0f} % to "
                 f"{WS[-1] * 100:.0f} % of generation; coal fell from {Y[0][0]:.0f} to {Y[0][-1]:.0f} TWh and nuclear from {Y[2][0]:.0f} to {Y[2][-1]:.0f}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "streamgraph", mode, meta=META)
