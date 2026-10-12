"""palette_sheet.py: the Vellum palette on one sheet per twin, with its checks computed by colorlab.

Neutrals, the six families (tint, tone, deep), the seven-step sequential ramps, the diverging scale and the status set,
every swatch with its hex, all read from style/vellum.json. The checks are recomputed here, not copied: OKLab distance
(x100) between neighbouring tones in normal vision and under protanopia and deuteranopia (Machado et al. 2009,
severity 1), and the WCAG contrast of each tone against the surface. Text on a swatch is in ink or in the surface colour,
whichever reaches the higher contrast; where neither reaches 4.5:1 the hex sits on a card-coloured chip.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.join(REPO, "generators"))
import colorlab as CL
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "style/vellum.json, checks computed with generators/colorlab.py"
W, H = 7.2, 9.15                     # inches; the sheet is drawn in inch coordinates, y downward
X0, X1 = 0.15, 7.05


def checks(V):
    T = V.tones()
    nv = [CL.de(T[i], T[i + 1]) for i in range(5)]
    cvd = [CL.de_cvd(T[i], T[i + 1]) for i in range(5)]
    con = [CL.contrast(t, V.surface) for t in T]
    return nv, cvd, con


def swatch(ax, V, x, y, w, h, col, lines, size=None, edge=False):
    """A swatch with its text in ink or surface (the higher contrast), or on a card chip when neither reaches 4.5:1."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=col, edgecolor=V.grid if edge else "none", lw=0.5))
    c_ink, c_sur = CL.contrast(col, V.ink), CL.contrast(col, V.surface)
    fg = V.ink if c_ink >= c_sur else V.surface
    chip = max(c_ink, c_sur) < 4.5
    ax.text(x + 0.06, y + h - 0.05, "\n".join(lines), fontsize=size or V.sz["footer"], color=V.ink if chip else fg, va="bottom",
            ha="left", linespacing=1.15,
            bbox=dict(boxstyle="round,pad=0.18,rounding_size=0.1", fc=V.card, ec="none") if chip else None)
    return chip


def header(ax, V, y, text, note=None):
    ax.text(X0, y, text, fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="baseline")
    if note: ax.text(X1, y, note, fontsize=V.sz["annotation"], color=V.muted, va="baseline", ha="right")


