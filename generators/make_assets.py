"""make_assets.py: generate the R, LaTeX, mplstyle, CSS and Office assets of Vellum from vellum.json.
Usage: python make_assets.py vellum.json <assets_dir>"""
import json, os, sys

S = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
L, Dk = S["light"], S["dark"]; names = S["order"]


def w(name, text):
    open(os.path.join(out, name), "w", encoding="utf-8", newline="\n").write(text)


# ---------------------------------------------------------------- mplstyle (light), for people who only want rcParams
N = L["neutrals"]
w("vellum.mplstyle", f"""# Vellum, light mode, as plain rcParams. Generated from vellum.json. Prefer vellum.py for the helpers.
font.family: {S['typography']['body']}, Lato, Segoe UI, DejaVu Sans
font.size: {S['sizes']['axis_label']}
mathtext.fontset: stixsans
figure.facecolor: {N['surface']}
axes.facecolor: {N['surface']}
savefig.facecolor: {N['surface']}
axes.edgecolor: {N['grid']}
axes.linewidth: 0.8
axes.spines.top: False
axes.spines.right: False
axes.spines.left: False
axes.grid: True
axes.grid.axis: y
grid.color: {N['grid']}
grid.linewidth: {S['marks']['grid_pt']}
grid.linestyle: -
axes.axisbelow: True
xtick.color: {N['muted']}
ytick.color: {N['muted']}
xtick.labelcolor: {N['muted']}
ytick.labelcolor: {N['muted']}
xtick.major.size: 0
ytick.major.size: 0
axes.labelcolor: {N['muted']}
text.color: {N['ink']}
axes.titlelocation: left
axes.titlesize: {S['sizes']['panel_title']}
axes.titleweight: bold
axes.prop_cycle: cycler('color', {L['tone']})
lines.linewidth: {S['marks']['line_pt']}
lines.solid_capstyle: round
legend.frameon: False
figure.dpi: 150
savefig.dpi: 300
savefig.bbox: tight
pdf.fonttype: 42
svg.fonttype: none
""")

