"""doubs_fish.py: the fish of the Doubs river (30 sites, 27 species) as a six-panel composite about one polluted stretch.

a  the river drawn from the site coordinates, source to mouth; dot area is the number of species at the site
b  along the river: species per site, and dissolved oxygen and ammonium below it on the same distance axis
c  the community table: 27 species by 30 sites in river order, species ordered by their abundance-weighted mean
   distance from the source; abundance classes 0–5 as recorded
d  beta diversity between neighbouring sites, Sørensen dissimilarity split into turnover (Simpson) and nestedness-
   resultant parts (Baselga 2010), computed here
e  tb-RDA of the Hellinger-transformed abundances on forward-selected environmental variables (vegan; scaling 1)
f  variation partitioning, environment against space (PCNM of the coordinates), as an area-proportional Euler diagram

The polluted stretch, sites 23–25 (ammonium and biological oxygen demand at their highest, oxygen at its lowest), is
terracotta in every panel; the rest is grey or neutral.
Data: data/ecology/doubs_*.csv, from ade4::doubs (Verneaux 1973), exported and analysed by export_data.R.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco import *
from matplotlib.patches import Circle, Rectangle

SOURCE = "Data: Doubs river fish (Verneaux 1973), via R ade4::doubs; analyses after Borcard, Gillet and Legendre (2018)"
F = table("doubs_fish.csv"); E = table("doubs_env.csv"); SPT = table("doubs_species.csv")
RS = table("doubs_rda_sites.csv"); RSP = table("doubs_rda_species.csv"); RA = table("doubs_rda_arrows.csv"); RFIT = table("doubs_rda_fit.csv")
VP = table("doubs_varpart.csv")
CODES = [k for k in F if k != "site"]; A = np.array([F[k] for k in CODES]).T                  # 30 sites x 27 species, classes 0-5
NAME = dict(zip(SPT["code"], SPT["English"])); SCI = dict(zip(SPT["code"], SPT["Scientific"]))
SITE = F["site"].astype(int); NS = len(SITE)
KM = E["dfs"] / 10; X, Y = E["x"], E["y"]                                                     # dfs is recorded in tenths of a km
OXY = E["oxy"] / 10; AMM = E["amm"] / 100; BOD = E["bdo"] / 10                                 # mg per litre
RICH = (A > 0).sum(1)
POL = np.isin(SITE, [23, 24, 25])
FR = dict(zip(VP["fraction"], VP["adj_r2"])); FP = dict(zip(VP["fraction"], VP["p"]))
EVARS = str(RFIT["selected"][0]).split(";"); NSPACE = len(str(VP["space_vars"][0]).split(";"))


def baselga(a_, b_):
    """Sørensen dissimilarity and its turnover (Simpson) and nestedness-resultant parts for two presence vectors."""
    a = np.sum(a_ & b_); b = np.sum(a_ & ~b_); c = np.sum(~a_ & b_)
    if a + b + c == 0 or (a_.sum() == 0 or b_.sum() == 0): return np.nan, np.nan, np.nan
    sor = (b + c) / (2 * a + b + c); sim = min(b, c) / (a + min(b, c))
    return sor, sim, sor - sim


PA = A > 0
BETA = np.array([baselga(PA[i], PA[i + 1]) for i in range(NS - 1)])                            # interval i: site i+1 to i+2
WMEAN = (A * KM[:, None]).sum(0) / A.sum(0)                                                   # abundance-weighted position

# ---- the claims, checked
up = SITE == 22; low = SITE == 23; down = SITE == 26
assert RICH[up][0] == 22 and RICH[low][0] == 3 and RICH[down][0] == 21
assert set(np.argsort(-AMM)[:3]) == set(np.where(POL)[0]) and POL[np.argmin(OXY)]
assert set(np.argsort(-BOD)[:3]) == set(np.where(POL)[0])
assert RICH[SITE == 8][0] == 0
B_IN = BETA[21, 0]; B_OUT = BETA[24, 0]                                                       # 22→23 and 25→26
NEST_IN = BETA[21, 2] / BETA[21, 0]
assert B_IN == np.nanmax(BETA[9:, 0]) or B_IN > 0.6

TITLE = (f"Doubs fish fall from {RICH[up][0]} species to {RICH[low][0]} at a polluted stretch, "
         f"and recover below it")
SUB = (f"{NS} sites over {KM[-1]:.0f} km, {len(CODES)} species · terracotta: sites 23–25, "
       f"ammonium up to {AMM.max():.1f} mg/L, oxygen down to {OXY.min():.1f} mg/L")


def grey(V): return V.secondary if V.mode == "light" else V.muted


# ---------------------------------------------------------------- a  the river
def panel_a(V, ax):
    ax.plot(X, Y, color=V.tint("teal"), lw=3.2, solid_capstyle="round", zorder=1)
    s = 6 + 3.2 * RICH
    for i in range(NS):
        if RICH[i] == 0:
            ax.scatter(X[i], Y[i], s=14, facecolor=V.surface, edgecolor=grey(V), lw=0.8, zorder=3)
        else:
            ax.scatter(X[i], Y[i], s=s[i], color=V.tone("terracotta") if POL[i] else grey(V), edgecolor=V.surface, lw=0.9,
                       zorder=4 if POL[i] else 3)
    lab = {1: ("source, site 1", (6, -4), "left", "top"), 30: ("mouth into the Saône, site 30", (2, -9), "left", "top"),
           8: ("site 8: no fish", (8, 0), "left", "center"), 16: ("16", (7, 0), "left", "center"),
           23: ("23", (5, 6), "left", "bottom"), 24: ("24", (0, 8), "center", "bottom"), 25: ("25", (-4, 7), "right", "bottom"),
           26: ("26", (-6, -7), "right", "top"), 22: ("22", (8, 0), "left", "center")}
    for k, (t, off, ha, va) in lab.items():
        i = k - 1
        ax.annotate(t, (X[i], Y[i]), xytext=off, textcoords="offset points", ha=ha, va=va, fontsize=V.sz["annotation"],
                    color=V.ink if k in (23, 24, 25) else V.secondary, path_effects=halo(V))
    # size key
    for j, n in enumerate((5, 15, 25)):
        ax.scatter(48 + j * 24, 238, s=6 + 3.2 * n, color=V.card, edgecolor=grey(V), lw=0.7, zorder=3)
        text(V, ax, 48 + j * 24, 224, f"{n}", color=V.muted, ha="center", va="center", size=V.sz["unit_line"])
    text(V, ax, 34, 238, "species", color=V.muted, ha="right", va="center", size=V.sz["unit_line"])
    ax.set_xlim(-5, 285); ax.set_ylim(-5, 250); ax.set_aspect("equal")
    ax.set_xticks([0, 100, 200]); ax.set_yticks([0, 100, 200]); ax.set_xticklabels(["0", "100", "200 km"])
    ax.grid(False); clean(ax, grid=False)
    head(V, ax, "a", "The river, source to mouth", unit="site coordinates, km · dot area: species")


# ---------------------------------------------------------------- b  along the river
def shade(V, ax, top):
    k0, k1 = KM[POL].min(), KM[POL].max()
    ax.axvspan(k0 - 4, k1 + 4, color=V.tint("terracotta"), alpha=0.35 if V.mode == "light" else 0.3, lw=0, zorder=0)


def panel_b(V, ax1, ax2, ax3):
    for ax in (ax1, ax2, ax3): shade(V, ax, None)
    m = RICH > 0
    ax1.plot(KM, RICH, color=V.rule, lw=1.0, zorder=2)
    V.dot(ax1, KM[m & ~POL], RICH[m & ~POL], grey(V), s=16, z=3, ring=0.8)
    V.dot(ax1, KM[POL], RICH[POL], V.tone("terracotta"), s=22, z=4, ring=0.8)
    ax1.scatter(KM[~m], RICH[~m], s=14, facecolor=V.surface, edgecolor=grey(V), lw=0.8, zorder=4)
    ax1.annotate(f"{RICH[up][0]}", (KM[up][0], RICH[up][0]), xytext=(-5, 3), textcoords="offset points", ha="right", va="bottom",
                 fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    ax1.annotate(f"{RICH[low][0]} species", (KM[low][0], RICH[low][0]), xytext=(4, -2), textcoords="offset points", ha="left",
                 va="top", fontsize=V.sz["annotation"], color=V.ink, fontweight="bold", path_effects=halo(V))
    ax1.annotate(f"{RICH[down][0]}", (KM[down][0], RICH[down][0]), xytext=(5, 3), textcoords="offset points", ha="left", va="bottom",
                 fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    ax1.set_ylim(0, 30); ax1.set_yticks([0, 10, 20, 30])
    for ax, v, col, unit, lim, ticks in ((ax2, OXY, V.tone("teal"), "dissolved oxygen, mg/L", (3, 13.5), [4, 8, 12]),
                                          (ax3, AMM, V.tone("indigo"), "ammonium, mg/L", (0, 2.0), [0, 1, 2])):
        ax.plot(KM, v, color=col, lw=1.3, zorder=2)
        V.dot(ax, KM[POL], v[POL], V.tone("terracotta"), s=16, z=4, ring=0.8)
        ax.set_ylim(*lim); ax.set_yticks(ticks)
        ax.text(0, 1.04, unit, transform=ax.transAxes, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")
    for ax in (ax1, ax2, ax3): ax.set_xlim(-5, 460); ax.set_xticks([0, 100, 200, 300, 400])
    ax1.set_xticklabels([]); ax2.set_xticklabels([])
    ax3.set_xlabel("distance from the source, km")
    text(V, ax1, (KM[POL].min() + KM[POL].max()) / 2, 29.5, "sites 23–25", color=V.deep("terracotta") if V.mode == "light"
         else V.tone("terracotta"), ha="center", va="top")
    head(V, ax1, "b", "Where oxygen drops and ammonium peaks, the fish go", unit="species per site")


# ---------------------------------------------------------------- c  the community table
def panel_c(V, fig, ax, cax):
    so = np.argsort(WMEAN, kind="stable")
    cm = V.cmap_gradient("lagoon")
    Z = A[:, so].T.astype(float); Z[Z == 0] = np.nan
    ax.set_facecolor(V.card)
    im = ax.imshow(Z, aspect="auto", cmap=cm, vmin=0.5, vmax=5.5, interpolation="nearest", extent=(0.5, NS + 0.5, len(CODES) - 0.5, -0.5))
    for j in range(NS + 1): ax.axvline(j + 0.5, color=V.surface, lw=0.6)
    for i in range(len(CODES) + 1): ax.axhline(i - 0.5, color=V.surface, lw=0.6)
    k0 = 22.5
    ax.add_patch(Rectangle((k0, -0.5), 3, len(CODES), facecolor="none", edgecolor=V.tone("terracotta"), lw=1.4, zorder=5))
    ax.set_xlim(0.5, NS + 0.5); ax.set_ylim(len(CODES) - 0.5, -0.5)
    ax.set_xticks([1, 5, 10, 15, 20, 23, 25, 30]); ax.tick_params(axis="x", pad=2)
    ax.set_yticks(range(len(CODES))); ax.set_yticklabels([NAME[CODES[i]].lower() for i in so])
    ax.tick_params(axis="y", labelsize=V.sz["unit_line"] - 0.5, labelcolor=V.secondary, pad=3)
    clean(ax, grid=False); ax.set_xlabel("site, source to mouth")
    text(V, ax, 24, -0.9, "polluted", color=V.deep("terracotta") if V.mode == "light" else V.tone("terracotta"), ha="center", va="bottom")
    cb = fig.colorbar(im, cax=cax); cb.outline.set_visible(False); cb.set_ticks([1, 2, 3, 4, 5])
    cb.ax.tick_params(size=0, labelsize=V.sz["unit_line"], colors=V.muted)
    cax.set_title("class", fontsize=V.sz["unit_line"], color=V.muted, loc="left", pad=4, fontweight="normal", linespacing=1.0)
    fig.canvas.draw()
    w = max(t.get_window_extent(fig.canvas.get_renderer()).width for t in ax.get_yticklabels()) / fig.dpi + 3 / 72
    head(V, ax, "c", "Trout give way to cyprinids downstream; at 23–25 almost every species is missing",
         unit="species ordered by their mean position along the river · blank: absent", dx_in=w)


# ---------------------------------------------------------------- d  beta diversity between neighbours
def panel_d(V, ax):
    x = np.arange(NS - 1) + 1.5                                                               # between site i and i+1
    sim, sne = BETA[:, 1], BETA[:, 2]
    ok = ~np.isnan(sim)
    pol_iv = np.isin(np.arange(NS - 1), [21, 22, 23, 24])                                     # intervals touching 23-25
    c_sim = [V.tone("terracotta") if p else grey(V) for p in pol_iv]
    c_sne = [V.tint("terracotta") if p else V.rule for p in pol_iv]
    ax.bar(x[ok], sim[ok], width=0.72, color=np.array(c_sim)[ok], edgecolor="none", zorder=2)
    ax.bar(x[ok], sne[ok], bottom=sim[ok], width=0.72, color=np.array(c_sne)[ok], edgecolor="none", zorder=2)
    for i in np.where(~ok)[0]:
        text(V, ax, x[i], 0.02, "×", color=V.muted, ha="center", va="bottom")
    text(V, ax, 8, 0.45, "× site 8\nhas no fish", color=V.muted, ha="center", va="bottom", linespacing=1.0, size=V.sz["unit_line"])
    ax.annotate(f"22 → 23: {B_IN:.2f},\n{NEST_IN * 100:.0f} % of it\nnestedness: species lost,\nnot replaced", (22.5, B_IN),
                xytext=(-8, -2), textcoords="offset points", ha="right", va="top", fontsize=V.sz["annotation"], color=V.ink,
                linespacing=1.0, path_effects=halo(V))
    ax.annotate(f"25 → 26: {B_OUT:.2f}", (25.5, B_OUT), xytext=(4, 3), textcoords="offset points", ha="left", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    # key, direct, on the first clear bar pair
    ax.set_xlim(0.8, NS + 0.2); ax.set_ylim(0, 1.0); ax.set_yticks([0, 0.5, 1.0])
    ax.set_xticks([1, 10, 20, 23, 26, 30]); ax.set_xlabel("between neighbouring sites, source to mouth")
    text(V, ax, 1.0, 0.97, "lower part: turnover (Simpson)\nupper part: nestedness", color=V.muted, ha="left", va="top", linespacing=1.05,
         size=V.sz["unit_line"])
    head(V, ax, "d", "Pollution removes species, it does not swap them", unit="Sørensen dissimilarity to the next site")


# ---------------------------------------------------------------- e  RDA
def panel_e(V, ax):
    pts = np.column_stack([RS["rda1"], RS["rda2"]]); s = RS["site"].astype(int); pol = np.isin(s, [23, 24, 25])
    ax.plot(pts[:, 0], pts[:, 1], color=V.grid, lw=0.6, zorder=1)                           # sites joined in river order
    V.dot(ax, pts[~pol, 0], pts[~pol, 1], grey(V), s=14, z=3, ring=0.7)
    V.dot(ax, pts[pol, 0], pts[pol, 1], V.tone("terracotta"), s=22, z=4, ring=0.8)
    for k in (1, 30):
        i = list(s).index(k)
        ax.annotate(f"{k}", pts[i], xytext=(4, 3), textcoords="offset points", fontsize=V.sz["unit_line"], color=V.secondary)
    names = {"dfs": "distance\nfrom source", "oxy": "oxygen", "bdo": "oxygen\ndemand"}
    lim = np.abs(pts).max() * 1.25; L = 0.8 * lim
    for v, x0, y0 in zip(RA["variable"], RA["rda1"], RA["rda2"]):
        d = np.array([x0, y0]) * L
        ax.annotate("", d, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=V.ink, lw=0.9, mutation_scale=7,
                                                         shrinkA=0, shrinkB=0), zorder=5)
        text(V, ax, d[0] * 1.1, d[1] * 1.1, names[v], ha="left" if d[0] > 0 else "right", va="center", color=V.ink,
             linespacing=1.0, path_effects=halo(V))
    ax.axhline(0, color=V.grid, lw=0.6, zorder=0); ax.axvline(0, color=V.grid, lw=0.6, zorder=0)
    ax.set_xlim(-lim, lim); ax.set_ylim(min(pts[:, 1].min(), -lim * 0.5) * 1.15, max(pts[:, 1].max(), lim * 0.5) * 1.15)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    ax.set_xlabel(f"RDA 1, {RFIT['axis1'][0] * 100:.0f} % of variation")
    head(V, ax, "e", f"Three variables explain {RFIT['adj_r2'][0] * 100:.0f} %",
         unit=f"RDA 2, {RFIT['axis2'][0] * 100:.0f} % · sites joined in river order")


# ---------------------------------------------------------------- f  Euler diagram
def panel_f(V, ax):
    r1, r2, d = euler_geometry(FR["env_total"], FR["space_total"], FR["shared"])
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=V.card, edgecolor=V.rule, lw=0.6, zorder=0))
    cy = 0.5; c1 = (0.5 - d / 2, cy); c2 = (0.5 + d / 2, cy)
    ax.add_patch(Circle(c1, r1, facecolor=V.tint("moss"), edgecolor="none", alpha=0.75, zorder=1))
    ax.add_patch(Circle(c2, r2, facecolor=V.tint("mauve"), edgecolor="none", alpha=0.55, zorder=2))
    ax.add_patch(Circle(c1, r1, facecolor="none", edgecolor=V.tone("moss"), lw=1.1, zorder=3))
    ax.add_patch(Circle(c2, r2, facecolor="none", edgecolor=V.tone("mauve"), lw=1.1, zorder=3))
    pct = lambda v: f"{v * 100:.0f} %"
    text(V, ax, 0.5, cy + 0.03, pct(FR["shared"]), color=V.ink, ha="center", va="bottom", size=V.sz["panel_title"] + 2, fontweight="bold")
    text(V, ax, 0.5, cy - 0.01, "shared", color=V.ink, ha="center", va="top")
    for (edge, sgn, lab, v) in ((c1[0] - r1, -1, "habitat\nalone", FR["env_only"]), (c2[0] + r2, 1, "space\nalone", FR["space_only"])):
        ax.annotate(f"{pct(v)}\n{lab}", (edge - sgn * 0.03, cy), xytext=(0.5 + sgn * 0.64, cy), textcoords="data",
                    ha="right" if sgn < 0 else "left", va="center", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.0,
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=2, shrinkB=0))
    text(V, ax, 0.0, 1.03, f"habitat {pct(FR['env_total'])}", color=V.deep("moss") if V.mode == "light" else V.tone("moss"),
         ha="left", va="bottom", size=V.sz["unit_line"])
    text(V, ax, 1.0, -0.03, f"space {pct(FR['space_total'])}", color=V.deep("mauve") if V.mode == "light" else V.tone("mauve"),
         ha="right", va="top", size=V.sz["unit_line"])
    text(V, ax, -0.03, 0.0, pct(FR["residual"]) + "\nunexplained", color=V.muted, ha="right", va="bottom", size=V.sz["unit_line"],
         linespacing=1.0)
    ax.set_xlim(-0.45, 1.45); ax.set_ylim(-0.14, 1.12); ax.set_aspect("equal"); ax.axis("off")
    head(V, ax, "f", "Space and habitat overlap", unit="square: all · areas: adjusted R²")


def draw(V):
    fig = plt.figure(figsize=(7.2, 9.7))
    a = axes_in(fig, 0.30, 1.30, 2.55, 2.28)
    b1 = axes_in(fig, 3.55, 1.30, 3.50, 1.00); b2 = axes_in(fig, 3.55, 2.62, 3.50, 0.42); b3 = axes_in(fig, 3.55, 3.30, 3.50, 0.42)
    c = axes_in(fig, 1.30, 4.62, 5.40, 2.25); cc = axes_in(fig, 6.82, 4.95, 0.07, 1.10)
    d = axes_in(fig, 0.42, 7.72, 2.85, 1.35)
    e = axes_in(fig, 3.55, 7.72, 1.75, 1.35)
    f = axes_in(fig, 5.55, 7.72, 1.65, 1.10)
    panel_a(V, a); panel_b(V, b1, b2, b3); panel_c(V, fig, c, cc); panel_d(V, d); panel_e(V, e); panel_f(V, f)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Six panels on the fish of the Doubs river. a: the river from source to mouth with dots sized by species per site. "
       f"b: species per site against distance from the source; richness falls from {RICH[up][0]} at site 22 to {RICH[low][0]} at "
       f"site 23 ({KM[low][0]:.0f} km), where oxygen is lowest and ammonium highest, and recovers to {RICH[down][0]} at site 26. "
       f"c: the 27-species community table in river order shows trout-zone species upstream, cyprinids downstream, and empty "
       f"columns at sites 23–25. d: Sørensen dissimilarity between neighbouring sites peaks at {B_IN:.2f} entering the stretch, "
       f"{NEST_IN * 100:.0f} % of it nestedness. e: RDA on distance from source, oxygen and oxygen demand explains "
       f"{RFIT['adj_r2'][0] * 100:.0f} % (adjusted). f: environment and space share {FR['shared'] * 100:.0f} % of the variation.")

META = dict(title=TITLE, subtitle=SUB, kind="composite",
            form="six-panel composite: river map, profiles, community table, beta-diversity partition, RDA triplot, Euler diagram",
            medium="paper", tool="matplotlib",
            data="Doubs river fish, Verneaux (1973), 30 sites × 27 species, via R ade4::doubs", script=rel(__file__), alt=ALT,
            note=(f"Abundance classes 0–5 as recorded. Site 8 has no fish and is left out of the RDA and the partition. tb-RDA on "
                  f"Hellinger-transformed abundances with standardised environment; forward selection (ordiR2step, double stopping) kept "
                  f"{', '.join(EVARS)}; adjusted R² {RFIT['adj_r2'][0]:.3f} (all 11 variables {RFIT['adj_r2_full'][0]:.3f}), p = "
                  f"{RFIT['p'][0]:.3f}. Variation partitioning against {NSPACE} forward-selected PCNM eigenfunctions of the site "
                  f"coordinates: environment alone {FR['env_only']:.3f} (p = {FP['env_only']:.3f}), shared {FR['shared']:.3f}, space "
                  f"alone {FR['space_only']:.3f} (p = {FP['space_only']:.3f}), residual {FR['residual']:.3f}. Beta diversity: "
                  f"Baselga (2010) partition of Sørensen into Simpson turnover and nestedness-resultant dissimilarity, presence–absence, "
                  f"computed in the script. Units: dfs in the data is tenths of a km, oxygen tenths of mg/L, ammonium hundredths of mg/L."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        print(save(draw(vellum.use(mode)), "ecology", "doubs_fish", mode, meta=META if mode == "light" else None))
