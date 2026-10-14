"""calanques.py: the Calanques of Marseille as a four-panel composite about a coast the rising sea drowned.

a  the coast from Marseille to Cassis: ground height (IGN RGE ALTI) and sea depth (EMODnet), with the shore of
   11,000 years ago (the isobath at the sea level of the time), the section of c, the block of d and the Cosquer cave
b  relative sea level on the French Mediterranean coast over the last 12,000 years: the sea-level index points of
   Vacchi et al. (2021) from the Languedoc to Nice, and a Gaussian-process fit with its 1-sigma band
c  a section through Cap Morgiou and the Cosquer cave, south to north: ground and sea floor along it, today's sea and
   the sea levels of the blocks
d  three block diagrams of the same 7 x 7 km of coast at three moments: the terrain is today's, the sea stands at
   the fitted level of the time, heights x3. The blocks are cut through the Sormiou valley (front face) and the sea
   floor (right face)

The moments are those the index points pin down: 11,000 years ago (the oldest points, in the Rhone delta), 7,500
years ago (where the fast rise ends) and today. The fit, the sea levels, the rise between the moments and the time the
sea reached the cave are all computed here.
Data: data/maps/calanques_terrain.png and med_slips_vacchi2021.csv, from fetch_calanques.py.
"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *                                       # noqa: F401,F403
from PIL import Image
from matplotlib import patheffects as pe
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.patches import Polygon, Rectangle
import contourpy
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

MAPS = os.path.join(DATA, "maps")
SOURCE = ("Data: IGN RGE ALTI (Licence Ouverte 2.0); EMODnet Bathymetry DTM (CC BY 4.0); sea-level index points, "
          "Vacchi et al. (2021), Zenodo (CC BY 4.0); Natural Earth. Lambert-93")

# ---------------------------------------------------------------- the terrain
META_T = json.load(open(os.path.join(MAPS, "calanques_terrain.json"), encoding="utf-8"))
Z = np.array(Image.open(os.path.join(MAPS, "calanques_terrain.png")), np.float64) / META_T["scale"] - META_T["offset"]
X0, Y1, STEP = META_T["x0"], META_T["y1"], META_T["step"]


def height(x, y):
    """Ground or sea-floor height in metres at Lambert-93 x, y, bilinear on the 25 m grid."""
    c = (np.asarray(x, float) - X0) / STEP - 0.5; r = (Y1 - np.asarray(y, float)) / STEP - 0.5
    c0 = np.clip(np.floor(c).astype(int), 0, Z.shape[1] - 2); r0 = np.clip(np.floor(r).astype(int), 0, Z.shape[0] - 2)
    tc = np.clip(c - c0, 0, 1); tr = np.clip(r - r0, 0, 1)
    return (Z[r0, c0] * (1 - tc) * (1 - tr) + Z[r0, c0 + 1] * tc * (1 - tr)
            + Z[r0 + 1, c0] * (1 - tc) * tr + Z[r0 + 1, c0 + 1] * tc * tr)


# the block of d and the section of c, Lambert-93 metres
BX0, BX1, BY0, BY1 = 896600, 903600, 6233000, 6240000      # west edge on the axis of the Sormiou valley
SEC = ((899200, 6233000), (899200, 6240000))                # through Cap Morgiou and the Cosquer cave, south to north
CAVE_NEAR = (899182, 6236810)                               # the published position, rounded; see the note
CAVE_DEPTH = -37.0                                          # the entrance, metres below today's sea level


def cave_point():
    """The point of the -37 m contour nearest the published position: at 25 m the cliff is two cells wide, so the
    entrance is placed on the contour, not at the rounded coordinate (which falls on the cape)."""
    x = np.arange(CAVE_NEAR[0] - 400, CAVE_NEAR[0] + 401, 5.0); y = np.arange(CAVE_NEAR[1] - 400, CAVE_NEAR[1] + 401, 5.0)
    gx, gy = np.meshgrid(x, y); h = height(gx, gy)
    d = np.hypot(gx - CAVE_NEAR[0], gy - CAVE_NEAR[1]) + 200 * np.abs(h - CAVE_DEPTH)
    i = np.unravel_index(np.argmin(d), d.shape)
    return float(gx[i]), float(gy[i])


CAVE = cave_point()
MORGIOU = (898791, 6237520)                                 # the head of the Morgiou inlet


def shelf_point(level):
    """In block coordinates, a point of the shelf that is dry at `level` but under today's sea, near the cave."""
    x = np.arange(BX0 + 500, BX1 - 500, 25.0); y = np.arange(BY0 + 500, BY1 - 500, 25.0)
    gx, gy = np.meshgrid(x, y); h = height(gx, gy)
    ok = (h > level + 6) & (h < -6)
    d = np.hypot(gx - CAVE_NEAR[0] + 900, gy - CAVE_NEAR[1]) + np.where(ok, 0, 1e9)
    i = np.unravel_index(np.argmin(d), d.shape)
    return (BY1 - gy[i]) / 1000, (gx[i] - BX0) / 1000

