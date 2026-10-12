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
def polys(gs):
    """All polygons of a list of (multi)polygons, in map units, without dissolving them (no topology needed to fill)."""
    out = []
    for g in gs:
        out += [q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon"]
    return [to_map(q) for q in out]


LAKES = polys([g for g, p in WATER if p["kind"] == "lake"])
RIVER_AREAS = polys([g for g, p in WATER if p["kind"] == "river"])
RIVERS = [(to_map(g), p) for g, p in load_fc("nl_rivers.geojson")]
BORDERS = [to_map(g) for g, p in load_fc("nl_borders.geojson")]
PLACES = json.load(open(os.path.join(MAPS, "nl_places.json"), encoding="utf-8"))
NL = LAND["nl"]
NL_PREP = shapely.prepared.prep(NL.buffer(0.004))

SHARE = STATS["share_below_nap"]
def thousands(v):
    return f"{v:,.0f}".replace(",", " ")              # thin space as the thousands separator


TITLE = f"{SHARE * 100:.0f} % of the Netherlands lies below sea level"
SUBTITLE = ("The Rhine, the Maas and the Schelde reach the North Sea across a delta of polders. Hatched: the "
            f"{thousands(round(STATS['km2_below_nap'], -1))} km² of land below NAP, the Dutch sea-level datum, "
            f"{SHARE * 100:.1f} % of the ground measured by AHN4 laser altimetry. Rivers, main canals and lakes over "
            "height contours")
import textwrap                                         # noqa: E402
TITLE_LINES = textwrap.wrap(TITLE, 25)
SUBTITLE_WRAPPED = "\n".join(textwrap.wrap(SUBTITLE, 62))
INSET_W = 10.2                                           # width of the map-in-map, paper cm
SOURCE = ("Data: © OpenStreetMap contributors (ODbL), via Overpass; AHN4 DTM, Rijkswaterstaat and Het Waterschapshuis, "
          "via PDOK (CC0); AWS Terrain Tiles (SRTM, GMTED, ETOPO1; Mapzen); Natural Earth (public domain). "
          "Mercator projection")


# ---------------------------------------------------------------- colours, all from vellum.json via the Vellum object
def palette(V):
    seq = V.sequential["teal"]
    if V.mode == "light":
        return dict(page=V.surface, sea=V.tint("teal"), lake=V.tint("teal"), shadow=V.deep("teal"), shadow_a=0.28,
                    land_nl=V.surface, land_other=V.card, other_veil=(V.grid, 0.25),
                    polder=seq[0], polder_a=0.7, hatch=V.tint("teal"), hatch_a=0.9, hatch_sp=3.4, hatch_w=0.6,
                    grat=seq[0], grat_a=0.9, cross=V.tone("teal"),
                    contour=V.rule, contour_major=V.muted, contour_a=0.6,
                    river1=V.deep("teal"), river2=V.tone("teal"), river3=seq[2], canal=V.tone("teal"),
                    river_out=V.tone("teal"), river_out_minor=seq[2], river_area=V.tint("teal"),
                    border=V.muted, border_band=V.grid,
                    ink=V.ink, secondary=V.secondary, muted=V.muted, halo=V.surface, water_ink=V.deep("teal"),
                    accent=V.tone("terracotta"), rule=V.rule, card=V.card, card_edge="none")
    return dict(page=V.surface, sea=seq[0], lake=seq[0], shadow="#000000", shadow_a=0.45,
                land_nl=V.grid, land_other=V.card, other_veil=(V.grid, 0.0),
                polder=V.tint("teal"), polder_a=0.35, hatch=V.tint("teal"), hatch_a=0.9, hatch_sp=3.4, hatch_w=0.6,
                grat=seq[1], grat_a=0.9, cross=seq[3],
                contour=V.rule, contour_major=V.muted, contour_a=0.7,
                river1=V.tone("teal"), river2=seq[4], river3=seq[3], canal=seq[4],
                river_out=seq[3], river_out_minor=seq[2], river_area=seq[0],
                border=V.muted, border_band=V.grid,
                ink=V.ink, secondary=V.secondary, muted=V.muted, halo=V.surface, water_ink=V.deep("teal"),
                accent=V.tone("terracotta"), rule=V.rule, card=V.card, card_edge=V.rule)


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
        gs = geom if isinstance(geom, list) else [geom]
        polys = [q for g in gs for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and not q.is_empty]
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
        z = np.where(q > 0, q / G.ELEV_SCALE - G.ELEV_OFFSET, -50.0)
        g = G.GRID
        cols = (np.arange(self.w) + 0.5) / self.w * (X1 - X0) / g["step"] - 0.5
        rows = (np.arange(self.h) + 0.5) / self.h * (Y1 - Y0) / g["step"] - 0.5
        R, C = np.meshgrid(rows, cols, indexing="ij")
        return ndimage.map_coordinates(z, [R, C], order=1, mode="nearest"), z


def blur(a, sigma_pt, F):
    return ndimage.gaussian_filter(a, sigma_pt * F.px_per_pt)


def shift(a, dx_pt, dy_pt, F):
    """Move a raster dx points to the right and dy points down."""
    return ndimage.shift(a, (dy_pt * F.px_per_pt, dx_pt * F.px_per_pt), order=1, mode="constant")


def over(base, color, alpha):
    """Composite a flat colour with per-pixel alpha onto an RGB float image."""
    a = alpha[..., None]
    return base * (1 - a) + rgb(color) * a


def hatch(shape_, px_per_pt, spacing_pt, width_pt, direction=1):
    """Anti-aliased diagonal hatching, 1 on the lines and 0 between, in device pixels."""
    h, w = shape_
    u = (np.arange(w, dtype=np.float32)[None, :] + direction * np.arange(h, dtype=np.float32)[:, None]) / np.sqrt(2)
    sp = spacing_pt * px_per_pt
    dist = np.abs(np.mod(u + sp / 2, sp) - sp / 2)
    return np.clip(width_pt * px_per_pt / 2 + 0.5 - dist, 0, 1)


def polder_paint(L, below, deep, P, px_per_pt):
    """Land below NAP: a pale wash with fine hatching; more than 4 m below, cross-hatched."""
    L = over(L, P["polder"], below * P["polder_a"])
    hz = hatch(L.shape[:2], px_per_pt, P["hatch_sp"], P["hatch_w"], 1)
    L = over(L, P["hatch"], hz * below * P["hatch_a"])
    hz2 = hatch(L.shape[:2], px_per_pt, P["hatch_sp"], P["hatch_w"], -1)
    L = over(L, P["hatch"], hz2 * deep * P["hatch_a"])
    return L


def build_rasters(P, F):
    """The sea (opaque RGB) and the land and lake layers (RGBA), as float arrays."""
    nl = F.mask(LAND["nl"])
    land = np.maximum(nl, F.mask(LAND["other"]))
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
    L = polder_paint(L, below, deep, P, F.px_per_pt)
    # the shore shadow: a soft, slightly offset drop of the land onto the sea (Bremer used canvas shadowBlur)
    sh = shift(blur(land, 7, F), 1.5, 2.0, F) * (1 - land)
    shadow_a = np.clip(sh * P["shadow_a"] * 1.6, 0, P["shadow_a"])
    land_rgba = np.concatenate([L, land[..., None]], 2)
    # shadow goes into the land layer as a dark veil where there is no land
    sh_rgb = rgb(P["shadow"])
    a_tot = land + shadow_a * (1 - land)
    col = (L * land[..., None] + sh_rgb * (shadow_a * (1 - land))[..., None]) / np.maximum(a_tot[..., None], 1e-6)
    land_rgba = np.concatenate([col, a_tot[..., None]], 2)
    # lakes, with an inner shadow along their shores
    inner = blur(shift(1 - lakes, 0.8, 1.2, F), 2.5, F) * lakes
    lake_rgb = over(np.ones((F.h, F.w, 3), np.float32) * rgb(P["lake"]), P["shadow"], np.clip(inner * P["shadow_a"], 0, 1))
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


def cm_to_data(x_cm, y_cm):
    """Paper cm (from the lower left of the sheet) to map units."""
    return (X0 + (x_cm - G.MARGIN_CM) / G.FIELD_CM[0] * (X1 - X0), Y0 + (y_cm - G.MARGIN_CM) / G.FIELD_CM[1] * (Y1 - Y0))


def in_boxes(x, y, boxes):
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes)


