"""_common.py: what every example script shares.

Paths, the git stamp for the footer, and `save`, which writes a figure into docs/figures/<group>/ and records it in
that group's manifest.json so the site build can list it in the gallery. Every example draws each figure twice,
once per twin, from the same function:

    from _common import *

    def draw(V):
        fig, ax = plt.subplots(figsize=V.size("double"))
        ...
        return fig

    for mode in MODES:
        V = vellum.use(mode)
        save(draw(V), "science", "co2_keeling", mode, meta=dict(title=..., ...))
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
STYLE = os.path.join(REPO, "style")
DATA = os.path.join(REPO, "data")
DOCS = os.path.join(REPO, "docs")
FIGURES = os.path.join(DOCS, "figures")
sys.path.insert(0, STYLE)

import numpy as np                      # noqa: E402
import matplotlib                       # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt         # noqa: E402
import vellum                           # noqa: E402

MODES = ("light", "dark")
SOURCE_PATHS = ("style", "examples", "data")   # the stamp follows the inputs of a figure, not its outputs


def stamp():
    """Short sha of the last commit that touched the inputs, with -dirty when they have uncommitted changes."""
    try:
        sha = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h", "--", *SOURCE_PATHS],
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", *SOURCE_PATHS],
                               capture_output=True, text=True).stdout.strip() != ""
        return (sha or "unstamped") + ("-dirty" if dirty else "")
    except Exception:
        return "unstamped"


def footer(source, script):
    """The footer line of a figure: data source, the script that drew it, and the git stamp."""
    return f"{source} · {os.path.basename(script)} · git {stamp()}"


def save(fig, group, name, mode, meta=None, pdf=True, dpi=220):
    """Write <name>_<mode>.png (and .pdf for the light twin) into docs/figures/<group>/ and record the figure.

    meta (recorded once, from the light call) is a dict with:
      title     the claim, as in the figure
      subtitle  one line on what is shown
      kind      gallery category: scientific, 3d, report, conference, infographic, slides, tools
      form      chart form, e.g. "line chart", "heat map", "3D surface with twin"
      medium    paper, dissertation, poster, slides, report, infographic, screen
      tool      matplotlib, ggplot2, pgfplots, TikZ, beamer, HTML
      data      data source in words, with year
      script    path of the script relative to the repo
      alt       alt text: the claim and the key number
    """
    out = os.path.join(FIGURES, group); os.makedirs(out, exist_ok=True)
    png = os.path.join(out, f"{name}_{mode}.png")
    fig.savefig(png, dpi=dpi)
    if pdf and mode == "light":
        fig.savefig(os.path.join(out, f"{name}_{mode}.pdf"))
    plt.close(fig)
    if meta is not None:
        record(group, name, meta)
    return png


def record(group, name, meta):
    """Merge one figure's metadata into docs/figures/<group>/manifest.json, keyed by name, order kept."""
    path = os.path.join(FIGURES, group, "manifest.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    items = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    entry = dict(id=name, group=group, **meta)
    entry.setdefault("files", {"light": f"figures/{group}/{name}_light.png", "dark": f"figures/{group}/{name}_dark.png",
                               "pdf": f"figures/{group}/{name}_light.pdf"})
    items = [e for e in items if e["id"] != name] + [entry]
    json.dump(items, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def rel(script_file):
    """Path of a script relative to the repository, with forward slashes, for the manifest."""
    return os.path.relpath(os.path.abspath(script_file), REPO).replace("\\", "/")


# ---- data loaders, so every figure reads the same files the same way

def load_json(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def load_csv(name):
    import csv
    return list(csv.DictReader(open(os.path.join(DATA, name), encoding="utf-8")))


def penguins():
    """Palmer penguins (Gorman, Williams and Fraser 2014; CC0), rows with complete measurements."""
    keys = ("Beak Length (mm)", "Beak Depth (mm)", "Flipper Length (mm)", "Body Mass (g)")
    return [r for r in load_json("penguins.json") if all(r.get(k) is not None for k in keys)]


# ---- the one analytic surface used by every 3D example (matplotlib, pgfplots, R persp and the web version)
# An illustrative two-trait adaptive landscape: mean fitness w over two trait values z1, z2 in [-2, 2], with a high
# peak, a lower peak and a saddle between them. Every implementation uses exactly this formula:
#     w(z1, z2) = exp(-((z1 - 0.9)^2 + (z2 - 0.7)^2) / 0.6) + 0.72 exp(-((z1 + 0.8)^2 + (z2 + 0.9)^2) / 0.9)
LANDSCAPE_DOMAIN = (-2.0, 2.0)


def landscape(z1, z2):
    return np.exp(-((z1 - 0.9) ** 2 + (z2 - 0.7) ** 2) / 0.6) + 0.72 * np.exp(-((z1 + 0.8) ** 2 + (z2 + 0.9) ** 2) / 0.9)
