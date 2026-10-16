"""butterfly_tree.py: the dated tree of the butterflies (Papilionoidea), genera sampled evenly, branches coloured by group
(the six smaller families and the twelve subfamilies of the brush-footed butterflies), each group with its number, genus
count, crown age and a butterfly drawn in pencil, the 95 % interval of each major node's age as a grey bar, a geological time
scale, and the seven families lettered on the tree and listed below it.

Data: data/butterflies_timetree.nwk and data/butterflies_taxa.csv, from fetch_butterflytree.py (Chazot et al. 2019, CC0).
Groups are clades of that tree named by the genera that anchor them (the most recent common ancestor of all their species).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
from newick import parse
from pencil_butterfly import draw_butterfly
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Rectangle
import collections, logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
sys.setrecursionlimit(20000)

SOURCE = "Chazot et al. (2019), Systematic Biology 68: 797–813; data doi:10.5061/dryad.fb88292 (CC0)"

parent, length, name, children = parse(open(os.path.join(DATA, "butterflies_timetree.nwk"), encoding="utf-8").read())
depth = [0.0] * len(parent); order = [0]
for v in order:
    for c in children[v]: depth[c] = depth[v] + length[c]; order.append(c)
HEIGHT = max(depth)
FAMILY = {r["genus"]: r["family"] for r in load_csv("butterflies_taxa.csv")}
GENUS = lambda s: s.split("_")[0]
TIPNAMES = [name[v] for v in range(len(parent)) if not children[v]]


class Node:
    def __init__(self, age, kids=(), tip=None, hpd=None, nfull=1):
        self.age, self.kids, self.tip, self.hpd, self.nfull, self.parent, self.y = age, list(kids), tip, hpd, nfull, None, 0.0
        for k in self.kids: k.parent = self


def build(v, keep):
    if not children[v]:
        return Node(0.0, tip=name[v]) if name[v] in keep else None
    kids = [k for k in (build(c, keep) for c in children[v]) if k]
    if not kids: return None
    if len(kids) == 1: return kids[0]
    lo, hi = (float(x) for x in name[v].split("_")) if name[v] else (None, None)
    return Node(HEIGHT - depth[v], kids, hpd=(lo, hi), nfull=sum(1 for _ in leaves_full(v)))


def leaves_full(v):
    st = [v]
    while st:
        x = st.pop()
        if children[x]: st.extend(children[x])
        else: yield x


def tips_of(n):
    out, st = [], [n]
    while st:
        x = st.pop()
        if x.tip: out.append(x)
        else: st.extend(x.kids)
    return out


def nodes_of(n):
    out, st = [], [n]
    while st:
        x = st.pop(); out.append(x); st.extend(x.kids)
    return out


def layout(n, ctr):
    if n.tip: n.y = ctr[0]; ctr[0] += 1; return
    n.kids.sort(key=lambda k: (len(tips_of(k)), min(t.tip for t in tips_of(k))))
    for k in n.kids: layout(k, ctr)
    n.y = (n.kids[0].y + n.kids[-1].y) / 2


def mrca(nodes):
    chains = []
    for n in nodes:
        a = []
        while n: a.append(n); n = n.parent
        chains.append(a)
    common = set.intersection(*[set(map(id, a)) for a in chains])
    return next(x for x in chains[0] if id(x) in common)


# ---- the groups: name, anchor genera, the butterfly drawn and the genus it stands for
GROUPS = [
    ("Papilionidae", ["Papilio", "Parnassius", "Baronia"], "Papilio"), ("Hedylidae", ["Macrosoma"], "Macrosoma"),
    ("Hesperiidae", ["Hesperia", "Pyrgus", "Coeliades"], "Hesperia"), ("Pieridae", ["Pieris", "Colias", "Dismorphia"], "Pieris"),
    ("Riodinidae", ["Riodina", "Hamearis", "Euselasia"], "Hamearis"), ("Lycaenidae", ["Lycaena", "Polyommatus", "Miletus", "Poritia", "Curetis"], "Lycaena"),
    ("Libytheinae", ["Libythea", "Libytheana"], "Libythea"), ("Danainae", ["Danaus", "Tithorea", "Euploea"], "Danaus"),
    ("Satyrinae", ["Morpho", "Caligo", "Bicyclus", "Erebia", "Coenonympha"], "Bicyclus"), ("Charaxinae", ["Charaxes", "Prepona", "Anaea"], "Charaxes"),
    ("Calinaginae", ["Calinaga"], "Calinaga"), ("Heliconiinae", ["Heliconius", "Acraea", "Argynnis"], "Heliconius"),
    ("Limenitidinae", ["Limenitis", "Adelpha", "Neptis", "Parthenos", "Cymothoe"], "Limenitis"),
    ("Nymphalinae", ["Nymphalis", "Vanessa", "Junonia", "Melitaea", "Historis", "Pycina"], "Nymphalis"),
    ("Biblidinae", ["Biblis", "Hamadryas", "Callicore"], "Hamadryas"), ("Apaturinae", ["Apatura", "Doxocopa", "Asterocampa", "Hestina"], "Apatura"),
    ("Cyrestinae", ["Cyrestis", "Marpesia"], "Marpesia"), ("Pseudergolinae", ["Pseudergolis", "Stibochiona", "Amnosia"], "Stibochiona"),
]
FAMILIES = ["Papilionidae", "Hedylidae", "Hesperiidae", "Pieridae", "Riodinidae", "Lycaenidae", "Nymphalidae"]


def assign(root):
    """Each node's group, the smallest group clade that holds it."""
    tips = tips_of(root); byg = collections.defaultdict(list)
    for t in tips: byg[GENUS(t.tip)].append(t)
    clade = {g: mrca([t for a in anchors for t in byg[a]]) for g, anchors, _ in GROUPS}
    of = {}
    for g in sorted(clade, key=lambda g: -len(tips_of(clade[g]))):
        for x in nodes_of(clade[g]): of[id(x)] = g
    return clade, of


