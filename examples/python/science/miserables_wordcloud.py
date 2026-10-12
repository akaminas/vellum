"""miserables_wordcloud.py: a word cloud of the characters of Les Misérables, each name sized by its co-appearances in
data/miserables.json, with a ranked list of the exact counts of the top five beside it.

A co-appearance count (weighted degree) is the sum of the link values of a character: for each other character, the
number of chapters the two share, summed over all partners. The area of a word grows with the count, so the font size
grows with its square root. The layout is deterministic: words are placed largest first along an Archimedean spiral
from the centre, at the first spot whose rendered text box collides with no word already placed (no randomness, no
`wordcloud` package, so the font and the colours stay the style's own).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import *
import re
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Lato fallback is not installed

SOURCE = "Data: Knuth, The Stanford GraphBase (1993), via vega-datasets 2.8.0"
D = load_json("miserables.json")
NAMES = [n["name"] for n in D["nodes"]]; N = len(NAMES)
W = np.zeros(N, int); DEG = np.zeros(N, int)
for l in D["links"]:
    for i in (l["source"], l["target"]): W[i] += l["value"]; DEG[i] += 1
ORDER = np.argsort(-W, kind="stable")                  # most co-appearances first, ties in data order
SHOW = 50                                              # the 50 most connected characters
TOP = int((W >= W[ORDER[4]]).sum())                    # the top five, and anyone tied with the fifth
HERO, RUNNER = ORDER[0], ORDER[1]
assert W[HERO] > W[RUNNER], "one character has more co-appearances than anyone"
label = lambda i: re.sub(r"\.(?=\S)", ". ", NAMES[i])   # "Mme.Thenardier" -> "Mme. Thenardier"

TITLE = (f"{label(HERO)} co-appears {W[HERO]} times with other characters, "
         f"{W[HERO] / W[RUNNER]:.1f} times as often as {label(RUNNER)}")
SUB = (f"Les Misérables · the {SHOW} most connected of {N} characters · "
       f"the area of each name is proportional to its co-appearances")
RANK = [1 + int((W > W[i]).sum()) for i in ORDER]        # competition ranking: tied counts share a rank


def colour(V, rank):
    """Words are the marks here, so they carry colour. By rank, not by group: the claim is about who is most connected,
    and the dataset's groups would scatter six hues over dozens of small words that the eye then tries to read as
    clusters the layout does not make. So: the top five (with ties) in teal (slot 1), ranks 6 to 20 in secondary text, the rest muted."""
    return V.tone(0) if rank < TOP else V.secondary if rank < 20 else V.muted


def layout(fig, ax, V, words, sizes, pad=1.6, step=0.35):
    """Place words largest first along an Archimedean spiral (stretched to the axes' aspect) from the centre; each takes
    the first spot where its padded text box overlaps no placed box and stays inside the axes. Units are points.
    Returns positions, or None if a word does not fit (the caller then scales every size down)."""
    r = fig.canvas.get_renderer()
    Wp, Hp = (ax.get_position().width * fig.get_figwidth() * 72, ax.get_position().height * fig.get_figheight() * 72)
    cx, cy, ex = Wp / 2, Hp / 2, Wp / Hp
    boxes, out = [], []
    for w, s in zip(words, sizes):
        t = ax.text(0, 0, w, fontsize=s, ha="center", va="center")
        bb = t.get_window_extent(r); t.remove()
        hw, hh = bb.width * 36 / fig.dpi + pad, bb.height * 36 / fig.dpi + pad * 0.5   # half sizes in points
        th, placed = 0.0, None
        while th < 400:
            rad = step * th
            x, y = cx + ex * rad * np.cos(th), cy + rad * np.sin(th)
            if hw <= x <= Wp - hw and hh <= y <= Hp - hh and not any(
                    abs(x - bx) < hw + bw and abs(y - by) < hh + bh for bx, by, bw, bh in boxes):
                placed = (x, y); break
            th += 0.6 / max(1.0, rad) ** 0.5 if rad > 1 else 0.3
        if placed is None: return None
        boxes.append((*placed, hw, hh)); out.append(placed)
    return out


def draw(V):
    fig = plt.figure(figsize=V.size("double_tall"))
    ax = fig.add_axes([0.012, 0.09, 0.70, 0.74]); ax.axis("off")
    Wp, Hp = ax.get_position().width * fig.get_figwidth() * 72, ax.get_position().height * fig.get_figheight() * 72
    ax.set_xlim(0, Wp); ax.set_ylim(0, Hp)
    idx = ORDER[:SHOW]; words = [label(i) for i in idx]
    fig.canvas.draw()
    smax = 34.0
    while True:                                         # shrink every word together until all fit
        sizes = np.maximum(smax * np.sqrt(W[idx] / W[HERO]), 6.5)
        pos = layout(fig, ax, V, words, sizes)
        if pos is not None: break
        smax *= 0.95
    for k, (i, w, s, (x, y)) in enumerate(zip(idx, words, sizes, pos)):
        ax.text(x, y, w, fontsize=s, ha="center", va="center", color=colour(V, k))

    # the values: a word cloud alone cannot be read as numbers, so the top five are listed with their counts
    axl = fig.add_axes([0.75, 0.26, 0.235, 0.50]); axl.axis("off")
    axl.set_xlim(0, 1); axl.set_ylim(TOP + 0.2, -1.2)
    axl.text(0, -1, "Top 5, co-appearances",          # a tie for fifth shows as 5= on both rows
             fontsize=V.sz["panel_title"], fontweight="bold", color=V.ink, va="center")
    for k, i in enumerate(ORDER[:TOP]):
        axl.text(0, k, f"{RANK[k]}" + ("=" if RANK.count(RANK[k]) > 1 else ""), fontsize=V.sz["annotation"], color=V.muted, va="center")
        axl.text(0.11, k, label(i), fontsize=V.sz["annotation"], color=V.ink, va="center")
        axl.text(1, k, f"{W[i]}", fontsize=V.sz["annotation"], color=V.ink, va="center", ha="right")
        axl.plot([0.11, 0.11 + 0.60 * W[i] / W[HERO]], [k + 0.36, k + 0.36], color=V.tone(0), lw=2.0 * V.scale, solid_capstyle="butt")
    V.note(axl, 0, TOP + 0.05, f"next: {label(ORDER[TOP])}, {W[ORDER[TOP]]}\n"
                                f"{label(HERO)} shares a chapter with {DEG[HERO]} others\n"
                                f"co-appearances: the chapters shared\nwith each other character, summed",
           va="top", linespacing=1.5)
    V.title(fig, TITLE, SUB, footer(SOURCE, __file__), x=0.012)
    return fig


META = dict(
    title=TITLE, subtitle=SUB, kind="scientific", form="word cloud with ranked values", medium="screen", tool="matplotlib",
    data="Knuth, The Stanford GraphBase (1993), Les Misérables co-occurrences, via vega-datasets 2.8.0",
    script=rel(__file__),
    alt=(f"Word cloud of the {SHOW} most connected of the {N} characters of Les Misérables, word area proportional to "
         f"co-appearances. Largest: " + ", ".join(f"{label(i)} ({W[i]})" for i in ORDER[:TOP]) + f". {label(HERO)} has "
         f"{W[HERO] / W[RUNNER]:.1f} times the co-appearances of {label(RUNNER)}, and shares a chapter with {DEG[HERO]} characters."),
    note="Layout: deterministic Archimedean spiral, largest word first, collision-checked on the rendered text boxes; no random seed involved.",
)

if __name__ == "__main__":
    for mode in MODES:
        V = vellum.use(mode)
        print(save(draw(V), "science", "miserables_wordcloud", mode, meta=META if mode == "light" else None))
