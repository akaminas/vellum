"""make_vellum_json.py: the single source of truth for the Vellum style, computed in OKLCH and written as JSON.
Every hex in every asset and note is generated from this file."""
import json, sys
import numpy as np
from colorlab import *
from build_palettes import mk, score

A = json.load(open("palettes.json"))["A_paper"]
names = A["names"]; hues = A["hues"]
light_surface = A["surface"]

# ---- neutrals (warm greys on hue 80, chroma ~0.01)
light = dict(surface="#FFFFFF", card="#FAF6EE", grid="#E6E0D4", rule="#C7C3BD", muted="#8A857C", secondary="#5A5650", ink="#2A2825")
dark = dict(surface="#2A2520", card="#342F2A", grid="#413C36", rule="#5A544D", muted="#A29E96", secondary="#C9C4BB", ink="#ECE7DF")
for k, v in light.items(): assert v.startswith("#")

# ---- light families: tone (lines, dots), tint (fills), deep (emphasis, text on tint)
tone_l, tint_l, deep_l = A["tone"], A["tint"], A["deep"]

# ---- dark twin: same hue angles, tones re-stepped for the dark surface (searched), tints and deeps swapped in lightness
rng = np.random.default_rng(3); best = None
for _ in range(6000):
    Ls = rng.uniform(0.68, 0.86, 6); pal = [mk(L, 0.085, H) for L, H in zip(Ls, hues)]; sc = score(pal, dark["surface"])
    if best is None or sc[0] > best[0][0]: best = (sc, pal, Ls)
sc, pal, Ls = best
for _ in range(4000):
    k = rng.integers(6); L2 = Ls.copy(); L2[k] = np.clip(L2[k] + rng.normal(0, 0.02), 0.68, 0.86)
    pal2 = [mk(L, 0.085, H) for L, H in zip(L2, hues)]; sc2 = score(pal2, dark["surface"])
    if sc2[0] > sc[0]: sc, pal, Ls = sc2, pal2, L2
tone_d = pal; tint_d = [mk(0.50, 0.05, H) for H in hues]; deep_d = [mk(0.92, 0.05, H) for H in hues]
checks_d = dict(min_nv=round(sc[1], 1), min_cvd=round(sc[2], 1), min_contrast=round(sc[3], 2))
# the light tones were searched on the cream card (palettes.json "surface"), but the light page is white: the distances do not
# depend on the surface, the contrast does, so it is measured again on the page (it is 3.03:1 on the card)
_, nv_l, cvd_l, con_l = score(tone_l, light["surface"])
checks_l = dict(min_nv=round(nv_l, 1), min_cvd=round(cvd_l, 1), min_contrast=round(con_l, 2))
assert (checks_l["min_nv"], checks_l["min_cvd"]) == (A["checks"]["min_nv"], A["checks"]["min_cvd"])


def ramp(H, dark_mode):
    Ls = [0.93, 0.84, 0.74, 0.64, 0.54, 0.45, 0.36]
    Cs = [0.03, 0.05, 0.07, 0.085, 0.085, 0.075, 0.06]
    if dark_mode: Ls = Ls[::-1]; Cs = Cs[::-1]
    return [mk(L, C, H) for L, C in zip(Ls, Cs)]


seq_l = {n: ramp(H, False) for n, H in zip(names, hues)}
seq_d = {n: ramp(H, True) for n, H in zip(names, hues)}

# ---- diverging: terracotta (warm) <-> teal (cool) through a neutral midpoint
div_l = seq_l["terracotta"][5:0:-1] + ["#E1DDD8"] + seq_l["teal"][1:6]
div_d = seq_d["terracotta"][1:6][::-1] + ["#585550"] + seq_d["teal"][1:6]

# ---- status: reserved, never a series colour (checked: far from every tone or clearly deeper)
status_l = dict(good="#007835", warning="#DAB327", serious="#CA6719", critical="#B02A2D")  # saturated on purpose: status is small marks plus an icon, never a series
status_d = dict(good="#5FC27A", warning="#DAB327", serious="#F08A3C", critical="#F06B6B")

# ---- semantic slots: what each family is used for by default
slots = dict(primary="teal", secondary="terracotta", tertiary="indigo", quaternary="ochre", quinary="mauve", senary="moss",
             highlight="terracotta", baseline="indigo", reference="ochre", model="teal", data="terracotta", mainland="indigo", island="teal")


