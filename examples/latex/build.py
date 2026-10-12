"""build.py: compile every .tex in examples/latex/ (not subfolders) into its light and dark twin, rasterise each PDF
to a PNG about 2000 px wide, copy both into docs/figures/tools/ and record them in that group's manifest.json.

    python examples/latex/build.py

Runs prepare_data.py first (the .dat files and the macros of computed numbers). Needs lualatex (MiKTeX or TeX Live, with
fontspec, unicode-math, TeX Gyre Pagella, Lato, tikz and pgfplots) and pdftoppm (poppler; MiKTeX ships it). The style
package is found in style/ without copying it: MiKTeX takes --include-directory, TeX Live takes TEXINPUTS.
Each twin is one run: `lualatex <name>.tex` draws the light twin, `-jobname=<name>_dark` the dark one (vellum-twin.sty).
"""
import glob, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
from _common import FIGURES, STYLE, record, rel, stamp   # noqa: E402

GROUP = "tools"
OUT = os.path.join(FIGURES, GROUP)
WIDTH_PX = 2000


def numbers():
    """The macros prepare_data.py wrote (\\def\\name{value}), so the manifest quotes the same numbers as the figures."""
    d = {}
    for f in glob.glob(os.path.join(HERE, "data", "*.tex")):
        d.update(re.findall(r"\\def\\(\w+)\{([^}]*)\}", open(f, encoding="utf-8").read()))
    return d


def meta(name, n):
    """Gallery metadata of each figure; titles are the claims as typeset, with the computed numbers filled in."""
    M = {
        "tikz_pipeline": dict(
            title="Every colour is defined once, in vellum.json, and every style file derives from it",
            subtitle="how the files of Vellum are made · an arrow points from a file to what is made from it",
            form="TikZ diagram", medium="screen", tool="TikZ", data="the repository's own generators/ and style/ folders",
            alt="A left-to-right diagram: build_palettes.py searches OKLCH for the tone lightness and writes palettes.json; "
                "make_vellum_json.py turns it into vellum.json, the source of truth; make_assets.py generates vellum.mplstyle, "
                "vellum.R, vellum-colors.sty, vellum.css and vellum-office.tsv, and the hand-written vellum.py reads vellum.json "
                "at run time; the files feed matplotlib, ggplot2, pgfplots, TikZ and beamer, the web, and Office and Canva."),
        "pgfplots_co2": dict(
            title=f"Carbon dioxide at Mauna Loa rose every year from {n['coFirstYear']} to {n['coLastYear']}",
            subtitle=f"annual means of the seasonally adjusted monthly record · up {n['coRise']} ppm in all; "
                     f"the smallest yearly rise was {n['coSmallestRise']} ppm",
            form="line chart", tool="pgfplots",
            data="Mauna Loa monthly CO2, NOAA Global Monitoring Laboratory and Scripps Institution of Oceanography, "
                 "1958-2020, via vega-datasets 2.8.0",
            alt=f"A line chart of annual mean CO2 at Mauna Loa rising every year from {n['coFirst']} ppm in {n['coFirstYear']} "
                f"to {n['coLast']} ppm in {n['coLastYear']}, passing the dotted 350 ppm reference in {n['coPassed']}."),
        "pgfplots_landscape": dict(
            title=f"A saddle at w = {n['lsSaddle']} separates the peak of {n['lsHigh']} from a lower peak of {n['lsLow']}",
            subtitle="illustrative two-trait landscape w(z₁, z₂) · the shape in 3D, and the same values from above to read them",
            form="3D surface with twin", tool="pgfplots",
            data="analytic two-trait landscape w(z1, z2) from examples/python/_common.py (illustrative)",
            alt=f"A lagoon-coloured surface with a high peak of {n['lsHigh']} at z1 = {n['lsHighX']}, z2 = {n['lsHighY']}, a lower "
                f"peak of {n['lsLow']} at z1 = {n['lsLowX']}, z2 = {n['lsLowY']}, and a saddle of {n['lsSaddle']} between them; "
                "beside it the same surface seen from above as a heat map with seven contour lines and a colour bar.",
            note="illustrative: an analytic function, not data. The same surface is drawn in matplotlib and base R persp."),
    }
    m = dict(kind="tools", medium="paper", script=rel(os.path.join(HERE, name + ".tex")))
    m.update(M[name])
    m["files"] = {k: f"figures/{GROUP}/{f}" for k, f in
                  (("light", f"{name}_light.png"), ("dark", f"{name}_dark.png"), ("pdf", f"{name}_light.pdf"))}
    return m


def lualatex(name, job, sha, tmp):
    """One lualatex run; job is the job name, so <name>_dark draws the dark twin. Returns the PDF path in tmp.
    It runs in examples/latex itself, not with -output-directory, because contour lua reads its table from the working
    directory; the PDF is moved to tmp and the run's own files are removed."""
    miktex = "MiKTeX" in subprocess.run(["lualatex", "--version"], capture_output=True, text=True).stdout
    env = dict(os.environ)
    args = ["lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-jobname={job}"]
    if miktex: args.append(f"--include-directory={STYLE}")
    else: env["TEXINPUTS"] = STYLE + os.pathsep          # a trailing separator keeps the default search path
    r = subprocess.run(args + [rf"\def\vellumstamp{{{sha}}}\input{{{name}.tex}}"], cwd=HERE, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    pdf = os.path.join(HERE, job + ".pdf")
    ok = r.returncode == 0 and os.path.exists(pdf)
    if ok: shutil.move(pdf, os.path.join(tmp, job + ".pdf"))
    for f in [os.path.join(HERE, job + e) for e in (".aux", ".log", ".pdf")] + glob.glob(os.path.join(HERE, job + "_contourtmp*")):
        if os.path.exists(f): os.remove(f)
    if not ok:
        sys.exit(f"lualatex failed on {job}:\n" + r.stdout[-3000:])
    return os.path.join(tmp, job + ".pdf")


def build(name, sha):
    tmp = tempfile.mkdtemp(prefix=f"vellum-{name}-")
    try:
        for mode, job in (("light", name), ("dark", name + "_dark")):
            pdf = lualatex(name, job, sha, tmp)
            png = os.path.join(OUT, f"{name}_{mode}")
            subprocess.run(["pdftoppm", "-png", "-singlefile", "-scale-to-x", str(WIDTH_PX), "-scale-to-y", "-1", pdf, png], check=True)
            if mode == "light": shutil.copy(pdf, os.path.join(OUT, f"{name}_light.pdf"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return name


if __name__ == "__main__":
    subprocess.run([sys.executable, os.path.join(HERE, "prepare_data.py")], check=True)
    os.makedirs(OUT, exist_ok=True)
    names = [os.path.splitext(os.path.basename(f))[0] for f in sorted(glob.glob(os.path.join(HERE, "*.tex")))]
    only = sys.argv[1:] or names                          # optional: build only the names given
    sha, n = stamp(), numbers()
    with ThreadPoolExecutor(4) as pool:
        for name in pool.map(lambda nm: build(nm, sha), [nm for nm in names if nm in only]):
            record(GROUP, name, meta(name, n))
            print("built", name)
