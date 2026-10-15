"""membrane.py: a graphical abstract of the cell membrane as a fluid mosaic, drawn as a Vellum block to molecular scale.

A slab of membrane 34 x 20 nm, seen in the Vellum 3D view (orthographic, elevation 24 degrees, azimuth -58), cut on two
faces to show the bilayer. Every part has one family: phospholipid heads in teal, a seven-helix receptor in
terracotta (cut open by the front face, so it is seen to span the bilayer), a channel in indigo, cholesterol in ochre,
a peripheral protein in mauve, sugars in moss. Flat colour, no shading, ringed heads and sugars as the style's ringed
markers. The scene is a schematic, not data; the sizes follow the published structure of fluid bilayers: heads about
0.8 nm apart, 3.9 nm between the head planes (Nagle and Tristram-Nagle 2000), a helix about 1 nm across.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Polygon, Circle, Ellipse
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib import patheffects as pe
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Schematic after Singer and Nicolson (1972), to scale with Nagle and Tristram-Nagle (2000); not data"
TITLE = "Proteins drift in a film of lipids under 5 nm thick, and sugars coat its outer face"
SUB = "The plasma membrane as a fluid mosaic, drawn to molecular scale · a 34 × 20 nm patch, cut to show the bilayer"

# ---- the view and the slab, in nm
EL, AZ = np.radians(24), np.radians(-58)
RIGHT = np.array([-np.sin(AZ), np.cos(AZ), 0.0])
UP = np.array([-np.sin(EL) * np.cos(AZ), -np.sin(EL) * np.sin(AZ), np.cos(EL)])
EYE = np.array([np.cos(EL) * np.cos(AZ), np.cos(EL) * np.sin(AZ), np.sin(EL)])
L, D = 34.0, 20.0
R_HEAD = 0.42
Z_IN, Z_OUT = 0.45, 0.45 + 3.9                 # centres of the inner and the outer head planes
Z_BOT, Z_TOP = Z_IN - R_HEAD, Z_OUT + R_HEAD
Z_MID = (Z_IN + Z_OUT) / 2
SPACING = 0.82

RNG = np.random.default_rng(7)                 # fixed: the tails' wiggle and the lattice jitter are the same every run


def P(x, y, z):
    p = np.stack(np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float)), -1)
    return np.stack([p @ RIGHT, p @ UP], -1)


def depth(x, y, z): return x * EYE[0] + y * EYE[1] + z * EYE[2]


# ---- the proteins: (x, y, radius, top) for the two cylinders, the receptor on the front face
CHANNEL = (22.0, 11.0, 2.4, Z_TOP + 1.5)
GLYCO = (29.0, 4.5, 1.3, Z_TOP + 0.9)
RECEPTOR_X = (8.6, 9.8, 11.0, 12.2)            # helix axes on the cut face (four of seven seen in section)
RECEPTOR = (10.4, 0.0, 2.3, Z_TOP + 1.3)
GLYCOLIPIDS = [(5.5, 13.0), (15.5, 16.5), (31.0, 15.5)]


def footprint_free(x, y):
    for (cx, cy, r, _) in (CHANNEL, GLYCO, RECEPTOR):
        if (x - cx) ** 2 + (y - cy) ** 2 < (r + 0.35) ** 2: return False
    return True


def heads_top():
    out = []
    for j, y in enumerate(np.arange(R_HEAD + 0.05, D - R_HEAD, SPACING * 0.866)):
        for x in np.arange(R_HEAD + 0.05 + (j % 2) * SPACING / 2, L - R_HEAD, SPACING):
            x2, y2 = x + RNG.normal(0, 0.05), y + RNG.normal(0, 0.05)
            if footprint_free(x2, y2): out.append((x2, y2))
    return np.array(out)


HEADS = heads_top()


def sugar_tree(x, y, z0, n=6, seed=0):
    """A short branched glycan: points and links, rising from (x, y, z0)."""
    r = np.random.default_rng(seed)
    pts = [(x, y, z0)]; links = []
    tips = [0]
    while len(pts) < n:
        k = tips.pop(0)
        px, py, pz = pts[k]
        for b in range(2 if len(pts) in (2, 4) else 1):
            ang = r.uniform(0, 2 * np.pi)
            q = (px + 0.45 * np.cos(ang) + (0.45 if b else -0.15), py + 0.45 * np.sin(ang), pz + 0.72)
            pts.append(q); links.append((k, len(pts) - 1)); tips.append(len(pts) - 1)
            if len(pts) >= n: break
    return np.array(pts), links


def ringed(V, ax, xy, r, fc, z, lw=0.55):
    ax.add_patch(Circle(xy, r, fc=fc, ec=V.surface, lw=lw, zorder=z))


def cylinder(V, ax, cx, cy, r, z0, z1, fc, top_fc, z, half=False):
    """A vertical cylinder from z0 to z1 in flat colour: the side is the half of the rim that faces the viewer, joined top
    to bottom; the cap sits on it with a seam in the surface colour. With half=True only the half behind y = cy is drawn."""
    a0 = np.arctan2(EYE[1], EYE[0]) - np.pi / 2                 # the visible side runs from a0 to a0 + pi
    arc = np.linspace(a0, a0 + np.pi, 80)
    cap = np.linspace(0, 2 * np.pi, 120)
    if half:
        arc = arc[np.sin(arc) >= 0]; cap = np.linspace(0, np.pi, 60)
    if len(arc) > 1:
        side = np.r_[P(cx + r * np.cos(arc), cy + r * np.sin(arc), z1),
                     P(cx + r * np.cos(arc[::-1]), cy + r * np.sin(arc[::-1]), z0)]
        ax.add_patch(Polygon(side, closed=True, fc=fc, ec="none", zorder=z))
    rim = P(cx + r * np.cos(cap), cy + r * np.sin(cap), z1)
    ax.add_patch(Polygon(rim, closed=True, fc=top_fc, ec=V.surface, lw=0.7, zorder=z + 0.01))


def draw(V):
    fig = plt.figure(figsize=(7.2, 4.3))
    ax = fig.add_axes([0.0, 0.03, 1.0, 0.80])
    teal, terra, indigo, ochre, mauve, moss = (V.tone(k) for k in range(6))
    head_fc = V.tint("teal") if V.mode == "light" else V.tone("teal")
    tail = V.rule
    face_fc = V.card if V.mode == "light" else V.grid
    top_fc = V.grid if V.mode == "light" else V.rule

    # the top face, under the heads
    corners = P([0, L, L, 0], [0, 0, D, D], [Z_OUT] * 4)
    ax.add_patch(Polygon(corners, closed=True, fc=top_fc, ec="none", zorder=1))

    # everything on the top, far to near: heads, the channel, the glycoprotein, the receptor's top, the glycans
    items = []
    for (x, y) in HEADS:
        items.append((depth(x, y, Z_OUT), "head", (x, y)))
    for k, (gx, gy) in enumerate(GLYCOLIPIDS):
        items.append((depth(gx, gy, Z_OUT) + 0.01, "glycan", (gx, gy, Z_TOP, 8, 11 + k)))
    items.append((depth(CHANNEL[0], CHANNEL[1], Z_OUT), "channel", CHANNEL))
    items.append((depth(GLYCO[0], GLYCO[1], Z_OUT), "glyco", GLYCO))
    items.append((depth(RECEPTOR[0], RECEPTOR[1] + 0.8, Z_OUT), "receptor", RECEPTOR))
    items.sort(key=lambda t: t[0])
    z = 2.0
    for _, kind, a in items:
        z += 0.001
        if kind == "head":
            ringed(V, ax, P(a[0], a[1], Z_OUT), R_HEAD, head_fc, z)
        elif kind == "glycan":
            pts, links = sugar_tree(*a)
            sp = P(pts[:, 0], pts[:, 1], pts[:, 2])
            ax.add_collection(LineCollection([[sp[i], sp[j]] for i, j in links], colors=moss, linewidths=0.9, zorder=z))
            for q in sp[1:]: ringed(V, ax, q, 0.34, moss, z + 0.0005, lw=0.5)
            ringed(V, ax, sp[0], R_HEAD, head_fc, z + 0.0004)
        elif kind == "channel":
            cx, cy, r, zt = a
            cylinder(V, ax, cx, cy, r, Z_OUT, zt, V.tint("indigo"), V.card if V.mode == "light" else V.grid, z)
            # four subunits and the pore
            for k in range(4):
                th = np.pi / 4 + k * np.pi / 2
                seg = P([cx + 0.75 * np.cos(th), cx + r * np.cos(th)], [cy + 0.75 * np.sin(th), cy + r * np.sin(th)], [zt, zt])
                ax.plot(seg[:, 0], seg[:, 1], color=V.surface, lw=0.8, zorder=z + 0.02)
            pore = P(cx + 0.7 * np.cos(np.linspace(0, 2 * np.pi, 60)), cy + 0.7 * np.sin(np.linspace(0, 2 * np.pi, 60)), zt)
            ax.add_patch(Polygon(pore, closed=True, fc=indigo, ec="none", zorder=z + 0.03))
        elif kind == "glyco":
            cx, cy, r, zt = a
            cylinder(V, ax, cx, cy, r, Z_OUT, zt, V.tint("terracotta"), V.card if V.mode == "light" else V.grid, z)
            pts, links = sugar_tree(cx, cy, zt, n=11, seed=3)
            sp = P(pts[:, 0], pts[:, 1], pts[:, 2])
            ax.add_collection(LineCollection([[sp[i], sp[j]] for i, j in links], colors=moss, linewidths=0.9, zorder=z + 0.02))
            for q in sp[1:]: ringed(V, ax, q, 0.34, moss, z + 0.03, lw=0.5)
        elif kind == "receptor":
            cx, cy, r, zt = a
            cylinder(V, ax, cx, cy, r, Z_OUT, zt, V.tint("terracotta"), V.card if V.mode == "light" else V.grid, z, half=True)

    # the cut faces: the front (y = 0) and the right (x = L)
    def face(us, fixed, along):
        """A face along x (front, y = 0) or along y (right, x = L): background, two rows of heads, tails, cholesterol."""
        def pt(u, zz):
            return P(u, 0.0, zz) if along == "x" else P(L, u, zz)
        poly = np.r_[pt(np.array([0, us]), np.array([Z_BOT, Z_BOT])), pt(np.array([us, 0]), np.array([Z_TOP, Z_TOP]))]
        ax.add_patch(Polygon(poly, closed=True, fc=face_fc, ec="none", zorder=5))
        lines = []
        for u in np.arange(R_HEAD, us - R_HEAD + 0.01, SPACING):
            if along == "x" and RECEPTOR_X[0] - 0.7 < u < RECEPTOR_X[-1] + 0.7: continue
            for zh, sgn in ((Z_OUT, -1), (Z_IN, 1)):
                for off in (-0.17, 0.17):
                    zz = np.linspace(zh + sgn * R_HEAD, Z_MID - sgn * 0.08, 14)
                    uu = u + off + 0.07 * np.sin(np.linspace(0, 3 * np.pi, 14) + RNG.uniform(0, 6))
                    lines.append(pt(uu, zz))
        ax.add_collection(LineCollection(lines, colors=tail, linewidths=0.55, zorder=5.1))
        for u in np.arange(R_HEAD, us - R_HEAD + 0.01, SPACING):
            if along == "x" and RECEPTOR_X[0] - 0.7 < u < RECEPTOR_X[-1] + 0.7: continue
            for zh in (Z_OUT, Z_IN):
                ringed(V, ax, pt(u, zh), R_HEAD, head_fc, 5.2)
        # cholesterol: short rigid rods tucked under the heads
        for u in (np.arange(2.6, us - 1, 5.3)):
            if along == "x" and RECEPTOR_X[0] - 1.5 < u < RECEPTOR_X[-1] + 1.5: continue
            for du, z0, z1 in ((0.41, Z_OUT - 0.55, Z_OUT - 1.9), (2.87, Z_IN + 0.55, Z_IN + 1.9)):
                if u + du > us - 0.6: continue
                seg = pt(np.array([u + du, u + du]), np.array([z0, z1]))
                ax.plot(seg[:, 0], seg[:, 1], color=ochre, lw=2.4, solid_capstyle="round", zorder=5.3)
        return poly

    face(L, 0.0, "x"); face(D, L, "y")
    # the receptor in section on the front face: helices spanning the bilayer, joined by loops on both sides
    for k, hx in enumerate(RECEPTOR_X):
        a = P(np.array([hx - 0.48, hx + 0.48, hx + 0.48, hx - 0.48]), 0.0, np.array([Z_BOT - 0.6, Z_BOT - 0.6, Z_TOP + 0.6, Z_TOP + 0.6]))
        ax.add_patch(Polygon(a, closed=True, fc=V.tint("terracotta"), ec=terra, lw=0.7, zorder=5.4))
    for k in range(len(RECEPTOR_X) - 1):
        zl = Z_TOP + 0.6 if k % 2 == 0 else Z_BOT - 0.6
        t = np.linspace(0, np.pi, 20)
        xs = RECEPTOR_X[k] + (RECEPTOR_X[k + 1] - RECEPTOR_X[k]) * (1 - np.cos(t)) / 2
        zs = zl + (0.55 if k % 2 == 0 else -0.55) * np.sin(t)
        q = P(xs, 0.0, zs)
        ax.plot(q[:, 0], q[:, 1], color=terra, lw=1.2, zorder=5.45, solid_capstyle="round")
    # a peripheral protein held on the inner face, under the receptor
    pc = P(10.6, 1.2, Z_BOT - 2.0)
    ax.add_patch(Ellipse(pc, 5.0, 2.4, angle=-6, fc=V.tint("mauve"), ec=V.surface, lw=0.8, zorder=5.5))
    ax.add_patch(Ellipse(pc + np.array([1.4, -0.3]), 2.4, 1.6, angle=-6, fc=mauve, ec=V.surface, lw=0.8, zorder=5.55))

    # labels: ink text, thin muted leaders, no arrowheads
    def call(xyz, text, dxy, ha="left", va="center"):
        p = P(*xyz)
        ax.annotate(text, p, xytext=dxy, textcoords="offset points", ha=ha, va=va, fontsize=V.sz["annotation"], color=V.ink,
                    linespacing=1.1, zorder=9, path_effects=[pe.withStroke(linewidth=2.4, foreground=V.surface)],
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=2))
    call((3.2, 3.0, Z_OUT), "phospholipid heads", (-44, 40), ha="right")
    call((2.0, 0.0, Z_MID), "fatty-acid tails", (-40, 0), ha="right")
    call((2.6 + 0.41, 0.0, Z_IN + 1.3), "cholesterol", (-46, -26), ha="right")
    call((RECEPTOR_X[1], 0.0, Z_TOP + 0.9), "receptor: seven helices\nspan the bilayer", (-60, 20), ha="right")
    call((10.6, 1.2, Z_BOT - 2.6), "peripheral protein", (-46, -16), ha="right")
    call((CHANNEL[0], CHANNEL[1], CHANNEL[3]), "channel with its pore", (14, 40))
    call((GLYCO[0] + 0.6, GLYCO[1] + 0.3, GLYCO[3] + 1.6), "glycoprotein", (34, -22))
    call((GLYCOLIPIDS[2][0], GLYCOLIPIDS[2][1], Z_TOP + 1.5), "glycolipid", (22, 18))
    # the thickness, on the right face, and a scale bar under the front edge
    a = P(L, D + 0.9, Z_BOT); b = P(L, D + 0.9, Z_TOP)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=V.ink, lw=0.8, zorder=9)
    for q in (a, b): ax.plot([q[0] - 0.25, q[0] + 0.25], [q[1], q[1]], color=V.ink, lw=0.8, zorder=9)
    ax.text(b[0] + 0.5, (a[1] + b[1]) / 2, f"{Z_TOP - Z_BOT:.1f} nm", ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink)
    s0 = P(L - 7.0, -1.6, Z_BOT - 0.6); s1 = P(L - 2.0, -1.6, Z_BOT - 0.6)
    ax.plot([s0[0], s1[0]], [s0[1], s1[1]], color=V.ink, lw=1.2, solid_capstyle="butt", zorder=9)
    ax.text((s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2 - 0.55, "5 nm", ha="center", va="top", fontsize=V.sz["annotation"], color=V.ink)
    o = P(9.0, D, Z_TOP + 2.2); c = P(0.0, 0.0, Z_BOT - 3.6)
    ax.text(o[0], o[1], "outside the cell", ha="center", va="bottom", fontsize=V.sz["unit_line"], color=V.muted)
    ax.text(c[0] + 1.0, c[1], "cytoplasm", ha="left", va="top", fontsize=V.sz["unit_line"], color=V.muted)

    xs = [P(x, y, z)[0] for x in (0, L) for y in (0, D) for z in (Z_BOT - 4, Z_TOP + 5)]
    ys = [P(x, y, z)[1] for x in (0, L) for y in (0, D) for z in (Z_BOT - 4, Z_TOP + 3.2)]
    ax.set_xlim(min(xs) - 9.5, max(xs) + 3.0); ax.set_ylim(min(ys) - 0.8, max(ys) + 0.5)
    ax.set_aspect("equal"); ax.axis("off")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = ("A graphical abstract: a 34 by 20 nanometre patch of cell membrane seen from above at an angle and cut open on two faces. "
       "The bilayer is 4.7 nm thick: two rows of phospholipid heads with fatty-acid tails between them and cholesterol rods tucked "
       "under the heads. A receptor of seven helices, cut open at the front, spans the bilayer, with a peripheral protein held "
       "under it on the inner side. A channel protein with a central pore and a glycoprotein rise from the outer face; short "
       "branched sugar chains sit on the glycoprotein and on glycolipids. A 5 nm scale bar.")
META = dict(title=TITLE, subtitle=SUB, kind="conference", also=["infographic"], form="graphical abstract: pseudo-3D block, to scale",
            medium="graphical abstract", tool="matplotlib",
            data="schematic; sizes after Nagle and Tristram-Nagle (2000)", script=rel(__file__), alt=ALT,
            note=("Drawn in the Vellum 3D view with flat colour and one family per part. Heads 0.84 nm across and 0.82 nm apart, "
                  "3.9 nm between the head planes, helices 1 nm across, a channel 4.8 nm across; the receptor is cut so that four "
                  "of its seven helices show in section."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        save(draw(vellum.use(mode)), "abstract", "membrane", mode, meta=META if mode == "light" else None)
