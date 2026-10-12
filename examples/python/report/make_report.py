"""make_report.py: a three-page A4 report in the Vellum style, as HTML that prints to PDF.

Global life expectancy, 1950-2023, and the setback of the pandemic years. Data: data/owid-life-expectancy.csv
(period life expectancy at birth; UN WPP 2024 and others, processed by Our World in Data, CC BY 4.0) and
data/ne_110m_admin_0_countries.geojson (Natural Earth v5.1.2 outlines and 2019 population estimates, public domain).

One run, end to end:
  1. computes every number the report states and writes them to docs/media/report/numbers.json;
  2. draws the four figures in both twins with vellum.py into docs/figures/report/ (PNG, PDF, and an SVG of the
     light twin with text as paths, which the page embeds so the print stays vector);
  3. fills template.html and report.css (next to this script) into docs/media/report/, so no number is typed by hand;
  4. prints report.pdf and a 2x PNG of each page (plus 600 px thumbnails) with headless Edge (tools/render.py);
  5. records the figures and the report in docs/figures/report/manifest.json.
"""
import os, sys, re, csv, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle
from matplotlib import patheffects as pe
from scipy import stats
sys.path.insert(0, os.path.join(REPO, "tools"))
import render                                                          # noqa: E402  headless Edge, PNG and PDF

SRC = os.path.dirname(os.path.abspath(__file__))       # template.html and report.css live next to this script
OUT = os.path.join(DOCS, "media", "report")
GROUP = "report"
MM = 1 / 25.4                                     # inches per millimetre
COL12, COL8 = 170 * MM, (8 * 10.5 + 7 * 4) * MM  # A4, 20 mm margins, 12 columns of 10.5 mm with 4 mm gutters
SRC_LE = "Our World in Data (UN WPP 2024 and others)"
SRC_NE = "Natural Earth v5.1.2"


# ================================================================ 1. data and numbers

def series():
    """{key: {year: value}} keyed by the entity name and by its code (regions and groups have OWID_ codes); {code: name}."""
    by, name = {}, {}
    for r in csv.DictReader(open(os.path.join(DATA, "owid-life-expectancy.csv"), encoding="utf-8")):
        s = by.setdefault(r["Entity"], {}); s[int(r["Year"])] = float(r["Life expectancy"])
        if r["Code"]: by[r["Code"]] = s; name[r["Code"]] = r["Entity"]
    return by, name


LE, OWID_NAME = series()
W = LE["OWID_WRL"]
GROUPS = {"high": "High-income countries", "umi": "Upper-middle-income countries",
          "lmi": "Lower-middle-income countries", "low": "Low-income countries"}
INC = {k: LE[v] for k, v in GROUPS.items()}
PANDEMIC = (2020, 2021, 2022)                    # the years in which a fall is counted against 2019


def trough(s):
    """Lowest value of 2019 and the pandemic years, and its year: the depth of the fall is s[2019] minus it."""
    y = min((2019,) + PANDEMIC, key=lambda t: s[t])
    return s[y], y


def countries():
    """Natural Earth features with their OWID code (ISO A3, or the ADM0 code where ISO is -99; Kosovo is OWID_KOS)."""
    feats = load_json("ne_110m_admin_0_countries.geojson")["features"]
    out = []
    for f in feats:
        p = f["properties"]
        code = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
        code = {"KOS": "OWID_KOS"}.get(code, code)
        label = min(p["NAME"], OWID_NAME.get(code, p["NAME"]), key=len)          # the shorter of the two names
        out.append(dict(code=code, name=label, short=p["NAME"], long=p["NAME_LONG"], continent=p["CONTINENT"], pop=p["POP_EST"],
                        geom=f["geometry"], value=LE.get(code, {}).get(2023)))
    return out


def fmt(x, d=1, sign=False):
    """A number as the report prints it: d decimals, a true minus sign, an optional plus."""
    s = f"{abs(x):.{d}f}"
    return ("\u2212" if x < 0 and float(s) != 0 else "+" if sign and x > 0 else "") + s


