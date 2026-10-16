"""hexbin.py: life expectancy of every country in every year since 1950 as a two-dimensional density: hexagons counted and
shaded along one sequential gradient, empty cells left bare. Data: data/owid-life-expectancy.csv (UN WPP 2024 and others,
processed by Our World in Data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = ("UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), "
          "Riley (2005); processed by Our World in Data")
ROWS = [r for r in load_csv("owid-life-expectancy.csv") if r["Code"] and not r["Code"].startswith("OWID") and int(r["Year"]) >= 1950]
YR = np.array([int(r["Year"]) for r in ROWS], float); LE = np.array([float(r["Life expectancy"]) for r in ROWS])
sd = lambda a, b: LE[(YR >= a) & (YR <= b)].std()
SD50, SD20 = sd(1950, 1959), sd(2014, 2023)
M50, M20 = np.median(LE[YR <= 1959]), np.median(LE[YR >= 2014])

TITLE = f"Typical life expectancy rose {M20 - M50:.0f} years since 1950, and the spread fell {100 * (1 - SD20 / SD50):.0f} %"
SUB = f"Life expectancy at birth of {len(set(r['Code'] for r in ROWS))} countries, 1950–2023 · {len(ROWS):,} country-years · line: median"


def draw(V):
    fig, ax = plt.subplots(figsize=V.size("double_tall"))
    fig.subplots_adjust(left=0.07, right=0.89, top=0.80, bottom=0.12)
    hb = ax.hexbin(YR, LE, gridsize=(37, 16), extent=(1950, 2024, 20, 90), mincnt=1, cmap=V.cmap_gradient("lagoon"),
                   edgecolors=V.surface, linewidths=0.4, zorder=3)
    V.gradient_bar(fig, hb, ax, "country-years")
    years = np.arange(1950, 2024)
    med = [np.median(LE[YR == y]) for y in years]
    ax.plot(years, med, color=V.ink, lw=V.lw * 1.4, zorder=5)
    ax.annotate("the middle country", (2006, med[56]), xytext=(0, -30), textcoords="offset points", ha="center", va="top",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=[vellum.pe.withStroke(linewidth=2.5, foreground=V.surface)],
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5), zorder=6)
    ax.set_xlim(1948, 2025); ax.set_ylim(20, 90)
    ax.set_xticks([1950, 1970, 1990, 2010]); ax.set_yticks([30, 50, 70, 90]); ax.grid(False)
    V.panel(ax, unit="life expectancy at birth, years")
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="2D density (hexagonal bins)", medium="screen", tool="matplotlib",
            data="Life expectancy by country, UN WPP 2024 via Our World in Data, 1950–2023", script=rel(__file__),
            alt=(f"Hexagonal-bin density of life expectancy by year, 1950–2023. The median rose from {M50:.0f} in the 1950s to "
                 f"{M20:.0f} in 2014–2023, and the standard deviation across countries fell from {SD50:.0f} to {SD20:.0f} years."))

for mode in MODES:
    save(draw(vellum.use(mode)), "forms", "hexbin", mode, meta=META)
