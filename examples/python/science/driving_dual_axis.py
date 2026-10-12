"""driving_dual_axis.py: miles driven per person (left axis) and the price of a gallon of petrol (right axis) in the
United States, 1956 to 2010, as two lines on a second y axis drawn the Vellum way.

The rules for a dual axis: two series only, in slots 1 and 2; tick labels stay muted on both sides; each axis carries
its unit line at its top, preceded by a short stroke in the colour of its series, so the reader knows which axis
belongs to which line; one hairline grid only, from the left axis, with the right axis limits chosen so that its ticks
fall on the same gridlines (the same number of intervals); end labels instead of a legend; only the bottom spine.
Data: data/driving.json (Hannah Fairfield, The New York Times, 2010, via vega-datasets)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import Affine2D, ScaledTranslation
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = "Hannah Fairfield, \"Driving Shifts Into Reverse\", The New York Times, 2 May 2010; via vega-datasets 2.8.0"
D = load_json("driving.json")
year = np.array([d["year"] for d in D]); miles = np.array([d["miles"] for d in D], float)
gas = np.array([d["gas"] for d in D], float)
at = lambda y: int(np.where(year == y)[0][0])
change = lambda y0, y1, v: 100 * (v[at(y1)] / v[at(y0)] - 1)

# the long cheapening: from the price peak of the second oil shock to the cheapest year before the 2000s rise
Y0 = int(year[np.argmax(np.where(year <= 1990, gas, -np.inf))])           # first year of the 1980s peak price
Y1 = int(year[np.argmin(np.where(year > Y0, gas, np.inf))])               # the cheapest year after it
P, M = change(Y0, Y1, gas), change(Y0, Y1, miles)
assert P < 0 < M, "price and driving moved apart over the period"
# and the end: the last price peak and how driving followed it
Y2 = int(year[np.argmax(gas)]); PEAK_MILES = int(year[np.argmax(miles)])


def aligned_limits(lo, hi, n):
    """Limits and step for n intervals: the smallest 'nice' step (1, 2, 2.5, 5 x 10^k) whose n intervals, started at a
    multiple of the step at or below lo, reach hi."""
    for k in range(-3, 6):
        for m in (1, 2, 2.5, 5):
            s = m * 10.0 ** k; a = np.floor(lo / s) * s
            if a + n * s >= hi: return a, a + n * s, s


def best_n(series, choices=(4, 5, 6)):
    """The number of intervals that wastes the least axis height, summed over both series."""
    waste = lambda n: sum(1 - (np.ptp(v)) / (aligned_limits(v.min(), v.max(), n)[1] - aligned_limits(v.min(), v.max(), n)[0]) for v in series)
    return min(choices, key=waste)


NINT = best_n([miles, gas])
L0, L1, LS = aligned_limits(miles.min(), miles.max(), NINT)
R0, R1, RS = aligned_limits(gas.min(), gas.max(), NINT)
to_left = lambda g: L0 + (g - R0) / (R1 - R0) * (L1 - L0)                  # a price in left-axis units, for the end labels

TITLE = (f"As petrol got {-P:.0f} % cheaper from {Y0} to {Y1}, Americans drove {M:.0f} % more miles each")
SUB = (f"Miles driven per person (left axis) and the price of a gallon of petrol in 2010 dollars (right axis), "
       f"United States, {year[0]}–{year[-1]}")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.075, right=0.925, top=0.82, bottom=0.12)
    axr = ax.twinx()
    ax.set_zorder(2); ax.patch.set_visible(False)                       # left series drawn above the right axis
    ax.plot(year, miles, color=V.tone(0), lw=V.lw, zorder=3)
    axr.plot(year, gas, color=V.tone(1), lw=V.lw, zorder=3)
    # the period of the claim, marked by its two years on both lines
    for y in (Y0, Y1):
        V.dot(ax, year[at(y)], miles[at(y)], V.tone(0), z=5)
        V.dot(axr, year[at(y)], gas[at(y)], V.tone(1), z=5)
    axr.axvspan(Y0, Y1, color=V.card, zorder=0, lw=0)                 # on the lower axes, under both lines
    axr.patch.set_visible(False)
    ax.annotate(f"{Y0}–{Y1}: price {P:+.0f} %, miles per person {M:+.0f} %".replace("-", "−"),
                ((Y0 + Y1) / 2, L0 + 0.06 * (L1 - L0)), ha="center", va="bottom", fontsize=V.sz["annotation"], color=V.secondary)

    # axes: aligned ticks, one grid (left), muted labels on both sides, bottom spine only
    ax.set_xlim(year[0] - 1, year[-1] + 8)
    ax.set_xticks(range(1960, 2011, 10))
    ax.set_ylim(L0, L1); ax.set_yticks(np.linspace(L0, L1, NINT + 1))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    axr.set_ylim(R0, R1); axr.set_yticks(np.linspace(R0, R1, NINT + 1))
    axr.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:.2f}"))
    axr.grid(False)
    for a in (ax, axr):
        for k in ("left", "right", "top"): a.spines[k].set_visible(False)
    axr.spines["bottom"].set_visible(False)
    ax.spines["bottom"].set_color(V.rule)
    ax.spines["bottom"].set_bounds(year[0] - 1, year[-1] + 8)
    axr.tick_params(axis="y", colors=V.muted, labelcolor=V.muted, pad=2 * V.scale)

    # end labels, in ink, pushed apart in left-axis units
    pts = [(year[-1], miles[-1]), (year[-1], to_left(gas[-1]))]
    ys = vellum.spread([p[1] for p in pts], 0.07 * (L1 - L0))
    for (x0, y0), y, t in zip(pts, ys, ("miles driven", "petrol price")):
        ax.annotate(t, (x0, y0), xytext=(x0 + 0.8, y), textcoords="data", va="center", ha="left", fontsize=V.sz["annotation"],
                    color=V.ink, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5 * V.scale, shrinkA=2 * V.scale, shrinkB=3 * V.scale,
                                    relpos=(0, 0.5)) if abs(y - y0) > 0.02 * (L1 - L0) else None)

    # unit lines with their line keys
    for side, a, text, col in (("left", ax, "miles driven per person in the year", V.tone(0)),
                               ("right", axr, "price of a gallon, 2010 dollars", V.tone(1))):
        place_unit(fig, a, V, text, col, side)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


def place_unit(fig, ax, V, text, color, side):
    """A unit line at the top of one axis, preceded by a 14-pt stroke in the colour of its series: left-aligned over the
    left axis, right-aligned over the right axis."""
    s = V.scale; key, gap, y = 14 * s, 4 * s, 1.03
    x = 0 if side == "left" else 1
    t = ax.text(x, y, text, transform=ax.transAxes, fontsize=V.sz["unit_line"], color=V.muted, va="baseline",
                ha="left" if side == "left" else "right")
    if side == "left":
        t.set_transform(ax.transAxes + ScaledTranslation((key + gap) / 72, 0, fig.dpi_scale_trans)); x0 = 0
    else:
        fig.canvas.draw()
        x0 = -(t.get_window_extent(fig.canvas.get_renderer()).width * 72 / fig.dpi + gap + key)
    # the key, in points from the anchor of the unit line, on the middle of the lower-case letters
    pts = Affine2D().scale(1 / 72) + fig.dpi_scale_trans + ScaledTranslation(x, y, ax.transAxes)
    mid = 0.27 * V.sz["unit_line"]
    fig.add_artist(Line2D([x0, x0 + key], [mid, mid], transform=pts, color=color, lw=V.lw, solid_capstyle="butt"))


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="line chart with a second y axis", medium="screen", tool="matplotlib",
            data="Miles driven per capita and petrol price in 2010 dollars, United States, 1956–2010 (Fairfield, NYT 2010; vega-datasets)",
            script=rel(__file__),
            alt=(f"Two lines on two y axes, 1956 to 2010: miles driven per person (left axis, teal) rises from {miles[0]:,.0f} to a peak "
                 f"of {miles.max():,.0f} in {PEAK_MILES}; the price of a gallon of petrol in 2010 dollars (right axis, terracotta) "
                 f"falls {-P:.0f} % from ${gas[at(Y0)]:.2f} in {Y0} to ${gas[at(Y1)]:.2f} in {Y1}, while driving per person rises "
                 f"{M:.0f} %. The price peaks at ${gas.max():.2f} in {Y2}."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "driving_dual_axis", mode, meta=META if mode == "light" else None)