# ---------------------------------------------------------------- R / ggplot2
def rvec(xs): return "c(" + ", ".join(f'"{x}"' for x in xs) + ")"
seq_r = ",\n".join(f'  {n} = {rvec(L["sequential"][n])}' for n in names)
seq_rd = ",\n".join(f'  {n} = {rvec(Dk["sequential"][n])}' for n in names)
w("vellum.R", f'''# vellum.R: the Vellum figure style for ggplot2. Generated from vellum.json; do not edit the hex values here.
# Usage:
#   source("vellum.R")
#   ggplot(d, aes(x, y, colour = series)) + geom_line(linewidth = vellum$lw) + scale_colour_vellum() + theme_vellum() +
#     labs(title = "The claim, in one sentence", subtitle = "unit line or settings", caption = "source and git stamp", y = NULL)
# Needs ggplot2 and scales. Fonts: Palatino Linotype and Corbel on Windows; use ragg::agg_png or ggsave(device = ragg::agg_png) so the
# system fonts are found; for PDF use cairo_pdf.

vellum <- list(
  mode = "light",
  surface = "{N['surface']}", card = "{N['card']}", grid = "{N['grid']}", rule = "{N['rule']}",
  muted = "{N['muted']}", secondary = "{N['secondary']}", ink = "{N['ink']}",
  names = {rvec(names)},
  tone = {rvec(L['tone'])},
  tint = {rvec(L['tint'])},
  deep = {rvec(L['deep'])},
  diverging = {rvec(L['diverging'])},
  status = c(good = "{L['status']['good']}", warning = "{L['status']['warning']}", serious = "{L['status']['serious']}", critical = "{L['status']['critical']}"),
  title_font = "{S['typography']['title']}", body_font = "{S['typography']['body']}",
  lw = {S['marks']['line_pt'] * 0.4:.2f}, thin = {S['marks']['thin_line_pt'] * 0.4:.2f}, band_alpha = {S['marks']['band_alpha']}
)
vellum$sequential <- list(
{seq_r}
)

vellum_dark <- list(
  mode = "dark",
  surface = "{Dk['neutrals']['surface']}", card = "{Dk['neutrals']['card']}", grid = "{Dk['neutrals']['grid']}", rule = "{Dk['neutrals']['rule']}",
  muted = "{Dk['neutrals']['muted']}", secondary = "{Dk['neutrals']['secondary']}", ink = "{Dk['neutrals']['ink']}",
  names = {rvec(names)},
  tone = {rvec(Dk['tone'])},
  tint = {rvec(Dk['tint'])},
  deep = {rvec(Dk['deep'])},
  diverging = {rvec(Dk['diverging'])},
  status = c(good = "{Dk['status']['good']}", warning = "{Dk['status']['warning']}", serious = "{Dk['status']['serious']}", critical = "{Dk['status']['critical']}"),
  title_font = "{S['typography']['title']}", body_font = "{S['typography']['body']}",
  lw = {S['marks']['line_pt'] * 0.4:.2f}, thin = {S['marks']['thin_line_pt'] * 0.4:.2f}, band_alpha = {S['marks']['band_alpha']}
)
vellum_dark$sequential <- list(
{seq_rd}
)

# ggplot linewidth is in mm; the style's 1.6 pt line is 0.56 mm.

# Fonts. With ragg installed, ggsave(device = ragg::agg_png) finds the system fonts by name. Without it, on Windows, the base
# png() device needs the families registered once per session; vellum_fonts() does that and is safe to call anywhere.
vellum_fonts <- function(V = vellum) {{
  if (.Platform$OS.type == "windows" && !requireNamespace("ragg", quietly = TRUE)) {{
    grDevices::windowsFonts(); args <- list()
    args[[V$title_font]] <- grDevices::windowsFont(V$title_font)
    args[[V$body_font]] <- grDevices::windowsFont(V$body_font)
    do.call(grDevices::windowsFonts, args)
  }}
  invisible(NULL)
}}

theme_vellum <- function(base_size = 9, V = vellum) {{
  ggplot2::theme_minimal(base_size = base_size, base_family = V$body_font) +
    ggplot2::theme(
      plot.background = ggplot2::element_rect(fill = V$surface, colour = NA),
      panel.background = ggplot2::element_rect(fill = V$surface, colour = NA),
      panel.grid.major.x = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.y = ggplot2::element_line(colour = V$grid, linewidth = 0.25),
      axis.line.x = ggplot2::element_line(colour = V$grid, linewidth = 0.3),
      axis.ticks = ggplot2::element_blank(),
      axis.text = ggplot2::element_text(colour = V$muted, size = base_size - 1),
      axis.title = ggplot2::element_text(colour = V$muted, size = base_size),
      axis.title.y = ggplot2::element_blank(),   # the unit goes in the subtitle or a unit line
      plot.title = ggplot2::element_text(family = V$title_font, colour = V$ink, size = base_size + 4, hjust = 0),
      plot.subtitle = ggplot2::element_text(colour = V$muted, size = base_size, margin = ggplot2::margin(b = 10)),
      plot.caption = ggplot2::element_text(colour = V$muted, size = base_size - 2.5, hjust = 0),
      plot.title.position = "plot", plot.caption.position = "plot",
      strip.text = ggplot2::element_text(colour = V$ink, face = "bold", hjust = 0, size = base_size),
      legend.position = "none",   # direct labels instead; set legend.position in labs() when there are more than four series
      legend.title = ggplot2::element_blank(),
      legend.text = ggplot2::element_text(colour = V$ink),
      plot.margin = ggplot2::margin(12, 16, 10, 12)
    )
}}

scale_colour_vellum <- function(V = vellum, ...) ggplot2::scale_colour_manual(values = V$tone, ...)
scale_fill_vellum   <- function(V = vellum, ...) ggplot2::scale_fill_manual(values = V$tint, ...)
scale_fill_vellum_tone <- function(V = vellum, ...) ggplot2::scale_fill_manual(values = V$tone, ...)
scale_colour_vellum_seq <- function(family = "teal", V = vellum, ...) ggplot2::scale_colour_gradientn(colours = c(V$surface, V$sequential[[family]]), ...)
scale_fill_vellum_seq   <- function(family = "teal", V = vellum, ...) ggplot2::scale_fill_gradientn(colours = c(V$surface, V$sequential[[family]]), ...)
scale_fill_vellum_div   <- function(V = vellum, ...) ggplot2::scale_fill_gradientn(colours = V$diverging, ...)
scale_colour_vellum_div <- function(V = vellum, ...) ggplot2::scale_colour_gradientn(colours = V$diverging, ...)

# A ringed point: draw the surface ring under the point.
geom_point_vellum <- function(mapping = NULL, data = NULL, size = 2, V = vellum, ...) {{
  list(ggplot2::geom_point(mapping, data, size = size + 0.8, colour = V$surface, ...),
       ggplot2::geom_point(mapping, data, size = size, ...))
}}

# Direct labels at the line ends (needs the last point per series; ggrepel is optional).
label_ends_vellum <- function(d, x, y, label, V = vellum, nudge = 0.01) {{
  ggplot2::geom_text(data = d, ggplot2::aes(x = {{{{ x }}}}, y = {{{{ y }}}}, label = {{{{ label }}}}), hjust = 0, nudge_x = nudge,
                     colour = V$ink, family = V$body_font, size = 2.6)
}}
''')

