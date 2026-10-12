// disasters_heat.js: deaths from natural disasters by type and decade, 1900s to 2010s, as a heat map on the lagoon
// gradient with a log scale. Data: docs/data/disasters.csv (EM-DAT, CRED / UCLouvain; processed by Our World in Data),
// without its "All natural disasters" rows.
//
// Vellum rules on show (1325.10, 1338.12, 1338.13): one named gradient for magnitude, applied across cells and never
// inside one; 1.2 pt surface gaps between cells; a cell with no record in the card colour with a terracotta hatch, never
// a stop of the gradient; a legend bar with labelled ends and ticks, where a small marker shows the hovered value;
// per-cell tooltips with the same detail on keyboard focus (arrow keys move between cells).

import * as V from "../vellum-web.js";

const NAME = "disasters_heat";
const SOURCE = "EM-DAT, CRED / UCLouvain; processed by Our World in Data; via vega-datasets 2.8.0";
const DECADES = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010];
const LOG = [0, 7];                         // colour domain: log10 of deaths, 1 to 10 million
const LTICKS = [0, 2, 4, 6, 7];             // the two ends and three round ticks between them
const GAP = 1.6;                            // the 1.2 pt surface gap between cells, in CSS pixels
const SUB = "Deaths per decade by type of disaster, colour on a log scale; the 2010s are 2010–2017. Point at or tab to " +
  "a cell to read it, and sort the rows by total or by name.";

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

const HEAT_CSS = `
.dh-cell { cursor: default; outline: none; }
.dh-sortlabel { color: var(--v-muted); font-size: 0.9rem; }`;

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

