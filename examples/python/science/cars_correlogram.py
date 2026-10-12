"""cars_correlogram.py: Pearson correlations between six measures of 1970s and early 1980s cars as a lower-triangle
correlogram on the diverging scale (terracotta below zero, teal above), the r value in each cell.
Data: data/cars.json (UCI Auto MPG, Quinlan 1993, via vega-datasets)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from matplotlib.colors import to_rgb
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "UCI Machine Learning Repository, Auto MPG data set (Quinlan 1993);\nvia vega-datasets 2.8.0"
KEYS = ["Miles_per_Gallon", "Cylinders", "Displacement", "Horsepower", "Weight_in_lbs", "Acceleration"]
NAMES = ["miles per gallon", "cylinders", "displacement", "horsepower", "weight", "acceleration"]

cars = load_json("cars.json")
ok = [r for r in cars if all(r.get(k) is not None for k in KEYS)]
R = np.corrcoef(np.array([[r[k] for k in KEYS] for r in ok], float).T)
n = len(KEYS)
best = min(range(1, n), key=lambda i: R[i, 0])          # the strongest (most negative) partner of fuel economy
assert abs(R[best, 0]) == max(abs(R[i, 0]) for i in range(1, n))
years = sorted({r["Year"][:4] for r in ok})

TITLE = f"Weight tracks fuel economy best, r = {R[best, 0]:.2f}".replace("-", "−")
SUB = (f"Pearson r between six measures of {len(ok)} cars, {years[0]}–{years[-1]};\n"
       f"{len(cars) - len(ok)} cars with a missing value left out")


def luminance(c):
    v = np.array(to_rgb(c)); v = np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("square"))
    fig.subplots_adjust(left=0.02, right=0.86, top=0.78, bottom=0.17)
    cmap = V.cmap_div()
    low = np.ma.masked_where(np.triu(np.ones((n, n), bool)), R)                  # the lower half, no diagonal
    im = ax.imshow(low, cmap=cmap, vmin=-1, vmax=1)
    for i in range(1, n):
        for j in range(i):
            cell = cmap((R[i, j] + 1) / 2)
            ink = V.ink if contrast(V.ink, cell) >= contrast(V.surface, cell) else V.surface   # whichever reads on the cell
            ax.text(j, i, f"{R[i, j]:.2f}".replace("-", "−"), ha="center", va="center", fontsize=V.sz["annotation"], color=ink)
    for i, name in enumerate(NAMES):                    # names on the diagonal: each labels its row and its column
        ax.text(i - 0.42, i, name, ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink)
    V.heat_gaps(ax, n, n)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-0.5, n - 0.5); ax.set_ylim(n - 0.5, -0.5)
    V.gradient_bar(fig, im, ax, "Pearson r", ticks=[-1, 0, 1])
    ax.set_anchor("W")                                   # the matrix to the left, so the row names have room before the bar
    ax.text(-0.5, n - 0.5 + 0.25, "each name labels the row to its left and the column below it", ha="left", va="top",
            fontsize=V.sz["annotation"], color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.02)
    return fig


META = dict(title=TITLE, subtitle=SUB.replace("\n", " "), kind="scientific", form="correlogram (lower-triangle, diverging scale)",
            medium="screen", tool="matplotlib", data=f"UCI Auto MPG (Quinlan 1993), {len(ok)} cars with complete records",
            script=rel(__file__),
            alt=(f"Lower-triangle correlation matrix of six car measures. Cylinders, displacement, horsepower and weight correlate "
                 f"at r = {min(R[i, j] for i in range(1, 5) for j in range(1, i)):.2f} or more; each correlates negatively with "
                 f"miles per gallon, most strongly weight at r = {R[best, 0]:.2f}; acceleration correlates weakly with the rest.").replace("-0", "−0"))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "cars_correlogram", mode, meta=META)