# ---------------------------------------------------------------- the sea-level index points and the fit
REGIONS = {"9", "10", "11", "12", "13", "14"}                # Languedoc, Rhone delta, Marseille, La Ciotat-Hyeres, Frejus, Cap Ferrat


def slips():
    rows = list(csv.reader(open(os.path.join(MAPS, "med_slips_vacchi2021.csv"), encoding="latin-1")))[2:]
    keep = [r for r in rows if r and r[1].strip() in REGIONS]
    t = np.array([(1950 - float(r[8])) / 1000 for r in keep])            # thousands of years before 1950
    st = np.array([float(r[9]) / 1000 for r in keep])
    y = np.array([float(r[5]) for r in keep])
    sy = np.array([(float(r[6]) + float(r[7])) / 2 for r in keep])
    site = np.array([r[0].strip() for r in keep])
    return t, st, y, sy, site


T, ST, RSL, SRSL, SITE = slips()


def gp(t, y, s2, tq, amp, ell):
    K = amp ** 2 * np.exp(-0.5 * (t[:, None] - t[None, :]) ** 2 / ell ** 2) + np.diag(s2)
    L = np.linalg.cholesky(K)
    a = np.linalg.solve(L.T, np.linalg.solve(L, y))
    Ks = amp ** 2 * np.exp(-0.5 * (tq[:, None] - t[None, :]) ** 2 / ell ** 2)
    mu = Ks @ a
    v = np.linalg.solve(L, Ks.T)
    var = amp ** 2 - np.sum(v ** 2, axis=0)
    loglik = -0.5 * y @ a - np.sum(np.log(np.diag(L)))
    return mu, np.sqrt(np.maximum(var, 0)), loglik


def fit():
    """A zero-mean Gaussian process with a squared-exponential kernel; amplitude and length scale by maximum marginal
    likelihood on a grid. Age errors enter as extra height variance (slope x age error), the slope taken from a first
    pass and updated once (the noisy-input approximation of McHutchon and Rasmussen 2011)."""
    tq = np.linspace(0, 12, 601)
    slope = np.zeros_like(T)
    for _ in range(2):
        s2 = SRSL ** 2 + (slope * ST) ** 2
        best = max(((gp(T, RSL, s2, tq, a, l)[2], a, l) for a in (10, 15, 20, 30, 40, 60) for l in (0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)))
        _, amp, ell = best
        mu, sd, _ = gp(T, RSL, s2, tq, amp, ell)
        slope = np.interp(T, tq, np.gradient(mu, tq))
    return tq, mu, sd, amp, ell


TQ, MU, SD, AMP, ELL = fit()


def at(t):
    return float(np.interp(t, TQ, MU)), float(np.interp(t, TQ, SD))


MOMENTS = [(11.0, "11,000 years ago"), (7.5, "7,500 years ago"), (0.0, "today")]
LEVEL = {t: (0.0 if t == 0 else round(at(t)[0])) for t, _ in MOMENTS}       # today's sea level is 0 by definition
RISE_EARLY = LEVEL[7.5] - LEVEL[11.0]; RISE_LATE = 0 - LEVEL[7.5]
RATE_EARLY = RISE_EARLY / 35 * 100; RATE_LATE = RISE_LATE / 75 * 100            # cm per century
# when the fitted sea level reached the cave entrance
_i = np.where((MU[:-1] - CAVE_DEPTH) * (MU[1:] - CAVE_DEPTH) <= 0)[0]
T_CAVE = float(np.interp(CAVE_DEPTH, MU[_i[-1]:_i[-1] + 2][::-1], TQ[_i[-1]:_i[-1] + 2][::-1])) if len(_i) else np.nan
N_PTS = len(T); N_OLD = int((T > 7.6).sum())
SHELF = shelf_point(LEVEL[11.0])

assert LEVEL[11.0] < CAVE_DEPTH < LEVEL[7.5], "the story: the entrance is dry 11,000 years ago and under water 7,500 years ago"
assert RISE_EARLY > 3 * RISE_LATE

