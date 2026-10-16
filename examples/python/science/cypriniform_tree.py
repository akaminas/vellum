"""cypriniform_tree.py: the time-calibrated tree of the carps, minnows and loaches, one species per genus, branches coloured by
family, each family with its number, species count and a fish drawn in its colour, a geological time scale under the tree
and the three fossil calibrations that pin it, in the spirit of a graphical abstract for a phylogeny paper.

Data: data/cypriniformes_timetree.nwk and data/cypriniformes_fossils.csv, cut from the Fish Tree of Life by
fetch_fishtree.py (Rabosky et al. 2018, CC0). The families are clades of that tree named by the genera that anchor them
(the most recent common ancestor of the anchors), in the scheme of Tan and Armbruster (2018) as far as the tree resolves it.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
from fetch_fishtree import parse
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib import patheffects as pe
import collections, logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
sys.setrecursionlimit(20000)

SOURCE = "Rabosky et al. (2018), Nature 559: 392–395, via the Fish Tree of Life (CC0)"

# ---- the tree: all 1,703 species, then one species per genus
parent, length, name, children = parse(open(os.path.join(DATA, "cypriniformes_timetree.nwk"), encoding="utf-8").read())
depth = [0.0] * len(parent); order = [0]
for v in order:
    for c in children[v]: depth[c] = depth[v] + length[c]; order.append(c)
HEIGHT = max(depth)
SPECIES = [name[v] for v in range(len(parent)) if not children[v]]
GENUS = lambda s: s.split("_")[0]
N_GENUS = collections.Counter(GENUS(s) for s in SPECIES)
PREFER = ("Danio_rerio", "Cyprinus_carpio", "Gobio_gobio", "Tinca_tinca", "Tanichthys_albonubes", "Rhodeus_sericeus", "Cobitis_taenia",
          "Catostomus_commersonii", "Hypophthalmichthys_molitrix", "Chromobotia_macracanthus", "Gyrinocheilus_aymonieri", "Notropis_atherinoides")
KEEP = {}
for s in sorted(SPECIES):
    KEEP.setdefault(GENUS(s), s)
for s in PREFER:
    if s in SPECIES: KEEP[GENUS(s)] = s
KEEP_SET = set(KEEP.values())


class Node:
    def __init__(self, age, kids=(), tip=None):
        self.age, self.kids, self.tip, self.parent, self.y = age, list(kids), tip, None, 0.0
        for k in self.kids: k.parent = self
        self.ntips = 1 if tip else sum(k.ntips for k in self.kids)


def build(v):
    if not children[v]:
        return Node(0.0, tip=name[v]) if name[v] in KEEP_SET else None
    kids = [k for k in (build(c) for c in children[v]) if k]
    if not kids: return None
    return kids[0] if len(kids) == 1 else Node(HEIGHT - depth[v], kids)


ROOT = build(0)
ROOT_AGE = ROOT.age


def layout(n, ctr):
    n.kids.sort(key=lambda k: (k.ntips, min(t.tip for t in tips_of(k))))
    if n.tip: n.y = ctr[0]; ctr[0] += 1; return
    for k in n.kids: layout(k, ctr)
    n.y = (n.kids[0].y + n.kids[-1].y) / 2


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


layout(ROOT, [0])
TIPS = sorted(tips_of(ROOT), key=lambda t: t.y); NT = len(TIPS)
BYGENUS = {GENUS(t.tip): t for t in TIPS}


def mrca(nodes):
    chains = []
    for n in nodes:
        a = []
        while n: a.append(n); n = n.parent
        chains.append(a)
    common = set.intersection(*[set(map(id, a)) for a in chains])
    return next(x for x in chains[0] if id(x) in common)


# ---- families: name, anchor genera, colour slot by order below, body length / depth of the fish drawn, species drawn
FAMILIES = [
    ("Gyrinocheilidae", ["Gyrinocheilus"], 0.17, "Gyrinocheilus_aymonieri"), ("Catostomidae", ["Catostomus", "Myxocyprinus"], 0.24, "Catostomus_commersonii"),
    ("Botiidae", ["Botia", "Leptobotia", "Syncrossus"], 0.19, "Chromobotia_macracanthus"), ("Vaillantellidae", ["Vaillantella"], 0.07, "Vaillantella_maassi"),
    ("Cobitidae", ["Cobitis", "Pangio"], 0.11, "Cobitis_taenia"), ("Ellopostomatidae", ["Ellopostoma"], 0.13, "Ellopostoma_mystax"),
    ("Nemacheilidae", ["Schistura", "Triplophysa", "Nemacheilus"], 0.12, "Nemacheilus_binotatus"), ("Serpenticobitidae", ["Serpenticobitis"], 0.12, "Serpenticobitis_zonata"),
    ("Balitoridae", ["Balitora", "Gastromyzon", "Homaloptera", "Pseudogastromyzon", "Beaufortia"], 0.14, "Homaloptera_orthogoniata"),
    ("Barbuccidae", ["Barbucca"], 0.12, "Barbucca_diabolica"), ("Danionidae", ["Danio", "Rasbora", "Raiamas"], 0.19, "Danio_rerio"),
    ("Leuciscidae", ["Notropis", "Squalius", "Gila", "Rutilus"], 0.23, "Notropis_atherinoides"), ("Gobionidae", ["Gobio", "Hemibarbus"], 0.18, "Gobio_gobio"),
    ("Acheilognathidae", ["Rhodeus", "Acheilognathus", "Acanthorhodeus"], 0.40, "Rhodeus_sericeus"), ("Xenocyprididae", ["Xenocypris", "Hypophthalmichthys", "Hemiculter", "Opsariichthys"], 0.24, "Hypophthalmichthys_molitrix"),
    ("Tincidae", ["Tinca"], 0.27, "Tinca_tinca"), ("Tanichthyidae", ["Tanichthys"], 0.18, "Tanichthys_albonubes"),
    ("Leptobarbidae", ["Leptobarbus"], 0.23, "Leptobarbus_hoevenii"), ("Psilorhynchidae", ["Psilorhynchus"], 0.15, "Psilorhynchus_sucatio"),
    ("Cyprinidae", ["Cyprinus", "Barbus", "Labeo", "Catlocarpio", "Probarbus"], 0.40, "Cyprinus_carpio"),
]
FAMILIES = [f for f in FAMILIES if all(g in BYGENUS for g in f[1])]
CLADE = {f[0]: mrca([BYGENUS[g] for g in f[1]]) for f in FAMILIES}
SIZE = {n: len(tips_of(c)) for n, c in CLADE.items()}
FAM_OF = {}                                                                   # node id -> family, the smallest clade that holds it
for fam in sorted(CLADE, key=lambda n: -SIZE[n]):
    for x in nodes_of(CLADE[fam]): FAM_OF[id(x)] = fam
for t in TIPS: t.fam = FAM_OF.get(id(t))
# the stem edge of a family belongs to it, so a node's family is its own; tip families come from the same map
SP_FAM = collections.Counter()
for s in SPECIES:
    t = BYGENUS[GENUS(s)]
    if t.fam: SP_FAM[t.fam] += 1
N_SP = len(SPECIES); N_ASSIGNED = sum(SP_FAM.values())

# order the families top to bottom by where most of their tips sit
RUNS = collections.defaultdict(list)
for i, t in enumerate(TIPS):
    if t.fam:
        if RUNS[t.fam] and RUNS[t.fam][-1][1] == i - 1: RUNS[t.fam][-1][1] = i
        else: RUNS[t.fam].append([i, i])
MAIN = {f: max(r, key=lambda r: r[1] - r[0]) for f, r in RUNS.items()}
ORDER = sorted(RUNS, key=lambda f: sum(MAIN[f]) / 2)
NUM = {f: i + 1 for i, f in enumerate(ORDER)}
SLOTS = [0, 2, 3, 4, 5]                                                         # teal, indigo, ochre, mauve, moss; terracotta is for the claim
SLOT = {f: SLOTS[i % len(SLOTS)] for i, f in enumerate(ORDER)}
CROWN = {f: CLADE[f].age for f in ORDER if SIZE[f] > 1}
YOUNG = sum(SP_FAM[f] for f in CROWN if CROWN[f] < 66) / N_ASSIGNED
OLD = [f for f in CROWN if CROWN[f] >= 66]

FOSSILS = load_csv("cypriniformes_fossils.csv")
CAL = []
for k, r in enumerate(FOSSILS):
    a, b = BYGENUS.get(GENUS(r["left"])), BYGENUS.get(GENUS(r["right"]))
    CAL.append(dict(letter="ABC"[k], node=mrca([a, b]), fossil=r["fossil"], clade=r["clade"], age=float(r["min_age_ma"]), node_age=float(r["node_age_ma"])))

TITLE = f"{YOUNG * 100:.0f} % of carps, minnows and loaches belong to families that arose after the dinosaurs"
SUB = f"Cypriniformes, {N_SP:,} species, one per genus ({NT}) drawn · crown: age of a family's last common ancestor"

# ---- geometry, in inches on a 7.2 x 9.6 canvas
W, H = 7.2, 9.6
XL, XR = 0.28, 3.70                                       # x of the root (100 Ma) and of the tips (0 Ma)
SCALE = (XR - XL) / ROOT_AGE
TOP, BOTTOM = 8.55, 2.75                                  # the tips run from TOP down to BOTTOM
DY = (TOP - BOTTOM) / (NT - 1)
X = lambda age: XR - age * SCALE
Y = lambda y: TOP - y * DY
ROW0, ROW_H = TOP - 0.02, (TOP - BOTTOM + 0.04) / len(ORDER)


def fish(ax, x, y, length, aspect, color, ring, ink, z=5):
    """A stock fish in flat colour facing left: body, forked tail, dorsal and pelvic fins, an eye. x, y: the centre of the body."""
    h = aspect * length
    u = np.linspace(0, 1, 60)
    prof = h * (0.07 * u ** 0.3 + 0.93 * np.sin(np.pi * u ** 0.78))
    bx = x - length / 2 + u * 0.8 * length
    top, bot = y + prof / 2, y - prof * 0.45
    body = np.r_[np.c_[bx, top], np.c_[bx[::-1], bot[::-1]]]
    xt = x - length / 2 + 0.78 * length; xe = x + length / 2
    tail = np.array([[xt, y + prof[-1] / 2], [xe, y + 0.42 * h], [x + length * 0.44, y], [xe, y - 0.42 * h], [xt, y - prof[-1] * 0.45]])
    i0, i1 = 22, 38
    dorsal = np.array([[bx[i0], top[i0] - 0.01 * h], [bx[i0 + 11], top[i0 + 11] + 0.30 * h], [bx[i1], top[i1] - 0.01 * h]])
    pelv = np.array([[bx[30], bot[30] + 0.01 * h], [bx[33], bot[33] - 0.24 * h], [bx[38], bot[38] + 0.01 * h]])
    for poly in (tail, dorsal, pelv, body):
        ax.add_patch(Polygon(poly, closed=True, fc=color, ec=ring, lw=0.6, zorder=z, joinstyle="round"))
    ex, ey = bx[6], y + 0.12 * h
    ax.add_patch(Circle((ex, ey), 0.12 * h + 0.004, fc=ring, ec="none", zorder=z + 0.1))
    ax.add_patch(Circle((ex, ey), 0.06 * h + 0.002, fc=ink, ec="none", zorder=z + 0.2))


def draw(V):
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    neutral = V.muted if V.mode == "light" else V.secondary
    colour = lambda f: neutral if f is None else V.tone(SLOT[f])
    # grid: every 20 Ma, and the end of the Cretaceous in the claim colour
    for a in range(0, 101, 20):
        ax.plot([X(a)] * 2, [BOTTOM - 0.07, TOP + 0.05], color=V.grid, lw=V.thin * 0.7, zorder=1)
    ax.plot([X(66)] * 2, [BOTTOM - 0.07, TOP + 0.12], color=V.tone(1), lw=V.lw * 0.8, ls=V.dotted, zorder=2)
    ax.text(X(66) + 0.04, TOP + 0.13, "66 Ma: end of the dinosaurs", fontsize=V.sz["annotation"], color=V.deep(1) if V.mode == "light" else V.tone(1), va="bottom", ha="left")
    # branches
    segs, cols = [], []
    ax.plot([X(ROOT_AGE + 4), X(ROOT_AGE)], [Y(ROOT.y)] * 2, color=neutral, lw=0.45, zorder=3)
    for n in nodes_of(ROOT):
        if n.tip: continue
        ys = [k.y for k in n.kids]
        segs.append([(X(n.age), Y(min(ys))), (X(n.age), Y(max(ys)))]); cols.append(colour(FAM_OF.get(id(n))) if n is not ROOT else neutral)
        for k in n.kids:
            segs.append([(X(n.age), Y(k.y)), (X(k.age), Y(k.y))]); cols.append(colour(FAM_OF.get(id(k))))
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.5, capstyle="round", zorder=3))
    # family bars beside the tips, and the leaders to the numbered rows
    bar_x = XR + 0.07
    for f in ORDER:
        for a, b in RUNS[f]:
            ax.add_patch(Rectangle((bar_x, Y(b) - DY * 0.5), 0.05, (b - a + 1) * DY, fc=V.tone(SLOT[f]), ec="none", zorder=3))
    for r, f in enumerate(ORDER):
        ry = ROW0 - (r + 0.5) * ROW_H; a, b = MAIN[f]; my = Y((a + b) / 2)
        ax.plot([bar_x + 0.06, 4.02, 4.2, 4.42], [my, my, ry, ry], color=V.rule, lw=0.4, zorder=2)
        c = V.tone(SLOT[f])
        ax.add_patch(Circle((4.52, ry), 0.092, fc=c, ec=V.surface, lw=0.9, zorder=4))
        ax.text(4.52, ry - 0.003, str(NUM[f]), ha="center", va="center", fontsize=5.8, fontweight="bold", color=V.surface if V.mode == "light" else V.card, zorder=5)
        ax.text(4.68, ry + 0.045, f, ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink)
        ax.text(4.68, ry - 0.075, f"{SP_FAM[f]:,} species" + (f", crown {CROWN[f]:.0f} Ma" if f in CROWN else ""), ha="left", va="center",
                fontsize=V.sz["footer"], color=V.muted)
        sp = [g for g in FAMILIES if g[0] == f][0]
        fish(ax, 6.2, ry + 0.005, 0.62, sp[2] * 0.72, c, V.surface, V.ink)
        ab = sp[3].split("_"); ax.text(6.55, ry - 0.005, f"{ab[0][0]}. {ab[1]}", ha="left", va="center", fontsize=V.sz["footer"] - 0.2, color=V.muted, style="italic")
    # fossil calibrations on the tree
    for c in CAL:
        px, py = X(c["node"].age), Y(c["node"].y)
        ax.add_patch(Circle((px, py), 0.075, fc=V.surface, ec=V.ink, lw=0.8, zorder=6))
        ax.text(px, py - 0.002, c["letter"], ha="center", va="center", fontsize=5.8, fontweight="bold", color=V.ink, zorder=7)
    # time scale
    ay = BOTTOM - 0.07
    ax.plot([X(100), X(0)], [ay, ay], color=V.rule, lw=V.thin, zorder=2)
    for a in range(0, 101, 20):
        ax.text(X(a), ay - 0.07, str(a), ha="center", va="top", fontsize=V.sz["tick"] - 1, color=V.muted)
    periods = [(100.0, 66.0, "Cretaceous", 5), (66.0, 23.03, "Paleogene", 3), (23.03, 2.58, "Neogene", 0), (2.58, 0.0, "", 4)]
    epochs = [(100.0, 66.0, "Late Cretaceous", 5), (66.0, 56.0, "Paleo.", 3), (56.0, 33.9, "Eocene", 3), (33.9, 23.03, "Oligo.", 3),
              (23.03, 5.33, "Miocene", 0), (5.33, 0.0, "", 0)]
    for rows, y0, h in ((periods, ay - 0.34, 0.15), (epochs, ay - 0.49, 0.15)):
        for r_ in rows:
            a0, a1, lab = r_[:3]
            slot = r_[3]
            ax.add_patch(Rectangle((X(a0), y0), (a0 - a1) * SCALE, h, fc=V.tint(slot), ec=V.surface, lw=0.8, zorder=2,
                                   alpha=1.0 if rows is periods else 0.55))
            ax.text(X((a0 + a1) / 2), y0 + h / 2, lab, ha="center", va="center", fontsize=V.sz["footer"],
                    color=V.deep(slot) if V.mode == "light" else V.tone(slot))
    ax.text(X(0) + 0.14, ay - 0.075, "millions of years ago", ha="left", va="top", fontsize=V.sz["unit_line"], color=V.muted)
    # bottom: the calibration box and the key
    bx0, by0, bw, bh = 0.28, 0.45, 3.45, 1.45
    ax.add_patch(Rectangle((bx0, by0), bw, bh, fc=V.card if V.mode == "light" else V.grid, ec="none", zorder=1))
    ax.text(bx0 + 0.15, by0 + bh - 0.14, "Fossil calibrations in the tree", ha="left", va="center", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink)
    for k, c in enumerate(CAL):
        yy = by0 + bh - 0.45 - k * 0.38
        ax.add_patch(Circle((bx0 + 0.25, yy), 0.075, fc=V.surface, ec=V.ink, lw=0.8, zorder=6))
        ax.text(bx0 + 0.25, yy - 0.002, c["letter"], ha="center", va="center", fontsize=5.8, fontweight="bold", color=V.ink, zorder=7)
        ax.text(bx0 + 0.42, yy + 0.04, "† " + c["fossil"], ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink, style="italic")
        ax.text(bx0 + 0.42, yy - 0.115, f"{c['clade']}; at least {c['age']:.1f} million years old", ha="left", va="center", fontsize=V.sz["footer"], color=V.muted)
    kx = 4.05
    ax.text(kx, by0 + bh - 0.14, "How to read it", ha="left", va="center", fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink)
    notes = ["branch colour and number: family", "bar and row: the species of that family", "dotted line: end of the Cretaceous, 66 Ma",
             "lettered disc: a fossil-calibrated node", "fish: a stock outline, not the species", "crown: age of a family's last common ancestor"]
    for k, s in enumerate(notes):
        ax.text(kx, by0 + bh - 0.42 - k * 0.2, s, ha="left", va="center", fontsize=V.sz["annotation"], color=V.secondary)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="time-calibrated phylogeny with family panels", medium="paper", tool="matplotlib",
            data="Fish Tree of Life timetree, Rabosky et al. (2018), Cypriniformes, 1,703 species, with the fossil calibrations inside the order",
            script=rel(__file__),
            alt=(f"Time tree of the carps, minnows and loaches (Cypriniformes), one species per genus, with {len(ORDER)} families numbered and coloured. "
                 f"The common ancestor of the order lived about {ROOT_AGE:.0f} million years ago; {YOUNG * 100:.0f} % of species belong to families whose "
                 f"common ancestor lived after the end of the Cretaceous 66 million years ago."))

if __name__ == "__main__":
    print(TITLE, "| tips", NT, "| families", len(ORDER), "| unassigned tips", sum(1 for t in TIPS if not t.fam))
    print({f: (SP_FAM[f], round(CROWN[f]) if f in CROWN else None) for f in ORDER})
    for mode in MODES:
        save(draw(vellum.use(mode)), "science", "cypriniform_tree", mode, meta=META if mode == "light" else None)
