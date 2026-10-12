"""mite_metacommunity.py: oribatid mites of a Sphagnum bog (70 cores, 35 species) as a five-panel composite.

a  the 10 × 2.6 m plot twice: water content of each core, and the community type of each core (Ward clustering of the
   Hellinger-transformed counts, four groups numbered I–IV by rising mean water content)
b  NMDS of Bray–Curtis dissimilarities with the cores coloured by community, convex hulls, the fitted water-content and
   substrate-density vectors and the centroids of topography and shrub cover (vegan envfit, 999 permutations)
c  variation partitioning (Borcard, Legendre and Drapeau 1992) as an area-proportional Euler diagram in a unit square:
   environment (5 variables) and space (8 forward-selected PCNM eigenfunctions), adjusted R²
d  the community table: 35 species by 70 cores, cores ordered by water content, species by their weighted-average
   water optimum, abundance as a share of each species' maximum; the water content and community of each core above
e  negative-binomial GAMs of four species against water content (mgcv, REML), points coloured by community

Data: data/ecology/mite_*.csv, from vegan::mite, mite.env and mite.xy (Borcard and Legendre 1994), and the analyses
in export_data.R.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco import *
from matplotlib.patches import Circle, Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap
from scipy.optimize import brentq
from scipy.spatial import ConvexHull

SOURCE = "Data: oribatid mites of Lac Geai bog, Québec, 70 cores (Borcard and Legendre 1994), via R vegan::mite, mite.env, mite.xy"
CNT = table("mite_counts.csv"); ENV = table("mite_env.csv"); NM = table("mite_nmds_sites.csv"); NSPS = table("mite_nmds_species.csv")
VEC = table("mite_envfit_vectors.csv"); CEN = table("mite_envfit_centroids.csv"); FAC = table("mite_envfit_factors.csv")
FIT = table("mite_nmds_fit.csv"); VP = table("mite_varpart.csv"); SEL = table("mite_selected.csv")
GC = table("mite_gam_curves.csv"); GS = table("mite_gam_species.csv")
SPP = [k for k in CNT if k != "core"]; M = np.array([CNT[k] for k in SPP]).T                # 70 cores x 35 species
W = ENV["WatrCont"]; CL = NM["cluster"].astype(int); NCL = 4; ROMAN = ["I", "II", "III", "IV"]
FR = dict(zip(VP["fraction"], VP["adj_r2"])); FP = dict(zip(VP["fraction"], VP["p"]))
R2V = dict(zip(VEC["variable"], VEC["r2"])); PV = dict(zip(VEC["variable"], VEC["p"]))
R2F = dict(zip(FAC["factor"], FAC["r2"])); PF = dict(zip(FAC["factor"], FAC["p"]))
N_SPACE = int((SEL["set"] == "space").sum()); N_ENV = int((SEL["set"] == "environment").sum())
WA = (M * W[:, None]).sum(0) / M.sum(0)                                                       # weighted-average optimum
CL_W = [W[CL == k].mean() for k in range(1, NCL + 1)]
FOCAL = ["FSET", "HMIN2", "LRUG", "LCIL"]                                                     # four optima along the gradient
GSD = {s: {k: GS[k][i] for k in GS} for i, s in enumerate(GS["species"])}


def describe(k):
    """The community in words: its most common topography and shrub cover."""
    m = CL == k
    topo = max(set(ENV["Topo"][m]), key=list(ENV["Topo"][m]).count)
    shrub = max(set(ENV["Shrub"][m]), key=list(ENV["Shrub"][m]).count)
    return f"{topo.lower()}, {'no' if shrub == 'None' else shrub.lower()} shrubs"


# ---- the claims, checked
assert abs(FR["env_only"] + FR["shared"] - FR["env_total"]) < 1e-9 and abs(FR["space_only"] + FR["shared"] - FR["space_total"]) < 1e-9
assert FR["shared"] > FR["env_only"] and FR["shared"] > FR["space_only"] and FP["env_only"] <= 0.001 and FP["space_only"] <= 0.001
assert R2V["WatrCont"] == max(list(R2V.values()) + list(R2F.values())) and PV["WatrCont"] <= 0.001
assert list(CL_W) == sorted(CL_W)
SHARE_SPATIAL = FR["shared"] / FR["env_total"]

TITLE = (f"Habitat explains {FR['env_total'] * 100:.0f} % of the mite community, "
         f"but {SHARE_SPATIAL * 100:.0f} % of that is shared with space")
SUB = (f"Oribatid mites in 70 cores of Sphagnum peat, 35 species, 10 × 2.6 m · four community types (I–IV, by rising water content) "
       f"in the same colours in every panel")


# ---------------------------------------------------------------- a  the two maps
def strip(V, ax, xy_cols, top):
    ax.add_patch(Rectangle((0, 0), 10, 2.6, facecolor=V.card, edgecolor="none", zorder=0))
    ax.set_xlim(-0.15, 10.15); ax.set_ylim(-0.25, 2.85); ax.set_aspect("equal")
    ax.set_xticks([0, 5, 10]); ax.set_xticklabels(["0", "5", "10 m"] if not top else [])
    ax.set_yticks([0, 2.6]); ax.set_yticklabels(["0", "2.6"])
    clean(ax, grid=False)


def panel_a(V, fig, ax1, ax2, cax):
    x, y = ENV["y"], ENV["x"]                                                                   # the long side runs across the page
    cmw = V.cmap_gradient("lagoon")
    strip(V, ax1, None, True)
    sc = ax1.scatter(x, y, c=W, cmap=cmw, vmin=100, vmax=850, s=34, edgecolor=V.surface, lw=0.8, zorder=3)
    strip(V, ax2, None, False)
    for k in range(1, NCL + 1):
        m = CL == k; ax2.scatter(x[m], y[m], s=34, color=V.tone(k - 1), edgecolor=V.surface, lw=0.8, zorder=3)
    text(V, ax2, -0.15, 3.0, "community type of each core, I–IV", color=V.muted, va="bottom", size=V.sz["unit_line"])
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal"); cb.outline.set_visible(False); cb.set_ticks([200, 500, 800])
    cb.ax.tick_params(size=0, labelsize=V.sz["unit_line"], colors=V.muted, pad=2)
    head(V, ax1, "a", "Wet and dry patches carry their own fauna", unit="water content of each core, g per litre")


def key(V, ax):
    """The community key, as a small table under the maps: colour, numeral, habitat in words, mean water content, cores."""
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    text(V, ax, 0.11, 0.98, "type", color=V.muted, va="top"); text(V, ax, 0.28, 0.98, "mostly", color=V.muted, va="top")
    text(V, ax, 0.80, 0.98, "water", color=V.muted, va="top", ha="right"); text(V, ax, 0.99, 0.98, "cores", color=V.muted, va="top", ha="right")
    for k in range(1, NCL + 1):
        y = 0.98 - 0.215 * k - 0.02
        ax.scatter(0.04, y, s=34, color=V.tone(k - 1), edgecolor=V.surface, lw=0.8, transform=ax.transAxes, clip_on=False)
        text(V, ax, 0.11, y, ROMAN[k - 1], color=V.ink)
        text(V, ax, 0.28, y, describe(k), color=V.secondary)
        text(V, ax, 0.80, y, f"{CL_W[k - 1]:.0f}", color=V.secondary, ha="right")
        text(V, ax, 0.99, y, f"{int((CL == k).sum())}", color=V.secondary, ha="right")


# ---------------------------------------------------------------- b  NMDS
def panel_b(V, ax):
    P = np.column_stack([NM["nmds1"], NM["nmds2"]])
    for k in range(1, NCL + 1):
        pts = P[CL == k]
        V.dot(ax, pts[:, 0], pts[:, 1], V.tone(k - 1), s=22, z=3, ring=0.8)
        c = pts.mean(0)
        text(V, ax, c[0], c[1], ROMAN[k - 1], color=V.deep(k - 1), ha="center", va="center", size=V.sz["panel_title"] + 2,
             fontweight="bold", path_effects=halo(V, 3.5), zorder=7)
    # fitted vectors, scaled by sqrt(r2) as in vegan's plot.envfit, to a common arrow length
    L = 1.15
    for v, lab in (("WatrCont", "water content"), ("SubsDens", "substrate density")):
        i = list(VEC["variable"]).index(v); d = np.array([VEC["nmds1"][i], VEC["nmds2"][i]]) * np.sqrt(R2V[v]) * L
        sig = PV[v] <= 0.05
        ax.annotate("", d, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=V.ink if sig else V.muted, lw=0.9 if sig else 0.6,
                                                         mutation_scale=7, shrinkA=0, shrinkB=0), zorder=5)
        txt = f"{lab}\nr² = {R2V[v]:.2f}" + ("" if sig else f", p = {PV[v]:.2f}")
        if sig: text(V, ax, d[0] * 1.06, d[1] - 0.05, txt, color=V.ink, ha="right", va="top", linespacing=1.0, path_effects=halo(V))
        else: text(V, ax, d[0] + 0.06, d[1] - 0.02, txt, color=V.muted, ha="left", va="top", linespacing=1.0, path_effects=halo(V))
    for f, labs in (("Topo", ("Blanket", "Hummock")),):
        for lv in labs:
            i = list(CEN["level"]).index(f + lv); c = (CEN["nmds1"][i], CEN["nmds2"][i])
            ax.scatter(*c, marker="D", s=14, color=V.surface, edgecolor=V.secondary, lw=0.8, zorder=6)
            name = {"Blanket": "blanket", "Hummock": "hummock", "None": "no shrubs", "Many": "many shrubs"}[lv]
            up = lv == "Hummock"
            text(V, ax, c[0], c[1] + (0.08 if up else -0.08), name, color=V.secondary, ha="center", va="bottom" if up else "top",
                 size=V.sz["unit_line"], path_effects=halo(V))
    ax.axhline(0, color=V.grid, lw=0.6, zorder=0); ax.axvline(0, color=V.grid, lw=0.6, zorder=0)
    ax.set_xlim(-1.45, 1.35); ax.set_ylim(-1.2, 1.25); ax.set_aspect("equal")
    ax.set_xticks([-1, 0, 1]); ax.set_yticks([-1, 0, 1])
    ax.set_xticklabels([minus("-1"), "0", "1"]); ax.set_yticklabels([minus("-1"), "0", "1"])
    ax.set_xlabel("NMDS 1"); ax.grid(False)
    text(V, ax, 1.33, -1.18, f"stress {FIT['stress'][0]:.2f}", color=V.muted, ha="right", va="bottom")
    head(V, ax, "b", f"Water content runs along the first axis, r² = {R2V['WatrCont']:.2f}", unit="NMDS 2 · ◇ centroids of the two topographies")


# ---------------------------------------------------------------- c  Euler diagram of the variation partition
def lens(r1, r2, d):
    if d >= r1 + r2: return 0.0
    if d <= abs(r1 - r2): return np.pi * min(r1, r2) ** 2
    a = r1 ** 2 * np.arccos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1)) + r2 ** 2 * np.arccos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    return a - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def panel_c(V, ax):
    r1, r2 = np.sqrt(FR["env_total"] / np.pi), np.sqrt(FR["space_total"] / np.pi)
    d = brentq(lambda d: lens(r1, r2, d) - FR["shared"], abs(r1 - r2) + 1e-9, r1 + r2 - 1e-9)
    assert abs(lens(r1, r2, d) - FR["shared"]) < 1e-9
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=V.card, edgecolor=V.rule, lw=0.6, zorder=0))
    cy = 0.5; c1 = (0.5 - d / 2, cy); c2 = (0.5 + d / 2, cy)
    ce, cs = V.tone("moss"), V.tone("mauve")
    ax.add_patch(Circle(c1, r1, facecolor=V.tint("moss"), edgecolor="none", alpha=0.75, zorder=1))
    ax.add_patch(Circle(c2, r2, facecolor=V.tint("mauve"), edgecolor="none", alpha=0.55, zorder=2))
    ax.add_patch(Circle(c1, r1, facecolor="none", edgecolor=ce, lw=1.1, zorder=3))
    ax.add_patch(Circle(c2, r2, facecolor="none", edgecolor=cs, lw=1.1, zorder=3))
    pct = lambda v: f"{v * 100:.0f} %"
    text(V, ax, 0.5, cy + 0.03, pct(FR["shared"]), color=V.ink, ha="center", va="bottom", size=V.sz["panel_title"] + 2, fontweight="bold")
    text(V, ax, 0.5, cy - 0.01, "shared", color=V.ink, ha="center", va="top")
    for (edge, sgn, lab, v) in ((c1[0] - r1, -1, "habitat\nalone", FR["env_only"]), (c2[0] + r2, 1, "space\nalone", FR["space_only"])):
        ax.annotate(f"{pct(v)}\n{lab}", (edge - sgn * 0.025, cy), xytext=(0.5 + sgn * 0.62, cy), textcoords="data",
                    ha="right" if sgn < 0 else "left", va="center", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.0,
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=0))
    text(V, ax, -0.03, 0.0, pct(FR["residual"]) + "\nunexplained", color=V.muted, ha="right", va="bottom", size=V.sz["unit_line"], linespacing=1.0)
    text(V, ax, 0.0, 1.03, f"habitat {pct(FR['env_total'])}", color=V.deep("moss") if V.mode == "light" else V.tone("moss"),
         ha="left", va="bottom", size=V.sz["unit_line"])
    text(V, ax, 1.0, -0.03, f"space {pct(FR['space_total'])}", color=V.deep("mauve") if V.mode == "light" else V.tone("mauve"),
         ha="right", va="top", size=V.sz["unit_line"])
    ax.set_xlim(-0.42, 1.42); ax.set_ylim(-0.14, 1.12); ax.set_aspect("equal"); ax.axis("off")
    head(V, ax, "c", "Most explained variation is shared", unit="square: all variation · areas: adjusted R²")
    return d


# ---------------------------------------------------------------- d  the community table
def panel_d(V, fig, ax, axw, axc, cax):
    co = np.argsort(W, kind="stable"); so = np.argsort(WA, kind="stable")
    A = M[co][:, so].T; A = A / A.max(axis=1, keepdims=True)
    cm = V.cmap_gradient("ember")
    im = ax.imshow(np.where(A > 0, A, np.nan), aspect="auto", cmap=cm, vmin=0, vmax=1, interpolation="nearest",
                   extent=(-0.5, 69.5, 34.5, -0.5))
    ax.set_facecolor(V.card if V.mode == "light" else V.card)
    ax.set_xlim(-0.5, 69.5); ax.set_ylim(34.5, -0.5); clean(ax, grid=False)
    names = [SPP[i] for i in so]
    ax.set_yticks([])
    rows = [names.index(s) for s in FOCAL]; ys = vellum.spread(rows, 2.4)
    for s_, r, yl in zip(FOCAL, rows, ys):
        ax.annotate(s_, (-0.6, r), xytext=(-5.5, yl), textcoords="data", ha="right", va="center", fontsize=V.sz["unit_line"],
                    color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.secondary, lw=0.5, shrinkA=1, shrinkB=0, relpos=(1, 0.5)))
    ax.set_xticks([0, 34, 69]); ax.set_xticklabels(["driest core", "", "wettest"]); ax.tick_params(axis="x", pad=3)
    ax.get_xticklabels()[0].set_ha("left"); ax.get_xticklabels()[-1].set_ha("right")
    text(V, ax, 70.5, 0, "dry-peat\nspecies", color=V.muted, ha="left", va="top", linespacing=1.0, size=V.sz["unit_line"])
    text(V, ax, 70.5, 34, "wet-peat\nspecies", color=V.muted, ha="left", va="bottom", linespacing=1.0, size=V.sz["unit_line"])
    ax.text(70.5, 17, "35 species,\nby water\noptimum", rotation=0, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="center")
    # water content of each core and its community, in the order of the columns
    axw.bar(np.arange(70), W[co], width=0.82, color=[V.cmap_gradient("lagoon")((w - 100) / 750) for w in W[co]], edgecolor="none")
    axw.set_xlim(-0.5, 69.5); axw.set_ylim(0, 900); axw.set_xticks([]); axw.set_yticks([0, 800]); axw.set_yticklabels(["0", "800"])
    axw.tick_params(axis="y", labelsize=V.sz["unit_line"], pad=2); clean(axw)
    text(V, axw, 70.5, 450, "water, g/L", color=V.muted, ha="left", va="center", size=V.sz["unit_line"])
    axc.imshow(np.array([[to_rgba_v(V, CL[i]) for i in co]]), aspect="auto", extent=(-0.5, 69.5, 0, 1), interpolation="nearest")
    for j in range(71): axc.axvline(j - 0.5, color=V.surface, lw=0.5)
    axc.set_xlim(-0.5, 69.5); axc.set_xticks([]); axc.set_yticks([]); clean(axc, grid=False)
    text(V, axc, 70.5, 0.5, "community", color=V.muted, ha="left", va="center", size=V.sz["unit_line"])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal"); cb.outline.set_visible(False); cb.set_ticks([0, 0.5, 1])
    cb.ax.set_xticklabels(["0", "½", "max"]); cb.ax.tick_params(size=0, labelsize=V.sz["unit_line"], colors=V.muted, pad=2)
    cax.set_title("abundance, share of the species' maximum · blank: absent", fontsize=V.sz["unit_line"], color=V.muted, loc="left",
                  pad=3, fontweight="normal")
    head(V, axw, "d", "Species replace one another along the water gradient", unit=None)


def to_rgba_v(V, k):
    from matplotlib.colors import to_rgb
    return to_rgb(V.tone(int(k) - 1))


# ---------------------------------------------------------------- e  response curves
def panel_e(V, axes):
    for j, (ax, s) in enumerate(zip(axes, FOCAL)):
        m = GC["species"] == s; x, f, lo, hi = GC["watrcont"][m], GC["fit"][m], GC["lo"][m], GC["hi"][m]
        y = CNT[s]
        ax.fill_between(x, lo, hi, color=V.tint("teal"), alpha=0.6, lw=0, zorder=1)
        for k in range(1, NCL + 1):
            mk = CL == k
            ax.scatter(W[mk], y[mk], s=10, color=V.tone(k - 1), edgecolor=V.surface, lw=0.5, zorder=3)
        ax.plot(x, f, color=V.tone("teal"), lw=1.4, zorder=4, clip_on=True)
        opt = GSD[s]["optimum"]; top = np.nanmax(y) * 1.3
        ax.axvline(opt, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=2)
        ax.set_xlim(100, 860); ax.set_xticks([200, 500, 800]); ax.set_ylim(-top * 0.04, top)
        ax.yaxis.set_major_locator(plt.MaxNLocator(3, integer=True))
        if j == 0: ax.set_xlabel("water content, g/L")
        dev = GSD[s]["dev_expl"] * 100
        text(V, ax, 0, 1.06, s, transform=ax.transAxes, color=V.ink, va="bottom", fontweight="bold", size=V.sz["annotation"])
        ax.annotate(f"optimum {opt:.0f} · {dev:.0f} %", (0, 1.06), xycoords="axes fraction", xytext=(31, 0),
                    textcoords="offset points", fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")
    a0 = axes[0]
    a0.set_title("e  Four species, four optima along the water gradient", color=V.ink, pad=27, loc="left")
    a0.text(0, 1.30, "individuals per core · line: negative-binomial GAM, 95 % band · dots coloured by community · dotted: optimum, g/L · %: deviance explained",
            transform=a0.transAxes, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")


def draw(V):
    fig = plt.figure(figsize=(7.2, 9.6))
    # row 1: maps and key | NMDS
    a1 = axes_in(fig, 0.42, 1.33, 3.30, 0.86); a2 = axes_in(fig, 0.42, 2.55, 3.30, 0.86)
    ca = axes_in(fig, 2.90, 2.25, 0.80, 0.05)
    k = axes_in(fig, 0.42, 3.77, 3.30, 0.80)
    b = axes_in(fig, 4.55, 1.33, 2.55, 2.23)
    # row 2: Euler diagram | community table
    c = axes_in(fig, 0.30, 5.30, 2.15, 1.45)
    dw = axes_in(fig, 3.05, 5.23, 3.40, 0.30); dc = axes_in(fig, 3.05, 5.57, 3.40, 0.10)
    d = axes_in(fig, 3.05, 5.71, 3.40, 1.62); cd = axes_in(fig, 3.05, 7.71, 1.2, 0.05)
    # row 3: response curves
    es = [axes_in(fig, 0.42 + i * 1.72, 8.47, 1.38, 0.55) for i in range(4)]
    panel_a(V, fig, a1, a2, ca); key(V, k); panel_b(V, b); panel_c(V, c); panel_d(V, fig, d, dw, dc, cd); panel_e(V, es)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Five panels on oribatid mites in 70 peat cores. a: two maps of the 10 by 2.6 m plot, water content and four community types; "
       f"wet and dry patches hold different types. b: NMDS (stress {FIT['stress'][0]:.2f}); water content aligns with the first axis "
       f"(r² = {R2V['WatrCont']:.2f}). c: an area-proportional Euler diagram: habitat explains {FR['env_total'] * 100:.0f} % and space "
       f"{FR['space_total'] * 100:.0f} %, {FR['shared'] * 100:.0f} % jointly; habitat alone {FR['env_only'] * 100:.0f} %, space alone "
       f"{FR['space_only'] * 100:.0f} %, unexplained {FR['residual'] * 100:.0f} %. d: the 35-species community table ordered by water "
       f"shows species replacing one another. e: GAM response curves of {', '.join(FOCAL)} with optima at "
       + ", ".join(f"{GSD[s]['optimum']:.0f}" for s in FOCAL) + " g/L.")

META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="five-panel composite: twin maps, NMDS with envfit, Euler diagram of variation partitioning, community table, GAM small multiples",
            medium="paper", tool="matplotlib",
            data="Oribatid mites of Lac Geai bog, Borcard and Legendre (1994), via R vegan::mite, mite.env, mite.xy", script=rel(__file__),
            alt=ALT,
            note=(f"Variation partitioning of Hellinger-transformed counts by RDA (vegan varpart), adjusted R²: habitat alone "
                  f"{FR['env_only']:.3f} (p = {FP['env_only']:.3f}), shared {FR['shared']:.3f}, space alone {FR['space_only']:.3f} "
                  f"(p = {FP['space_only']:.3f}), residual {FR['residual']:.3f}; 999 permutations. Habitat: {N_ENV} variables "
                  f"(water content, substrate density, substrate, shrub cover, topography), all kept by forward selection; space: "
                  f"{N_SPACE} PCNM eigenfunctions forward-selected from 43 with the double stopping criterion (ordiR2step). "
                  f"NMDS: metaMDS on Bray–Curtis, k = 2, stress {FIT['stress'][0]:.3f}. envfit r² (p): " +
                  ", ".join(f"{v} {R2V[v]:.2f} ({PV[v]:.3f})" for v in R2V) + ", " +
                  ", ".join(f"{f} {R2F[f]:.2f} ({PF[f]:.3f})" for f in R2F) +
                  ". Communities: Ward clustering on Hellinger distance, four groups. GAMs: y ~ s(water, k = 5), negative binomial, REML."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        print(save(draw(vellum.use(mode)), "ecology", "mite_metacommunity", mode, meta=META if mode == "light" else None))
