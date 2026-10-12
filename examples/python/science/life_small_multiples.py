"""life_small_multiples.py: life expectancy at birth, 1950–2023, as six small multiples. Each panel shows one country in
its family tone over every other country in rule grey, with the collapse it went through noted at the dip.
Data: data/owid-life-expectancy.csv (UN WPP 2024 and others, processed by Our World in Data); countries only."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
from matplotlib.collections import LineCollection
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = ("UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), "
          "Riley (2005);\nprocessed by Our World in Data")
YEARS = np.arange(1950, 2024)

LE = collections.defaultdict(dict)
for r in load_csv("owid-life-expectancy.csv"):
    if len(r["Code"]) == 3 and 1950 <= int(r["Year"]) <= 2023:          # a three-letter code is a country or territory
        LE[r["Entity"]][int(r["Year"])] = float(r["Life expectancy"])
SERIES = {c: np.array([v.get(y, np.nan) for y in YEARS]) for c, v in LE.items() if len(v) == len(YEARS)}
rose = sum(s[-1] > s[0] for s in SERIES.values())

# (country, what happened, the year before it began or None for the peak before the trough, years in which to find the trough)
STORIES = [("Japan", None, None, None), ("China", "famine", 1958, (1959, 1962)), ("Lebanon", "civil war", 1974, (1975, 1977)),
           ("Rwanda", "genocide", 1993, (1994, 1994)), ("Eswatini", "HIV", None, (1995, 2010)),
           ("Bolivia", "covid-19", 2019, (2020, 2021))]
PANELS = []
for c, what, ref, win in STORIES:
    s = SERIES[c]; at = lambda y: s[y - 1950]
    if what is None:
        PANELS.append(dict(country=c, title=f"{c} gained {s[-1] - s[0]:.0f} years, steadily", x=1950, y=s[0],
                           note=f"{1950}: {s[0]:.0f} years · no fall above {-np.diff(s).min():.1f} in a year"))
        continue
    yrs = np.arange(win[0], win[1] + 1); trough = yrs[np.argmin([at(y) for y in yrs])]
    peak = ref is None                                  # a slow fall is counted from the peak before it, and the note says so
    if peak: ref = 1950 + int(np.argmax(s[:trough - 1950]))
    PANELS.append(dict(country=c, title=f"{c} lost {at(ref) - at(trough):.0f} years to {what}", x=trough, y=at(trough),
                       note=f"{trough}: {at(trough):.0f} years" + (f"\npeak {at(ref):.0f} in {ref}" if peak else "")))

TITLE = f"Life expectancy rose in all {rose} countries since 1950, but the trend hides collapses"
SUB = (f"Life expectancy at birth · one country per panel, the other {len(SERIES) - 1} countries and territories in grey"
       f" · each loss from the year before the crisis")


def draw(V):
    fig = plt.figure(figsize=V.size("double_tall"))
    gs = fig.add_gridspec(2, 3, left=0.055, right=0.955, top=0.78, bottom=0.12, wspace=0.22, hspace=0.5)
    others = np.array([np.column_stack([YEARS, s]) for s in SERIES.values()])
    for k, p in enumerate(PANELS):
        ax = fig.add_subplot(gs[k // 3, k % 3])
        ax.add_collection(LineCollection(others, colors=V.rule, linewidths=0.4, alpha=0.2, zorder=1))
        s = SERIES[p["country"]]
        ax.plot(YEARS, s, color=V.tone(k), lw=V.lw, zorder=3)
        V.dot(ax, YEARS[-1], s[-1], V.tone(k), z=4)
        V.endlabel(ax, YEARS[-1], s[-1], f"{s[-1]:.0f}", dx=5)
        late = p["x"] > 2010                             # a late dip takes its note below and to the left
        ax.annotate(p["note"], (p["x"], p["y"]), xytext=(-4, -8) if late else (5, -2), textcoords="offset points",
                    ha="right" if late else "left", va="top", fontsize=V.sz["annotation"], color=V.muted, zorder=5,
                    path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
        ax.set_xlim(1950, 2023); ax.set_xticks([1960, 1990, 2020])
        ax.set_ylim(0, 90); ax.set_yticks([20, 40, 60, 80])
        if k % 3: ax.set_yticklabels([])
        if k < 3: ax.set_xticklabels([])
        ax.set_title(p["title"], color=V.ink, fontsize=V.sz["panel_title"], pad=16)   # one title height across the row
        if k % 3 == 0: V.panel(ax, unit="life expectancy at birth, years")   # the unit line once per row
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="small multiples of line charts", medium="screen",
            tool="matplotlib", data="Our World in Data, period life expectancy at birth (UN WPP 2024 and others), 1950–2023, countries only",
            script=rel(__file__),
            alt=("Six small line charts of life expectancy from 1950 to 2023 over all other countries in grey: "
                 + "; ".join(f"{p['title']} ({p['note']})".replace("\n", ", ") for p in PANELS) + "."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "life_small_multiples", mode, meta=META)
