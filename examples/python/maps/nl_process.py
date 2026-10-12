"""nl_process.py: turn the raw downloads cached by fetch_nl.py into the small files in data/maps/.

Called by fetch_nl.py. Writes
  nl_land.geojson      land polygons built from the OSM coastline, clipped to the download box, tagged nl / other
  nl_water.geojson     lakes (0.15 km2 and more) and the wide water of rivers and canals (0.02 km2 and more)
  nl_rivers.geojson    rivers and main canals as merged, simplified lines with name, kind, rank and country
  nl_borders.geojson   the land borders of the Netherlands and its neighbours (OSM admin_level 2, maritime parts dropped)
  nl_places.json       cities and towns with population
  nl_elevation.png     ground height on the map's Mercator grid, 16 bit: metres = value / 10 - 100, 0 = sea
  nl_stats.json        the numbers the map quotes, computed here
  nl_inset.geojson     Natural Earth rivers, lakes and countries for the Rhine-Meuse inset
"""
import json, math, os, sys, zipfile
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import shapely
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, Point, box, mapping, shape
from shapely.ops import linemerge, polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_nl as F                                          # noqa: E402
from nl_geo import FRAME, BBOX, GRID, grid_lonlat, merc_y, ELEV_SCALE, ELEV_OFFSET   # noqa: E402

OUT = F.OUT
S, W, N, E = BBOX
CLIP = box(W + 0.03, S + 0.03, E - 0.03, N - 0.03)             # inside the download box, so clipped ways are complete


def km2(geom):
    """Area of a lon/lat geometry in km2 (local equirectangular scale at its centroid; fine at this size)."""
    lat = geom.centroid.y if not geom.is_empty else 52
    return geom.area * 111.32 ** 2 * math.cos(math.radians(lat))


def km(geom):
    lat = geom.centroid.y if not geom.is_empty else 52
    c = math.cos(math.radians(lat))
    tot = 0.0
    for g in getattr(geom, "geoms", [geom]):
        a = np.asarray(g.coords)
        if len(a) > 1:
            d = np.diff(a, axis=0); tot += np.sum(np.hypot(d[:, 0] * c, d[:, 1])) * 111.32
    return tot


def way_line(el):
    return LineString([(p["lon"], p["lat"]) for p in el["geometry"]]) if len(el.get("geometry", [])) > 1 else None


def rounded(geom, nd=5):
    """GeoJSON mapping with coordinates rounded to about 1 m."""
    return json.loads(json.dumps(mapping(geom)), parse_float=lambda s: round(float(s), nd))


