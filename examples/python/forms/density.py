"""density.py: the distribution of car weight for American, European and Japanese cars as overlaid density curves, each
filled in a tint, outlined in its tone and labelled where it peaks. Data: data/cars.json (UCI Auto MPG, Quinlan 1993)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from scipy import stats
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Quinlan (1993), UCI Machine Learning Repository, Auto MPG data set; via vega-datasets 2.8.0"
ORIGINS = ("USA", "Europe", "Japan")                     # slot order: teal, terracotta, indigo
C = load_json("cars.json")
W = {o: np.array([r["Weight_in_lbs"] for r in C if r["Origin"] == o and r["Weight_in_lbs"]], float) for o in ORIGINS}
XS = np.linspace(1200, 5400, 400)
D = {o: stats.gaussian_kde(W[o], bw_method=0.3)(XS) for o in ORIGINS}
PEAK = {o: XS[D[o].argmax()] for o in ORIGINS}

TITLE = f"The commonest American car weighed {PEAK['USA']:,.0f} lb, the commonest Japanese car {PEAK['Japan']:,.0f} lb"
SUB = f"Weight of {sum(len(w) for w in W.values())} cars sold 1970–1982 by origin of the maker · density curves, equal areas"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.05, right=0.97, top=0.80, bottom=0.12)
    for k, o in enumerate(ORIGINS):
        ax.fill_between(XS, D[o], color=V.tint(k), alpha=0.7, lw=0, zorder=2)
        ax.plot(XS, D[o], color=V.tone(k), lw=V.lw, zorder=3)
        top = D["Japan"].max() * 1.04 if o == "Europe" else D[o].max()          # Europe's line runs up beside Japan's peak
        side = {"USA": 0, "Europe": 1, "Japan": -1}[o]
        ax.annotate(f"{o}\n{len(W[o])} cars", (PEAK[o], top), xytext=(5 * side, 7), textcoords="offset points",
                    ha={0: "center", 1: "left", -1: "right"}[side], va="bottom",
                    fontsize=V.sz["annotation"], color=V.deep(k) if V.mode == "light" else V.tone(k), linespacing=1.1)
        ax.plot([PEAK[o]] * 2, [0, top], color=V.tone(k), lw=V.thin, ls=(0, (1, 2)), zorder=3)
    ax.set_xlim(1200, 5400); ax.set_ylim(0, D["Japan"].max() * 1.22)
    ax.set_xticks([2000, 3000, 4000, 5000]); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_yticks([]); ax.grid(False, axis="y"); ax.set_xlabel("weight, lb")
    V.note(ax, 5350, ax.get_ylim()[1] * 0.97, "dotted line: the most common weight", ha="right")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="density plot", medium="screen", tool="matplotlib",
            data="Auto MPG, Quinlan (1993), 406 cars, 1970–1982", script=rel(__file__),
            alt=(f"Overlaid density curves of car weight. American cars peak at {PEAK['USA']:,.0f} lb, European at "
                 f"{PEAK['Europe']:,.0f} lb and Japanese at {PEAK['Japan']:,.0f} lb."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "density", mode, meta=META)