TITLE = (f"The sea rose {-LEVEL[11.0]:.0f} m in 11,000 years, {RISE_EARLY:.0f} m of it in the first 3,500, "
         f"and turned the valleys of the Calanques into inlets")
SUB = (f"Marseille to Cassis · relative sea level from {N_PTS} index points on the French Mediterranean coast "
       f"(Vacchi et al. 2021) · ground from IGN RGE ALTI, sea floor from EMODnet")


# ---------------------------------------------------------------- shared helpers
def axes_in(fig, left, top, width, height_, **kw):
    W, H = fig.get_size_inches()
    return fig.add_axes([left / W, 1 - (top + height_) / H, width / W, height_ / H], **kw)


def halo(V, w=2.4):
    return [pe.withStroke(linewidth=w * V.scale, foreground=V.surface)]


def ramp(colors, n=256):
    return LinearSegmentedColormap.from_list("r", colors, N=n)


def land_cmap(V): return ramp(V.gradient("ember", 9))
def sea_cmap(V): return ramp(V.sequential["teal"])


LAND_MAX, SEA_MAX = 600.0, 200.0


def land_rgba(V, h):                     # h: metres above the sea of the time
    return land_cmap(V)(np.clip(h / LAND_MAX, 0, 1))


def sea_rgba(V, d):                      # d: metres below the sea of the time
    return sea_cmap(V)(np.clip(d / SEA_MAX, 0, 1))


def text(V, ax, x, y, s, size="annotation", color=None, ha="left", va="center", h=True, **kw):
    return ax.text(x, y, s, fontsize=V.sz[size] if isinstance(size, str) else size, color=color or V.ink, ha=ha, va=va,
                   path_effects=halo(V) if h else None, **kw)


def accent(V): return V.tone("terracotta")


# ---------------------------------------------------------------- a  the map
MAP = (886000, 908000, 6230000, 6248000)


def panel_a(V, ax, cax1, cax2):
    x0, x1, y0, y1 = MAP
    c0, c1 = (x0 - X0) // STEP, (x1 - X0) // STEP; r0, r1 = (Y1 - y1) // STEP, (Y1 - y0) // STEP
    z = Z[r0:r1, c0:c1]
    ext = (x0, x1, y0, y1)
    land = np.ma.masked_where(z <= 0, z); sea = np.ma.masked_where(z > 0, -z)
    ax.imshow(sea, extent=ext, cmap=sea_cmap(V), vmin=0, vmax=SEA_MAX, interpolation="bilinear", rasterized=True, zorder=1)
    ax.imshow(land, extent=ext, cmap=land_cmap(V), vmin=0, vmax=LAND_MAX, interpolation="bilinear", rasterized=True, zorder=2)
    xs = np.linspace(x0 + STEP / 2, x1 - STEP / 2, z.shape[1]); ys = np.linspace(y1 - STEP / 2, y0 + STEP / 2, z.shape[0])
    ax.contour(xs, ys, z, levels=[0], colors=[V.deep("teal") if V.mode == "light" else V.tone("teal")], linewidths=0.45, zorder=3)
    ax.contour(xs, ys, z, levels=[LEVEL[11.0]], colors=[V.tone("ochre")], linewidths=0.8, linestyles=[(0, (1, 2))], zorder=3)
    # the block and the section
    ax.add_patch(Rectangle((BX0, BY0), BX1 - BX0, BY1 - BY0, fill=False, ec=V.ink, lw=0.7, zorder=5))
    text(V, ax, BX1 + 250, BY1 - 150, "d", size="panel_title", ha="left", va="top", fontweight="bold")
    (sx0, sy0), (sx1, sy1) = SEC
    ax.plot([sx0, sx1], [sy0, sy1], color=V.ink, lw=1.0, solid_capstyle="butt", zorder=6)
    text(V, ax, sx0, sy0 - 250, "c", size="panel_title", ha="center", va="top", fontweight="bold")
    V.dot(ax, CAVE[0], CAVE[1], accent(V), s=26, z=8, ring=1.0)
    ax.annotate("Cosquer cave", CAVE, xytext=(10, -20), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V), zorder=9,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=3))
    places = [("Marseille", 891300, 6246200, "left", V.ink), ("Marseilleveyre", 893400, 6239600, "center", V.secondary),
              ("Mont Puget", 900700, 6240700, "center", V.secondary), ("Cassis", 906300, 6239100, "center", V.ink),
              ("Riou", 894500, 6232700, "center", V.secondary), ("Frioul", 887700, 6244600, "center", V.secondary),
              ("Sormiou", 896300, 6236500, "right", V.secondary), ("Cassidaigne canyon", 902500, 6230900, "center", V.muted)]
    for s, x, y, ha, col in places:
        text(V, ax, x, y, s, ha=ha, color=col, zorder=9)
    text(V, ax, 887000, 6237600, f"dotted: the shore\n11,000 years ago,\n{abs(LEVEL[11.0]):.0f} m below today’s",
         color=V.deep("ochre") if V.mode == "light" else V.tone("ochre"), size="unit_line", ha="left", va="center", zorder=9,
         linespacing=1.05)
    # scale bar
    ax.plot([902000, 907000], [6246900, 6246900], color=V.ink, lw=1.2, solid_capstyle="butt", zorder=9)
    text(V, ax, 904500, 6247250, "5 km", size="unit_line", ha="center", va="bottom", zorder=9)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    # the two ramps
    for cax, cm, vmax, lab, ticks in ((cax1, land_cmap(V), LAND_MAX, "height, m", [0, 300, 600]),
                                       (cax2, sea_cmap(V), SEA_MAX, "depth, m", [0, 100, 200])):
        cax.imshow(np.linspace(0, 1, 256)[None, :], cmap=cm, aspect="auto", extent=(0, vmax, 0, 1))
        cax.set_yticks([]); cax.set_xticks(ticks); cax.tick_params(length=0, pad=2, labelsize=V.sz["unit_line"])
        for s in cax.spines.values(): s.set_visible(False)
        cax.text(0, 1.5, lab, transform=cax.transAxes, fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="bottom")
        cax.grid(False)


