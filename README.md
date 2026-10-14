# Vellum

**One visual style for every figure, and a written reason for every rule.**

Vellum is a visual language for scientific figures, reports, conference posters, slides and infographics: a white page,
warm cream cards, six muted earth pigments and a serif claim over a sans body. Its colours were searched in a perceptual
colour space (OKLCH) and checked for colour-vision deficiency and contrast. Its anatomy is fixed, so a reader who has seen
one figure knows where to look in the next.

**The site, with the rules, the reasoning and every worked example: https://akaminas.github.io/vellum/**

New here? Start with the guide, from a claim to a finished figure in seven steps: https://akaminas.github.io/vellum/guide.html

## The style in one paragraph

Each of six hue families (teal, terracotta, indigo, ochre, mauve, moss) has three steps of one hue angle: a pastel
**tint** for areas, a muted **tone** for lines, dots and bars, and a **deep** step for emphasis and for text on a tint.
Chroma is held low on purpose, and neighbouring series alternate in lightness, which is how a muted palette stays
distinguishable: the smallest colour distance between neighbouring series is ΔE 18.3 (floor 15), and 11.4 under
protanopia or deuteranopia (target 8). Every figure has the same parts: a claim in Palatino at the top left, a unit line
in place of a rotated y label, direct labels at the line ends instead of a legend, a horizontal hairline grid, no frame,
and a footer naming the data, the script and the git commit. A dark twin on warm charcoal uses the same hue angles for
talks and screens.

## What is in the repository

| path | what |
|---|---|
| `style/vellum.json` | every colour of both twins, the slot order, gradients, fonts, mark and type sizes. The single source of truth. |
| `style/vellum.py` | matplotlib: `V = vellum.use("light")` sets the style and returns the palette with the anatomy as helpers |
| `style/vellum.R` | ggplot2: `theme_vellum()`, colour and fill scales, gradients, ringed points, end labels |
| `style/vellum-colors.sty` | LaTeX: xcolor names, pgfplots styles and colormaps, TikZ node styles, `\vellumbeamer` |
| `style/vellum.css` | the palette and gradients as CSS variables, light and dark |
| `style/vellum-office.tsv` | every colour as hex and RGB for PowerPoint, Word, Excel, Canva and Google |
| `style/vellum-web.js` | SVG on the web: reads `vellum.json`, draws the anatomy (axes, unit line, ringed dots, end labels, tooltips) and does the colour science |
| `generators/` | the seeded palette search and the scripts that write every file in `style/` except `vellum.py` |
| `examples/` | the scripts that draw every figure on the site: `python/`, `latex/`, `r/` |
| `data/` | the datasets the examples use, with their sources and licences in `data/SOURCES.md` |
| `docs/` | the website, served by GitHub Pages; plain HTML, CSS and JavaScript with no build step at serve time |
| `tools/` | `build_site.py` assembles the site; `render.py` renders HTML to PNG and PDF with headless Edge or Chrome |

## Quick start

```python
import sys; sys.path.insert(0, "vellum/style")
import vellum, matplotlib.pyplot as plt

V = vellum.use("light")                         # "dark" for the twin; scale=2.2 for slides, 2.6 for posters
fig, ax = plt.subplots(figsize=V.size("double"))
fig.subplots_adjust(left=0.07, right=0.84, top=0.74, bottom=0.17)
ax.plot(year, ppm, color=V.tone(0))
V.dot(ax, year[-1], ppm[-1], V.tone(0)); V.endlabel(ax, year[-1], ppm[-1], "annual mean")
V.reference(ax, y=350, text="350 ppm")
V.panel(ax, unit="parts per million")
V.title(fig, "Carbon dioxide rose every year since 1959", "Mauna Loa, annual mean", "NOAA GML · co2.py · git " + vellum.stamp())
fig.savefig("co2.pdf"); fig.savefig("co2.png")
```

```r
source("vellum/style/vellum.R"); library(ggplot2); vellum_fonts()
ggplot(d, aes(year, ppm)) + geom_line(colour = vellum$tone[1], linewidth = vellum$lw) +
  labs(title = "Carbon dioxide rose every year since 1959", subtitle = "parts per million", caption = "NOAA GML · co2.R",
       x = NULL, y = NULL) + theme_vellum()
```

```latex
\usepackage{tikz}\usepackage{pgfplots}\pgfplotsset{compat=1.18}
\usepackage{vellum-colors}
\begin{axis}[vellum, xlabel={year}, title={parts per million}] \addplot table {co2.dat}; \end{axis}
```

Fonts: Palatino Linotype and Corbel on Windows; TeX Gyre Pagella and Lato in LaTeX and on the web.

## Rebuilding everything

```sh
# the style files, from the palette search (reproduces style/ byte for byte)
cd generators
python build_palettes.py palettes.json
python make_vellum_json.py ../style/vellum.json
python make_assets.py ../style/vellum.json ../style
cd ..

# every example figure, the report, infographics, decks, poster and the site (Python 3.13 with matplotlib,
# numpy, scipy and Pillow; lualatex and pdftoppm for LaTeX; R with ggplot2; Edge or Chrome for HTML renders)
python tools/build_all.py
cd docs && python -m http.server 8000      # then open http://localhost:8000
```

Each figure's footer carries the git commit of the inputs it was drawn from (`style/`, `examples/`, `data/`), with
`-dirty` when they had uncommitted changes.

## Licences

Code (`style/`, `generators/`, `examples/`, `tools/`, `docs/assets/js/`) is under the MIT licence in `LICENSE`. The text
of the site and the example figures are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The datasets
keep their own licences, listed in `data/SOURCES.md`. TeX Gyre Pagella, served as the web fallback for Palatino, is under
the GUST Font License (`docs/assets/fonts/GUST-FONT-LICENSE.txt`).

## References

- Björn Ottosson (2020), *A perceptual color space for image processing* (OKLab), https://bottosson.github.io/posts/oklab/
- Machado, Oliveira and Fernandes (2009), *A physiologically-based model for simulation of color vision deficiency*,
  IEEE TVCG 15(6), 1291–1298.
