"""make_talk_figures.py: the figures and the numbers of the example talk (examples/latex/talk/talk.tex).

An illustrative simulation on the shared two-trait adaptive landscape w(z1, z2) of _common.landscape. Each generation
the mean traits of a population take a step of G times the gradient of ln w (Lande's equation) plus a little drift,
from a fixed seed. Drawn in the dark twin at slide scale (the deck is for a dark hall), with no title block because
the frame title carries the claim:
  fig/reveal_1.pdf ... reveal_4.pdf   mean fitness against generation, one population added per step (slide)
  fig/surface_a.pdf, surface_b.pdf    the landscape at two fixed views (slide_half)
  fig/twin.pdf                        its heat-map twin with the four paths, the peaks and the basin boundary (slide_half)
  fig/numbers.tex                     every number the slides print, as macros, with the git stamp
Run: python examples/python/talk/make_talk_figures.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import *
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # Lato, the fallback face, is not installed here
from matplotlib import patheffects as pe
from scipy.optimize import minimize, root

OUT = os.path.join(REPO, "examples", "latex", "talk", "fig")
G, DRIFT, T, SEED, N_STARTS = 0.02, 0.02, 100, 2026, 500
LO, HI = LANDSCAPE_DOMAIN
VIEWS = {"a": -58, "b": -148}           # azimuths; elevation 24 for both. b is the default turned by 90 degrees


def grad_ln(z, h=1e-5):
    """Gradient of ln w by central differences of the shared landscape, so its formula is not retyped here."""
    z = np.asarray(z, float); e1, e2 = np.array([h, 0.0]), np.array([0.0, h])
    f = lambda q: np.log(landscape(q[..., 0], q[..., 1]))
    return np.stack([(f(z + e1) - f(z - e1)) / (2 * h), (f(z + e2) - f(z - e2)) / (2 * h)], axis=-1)


def climb(z0, rng, drift=DRIFT, steps=T):
    """Mean traits over the generations: z <- z + G grad ln w + drift, kept inside the domain. z0 may be (n, 2)."""
    z = np.array(z0, float); path = [z.copy()]
    for _ in range(steps):
        z = np.clip(z + G * grad_ln(z) + (rng.normal(0, drift, z.shape) if drift else 0), LO, HI); path.append(z.copy())
    return np.array(path)


# ---- the landscape's features, found numerically from the shared function
w_at = lambda p: float(landscape(*p))
p_high = minimize(lambda p: -w_at(p), (0.9, 0.7)).x
p_low = minimize(lambda p: -w_at(p), (-0.8, -0.9)).x
p_saddle = root(lambda p: grad_ln(p), (p_high + p_low) / 2).x
mid = (p_high + p_low) / 2; perp = np.array([-(p_high - p_low)[1], (p_high - p_low)[0]]); perp /= np.hypot(*perp)

# ---- four populations, in slot order; the third starts exactly as far from one peak as from the other
STARTS = [("near the higher peak", (1.8, 1.9)), ("near the lower peak", (-1.8, -1.8)),
          ("equidistant from both", tuple(mid + 2.3 * perp)), ("on the saddle", tuple(p_saddle))]
paths = [climb(z0, np.random.default_rng([SEED, k])) for k, (_, z0) in enumerate(STARTS)]
fits = [landscape(p[:, 0], p[:, 1]) for p in paths]
gens = np.arange(T + 1)
final = [float(np.mean(f[-30:])) for f in fits]                       # the plateau: mean of the last 30 generations
t95 = [int(np.argmax(f >= 0.95 * fin)) for f, fin in zip(fits, final)]       # generations to 95 % of the plateau
wait = int(np.argmax(fits[3] > w_at(p_saddle) + 0.05))                 # generations the saddle start stays within 0.05 of it
on_low = [np.hypot(*(p[-1] - p_low)) < np.hypot(*(p[-1] - p_high)) for p in paths]
assert on_low[:3] == [False, True, True], "frames 3 to 5 claim where the first three populations end"

# ---- the ensemble behind the stat tile: random starts over the whole domain, one drift seed
rng = np.random.default_rng([SEED, 99])
ens = climb(rng.uniform(LO, HI, (N_STARTS, 2)), rng)[-1]
low_share = float(np.mean(np.hypot(*(ens - p_low).T) < np.hypot(*(ens - p_high).T)))
assert low_share > 0.5, "the talk claims that most random starts end on the lower peak"

# ---- the deterministic basins on a grid, for the boundary drawn on the twin
g = np.linspace(LO, HI, 161); B1, B2 = np.meshgrid(g, g)
flow = climb(np.stack([B1, B2], -1), None, drift=0, steps=600)[-1]
basin = (np.hypot(flow[..., 0] - p_low[0], flow[..., 1] - p_low[1]) < 0.3).astype(float)       # 1 in the lower peak's basin

S = np.linspace(LO, HI, 90); Z1, Z2 = np.meshgrid(S, S); W = landscape(Z1, Z2); WMAX = float(W.max())
WBAR = r"mean fitness $\bar{w}$"
NOTE = f"illustrative simulation, seed {SEED}\n" + r"step $G\,\nabla\ln\bar{w}$" + f" with $G$ = {G}, drift sd {DRIFT}"


def draw_reveal(V, k):
    """Mean fitness against generation for the first k populations; axes and label places fixed for every step."""
    fig, ax = plt.subplots(figsize=V.size("slide")); fig.subplots_adjust(left=0.07, right=0.72, top=0.87, bottom=0.17)
    ax.set_xlim(0, T); ax.set_ylim(0, 1.05); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
    ends = [f[-1] for f in fits]; ys = list(ends)   # label places fixed from all four; a later label steps below one it would hit
    for j in range(4):
        for i in range(j):
            if abs(ys[j] - ys[i]) < 0.085: ys[j] = ys[i] - 0.085
    ax.tick_params(axis="x", pad=4 * V.scale); ax.tick_params(axis="y", pad=2 * V.scale)    # the rc pads are print size
    for j in range(k):
        ax.plot(gens, fits[j], color=V.tone(j), zorder=3)
        V.dot(ax, T, ends[j], V.tone(j))
        leader = dict(arrowstyle="-", color=V.muted, lw=0.5 * V.scale, shrinkA=2 * V.scale, shrinkB=3 * V.scale,
                      relpos=(0, 0.5)) if ys[j] != ends[j] else None             # from the label's left edge, clear of the label above
        ax.annotate(STARTS[j][0], (T, ends[j]), xytext=(T * 1.05, ys[j]), textcoords="data", va="center", ha="left",
                    fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False, arrowprops=leader)   # a leader only when pushed
    if k == 4: V.reference(ax, y=w_at(p_saddle), text=f"saddle {w_at(p_saddle):.2f}", color=V.rule)
    V.note(ax, T, 0.04, NOTE, ha="right", va="bottom")
    ax.set_xlabel("generation"); V.panel(ax, unit=WBAR)
    return fig


def draw_surface(V, azim):
    """The landscape as a flat-shaded surface coloured by height (lagoon), orthographic, elevation 24."""
    fig = plt.figure(figsize=V.size("slide_half"))
    ax = V.axes3d(fig, rect=(0.03, 0.05, 0.80, 0.90), azim=azim, labels=("trait $z_1$", "trait $z_2$", WBAR))
    V.surface3d(ax, Z1, Z2, W, cmap=V.cmap_gradient("lagoon"), vmin=0, vmax=WMAX)
    ax.set_xticks([-1, 0, 1]); ax.set_yticks([-1, 0, 1]); ax.set_zticks([0, 0.5, 1])
    ax.zaxis.set_major_formatter(lambda v, _: f"{v:g}")
    ax.xaxis.labelpad = ax.yaxis.labelpad = 4 * V.scale; ax.zaxis.labelpad = 3 * V.scale   # the module's pads are for print size
    ax.set_box_aspect((1, 1, 0.62), zoom=1.05)                                               # fill the half slide
    return fig


def draw_twin(V):
    """The heat-map twin: same gradient and limits, contours, the basin boundary, the four paths and the two peaks."""
    fig, ax = plt.subplots(figsize=V.size("slide_half")); fig.subplots_adjust(left=0.13, right=0.86, top=0.90, bottom=0.14)
    im = ax.imshow(W, origin="lower", extent=[LO, HI, LO, HI], cmap=V.cmap_gradient("lagoon"), vmin=0, vmax=WMAX)
    ax.contour(Z1, Z2, W, levels=7, colors=V.surface, linewidths=0.5 * V.scale, alpha=0.8)
    ax.contour(B1, B2, basin, levels=[0.5], colors=V.ink, linewidths=V.thin, linestyles=[V.dotted])
    halo = [pe.Stroke(linewidth=V.lw + 2 * V.scale, foreground=V.surface), pe.Normal()]   # the surface ring, for a line on a map
    for j, p in enumerate(paths):
        ax.plot(p[:, 0], p[:, 1], color=V.tone(j), lw=V.lw * 0.7, path_effects=halo, zorder=3)
        V.dot(ax, p[0, 0], p[0, 1], V.tone(j), z=5)
    ring = [pe.withStroke(linewidth=2.5 * V.scale, foreground=V.surface)]
    for p in (p_high, p_low):                       # the peaks: a cross and the height, to the right where no path runs
        ax.scatter(*p, s=60 * V.scale ** 2, marker="+", color=V.ink, linewidths=V.thin * 1.4, zorder=6)
        ax.annotate(f"{w_at(p):.2f}", p, xytext=(9 * V.scale, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=V.sz["annotation"], color=V.ink, zorder=6, path_effects=ring)
    ax.text(HI - 0.05, LO + 0.08, "basin boundary", ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.ink, path_effects=ring)
    ax.set_xticks([-2, -1, 0, 1, 2]); ax.set_yticks([-2, -1, 0, 1, 2]); ax.grid(False)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xlabel("trait $z_1$"); V.panel(ax, unit="trait $z_2$")
    cb = V.gradient_bar(fig, im, ax, WBAR, ticks=[0, 0.5, 1])
    cb.ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}"); cb.ax.tick_params(labelsize=18)   # legend ticks 18 pt on a slide (1329.08)
    ax.tick_params(axis="x", pad=4 * V.scale); ax.tick_params(axis="y", pad=2 * V.scale)
    return fig


def numbers_tex():
    """The macros the slides use, so no number in talk.tex is typed by hand."""
    f2 = lambda v: f"{v:.2f}".replace("-", "−")
    pt = lambda p: f"({f2(p[0])}, {f2(p[1])})"
    m = dict(Gstep=G, Drift=DRIFT, Gens=T, Nstarts=N_STARTS, LowShare=round(100 * low_share), BasinShare=round(100 * basin.mean()),
             HighPeak=f2(w_at(p_high)), HighPeakAt=pt(p_high), LowPeak=f2(w_at(p_low)), LowPeakAt=pt(p_low),
             Saddle=f2(w_at(p_saddle)), SaddleAt=pt(p_saddle), PeakGap=f2(w_at(p_high) - w_at(p_low)),
             ClimbA=t95[0], EndB=f2(final[1]), WaitD=wait,
             AzimA=str(VIEWS["a"]).replace("-", "−"), AzimB=str(VIEWS["b"]).replace("-", "−"), Stamp=stamp())
    return "% written by make_talk_figures.py; do not edit\n" + "".join(f"\\newcommand\\v{k}{{{v}}}\n" for k, v in m.items())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    V = vellum.use("dark", scale=2.2)                  # one twin per deck: dark, for a hall with the lights down
    reveal = [draw_reveal(V, k) for k in range(1, 5)]
    box = reveal[-1].get_tightbbox().padded(0.08)          # one crop for the four steps, so the axes never move on the slide
    for k, fig in enumerate(reveal, 1):
        fig.savefig(os.path.join(OUT, f"reveal_{k}.pdf"), bbox_inches=box); plt.close(fig)
    figs = {f"surface_{v}": draw_surface(V, az) for v, az in VIEWS.items()}; figs["twin"] = draw_twin(V)
    for name, fig in figs.items():
        fig.savefig(os.path.join(OUT, name + ".pdf")); plt.close(fig)
    open(os.path.join(OUT, "numbers.tex"), "w", encoding="utf-8").write(numbers_tex())