def locator(V, ax):
    """France on a small plate, Marseille marked."""
    gj = json.load(open(os.path.join(DATA, "ne_110m_admin_0_countries.geojson"), encoding="utf-8"))
    for f in gj["features"]:
        if f["properties"].get("ADMIN") != "France": continue
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            ring = np.array(p[0])
            if ring[:, 0].min() < -6 or ring[:, 1].min() < 40: continue                 # metropolitan France only
            ax.add_patch(Polygon(ring, closed=True, fc=V.card, ec=V.rule, lw=0.5))
    V.dot(ax, 5.37, 43.29, accent(V), s=14, z=5, ring=0.8)
    ax.set_xlim(-5.4, 9.8); ax.set_ylim(41.0, 51.4); ax.set_aspect(1 / np.cos(np.radians(46))); ax.axis("off")


# ---------------------------------------------------------------- b  sea level
def panel_b(V, ax):
    grey = V.secondary if V.mode == "light" else V.muted
    ax.fill_between(TQ, MU - SD, MU + SD, color=V.tint("teal"), alpha=V.band_alpha, lw=0, zorder=1)
    ax.errorbar(T, RSL, yerr=SRSL, xerr=ST, fmt="none", ecolor=V.rule, elinewidth=0.5, capsize=0, zorder=2)
    V.dot(ax, T, RSL, grey, s=10, z=3, ring=0.6)
    ax.plot(TQ, MU, color=V.tone("teal"), lw=V.lw, zorder=4, solid_capstyle="round")
    V.reference(ax, y=CAVE_DEPTH, text="the Cosquer entrance, −37 m")
    for t, lab in MOMENTS:
        y = LEVEL[t]
        V.dot(ax, t, y, accent(V), s=24, z=6, ring=1.0)
    ax.annotate(f"{LEVEL[11.0]:.0f} m".replace("-", "−"), (11.0, LEVEL[11.0]), xytext=(7, -1), textcoords="offset points",
                ha="left", va="top", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    ax.annotate(f"{LEVEL[7.5]:.0f} m".replace("-", "−"), (7.5, LEVEL[7.5]), xytext=(4, -6), textcoords="offset points",
                ha="left", va="top", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    ax.annotate(f"the sea reaches the cave\nabout {T_CAVE * 1000 // 100 * 100:,.0f} years ago", (T_CAVE, CAVE_DEPTH),
                xytext=(52, 22), textcoords="offset points", ha="left", va="bottom", fontsize=V.sz["annotation"], color=V.ink,
                path_effects=halo(V), linespacing=1.05, arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=2))
    text(V, ax, 7.0, -17, "no index points from\n7,500 to 10,400 years ago", color=V.muted, size="unit_line", ha="left",
         va="center", linespacing=1.05)
    ax.set_xlim(12.2, -0.3); ax.set_ylim(-47, 3)
    ax.set_xticks([12, 9, 6, 3, 0]); ax.set_yticks([-40, -30, -20, -10, 0])
    ax.set_yticklabels(["−40", "−30", "−20", "−10", "0"])
    ax.set_xlabel("thousands of years ago")
    V.panel(ax, "b", f"The rise slowed from {RATE_EARLY:.0f} cm a century to {RATE_LATE:.0f} cm", unit="relative sea level, m")


# ---------------------------------------------------------------- c  the section
EXAG_C = 2.5


def panel_c(V, ax):
    (sx0, sy0), (sx1, sy1) = SEC
    n = 600; f = np.linspace(0, 1, n)
    xs = sx0 + f * (sx1 - sx0); ys = sy0 + f * (sy1 - sy0)
    d = f * np.hypot(sx1 - sx0, sy1 - sy0) / 1000                      # km from the south end
    h = height(xs, ys)
    bottom = -160
    ax.fill_between(d, bottom, h, color=V.card if V.mode == "light" else V.grid, lw=0, zorder=1)
    ax.fill_between(d, h, 0, where=h < 0, color=V.tint("teal"), alpha=V.band_alpha, lw=0, zorder=2, interpolate=True)
    ax.plot(d, h, color=V.secondary if V.mode == "light" else V.muted, lw=0.9, zorder=4)
    for t, lab in MOMENTS[:2]:
        y = LEVEL[t]
        ax.plot([0, d[-1]], [y, y], color=V.tone("ochre"), lw=0.7, dashes=(1, 3), zorder=3, dash_capstyle="round")
    text(V, ax, 0.08, 8, f"sea level today, and {LEVEL[7.5]:.0f} m 7,500 years ago".replace("-", "−"), color=V.muted,
         size="unit_line", ha="left", va="bottom")
    text(V, ax, 0.08, LEVEL[11.0] - 6, f"{LEVEL[11.0]:.0f} m, 11,000 years ago".replace("-", "−"), color=V.muted,
         size="unit_line", ha="left", va="top")
    # the cave: where the section crosses -37 m nearest the cave
    dc = np.hypot(xs - CAVE[0], ys - CAVE[1])
    k = np.argmin(np.abs(h - CAVE_DEPTH) + dc / 50)
    V.dot(ax, d[k], CAVE_DEPTH, accent(V), s=26, z=6, ring=1.0)
    ax.annotate("Cosquer cave entrance,\n37 m below today’s sea", (d[k], CAVE_DEPTH), xytext=(-96, 30), textcoords="offset points",
                ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V), linespacing=1.05,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=3))
    # what the section crosses, read off the profile
    land = np.where(h > 0)[0]
    cape = land[0]; inlet = np.where((h < 0) & (np.arange(n) > cape))[0]
    text(V, ax, d[cape] - 0.05, h[cape] + 70, "Cap Morgiou", ha="right", va="bottom", color=V.secondary)
    if len(inlet):
        text(V, ax, d[inlet].mean(), 70, "Morgiou inlet", ha="center", va="bottom", color=V.secondary)
    top = np.argmax(h)
    text(V, ax, d[top], h[top] + 18, "slopes of Mont Puget", ha="center", va="bottom", color=V.secondary)
    text(V, ax, 0.08, -118, "the sea floor, 90–100 m down", color=V.muted, size="unit_line", ha="left", va="top")
    ax.set_xlim(0, d[-1]); ax.set_ylim(bottom, 420)
    ax.set_yticks([-100, 0, 100, 200, 300, 400]); ax.set_yticklabels(["−100", "0", "100", "200", "300", "400"])
    ax.set_xticks(range(0, 8)); ax.set_xlabel("km north along the section")
    ax.grid(False)
    for s in ("left", "right", "top"): ax.spines[s].set_visible(False)
    V.panel(ax, "c", "Through Cap Morgiou: cliffs plunge to a floor that was dry land",
            unit=f"height relative to today’s sea level, m · heights ×{EXAG_C:g}")


