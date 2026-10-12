// vellum-web.js: the Vellum figure style for SVG on the web.
//
// The colours come from vellum.json (the same file every other tool is generated from), so a web figure and a
// matplotlib figure share their values exactly. The helpers are the anatomy of a Vellum figure as functions:
// hairline horizontal grid, bottom spine in the grid colour, muted ticks without marks, a unit line in place of a
// rotated y label, ringed dots, direct end labels pushed apart with leaders, and a tooltip that leads with the value.
//
//   import * as V from "./vellum-web.js";
//   const P = await V.palette();                 // the current twin (light or dark), from <html data-theme>
//   V.responsive(el, (width) => draw(el, width, P));   // redraws on resize and on theme change
//
// Every interactive figure on the site is built on this module.

// On this site vellum.json sits one folder up from the module. Elsewhere, call V.load("path/to/vellum.json") first.
const SPEC_URL = new URL("../vellum.json", import.meta.url);
let specPromise = null;

export function load(url) {
  specPromise = fetch(url).then((r) => r.json());
  return specPromise;
}

export function spec() {
  if (!specPromise) specPromise = fetch(SPEC_URL).then((r) => r.json());
  return specPromise;
}

export function mode() {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

// The palette of one twin, by job. tone for lines and dots, tint for areas, deep for emphasis and text on a tint.
export async function palette(m = mode()) {
  const S = await spec();
  const M = S[m];
  const N = M.neutrals;
  const P = {
    mode: m, names: S.order, ...N,
    tone: M.tone, tint: M.tint, deep: M.deep,
    sequential: M.sequential, diverging: M.diverging, status: M.status,
    gradients: Object.fromEntries(Object.entries(S.gradients).map(([k, g]) => [k, g[m]])),
    marks: S.marks, sizes: S.sizes,
    fontTitle: S.typography.web.title, fontBody: S.typography.web.body,
  };
  P.family = (name) => S.order.indexOf(name);
  return P;
}

// ---------------------------------------------------------------- theme

export function onTheme(cb) {
  const obs = new MutationObserver(() => cb(mode()));
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => obs.disconnect();
}

// Redraw `draw(width, palette)` when the container is resized or the twin changes. Returns a function that redraws.
export function responsive(el, draw) {
  let last = -1, busy = false;
  const run = async (force) => {
    const w = Math.round(el.clientWidth);
    if (!force && (w === last || busy)) return;
    busy = true; last = w;
    try { await draw(w, await palette()); } finally { busy = false; }
  };
  new ResizeObserver(() => run(false)).observe(el);
  onTheme(() => run(true));
  run(true);
  return () => run(true);
}

// ---------------------------------------------------------------- DOM and SVG

const NS = "http://www.w3.org/2000/svg";

export function el(tag, attrs = {}, parent = null, text = null) {
  const svgTags = /^(svg|g|path|line|rect|circle|text|tspan|polyline|polygon|defs|pattern|clipPath|title|desc|linearGradient|stop|ellipse|use|mask|filter|feColorMatrix|image|foreignObject)$/;
  const node = svgTags.test(tag) ? document.createElementNS(NS, tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "style" && typeof v === "object") Object.assign(node.style, v);
    else if (k === "class") node.setAttribute("class", v);
    else node.setAttribute(k, v);
  }
  if (text !== null) node.textContent = text;     // labels are data: always textContent, never innerHTML
  if (parent) parent.appendChild(node);
  return node;
}

export function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }

// An SVG of the given size inside `parent`, with a <title> and <desc> for screen readers. A figure whose marks take
// keyboard focus passes role "group", so its children stay reachable; a picture keeps "img".
export function svg(parent, width, height, { title = "", desc = "", role = "img" } = {}) {
  const s = el("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role, class: "vsvg" }, parent);
  if (title) el("title", {}, s, title);
  if (desc) el("desc", {}, s, desc);
  return s;
}

// The title block and footer around a figure, in HTML so they wrap on a phone. Returns the plot container.
export function frame(parent, { title, subtitle, footer } = {}) {
  clear(parent);
  if (title) el("p", { class: "vfig-title" }, parent, title);
  if (subtitle) el("p", { class: "vfig-subtitle" }, parent, subtitle);
  const plot = el("div", { class: "vfig-plot" }, parent);
  if (footer) el("p", { class: "vfig-footer" }, parent, footer);
  return plot;
}

// ---------------------------------------------------------------- scales, ticks, numbers

export function linear([d0, d1], [r0, r1]) {
  const k = (r1 - r0) / ((d1 - d0) || 1);
  const f = (x) => r0 + (x - d0) * k;
  f.invert = (y) => d0 + (y - r0) / k;
  f.domain = [d0, d1]; f.range = [r0, r1];
  return f;
}

// Three to five ticks at round numbers.
export function ticks(lo, hi, n = 4) {
  const span = hi - lo;
  if (!(span > 0)) return [lo];
  const raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n + 0.5) || 10 * mag;
  const out = [];
  for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

export function extent(values) {
  let lo = Infinity, hi = -Infinity;
  for (const v of values) if (Number.isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; }
  return [lo, hi];
}

// Numbers as text: a true minus sign, a comma for thousands, a fixed number of decimals.
export function fmt(v, digits = 0) {
  if (!Number.isFinite(v)) return "–";
  const s = Math.abs(v).toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return (v < 0 ? "−" : "") + s;
}

// Years and other labels that are names rather than quantities: no thousands separator.
export const year = (v) => String(Math.round(v));

// ---------------------------------------------------------------- the anatomy

// Text at a type size of the style (pixels on screen), in the body face, coloured by its job.
export function text(parent, x, y, str, P, { size = 13, color, anchor = "start", baseline = "middle", weight, font, cls } = {}) {
  return el("text", {
    x, y, "text-anchor": anchor, "dominant-baseline": baseline, "font-size": size, "font-weight": weight,
    "font-family": font || P.fontBody, fill: color || P.ink, class: cls,
  }, parent, str);
}

// Plot area with Vellum axes: hairline horizontal grid at the y ticks, bottom spine in the grid colour, tick labels in
// muted without tick marks, the unit line above the y axis (never a rotated label), the x label under the axis.
export function axes(g, P, { x, y, xticks, yticks, xfmt = (v) => fmt(v), yfmt = (v) => fmt(v), unit, xlabel, width, height, grid = true }) {
  const ax = el("g", { class: "vaxes" }, g);
  if (grid) for (const t of yticks) {
    el("line", { x1: 0, x2: width, y1: y(t), y2: y(t), stroke: P.grid, "stroke-width": 1, "shape-rendering": "crispEdges" }, ax);
  }
  el("line", { x1: 0, x2: width, y1: height, y2: height, stroke: P.grid, "stroke-width": 1.3, "shape-rendering": "crispEdges" }, ax);
  for (const t of yticks) text(ax, -8, y(t), yfmt(t), P, { size: 12, color: P.muted, anchor: "end" });
  for (const t of xticks) text(ax, x(t), height + 16, xfmt(t), P, { size: 12, color: P.muted, anchor: "middle" });
  if (unit) text(ax, 0, -14, unit, P, { size: 12.5, color: P.muted, baseline: "auto" });
  if (xlabel) text(ax, width / 2, height + 38, xlabel, P, { size: 13, color: P.muted, anchor: "middle" });
  return ax;
}

// A marker ringed in the surface colour, so it stays legible where it crosses a line.
export function dot(g, cx, cy, color, P, r = 4.5) {
  return el("circle", { cx, cy, r, fill: color, stroke: P.surface, "stroke-width": 1.8 }, g);
}

// A line through points [[x, y], ...] in data space, already scaled by the caller's x and y.
export function path(points) {
  let d = "", pen = false;
  for (const [px, py] of points) {
    if (!Number.isFinite(px) || !Number.isFinite(py)) { pen = false; continue; }
    d += (pen ? "L" : "M") + px.toFixed(2) + "," + py.toFixed(2); pen = true;
  }
  return d;
}

export function line(g, points, color, { width = 2.2, dash, opacity } = {}) {
  return el("path", {
    d: path(points), fill: "none", stroke: color, "stroke-width": width, "stroke-linecap": "round",
    "stroke-linejoin": "round", "stroke-dasharray": dash, opacity,
  }, g);
}

// A band between lo and hi (arrays of [x, y]) in the tint at the band opacity, no edge.
export function band(g, lo, hi, color, P, opacity) {
  const pts = lo.concat(hi.slice().reverse());
  return el("path", { d: path(pts) + "Z", fill: color, opacity: opacity ?? P.marks.band_alpha, stroke: "none" }, g);
}

// A dotted reference line with its label at the right end, above the line, in muted.
export function reference(g, P, { y, x1, x2, label, color }) {
  // dotted, 1 on 3 off: a zero-length dash with a round cap draws a dot
  el("line", { x1, x2, y1: y, y2: y, stroke: color || P.tone[3], "stroke-width": 1.4, "stroke-dasharray": "0.01 4", "stroke-linecap": "round" }, g);
  if (label) text(g, x2, y - 7, label, P, { size: 12, color: P.muted, anchor: "end", baseline: "auto" });
}

// Push label positions apart so neighbours are at least `gap` apart, order kept (same algorithm as vellum.py).
export function spread(ys, gap) {
  const idx = ys.map((_, i) => i).sort((a, b) => ys[a] - ys[b]);
  const y = idx.map((i) => ys[i]);
  for (let it = 0; it < 50; it++) {
    for (let i = 1; i < y.length; i++) if (y[i] - y[i - 1] < gap) y[i] = y[i - 1] + gap;
    for (let i = y.length - 2; i >= 0; i--) if (y[i + 1] - y[i] < gap) y[i] = y[i + 1] - gap;
  }
  const out = new Array(ys.length);
  idx.forEach((i, k) => { out[i] = y[k]; });
  return out;
}

// Direct labels at line ends: items [{x, y, text}] in pixels. Labels pushed apart get a 0.5 pt leader in muted.
export function endLabels(g, items, P, { gap = 16, dx = 10, size = 13 } = {}) {
  const ys = spread(items.map((d) => d.y), gap);
  items.forEach((d, i) => {
    const ty = ys[i];
    if (Math.abs(ty - d.y) > 1.5) {
      el("polyline", { points: `${d.x + 6},${d.y} ${d.x + dx - 2},${ty}`, fill: "none", stroke: P.muted, "stroke-width": 0.75 }, g);
    }
    text(g, d.x + dx, ty, d.text, P, { size, color: P.ink });
  });
}

// A quiet note in muted at annotation size.
export function note(g, x, y, str, P, opts = {}) {
  return text(g, x, y, str, P, { size: 12, color: P.muted, ...opts });
}

// ---------------------------------------------------------------- tooltip

// One tooltip per figure. Rows lead with the value (strong, ink) and follow with the label (muted); a row is keyed by a
// short stroke of the series colour (a line key), or a small square for areas and cells.
export function tooltip(container) {
  container.style.position = container.style.position || "relative";
  const tip = el("div", { class: "vtip", role: "status", "aria-live": "polite" }, container);
  tip.hidden = true;
  return {
    show(px, py, heading, rows) {
      clear(tip);
      if (heading) el("div", { class: "vtip-head" }, tip, heading);
      for (const r of rows) {
        const row = el("div", { class: "vtip-row" }, tip);
        const key = el("span", { class: "vtip-key" + (r.kind === "rect" ? " rect" : "") }, row);
        key.style.background = r.color || "transparent";
        el("strong", {}, row, r.value);
        if (r.label) el("span", { class: "vtip-label" }, row, r.label);
      }
      tip.hidden = false;
      const cw = container.clientWidth, tw = tip.offsetWidth, th = tip.offsetHeight;
      let left = px + 14, top = py - th - 10;
      if (left + tw > cw) left = px - tw - 14;
      if (left < 0) left = 4;
      if (top < 0) top = py + 16;
      tip.style.left = left + "px"; tip.style.top = top + "px";
    },
    hide() { tip.hidden = true; },
  };
}

// ---------------------------------------------------------------- colour science (OKLab, CVD, contrast)
// The same formulas as generators/colorlab.py: OKLab (Ottosson 2020), Machado, Oliveira and Fernandes (2009) at
// severity 1 in linear RGB, ΔE as the OKLab distance times 100, WCAG relative-luminance contrast.

export const hexToRgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
export const rgbToHex = (rgb) => "#" + rgb.map((c) => Math.round(Math.min(1, Math.max(0, c)) * 255).toString(16).padStart(2, "0")).join("").toUpperCase();
export const toLinear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
export const toGamma = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * Math.max(c, 0) ** (1 / 2.4) - 0.055);