def write_fc(name, feats):
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": p, "geometry": rounded(g)} for g, p in feats
                                                    if g is not None and not g.is_empty]}
    path = os.path.join(OUT, name)
    json.dump(fc, open(path, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print(f"  {name}: {len(fc['features'])} features, {os.path.getsize(path) / 1e6:.2f} MB")


# ---- land from the coastline: OSM coastlines have the land on their left
def land_polygons():
    js = F.overpass("coastline")
    lines = [l for l in (way_line(e) for e in js["elements"] if e["type"] == "way") if l is not None]
    coast = unary_union([l.intersection(CLIP) for l in lines])
    faces = list(polygonize(unary_union([coast, CLIP.exterior])))
    # sample points a few metres left (land) and right (water) of every coastline segment
    land_pts, water_pts = [], []
    eps = 2e-5
    for l in lines:
        a = np.asarray(l.coords)
        if len(a) < 2: continue
        d = np.diff(a, axis=0); m = (a[1:] + a[:-1]) / 2
        nrm = np.hypot(d[:, 0], d[:, 1]); ok = nrm > 0
        left = np.stack([-d[ok, 1], d[ok, 0]], 1) / nrm[ok, None]
        land_pts.append(m[ok] + eps * left); water_pts.append(m[ok] - eps * left)
    land_pts, water_pts = np.concatenate(land_pts), np.concatenate(water_pts)
    land = []
    for f in faces:
        b = f.bounds
        def count(P):
            sel = P[(P[:, 0] >= b[0]) & (P[:, 0] <= b[2]) & (P[:, 1] >= b[1]) & (P[:, 1] <= b[3])]
            if len(sel) > 4000: sel = sel[:: len(sel) // 4000 + 1]
            return int(shapely.contains_xy(f, sel[:, 0], sel[:, 1]).sum()) if len(sel) else 0
        nl_, nw = count(land_pts), count(water_pts)
        if nl_ > nw: land.append(f)
    return unary_union(land)


def nl_country():
    """The Netherlands (European part) from relation 47796, which includes its territorial sea."""
    js = F.overpass("nl_relation")
    rel = [e for e in js["elements"] if e["type"] == "relation"][0]
    outer = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in rel["members"]
             if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
    inner = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in rel["members"]
             if m["type"] == "way" and m.get("role") == "inner" and m.get("geometry")]
    poly = unary_union(list(polygonize(unary_union(outer))))
    if inner:
        poly = poly.difference(unary_union(list(polygonize(unary_union(inner)))))
    return poly


# ---- water areas
def assemble_relation(el):
    outer, inner = [], []
    for m in el.get("members", []):
        if m["type"] != "way" or not m.get("geometry"): continue
        l = LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) if len(m["geometry"]) > 1 else None
        if l is None: continue
        (inner if m.get("role") == "inner" else outer).append(l)
    if not outer: return None
    try:
        poly = unary_union(list(polygonize(unary_union(outer))))
        if inner:
            poly = poly.difference(unary_union(list(polygonize(unary_union(inner)))))
        return poly.buffer(0)
    except Exception:
        return None


def water_areas():
    feats = []
    for name in ("water_rel", "water_way", "water_way_named"):
        for el in F.overpass(name)["elements"]:
            t = el.get("tags", {})
            if el["type"] == "relation":
                g = assemble_relation(el)
            elif el["type"] == "way" and len(el.get("geometry", [])) > 3:
                c = [(p["lon"], p["lat"]) for p in el["geometry"]]
                if c[0] != c[-1]: continue
                g = Polygon(c).buffer(0)
            else:
                continue
            if g is None or g.is_empty: continue
            g = g.intersection(CLIP)
            if g.is_empty: continue
            a = km2(g)
            w = t.get("water", "")
            kind = "river" if w in ("river", "canal", "oxbow") else "lake"
            if (kind == "lake" and a < 0.15) or (kind == "river" and a < 0.02): continue
            feats.append((g, dict(kind=kind, name=t.get("name", ""), water=w, km2=round(a, 3))))
    print(f"  water areas kept: {len(feats)}")
    # merge into one lake layer and one river layer, simplified to about 15 m
    out = []
    for kind in ("lake", "river"):
        u = unary_union([g for g, p in feats if p["kind"] == kind]).simplify(0.00015, preserve_topology=True)
        for g in getattr(u, "geoms", [u]):
            if km2(g) >= (0.15 if kind == "lake" else 0.02):
                out.append((g, dict(kind=kind)))
    named = sorted([(p["km2"], p["name"], g.representative_point().coords[0]) for g, p in feats if p["name"]], reverse=True)[:60]
    return out, named


# ---- rivers and canals
MAJOR = {  # the big branches of the Rhine-Meuse-Scheldt delta and their German / Belgian continuations: rank 1
    "Rijn", "Rhein", "Bovenrijn", "Waal", "Nederrijn", "Lek", "IJssel", "Gelderse IJssel", "Maas", "Meuse", "Bergsche Maas",
    "Amer", "Nieuwe Merwede", "Boven Merwede", "Beneden Merwede", "Noord", "Oude Maas", "Nieuwe Maas", "Nieuwe Waterweg",
    "Pannerdensch Kanaal", "Dordtsche Kil", "Spui", "Hollandsch Diep", "Haringvliet", "Scheur", "Schelde", "Escaut",
    "Zeeschelde", "Ems", "Eems", "Afgedamde Maas", "Boven-Rijn", "Boven-Merwede", "Beneden-Merwede",
}


def rivers(nl):
    """Each river or canal is written as up to two features, its part in the Netherlands (part "nl", the country
    widened by about 250 m so that border rivers such as the Maas in Limburg count as Dutch) and its part abroad."""
    nl = nl.buffer(0.003)
    feats = []
    groups = defaultdict(list)
    local = {}                                       # the Dutch name keys the line; the local name labels it abroad
    for name in ("rivers", "canals"):
        for el in F.overpass(name)["elements"]:
            if el["type"] != "way": continue
            t = el.get("tags", {})
            l = way_line(el)
            if l is None: continue
            l = l.intersection(CLIP)
            if l.is_empty: continue
            nm = t.get("name:nl") or t.get("name") or ""
            if nm and t.get("name"):
                local.setdefault(nm, t["name"])
            kind = t.get("waterway")
            cemt = t.get("CEMT", t.get("cemt", ""))
            if kind == "canal" and not (cemt or nm.lower().endswith(("kanaal", "kanal", "canal")) or "kanaal" in nm.lower()
                                        or "vaart" in nm.lower() or t.get("ship") == "yes"):
                continue
            groups[(kind, nm, cemt if kind == "canal" else "")].append(l)
    for (kind, nm, cemt), ls in groups.items():
        merged = linemerge(unary_union(ls)) if len(ls) > 1 else ls[0]
        if not nm:                                   # unnamed water: keep only continuous stretches of 5 km or more
            keep = [g for g in getattr(merged, "geoms", [merged]) if km(g) >= 5]
            if not keep: continue
            merged = MultiLineString(keep) if len(keep) > 1 else keep[0]
        L = km(merged)
        major = nm in MAJOR
        if kind == "river" and not nm and L < 3: continue
        if kind == "river" and L < 4 and not major: continue
        if kind == "canal" and L < (3 if cemt else 8): continue
        merged = merged.simplify(0.00008, preserve_topology=False)
        inside = merged.intersection(nl)
        outside = merged.difference(nl)
        frac = km(inside) / max(L, 1e-9)
        big_canal = kind == "canal" and cemt in ("IV", "Va", "Vb", "VIa", "VIb", "VIc", "VII")
        rank = 1 if major else (2 if nm and ((kind == "river" and L >= 25) or big_canal) else 3)
        props = dict(name=nm, local=local.get(nm, nm), kind=kind, cemt=cemt, rank=rank, km=round(L, 1), nl=round(frac, 2))
        for part, g in (("nl", inside), ("abroad", outside)):
            g = linemerge(g) if g.geom_type == "MultiLineString" else g
            if not g.is_empty and g.length > 0:
                feats.append((g, dict(props, part=part)))
    return feats


def borders():
    feats = []
    for el in F.overpass("borders")["elements"]:
        t = el.get("tags", {})
        if el["type"] != "way" or t.get("maritime") == "yes" or t.get("natural") == "coastline": continue
        l = way_line(el)
        if l is None: continue
        l = l.intersection(CLIP)
        if not l.is_empty: feats.append(l)
    u = linemerge(unary_union(feats)).simplify(0.0001)
    return [(g, {}) for g in getattr(u, "geoms", [u])]


def places():
    out = []
    for el in F.overpass("places")["elements"]:
        t = el.get("tags", {})
        if "name" not in t: continue
        try: pop = int(str(t.get("population", "0")).replace(",", "").replace(".", "").split(";")[0] or 0)
        except ValueError: pop = 0
        out.append(dict(name=t.get("name:nl", t["name"]) if t.get("name:nl") else t["name"], local=t["name"],
                        place=t["place"], pop=pop, lon=round(el["lon"], 5), lat=round(el["lat"], 5)))
    return sorted(out, key=lambda p: -p["pop"])


# ---- rasters
def rasterize(geom, shape_, to_px, ss=1):
    """Mask of a (multi)polygon on a pixel grid; to_px maps (lon, lat) arrays to fractional (col, row)."""
    h, w = shape_
    img = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(img)
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.geom_type != "Polygon": continue
        def ring(r):
            a = np.asarray(r.coords); c, rr = to_px(a[:, 0], a[:, 1])
            return list(zip(c * ss, rr * ss))
        d.polygon(ring(g.exterior), fill=255)
        for h_ in g.interiors:
            d.polygon(ring(h_), fill=0)
    m = np.asarray(img, np.float32) / 255
    if ss > 1:
        m = m.reshape(h, ss, w, ss).mean(axis=(1, 3))
    return m


def fill_gaps(z, sigma=3, rounds=6):
    """Fill NaN cells by normalized Gaussian convolution, widening until nothing is left."""
    z = z.copy()
    for k in range(rounds):
        bad = np.isnan(z)
        if not bad.any(): break
        v = np.where(bad, 0, z); w = (~bad).astype(np.float32)
        s = sigma * (2 ** k)
        num, den = ndimage.gaussian_filter(v, s), ndimage.gaussian_filter(w, s)
        z[bad] = np.where(den[bad] > 1e-3, num[bad] / np.maximum(den[bad], 1e-6), np.nan)
    return z


def elevation(nl_land, water, land):
    ahn = F.ahn()                                     # 100 m point samples, RD New, row 0 north
    ny, nx = ahn.shape
    x0, y1, res = F.AHN_X[0], F.AHN_Y[1], F.AHN_RES

    def rd_px(lon, lat):
        x, y = F.wgs84_to_rd(np.asarray(lon), np.asarray(lat))
        return (x - x0) / res, (y1 - y) / res

    # the share of the Netherlands below NAP: land cells (country minus water areas), ground samples only
    land_rd = rasterize(nl_land, ahn.shape, rd_px) > 0.5
    water_rd = rasterize(water, ahn.shape, rd_px) > 0.5
    land_rd &= ~water_rd
    valid = land_rd & ~np.isnan(ahn)
    zz = ahn[valid]
    stats = dict(land_cells_ha=int(land_rd.sum()), ground_samples=int(valid.sum()),
                 share_below_nap=float((zz < 0).mean()), share_below_minus2=float((zz < -2).mean()),
                 share_below_plus1=float((zz < 1).mean()),
                 km2_below_nap=float((zz < 0).mean() * land_rd.sum() / 100.0), land_km2=float(land_rd.sum() / 100.0))
    # lowest and highest ground on a 300 m smoothed surface (single samples are noisy)
    sm = ndimage.uniform_filter(np.nan_to_num(fill_gaps(ahn), nan=0), 3)
    sm_masked = np.where(valid, sm, np.nan)
    r, c = np.unravel_index(np.nanargmin(sm_masked), sm.shape)
    lo = F.rd_to_wgs84(x0 + (c + 0.5) * res, y1 - (r + 0.5) * res)
    stats["lowest"] = dict(m=float(ahn[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2][~np.isnan(ahn[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2])].min()),
                           lon=lo[0], lat=lo[1])
    r, c = np.unravel_index(np.nanargmax(np.where(valid, ahn, np.nan)), sm.shape)
    hi = F.rd_to_wgs84(x0 + (c + 0.5) * res, y1 - (r + 0.5) * res)
    stats["highest"] = dict(m=float(ahn[r, c]), lon=hi[0], lat=hi[1])
    print("  stats", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in stats.items()})

    # AHN on the map grid: gaps (water, buildings) filled, lightly smoothed, then sampled bilinearly
    ahn_f = ndimage.gaussian_filter(fill_gaps(ahn), 1.0)
    lon, lat = grid_lonlat()
    c, r = rd_px(lon, lat)
    inside = (c >= 0) & (c <= nx - 1) & (r >= 0) & (r <= ny - 1) & ~np.isnan(ahn_f[np.clip(r.astype(int), 0, ny - 1), np.clip(c.astype(int), 0, nx - 1)])
    za = ndimage.map_coordinates(np.nan_to_num(ahn_f, nan=0), [r - 0.5 + 0.5, c - 0.5 + 0.5], order=1, mode="nearest")
    # terrarium outside the Netherlands, on the same Mercator grid
    tz, ext = F.terrarium()
    tz = ndimage.gaussian_filter(tz, 0.8)
    n_ = 2 ** F.TERRA_Z * 256
    gx = (lon + 180) / 360 * n_
    gy = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * n_
    tx0, ty0 = F.tile_xy(ext[0], ext[3], F.TERRA_Z)
    zt = ndimage.map_coordinates(tz, [gy - ty0 * 256 - 0.5, gx - tx0 * 256 - 0.5], order=1, mode="nearest")
    # blend: AHN inside the Netherlands (and its coverage), terrarium elsewhere, feathered over about 1.5 km
    to_grid = lambda lo_, la_: ((lo_ - GRID["x0"]) / GRID["step"], (GRID["y1"] - merc_y(la_)) / GRID["step"])
    nl_mask = rasterize(nl_land.buffer(0.01), lon.shape, to_grid) > 0.5
    wgt = ndimage.gaussian_filter((nl_mask & inside).astype(np.float32), 5) * inside
    z = wgt * za + (1 - wgt) * zt
    land_g = rasterize(land.buffer(0.01), lon.shape, to_grid) > 0.5       # the sea carries no height on this map
    q = np.clip(np.round((z + ELEV_OFFSET) * ELEV_SCALE), 1, 65535).astype(np.uint16)
    q[~land_g] = 0
    Image.fromarray(q).save(os.path.join(OUT, "nl_elevation.png"), optimize=True)
    print(f"  nl_elevation.png {q.shape}, {os.path.getsize(os.path.join(OUT, 'nl_elevation.png')) / 1e6:.2f} MB")
    return stats


