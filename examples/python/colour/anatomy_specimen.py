"""anatomy_specimen.py: an annotated specimen of a Vellum line figure, its eleven parts numbered in the margin.

The specimen is a real figure: period life expectancy of four continents, 1950-2023 (Our World in Data), with a band for
the middle half of Asian countries (countries placed on continents by Natural Earth), a dotted ochre reference line at the
world's 1950 level, end labels (pushed apart with a leader where they would collide) and a quiet note. Numbered callouts
in the secondary colour with 0.5 pt muted leaders point at each part from the margin; the key (number, part, rule) is
written into the manifest under "parts" for the site to print beside the image.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Circle
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: UN WPP (2024) and others, processed by Our World in Data (CC BY 4.0); continents: Natural Earth"
W, H = 7.2, 4.6
SZ, MK = vellum.SPEC["sizes"], vellum.SPEC["marks"]
REGIONS = ("Asia", "Africa", "Americas", "Europe")            # slot order: teal, terracotta, indigo, ochre
ROWS = load_csv("owid-life-expectancy.csv")
series = lambda e: np.array(sorted((int(r["Year"]), float(r["Life expectancy"])) for r in ROWS if r["Entity"] == e and int(r["Year"]) >= 1950))
SERIES = {r: series(r) for r in REGIONS}
WORLD_1950 = float(series("World")[0, 1])
GAIN = {r: float(s[-1, 1] - s[0, 1]) for r, s in SERIES.items()}
TOP = max(GAIN, key=GAIN.get); assert TOP == "Asia"
TITLE = f"Asia gained {GAIN['Asia']:.0f} years of life expectancy since 1950, the most of any continent"


def asia_band():
    """25th and 75th percentile, per year, of the countries Natural Earth places in Asia."""
    cont = {}
    for f in load_json("ne_110m_admin_0_countries.geojson")["features"]:
        p = f["properties"]
        for k in ("ISO_A3_EH", "ISO_A3", "ADM0_A3"):
            if p[k] and p[k] != "-99": cont.setdefault(p[k], p["CONTINENT"])
    years = SERIES["Asia"][:, 0].astype(int); by = {y: [] for y in years}
    for r in ROWS:
        if cont.get(r["Code"]) == "Asia" and int(r["Year"]) in by: by[int(r["Year"])].append(float(r["Life expectancy"]))
    q = np.array([np.percentile(by[y], [25, 75]) for y in years])
    return years, q[:, 0], q[:, 1], len({r["Code"] for r in ROWS if cont.get(r["Code"]) == "Asia"})


YEARS, LO, HI, N_ASIA = asia_band()

PARTS = [
    f"1 · claim title · a sentence with a verb, Palatino {SZ['title']:g} pt in ink, top left",
    f"2 · subtitle · what, where, when, Corbel {SZ['subtitle']:g} pt in muted, one title height below the claim",
    f"3 · unit line · the quantity and unit above the y axis, {SZ['unit_line']:g} pt muted, never a rotated label",
    f"4 · hairline grid · horizontal only, {MK['grid_pt']:g} pt in the grid colour, behind the data",
    "5 · bottom spine · 0.8 pt in the grid colour; no top, left or right spine and no tick marks",
    f"6 · ringed end dot · {MK['marker_pt2']:g} pt² in the tone with a {MK['ring_pt']:g} pt ring in the surface colour",
    f"7 · direct end label · {SZ['annotation']:g} pt in ink beside the dot; pushed apart with a 0.5 pt muted leader when labels collide",
    f"8 · band · the tint at {MK['band_alpha']:g} opacity, no edge, explained by a quiet note",
    f"9 · reference line · {MK['thin_line_pt']:g} pt dotted ({MK['dotted'][0]:g} on {MK['dotted'][1]:g} off) in ochre, labelled at its right end in muted",
    f"10 · quiet note · {SZ['annotation']:g} pt muted, inside the plot where the data are not",
    f"11 · footer · source, script and git stamp, {SZ['footer']:g} pt muted, bottom left",
]


def draw(V):
    fig = plt.figure(figsize=(W, H))
    cv = fig.add_axes([0, 0, 1, 1]); cv.set_xlim(0, W); cv.set_ylim(H, 0); cv.axis("off"); cv.set_zorder(5)   # the margin canvas
    to_cv = lambda ax, p: cv.transData.inverted().transform(ax.transData.transform(p))
    X0 = 0.75                                                                                 # left edge of the specimen
    # the specimen: title block, plot, end labels, footer
    fig.text(X0 / W, 1 - 0.1 / H, TITLE, fontsize=V.sz["title"], fontfamily=V.title_font, color=V.ink, va="top")
    y_sub = 0.1 + (V.sz["title"] / 72) * 1.45
    fig.text(X0 / W, 1 - y_sub / H, "Period life expectancy at birth, four continents, 1950–2023", fontsize=V.sz["subtitle"],
             color=V.muted, va="top")
    fig.text(X0 / W, 0.12 / H, footer(SOURCE, __file__), fontsize=V.sz["footer"], color=V.muted, va="bottom")
    ax = fig.add_axes([1.12 / W, 1 - 3.85 / H, 4.4 / W, 2.75 / H])
    ax.fill_between(YEARS, LO, HI, color=V.tint(0), alpha=V.band_alpha, lw=0)
    V.reference(ax, y=WORLD_1950, text=f"the world in 1950, {WORLD_1950:.0f} years")
    ends = []
    for k, r in enumerate(REGIONS):
        s = SERIES[r]; ax.plot(s[:, 0], s[:, 1], color=V.tone(k)); V.dot(ax, s[-1, 0], s[-1, 1], V.tone(k)); ends.append(s[-1])
    ax.set_xlim(1950, 2023.6); ax.set_ylim(30, 85); ax.set_yticks([40, 60, 80]); ax.set_xticks([1960, 1980, 2000, 2020])
    V.panel(ax, unit="life expectancy at birth, years")
    V.note(ax, 1951.5, 83.5, f"band: middle half of the {N_ASIA} Asian countries")
    # end labels: pushed upward from the lowest only as far as they must be; a leader only on a label that moved
    gap = (SZ["annotation"] * 1.35 / 72) / (2.75 / 55)
    order = np.argsort([e[1] for e in ends]); placed = {}; prev = -np.inf
    for i in order:
        placed[i] = max(ends[i][1], prev + gap); prev = placed[i]
    labels = {}
    for i, r in enumerate(REGIONS):
        x, y = ends[i]; moved = placed[i] - y > 0.3
        labels[r] = ax.annotate(r, (x, y), xytext=(x + (5.5 if moved else 1.8), placed[i]), textcoords="data", va="center",
                                fontsize=V.sz["annotation"], color=V.ink, annotation_clip=False,
                                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkA=1, shrinkB=3.5) if moved else None)
    # the callouts: circled numbers in the secondary colour, 0.5 pt muted leaders, all in the margin
    fig.canvas.draw(); r_ = fig.canvas.get_renderer()
    b = lambda t: cv.transData.inverted().transform(t.get_window_extent(r_).get_points())   # [[x0, y], [x1, y]] in inches
    yc = lambda t: b(t)[:, 1].mean()
    title_t, sub_t, foot_t = fig.texts
    unit_t, note_t = ([t for t in ax.texts if t.get_text().startswith(w)][0] for w in ("life", "band"))
    XL, XR = 0.3, 6.88
    europe = SERIES["Europe"][-1]
    lab_af = b(labels["Africa"])
    callouts = [
        (1, (XL, yc(title_t)), (b(title_t)[0, 0] - 0.04, yc(title_t))),
        (2, (XL, yc(sub_t)), (b(sub_t)[0, 0] - 0.04, yc(sub_t))),
        (3, (XL, yc(unit_t)), (b(unit_t)[0, 0] - 0.04, yc(unit_t))),
        (4, (XR, to_cv(ax, (2023.6, 40))[1]), to_cv(ax, (2023.6, 40))),
        (5, (XR, to_cv(ax, (2023.6, 30))[1]), to_cv(ax, (2023.6, 30))),
        (6, (to_cv(ax, europe)[0], 0.78), to_cv(ax, europe)),
        (7, (XR, yc(labels["Africa"])), (lab_af[1, 0] + 0.04, yc(labels["Africa"]))),
        (8, (XL, to_cv(ax, (1950, 44.6))[1]), to_cv(ax, (1950.6, 44.6))),
        (9, (XR, to_cv(ax, (2023.6, WORLD_1950))[1]), to_cv(ax, (2023.6, WORLD_1950))),
        (10, (XL, yc(note_t)), (b(note_t)[0, 0] - 0.04, yc(note_t))),
        (11, (XL, yc(foot_t)), (b(foot_t)[0, 0] - 0.04, yc(foot_t))),
    ]
    rad = 0.075
    for n, (cx, cy), (tx, ty) in callouts:
        d = np.array([tx - cx, ty - cy]); u = d / np.hypot(*d)
        cv.plot([cx + rad * u[0], tx], [cy + rad * u[1], ty], color=V.muted, lw=0.5, solid_capstyle="butt")
        cv.add_patch(Circle((cx, cy), rad, facecolor=V.surface, edgecolor=V.secondary, lw=0.6))
        cv.text(cx, cy + 0.004, str(n), fontsize=V.sz["footer"], color=V.secondary, ha="center", va="center")
    return fig


META = dict(
    title="A Vellum figure is built from eleven parts, each with one rule",
    subtitle=f"An annotated specimen of a line figure, numbered in the margin: “{TITLE}”",
    kind="colour", form="annotated specimen", medium="paper", tool="matplotlib",
    data="Period life expectancy, UN WPP (2024) and others, processed by Our World in Data (CC BY 4.0); continents of countries from "
         "Natural Earth v5.1.2",
    script=rel(__file__),
    alt=f"A line chart of life expectancy in Asia, Africa, the Americas and Europe since 1950, with eleven numbered callouts in the "
        f"margin pointing at the claim title, subtitle, unit line, grid, bottom spine, an end dot, an end label, the band, the dotted "
        f"reference line, the quiet note and the footer. Asia gained {GAIN['Asia']:.0f} years, Africa {GAIN['Africa']:.0f}, the Americas "
        f"{GAIN['Americas']:.0f} and Europe {GAIN['Europe']:.0f}.",
    note=f"Specimen claim computed from the data: gains 1950–2023 of {', '.join(f'{r} {g:.1f}' for r, g in GAIN.items())} years. "
         f"Reference line: the world in 1950, {WORLD_1950:.1f} years. Band: 25th to 75th percentile of the {N_ASIA} countries Natural Earth "
         f"places in Asia, per year.",
    parts=PARTS,
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "colour", "anatomy", mode, meta=META if mode == "light" else None))
