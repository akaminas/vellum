"""landscape_3d.py: the analytic two-trait adaptive landscape of _common.landscape as a 3D surface with its 2D twin.

a: the surface w(z1, z2) on [-2, 2]^2, orthographic, elevation 24, azimuth -58, lagoon gradient, 90 x 90 grid, floor contours.
b: the twin: the same values as a heat map with contour lines, same gradient and limits, with the two peaks and the saddle
between them marked. The peaks are found by maximisation and the saddle by solving grad w = 0 from the lowest point of the
straight path between the peaks; the Hessian there is checked to be indefinite. Illustrative by construction.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib import patheffects as pe
from scipy import optimize
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Analytic function landscape(z1, z2) in _common.py, illustrative"
LO, HI = LANDSCAPE_DOMAIN


def grad(p, h=1e-6):
    return np.array([(landscape(p[0] + h, p[1]) - landscape(p[0] - h, p[1])) / (2 * h),
                     (landscape(p[0], p[1] + h) - landscape(p[0], p[1] - h)) / (2 * h)])


def features():
    """The two peaks (maxima) and the saddle on the path between them, with their heights."""
    peaks = [optimize.minimize(lambda p: -landscape(*p), x0, method="Nelder-Mead", options=dict(xatol=1e-10, fatol=1e-12)).x
             for x0 in ((1.0, 1.0), (-1.0, -1.0))]
    t = np.linspace(0, 1, 2001)[:, None]; path = peaks[0] + t * (peaks[1] - peaks[0])
    saddle = optimize.root(grad, path[np.argmin(landscape(path[:, 0], path[:, 1]))], tol=1e-12).x
    h = 1e-4; H = np.array([(grad(saddle + d) - grad(saddle - d)) / (2 * h) for d in np.eye(2) * h])
    ev = np.linalg.eigvalsh((H + H.T) / 2); assert ev[0] < 0 < ev[1], ev           # a saddle: one direction up, one down
    return [(p, float(landscape(*p))) for p in (*peaks, saddle)]


(P1, W1), (P2, W2), (S, WS) = features()
z = np.linspace(LO, HI, 90); Z1, Z2 = np.meshgrid(z, z); W = landscape(Z1, Z2)
VMIN, VMAX = float(W.min()), float(W.max())
fmt = lambda p: f"({p[0]:.2f}, {p[1]:.2f})".replace("-", "−")
TITLE = f"Two adaptive peaks, {W1:.2f} and {W2:.2f}, are joined by a saddle at w = {WS:.2f}"


def draw(V):
    fig = plt.figure(figsize=(7.2, 3.6))
    cm = V.cmap_gradient("lagoon")
    ax = V.axes3d(fig, rect=(-0.01, 0.04, 0.56, 0.72), labels=("trait z₁", "trait z₂", ""))
    V.surface3d(ax, Z1, Z2, W, cmap=cm, vmin=VMIN, vmax=VMAX)
    ax.set_xticks([-1, 0, 1]); ax.set_yticks([-1, 0, 1]); ax.set_zticks([0, 0.5, 1])       # ticks away from the shared corner
    ax.set_xlim(LO, HI); ax.set_ylim(LO, HI)
    # the z quantity as a horizontal unit line above the top of the z axis (the corner of the box drawn rightmost)
    from mpl_toolkits.mplot3d import proj3d
    tops = [proj3d.proj_transform(x, y, ax.get_zlim()[1], ax.get_proj())[:2] for x in (LO, HI) for y in (LO, HI)]
    ax.text2D(*max(tops), "mean fitness w", transform=ax.transData, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")
    # b: the twin, where values are read
    ax2 = fig.add_axes([0.635, 0.17, 0.27, 0.54])
    im = ax2.imshow(W, origin="lower", extent=[LO, HI, LO, HI], cmap=cm, vmin=VMIN, vmax=VMAX, aspect="equal", interpolation="bilinear")
    ax2.contour(Z1, Z2, W, levels=7, colors=V.surface, linewidths=0.5, alpha=0.8)
    halo = [pe.withStroke(linewidth=2, foreground=V.surface)]
    for p, w, name, off, ha in ((P1, W1, "high peak", (-6, 9), "right"), (P2, W2, "low peak", (6, -9), "left"),
                                (S, WS, "saddle", (7, 0), "left")):
        V.dot(ax2, p[0], p[1], V.tone("terracotta"), s=22, z=5)
        ax2.annotate(f"{name} {w:.2f}", p, xytext=off, textcoords="offset points", ha=ha, va="center", fontsize=V.sz["annotation"],
                     color=V.ink, path_effects=halo)
    ax2.set_xticks([-2, -1, 0, 1, 2]); ax2.set_yticks([-2, -1, 0, 1, 2]); ax2.set_xlabel("trait z₁"); ax2.grid(False)
    for s in ax2.spines.values(): s.set_visible(False)
    V.panel(ax2, "b", "The values, read from the twin", unit="trait z₂")
    V.gradient_bar(fig, im, ax2, "mean fitness w", ticks=[0, 0.25, 0.5, 0.75, 1.0])
    fig.canvas.draw()                                                                       # panel a's title level with panel b's
    y_b = fig.transFigure.inverted().transform(ax2.title.get_transform().transform(ax2.title.get_position()))[1]
    fig.text(0.07, y_b, "a  The shape: two peaks and a saddle", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline")
    V.title(fig, TITLE, "Illustrative landscape w(z₁, z₂) · same gradient and limits in both panels · orthographic, elevation 24°, azimuth −58°",
            footer(SOURCE, __file__))
    return fig


META = dict(
    title=TITLE,
    subtitle="An illustrative two-trait adaptive landscape as a 3D surface with its heat-map twin",
    kind="3d", form="3D surface with twin", medium="paper", tool="matplotlib",
    data="Analytic function landscape(z1, z2) in examples/python/_common.py (illustrative)",
    script=rel(__file__),
    alt=f"A 3D surface of mean fitness w over two traits on [−2, 2]², with a heat-map twin. Two peaks: the high one w = {W1:.2f} at "
        f"(z₁, z₂) = {fmt(P1)} and the low one w = {W2:.2f} at {fmt(P2)}, joined by a saddle at w = {WS:.2f} at {fmt(S)}.",
    note=f"Illustrative analytic landscape. High peak w = {W1:.3f} at {fmt(P1)}; low peak w = {W2:.3f} at {fmt(P2)}; "
         f"saddle w = {WS:.3f} at {fmt(S)} (grad w = 0, Hessian indefinite), on the path between the peaks. "
         f"Surface 90 × 90, lagoon gradient from {VMIN:.3f} to {VMAX:.3f} in both panels.",
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "threed", "landscape_surface", mode, meta=META if mode == "light" else None))
