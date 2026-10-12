// cvd_simulator.js: one sample figure in Vellum's tones and in a common default palette, seen with normal vision, under
// three colour-vision deficiencies and in greyscale.
//
// The figure: life expectancy of four regions, 1950 to 2023 (a line chart with end labels), and of six regions in 2023
// (a bar chart, one tone per region). A segmented control re-computes every series colour with V.simulate (Machado,
// Oliveira and Fernandes 2009 at full severity, or relative luminance for greyscale), so the page shows the colours a
// reader with that vision sees, not a CSS filter. Under each copy, the smallest distance between neighbouring colours
// in slot order, computed from the unrounded simulation as generators/colorlab.py does it, against its target.
import * as V from "../vellum-web.js";

const DATA = new URL("../../../data/owid-life-expectancy.csv", import.meta.url);
const TAB10 = ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", "#8C564B"];   // matplotlib's default, first six
const TAB_NAMES = ["blue", "orange", "green", "red", "purple", "brown"];
const REGIONS = [   // OWID entity, short label; slot order: the colour follows the region in both charts
  ["Africa", "Africa"], ["Asia", "Asia"], ["Europe", "Europe"], ["Latin America and the Caribbean", "Latin America"],
  ["Northern America", "Northern America"], ["Oceania", "Oceania"],
];
const LINES = 4;
const KINDS = [["normal", "normal vision"], ["protanopia", "protanopia"], ["deuteranopia", "deuteranopia"], ["tritanopia", "tritanopia"], ["greyscale", "greyscale"]];
const TARGET = { normal: 15, other: 8 };
const SOURCE = "UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), Riley (2005); processed by Our World in Data";

const CSS = `
.vcvd .seg { flex-wrap: wrap; border-radius: 18px; }
.vcvd .seg button { white-space: nowrap; }
.vcvd .panels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px 40px; }
.vcvd .panels.narrow { grid-template-columns: minmax(0, 1fr); }
.vcvd .panel { position: relative; min-width: 0; }
.vcvd .ptitle { font-weight: 700; color: var(--v-ink); font-size: 0.95rem; margin: 0 0 2px; }
.vcvd .ptitle b { margin-right: 8px; }
.vcvd .psub { color: var(--v-muted); font-size: 0.85rem; margin: 0 0 8px; }
.vcvd .readout { font-size: 0.92rem; color: var(--v-secondary); margin: 6px 0 0; line-height: 1.45; }
.vcvd .readout strong { font-variant-numeric: lining-nums; }
.vcvd .verdict { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.vcvd .verdict svg { flex: none; }
.vcvd .vnote { color: var(--v-muted); font-size: 0.88rem; margin: 18px 0 0; max-width: 80ch; }
.vcvd .hit:focus { outline: none; }
.vcvd .hit:focus-visible .focusring { stroke: var(--v-teal); stroke-width: 2; }
.vcvd details.data-table { margin-top: 20px; }
.vcvd details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; }
.vcvd details.data-table .table-wrap { margin: 12px 0 16px; }
`;

let dataPromise = null;

function parseCsv(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line) continue;
    const out = []; let cur = "", q = false;
    for (const ch of line) {
      if (ch === '"') q = !q;
      else if (ch === "," && !q) { out.push(cur); cur = ""; }
      else cur += ch;
    }
    out.push(cur); rows.push(out);
  }
  return rows;
}

// The six regions' series from 1950, and their 2023 values.
function load() {
  if (!dataPromise) dataPromise = fetch(DATA).then((r) => r.text()).then((t) => {
    const want = new Map(REGIONS.map(([e], i) => [e, i]));
    const series = REGIONS.map(() => []);
    for (const [ent, , yr, v] of parseCsv(t).slice(1)) {
      const i = want.get(ent), y = +yr;
      if (i !== undefined && y >= 1950) series[i].push([y, +v]);
    }
    series.forEach((s) => s.sort((a, b) => a[0] - b[0]));
    return { series, last: series.map((s) => s[s.length - 1]) };
  });
  return dataPromise;
}

// Linear RGB as a reader with this vision sees it, unrounded (V.simulate rounds to 8-bit hex for drawing).
function simLin(hex, kind) {
  const l = V.hexToRgb(hex).map(V.toLinear);
  if (kind === "normal") return l;
  if (kind === "greyscale") { const Y = 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]; return [Y, Y, Y]; }
  return V.CVD[kind].map((r) => Math.min(1, Math.max(0, r[0] * l[0] + r[1] * l[1] + r[2] * l[2])));
}
function dE(a, b, kind) {
  const p = V.linToOklab(simLin(a, kind)), q = V.linToOklab(simLin(b, kind));
  return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) * 100;
}
// Distances between neighbours in slot order, and the closest pair.
function neighbours(pal, kind) {
  const d = pal.slice(0, -1).map((h, i) => dE(h, pal[i + 1], kind));
  const i = d.indexOf(Math.min(...d));
  return { d, i, min: d[i] };
}