# ---------------------------------------------------------------- d  the blocks
EL, AZ = np.radians(24), np.radians(-58)                       # the Vellum 3D view
RIGHT = np.array([-np.sin(AZ), np.cos(AZ), 0.0])
UP = np.array([-np.sin(EL) * np.cos(AZ), -np.sin(EL) * np.sin(AZ), np.cos(EL)])
EYE = np.array([np.cos(EL) * np.cos(AZ), np.cos(EL) * np.sin(AZ), np.sin(EL)])
EXAG = 3.5
NB = 100                                                       # faces per side, as the 3D rules ask
BASE = -240.0
KM = (BX1 - BX0) / 1000


def block_grid():
    """Block coordinates: u from the inland edge (0) to the sea edge (7 km), w along the coast from the west edge
    (0) to the east (7 km); heights from the terrain."""
    u = np.linspace(0, KM, NB + 1); w = np.linspace(0, KM, NB + 1)
    U_, W_ = np.meshgrid(u, w, indexing="ij")
    x = BX0 + W_ * 1000; y = BY1 - U_ * 1000
    return U_, W_, height(x, y)


BU, BW, BZ = block_grid()


def proj(u, w, z):
    p = np.stack([np.asarray(u, float), np.asarray(w, float), np.asarray(z, float) * EXAG / 1000], -1)
    return p @ RIGHT, p @ UP