# ---------------------------------------------------------------- LaTeX: xcolor, TikZ, pgfplots, beamer
def tex_colors(M, suffix):
    rows = []
    for n, to, ti, dp in zip(names, M["tone"], M["tint"], M["deep"]):
        rows.append(f"\\definecolor{{v{n}{suffix}}}{{HTML}}{{{to[1:]}}}")
        rows.append(f"\\definecolor{{v{n}Tint{suffix}}}{{HTML}}{{{ti[1:]}}}")
        rows.append(f"\\definecolor{{v{n}Deep{suffix}}}{{HTML}}{{{dp[1:]}}}")
    for k, v in M["neutrals"].items(): rows.append(f"\\definecolor{{v{k.capitalize()}{suffix}}}{{HTML}}{{{v[1:]}}}")
    for k, v in M["status"].items(): rows.append(f"\\definecolor{{vStatus{k.capitalize()}{suffix}}}{{HTML}}{{{v[1:]}}}")
    for i, c in enumerate(M["diverging"]): rows.append(f"\\definecolor{{vDiv{i}{suffix}}}{{HTML}}{{{c[1:]}}}")
    return "\n".join(rows)


w("vellum-colors.sty", f"""% vellum-colors.sty: the Vellum palette for LaTeX (xcolor), with TikZ, pgfplots and beamer styles.
% Generated from vellum.json; the hex values are not to be edited here.
% Usage: \\usepackage{{vellum-colors}}  then  \\usetikzlibrary{{...}}  and  \\pgfplotsset{{vellum}}  or  \\usetheme-free beamer via \\vellumbeamer
% Light mode names: vteal, vterracotta, vindigo, vochre, vmauve, vmoss (tones); vtealTint ... (tints); vtealDeep ... (deeps);
% neutrals vSurface, vCard, vGrid, vRule, vMuted, vSecondary, vInk; status vStatusGood ... ; diverging vDiv0 ... vDiv10.
% Dark mode: the same names with the suffix D (vtealD, vSurfaceD, ...).
\\NeedsTeXFormat{{LaTeX2e}}
\\ProvidesPackage{{vellum-colors}}[Vellum palette]
\\RequirePackage{{xcolor}}
{tex_colors(L, "")}
{tex_colors(Dk, "D")}
% the categorical order, as a pgfplots cycle list
\\@ifpackageloaded{{pgfplots}}{{%
\\pgfplotscreateplotcyclelist{{vellum}}{{%
  {{vteal, line width=1.1pt}},
  {{vterracotta, line width=1.1pt}},
  {{vindigo, line width=1.1pt}},
  {{vochre, line width=1.1pt}},
  {{vmauve, line width=1.1pt}},
  {{vmoss, line width=1.1pt}}}}
\\pgfplotsset{{vellum/.style={{
  cycle list name=vellum,
  axis background/.style={{fill=vSurface}},
  axis line style={{vGrid, line width=0.5pt}},
  axis x line*=bottom, axis y line*=left, y axis line style={{draw=none}},
  ymajorgrids, grid style={{vGrid, line width=0.4pt}},
  tick style={{draw=none}}, ticklabel style={{vMuted, font=\\scriptsize}},
  xlabel style={{vMuted, font=\\footnotesize}}, ylabel style={{vMuted, font=\\footnotesize, at={{(0,1)}}, anchor=south west, rotate=-90, yshift=4pt}},
  title style={{vInk, font=\\footnotesize\\bfseries, at={{(0,1)}}, anchor=south west, xshift=-2pt, yshift=10pt}},
  legend style={{draw=none, fill=none, font=\\scriptsize, text=vInk}},
  every axis plot/.append style={{line cap=round, line join=round}},
  clip=false
}},
  vellum dark/.style={{vellum,
  axis background/.style={{fill=vSurfaceD}}, axis line style={{vGridD}}, grid style={{vGridD}},
  ticklabel style={{vMutedD}}, xlabel style={{vMutedD}}, ylabel style={{vMutedD}}, title style={{vInkD}}, legend style={{text=vInkD}}
}}}}
% sequential colormaps, one per family
\\pgfplotsset{{
  colormap={{vellum teal}}{{color=(vSurface) color=(vtealTint) color=(vteal) color=(vtealDeep)}},
  colormap={{vellum terracotta}}{{color=(vSurface) color=(vterracottaTint) color=(vterracotta) color=(vterracottaDeep)}},
  colormap={{vellum indigo}}{{color=(vSurface) color=(vindigoTint) color=(vindigo) color=(vindigoDeep)}},
  colormap={{vellum diverging}}{{color=(vDiv0) color=(vDiv2) color=(vDiv4) color=(vDiv5) color=(vDiv6) color=(vDiv8) color=(vDiv10)}}
}}
}}{{}}
% TikZ styles for diagrams in the same language
\\@ifpackageloaded{{tikz}}{{%
\\tikzset{{
  vellum box/.style={{draw=vRule, fill=vCard, line width=0.5pt, rounded corners=2pt, inner sep=5pt, text=vInk, font=\\footnotesize}},
  vellum box tint/.style={{draw=none, fill=v#1Tint, text=v#1Deep, rounded corners=2pt, inner sep=5pt, font=\\footnotesize, align=center}},
  vellum arrow/.style={{->, >=stealth, vSecondary, line width=0.6pt, shorten >=2pt, shorten <=2pt}},
  vellum guide/.style={{vRule, line width=0.4pt, dash pattern=on 1pt off 2pt}},
  vellum label/.style={{vMuted, font=\\scriptsize, align=left}},
  vellum claim/.style={{vInk, font=\\footnotesize\\bfseries, align=left}}
}}}}{{}}
% beamer: call \\vellumbeamer in the preamble after \\usepackage{{vellum-colors}}
\\providecommand{{\\vellumbeamer}}{{%
  \\setbeamercolor{{background canvas}}{{bg=vSurface}}
  \\setbeamercolor{{normal text}}{{fg=vInk, bg=vSurface}}
  \\setbeamercolor{{structure}}{{fg=vteal}}
  \\setbeamercolor{{frametitle}}{{fg=vInk, bg=vSurface}}
  \\setbeamercolor{{title}}{{fg=vInk}}
  \\setbeamercolor{{alerted text}}{{fg=vterracotta}}
  \\setbeamercolor{{example text}}{{fg=vmoss}}
  \\setbeamercolor{{block title}}{{fg=vInk, bg=vCard}}
  \\setbeamercolor{{block body}}{{fg=vInk, bg=vCard}}
  \\setbeamercolor{{footline}}{{fg=vMuted}}
  \\setbeamerfont{{frametitle}}{{family=\\rmfamily, size=\\Large}}
  \\setbeamerfont{{title}}{{family=\\rmfamily, size=\\huge}}
  \\setbeamertemplate{{navigation symbols}}{{}}
  \\setbeamertemplate{{itemize items}}{{\\textcolor{{vteal}}{{\\tiny$\\bullet$}}}}
}}
\\providecommand{{\\vellumbeamerdark}}{{%
  \\setbeamercolor{{background canvas}}{{bg=vSurfaceD}}
  \\setbeamercolor{{normal text}}{{fg=vInkD, bg=vSurfaceD}}
  \\setbeamercolor{{structure}}{{fg=vtealD}}
  \\setbeamercolor{{frametitle}}{{fg=vInkD, bg=vSurfaceD}}
  \\setbeamercolor{{title}}{{fg=vInkD}}
  \\setbeamercolor{{alerted text}}{{fg=vterracottaD}}
  \\setbeamercolor{{example text}}{{fg=vmossD}}
  \\setbeamercolor{{block title}}{{fg=vInkD, bg=vCardD}}
  \\setbeamercolor{{block body}}{{fg=vInkD, bg=vCardD}}
  \\setbeamercolor{{footline}}{{fg=vMutedD}}
  \\setbeamerfont{{frametitle}}{{family=\\rmfamily, size=\\Large}}
  \\setbeamerfont{{title}}{{family=\\rmfamily, size=\\huge}}
  \\setbeamertemplate{{navigation symbols}}{{}}
}}
\\endinput
""")

