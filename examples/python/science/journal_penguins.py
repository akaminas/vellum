"""journal_penguins.py: a paper-mode figure (no title block, no footer; the claim is in the caption, in the manifest).
Simpson's paradox in penguin beaks: a, beak length against depth with a pooled fit and one fit per species; b, beak depth
by species and sex; c, the correlation pooled, per species and within groups, with 95 % intervals.
Data: data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SPECIES = ("Adelie", "Chinstrap", "Gentoo")
MARK, RING = 20, 1.0                                    # paper marks: 20 pt² markers with a 1.0 pt ring
P = penguins()
L = np.array([r["Beak Length (mm)"] for r in P]); D = np.array([r["Beak Depth (mm)"] for r in P])
SP = np.array([r["Species"] for r in P]); SEX = np.array([r["Sex"] if r["Sex"] in ("FEMALE", "MALE") else "" for r in P])


def centred(groups):
    """Length and depth with each group's mean taken out, for the within-group correlation."""
    lc, dc = L.astype(float).copy(), D.astype(float).copy()
    for g in set(groups):
        m = groups == g; lc[m] -= L[m].mean(); dc[m] -= D[m].mean()
    return lc, dc


def r_ci(x, y, k=1):
    """Pearson r and its 95 % interval by Fisher's z; k groups removed cost k − 1 degrees of freedom."""
    r = np.corrcoef(x, y)[0, 1]; se = 1 / np.sqrt(len(x) - 3 - (k - 1))
    return r, np.tanh(np.arctanh(r) - 1.96 * se), np.tanh(np.arctanh(r) + 1.96 * se)


known = SEX != ""
ROWS = [("all birds", r_ci(L, D), None)]
ROWS += [(s, r_ci(L[SP == s], D[SP == s]), k) for k, s in enumerate(SPECIES)]
ROWS += [("within species", r_ci(*centred(SP), k=3), None)]
lc, dc = centred(np.char.add(SP, SEX))
ROWS += [("within species and sex", r_ci(lc[known], dc[known], k=6), None)]
R = {name: v[0] for name, v, _ in ROWS}
dmean = {(s, x): D[(SP == s) & (SEX == x)].mean() for s in SPECIES for x in ("FEMALE", "MALE")}
sex_gap = [dmean[(s, "MALE")] - dmean[(s, "FEMALE")] for s in SPECIES]
gentoo_gap = [dmean[(s, x)] - dmean[("Gentoo", x)] for s in SPECIES[:2] for x in ("FEMALE", "MALE")]   # against the same sex


def letter(V, ax, ch, unit):
    """Bold panel letter and the unit line: V.panel draws the letter only together with a claim, so it is set here."""
    ax.set_title(ch, color=V.ink, pad=16)
    V.panel(ax, unit=unit)


def dots(V, ax, x, y, color, s=MARK, z=4):
    ax.scatter(x, y, s=s, color=color, edgecolor=V.surface, linewidth=RING, zorder=z)


