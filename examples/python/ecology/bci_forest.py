"""bci_forest.py: the tree community of the Barro Colorado Island 50-ha plot as a seven-panel composite.

a  rank-abundance (Whittaker) plot of the 225 species with four radfit models; ΔAIC beside each
b  the ten commonest species and their share of the 21 457 stems
c  occupancy against abundance, with the occupancy expected if stems were placed at random among the 50 plots
d  species accumulation over plots (999 random orders) with Chao1 and first-order jackknife estimates of the total
e  distance decay of Bray–Curtis similarity between the 1 225 pairs of plots, with Mantel r
f  richness of each one-hectare plot on the 10 × 5 grid, the high plateau outlined
g  stems of the commonest species, Faramea occidentalis, on the same grid

Shared code: the ten commonest species are terracotta and the singletons indigo in every panel where species are points.
Data: data/ecology/bci_*.csv, exported from vegan::BCI and BCI.env by export_data.R (Condit et al. 2002; trees with dbh ≥ 10 cm).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco import *
from matplotlib.ticker import FixedLocator, NullLocator
from matplotlib.colors import to_rgb
from scipy.optimize import curve_fit

SOURCE = "Data: Barro Colorado Island 50-ha plot, trees ≥ 10 cm dbh, 1982 census (Condit et al. 2002, Science), via R vegan::BCI"
C = table("bci_counts.csv"); P = table("bci_plots.csv"); RF = table("bci_radfit.csv"); RM = table("bci_radfit_models.csv")
SA = table("bci_specaccum.csv"); POOL = table("bci_specpool.csv"); TESTS = table("bci_tests.csv")
SP = [k for k in C if k != "plot"]; M = np.array([C[k] for k in SP]).T                     # 50 plots x 225 species
TOT = M.sum(0); NSTEM = int(TOT.sum()); NSP = len(SP)
ORDER = np.argsort(-TOT, kind="stable"); SHARE = TOT[ORDER] / NSTEM
TOP = ORDER[:10]; HALF = int(np.searchsorted(np.cumsum(SHARE), 0.5) + 1)
SINGLE = np.where(TOT == 1)[0]; DOUBLE = int((TOT == 2).sum())
OCC = (M > 0).sum(0); EXP_OCC = 50 * (1 - np.exp(-TOT / 50))                               # Poisson placement among 50 plots
CLUMPED = float((OCC < EXP_OCC).mean()); EVERY = int((OCC == 50).sum())
name = lambda i: SP[i].replace(".", " ")

# AIC of the rank-abundance models, against the best
AIC = dict(zip(RM["model"], RM["AIC"])); BEST = min((k for k in AIC if k != "Null"), key=AIC.get)
MODELS = [("Lognormal", "lognormal"), ("Mandelbrot", "Zipf–Mandelbrot"), ("Preemption", "preemption"), ("Zipf", "Zipf")]

# distance decay: Bray-Curtis similarity between plot centres
XY = np.column_stack([P["utm_ew"], P["utm_ns"]])
DIST = np.hypot(*(XY[:, None, :] - XY[None, :, :]).transpose(2, 0, 1))
BC = 1 - np.abs(M[:, None, :] - M[None, :, :]).sum(2) / (M.sum(1)[:, None] + M.sum(1)[None, :])
iu = np.triu_indices(50, 1); PD, PS = DIST[iu], BC[iu]
decay = lambda d, a, c, L: c + (a - c) * np.exp(-d / L)
(DA, DC, DL), _ = curve_fit(decay, PD, PS, p0=(0.7, 0.5, 200))
BINS = np.arange(50, 1050, 100); BMID, BMEAN, BSE = [], [], []
for lo in BINS:
    m = (PD >= lo) & (PD < lo + 100)
    if m.sum() >= 10: BMID.append(PD[m].mean()); BMEAN.append(PS[m].mean()); BSE.append(PS[m].std(ddof=1) / np.sqrt(m.sum()))
BMID, BMEAN, BSE = map(np.array, (BMID, BMEAN, BSE))
MANTEL = dict(zip(TESTS["test"], zip(TESTS["r"], TESTS["p"])))["mantel_bray"]
NEAR = PS[np.isclose(PD, 100)].mean(); FAR = PS[PD >= 900].mean()

# the grid: 10 columns west to east, 5 rows south to north, one hectare each
GRID_R = np.full((5, 10), np.nan); GRID_F = np.full((5, 10), np.nan); HAB = np.empty((5, 10), dtype=object)
FAR_I = SP.index("Faramea.occidentalis")
for k in range(50):
    r, c = int(P["row"][k]), int(P["col"][k])
    GRID_R[r, c] = P["richness"][k]; GRID_F[r, c] = M[k, FAR_I]; HAB[r, c] = P["habitat"][k]
HIGH = P["habitat"] == "OldHigh"; R_HIGH, R_REST = P["richness"][HIGH].mean(), P["richness"][~HIGH].mean()

# ---- the claims, checked
assert NSP == 225 and NSTEM == 21457 and HALF == 15 and len(SINGLE) == 19
assert SP[ORDER[0]] == "Faramea.occidentalis" and BEST == "Lognormal"
assert MANTEL[1] <= 0.001 and 0.40 < MANTEL[0] < 0.42

TITLE = f"Fifteen of {NSP} tree species hold half of Barro Colorado's {NSTEM:,} trees, while {len(SINGLE)} were found once".replace(",", " ", 1)
SUB = (f"Barro Colorado Island, Panama · 50 one-hectare plots, trees ≥ 10 cm in diameter · "
       f"terracotta: the ten commonest species, indigo: the {len(SINGLE)} singletons")


def log_ticks(ax, axis, ticks, labels=None):
    loc = FixedLocator(ticks); lab = labels or [f"{t:,}".replace(",", " ") if t >= 1 else f"{t:g}" for t in ticks]
    a = ax.xaxis if axis == "x" else ax.yaxis
    a.set_major_locator(loc); a.set_minor_locator(NullLocator())
    (ax.set_xticklabels if axis == "x" else ax.set_yticklabels)(lab)


def species_colour(V, i):
    return V.tone("terracotta") if i in TOP else V.tone("indigo") if TOT[i] == 1 else None


def panel_a(V, ax):
    rank = np.arange(1, NSP + 1); ab = TOT[ORDER]
    styles = {"Lognormal": (V.tone("teal"), 1.5, "-"), "Mandelbrot": (V.secondary, 0.8, (0, (5, 2))),
              "Preemption": (V.secondary, 0.8, (0, (1, 1.6))), "Zipf": (V.secondary, 0.8, (0, (5, 1.5, 1, 1.5)))}
    for key, _ in MODELS[::-1]:
        c, lw, ls = styles[key]; ax.plot(RF["rank"], RF[key], color=c, lw=lw, ls=ls, zorder=3 if key == BEST else 2)
    mid = (~np.isin(ORDER, TOP)) & (ab > 1)
    ax.scatter(rank[mid], ab[mid], s=9, color=V.rule, edgecolor=V.surface, lw=0.4, zorder=4)
    V.dot(ax, rank[:10], ab[:10], V.tone("terracotta"), s=16, z=5, ring=0.7)
    V.dot(ax, rank[ab == 1], ab[ab == 1], V.tone("indigo"), s=16, z=5, ring=0.7)
    ax.annotate(f"{name(ORDER[0])}, {int(ab[0]):,} stems".replace(",", " "), (1, ab[0]), xytext=(8, 2), textcoords="offset points",
                ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink, fontstyle="italic", path_effects=halo(V))
    ax.annotate(f"{len(SINGLE)} singletons", (rank[ab == 1].mean(), 1), xytext=(-4, -6), textcoords="offset points",
                ha="center", va="top", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    # the model key, as a small table of ΔAIC with a line sample each, in the empty upper right
    x0, y0, dy = 0.47, 0.97, 0.092
    text(V, ax, x0 + 0.155, y0, "model", color=V.muted, transform=ax.transAxes, va="top")
    text(V, ax, 0.995, y0, "ΔAIC", color=V.muted, transform=ax.transAxes, ha="right", va="top")
    for k, (key, lab) in enumerate(MODELS):
        y = y0 - (k + 1) * dy - 0.035; c, lw, ls = styles[key]
        ax.plot([x0, x0 + 0.12], [y, y], transform=ax.transAxes, color=c, lw=lw, ls=ls, solid_capstyle="butt")
        text(V, ax, x0 + 0.155, y, lab, transform=ax.transAxes, color=V.ink if key == BEST else V.secondary)
        text(V, ax, 0.995, y, "best" if key == BEST else f"+{AIC[key] - AIC[BEST]:,.0f}".replace(",", " "), transform=ax.transAxes,
             ha="right", color=V.ink if key == BEST else V.secondary)
    ax.set_yscale("log"); ax.set_ylim(0.2, 9000); log_ticks(ax, "y", [1, 10, 100, 1000])
    ax.set_xlim(-4, NSP + 5); ax.set_xticks([1, 50, 100, 150, 200, 225])
    ax.set_xlabel("species rank, commonest first")
    head(V, ax, "a", f"Abundances span three orders; a lognormal fits best", unit="stems in 50 ha, log scale")


def panel_b(V, ax):
    y = np.arange(10)
    ax.barh(y, SHARE[:10] * 100, height=0.66, color=V.tone("terracotta"), edgecolor="none", zorder=2)
    for k in range(10):
        text(V, ax, SHARE[k] * 100 + 0.25, k, f"{SHARE[k] * 100:.1f}", color=V.secondary, va="center")
    ax.set_yticks(y); ax.set_yticklabels([name(i) for i in TOP], fontstyle="italic"); ax.set_ylim(9.6, -0.6)
    ax.tick_params(axis="y", labelcolor=V.secondary, labelsize=V.sz["annotation"])
    ax.set_xlim(0, 9.8); ax.set_xticks([0, 4, 8]); ax.grid(False); ax.grid(True, axis="x")
    ax.set_xlabel("share of stems, %")
    text(V, ax, 9.8, 7.0, f"together\n{SHARE[:10].sum() * 100:.1f} %", color=V.ink, ha="right", va="center", linespacing=1.0)
    text(V, ax, 9.8, 8.6, f"{HALF} species\nhold half", color=V.muted, ha="right", va="center", linespacing=1.0)
    fig = ax.figure; r = fig.canvas.get_renderer()
    w = max(t.get_window_extent(r).width for t in ax.get_yticklabels()) / fig.dpi + 4 / 72     # labels plus the tick pad
    head(V, ax, "b", f"Ten species hold {SHARE[:10].sum() * 100:.0f} %", unit="share of the 21 457 stems", dx_in=w)


def panel_c(V, ax):
    n = np.logspace(0, np.log10(2500), 300)
    ax.plot(n, 50 * (1 - np.exp(-n / 50)), color=V.tone("ochre"), lw=V.thin * 1.4, ls=V.dotted, zorder=2)
    ax.annotate("random\nplacement", (70, 50 * (1 - np.exp(-70 / 50))), xytext=(400, 16), textcoords="data",
                ha="center", va="center", fontsize=V.sz["annotation"], color=V.muted, linespacing=1.0,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=2))
    keys, cnt = np.unique(np.column_stack([TOT, OCC]), axis=0, return_counts=True)
    base = [(k, c) for k, c in zip(keys, cnt)]
    for (t, o), c in base:
        i = np.where((TOT == t) & (OCC == o))[0]
        col = V.tone("terracotta") if np.isin(i, TOP).any() else V.tone("indigo") if t == 1 else V.rule
        ax.scatter(t, o, s=7 + 5 * c, color=col, edgecolor=V.surface, lw=0.5, zorder=4 if col != V.rule else 3)
    ax.annotate(f"{len(SINGLE)} singletons", (1, 1), xytext=(6, 12), textcoords="offset points", ha="left", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V),
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=4))
    first = TOT[OCC == 50].min()
    ax.annotate(f"{EVERY} species in all 50", (first, 50), xytext=(30, 50), textcoords="data", ha="right", va="center",
                fontsize=V.sz["annotation"], color=V.muted, path_effects=halo(V),
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=4))
    ax.set_xscale("log"); ax.set_xlim(0.7, 3000); log_ticks(ax, "x", [1, 10, 100, 1000])
    ax.set_ylim(-1, 52); ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.set_xlabel("stems in 50 ha")
    head(V, ax, "c", f"{CLUMPED * 100:.0f} % fill fewer plots than chance", unit="plots occupied, of 50 · dot area: species")


def panel_d(V, ax):
    x = SA["plots"]
    ax.fill_between(x, SA["lo"], SA["hi"], color=V.tint("teal"), alpha=0.7, lw=0, zorder=1)
    ax.plot(x, SA["richness"], color=V.tone("teal"), lw=1.4, zorder=3)
    for lab, v, se, xx, va, dy in (("Chao1", POOL["chao"][0], POOL["chao_se"][0], 54, "top", -2),
                                   ("jackknife", POOL["jack1"][0], POOL["jack1_se"][0], 57.5, "bottom", 2)):
        ax.axhline(v, xmax=(xx - 0.5) / 61, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=1)
        ax.plot([xx, xx], [v - 1.96 * se, v + 1.96 * se], color=V.secondary, lw=0.8, solid_capstyle="butt", zorder=3)
        V.dot(ax, xx, v, V.tone("ochre"), s=18, z=4, ring=0.9)
        ax.annotate(f"{lab} estimate, {v:.0f}", (1, v), xytext=(0, dy), textcoords="offset points", ha="left", va=va,
                    fontsize=V.sz["annotation"], color=V.secondary)
    V.dot(ax, 50, SA["richness"][-1], V.tone("teal"), s=20, z=5, ring=0.9)
    ax.annotate(f"{int(SA['richness'][-1])} seen", (50, SA["richness"][-1]), xytext=(-2, -7), textcoords="offset points",
                ha="right", va="top", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    text(V, ax, 22, 150, "95 % of 999\nrandom orders", color=V.muted, ha="left", va="top", linespacing=1.0)
    ax.set_xlim(0, 61); ax.set_xticks([1, 10, 20, 30, 40, 50]); ax.set_ylim(80, 268); ax.set_yticks([100, 150, 200, 250])
    ax.set_xlabel("hectares sampled")
    missing = (POOL["chao"][0] - NSP, POOL["jack1"][0] - NSP)
    head(V, ax, "d", f"50 ha still miss {missing[0]:.0f} to {missing[1]:.0f} species", unit="species")


def panel_e(V, ax):
    ax.scatter(PD, PS, s=3, color=V.rule, lw=0, alpha=0.7, zorder=1, rasterized=True)
    d = np.linspace(100, 1000, 200)
    ax.plot(d, decay(d, DA, DC, DL), color=V.tone("teal"), lw=1.4, zorder=3)
    ax.errorbar(BMID, BMEAN, yerr=1.96 * BSE, fmt="none", ecolor=V.secondary, elinewidth=0.8, capsize=0, zorder=4)
    V.dot(ax, BMID, BMEAN, V.tone("teal"), s=16, z=5, ring=0.8)
    text(V, ax, 1000, 0.215, f"Mantel r = {MANTEL[0]:.2f}, p = {MANTEL[1]:.3f}\n999 permutations", color=V.muted, ha="right",
         va="bottom", linespacing=1.05)
    ax.annotate(f"neighbours: {NEAR:.2f}", (BMID[0], BMEAN[0]), xytext=(6, 10), textcoords="offset points", ha="left",
                va="bottom", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    ax.set_xlim(60, 1010); ax.set_xticks([100, 400, 700, 1000]); ax.set_ylim(0.2, 0.76); ax.set_yticks([0.2, 0.4, 0.6])
    ax.set_xlabel("distance between plots, m")
    head(V, ax, "e", f"Similarity falls from {NEAR:.2f} to {FAR:.2f} with distance", unit="Bray–Curtis similarity · dots: 1 225 pairs")


def grid_map(V, fig, ax, cax, Z, cmap, label, ticks, fmt="{:.0f}", outline=None, lim=None, yticks=True):
    lo, hi = lim or (ticks[0], ticks[-1])
    im = ax.imshow(Z, origin="lower", cmap=cmap, vmin=lo, vmax=hi, extent=(-0.5, 9.5, -0.5, 4.5), aspect="equal")
    V.heat_gaps(ax, 10, 5)
    for r in range(5):
        for c in range(10):
            rgb = np.array(cmap((Z[r, c] - lo) / (hi - lo))[:3])
            lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            ax.text(c, r, fmt.format(Z[r, c]), ha="center", va="center", fontsize=V.sz["unit_line"],
                    color="#FFFFFF" if lum < 0.45 else "#2A2825")
    if outline is not None:                                                               # cell edges between in and out
        for r in range(5):
            for c in range(10):
                if not outline[r, c]: continue
                for dr, dc, seg in ((1, 0, ([c - .5, c + .5], [r + .5, r + .5])), (-1, 0, ([c - .5, c + .5], [r - .5, r - .5])),
                                    (0, 1, ([c + .5, c + .5], [r - .5, r + .5])), (0, -1, ([c - .5, c - .5], [r - .5, r + .5]))):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < 5 and 0 <= cc < 10) or not outline[rr, cc]:
                        ax.plot(*seg, color=V.ink, lw=1.3, solid_capstyle="projecting", zorder=5)
    ax.set_xlim(-0.55, 9.55); ax.set_ylim(-0.55, 4.55)
    ax.set_xticks([-0.5, 4.5, 9.5]); ax.set_xticklabels(["0", "500", "1 000 m"])
    ax.set_yticks([-0.5, 4.5] if yticks else []); ax.set_yticklabels(["0", "500 m"] if yticks else [])
    cb = fig.colorbar(im, cax=cax); cb.outline.set_visible(False); cb.set_ticks(ticks)
    cb.ax.tick_params(size=0, labelsize=V.sz["unit_line"], colors=V.muted)
    cax.set_title(label, fontsize=V.sz["unit_line"], color=V.muted, loc="left", pad=4, fontweight="normal")
    return im


def panel_f(V, fig, ax, cax):
    grid_map(V, fig, ax, cax, GRID_R, V.cmap_gradient("lagoon"), "species", [75, 90, 105], lim=(75, 110),
             outline=(HAB == "OldHigh"))
    head(V, ax, "f", f"{int(np.nanmin(GRID_R))} to {int(np.nanmax(GRID_R))} species in every hectare",
         unit=f"species per plot · outlined: the high plateau, {R_HIGH:.0f} against {R_REST:.0f}")


def panel_g(V, fig, ax, cax):
    grid_map(V, fig, ax, cax, GRID_F, V.cmap_gradient("ember"), "stems", [0, 20, 40, 60, 80], yticks=False)
    head(V, ax, "g", f"The commonest tree is everywhere, {int(np.nanmin(GRID_F))} to {int(np.nanmax(GRID_F))} per hectare",
         unit="stems of Faramea occidentalis per plot")


def draw(V):
    fig = plt.figure(figsize=(7.2, 8.25))
    a = axes_in(fig, 0.42, 1.22, 3.70, 1.75)
    b = axes_in(fig, 5.55, 1.22, 1.30, 1.75)
    c = axes_in(fig, 0.42, 3.85, 1.80, 1.50)
    d = axes_in(fig, 2.80, 3.85, 1.80, 1.50)
    e = axes_in(fig, 5.10, 3.85, 1.90, 1.50)
    f = axes_in(fig, 0.42, 6.32, 2.86, 1.43); fc = axes_in(fig, 3.36, 6.50, 0.07, 1.10)
    g = axes_in(fig, 3.98, 6.32, 2.86, 1.43); gc = axes_in(fig, 6.92, 6.50, 0.07, 1.10)
    panel_a(V, a); panel_b(V, b); panel_c(V, c); panel_d(V, d); panel_e(V, e); panel_f(V, fig, f, fc); panel_g(V, fig, g, gc)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Seven panels on the {NSP} tree species of the 50-ha Barro Colorado plot. a: rank-abundance plot; abundances run from "
       f"{int(TOT.max())} stems to one, and a lognormal model fits best by AIC. b: the ten commonest species hold "
       f"{SHARE[:10].sum() * 100:.1f} % of {NSTEM} stems, led by Faramea occidentalis with {SHARE[0] * 100:.1f} %. c: occupancy "
       f"against abundance; {CLUMPED * 100:.0f} % of species occupy fewer plots than random placement predicts; {len(SINGLE)} "
       f"singletons. d: species accumulation reaches {NSP} at 50 ha; Chao1 estimates {POOL['chao'][0]:.0f} and the jackknife "
       f"{POOL['jack1'][0]:.0f}. e: Bray–Curtis similarity falls from {NEAR:.2f} for neighbouring plots to {FAR:.2f} at 900 m or "
       f"more (Mantel r = {MANTEL[0]:.2f}). f: {int(np.nanmin(GRID_R))} to {int(np.nanmax(GRID_R))} species per hectare, fewer on "
       f"the high plateau. g: Faramea occidentalis occurs in every plot, {int(np.nanmin(GRID_F))} to {int(np.nanmax(GRID_F))} stems.")

META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="seven-panel composite: rank-abundance with models, bars, occupancy-abundance, accumulation, distance decay, two grid maps",
            medium="paper", tool="matplotlib",
            data="Barro Colorado Island 50-ha plot, 1982 census, Condit et al. (2002), via R vegan::BCI and BCI.env", script=rel(__file__),
            alt=ALT,
            note=(f"radfit (vegan 2.7.5) Poisson fits to the pooled abundances; AIC: " +
                  ", ".join(f"{k} {AIC[k]:.0f}" for k, _ in MODELS) +
                  f". Species accumulation: specaccum, method random, 999 permutations, 2.5–97.5 % band. Chao1 {POOL['chao'][0]:.1f} "
                  f"(se {POOL['chao_se'][0]:.1f}), jackknife {POOL['jack1'][0]:.1f} (se {POOL['jack1_se'][0]:.1f}); intervals ±1.96 se. "
                  f"Distance decay: exponential with asymptote fitted by least squares, s = {DC:.2f} + {DA - DC:.2f} exp(−d / {DL:.0f} m); "
                  f"bin means of 100 m with ±1.96 se. Mantel test on Bray–Curtis dissimilarity and distance, Pearson, 999 permutations. "
                  f"Occupancy expected under Poisson placement: 50 (1 − exp(−N / 50)). {DOUBLE} species have two stems."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        print(save(draw(vellum.use(mode)), "ecology", "bci_forest", mode, meta=META if mode == "light" else None))