def names(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def numbers():
    n = {}
    # ---- the world, 1950 to 2023
    n["w1950"], n["w2019"], n["w2023"] = W[1950], W[2019], W[2023]
    n["gain"] = W[2023] - W[1950]
    tw, ty = trough(W)
    n["w_trough"], n["trough_year"], n["dip"] = tw, ty, W[2019] - tw
    # the last two-year fall before 2020 at least as deep as the pandemic's
    n["prev_fall_year"] = max(y for y in range(1952, 2020) if W[y] - W[y - 2] <= -n["dip"])
    n["prev_fall"] = W[n["prev_fall_year"] - 2] - W[n["prev_fall_year"]]
    n["back_year"] = min(y for y in range(ty + 1, 2024) if W[y] >= W[2019])
    n["above2019"], n["regained"] = W[2023] - W[2019], W[2023] - tw
    china = LE["CHN"]
    n["china1958"], n["china1960"] = china[1958], china[1960]
    # ---- income groups: the long gap and the depth of the fall in each
    for k, s in INC.items():
        n[f"{k}2023"], n[f"{k}1950"] = s[2023], s[1950]
        n[f"{k}_dip"] = s[2019] - trough(s)[0]
    n["inc_gap2023"], n["inc_gap1950"] = INC["high"][2023] - INC["low"][2023], INC["high"][1950] - INC["low"][1950]
    n["gap_over_dip"] = n["inc_gap2023"] / n["dip"]
    # ---- the 2000-2019 trend, extended: ordinary least squares and its 95 % prediction interval
    x = np.arange(2000, 2020); y = np.array([W[t] for t in x])
    fit = stats.linregress(x, y)
    s = np.sqrt(np.sum((y - (fit.intercept + fit.slope * x)) ** 2) / (len(x) - 2))
    tq = stats.t.ppf(0.975, len(x) - 2)
    n["trend"] = dict(intercept=fit.intercept, slope=fit.slope, s=s, t=tq, xbar=x.mean(), sxx=np.sum((x - x.mean()) ** 2), n=len(x))
    pred23, half23 = trend_at(n["trend"], 2023)
    n["trend2023"], n["pi2023"], n["trend_gap"] = pred23, half23, pred23 - W[2023]
    n["below_band"] = bool(W[2023] < pred23 - half23)
    n["trend_slope_decade"] = 10 * fit.slope
    # ---- the map: quintiles of 2023 over the countries drawn with a value
    C = countries()
    vals = np.array([c["value"] for c in C if c["value"] is not None])
    q = np.percentile(vals, [20, 40, 60, 80])
    low = [c for c in C if c["value"] is not None and c["value"] < q[0]]
    n["map_n"], n["breaks"] = len(vals), [float(v) for v in q]
    n["low_n"], n["low_africa"] = len(low), sum(c["continent"] == "Africa" for c in low)
    lo, hi = min((c for c in C if c["value"]), key=lambda c: c["value"]), max((c for c in C if c["value"]), key=lambda c: c["value"])
    n["map_min"], n["map_min_name"], n["map_max"], n["map_max_name"] = lo["value"], lo["name"], hi["value"], hi["name"]
    gone = [c for c in C if c["value"] is None and c["continent"] != "Antarctica"]
    n["missing"], n["missing_short"] = [c["long"] for c in gone], [c["short"] for c in gone]
    # ---- the dot plot: the most populous countries, their 2023 level, 2019 and the deepest pandemic year
    ranked = sorted((c for c in C if c["value"] is not None), key=lambda c: -c["pop"])[:30]
    n["pop_n"], n["pop_share"] = len(ranked), sum(c["pop"] for c in ranked) / sum(c["pop"] for c in C)
    rows = []
    for c in ranked:
        s = LE[c["code"]]; tv, tyr = trough(s)
        rows.append(dict(name=c["name"], v19=s[2019], v23=s[2023], trough=tv, trough_year=tyr, fall=s[2019] - tv))
    n["rows"] = sorted(rows, key=lambda r: r["v23"])
    focal = sorted((r for r in rows if r["fall"] >= 4.0), key=lambda r: -r["fall"])   # the claim: four years or more
    n["focal"] = [r["name"] for r in focal]
    n["focal_back"] = all(r["v23"] >= r["v19"] for r in focal)
    n["focal_max"], n["focal_max_name"] = focal[0]["fall"], focal[0]["name"]
    n["n_below2019"] = sum(r["v23"] < r["v19"] for r in rows)
    n["n_nofall"] = sum(r["fall"] <= 0 for r in rows)
    return n


def trend_at(tr, t):
    """Value of the 2000-2019 trend at year t and the half width of its 95 % prediction interval."""
    t = np.asarray(t, float)
    pred = tr["intercept"] + tr["slope"] * t
    half = tr["t"] * tr["s"] * np.sqrt(1 + 1 / tr["n"] + (t - tr["xbar"]) ** 2 / tr["sxx"])
    return pred, half


N = numbers()

# the claims: one per figure, written from the numbers, never typed
CLAIM = dict(
    world=f"World life expectancy rose {fmt(N['gain'])} years since 1950; the pandemic took {fmt(N['dip'])} back",
    projection=f"In 2023 the world was {fmt(N['trend_gap'])} years below its trend",
    map=f"Of the {N['low_n']} countries with the lowest life expectancy, {N['low_africa']} are in Africa",
    dots=(f"{names(N['focal'])} fell four years or more"
          + (" and were back by 2023" if N["focal_back"] else ", and not all were back by 2023")),
)
SUB = dict(
    world="Period life expectancy at birth, 1950–2023: the world, high-income countries and low-income countries",
    projection="World life expectancy at birth, 2000–2023, against the 2000–2019 trend",
    map=f"Period life expectancy at birth in 2023, {N['map_n']} countries in five classes of equal count (quintiles)",
    dots=f"Life expectancy at birth in the {N['pop_n']} most populous countries, 2019 to 2023",
)


# ================================================================ 2. figures

def at(fig, left, top, width, height):
    """Axes placed in inches from the left and top edges of the figure: the layout is exact, never 'tight'."""
    fw, fh = fig.get_size_inches()
    return fig.add_axes([left / fw, 1 - (top + height) / fh, width / fw, height / fh])


def wrap(fig, text, width, **kw):
    """Greedy word wrap of `text` to `width` inches, measured with the figure's renderer (less 4 % for the hinting at
    other resolutions)."""
    r = fig.canvas.get_renderer(); lines, cur = [], ""
    for w in text.split(" "):                          # a no-break space keeps a name on one line
        trial = (cur + " " + w).strip()
        t = fig.text(0, 0, trial, **kw); wide = t.get_window_extent(r).width / fig.dpi; t.remove()
        if wide > 0.96 * width and cur: lines.append(cur); cur = w
        else: cur = trial
    return lines + [cur]


PT = 1 / 72


def head(V, title, subtitle, source, width, plot_height, gap_top=0.30, gap_bottom=0.33):
    """A figure of `width` whose plot area is `plot_height` inches, with the title block of V.title above it, flush with
    the column edge and wrapped to the width: the claim in Palatino, the subtitle one title height below its last line,
    the footer (wrapped too) at the bottom. Returns the figure and the depth of the title block in inches."""
    probe = plt.figure(figsize=(width, 1))
    tl = wrap(probe, title, width, fontsize=V.sz["title"], fontfamily=V.title_font)
    sl = wrap(probe, subtitle, width, fontsize=V.sz["subtitle"])
    fl = wrap(probe, source, width, fontsize=V.sz["footer"]); plt.close(probe)
    y_sub = 0.02 + (len(tl) - 1) * V.sz["title"] * 1.15 * PT + V.sz["title"] * 1.45 * PT
    top = y_sub + len(sl) * V.sz["subtitle"] * 1.2 * PT
    foot = 0.03 + len(fl) * V.sz["footer"] * 1.2 * PT
    H = top + gap_top + plot_height + gap_bottom + foot
    fig = plt.figure(figsize=(width, H))
    fig.text(0, 1 - 0.02 / H, "\n".join(tl), fontsize=V.sz["title"], fontfamily=V.title_font, color=V.ink, va="top", ha="left",
             linespacing=1.15)
    fig.text(0, 1 - y_sub / H, "\n".join(sl), fontsize=V.sz["subtitle"], color=V.muted, va="top", ha="left", linespacing=1.2)
    fig.text(0, 0.03 / H, "\n".join(fl), fontsize=V.sz["footer"], color=V.muted, va="bottom", ha="left", linespacing=1.2)
    return fig, top + gap_top


def unit(ax, V, text):
    """The unit line above the y axis, a fixed 5 pt above the plot area, in place of a rotated y label."""
    ax.annotate(text, (0, 1), xycoords="axes fraction", xytext=(0, 5), textcoords="offset points",
                fontsize=V.sz["unit_line"], color=V.muted, va="bottom", ha="left", annotation_clip=False)


def leader(ax, V, xy, text, xytext, **kw):
    """V.callout with the text placed in data coordinates and the leader leaving from the side of the text it faces."""
    ax.annotate(text, xy, xytext=xytext, textcoords="data", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.2,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.6, shrinkA=2, shrinkB=3, relpos=kw.pop("relpos", (1, 0.5))), **kw)


