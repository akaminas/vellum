"""primates_tree.py: a rectangular, time-scaled phylogeny of twelve primates.

The topology is the accepted one; the divergence times are approximate values after TimeTree 5 (Kumar et al. 2022),
rounded and typed in here, so the figure is illustrative. Great apes, Old World monkeys and New World monkeys take the
first three tones; the gibbon and the two lemurs stay in secondary.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Divergence times: approximate, after TimeTree 5 (Kumar et al. 2022), illustrative"

# (age of the split in million years, [children]); a leaf is its common name. Times are approximate.
TREE = (70, [(43, [(29, [(19, [(15.5, [(9, [(6.5, ["human", (2, ["chimpanzee", "bonobo"])]), "gorilla"]), "Bornean orangutan"]),
                               "white-handed gibbon"]),
                         (10, ["rhesus macaque", "olive baboon"])]),
                   (19, ["common marmoset", "squirrel monkey"])]),
             (55, ["ring-tailed lemur", "mouse lemur"])])
CLADES = {"great apes": ("human", "chimpanzee", "bonobo", "gorilla", "Bornean orangutan"),     # slot order: teal, terracotta, indigo
          "Old World monkeys": ("rhesus macaque", "olive baboon"),
          "New World monkeys": ("common marmoset", "squirrel monkey")}


def leaves(node):
    return [node] if isinstance(node, str) else [x for c in node[1] for x in leaves(c)]


def age(node):
    return 0.0 if isinstance(node, str) else node[0]


def find(node, tips):
    """The smallest node whose leaves include all `tips`."""
    if isinstance(node, str): return node if (node,) == tuple(tips) else None
    for c in node[1]:
        if set(tips) <= set(leaves(c)): return find(c, tips)
    return node


TIPS = leaves(TREE); Y = {t: len(TIPS) - 1 - k for k, t in enumerate(TIPS)}
HC = find(TREE, ("human", "chimpanzee"))[0]; ROOT = TREE[0]
FRAC = HC / ROOT
assert round(FRAC, 1) == 0.1                     # "about a tenth": 6.5 / 70 rounds to 0.1


def draw(V):
    fig = plt.figure(figsize=V.size("double_tall"))
    ax = fig.add_axes([0.05, 0.15, 0.58, 0.64])
    clade_of = {t: k for k, tips in enumerate(CLADES.values()) for t in tips}
    crowns = [find(TREE, tips) for tips in CLADES.values()]

    def col(node, k):
        return V.tone(k) if k is not None else V.secondary

    def walk(node, k=None):
        """Draw the subtree; k is the clade index once inside a highlighted crown."""
        if any(node is c for c in crowns): k = [i for i, c in enumerate(crowns) if node is c][0]
        if isinstance(node, str):
            return Y[node]
        ys = [walk(c, k) for c in node[1]]
        for c, y in zip(node[1], ys):          # each child: a horizontal branch from this split to the child's split or tip
            ax.plot([-node[0], -age(c)], [y, y], color=col(c, k), lw=1.0, solid_capstyle="butt", zorder=2)
        ax.plot([-node[0], -node[0]], [min(ys), max(ys)], color=col(node, k), lw=1.0, solid_capstyle="projecting", zorder=2)
        return (min(ys) + max(ys)) / 2

    y_root = walk(TREE)
    ax.plot([-ROOT - 4, -ROOT], [y_root, y_root], color=V.secondary, lw=1.0, solid_capstyle="butt")
    names = []
    for t in TIPS:
        k = clade_of.get(t)
        V.dot(ax, 0, Y[t], V.tone(k) if k is not None else V.secondary, z=5)
        names.append(ax.annotate(t, (0, Y[t]), xytext=(7, 0), textcoords="offset points", va="center", fontsize=V.sz["annotation"],
                                 color=V.ink, annotation_clip=False))
    # clade labels: a bracket in the clade's tone beside the longest tip name of the tree, the name in ink
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    xb = max(n.get_window_extent(r).x1 for n in names) / fig.dpi * 72 - ax.transData.transform((0, 0))[0] / fig.dpi * 72 + 8
    for k, (name, tips) in enumerate(CLADES.items()):
        ys = [Y[t] for t in tips]; ym = (min(ys) + max(ys)) / 2
        ax.annotate(name, (0, ym), xytext=(xb + 6, 0), textcoords="offset points", va="center", fontsize=V.sz["annotation"],
                    color=V.ink, annotation_clip=False)
        bracket = matplotlib.transforms.offset_copy(ax.transData, fig=fig, x=xb, y=0, units="points")
        ax.plot([0, 0], [min(ys) - 0.3, max(ys) + 0.3], transform=bracket, color=V.tone(k), lw=1.6, solid_capstyle="butt", clip_on=False)
    # the two splits the claim compares
    yh = (Y["human"] + (Y["chimpanzee"] + Y["bonobo"]) / 2) / 2
    V.callout(ax, (-HC, yh), f"humans and chimpanzees, {HC:g} million years ago", (-30, 14), ha="right", va="bottom")
    ax.annotate(f"first split of the primates, {ROOT:g} million years ago", (-ROOT, y_root), xytext=(-ROOT - 4, y_root + 3.6), ha="left",
                va="bottom", fontsize=V.sz["annotation"], color=V.ink, arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.6, shrinkB=3, relpos=(0.02, 0)))
    ax.set_xlim(-ROOT - 4, 0.5); ax.set_ylim(-0.7, len(TIPS) - 0.3)
    ax.set_xticks([-60, -40, -20, 0]); ax.set_xticklabels(["60", "40", "20", "0"])
    ax.set_yticks([]); ax.grid(False)
    ax.set_xlabel("million years ago")
    V.title(fig, f"Humans and chimpanzees split {HC:g} million years ago, about a tenth of primate history",
            f"{len(TIPS)} primates · branch length is time · approximate divergence times, illustrative; after TimeTree (Kumar et al. 2022)",
            footer(SOURCE, __file__))
    return fig


META = dict(
    title=f"Humans and chimpanzees split {HC:g} million years ago, about a tenth of primate history",
    subtitle=f"Time-scaled phylogeny of {len(TIPS)} primates; approximate divergence times, illustrative; after TimeTree (Kumar et al. 2022)",
    kind="scientific", form="phylogeny (rectangular, time-scaled)", medium="paper", tool="matplotlib",
    data="Approximate divergence times after TimeTree 5 (Kumar et al. 2022), rounded; illustrative",
    script=rel(__file__),
    alt=f"A rectangular phylogeny of {len(TIPS)} primates with time running from {ROOT:g} million years ago on the left to the present on the right. "
        f"Great apes in teal, Old World monkeys in terracotta, New World monkeys in indigo. Humans and chimpanzees split {HC:g} million years ago, "
        f"{FRAC:.0%} of the {ROOT:g} million years since the first split of the primates.",
    note=f"Illustrative: the topology is standard but the divergence times are rounded approximations after TimeTree, typed into the script. "
         f"{HC:g} / {ROOT:g} = {FRAC:.3f}.",
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "science", "primates_tree", mode, meta=META if mode == "light" else None))
