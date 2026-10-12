"""miserables_network.py: the co-occurrence network of Les Misérables in two panels, from data/miserables.json.

a: the whole network, nodes coloured by the six largest groups of the data (the rest folded into "other" in rule grey).
b: the same layout with Jean Valjean and his neighbours in terracotta and everyone else faded to the grid colour.
The layout is a seeded Fruchterman-Reingold force layout computed here in numpy.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib import patheffects as pe
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: Knuth, The Stanford GraphBase (1993), via vega-datasets 2.8.0"
D = load_json("miserables.json")
NAMES = [n["name"] for n in D["nodes"]]; GROUP = np.array([n["group"] for n in D["nodes"]])
EDGES = np.array([(l["source"], l["target"]) for l in D["links"]])
N = len(NAMES)
NB = [set() for _ in range(N)]
for a, b in EDGES: NB[a].add(b); NB[b].add(a)
DEG = np.array([len(s) for s in NB])
HERO = NAMES.index("Valjean")
assert DEG[HERO] == DEG.max() and (DEG == DEG.max()).sum() == 1           # the claim: more co-occurrences than anyone
RUNNER = int(np.argsort(DEG)[-2])

# the six largest groups in slot order (ties by group number), the rest folded into "other"
sizes = {g: int((GROUP == g).sum()) for g in sorted(set(GROUP))}
TOP = sorted(sizes, key=lambda g: (-sizes[g], g))[:6]
OTHER = [g for g in sizes if g not in TOP]
HUB = {g: max(np.where(GROUP == g)[0], key=lambda i: DEG[i]) for g in TOP}   # each group named by its best-connected character
HERO_GROUPS = len({GROUP[j] for j in NB[HERO]} | {GROUP[HERO]})


def fruchterman_reingold(n, edges, seed=7, iters=600):
    """Seeded Fruchterman-Reingold: repulsion k^2/d between all pairs, attraction d^2/k along edges, linear cooling,
    plus a weak pull to the centre so the few loosely tied characters stay on the page."""
    rng = np.random.default_rng(seed)
    pos = rng.uniform(-1, 1, (n, 2)); k = np.sqrt(4.0 / n); t = 0.2
    A = np.zeros((n, n)); A[edges[:, 0], edges[:, 1]] = A[edges[:, 1], edges[:, 0]] = 1
    for it in range(iters):
        delta = pos[:, None, :] - pos[None, :, :]
        d = np.maximum(np.linalg.norm(delta, axis=2), 1e-3)
        force = (k * k / d ** 2 - A * d / k)[:, :, None] * delta          # (k^2/d - A d^2/k) along the unit vector
        disp = force.sum(axis=1) - 0.06 * pos * np.linalg.norm(pos, axis=1, keepdims=True) / k
        step = np.linalg.norm(disp, axis=1, keepdims=True)
        pos += disp / np.maximum(step, 1e-9) * np.minimum(step, t)
        t = 0.2 * (1 - it / iters) + 0.002
    pos -= pos.mean(axis=0)
    return pos / np.abs(pos).max()


POS = fruchterman_reingold(N, EDGES)
SIZE = 10 + 38 * np.sqrt(DEG / DEG.max())          # modest: area grows with the square root of the degree


def network(ax, V, colors, edge_colors, order):
    for (a, b), c in zip(EDGES, edge_colors):
        ax.plot(POS[[a, b], 0], POS[[a, b], 1], color=c, lw=0.4, alpha=0.6, zorder=1, solid_capstyle="round")
    for i in order:
        ax.scatter(POS[i, 0], POS[i, 1], s=SIZE[i], color=colors[i], edgecolor=V.surface, linewidth=1.0, zorder=3)
    lo, hi = POS.min(axis=0) - 0.06, POS.max(axis=0) + 0.06
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_aspect("equal")
    ax.axis("off")


def _seg_dist(p, a, b):
    """Distance from points p (n x 2) to the segment a-b."""
    ab = b - a; t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.hypot(*(p - (a + t[:, None] * ab)).T)


def _crosses(a, b, c, d):
    """True if segment a-b crosses segment c-d."""
    o = lambda p, q, r: np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    return o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b)


def place_labels(fig, ax, V, items):
    """Greedy direct labels. Each name tries spots on rings around its node (7 to 30 pt, 16 directions) and takes the
    closest one that covers no node and no label already placed, is not nearer another node than its own, and whose
    leader (0.5 pt muted, beyond the first ring) passes no node and crosses no other leader. items: (node index, text)."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    pts = ax.transData.transform(POS); frame = ax.transAxes.transform([(0, 0), (1, 1)]); boxes, leaders = [], []
    px = fig.dpi / 72
    for i, text in items:
        best = None
        for rad in (7, 14, 22, 30):
            for a in np.radians(np.arange(0, 360, 22.5)):
                ux, uy = np.cos(a), np.sin(a)
                ha = "left" if ux > 0.3 else "right" if ux < -0.3 else "center"
                va = "bottom" if uy > 0.3 else "top" if uy < -0.3 else "center"
                t = ax.annotate(text, POS[i], xytext=(rad * ux, rad * uy), textcoords="offset points", fontsize=V.sz["annotation"], ha=ha, va=va)
                bb = t.get_window_extent(r).expanded(1.06, 1.12); t.remove()
                gap = np.hypot(np.maximum(0, np.maximum(bb.x0 - pts[:, 0], pts[:, 0] - bb.x1)),
                               np.maximum(0, np.maximum(bb.y0 - pts[:, 1], pts[:, 1] - bb.y1)))
                others = np.delete(gap, i)
                end = pts[i] + px * rad * np.array([ux, uy]); lead = rad > 8
                bad = (bb.x0 < frame[0, 0] or bb.x1 > frame[1, 0] or bb.y0 < frame[0, 1] or bb.y1 > frame[1, 1]
                       or any(bb.overlaps(o) for o in boxes) or (lead and any(_crosses(pts[i], end, *l) for l in leaders)))
                score = (10 * (others < 5).sum() + 2 * (others < gap[i] + 4).sum() * (not lead) + rad / 10 + 100 * bad
                         + (3 * (np.delete(_seg_dist(pts, pts[i], end), i) < 4 * px).sum() if lead else 0))
                if best is None or score < best[0]: best = (score, (rad * ux, rad * uy, ha, va, lead), bb, (pts[i], end))
        (dx, dy, ha, va, lead), bb, seg = best[1:]; boxes.append(bb)
        if lead: leaders.append(seg)
        ax.annotate(text, POS[i], xytext=(dx, dy), textcoords="offset points", fontsize=V.sz["annotation"], color=V.ink, ha=ha, va=va,
                    zorder=5, path_effects=[pe.withStroke(linewidth=2.5, foreground=V.surface)],
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=3.5) if lead else None)