function verdict(parent, ok, P) {
  const v = V.el("span", { class: "verdict" }, parent);
  const s = V.svg(v, 14, 14);
  s.setAttribute("aria-hidden", "true");
  V.el("circle", { cx: 7, cy: 7, r: 7, fill: ok ? P.status.good : P.status.critical }, s);
  V.el("path", { d: ok ? "M3.8 7.2 6.1 9.4 10.3 4.8" : "M4.5 4.5 9.5 9.5M9.5 4.5 4.5 9.5", fill: "none", stroke: P.surface, "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
  V.el("span", {}, v, ok ? "passes" : "fails");
}

// One copy of the sample figure: the line chart over the bar chart, in the colours `pal` seen under `kind`.
function panel(parent, width, P, D, { pal, names, kind, letter, title, sub, claim }) {
  const box = V.el("div", { class: "panel" }, parent);
  const pt = V.el("p", { class: "ptitle" }, box);
  V.el("b", {}, pt, letter);
  pt.appendChild(document.createTextNode(title));
  V.el("p", { class: "psub" }, box, sub);
  const col = pal.map((h) => (kind === "normal" ? h : V.simulate(h, kind)));
  const tip = V.tooltip(box);
  const kindName = KINDS.find((k) => k[0] === kind)[1];

  // ---- line chart: four regions, 1950-2023
  const narrowLabels = width < 340;
  const m = { l: 34, r: narrowLabels ? 84 : 104, t: 30, b: 30 }, H = 230;
  const w = width - m.l - m.r, h = H - m.t - m.b;
  const lab = narrowLabels ? 104 : 118, bm = { l: lab, r: 40, t: 32 }, slot = 25, bh = 6 * slot;   // the bar chart below
  const s = V.svg(box, width, H + bm.t + bh + 24, {
    title: claim, desc: `Life expectancy at birth in ${REGIONS.slice(0, LINES).map((r) => r[1]).join(", ")}, 1950 to 2023, and in six regions in 2023, drawn in ${title.toLowerCase()} as seen with ${kindName}.`,
  });
  const g = V.el("g", { transform: `translate(${m.l},${m.t})` }, s);
  const x = V.linear([1950, 2023], [0, w]), y = V.linear([30, 82], [h, 0]);
  V.axes(g, P, { x, y, xticks: V.ticks(1950, 2023, 4), yticks: [40, 60, 80], xfmt: V.year, unit: "life expectancy at birth, years (axis from 30)", width: w, height: h });
  const lines = D.series.slice(0, LINES);
  lines.forEach((ser, i) => V.line(g, ser.map(([a, b]) => [x(a), y(b)]), col[i], { width: 2.2 }));
  lines.forEach((ser, i) => { const [a, b] = ser[ser.length - 1]; V.dot(g, x(a), y(b), col[i], P); });
  V.endLabels(g, lines.map((ser, i) => { const [a, b] = ser[ser.length - 1]; return { x: x(a), y: y(b), text: REGIONS[i][1] }; }), P, { gap: 15, size: 12.5 });

  // crosshair: snaps to the nearest year, one tooltip listing every region at that year
  const at = lines.map((ser) => new Map(ser));
  const cross = V.el("g", { "pointer-events": "none", visibility: "hidden" }, g);
  const hair = V.el("line", { y1: 0, y2: h, stroke: P.muted, "stroke-width": 0.75 }, cross);
  const marks = lines.map((_, i) => V.dot(cross, 0, 0, col[i], P, 4));
  const showYear = (yr) => {
    const px = x(yr);
    hair.setAttribute("x1", px); hair.setAttribute("x2", px);
    const rows = at.map((m, i) => ({ v: m.get(yr), i })).sort((a, b) => b.v - a.v);
    at.forEach((m, i) => { marks[i].setAttribute("cx", px); marks[i].setAttribute("cy", y(m.get(yr))); });
    cross.setAttribute("visibility", "visible");
    tip.show(m.l + px, s.getBoundingClientRect().top - box.getBoundingClientRect().top + m.t + y(rows[0].v), V.year(yr),
      rows.map((r) => ({ value: V.fmt(r.v, 1), label: REGIONS[r.i][1], color: col[r.i] })));
  };
  const hide = () => { cross.setAttribute("visibility", "hidden"); tip.hide(); };
  const hit = V.el("g", { class: "hit", tabindex: 0, role: "group", "aria-label": "Line chart: use the left and right arrow keys to read the values of each year" }, g);
  V.el("rect", { x: 0, y: 0, width: w, height: h, fill: "transparent" }, hit);
  V.el("rect", { class: "focusring", x: -4, y: -4, width: w + 8, height: h + 8, fill: "none", stroke: "none", rx: 6 }, hit);
  let cur = 2023;
  hit.addEventListener("pointermove", (e) => {
    const r = hit.getBoundingClientRect();
    cur = Math.min(2023, Math.max(1950, Math.round(x.invert(e.clientX - r.left))));
    showYear(cur);
  });
  hit.addEventListener("pointerleave", hide);
  hit.addEventListener("focus", () => showYear(cur));
  hit.addEventListener("blur", hide);
  hit.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, PageDown: -10, PageUp: 10 }[e.key];
    if (!step) return;
    e.preventDefault(); cur = Math.min(2023, Math.max(1950, cur + step)); showYear(cur);
  });

  // ---- bar chart: six regions in 2023, horizontal because the labels are words
  const bw = width - bm.l - bm.r;
  const bg = V.el("g", { transform: `translate(${bm.l},${H + bm.t})` }, s);
  const bx = V.linear([0, 85], [0, bw]);
  for (const t of [0, 20, 40, 60, 80]) V.text(bg, bx(t), bh + 14, V.fmt(t), P, { size: 12, color: P.muted, anchor: "middle" });   // no vertical grid
  V.text(bg, -lab, -14, "life expectancy in 2023, years", P, { size: 12.5, color: P.muted, baseline: "auto" });
  D.last.forEach(([, v], i) => {
    const cy = i * slot, b = V.el("g", { class: "hit", tabindex: 0, role: "img", "aria-label": `${REGIONS[i][0]}: ${V.fmt(v, 1)} years in 2023` }, bg);
    V.el("rect", { x: -lab, y: cy, width: bw + lab + bm.r, height: slot, fill: "transparent" }, b);
    const bar = V.el("rect", { x: 0, y: cy + slot * 0.2, width: bx(v), height: slot * 0.6, fill: col[i] }, b);
    V.el("rect", { class: "focusring", x: -lab, y: cy, width: bw + lab + bm.r - 4, height: slot, fill: "none", stroke: "none", rx: 4 }, b);
    V.text(b, -8, cy + slot / 2, REGIONS[i][1], P, { size: 12.5, anchor: "end" });
    V.text(b, bx(v) + 5, cy + slot / 2, V.fmt(v, 1), P, { size: 12 });
    const show = () => {
      bar.setAttribute("opacity", 0.8);
      const r = bar.getBoundingClientRect(), br = box.getBoundingClientRect();
      tip.show(r.right - br.left, r.top - br.top, "2023", [{ value: `${V.fmt(v, 1)} years`, label: REGIONS[i][0], color: col[i], kind: "rect" }]);
    };
    const off = () => { bar.removeAttribute("opacity"); tip.hide(); };
    b.addEventListener("pointerenter", show); b.addEventListener("pointerleave", off);
    b.addEventListener("focus", show); b.addEventListener("blur", off);
  });

  // ---- the readout: the closest neighbours under this vision, against the target
  const N = neighbours(pal, kind), target = kind === "normal" ? TARGET.normal : TARGET.other;
  const ro = V.el("p", { class: "readout" }, box);
  ro.appendChild(document.createTextNode(`Closest neighbours ${kind === "normal" ? "with normal vision" : "under " + kindName}: `));
  V.el("strong", {}, ro, V.fmt(N.min, 1));
  ro.appendChild(document.createTextNode(` (${names[N.i]} and ${names[N.i + 1]}) · ${kind === "normal" ? "floor" : "target"} ${target} · `));
  verdict(ro, N.min >= target, P);
  return N;
}

