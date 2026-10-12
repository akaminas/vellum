"""vellum.py: the Vellum figure style for matplotlib.

Every colour is read from vellum.json, which sits next to this file. Nothing is retyped.

Usage
-----
    import vellum
    V = vellum.use("light")            # or "dark"; sets rcParams and returns the palette object
    fig, ax = plt.subplots(figsize=V.size("single"))
    ax.plot(x, y, color=V.tone(0))     # tone for lines and dots
    ax.fill_between(x, lo, hi, color=V.tint(0), alpha=V.band_alpha, lw=0)
    V.title(fig, "The claim, in one sentence", "unit line or settings", "source and git stamp")
    V.panel(ax, "a", "The claim of this panel", unit="morphospecies")
    V.endlabel(ax, x_end, y_end, "series name")
    V.dot(ax, x, y, V.tone(1))        # marker with a surface ring
    fig.savefig("figure.pdf")

Rules the helpers enforce: title left aligned, a unit line instead of a rotated y label, no top or right spine,
hairline grid on y only, direct end labels, markers ringed in the surface colour, a footer with the source.
"""
import json, os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "vellum.json"), encoding="utf-8"))

# figure widths in inches: single column, double column, slide, poster panel
SIZES = {"single": (3.5, 2.5), "single_tall": (3.5, 3.2), "double": (7.2, 2.8), "double_tall": (7.2, 4.6),
         "slide": (10.0, 5.2), "slide_half": (4.9, 5.2), "poster": (12.0, 7.0), "square": (3.5, 3.5)}