def crosses(ax, P, V, boxes=()):
    """Small thick crosses at the whole degrees: teal on the sea, a quiet grey on land."""
    arm = 6.5 / PT_PER_UNIT
    land = [LAND["nl"], LAND["other"]]
    for lon in np.arange(3.0, 7.6, MAJOR):
        for lat in np.arange(51.0, 54.0, MAJOR):
            x, y = lon, float(G.merc_y(lat))
            if in_boxes(x, y, boxes): continue
            on_land = any(g.contains(Point(x, y)) for g in land)
            for dx, dy in ((arm, 0), (0, arm)):
                ax.plot([x - dx, x + dx], [y - dy, y + dy], color=P["rule"] if on_land else P["cross"], lw=1.5,
                        solid_capstyle="butt", zorder=12)


def degree_labels(fig, ax, P, V):
    """Degree notation around the edge of the field, in the margin."""
    fprop = T.fp(SANS)
    size = 8.5
    for lon in np.arange(3.0, 7.6, MAJOR):
        for y, va, d in ((Y1, "bottom", 6), (Y0, "top", -6)):
            T.straight_label(ax, PAPER, f"{lon:.0f}° E", (lon, y), fprop, size, P["muted"], ha="center",
                             va="bottom" if va == "bottom" else "top", dy=d, tracking=0.04, clip=False)
    for lat in np.arange(51.0, 54.0, MAJOR):
        y = float(G.merc_y(lat))
        T.straight_label(ax, PAPER, f"{lat:.0f}° N", (X0, y), fprop, size, P["muted"], ha="center", va="bottom",
                         angle=90, dx=-6, tracking=0.04, clip=False)
        T.straight_label(ax, PAPER, f"{lat:.0f}° N", (X1, y), fprop, size, P["muted"], ha="center", va="bottom",
                         angle=-90, dx=6, tracking=0.04, clip=False)


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
    (1, "river"): 2.6, (2, "river"): 1.15, (3, "river"): 0.55,
    (1, "canal"): 2.0, (2, "canal"): 1.0, (3, "canal"): 0.55,
}


def rivers(ax, P):
    """Rivers and canals, grouped by style so that each style is one LineCollection; the Dutch parts in the featured
    colours, the parts abroad lighter and thinner."""
    groups = {}
    for g, p in RIVERS:
        # the Eems estuary is a disputed border water: drawn as foreign, like the Ems upstream
        r, kind, home = p["rank"], p["kind"], p["part"] == "nl" and p["name"] not in ("Eems", "Ems")
        lw = RIVER_STYLE[(r, "river" if r == 1 else kind)]
        if home:
            col = {1: P["river1"], 2: P["river2"] if kind == "river" else P["canal"], 3: P["river3"]}[r]
            if kind == "canal" and r == 2: lw = 1.0
            z = 8.3 - r * 0.1
        else:
            col = P["river_out"] if r == 1 else P["river_out_minor"]
            lw *= 0.7; z = 7.5 - r * 0.1
        groups.setdefault((col, lw, z), []).extend(lines_of(g))
    for (col, lw, z), segs in groups.items():
        ax.add_collection(LineCollection(segs, colors=col, linewidths=lw, zorder=z, capstyle="round", joinstyle="round"))