def draw_world(V):
    fig, top = head(V, CLAIM["world"], SUB["world"], footer(SRC_LE + ", 1950–2023", __file__), COL12, 1.85)
    ax = at(fig, 0.30, top, COL12 - 0.30 - 1.62, 1.85)
    yrs = np.arange(1950, 2024)
    lines = [("World", W, V.tone(0)), ("High-income countries", INC["high"], V.tone(1)), ("Low-income countries", INC["low"], V.tone(2))]
    for label, s, c in lines:
        ax.plot(yrs, [s[t] for t in yrs], color=c, lw=V.lw, zorder=3)
        V.dot(ax, 2023, s[2023], c)
    V.endlabels(ax, [(2023, s[2023]) for _, s, _ in lines], [f"{lab}, {fmt(s[2023])}" for lab, s, _ in lines], gap=3.2, x_text=2026.5)
    # the pandemic fall: the text sits where the world and low-income lines are furthest apart, and its leader runs
    # between them to the lowest year without crossing either
    ty = N["trough_year"]
    leader(ax, V, (ty, N["w_trough"]), f"2019–{ty % 100:02d}: {fmt(-N['dip'])} years\n{ty}–23: {fmt(N['regained'], sign=True)} years",
           (1997.6, 57.2), ha="right", va="center")
    V.note(ax, 1961.3, 46.3, "famine in China", va="bottom")
    ax.set_xlim(1949, 2024.5); ax.set_xticks([1950, 1970, 1990, 2010])
    ax.set_ylim(30, 86); ax.set_yticks([40, 60, 80])
    unit(ax, V, "life expectancy at birth, years; the axis starts at 30")
    return fig


