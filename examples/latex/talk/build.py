"""build.py: builds the example talk from nothing but the repository.

Runs examples/python/talk/make_talk_figures.py (figures and numbers), compiles talk.tex twice with lualatex (the
overlays and the frame count need the second run) with style/ on the TeX search path through TEXINPUTS, so
vellum-colors.sty is used where it lives, rasterises every page to a 1600 x 900 PNG with pdftoppm, and records the deck
in docs/figures/talk/manifest.json. Outputs: docs/media/talk/talk.pdf and talk-01.png, talk-02.png, ...
Needs lualatex with beamer, fontspec, unicode-math, TeX Gyre Pagella (and its Math) and Lato; pdftoppm (Poppler).
Run: python examples/latex/talk/build.py
"""
import glob, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "python"))
from _common import REPO, STYLE, DOCS, record, rel

OUT = os.path.join(DOCS, "media", "talk")


def run(*cmd, cwd=None):
    env = dict(os.environ, TEXINPUTS=STYLE + os.pathsep)   # the trailing separator keeps the default search path
    subprocess.run(cmd, cwd=cwd, env=env, check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    run(sys.executable, os.path.join(REPO, "examples", "python", "talk", "make_talk_figures.py"))
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:                # aux files stay out of the repository
        for _ in range(2):
            run("lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={tmp}", "talk.tex", cwd=HERE)
        shutil.copy(os.path.join(tmp, "talk.pdf"), os.path.join(OUT, "talk.pdf"))
    for old in glob.glob(os.path.join(OUT, "talk-*.png")): os.remove(old)
    run("pdftoppm", "-png", "-scale-to-x", "1600", "-scale-to-y", "900", os.path.join(OUT, "talk.pdf"), os.path.join(OUT, "talk"))
    pages = [os.path.relpath(p, DOCS).replace("\\", "/") for p in sorted(glob.glob(os.path.join(OUT, "talk-*.png")))]
    record("talk", "talk", dict(
        title="Where a population starts decides which peak it climbs",
        subtitle="A conference talk in the dark twin: a stat tile, a progressive reveal in four steps, the surface at two "
                 "fixed views, its heat-map twin and a TikZ diagram built step by step",
        kind="slides", form="beamer deck", medium="slides", tool="beamer",
        data="illustrative simulation on the analytic landscape w(z1, z2) of examples/python/_common.py; not data",
        script=rel(os.path.join(HERE, "talk.tex")),
        alt="A dark 16:9 deck of 11 frames (14 pages with the diagram's build steps). In an illustrative simulation on a "
            "two-peak landscape, most random starts end on the lower peak at fitness 0.72, not on the higher one at 1.00; "
            "four populations are revealed one by one, the surface is shown at two fixed views and then as a heat map "
            "with the basin boundary.",
        note="Illustrative simulation, labelled on every slide. Figures by examples/python/talk/make_talk_figures.py, "
             "built by examples/latex/talk/build.py. The page is the 160 x 90 mm frame enlarged by 1.764 so the 10 in "
             "slide figure and the 28/20/10 pt type sizes hold at 1:1.",
        files={"pdf": "media/talk/talk.pdf", "pages": pages, "light": pages[0]}))
    print(f"talk: {len(pages)} pages -> {os.path.relpath(OUT, REPO)}")