const mul = (M, v) => M.map((r) => r[0] * v[0] + r[1] * v[1] + r[2] * v[2]);
const M1 = [[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]];
const M2 = [[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]];
const M2i = [[1, 0.3963377774, 0.2158037573], [1, -0.1055613458, -0.0638541728], [1, -0.0894841775, -1.2914855480]];
const M1i = [[4.0767416621, -3.3077115913, 0.2309699292], [-1.2684380046, 2.6097574011, -0.3413193965], [-0.0041960863, -0.7034186147, 1.7076147010]];

export const linToOklab = (lin) => mul(M2, mul(M1, lin).map(Math.cbrt));
export const oklabToLin = (lab) => mul(M1i, mul(M2i, lab).map((c) => c ** 3));
export const hexToOklab = (h) => linToOklab(hexToRgb(h).map(toLinear));
export function hexToOklch(h) {
  const [L, a, b] = hexToOklab(h);
  return [L, Math.hypot(a, b), ((Math.atan2(b, a) * 180) / Math.PI + 360) % 360];
}
export function oklchToHex(L, C, H) {
  const r = (H * Math.PI) / 180;
  return rgbToHex(oklabToLin([L, C * Math.cos(r), C * Math.sin(r)]).map(toGamma));
}

export const CVD = {
  protanopia: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deuteranopia: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
  tritanopia: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
};