class Vellum:
    def __init__(self, mode="light", scale=1.0):
        """mode: "light" or "dark". scale: multiplies every type size and line width; 1.0 for print, 2.2 for slides, 2.6 for posters."""
        self.mode, self.scale = mode, scale
        M = SPEC[mode]; N = M["neutrals"]
        self.surface, self.card, self.grid, self.rule = N["surface"], N["card"], N["grid"], N["rule"]
        self.muted, self.secondary, self.ink = N["muted"], N["secondary"], N["ink"]
        self.names = SPEC["order"]
        self._tone, self._tint, self._deep = M["tone"], M["tint"], M["deep"]
        self.sequential, self.diverging, self.status = M["sequential"], M["diverging"], M["status"]
        self.title_font, self.body_font, self.mono_font = SPEC["typography"]["title"], SPEC["typography"]["body"], SPEC["typography"]["mono"]
        mk = SPEC["marks"]; self.lw, self.thin, self.band_alpha = mk["line_pt"] * scale, mk["thin_line_pt"] * scale, mk["band_alpha"]
        self.dotted = (0, tuple(mk["dotted"]))
        self.sz = {k: v * scale for k, v in SPEC["sizes"].items()}

    # ---- colours by job
    def _idx(self, k):
        return self.names.index(k) if isinstance(k, str) else k

    def tone(self, k=0): return self._tone[self._idx(k)]
    def tint(self, k=0): return self._tint[self._idx(k)]
    def deep(self, k=0): return self._deep[self._idx(k)]
    def tones(self, n=None): return self._tone[:n] if n else list(self._tone)
    def tints(self, n=None): return self._tint[:n] if n else list(self._tint)

    def cmap(self, family="teal"):
        """Sequential colormap of one hue family, surface to deep."""
        return LinearSegmentedColormap.from_list(f"vellum_{family}", [self.surface] + self.sequential[family])

    def cmap_div(self):
        """Diverging colormap, terracotta to teal through a neutral midpoint."""
        return LinearSegmentedColormap.from_list("vellum_div", self.diverging)

    def listed(self, family="teal", n=7):
        return ListedColormap(self.sequential[family][:n])

    # ---- rcParams
    def rc(self):
        plt.rcdefaults()
        plt.rcParams.update({
            "font.family": [self.body_font, "Lato", "Segoe UI", "DejaVu Sans"], "font.size": self.sz["axis_label"],
            "mathtext.fontset": "stixsans",
            "figure.facecolor": self.surface, "axes.facecolor": self.surface, "savefig.facecolor": self.surface,
            "axes.edgecolor": self.grid, "axes.linewidth": 0.8,
            "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
            "axes.grid": True, "axes.grid.axis": "y", "grid.color": self.grid, "grid.linewidth": SPEC["marks"]["grid_pt"], "grid.linestyle": "-",
            "axes.axisbelow": True,
            "xtick.color": self.muted, "ytick.color": self.muted, "xtick.labelcolor": self.muted, "ytick.labelcolor": self.muted,
            "xtick.labelsize": self.sz["tick"], "ytick.labelsize": self.sz["tick"],
            "xtick.major.size": 0, "ytick.major.size": 0, "xtick.minor.size": 0, "ytick.minor.size": 0,
            "xtick.major.pad": 4, "ytick.major.pad": 2,
            "axes.labelcolor": self.muted, "axes.labelsize": self.sz["axis_label"], "text.color": self.ink,
            "axes.titlelocation": "left", "axes.titlesize": self.sz["panel_title"], "axes.titleweight": "bold", "axes.titlepad": 16,
            "axes.prop_cycle": matplotlib.cycler(color=self._tone),
            "lines.linewidth": self.lw, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
            "legend.frameon": False, "legend.fontsize": self.sz["annotation"],
            "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.08,
            "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        })
        return self

    def size(self, key="single"):
        return SIZES[key]

    # ---- anatomy helpers
    def title(self, fig, title, subtitle=None, source=None, x=0.02):
        """Claim title in the serif face, subtitle in muted text, footer with the source. Leaves room with top=0.80, bottom=0.14."""
        fig.text(x, 0.985, title, fontsize=self.sz["title"], fontfamily=self.title_font, color=self.ink, va="top", ha="left")
        if subtitle:
            # the subtitle sits one title height plus a gap below the title, whatever the figure height
            y_sub = 0.985 - (self.sz["title"] / 72) * 1.45 / fig.get_size_inches()[1]
            fig.text(x, y_sub, subtitle, fontsize=self.sz["subtitle"], color=self.muted, va="top", ha="left")
        if source: fig.text(x, 0.01, source, fontsize=self.sz["footer"], color=self.muted, va="bottom", ha="left")

    def panel(self, ax, letter=None, claim=None, unit=None):
        """Panel title (bold letter and claim) and a unit line above the axis in place of a rotated y label."""
        if claim is not None:
            ax.set_title((f"{letter}  " if letter else "") + claim, color=self.ink, pad=16 if unit else 8)
        if unit:
            ax.set_ylabel("")
            ax.text(0, 1.03, unit, transform=ax.transAxes, fontsize=self.sz["unit_line"], color=self.muted, va="bottom", ha="left")

    def endlabel(self, ax, x, y, text, color=None, dx=6):
        """Direct label at the end of a line, in ink, with a surface halo."""
        ax.annotate(text, (x, y), xytext=(dx, 0), textcoords="offset points", va="center", ha="left",
                    fontsize=self.sz["annotation"], color=self.ink, annotation_clip=False,
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=self.surface)])

    def endlabels(self, ax, points, texts, gap, x_text=None):
        """Several end labels pushed apart by `gap` (data units) with thin leader lines. points: list of (x, y)."""
        ys = spread([p[1] for p in points], gap)
        for (x0, y0), y, t in zip(points, ys, texts):
            ax.annotate(t, (x0, y0), xytext=(x_text if x_text is not None else x0, y), textcoords="data", va="center", ha="left",
                        fontsize=self.sz["annotation"], color=self.ink, annotation_clip=False,
                        arrowprops=dict(arrowstyle="-", color=self.muted, lw=0.5, shrinkA=0, shrinkB=3))

    def note(self, ax, x, y, text, ha="left", va="top", **kw):
        """A quiet annotation in muted text, in data coordinates."""
        ax.text(x, y, text, fontsize=self.sz["annotation"], color=self.muted, ha=ha, va=va, **kw)

    def callout(self, ax, xy, text, xytext, **kw):
        """An annotation in ink with a thin leader."""
        ax.annotate(text, xy, xytext=xytext, textcoords="offset points", fontsize=self.sz["annotation"], color=self.ink,
                    arrowprops=dict(arrowstyle="-", color=self.muted, lw=0.6, shrinkB=4), **kw)

    def dot(self, ax, x, y, color=None, s=None, z=4):
        """Marker ringed in the surface colour so it stays legible where it crosses a line."""
        ax.scatter(x, y, s=s or SPEC["marks"]["marker_pt2"] * self.scale ** 2, color=color or self.tone(0), edgecolor=self.surface,
                   linewidth=SPEC["marks"]["ring_pt"] * self.scale, zorder=z)

    def reference(self, ax, y=None, x=None, text=None, color=None):
        """A reference line (a bound, a prediction) as a thin dotted line with its label at the right end."""
        c = color or self.tone("ochre")
        if y is not None:
            ax.axhline(y, color=c, lw=self.thin, ls=self.dotted)
            if text: ax.annotate(text, (1, y), xycoords=("axes fraction", "data"), xytext=(-4, 4), textcoords="offset points",
                                 ha="right", va="bottom", fontsize=self.sz["annotation"], color=self.muted)
        if x is not None:
            ax.axvline(x, color=c, lw=self.thin, ls=self.dotted)
            if text: ax.annotate(text, (x, 1), xycoords=("data", "axes fraction"), xytext=(4, -4), textcoords="offset points",
                                 ha="left", va="top", fontsize=self.sz["annotation"], color=self.muted, rotation=90)

    def identity(self, ax, lim, text="y = x"):
        ax.plot(lim, lim, color=self.rule, lw=0.9, zorder=1)
        # the label sits on the diagonal of the axes box, which is the line when both axes have the same limits and scale
        # below the line, where the data points (which lie on it) are not
        ax.annotate(text, xy=(0.70, 0.70), xycoords="axes fraction", xytext=(0, -12), textcoords="offset points", color=self.muted,
                    fontsize=self.sz["annotation"], rotation=45, rotation_mode="anchor", ha="center", va="top")

    def heat_gaps(self, ax, nx, ny):
        """Surface-coloured gaps between the cells of a heat map."""
        for j in range(nx + 1): ax.axvline(j - 0.5, color=self.surface, lw=1.2)
        for i in range(ny + 1): ax.axhline(i - 0.5, color=self.surface, lw=1.2)
        ax.grid(False)
        for s in ax.spines.values(): s.set_visible(False)

    def colorbar(self, fig, im, ax, label):
        cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
        cb.outline.set_visible(False); cb.ax.tick_params(size=0, labelsize=self.sz["unit_line"], colors=self.muted)
        cb.set_label(label, color=self.muted, fontsize=self.sz["unit_line"])
        return cb

    def bars(self, ax, x, h, color=None, width=0.6, **kw):
        """Bars with the surface gap built in (the width leaves air) and no edge stroke."""
        return ax.bar(x, h, width=width, color=color or self.tone(0), edgecolor="none", **kw)

    # ---- gradients (multi-hue sequential scales; see "Vellum - colour gradients")
    def gradient(self, name="lagoon", n=9):
        """n colours along a named gradient (lagoon, ember, shore). The nine stored stops are OKLCH-built and 7 apart in dE,
        so interpolating in RGB between neighbouring stops stays on the gradient."""
        stops = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in SPEC["gradients"][name][self.mode]]) / 255.0
        pos = np.linspace(0, 1, len(stops)); t = np.linspace(0, 1, n)
        rgb = np.stack([np.interp(t, pos, stops[:, c]) for c in range(3)], axis=1)
        return ["#" + "".join(f"{int(round(v * 255)):02X}" for v in row) for row in rgb]

    def cmap_gradient(self, name="lagoon"):
        """A 256-step colormap of a named gradient. The lowest stop is not the surface; draw cells with no data in the card colour."""
        return LinearSegmentedColormap.from_list(f"vellum_{name}", self.gradient(name, 256), N=256)

    def gradient_bar(self, fig, im, ax, label, ticks=None):
        """The legend of a gradient: a thin bar without outline, three to five ticks, the unit in muted text."""
        cb = self.colorbar(fig, im, ax, label)
        if ticks is not None: cb.set_ticks(ticks)
        return cb

    # ---- three-dimensional axes (see "Vellum - 3D figures")
    def axes3d(self, fig, rect=(0.04, 0.08, 0.92, 0.72), elev=24, azim=-58, aspect=(1, 1, 0.62), labels=("x", "y", "z"), nticks=3):
        """Orthographic 3D axes with transparent panes, hairline grid, three ticks per axis and muted labels."""
        from matplotlib.ticker import MaxNLocator
        ax = fig.add_axes(rect, projection="3d")
        ax.set_proj_type("ortho"); ax.view_init(elev=elev, azim=azim); ax.set_box_aspect(aspect)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_pane_color((1, 1, 1, 0)); axis.pane.set_edgecolor(self.grid); axis.pane.set_linewidth(0.5)
            axis._axinfo["grid"].update(color=self.grid, linewidth=0.5, linestyle="-")
            axis._axinfo["axisline"].update(color=self.rule, linewidth=0.8)
            axis._axinfo["tick"].update(inward_factor=0.0, outward_factor=0.0)
            axis.set_major_locator(MaxNLocator(nticks)); axis.line.set_color(self.rule)
            axis.label.set_color(self.muted)
        ax.set_xlabel(labels[0], labelpad=-2); ax.set_ylabel(labels[1], labelpad=-2); ax.set_zlabel(labels[2], labelpad=-4)
        ax.tick_params(axis="both", which="major", pad=-3, labelsize=self.sz["tick"], labelcolor=self.muted)
        ax.tick_params(axis="z", pad=-1)
        ax.set_facecolor((1, 1, 1, 0))
        return ax

    def surface3d(self, ax, X, Y, Z, cmap=None, floor=True, levels=7, **kw):
        """A flat-shaded surface coloured by height (the colour repeats the z value), no mesh lines, with contour lines on the floor.
        The surface layer is rasterised so a PDF stays small and the text stays vector."""
        cm = cmap or self.cmap("teal")
        surf = ax.plot_surface(X, Y, Z, cmap=cm, linewidth=0, antialiased=False, shade=False, rstride=1, cstride=1, rasterized=True, **kw)
        if floor:
            zmin = float(np.min(Z)) - 0.06 * float(np.ptp(Z))
            ax.contour(X, Y, Z, zdir="z", offset=zmin, levels=levels, colors=self.rule, linewidths=0.5)
            ax.set_zlim(zmin, float(np.max(Z)))
        return surf

    def swatches(self, path=None):
        """A palette sheet for the record."""
        fig = plt.figure(figsize=(7.2, 3.2)); self.rc(); fig.set_facecolor(self.surface)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 7.2); ax.set_ylim(0, 3.2); ax.axis("off")
        ax.text(0.3, 2.95, f"Vellum · {self.mode}", fontsize=12, fontfamily=self.title_font, color=self.ink, va="center")
        ax.text(0.3, 2.65, f"surface {self.surface}  card {self.card}  grid {self.grid}  rule {self.rule}  muted {self.muted}  secondary {self.secondary}  ink {self.ink}",
                fontsize=6.5, color=self.muted, va="center")
        from matplotlib.patches import Rectangle
        for k, nm in enumerate(self.names):
            x = 0.3 + k * 1.12
            for row, col in enumerate((self.tint(k), self.tone(k), self.deep(k))):
                y = 1.75 - row * 0.5
                ax.add_patch(Rectangle((x, y), 1.0, 0.42, facecolor=col, edgecolor="none"))
                ax.text(x + 0.05, y + 0.06, col, fontsize=6.5, color=self.deep(k) if row == 0 else (self.surface if self.mode == "light" else self.ink) if row == 1 else (self.surface if self.mode == "light" else self.surface))
            ax.text(x, 2.23, nm, fontsize=8, color=self.ink, va="bottom")
        for k, (nm, col) in enumerate(self.status.items()):
            x = 0.3 + k * 0.6
            ax.add_patch(Rectangle((x, 0.3), 0.5, 0.3, facecolor=col, edgecolor="none")); ax.text(x, 0.65, nm, fontsize=6.5, color=self.muted)
        ax.text(3.0, 0.45, "status: reserved, always with an icon and a label", fontsize=6.5, color=self.muted, va="center")
        if path: fig.savefig(path); plt.close(fig)
        return fig


def spread(ys, gap):
    """Push label positions apart so that neighbours are at least `gap` apart; order preserved."""
    idx = np.argsort(ys); y = np.array(ys, float)[idx]
    for _ in range(50):
        for i in range(1, len(y)):
            if y[i] - y[i - 1] < gap: y[i] = y[i - 1] + gap
        for i in range(len(y) - 2, -1, -1):
            if y[i + 1] - y[i] < gap: y[i] = y[i + 1] - gap
    out = np.empty_like(y); out[idx] = y
    return out


def use(mode="light", scale=1.0):
    """Set the rcParams for the mode (and scale: 1.0 print, 2.2 slides, 2.6 posters) and return the palette object."""
    return Vellum(mode, scale).rc()


def stamp(repo=None):
    """Short git sha of `repo` (or the current directory) with -dirty when the tree is not clean, for the footer."""
    import subprocess
    try:
        sha = subprocess.run(["git", "-C", repo or ".", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo or ".", "status", "--porcelain"], capture_output=True, text=True).stdout.strip() != ""
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unstamped"
