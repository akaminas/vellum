"""bar.py: deaths from natural disasters worldwide, 1900–2017, by type of disaster, as horizontal bars sorted by length with
the value at the end of each; the two longest are the claim and carry the one accent colour. Data: data/disasters.csv
(EM-DAT, CRED / UCLouvain, processed by Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import collections, logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "EM-DAT, CRED / UCLouvain; processed by Our World in Data; via vega-datasets 2.8.0"
TOT = collections.Counter()
for r in load_csv("disasters.csv"):
    if r["Entity"] != "All natural disasters": TOT[r["Entity"]] += float(r["Deaths"])
ITEMS = TOT.most_common()
ALL = sum(TOT.values())
TOP2 = sum(v for _, v in ITEMS[:2]) / ALL

TITLE = f"{ITEMS[0][0]} and {ITEMS[1][0].lower()} caused {TOP2 * 100:.0f} % of all natural-disaster deaths since 1900"
SUB = f"Deaths worldwide by type of disaster, 1900–2017, {ALL / 1e6:.0f} million in all · bars sorted by length"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.22, right=0.93, top=0.80, bottom=0.08)
    n = len(ITEMS)
    for i, (name, v) in enumerate(ITEMS):
        y = n - 1 - i
        ax.barh(y, v / 1e6, height=0.62, color=V.tone(1 if i < 2 else 0), zorder=3)
        ax.text(v / 1e6 + 0.12, y, f"{v / 1e6:.1f} million" if v >= 1e5 else f"{v / 1e3:.0f} thousand", va="center", ha="left",
                fontsize=V.sz["annotation"], color=V.ink)
        ax.text(-0.15, y, name, va="center", ha="right", fontsize=V.sz["annotation"], color=V.ink)
    ax.set_ylim(-0.6, n - 0.4); ax.set_xlim(0, max(v for _, v in ITEMS) / 1e6 * 1.22)
    ax.set_yticks([]); ax.set_xticks([]); ax.grid(False)
    for s in ("left", "bottom"): ax.spines[s].set_visible(False)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="bar chart", medium="screen", tool="matplotlib",
            data="EM-DAT disaster deaths by type, 1900–2017, via Our World in Data", script=rel(__file__),
            alt=(f"Horizontal bars of deaths by type of natural disaster, 1900–2017. {ITEMS[0][0]} ({ITEMS[0][1] / 1e6:.1f} million) "
                 f"and {ITEMS[1][0].lower()} ({ITEMS[1][1] / 1e6:.1f} million) are {TOP2 * 100:.0f} % of the {ALL / 1e6:.0f} million."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "bar", mode, meta=META)
