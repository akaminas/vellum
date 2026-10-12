"""gradients_sheet.py: the gradients of Vellum and why they are built the way they are, from style/vellum.json.

a: the three named gradients (lagoon, ember, shore), nine stops each, over their greyscale (the luminance of each stop).
b, c: OKLCH lightness and chroma of every stop of the three, computed with colorlab: lightness moves in equal steps,
chroma is a bell. d: the single-family teal ramp and the diverging scale over their greyscale. e: the teal and
terracotta tones joined directly in OKLab, with the chroma along the join: the middle goes grey.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.join(REPO, "generators"))
import colorlab as CL
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "style/vellum.json, OKLCH and luminance computed with generators/colorlab.py"
W, H = 7.2, 6.25
NAMES = ("lagoon", "ember", "shore")
HUES = {"lagoon": "moss → teal → indigo", "ember": "ochre → terracotta → mauve", "shore": "ochre → moss → teal"}


def grey(h):
    """The grey of the same relative luminance: what the stop looks like with its hue removed."""
    v = CL.linear_to_srgb(np.array(CL.luminance(h))); return CL.rgb_to_hex([v, v, v])


def lch(cols):
    return np.array([CL.hex_to_oklch(c)[:2] for c in cols])


def join(h1, h2, n):
    """n colours from h1 to h2 interpolated in OKLab."""
    a, b = (CL.linear_to_oklab(CL.srgb_to_linear(CL.hex_to_rgb(h))) for h in (h1, h2))
    return [CL.rgb_to_hex(CL.linear_to_srgb(CL.oklab_to_linear((1 - t) * a + t * b))) for t in np.linspace(0, 1, n)]


def numbers(mode):
    V = vellum.Vellum(mode)
    P = {g: lch(V.gradient(g, 9)) for g in NAMES}
    steps = np.concatenate([np.diff(p[:, 0]) for p in P.values()])
    J = join(V.tone("teal"), V.tone("terracotta"), 21)
    return dict(P=P, step=float(np.mean(np.abs(steps))), step_min=float(np.min(np.abs(steps))),
                cmax=float(max(p[:, 1].max() for p in P.values())), cend=float(max(p[[0, -1], 1].max() for p in P.values())),
                J=J, Jc=lch(J)[:, 1], mono=all(np.all(np.diff(np.sign(np.diff(p[:, 0]))) == 0) for p in P.values()))


def strip(ax, cols, x, y, w, h, gap=0.02):
    """Touching cells with a surface gap, in inch coordinates (y downward)."""
    step = w / len(cols)
    for k, c in enumerate(cols):
        ax.add_patch(Rectangle((x + k * step, y), step - gap, h, facecolor=c, edgecolor="none"))


def inch_axes(fig, x, y, w, h):
    """Real axes placed by inches from the top left of the figure."""
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def draw(V):
    N = numbers(V.mode); assert N["mono"]                       # the claim: lightness monotone along every gradient
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    pt = lambda y, s, **kw: ax.text(0.15, y, s, fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline", **kw)
    # a: the three gradients over their greyscale
    pt(1.02, "a  Three gradients over their greyscale: the order survives without the hue")
    for r, g in enumerate(NAMES):
        y = 1.32 + r * 0.66
        cols = V.gradient(g, 9)
        ax.text(0.15, y - 0.06, g, fontsize=V.sz["annotation"], color=V.ink, va="baseline")
        ax.text(0.7, y - 0.06, HUES[g] + " · " + " → ".join(f"{h % 360}°" for h in vellum.SPEC["gradients"][g]["hues"]),
                fontsize=V.sz["footer"], color=V.muted, va="baseline")
        strip(ax, cols, 0.15, y, 4.2, 0.28); strip(ax, [grey(c) for c in cols], 0.15, y + 0.3, 4.2, 0.12)
    ax.text(0.15, 3.28, "upper strip: the nine stops · lower strip: the grey of equal luminance, hue removed", fontsize=V.sz["footer"],
            color=V.muted, va="baseline")
    # b, c: lightness and chroma per stop, the three gradients side by side at each stop, dots in the stop colours
    for (y, key, claim, unit, lim, ticks) in (
            (0.95, 0, f"b  Lightness {'falls' if V.mode == 'light' else 'rises'} {N['step']:.2f} per stop", "OKLCH lightness L", (0.25, 1.0), [0.4, 0.6, 0.8, 1.0]),
            (2.5, 1, f"c  Chroma peaks at {N['cmax']:.3f} mid-way", "OKLCH chroma C", (0, 0.1), [0, 0.05, 0.1])):
        a = inch_axes(fig, 4.85, y + 0.3, 2.15, 0.8)
        a.plot(np.arange(1, 10), np.mean([N["P"][g][:, key] for g in NAMES], axis=0), color=V.rule, lw=V.thin, zorder=2)
        for k, g in enumerate(NAMES):
            x = np.arange(1, 10) + (k - 1) * 0.22
            a.scatter(x, N["P"][g][:, key], s=16, c=V.gradient(g, 9), edgecolor=V.surface, linewidth=0.8, zorder=3)
        a.set_xlim(0.5, 9.5); a.set_ylim(*lim); a.set_yticks(ticks); a.set_xticks([1, 5, 9])
        a.set_title(claim, loc="left", color=V.ink, pad=14)
        a.text(0, 1.04, unit, transform=a.transAxes, fontsize=V.sz["unit_line"], color=V.muted, va="bottom")
    a.set_xlabel("stop, lagoon · ember · shore side by side", fontsize=V.sz["unit_line"])
    # d: one family and the diverging scale
    pt(4.3, "d  One family orders by lightness; the diverging scale orders from its middle")
    for r, (name, cols, note) in enumerate((("teal", V.sequential["teal"], "single-family ramp, seven steps"),
                                            ("diverging", V.diverging, "terracotta to teal through a neutral on the baseline"))):
        y = 4.6 + r * 0.66
        ax.text(0.15, y - 0.06, name, fontsize=V.sz["annotation"], color=V.ink, va="baseline")
        ax.text(0.95, y - 0.06, note, fontsize=V.sz["footer"], color=V.muted, va="baseline")
        strip(ax, cols, 0.15, y, 4.2, 0.28); strip(ax, [grey(c) for c in cols], 0.15, y + 0.3, 4.2, 0.12)
    # e: complements joined directly
    J, Jc = N["J"], N["Jc"]; m = len(J) // 2
    ax.text(4.85, 4.3, "e  Complements joined directly go grey", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink,
            va="baseline")
    ax.text(4.85, 4.48, "the teal and terracotta tones interpolated in OKLab", fontsize=V.sz["footer"], color=V.muted, va="baseline")
    strip(ax, J, 4.85, 4.6, 2.15, 0.28, gap=0)
    a = inch_axes(fig, 4.85, 5.15, 2.15, 0.6)
    a.plot(np.arange(len(J)), Jc, color=V.secondary, lw=V.thin, zorder=2)
    V.dot(a, m, Jc[m], V.secondary, s=22)
    a.annotate(f"middle {J[m]}, C {Jc[m]:.3f}", (m, Jc[m]), xytext=(0, -9), textcoords="offset points", ha="center", va="top",
               fontsize=V.sz["footer"], color=V.ink)
    a.text(0.4, Jc[0] + 0.008, f"C {Jc[0]:.3f}", fontsize=V.sz["footer"], color=V.muted, va="bottom", ha="left")
    a.text(len(J) - 1.4, Jc[-1] + 0.008, f"C {Jc[-1]:.3f}", fontsize=V.sz["footer"], color=V.muted, va="bottom", ha="right")
    a.set_xlim(-0.3, len(J) - 0.7); a.set_ylim(-0.05, 0.115); a.set_yticks([0, 0.04, 0.08]); a.set_xticks([])
    a.text(0, 1.04, "OKLCH chroma C along the join", transform=a.transAxes, fontsize=V.sz["unit_line"], color=V.muted, va="bottom")
    V.title(fig, "Lightness carries the order, hue adds the range",
            f"Vellum gradients, {V.mode} twin · nine stops each, built in OKLCH · greys of equal luminance computed with colorlab", footer(SOURCE, __file__))
    return fig


def meta():
    L, D = numbers("light"), numbers("dark")
    m = len(L["J"]) // 2
    return dict(
        title="Lightness carries the order, hue adds the range",
        subtitle="The three named gradients over their greyscale, their OKLCH lightness and chroma, the teal ramp, the diverging scale "
                 "and the grey middle of two joined complements",
        kind="colour", form="gradient sheet", medium="screen", tool="matplotlib",
        data="style/vellum.json; OKLCH and luminance computed with generators/colorlab.py",
        script=rel(__file__),
        alt=f"Three nine-stop gradients (lagoon, ember, shore) each over a greyscale strip that darkens evenly; lightness falls "
            f"{L['step']:.3f} per stop and chroma rises from {L['cend']:.3f} to {L['cmax']:.3f} and back. Teal joined directly to "
            f"terracotta in OKLab drops to chroma {L['Jc'][m]:.3f} in the middle ({L['J'][m]}).",
        note=f"Light: mean lightness step {L['step']:.3f} (smallest {L['step_min']:.3f}), chroma peak {L['cmax']:.3f}; "
             f"teal–terracotta OKLab middle {L['J'][m]} at C {L['Jc'][m]:.3f} (ends {L['Jc'][0]:.3f}, {L['Jc'][-1]:.3f}). "
             f"Dark: step {D['step']:.3f}, peak {D['cmax']:.3f}, middle {D['J'][m]} at C {D['Jc'][m]:.3f}.",
    )


if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "colour", "gradients", mode, meta=meta() if mode == "light" else None))
