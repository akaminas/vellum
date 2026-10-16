"""stackedbar.py: where eight countries got their electricity in 2023, as bars that each sum to 100 %: fossil fuels in the warm
hues, low-carbon sources in the cool ones, the countries sorted by their fossil share. Data: data/sustainability/owid-energy.csv
(Ember and the Energy Institute, via Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Ember and Energy Institute Statistical Review of World Energy, via Our World in Data energy dataset"
YEAR = "2023"
COUNTRIES = ["India", "South Africa", "China", "United States", "Japan", "Germany", "France", "Brazil", "Norway", "Denmark"]
# source, columns summed, slot: warm for fossil fuels, cool for the rest
PARTS = [("Coal", ("coal",), 3), ("Gas and oil", ("gas", "oil"), 1), ("Nuclear", ("nuclear",), 4), ("Hydro", ("hydro",), 2),
         ("Wind", ("wind",), 0), ("Solar", ("solar",), 5)]
ROWS = {r["country"]: r for r in load_csv("sustainability/owid-energy.csv") if r["year"] == YEAR and r["country"] in COUNTRIES}
val = lambda c, k: float(ROWS[c][f"{k}_share_elec"])
DATA = {c: [sum(val(c, k) for k in cols) for _, cols, _ in PARTS] for c in COUNTRIES}
for c in COUNTRIES: DATA[c].append(max(0.0, 100 - sum(DATA[c])))                      # biomass, geothermal, other
FOSSIL = {c: DATA[c][0] + DATA[c][1] for c in COUNTRIES}
ORDER = sorted(COUNTRIES, key=lambda c: -FOSSIL[c])

TITLE = f"Coal makes {DATA['India'][0]:.0f} % of India's electricity; water makes {DATA['Norway'][3]:.0f} % of Norway's"
SUB = f"Share of electricity generation by source, {YEAR}, ten countries sorted by fossil share · warm: fossil, cool: low-carbon"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.76, bottom=0.07)
    n = len(ORDER)
    for i, c in enumerate(ORDER):
        y = n - 1 - i; left = 0.0
        for j, v in enumerate(DATA[c]):
            col = V.tone(PARTS[j][2]) if j < len(PARTS) else V.rule
            ax.barh(y, v, left=left, height=0.7, color=col, edgecolor=V.surface, linewidth=1.0, zorder=3)
            if v >= 7 and j < len(PARTS):
                ax.text(left + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=V.sz["annotation"],
                        color=V.surface if V.mode == "light" else V.card)
            left += v
        ax.text(-1.2, y, c, ha="right", va="center", fontsize=V.sz["annotation"], color=V.ink)
    for j, (name, _, slot) in enumerate(PARTS):                                       # the key, as a row above the bars
        x = [0, 11, 29, 42, 53, 63][j]
        ax.add_patch(plt.Rectangle((x, n - 0.05), 2.2, 0.5, fc=V.tone(slot), ec="none", clip_on=False, zorder=3))
        ax.text(x + 3.2, n + 0.2, name, ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink, clip_on=False)
    ax.add_patch(plt.Rectangle((73, n - 0.05), 2.2, 0.5, fc=V.rule, ec="none", clip_on=False, zorder=3))
    ax.text(76.2, n + 0.2, "Other", ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink, clip_on=False)
    ax.set_xlim(0, 100); ax.set_ylim(-0.6, n - 0.4)
    ax.set_yticks([]); ax.set_xticks([]); ax.grid(False)
    for s in ("left", "bottom"): ax.spines[s].set_visible(False)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="stacked bar chart (100 %)", medium="screen", tool="matplotlib",
            data="Electricity generation by source, Ember and Energy Institute via Our World in Data, 2023", script=rel(__file__),
            alt=(f"Stacked bars of electricity by source in ten countries, {YEAR}. Coal is {DATA['India'][0]:.0f} % of India's "
                 f"electricity; hydro is {DATA['Norway'][3]:.0f} % of Norway's."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "stackedbar", mode, meta=META)
