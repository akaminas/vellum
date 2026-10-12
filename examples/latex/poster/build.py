"""build.py: builds the example A0 poster from nothing but the repository.

Runs examples/python/poster/make_poster_figures.py (the central figure and the numbers), compiles poster.tex twice
with lualatex (the TikZ overlay needs the second run) with style/ on the TeX search path through TEXINPUTS, so
vellum-colors.sty is used where it lives, rasterises the sheet with pdftoppm for the site (1800 px wide) and as a
600 px thumbnail, and records the poster in docs/figures/poster/manifest.json.
Outputs: docs/media/poster/poster.pdf, poster.png, poster-thumb.png.
Needs lualatex with beamer, beamerposter, fontspec, qrcode, TeX Gyre Pagella and Lato; pdftoppm (Poppler).
Run: python examples/latex/poster/build.py
"""
import os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "python"))
from _common import REPO, STYLE, DOCS, record, rel

OUT = os.path.join(DOCS, "media", "poster")


def run(*cmd, cwd=None):
    env = dict(os.environ, TEXINPUTS=STYLE + os.pathsep)   # the trailing separator keeps the default search path
    subprocess.run(cmd, cwd=cwd, env=env, check=True, stdout=subprocess.DEVNULL)


def png(width, name):
    """One page to a PNG of the given width; pdftoppm writes <root>.png with -singlefile."""
    run("pdftoppm", "-png", "-singlefile", "-scale-to-x", str(width), "-scale-to-y", "-1",
        os.path.join(OUT, "poster.pdf"), os.path.join(OUT, name))


if __name__ == "__main__":
    run(sys.executable, os.path.join(REPO, "examples", "python", "poster", "make_poster_figures.py"))
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:                # aux files stay out of the repository
        for _ in range(2):
            run("lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={tmp}", "poster.tex", cwd=HERE)
        shutil.copy(os.path.join(tmp, "poster.pdf"), os.path.join(OUT, "poster.pdf"))
    png(1800, "poster"); png(600, "poster-thumb")
    numbers = dict(re.findall(r"\\newcommand\\p(\w+)\{(.*)\}", open(os.path.join(HERE, "fig", "numbers.tex"), encoding="utf-8").read()))
    record("poster", "poster", dict(
        title="Beak shape, not body size, tells penguin species apart",
        subtitle="An A0 conference poster: one 3D scatter with its 2D twin as the central figure, three short columns "
                 "and one stat tile",
        kind="conference", form="A0 poster", medium="poster", tool="beamerposter",
        data="Palmer penguins: Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; "
             "via the palmerpenguins R package and vega-datasets 2.8.0 (CC0)",
        script=rel(os.path.join(HERE, "poster.tex")),
        alt=f"An A0 portrait poster on white with cream cards. Headline: beak shape, not body size, tells penguin "
            f"species apart. The central figure is a 3D scatter of beak depth, beak length and flipper length for "
            f"{numbers['Birds']} penguins of three species, with its beak-length against beak-depth twin beside it. "
            f"Stat tile: {numbers['AccBeak']} % of birds are placed in their own species by beak length and depth "
            f"(leave-one-out nearest species mean), against {numbers['AccMass']} % by body mass alone.",
        note="Figure and every number by examples/python/poster/make_poster_figures.py (light, scale 2.6 on 2.6 x "
             "V.size('poster'), placed at 1:1); built by examples/latex/poster/build.py. QR code to "
             "https://akaminas.github.io/vellum/ by the qrcode package.",
        files={"pdf": "media/poster/poster.pdf", "light": "media/poster/poster.png", "thumb": "media/poster/poster-thumb.png"}))
    print(f"poster -> {os.path.relpath(OUT, REPO)}")
