"""make_world.py: compact world outlines for the web map, from Natural Earth.

    python tools/make_world.py

Reads data/ne_110m_admin_0_countries.geojson (Natural Earth v5.1.2, public domain), drops Antarctica, keeps for each
country its ADM0_A3 and ISO_A3 codes (ISO_A3 is "-99" in Natural Earth for France, Norway and a few others; their
ISO_A3_EH code is used instead, and where that is "-99" too the field stays "-99"), its name and its continent, rounds
every coordinate to 0.01 degree, drops points that repeat after rounding, and writes docs/data/world-110m.json:

    {"source": ..., "features": [{"a3", "iso", "name", "continent", "rings": [[[lon, lat], ...], ...]}, ...]}

`rings` holds every ring of every polygon of the country; drawn with the even-odd rule, holes stay holes.
"""
import json, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO, "data", "ne_110m_admin_0_countries.geojson")
OUT = os.path.join(REPO, "docs", "data", "world-110m.json")


def ring(coords):
    out = []
    for lon, lat in coords:
        p = [round(lon, 2), round(lat, 2)]
        if not out or p != out[-1]: out.append(p)
    return out if len(out) >= 4 else None


def main():
    src = json.load(open(SRC, encoding="utf-8"))
    feats = []
    for f in src["features"]:
        p, geom = f["properties"], f["geometry"]
        if p["ADM0_A3"] == "ATA": continue
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        rings = [r for poly in polys for r in (ring(c) for c in poly) if r]
        iso = p["ISO_A3"] if p["ISO_A3"] != "-99" else p["ISO_A3_EH"]
        feats.append(dict(a3=p["ADM0_A3"], iso=iso, name=p["NAME"], continent=p["CONTINENT"], rings=rings))
    out = dict(source="Natural Earth v5.1.2, admin 0 countries at 1:110 million; Antarctica dropped; coordinates "
                      "rounded to 0.01 degree by tools/make_world.py", features=feats)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT}: {len(feats)} countries, {sum(len(r) for f in feats for r in f['rings'])} points, "
          f"{os.path.getsize(OUT) / 1024:.0f} kB")


if __name__ == "__main__":
    main()