# ---------------------------------------------------------------- CSS variables (Obsidian snippet, HTML, Excalidraw reference)
def css(M, prefix):
    rows = [f"  --{prefix}{k}: {v};" for k, v in M["neutrals"].items()]
    for n, to, ti, dp in zip(names, M["tone"], M["tint"], M["deep"]):
        rows += [f"  --{prefix}{n}: {to};", f"  --{prefix}{n}-tint: {ti};", f"  --{prefix}{n}-deep: {dp};"]
    rows += [f"  --{prefix}status-{k}: {v};" for k, v in M["status"].items()]
    return "\n".join(rows)
w("vellum.css", f""":root {{
{css(L, "v-")}
  --v-font-title: {S['typography']['web']['title']};
  --v-font-body: {S['typography']['web']['body']};
}}
:root[data-theme="dark"], .theme-dark {{
{css(Dk, "v-")}
}}
""")

# ---------------------------------------------------------------- Office / Canva: a plain list, RGB and hex
def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
rows = ["role\tname\thex\tR\tG\tB"]
for k, v in L["neutrals"].items(): rows.append(f"neutral\t{k}\t{v}\t" + "\t".join(map(str, rgb(v))))
for n, to, ti, dp in zip(names, L["tone"], L["tint"], L["deep"]):
    rows.append(f"tone\t{n}\t{to}\t" + "\t".join(map(str, rgb(to)))); rows.append(f"tint\t{n}\t{ti}\t" + "\t".join(map(str, rgb(ti)))); rows.append(f"deep\t{n}\t{dp}\t" + "\t".join(map(str, rgb(dp))))
