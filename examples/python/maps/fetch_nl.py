"""fetch_nl.py: download, clip, simplify and cache the open data behind netherlands_rivers.py.

Run once (about ten minutes, most of it Overpass and the AHN coverage service); it writes small processed files into
data/maps/ and keeps the raw downloads in a cache folder outside the repository (VELLUM_MAP_CACHE, default
%TEMP%/vellum-maps-cache), so a second run only reprocesses.

    python examples/python/maps/fetch_nl.py            # everything
    python examples/python/maps/fetch_nl.py process    # reprocess from the cache only

Sources (see data/maps/SOURCES.md):
  OpenStreetMap via the Overpass API (ODbL, (c) OpenStreetMap contributors): coastline, rivers, canals, water areas,
      the land borders of the Netherlands, places.
  AHN4 DTM 0.5 m, Rijkswaterstaat / Het Waterschapshuis, via the PDOK WCS (CC0), point-sampled on a 100 m grid.
  AWS Terrain Tiles (terrarium encoding; SRTM, GMTED, ETOPO1 and others; Mapzen / Amazon open data), zoom 10,
      for the ground outside the Netherlands.
  Natural Earth 10 m rivers and lakes and admin-0 countries (public domain), for the Rhine-Meuse inset.

Projection: everything is stored in lon / lat (EPSG:4326). The elevation grid is stored on the map's own Mercator grid.
"""
import json, math, os, sys, tempfile, time, urllib.parse, urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "data", "maps")
CACHE = os.environ.get("VELLUM_MAP_CACHE", os.path.join(tempfile.gettempdir(), "vellum-maps-cache"))
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
sys.path.insert(0, HERE)
from nl_geo import FRAME, BBOX, merc_y, merc_lat, GRID   # noqa: E402  (the map frame, shared with the drawing script)

UA = {"User-Agent": "vellum-figure-style/1.0 (https://github.com/akaminas/vellum; one-off map download)"}
OVERPASS = os.environ.get("VELLUM_OVERPASS", "https://overpass-api.de/api/interpreter,https://maps.mail.ru/osm/tools/overpass/api/interpreter").split(",")
S, W, N, E = BBOX
QUERIES = {   # {B} is the bounding box; the heavy queries run in TILES x TILES pieces, merged by element id
    "coastline": 'way["natural"="coastline"]{B};out geom;',
    "rivers": 'way["waterway"="river"]{B};out tags geom;',
    "canals": 'way["waterway"="canal"]{B};out tags geom;',
    "water_rel": 'rel["natural"="water"]{B};out geom;',
    "water_way": 'way["natural"="water"]["water"~"^(lake|river|reservoir|lagoon|oxbow|canal|basin)$"]{B};out tags geom;',
    "water_way_named": 'way["natural"="water"][!"water"]["name"]{B};out tags geom;',
    "borders": 'way["boundary"="administrative"]["admin_level"="2"]{B};out tags geom;',
    "nl_relation": 'rel(47796);out geom;',
    "places": 'node["place"~"^(city|town)$"]{B};out;',
}
TILES = {"rivers": 3, "canals": 2, "water_rel": 3, "water_way": 3, "water_way_named": 2, "borders": 2}


def get(url, data=None, tries=4, timeout=600):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:                       # busy servers answer 429 / 504; wait and try again
            print(f"  retry {k + 1} after {e}", flush=True)
            time.sleep(20 * (k + 1))
    raise RuntimeError(f"could not fetch {url}")