def borders(ax, P):
    segs = []
    for g in BORDERS:
        segs += lines_of(g)
    ax.add_collection(LineCollection(segs, colors=P["border_band"], linewidths=5.5, alpha=0.8, zorder=4,
                                     capstyle="round", joinstyle="round"))
    ax.add_collection(LineCollection(segs, colors=P["border"], linewidths=0.8, linestyles=(0, (4, 2, 1, 2)), zorder=9.5))


# ---------------------------------------------------------------- labels
# Every label is placed by hand: name, size and the side of its dot it sits on
CITIES = [  # provincial capitals and the largest cities: bold capitals
    ("Amsterdam", 13.5, "s"), ("Rotterdam", 13.5, "w"), ("Den Haag", 13.5, "w"), ("Utrecht", 13.5, "e"),
    ("Eindhoven", 11, "e"), ("Groningen", 11, "e"), ("Tilburg", 11, "s"), ("Almere", 11, "e"), ("Breda", 11, "s"),
    ("Nijmegen", 11, "s"), ("Arnhem", 11, "n"), ("Zwolle", 11, "e"), ("Leeuwarden", 11, "w"), ("Maastricht", 11, "w"),
    ("Enschede", 11, "s"), ("Apeldoorn", 11, "e"), ("Haarlem", 11, "w"), ("'s-Hertogenbosch", 11, "s"),
    ("Middelburg", 11, "n"), ("Assen", 11, "e"), ("Lelystad", 11, "e"),
]
TOWNS = [
    ("Den Helder", "e"), ("Alkmaar", "e"), ("Hoorn", "e"), ("Harlingen", "w"), ("Delfzijl", "e"), ("Emmen", "e"),
    ("Deventer", "e"), ("Venlo", "e"), ("Roermond", "e"), ("Vlissingen", "s"), ("Dordrecht", "s"), ("Leiden", "w"),
    ("Amersfoort", "e"), ("Kampen", "w"), ("Meppel", "e"), ("Heerenveen", "e"), ("Sneek", "w"), ("Zutphen", "e"),
    ("Tiel", "n"), ("Gorinchem", "n"), ("Terneuzen", "s"), ("Goes", "n"), ("Hengelo", "n"), ("Heerlen", "e"),
    ("Bergen op Zoom", "w"), ("Zierikzee", "n"), ("Wageningen", "n"), ("Doetinchem", "e"), ("Gouda", "n"),
    ("Hilversum", "e"), ("Helmond", "e"), ("Oss", "e"), ("Sittard", "w"), ("Steenwijk", "e"), ("Winterswijk", "e"),
    ("Hardenberg", "e"), ("Stadskanaal", "e"), ("Delft", "w"),
]
NEIGHBOUR_CITIES = [("Antwerpen", "e"), ("Gent", "s"), ("Brugge", "s"), ("Bruxelles - Brussel", "s"), ("Leuven", "e"),
                    ("Hasselt", "e"), ("Liège", "e"), ("Aachen", "n"), ("Köln", "e"), ("Düsseldorf", "e"),
                    ("Duisburg", "e"), ("Essen", "e"), ("Mönchengladbach", "e"), ("Emden", "e"),
                    ("Oostende", "s"), ("Bonn", "e"), ("Krefeld", "w"), ("Nordhorn", "e"), ("Bocholt", "e"),
                    ("Mechelen", "e"), ("Wesel", "e")]
DISPLAY = {"Bruxelles - Brussel": "Brussel", "'s-Hertogenbosch": "’s-Hertogenbosch"}
PROVINCES = [("FRYSLÂN", 5.97, 53.07, 0), ("GRONINGEN", 6.86, 53.12, 0), ("DRENTHE", 6.62, 52.84, 0),
             ("OVERIJSSEL", 6.42, 52.40, 0), ("FLEVOLAND", 5.62, 52.62, 0), ("GELDERLAND", 6.42, 52.06, 0),
             ("NOORD-HOLLAND", 4.96, 52.70, 0), ("ZUID-HOLLAND", 4.70, 52.10, 0),
             ("ZEELAND", 3.55, 51.31, 0), ("NOORD-BRABANT", 5.25, 51.43, 0), ("LIMBURG", 5.93, 51.26, -72)]
COUNTRIES = [("BELGIË", 4.25, 50.62), ("DEUTSCHLAND", 6.95, 51.80)]


def place(name):
    for p in PLACES:
        if p["local"] == name or p["name"] == name:
            return p
    raise KeyError(name)


ANCHOR = {"e": ("left", "center", 1, 0), "w": ("right", "center", -1, 0), "n": ("center", "bottom", 0, 1),
          "s": ("center", "top", 0, -1), "ne": ("left", "bottom", 0.7, 0.7), "nw": ("right", "bottom", -0.7, 0.7),
          "se": ("left", "top", 0.7, -0.7), "sw": ("right", "top", -0.7, -0.7)}


def dot(ax, x, y, r_pt, face, ring, ring_pt=1.0, z=18):
    ax.scatter([x], [y], s=(2 * r_pt) ** 2, color=face, edgecolors=ring, linewidths=ring_pt, zorder=z)