export async function mount(node) {
  injectStyle("vi-heat-style", HEAT_CSS);
  node.classList.add("vi");
  const text = await (await fetch(new URL("../../../data/disasters.csv", import.meta.url))).text();
  const cells = new Map();                  // "type|decade" -> deaths; a missing key means no record that decade
  const yearly = new Map();                 // type -> deaths by year, for the claim
  for (const line of text.trim().split(/\r?\n/).slice(1)) {
    const [type, yr, d] = line.split(",");
    if (type === "All natural disasters") continue;
    const dec = Math.floor(+yr / 10) * 10, key = `${type}|${dec}`;
    cells.set(key, (cells.get(key) || 0) + +d);
    if (!yearly.has(type)) yearly.set(type, new Map());
    yearly.get(type).set(+yr, +d);
  }
  const types = [...yearly.keys()];
  const value = (t, d) => cells.get(`${t}|${d}`);
  const total = (t) => DECADES.reduce((s, d) => s + (value(t, d) || 0), 0);
  const decadeTotal = (d) => types.reduce((s, t) => s + (value(t, d) || 0), 0);
  const label = (d) => `${d}s`;
  const share = (f) => { const p = 100 * f; return p < 0.01 ? "< 0.01 %" : `${V.fmt(p, p >= 10 ? 0 : p >= 1 ? 1 : p >= 0.1 ? 2 : 3)} %`; };

  // the claim: the two deadliest types of 1900–1929, deaths per year then and in 2010–2017
  const span = (t, a, b) => { let s = 0; for (let y = a; y <= b; y++) s += yearly.get(t).get(y) || 0; return s; };
  const lastYear = Math.max(...[...yearly.values()].flatMap((m) => [...m.keys()]));
  const top = types.slice().sort((a, b) => span(b, 1900, 1929) - span(a, 1900, 1929)).slice(0, 2);
  const early = (span(top[0], 1900, 1929) + span(top[1], 1900, 1929)) / 30;
  const late = (span(top[0], 2010, lastYear) + span(top[1], 2010, lastYear)) / (lastYear - 2009);
  const round = (v) => { const p = 10 ** Math.max(0, Math.floor(Math.log10(v)) - 1); return Math.round(v / p) * p; };   // two significant digits
  const plural = (t) => (/^(Drought|Earthquake|Epidemic|Flood|Landslide|Wildfire)$/.test(t) ? t + "s" : t);
  const titleText = `${plural(top[0])} and ${plural(top[1]).toLowerCase()} killed ${V.fmt(round(early))} a year in 1900–1929 and ` +
    `${V.fmt(round(late))} in 2010–${lastYear}`;

  let sort = "total", P = null, width = 0, focus = { r: 0, c: 0 };
  const rows = () => types.slice().sort(sort === "total" ? (a, b) => total(b) - total(a) : (a, b) => a.localeCompare(b));

  // ---- skeleton
  const plot = V.frame(node, { title: titleText, subtitle: SUB, footer: `${SOURCE} · assets/js/interactive/${NAME}.js` });
  const controls = V.el("div", { class: "vfig-controls" });
  plot.before(controls);
  V.el("span", { class: "dh-sortlabel", id: `${NAME}-sort` }, controls, "Sort rows");
  const seg = V.el("div", { class: "seg", role: "group", "aria-labelledby": `${NAME}-sort` }, controls);
  const sortBtns = [["total", "by total"], ["name", "by name"]].map(([k, txt]) => {
    const b = V.el("button", { type: "button" }, seg, txt);
    b.addEventListener("click", () => { sort = k; draw(); });
    return [k, b];
  });
  table(node, "Deaths per decade by type of natural disaster (– : no record that decade; the 2010s are 2010–2017)",
    ["type", ...DECADES.map(label), "total"],
    types.slice().sort((a, b) => total(b) - total(a)).map((t) => [t, ...DECADES.map((d) => (value(t, d) === undefined ? "–" : V.fmt(value(t, d)))), V.fmt(total(t))]));

  const measure = (() => { const c = document.createElement("canvas").getContext("2d"); return (s, size = 12) => { c.font = `${size}px ${P.fontBody}`; return c.measureText(s).width; }; })();

  function draw() {
    if (!P) return;
    sortBtns.forEach(([k, b]) => b.setAttribute("aria-pressed", k === sort));
    V.clear(plot);
    const order = rows(), narrow = width < 640;
    const lut = (t) => V.ramp(P.gradients.lagoon, (t - LOG[0]) / (LOG[1] - LOG[0]));
    const labW = Math.max(...types.map((t) => measure(t))) + 12;
    const legendW = narrow ? 0 : 96, legendH = narrow ? 100 : 0;
    const m = { l: labW, t: 26, r: 8 + legendW, b: 40 + legendH };
    const cw = Math.max(14, (width - m.l - m.r) / DECADES.length), ch = narrow ? 24 : 28;
    const gw = cw * DECADES.length, gh = ch * order.length, H = m.t + gh + m.b;
    const svg = V.svg(plot, width, H, { title: titleText, desc: `Heat map of deaths per decade for ${types.length} types of natural disaster, 1900s to 2010s.` });
    svg.setAttribute("role", "group");
    svg.setAttribute("aria-label", `${titleText}. Heat map: use the arrow keys to move between cells.`);
    const defs = V.el("defs", {}, svg), hatchId = `${NAME}-hatch`;
    // a missing cell: the card colour with a hatch in the terracotta tone, never a stop of the gradient
    const pat = V.el("pattern", { id: hatchId, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    V.el("rect", { width: 6, height: 6, fill: P.card }, pat);
    V.el("line", { x1: 0, y1: 0, x2: 0, y2: 6, stroke: P.tone[1], "stroke-width": 1.4 }, pat);
    const g = V.el("g", { transform: `translate(${m.l},${m.t})` }, svg);

    V.text(g, -labW, -14, "type of disaster", P, { size: 12.5, color: P.muted, baseline: "auto" });
    order.forEach((t, r) => V.text(g, -8, r * ch + ch / 2, t, P, { size: 12, color: P.muted, anchor: "end" }));
    const every = Math.ceil((measure("1900s") + 8) / cw);   // as many decade labels as fit side by side
    DECADES.forEach((d, c) => {
      if (c % every) return;
      V.text(g, c * cw + cw / 2, gh + 14, label(d), P, { size: 12, color: P.muted, anchor: "middle" });
    });
    V.text(g, gw / 2, gh + 34, "decade (the 2010s are 2010–2017)", P, { size: 12.5, color: P.muted, anchor: "middle" });

    // the cells, inset by half the gap on each side so that neighbours are separated by a surface-coloured gap
    const tip = V.tooltip(plot), cellEls = [];
    const ring = V.el("rect", { fill: "none", stroke: P.ink, "stroke-width": 1.5, rx: 1, "pointer-events": "none", visibility: "hidden" });
    order.forEach((t, r) => {
      cellEls.push(DECADES.map((d, c) => {
        const v = value(t, d), lv = v > 0 ? Math.log10(v) : null;
        const rect = V.el("rect", {
          x: c * cw + GAP / 2, y: r * ch + GAP / 2, width: cw - GAP, height: ch - GAP, class: "dh-cell",
          fill: v === undefined ? `url(#${hatchId})` : lut(lv ?? 0), tabindex: r === focus.r && c === focus.c ? 0 : -1,
          "aria-label": `${t}, ${label(d)}: ${v === undefined ? "no record" : `${V.fmt(v)} deaths`}`,
        }, g);
        const show = () => {
          focus = { r, c };
          ring.setAttribute("x", c * cw + GAP / 2); ring.setAttribute("y", r * ch + GAP / 2);
          ring.setAttribute("width", cw - GAP); ring.setAttribute("height", ch - GAP); ring.setAttribute("visibility", "visible");
          const head = `${t}, ${label(d)}${d === 2010 ? ` (2010–${lastYear})` : ""}`;
          tip.show(m.l + c * cw + cw / 2, m.t + r * ch, head, v === undefined ? [{ value: "no record", label: "that decade" }] : [
            { value: V.fmt(v), label: "deaths", color: lut(lv ?? 0), kind: "rect" },
            { value: share(v / decadeTotal(d)), label: "of that decade's deaths" }]);
          marker(v === undefined ? null : lv ?? 0);
        };
        const hide = () => { ring.setAttribute("visibility", "hidden"); tip.hide(); marker(null); };
        rect.addEventListener("pointerenter", show);
        rect.addEventListener("pointerdown", show);
        rect.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && document.activeElement !== rect) hide(); });
        rect.addEventListener("focus", show);
        rect.addEventListener("blur", hide);
        rect.addEventListener("keydown", (e) => {
          const mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key];
          const to = mv ? [r + mv[0], c + mv[1]] : e.key === "Home" ? [r, 0] : e.key === "End" ? [r, DECADES.length - 1] : null;
          if (!to) return;
          e.preventDefault();
          const nr = Math.max(0, Math.min(order.length - 1, to[0])), nc = Math.max(0, Math.min(DECADES.length - 1, to[1]));
          rect.tabIndex = -1; cellEls[nr][nc].tabIndex = 0; cellEls[nr][nc].focus();
        });
        return rect;
      }));
    });
    g.appendChild(ring);

    // the legend bar: lagoon, labelled ends and round ticks as numbers of deaths, a hatched key for "no record"
    const grad = V.el("linearGradient", { id: `${NAME}-grad`, x1: 0, y1: narrow ? 0 : 1, x2: narrow ? 1 : 0, y2: 0 }, defs);
    P.gradients.lagoon.forEach((c, k, a) => V.el("stop", { offset: k / (a.length - 1), "stop-color": c }, grad));
    const lg = V.el("g", {}, svg), tickText = (v) => (v === 7 ? "10 million" : V.fmt(10 ** v));
    let pos;
    if (narrow) {
      const bx = m.l, by = m.t + gh + 78, bw = Math.min(gw, 300);
      pos = (v) => [bx + ((v - LOG[0]) / (LOG[1] - LOG[0])) * bw, by];
      V.text(lg, bx, by - 10, "deaths per decade, log scale", P, { size: 12, color: P.muted, baseline: "auto" });
      V.el("rect", { x: bx, y: by, width: bw, height: 8, fill: `url(#${NAME}-grad)` }, lg);
      for (const t of LTICKS) if (t !== 6 || bw > 320) V.text(lg, pos(t)[0], by + 20, tickText(t), P, { size: 12, color: P.muted, anchor: t === 0 ? "start" : t === 7 ? "end" : "middle" });
      V.el("rect", { x: bx, y: by + 34, width: 10, height: 10, fill: `url(#${hatchId})` }, lg);
      V.text(lg, bx + 16, by + 39, "no record", P, { size: 12, color: P.muted });
    } else {
      const bx = m.l + gw + 18, by = m.t, bh = gh;
      pos = (v) => [bx, by + bh - ((v - LOG[0]) / (LOG[1] - LOG[0])) * bh];
      V.text(lg, bx, by - 14, "deaths per decade", P, { size: 12, color: P.muted, baseline: "auto" });
      V.el("rect", { x: bx, y: by, width: 8, height: bh, fill: `url(#${NAME}-grad)` }, lg);
      for (const t of LTICKS) V.text(lg, bx + 14, Math.max(by + 6, Math.min(by + bh - 6, pos(t)[1])), tickText(t), P, { size: 12, color: P.muted });
      V.el("rect", { x: bx, y: by + bh + 10, width: 10, height: 10, fill: `url(#${hatchId})` }, lg);
      V.text(lg, bx + 16, by + bh + 15, "no record", P, { size: 12, color: P.muted });
      V.text(lg, bx, by + bh + 34, "log scale", P, { size: 12, color: P.muted });
    }
    const mk = V.el("path", { fill: P.ink, visibility: "hidden" }, lg);
    function marker(v) {
      if (v === null) { mk.setAttribute("visibility", "hidden"); return; }
      const [x, y] = pos(v);
      mk.setAttribute("d", narrow ? `M${x},${y - 1} l-4.5,-6 h9 z` : `M${x - 1},${y} l-6,-4.5 v9 z`);
      mk.setAttribute("visibility", "visible");
    }
  }

  await document.fonts?.ready;
  V.responsive(node, (w, palette) => { width = w; P = palette; draw(); });
}
