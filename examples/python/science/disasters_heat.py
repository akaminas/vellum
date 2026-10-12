"""disasters_heat.py: deaths from natural disasters by type and decade as a heat map on the lagoon gradient (log10 of
deaths), with hatched cards for decades with no record. Data: data/disasters.csv (EM-DAT via Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
from matplotlib.patches import Rectangle
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "EM-DAT, CRED / UCLouvain; processed by Our World in Data; via vega-datasets 2.8.0"
DECADES = list(range(1900, 2020, 10))

rows = [r for r in load_csv("disasters.csv") if r["Entity"] != "All natural disasters"]
S = collections.defaultdict(float)
for r in rows: S[(r["Entity"], int(r["Year"]) // 10 * 10)] += float(r["Deaths"])
TYPES = sorted({r["Entity"] for r in rows}, key=lambda e: -sum(S.get((e, d), 0) for d in DECADES))   # rows by total deaths
M = np.array([[S.get((e, d), np.nan) for d in DECADES] for e in TYPES])           # NaN: no death recorded in the decade
last_year = max(int(r["Year"]) for r in rows)

# the claim: droughts, epidemics and floods, deaths per year before 1970 against since 2000
big = ("Drought", "Epidemic", "Flood")
per_year = lambda y0, y1: sum(float(r["Deaths"]) for r in rows if r["Entity"] in big and y0 <= int(r["Year"]) <= y1) / (y1 - y0 + 1)
early, late = per_year(1900, 1969), per_year(2000, last_year)
ratio = early / late

TITLE = f"Droughts, epidemics and floods now kill {ratio:.0f} times fewer people a year than before 1970"
SUB = (f"Deaths by type and decade, 1900–{last_year} (the 2010s cover 2010–{last_year}), rows by total · "
       f"{round(early, -3):,.0f} a year before 1970, {round(late, -2):,.0f} since 2000")

VMIN, VMAX = 1, 7                                       # log10 of deaths: 10 to 10 million


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.17, right=0.90, top=0.80, bottom=0.12)
    L = np.log10(M)
    plt.rcParams["hatch.linewidth"] = 0.8
    im = ax.imshow(np.ma.masked_invalid(L), cmap=V.cmap_gradient("lagoon"), vmin=VMIN, vmax=VMAX, aspect="auto",
                   interpolation="nearest")
    # no value: the card colour with a terracotta hatch, never a stop of the scale. Numbers stay out of the cells: about a
    # quarter of them fall on stop 6, which reaches 4.5:1 with neither ink nor surface, and the claim is in orders of magnitude
    for i, j in zip(*np.where(np.isnan(M))):
        ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=V.card, edgecolor="none", hatch="////",
                               hatchcolor=V.tone("terracotta"), lw=0, zorder=1))
    V.heat_gaps(ax, len(DECADES), len(TYPES))
    ax.set_xticks(range(len(DECADES))); ax.set_xticklabels([f"{d}s" for d in DECADES])
    ax.set_yticks(range(len(TYPES))); ax.set_yticklabels(["Dry mass movement" if t == "Mass movement (dry)" else t for t in TYPES])
    ax.tick_params(axis="y", labelsize=V.sz["tick"], pad=4)
    cb = V.gradient_bar(fig, im, ax, "deaths per decade, log scale", ticks=[1, 3, 5, 7])
    cb.set_ticklabels(["10", "1,000", "100,000", "10 million"])
    ax.text(len(DECADES) - 0.5, -0.62, "hatched: no death recorded · fewer than 10 deaths take the palest colour",
            ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="heat map on a named gradient (lagoon, log scale)", medium="screen",
            tool="matplotlib", data=f"EM-DAT deaths from natural disasters by type and year, 1900–{last_year}, via Our World in Data",
            script=rel(__file__),
            note="Gradient checks of 'Vellum - colour gradients' 1338.18 applied: lagoon, legend bar with labelled ends, hatched card cells for no record.",
            alt=(f"Heat map of deaths per decade for ten kinds of natural disaster from the 1900s to the 2010s. Droughts, epidemics and "
                 f"floods killed about {early / 1e3:,.0f} thousand people a year from 1900 to 1969 and about {late / 1e3:,.1f} thousand a "
                 f"year since 2000, {ratio:.0f} times fewer; earthquakes kill tens to hundreds of thousands in every decade."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "disasters_heat", mode, meta=META)
