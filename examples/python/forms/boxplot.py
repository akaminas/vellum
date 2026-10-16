"""boxplot.py: fish species per site along the river Doubs in three stretches of ten sites, as box plots with every site
shown beside its box. Box: quartiles, line: median, whiskers: the range. Data: data/ecology/doubs_fish.csv."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Verneaux (1973), Doubs river fish, France and Switzerland; via R ade4::doubs"
F = load_csv("ecology/doubs_fish.csv"); E = load_csv("ecology/doubs_env.csv")
CODES = [c for c in F[0] if c != "site"]
RICH = np.array([sum(float(r[c]) > 0 for c in CODES) for r in F])
KM = np.array([float(r["dfs"]) / 10 for r in E])
ORDER = np.argsort(KM)
GROUPS = [("Upstream", ORDER[:10]), ("Middle", ORDER[10:20]), ("Downstream", ORDER[20:])]       # slot order: teal, terracotta, indigo
MED = [np.median(RICH[i]) for _, i in GROUPS]

TITLE = f"Fish richness climbs from {MED[0]:.0f} species per site near the source to {MED[2]:.0f} near the mouth"
SUB = f"Species per site in {len(RICH)} sites of the Doubs, in three stretches of ten · box: quartiles · line: median · whiskers: range"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.14)
    rng = np.random.default_rng(3)
    for k, (name, idx) in enumerate(GROUPS):
        v = RICH[idx]; q1, q2, q3 = np.percentile(v, [25, 50, 75])
        col = V.tone(k)
        ax.add_patch(plt.Rectangle((k - 0.22, q1), 0.44, q3 - q1, fc=V.tint(k), ec=col, lw=V.lw, zorder=2))
        ax.plot([k - 0.22, k + 0.22], [q2, q2], color=V.deep(k) if V.mode == "light" else col, lw=V.lw * 2, solid_capstyle="butt", zorder=4)
        for lo, hi, end in ((v.min(), q1, v.min()), (q3, v.max(), v.max())):
            ax.plot([k, k], [lo, hi], color=col, lw=V.lw, zorder=2)
            ax.plot([k - 0.09, k + 0.09], [end, end], color=col, lw=V.lw, zorder=2)
        V.dot(ax, k + 0.42 + rng.uniform(-0.06, 0.06, len(v)), v, col, s=22, z=5)
    ax.set_xlim(-0.75, 2.85); ax.set_xticks(range(3))
    ax.set_xticklabels([f"{n}\n{KM[i].min():.0f}–{KM[i].max():.0f} km\nmedian {np.median(RICH[i]):.0f}" for n, i in GROUPS], color=V.ink, fontsize=V.sz["annotation"])
    ax.set_ylim(-1, 28); ax.set_yticks([0, 5, 10, 15, 20, 25]); ax.grid(False, axis="x")
    V.panel(ax, unit="fish species per site")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="box plot", medium="screen", tool="matplotlib",
            data="Doubs river fish, Verneaux (1973), 30 sites × 27 species", script=rel(__file__),
            alt=(f"Box plots of species per site in three stretches of the Doubs. Medians {MED[0]:.0f}, {MED[1]:.0f} and "
                 f"{MED[2]:.0f} from source to mouth."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "boxplot", mode, meta=META)