def to_block(x, y):
    return (BY1 - y) / 1000, (x - BX0) / 1000


def draw_block(V, ax, sl, show_today_coast):
    zt = np.maximum(BZ, sl)                                    # the top: ground, or the sea surface over it
    # top faces, far first
    c = 0.25 * (zt[:-1, :-1] + zt[1:, :-1] + zt[:-1, 1:] + zt[1:, 1:])
    g = 0.25 * (BZ[:-1, :-1] + BZ[1:, :-1] + BZ[:-1, 1:] + BZ[1:, 1:])
    uc = 0.5 * (BU[:-1, :-1] + BU[1:, 1:]); wc = 0.5 * (BW[:-1, :-1] + BW[1:, 1:])
    depth = uc * EYE[0] + wc * EYE[1] + c * EXAG / 1000 * EYE[2]
    order = np.argsort(depth.ravel())
    sx, sy = proj(BU, BW, zt)
    quads = np.stack([np.stack([sx[:-1, :-1], sy[:-1, :-1]], -1), np.stack([sx[1:, :-1], sy[1:, :-1]], -1),
                      np.stack([sx[1:, 1:], sy[1:, 1:]], -1), np.stack([sx[:-1, 1:], sy[:-1, 1:]], -1)], 2)
    quads = quads.reshape(-1, 4, 2)[order]
    gg = g.ravel()[order]
    col = np.where((gg < sl)[:, None], sea_rgba(V, sl - gg), land_rgba(V, gg - sl))
    ax.add_collection(PolyCollection(quads, facecolors=col, edgecolors=col, linewidths=0.15, rasterized=True, zorder=1))
    # the shore of the time on the top, and today's shore on the past blocks
    shore = V.deep("teal") if V.mode == "light" else V.tone("teal")
    for level, colr, ls, lw in ((sl, shore, "-", 0.5), (0.0, V.tone("ochre"), (0, (1, 2)), 0.9)):
        if level == 0.0 and not show_today_coast: continue
        for seg in contourpy.contour_generator(BU, BW, BZ).lines(level):
            if len(seg) < 4: continue
            px, py = proj(seg[:, 0], seg[:, 1], np.full(len(seg), max(level, sl)))
            ax.plot(px, py, color=colr, lw=lw, linestyle=ls, zorder=3, solid_capstyle="round", dash_capstyle="round")
    # the two cut faces: the front (w = 0, the Sormiou valley) and the right (u = 7 km, the sea floor)
    rock = V.card if V.mode == "light" else V.grid
    bed = V.grid if V.mode == "light" else V.rule
    for (uu, ww, zz) in ((BU[:, 0], BW[:, 0], BZ[:, 0]), (BU[-1, :], BW[-1, :], BZ[-1, :])):
        top = np.maximum(zz, BASE)
        px, py = proj(uu, ww, top); bx, by = proj(uu, ww, np.full_like(zz, BASE))
        poly = np.concatenate([np.stack([px, py], 1), np.stack([bx, by], 1)[::-1]])
        patch = Polygon(poly, closed=True, fc=rock, ec="none", zorder=4)
        ax.add_patch(patch)
        for lev in np.arange(-230, 600, 40):                  # bedding, every 40 m
            lx, ly = proj(uu, ww, np.full_like(zz, lev))
            ln, = ax.plot(lx, ly, color=bed, lw=0.4, zorder=4.1)
            ln.set_clip_path(patch)
        # the sea of the time against the face
        wet = zz < sl
        if wet.any():
            sx_, sy_ = proj(uu, ww, np.minimum(zz, sl)); tx_, ty_ = proj(uu, ww, np.full_like(zz, sl))
            for seg in np.split(np.arange(len(zz)), np.where(np.diff(wet.astype(int)) != 0)[0] + 1):
                if not wet[seg[0]]: continue
                seg = np.r_[max(seg[0] - 1, 0), seg, min(seg[-1] + 1, len(zz) - 1)]
                wp = np.concatenate([np.stack([tx_[seg], ty_[seg]], 1), np.stack([sx_[seg], sy_[seg]], 1)[::-1]])
                ax.add_patch(Polygon(wp, closed=True, fc=V.tint("teal"), ec="none", alpha=0.85, zorder=4.2))
        ax.plot(px, py, color=V.secondary if V.mode == "light" else V.muted, lw=0.6, zorder=4.3)
    # the vertical edges of the block, as seams in the surface colour
    edge = [(0, 0), (KM, 0), (KM, KM)]
    for (ua, wa) in edge:
        za = max(float(height(BX0 + wa * 1000, BY1 - ua * 1000)), sl)
        x0_, y0_ = proj(ua, wa, BASE); x1_, y1_ = proj(ua, wa, za)
        ax.plot([x0_, x1_], [y0_, y1_], color=V.surface, lw=1.2, zorder=4.4, solid_capstyle="butt")
    bx_, by_ = proj(np.array([0, KM, KM]), np.array([0, 0, KM]), np.full(3, BASE))
    ax.plot(bx_, by_, color=V.rule, lw=0.6, zorder=4.5)
    ax.set_aspect("equal"); ax.axis("off")


