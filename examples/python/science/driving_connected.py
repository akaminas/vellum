"""driving_connected.py: a connected scatter of miles driven per person against the price of petrol in the United
States, one dot per year from 1956 to 2010, years labelled every five years on the side the data give.
Data: data/driving.json (Hannah Fairfield, The New York Times, 2010, via vega-datasets)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "Hannah Fairfield, \"Driving Shifts Into Reverse\", The New York Times, 2 May 2010; via vega-datasets 2.8.0"
D = load_json("driving.json")
year = np.array([d["year"] for d in D]); miles = np.array([d["miles"] for d in D], float)
gas = np.array([d["gas"] for d in D], float)
side = {d["year"]: d["side"] for d in D}

# runs of years in which driving per person fell, and the three that follow the price shocks
fell = year[1:][np.diff(miles) < 0]
runs = []
for y in fell:
    if runs and y == runs[-1][1] + 1: runs[-1][1] = y
    else: runs.append([y, y])
after = {start: next(b - a + 1 for a, b in runs if a >= start) for start in (1974, 1979, 2006)}
WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
assert after[2006] == max(b - a + 1 for a, b in runs), "the longest fall is the one after 2005"
at = lambda y: int(np.where(year == y)[0][0])
change = lambda y0, y1, v: 100 * (v[at(y1)] / v[at(y0)] - 1)

TITLE = (f"Driving fell for {WORD[after[1974]]} year in the 1973 oil shock, {WORD[after[1979]]} in the 1979 shock "
         f"and {WORD[after[2006]]} from 2006")
SUB = (f"Miles driven per person and the price of a gallon of petrol in 2010 dollars, United States, {year[0]}–{year[-1]} · "
       f"one dot per year, joined in time order")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.12)
    ax.plot(miles, gas, color=V.tone(0), lw=V.lw, zorder=2)
    V.dot(ax, miles, gas, V.tone(0), s=16, z=3)
    off = {"left": (-6, 0, "right", "center"), "right": (6, 0, "left", "center"),
           "top": (0, 6, "center", "bottom"), "bottom": (0, -6, "center", "top")}
    for y in year:
        ends = y in (year[0], year[-1])
        if y % 5 and not ends: continue
        dx, dy, ha, va = off[side[y]]
        ax.annotate(str(y), (miles[at(y)], gas[at(y)]), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                    fontsize=V.sz["annotation"], color=V.ink if ends else V.muted, zorder=5,
                    path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
    # the three shocks, said once each beside the loop they make
    notes = [(1974, 1973, 1974, (-14, 24), "right"), (1980, 1978, 1980, (14, 14), "left"), (2008, 2005, 2008, (-30, 6), "right")]
    for y, y0, y1, xy, ha in notes:
        V.callout(ax, (miles[at(y)], gas[at(y)]),
                  f"{y0}–{y1}: price {change(y0, y1, gas):+.0f} %,\ndriving {change(y0, y1, miles):+.1f} %".replace("-", "−"),
                  xy, ha=ha, va="bottom")
    ax.set_xlim(3000, 10800); ax.set_xticks([4000, 6000, 8000, 10000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylim(1.2, 3.5); ax.set_yticks([1.5, 2.0, 2.5, 3.0])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:.2f}"))
    ax.set_xlabel("miles driven per person in the year")
    V.panel(ax, unit="price of a gallon of petrol, 2010 dollars; the axis starts at $1.20")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="connected scatter plot", medium="screen", tool="matplotlib",
            data="Miles driven per capita and petrol price in 2010 dollars, United States, 1956–2010 (Fairfield, NYT 2010; vega-datasets)",
            script=rel(__file__),
            alt=(f"Connected scatter of miles driven per person against petrol price, 1956 to 2010. Driving rises from "
                 f"{miles[0]:,.0f} to a peak of {miles.max():,.0f} miles in {year[np.argmax(miles)]}; it falls for one year in "
                 f"the 1973 shock, two in the 1979 shock and five years running from 2006, while the price reaches ${gas.max():.2f} in "
                 f"{year[np.argmax(gas)]}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "driving_connected", mode, meta=META)