function draw(node, width, P, D, state) {
  const vel = P.tone, deut = { v: neighbours(vel, "deuteranopia"), t: neighbours(TAB10, "deuteranopia") };
  const claim = `Under deuteranopia a default palette's closest pair falls to ${V.fmt(deut.t.min, 1)}; Vellum's stays at ${V.fmt(deut.v.min, 1)}`;
  const plot = V.frame(node, {
    title: claim,
    subtitle: "The same figure in Vellum's tones and in a common default palette. Pick a kind of vision: every series colour is re-computed " +
      "as that reader sees it. Distances are ΔE in OKLab × 100 between neighbours in slot order. Hover or focus a chart for its values.",
    footer: `${SOURCE} · assets/js/interactive/cvd_simulator.js`,
  });
  const ctl = V.el("div", { class: "vfig-controls" }, plot);
  const seg = V.el("div", { class: "seg", role: "group", "aria-label": "Simulate colour vision" }, ctl);
  for (const [k, label] of KINDS) {
    const b = V.el("button", { type: "button", "aria-pressed": String(k === state.kind) }, seg, label);
    b.addEventListener("click", () => { state.kind = k; state.focus = k; draw(node, width, P, D, state); });
  }
  if (state.focus) { [...seg.children][KINDS.findIndex((k) => k[0] === state.focus)].focus(); state.focus = null; }

  const narrow = width < 760;
  const panels = V.el("div", { class: "panels" + (narrow ? " narrow" : "") }, plot);
  const pw = narrow ? width : Math.floor((width - 40) / 2);
  const NV = panel(panels, pw, P, D, { pal: vel, names: P.names, kind: state.kind, letter: "a", title: "Vellum tones", sub: "teal, terracotta, indigo, ochre, mauve, moss, in slot order", claim });
  const NT = panel(panels, pw, P, D, { pal: TAB10, names: TAB_NAMES, kind: state.kind, letter: "b", title: "A common default palette", sub: "the first six colours of matplotlib's tab10, as a counterexample", claim });

  // a quiet note on what the current view shows, computed
  const tv = state.kind === "normal" ? TARGET.normal : TARGET.other, okV = NV.min >= tv, okT = NT.min >= tv;
  let msg;
  if (okV && !okT) msg = `Here the default's ${TAB_NAMES[NT.i]} and ${TAB_NAMES[NT.i + 1]} are ${V.fmt(NT.min, 1)} apart, below the target of ${tv}; Vellum's closest pair keeps ${V.fmt(NV.min, 1)}, because it alternates lightness as well as hue.`;
  else if (!okV && !okT) msg = `Neither palette reaches ${tv} here (Vellum ${V.fmt(NV.min, 1)}, the default ${V.fmt(NT.min, 1)}). This is why a Vellum line ends in a direct label: identity never rests on colour alone.`;
  else if (okV && okT) msg = `Both palettes pass here (Vellum ${V.fmt(NV.min, 1)}, the default ${V.fmt(NT.min, 1)}). Try protanopia or deuteranopia, where red and green collapse.`;
  else msg = `Vellum's closest pair is ${V.fmt(NV.min, 1)} apart here and the default's ${V.fmt(NT.min, 1)}.`;
  V.el("p", { class: "vnote" }, plot, msg);

  // ---- the data, as tables
  const det = V.el("details", { class: "data-table" }, plot);
  V.el("summary", {}, det, "Show the data as a table");
  let wrap = V.el("div", { class: "table-wrap" }, det), tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, "Distance between neighbouring colours in slot order (ΔE, OKLab × 100), by kind of vision");
  let tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["palette", 0], ["pair", 0], ...KINDS.map(([, l]) => [l, 1])]) V.el("th", { class: r ? "r" : null }, tr, h);
  let body = V.el("tbody", {}, tb);
  for (const [pname, pal, names] of [["Vellum", vel, P.names], ["default", TAB10, TAB_NAMES]]) {
    const all = KINDS.map(([k]) => neighbours(pal, k));
    for (let i = 0; i < pal.length - 1; i++) {
      tr = V.el("tr", {}, body);
      V.el("td", {}, tr, pname);
      V.el("td", {}, tr, `${names[i]}, ${names[i + 1]}`);
      all.forEach((N) => V.el("td", { class: "r", style: N.i === i ? { fontWeight: 700 } : null }, tr, V.fmt(N.d[i], 1)));
    }
  }
  wrap = V.el("div", { class: "table-wrap" }, det); tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, "Life expectancy at birth, years, every ten years and in 2023");
  tr = V.el("tr", {}, V.el("thead", {}, tb));
  const yrs = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2023];
  V.el("th", {}, tr, "region");
  for (const yy of yrs) V.el("th", { class: "r" }, tr, V.year(yy));
  body = V.el("tbody", {}, tb);
  D.series.forEach((ser, i) => {
    tr = V.el("tr", {}, body);
    V.el("td", {}, tr, REGIONS[i][0]);
    const at = new Map(ser);
    for (const yy of yrs) V.el("td", { class: "r" }, tr, V.fmt(at.get(yy), 1));
  });
}

export async function mount(node) {
  if (!document.getElementById("vcvd-css")) V.el("style", { id: "vcvd-css" }, document.head, CSS);
  node.classList.add("vcvd");
  const D = await load();
  const state = { kind: "deuteranopia", focus: null };   // first paint shows the claim; the control goes back to normal vision
  V.responsive(node, (w, P) => draw(node, w, P, D, state));
}