def place_label(ax, P, name, size, where, style, gap=None):
    p = place(name)
    x, y = xy(p["lon"], p["lat"])
    ha, va, ux, uy = ANCHOR[where]
    text = DISPLAY.get(name, name)
    if style == "city":
        r = 3.2 if size > 12 else 2.6
        dot(ax, x, y, r, P["ink"], P["halo"], 1.2)
        prop, col, tr, txt, halo = T.fp(SANS, "bold"), P["ink"], 0.07, text.upper(), 3.2
    elif style == "town":
        r = 1.8
        dot(ax, x, y, r, P["secondary"], P["halo"], 0.9)
        prop, col, tr, txt, halo = T.fp(SANS), P["secondary"], 0.02, text, 2.6
    else:
        r = 1.8
        dot(ax, x, y, r, P["muted"], P["halo"], 0.8)
        prop, col, tr, txt, halo = T.fp(SANS, "bold"), P["muted"], 0.08, text.upper(), 2.4
    g = gap if gap is not None else r + 3.5
    T.straight_label(ax, PAPER, txt, (x, y), prop, size, col, ha=ha, va=va, halo=P["halo"], halo_pt=halo,
                     tracking=tr, dx=ux * g, dy=uy * g, zorder=21)


def river_geom(name):
    gs = [g for g, p in RIVERS if p["name"] == name]
    if not gs:
        raise KeyError(name)
    return linemerge(unary_union(gs)) if len(gs) > 1 else gs[0]


def river_guide(name, lon, lat, length_pt):
    """A piece of the named river's line, `length_pt` long, centred on the point nearest (lon, lat)."""
    g = river_geom(name)
    pt = Point(*xy(lon, lat))
    parts = [l for l in getattr(g, "geoms", [g])]
    line = min(parts, key=lambda l: l.distance(pt))
    s0 = line.project(pt); half = length_pt / PT_PER_UNIT / 2
    a, b = max(s0 - half, 0), min(s0 + half, line.length)
    return np.asarray(shapely.ops.substring(line, a, b).coords)


RIVER_LABELS = [  # name in the data, label text, anchor lon, lat, side (+1 above the line, -1 below), size
    ("Waal", "Waal", 5.72, 51.88, 1, 13), ("Nederrijn", "Nederrijn", 5.50, 51.955, 1, 12), ("Lek", "Lek", 5.18, 51.985, 1, 12),
    ("IJssel", "IJssel", 6.13, 52.36, 1, 13), ("Maas", "Maas", 5.88, 51.45, -1, 13), ("Maas", "Maas", 5.25, 51.775, 1, 12),
    ("Bergsche Maas", "Bergsche Maas", 4.97, 51.715, -1, 10.5), ("Rijn", "Rhein", 6.45, 51.74, 1, 12),
    ("Eems", "Ems", 7.30, 53.05, 1, 11),
    ("Maas", "Meuse", 5.25, 50.53, 1, 10.5), ("Schelde", "Schelde", 4.29, 51.10, 1, 10.5),
    ("Overijsselsche Vecht", "Vecht", 6.55, 52.55, 1, 10), ("Zwarte Water", "Zwarte Water", 6.08, 52.58, 1, 9),
    ("Roer", "Roer", 6.10, 51.12, 1, 9), ("Dommel", "Dommel", 5.40, 51.58, 1, 9), ("Linge", "Linge", 5.25, 51.86, -1, 9),
    ("Noordzeekanaal", "Noordzeekanaal", 4.72, 52.43, 1, 9), ("Amsterdam-Rijnkanaal", "Amsterdam-Rijnkanaal", 5.20, 52.20, 1, 8.5),
    ("Twentekanaal", "Twentekanaal", 6.45, 52.22, 1, 8.5), ("Prinses Margrietkanaal", "Prinses Margrietkanaal", 5.62, 53.0, 1, 8.5),
    ("Van Starkenborghkanaal", "Van Starkenborghkanaal", 6.28, 53.245, -1, 8.5),
    ("Lippe", "Lippe", 7.10, 51.67, 1, 9.5),
]


def river_label(ax, P, name, text, lon, lat, side, size):
    try:
        verts, codes, width = T.layout(text, T.fp(SERIF, style="italic"), size, 0.06)
        G_ = river_guide(name, lon, lat, width + 40)
    except (KeyError, ValueError) as e:
        print("  no river", name, e); return
    lw = 2.6 if name in ("Waal", "Nederrijn", "Lek", "IJssel", "Maas", "Rijn", "Bergsche Maas", "Nieuwe Waterweg") else 1.2
    off = (lw / 2 + 2.5) if side > 0 else -(lw / 2 + 2.5 + 0.68 * size)
    T.curved_label(ax, PAPER, text, G_, T.fp(SERIF, style="italic"), size, P["water_ink"], halo=P["halo"], halo_pt=2.6,
                   tracking=0.06, offset=off, valign="baseline", smooth=10, zorder=19)


WATER_LABELS = [  # text, guide points (lon, lat), size, tracking
    ("NOORDZEE", [(2.66, 51.755), (3.10, 51.80), (3.54, 51.765)], 26, 0.6),
    ("WADDENZEE", [(5.05, 53.22), (5.5, 53.33), (6.0, 53.43)], 15, 0.5),
    ("IJsselmeer", [(5.20, 52.79), (5.48, 52.87)], 16, 0.18),
    ("Markermeer", [(5.12, 52.52), (5.33, 52.58)], 12, 0.15),
    ("Oosterschelde", [(3.72, 51.62), (3.92, 51.56), (4.08, 51.52)], 11, 0.12),
    ("Westerschelde", [(3.55, 51.41), (3.75, 51.38), (3.95, 51.37)], 11, 0.12),
    ("Haringvliet", [(4.05, 51.80), (4.25, 51.73)], 10, 0.1),
    ("Hollandsch Diep", [(4.47, 51.672), (4.62, 51.682)], 8.5, 0.06),
    ("Grevelingen", [(3.88, 51.735), (4.05, 51.71)], 9, 0.1),
    ("Lauwersmeer", [(6.15, 53.37), (6.25, 53.36)], 8, 0.05),
    ("Eems", [(6.95, 53.45), (7.05, 53.35)], 10, 0.12),
    ("Dollard", [(7.10, 53.27), (7.25, 53.26)], 9, 0.1),
]
ISLANDS = [("Texel", [(4.745, 53.03), (4.79, 53.10), (4.86, 53.165)]), ("Vlieland", [(4.93, 53.228), (5.10, 53.293)]),
           ("Terschelling", [(5.17, 53.36), (5.33, 53.408), (5.52, 53.438)]), ("Ameland", [(5.64, 53.445), (5.90, 53.452)]),
           ("Schiermonnikoog", [(6.12, 53.472), (6.30, 53.484)])]
