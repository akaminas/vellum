// penguins_scatter.js: the Palmer penguins as a scatter of two measures the reader chooses, with a least-squares line
// and the within-species correlation for each species. Data: docs/data/penguins.json (Gorman, Williams and Fraser 2014),
// the 342 birds with all four measures.
//
// Vellum rules on show: ringed dots in the species tones (Adelie teal, Chinstrap terracotta, Gentoo indigo: slot order,
// and a filter never repaints a survivor), fit lines in the tone, direct species labels instead of a legend, nearest-
// point hover within 24 px, highlight one species with the rest faded to the grid colour, a claim recomputed for the
// chosen axes, and Simpson's paradox stated and drawn (the pooled fit, dotted, in rule grey) when the pooled
// correlation has the opposite sign of every within-species one.

import * as V from "../vellum-web.js";

const NAME = "penguins_scatter";
const SOURCE = "Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0";
const SPECIES = ["Adelie", "Chinstrap", "Gentoo"];        // slots 1 to 3: teal, terracotta, indigo
const MEASURES = [
  { key: "Beak Length (mm)", name: "beak length", unit: "mm", d: 1 },
  { key: "Beak Depth (mm)", name: "beak depth", unit: "mm", d: 1 },
  { key: "Flipper Length (mm)", name: "flipper length", unit: "mm", d: 0 },
  { key: "Body Mass (g)", name: "body mass", unit: "g", d: 0 },
];
const SUB = "Palmer Archipelago, 2007–2009, 342 birds. Choose the two measures, switch species on and off, point at a bird " +
  "to read it; pointing at a species button highlights that species.";

// The shared look of the interactive figures: identical in every module, injected once by whichever loads first.
const COMMON_CSS = `
.vi details.data-table { margin: 14px 0 0; }
.vi details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; width: max-content; max-width: 100%; }
.vi details.data-table .table-wrap { margin: 10px 0 0; }
.vi details.data-table table { font-size: 0.88rem; width: auto; min-width: 50%; }
.vi details.data-table caption { padding-top: 6px; }
.vi .vi-head { font-weight: 700; font-size: 0.95rem; color: var(--v-ink); margin: 0 0 6px; }
.vi .vi-readout { color: var(--v-muted); font-size: 0.88rem; font-variant-numeric: lining-nums; }
.vi .vi-step { color: var(--v-secondary); font-size: 0.95rem; margin: 10px 0 0; min-height: 3em; max-width: 72ch; }
.vi .vi-stage { position: relative; }
.vi canvas { display: block; }
.vi .btn:disabled { opacity: 0.4; cursor: default; pointer-events: none; }`;

function injectStyle(id, css) {
  if (!document.getElementById("vi-common-style")) V.el("style", { id: "vi-common-style" }, document.head, COMMON_CSS);
  if (!document.getElementById(id)) V.el("style", { id }, document.head, css);
}

const PENG_CSS = `
.ps-field { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 8px; max-width: 100%; }
.ps-field label, .ps-label { color: var(--v-muted); font-size: 0.9rem; }
.ps-chip { display: inline-flex; align-items: center; gap: 8px; }
.ps-chip .ps-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; box-shadow: 0 0 0 1.5px var(--v-surface); }
.ps-chip[aria-pressed="true"] { background: var(--v-card); color: var(--v-ink); }
.ps-chip[aria-pressed="false"] { color: var(--v-muted); background: transparent; box-shadow: inset 0 0 0 1px var(--v-grid); }
.ps-chip[aria-pressed="false"] .ps-dot { opacity: 0.35; }
.ps-hit { cursor: crosshair; touch-action: pan-y; }`;

function table(parent, caption, head, rows) {
  const det = V.el("details", { class: "data-table" }, parent);
  V.el("summary", {}, det, "Show the data as a table");
  const t = V.el("table", {}, V.el("div", { class: "table-wrap" }, det));
  V.el("caption", {}, t, caption);
  const hr = V.el("tr", {}, V.el("thead", {}, t));
  head.forEach((h, k) => V.el("th", { class: k ? "r" : null, scope: "col" }, hr, h));
  const body = V.el("tbody", {}, t);
  for (const r of rows) {
    const tr = V.el("tr", {}, body);
    r.forEach((c, k) => V.el(k ? "td" : "th", { class: k ? "r" : null, scope: k ? null : "row" }, tr, c));
  }
  return det;
}

