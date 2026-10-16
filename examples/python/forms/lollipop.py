"""lollipop.py: the twelve commonest fish of the river Doubs ranked by total abundance, a thin stem and a ringed dot for each,
the leader in terracotta. Abundance is the sum of the recorded classes 0–5 over 30 sites. Data: data/ecology/doubs_fish.csv."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Verneaux (1973), Doubs river fish, France and Switzerland; via R ade4::doubs"
F = load_csv("ecology/doubs_fish.csv")
NAMES = {r["code"]: r["English"] for r in load_csv("ecology/doubs_species.csv")}
CODES = [c for c in F[0] if c != "site"]
TOT = {c: sum(float(r[c]) for r in F) for c in CODES}
TOP = sorted(CODES, key=lambda c: -TOT[c])[:12]
SHARE = sum(TOT[c] for c in TOP[:3]) / sum(TOT.values())

TITLE = f"{NAMES[TOP[0]].capitalize()}, {NAMES[TOP[1]]} and {NAMES[TOP[2]]} are the commonest fish of the Doubs"
SUB = (f"Total abundance (classes 0–5 summed over {len(F)} sites) of the twelve commonest of {len(CODES)} species · "
       f"the three are {SHARE * 100:.0f} % of the total")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.22, right=0.95, top=0.80, bottom=0.09)
    n = len(TOP)
    for i, c in enumerate(TOP):
        y = n - 1 - i; col = V.tone(1 if i < 3 else 0)
        ax.plot([0, TOT[c]], [y, y], color=col, lw=V.lw, solid_capstyle="butt", zorder=2)
        V.dot(ax, [TOT[c]], [y], col, s=70, z=4)
        ax.text(TOT[c] + 2, y, f"{TOT[c]:.0f}", va="center", ha="left", fontsize=V.sz["annotation"], color=V.ink)
        ax.text(-4, y, NAMES[c].capitalize(), va="center", ha="right", fontsize=V.sz["annotation"], color=V.ink)
    ax.set_ylim(-0.7, n - 0.3); ax.set_xlim(0, max(TOT.values()) * 1.12)
    ax.set_yticks([]); ax.set_xticks([]); ax.grid(False)
    for s in ("left", "bottom"): ax.spines[s].set_visible(False)
    V.note(ax, max(TOT.values()) * 1.1, 1.0, "terracotta: the three commonest", ha="right", va="center")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="lollipop chart", medium="screen", tool="matplotlib",
            data="Doubs river fish, Verneaux (1973), 30 sites × 27 species", script=rel(__file__),
            alt=(f"Lollipop chart of the twelve commonest fish of the Doubs by total abundance. {NAMES[TOP[0]].capitalize()} leads with "
                 f"{TOT[TOP[0]]:.0f}; the top three are {SHARE * 100:.0f} % of all abundance."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "lollipop", mode, meta=META)
