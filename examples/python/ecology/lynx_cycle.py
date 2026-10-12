"""lynx_cycle.py: a century of Canadian lynx cycles as a six-panel composite.

a  the 114-year record (log scale) with every complete peak and the interval to the next one
b  the periodogram of log10 counts, as the share of variance per Fourier frequency, with the AR(2) spectrum over it
c  three estimates of the period side by side: peak to peak, the periodogram maximum, the AR(2) quasi-period
d  the lag-2 phase portrait, log N(t) against log N(t − 2), coloured by year: the cycle is a loop
e  the AR(2) coefficients in the stationarity triangle, with the curve that separates cycles from no cycles and lines
   of equal period; the full-record estimate with its 95 % confidence ellipse and the two half-century estimates
f  the model trained on 1821–1914 and forecast for the 20 held-out years, 1915–1934, with 50 % and 95 % bands

Model: log10 N(t) = c + φ1 log10 N(t − 1) + φ2 log10 N(t − 2) + ε, fitted by least squares (Moran 1953). A statistical
model of the counts, not a mechanistic predator–prey model.
Data: data/ecology/lynx.csv (datasets::lynx in R; Elton and Nicholson 1942), exported by export_data.R.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco import *
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse, Polygon
from matplotlib.ticker import FixedLocator, NullLocator

SOURCE = "Data: Hudson's Bay Company lynx returns, 1821–1934 (Elton and Nicholson 1942), R datasets::lynx"
T = table("lynx.csv")
YR = T["year"].astype(int); N = T["trapped"]; X = np.log10(N); n = len(X)

# ---- peaks: a year that is the maximum of the seven years around it; the window must fit inside the record
PK = np.array([i for i in range(3, n - 3) if N[i] == N[i - 3:i + 4].max()])
GAPS = np.diff(YR[PK]); P_MEAN = GAPS.mean()
P_CI = P_MEAN + np.array([-1, 1]) * 2.262 * GAPS.std(ddof=1) / np.sqrt(len(GAPS))     # t(0.975, 9) = 2.262
END_RISING = N[-1] > N[-2]                                                             # 1934 is still rising: no peak yet


# ---- periodogram of the centred log counts, as the share of the variance at each Fourier frequency
xc = X - X.mean(); F = np.fft.rfft(xc)
POW = 2 * np.abs(F[1:]) ** 2 / n ** 2; FREQ = np.arange(1, len(F)) / n
if n % 2 == 0: POW[-1] /= 2                                                             # the Nyquist term counts once
SHARE = POW / xc.var(); K = int(np.argmax(SHARE)); P_SPEC = 1 / FREQ[K]
P_SPEC_RANGE = (n / (K + 1 + 0.5), n / (K + 1 - 0.5))                                 # half a frequency bin each side


# ---- AR(2) by least squares
def ar2(x):
    X_ = np.column_stack([np.ones(len(x) - 2), x[1:-1], x[:-2]]); y = x[2:]
    b = np.linalg.lstsq(X_, y, rcond=None)[0]; e = y - X_ @ b; s2 = e @ e / (len(y) - 3)
    return b, s2, s2 * np.linalg.inv(X_.T @ X_), 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))


def period(p1, p2):
    """Quasi-period of an AR(2) with complex roots: 2π over the argument of the roots."""
    return 2 * np.pi / np.arccos(p1 / (2 * np.sqrt(-p2)))


B, S2, COV, R2 = ar2(X)
P_AR = period(B[1], B[2]); MOD = np.sqrt(-B[2])
rng = np.random.default_rng(1934)
draws = rng.multivariate_normal(B, COV, 20000); ok = draws[:, 1] ** 2 + 4 * draws[:, 2] < 0
P_AR_CI = np.percentile(period(draws[ok, 1], draws[ok, 2]), [2.5, 97.5])
HALVES = [(f"{YR[s][0]}–{str(YR[s][-1])[2:]}", ar2(X[s])[0]) for s in (slice(0, n // 2), slice(n // 2, None))]


def ar_spectrum(f, b, s2):
    """Spectral density of the AR(2) on (0, 1/2], as a share of its variance per Fourier bin of width 1/n."""
    S = s2 / np.abs(1 - b[1] * np.exp(-2j * np.pi * f) - b[2] * np.exp(-4j * np.pi * f)) ** 2
    ff = np.linspace(1e-4, 0.5, 20001); tot = np.trapezoid(2 * s2 / np.abs(1 - b[1] * np.exp(-2j * np.pi * ff) - b[2] * np.exp(-4j * np.pi * ff)) ** 2, ff)
    return 2 * S / n / tot


# ---- out-of-sample forecast: train to 1914, forecast the 20 years after with the psi-weight variance
CUT = int(np.searchsorted(YR, 1914)) + 1
BT, S2T, _, _ = ar2(X[:CUT]); H = n - CUT
m = list(X[:CUT])
for _ in range(H): m.append(BT[0] + BT[1] * m[-1] + BT[2] * m[-2])
FC = np.array(m[CUT:])
psi = [1.0, BT[1]]
for _ in range(2, H): psi.append(BT[1] * psi[-1] + BT[2] * psi[-2])
FSD = np.sqrt(S2T * np.cumsum(np.array(psi) ** 2))
INSIDE = int((np.abs(X[CUT:] - FC) < 1.96 * FSD).sum())
FC_PEAK = YR[CUT:][np.argmax(FC[3:]) + 3]; OBS_PEAK = YR[CUT:][np.argmax(X[CUT:][3:]) + 3]   # the peak after the trough
FC_TROUGH = YR[CUT:][np.argmin(FC)]; OBS_TROUGH = YR[CUT:][np.argmin(X[CUT:])]

# ---- the claims, checked
assert len(PK) == 11 and round(P_MEAN, 1) == 9.7, (len(PK), P_MEAN)
assert round(P_SPEC, 1) == 9.5 and round(P_AR, 1) == 9.8, (P_SPEC, P_AR)
assert B[1] ** 2 + 4 * B[2] < 0 and abs(B[2]) < 1                                       # complex roots, stationary: a damped cycle
assert all(h[1][1] ** 2 + 4 * h[1][2] < 0 for h in HALVES)                              # cyclic in both halves
assert INSIDE == H

TITLE = f"Canadian lynx peaked every {P_MEAN:.1f} years for a century, a rhythm a two-year memory reproduces"
SUB = (f"Lynx trapped per year, {YR[0]}–{YR[-1]} · {len(PK)} complete peaks, {YR[PK][0]}–{YR[PK][-1]} · "
       f"AR(2) on log₁₀ counts: φ₁ = {B[1]:.2f}, φ₂ = {minus(f'{B[2]:.2f}')}, R² = {R2:.2f}")


def unit_ticks(ax, axis, ticks):
    """Log axis labelled in counts."""
    loc = FixedLocator(np.log10(ticks)); lab = [f"{t:,}".replace(",", " ") for t in ticks]
    if axis == "x": ax.xaxis.set_major_locator(loc); ax.set_xticklabels(lab)
    else: ax.yaxis.set_major_locator(loc); ax.set_yticklabels(lab)


def panel_a(V, ax):
    data = V.tone("terracotta")
    ax.axvspan(YR[CUT] - 0.5, YR[-1] + 0.5, color=V.card, lw=0, zorder=0)
    text(V, ax, (YR[CUT] + YR[-1]) / 2, np.log10(25), "held out in f", color=V.muted, ha="center", va="bottom")
    ax.fill_between(YR, np.log10(20), X, color=V.tint("terracotta"), alpha=0.35, lw=0, zorder=1)
    ax.plot(YR, X, color=data, lw=1.3, zorder=3)
    V.dot(ax, YR[PK], X[PK], V.deep("terracotta"), s=26, z=5, ring=1.0)
    # the rhythm ruler: a bracket from peak to peak above the record, with the interval in years
    yb = np.log10(11500)
    for i, (a, b) in enumerate(zip(YR[PK][:-1], YR[PK][1:])):
        ax.plot([a + 0.6, a + 0.6, b - 0.6, b - 0.6], [yb - 0.06, yb, yb, yb - 0.06], color=V.rule, lw=0.6, zorder=2,
                solid_capstyle="butt")
        text(V, ax, (a + b) / 2, yb + 0.05, f"{b - a}", color=V.ink if b - a != round(P_MEAN) else V.secondary,
             ha="center", va="bottom", size=V.sz["annotation"])
    ax.annotate(f"{YR[PK][np.argmax(N[PK])]}: {int(N[PK].max()):,} lynx".replace(",", " "),
                (YR[PK][np.argmax(N[PK])], X[PK].max()), xytext=(-7, 0), textcoords="offset points", ha="right", va="center",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    lo = int(np.argmin(N))
    ax.annotate(f"{YR[lo]}: {int(N[lo])}", (YR[lo], X[lo]), xytext=(5, -1), textcoords="offset points", ha="left", va="top",
                fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V))
    if END_RISING:                                                                       # the open interval after the last peak
        ax.plot([YR[PK][-1] + 0.6, YR[PK][-1] + 0.6, YR[-1] + 0.4], [yb - 0.06, yb, yb], color=V.rule, lw=0.6, ls=V.dotted,
                solid_capstyle="butt", zorder=2)
        text(V, ax, (YR[PK][-1] + YR[-1]) / 2 + 0.5, yb + 0.05, "≥ 9", color=V.muted, ha="center",
             va="bottom")
    ax.set_xlim(YR[0] - 1, YR[-1] + 1); ax.set_xticks(range(1830, 1935, 10))
    ax.set_ylim(np.log10(20), np.log10(26000)); unit_ticks(ax, "y", [30, 100, 300, 1000, 3000])
    head(V, ax, "a", f"{len(PK)} complete peaks, {int(GAPS.min())} to {int(GAPS.max())} years apart",
         unit="lynx trapped per year, log scale · brackets: years from one peak to the next; the record ends while still rising")


def panel_b(V, ax):
    per = 1 / FREQ
    ax.vlines(per, 0, SHARE * 100, color=V.rule, lw=1.1, zorder=2)
    ax.vlines(per[K], 0, SHARE[K] * 100, color=V.tone("terracotta"), lw=2.0, zorder=3)
    ff = np.linspace(1 / 120, 0.5, 2000)
    ax.plot(1 / ff, ar_spectrum(ff, B, S2) * 100, color=V.tone("teal"), lw=1.3, zorder=4)
    ax.annotate(f"{P_SPEC:.1f} years:\n{SHARE[K] * 100:.0f} % of the\nvariance", (per[K], SHARE[K] * 100), xytext=(6, -1),
                textcoords="offset points", ha="left", va="top", fontsize=V.sz["annotation"], color=V.ink, path_effects=halo(V),
                linespacing=1.05)
    pk_ar = 1 / ff[np.argmax(ar_spectrum(ff, B, S2))]
    ax.annotate("AR(2) model", (7.2, ar_spectrum(np.array([1 / 7.2]), B, S2)[0] * 100), xytext=(-12, 10),
                textcoords="offset points", ha="right", va="bottom", fontsize=V.sz["annotation"], color=V.ink,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=1, relpos=(1, 0.3)))
    j = int(np.argmin(np.abs(per - 38)))                                                  # a long, minor period of the data
    ax.annotate("other periods", (per[j], SHARE[j] * 100), xytext=(0, 18), textcoords="offset points", ha="center",
                va="bottom", fontsize=V.sz["annotation"], color=V.muted,
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=2))
    ax.set_xscale("log"); ax.set_xlim(2, 120); ax.xaxis.set_major_locator(FixedLocator([2, 5, 10, 20, 50, 100]))
    ax.xaxis.set_minor_locator(NullLocator()); ax.set_xticklabels(["2", "5", "10", "20", "50", "100"])
    ax.set_ylim(0, 66); ax.set_yticks([0, 20, 40, 60])
    ax.set_xlabel("period, years")
    head(V, ax, "b", f"One period holds {SHARE[K] * 100:.0f} % of the variance", unit="share of variance, %")
    return pk_ar


def panel_c(V, ax, pk_ar):
    rows = [("peak to peak", P_MEAN, P_CI, "terracotta"), ("periodogram", P_SPEC, P_SPEC_RANGE, "terracotta"),
            ("AR(2) model", P_AR, P_AR_CI, "teal")]
    vals, cnt = np.unique(GAPS, return_counts=True)
    for v, c in zip(vals, cnt):                                                           # the ten intervals as dot stacks
        ys = 0.28 - 0.17 * np.arange(c)
        ax.scatter(np.full(c, v), ys, s=13, color=V.tint("terracotta"), edgecolor=V.surface, lw=0.6, zorder=3)
    ax.axvline(P_MEAN, color=V.tone("ochre"), lw=V.thin, ls=V.dotted, zorder=1)
    for i, (name, v, ci, fam) in enumerate(rows, start=1):
        ax.plot(ci, [i, i], color=V.secondary, lw=0.8, zorder=2, solid_capstyle="butt")
        V.dot(ax, v, i, V.tone(fam), s=30, z=4, ring=1.0)
        text(V, ax, ci[1] + 0.15, i, f"{v:.1f}", ha="left", va="center")
    ax.set_yticks(range(4)); ax.set_yticklabels([f"{len(GAPS)} intervals"] + [r[0] for r in rows]); ax.set_ylim(3.5, -0.5)
    ax.tick_params(axis="y", labelcolor=V.secondary)
    ax.set_xlim(8.3, 12.7); ax.set_xticks([9, 10, 11, 12]); ax.set_xlabel("period, years")
    ax.grid(False)
    head(V, ax, "c", "Three estimates, one period", unit="estimate with 95 % interval")


def panel_d(V, fig, ax, cax):
    x0, x1 = X[:-2], X[2:]
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("lagoon_cut", V.gradient("lagoon", 256)[64:])    # no stop too pale for the page
    norm = plt.Normalize(YR[0], YR[-1])
    pts = np.column_stack([x0, x1]); seg = np.stack([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(seg, cmap=cm, norm=norm, lw=0.7, zorder=2, alpha=0.9); lc.set_array(YR[2:-1] + 0.5); ax.add_collection(lc)
    sc = ax.scatter(x0, x1, c=YR[2:], cmap=cm, norm=norm, s=7, edgecolor="none", zorder=3)
    ax.plot([1.4, 4.0], [1.4, 4.0], color=V.rule, lw=0.6, ls=V.dotted, zorder=1)
    # direction of travel, once, on a long segment of the loop
    j = int(np.argmax(np.hypot(*np.diff(pts, axis=0).T)))
    ax.annotate("", pts[j + 1], xytext=pts[j], arrowprops=dict(arrowstyle="-|>", color=V.ink, lw=0.8,
                                                                 mutation_scale=8, shrinkA=8, shrinkB=8), zorder=4)
    text(V, ax, np.log10(36), np.log10(8200), "clockwise:\nrise, crash,\nrecover", color=V.muted, va="top", linespacing=1.0)
    for a in ("x", "y"): unit_ticks(ax, a, [100, 1000])
    ax.set_xlim(np.log10(30), np.log10(9000)); ax.set_ylim(np.log10(30), np.log10(9000))
    ax.set_xlabel("lynx two years before")
    ax.grid(True, axis="both")
    head(V, ax, "d", "The same loop for a century", unit="lynx in year t, log scale")
    cb = fig.colorbar(sc, cax=cax); cb.outline.set_visible(False)
    cb.ax.tick_params(size=0, labelsize=V.sz["unit_line"], colors=V.muted); cb.set_ticks([1830, 1880, 1930])
    cax.set_title("year", fontsize=V.sz["unit_line"], color=V.muted, loc="left", pad=4, fontweight="normal")
    return cb


def panel_e(V, ax):
    tri = np.array([[-2, -1], [2, -1], [0, 1]])
    ax.add_patch(Polygon(tri, closed=True, facecolor=V.card, edgecolor=V.rule, lw=0.7, zorder=0))
    p1 = np.linspace(-2, 2, 400)
    ax.fill_between(p1, -1, -p1 ** 2 / 4, color=V.tint("teal"), alpha=0.45, lw=0, zorder=1)
    ax.plot(p1, -p1 ** 2 / 4, color=V.tone("teal"), lw=0.8, zorder=2)
    p2 = np.linspace(-1, 0, 200)
    iso = V.surface if V.mode == "light" else V.rule
    for Tp in (4, 6, 10, 20):
        ax.plot(2 * np.cos(2 * np.pi / Tp) * np.sqrt(-p2), p2, color=iso, lw=0.7, zorder=2)
        text(V, ax, 2 * np.cos(2 * np.pi / Tp) + 0.05, -0.97, f"{Tp}", color=V.secondary, ha="left", va="bottom",
             size=V.sz["unit_line"])
    text(V, ax, -0.06, -0.97, "period, years", color=V.secondary, ha="right", va="bottom", size=V.sz["unit_line"])
    text(V, ax, -0.55, -0.6, "complex roots:\ndamped cycles", color=V.deep("teal"), ha="center", va="center", linespacing=1.0)
    text(V, ax, 0.0, 0.40, "real roots:\nno cycles", color=V.muted, ha="center", va="center", linespacing=1.0)
    # the full-record estimate with its 95 % ellipse (chi-square, 2 df) and the two half-century estimates
    ev, evec = np.linalg.eigh(COV[1:, 1:]); k = np.sqrt(5.991)
    ang = np.degrees(np.arctan2(evec[1, 1], evec[0, 1]))
    ax.add_patch(Ellipse(B[1:], 2 * k * np.sqrt(ev[1]), 2 * k * np.sqrt(ev[0]), angle=ang, facecolor="none",
                         edgecolor=V.tone("terracotta"), lw=0.8, zorder=4))
    for name, b in HALVES:
        ax.scatter(*b[1:], s=14, facecolor=V.surface, edgecolor=V.tone("terracotta"), lw=0.9, zorder=5)
    V.dot(ax, *B[1:], V.tone("terracotta"), s=24, z=6, ring=1.0)
    ax.annotate(f"lynx, {YR[0]}–{YR[-1]},\n95 % ellipse;\nopen: each half", B[1:], xytext=(1.02, 0.62), textcoords="data",
                ha="left", va="top", fontsize=V.sz["annotation"], color=V.ink, linespacing=1.0, path_effects=halo(V),
                arrowprops=dict(arrowstyle="-", color=V.muted, lw=0.5, shrinkB=6, relpos=(0.15, 0)))
    ax.set_xlim(-2.1, 2.1); ax.set_ylim(-1.0, 1.05); ax.set_xticks([-2, -1, 0, 1, 2]); ax.set_yticks([-1, 0, 1])
    ax.set_xticklabels([minus(t) for t in ("-2", "-1", "0", "1", "2")]); ax.set_yticklabels([minus("-1"), "0", "1"])
    ax.set_xlabel("φ₁, weight of last year")
    clean(ax, grid=False)
    head(V, ax, "e", "Lynx sit on the 10-year line", unit="φ₂, weight of two years ago")


def panel_f(V, ax):
    yrs = YR[CUT:]; lead = slice(CUT - 25, CUT)
    t = V.tone("teal")
    ax.fill_between(yrs, FC - 1.96 * FSD, FC + 1.96 * FSD, color=V.tint("teal"), alpha=0.35, lw=0, zorder=1)
    ax.fill_between(yrs, FC - 0.674 * FSD, FC + 0.674 * FSD, color=V.tint("teal"), alpha=0.8, lw=0, zorder=1)
    ax.plot(np.r_[YR[CUT - 1], yrs], np.r_[X[CUT - 1], FC], color=t, lw=1.3, zorder=3)
    ax.plot(YR[lead.start:], X[lead.start:], color=V.tone("terracotta"), lw=1.3, zorder=4)
    V.dot(ax, yrs, X[CUT:], V.tone("terracotta"), s=14, z=5, ring=0.8)
    ax.axvline(YR[CUT - 1] + 0.5, color=V.rule, lw=0.6, zorder=0)
    top = np.log10(26000)
    text(V, ax, YR[CUT - 1] + 0.1, top, "trained to 1914 ", color=V.muted, ha="right", va="top")
    text(V, ax, YR[CUT - 1] + 0.9, top, " forecast, with 50 % and 95 % bands", color=V.muted, ha="left", va="top")
    V.endlabel(ax, YR[-1], X[-1], "observed")
    V.endlabel(ax, YR[-1], FC[-1], "model mean")
    ax.set_xlim(YR[lead.start] - 0.5, YR[-1] + 0.5); ax.set_xticks([1890, 1900, 1910, 1920, 1930])
    ax.set_ylim(np.log10(25), top); unit_ticks(ax, "y", [30, 100, 300, 1000, 3000, 10000])
    head(V, ax, "f", f"Trained to 1914, it holds all {H} later years in its 95 % band", unit="lynx trapped per year, log scale")


def draw(V):
    fig = plt.figure(figsize=(7.2, 8.0))
    a = axes_in(fig, 0.62, 1.22, 6.42, 1.62)
    b = axes_in(fig, 0.42, 3.62, 1.82, 1.42)
    c = axes_in(fig, 3.12, 3.62, 1.42, 1.42)
    d = axes_in(fig, 5.12, 3.62, 1.42, 1.42); cax = axes_in(fig, 6.66, 3.72, 0.07, 1.0)
    e = axes_in(fig, 0.42, 5.88, 2.12, 1.42)
    f = axes_in(fig, 3.12, 5.88, 3.30, 1.42)
    panel_a(V, a); pk_ar = panel_b(V, b); panel_c(V, c, pk_ar); panel_d(V, fig, d, cax); panel_e(V, e); panel_f(V, f)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Six panels on Canadian lynx trappings, {YR[0]}–{YR[-1]}. a: the yearly record on a log scale with {len(PK)} complete "
       f"peaks from {YR[PK][0]} to {YR[PK][-1]}, {int(GAPS.min())} to {int(GAPS.max())} years apart, mean {P_MEAN:.1f}. "
       f"b: the periodogram; the {P_SPEC:.1f}-year period holds {SHARE[K] * 100:.0f} % of the variance of log counts. "
       f"c: peak-to-peak {P_MEAN:.1f} years ({P_CI[0]:.1f}–{P_CI[1]:.1f}), periodogram {P_SPEC:.1f}, AR(2) quasi-period {P_AR:.1f} "
       f"({P_AR_CI[0]:.1f}–{P_AR_CI[1]:.1f}). d: the lag-2 phase portrait is a clockwise loop. e: the AR(2) coefficients "
       f"φ₁ = {B[1]:.2f}, φ₂ = {minus(f'{B[2]:.2f}')} lie in the complex-root region on the 10-year line, in both half-centuries. "
       f"f: trained to 1914, the model's 95 % band holds all {H} held-out years.")

META = dict(title=TITLE, subtitle=SUB, kind="composite", form="six-panel composite: time series, periodogram, interval plot, "
            "phase portrait, parameter triangle, forecast", medium="paper", tool="matplotlib",
            data="Canadian lynx trappings 1821–1934, Elton and Nicholson (1942), via R datasets::lynx", script=rel(__file__), alt=ALT,
            note=(f"Peaks: years that are the maximum of the seven years around them, with the window inside the record "
                  f"(1934, the last year, is still rising and is not counted). AR(2) by least squares on log10 counts: "
                  f"c = {B[0]:.3f}, φ₁ = {B[1]:.3f} (se {np.sqrt(COV[1, 1]):.3f}), φ₂ = {B[2]:.3f} (se {np.sqrt(COV[2, 2]):.3f}), "
                  f"residual sd {np.sqrt(S2):.3f}, R² = {R2:.3f}; modulus of the roots {MOD:.3f}. Quasi-period interval from "
                  f"20 000 draws of the coefficients. Periodogram range: half a Fourier bin each side. Forecast from 1914 with "
                  f"psi-weight variance (coefficients of the 1821–1914 fit, φ₁ = {BT[1]:.2f}, φ₂ = {BT[2]:.2f}); forecast trough "
                  f"{FC_TROUGH}, observed {OBS_TROUGH}; forecast peak {FC_PEAK}, observed {OBS_PEAK}."))

if __name__ == "__main__":
    print(TITLE); print(META["note"])
    for mode in MODES:
        print(save(draw(vellum.use(mode)), "ecology", "lynx_cycle", mode, meta=META if mode == "light" else None))
