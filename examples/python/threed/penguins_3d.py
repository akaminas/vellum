"""penguins_3d.py: beak length, beak depth and flipper length of the Palmer penguins as a 3D scatter with its 2D twins.

a: the 3D scatter (orthographic, elevation 24, azimuth -58), one family per species in slot order, ringed dots, the
floor projection of every bird in the tints. b and c: two 2D projections with the same colours and direct labels.
Separation is measured by a nearest-centroid rule on standardised measurements (each bird assigned to the species whose
mean it is closest to), in 3D and in each projection.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib import patheffects as pe
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: Gorman, Williams and Fraser (2014), Palmer Station LTER, via vega-datasets 2.8.0 (CC0)"
KEYS = ("Beak Length (mm)", "Beak Depth (mm)", "Flipper Length (mm)")
NAMES = ("beak length", "beak depth", "flipper length")
ROWS = penguins()
X = np.array([[r[k] for k in KEYS] for r in ROWS], float)
SP = np.array([r["Species"] for r in ROWS]); SPECIES = ("Adelie", "Chinstrap", "Gentoo")      # slot order: teal, terracotta, indigo
assert set(SP) == set(SPECIES) and len(X) <= 500


def nearest_centroid(cols):
    """Share of birds whose standardised measurements (columns `cols`) lie nearest their own species' mean, and per species."""
    Z = ((X - X.mean(0)) / X.std(0))[:, cols]
    C = np.array([Z[SP == s].mean(0) for s in SPECIES])
    pred = np.array(SPECIES)[((Z[:, None, :] - C[None]) ** 2).sum(2).argmin(1)]
    return (pred == SP).mean(), {s: (pred[SP == s] == s).mean() for s in SPECIES}


ACC3, _ = nearest_centroid([0, 1, 2])
ACC_B, _ = nearest_centroid([0, 1])
ACC_C, PER_C = nearest_centroid([1, 2])
ACC_AC = sum(PER_C[s] * (SP == s).sum() for s in ("Adelie", "Chinstrap")) / np.isin(SP, ("Adelie", "Chinstrap")).sum()
pct = lambda a: f"{100 * a:.0f} %"
TITLE = f"Three measurements place {pct(ACC3)} of penguins nearest their own species"


