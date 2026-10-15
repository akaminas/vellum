"""canid_history.py: the early history of dogs, wolves and the golden jackal as a population tree whose tubes are as wide as
the effective population size, with the splits in time and the gene flow between lineages.

The estimates are the main G-PhoCS model of Freedman et al. (2014): six genomes (Basenji, Dingo, Chinese, Israeli and
Croatian wolf, golden jackal) and the Boxer reference, calibrated with a mutation rate of 1e-8 per site per generation
and three-year generations. The topology is the paper's figure 5A. Total migration rates are the probabilities that a
lineage crosses the band over its whole duration, so they can exceed 1. The Boxer is the reference genome, and its
population size could not be estimated. Data: data/canids_freedman2014.csv, transcribed from Table S12.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle
from matplotlib import patheffects as pe
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Freedman et al. (2014), PLOS Genetics 10: e1004016, Table S12 (CC0)"
ROWS = load_csv("canids_freedman2014.csv")
P = {r["parameter"]: r for r in ROWS}


def N(k): return float(P["N" + k]["calibrated"]), float(P["N" + k]["cal_lo"]), float(P["N" + k]["cal_hi"])
def T(k): return float(P["T" + k]["calibrated"]) / 1000, float(P["T" + k]["cal_lo"]) / 1000, float(P["T" + k]["cal_hi"]) / 1000
def M(k): return float(P["m" + k]["raw_x1e4"])


# ---- the tree: leaves at their x, ancestors centred over their two children
LEAF = {"BOX": 0.00, "BSJ": 0.55, "DNG": 1.10, "CHW": 2.05, "ISW": 3.25, "CRW": 4.75, "GLJ": 6.35}
NAME = {"BOX": "Boxer", "BSJ": "Basenji", "DNG": "Dingo", "CHW": "Chinese\nwolf", "ISW": "Israeli\nwolf",
        "CRW": "Croatian\nwolf", "GLJ": "Golden\njackal"}
FAMILY = {"BOX": "teal", "BSJ": "teal", "DNG": "teal", "ancDOG1": "teal", "ancDOG": "teal",
          "CHW": "ochre", "ISW": "ochre", "CRW": "ochre", "ancWLF1": "ochre", "ancWLF": "ochre",
          "GLJ": "terracotta", "ancDW": None, "root": None}
SPLIT = {"ancDOG1": ("BOX", "BSJ", "ancDOG1"), "ancDOG": ("ancDOG1", "DNG", "ancDOG"),
         "ancWLF1": ("CHW", "ISW", "ancWLF1"), "ancWLF": ("ancWLF1", "CRW", "ancWLF"),
         "ancDW": ("ancDOG", "ancWLF", "ancDW"), "root": ("ancDW", "GLJ", "root")}
TOP = 432.0                                                    # the root runs to the top of the frame
X = dict(LEAF); START = {k: 0.0 for k in LEAF}; END = {}
for anc, (a, b, key) in SPLIT.items():
    t = T(key)[0]; END[a] = t; END[b] = t; START[anc] = t
    X[anc] = (X[a] + X[b]) / 2
END["root"] = TOP
SIZE = {k: N(k)[0] for k in X if k != "BOX"}
W_PER = 2.4 / 45000                                            # tube width per individual, data units

DW, DOG, DOG_CI = T("ancDW"), N("ancDOG"), N("ancDOG")
TITLE = f"Dogs and wolves split {round(DW[0] * 1000, -2):,.0f} years ago; the first dogs numbered about {round(DOG[0], -3):,.0f}"
SUB = "Tube width: effective population size, from a coalescent model of seven canid genomes · arrows: gene flow"
assert N("ancDW")[0] > 20 * DOG[0] / 2 and DW[0] > T("ancDOG")[0]


def halo(V, w=2.4):
    return [pe.withStroke(linewidth=w * V.scale, foreground=V.surface)]


def fill(V, k):
    f = FAMILY[k]
    return V.tint(f) if f else (V.grid if V.mode == "light" else V.rule)


def ink(V, k):
    f = FAMILY[k]
    return (V.deep(f) if V.mode == "light" else V.tone(f)) if f else V.secondary


def draw_tree(V, ax, lo, hi):
    """The tubes and the joins, clipped to the time window [lo, hi] of this axis."""
    for k in X:
        y0, y1 = max(START[k], lo), min(END[k], hi)
        if y1 <= y0: continue
        if k == "BOX":
            w = 0.07
            ax.add_patch(Rectangle((X[k] - w / 2, y0), w, y1 - y0, fc="none", ec=V.rule, lw=0.7, zorder=2))
            continue
        w = SIZE[k] * W_PER
        ax.add_patch(Rectangle((X[k] - w / 2, y0), w, y1 - y0, fc=fill(V, k), ec="none", zorder=2))
    for anc, (a, b, key) in SPLIT.items():
        t = START[anc]
        if not lo <= t <= hi: continue
        wa = 0.07 if a == "BOX" else SIZE[a] * W_PER; wb = SIZE[b] * W_PER
        x0 = X[a] - wa / 2; x1 = X[b] + wb / 2
        h = 0.016 * (hi - lo)
        ax.add_patch(Rectangle((x0, t - h * 0.2), x1 - x0, h, fc=fill(V, anc), ec="none", zorder=3))


def flow(V, ax, a, b, y, rate, dy=0.0, side="above"):
    """Gene flow from lineage a to b at time y: a dotted arrow edge to edge, the rate beside it."""
    wa = 0.07 if a == "BOX" else SIZE[a] * W_PER; wb = SIZE[b] * W_PER
    xa = X[a] + np.sign(X[b] - X[a]) * wa / 2; xb = X[b] - np.sign(X[b] - X[a]) * wb / 2
    col = V.secondary if V.mode == "light" else V.muted
    ax.annotate("", xy=(xb, y + dy), xytext=(xa, y + dy), zorder=6,
                arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, linestyle=(0, (1, 1.6)), mutation_scale=7, shrinkA=1, shrinkB=1))
    lab = f"{rate * 100:.0f} %" if rate >= 0.01 else "<1 %"
    ax.text((xa + xb) / 2, y + dy, lab, ha="center", va="bottom" if side == "above" else "top", fontsize=V.sz["unit_line"],
            color=V.ink, path_effects=halo(V), zorder=7)


def draw(V):
    fig = plt.figure(figsize=(7.2, 6.0))
    up = fig.add_axes([0.085, 0.705, 0.80, 0.135]); lo = fig.add_axes([0.085, 0.165, 0.80, 0.525])
    LO_MAX = 17.0
    draw_tree(V, lo, 0, LO_MAX); draw_tree(V, up, LO_MAX, TOP)
    for ax, (y0, y1), ticks in ((lo, (0, LO_MAX), [0, 5, 10]), (up, (LO_MAX, TOP), [100, 200, 300, 400])):
        ax.set_xlim(-1.75, 7.4); ax.set_ylim(y0, y1); ax.set_yticks(ticks)
        ax.set_xticks([]); ax.grid(axis="x", visible=False)
        for s in ax.spines.values(): s.set_visible(False)
    lo.spines["bottom"].set_visible(True)
    up.set_yticklabels([f"{t}" for t in [100, 200, 300, 400]])
    # the break between the two time scales
    for yy in (0.0,):
        for dx in (-0.006, 0.006):
            fig.add_artist(plt.Line2D([0.075 + dx, 0.083 + dx], [0.695, 0.705], color=V.muted, lw=0.7, transform=fig.transFigure))
    up.text(0, 1.10, "thousands of years ago · the scale changes above 17", transform=up.transAxes, fontsize=V.sz["unit_line"],
            color=V.muted, ha="left", va="bottom")
    # sizes of the living lineages, inside or beside their tube
    for k in ("BSJ", "DNG", "CHW", "ISW", "CRW", "GLJ"):
        n, a, b = N(k); w = n * W_PER
        s = f"{round(n, -2):,.0f}"
        if w > 0.5:
            lo.text(X[k], 5.2, f"{s}\n{round(a, -2):,.0f}–{round(b, -2):,.0f}", ha="center", va="center", fontsize=V.sz["unit_line"],
                    color=ink(V, k), linespacing=1.15, zorder=8)
        else:
            lo.text(X[k] + w / 2 + 0.05, 1.2, s, ha="left", va="bottom", rotation=90, fontsize=V.sz["unit_line"], color=ink(V, k), zorder=8)
    lo.text(X["BOX"] - 0.07, 1.2, "size not estimated", ha="right", va="bottom", rotation=90, fontsize=V.sz["unit_line"], color=V.muted)
    # ancestral sizes
    n, a, b = N("ancDW")
    up.text(X["ancDW"], 170, f"{round(n, -2):,.0f}\n{round(a, -2):,.0f}–{round(b, -2):,.0f}", ha="center", va="center",
            fontsize=V.sz["annotation"], color=V.secondary, linespacing=1.15)
    up.text(X["ancDW"], 300, "ancestor of dogs and wolves", ha="center", va="center", fontsize=V.sz["unit_line"], color=V.secondary)
    n, a, b = N("ancDOG")
    lo.annotate(f"first dogs\n{round(n, -2):,.0f} ({round(a, -2):,.0f}–{round(b, -2):,.0f})", (X["ancDOG"], 13.9), xytext=(-12, 26),
                textcoords="offset points", ha="right", va="bottom", fontsize=V.sz["annotation"], color=ink(V, "ancDOG"),
                path_effects=halo(V), linespacing=1.1, arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=1))
    n, a, b = N("ancWLF")
    lo.text(X["ancWLF"], 14.2, f"{round(n, -2):,.0f}", ha="center", va="center", fontsize=V.sz["unit_line"], color=ink(V, "ancWLF"),
            zorder=8)
    # split times
    for key, x, ha, dx in (("ancDOG1", X["BOX"] - 0.12, "right", 0), ("ancDOG", X["BOX"] - 0.12, "right", 0),
                           ("ancWLF", X["CRW"] + 0.55, "left", 0), ("ancDW", X["BOX"] - 0.12, "right", 0)):
        t, a, b = T(key)
        lo.text(x, t, f"{round(t * 1000, -2):,.0f} years ago", ha=ha, va="center", fontsize=V.sz["unit_line"], color=V.muted)
    t = T("root")[0]
    up.text(X["GLJ"] + 0.62, t, f"{round(t):,.0f},000 years ago", ha="left", va="center",
            fontsize=V.sz["unit_line"], color=V.muted)
    # gene flow
    flow(V, lo, "ISW", "BSJ", 3.0, M("ISW->BSJ"), dy=0.45)
    flow(V, lo, "BSJ", "ISW", 3.0, M("BSJ->ISW"), dy=-0.45, side="below")
    flow(V, lo, "CHW", "DNG", 8.2, M("CHW->DNG"), dy=0.45)
    flow(V, lo, "DNG", "CHW", 8.2, M("DNG->CHW"), dy=-0.45, side="below")
    flow(V, lo, "ISW", "GLJ", 10.6, M("ISW->GLJ"))
    flow(V, up, "ancDW", "GLJ", 240, M("ancDW->GLJ"))
    flow(V, up, "GLJ", "ancDW", 120, M("GLJ->ancDW"), side="below")
    # names
    for k in LEAF:
        lo.text(X[k], -0.6, NAME[k], ha="center", va="top", fontsize=V.sz["annotation"], color=ink(V, k) if k != "BOX" else ink(V, "BSJ"),
                linespacing=1.05)
    # width key
    kx, ky = 4.35, 16.0
    lo.add_patch(Rectangle((kx, ky), 10000 * W_PER, 0.35, fc=V.rule, ec="none"))
    lo.text(kx + 10000 * W_PER + 0.08, ky + 0.17, "width: 10,000 individuals", ha="left", va="center", fontsize=V.sz["unit_line"],
            color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE + "; μ = 1 × 10⁻⁸ per generation, 3-year generations", __file__), x=0.012)
    return fig


ALT = (f"Population tree of dogs, wolves and the golden jackal, tube widths proportional to effective population size. The "
       f"golden jackal splits from the ancestor of dogs and wolves {T('root')[0]:,.0f},000 years ago. That ancestor, "
       f"{N('ancDW')[0]:,.0f} strong, splits into dogs and wolves {DW[0] * 1000:,.0f} years ago. The first dogs number about "
       f"{DOG[0]:,.0f}; the Dingo splits off {T('ancDOG')[0] * 1000:,.0f} years ago and Boxer and Basenji "
       f"{T('ancDOG1')[0] * 1000:,.0f} years ago. Wolves split about {T('ancWLF')[0] * 1000:,.0f} years ago into lineages of "
       f"{N('CHW')[0]:,.0f} (Chinese), {N('ISW')[0]:,.0f} (Israeli) and {N('CRW')[0]:,.0f} (Croatian). Gene flow: Israeli wolf to "
       f"Basenji {M('ISW->BSJ') * 100:.0f} %, Basenji to Israeli wolf {M('BSJ->ISW') * 100:.0f} %, between Chinese wolf and Dingo "
       f"3–4 %, from the dog-wolf ancestor into the golden jackal {M('ancDW->GLJ') * 100:.0f} %.")
META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="population tree with tube widths (demographic history)",
            medium="paper", tool="matplotlib",
            data="Freedman et al. (2014), PLOS Genetics, G-PhoCS estimates, Table S12", script=rel(__file__), alt=ALT,
            note=("Calibrated with μ = 1 × 10⁻⁸ per site per generation and three-year generations, as in the paper; the mutation "
                  "rate is the main source of uncertainty in the dates. Total migration rates are probabilities over the whole "
                  "band and can exceed 100 %; the arrows are placed at an arbitrary time within the band. The two wolf splits, "
                  "13,455 and 13,389 years ago, are within each other's intervals."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        save(draw(vellum.use(mode)), "science", "canid_history", mode, meta=META if mode == "light" else None)