REGIONS = [("VELUWE", [(5.70, 52.26), (5.95, 52.26)]), ("DE PEEL", [(5.75, 51.38), (5.95, 51.38)]),
           ("Afsluitdijk", [(5.10, 52.945), (5.33, 53.045)])]


def smooth_guide(pts):
    g = np.array([xy(a, b) for a, b in pts])
    if len(g) == 2:
        return np.linspace(g[0], g[1], 20)
    t = np.linspace(0, 1, 60)[:, None]           # a quadratic curve through the three points
    c = 2 * g[1] - (g[0] + g[2]) / 2
    return (1 - t) ** 2 * g[0] + 2 * (1 - t) * t * c + t ** 2 * g[2]


def labels(ax, P):
    for name, x_, y_, ang in PROVINCES:
        T.straight_label(ax, PAPER, name, xy(x_, y_), T.fp(SANS), 11.5, P["muted"], ha="center", va="center",
                         tracking=0.3, alpha=0.6, angle=ang, zorder=15)
    for name, x_, y_ in COUNTRIES:
        T.straight_label(ax, PAPER, name, xy(x_, y_), T.fp(SANS), 16, P["muted"], ha="center", va="center",
                         tracking=0.6, alpha=0.55, zorder=15)
    for name, pts in REGIONS:
        on_water = name == "Afsluitdijk"                # the dam's name sits on the water beside it
        T.curved_label(ax, PAPER, name, smooth_guide(pts), T.fp(SERIF, style="italic"), 9,
                       P["water_ink"] if on_water else P["muted"], tracking=0.3 if not on_water else 0.12, smooth=0,
                       zorder=15, halo=P["lake"] if on_water else P["halo"], halo_pt=2.0)
    for text, pts, size, tr in WATER_LABELS:
        T.curved_label(ax, PAPER, text, smooth_guide(pts), T.fp(SERIF, style="italic"), size, P["water_ink"],
                       tracking=tr, smooth=0, zorder=16, alpha=0.9, halo=P["lake"], halo_pt=2.4)
    for name, pts in ISLANDS:
        T.curved_label(ax, PAPER, name, smooth_guide(pts), T.fp(SANS, "bold"), 8.5, P["ink"], tracking=0.16,
                       smooth=0, zorder=15, alpha=0.32)
    for name, size, where in CITIES:
        place_label(ax, P, name, size, where, "city")
    for name, where in TOWNS:
        place_label(ax, P, name, 9.5, where, "town")
    for name, where in NEIGHBOUR_CITIES:
        try:
            place_label(ax, P, name, 8.5, where, "neighbour")
        except KeyError:
            print("  no place", name)
    for args in RIVER_LABELS:
        river_label(ax, P, *args)


# ---------------------------------------------------------------- story marks: the Rhine's two bifurcations
def bifurcations():
    """The upstream ends of the Pannerdensch Kanaal (Pannerdensche Kop) and of the IJssel (IJsselkop), from the data."""
    out = []
    for name, label, near in (("Pannerdensch Kanaal", "Pannerdensche Kop", (6.05, 51.87)), ("IJssel", "IJsselkop", (5.94, 51.96))):
        try:
            g = river_geom(name)
        except KeyError:
            continue
        pt = Point(*xy(*near))
        ends = [Point(l.coords[0]) for l in getattr(g, "geoms", [g])] + [Point(l.coords[-1]) for l in getattr(g, "geoms", [g])]
        e = min(ends, key=lambda q: q.distance(pt))
        out.append((label, e.x, e.y))
    return out


def diamond(ax, x, y, r_pt, face, ring, z=22):
    ax.scatter([x], [y], s=(2 * r_pt) ** 2, marker="D", color=face, edgecolors=ring, linewidths=1.2, zorder=z)


def story(ax, P):
    for label, x, y in bifurcations():
        diamond(ax, x, y, 4.2, P["accent"], P["halo"])
        dx, ha = 8, "left"
        dy = -9 if label == "Pannerdensche Kop" else 7
        T.straight_label(ax, PAPER, label, (x, y), T.fp(SERIF, "bold", "italic"), 10, P["accent"], ha=ha, va="center",
                         halo=P["halo"], halo_pt=2.8, dx=dx, dy=dy, zorder=22)
    hi, lo = STATS["highest"], STATS["lowest"]
    x, y = xy(hi["lon"], hi["lat"])
    ax.scatter([x], [y], s=46, marker="^", color=P["ink"], edgecolors=P["halo"], linewidths=1.0, zorder=22)
    T.straight_label(ax, PAPER, f"Vaalserberg {hi['m']:.0f} m", (x, y), T.fp(SANS, "bold", "italic"), 10, P["ink"],
                     ha="center", va="top", halo=P["halo"], halo_pt=2.8, dy=-7, zorder=22)
    x, y = xy(lo["lon"], lo["lat"])
    ax.scatter([x], [y], s=46, marker="v", color=P["ink"], edgecolors=P["halo"], linewidths=1.0, zorder=22)
    T.straight_label(ax, PAPER, f"lowest ground {LOWEST} m", (x, y), T.fp(SANS, "bold", "italic"), 9.5,
                     P["ink"], ha="right", va="center", halo=P["halo"], halo_pt=2.8, dx=-7, dy=-1, zorder=22)


