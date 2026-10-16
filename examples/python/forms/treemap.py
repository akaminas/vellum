"""treemap.py: what the United States burns as petroleum products in 2025, as a treemap: each rectangle's area is the barrels a
day supplied, laid out by the squarified algorithm, the leading product in terracotta. Data: data/eia_petroleum.csv (EIA
Monthly Energy Review, table 3.5), written by examples/python/science/fetch_eia_petroleum.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "US EIA, Monthly Energy Review, table 3.5 (public domain)"
ROWS = load_csv("eia_petroleum.csv")
YEAR = max(r["year"] for r in ROWS if r["description"] == "Total Petroleum Products Supplied")
V_ = {r["description"]: float(r["value"]) / 1000 for r in ROWS if r["year"] == YEAR}          # million barrels a day
TOTAL = V_["Total Petroleum Products Supplied"]
PARTS = {"Motor gasoline": V_["Motor Gasoline Product Supplied"] + V_["Aviation Gasoline Product Supplied"],
         "Distillate fuel oil": V_["Distillate Fuel Oil Product Supplied"], "Hydrocarbon gas liquids": V_["Total Hydrocarbon Gas Liquids Product Supplied"],
         "Jet fuel": V_["Jet Fuel Product Supplied"], "Residual fuel oil": V_["Residual Fuel Oil Product Supplied"]}
PARTS["Asphalt, coke, lubricants, other"] = TOTAL - sum(PARTS.values())
ITEMS = sorted(PARTS.items(), key=lambda kv: -kv[1])
assert all(v > 0 for _, v in ITEMS)
GAS = ITEMS[0][1] / TOTAL

TITLE = f"Gasoline is {GAS * 100:.0f} % of the petroleum the United States burns"
SUB = f"Petroleum products supplied in {YEAR}, {TOTAL:.1f} million barrels a day · area: barrels a day"


def squarify(vals, x, y, w, h):
    """Rectangles (x, y, w, h) for vals, sorted descending, tiling the box with areas in proportion to the values."""
    k = w * h / sum(vals); areas = [v * k for v in vals]; out = []
    while areas:
        side = min(w, h); row = [areas[0]]
        worst = lambda r: max(max(side * side * a / sum(r) ** 2, sum(r) ** 2 / (side * side * a)) for a in r)
        i = 1
        while i < len(areas) and worst(row + [areas[i]]) <= worst(row):
            row.append(areas[i]); i += 1
        thick = sum(row) / side; pos = 0                          # the row runs along the short side

        for a in row:
            ln = a / thick
            out.append((x, y + pos, thick, ln) if w >= h else (x + pos, y, ln, thick))
            pos += ln
        if w >= h: x += thick; w -= thick
        else: y += thick; h -= thick
        areas = areas[len(row):]
    return out


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.012, right=0.988, top=0.80, bottom=0.07)
    W_, H_ = 100, 62
    rects = squarify([v for _, v in ITEMS], 0, 0, W_, H_)
    for i, ((name, v), (x, y, w, h)) in enumerate(zip(ITEMS, rects)):
        ax.add_patch(Rectangle((x, y), w, h, fc=V.tone(1 if i == 0 else [0, 2, 3, 5, 4][i - 1]), ec=V.surface, lw=3, zorder=2))
        fs = V.sz["annotation"]
        small = w < 16 or h < 9
        ax.text(x + 1.4, y + h - 1.6, name, ha="left", va="top", fontsize=fs, color=V.surface if V.mode == "light" else V.card,
                fontweight="bold", wrap=True) if not small else None
        if not small:
            ax.text(x + 1.4, y + h - 5.4, f"{v:.1f} million, {v / TOTAL * 100:.0f} %", ha="left", va="top", fontsize=fs,
                    color=V.surface if V.mode == "light" else V.card)
        else:
            ax.annotate(f"{name}, {v:.1f} million", (x + w, y + h), xytext=(0, 5), textcoords="offset points", ha="right", va="bottom",
                        fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False)
    ax.set_xlim(0, W_); ax.set_ylim(0, H_); ax.set_aspect("auto"); ax.axis("off")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="treemap", medium="screen", tool="matplotlib",
            data=f"EIA Monthly Energy Review, petroleum products supplied, {YEAR}", script=rel(__file__),
            alt=(f"Treemap of US petroleum products supplied in {YEAR}. Motor gasoline is {ITEMS[0][1]:.1f} of {TOTAL:.1f} million "
                 f"barrels a day, {GAS * 100:.0f} %; distillate and hydrocarbon gas liquids follow."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "treemap", mode, meta=META)
