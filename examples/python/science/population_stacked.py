"""population_stacked.py: the share of the United States population in four age groups at each census, 1850–2000, as a
stacked area of tints with surface gaps, each layer labelled at its right end in its deep step.
Data: data/population.json (IPUMS USA via vega-datasets); five-year groups summed over both sexes."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "IPUMS USA, Minnesota Population Center; via vega-datasets 2.8.0"
GROUPS = ["0 to 19", "20 to 39", "40 to 59", "60 and over"]          # slot order from the bottom

S = collections.defaultdict(float)
for r in load_json("population.json"):
    S[(r["year"], min(r["age"] // 20, 3))] += r["people"]              # `age` is the lower bound of a five-year group
YEARS = np.array(sorted({y for y, _ in S}))
missing = [y for y in range(YEARS[0], YEARS[-1] + 1, 10) if y not in YEARS]
share = np.array([[100 * S[(y, g)] / sum(S[(y, k)] for k in range(4)) for y in YEARS] for g in range(4)])

TITLE = (f"Americans aged 60 and over grew from {share[3, 0]:.0f} to {share[3, -1]:.0f} per cent of the population, "
         f"{YEARS[0]} to {YEARS[-1]}")
SUB = (f"Share of the population by age group at each census · the under-20s fell from {share[0, 0]:.1f} to "
       f"{share[0, -1]:.1f} per cent")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double"))
    fig.subplots_adjust(left=0.065, right=0.97, top=0.72, bottom=0.17)
    top = np.cumsum(share, axis=0); base = np.vstack([np.zeros(len(YEARS)), top[:-1]])
    for k in range(4):
        ax.fill_between(YEARS, base[k], top[k], color=V.tint(k), lw=0, zorder=2)
        if k < 3: ax.plot(YEARS, top[k], color=V.surface, lw=1.2, zorder=3)        # the surface gap between layers
        mid = (base[k, -1] + top[k, -1]) / 2
        ax.text(YEARS[-1] - 2, mid, f"{GROUPS[k]}  {share[k, -1]:.1f} %", ha="right", va="center",
                fontsize=V.sz["annotation"], color=V.deep(k), zorder=4)         # text on a tint takes the deep step
    ax.set_xlim(YEARS[0], YEARS[-1]); ax.set_xticks([1850, 1900, 1950, 2000])
    ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    V.panel(ax, unit="share of the population, per cent")
    if missing:
        ax.text(1, 1.03, f"no census record for {', '.join(map(str, missing))} in the file: the layers run straight across it",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="stacked area (part of a whole over time)", medium="screen",
            tool="matplotlib", data=f"United States census population by age and sex, IPUMS USA, {YEARS[0]}–{YEARS[-1]} (vega-datasets)",
            script=rel(__file__),
            note=f"The file has no {', '.join(map(str, missing))} census; the layers are drawn straight across the gap.",
            alt=(f"Stacked area of the US population in four age groups from {YEARS[0]} to {YEARS[-1]}. The under-20s shrink from "
                 f"{share[0, 0]:.1f} to {share[0, -1]:.1f} per cent and those aged 60 and over grow from {share[3, 0]:.0f} to "
                 f"{share[3, -1]:.0f} per cent."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "population_stacked", mode, meta=META)
