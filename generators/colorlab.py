"""colorlab.py: OKLCH <-> sRGB, CVD simulation (Machado 2009, severity 1), Delta E in OKLab x100, WCAG contrast.
Pure numpy. Used to build and check the candidate palettes."""
import numpy as np


def hex_to_rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def rgb_to_hex(rgb):
    rgb = np.clip(np.asarray(rgb), 0, 1)
    return "#" + "".join(f"{int(round(c * 255)):02X}" for c in rgb)


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
               [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
               [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])


def linear_to_oklab(rgb):
    lms = M1 @ np.asarray(rgb)
    lms_ = np.cbrt(lms)
    return M2 @ lms_


def oklab_to_linear(lab):
    lms_ = np.linalg.solve(M2, np.asarray(lab))
    lms = lms_ ** 3
    return np.linalg.solve(M1, lms)


def hex_to_oklch(h):
    L, a, b = linear_to_oklab(srgb_to_linear(hex_to_rgb(h)))
    C = np.hypot(a, b); H = np.degrees(np.arctan2(b, a)) % 360
    return L, C, H


def oklch_to_hex(L, C, H):
    a = C * np.cos(np.radians(H)); b = C * np.sin(np.radians(H))
    rgb = linear_to_srgb(oklab_to_linear([L, a, b]))
    return rgb_to_hex(rgb), bool(np.all((rgb >= -1e-6) & (rgb <= 1 + 1e-6)))


def oklch_in_gamut(L, C, H):
    return oklch_to_hex(L, C, H)[1]


def max_chroma(L, H, cap=0.4):
    lo, hi = 0.0, cap
    for _ in range(40):
        mid = (lo + hi) / 2
        if oklch_in_gamut(L, mid, H): lo = mid
        else: hi = mid
    return lo


# Machado, Oliveira, Fernandes 2009, severity 1.0, applied in linear RGB
PROT = np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]])
DEUT = np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]])


def simulate(h, M):
    lin = srgb_to_linear(hex_to_rgb(h))
    return np.clip(M @ lin, 0, 1)


def de_lin(lin1, lin2):
    return float(np.linalg.norm(linear_to_oklab(lin1) - linear_to_oklab(lin2)) * 100)


def de(h1, h2):
    return de_lin(srgb_to_linear(hex_to_rgb(h1)), srgb_to_linear(hex_to_rgb(h2)))


def de_cvd(h1, h2):
    return min(de_lin(simulate(h1, PROT), simulate(h2, PROT)), de_lin(simulate(h1, DEUT), simulate(h2, DEUT)))


def luminance(h):
    lin = srgb_to_linear(hex_to_rgb(h)); return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def contrast(h1, h2):
    a, b = luminance(h1), luminance(h2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def report(pal, surface, pairs="adjacent"):
    lines = []
    idx = list(range(len(pal)))
    pr = [(i, i + 1) for i in idx[:-1]] if pairs == "adjacent" else [(i, j) for i in idx for j in idx if i < j]
    worst_cvd = min((de_cvd(pal[i], pal[j]), i, j) for i, j in pr)
    worst_nv = min((de(pal[i], pal[j]), i, j) for i, j in pr)
    for h in pal:
        L, C, H = hex_to_oklch(h)
        lines.append(f"  {h}  L={L:.2f} C={C:.3f} H={H:5.1f}  contrast vs surface {contrast(h, surface):.2f}:1")
    lines.append(f"  worst CVD dE ({pairs}) = {worst_cvd[0]:.1f} between {pal[worst_cvd[1]]} and {pal[worst_cvd[2]]}  (target >= 8, floor 6)")
    lines.append(f"  worst normal-vision dE ({pairs}) = {worst_nv[0]:.1f} between {pal[worst_nv[1]]} and {pal[worst_nv[2]]}  (floor 15)")
    return "\n".join(lines)