def labels2d(fig, ax, V, i, j):
    """Species names in the empty space beside their clusters: of a grid of candidate spots, each name takes the one whose
    box holds no bird and no other name, whose nearest birds are of its own species, and which is closest to its species."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    pts = ax.transData.transform(X[:, [i, j]]); frame = ax.get_window_extent(r)
    boxes = [(b.x0 - 3, b.x1 + 3, b.y0 - 3, b.y1 + 3) for b in (t.get_window_extent(r) for t in ax.texts)]   # notes already there
    gx, gy = np.meshgrid(np.linspace(frame.x0, frame.x1, 40), np.linspace(frame.y0, frame.y1, 40))
    for k, s in enumerate(SPECIES):
        t = ax.text(0, 0, s, fontsize=V.sz["annotation"]); w, h = t.get_window_extent(r).width + 6, t.get_window_extent(r).height + 4; t.remove()
        own = pts[SP == s]; best = None
        for cx, cy in zip(gx.ravel(), gy.ravel()):
            x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
            if x0 < frame.x0 or x1 > frame.x1 or y0 < frame.y0 or y1 > frame.y1: continue
            if ((pts[:, 0] > x0 - 3) & (pts[:, 0] < x1 + 3) & (pts[:, 1] > y0 - 3) & (pts[:, 1] < y1 + 3)).any(): continue
            if any(not (x1 < b[0] or x0 > b[1] or y1 < b[2] or y0 > b[3]) for b in boxes): continue
            d = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
            if SP[np.argsort(d)[:5]].tolist().count(s) < 5: continue          # its five nearest birds are all of its species
            score = np.hypot(*(own.mean(0) - (cx, cy)))
            if best is None or score < best[0]: best = (score, cx, cy, (x0, x1, y0, y1))
        _, cx, cy, box = best; boxes.append(box)
        ax.text(*ax.transData.inverted().transform((cx, cy)), s, fontsize=V.sz["annotation"], color=V.ink, ha="center", va="center", zorder=6)


def draw(V):
    fig = plt.figure(figsize=(7.2, 3.6))
    lim = [(32, 60), (13, 22), (170, 232)]
    ax = V.axes3d(fig, rect=(-0.03, 0.04, 0.47, 0.72), labels=(f"{NAMES[0]} (mm)", f"{NAMES[1]} (mm)", ""))
    for k, s in enumerate(SPECIES):        # floor projection of every bird in the tint, under the points
        P = X[SP == s]
        ax.scatter(P[:, 0], P[:, 1], np.full(len(P), lim[2][0]), s=6, color=V.tint(k), edgecolor="none", depthshade=False, zorder=1)
    for k, s in enumerate(SPECIES):        # ringed dots, no depth shading, no size for depth
        P = X[SP == s]
        ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=20, color=V.tone(k), edgecolor=V.surface, linewidth=0.9, depthshade=False, zorder=3)
    ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1]); ax.set_zlim(*lim[2])
    ax.set_xticks([35, 45, 55]); ax.set_yticks([15, 18, 21]); ax.set_zticks([180, 200, 220])
    # the z quantity as a horizontal unit line above the top of the z axis (the corner of the box drawn rightmost)
    from mpl_toolkits.mplot3d import proj3d
    tops = [proj3d.proj_transform(x, y, lim[2][1], ax.get_proj())[:2] for x in lim[0] for y in lim[1]]
    ax.text2D(*max(tops), f"{NAMES[2]} (mm)", transform=ax.transData, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")
    # b and c: two projections, where the overlap can be read
    axb = fig.add_axes([0.545, 0.17, 0.19, 0.52]); axc = fig.add_axes([0.785, 0.17, 0.19, 0.52])
    for a, (i, j), claim in ((axb, (0, 1), f"b  Length and depth: {pct(ACC_B)}"), (axc, (1, 2), f"c  Depth and flipper: {pct(ACC_C)}")):
        for k, s in enumerate(SPECIES):
            P = X[SP == s]; V.dot(a, P[:, i], P[:, j], V.tone(k), s=14)
        a.set_xlim(*lim[i]); a.set_ylim(*lim[j]); a.set_xlabel(f"{NAMES[i]} (mm)")
        V.panel(a, None, claim, unit=f"{NAMES[j]} (mm)")
    axb.set_xticks([35, 45, 55]); axb.set_yticks([14, 17, 20]); axc.set_xticks([14, 17, 20]); axc.set_yticks([180, 200, 220])
    V.note(axc, 22, 232, f"Gentoo {pct(PER_C['Gentoo'])}\nthe others {pct(ACC_AC)}", ha="right")
    labels2d(fig, axb, V, 0, 1); labels2d(fig, axc, V, 1, 2)
    fig.canvas.draw()                      # panel a's title level with the others
    y_b = fig.transFigure.inverted().transform(axb.title.get_transform().transform(axb.title.get_position()))[1]
    fig.text(0.04, y_b, "a  All three: " + pct(ACC3), fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline")
    V.title(fig, TITLE, f"Palmer penguins, {len(X)} birds · each bird assigned to the nearest species mean of its standardised measurements", footer(SOURCE, __file__))
    return fig


META = dict(
    title=TITLE,
    subtitle=f"Beak length, beak depth and flipper length of {len(X)} Palmer penguins as a 3D scatter, with two 2D projections",
    kind="3d", form="3D scatter with 2D twins", medium="paper", tool="matplotlib",
    data="Palmer penguins, Gorman, Williams and Fraser (2014), Palmer Station LTER, via vega-datasets 2.8.0 (CC0)",
    script=rel(__file__),
    alt=f"A 3D scatter of beak length, beak depth and flipper length for {len(X)} penguins of three species (Adelie teal, Chinstrap "
        f"terracotta, Gentoo indigo), with two 2D projections. Assigned to the nearest species mean, {pct(ACC3)} of birds are placed correctly "
        f"with all three measurements, {pct(ACC_B)} with beak length and depth, {pct(ACC_C)} with beak depth and flipper length, where Adelie "
        f"and Chinstrap overlap.",
    note=f"Separation: nearest-centroid rule on z-scored measurements, resubstitution (no hold-out). 3D {ACC3:.3f}; beak length × depth "
         f"{ACC_B:.3f}; beak depth × flipper {ACC_C:.3f}.",
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "threed", "penguins_scatter3d", mode, meta=META if mode == "light" else None))