# ---------------------------------------------------------------- title block, legend, scale bar
def cm_to_fig(x_cm, y_cm):
    return x_cm / G.PAPER_CM[0], y_cm / G.PAPER_CM[1]


def title_block(fig, ax, P, V):
    x = G.MARGIN_CM + 1.4                                  # left edge of the block on paper, cm
    top = G.PAPER_CM[1] - G.MARGIN_CM - 1.5
    fx, fy = cm_to_fig(x, top)
    fig.text(fx, fy, "NEDERLAND  ·  RIVERS, CANALS AND THE LAND BELOW THE SEA", fontsize=10, color=P["water_ink"],
             fontfamily=SANS, fontweight="bold", va="top", ha="left")
    lines = TITLE_LINES
    ty = top - 1.0
    for i, line in enumerate(lines):
        fig.text(fx, cm_to_fig(0, ty - i * 1.62)[1], line, fontsize=41, color=P["ink"], fontfamily=SERIF, va="top", ha="left")
    sy = ty - len(lines) * 1.62 - 0.45
    fig.text(fx, cm_to_fig(0, sy)[1], SUBTITLE_WRAPPED, fontsize=12.5, color=P["secondary"], fontfamily=SANS, va="top",
             ha="left", linespacing=1.45)
    bottom = sy - 0.62 * (SUBTITLE_WRAPPED.count("\n") + 1) - 0.4
    return bottom - 1.2, (x - 0.6, bottom, x + 15.6, top + 0.6)


def legend(fig, ax, P, V, top_cm):
    """Legend rows drawn in figure cm on an overlay axes."""
    x = G.MARGIN_CM + 1.4
    lax = fig.add_axes([0, 0, 1, 1], facecolor="none"); lax.set_xlim(0, G.PAPER_CM[0]); lax.set_ylim(0, G.PAPER_CM[1])
    lax.axis("off"); lax.set_zorder(40); lax.set_aspect("auto")
    card = (x - 0.6, top_cm - 8 * 0.78 - 1.95, x + 11.4, top_cm + 0.65)
    for k, a in enumerate((0.05, 0.035, 0.025, 0.015)):
        d = 0.05 * (k + 1)
        lax.add_patch(Rectangle((card[0] - d + 0.06, card[1] - d - 0.08), card[2] - card[0] + 2 * d, card[3] - card[1] + 2 * d,
                                facecolor=P["shadow"], alpha=a, edgecolor="none", zorder=-2))
    lax.add_patch(Rectangle(card[:2], card[2] - card[0], card[3] - card[1], facecolor=P["card"], edgecolor=P["card_edge"],
                            lw=0.6, zorder=-1))
    rows = [
        ("swatch", 0, None, "Land below sea level (NAP 0 m), hatched"),
        ("swatch", 1, None, "More than 4 m below, cross-hatched"),
        ("contour", None, None, "Height contours: −5, 0, 5, 20, 50 m, then every 100 m"),
        ("line", P["river1"], 2.6, "Rhine, Maas and Schelde: the delta\u2019s main branches"),
        ("line", P["river2"], 1.15, "Rivers of 25 km and more; canals for large ships"),
        ("line", P["river3"], 0.55, "Smaller rivers and canals"),
        ("line", P["river_out"], 1.8, "Rivers beyond the border"),
        ("diamond", P["accent"], None, "Where the Rhine splits in three"),
    ]
    y = top_cm
    for kind, col, a, text in rows:
        cx = x + 0.55
        if kind == "swatch":
            w_px, h_px = int(1.1 * CM * DPI), int(0.44 * CM * DPI)
            sw = np.ones((h_px, w_px, 3), np.float32) * rgb(P["land_nl"])
            one = np.ones((h_px, w_px), np.float32)
            sw = polder_paint(sw, one, one * col, P, DPI / 72.0)
            lax.imshow(np.clip(sw, 0, 1), extent=(x, x + 1.1, y - 0.22, y + 0.22), interpolation="none", zorder=1)
            lax.add_patch(Rectangle((x, y - 0.22), 1.1, 0.44, fill=False, edgecolor=P["rule"], lw=0.5, zorder=2))
        elif kind == "contour":
            for k, dy in enumerate((-0.14, 0.0, 0.14)):
                lax.plot([x, x + 1.1], [y + dy + 0.05 * math.sin(k), y + dy - 0.03], color=P["contour"], lw=0.5, alpha=0.9)
        elif kind == "line":
            lax.plot([x, x + 1.1], [y, y], color=col, lw=a, solid_capstyle="round")
        elif kind == "diamond":
            lax.scatter([cx], [y], s=(2 * 4.2) ** 2, marker="D", color=col, edgecolors=P["halo"], linewidths=1.2)
        lax.text(x + 1.5, y, text, fontsize=11, color=P["secondary"], fontfamily=SANS, va="center", ha="left")
        y -= 0.78
    # scale bar, true at 52° N
    y -= 0.5
    km_cm = G.FIELD_CM[0] / ((X1 - X0) * 111.32 * math.cos(math.radians(52)))
    ticks = [0, 10, 20, 30, 40, 50]
    for i in range(5):
        lax.add_patch(Rectangle((x + ticks[i] * km_cm, y), 10 * km_cm, 0.16, facecolor=P["ink"] if i % 2 == 0 else P["halo"],
                                edgecolor=P["ink"], lw=0.6))
    for t in ticks:
        lax.text(x + t * km_cm, y + 0.32, f"{t}", fontsize=9, color=P["secondary"], fontfamily=SANS, ha="center", va="bottom")
    lax.text(x + 50 * km_cm + 0.35, y + 0.08, "km", fontsize=9, color=P["secondary"], fontfamily=SANS, ha="left", va="center")
    lax.text(x, y - 0.35, f"Scale 1 : {thousands(round(G.scale_denominator() / 1000) * 1000)} at 52° N; Mercator projection",
             fontsize=9, color=P["muted"], fontfamily=SANS, ha="left", va="top")
    return card


