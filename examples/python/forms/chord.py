"""chord.py: which of three Palmer Archipelago islands each penguin species lives on, as a chord diagram: the species on one half
of the circle, the islands on the other, a ribbon as wide as the number of birds joining a species to an island. Data:
data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Polygon
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0"
SPECIES = ("Adelie", "Chinstrap", "Gentoo")             # slot order: teal, terracotta, indigo
ISLANDS = ("Biscoe", "Dream", "Torgersen")
ROWS = load_json("penguins.json")
N = {(s, i): sum(r["Species"] == s and r["Island"] == i for r in ROWS) for s in SPECIES for i in ISLANDS}
SP = {s: sum(N[s, i] for i in ISLANDS) for s in SPECIES}; IS = {i: sum(N[s, i] for s in SPECIES) for i in ISLANDS}
TOTAL = sum(SP.values())
ON = {s: [i for i in ISLANDS if N[s, i]] for s in SPECIES}
assert [len(ON[s]) for s in SPECIES] == [3, 1, 1], ON

TITLE = "Only Adelie penguins live on all three islands; Gentoo and Chinstrap keep to one"
SUB = f"Penguins of the Palmer Archipelago by species and island, {TOTAL} birds · ribbon width: number of birds"
GAP = 0.09                                                           # radians between neighbouring arcs


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.04)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.9, 1.9); ax.set_ylim(-1.3, 1.25)
    # species on the right half, from the top downwards; islands on the left half, from the bottom upwards
    unit = (np.pi - 3 * GAP - 0.04) / TOTAL
    pos = {}; a = np.pi / 2 - 0.02
    for s in SPECIES:
        pos[s] = (a, a - SP[s] * unit); a -= SP[s] * unit + GAP
    a = -np.pi / 2 - 0.02 - 0.04 + 0.04
    for i in ISLANDS:
        pos[i] = (a, a - IS[i] * unit); a -= IS[i] * unit + GAP
    cur = {k: v[0] for k, v in pos.items()}
    R, R0 = 1.0, 0.93
    th = lambda a0, a1, n=40: np.linspace(a0, a1, max(4, int(n * abs(a1 - a0)) + 2))
    for s in SPECIES:                                                       # ribbons first, under the arcs
        for i in ISLANDS:
            w = N[s, i] * unit
            if not w: continue
            sa = th(cur[s], cur[s] - w); ia = th(cur[i], cur[i] - w)
            cur[s] -= w; cur[i] -= w
            P0 = np.c_[R0 * np.cos(sa), R0 * np.sin(sa)]; P1 = np.c_[R0 * np.cos(ia), R0 * np.sin(ia)]
            def bez(p, q, n=30):
                t = np.linspace(0, 1, n)[:, None]; return (1 - t) ** 2 * p + t ** 2 * q               # control point at the centre
            poly = np.r_[P0, bez(P0[-1], P1[0]), P1, bez(P1[-1], P0[0])]
            ax.add_patch(Polygon(poly, closed=True, fc=V.tint(SPECIES.index(s)), ec=V.tone(SPECIES.index(s)), lw=0.5, alpha=0.8, zorder=2))
    for k, (name, (a0, a1)) in enumerate(pos.items()):
        t = th(a0, a1, 60); col = V.tone(k) if k < 3 else V.muted if V.mode == "dark" else V.secondary
        ax.fill(np.r_[R0 * np.cos(t), R * np.cos(t[::-1])], np.r_[R0 * np.sin(t), R * np.sin(t[::-1])], color=col, lw=0, zorder=3)
        m = (a0 + a1) / 2; right = np.cos(m) > 0
        n = SP.get(name, IS.get(name))
        ax.text(1.1 * np.cos(m), 1.1 * np.sin(m), f"{name}\n{n} birds", ha="left" if right else "right", va="center",
                fontsize=V.sz["annotation"], color=V.ink, linespacing=1.15)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="chord diagram", medium="screen", tool="matplotlib",
            data="Palmer penguins, Gorman, Williams and Fraser (2014), 344 birds", script=rel(__file__),
            alt=("Chord diagram joining three penguin species to three islands. Adelie ribbons reach Biscoe, Dream and Torgersen; "
                 "Gentoo reaches only Biscoe and Chinstrap only Dream."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "chord", mode, meta=META)
