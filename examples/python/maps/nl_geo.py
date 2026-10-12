"""nl_geo.py: the map frame and the Mercator projection shared by fetch_nl.py, nl_process.py and netherlands_rivers.py.

Coordinates on the map are (lon, y) with y = Mercator northing in degrees, so one unit of x and one unit of y are the
same length on paper and the graticule is straight. The frame is the 44 x 54 cm map field of a 50 x 60 cm print with a
3 cm margin.
"""
import math
import numpy as np

PAPER_CM = (50.0, 60.0)
MARGIN_CM = 3.0
FIELD_CM = (PAPER_CM[0] - 2 * MARGIN_CM, PAPER_CM[1] - 2 * MARGIN_CM)


def merc_y(lat):
    """Mercator northing in degrees."""
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


def merc_lat(y):
    return np.degrees(2 * np.arctan(np.exp(np.radians(y))) - np.pi / 2)


LON0, LON1, LAT1 = 2.55, 7.45, 53.95
_Y1 = float(merc_y(LAT1))
_Y0 = _Y1 - (LON1 - LON0) * FIELD_CM[1] / FIELD_CM[0]
FRAME = (LON0, LON1, _Y0, _Y1)                   # x0, x1, y0, y1 in map units
LAT0 = float(merc_lat(_Y0))
BBOX = (round(LAT0 - 0.15, 2), round(LON0 - 0.15, 2), round(LAT1 + 0.15, 2), round(LON1 + 0.15, 2))   # south, west, north, east for downloads

# the elevation grid is stored as 16-bit PNG: metres = value / ELEV_SCALE - ELEV_OFFSET; 0 marks the sea
ELEV_SCALE, ELEV_OFFSET = 10.0, 100.0

# the elevation grid, on the map's own Mercator grid: cell size in map units and the grid shape
GRID_STEP = 0.002
GRID = dict(x0=LON0, y1=_Y1, step=GRID_STEP, nx=int(round((LON1 - LON0) / GRID_STEP)),
            ny=int(round((_Y1 - _Y0) / GRID_STEP)))


def grid_lonlat():
    """lon, lat of the cell centres of GRID, row 0 at the north edge."""
    xs = GRID["x0"] + (np.arange(GRID["nx"]) + 0.5) * GRID["step"]
    ys = GRID["y1"] - (np.arange(GRID["ny"]) + 0.5) * GRID["step"]
    return np.meshgrid(xs, merc_lat(ys))


def scale_denominator(lat=52.0):
    """Paper scale 1 : n at latitude lat."""
    km_per_deg = 111.32 * math.cos(math.radians(lat))
    return (LON1 - LON0) * km_per_deg * 1e5 / FIELD_CM[0]