def footer_line(fig, P):
    fig.text(G.MARGIN_CM / G.PAPER_CM[0], 1.55 / G.PAPER_CM[1], footer(SOURCE, __file__), fontsize=8.5, color=P["muted"],
             fontfamily=SANS, ha="left", va="center")


# ---------------------------------------------------------------- map-in-map: the Rhine and Maas from source to sea
INSET_EXT = (1.0, 12.6, 45.6, 54.4)


def inset(fig, P, V, rect_cm):
    """The map-in-map on a card; rect_cm is the x and the top of the card's content, and the map's width, in paper cm.
    Returns the card's box."""
    feats = load_fc("nl_inset.geojson")
    x0, x1, la0, la1 = INSET_EXT
    y0, y1 = float(G.merc_y(la0)), float(G.merc_y(la1))
    x_cm, top_cm, w_cm = rect_cm
    h_cm = w_cm * (y1 - y0) / (x1 - x0)
    y_cm = top_cm - h_cm
    # a card like the legend's, holding the map and its caption
    sax = fig.add_axes([0, 0, 1, 1], facecolor="none"); sax.set_xlim(0, G.PAPER_CM[0]); sax.set_ylim(0, G.PAPER_CM[1]); sax.axis("off")
    sax.set_zorder(35); sax.set_aspect("auto")
    card = (x_cm - 0.6, y_cm - 2.15, x_cm + w_cm + 0.6, y_cm + h_cm + 0.6)
    for k, a in enumerate((0.05, 0.035, 0.025, 0.015)):
        d = 0.05 * (k + 1)
        sax.add_patch(Rectangle((card[0] - d + 0.06, card[1] - d - 0.08), card[2] - card[0] + 2 * d, card[3] - card[1] + 2 * d,
                                facecolor=P["shadow"], alpha=a, edgecolor="none"))
    sax.add_patch(Rectangle(card[:2], card[2] - card[0], card[3] - card[1], facecolor=P["card"], edgecolor=P["card_edge"], lw=0.6))
    iax = fig.add_axes([x_cm / G.PAPER_CM[0], y_cm / G.PAPER_CM[1], w_cm / G.PAPER_CM[0], h_cm / G.PAPER_CM[1]])
    iax.set_zorder(36)
    iax.set_xlim(x0, x1); iax.set_ylim(y0, y1); iax.set_xticks([]); iax.set_yticks([])
    iax.set_facecolor(P["sea"])
    for s_ in iax.spines.values():
        s_.set_visible(True); s_.set_color(P["rule"]); s_.set_linewidth(0.5)
    for g, p in feats:
        g = to_map(g)
        if p["layer"] == "country":
            col = P["land_nl"] if p.get("iso") == "NL" else P["land_other"]
            for poly in getattr(g, "geoms", [g]):
                if poly.geom_type != "Polygon": continue
                iax.add_patch(MPoly(np.asarray(poly.exterior.coords), closed=True, facecolor=col, edgecolor=P["rule"], lw=0.35))
    for g, p in feats:
        if p["layer"] == "lake":
            g = to_map(g)
            for poly in getattr(g, "geoms", [g]):
                if poly.geom_type == "Polygon":
                    iax.add_patch(MPoly(np.asarray(poly.exterior.coords), closed=True, facecolor=P["lake"], edgecolor=P["river_out"], lw=0.3))
    main = {"Rhine", "Rhein", "Rhin", "Waal", "Nederrijn", "Lek", "IJssel", "Meuse", "Maas", "Rhine/Rhein", "Hinterrhein",
            "Vorderrhein", "Alpenrhein", "Hochrhein", "Oberrhein", "Niederrhein", "Meuse/Maas"}
    for g, p in feats:
        if p["layer"] != "river": continue
        g = to_map(g)
        nm = p.get("name", "")
        is_main = any(m.lower() in nm.lower() for m in ("rhine", "rhein", "rhin", "meuse", "maas", "waal", "ijssel", "lek"))
        col = P["river1"] if is_main else P["river_out_minor"]
        lw = 1.5 if is_main else 0.45
        iax.add_collection(LineCollection(lines_of(g), colors=col, linewidths=lw, zorder=3 if is_main else 2,
                                          capstyle="round", joinstyle="round"))
    # the main map's frame
    iax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fill=False, edgecolor=P["ink"], lw=0.7, zorder=5))
    ip = T.Paper(x0, y0, w_cm * CM * 72 / (x1 - x0))
    T.straight_label(iax, ip, "Rhein", xy(8.15, 49.6), T.fp(SERIF, style="italic"), 9, P["water_ink"], ha="left", va="center",
                     halo=P["halo"], halo_pt=2, dx=4, angle=70)
    T.straight_label(iax, ip, "Maas", xy(5.05, 49.2), T.fp(SERIF, style="italic"), 9, P["water_ink"], ha="right", va="center",
                     halo=P["halo"], halo_pt=2, dx=-4, angle=60)
    T.straight_label(iax, ip, "Bodensee", xy(9.35, 47.62), T.fp(SERIF, style="italic"), 7, P["water_ink"], ha="center", va="top",
                     halo=P["halo"], halo_pt=2, dy=-5)
    T.straight_label(iax, ip, "ALPEN", xy(9.7, 46.4), T.fp(SANS), 7.5, P["muted"], ha="center", va="center", tracking=0.4)
    # caption under the card
    sax.text(x_cm, y_cm - 0.35, "WHERE THE WATER COMES FROM", fontsize=9, color=P["water_ink"], fontfamily=SANS,
             fontweight="bold", ha="left", va="top")
    sax.text(x_cm, y_cm - 0.9, "The Rhine rises in the Swiss Alps, the Maas in north-east France;\nthe rectangle is the extent of the main map",
             fontsize=10, color=P["secondary"], fontfamily=SANS, ha="left", va="top", linespacing=1.35)
    return card


