"""lightness_trap.py: the equal-lightness trap of colour theory, step 4.

a: the six Vellum hue angles in slot order rebuilt with colorlab at ONE OKLCH lightness (the mean lightness of the
tones) and chroma 0.085. b: the Vellum tones themselves, whose lightness alternates. Each set colours the same four-line
chart (period life expectancy of four continents, Our World in Data), is shown again in greyscale, and as six swatches over
their greys, with the smallest distance between neighbouring slots computed in colour, in greyscale and under
colour-vision deficiency. The left set is a demonstration and is not part of the palette.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.join(REPO, "generators"))
import colorlab as CL
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: UN WPP (2024) and others, processed by Our World in Data (CC BY 4.0); colours from style/vellum.json and colorlab"
W, H = 7.2, 5.4
HUES = [f["hue"] for f in vellum.SPEC["families"]]
REGIONS = ("Europe", "Americas", "Asia", "Africa")
ROWS = load_csv("owid-life-expectancy.csv")
SERIES = {r: np.array(sorted((int(x["Year"]), float(x["Life expectancy"])) for x in ROWS if x["Entity"] == r and int(x["Year"]) >= 1950))
          for r in REGIONS}


def grey(h):
    v = CL.linear_to_srgb(np.array(CL.luminance(h))); return CL.rgb_to_hex([v, v, v])


def sets(V):
    """The equal-lightness set (same hues, one L, C 0.085) and the Vellum tones, with their neighbour distances."""
    L = float(np.mean([CL.hex_to_oklch(t)[0] for t in V.tones()]))
    eq = [CL.oklch_to_hex(L, 0.085, h) for h in HUES]; assert all(ok for _, ok in eq)    # all six inside sRGB
    out = []
    for cols in ([h for h, _ in eq], V.tones()):
        pairs = list(zip(cols[:-1], cols[1:]))
        out.append(dict(cols=cols, nv=min(CL.de(a, b) for a, b in pairs), grey=min(CL.de(grey(a), grey(b)) for a, b in pairs),
                        cvd=min(CL.de_cvd(a, b) for a, b in pairs), L=[CL.hex_to_oklch(c)[0] for c in cols]))
    return L, out


def inch_axes(fig, x, y, w, h):
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def chart(fig, V, x, y, cols, labels):
    a = inch_axes(fig, x, y, 2.2, 1.0)
    pts = []
    for r, c in zip(REGIONS, cols):
        s = SERIES[r]; a.plot(s[:, 0], s[:, 1], color=c, lw=V.lw)
        V.dot(a, s[-1, 0], s[-1, 1], c); pts.append(tuple(s[-1]))
    if labels: V.endlabels(a, pts, REGIONS, gap=6.5, x_text=2030)
    a.set_xlim(1950, 2024); a.set_ylim(30, 85); a.set_yticks([40, 60, 80]); a.set_xticks([1960, 1990, 2020])
    return a


def draw(V):
    L, (eq, ve) = sets(V)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off"); ax.set_zorder(-1)
    for k, (x, S, claim) in enumerate(((0.15, eq, f"a  Six hues at one lightness, L {L:.2f}, C 0.085"),
                                        (3.75, ve, "b  The Vellum tones, lightness alternating"))):
        ax.text(x, 1.02, claim, fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline")
        a = chart(fig, V, x + 0.3, 1.38, S["cols"][:4], True)
        a.text(0, 1.04, "life expectancy at birth, years", transform=a.transAxes, fontsize=V.sz["unit_line"], color=V.muted, va="bottom")
        ax.text(x, 2.85, "the same chart in greyscale, labels removed", fontsize=V.sz["annotation"], color=V.muted, va="baseline")
        chart(fig, V, x + 0.3, 3.0, [grey(c) for c in S["cols"][:4]], False)
        # the six swatches over their greys, and the numbers
        w = 3.0 / 6
        for i, c in enumerate(S["cols"]):
            ax.add_patch(Rectangle((x + i * w, 4.35), w - 0.03, 0.26, facecolor=c, edgecolor="none"))
            ax.add_patch(Rectangle((x + i * w, 4.63), w - 0.03, 0.1, facecolor=grey(c), edgecolor="none"))
            ax.text(x + i * w, 4.31, f"L {S['L'][i]:.2f}", fontsize=V.sz["footer"], color=V.muted, va="baseline")
        ax.text(x, 4.9, "smallest distance between neighbouring slots", fontsize=V.sz["footer"], color=V.muted, va="baseline")
        ax.text(x, 5.07, f"{S['nv']:.1f} in colour · {S['grey']:.1f} in greyscale · {S['cvd']:.1f} under deficiency",
                fontsize=V.sz["annotation"], color=V.ink, va="baseline")
    V.title(fig, "At equal lightness six muted hues are six greys; alternating lightness separates them",
            f"{V.mode.capitalize()} twin · same six hue angles in slot order · distances in OKLab × 100, floor 15 in colour; "
            "deficiency after Machado et al. (2009)", footer(SOURCE, __file__))
    return fig


def meta():
    out = {m: sets(vellum.Vellum(m)) for m in MODES}
    L, (eq, ve) = out["light"]
    fmt = lambda S: f"{S['nv']:.1f} in colour, {S['grey']:.1f} in greyscale, {S['cvd']:.1f} under deficiency"
    return dict(
        title="At equal lightness six muted hues are six greys; alternating lightness separates them",
        subtitle="Six hues at one OKLCH lightness against the Vellum tones, each colouring the same four-line chart, in colour and in greyscale",
        kind="colour", form="comparison of two colour sets", medium="screen", tool="matplotlib",
        data="Period life expectancy of four continents, UN WPP (2024) and others, processed by Our World in Data; colours from style/vellum.json "
             "and generators/colorlab.py",
        script=rel(__file__),
        alt=f"Two versions of the same four-line chart. Left: the six Vellum hues rebuilt at one lightness (L {L:.2f}, C 0.085); in greyscale "
            f"the lines are the same grey (smallest neighbour distance {eq['grey']:.1f}). Right: the Vellum tones, whose lightness alternates; "
            f"in greyscale the lines stay apart (smallest distance {ve['grey']:.1f}).",
        note=f"Smallest neighbour distance (OKLab × 100), light twin. Equal lightness: {fmt(eq)}. Vellum tones: {fmt(ve)}. "
             f"Dark twin, equal lightness L {out['dark'][0]:.2f}: {fmt(out['dark'][1][0])}; Vellum: {fmt(out['dark'][1][1])}. "
             "The equal-lightness colours are a demonstration, not part of the palette.",
    )


if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "colour", "lightness_trap", mode, meta=meta() if mode == "light" else None))
