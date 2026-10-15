"""petroleum_sankey.py: where the petroleum of the United States comes from, what it becomes and who burns it, as a
three-stage Sankey diagram for the latest full year of the EIA Monthly Energy Review.

Sources (field production of crude oil and of natural gas liquids, imports, biofuels, refinery processing gain, the
statistical adjustment) flow into one supply node; exports and the stock change leave it, and what is left, the
products supplied, splits into six product families and then into the five end-use sectors. Every flow is a table
value; the script checks that each node balances. Data: data/eia_petroleum.csv, from fetch_eia_petroleum.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
from matplotlib.patches import Rectangle, Polygon
from matplotlib import patheffects as pe
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

SOURCE = "US EIA, Monthly Energy Review, tables 3.1, 3.5, 3.7a–c (public domain)"

# ---- data: the latest year with every series, in million barrels a day
ROWS = load_csv("eia_petroleum.csv")
YEAR = max(r["year"] for r in ROWS if r["msn"] == "PATCPUS")          # total consumed by the transportation sector
V_ = {r["description"]: float(r["value"]) / 1000 for r in ROWS if r["year"] == YEAR}


def v(name): return V_[name]


SOURCES = [("Crude oil, US fields", v("Crude Oil Production, Total")),
           ("Natural gas liquids, US fields", v("Natural Gas Liquids Production")),
           ("Imports", v("Petroleum Imports")),
           ("Biofuels", v("Biofuels Plant Net Production")),
           ("Refinery processing gain", v("Petroleum Processing Gain")),
           ("Statistical adjustment", v("Petroleum Adjustments"))]
SUPPLY = sum(x for _, x in SOURCES)
EXPORTS = v("Petroleum Exports"); STOCKS = v("Petroleum Stock Change")
SUPPLIED = v("Total Petroleum Products Supplied")
assert abs(SUPPLY - EXPORTS - STOCKS - SUPPLIED) < 0.002, "the supply node balances"

SECTORS = ["Transportation", "Industrial", "Residential", "Commercial", "Electric Power"]          # EIA names


def sector(prod, s):
    k = f"{prod} Consumed by the {s} Sector"
    return V_.get(k, 0.0)


# product families, each a row of flows to the sectors, in slot order
OTHER = ("Asphalt and Road Oil", "Lubricants", "Petroleum Coke", "Kerosene")
FAM = [
    ("Motor gasoline", "with ethanol and aviation gasoline",
     {s: sector("Motor Gasoline", s) + sector("Aviation Gasoline", s) for s in SECTORS}),
    ("Jet fuel", "", {s: sector("Jet Fuel", s) for s in SECTORS}),
    ("Distillate fuel oil", "diesel and heating oil", {s: sector("Distillate Fuel Oil", s) for s in SECTORS}),
    ("Residual fuel oil", "ships and power plants", {s: sector("Residual Fuel Oil", s) for s in SECTORS}),
    ("Hydrocarbon gas liquids", "ethane, propane, butane",
     {s: (sector("Total Hydrocarbon Gas Liquids", s) if s == "Industrial" else sector("Propane", s)) for s in SECTORS}),
    ("Asphalt, coke, lubricants, other", "",
     {s: sum(sector(p, s) for p in OTHER) + sector("Other Petroleum Products", s) + sector("Other Products", s) for s in SECTORS}),
]
FLOW = np.array([[f[2][s] for s in SECTORS] for f in FAM])           # families x sectors
SEC_TOT = np.array([v(f"Total Petroleum Consumed by the {s} Sector") for s in SECTORS])
assert np.allclose(FLOW.sum(0), SEC_TOT, atol=0.002), "each sector balances"
assert abs(FLOW.sum() - SUPPLIED) < 0.002, "the products add up to what was supplied"
FAM_TOT = FLOW.sum(1)

TRANSPORT = SEC_TOT[0] / SUPPLIED
assert 0.6 < TRANSPORT < 0.7 and EXPORTS > v("Petroleum Imports")
TITLE = "Two thirds of US petroleum moves vehicles, and exports now exceed imports"
SUB = (f"Petroleum in {YEAR}, million barrels a day: sources, products and the sectors that use them · "
       f"{SEC_TOT[0]:.1f} of {SUPPLIED:.1f} ({TRANSPORT * 100:.0f} %) to transportation")

# ---- geometry, in data units: x across, y in million barrels a day
XS, XH, XP, XE = 2.25, 4.55, 7.35, 9.2                          # sources, supply, products, sectors
BAR = 0.10
GAP = 0.85


def stack(values, top, gap=GAP):
    """Top-down positions (y0, y1) of bars with the given heights and gaps."""
    out = []; y = top
    for h in values:
        out.append((y - h, y)); y -= h + gap
    return out


def ribbon(ax, x0, a0, b0, x1, a1, b1, color, alpha, z=1):
    """A band from the interval (a0, b0) at x0 to (a1, b1) at x1, with horizontal tangents at both ends."""
    t = np.linspace(0, 1, 60); s = 3 * t ** 2 - 2 * t ** 3
    x = x0 + (x1 - x0) * t
    lo = a0 + (a1 - a0) * s; hi = b0 + (b1 - b0) * s
    ax.add_patch(Polygon(np.r_[np.c_[x, hi], np.c_[x[::-1], lo[::-1]]], closed=True, fc=color, ec="none", alpha=alpha, zorder=z))


def halo(V, w=2.4):
    return [pe.withStroke(linewidth=w * V.scale, foreground=V.surface)]


def draw(V):
    fig = plt.figure(figsize=(7.2, 4.6))
    ax = fig.add_axes([0.0, 0.06, 1.0, 0.75])
    neutral = V.secondary if V.mode == "light" else V.muted
    flow_n = V.rule
    TOP = SUPPLY + 5 * GAP
    # sources
    src = stack([x for _, x in SOURCES], TOP)
    hub0 = TOP - (TOP - SUPPLY) / 2; hub = (hub0 - SUPPLY, hub0)
    y = hub[1]
    for (name, x), (a, b) in zip(SOURCES, src):
        ax.add_patch(Rectangle((XS - BAR, a), BAR, b - a, fc=neutral, ec="none", zorder=3))
        ribbon(ax, XS, a, b, XH - BAR, y - x, y, flow_n, 0.6)
        y -= x
        lab = f"{name}  " if x > 0.6 else f"{name} "
        ax.text(XS - BAR - 0.08, (a + b) / 2, name, ha="right", va="center", fontsize=V.sz["annotation"], color=V.ink)
        ax.text(XS - BAR - 0.08, (a + b) / 2 - 0.62 if b - a > 1.6 else (a + b) / 2, "" if b - a <= 1.6 else f"{x:.2f}",
                ha="right", va="top", fontsize=V.sz["unit_line"], color=V.muted)
        if b - a <= 1.6:
            ax.texts[-2].set_text(f"{name}  {x:.2f}")
    ax.add_patch(Rectangle((XH - BAR, hub[0]), BAR, SUPPLY, fc=V.ink, ec="none", zorder=3))
    ax.text(XH - BAR / 2, hub[1] + 0.5, f"supply\n{SUPPLY:.1f}", ha="center", va="bottom", fontsize=V.sz["annotation"], color=V.ink,
            linespacing=1.1)
    # out of the supply: exports, the stock change, and the products supplied
    outs = [("Exports", EXPORTS), ("Added to stocks", STOCKS)]
    fam_pos = stack(FAM_TOT, TOP - EXPORTS - STOCKS - 2 * GAP - 1.2)
    top_out = stack([x for _, x in outs], TOP + 0.2, gap=0.6)
    y = hub[1]
    for (name, x), (a, b) in zip(outs, top_out):
        ribbon(ax, XH, y - x, y, XP - BAR, a, b, flow_n, 0.6)
        ax.add_patch(Rectangle((XP - BAR, a), BAR, b - a, fc=neutral, ec="none", zorder=3))
        ax.text(XP + 0.08, (a + b) / 2, f"{name}  {x:.2f}", ha="left", va="center", fontsize=V.sz["annotation"], color=V.ink,
                path_effects=halo(V))
        y -= x
    for k, ((name, note, _), (a, b)) in enumerate(zip(FAM, fam_pos)):
        x = FAM_TOT[k]; col = V.tone(k); tint = V.tint(k)
        ribbon(ax, XH, y - x, y, XP - BAR, a, b, tint, 0.6)
        y -= x
        ax.add_patch(Rectangle((XP - BAR, a), BAR, b - a, fc=col, ec="none", zorder=3))
    # products to sectors
    sec_pos = stack(SEC_TOT, fam_pos[0][1], gap=GAP * 1.35)
    sec_fill = [p[1] for p in sec_pos]
    for k, (a, b) in enumerate(fam_pos):
        y = b
        for j in range(len(SECTORS)):
            x = FLOW[k, j]
            if x <= 0: continue
            ribbon(ax, XP, y - x, y, XE - BAR, sec_fill[j] - x, sec_fill[j], V.tint(k), 0.6, z=1 + 0.01 * k)
            y -= x; sec_fill[j] -= x
    for j, (name, (a, b)) in enumerate(zip(SECTORS, sec_pos)):
        ax.add_patch(Rectangle((XE - BAR, a), BAR, b - a, fc=neutral, ec="none", zorder=3))
        share = SEC_TOT[j] / SUPPLIED * 100
        sh = f"{share:.0f} %" if share >= 1 else "<1 %"
        name = name.replace("Power", "power")
        ax.text(XE + 0.08, (a + b) / 2, f"{name}", ha="left", va="center" if b - a < 1.6 else "bottom", fontsize=V.sz["annotation"],
                color=V.ink)
        ax.text(XE + 0.08, (a + b) / 2 - (0.0 if b - a < 1.6 else 0.25), ("" if b - a < 1.6 else f"{SEC_TOT[j]:.2f} · {sh}"),
                ha="left", va="top", fontsize=V.sz["unit_line"], color=V.muted)
        if b - a < 1.6:
            ax.texts[-2].set_text(f"{name}  {SEC_TOT[j]:.2f} · {sh}")
    # product labels, over their own incoming band
    for k, ((name, note, _), (a, b)) in enumerate(zip(FAM, fam_pos)):
        lab = f"{name}  {FAM_TOT[k]:.2f}" + (f"\n{note}" if note and b - a > 1.0 else "")
        t = ax.text(XP - BAR - 0.08, (a + b) / 2, lab, ha="right", va="center", fontsize=V.sz["annotation"],
                    color=V.deep(k) if V.mode == "light" else V.ink, path_effects=halo(V), linespacing=1.05, zorder=6)
    lo = min(sec_pos[-1][0], fam_pos[-1][0], src[-1][0]) - 0.6
    ax.set_xlim(0, 11.0); ax.set_ylim(lo, TOP + 1.2); ax.axis("off")
    ax.text(0.05, TOP + 1.0, "million barrels a day", ha="left", va="bottom", fontsize=V.sz["unit_line"], color=V.muted)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


ALT = (f"Sankey diagram of US petroleum in {YEAR}, million barrels a day. Supply of {SUPPLY:.1f}: crude oil from US fields "
       f"{SOURCES[0][1]:.1f}, natural gas liquids {SOURCES[1][1]:.1f}, imports {SOURCES[2][1]:.1f}, biofuels {SOURCES[3][1]:.1f}, "
       f"processing gain {SOURCES[4][1]:.1f}. Exports take {EXPORTS:.1f}; {SUPPLIED:.1f} is supplied: motor gasoline "
       f"{FAM_TOT[0]:.1f}, jet fuel {FAM_TOT[1]:.1f}, distillate {FAM_TOT[2]:.1f}, residual fuel {FAM_TOT[3]:.1f}, gas liquids "
       f"{FAM_TOT[4]:.1f}, other products {FAM_TOT[5]:.1f}. Transportation uses {SEC_TOT[0]:.1f} ({TRANSPORT * 100:.0f} %), "
       f"industry {SEC_TOT[1]:.1f}, homes {SEC_TOT[2]:.2f}, commerce {SEC_TOT[3]:.2f}, power plants {SEC_TOT[4]:.2f}.")
META = dict(title=TITLE, subtitle=SUB, kind="scientific", form="Sankey diagram, three stages", medium="screen", tool="matplotlib",
            data=f"EIA Monthly Energy Review, petroleum supply and consumption by product and sector, {YEAR}",
            script=rel(__file__), alt=ALT,
            note=("Products supplied is EIA's measure of consumption. Gas liquids include the ethane and other feedstocks the "
                  "petrochemical industry uses; outside industry they are propane. Motor gasoline includes the ethanol blended "
                  "into it, which is why biofuels enter on the supply side."))

if __name__ == "__main__":
    print(TITLE)
    for mode in MODES:
        save(draw(vellum.use(mode)), "science", "petroleum_sankey", mode, meta=META if mode == "light" else None)
