"""build_palettes.py: three candidate muted palettes built in OKLCH.
Each hue family has three steps of the same hue angle: a TONE (muted, for lines and dots), a TINT
(pastel, for fills and bands) and a DEEP (for emphasis and in-fill text). Chroma is fixed in the muted
band; only the tone lightness is searched so that adjacent tones clear the normal-vision floor
(dE >= 15 in OKLab x100) and the CVD target (dE >= 8), with >= 3:1 contrast against the surface."""
import json, sys
import numpy as np
from colorlab import *

rng = np.random.default_rng(11)

CANDS = {
    "A_paper": dict(surface="#FAF6EE", ink="#2A2825", muted="#8A857C", grid="#E6E0D4",
                    names=["teal", "terracotta", "indigo", "ochre", "mauve", "moss"],
                    hues=[200, 40, 265, 85, 335, 140], L=(0.46, 0.64), C_tone=0.085, C_tint=0.05, L_tint=0.84, L_deep=0.38, dark=False),
    "B_slate": dict(surface="#23272F", ink="#ECE8DF", muted="#9A9AA3", grid="#343945",
                    names=["mint", "peach", "lavender", "butter", "sky", "rose"],
                    hues=[170, 45, 285, 95, 230, 355], L=(0.70, 0.86), C_tone=0.085, C_tint=0.05, L_tint=0.56, L_deep=0.92, dark=True),
    "C_stone": dict(surface="#F4F5F7", ink="#23262B", muted="#80858E", grid="#E1E4E9",
                    names=["blue", "coral", "sage", "plum", "sand", "sea"],
                    hues=[250, 30, 145, 310, 80, 190], L=(0.46, 0.64), C_tone=0.09, C_tint=0.05, L_tint=0.86, L_deep=0.38, dark=False),
}


def mk(L, C, H):
    h, ok = oklch_to_hex(L, C, H)
    if not ok:
        C = min(C, max_chroma(L, H)); h, ok = oklch_to_hex(L, C, H)
    return h


def score(pal, surface):
    adj = [(i, i + 1) for i in range(len(pal) - 1)]
    allp = [(i, j) for i in range(3) for j in range(3) if i < j]
    s_nv = min(de(pal[i], pal[j]) for i, j in adj + allp)
    s_cvd = min(de_cvd(pal[i], pal[j]) for i, j in adj + allp)
    s_con = min(contrast(h, surface) for h in pal)
    pen = (3.0 - s_con) * 40 if s_con < 3.0 else 0
    return min(s_nv - 15, (s_cvd - 8) * 2) - pen, s_nv, s_cvd, s_con


def build(spec):
    hues = spec["hues"]; n = len(hues)
    best = None
    for _ in range(5000):
        Ls = rng.uniform(*spec["L"], n)
        pal = [mk(L, spec["C_tone"], H) for L, H in zip(Ls, hues)]
        sc = score(pal, spec["surface"])
        if best is None or sc[0] > best[0][0]: best = (sc, pal, Ls)
    sc, pal, Ls = best
    for _ in range(3000):
        k = rng.integers(n); L2 = Ls.copy(); L2[k] = np.clip(L2[k] + rng.normal(0, 0.02), *spec["L"])
        pal2 = [mk(L, spec["C_tone"], H) for L, H in zip(L2, hues)]
        sc2 = score(pal2, spec["surface"])
        if sc2[0] > sc[0]: sc, pal, Ls = sc2, pal2, L2
    return pal, sc


if __name__ == "__main__":
    out = {}
    for name, spec in CANDS.items():
        tones, sc = build(spec)
        tints = [mk(spec["L_tint"], spec["C_tint"], H) for H in spec["hues"]]
        deeps = [mk(spec["L_deep"], 0.07, H) for H in spec["hues"]]
        print(f"== {name}  surface {spec['surface']}  minNV {sc[1]:.1f}  minCVD {sc[2]:.1f}  minContrast {sc[3]:.2f}")
        print(report(tones, spec["surface"]))
        out[name] = {k: spec[k] for k in ("surface", "ink", "muted", "grid", "names", "hues", "dark")}
        out[name].update(tone=tones, tint=tints, deep=deeps,
                         checks=dict(min_nv=round(sc[1], 1), min_cvd=round(sc[2], 1), min_contrast=round(sc[3], 2)))
    json.dump(out, open(sys.argv[1], "w"), indent=1)