# ---- inset: Natural Earth
def read_shp(zpath, keep=None):
    import shapefile                                   # pyshp
    z = zipfile.ZipFile(zpath)
    base = [n[:-4] for n in z.namelist() if n.endswith(".shp")][0]
    r = shapefile.Reader(shp=io_(z, base + ".shp"), dbf=io_(z, base + ".dbf"), shx=io_(z, base + ".shx"), encoding="utf-8")
    fields = [f[0] for f in r.fields[1:]]
    for sr in r.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        if keep and not keep(rec): continue
        yield shape(sr.shape.__geo_interface__), rec


def io_(z, name):
    import io
    return io.BytesIO(z.read(name))


INSET = box(1.0, 45.6, 12.6, 54.4)


def inset():
    feats = []
    for nm in ("rivers_lake_centerlines", "rivers_europe"):
        for g, rec in read_shp(F.natural_earth(nm, "physical")):
            if not g.intersects(INSET): continue
            name = rec.get("name") or rec.get("name_en") or ""
            g = g.intersection(INSET)
            feats.append((g.simplify(0.01), dict(layer="river", name=name, scalerank=rec.get("scalerank", 9))))
    for g, rec in read_shp(F.natural_earth("lakes", "physical")):
        if g.intersects(INSET) and (rec.get("scalerank", 9) or 9) <= 6:
            feats.append((g.intersection(INSET).simplify(0.01), dict(layer="lake", name=rec.get("name") or "")))
    for g, rec in read_shp(F.natural_earth("admin_0_countries", "cultural")):
        if g.intersects(INSET):
            feats.append((g.intersection(INSET).simplify(0.01), dict(layer="country", name=rec.get("NAME", ""), iso=rec.get("ISO_A2_EH", rec.get("ISO_A2", "")))))
    return feats


def run():
    print("land")
    land = land_polygons()
    nl = nl_country()
    nl_land = land.intersection(nl)
    other = land.difference(nl)
    write_fc("nl_land.geojson", [(nl_land.simplify(0.0001), dict(country="nl")), (other.simplify(0.0001), dict(country="other"))])
    print("water")
    water, named = water_areas()
    write_fc("nl_water.geojson", water)
    print("rivers")
    write_fc("nl_rivers.geojson", rivers(nl))
    print("borders")
    write_fc("nl_borders.geojson", borders())
    pl = places()
    json.dump(pl, open(os.path.join(OUT, "nl_places.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("elevation")
    wat = unary_union([g for g, p in water])
    stats = elevation(nl_land, wat, land)
    stats["water_names"] = named
    print("inset")
    write_fc("nl_inset.geojson", inset())
    json.dump(stats, open(os.path.join(OUT, "nl_stats.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