# the full tree: group sizes, crown ages and the family ages
FULL = build(0, set(TIPNAMES)); layout(FULL, [0])
CLADE_F, OF_F = assign(FULL)
N_GEN = collections.Counter(OF_F.get(id(t)) for t in tips_of(FULL))
assert None not in N_GEN, [t.tip for t in tips_of(FULL) if id(t) not in OF_F]
CROWN = {g: CLADE_F[g].age for g in CLADE_F if not CLADE_F[g].tip}
byfam = collections.defaultdict(list)
for t in tips_of(FULL): byfam[FAMILY[GENUS(t.tip)]].append(t)
FAM_NODE = {f: mrca(byfam[f]) for f in FAMILIES}
for f in FAMILIES: assert all(FAMILY[GENUS(t.tip)] == f for t in tips_of(FAM_NODE[f])), f
STEM = {f: FAM_NODE[f].parent.age for f in FAMILIES}
GAP = min(STEM.values()) - 66
assert GAP > 20

# the tree drawn: genera sampled evenly within each group (every group keeps at least six, or all it has), anchors always
KEEP = set()
for g, anchors, rep in GROUPS:
    ts = sorted((t for t in tips_of(FULL) if OF_F.get(id(t)) == g), key=lambda t: t.y)
    k = len(ts) if len(ts) <= 6 else max(6, round(len(ts) * 0.42))
    KEEP |= {ts[int(i)].tip for i in np.linspace(0, len(ts) - 1, k).round()}
    KEEP |= {t.tip for t in ts if GENUS(t.tip) in anchors[:2] + [rep]}
ROOT = build(0, KEEP); layout(ROOT, [0])
TIPS = sorted(tips_of(ROOT), key=lambda t: t.y); NT = len(TIPS)
GROUP_OF_TIP = {t.tip: OF_F[id(t)] for t in tips_of(FULL)}
OF = {}                                                                 # a drawn node takes the group all its genera share
for n in nodes_of(ROOT):
    gs = {GROUP_OF_TIP[t.tip] for t in tips_of(n)}
    if len(gs) == 1 and n.age <= CLADE_F[next(iter(gs))].age + 1e-6: OF[id(n)] = next(iter(gs))
