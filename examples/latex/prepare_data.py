"""prepare_data.py: the data and the computed numbers of the LaTeX examples, written into examples/latex/data/.

    vellum_sizes.tex      type sizes and mark widths from style/vellum.json, so no .tex file retypes them
    co2_annual.dat        annual mean CO2 at Mauna Loa, 1959-2019, from data/co2-concentration.csv
    co2_macros.tex        every number the CO2 figure states (years, rise, last value, the year 350 ppm was passed)
    landscape_macros.tex  the two peaks and the saddle of the shared landscape, and the contour levels
    landscape_contours.dat  the seven contour lines of the landscape, for the floor of the 3D panel

build.py runs it before compiling; it also runs alone: python examples/latex/prepare_data.py
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
from _common import REPO, STYLE, load_csv, landscape, LANDSCAPE_DOMAIN   # noqa: E402
import numpy as np                                                         # noqa: E402
import contourpy                                                           # noqa: E402
from scipy.optimize import minimize, root                                  # noqa: E402

OUT = os.path.join(REPO, "examples", "latex", "data")


def write(name, text):
    open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(text)


def macros(d):
    return "".join(f"\\def\\{k}{{{v}}}\n" for k, v in d.items())


def sizes():
    """Type sizes (pt) with a 1.25 leading, and the marks of vellum.json as TeX dimensions."""
    S = json.load(open(os.path.join(STYLE, "vellum.json"), encoding="utf-8"))
    names = dict(title="Title", subtitle="Subtitle", axis_label="Axis", tick="Tick", unit_line="Unit", footer="Footer")
    d = {}
    for key, nm in names.items():
        d[f"vSize{nm}"] = f"{S['sizes'][key]:g}"; d[f"vSkip{nm}"] = f"{1.25 * S['sizes'][key]:g}"
    m = S["marks"]
    d.update(vLine=f"{m['line_pt']:g}pt", vThin=f"{m['thin_line_pt']:g}pt", vRing=f"{m['ring_pt']:g}pt",
             vMarker=f"{np.sqrt(m['marker_pt2']):.2f}pt",             # 28 pt^2 is a dot 5.3 pt across, as in matplotlib
             vGridW=f"{m['grid_pt']:g}pt", vBandAlpha=f"{m['band_alpha']:g}",
             vDotOn=f"{m['dotted'][0] * m['thin_line_pt']:g}pt", vDotOff=f"{m['dotted'][1] * m['thin_line_pt']:g}pt")
    write("vellum_sizes.tex", "% written by prepare_data.py from style/vellum.json\n" + macros(d))


def co2():
    """Annual means of the seasonally adjusted monthly values. 1964 lacks three months, so the raw values would bias its
    mean by the seasonal cycle; the adjusted series does not. 1958 and 2020 are partial years and are left out."""
    by_year = defaultdict(list)
    for r in load_csv("co2-concentration.csv"):
        by_year[int(r["Date"][:4])].append(float(r["adjusted CO2"]))
    years = [y for y in sorted(by_year) if len(by_year[y]) >= 9 and 1958 < y < 2020]
    mean = np.array([np.mean(by_year[y]) for y in years])
    rises = np.diff(mean)
    assert np.all(rises > 0), "the claim 'rose every year' no longer holds"
    write("co2_annual.dat", "year ppm\n" + "".join(f"{y} {v:.3f}\n" for y, v in zip(years, mean)))
    passed = years[int(np.argmax(mean > 350))]
    write("co2_macros.tex", "% written by prepare_data.py from data/co2-concentration.csv\n" + macros(dict(
        coFirstYear=years[0], coLastYear=years[-1], coFirst=f"{mean[0]:.1f}", coLast=f"{mean[-1]:.1f}",
        coRise=f"{mean[-1] - mean[0]:.1f}", coRises=int(np.sum(rises > 0)), coSpan=years[-1] - years[0],
        coSmallestRise=f"{rises.min():.2f}", coPassed=passed)))


def landscape_numbers():
    """The two peaks (maxima from the two centres), the saddle between them (where the gradient vanishes), and the seven
    contour lines as x y segments separated by blank lines. The 3D panel draws these on its floor: pgfplots' contour lua
    applies a z filter before it contours, so it cannot project its own lines onto the floor."""
    f = lambda p: landscape(p[0], p[1])
    peaks = [minimize(lambda p: -f(p), x0).x for x0 in ((0.9, 0.7), (-0.8, -0.9))]
    grad = lambda p, h=1e-6: [(f(p + [h, 0]) - f(p - [h, 0])) / (2 * h), (f(p + [0, h]) - f(p - [0, h])) / (2 * h)]
    saddle = root(grad, np.mean(peaks, axis=0)).x
    lo, hi = LANDSCAPE_DOMAIN
    g = np.linspace(lo, hi, 401); W = landscape(*np.meshgrid(g, g))
    levels = np.linspace(0, round(W.max(), 1), 9)[1:-1]                    # seven contour levels, as the 3D note asks
    write("landscape_macros.tex", "% written by prepare_data.py from the landscape in examples/python/_common.py\n" + macros(dict(
        lsHigh=f"{f(peaks[0]):.2f}", lsHighX=f"{peaks[0][0]:.2f}", lsHighY=f"{peaks[0][1]:.2f}",
        lsLow=f"{f(peaks[1]):.2f}", lsLowX=f"{peaks[1][0]:.2f}", lsLowY=f"{peaks[1][1]:.2f}",
        lsSaddle=f"{f(saddle):.2f}", lsSaddleX=f"{saddle[0]:.2f}", lsSaddleY=f"{saddle[1]:.2f}",
        lsMin=f"{W.min():.4f}", lsMax=f"{W.max():.4f}", lsFloor=f"{W.min() - 0.06 * np.ptp(W):.4f}",
        lsLevels=",".join(f"{v:g}" for v in levels))))
    gen = contourpy.contour_generator(g, g, W)
    write("landscape_contours.dat", "x y\n" + "\n".join(
        "".join(f"{x:.4f} {y:.4f}\n" for x, y in seg) for v in levels for seg in gen.lines(v)))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sizes(); co2(); landscape_numbers()
    print("written", ", ".join(sorted(os.listdir(OUT))))