def panel_d(V, fig, axes, top_in):
    for k, ((t, lab), ax) in enumerate(zip(MOMENTS, axes)):
        sl = LEVEL[t]
        draw_block(V, ax, sl, show_today_coast=(t != 0))
        # the cave
        cu, cw = to_block(*CAVE)
        cz = max(CAVE_DEPTH, sl)
        px, py = proj(cu, cw, cz)
        V.dot(ax, px, py, accent(V), s=22, z=8, ring=0.9)
        under = sl - CAVE_DEPTH
        note = "cave entrance\non the shore" if under <= 0 else f"cave entrance\n{under:.0f} m under water"
        ax.annotate(note, (px, py), xytext=(30, 2), textcoords="offset points", ha="left", va="center", fontsize=V.sz["unit_line"],
                    color=V.ink, path_effects=halo(V), linespacing=1.05, zorder=9,
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=3))
        if t == 11.0:                                          # the strip of shelf that was land
            pu, pw = SHELF; qx, qy = proj(pu, pw, float(height(BX0 + pw * 1000, BY1 - pu * 1000)))
            ax.annotate("dry ground below\ntoday’s cliffs", (qx, qy), xytext=(-8, -40), textcoords="offset points", ha="right",
                        va="top", fontsize=V.sz["unit_line"], color=V.ink, path_effects=halo(V), linespacing=1.05, zorder=9,
                        arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=2))
        if t == 0.0:                                           # the Morgiou valley, now an inlet
            mu_, mw_ = to_block(*MORGIOU); qx, qy = proj(mu_, mw_, 0.0)
            ax.annotate("Morgiou: a valley\ndrowned as an inlet", (qx, qy), xytext=(-14, -46), textcoords="offset points", ha="right",
                        va="top", fontsize=V.sz["unit_line"], color=V.ink, path_effects=halo(V), linespacing=1.05, zorder=9,
                        arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=0, shrinkB=2))
        ax.text(0.0, 1.0, lab, transform=ax.transAxes, fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, ha="left", va="top")
        ax.text(0.0, 0.90, ("sea level " + f"{sl:.0f} m".replace("-", "−")) if t else "sea level 0", transform=ax.transAxes,
                fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="top")
    # a common frame, so the three blocks are drawn at one scale
    xs, ys = [], []
    for u, w in ((0, 0), (KM, 0), (KM, KM), (0, KM)):
        for z in (BASE, float(BZ.max())):
            a, b = proj(u, w, z); xs.append(a); ys.append(b)
    for ax in axes:
        ax.set_xlim(min(xs) - 0.05, max(xs) + 0.05); ax.set_ylim(min(ys) - 0.05, max(ys) + 0.22)
    # the rise between the moments
    for k, (t0, t1) in enumerate(((11.0, 7.5), (7.5, 0.0))):
        rise = LEVEL[t1] - LEVEL[t0]; yrs = (t0 - t1) * 1000
        a0, a1 = axes[k].get_position(), axes[k + 1].get_position()
        fig.text((a0.x1 + a1.x0) / 2, a0.y0 + 0.62 * a0.height, f"+{rise:.0f} m\nin {yrs:,.0f}\nyears", fontsize=V.sz["annotation"],
                 color=V.deep("teal") if V.mode == "light" else V.tone("teal"), ha="center", va="center", linespacing=1.1)