export function simulate(h, kind) {
  const lin = hexToRgb(h).map(toLinear);
  if (kind === "greyscale") {
    const Y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
    return rgbToHex([Y, Y, Y].map(toGamma));
  }
  if (!CVD[kind]) return h;
  return rgbToHex(mul(CVD[kind], lin).map((c) => toGamma(Math.min(1, Math.max(0, c)))));
}

export function deltaE(h1, h2) {
  const a = hexToOklab(h1), b = hexToOklab(h2);
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) * 100;
}

export function luminance(h) {
  const [r, g, b] = hexToRgb(h).map(toLinear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(h1, h2) {
  const a = luminance(h1), b = luminance(h2);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

// n colours along a list of stops, interpolated in RGB between neighbouring stops (as vellum.py does: the stored stops
// are close enough in OKLab that RGB interpolation between them stays on the gradient).
export function ramp(stops, t) {
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(x)), f = x - i;
  const a = hexToRgb(stops[i]), b = hexToRgb(stops[i + 1]);
  return rgbToHex(a.map((c, k) => c + (b[k] - c) * f));
}

// A copy-to-clipboard helper with a short confirmation in the element's own text.
export async function copy(str, node) {
  let said = "copied";
  try { await navigator.clipboard.writeText(str); } catch { said = "copy blocked"; }
  if (!node) return;
  const old = node.getAttribute("data-copied");
  node.setAttribute("data-copied", said);
  setTimeout(() => (old ? node.setAttribute("data-copied", old) : node.removeAttribute("data-copied")), 1100);
}