def draw_projection(V):
    fig, top = head(V, CLAIM["projection"], SUB["projection"], footer(SRC_LE + ", 2000–2023", __file__), COL8, 1.42)
    ax = at(fig, 0.30, top, COL8 - 0.30 - 0.95, 1.42)
    tr = N["trend"]
    obs = np.arange(2000, 2024); fitx = np.arange(2000, 2020); ext = np.linspace(2019, 2030, 45)
    pred, half = trend_at(tr, ext)
    # the projection: tint band and a dotted line after the last year of the fit, the fit itself thin and solid
    ax.fill_between(ext, pred - half, pred + half, color=V.tint("ochre"), alpha=V.band_alpha, lw=0, zorder=1)
    ax.plot(fitx, trend_at(tr, fitx)[0], color=V.tone("ochre"), lw=V.thin, zorder=2)
    ax.plot(ext, pred, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=2)
    ax.plot(obs, [W[t] for t in obs], color=V.tone(0), lw=V.lw, zorder=3)
    # the gap: a thin bracket at 2023 from the observed value up to the trend, its number beside the end dot
    ax.plot([2023, 2023], [W[2023], N["trend2023"]], color=V.ink, lw=V.thin, zorder=4, solid_capstyle="butt")
    V.dot(ax, 2023, W[2023], V.tone(0), z=5)
    ax.annotate(f"world, {fmt(W[2023])} in 2023:\n{fmt(N['trend_gap'])} years below the trend", (2023, W[2023]), xytext=(6, -3),
                textcoords="offset points", ha="left", va="top", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.2,
                annotation_clip=False)
    V.endlabel(ax, 2030, pred[-1], "2000–2019 trend", dx=5)
    V.note(ax, 2000.3, 77.7, "projection: the trend of 2000–2019 extended, not a forecast\n"
                             "band: 95 % prediction interval of that straight line", linespacing=1.25)
    ax.set_xlim(1999.5, 2030.5); ax.set_xticks([2000, 2010, 2020, 2030]); ax.tick_params(axis="x", pad=6)
    ax.set_ylim(65, 78); ax.set_yticks([65, 70, 75])
    unit(ax, V, "life expectancy at birth, years; the axis starts at 65")
    return fig


# ---- the map: Equal Earth (Šavrič, Patterson and Jenny 2018), written out rather than imported
EE = (1.340264, -0.081106, 0.000893, 0.003796)
MAP_LAT = (-56.5, 84.0)                            # Antarctica dropped; Tierra del Fuego to the north of Greenland