def draw(V):
    H = 9.42
    fig = plt.figure(figsize=(7.2, H))
    a = axes_in(fig, 0.25, 1.10, 3.30, 2.70); loc = axes_in(fig, 2.98, 3.90, 0.55, 0.50)
    c1 = axes_in(fig, 0.45, 4.10, 1.0, 0.05); c2 = axes_in(fig, 1.75, 4.10, 1.0, 0.05)
    b = axes_in(fig, 4.25, 1.30, 2.80, 2.42)
    c = axes_in(fig, 0.45, 5.00, 6.60, 1.30)
    d = [axes_in(fig, 0.0 + k * 2.32, 7.08, 2.32, 2.05) for k in range(3)]
    for k in (1, 2):
        p = d[k].get_position(); d[k].set_position([p.x0 + 0.22 / 7.2 * k, p.y0, p.width, p.height])
    panel_a(V, a, c1, c2); locator(V, loc); panel_b(V, b); panel_c(V, c); panel_d(V, fig, d, 7.08)
    V.panel(a, "a", "The coast from Marseille to Cassis", unit="ground height and sea depth")
    fig.text(0.05 / 7.2, 1 - 6.84 / H, "d  The sea climbed the cliffs, then filled the valleys", fontsize=V.sz["panel_title"], fontweight="bold",
             color=V.ink, ha="left", va="bottom")
    fig.text(0.05 / 7.2, 1 - 6.90 / H, f"today’s ground at three sea levels · heights ×{EXAG:g} · front face: the Sormiou valley; "
             f"right face: the sea floor · dotted: today’s shore", fontsize=V.sz["unit_line"], color=V.muted, ha="left", va="top")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Four panels on the Calanques coast near Marseille. a: a map from Marseille to Cassis with ground height and sea "
       f"depth; the shore of 11,000 years ago follows the {LEVEL[11.0]:.0f} m isobath a few hundred metres off today's cliffs. "
       f"b: relative sea level from {N_PTS} index points on the French Mediterranean coast: {LEVEL[11.0]:.0f} m 11,000 years "
       f"ago, {LEVEL[7.5]:.0f} m 7,500 years ago, then a slow rise to today; the sea reached the depth of the Cosquer cave "
       f"entrance, 37 m, about {T_CAVE * 1000:,.0f} years ago. c: a section through Cap Morgiou: cliffs plunge from the "
       f"slopes of Mont Puget to a sea floor 90 to 100 m down. d: three block diagrams of the same coast at sea levels of "
       f"{LEVEL[11.0]:.0f} m, {LEVEL[7.5]:.0f} m and 0: a strip of land below the cliffs, then the sea against the cliffs, "
       f"then the valleys flooded as inlets.")

META = dict(title=TITLE, subtitle=SUB, kind="composite", also=["map"],
            form="four-panel composite: relief map, index points with Gaussian-process fit, terrain section, three block diagrams",
            medium="paper", tool="matplotlib",
            data=(f"IGN RGE ALTI and EMODnet Bathymetry DTM for the Calanques coast; {N_PTS} sea-level index points from the "
                  f"Languedoc to Nice, Vacchi et al. (2021)"),
            script=rel(__file__), alt=ALT,
            note=(f"Index points of regions 9–14 of Vacchi et al. (2021): Languedoc, Rhône delta, Marseille, La Ciotat–Hyères, "
                  f"Fréjus and Cap Ferrat; the {N_OLD} older than 7,600 years are all from the Rhône delta, where compaction may "
                  f"lower them. Fit: a Gaussian process, squared-exponential kernel, amplitude {AMP:g} m and length scale "
                  f"{ELL:g} thousand years by maximum likelihood, age errors as extra height variance. The blocks keep today's "
                  f"ground: no sediment is removed or added, so they show where the sea stood, not the coast's full history. "
                  f"The Cosquer cave is placed on the −37 m contour nearest its published position; its entrance depth is from "
                  f"Clottes, Courtin and Vanrell (2005). Sea floor depths are referred to lowest astronomical tide, about 0.2 m "
                  f"below mean sea level at Marseille."))

if __name__ == "__main__":
    print(TITLE)
    print("levels", LEVEL, "cave reached", round(T_CAVE, 2), "ka; gp", AMP, ELL, "cave pt", CAVE)
    for mode in MODES:
        print(save(draw(vellum.use(mode)), "maps", "calanques", mode, meta=META if mode == "light" else None))
