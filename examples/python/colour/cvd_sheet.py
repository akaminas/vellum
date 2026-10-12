"""cvd_sheet.py: the six Vellum tones and a four-series line chart seen four ways.

Columns: normal vision, protanopia, deuteranopia (Machado, Oliveira and Fernandes 2009, severity 1, applied in linear
RGB by generators/colorlab.py) and greyscale (the grey of equal relative luminance). Under each column, the smallest
OKLab distance (x100) between neighbouring slots as that viewer sees them. The chart is period life expectancy in four
countries (Our World in Data), chosen because the lines cross.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.join(REPO, "generators"))
import colorlab as CL
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: UN WPP (2024) and others, processed by Our World in Data (CC BY 4.0); simulation: generators/colorlab.py"
W, H = 7.2, 4.35
COUNTRIES = ("China", "Russia", "Brazil", "India")
ROWS = load_csv("owid-life-expectancy.csv")
SERIES = {c: np.array(sorted((int(x["Year"]), float(x["Life expectancy"])) for x in ROWS if x["Entity"] == c and int(x["Year"]) >= 1950))
          for c in COUNTRIES}
VIEWS = (("Normal vision", None), ("Protanopia", CL.PROT), ("Deuteranopia", CL.DEUT), ("Greyscale", "grey"))


def seen(h, how):
    """The colour as the viewer sees it, as a hex for drawing."""
    if how is None: return h
    if isinstance(how, str):
        v = CL.linear_to_srgb(np.array(CL.luminance(h))); return CL.rgb_to_hex([v, v, v])
    return CL.rgb_to_hex(CL.linear_to_srgb(CL.simulate(h, how)))


def smallest(V, how):
    """Smallest distance between neighbouring tones as seen (simulated in linear RGB, distance in OKLab x 100)."""
    T = V.tones()
    if how is None or isinstance(how, str):
        return min(CL.de(seen(a, how), seen(b, how)) for a, b in zip(T[:-1], T[1:]))
    return min(CL.de_lin(CL.simulate(a, how), CL.simulate(b, how)) for a, b in zip(T[:-1], T[1:]))


def draw(V):
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off"); ax.set_zorder(-1)
    cw = (7.05 - 0.15) / 4
    for k, (name, how) in enumerate(VIEWS):
        x = 0.15 + k * cw
        ax.text(x, 1.02, name, fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline")
        cols = [seen(t, how) for t in V.tones()]
        sw = (cw - 0.3) / 6
        for i, c in enumerate(cols):                      # the six tones as this viewer sees them
            ax.add_patch(Rectangle((x + i * sw, 1.14), sw - 0.03, 0.3, facecolor=c, edgecolor="none"))
        a = fig.add_axes([(x + 0.22) / W, 1 - 3.35 / H, (cw - 0.8) / W, 1.5 / H])
        pts = []
        for c, country in zip(cols, COUNTRIES):
            s = SERIES[country]; a.plot(s[:, 0], s[:, 1], color=c, lw=V.lw)
            V.dot(a, s[-1, 0], s[-1, 1], c); pts.append(tuple(s[-1]))
        V.endlabels(a, pts, COUNTRIES, gap=4.0, x_text=2031)
        a.set_xlim(1950, 2024); a.set_ylim(30, 85); a.set_yticks([40, 60, 80]); a.set_xticks([1960, 2020])
        a.text(0, 1.04, "life expectancy, years", transform=a.transAxes, fontsize=V.sz["unit_line"], color=V.muted, va="bottom")
        d = smallest(V, how)
        ax.text(x, 3.85, "smallest neighbour distance", fontsize=V.sz["footer"], color=V.muted, va="baseline")
        ax.text(x, 4.05, f"{d:.1f}", fontsize=V.sz["title"], color=V.ink, va="baseline")
        ax.text(x + 0.42, 4.05, ("floor 15" if how is None else "lightness alone" if isinstance(how, str) else "target 8"),
                fontsize=V.sz["footer"], color=V.muted, va="baseline")
    V.title(fig, "The palette survives colour-vision deficiency because lightness alternates",
            f"Six tones and a four-line chart, {V.mode} twin · simulated after Machado, Oliveira and Fernandes (2009), severity 1", footer(SOURCE, __file__))
    return fig


def meta():
    nums = {m: {name: round(smallest(vellum.Vellum(m), how), 1) for name, how in VIEWS} for m in MODES}
    L = nums["light"]
    return dict(
        title="The palette survives colour-vision deficiency because lightness alternates",
        subtitle="The six tones and a four-line chart under normal vision, protanopia, deuteranopia and in greyscale",
        kind="colour", form="colour-vision simulation strip", medium="screen", tool="matplotlib",
        data="Period life expectancy of China, Russia, Brazil and India, UN WPP (2024) and others, processed by Our World in Data; "
             "simulation with generators/colorlab.py (Machado et al. 2009, severity 1)",
        script=rel(__file__),
        alt="Four columns showing the six Vellum tones and the same four-line chart as seen with normal vision, protanopia, deuteranopia "
            f"and in greyscale. The smallest distance between neighbouring tones is {L['Normal vision']} in normal vision, "
            f"{L['Protanopia']} under protanopia, {L['Deuteranopia']} under deuteranopia and {L['Greyscale']} in greyscale.",
        note="Smallest neighbour distance (OKLab × 100): " + "; ".join(f"{m}: " + ", ".join(f"{k.lower()} {v}" for k, v in n.items())
                                                                         for m, n in nums.items()) + ".",
    )


if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "colour", "cvd_sheet", mode, meta=meta() if mode == "light" else None))