// least squares and Pearson's r of y on x
function fit(xs, ys) {
  const n = xs.length, mx = xs.reduce((a, b) => a + b, 0) / n, my = ys.reduce((a, b) => a + b, 0) / n;
  let sxx = 0, syy = 0, sxy = 0;
  for (let i = 0; i < n; i++) { const dx = xs[i] - mx, dy = ys[i] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; }
  const b = sxy / sxx;
  return { n, mx, my, b, a: my - b * mx, r: sxy / Math.sqrt(sxx * syy), lo: Math.min(...xs), hi: Math.max(...xs) };
}

export async function mount(node) {
  injectStyle("vi-peng-style", PENG_CSS);
  node.classList.add("vi");
  const raw = await (await fetch(new URL("../../../data/penguins.json", import.meta.url))).json();
  const birds = raw.filter((r) => MEASURES.every((m) => r[m.key] !== null && r[m.key] !== undefined));
  const sex = (s) => (s === "MALE" ? "male" : s === "FEMALE" ? "female" : "sex not recorded");
  const state = { x: 0, y: 1, on: new Set(SPECIES), focus: null, hover: null };
  let P = null, width = 0, paint = () => {};

  // ---- skeleton
  const plot = V.frame(node, { title: " ", subtitle: SUB, footer: `${SOURCE} · assets/js/interactive/${NAME}.js` });
  const titleEl = node.querySelector(".vfig-title");
  const controls = V.el("div", { class: "vfig-controls" });
  plot.before(controls);
  const select = (axis, label) => {
    const f = V.el("span", { class: "ps-field" }, controls);
    V.el("label", { for: `${NAME}-${axis}` }, f, label);
    const s = V.el("select", { id: `${NAME}-${axis}` }, f);
    MEASURES.forEach((m, k) => V.el("option", { value: k }, s, `${m.name}, ${m.unit}`));
    s.value = state[axis];
    s.addEventListener("change", () => {
      const k = +s.value, other = axis === "x" ? "y" : "x";
      if (k === state[other]) { state[other] = state[axis]; selects[other].value = state[other]; }   // never the same measure twice
      state[axis] = k; state.hover = null; draw();
    });
    return s;
  };
  const selects = { x: select("x", "Across"), y: select("y", "Up") };
  const chipRow = V.el("span", { class: "ps-field", role: "group", "aria-label": "Species" }, controls);
  V.el("span", { class: "ps-label" }, chipRow, "Species");
  const chips = SPECIES.map((sp) => {
    const b = V.el("button", { type: "button", class: "chip ps-chip", "aria-pressed": "true" }, chipRow);
    const dot = V.el("span", { class: "ps-dot" }, b);
    V.el("span", {}, b, sp);
    b.addEventListener("click", () => {
      if (state.on.has(sp) && state.on.size === 1) return;   // one species always stays on
      state.on.has(sp) ? state.on.delete(sp) : state.on.add(sp);
      b.setAttribute("aria-pressed", state.on.has(sp)); state.hover = null; draw();
    });
    const hi = (on) => { const f = on && state.on.has(sp) ? sp : null; if (f !== state.focus) { state.focus = f; paint(); } };
    b.addEventListener("pointerenter", () => hi(true));
    b.addEventListener("pointerleave", () => hi(false));
    b.addEventListener("focus", () => hi(true));
    b.addEventListener("blur", () => hi(false));
    return { sp, b, dot };
  });
  const noteEl = V.el("p", { class: "vi-step" });
  plot.after(noteEl);
  let tableNode = null;

  const measure = (() => { const c = document.createElement("canvas").getContext("2d"); return (s) => { c.font = `13px ${P.fontBody}`; return c.measureText(s).width; }; })();
  const r2 = (r) => V.fmt(r, 2);

  function claim(fits, pooled, X, Y) {
    const shown = SPECIES.filter((s) => state.on.has(s)), rs = shown.map((s) => fits[s].r);
    const lo = Math.min(...rs), hi = Math.max(...rs), up = lo > 0, down = hi < 0;
    const range = lo === hi ? `r = ${r2(lo)}` : `r = ${r2(lo)} to ${r2(hi)}`;
    if (shown.length === 1) return `In ${shown[0]} penguins, ${Y} ${up ? "rises" : down ? "falls" : "barely moves"} with ${X}, ${range}`;
    const simpson = (up && pooled.r < 0) || (down && pooled.r > 0);
    if (simpson) return `${Y[0].toUpperCase() + Y.slice(1)} ${up ? "rises" : "falls"} with ${X} within each species, yet pooled r is ${r2(pooled.r)}`;
    if (up || down) return `Within each species, ${Y} ${up ? "rises" : "falls"} with ${X}, ${range}`;
    return `${Y[0].toUpperCase() + Y.slice(1)} and ${X} go different ways by species, ${range}`;
  }

  function draw() {
    if (!P) return;
    const mx = MEASURES[state.x], my = MEASURES[state.y];
    const X = (b) => b[mx.key], Y = (b) => b[my.key];
    const color = (sp) => P.tone[SPECIES.indexOf(sp)];
    const shown = birds.filter((b) => state.on.has(b.Species));
    const fits = Object.fromEntries(SPECIES.map((s) => { const bs = birds.filter((b) => b.Species === s); return [s, fit(bs.map(X), bs.map(Y))]; }));
    const pooled = fit(shown.map(X), shown.map(Y));
    const rs = SPECIES.filter((s) => state.on.has(s)).map((s) => fits[s].r);
    const simpson = state.on.size > 1 && (rs.every((r) => r > 0) && pooled.r < 0 || rs.every((r) => r < 0) && pooled.r > 0);
    titleEl.textContent = claim(fits, pooled, mx.name, my.name);
    chips.forEach(({ sp, dot }) => { dot.style.background = color(sp); });
    noteEl.textContent = "Lines: least-squares fit per species; r is the correlation within a species. " + (simpson
      ? `Simpson's paradox: pooled over the species shown, r = ${r2(pooled.r)} (the dotted grey line), the opposite sign of every within-species r.`
      : `Pooled over the species shown, r = ${r2(pooled.r)}.`);

    // axes from every bird, so switching a species off never rescales the plot
    const pad = (lo, hi) => [lo - (hi - lo) * 0.04, hi + (hi - lo) * 0.04];
    const [x0, x1] = pad(...V.extent(birds.map(X))), [y0, y1] = pad(...V.extent(birds.map(Y)));
    const narrow = width < 560;
    const m = { l: mx.unit === "g" || my.unit === "g" ? 46 : 36, t: 30, b: 44, r: 14 };
    const H = Math.round(Math.min(480, Math.max(320, width * 0.58))), iw = width - m.l - m.r, ih = H - m.t - m.b;
    const x = V.linear([x0, x1], [0, iw]), y = V.linear([y0, y1], [ih, 0]);
    V.clear(plot);
    const svg = V.svg(plot, width, H, { title: titleEl.textContent, desc: SPECIES.filter((s) => state.on.has(s)).map((s) => `${s}: r = ${r2(fits[s].r)}, n = ${fits[s].n}`).join("; ") + `; pooled r = ${r2(pooled.r)}.` });
    svg.setAttribute("tabindex", 0);
    svg.setAttribute("aria-label", `${titleEl.textContent}. Use the arrow keys to step from bird to bird.`);
    const g = V.el("g", { transform: `translate(${m.l},${m.t})` }, svg);
    const fx = (v, mm) => V.fmt(v, mm.unit === "g" ? 0 : Number.isInteger(v) ? 0 : 1);
    V.axes(g, P, { x, y, xticks: V.ticks(x0, x1, narrow ? 3 : 5), yticks: V.ticks(y0, y1, 4), xfmt: (v) => fx(v, mx), yfmt: (v) => fx(v, my),
      unit: `${my.name}, ${my.unit}`, xlabel: `${mx.name}, ${mx.unit}`, width: iw, height: ih });

    const order = SPECIES.filter((s) => state.on.has(s));
    if (simpson) {
      const yy = (v) => y(pooled.a + pooled.b * v), xs = [Math.max(x0, pooled.lo), Math.min(x1, pooled.hi)];
      V.line(g, xs.map((v) => [x(v), yy(v)]), P.rule, { width: 1.6, dash: "0.01 4" });
    }
    const layer = Object.fromEntries(order.map((sp) => [sp, V.el("g", {}, g)]));   // one group per species: dots, then its line
    for (const sp of order) for (const b of shown) if (b.Species === sp) V.dot(layer[sp], x(X(b)), y(Y(b)), color(sp), P, 3.6);
    const segs = {};
    for (const sp of order) {
      const f = fits[sp];
      segs[sp] = [f.lo, f.hi].map((v) => [x(v), y(f.a + f.b * v)]);
      V.line(layer[sp], segs[sp], color(sp));
    }
    // species labels at one end of their fit line: of six places (either end; on, above or below the line) each takes
    // the one that covers the fewest dots and other lines, inside the plot, and never another label
    const placed = [], pts = shown.map((b) => [x(X(b)), y(Y(b))]);
    for (const sp of order) {
      const text = `${sp}, r = ${r2(fits[sp].r)}`, w = measure(text), [a, b] = segs[sp];
      // places are pulled inside the plot before they are scored, so a label never ends past an edge
      const clamp = (c) => ({ ...c, x: c.anchor === "start" ? Math.min(c.x, iw - w) : Math.max(c.x, w), y: Math.max(9, Math.min(ih - 9, c.y)) });
      const cands = [0, -13, 13].flatMap((dy) => [{ x: b[0] + 8, y: b[1] + dy, anchor: "start" }, { x: a[0] - 8, y: a[1] + dy, anchor: "end" }]).map(clamp);
      const box = (c) => [c.anchor === "start" ? c.x : c.x - w, c.y - 8, w, 16];
      const inside = ([bx, by, bw, bh], [px, py], r = 0) => px > bx - r && px < bx + bw + r && py > by - r && py < by + bh + r;
      const cost = (c) => {
        const bb = box(c);
        let n = 0;
        if (placed.some((p) => !(bb[0] > p[0] + p[2] || p[0] > bb[0] + bb[2] || bb[1] > p[1] + p[3] || p[1] > bb[1] + bb[3]))) n += 1e4;
        n += pts.filter((p) => inside(bb, p, 3)).length;
        for (const o of order) for (let k = 0; k <= 20; k++) {
          const [s0, s1] = segs[o], q = [s0[0] + ((s1[0] - s0[0]) * k) / 20, s0[1] + ((s1[1] - s0[1]) * k) / 20];
          if (o === sp ? inside(bb, q) : inside(bb, q, 8)) n += o === sp ? 1 : 3;   // keep clear of other species' lines
        }
        return n + Math.abs(c.y - (c.anchor === "start" ? b[1] : a[1])) / 26;   // a small preference for sitting on the line
      };
      const best = cands.reduce((p, c) => (cost(c) < cost(p) ? c : p));
      placed.push(box(best));
      const t = V.text(g, best.x, best.y, text, P, { size: 13, anchor: best.anchor });
      t.setAttribute("stroke", P.surface); t.setAttribute("stroke-width", 3); t.setAttribute("paint-order", "stroke"); t.setAttribute("stroke-linejoin", "round");
    }
    if (simpson) {
      const lx = Math.min(x1, pooled.hi), lyp = y(pooled.a + pooled.b * lx);
      const t = V.note(g, x(lx) - 4, lyp - 8, `pooled, r = ${r2(pooled.r)}`, P, { anchor: "end", baseline: "auto" });
      t.setAttribute("stroke", P.surface); t.setAttribute("stroke-width", 3); t.setAttribute("paint-order", "stroke");
    }

    // highlight: the pointed species keeps its tone and comes to the front, the others fade to the grid colour
    paint = () => {
      for (const sp of order) {
        const c = state.focus && sp !== state.focus ? P.grid : color(sp);
        for (const el of layer[sp].children) el.setAttribute(el.tagName === "circle" ? "fill" : "stroke", c);
      }
      if (state.focus && layer[state.focus]) g.insertBefore(layer[state.focus], layer[order[order.length - 1]].nextSibling);
      else order.forEach((sp, k) => k && g.insertBefore(layer[sp], layer[order[k - 1]].nextSibling));
    };
    paint();

    // nearest bird within 24 px, ringed in ink, with all four measures, the island and the sex in the tooltip
    const tip = V.tooltip(plot), mark = V.el("g", { "pointer-events": "none" }, g);
    const byX = shown.slice().sort((a, b) => X(a) - X(b) || Y(a) - Y(b));
    const show = (b) => {
      state.hover = b; V.clear(mark);
      if (!b) { tip.hide(); return; }
      const px = x(X(b)), py = y(Y(b));
      V.el("circle", { cx: px, cy: py, r: 7.5, fill: "none", stroke: P.ink, "stroke-width": 1.5 }, mark);
      tip.show(m.l + px, m.t + py, `${b.Species}, ${b.Island}, ${sex(b.Sex)}`, MEASURES.map((mm) => ({
        value: `${V.fmt(b[mm.key], mm.unit === "g" ? 0 : mm.d)} ${mm.unit}`, label: mm.name,
        color: mm === mx || mm === my ? color(b.Species) : null })));
    };
    const hit = V.el("rect", { width: iw, height: ih, fill: "transparent", class: "ps-hit" }, g);
    const nearest = (e) => {
      const r = svg.getBoundingClientRect(), px = e.clientX - r.left - m.l, py = e.clientY - r.top - m.t;
      let best = null, bd = 24 * 24;
      for (const b of shown) { const d = (x(X(b)) - px) ** 2 + (y(Y(b)) - py) ** 2; if (d < bd) { bd = d; best = b; } }
      return best;
    };
    hit.addEventListener("pointermove", (e) => show(nearest(e)));
    hit.addEventListener("pointerdown", (e) => show(nearest(e)));
    hit.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") show(null); });
    svg.addEventListener("focus", () => show(state.hover || byX[0]));
    svg.addEventListener("blur", () => show(null));
    svg.addEventListener("keydown", (e) => {
      const d = { ArrowRight: 1, ArrowLeft: -1, ArrowUp: 1, ArrowDown: -1 }[e.key];
      if (e.key === "Escape") { show(null); return; }
      if (!d) return;
      e.preventDefault();
      const i = state.hover ? byX.indexOf(state.hover) : -1;
      show(byX[Math.max(0, Math.min(byX.length - 1, i + d))]);
    });
    if (state.hover && shown.includes(state.hover)) show(state.hover);

    // the table: per species for the chosen pair, then pooled
    const open = tableNode?.open;
    tableNode?.remove();
    const sig = (v) => V.fmt(v, Math.max(0, 2 - Math.floor(Math.log10(Math.abs(v)))));   // three significant digits
    const row = (name, f) => [name, String(f.n), fx(f.mx, mx), fx(f.my, my), r2(f.r), sig(f.b)];
    tableNode = table(node, `Means, within-species correlation and least-squares slope of ${my.name} on ${mx.name}`,
      ["species", "birds", `mean ${mx.name}, ${mx.unit}`, `mean ${my.name}, ${my.unit}`, "r", `slope, ${my.unit} per ${mx.unit}`],
      [...SPECIES.filter((s) => state.on.has(s)).map((s) => row(s, fits[s])), row("pooled", pooled)]);
    tableNode.open = !!open;
  }

  await document.fonts?.ready;
  V.responsive(node, (w, palette) => { width = w; P = palette; draw(); });
}
