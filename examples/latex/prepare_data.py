"""prepare_data.py: the data and the computed numbers of the LaTeX examples, written into examples/latex/data/.

    vellum_sizes.tex      type sizes and mark widths from style/vellum.json, so no .tex file retypes them
    co2_annual.dat        annual mean CO2 at Mauna Loa, 1959-2019, from data/co2-concentration.csv
    co2_macros.tex        every number the CO2 figure states (years, rise, last value, the year 350 ppm was passed)
    landscape_macros.tex  the two peaks and the saddle of the shared landscape, and the contour levels
    landscape_contours.dat  the seven contour lines of the landscape, for the floor of the 3D panel
    enrich_*.dat, enrich_macros.tex  the Rosenzweig-MacArthur model: direction fields, orbits, the bifurcation in K
    ricker_*.dat, ricker_macros.tex  the Ricker map: attractor points, Lyapunov exponent and three time series
    turtle_*.dat, turtle_macros.tex  the loggerhead stage model: elasticities and the survival scenarios

build.py runs it before compiling; it also runs alone: python examples/latex/prepare_data.py
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
from _common import REPO, STYLE, load_csv, landscape, LANDSCAPE_DOMAIN   # noqa: E402
import numpy as np                                                         # noqa: E402
import contourpy                                                           # noqa: E402
from scipy.optimize import brentq, minimize, root                          # noqa: E402
from scipy.integrate import solve_ivp                                      # noqa: E402

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


def table(name, header, rows, fmt="{:.4f}"):
    """A whitespace table for pgfplots."""
    write(name, header + "\n" + "".join(" ".join(fmt.format(v) for v in r) + "\n" for r in rows))


# ---- the paradox of enrichment: dN/dt = N(1 - N/K) - NP/(1 + N), dP/dt = b NP/(1 + N) - dP (Rosenzweig 1971)
EN_B, EN_D = 0.5, 0.2                    # conversion and predator death; the predator's equilibrium prey is d/(b - d)
EN_KA, EN_KB = 2.0, 3.0                  # the carrying capacities of panels a and b
EN_N, EN_P = 3.0, 2.4                    # the phase planes span N in [0, 3] and P in [0, 2.4]


def enrichment():
    """Two phase planes (direction field, prey nullcline, orbit) and the predator's equilibrium and cycle range against K.
    The equilibrium prey density N* = d/(b - d) does not depend on K; the hump of the prey nullcline is at (K - 1)/2,
    so the equilibrium turns unstable (a Hopf bifurcation) when K passes 1 + 2N*."""
    b, d = EN_B, EN_D
    ns = d / (b - d); kh = 1 + 2 * ns
    pstar = lambda K: (1 - ns / K) * (1 + ns)

    def rhs(t, z, K):
        N, P = z; f = N * P / (1 + N)
        return [N * (1 - N / K) - f, b * f - d * P]

    def orbit(K, z0, t0, t1, n, tol=1e-10):
        s = solve_ivp(rhs, (0, t1), z0, args=(K,), rtol=tol, atol=tol / 100, t_eval=np.linspace(t0, t1, n))
        return s.y.T

    # direction fields: arrows of one length on the page, whatever the speed, on a 12 x 10 grid
    for tag, K in (("a", EN_KA), ("b", EN_KB)):
        rows = []
        for N in np.linspace(0.125, EN_N - 0.125, 12):
            for P in np.linspace(0.12, EN_P - 0.12, 10):
                u, v = rhs(0, (N, P), K)
                su, sv = u / EN_N, v / EN_P; L = np.hypot(su, sv)
                if L > 0: rows.append((N, P, 0.042 * su / L * EN_N, 0.042 * sv / L * EN_P))
        table(f"enrich_field_{tag}.dat", "N P u v", rows)
        table(f"enrich_null_{tag}.dat", "N P", [(N, (1 - N / K) * (1 + N)) for N in np.linspace(0, K, 120)])
    cyc = orbit(EN_KB, [ns, pstar(EN_KB)], 3000, 3060, 1200)            # long after the transient: the limit cycle
    table("enrich_orbit_a.dat", "N P", orbit(EN_KA, [1.85, 0.3], 0, 140, 1400))
    table("enrich_orbit_b.dat", "N P", orbit(EN_KB, [ns + 0.04, pstar(EN_KB)], 0, 150, 1500))
    table("enrich_cycle_b.dat", "N P", cyc)
    # the bifurcation diagram in K: the equilibrium (stable up to the Hopf point) and the range of the predator's cycle
    Ks = np.linspace(0.3, 4.5, 211)
    table("enrich_eq_stable.dat", "K P", [(K, max(pstar(K), 0)) for K in Ks if K < kh] + [(kh, pstar(kh))])
    table("enrich_eq_unstable.dat", "K P", [(kh, pstar(kh))] + [(K, pstar(K)) for K in Ks if K > kh])
    # walked down from K = 4.5, each orbit starting on the previous cycle, so it needs no long transient
    env, z = [], [ns, pstar(4.5) * 1.5]
    for K in np.linspace(4.5, kh + 0.02, 90):
        o = orbit(K, z, 900, 1300, 4000, tol=1e-8)
        env.append((K, o[:, 1].min(), o[:, 1].max())); z = o[-1]
    env = [(kh, pstar(kh), pstar(kh))] + env[::-1]
    table("enrich_cycle_range.dat", "K lo hi", env)
    table("enrich_cycle_band.dat", "K P", [(K, hi) for K, lo, hi in env] + [(K, lo) for K, lo, hi in env[::-1]])
    write("enrich_macros.tex", "% written by prepare_data.py: the Rosenzweig-MacArthur model\n" + macros(dict(
        enB=f"{b:g}", enD=f"{d:g}", enKa=f"{EN_KA:g}", enKb=f"{EN_KB:g}", enNstar=f"{ns:.2f}", enKh=f"{kh:.2f}",
        enPa=f"{pstar(EN_KA):.2f}", enPb=f"{pstar(EN_KB):.2f}", enPh=f"{pstar(kh):.2f}",
        enCycLo=f"{cyc[:, 1].min():.2f}", enCycHi=f"{cyc[:, 1].max():.2f}",
        enFold=f"{cyc[:, 1].max() / cyc[:, 1].min():.1f}", enHiK=f"{env[-1][2]:.2f}", enLoK=f"{env[-1][1]:.2f}")))


# ---- the Ricker map N(t+1) = N(t) exp(r (1 - N(t))) (Ricker 1954; May 1976)
RK_R = (1.6, 3.6)                        # the range of r on the diagram
RK_SERIES = (1.8, 2.4, 3.0)              # the three time series beside it


def ricker():
    """The attractor at each r (after 600 steps, the next 200, merged where two points fall within 1/400 on the N axis,
    so a periodic window costs a handful of points), the Lyapunov exponent, its first positive r, and three series."""
    f = lambda x, r: x * np.exp(r * (1 - x))
    lyap_step = lambda x, r: np.log(np.abs(np.exp(r * (1 - x)) * (1 - r * x)) + 1e-300)
    rs = np.linspace(*RK_R, 560)
    x = np.full(rs.shape, 0.3)
    for _ in range(600): x = f(x, rs)
    pts = set()
    for _ in range(200):
        x = f(x, rs)
        pts.update((round(r, 5), round(v * 400) / 400) for r, v in zip(rs, x))
    table("ricker_points.dat", "r N", sorted(pts))
    rl = np.linspace(*RK_R, 1400)
    x = np.full(rl.shape, 0.3); acc = np.zeros_like(rl)
    for _ in range(500): x = f(x, rl)
    for _ in range(4000): acc += lyap_step(x, rl); x = f(x, rl)
    lam = np.maximum(acc / 4000, -1.6)           # superstable points go to minus infinity; the axis stops at -1.6
    table("ricker_lyapunov.dat", "r lam pos neg", [(r, l, max(l, 0), min(l, 0)) for r, l in zip(rl, lam)])
    fine = np.linspace(2.6, 2.75, 1501)
    x = np.full(fine.shape, 0.3); acc = np.zeros_like(fine)
    for _ in range(2000): x = f(x, fine)
    for _ in range(20000): acc += lyap_step(x, fine); x = f(x, fine)
    onset = fine[np.argmax(acc > 0)]
    for k, r in enumerate(RK_SERIES):
        v = [0.3]
        for _ in range(40): v.append(f(v[-1], r))
        table(f"ricker_series_{k}.dat", "t N", list(enumerate(v)))
    write("ricker_macros.tex", "% written by prepare_data.py: the Ricker map\n" + macros(dict(
        rkOnset=f"{onset:.2f}", rkSa=f"{RK_SERIES[0]:.1f}", rkSb=f"{RK_SERIES[1]:.1f}", rkSc=f"{RK_SERIES[2]:.1f}")))


# ---- the loggerhead stage model (Crouse, Crowder and Caswell 1987)
def turtle():
    """lambda and the elasticity of each matrix entry (Caswell 2001: e = a s / lambda, s = v w' / <v, w>), summed by stage
    and kind; and lambda as the annual survival of one stage is raised from its value to 1, its split between staying
    and growing kept."""
    A = np.zeros((7, 7)); kind = {}
    for r in load_csv(os.path.join("ecology", "loggerhead_crouse1987.csv")):
        i, j = int(r["to"]) - 1, int(r["from"]) - 1
        A[i, j] = float(r["rate"]); kind[(i, j)] = r["type"]
    lam_of = lambda M: max(np.linalg.eigvals(M).real)
    w, V = np.linalg.eig(A); k = np.argmax(w.real); lam = w[k].real; right = np.abs(V[:, k].real)
    w2, U = np.linalg.eig(A.T); left = np.abs(U[:, np.argmax(w2.real)].real)
    E = np.outer(left, right) / (left @ right) * A / lam
    L = "abcdefg"
    macro = dict(tuLambda=f"{lam:.3f}", tuDecline=f"{100 * (1 - lam):.1f}")
    for (i, j), kd in kind.items():               # \tuE<from><to>: elasticity, \tuA<from><to>: rate, stages as letters
        macro[f"tuE{L[j]}{L[i]}"] = f"{E[i, j]:.3f}"; macro[f"tuA{L[j]}{L[i]}"] = f"{A[i, j]:g}"
    by = lambda s, kd: sum(E[i, j] for (i, j), k2 in kind.items() if j == s and k2 == kd)
    table("turtle_elasticity.dat", "stage stasis growth fecundity",
          [(s + 1, by(s, "stasis"), by(s, "growth"), by(s, "fecundity")) for s in range(7)])
    F = np.zeros_like(A); F[0] = A[0]; S = A - F
    for s in (0, 1, 2, 3, 6):
        surv = S[:, s].sum(); xmax = 1 / surv - 1

        def lam_x(x, s=s):
            M = A.copy(); M[1:, s] = S[1:, s] * (1 + x); return lam_of(M)
        table(f"turtle_scenario_{s + 1}.dat", "surv lam", [(surv * (1 + x), lam_x(x)) for x in np.linspace(0, xmax, 60)])
        macro[f"tuMax{L[s]}"] = f"{lam_x(xmax):.3f}"; macro[f"tuXmax{L[s]}"] = f"{100 * xmax:.0f}"
        macro[f"tuSurv{L[s]}"] = f"{surv:.4f}"
        macro[f"tuNeed{L[s]}"] = f"{100 * brentq(lambda x: lam_x(x) - 1, 0, xmax):.0f}" if lam_x(xmax) > 1 else "none"
    write("turtle_macros.tex", "% written by prepare_data.py from data/ecology/loggerhead_crouse1987.csv\n" + macros(macro))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sizes(); co2(); landscape_numbers(); enrichment(); ricker(); turtle()
    print("written", ", ".join(sorted(os.listdir(OUT))))
