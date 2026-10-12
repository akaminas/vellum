"""life_slope.py: a slope chart of life expectancy at birth in 1950 and 2023 for twelve countries on six continents, the
largest and the smallest gain in colour and the rest in rule grey, labels at both ends pushed apart with leaders.
Data: data/owid-life-expectancy.csv (UN WPP 2024 and others, processed by Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = ("UN World Population Prospects (2024), Human Mortality Database (2024),\nZijdeman and Ribeira da Silva (2015), "
          "Riley (2005);\nprocessed by Our World in Data")
COUNTRIES = ["United States", "Mexico", "Brazil", "Germany", "Russia", "Nigeria", "Ethiopia", "Egypt", "India", "China",
             "Japan", "Australia"]          # two in the Americas, two in Europe, three in Africa, three in Asia, one in Oceania
Y0, Y1 = 1950, 2023

LE = collections.defaultdict(dict)
for r in load_csv("owid-life-expectancy.csv"):
    if r["Entity"] in COUNTRIES and int(r["Year"]) in (Y0, Y1): LE[r["Entity"]][int(r["Year"])] = float(r["Life expectancy"])
gain = {c: LE[c][Y1] - LE[c][Y0] for c in COUNTRIES}
most, least = max(COUNTRIES, key=gain.get), min(COUNTRIES, key=gain.get)
FOCUS = {most: 0, least: 1}                # teal for the largest gain, terracotta for the smallest

short = lambda c: "the US" if c == "United States" else c          # the title must fit 3.5 in; the labels keep the full name
TITLE = f"{short(most)[0].upper() + short(most)[1:]} gained {gain[most]:.0f} years of life, {short(least)} {gain[least]:.0f}"
SUB = f"Life expectancy at birth in years, {Y0} and {Y1}, twelve countries"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("square"))
    fig.subplots_adjust(left=0.36, right=0.64, top=0.82, bottom=0.22)
    ax.set_xlim(0, 1)
    for c in sorted(COUNTRIES, key=lambda c: c in FOCUS):                      # the grey first, the focus on top
        col = V.tone(FOCUS[c]) if c in FOCUS else V.rule
        ax.plot([0, 1], [LE[c][Y0], LE[c][Y1]], color=col, lw=V.lw if c in FOCUS else V.thin, zorder=3 if c in FOCUS else 2)
        V.dot(ax, [0, 1], [LE[c][Y0], LE[c][Y1]], col, z=4 if c in FOCUS else 3)
    # labels at both ends, pushed apart by one line of text; the y range must hold the pushed labels, and the gap in data
    # units depends on that range, so the two are settled together
    vals = {year: [LE[c][year] for c in COUNTRIES] for year in (Y0, Y1)}
    lim = (min(vals[Y0] + vals[Y1]) - 3, max(vals[Y0] + vals[Y1]) + 3)
    for _ in range(6):
        ax.set_ylim(*lim); fig.canvas.draw()
        gap = 1.2 * V.sz["annotation"] / 72 * np.ptp(lim) / (ax.get_window_extent().height / fig.dpi)
        pos = {year: vellum.spread(vals[year], gap) for year in (Y0, Y1)}
        allp = np.concatenate(list(pos.values()))
        lim = (min(lim[0], allp.min() - gap), max(lim[1], allp.max() + gap))
    for x, year, side in ((0, Y0, -1), (1, Y1, 1)):
        for c, v, y in zip(COUNTRIES, vals[year], pos[year]):
            text = f"{c}  {v:.0f}" if side < 0 else f"{v:.0f}  {c}"
            ax.annotate(text, (x, v), xytext=(x + side * 0.2, y), textcoords="data", ha="right" if side < 0 else "left",
                        va="center", fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False,
                        arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=4,
                                        relpos=(1, 0.5) if side < 0 else (0, 0.5)))   # the leader meets the near end of the text
    ax.set_xticks([0, 1]); ax.set_xticklabels([str(Y0), str(Y1)]); ax.set_yticks([])
    ax.grid(False); ax.spines["bottom"].set_visible(False)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.02)
    fig.text(0.02, 0.13, "colour: the largest and the smallest gain of the twelve", fontsize=V.sz["annotation"], color=V.muted)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="slope chart", medium="screen", tool="matplotlib",
            data=f"Our World in Data, period life expectancy at birth (UN WPP 2024 and others), {Y0} and {Y1}", script=rel(__file__),
            alt=(f"Slope chart of life expectancy in {Y0} and {Y1} for twelve countries. All rise. {most} rises most, from "
                 f"{LE[most][Y0]:.0f} to {LE[most][Y1]:.0f} years; {least} least, from {LE[least][Y0]:.0f} to {LE[least][Y1]:.0f}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "life_slope", mode, meta=META)
