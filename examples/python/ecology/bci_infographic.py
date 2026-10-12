"""bci_infographic.py: "The forest in numbers", a portrait infographic (1080 × 1920, drawn at 2×) on the Barro Colorado
Island 50-ha plot, in matplotlib.

Sections: kicker and headline; the hero number (trees counted); three stat tiles; a 100-cell waffle of who owns the
trees (one cell = 1 % of stems, the 15 species that hold half in terracotta); the long tail of all 225 species by
abundance with the singletons in indigo; the 50 hectares as a grid of species counts; the accumulation curve with the
estimates of the species not yet found; sources. Every number is computed from data/ecology/bci_*.csv.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco import *
from matplotlib.patches import FancyBboxPatch, Rectangle

C = table("bci_counts.csv"); P = table("bci_plots.csv"); SA = table("bci_specaccum.csv"); POOL = table("bci_specpool.csv")
SP = [k for k in C if k != "plot"]; M = np.array([C[k] for k in SP]).T
TOT = M.sum(0); NSTEM = int(TOT.sum()); NSP = len(SP)
ORDER = np.argsort(-TOT, kind="stable"); SHARE = TOT[ORDER] / NSTEM; CUM = np.cumsum(SHARE)
HALF = int(np.searchsorted(CUM, 0.5) + 1); NSING = int((TOT == 1).sum()); OCC = (M > 0).sum(0); EVERY = int((OCC == 50).sum())
RICH = P["richness"]; CHAO, JACK = POOL["chao"][0], POOL["jack1"][0]
name = lambda i: SP[i].replace(".", " ")
assert HALF == 15 and NSING == 19 and NSTEM == 21457 and EVERY == 7

W, H = 7.2, 12.8
SRC = ("Data: Condit et al. (2002) Science 295, 666–669; Barro Colorado Island 50-ha plot, 1982 census, trees ≥ 10 cm dbh; "
       "via R vegan::BCI")
fmt = lambda n: f"{n:,}".replace(",", " ")


def fig_text(V, fig, x, y, s, size, color=None, family=None, **kw):
    """Text placed in inches from the top left."""
    return fig.text(x / W, 1 - y / H, s, fontsize=size, color=color or V.ink, fontfamily=family or plt.rcParams["font.family"],
                    va=kw.pop("va", "top"), ha=kw.pop("ha", "left"), **kw)


def section(V, fig, y, kicker, head):
    fig.add_artist(plt.Line2D([0.45 / W, (W - 0.45) / W], [1 - y / H] * 2, color=V.rule, lw=0.6))
    fig_text(V, fig, 0.45, y + 0.16, kicker.upper(), 8.5, V.muted, fontweight="bold")
    fig_text(V, fig, 0.45, y + 0.40, head, 17, V.ink, V.title_font)


def tile(V, fig, x, y, w, h, value, label, hi=False):
    ax = axes_in(fig, x, y, w, h); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06", transform=ax.transAxes,
                                facecolor=V.card, edgecolor="none", mutation_aspect=w / h))
    ax.text(0.09, 0.80, value, fontsize=34, fontfamily=V.title_font, va="top",
            color=V.tone("terracotta") if hi else V.ink)
    ax.text(0.09, 0.30, label, fontsize=10, color=V.secondary, va="center", linespacing=1.15)


def waffle(V, fig, y):
    """100 cells, one per cent of the stems, filled species by species from the commonest; the 15 that hold half in
    terracotta (alternating tone and deep so neighbours separate), everyone else in rule grey."""
    ax = axes_in(fig, 0.45, y, 6.3, 1.03); ax.axis("off")
    cells = np.round(CUM * 100).astype(int); owner = np.searchsorted(cells, np.arange(1, 101), side="left")
    for k in range(100):
        r, c = k // 25, k % 25
        sp = owner[k]
        col = (V.tone("terracotta") if sp % 2 == 0 else V.deep("terracotta") if V.mode == "light" else V.tint("terracotta")) \
            if sp < HALF else V.grid
        ax.add_patch(Rectangle((c, 3 - r), 0.88, 0.88, facecolor=col, edgecolor="none"))
    ax.set_xlim(-0.05, 25); ax.set_ylim(-0.1, 4); ax.set_aspect("equal")
    # the three commonest named under the grid
    lab = []
    for j in range(3):
        k0 = int(np.where(owner == j)[0][0]); lab.append((k0, j))
    x0 = 0.45
    fig_text(V, fig, 0.45, y + 1.12, "one square = 1 % of all trees", 9.5, V.muted)
    names = "  ·  ".join(f"{name(ORDER[j])} {SHARE[j] * 100:.0f} %" for j in range(3))
    fig_text(V, fig, 0.45, y + 1.34, f"commonest: {names}", 9.5, V.secondary, fontstyle="italic")
    fig_text(V, fig, W - 0.45, y + 1.12, f"{HALF} species in terracotta", 9.5, V.tone("terracotta") if V.mode == "dark" else V.deep("terracotta"),
             ha="right", fontweight="bold")


def tail(V, fig, y):
    ax = axes_in(fig, 0.75, y, 6.0, 1.22)
    ab = TOT[ORDER]; x = np.arange(1, NSP + 1)
    col = [V.tone("terracotta") if i < HALF else V.tone("indigo") if ab[i] == 1 else V.rule for i in range(NSP)]
    ax.bar(x, ab, width=0.8, color=col, edgecolor="none")
    ax.set_yscale("log"); ax.set_ylim(0.6, 3000); ax.set_xlim(0, NSP + 1)
    ax.set_yticks([1, 10, 100, 1000]); ax.set_yticklabels(["1", "10", "100", "1 000"]); ax.minorticks_off()
    ax.set_xticks([1, 50, 100, 150, 200, 225]); ax.tick_params(labelsize=9)
    for s in ax.spines.values(): s.set_visible(False)
    ax.text(0, 1.05, "trees per species, log scale", transform=ax.transAxes, fontsize=9, color=V.muted)
    ax.annotate(f"{NSING} species: one tree each", (NSP - NSING / 2, 1), xytext=(-6, 34), textcoords="offset points",
                ha="right", va="bottom", fontsize=10, color=V.ink, arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.6, shrinkB=6),
                path_effects=halo(V))
    ax.annotate(f"Faramea occidentalis: {fmt(int(ab[0]))}", (1, ab[0]), xytext=(10, 0), textcoords="offset points", ha="left",
                va="center", fontsize=10, color=V.ink, fontstyle="italic", path_effects=halo(V))
    fig_text(V, fig, 0.75, y + 1.47, "species, from commonest to rarest", 9, V.muted)


def grid_map(V, fig, y):
    ax = axes_in(fig, 0.45, y, 3.3, 1.65)
    Z = np.full((5, 10), np.nan)
    for k in range(50): Z[int(P["row"][k]), int(P["col"][k])] = RICH[k]
    cm = V.cmap_gradient("lagoon")
    ax.imshow(Z, origin="lower", cmap=cm, vmin=72, vmax=112, aspect="equal")
    V.heat_gaps(ax, 10, 5)
    for r in range(5):
        for c in range(10):
            rgb = cm((Z[r, c] - 72) / 40)[:3]; lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            ax.text(c, r, f"{Z[r, c]:.0f}", ha="center", va="center", fontsize=8.5, color="#FFFFFF" if lum < 0.45 else "#2A2825")
    ax.set_xticks([]); ax.set_yticks([])
    fig_text(V, fig, 0.45, y + 1.72, "1 000 m × 500 m · species in each hectare; the colour repeats the number", 9, V.muted)


def accumulation(V, fig, y):
    ax = axes_in(fig, 4.55, y + 0.12, 2.15, 1.30)
    ax.fill_between(SA["plots"], SA["lo"], SA["hi"], color=V.tint("teal"), alpha=0.7, lw=0)
    ax.plot(SA["plots"], SA["richness"], color=V.tone("teal"), lw=2.0)
    for v, lab, va in ((CHAO, "Chao1", "top"), (JACK, "jackknife", "bottom")):
        ax.axhline(v, color=V.tone("ochre"), lw=0.9, ls=V.dotted)
        ax.text(1, v + (-3 if va == "top" else 3), f"{lab} {v:.0f}", fontsize=8.5, color=V.secondary, va=va)
    V.dot(ax, 50, NSP, V.tone("teal"), s=30)
    ax.set_xlim(0, 52); ax.set_ylim(80, 272); ax.set_xticks([1, 25, 50]); ax.set_yticks([100, 150, 200, 250])
    ax.tick_params(labelsize=9)
    ax.set_xlabel("hectares searched", fontsize=9)
    ax.text(0, 1.05, "species found", transform=ax.transAxes, fontsize=9, color=V.muted)


def draw(V):
    fig = plt.figure(figsize=(W, H))
    fig_text(V, fig, 0.45, 0.45, "BARRO COLORADO ISLAND · PANAMA · 50-HECTARE FOREST PLOT", 9, V.muted, fontweight="bold")
    fig_text(V, fig, 0.45, 0.72, "The forest in numbers", 34, V.ink, V.title_font)
    fig_text(V, fig, 0.45, 1.42, "Every tree at least 10 cm across was tagged, measured and named in a 1 km × 500 m rectangle\n"
                                 "of old tropical forest. A few species dominate it; most are rare.", 11, V.secondary, linespacing=1.35)
    # hero
    fig_text(V, fig, 0.40, 1.98, fmt(NSTEM), 80, V.ink, V.title_font)
    fig_text(V, fig, 4.25, 2.28, f"trees counted, of\n{NSP} species, in 50\none-hectare plots", 13, V.secondary, linespacing=1.3)
    # tiles
    tw = (W - 0.9 - 2 * 0.2) / 3
    for j, (v, l, hi) in enumerate(((f"{HALF}", "species hold half\nof all the trees", True),
                                    (f"{NSING}", "species were found\nonly once", False),
                                    (f"{EVERY}", "species grow in\nevery hectare", False))):
        tile(V, fig, 0.45 + j * (tw + 0.2), 3.40, tw, 1.10, v, l, hi)
    section(V, fig, 4.80, "1 · Who owns the forest", f"Half of all trees belong to just {HALF} species")
    waffle(V, fig, 5.55)
    section(V, fig, 7.30, "2 · The long tail", f"The other {NSP - HALF} species share the rest")
    tail(V, fig, 8.28)
    section(V, fig, 9.92, "3 · Place and search", f"{int(RICH.min())} to {int(RICH.max())} species a hectare, and more to find")
    grid_map(V, fig, 10.62)
    accumulation(V, fig, 10.62)
    fig_text(V, fig, 0.45, 12.50, SRC, 7.5, V.muted)
    fig_text(V, fig, 0.45, 12.64, f"{os.path.basename(__file__)} · git {stamp()} · Vellum", 7.5, V.muted)
    return fig


META = dict(title=f"The forest in numbers: {HALF} of {NSP} species hold half of Barro Colorado's {fmt(NSTEM)} trees",
            subtitle="Portrait infographic, 1080 × 1920: hero number, three tiles, waffle, long tail, grid map, accumulation",
            kind="composite", form="infographic: hero number, stat tiles, waffle, bar chart, grid map, accumulation curve",
            medium="infographic", tool="matplotlib",
            data="Barro Colorado Island 50-ha plot, 1982 census, Condit et al. (2002), via R vegan::BCI", script=rel(__file__),
            alt=(f"A portrait infographic about the Barro Colorado Island forest plot: {fmt(NSTEM)} trees of {NSP} species in 50 "
                 f"hectares. {HALF} species hold half of the trees, {NSING} species were found once, {EVERY} grow in every hectare. "
                 f"A waffle shows the share of the commonest species, a bar chart the long tail of rare species, a grid map "
                 f"{int(RICH.min())} to {int(RICH.max())} species per hectare, and an accumulation curve that reaches {NSP} with "
                 f"estimates of {CHAO:.0f} to {JACK:.0f} species in all."))

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        plt.rcParams["savefig.bbox"] = "standard"                     # the exact page, 1080 x 1920 at 150 dpi, 2x here
        print(save(draw(V), "ecology", "bci_infographic", mode, meta=META if mode == "light" else None, dpi=300))