def equal_earth(lon, lat):
    A1, A2, A3, A4 = EE
    th = np.arcsin(np.sqrt(3) / 2 * np.sin(np.radians(lat)))
    t2 = th * th; t6 = t2 ** 3
    x = 2 * np.sqrt(3) * np.radians(lon) * np.cos(th) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


def country_path(geom):
    """One compound path per country: exterior rings counter-clockwise, holes clockwise, so the non-zero rule cuts holes."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    verts, codes = [], []
    for poly in polys:
        for k, ring in enumerate(poly):
            r = np.array(ring, float); x, y = equal_earth(r[:, 0], r[:, 1])
            area = 0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
            if (area < 0) == (k == 0): x, y = x[::-1], y[::-1]
            verts += list(zip(x, y)); codes += [Path.MOVETO] + [Path.LINETO] * (len(x) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes)


def draw_map(V):
    x0, x1 = equal_earth(np.array([-180.0, 180.0]), np.zeros(2))[0]
    y0, y1 = equal_earth(0.0, MAP_LAT[0])[1], equal_earth(0.0, MAP_LAT[1])[1]
    mh = COL12 * (y1 - y0) / (x1 - x0)                            # the map's height at the full column width
    fig, top = head(V, CLAIM["map"], SUB["map"], footer(f"{SRC_LE}, 2023 · outlines {SRC_NE}, Equal Earth projection", __file__),
                    COL12, mh, gap_top=0.06, gap_bottom=0.06)
    ax = at(fig, 0, top, COL12, mh); ax.set_axis_off()
    classes = V.sequential["teal"][1:6]                           # five steps of one ramp: darker (light) or brighter (dark) is longer
    edges = N["breaks"]
    hatch = dict(facecolor=V.card, hatch="//////", hatchcolor=V.tone(1))   # no value: card with a terracotta hatch, never a class
    with plt.rc_context({"hatch.linewidth": 0.45}):
        for c in countries():
            if c["continent"] == "Antarctica": continue
            path = country_path(c["geom"])
            fill = hatch if c["value"] is None else dict(facecolor=classes[int(np.digitize(c["value"], edges))])
            ax.add_patch(PathPatch(path, edgecolor=V.grid, lw=0.4, **fill))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        # the legend, in the empty South Pacific west of Chile: the five classes with their break values, then the hatch
        lg = at(fig, 0, top + mh - 0.90, 2.0, 0.90); lg.set_axis_off(); lg.set_xlim(0, 2.0); lg.set_ylim(0.90, 0)  # inches, down
        lg.text(0, 0, "years of life expectancy at birth, 2023", fontsize=V.sz["unit_line"], color=V.muted, va="top")
        sw = 0.37
        for k, col in enumerate(classes):
            lg.add_patch(Rectangle((k * sw, 0.16), sw - 0.02, 0.10, facecolor=col, edgecolor="none"))
        ticks = [N["map_min"]] + edges + [N["map_max"]]
        for k, t in enumerate(ticks):
            lg.text(k * sw - (0.01 if k else 0), 0.30, fmt(t), fontsize=V.sz["unit_line"], color=V.muted, va="top",
                    ha="left" if k == 0 else "right" if k == len(ticks) - 1 else "center")
        lg.add_patch(Rectangle((0, 0.52), 0.22, 0.10, edgecolor="none", **hatch))
        gone = ["no separate estimate:"] + wrap(fig, names([m.replace(" ", "\u00a0") for m in N["missing_short"]]), 1.6,
                                                fontsize=V.sz["unit_line"])
        lg.text(0.29, 0.505, "\n".join(gone), fontsize=V.sz["unit_line"], color=V.muted, va="top", linespacing=1.2)
    return fig


def draw_dots(V):
    rows = N["rows"]; n = len(rows); row_h = 0.122; left, right = 1.0, 0.40
    fig, top = head(V, CLAIM["dots"], SUB["dots"],
                    footer(f"{SRC_LE}, {SRC_NE}", __file__), COL8, n * row_h, gap_top=0.36, gap_bottom=0.42)
    ax = at(fig, left, top, COL8 - left - right, n * row_h)
    ax.grid(False); ax.spines["bottom"].set_visible(False)
    focal = set(N["focal"])
    for i, r in enumerate(rows):
        f = r["name"] in focal
        c = V.tone(1) if f else V.rule                          # about a few things: terracotta for them, rule grey for the rest
        ax.axhline(i, color=V.grid, lw=0.5, zorder=0)            # the row's hairline, horizontal like every Vellum grid
        lo, hi = min(r["trough"], r["v23"]), max(r["v19"], r["v23"])
        ax.plot([lo, hi], [i, i], color=c, lw=V.thin * (1.6 if f else 1), solid_capstyle="butt", zorder=2)
        ax.scatter(r["v19"], i, s=20, facecolor=V.surface, edgecolor=c, linewidth=0.9, zorder=3)
        V.dot(ax, r["v23"], i, c)
        if f:
            ax.annotate(f"{fmt(-r['fall'])} in {r['trough_year']}", (lo, i), xytext=(-5, 0), textcoords="offset points",
                        ha="right", va="center", fontsize=V.sz["annotation"], color=V.ink,
                        path_effects=[pe.withStroke(linewidth=2.5, foreground=V.surface)])
        ax.annotate(fmt(r["v23"]), (1, i), xycoords=("axes fraction", "data"), xytext=(right * 72 - 1, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=V.sz["annotation"], color=V.ink if f else V.muted, annotation_clip=False)
    ax.set_yticks(range(n)); ax.set_yticklabels([r["name"] for r in rows], fontsize=V.sz["annotation"])
    for lab, r in zip(ax.get_yticklabels(), rows):
        lab.set_color(V.ink if r["name"] in focal else V.muted)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(50, 87); ax.set_xticks([50, 60, 70, 80]); ax.tick_params(axis="x", pad=2)
    ax.set_xlabel("life expectancy at birth, years", fontsize=V.sz["unit_line"], labelpad=3)
    # the key, in place of a legend box: what each mark is; the value column is headed by its year
    ky = at(fig, left, top - 0.27, COL8 - left - right, 0.14); ky.set_axis_off(); ky.set_xlim(0, 1); ky.set_ylim(-1, 1)
    k = (COL8 - left - right)                                   # key positions in inches along the plot width
    ky.scatter([0.05 / k], [0], s=28, color=V.rule, edgecolor=V.surface, linewidth=1.2)
    ky.text(0.13 / k, 0, "2023", fontsize=V.sz["unit_line"], color=V.muted, va="center")
    ky.scatter([0.55 / k], [0], s=20, facecolor=V.surface, edgecolor=V.rule, linewidth=0.9)
    ky.text(0.63 / k, 0, "2019", fontsize=V.sz["unit_line"], color=V.muted, va="center")
    ky.plot([1.05 / k, 1.30 / k], [0, 0], color=V.rule, lw=V.thin)
    ky.text(1.37 / k, 0, f"down to the lowest year of {PANDEMIC[0]}–{PANDEMIC[-1]}", fontsize=V.sz["unit_line"], color=V.muted, va="center")
    ax.annotate("2023", (1, n - 0.4), xycoords=("axes fraction", "data"), xytext=(right * 72 - 1, 3), textcoords="offset points",
                ha="right", va="bottom", fontsize=V.sz["unit_line"], color=V.muted, annotation_clip=False)
    return fig


# ================================================================ 3. the words: every number the page prints, as text

WORDS = "no one two three four five six seven eight nine ten eleven twelve".split()


def word(k, cap=False):
    w = WORDS[k] if 0 <= k < len(WORDS) else str(k)
    return w[0].upper() + w[1:] if cap else w


def text():
    f, top = fmt, max(N["rows"], key=lambda r: r["fall"])
    T = dict(
        w1950=f(N["w1950"]), w2019=f(N["w2019"]), w2023=f(N["w2023"]), gain=f(N["gain"]), gain_per_year=f(N["gain"] / (2023 - 1950), 2),
        dip=f(N["dip"]), dip_neg=f(-N["dip"]), trough_year=N["trough_year"], prev_fall_year=N["prev_fall_year"],
        back_year=N["back_year"], above2019=f(N["above2019"]), above2019_signed=f(N["above2019"], sign=True),
        regained=f(N["regained"]), china1958=f(N["china1958"]), china1960=f(N["china1960"]),
        high2023=f(N["high2023"]), low2023=f(N["low2023"]), inc_gap2023=f(N["inc_gap2023"]), inc_gap1950=f(N["inc_gap1950"]),
        high_dip=f(N["high_dip"]), umi_dip=f(N["umi_dip"]), lmi_dip=f(N["lmi_dip"]), low_dip=f(N["low_dip"]),
        gap_over_dip=f"more than {word(int(N['gap_over_dip']))}",
        trend_decade=f(N["trend_slope_decade"]), slope=f(N["trend"]["slope"], 2), trend2023=f(N["trend2023"]),
        trend_gap=f(N["trend_gap"]), pi2023=f(N["pi2023"]), band_where="outside" if N["below_band"] else "inside",
        map_n=N["map_n"], map_min=f(N["map_min"]), map_min_name=N["map_min_name"], map_max=f(N["map_max"]),
        map_max_name=N["map_max_name"], map_spread=f(N["map_max"] - N["map_min"]), low_n=N["low_n"], low_africa=N["low_africa"],
        b1=f(N["breaks"][0]), b2=f(N["breaks"][1]), b3=f(N["breaks"][2]), b4=f(N["breaks"][3]), missing=names(N["missing"]),
        pop_n=N["pop_n"], pop_share=f"{100 * N['pop_share']:.0f}",
        focal_max_neg=f(-top["fall"]), focal_max_name=top["name"], focal_max_year=top["trough_year"], focal_max_back=f(top["v23"] - top["v19"]),
        n_nofall_word=word(N["n_nofall"], cap=True), n_below_word=word(N["n_below2019"]),
        claim_world=CLAIM["world"], claim_projection=CLAIM["projection"], claim_map=CLAIM["map"], claim_dots=CLAIM["dots"],
        stamp=stamp(),
    )
    T.update({f"alt_{k}": v for k, v in ALT.items()})
    return T


ALT = dict(
    world=(f"Line chart of life expectancy at birth, 1950 to 2023. The world rises from {fmt(N['w1950'])} to {fmt(N['w2023'])} years; "
           f"high-income countries reach {fmt(N['high2023'])} and low-income countries {fmt(N['low2023'])}. The world falls "
           f"{fmt(N['dip'])} years from 2019 to {N['trough_year']} and gains {fmt(N['regained'])} back by 2023."),
    projection=(f"Line chart of world life expectancy, 2000 to 2023, with the 2000–2019 trend extended as a dotted line in a band "
                f"to 2030. In 2023 the world, at {fmt(N['w2023'])} years, is {fmt(N['trend_gap'])} years below the trend value of "
                f"{fmt(N['trend2023'])}."),
    map=(f"World map of life expectancy at birth in 2023 in five classes, from {fmt(N['map_min'])} years in {N['map_min_name']} to "
         f"{fmt(N['map_max'])} in {N['map_max_name']}. {N['low_africa']} of the {N['low_n']} countries in the lowest class are in Africa."),
    dots=(f"Dot plot of life expectancy in 2023 in the {N['pop_n']} most populous countries, from {fmt(N['rows'][-1]['v23'])} in "
          f"{N['rows'][-1]['name']} to {fmt(N['rows'][0]['v23'])} in {N['rows'][0]['name']}, with 2019 and the lowest year of "
          f"2020–2022. {names(N['focal'])} fell four years or more."),
)


# ================================================================ 4. figures in both twins, and the manifest

FIGS = dict(
    report_world_line=(draw_world, "world", "line chart with callouts", "1950–2023"),
    report_projection=(draw_projection, "projection", "line chart with a projection band", "2000–2023"),
    report_choropleth=(draw_map, "map", "choropleth, Equal Earth projection", "2023; outlines Natural Earth v5.1.2"),
    report_dotplot=(draw_dots, "dots", "dot plot with range lines", "2019–2023; population Natural Earth v5.1.2 (2019)"),
)
DATA_LE = "Period life expectancy at birth, UN World Population Prospects (2024) and others, processed by Our World in Data"


def figures():
    for name, (draw, key, form, years) in FIGS.items():
        meta = dict(title=CLAIM[key], subtitle=SUB[key], kind="report", form=form, medium="report", tool="matplotlib",
                    data=f"{DATA_LE}, {years}", script=rel(__file__), alt=ALT[key],
                    note="One of the four figures of the example report (media/report/index.html); drawn at its printed width.")
        for mode in MODES:
            V = vellum.use(mode)
            plt.rcParams["savefig.bbox"] = None               # drawn at its printed size: the page places it 1:1
            fig = draw(V)
            if mode == "light":                                # the page embeds a vector copy with the text as paths
                with plt.rc_context({"svg.fonttype": "path"}):
                    fig.savefig(os.path.join(FIGURES, GROUP, f"{name}_light.svg"))
            save(fig, GROUP, name, mode, meta=meta if mode == "light" else None)


# ================================================================ 5. the page, the PDF and the PNGs

PAGES = 3


def sheet_tokens():
    """The light tokens of vellum.json, fixed on .sheet: the report is print and keeps them in the site's dark mode."""
    L = vellum.SPEC["light"]
    lines = [f"  --v-{k}: {v};" for k, v in L["neutrals"].items()]
    for i, fam in enumerate(vellum.SPEC["order"]):
        lines += [f"  --v-{fam}: {L['tone'][i]};", f"  --v-{fam}-tint: {L['tint'][i]};", f"  --v-{fam}-deep: {L['deep'][i]};"]
    return ("/* Generated by examples/python/report/make_report.py: the light tokens of style/vellum.json, then report.css. */\n"
            ".sheet {\n  color-scheme: light;\n" + "\n".join(lines) + "\n}\n\n")


