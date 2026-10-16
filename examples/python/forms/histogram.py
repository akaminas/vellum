"""histogram.py: how many Canadian lynx were trapped each year, as a histogram in bins of 500 pelts; the bins above 4,000
pelts, a few years at the crests of the cycle, are the one thing claimed. Data: data/ecology/lynx.csv (Elton and Nicholson 1942)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Elton and Nicholson (1942), Hudson Bay Company lynx returns, Mackenzie River; via R datasets::lynx"
ROWS = load_csv("ecology/lynx.csv")
L = np.array([float(r["trapped"]) for r in ROWS])
EDGES = np.arange(0, 7501, 500)
N, _ = np.histogram(L, EDGES)
LOW = int((L < 1000).sum()); HIGH = int((L >= 4000).sum())

TITLE = f"In {LOW} of {len(L)} years fewer than 1,000 lynx were trapped; only {HIGH} years passed 4,000"
SUB = f"Annual lynx pelts, Mackenzie River, {ROWS[0]['year']}–{ROWS[-1]['year']} · median {np.median(L):,.0f} · years per bin of 500 pelts"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.14)
    mid = EDGES[:-1] + 250
    hot = mid >= 4000
    ax.bar(mid[~hot], N[~hot], width=500, color=V.tone(0), edgecolor=V.surface, linewidth=1.4, zorder=3)
    ax.bar(mid[hot], N[hot], width=500, color=V.tone(1), edgecolor=V.surface, linewidth=1.4, zorder=3)
    for x, n in zip(mid, N):
        if n: ax.text(x, n + 0.8, str(n), ha="center", va="bottom", fontsize=V.sz["annotation"], color=V.ink)
    ax.set_xlim(0, 7500); ax.set_xticks(range(0, 7501, 1000)); ax.set_xticklabels([f"{v:,}" for v in range(0, 7501, 1000)])
    ax.set_ylim(0, N.max() * 1.15); ax.set_yticks([]); ax.grid(False, axis="y"); ax.spines["left"].set_visible(False)
    ax.set_xlabel("lynx pelts trapped in a year")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="histogram", medium="screen", tool="matplotlib",
            data="Canadian lynx returns, Elton and Nicholson (1942), 114 years", script=rel(__file__),
            alt=f"Histogram of annual lynx catches. {LOW} years under 1,000, {HIGH} years of 4,000 or more, median {np.median(L):,.0f}.")

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "histogram", mode, meta=META)
