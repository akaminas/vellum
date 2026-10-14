"""fetch_calanques.py: download and merge the open data behind calanques.py.

Run once (a minute or two); it writes small processed files into data/maps/ and keeps the raw downloads in a cache
folder outside the repository (VELLUM_MAP_CACHE, default %TEMP%/vellum-maps-cache), so a second run only reprocesses.

    python examples/python/maps/fetch_calanques.py

Sources (see data/maps/SOURCES.md):
  IGN RGE ALTI (1 m to 5 m terrain model), via the Géoplateforme raster WMS as 32-bit floats (Licence Ouverte 2.0),
      for the ground above the sea.
  EMODnet Bathymetry DTM, via its WCS (CC BY 4.0), for the sea floor.
  Vacchi et al. (2021), sea-level index points of the central and western Mediterranean, Zenodo (CC BY 4.0).

The terrain is stored on a Lambert-93 grid (EPSG:2154), 25 m cells, as a 16-bit PNG: metres = value / 10 - 1000.
"""
import json, os, shutil, sys, tempfile, time, urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "data", "maps")
CACHE = os.environ.get("VELLUM_MAP_CACHE", os.path.join(tempfile.gettempdir(), "vellum-maps-cache"))
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "vellum-figure-style/1.0 (https://github.com/akaminas/vellum; one-off map download)"}

# the grid: Lambert-93, from the south of Marseille to Cassis and out over the shelf
X0, X1, Y0, Y1, STEP = 884000, 910000, 6228000, 6250000, 25
NX, NY = (X1 - X0) // STEP, (Y1 - Y0) // STEP
SCALE, OFFSET = 10.0, 1000.0

IGN = ("https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"
       "&STYLES=&CRS=EPSG:2154&BBOX={x0},{y0},{x1},{y1}&WIDTH={w}&HEIGHT={h}&FORMAT=image/x-bil;bits=32")
EMOD = ("https://ows.emodnet-bathymetry.eu/wcs?service=WCS&version=2.0.1&request=GetCoverage&coverageId=emodnet__mean"
        "&format=image/tiff&subset=Lat({s},{n})&subset=Long({w},{e})")
SLIPS = "https://zenodo.org/api/records/4737120/files/SLIPs_Vacchi_et_al_2021.csv/content"


def get(url, path, tries=4):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
                shutil.copyfileobj(r, f)
            return path
        except Exception as e:                       # busy servers: wait and try again
            print(f"  retry {k + 1} after {e}", flush=True)
            time.sleep(10 * (k + 1))
    raise RuntimeError(f"could not fetch {url}")


def ign():
    """Ground height on the grid, in tiles of at most 520 x 440 cells; 0 over the sea."""
    z = np.zeros((NY, NX), np.float32)
    tx, ty = 2, 2
    for i in range(ty):
        for j in range(tx):
            c0, c1 = j * NX // tx, (j + 1) * NX // tx
            r0, r1 = i * NY // ty, (i + 1) * NY // ty                 # rows from the north edge
            x0, x1 = X0 + c0 * STEP, X0 + c1 * STEP
            y1, y0 = Y1 - r0 * STEP, Y1 - r1 * STEP
            path = os.path.join(CACHE, f"calanques_ign_{x0}_{y0}_{x1}_{y1}.bil")
            get(IGN.format(x0=x0, y0=y0, x1=x1, y1=y1, w=c1 - c0, h=r1 - r0), path)
            z[r0:r1, c0:c1] = np.fromfile(path, "<f4").reshape(r1 - r0, c1 - c0)
            print(f"  IGN tile {i},{j}", flush=True)
    return z


def emodnet():
    """The sea floor, bilinearly resampled from EMODnet's 1/16 arc-minute grid onto the Lambert-93 grid."""
    from pyproj import Transformer
    s, n, w, e = 43.08, 43.38, 5.20, 5.70
    path = os.path.join(CACHE, "calanques_emodnet.tif")
    get(EMOD.format(s=s, n=n, w=w, e=e), path)
    a = np.array(Image.open(path), np.float64)                        # rows from the north
    ny, nx = a.shape
    lon_c = w + (np.arange(nx) + 0.5) * (e - w) / nx
    lat_c = n - (np.arange(ny) + 0.5) * (n - s) / ny
    xs = X0 + (np.arange(NX) + 0.5) * STEP
    ys = Y1 - (np.arange(NY) + 0.5) * STEP
    gx, gy = np.meshgrid(xs, ys)
    lon, lat = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True).transform(gx, gy)
    fi = (lon - lon_c[0]) / (lon_c[1] - lon_c[0])
    fj = (lat - lat_c[0]) / (lat_c[1] - lat_c[0])
    i0 = np.clip(np.floor(fi).astype(int), 0, nx - 2); j0 = np.clip(np.floor(fj).astype(int), 0, ny - 2)
    ti = np.clip(fi - i0, 0, 1); tj = np.clip(fj - j0, 0, 1)
    v = (a[j0, i0] * (1 - ti) * (1 - tj) + a[j0, i0 + 1] * ti * (1 - tj)
         + a[j0 + 1, i0] * (1 - ti) * tj + a[j0 + 1, i0 + 1] * ti * tj)
    return v.astype(np.float32)


def merge(land, sea):
    """IGN where it has ground (above 0), EMODnet elsewhere; sea cells EMODnet places above water (its coarser coast)
    are set just below the surface, so the coastline is IGN's."""
    z = np.where(land > 0.0, land, np.minimum(sea, -0.5))
    return z


def main():
    print("IGN RGE ALTI"); land = ign()
    print("EMODnet"); sea = emodnet()
    z = merge(land, sea)
    v = np.clip(np.round((z + OFFSET) * SCALE), 0, 65535).astype(np.uint16)
    Image.fromarray(v).save(os.path.join(OUT, "calanques_terrain.png"))
    meta = dict(crs="EPSG:2154", x0=X0, x1=X1, y0=Y0, y1=Y1, step=STEP, nx=NX, ny=NY, scale=SCALE, offset=OFFSET,
                rows="north to south", decode="metres = value / scale - offset",
                land_cells=int((land > 0).sum()), min=float(z.min()), max=float(z.max()))
    json.dump(meta, open(os.path.join(OUT, "calanques_terrain.json"), "w"), indent=1)
    print("Zenodo"); get(SLIPS, os.path.join(CACHE, "SLIPs_Vacchi_et_al_2021.csv"))
    shutil.copy(os.path.join(CACHE, "SLIPs_Vacchi_et_al_2021.csv"), os.path.join(OUT, "med_slips_vacchi2021.csv"))
    print(f"terrain {NX} x {NY}, {z.min():.0f} to {z.max():.0f} m; land cells {meta['land_cells']}")


if __name__ == "__main__":
    main()
