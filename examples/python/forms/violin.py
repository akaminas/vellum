"""violin.py: the distribution of body mass in three penguin species as violins, the quartiles marked inside each, the
median as a ringed dot. A violin is a mirrored density; the area shows where birds are common, the dot where the middle is.
Data: data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from scipy import stats
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0"
SPECIES = ("Adelie", "Chinstrap", "Gentoo")             # slot order: teal, terracotta, indigo
P = penguins()
M = {s: np.array([r["Body Mass (g)"] for r in P if r["Species"] == s], float) for s in SPECIES}
MED = {s: np.median(m) for s, m in M.items()}
gap = MED["Gentoo"] - max(MED["Adelie"], MED["Chinstrap"])

TITLE = f"The median Gentoo penguin weighs {gap:,.0f} g more than the other two species"
SUB = f"Body mass of {len(P)} penguins of the Palmer Archipelago, 2007–2009 · violin: density · bar: quartiles · dot: median"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.12)
    for k, s in enumerate(SPECIES):
        ys = np.linspace(M[s].min(), M[s].max(), 200)
        d = stats.gaussian_kde(M[s], bw_method=0.35)(ys); d = 0.42 * d / d.max()
        ax.fill_betweenx(ys, k - d, k + d, color=V.tint(k), alpha=0.9, lw=0, zorder=2)
        ax.plot(np.r_[k - d, (k + d)[::-1]], np.r_[ys, ys[::-1]], color=V.tone(k), lw=V.thin * 1.4, zorder=3)
        q1, q2, q3 = np.percentile(M[s], [25, 50, 75])
        ax.plot([k, k], [q1, q3], color=V.deep(k) if V.mode == "light" else V.tone(k), lw=V.lw * 2.6, solid_capstyle="butt", zorder=4)
        ax.scatter([k], [q2], s=38, color=V.surface, edgecolor=V.tone(k), linewidth=1.6, zorder=5)
    ax.set_xlim(-0.65, 2.65); ax.grid(False, axis="x")
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{s}\nmedian {MED[s]:,.0f} g" for s in SPECIES], color=V.ink, fontsize=V.sz["annotation"])
    ax.set_ylim(2500, 6700); ax.set_yticks([3000, 4000, 5000, 6000])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    V.panel(ax, unit="body mass, g")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="violin plot", medium="screen", tool="matplotlib",
            data="Palmer penguins, Gorman, Williams and Fraser (2014), 342 birds with complete measurements", script=rel(__file__),
            alt=(f"Violins of body mass for three penguin species. Medians: Adelie {MED['Adelie']:,.0f} g, Chinstrap "
                 f"{MED['Chinstrap']:,.0f} g, Gentoo {MED['Gentoo']:,.0f} g. Gentoo is {gap:,.0f} g above the next species."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "violin", mode, meta=META)
