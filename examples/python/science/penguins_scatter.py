"""penguins_scatter.py: flipper length against body mass for three penguin species, ringed dots, one least-squares
line per species with its 95 % confidence band, direct labels. Data: data/penguins.json (Palmer penguins)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
from scipy import stats
from matplotlib.ticker import FuncFormatter
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # silence the Lato fallback lookups

SOURCE = ("Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; "
          "via the palmerpenguins R package and vega-datasets 2.8.0")
SPECIES = ("Adelie", "Chinstrap", "Gentoo")             # slot order: teal, terracotta, indigo

P = penguins()
FITS = {}
for s in SPECIES:
    x = np.array([r["Flipper Length (mm)"] for r in P if r["Species"] == s], float)
    y = np.array([r["Body Mass (g)"] for r in P if r["Species"] == s], float)
    n = len(x); b, a = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 60)
    resid = y - (a + b * x); sd = np.sqrt(resid @ resid / (n - 2))
    half = stats.t.ppf(0.975, n - 2) * sd * np.sqrt(1 / n + (xs - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum())
    FITS[s] = dict(x=x, y=y, n=n, slope=b, xs=xs, fit=a + b * xs, half=half, r=np.corrcoef(x, y)[0, 1])
lo, hi = min(f["slope"] for f in FITS.values()), max(f["slope"] for f in FITS.values())

TITLE = f"In every species, body mass rises by {lo:.0f} to {hi:.0f} g with each millimetre of flipper"
SUB = (f"{len(P)} penguins of the Palmer Archipelago, 2007–2009 · one least-squares line per species · "
       f"r = {FITS['Adelie']['r']:.2f}, {FITS['Chinstrap']['r']:.2f} and {FITS['Gentoo']['r']:.2f}")


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.08, right=0.84, top=0.80, bottom=0.12)
    for k, s in enumerate(SPECIES):
        f = FITS[s]
        ax.fill_between(f["xs"], f["fit"] - f["half"], f["fit"] + f["half"], color=V.tint(k), alpha=V.band_alpha, lw=0, zorder=2)
        V.dot(ax, f["x"], f["y"], V.tone(k), z=3)
        ax.plot(f["xs"], f["fit"], color=V.tone(k), lw=V.lw, zorder=5)
        label = f"{s}, {f['slope']:.0f} g per mm"
        if s == "Adelie":     # Adelie and Chinstrap end together at the right, so Adelie is labelled at its left end
            ax.annotate(label, (f["xs"][0], f["fit"][0]), xytext=(-8, 0), textcoords="offset points", ha="right", va="center",
                        fontsize=V.sz["annotation"], color=V.ink, path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)])
        else:
            V.endlabel(ax, f["xs"][-1], f["fit"][-1], label, dx=8)
    V.note(ax, 158, 6460, "line: least-squares fit per species\nband: its 95 % confidence interval")
    ax.set_xlim(156, 235); ax.set_xticks([170, 190, 210, 230])
    ax.set_ylim(2500, 6500); ax.set_yticks([3000, 4000, 5000, 6000])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlabel("flipper length, mm")
    V.panel(ax, unit="body mass, g")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="scatter plot with fit lines and confidence bands", medium="screen",
            tool="matplotlib", data="Palmer penguins, Gorman, Williams and Fraser (2014), 342 birds with complete measurements",
            script=rel(__file__),
            alt=(f"Scatter of body mass against flipper length for {len(P)} penguins. Adelie and Chinstrap overlap at short flippers "
                 f"and low mass, Gentoo sit apart at long flippers and high mass. Fitted slopes are {FITS['Adelie']['slope']:.0f}, "
                 f"{FITS['Chinstrap']['slope']:.0f} and {FITS['Gentoo']['slope']:.0f} g per mm."))

for mode in MODES:
    save(draw(vellum.use(mode)), "science", "penguins_scatter", mode, meta=META)