def page():
    """Fill template.html with the words, write the stylesheet and numbers.json."""
    import html
    os.makedirs(OUT, exist_ok=True)
    T = text()

    def fill(m):
        if m.group(1) not in T: raise KeyError(f"template.html asks for {m.group(1)}, which the script does not compute")
        return html.escape(str(T[m.group(1)]), quote=True)
    out = re.sub(r"\{\{(\w+)\}\}", fill, open(os.path.join(SRC, "template.html"), encoding="utf-8").read())
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n") as fh: fh.write(out)
    with open(os.path.join(OUT, "report.css"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sheet_tokens() + open(os.path.join(SRC, "report.css"), encoding="utf-8").read())

    def plain(v):                                      # numpy and nested values as JSON, floats to four places
        if isinstance(v, dict): return {k: plain(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)): return [plain(x) for x in v]
        if isinstance(v, (float, np.floating)): return round(float(v), 4)
        if isinstance(v, np.integer): return int(v)
        return v
    json.dump(dict(source=rel(__file__), stamp=T["stamp"], numbers=plain(N), text={k: v for k, v in T.items() if not k.startswith("alt_")}),
              open(os.path.join(OUT, "numbers.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def prints():
    """report.pdf from the print stylesheet, then each sheet alone (?page=N) as a 2x PNG and a 600 px thumbnail."""
    from PIL import Image
    index = os.path.join(OUT, "index.html")
    render.pdf(index, os.path.join(OUT, "report.pdf"))
    os.makedirs(os.path.join(OUT, "thumbs"), exist_ok=True)
    for k in range(1, PAGES + 1):
        png = os.path.join(OUT, f"page-{k}.png")
        render.png(f"{index}?page={k}", png, 794, 1123, 2)          # A4 at 96 px per inch, twice
        im = Image.open(png).convert("RGB")
        im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS).save(os.path.join(OUT, "thumbs", f"page-{k}.png"), optimize=True)


REPORT = dict(
    title="Recovered, but not back on track", kind="report", form="A4 report, 3 pages", medium="report", tool="HTML + matplotlib",
    subtitle="Global life expectancy, 1950–2023, and the setback of the pandemic years: an example report, illustrative layout, real data",
    data=f"{DATA_LE}, 1950–2023; country outlines and 2019 population estimates, Natural Earth v5.1.2",
    script=rel(__file__),
    alt=(f"Page one of a three-page A4 report: a summary of five claims, three stat tiles and a line chart of world life expectancy, "
         f"which rose from {fmt(N['w1950'])} years in 1950 to {fmt(N['w2023'])} in 2023."),
    note="Illustrative layout, real data. Every number is computed by the script and written to media/report/numbers.json.",
    files={"html": "media/report/index.html", "pdf": "media/report/report.pdf", "light": "media/report/page-1.png",
           "pages": [f"media/report/page-{k}.png" for k in range(1, PAGES + 1)],
           "thumbs": [f"media/report/thumbs/page-{k}.png" for k in range(1, PAGES + 1)],
           "numbers": "media/report/numbers.json"},
)

if __name__ == "__main__":
    steps = sys.argv[1:] or ["figures", "page", "prints"]           # all three by default; a step can be run alone
    os.makedirs(os.path.join(FIGURES, GROUP), exist_ok=True)
    record(GROUP, "report", REPORT)                                  # first, so the report leads its group in the gallery
    if "figures" in steps: figures()
    if "page" in steps: page()
    if "prints" in steps: prints()