def draw(V):
    nv, cvd, con = checks(V)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    chips = 0
    # neutrals
    header(ax, V, 1.0, "Neutrals", "warm greys on hue 80; the surface is the page")
    names = ("surface", "card", "grid", "rule", "muted", "secondary", "ink")
    w = (X1 - X0 - 6 * 0.08) / 7
    for k, n in enumerate(names):
        col = getattr(V, n)
        chips += swatch(ax, V, X0 + k * (w + 0.08), 1.1, w, 0.46, col, [n, col], size=V.sz["footer"], edge=n == "surface")
    # the six families: tint, tone, deep
    header(ax, V, 1.95, "Six families in slot order: tint, tone, deep", "tint for areas, tone for marks, deep for emphasis and text on a tint")
    w = (X1 - X0 - 5 * 0.16) / 6
    for k, fam in enumerate(V.names):
        x = X0 + k * (w + 0.16)
        hue = vellum.SPEC["families"][k]["hue"]
        ax.text(x, 2.17, f"{k + 1}  {fam}", fontsize=V.sz["annotation"], color=V.ink, va="baseline")
        ax.text(x + w, 2.17, f"{hue}°", fontsize=V.sz["footer"], color=V.muted, va="baseline", ha="right")
        for row, (role, col) in enumerate((("tint", V.tint(k)), ("tone", V.tone(k)), ("deep", V.deep(k)))):
            chips += swatch(ax, V, x, 2.25 + row * 0.42, w, 0.38, col, [role, col])
        ax.text(x, 3.62, f"{con[k]:.2f}:1 on the surface", fontsize=V.sz["footer"], color=V.muted, va="baseline")
        if k < 5:                     # the distance to the next slot, between the two columns
            ax.text(x + w + 0.08, 3.86, f"ΔE {nv[k]:.1f} · {cvd[k]:.1f}", fontsize=V.sz["footer"], color=V.ink, va="baseline", ha="center")
    ax.text(X0, 4.06, "between columns: distance to the next slot in OKLab × 100, in normal vision · under the worse of protanopia "
                      "and deuteranopia (Machado 2009, severity 1)", fontsize=V.sz["footer"], color=V.muted, va="baseline")
    # sequential ramps
    header(ax, V, 4.42, "Sequential ramps, seven steps", "magnitude only; " + ("lightness falls" if V.mode == "light" else "lightness rises") + " step by step")
    lw_ = 0.78; w = (X1 - X0 - lw_) / 7
    for r, fam in enumerate(V.names):
        y = 4.52 + r * 0.25
        ax.text(X0, y + 0.15, fam, fontsize=V.sz["annotation"], color=V.ink, va="center")
        for k, col in enumerate(V.sequential[fam]):
            ax.add_patch(Rectangle((X0 + lw_ + k * w, y), w - 0.025, 0.225, facecolor=col, edgecolor="none"))   # surface gap between steps
            c_ink, c_sur = CL.contrast(col, V.ink), CL.contrast(col, V.surface)
            chip = max(c_ink, c_sur) < 4.5; chips += chip
            ax.text(X0 + lw_ + k * w + 0.05, y + 0.115, col, fontsize=V.sz["footer"], va="center", ha="left",
                    color=V.ink if chip or c_ink >= c_sur else V.surface,
                    bbox=dict(boxstyle="round,pad=0.12,rounding_size=0.08", fc=V.card, ec="none") if chip else None)
    # diverging
    header(ax, V, 6.25, "Diverging, terracotta to teal through a neutral", "polarity only; the neutral sits on the baseline")
    w = (X1 - X0) / 11
    for k, col in enumerate(V.diverging):
        ax.add_patch(Rectangle((X0 + k * w, 6.35), w - 0.025, 0.3, facecolor=col, edgecolor="none"))
        ax.text(X0 + k * w + w / 2 - 0.0125, 6.78, col, fontsize=V.sz["footer"], color=V.muted, ha="center", va="baseline")
    ax.text(X0 + 5.5 * w, 6.95, "baseline", fontsize=V.sz["footer"], color=V.ink, ha="center", va="baseline")
    ax.text(X0, 6.95, "below", fontsize=V.sz["footer"], color=V.ink, va="baseline")
    ax.text(X1, 6.95, "above", fontsize=V.sz["footer"], color=V.ink, va="baseline", ha="right")
    # status
    header(ax, V, 7.3, "Status")
    w = 0.95
    for k, (n, col) in enumerate(V.status.items()):
        chips += swatch(ax, V, X0 + k * (w + 0.08), 7.4, w, 0.36, col, [n, col])
    ax.text(X0 + 4 * (w + 0.08) + 0.1, 7.6, "reserved, always with an icon and a label;\nsaturated on purpose and never a series colour",
            fontsize=V.sz["annotation"], color=V.muted, va="center")
    # the checks, as three tiles on the card
    header(ax, V, 8.12, "Checks, computed from the hex values", "a hex on a cream chip: neither ink nor the surface reaches 4.5:1 on that swatch")
    tiles = ((f"{min(nv):.1f}", "smallest distance between\nneighbouring tones", "floor 15"),
             (f"{min(cvd):.1f}", "the same under protanopia\nor deuteranopia", "target 8"),
             (f"{min(con):.2f}:1", "lowest contrast of a tone\non the surface", "floor 3:1"))
    w = (X1 - X0 - 2 * 0.12) / 3
    for k, (num, what, floor) in enumerate(tiles):
        x = X0 + k * (w + 0.12)
        ax.add_patch(Rectangle((x, 8.22), w, 0.56, facecolor=V.card, edgecolor="none"))
        ax.text(x + 0.12, 8.5, num, fontsize=V.sz["title"], color=V.ink, va="center")
        ax.text(x + 0.85, 8.42, what, fontsize=V.sz["footer"], color=V.ink, va="center", linespacing=1.2)
        ax.text(x + 0.85, 8.64, floor, fontsize=V.sz["footer"], color=V.muted, va="center")
    V.title(fig, f"Neighbouring tones differ by {int(min(nv))} or more, by {int(min(cvd))} or more under colour-vision deficiency",
            f"Vellum, {V.mode} twin · distances in OKLab × 100; deficiency simulated after Machado, Oliveira and Fernandes (2009), severity 1",
            footer(SOURCE, __file__))
    return fig


def meta():
    out = {}
    for mode in MODES:
        nv, cvd, con = checks(vellum.Vellum(mode))
        out[mode] = dict(min_adjacent_dE=round(min(nv), 1), min_adjacent_dE_cvd=round(min(cvd), 1), min_contrast=round(min(con), 2),
                         adjacent_dE=[round(v, 1) for v in nv], adjacent_dE_cvd=[round(v, 1) for v in cvd], contrast=[round(v, 2) for v in con])
    L = out["light"]
    return dict(
        title=f"Neighbouring tones differ by {int(L['min_adjacent_dE'])} or more, by {int(L['min_adjacent_dE_cvd'])} or more under colour-vision deficiency",
        subtitle="The Vellum palette: neutrals, six families, sequential ramps, diverging scale and status, with computed checks",
        kind="colour", form="palette sheet", medium="screen", tool="matplotlib",
        data="style/vellum.json; checks computed with generators/colorlab.py (OKLab, Machado et al. 2009, WCAG 2)",
        script=rel(__file__),
        alt=f"A palette sheet: seven warm neutrals, six hue families in tint, tone and deep steps, six seven-step ramps, an eleven-step "
            f"diverging scale and four status colours, each with its hex. Neighbouring tones differ by at least {L['min_adjacent_dE']} in OKLab "
            f"(×100), {L['min_adjacent_dE_cvd']} under protanopia or deuteranopia, and every tone reaches {L['min_contrast']}:1 on white.",
        note="Checks recomputed from the hex values by the script. " +
             "; ".join(f"{m}: smallest adjacent ΔE {o['min_adjacent_dE']}, under CVD {o['min_adjacent_dE_cvd']}, lowest contrast {o['min_contrast']}:1"
                       for m, o in out.items()),
        checks=out,
    )


if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "colour", "palette", mode, meta=meta() if mode == "light" else None))