for t in TIPS: t.group = OF[id(t)]
RUNS = collections.defaultdict(list)
for i, t in enumerate(TIPS):
    if RUNS[t.group] and RUNS[t.group][-1][1] == i - 1: RUNS[t.group][-1][1] = i
    else: RUNS[t.group].append([i, i])
MAIN = {g: max(r, key=lambda r: r[1] - r[0]) for g, r in RUNS.items()}
ORDER = sorted(RUNS, key=lambda g: sum(MAIN[g]) / 2)
NUM = {g: i + 1 for i, g in enumerate(ORDER)}
SLOTS = [0, 2, 3, 4, 5]                                                 # teal, indigo, ochre, mauve, moss; terracotta is the claim
SLOT = {g: SLOTS[i % len(SLOTS)] for i, g in enumerate(ORDER)}
REP = {g: next(t for t in TIPNAMES if GENUS(t) == rep) for g, _, rep in GROUPS}
LETTER = {f: "ABCDEFG"[i] for i, f in enumerate(sorted(FAMILIES, key=lambda f: min(t.y for t in tips_of(ROOT) if FAMILY[GENUS(t.tip)] == f)))}
FAM_NODE_DRAWN = {f: mrca([t for t in TIPS if FAMILY[GENUS(t.tip)] == f]) for f in FAMILIES}

TITLE = f"Every butterfly family had split off over {int(GAP // 5 * 5)} million years before the asteroid hit"
SUB = (f"Papilionoidea, {len(TIPNAMES)} genera, {NT} drawn · grey bars: 95 % interval of a node's age · "
       f"crown: age of a group's last common ancestor")

# ---- geometry, in inches on a 7.2 x 9.6 canvas
W, H = 7.2, 9.6
AGE_MAX = 130
XL, XR = 0.28, 3.45
SCALE = (XR - XL) / AGE_MAX
TOP, BOTTOM = 8.55, 2.75
DY = (TOP - BOTTOM) / (NT - 1)
X = lambda age: XR - age * SCALE
Y = lambda y: TOP - y * DY
ROW_H = (TOP - BOTTOM + 0.04) / len(ORDER); ROW0 = TOP - 0.02