for k, v in L["status"].items(): rows.append(f"status\t{k}\t{v}\t" + "\t".join(map(str, rgb(v))))
rows.append("")
rows.append("dark mode")
for k, v in Dk["neutrals"].items(): rows.append(f"neutral\t{k}\t{v}\t" + "\t".join(map(str, rgb(v))))
for n, to, ti, dp in zip(names, Dk["tone"], Dk["tint"], Dk["deep"]):
    rows.append(f"tone\t{n}\t{to}\t" + "\t".join(map(str, rgb(to)))); rows.append(f"tint\t{n}\t{ti}\t" + "\t".join(map(str, rgb(ti)))); rows.append(f"deep\t{n}\t{dp}\t" + "\t".join(map(str, rgb(dp))))
w("vellum-office.tsv", "\n".join(rows) + "\n")

# ---------------------------------------------------------------- gradients (appended to the files written above)
G = S["gradients"]
def rlist(M): return "list(\n" + ",\n".join(f"  {k} = {rvec(g[M])}" for k, g in G.items()) + "\n)"
open(os.path.join(out, "vellum.R"), "a", encoding="utf-8", newline="\n").write(f"""
# Gradients: multi-hue sequential scales, nine stops, lightness monotone. Use for magnitude only, never as a decoration.
vellum$gradients <- {rlist("light")}
vellum_dark$gradients <- {rlist("dark")}
scale_fill_vellum_grad   <- function(name = "lagoon", V = vellum, ...) ggplot2::scale_fill_gradientn(colours = V$gradients[[name]], ...)
scale_colour_vellum_grad <- function(name = "lagoon", V = vellum, ...) ggplot2::scale_colour_gradientn(colours = V$gradients[[name]], ...)
""")

