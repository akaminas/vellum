"""site_blocks.py: the tables and diagrams the site quotes from style/vellum.json, computed with generators/colorlab.py.

build_site.py replaces <!--#table NAME--> ... <!--/table-->, <!--#wheel--> and <!--#lightness--> in the pages with these,
so no hex value or check number on the site is typed by hand.
"""
import html, json, math, os, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "generators"))
from colorlab import contrast, de, de_cvd, hex_to_oklch   # noqa: E402

SPEC = json.load(open(os.path.join(REPO, "style", "vellum.json"), encoding="utf-8"))
e = html.escape

NEUTRAL_JOBS = {"surface": "the page or figure background", "card": "a panel, a box, a stat tile, a table stripe (the cream)",
                "grid": "gridlines, the bottom axis line, a colour bar edge", "rule": "identity line, greyed-out series, leader lines",
                "muted": "ticks, unit line, axis labels, footer, quiet notes", "secondary": "body text in a report, error bars, arrows",
                "ink": "titles, claims, direct labels, text that must be read"}


def sw(h, label=True):
    chip = f'<span class="sw" style="background:{h};box-shadow:inset 0 0 0 1px rgba(128,120,110,.25)"></span>'
    return chip + (f"<code>{h}</code>" if label else "")


def table(head, rows, caption=""):
    th = "".join(f'<th class="r">{c[1:]}</th>' if c.startswith(">") else f"<th>{c}</th>" for c in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<div class="table-wrap"><table>{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def right(x):
    return f'<span class="num" style="display:block;text-align:right">{x}</span>'


def t_neutrals():
    L, D = SPEC["light"]["neutrals"], SPEC["dark"]["neutrals"]
    return table(["role", "light", "dark", "job"], [[k, sw(L[k]), sw(D[k]), e(NEUTRAL_JOBS[k])] for k in L])


def t_families():
    rows = []
    for i, f in enumerate(SPEC["families"]):
        l, d = f["light"], f["dark"]
        rows.append([str(i + 1), f'<strong>{f["name"]}</strong>', f'{f["hue"]}°', sw(l["tone"]), sw(l["tint"]), sw(l["deep"]),
                     sw(d["tone"]), sw(d["tint"]), sw(d["deep"])])
    return table(["slot", "family", "hue", "tone", "tint", "deep", "dark tone", "dark tint", "dark deep"], rows,
                 caption="tone for lines, dots and bars · tint for bands and fills · deep for emphasis and text on a tint")


def t_contrast():
    rows = []
    for m in ("light", "dark"):
        M = SPEC[m]; N = M["neutrals"]; surf = N["surface"]
        for k in ("ink", "secondary", "muted"):
            rows.append([m, k, sw(N[k]), right(f"{contrast(N[k], surf):.2f}:1")])
        tones = M["tone"]; w = min(range(6), key=lambda i: contrast(tones[i], surf))
        rows.append([m, f"lowest tone ({SPEC['order'][w]})", sw(tones[w]), right(f"{contrast(tones[w], surf):.2f}:1")])
        rows.append([m, "a tint (teal)", sw(M["tint"][0]), right(f'{contrast(M["tint"][0], surf):.2f}:1')])
        k = min(range(6), key=lambda i: contrast(M["deep"][i], M["tint"][i]))
        rows.append([m, f"deep on its tint, lowest ({SPEC['order'][k]})", sw(M["deep"][k]), right(f'{contrast(M["deep"][k], M["tint"][k]):.2f}:1')])
    return table(["twin", "colour", "value", ">contrast"], rows, caption="Against the twin's surface, except the last row of each twin, which is against the tint")


def t_ramps():
    M = SPEC["light"]; rows = []
    for name, steps in M["sequential"].items():
        rows.append([f"<strong>{name}</strong>"] + [sw(h, False) + f'<code class="small">{h}</code>' for h in steps])
    out = table(["family", "1", "2", "3", "4", "5", "6", "7"], rows,
                caption="Sequential ramps, light twin, from near the surface to past the deep step. The dark twin uses the same steps in reverse order.")
    div = M["diverging"]
    cells = "".join(f'<div style="flex:1;background:{h};height:40px" title="{h}"></div>' for h in div)
    return out + ('<p class="small muted mt-2 mb-0">Diverging, eleven steps: terracotta below the baseline, teal above, the neutral '
                  f'<code>{div[5]}</code> on the baseline.</p><div style="display:flex;gap:2px;margin:8px 0 32px;max-width:720px">{cells}</div>')


def t_status():
    rows = []
    for k in SPEC["light"]["status"]:
        l, d = SPEC["light"]["status"][k], SPEC["dark"]["status"][k]
        rows.append([k, sw(l), right(f'{contrast(l, SPEC["light"]["neutrals"]["surface"]):.2f}:1'),
                     sw(d), right(f'{contrast(d, SPEC["dark"]["neutrals"]["surface"]):.2f}:1')])
    return table(["state", "light", ">on white", "dark", ">on charcoal"], rows)


def t_gradients():
    out = []
    for name, g in SPEC["gradients"].items():
        Ls = [hex_to_oklch(h)[0] for h in g["light"]]
        bar = "linear-gradient(to right, " + ", ".join(g["light"]) + ")"
        bar_d = "linear-gradient(to right, " + ", ".join(g["dark"]) + ")"
        stops = "".join(f'<div style="flex:1;background:{h};height:22px" title="{h}"></div>' for h in g["light"])
        hues = " → ".join(f"{h}°" for h in g["hues"])
        out.append('<div class="card mt-2"><div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">'
                   f'<h4 class="mt-0 mb-0">{name}</h4><span class="small muted">hues {hues} · lightness {Ls[0]:.2f} → {Ls[-1]:.2f}</span></div>'
                   f'<p class="small secondary">{e(g["use"])}</p>'
                   f'<div class="legend-bar twin-light" style="background:{bar};height:14px" role="img" aria-label="{name}, light twin"></div>'
                   f'<div class="legend-bar twin-dark" style="background:{bar_d};height:14px" role="img" aria-label="{name}, dark twin"></div>'
                   f'<div style="display:flex;gap:2px;margin-top:6px">{stops}</div>'
                   f'<p class="small mb-0 mt-1" style="overflow-wrap:anywhere"><code style="white-space:normal">{" ".join(g["light"])}</code></p></div>')
    return "".join(out)


def t_checks():
    def adj(tones, f): return min(f(tones[i], tones[i + 1]) for i in range(5))
    pairs3 = ((0, 1), (0, 2), (1, 2))
    checks = [
        ("smallest ΔE between neighbouring tones, normal vision", "≥ 15 (hard floor)", lambda m: f"{adj(SPEC[m]['tone'], de):.1f}"),
        ("smallest ΔE between neighbouring tones, protanopia or deuteranopia", "≥ 8 (target; 6 with labels)", lambda m: f"{adj(SPEC[m]['tone'], de_cvd):.1f}"),
        ("smallest ΔE among the first three tones, all pairs", "≥ 15, so three series need no labels",
         lambda m: f"{min(de(SPEC[m]['tone'][i], SPEC[m]['tone'][j]) for i, j in pairs3):.1f}"),
        ("lowest contrast of a tone on the surface", "≥ 3:1 for marks", lambda m: f"{min(contrast(t, SPEC[m]['neutrals']['surface']) for t in SPEC[m]['tone']):.2f}:1"),
        ("contrast of ink on the surface", "≥ 4.5:1 for body text", lambda m: f"{contrast(SPEC[m]['neutrals']['ink'], SPEC[m]['neutrals']['surface']):.2f}:1"),
        ("lowest contrast of a deep step on its tint", "≥ 4.5:1", lambda m: f"{min(contrast(SPEC[m]['deep'][i], SPEC[m]['tint'][i]) for i in range(6)):.2f}:1"),
        ("smallest lightness step between gradient stops", "≥ 0.06, monotone",
         lambda m: f"{min(abs(hex_to_oklch(g[m][i])[0] - hex_to_oklch(g[m][i + 1])[0]) for g in SPEC['gradients'].values() for i in range(8)):.3f}"),
    ]
    rows = [[e(label), e(thr), right(f("light")), right(f("dark"))] for label, thr, f in checks]
    return table(["check", "passes when", ">light twin", ">dark twin"], rows,
                 caption="Computed with generators/colorlab.py every time the site is built")


def wheel():
    cx, cy, R = 170, 170, 112
    pos = {f["name"]: (cx + R * math.cos(math.radians(f["hue"])), cy - R * math.sin(math.radians(f["hue"])), math.radians(f["hue"]))
           for f in SPEC["families"]}
    p = ['<svg viewBox="-70 0 480 340" role="img" aria-label="The six hue angles of Vellum on the OKLCH hue wheel, with the complement pairs joined" style="width:100%;max-width:520px">',
         f'<circle cx="{cx}" cy="{cy}" r="{R}" style="fill:none;stroke:var(--v-grid);stroke-width:1"/>']
    for a, b in (("teal", "terracotta"), ("indigo", "ochre"), ("mauve", "moss")):
        (x1, y1, _), (x2, y2, _) = pos[a], pos[b]
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" style="stroke:var(--v-rule);stroke-width:1.4;stroke-dasharray:0.01 4;stroke-linecap:round"/>')
    for i, f in enumerate(SPEC["families"]):
        x, y, a = pos[f["name"]]
        lx, ly = cx + (R + 30) * math.cos(a), cy - (R + 30) * math.sin(a)
        anchor = "start" if math.cos(a) > 0.3 else ("end" if math.cos(a) < -0.3 else "middle")
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" style="fill:var(--v-{f["name"]});stroke:var(--v-surface);stroke-width:2.5"/>')
        p.append(f'<text x="{lx:.1f}" y="{ly - 1:.1f}" text-anchor="{anchor}" style="fill:var(--v-ink);font-size:13px;font-family:var(--v-font-body)">{i + 1} {f["name"]}</text>')
        p.append(f'<text x="{lx:.1f}" y="{ly + 14:.1f}" text-anchor="{anchor}" style="fill:var(--v-muted);font-size:12px;font-family:var(--v-font-body)">{f["hue"]}°</text>')
    p.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" style="fill:var(--v-muted);font-size:12px;font-family:var(--v-font-body)">OKLCH hue</text></svg>')
    p.append('<p class="small muted">Numbers are the slot order. The dotted chords join the complement pairs. The dots take the current twin\'s tones.</p>')
    return "".join(p)


def lightness():
    out = []
    for m in ("light", "dark"):
        M = SPEC[m]; N = M["neutrals"]
        Ls = [hex_to_oklch(h)[0] for h in M["tone"]]
        W, H, l, r, t, b = 440, 250, 46, 24, 62, 36
        lo, hi = (0.40, 0.70) if m == "light" else (0.62, 0.92)
        y = lambda v: t + (hi - v) / (hi - lo) * (H - t - b)
        x = lambda i: l + i * (W - l - r) / 5
        font = "font-family:var(--v-font-body)"
        p = [f'<svg class="twin-{m}" viewBox="0 0 {W} {H}" role="img" aria-label="OKLCH lightness of the six tones in slot order, {m} twin: neighbours alternate dark and light" style="width:100%;max-width:540px">',
             f'<text x="0" y="20" style="fill:{N["ink"]};font-size:16px;font-family:var(--v-font-title)">Neighbouring tones alternate dark and light</text>',
             f'<text x="0" y="{t - 14}" style="fill:{N["muted"]};font-size:11.5px;{font}">OKLCH lightness of each tone, {m} twin</text>']
        for v in ((0.45, 0.55, 0.65) if m == "light" else (0.65, 0.75, 0.85)):
            p.append(f'<line x1="{l}" x2="{W - r}" y1="{y(v):.1f}" y2="{y(v):.1f}" style="stroke:{N["grid"]}"/>'
                     f'<text x="{l - 8}" y="{y(v) + 4:.1f}" text-anchor="end" style="fill:{N["muted"]};font-size:11px;{font}">{v:.2f}</text>')
        p.append(f'<polyline points="{" ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(Ls))}" style="fill:none;stroke:{N["rule"]};stroke-width:1.2"/>')
        for i, v in enumerate(Ls):
            p.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="7" style="fill:{M["tone"][i]};stroke:{N["surface"]};stroke-width:2"/>'
                     f'<text x="{x(i):.1f}" y="{H - 8}" text-anchor="middle" style="fill:{N["muted"]};font-size:11px;{font}">{SPEC["order"][i]}</text>')
        p.append("</svg>")
        out.append("".join(p))
    return "".join(out)


BLOCKS = {"neutrals": t_neutrals, "families": t_families, "contrast": t_contrast, "ramps": t_ramps, "status": t_status,
          "gradients": t_gradients, "checks": t_checks}
