"""tilemap.py: life expectancy at birth in 37 European countries in 2023 on a tile map: every country one equal square placed
where it sits on the map, so a small country is as easy to read as a large one, shaded in five classes along one gradient.
Data: data/owid-life-expectancy.csv (UN WPP 2024 and others, processed by Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = ("UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), "
          "Riley (2005); processed by Our World in Data")
YEAR = 2023
# ISO code: (column, row) on the tile grid, row 0 at the north
GRID = {"ISL": (0, 0), "NOR": (4, 0), "SWE": (5, 0), "FIN": (6, 0),
        "IRL": (1, 1), "GBR": (2, 1), "DNK": (4, 1), "EST": (6, 1),
        "NLD": (3, 2), "DEU": (4, 2), "POL": (5, 2), "LVA": (6, 2),
        "BEL": (3, 3), "CZE": (4, 3), "SVK": (5, 3), "LTU": (6, 3), "BLR": (7, 3), "UKR": (8, 3),
        "FRA": (3, 4), "CHE": (4, 4), "AUT": (5, 4), "HUN": (6, 4), "ROU": (7, 4), "MDA": (8, 4),
        "PRT": (1, 5), "ESP": (2, 5), "ITA": (4, 5), "SVN": (5, 5), "HRV": (6, 5), "SRB": (7, 5), "BGR": (8, 5),
        "BIH": (6, 6), "MNE": (7, 6), "MKD": (8, 6), "TUR": (9, 6), "ALB": (7, 7), "GRC": (8, 7)}
ROWS = [r for r in load_csv("owid-life-expectancy.csv") if r["Year"] == str(YEAR) and r["Code"] in GRID]
LE = {r["Code"]: float(r["Life expectancy"]) for r in ROWS}
NAME = {r["Code"]: r["Entity"] for r in ROWS}
assert set(LE) == set(GRID), set(GRID) - set(LE)
LO, HI = min(LE, key=LE.get), max(LE, key=LE.get)
EDGES = np.array([70, 74, 78, 80, 82, 85])
cls = lambda v: int(np.searchsorted(EDGES, v, side="right") - 1)
EAST = np.mean([LE[c] for c in GRID if GRID[c][0] >= 7]); WEST = np.mean([LE[c] for c in GRID if GRID[c][0] <= 3])

TITLE = f"Europeans live {LE[HI] - LE[LO]:.0f} years longer in {NAME[HI]} than in {NAME[LO]}"
SUB = f"Life expectancy at birth in {len(LE)} European countries, {YEAR} · one tile per country, placed as on the map"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.04)
    cols = V.gradient("lagoon", 5)
    for c, (gx, gy) in GRID.items():
        k = cls(LE[c]); ax.add_patch(Rectangle((gx, -gy), 0.92, 0.92, fc=cols[k], ec="none", zorder=2))
        tc = V.ink if k <= (1 if V.mode == "light" else 2) else V.surface           # ink on the pale tiles, surface on the deep ones
        ax.text(gx + 0.46, -gy + 0.58, c, ha="center", va="center", fontsize=V.sz["annotation"], color=tc, fontweight="bold")
        ax.text(gx + 0.46, -gy + 0.28, f"{LE[c]:.1f}", ha="center", va="center", fontsize=V.sz["unit_line"], color=tc)
    for k in range(5):                                                        # the key, in the empty top right
        y = -0.15 - 0.42 * k
        ax.add_patch(Rectangle((7.9, y), 0.3, 0.3, fc=cols[k], ec="none", zorder=2))
        ax.text(8.32, y + 0.15, f"{EDGES[k]}–{EDGES[k + 1]}" if k else f"under {EDGES[1]}", va="center", ha="left",
                fontsize=V.sz["annotation"], color=V.ink)
    ax.text(7.9, 0.45, "years", ha="left", va="center", fontsize=V.sz["unit_line"], color=V.muted)
    ax.set_xlim(-0.2, 10.2); ax.set_ylim(-7.3, 1.0); ax.set_aspect("equal"); ax.axis("off")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", also=["map"], form="tile map", medium="screen", tool="matplotlib",
            data=f"Life expectancy by country, UN WPP 2024 via Our World in Data, {YEAR}", script=rel(__file__),
            alt=(f"Tile map of life expectancy in {len(LE)} European countries in {YEAR}. {NAME[HI]} is highest at {LE[HI]:.1f} years and "
                 f"{NAME[LO]} lowest at {LE[LO]:.1f}; the countries in the east average {EAST:.1f}, those in the west {WEST:.1f}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "tilemap", mode, meta=META)