sty_path = os.path.join(out, "vellum-colors.sty"); sty = open(sty_path, encoding="utf-8").read()
defs, maps = [], []
for k, g in G.items():
    for suffix, M in (("", "light"), ("D", "dark")):
        for i, c in enumerate(g[M]): defs.append(f"\\definecolor{{vgrad{k}{suffix}{i}}}{{HTML}}{{{c[1:]}}}")
        maps.append(f"  colormap={{vellum {k}{' dark' if suffix else ''}}}{{" + " ".join(f"color=(vgrad{k}{suffix}{i})" for i in range(len(g[M]))) + "}")
style3d = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "style3d.tex.txt"), encoding="utf-8").read()
block = "% gradients: nine stops each, light and dark (suffix D); pgfplots colormaps 'vellum lagoon', 'vellum ember', 'vellum shore', and '... dark'\n" + "\n".join(defs) + "\n\\@ifpackageloaded{pgfplots}{\\pgfplotsset{\n" + ",\n".join(maps) + "\n}}{}\n"
sty = sty.replace("\\endinput", block + style3d + "\\endinput")
open(sty_path, "w", encoding="utf-8", newline="\n").write(sty)

def css_grad(M, prefix):
    return "\n".join(f"  --{prefix}grad-{k}: linear-gradient(to right, {', '.join(g[M])});" for k, g in G.items())
css_path = os.path.join(out, "vellum.css"); c = open(css_path, encoding="utf-8").read()
c = c.replace('}\n:root[data-theme="dark"]', css_grad("light", "v-") + "\n}\n:root[data-theme=\"dark\"]", 1)
c = c.rstrip()
assert c.endswith("}")
c = c[:-1] + css_grad("dark", "v-") + "\n}\n"
open(css_path, "w", encoding="utf-8", newline="\n").write(c)

with open(os.path.join(out, "vellum-office.tsv"), "a", encoding="utf-8", newline="\n") as f:
    for M in ("light", "dark"):
        f.write(f"\ngradients, {M} mode, nine stops from the low end to the high end\n")
        for k, g in G.items():
            for i, h in enumerate(g[M]): f.write(f"gradient\t{k} {i + 1}\t{h}\t" + "\t".join(map(str, rgb(h))) + "\n")
print("assets written to", out)
