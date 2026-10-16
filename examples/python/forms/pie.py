"""pie.py: the end-use sectors of United States petroleum in 2025 as a pie of five slices, the largest, transportation, in
terracotta, every slice labelled outside with its name and share. Pie only because there are few parts and one of them is
more than half. Data: data/eia_petroleum.csv (EIA Monthly Energy Review, table 3.7)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Wedge
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "US EIA, Monthly Energy Review, tables 3.7a–c (public domain)"
ROWS = load_csv("eia_petroleum.csv")
YEAR = max(r["year"] for r in ROWS if r["msn"] == "PATCPUS")
V_ = {r["description"]: float(r["value"]) / 1000 for r in ROWS if r["year"] == YEAR}
SECTORS = [("Transportation", "Transportation"), ("Industrial", "Industrial"), ("Residential", "Residential"),
           ("Commercial", "Commercial"), ("Electric power", "Electric Power")]
VAL = [(name, V_[f"Total Petroleum Consumed by the {key} Sector"]) for name, key in SECTORS]
TOTAL = sum(v for _, v in VAL)
SHARE = [v / TOTAL for _, v in VAL]

TITLE = f"Transportation burns {SHARE[0] * 100:.0f} % of US petroleum; power plants burn {SHARE[4] * 100:.1f} %"
SUB = f"Petroleum consumed by end-use sector, {YEAR}, {TOTAL:.1f} million barrels a day · slices clockwise from the top"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.07)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-2.1, 2.1); ax.set_ylim(-1.25, 1.85)
    a0 = 90.0
    for i, ((name, v), s) in enumerate(zip(VAL, SHARE)):
        a1 = a0 - s * 360
        ax.add_patch(Wedge((0, 0), 1.0, a1, a0, fc=V.tone(1 if i == 0 else [0, 2, 3, 5][i - 1]), ec=V.surface, lw=2.2, zorder=3))
        mid = np.deg2rad((a0 + a1) / 2); r = 1.0
        x, y = np.cos(mid), np.sin(mid)
        side = 1 if x >= 0 else -1
        label = f"{name}\n" + (f"{s * 100:.0f} %" if s >= 0.0095 else f"{s * 100:.1f} %")
        if s < 0.04:                                    # the thin slices at the top: labels in a row above, on straight leaders
            lx = {"Residential": -1.45, "Commercial": -0.7, "Electric power": 0.05}[name]
            ax.plot([x, lx], [y, 1.37], color=V.muted, lw=0.5, zorder=2)
            ax.text(lx, 1.4, label, ha="center", va="bottom", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15)
        else:
            ax.plot([r * 0.98 * x, 1.17 * x, 1.17 * x + side * 0.12], [r * 0.98 * y, 1.17 * y, 1.17 * y], color=V.muted, lw=0.5, zorder=2)
            ax.text(1.17 * x + side * 0.17, 1.17 * y, label, ha="left" if side > 0 else "right", va="center",
                    fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15)
        a0 = a1
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="pie chart", medium="screen", tool="matplotlib",
            data=f"EIA Monthly Energy Review, petroleum consumption by sector, {YEAR}", script=rel(__file__),
            alt=(f"Pie chart of US petroleum use by sector in {YEAR}: transportation {SHARE[0] * 100:.0f} %, industrial "
                 f"{SHARE[1] * 100:.0f} %, residential {SHARE[2] * 100:.0f} %, commercial {SHARE[3] * 100:.0f} %, electric power {SHARE[4] * 100:.1f} %."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "pie", mode, meta=META)
