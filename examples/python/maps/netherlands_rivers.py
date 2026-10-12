"""netherlands_rivers.py: a 50 x 60 cm print map of the Netherlands with its rivers and main canals as the featured layer,
the land below sea level tinted, in the manner of Nadieh Bremer's personal map of Norway (2023), in Vellum's colours.

Layers, bottom to top: sea; graticule (over the sea); land with a soft shadow along the shore, the Netherlands brighter
than its neighbours, the ground below NAP tinted; height contours (-5, 0, 5, 20, 50 m, then every 100 m); lakes with an
inner shadow; wide river water; rivers and canals in three weights; the national border; labels set as glyph outlines
(cities, towns, provinces, water bodies and rivers along their course); title block, legend, scale bar and a
map-in-map of the Rhine and Maas basins; footer with sources and the git stamp.

Data: data/maps/ (built by fetch_nl.py; see data/maps/SOURCES.md). The claim is computed from AHN4 there.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from _common import *                                    # noqa: E402,F401
import logging                                           # noqa: E402
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

from PIL import Image, ImageDraw                         # noqa: E402
from scipy import ndimage                                # noqa: E402
import shapely                                           # noqa: E402
from shapely.geometry import shape, box, LineString, Point   # noqa: E402
from shapely.ops import unary_union, linemerge          # noqa: E402
import contourpy                                         # noqa: E402
from matplotlib.collections import LineCollection       # noqa: E402
from matplotlib.colors import to_rgb                     # noqa: E402
from matplotlib.patches import Rectangle, Polygon as MPoly, PathPatch   # noqa: E402
from matplotlib.path import Path                         # noqa: E402
from matplotlib import patheffects as pe                 # noqa: E402

import nl_geo as G                                       # noqa: E402
import nl_text as T                                      # noqa: E402

MAPS = os.path.join(DATA, "maps")
GROUP, NAME = "maps", "netherlands_rivers"
X0, X1, Y0, Y1 = G.FRAME
CM = 1 / 2.54
FIG_IN = (G.PAPER_CM[0] * CM, G.PAPER_CM[1] * CM)
FIELD = (G.MARGIN_CM / G.PAPER_CM[0], G.MARGIN_CM / G.PAPER_CM[1], G.FIELD_CM[0] / G.PAPER_CM[0], G.FIELD_CM[1] / G.PAPER_CM[1])
PT_PER_UNIT = G.FIELD_CM[0] * CM * 72 / (X1 - X0)       # paper points per map unit (degree of longitude)
PAPER = T.Paper(X0, Y0, PT_PER_UNIT)
DPI = 200                                                # PNG; the PDF embeds the same rasters

SERIF, SANS = "Palatino Linotype", "Corbel"


# ---------------------------------------------------------------- data
def load_fc(name):
    fc = json.load(open(os.path.join(MAPS, name), encoding="utf-8"))
    return [(shape(f["geometry"]), f["properties"]) for f in fc["features"]]


def to_map(g):
    """lon / lat geometry to map units (lon, Mercator y)."""
    return shapely.transform(g, lambda a: np.stack([a[:, 0], G.merc_y(a[:, 1])], 1))


def xy(lon, lat):
    return lon, float(G.merc_y(lat))


STATS = json.load(open(os.path.join(MAPS, "nl_stats.json"), encoding="utf-8"))
LAND = {p["country"]: to_map(g) for g, p in load_fc("nl_land.geojson")}
WATER = load_fc("nl_water.geojson")
LAKES = to_map(unary_union([g for g, p in WATER if p["kind"] == "lake"]))
RIVER_AREAS = to_map(unary_union([g for g, p in WATER if p["kind"] == "river"]))
RIVERS = [(to_map(g), p) for g, p in load_fc("nl_rivers.geojson")]
BORDERS = [to_map(g) for g, p in load_fc("nl_borders.geojson")]
PLACES = json.load(open(os.path.join(MAPS, "nl_places.json"), encoding="utf-8"))
NL = LAND["nl"]
NL_PREP = shapely.prepared.prep(NL.buffer(0.004))

SHARE = STATS["share_below_nap"]
TITLE = f"{SHARE * 100:.0f} % of the Netherlands lies below the sea its rivers run to"
SUBTITLE = ("Rivers, main canals and lakes of the Rhine–Maas–Schelde delta over the height of the ground. "
            f"Land below NAP, the Dutch sea-level datum, is tinted: {STATS['km2_below_nap']:,.0f} of "
            f"{STATS['land_km2']:,.0f} km² of land, from AHN4 laser altimetry".replace(",", " "))
SOURCE = ("Data: © OpenStreetMap contributors (ODbL), via Overpass; AHN4 DTM, Rijkswaterstaat and Het Waterschapshuis, "
          "via PDOK (CC0); AWS Terrain Tiles (SRTM, GMTED, ETOPO1; Mapzen); Natural Earth (public domain). "
          "Mercator projection")


# ---------------------------------------------------------------- colours, all from vellum.json via the Vellum object
def palette(V):
    seq = V.sequential["teal"]
    if V.mode == "light":
        return dict(page=V.surface, sea=seq[0], lake=seq[0], shadow=V.deep("teal"), shadow_a=0.30,
                    land_nl=V.surface, land_other=V.card, other_veil=(V.grid, 0.35),
                    polder=V.tint("teal"), polder_a=0.42, polder_deep_a=0.62,
                    grat=V.tint("teal"), grat_a=0.9, cross=V.tone("teal"),
                    contour=V.rule, contour_major=V.muted, contour_a=0.55,
                    river1=V.deep("teal"), river2=seq[5], river3=V.tone("teal"), canal=V.tone("teal"),
                    river_out=V.tone("teal"), river_out_minor=seq[2], river_area=seq[4],
                    border=V.muted, border_band=V.grid,
                    ink=V.ink, secondary=V.secondary, muted=V.muted, halo=V.surface, water_ink=V.deep("teal"),
                    accent=V.tone("terracotta"), rule=V.rule, card=V.card)
    return dict(page=V.surface, sea=seq[0], lake=seq[0], shadow="#000000", shadow_a=0.45,
                land_nl=V.card, land_other=V.surface, other_veil=(V.grid, 0.0),
                polder=V.tint("teal"), polder_a=0.55, polder_deep_a=0.80,
                grat=seq[1], grat_a=0.9, cross=seq[3],
                contour=V.rule, contour_major=V.muted, contour_a=0.7,
                river1=V.tone("teal"), river2=seq[4], river3=seq[3], canal=seq[3],
                river_out=seq[3], river_out_minor=seq[2], river_area=seq[3],
                border=V.muted, border_band=V.grid,
                ink=V.ink, secondary=V.secondary, muted=V.muted, halo=V.surface, water_ink=V.deep("teal"),
                accent=V.tone("terracotta"), rule=V.rule, card=V.card)


def rgb(c):
    return np.array(to_rgb(c), np.float32)


# ---------------------------------------------------------------- rasters on the map field
class Field:
    """Pixel grid of the map field at a given dpi, and rasterisation of map-unit geometries onto it."""

    def __init__(self, dpi):
        self.w = int(round(G.FIELD_CM[0] * CM * dpi)); self.h = int(round(G.FIELD_CM[1] * CM * dpi))
        self.px_per_pt = dpi / 72.0

    def px(self, x, y):
        return (x - X0) / (X1 - X0) * self.w, (Y1 - y) / (Y1 - Y0) * self.h

    def mask(self, geom, ss=3):
        img = Image.new("L", (self.w * ss, self.h * ss), 0)
        d = ImageDraw.Draw(img)
        polys = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "Polygon" and not g.is_empty]
        for g in polys:
            a = np.asarray(g.exterior.coords); c, r = self.px(a[:, 0], a[:, 1])
            d.polygon(list(zip(c * ss, r * ss)), fill=255)
        for g in polys:                               # holes after all shells, so islands in lakes stay correct
            for h in g.interiors:
                a = np.asarray(h.coords); c, r = self.px(a[:, 0], a[:, 1])
                d.polygon(list(zip(c * ss, r * ss)), fill=0)
        img = img.resize((self.w, self.h), Image.BOX)
        return np.asarray(img, np.float32) / 255

    def elevation(self):
        q = np.asarray(Image.open(os.path.join(MAPS, "nl_elevation.png")), np.float32)
        z = q / 50.0 - 100.0
        g = G.GRID
        cols = (np.arange(self.w) + 0.5) / self.w * (X1 - X0) / g["step"] - 0.5
        rows = (np.arange(self.h) + 0.5) / self.h * (Y1 - Y0) / g["step"] - 0.5
        R, C = np.meshgrid(rows, cols, indexing="ij")
        return ndimage.map_coordinates(z, [R, C], order=1, mode="nearest"), z


def blur(a, sigma_pt, F):
    return ndimage.gaussian_filter(a, sigma_pt * F.px_per_pt)


def shift(a, dx_pt, dy_pt, F):
    return ndimage.shift(a, (dy_pt * F.px_per_pt, dx_pt * F.px_per_pt), order=1, mode="constant")


def over(base, color, alpha):
    """Composite a flat colour with per-pixel alpha onto an RGB float image."""
    a = alpha[..., None]
    return base * (1 - a) + rgb(color) * a


def build_rasters(P, F):
    """The sea (opaque RGB) and the land and lake layers (RGBA), as float arrays."""
    land = F.mask(LAND["nl"].union(LAND["other"]))
    nl = F.mask(LAND["nl"])
    lakes = F.mask(LAKES)
    z, zgrid = F.elevation()
    # sea
    sea = np.ones((F.h, F.w, 3), np.float32) * rgb(P["sea"])
    # the land: the Netherlands, its neighbours quieter, the ground below NAP tinted
    L = np.ones((F.h, F.w, 3), np.float32) * rgb(P["land_other"])
    vc, va = P["other_veil"]
    if va > 0:
        L = over(L, vc, np.full(L.shape[:2], va, np.float32))
    L = L * (1 - nl[..., None]) + rgb(P["land_nl"]) * nl[..., None]
    zs = ndimage.gaussian_filter(z, 1.2 * F.px_per_pt)
    below = np.clip(-zs / 0.25, 0, 1) * nl                     # soft edge over the last 25 cm of height
    deep = np.clip((-zs - 4.0) / 0.5, 0, 1) * nl               # and a second step below -4 m
    L = over(L, P["polder"], below * P["polder_a"] + deep * (P["polder_deep_a"] - P["polder_a"]))
    # the shore shadow: a soft, slightly offset drop of the land onto the sea (Bremer used canvas shadowBlur)
    sh = shift(blur(land, 7, F), 1.5, -2.0, F) * (1 - land)
    shadow_a = np.clip(sh * P["shadow_a"] * 1.6, 0, P["shadow_a"])
    land_rgba = np.concatenate([L, land[..., None]], 2)
    # shadow goes into the land layer as a dark veil where there is no land
    sh_rgb = rgb(P["shadow"])
    a_tot = land + shadow_a * (1 - land)
    col = (L * land[..., None] + sh_rgb * (shadow_a * (1 - land))[..., None]) / np.maximum(a_tot[..., None], 1e-6)
    land_rgba = np.concatenate([col, a_tot[..., None]], 2)
    # lakes, with an inner shadow along their shores
    inner = blur(shift(1 - lakes, 1.0, -1.5, F), 4, F) * lakes
    lake_rgb = over(np.ones((F.h, F.w, 3), np.float32) * rgb(P["lake"]), P["shadow"], np.clip(inner * P["shadow_a"] * 1.4, 0, 1))
    lake_rgba = np.concatenate([lake_rgb, lakes[..., None]], 2)
    return sea, land_rgba, lake_rgba, z, land, nl, lakes


def show(ax, img, z):
    ax.imshow(np.clip(img, 0, 1), extent=(X0, X1, Y0, Y1), origin="upper", interpolation="none", zorder=z,
              resample=False)


# ---------------------------------------------------------------- graticule
MAJOR, MINOR = 1.0, 0.5


def graticule(ax, P, V):
    lw_minor, lw_major = 0.45, 0.9
    for lon in np.arange(3.0, 7.5, MINOR):
        major = abs(lon - round(lon)) < 1e-6
        ax.plot([lon, lon], [Y0, Y1], color=P["grat"], lw=lw_major if major else lw_minor, alpha=P["grat_a"], zorder=1,
                solid_capstyle="butt")
    for lat in np.arange(50.5, 54.0, MINOR):
        major = abs(lat - round(lat)) < 1e-6
        y = float(G.merc_y(lat))
        ax.plot([X0, X1], [y, y], color=P["grat"], lw=lw_major if major else lw_minor, alpha=P["grat_a"], zorder=1,
                solid_capstyle="butt")


def crosses(ax, P, V):
    arm = 7 / PT_PER_UNIT
    for lon in np.arange(3.0, 7.6, MAJOR):
        for lat in np.arange(51.0, 54.0, MAJOR):
            x, y = lon, float(G.merc_y(lat))
            for dx, dy in ((arm, 0), (0, arm)):
                ax.plot([x - dx, x + dx], [y - dy, y + dy], color=P["cross"], lw=1.6, solid_capstyle="butt", zorder=12)


def degree_labels(fig, ax, P, V):
    """Degree notation around the edge of the field, in the margin."""
    fprop = T.fp(SANS)
    size = 8.5
    for lon in np.arange(3.0, 7.6, MAJOR):
        for y, va, d in ((Y1, "bottom", 6), (Y0, "top", -6)):
            T.straight_label(ax, PAPER, f"{lon:.0f}° E", (lon, y), fprop, size, P["muted"], ha="center",
                             va="bottom" if va == "bottom" else "top", dy=d, tracking=0.04)
    for lat in np.arange(51.0, 54.0, MAJOR):
        y = float(G.merc_y(lat))
        T.straight_label(ax, PAPER, f"{lat:.0f}° N", (X0, y), fprop, size, P["muted"], ha="center", va="bottom",
                         angle=90, dx=-6, tracking=0.04)
        T.straight_label(ax, PAPER, f"{lat:.0f}° N", (X1, y), fprop, size, P["muted"], ha="center", va="bottom",
                         angle=-90, dx=6, tracking=0.04)


# ---------------------------------------------------------------- contours
LEVELS_NL = [-5, 0, 5, 20, 50, 100, 200, 300]
LEVELS_OUT = [50, 100, 200, 300, 400, 500, 600]


def contours(ax, P, z_grid, nl_grid_mask, land_grid_mask):
    g = G.GRID
    xs = g["x0"] + (np.arange(g["nx"]) + 0.5) * g["step"]
    ys = g["y1"] - (np.arange(g["ny"]) + 0.5) * g["step"]
    zs = ndimage.gaussian_filter(z_grid, 1.2)
    for region, levels, sel in (("nl", LEVELS_NL, nl_grid_mask), ("out", LEVELS_OUT, land_grid_mask & ~nl_grid_mask)):
        zz = np.where(sel, zs, np.nan)
        gen = contourpy.contour_generator(xs, ys, np.ma.masked_invalid(zz), line_type="Separate")
        for lev in levels:
            segs = []
            for s in gen.lines(lev):
                if len(s) < 4: continue
                L = np.hypot(*np.diff(s, axis=0).T).sum()
                if L < 0.02 and np.allclose(s[0], s[-1]): continue     # drop small closed rings (< about 1.4 km)
                segs.append(s)
            major = lev in (0, 100, 200, 300, 400, 500, 600)
            lw = 0.75 if lev == 0 else (0.6 if major else 0.4)
            col = P["contour_major"] if lev == 0 else P["contour"]
            a = P["contour_a"] * (0.75 if region == "out" else 1.0)
            ax.add_collection(LineCollection(segs, colors=col, linewidths=lw, alpha=a, zorder=3,
                                             capstyle="round", joinstyle="round"))


# ---------------------------------------------------------------- rivers
def split_nl(g):
    try:
        inside = g.intersection(NL.buffer(0.004)); outside = g.difference(NL.buffer(0.004))
    except Exception:
        return g, None
    return inside, outside


def lines_of(g):
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "LineString" and len(p.coords) > 1:
            out.append(np.asarray(p.coords))
        elif hasattr(p, "geoms"):
            out += lines_of(p)
    return out


RIVER_STYLE = {  # (rank, kind) -> line width in points inside the Netherlands
    (1, "river"): 2.6, (2, "river"): 1.3, (3, "river"): 0.7,
    (1, "canal"): 2.0, (2, "canal"): 1.0, (3, "canal"): 0.6,
}


def rivers(ax, P):
    for (g, p) in sorted(RIVERS, key=lambda gp: -gp[1]["rank"]):
        inside, outside = split_nl(g)
        lw = RIVER_STYLE[(p["rank"], p["kind"])]
        col = {1: P["river1"], 2: P["river2"], 3: P["river3"]}[p["rank"]]
        if p["kind"] == "canal":
            col = P["canal"] if p["rank"] > 1 else P["river2"]
        z = 8 - p["rank"] * 0.1
        if inside is not None and not inside.is_empty:
            ax.add_collection(LineCollection(lines_of(inside), colors=col, linewidths=lw, zorder=z,
                                             capstyle="round", joinstyle="round"))
        if outside is not None and not outside.is_empty:
            oc = P["river_out"] if p["rank"] == 1 else P["river_out_minor"]
            ax.add_collection(LineCollection(lines_of(outside), colors=oc, linewidths=lw * 0.75, zorder=z - 0.5,
                                             capstyle="round", joinstyle="round"))


def borders(ax, P):
    segs = []
    for g in BORDERS:
        segs += lines_of(g)
    ax.add_collection(LineCollection(segs, colors=P["border_band"], linewidths=5.5, alpha=0.8, zorder=4,
                                     capstyle="round", joinstyle="round"))
    ax.add_collection(LineCollection(segs, colors=P["border"], linewidths=0.8, linestyles=(0, (4, 2, 1, 2)), zorder=9.5))


# ---------------------------------------------------------------- draw
def draw(V):
    P = palette(V)
    F = Field(DPI)
    fig = plt.figure(figsize=FIG_IN)
    fig.patch.set_facecolor(P["page"])
    ax = fig.add_axes(FIELD)
    ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect("auto"); ax.axis("off")
    ax.set_facecolor(P["sea"])
    sea, land_rgba, lake_rgba, z, land, nl, lakes = build_rasters(P, F)
    show(ax, sea, 0)
    graticule(ax, P, V)
    show(ax, land_rgba, 2)
    # contours on the elevation grid, masked to land
    gF = G.GRID
    sub = Field.__new__(Field); sub.w, sub.h, sub.px_per_pt = gF["nx"], gF["ny"], 1
    zgrid = np.asarray(Image.open(os.path.join(MAPS, "nl_elevation.png")), np.float32) / 50 - 100
    land_g = sub.mask(LAND["nl"].union(LAND["other"]), ss=1) > 0.5
    nl_g = sub.mask(NL, ss=1) > 0.5
    lakes_g = sub.mask(LAKES, ss=1) > 0.5
    contours(ax, P, zgrid, nl_g & ~lakes_g, land_g & ~lakes_g)
    show(ax, lake_rgba, 5)
    # wide river water
    ra = F.mask(RIVER_AREAS)
    show(ax, np.concatenate([np.ones((F.h, F.w, 3), np.float32) * rgb(P["river_area"]), ra[..., None]], 2), 6)
    borders(ax, P)
    rivers(ax, P)
    crosses(ax, P, V)
    # frame
    ax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fill=False, edgecolor=P["ink"], lw=0.8, zorder=30))
    degree_labels(fig, ax, P, V)
    return fig


if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        fig = draw(V)
        out = os.path.join(FIGURES, GROUP); os.makedirs(out, exist_ok=True)
        fig.savefig(os.path.join(out, f"{NAME}_{mode}.png"), dpi=DPI, facecolor=fig.get_facecolor())
        plt.close(fig)
        print(mode, "done")