def draw(V):
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    neutral = V.muted if V.mode == "light" else V.secondary
    graphite = V.secondary if V.mode == "light" else V.ink
    colour = lambda g: neutral if g is None else V.tone(SLOT[g])
    for a in range(0, AGE_MAX + 1, 20):
        ax.plot([X(a)] * 2, [BOTTOM - 0.07, TOP + 0.05], color=V.grid, lw=V.thin * 0.7, zorder=1)
    ax.plot([X(66)] * 2, [BOTTOM - 0.07, TOP + 0.12], color=V.tone(1), lw=V.lw * 0.8, ls=V.dotted, zorder=2)
    ax.text(X(66) + 0.04, TOP + 0.13, "66 Ma: the asteroid", fontsize=V.sz["annotation"], color=V.deep(1) if V.mode == "light" else V.tone(1),
            va="bottom", ha="left")
    # the 95 % intervals of the major nodes, under the branches
    for n in nodes_of(ROOT):
        if n.tip or n.nfull < 40 or n.hpd[0] is None: continue
        ax.plot([X(n.hpd[1]), X(n.hpd[0])], [Y(n.y)] * 2, color=V.rule, lw=2.6, alpha=0.55,
                solid_capstyle="butt", zorder=2)
    segs, cols = [], []
    ax.plot([X(ROOT.age + 5), X(ROOT.age)], [Y(ROOT.y)] * 2, color=neutral, lw=0.45, zorder=3)
    for n in nodes_of(ROOT):
        if n.tip: continue
        ys = [k.y for k in n.kids]
        segs.append([(X(n.age), Y(min(ys))), (X(n.age), Y(max(ys)))]); cols.append(colour(OF.get(id(n))))
        for k in n.kids:
            segs.append([(X(n.age), Y(k.y)), (X(k.age), Y(k.y))]); cols.append(colour(OF.get(id(k))))
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.5, capstyle="round", zorder=3))
    # the seven families, lettered at their crowns
    for f, n in FAM_NODE_DRAWN.items():
        px, py = X(n.age), Y(n.y)
        ax.add_patch(Circle((px, py), 0.07, fc=V.surface, ec=V.ink, lw=0.8, zorder=6))
        ax.text(px, py - 0.002, LETTER[f], ha="center", va="center", fontsize=5.6, fontweight="bold", color=V.ink, zorder=7)
    # group bars, the brush-foot bracket, leaders and the numbered rows
    bar_x = XR + 0.07
    for g in ORDER:
        for a, b in RUNS[g]:
            ax.add_patch(Rectangle((bar_x, Y(b) - DY * 0.5), 0.05, (b - a + 1) * DY, fc=V.tone(SLOT[g]), ec="none", zorder=3))
    ny = [Y(t.y) for t in TIPS if FAMILY[GENUS(t.tip)] == "Nymphalidae"]
    bx = bar_x + 0.11
    ax.plot([bx, bx], [min(ny), max(ny)], color=V.ink, lw=0.6, zorder=3)
    ax.text(bx + 0.05, (min(ny) + max(ny)) / 2, "Nymphalidae, the brush-footed butterflies", rotation=90, ha="left", va="center",
            fontsize=V.sz["footer"], color=V.secondary)
    for r, g in enumerate(ORDER):
        ry = ROW0 - (r + 0.5) * ROW_H; a, b = MAIN[g]; my = Y((a + b) / 2)
        x0 = bx + 0.2 if FAMILY.get(GENUS(REP[g])) == "Nymphalidae" else bar_x + 0.06
        ax.plot([x0, 3.92, 4.12, 4.30], [my, my, ry, ry], color=V.rule, lw=0.4, zorder=2)
        c = V.tone(SLOT[g])
        ax.add_patch(Circle((4.40, ry), 0.092, fc=c, ec=V.surface, lw=0.9, zorder=4))
        ax.text(4.40, ry - 0.003, str(NUM[g]), ha="center", va="center", fontsize=5.8, fontweight="bold",
                color=V.surface if V.mode == "light" else V.card, zorder=5)
        ax.text(4.56, ry + 0.045, g, ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink)
        ax.text(4.56, ry - 0.075, (f"{N_GEN[g]} genera" if N_GEN[g] > 1 else "1 genus") + (f", crown {CROWN[g]:.0f} Ma" if g in CROWN else ""), ha="left", va="center",
                fontsize=V.sz["footer"], color=V.muted)
        cx = 5.95 if r % 2 == 0 else 6.78
        draw_butterfly(ax, cx, ry + 0.05, 0.64, g, graphite, V.surface, seed=r, z=6)
        gname, sp = REP[g].split("_", 1)
        ax.text(cx, ry - 0.295, f"{gname} {sp.replace('_', ' ')}" if sp != "sp" else f"{gname} sp.", ha="center", va="center",
                fontsize=V.sz["footer"] - 0.5, color=V.muted, style="italic", zorder=8)
    # time scale
    ay = BOTTOM - 0.07
    ax.plot([X(AGE_MAX), X(0)], [ay, ay], color=V.rule, lw=V.thin, zorder=2)
    for a in range(0, AGE_MAX + 1, 20):
        ax.text(X(a), ay - 0.07, str(a), ha="center", va="top", fontsize=V.sz["tick"] - 1, color=V.muted)
    ax.text(X(0) + 0.14, ay - 0.075, "millions of years ago", ha="left", va="top", fontsize=V.sz["unit_line"], color=V.muted)
    periods = [(AGE_MAX, 66.0, "Cretaceous", 5), (66.0, 23.03, "Paleogene", 3), (23.03, 2.58, "Neogene", 0), (2.58, 0.0, "", 4)]
    epochs = [(AGE_MAX, 100.5, "Early Cret.", 5), (100.5, 66.0, "Late Cretaceous", 5), (66.0, 56.0, "Pal.", 3), (56.0, 33.9, "Eocene", 3),
              (33.9, 23.03, "Olig.", 3), (23.03, 5.33, "Miocene", 0), (5.33, 0.0, "", 0)]
    for rows, y0, h in ((periods, ay - 0.34, 0.15), (epochs, ay - 0.49, 0.15)):
        for a0, a1, lab, slot in rows:
            ax.add_patch(Rectangle((X(a0), y0), (a0 - a1) * SCALE, h, fc=V.tint(slot), ec=V.surface, lw=0.8, zorder=2,
                                   alpha=1.0 if rows is periods else 0.55))
            ax.text(X((a0 + a1) / 2), y0 + h / 2, lab, ha="center", va="center", fontsize=V.sz["footer"],
                    color=V.deep(slot) if V.mode == "light" else V.tone(slot))
    # bottom: the families and the key
    bx0, by0, bw, bh = 0.28, 0.40, 3.62, 1.55
    ax.add_patch(Rectangle((bx0, by0), bw, bh, fc=V.card if V.mode == "light" else V.grid, ec="none", zorder=1))
    ax.text(bx0 + 0.15, by0 + bh - 0.14, "The seven families", ha="left", va="center", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink)
    for k, f in enumerate(sorted(FAMILIES, key=lambda f: LETTER[f])):
        yy = by0 + bh - 0.38 - k * 0.165
        ax.add_patch(Circle((bx0 + 0.23, yy), 0.065, fc=V.surface, ec=V.ink, lw=0.8, zorder=6))
        ax.text(bx0 + 0.23, yy - 0.002, LETTER[f], ha="center", va="center", fontsize=5.6, fontweight="bold", color=V.ink, zorder=7)
        ax.text(bx0 + 0.38, yy, f, ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink)
        crown = "" if FAM_NODE[f].tip else f", crown {FAM_NODE[f].age:.0f}"
        ax.text(bx0 + 1.45, yy, f"{len(byfam[f])} genera · split {STEM[f]:.0f} Ma{crown}", ha="left", va="center", fontsize=V.sz["footer"],
                color=V.muted)
    kx = 4.15
    ax.text(kx, by0 + bh - 0.14, "How to read it", ha="left", va="center", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink)
    notes = ["branch colour and number: group", "bar and row: the genera of that group", "grey bar: 95 % interval of a node's age",
             "lettered disc: a family's last common ancestor", "dotted line: the asteroid, 66 Ma", "drawings: pencil sketches of the group, not the genus"]
    for k, s in enumerate(notes):
        ax.text(kx, by0 + bh - 0.40 - k * 0.2, s, ha="left", va="center", fontsize=V.sz["annotation"], color=V.secondary)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", also=["infographic"], form="time-calibrated phylogeny with group panels and pencil drawings",
            medium="paper", tool="matplotlib",
            data="Dated tree of 994 butterfly genera, Chazot et al. (2019), core analysis, median ages with 95 % intervals",
            script=rel(__file__),
            alt=(f"Time tree of the butterflies, {NT} of {len(TIPNAMES)} genera drawn, in {len(ORDER)} coloured and numbered groups with pencil "
                 f"drawings. The tree's root is {ROOT.age:.0f} million years old; every family had split from its sister lineage by "
                 f"{min(STEM.values()):.0f} million years ago, more than {int(GAP // 5 * 5)} million years before the asteroid at 66 million years."))

if __name__ == "__main__":
    print(TITLE, "| drawn", NT, "| groups", len(ORDER))
    print({g: (N_GEN[g], round(CROWN[g]) if g in CROWN else None) for g in ORDER})
    print({f: round(STEM[f], 1) for f in FAMILIES})
    for mode in MODES:
        save(draw(vellum.use(mode)), "science", "butterfly_tree", mode, meta=META)
