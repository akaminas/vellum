"""bubble.py: fertility against life expectancy for 63 countries in 2005, bubble area in proportion to population, China and
India in terracotta, a key of two reference bubbles. Data: data/gapminder.json (Gapminder Foundation)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Gapminder Foundation; via vega-datasets 2.8.0"
YEAR = 2005
R = [r for r in load_json("gapminder.json") if r["year"] == YEAR]
BIG = ("China", "India")
SHARE = sum(r["pop"] for r in R if r["country"] in BIG) / sum(r["pop"] for r in R)
r_ = np.corrcoef([r["life_expect"] for r in R], [r["fertility"] for r in R])[0, 1]
K = 80 / 1e8                                    # pt² per person: 100 million people are an 80 pt² disc

TITLE = f"Fertility falls as people live longer; China and India are {SHARE * 100:.0f} % of those shown"
SUB = f"Fertility against life expectancy in {len(R)} countries, {YEAR} · bubble area: population · r = {r_:.2f}".replace("-", "−")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.12)
    for r in sorted(R, key=lambda r: -r["pop"]):                           # the large first, the small on top
        big = r["country"] in BIG
        ax.scatter(r["life_expect"], r["fertility"], s=K * r["pop"] + 6, color=V.tone(1 if big else 0), alpha=0.88,
                   edgecolor=V.surface, linewidth=min(0.9, 0.1 * np.sqrt(K * r["pop"] + 6)), zorder=3)
        if big:
            ax.annotate(r["country"], (r["life_expect"], r["fertility"]), xytext=(0, -np.sqrt(K * r["pop"]) / 2 - 7), textcoords="offset points",
                        ha="center", va="top", fontsize=V.sz["annotation"], color=V.ink)
    ax.set_xlim(35, 85); ax.set_ylim(0.8, 8.4)
    ax.set_xticks([40, 50, 60, 70, 80]); ax.set_yticks([2, 4, 6, 8]); ax.set_xlabel("life expectancy at birth, years")
    for i, (pop, lab) in enumerate(((1e8, "100 million"), (1e9, "1 billion"))):
        cx, cy = 39.5 + 7.5 * i, 1.75
        ax.scatter([cx], [cy], s=K * pop, facecolor="none", edgecolor=V.muted, linewidth=0.8, zorder=3)
        ax.text(cx, cy + 0.34 + np.sqrt(K * pop) / 40, lab, ha="center", va="bottom", fontsize=V.sz["unit_line"], color=V.muted)
    V.panel(ax, unit="children per woman")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="bubble chart", medium="screen", tool="matplotlib",
            data="Gapminder, 63 countries, 2005", script=rel(__file__),
            alt=(f"Bubble chart of fertility against life expectancy in {YEAR}, bubble area is population. Longer-lived countries "
                 f"have fewer children (r = {r_:.2f}); China and India are the two largest bubbles, {SHARE * 100:.0f} % of the people."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "bubble", mode, meta=META)
