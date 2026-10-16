"""doughnut.py: the 344 penguins counted at Palmer Station, by species, as a doughnut with the total in the hole; the ring is the
whole and each arc a share, labelled outside. Data: data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Wedge
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0"
SPECIES = ("Adelie", "Chinstrap", "Gentoo")             # slot order: teal, terracotta, indigo
ROWS = load_json("penguins.json")
N = {s: sum(r["Species"] == s for r in ROWS) for s in SPECIES}
TOTAL = sum(N.values())
ISL = {s: {i: sum(r["Species"] == s and r["Island"] == i for r in ROWS) for i in ("Biscoe", "Dream", "Torgersen")} for s in SPECIES}

TITLE = f"Adelie penguins are {N['Adelie'] / TOTAL * 100:.0f} % of the {TOTAL} birds counted, Chinstraps only {N['Chinstrap'] / TOTAL * 100:.0f} %"
SUB = "Penguins measured at Palmer Station, Antarctica, 2007–2009, by species · arc length: share of birds"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.07)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-2.1, 2.1); ax.set_ylim(-1.25, 1.35)
    a0 = 90.0
    for k, s in enumerate(SPECIES):
        sh = N[s] / TOTAL; a1 = a0 - sh * 360
        ax.add_patch(Wedge((0, 0), 1.0, a1, a0, width=0.38, fc=V.tone(k), ec=V.surface, lw=2.2, zorder=3))
        mid = np.deg2rad((a0 + a1) / 2); x, y = np.cos(mid), np.sin(mid); side = 1 if x >= 0 else -1
        ax.plot([0.99 * x, 1.17 * x, 1.17 * x + side * 0.12], [0.99 * y, 1.17 * y, 1.17 * y], color=V.muted, lw=0.5, zorder=2)
        ax.text(1.17 * x + side * 0.17, 1.17 * y, f"{s}\n{N[s]} birds, {sh * 100:.0f} %", ha="left" if side > 0 else "right", va="center",
                fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15)
        a0 = a1
    ax.text(0, 0.08, str(TOTAL), ha="center", va="center", fontsize=V.sz["title"] * 1.5, color=V.ink, fontfamily=V.title_font)
    ax.text(0, -0.2, "penguins", ha="center", va="center", fontsize=V.sz["annotation"], color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="doughnut chart", medium="screen", tool="matplotlib",
            data="Palmer penguins, Gorman, Williams and Fraser (2014), 344 birds", script=rel(__file__),
            alt=(f"Doughnut of {TOTAL} penguins by species: Adelie {N['Adelie']}, Gentoo {N['Gentoo']}, Chinstrap {N['Chinstrap']}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "doughnut", mode, meta=META)
