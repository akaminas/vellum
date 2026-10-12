"""make_poster_figures.py: the central figure and the numbers of the example A0 poster (examples/latex/poster/poster.tex).

Palmer penguins (Gorman, Williams and Fraser 2014; data/penguins.json via _common.penguins(), the 342 birds with all
four measurements). The figure is the poster's one memorable form:
  a  a 3D scatter of beak length, beak depth and flipper length, ringed dots, one family per species, the floor
     projection in the tints, orthographic, elevation 24, azimuth -58;
  b  its 2D twin, beak length against beak depth, with direct labels.
Drawn light at poster scale: vellum.use("light", scale=2.6) on V.size("poster") enlarged by the same 2.6, so the whole
scale moves together, the 9 pt body is 23 pt and the figure is placed on the sheet at 1:1. No title block and no footer:
the poster's headline carries the claim and its footer band the source and stamp at 18 pt.
Writes examples/latex/poster/fig/central.pdf and fig/numbers.tex: leave-one-out nearest-centroid accuracies (each
measure scaled to mean 0 and sd 1; each bird assigned to the species whose mean, computed without it, is nearest),
the counts and the species means, so the poster types no number by hand.
Run: python examples/python/poster/make_poster_figures.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import *
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # Lato, the fallback face, is not installed here
from matplotlib import patheffects as pe
from mpl_toolkits.mplot3d import proj3d
from matplotlib.transforms import Bbox

OUT = os.path.join(REPO, "examples", "latex", "poster", "fig")
SCALE = 2.6
SPECIES = ("Adelie", "Chinstrap", "Gentoo")                    # slot order: teal, terracotta, indigo
NAMES = {"Adelie": "Adélie", "Chinstrap": "Chinstrap", "Gentoo": "Gentoo"}
COLS = {"bl": "Beak Length (mm)", "bd": "Beak Depth (mm)", "fl": "Flipper Length (mm)", "bm": "Body Mass (g)"}

P = penguins()
sp = np.array([r["Species"] for r in P])
X = {k: np.array([r[c] for r in P], float) for k, c in COLS.items()}


def loo_accuracy(keys):
    """Share of birds assigned to their own species by the nearest species mean, leaving each bird out of the means."""
    F = np.stack([(X[k] - X[k].mean()) / X[k].std() for k in keys], axis=1)
    hits = 0
    for i in range(len(F)):
        keep = np.arange(len(F)) != i
        centres = [F[keep & (sp == s)].mean(axis=0) for s in SPECIES]
        hits += SPECIES[int(np.argmin([np.sum((F[i] - c) ** 2) for c in centres]))] == sp[i]
    return hits / len(F)


acc = {"beak": loo_accuracy(("bl", "bd")), "mass": loo_accuracy(("bm",)), "flipper": loo_accuracy(("fl",))}
assert acc["beak"] > acc["flipper"] > acc["mass"], "the poster claims that beak shape separates the species better than size"
mean = {s: {k: X[k][sp == s].mean() for k in COLS} for s in SPECIES}
assert mean["Adelie"]["bl"] < min(mean["Chinstrap"]["bl"], mean["Gentoo"]["bl"]) and \
       mean["Gentoo"]["bd"] < min(mean["Adelie"]["bd"], mean["Chinstrap"]["bd"]), "the poster says which beaks are short and shallow"


def draw(V):
    w, h = V.size("poster"); fig = plt.figure(figsize=(w * SCALE, h * SCALE))
    fig.text(0.012, 0.985, "Each dot is one bird. In a, the pale dots on the floor are the same birds seen from above: "
             "that view is b.", fontsize=V.sz["subtitle"], color=V.muted, va="top", ha="left")
    ring = vellum.SPEC["marks"]["ring_pt"] * V.scale                 # the surface ring of a marker
    halo = [pe.withStroke(linewidth=3 * V.scale, foreground=V.surface)]
    col = np.array([V.tone(SPECIES.index(s)) for s in sp]); tint = np.array([V.tint(SPECIES.index(s)) for s in sp])
    # ---- a: the 3D scatter; depth on x and length on y, so the floor is panel b and the three clouds sit apart in this view
    ax = V.axes3d(fig, rect=(0.01, -0.06, 0.60, 0.99), labels=("beak depth, mm", "beak length, mm", "flipper length, mm"))
    ax.computed_zorder = False                                   # floor first, then one depth-sorted collection of all birds
    zfloor = X["fl"].min() - 0.06 * np.ptp(X["fl"])
    ax.scatter(X["bd"], X["bl"], np.full(len(sp), zfloor), s=14 * V.scale ** 2, c=tint, edgecolors="none", depthshade=False, zorder=1)
    ax.scatter(X["bd"], X["bl"], X["fl"], s=24 * V.scale ** 2, c=col, edgecolors=V.surface, linewidths=ring, depthshade=False, zorder=3)
    ax.set_xlim(13, 22); ax.set_ylim(31, 61); ax.set_zlim(zfloor, 232)
    ax.set_xticks([14, 17, 20]); ax.set_yticks([35, 45, 55]); ax.set_zticks([180, 200, 220])
    ax.xaxis.labelpad = ax.yaxis.labelpad = 7 * V.scale; ax.zaxis.labelpad = 6 * V.scale    # the module's pads are print size
    ax.set_box_aspect((1, 1, 0.62), zoom=1.16)
    px, py, _ = proj3d.proj_transform(X["bd"], X["bl"], X["fl"], ax.get_proj())          # the birds as drawn on the page
    for s, side in zip(SPECIES, ("right", "top", "top")):     # direct labels just outside each cloud, where no bird is
        x, y = px[sp == s], py[sp == s]
        xy = (np.percentile(x, 97), np.median(y)) if side == "right" else (np.median(x), np.percentile(y, 97))
        ax.annotate(NAMES[s], xy, xytext=(14 * V.scale, 0) if side == "right" else (0, 12 * V.scale), textcoords="offset points",
                    ha="left" if side == "right" else "center", va="center" if side == "right" else "bottom",
                    fontsize=V.sz["annotation"], color=V.ink, path_effects=halo, zorder=6, annotation_clip=False)
    fig.text(0.012, 0.905, "a  Flipper length, a measure of size, sets only Gentoo apart", fontsize=V.sz["panel_title"],
             fontweight="bold", color=V.ink, va="bottom", ha="left")
    # ---- b: the twin, beak length against beak depth, the same axes as the floor of a
    bx = fig.add_axes([0.725, 0.085, 0.26, 0.745])
    for k, s in enumerate(SPECIES):
        V.dot(bx, X["bd"][sp == s], X["bl"][sp == s], V.tone(k), s=24 * V.scale ** 2)
    bx.set_xlim(13, 22); bx.set_ylim(31, 61); bx.set_xticks([14, 17, 20]); bx.set_yticks([35, 45, 55])
    bx.tick_params(axis="x", pad=4 * V.scale); bx.tick_params(axis="y", pad=2 * V.scale)
    for s, (x, y, ha) in zip(SPECIES, ((21.6, 33.0, "right"), (21.6, 58.5, "right"), (13.4, 58.5, "left"))):
        bx.text(x, y, NAMES[s], fontsize=V.sz["annotation"], color=V.ink, ha=ha, va="center", path_effects=halo)
    bx.set_xlabel("beak depth, mm"); V.panel(bx, unit="beak length, mm")
    fig.text(0.725, 0.905, "b  Beak length and depth alone separate all three", fontsize=V.sz["panel_title"],
             fontweight="bold", color=V.ink, va="bottom", ha="left")          # on the line of a, so the two panels read as a pair
    return fig


def ink_box(fig):
    """The crop of what is drawn. The tight box of a 3D axes counts its whole rectangle, which is mostly empty paper."""
    r = fig.canvas.get_renderer(); ax, bx = fig.axes
    parts = [a.get_tightbbox(r) for a in (ax.xaxis, ax.yaxis, ax.zaxis, bx)] + [t.get_window_extent(r) for t in fig.texts]
    return Bbox.union(parts).transformed(fig.dpi_scale_trans.inverted()).padded(0.08)


def numbers_tex():
    """The macros the poster uses, so no number in poster.tex is typed by hand."""
    pc = lambda v: f"{100 * v:.0f}"
    g = lambda v: f"{v:,.0f}".replace(",", "\\,")                  # thousands with a thin space
    m = dict(Birds=len(sp), AccBeak=pc(acc["beak"]), AccMass=pc(acc["mass"]), AccFlipper=pc(acc["flipper"]),
             MassGentoo=g(mean["Gentoo"]["bm"]), MassGap=g(abs(mean["Chinstrap"]["bm"] - mean["Adelie"]["bm"])), Stamp=stamp())
    return "% written by make_poster_figures.py; do not edit\n" + "".join(f"\\newcommand\\p{k}{{{v}}}\n" for k, v in m.items())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    V = vellum.use("light", scale=SCALE)               # a poster is printed: the light twin, the poster scale
    fig = draw(V); fig.savefig(os.path.join(OUT, "central.pdf"), bbox_inches=ink_box(fig)); plt.close(fig)
    open(os.path.join(OUT, "numbers.tex"), "w", encoding="utf-8").write(numbers_tex())
