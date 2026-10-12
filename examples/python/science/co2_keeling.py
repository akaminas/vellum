"""co2_keeling.py: the Keeling curve. Monthly mean CO2 at Mauna Loa as a thin member line, the annual mean on top,
and a dotted reference at 350 ppm. Data: data/co2-concentration.csv (NOAA GML and Scripps, via vega-datasets)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "NOAA Global Monitoring Laboratory and Scripps Institution of Oceanography; via vega-datasets 2.8.0"

# ---- data: monthly values, and annual means of the seasonally adjusted series (1964 lacks February to April,
# and the adjusted series keeps a year with missing months from being biased by the season)
rows = load_csv("co2-concentration.csv")
t = np.array([int(r["Date"][:4]) + (int(r["Date"][5:7]) - 0.5) / 12 for r in rows])
co2 = np.array([float(r["CO2"]) for r in rows])
adj = collections.defaultdict(list)
for r in rows: adj[int(r["Date"][:4])].append(float(r["adjusted CO2"]))
years = np.arange(1959, 2020)                       # the full calendar years of the record
annual = np.array([np.mean(adj[y]) for y in years])
step = np.diff(annual)
assert (step > 0).all(), "the title claims a rise in every year"
rise = annual[-1] - annual[0]
rate60s, rate10s = step[(years[1:] >= 1960) & (years[1:] <= 1969)].mean(), step[years[1:] >= 2010].mean()
first350 = years[np.argmax(annual > 350)]

TITLE = f"Carbon dioxide at Mauna Loa rose in every year from 1959 to 2019, by {rise:.0f} ppm in all"
SUB = (f"Monthly mean CO₂, March 1958 to April 2020 · the yearly rise grew from {rate60s:.1f} ppm in the 1960s "
       f"to {rate10s:.1f} ppm in the 2010s")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double"))
    fig.subplots_adjust(left=0.065, right=0.865, top=0.72, bottom=0.17)
    ax.plot(t, co2, color=V.tone(0), lw=V.thin)                    # the members: every month, seasonal cycle included
    ax.plot(years + 0.5, annual, color=V.tone(0), lw=V.lw)          # the mean on top
    V.dot(ax, years[-1] + 0.5, annual[-1], V.tone(0))
    V.endlabel(ax, years[-1] + 0.5, annual[-1], f"{years[-1]} mean {annual[-1]:.1f} ppm", dx=8)
    V.reference(ax, y=350, text="350 ppm")
    V.note(ax, 1959, 397, "thin line: monthly means, with the seasonal cycle\nthick line: annual mean, seasonally adjusted")
    V.callout(ax, (first350 + 0.5, annual[first350 - 1959]), f"the annual mean passes 350 ppm in {first350}", (28, -15), ha="left", va="top")
    ax.set_xlim(1957, 2021); ax.set_xticks([1960, 1980, 2000, 2020])
    ax.set_ylim(310, 420); ax.set_yticks([320, 340, 360, 380, 400])
    V.panel(ax, unit="CO₂ in parts per million (ppm); the axis starts at 310")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="line chart (members and mean)", medium="screen",
            tool="matplotlib", data="Mauna Loa monthly CO₂, NOAA GML and Scripps, March 1958 to April 2020 (vega-datasets 2.8.0)",
            script=rel(__file__),
            alt=(f"Line chart of monthly CO₂ at Mauna Loa from 1958 to 2020. The annual mean rises in every year, from "
                 f"{annual[0]:.1f} ppm in 1959 to {annual[-1]:.1f} ppm in 2019, and passes the dotted 350 ppm line in {first350}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "co2_keeling", mode, meta=META)