def draw(V):
    fig = plt.figure(figsize=V.size("double_tall"))
    axa = fig.add_axes([0.02, 0.14, 0.46, 0.68]); axb = fig.add_axes([0.52, 0.14, 0.46, 0.68])
    # a: identity by group, six tones in slot order, other in rule grey
    col = [V.tone(TOP.index(g)) if g in TOP else V.rule for g in GROUP]
    network(axa, V, col, [V.rule] * len(EDGES), np.argsort(DEG))
    place_labels(fig, axa, V, [(HUB[g], NAMES[HUB[g]]) for g in TOP])
    axa.set_title(f"a  {len(sizes)} groups of characters, the six largest in colour", loc="left", color=V.ink, pad=6)
    V.note(axa, 0, -0.02, f"named: the best-connected character of each group\ngrey: {len(OTHER)} small groups ({int(sum(sizes[g] for g in OTHER))} characters) folded into other",
           transform=axa.transAxes)
    # b: about one character: Valjean and his neighbours in terracotta, everyone else faded to the grid colour
    on = NB[HERO] | {HERO}
    colb = [V.tone("terracotta") if i in on else V.grid for i in range(N)]
    ecol = [V.tone("terracotta") if HERO in (a, b) else V.grid for a, b in EDGES]
    order = [i for i in np.argsort(DEG) if i not in on] + [i for i in np.argsort(DEG) if i in on]
    network(axb, V, colb, ecol, order)
    place_labels(fig, axb, V, [(HERO, "Jean Valjean")] + [(NAMES.index(n), n) for n in ("Javert", "Cosette", "Marius", "Fantine", "Myriel", "Gavroche")])
    axb.set_title(f"b  His {DEG[HERO]} neighbours come from {HERO_GROUPS} of the {len(sizes)} groups", loc="left", color=V.ink, pad=6)
    V.note(axb, 0, -0.02, f"next best connected: {NAMES[RUNNER]}, with {DEG[RUNNER]} characters", transform=axb.transAxes)
    V.title(fig, f"Jean Valjean shares a chapter with {DEG[HERO]} of the other {N - 1} characters, more than anyone",
            f"Les Misérables · {N} characters, {len(EDGES)} co-occurrences · force layout (Fruchterman–Reingold, seed 7) · dot area grows with the degree",
            footer(SOURCE, __file__))
    return fig


META = dict(
    title=f"Jean Valjean shares a chapter with {DEG[HERO]} of the other {N - 1} characters, more than anyone",
    subtitle=f"Co-occurrence network of Les Misérables, {N} characters and {len(EDGES)} links, force layout",
    kind="scientific", form="network (two panels)", medium="paper", tool="matplotlib",
    data="Knuth, The Stanford GraphBase (1993), Les Misérables co-occurrences, via vega-datasets 2.8.0",
    script=rel(__file__),
    alt=f"Two network drawings of the {N} characters of Les Misérables. Left: nodes coloured by the six largest of {len(sizes)} groups. "
        f"Right: Jean Valjean and his {DEG[HERO]} neighbours highlighted in terracotta; they span {HERO_GROUPS} of the {len(sizes)} groups. "
        f"The next best connected character, {NAMES[RUNNER]}, has {DEG[RUNNER]} neighbours.",
    note=f"Layout: seeded Fruchterman–Reingold computed in numpy. The {len(OTHER)} smallest groups ({int(sum(sizes[g] for g in OTHER))} characters) are folded into 'other' in rule grey.",
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "science", "miserables_network", mode, meta=META if mode == "light" else None))
