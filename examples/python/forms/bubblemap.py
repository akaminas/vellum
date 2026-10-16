"""bubblemap.py: fossil CO2 emitted by every country in 2022 on an Equal Earth world map, one ringed bubble per country at its
centre, bubble area in proportion to the tonnes, the three largest emitters in terracotta. Data: data/ne_110m_admin_0_countries.geojson
(Natural Earth) and data/sustainability/owid-co2.csv (Global Carbon Project via Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Polygon
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "Global Carbon Project (2023) via Our World in Data; Natural Earth 1:110m countries (public domain)"
YEAR = 2022
CO2 = {r["iso_code"]: float(r["co2"]) for r in load_csv("sustainability/owid-co2.csv")
       if r["year"] == str(YEAR) and r["co2"] and r["iso_code"] and not r["iso_code"].startswith("OWID")}
TOT = sum(CO2.values())
TOP3 = sorted(CO2, key=CO2.get, reverse=True)[:3]
SHARE = sum(CO2[c] for c in TOP3) / TOT
NAME = {"CHN": "China", "USA": "United States", "IND": "India"}


def equal_earth(lon, lat):
    A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
    lam = np.radians(lon); th = np.arcsin(np.sqrt(3) / 2 * np.sin(np.radians(lat)))
    x = 2 * np.sqrt(3) * lam * np.cos(th) / (3 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1))
    y = th * (A1 + A2 * th ** 2 + th ** 6 * (A3 + A4 * th ** 2))
    return x, y


def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [np.array(p[0]) for p in polys]


def centre(rs):
    r = max(rs, key=lambda a: abs(np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])))
    x, y = r[:-1, 0], r[:-1, 1]; x1, y1 = r[1:, 0], r[1:, 1]
    a = x * y1 - x1 * y; A = a.sum() / 2
    return ((x + x1) * a).sum() / (6 * A), ((y + y1) * a).sum() / (6 * A)


FEATURES = [f for f in load_json("ne_110m_admin_0_countries.geojson")["features"] if f["properties"]["ADM0_A3"] != "ATA"]
TITLE = f"China, the United States and India emit {SHARE * 100:.0f} % of the world's fossil CO₂"
SUB = f"Fossil CO₂ from burning fuels and making cement, {YEAR}, {TOT / 1e3:.0f} billion tonnes · bubble area: tonnes emitted"
K = 560 / 1.2e4                                    # pt² per million tonnes: China's 12 billion tonnes is a 560 pt² disc


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.04)
    for f in FEATURES:
        for r in rings(f["geometry"]):
            x, y = equal_earth(r[:, 0], r[:, 1])
            ax.add_patch(Polygon(np.c_[x, y], closed=True, fc=V.grid if V.mode == "light" else V.card, ec=V.surface, lw=0.4, zorder=2))
    pts = []
    for f in FEATURES:
        iso = f["properties"]["ADM0_A3"]
        if iso not in CO2: continue
        lon, lat = centre(rings(f["geometry"])); x, y = equal_earth(np.array(lon), np.array(lat))
        pts.append((float(x), float(y), CO2[iso], iso))
    for x, y, v, iso in sorted(pts, key=lambda p: -p[2]):                 # the large first, the small on top
        ax.scatter([x], [y], s=K * v + 2, color=V.tone(1 if iso in TOP3 else 0), alpha=0.85, edgecolor=V.surface, linewidth=0.8, zorder=4)
    for x, y, v, iso in pts:
        if iso in TOP3:
            up = iso == "CHN"                                            # China's label above, clear of India's below
            ax.annotate(f"{NAME[iso]}\n{v / 1e3:.1f} billion t", (x, y), xytext=(0, (1 if up else -1) * (np.sqrt(K * v / np.pi) + 4)),
                        textcoords="offset points", ha="center", va="bottom" if up else "top", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.1,
                        path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)], zorder=6)
    for i, (v, lab) in enumerate(((1000, "1 billion t"), (5000, "5 billion t"))):                   # the key, in the southern Pacific
        kx, ky = -2.35 + 0.62 * i, -0.62
        ax.scatter([kx], [ky], s=K * v, facecolor="none", edgecolor=V.muted, linewidth=0.8, zorder=4)
        ax.annotate(lab, (kx, ky), xytext=(0, -np.sqrt(K * v / np.pi) - 3), textcoords="offset points", ha="center", va="top",
                    fontsize=V.sz["unit_line"], color=V.muted)
    ax.set_aspect("equal"); ax.set_xlim(-2.9, 2.9); ax.set_ylim(-1.0, 1.4); ax.axis("off")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", also=["map"], form="bubble map", medium="screen", tool="matplotlib",
            data=f"Fossil CO2 by country, {YEAR}, Global Carbon Project via Our World in Data; Natural Earth 110m", script=rel(__file__),
            alt=(f"Equal Earth world map with a bubble per country sized by fossil CO2 emitted in {YEAR}. China, the United States and "
                 f"India, in terracotta, are {SHARE * 100:.0f} % of the world total of {TOT / 1e3:.0f} billion tonnes."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "bubblemap", mode, meta=META)
