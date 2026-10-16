"""beeswarm.py: the fuel economy of 398 cars by origin of the maker as a beeswarm, every car one ringed dot, pushed
sideways only as far as it takes not to touch its neighbours, the median marked by a bar. Data: data/cars.json."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Quinlan (1993), UCI Machine Learning Repository, Auto MPG data set; via vega-datasets 2.8.0"
ORIGINS = ("USA", "Europe", "Japan")                     # slot order: teal, terracotta, indigo
C = [r for r in load_json("cars.json") if r["Miles_per_Gallon"]]
MPG = {o: np.array([r["Miles_per_Gallon"] for r in C if r["Origin"] == o], float) for o in ORIGINS}
MED = {o: np.median(v) for o, v in MPG.items()}

TITLE = f"The median Japanese car did {MED['Japan']:.0f} miles to the gallon, the median American car {MED['USA']:.0f}"
SUB = f"Fuel economy of {len(C)} cars sold 1970–1982, one dot per car, by origin of the maker · bar: median"
YLIM = (5, 50)


def swarm(ax, y, centre, width_pt, dot_pt):
    """x positions: dots sorted by y, each placed at the offset nearest the centre where it clears the dots already placed."""
    ax.figure.canvas.draw()
    px = ax.transData.transform(np.c_[np.zeros_like(y), y])[:, 1] * 72 / ax.figure.dpi          # y in points
    xs = np.zeros(len(y)); placed = []
    for i in np.argsort(px):
        for step in range(400):
            off = (step + 1) // 2 * (dot_pt * 0.55) * (1 if step % 2 else -1)
            if all((off - ox) ** 2 + (px[i] - oy) ** 2 >= dot_pt ** 2 for ox, oy in placed if abs(px[i] - oy) < dot_pt):
                xs[i] = off; placed.append((off, px[i])); break
    return xs


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.14)
    ax.set_ylim(*YLIM); ax.set_xlim(-0.7, 2.85)
    for k, o in enumerate(ORIGINS):
        v = MPG[o]
        off = swarm(ax, v, k, 60, 5.2)
        pt_per_x = ax.get_window_extent().width / 3.55 * 72 / fig.dpi
        ax.scatter(k + off / pt_per_x, v, s=26, color=V.tone(k), edgecolor=V.surface, linewidth=0.5, zorder=3)
        half = np.abs(off).max() / pt_per_x + 0.07
        ax.plot([k - half, k + half], [MED[o]] * 2, color=V.ink, lw=V.lw * 1.6, solid_capstyle="butt", zorder=4)
        ax.text(k + half + 0.03, MED[o], f"median {MED[o]:.0f}", ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink,
                path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)], zorder=5)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{o}\n{len(MPG[o])} cars" for o in ORIGINS], color=V.ink, fontsize=V.sz["annotation"])
    ax.set_yticks([10, 20, 30, 40]); ax.grid(False, axis="x")
    V.panel(ax, unit="miles per gallon")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="beeswarm", medium="screen", tool="matplotlib",
            data="Auto MPG, Quinlan (1993), 398 cars with a recorded fuel economy, 1970–1982", script=rel(__file__),
            alt=(f"Beeswarm of fuel economy by origin. Medians: American {MED['USA']:.0f}, European {MED['Europe']:.0f} and "
                 f"Japanese {MED['Japan']:.0f} miles per gallon."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "beeswarm", mode, meta=META)