def curl_post(url, q, timeout=400):
    """POST an Overpass query with curl (the public instances turned urllib requests away with 504s here)."""
    import subprocess
    r = subprocess.run(["curl", "-s", "-f", "-m", str(timeout), "-A", "vellum-map/1.0", url, "--data-urlencode", f"data={q}"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl exit {r.returncode}")
    return r.stdout


def overpass_one(q, path, label):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    q = f"[out:json][timeout:300];{q}"
    for k in range(10):
        ep = OVERPASS[k % len(OVERPASS)]
        print(f"overpass {label} via {ep}", flush=True)
        try:
            raw = curl_post(ep, q, timeout=330)
            js = json.loads(raw)
            if "remark" in js and "error" in js["remark"].lower():
                raise RuntimeError(js["remark"])
            open(path, "wb").write(raw)
            return js
        except Exception as e:
            print(f"  failed: {str(e)[:200]}", flush=True)
            time.sleep(30 + 15 * k)
    raise RuntimeError(f"overpass {label} failed")


def overpass(name):
    n = TILES.get(name, 1)
    if n == 1:
        return overpass_one(QUERIES[name].format(B=f"({S},{W},{N},{E})"), os.path.join(CACHE, f"osm_{name}.json"), name)
    seen, els = set(), []
    for i in range(n):
        for j in range(n):
            s0, s1 = S + (N - S) * j / n, S + (N - S) * (j + 1) / n
            w0, w1 = W + (E - W) * i / n, W + (E - W) * (i + 1) / n
            b = f"({s0:.4f},{w0:.4f},{s1:.4f},{w1:.4f})"
            js = overpass_one(QUERIES[name].format(B=b), os.path.join(CACHE, f"osm_{name}_{i}{j}.json"), f"{name} {i}{j}")
            for e in js["elements"]:
                key = (e["type"], e["id"])
                if key not in seen:
                    seen.add(key); els.append(e)
    return {"elements": els}


# ---- AHN: the PDOK WCS, point-sampled on a 100 m grid in RD New, in tiles of 50 km
AHN_URL = ("https://service.pdok.nl/rws/ahn/wcs/v1_0?SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCoverage&COVERAGE=dtm_05m"
           "&CRS=EPSG:28992&BBOX={x0},{y0},{x1},{y1}&WIDTH={w}&HEIGHT={h}&FORMAT=GEOTIFF&INTERPOLATION=nearest%20neighbor")
AHN_RES, AHN_TILE = 100, 50000
AHN_X, AHN_Y = (0, 300000), (300000, 650000)       # RD New extent of the AHN coverage, rounded out


def ahn():
    path = os.path.join(CACHE, "ahn_100m.npy")
    if os.path.exists(path):
        return np.load(path)
    nx, ny = (AHN_X[1] - AHN_X[0]) // AHN_RES, (AHN_Y[1] - AHN_Y[0]) // AHN_RES
    z = np.full((ny, nx), np.nan, np.float32)        # row 0 is the north edge
    t = AHN_TILE // AHN_RES
    for x0 in range(AHN_X[0], AHN_X[1], AHN_TILE):
        for y0 in range(AHN_Y[0], AHN_Y[1], AHN_TILE):
            tp = os.path.join(CACHE, f"ahn_{x0}_{y0}.tif")
            if not os.path.exists(tp):
                url = AHN_URL.format(x0=x0, y0=y0, x1=x0 + AHN_TILE, y1=y0 + AHN_TILE, w=t, h=t)
                print("ahn", x0, y0, flush=True)
                open(tp, "wb").write(get(url, timeout=300))
            a = np.array(Image.open(tp), np.float32)
            a[(a > 1e30) | (a < -100)] = np.nan
            r0 = (AHN_Y[1] - (y0 + AHN_TILE)) // AHN_RES; c0 = (x0 - AHN_X[0]) // AHN_RES
            z[r0:r0 + t, c0:c0 + t] = a
    np.save(path, z)
    return z


def rd_to_wgs84(x, y):
    """RD New (EPSG:28992) to WGS84 lon, lat by the Schreutelkamp and Strang van Hees (2001) series; about 1 m."""
    dx, dy = (x - 155000.0) * 1e-5, (y - 463000.0) * 1e-5
    K = [(0, 1, 3235.65389), (2, 0, -32.58297), (0, 2, -0.24750), (2, 1, -0.84978), (0, 3, -0.06550),
         (2, 2, -0.01709), (1, 0, -0.00738), (4, 0, 0.00530), (2, 3, -0.00039), (4, 1, 0.00033), (1, 1, -0.00012)]
    L = [(1, 0, 5260.52916), (1, 1, 105.94684), (1, 2, 2.45656), (3, 0, -0.81885), (1, 3, 0.05594),
         (3, 1, -0.05607), (0, 1, 0.01199), (3, 2, -0.00256), (1, 4, 0.00128), (0, 2, 0.00022), (2, 0, -0.00022),
         (5, 0, 0.00026)]
    lat = 52.15517440 + sum(c * dx ** p * dy ** q for p, q, c in K) / 3600.0
    lon = 5.38720621 + sum(c * dx ** p * dy ** q for p, q, c in L) / 3600.0
    return lon, lat


def wgs84_to_rd(lon, lat):
    """The inverse series (same source)."""
    dphi, dlam = 0.36 * (lat - 52.15517440), 0.36 * (lon - 5.38720621)
    R = [(0, 1, 190094.945), (1, 1, -11832.228), (2, 1, -114.221), (0, 3, -32.391), (1, 0, -0.705),
         (3, 1, -2.340), (1, 3, -0.608), (0, 2, -0.008), (2, 3, 0.148)]
    S_ = [(1, 0, 309056.544), (0, 2, 3638.893), (2, 0, 73.077), (1, 2, -157.984), (3, 0, 59.788), (0, 1, 0.433),
          (2, 2, -6.439), (1, 1, -0.032), (0, 4, 0.092), (1, 4, -0.054)]
    x = 155000.0 + sum(c * dphi ** p * dlam ** q for p, q, c in R)
    y = 463000.0 + sum(c * dphi ** p * dlam ** q for p, q, c in S_)
    return x, y


# ---- AWS Terrain Tiles, terrarium encoding: metres = R * 256 + G + B / 256 - 32768
TERRA_Z = 10


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def terrarium():
    path = os.path.join(CACHE, f"terrarium_z{TERRA_Z}.npz")
    if os.path.exists(path):
        d = np.load(path); return d["z"], tuple(d["ext"])
    z = TERRA_Z
    x0, y0 = tile_xy(W, N, z); x1, y1 = tile_xy(E, S, z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    out = np.zeros((256 * len(ys), 256 * len(xs)), np.float32)
    for j, ty in enumerate(ys):
        for i, tx in enumerate(xs):
            tp = os.path.join(CACHE, f"terrarium_{z}_{tx}_{ty}.png")
            if not os.path.exists(tp):
                open(tp, "wb").write(get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png"))
            a = np.array(Image.open(tp).convert("RGB"), np.float32)
            out[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    n = 2 ** z
    lon0, lon1 = xs[0] / n * 360 - 180, (xs[-1] + 1) / n * 360 - 180
    lat_of = lambda ty: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    ext = (lon0, lon1, lat_of(ys[-1] + 1), lat_of(ys[0]))          # west, east, south, north
    np.savez_compressed(path, z=out, ext=np.array(ext))
    return out, ext


def natural_earth(name, kind):
    path = os.path.join(CACHE, f"ne_10m_{name}.zip")
    if not os.path.exists(path):
        open(path, "wb").write(get(f"https://naciscdn.org/naturalearth/10m/{kind}/ne_10m_{name}.zip"))
    return path


def download():
    for name in QUERIES:
        overpass(name)
    terrarium()
    ahn()
    natural_earth("rivers_lake_centerlines", "physical"); natural_earth("rivers_europe", "physical")
    natural_earth("lakes", "physical"); natural_earth("admin_0_countries", "cultural")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "process":
        download()
    import nl_process
    nl_process.run()
