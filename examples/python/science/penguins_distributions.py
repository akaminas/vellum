"""penguins_distributions.py: two distributions per species. a, a ridgeline of body mass (Gaussian kernel density written
with numpy); b, box plots of beak depth over a beeswarm of the birds. Data: data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = ("Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER;\n"
          "via the palmerpenguins R package and vega-datasets 2.8.0")
SPECIES = ("Adelie", "Chinstrap", "Gentoo")             # slot order, rows from the top
BW = 150                                                # kernel bandwidth, g
P = penguins()
MASS = {s: np.array([r["Body Mass (g)"] for r in P if r["Species"] == s], float) for s in SPECIES}
DEPTH = {s: np.array([r["Beak Depth (mm)"] for r in P if r["Species"] == s], float) for s in SPECIES}
med_m = {s: np.median(v) for s, v in MASS.items()}
med_d = {s: np.median(v) for s, v in DEPTH.items()}
heavier = med_m["Gentoo"] - max(med_m["Adelie"], med_m["Chinstrap"])
shallower = min(med_d["Adelie"], med_d["Chinstrap"]) - med_d["Gentoo"]
assert heavier > 0 and shallower > 0, "the title claims Gentoo are heaviest and shallowest"

TITLE = f"Gentoo penguins are the heaviest by {heavier:,.0f} g, yet have the shallowest beaks by {shallower:.1f} mm"
SUB = (f"{len(P)} penguins of the Palmer Archipelago, 2007–2009 · a: Gaussian kernel density, bandwidth {BW} g · "
       f"b: one dot per bird")


def kde(x, grid, bw):
    """Gaussian kernel density estimate of the sample x on grid, bandwidth bw."""
    z = (grid[:, None] - x[None, :]) / bw
    return np.exp(-0.5 * z ** 2).sum(axis=1) / (len(x) * bw * np.sqrt(2 * np.pi))


def beeswarm(x, d):
    """Offsets for a one-row beeswarm: each point takes the smallest |offset| at which it is d away from those placed."""
    order = np.argsort(x); off = np.zeros(len(x)); placed = []
    for i in order:
        for k in range(200):
            o = (k + 1) // 2 * d * (1 if k % 2 else -1)
            if all((x[i] - x[j]) ** 2 + (o - off[j]) ** 2 >= d * d for j in placed if abs(x[i] - x[j]) < d):
                off[i] = o; break
        placed.append(i)
    return off


def ridgeline(V, ax):
    grid = np.linspace(1800, 7000, 520)
    dens = {s: kde(MASS[s], grid, BW) for s in SPECIES}
    peak = max(d.max() for d in dens.values())
    for k, s in enumerate(SPECIES):
        base = len(SPECIES) - 1 - k                      # rows in slot order from the top
        y = base + 1.25 * dens[s] / peak
        on = dens[s] > 0.01 * peak                       # draw the curve where the density is, not along the empty baseline
        ax.fill_between(grid[on], base, y[on], color=V.tint(k), alpha=0.3, lw=0, zorder=2 + k)
        ax.plot(grid[on], y[on], color=V.tone(k), lw=V.lw, zorder=2 + k)
        V.dot(ax, med_m[s], base, V.tone(k), z=6 + k)
        side = -1 if s == "Gentoo" else 1                # the median label goes where the curve is not
        xl = grid[dens[s] > 0.02 * peak][0 if side < 0 else -1]
        ax.text(xl + side * 120, base + 0.12, f"median {med_m[s]:,.0f} g", ha="right" if side < 0 else "left", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink, zorder=10)
    ax.set_yticks(range(len(SPECIES))); ax.set_yticklabels(SPECIES[::-1])
    ax.set_ylim(-0.08, len(SPECIES) + 0.35)
    ax.set_xlim(2100, 6800); ax.set_xticks([3000, 4000, 5000, 6000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlabel("body mass, g")
    V.note(ax, 2150, len(SPECIES) + 0.3, "dot: median")
    V.panel(ax, "a", f"Gentoo are {heavier:,.0f} g heavier at the median", unit="density of body mass, one row per species")


def boxes(V, ax, fig):
    fig.canvas.draw()
    w_in = ax.get_window_extent().width / fig.dpi; h_in = ax.get_window_extent().height / fig.dpi
    xlo, xhi, nrow = 12.5, 22.5, len(SPECIES)
    d_in = 0.034                                            # dot spacing, inches (a 5 pt² dot is about 0.031 in across)
    for k, s in enumerate(SPECIES):
        row = nrow - 1 - k; v = DEPTH[s]
        q1, med, q3 = np.percentile(v, [25, 50, 75]); iqr = q3 - q1
        lo, hi = v[v >= q1 - 1.5 * iqr].min(), v[v <= q3 + 1.5 * iqr].max()
        ax.add_patch(Rectangle((q1, row - 0.22), q3 - q1, 0.44, facecolor=V.tint(k), edgecolor=V.tone(k), lw=V.thin, zorder=2))
        ax.plot([lo, q1], [row, row], color=V.tone(k), lw=V.thin, zorder=2)
        ax.plot([q3, hi], [row, row], color=V.tone(k), lw=V.thin, zorder=2)
        # the swarm is computed in inches so the dots do not touch, then put back into data units
        off = beeswarm(v * w_in / (xhi - xlo), d_in) * (ax.get_ylim()[1] - ax.get_ylim()[0]) / h_in
        ax.scatter(v, row + off, s=5, color=V.tone(k), edgecolor=V.surface, linewidth=0.4, zorder=3)
        ax.plot([med, med], [row - 0.22, row + 0.22], color=V.tone(k), lw=V.lw, zorder=4, solid_capstyle="butt")
        ax.text(med, row + max(0.25, off.max() + 0.06), f"median {med:.1f} mm", ha="center", va="bottom",
                fontsize=V.sz["annotation"], color=V.ink, zorder=5, path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
    ax.set_xlim(xlo, xhi); ax.set_xticks([14, 16, 18, 20, 22])
    ax.set_xlabel("beak depth, mm")
    ax.grid(False)                                         # the rows are categories; no value grid on y
    V.panel(ax, "b", f"but their beaks are {shallower:.1f} mm shallower",
            unit="box: middle half of the birds, line: median, whiskers: 1.5 × the box")


def draw(V):
    fig = plt.figure(figsize=V.size("double_tall"))
    gs = fig.add_gridspec(1, 2, left=0.09, right=0.98, top=0.77, bottom=0.155, wspace=0.30)
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    ridgeline(V, a)
    b.set_ylim(-0.6, len(SPECIES) - 0.4); b.set_yticks(range(len(SPECIES))); b.set_yticklabels(SPECIES[::-1])
    boxes(V, b, fig)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="ridgeline and box plots with a beeswarm", medium="screen",
            tool="matplotlib", data="Palmer penguins, Gorman, Williams and Fraser (2014), 342 birds with complete measurements",
            script=rel(__file__),
            alt=(f"Two panels. a: body-mass densities per species; Gentoo peak near {med_m['Gentoo']:,.0f} g, Adelie and Chinstrap "
                 f"near {med_m['Adelie']:,.0f} g. b: box plots of beak depth; Gentoo median {med_d['Gentoo']:.1f} mm against "
                 f"{med_d['Adelie']:.1f} and {med_d['Chinstrap']:.1f} mm for Adelie and Chinstrap."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "penguins_distributions", mode, meta=META)
