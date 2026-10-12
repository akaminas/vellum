# Map data

The files in this folder are built by `examples/python/maps/fetch_nl.py` (downloads, cached outside the repository)
and `examples/python/maps/nl_process.py` (clipping, merging, simplifying), and drawn by
`examples/python/maps/netherlands_rivers.py`. Downloaded on 2026-10-12. Coordinates are WGS84 longitude and latitude,
except `nl_elevation.png`, which is on the map's own Mercator grid (`nl_geo.GRID`).

| file | what it is | source | licence |
|---|---|---|---|
| `nl_land.geojson` | Land polygons built from the OSM coastline (land lies left of a coastline way), split into the Netherlands (OSM relation 47796) and the rest; simplified to about 10 m | OpenStreetMap contributors, via the Overpass API | ODbL 1.0, © OpenStreetMap contributors |
| `nl_water.geojson` | Lakes (0.15 km² and larger) and the water area of rivers and canals (0.02 km² and larger) from `natural=water`; merged and simplified to about 15 m | OpenStreetMap contributors, via the Overpass API | ODbL 1.0, © OpenStreetMap contributors |
| `nl_rivers.geojson` | `waterway=river` and navigable or named `waterway=canal` lines, merged by name, simplified to about 8 m, with a rank (1 the Rhine–Maas–Schelde branches, 2 rivers of 25 km and more and canals of CEMT class IV and up, 3 the rest) and the share of each line inside the Netherlands | OpenStreetMap contributors, via the Overpass API | ODbL 1.0, © OpenStreetMap contributors |
| `nl_borders.geojson` | Land borders (`boundary=administrative`, `admin_level=2`, maritime parts dropped) | OpenStreetMap contributors, via the Overpass API | ODbL 1.0, © OpenStreetMap contributors |
| `nl_places.json` | Cities and towns (`place=city|town`) with name and population | OpenStreetMap contributors, via the Overpass API | ODbL 1.0, © OpenStreetMap contributors |
| `nl_elevation.png` | Ground height on the map's Mercator grid (0.002° of longitude, about 140 m), 16-bit: metres = value / 10 − 100 (10 cm steps); 0 marks the sea. Inside the Netherlands: AHN4 DTM 0.5 m, point-sampled every 100 m in RD New, gaps (water, buildings) filled, lightly smoothed. Outside: AWS Terrain Tiles, terrarium encoding, zoom 10. The two are feathered over about 1.5 km at the border | AHN4, Rijkswaterstaat and Het Waterschapshuis, via the PDOK WCS `service.pdok.nl/rws/ahn/wcs/v1_0`; AWS Terrain Tiles (Mapzen / Tilezen joerd; SRTM, GMTED2010, ETOPO1 and others) on the Registry of Open Data on AWS | AHN: CC0 1.0. Terrain Tiles: open, with attribution to the underlying sources (see tilezen/joerd attribution) |
| `nl_stats.json` | The numbers the map quotes: share and area of Dutch land below NAP, lowest and highest ground, all from the AHN4 100 m sample of land cells (country minus water areas) | computed by `nl_process.py` | as AHN4 (CC0) and OSM (ODbL) |
| `nl_inset.geojson` | Rivers, lakes and countries of the Rhine and Maas basins for the map-in-map | Natural Earth 10 m `rivers_lake_centerlines`, `rivers_europe`, `lakes`, `admin_0_countries`, v5 | public domain |

The share below sea level counts AHN4 ground samples on a 100 m grid over Dutch land (OSM coastline and national
border, minus lakes and wide rivers). AHN4 has no ground value under buildings and water, so those samples are left
out; each 100 m cell is one hectare, so counts are areas. NAP (Normaal Amsterdams Peil) is the Dutch vertical datum,
close to mean sea level.