def panel_a(V, ax):
    for k, s in enumerate(SPECIES):
        m = SP == s; dots(V, ax, L[m], D[m], V.tone(k), z=2)
    xs = np.array([L.min(), L.max()]); b, a = np.polyfit(L, D, 1)
    ax.plot(xs, a + b * xs, color=V.rule, zorder=3)                                   # the pooled fit, the misleading one
    ax.annotate("all birds", (xs[-1], a + b * xs[-1]), xytext=(3, -2), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["annotation"], color=V.ink)
    place = {"Adelie": ("left", (-4, 0), "right"), "Chinstrap": ("right", (4, 0), "left"), "Gentoo": ("right", (4, 0), "left")}
    for k, s in enumerate(SPECIES):
        m = SP == s; xs = np.array([L[m].min(), L[m].max()]); b, a = np.polyfit(L[m], D[m], 1)
        ax.plot(xs, a + b * xs, color=V.tone(k), zorder=4)
        end, off, ha = place[s]; xe = xs[0] if end == "left" else xs[-1]
        ax.annotate(s, (xe, a + b * xe), xytext=off, textcoords="offset points", ha=ha, va="center",
                    fontsize=V.sz["annotation"], color=V.ink, zorder=5,
                    path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
    ax.set_xlim(26, 66); ax.set_xticks([30, 40, 50, 60])
    ax.set_ylim(12.5, 22); ax.set_yticks([14, 16, 18, 20, 22])
    ax.set_xlabel("beak length, mm")
    letter(V, ax, "a", "beak depth, mm")


def panel_b(V, ax):
    rng = np.random.default_rng(1)                                                   # a fixed jitter, so the figure regenerates
    for k, s in enumerate(SPECIES):
        for j, (x, dx) in enumerate((("FEMALE", -0.19), ("MALE", 0.19))):
            m = (SP == s) & (SEX == x)
            ax.scatter(k + dx + rng.uniform(-0.07, 0.07, m.sum()), D[m], s=5, color=V.tint(k), lw=0, zorder=2)
            dots(V, ax, k + dx, D[m].mean(), V.tone(k), s=MARK * 1.6)
            if k == 0:                                                               # the sexes are named once, under Adelie
                ax.annotate(x.lower(), (k + dx, D[m].min()), xytext=(0, -5), textcoords="offset points", ha="center",
                            va="top", fontsize=V.sz["annotation"], color=V.muted)
    ax.set_xlim(-0.5, 2.5); ax.set_xticks(range(3)); ax.set_xticklabels(SPECIES)
    ax.set_ylim(12.5, 22); ax.set_yticks([14, 16, 18, 20, 22])
    letter(V, ax, "b", "beak depth, mm")


def panel_c(V, ax):
    for i, (name, (r, lo, hi), k) in enumerate(ROWS):
        col = V.tone(k) if k is not None else V.rule if name == "all birds" else V.secondary
        ax.plot([lo, hi], [i, i], color=V.secondary, lw=0.7, zorder=2)                 # the interval, as an error bar
        dots(V, ax, r, i, col)
        ax.annotate(f"{r:.2f}".replace("-", "−"), (hi, i), xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=V.sz["annotation"], color=V.ink, path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
    ax.axvline(0, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=1)
    ax.set_yticks(range(len(ROWS))); ax.set_yticklabels([n for n, _, _ in ROWS]); ax.set_ylim(len(ROWS) - 0.4, -0.6)
    ax.set_xlim(-0.5, 1); ax.set_xticks([-0.5, 0, 0.5, 1])
    ax.set_xlabel("Pearson r, length and depth")
    letter(V, ax, "c", "r with its 95 % interval")


def draw(V):
    plt.rcParams["lines.linewidth"] = 1.2                                           # paper: lines 1.2 pt
    fig = plt.figure(figsize=V.size("double"))
    gs = fig.add_gridspec(1, 3, left=0.055, right=0.975, top=0.86, bottom=0.17, wspace=0.42, width_ratios=[1.15, 1, 1])
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    panel_a(V, a); panel_b(V, b); panel_c(V, c)
    # c carries long row names at its left: move it right by their width so they sit in the gap, not over b
    fig.canvas.draw()
    w = max(t.get_window_extent().width for t in c.get_yticklabels()) / fig.dpi / fig.get_size_inches()[0]
    p = c.get_position(); c.set_position([p.x0 + w * 0.55, p.y0, p.width - w * 0.55, p.height])
    return fig


CAPTION = (
    f"Beak depth falls with beak length across all penguins but rises within every species. "
    f"a, Beak length against beak depth for {len(P)} penguins; the grey line is the least-squares fit to all birds "
    f"(r = {R['all birds']:.2f}), the coloured lines are fits within each species (r = {R['Adelie']:.2f}, {R['Chinstrap']:.2f} "
    f"and {R['Gentoo']:.2f} for Adelie, Chinstrap and Gentoo). "
    f"b, Beak depth by species and sex; small dots are birds, ringed dots are means. Gentoo beaks are "
    f"{min(gentoo_gap):.1f} to {max(gentoo_gap):.1f} mm shallower than those of the other species of the same sex, and males are deeper than females by "
    f"{min(sex_gap):.1f} to {max(sex_gap):.1f} mm in every species, so the differences between species, not the relation within them, make the pooled slope negative. "
    f"c, Pearson r between beak length and depth with 95 % intervals from Fisher's z: the sign turns positive once species is "
    f"taken into account (r = {R['within species']:.2f}) and stays positive within species and sex (r = {R['within species and sex']:.2f}). "
    f"n = {len(P)} birds with complete measurements, {known.sum()} with recorded sex (b and the last row of c). "
    f"Data: Palmer penguins, Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; "
    f"via the palmerpenguins R package and vega-datasets 2.8.0; "
    f"figure drawn by examples/python/science/journal_penguins.py at git {stamp()}.").replace("-0", "−0")

META = dict(title=CAPTION.split(". ")[0], subtitle="Paper-mode figure: no title block or footer; the claim is the caption's first sentence",
            kind="scientific", form="three-panel figure: scatter with fits, dot plot with means, interval plot", medium="paper",
            tool="matplotlib", data="Palmer penguins, Gorman, Williams and Fraser (2014), 342 birds with complete measurements",
            script=rel(__file__), caption=CAPTION,
            alt=(f"Three panels. a: beak depth against beak length; the pooled fit slopes down (r = {R['all birds']:.2f}) while each "
                 f"species' fit slopes up. b: Gentoo beaks are about {np.mean(gentoo_gap):.1f} mm shallower than Adelie and Chinstrap in both "
                 f"sexes. c: correlations with intervals, negative pooled and positive within species ({R['within species']:.2f}).").replace("-0", "−0"))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "journal_penguins", mode, meta=META)