# ---------------------------------------------------------------- draw
def draw(V):
    P = palette(V)
    plt.rcParams["savefig.bbox"] = "standard"
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
    zgrid = F.elevation()[1]
    nl_g = sub.mask(NL, ss=1) > 0.5
    land_g = nl_g | (sub.mask(LAND["other"], ss=1) > 0.5)
    lakes_g = sub.mask(LAKES, ss=1) > 0.5
    contours(ax, P, zgrid, nl_g & ~lakes_g, land_g & ~lakes_g)
    show(ax, lake_rgba, 5)
    # wide river water
    ra = F.mask(RIVER_AREAS)
    show(ax, np.concatenate([np.ones((F.h, F.w, 3), np.float32) * rgb(P["river_area"]), ra[..., None]], 2), 6)
    borders(ax, P)
    rivers(ax, P)
    labels(ax, P)
    story(ax, P)
    bottom, tbox = title_block(fig, ax, P, V)
    legend_h = 0.65 + 8 * 0.78 + 2.0                  # the legend card sits on the quiet land in the lower left
    lbox = legend(fig, ax, P, V, G.MARGIN_CM + 0.8 + legend_h - 0.65)
    ibox = inset(fig, P, V, (G.MARGIN_CM + 1.4, bottom, INSET_W))
    boxes = [cm_to_data(*b[:2]) + cm_to_data(*b[2:]) for b in (tbox, lbox, ibox)]
    a, b = cm_to_data(*tbox[:2]), cm_to_data(*tbox[2:])
    ax.add_patch(Rectangle(a, b[0] - a[0], b[1] - a[1], facecolor=P["sea"], edgecolor="none", zorder=1.5))
    crosses(ax, P, V, boxes)
    footer_line(fig, P)
    # frame
    ax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fill=False, edgecolor=P["ink"], lw=0.8, zorder=30))
    degree_labels(fig, ax, P, V)
    return fig


LOWEST = f"{STATS['lowest']['m']:.1f}".replace("-", "−")
META = dict(
    title=TITLE,
    subtitle=("A 50 × 60 cm print map in the manner of Nadieh Bremer's personal map of Norway: rivers and main canals as "
              "the featured layer, land below sea level hatched, height contours, a map-in-map of the Rhine and Maas basins"),
    kind="map", form="reference map", medium="print", tool="matplotlib",
    data=("OpenStreetMap contributors (ODbL), coastline, rivers, canals, water areas, borders and places, via the Overpass "
          "API, downloaded 2026-10-12; AHN4 DTM (Rijkswaterstaat and Het Waterschapshuis, via PDOK, CC0); AWS Terrain Tiles "
          "(Mapzen; SRTM, GMTED2010, ETOPO1); Natural Earth 10 m rivers, lakes and countries (public domain)"),
    script=rel(__file__),
    alt=(f"A portrait print map of the Netherlands in Mercator projection. The country is white on a pale teal North Sea, "
         f"its neighbours in cream. Land below sea level is hatched in teal: {SHARE * 100:.1f} % of the ground measured "
         f"by AHN4, about {thousands(round(STATS['km2_below_nap'], -1))} km², most of Holland, Flevoland, Friesland and "
         "Groningen. The Rhine enters from Germany and splits at the Pannerdensche Kop and the IJsselkop, marked in "
         "terracotta, into the Waal, Nederrijn–Lek and IJssel; with the Maas they are drawn in the deepest teal and "
         "thickest line, other rivers and canals thinner and lighter. Height contours rise to the Vaalserberg, "
         f"{STATS['highest']['m']:.0f} m; the lowest ground is {LOWEST} m in the Zuidplaspolder. "
         "A map-in-map shows the Rhine from the Alps and the Maas from France."),
    note=("Every number is computed from data/maps/ (nl_stats.json, written by fetch_nl.py). Labels are set as glyph "
          "outlines, bent along rivers and water bodies where they follow a shape. Rasters (sea, land, hatching, shadows, "
          f"lakes) are drawn at {DPI} dpi and embedded in the PDF; lines and type are vector."),
)


if __name__ == "__main__":
    out = os.path.join(FIGURES, GROUP); os.makedirs(out, exist_ok=True)
    for mode in (sys.argv[1:] or MODES):
        V = vellum.use(mode)
        fig = draw(V)
        fig.savefig(os.path.join(out, f"{NAME}_{mode}.png"), dpi=DPI, facecolor=fig.get_facecolor())
        if mode == "light":
            fig.savefig(os.path.join(out, f"{NAME}_{mode}.pdf"), dpi=DPI, facecolor=fig.get_facecolor())
        plt.close(fig)
        print(mode, "done")
    record(GROUP, NAME, META)