# ---- gradients: multi-hue sequential scales between neighbouring families, interpolated in OKLCH with monotone lightness
def gradient(knots, dark_mode, n=9, cmax=0.085):
    """knots: hue angles at equal spacing along the gradient (unwrapped, degrees). Light mode runs from near white to deep;
    dark mode from near the surface to light. Chroma follows a bell so the middle stops are the most coloured."""
    Ls = np.linspace(0.34, 0.90, n) if dark_mode else np.linspace(0.94, 0.36, n)
    t = np.linspace(0, 1, n)
    Cs = 0.02 + (cmax - 0.02) * np.sin(np.pi * t) ** 0.8
    xs = np.linspace(0, 1, len(knots))
    Hs = np.interp(t, xs, knots) % 360
    return [mk(L, C, H) for L, C, H in zip(Ls, Cs, Hs)]


GRAD_KNOTS = dict(lagoon=[140, 200, 265], ember=[85, 40, -25], shore=[85, 140, 200])
GRAD_USE = dict(lagoon="general magnitude with more range than one family: moss to teal to indigo",
                ember="warm magnitude, a heat or a risk: ochre to terracotta to mauve",
                shore="neutral-warm to cool magnitude: ochre to moss to teal")
gradients = {k: dict(hues=v, use=GRAD_USE[k], light=gradient(v, False), dark=gradient(v, True)) for k, v in GRAD_KNOTS.items()}
for k, g in gradients.items():
    for m in ("light", "dark"):
        Ls = [hex_to_oklch(h)[0] for h in g[m]]
        assert all(np.diff(Ls) < 0) if m == "light" else all(np.diff(Ls) > 0), (k, m, "lightness not monotone")
        print("gradient", k, m, g[m], "min dL", round(min(abs(np.diff(Ls))), 3), "min adjacent dE", round(min(de(a, b) for a, b in zip(g[m][:-1], g[m][1:])), 1))

out = dict(
    name="Vellum", version="1.0",
    description="White page with warm cream cards, six earth-pigment hue families, each in three steps of one hue angle (tint, tone, deep). "
                "Chroma held in the muted band (OKLCH C about 0.085 for tones, 0.05 for tints). Dark twin on warm charcoal.",
    families=[dict(name=n, hue=h, light=dict(tint=tl, tone=to, deep=dp), dark=dict(tint=tdd, tone=tdo, deep=ddp))
              for n, h, tl, to, dp, tdd, tdo, ddp in zip(names, hues, tint_l, tone_l, deep_l, tint_d, tone_d, deep_d)],
    order=names, slots=slots,
    light=dict(neutrals=light, tone=tone_l, tint=tint_l, deep=deep_l, sequential=seq_l, diverging=div_l, status=status_l, checks=checks_l),
    dark=dict(neutrals=dark, tone=tone_d, tint=tint_d, deep=deep_d, sequential=seq_d, diverging=div_d, status=status_d, checks=checks_d),
    gradients=gradients,
    typography=dict(title="Palatino Linotype", body="Corbel", mono="Consolas",
                    latex=dict(title="TeX Gyre Pagella (tgpagella)", body="Lato (lato)", engine="any; lualatex or xelatex for fontspec"),
                    web=dict(title="'Palatino Linotype', 'TeX Gyre Pagella', Palatino, serif", body="Corbel, Lato, 'Segoe UI', sans-serif")),
    marks=dict(line_pt=1.6, thin_line_pt=0.7, ring_pt=1.2, marker_pt2=28, bar_gap_px=2, band_alpha=0.55, grid_pt=0.6, dotted=[1, 3]),
    sizes=dict(title=13, subtitle=9, panel_title=9, unit_line=7.5, axis_label=9, tick=8, annotation=7.5, footer=6.5),
)
json.dump(out, open(sys.argv[1], "w"), indent=1)
# verification printout
print("dark tones", tone_d, checks_d)
print("status light min dE to tones:", {k: round(min(de(v, t) for t in tone_l), 1) for k, v in status_l.items()})
print("status dark contrast:", {k: round(contrast(v, dark["surface"]), 2) for k, v in status_d.items()})
print("text contrast light: ink", round(contrast(light["ink"], light["surface"]), 2), "secondary", round(contrast(light["secondary"], light["surface"]), 2), "muted", round(contrast(light["muted"], light["surface"]), 2))
print("text contrast dark: ink", round(contrast(dark["ink"], dark["surface"]), 2), "secondary", round(contrast(dark["secondary"], dark["surface"]), 2), "muted", round(contrast(dark["muted"], dark["surface"]), 2))
print("deep on tint (light):", [round(contrast(d, t), 2) for d, t in zip(deep_l, tint_l)])
print("deep on tint (dark):", [round(contrast(d, t), 2) for d, t in zip(deep_d, tint_d)])
print("div light", div_l); print("div dark", div_d)
