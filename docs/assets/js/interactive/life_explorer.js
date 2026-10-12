// life_explorer.js: period life expectancy at birth, 1950–2023, for up to four countries the reader chooses, with the
// world as context. Data: docs/data/owid-life-expectancy.csv (Our World in Data); countries are the rows with a
// three-letter code.
//
// Vellum rules on show: a line chart with direct end labels and ringed end dots (no legend for four series), the world
// in rule grey as the context the claim is measured against, colour by entity (a country takes the first free slot of
// the slot order and keeps it while it stays chosen, so removing one never repaints another), a crosshair that snaps
// to the nearest year with a tooltip listing every line, and a claim title recomputed from the chosen countries.

import * as V from "../vellum-web.js";

const NAME = "life_explorer";
const SOURCE = "UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), " +
  "Riley (2005); processed by Our World in Data";
const Y0 = 1950, Y1 = 2023, MAX = 4;
const DEFAULTS = ["South Korea", "China", "Russia", "Nigeria"];   // a catch-up, a famine and a rise, a stall, a slow climb
const TABLE_YEARS = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2019, 2020, 2021, 2022, 2023];
const SUB = "Period life expectancy at birth, 1950–2023, for up to four countries against the world. Type a name to add " +
  "a country, press its chip to remove it, point at the chart to read a year.";

// RFC 4180 lines: fields may be quoted and contain commas
function parseCSV(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line) continue;
    const out = []; let cur = "", q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (q) { if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
      else if (c === '"') q = true;
      else if (c === ",") { out.push(cur); cur = ""; }
      else cur += c;
    }
    out.push(cur); rows.push(out);
  }
  return rows;
}

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

const LIFE_CSS = `
.le-add { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.le-add label { color: var(--v-muted); font-size: 0.9rem; }
.le-add input { width: 15rem; max-width: 100%; cursor: text; border-radius: 8px; }
.le-add input:disabled { cursor: not-allowed; color: var(--v-muted); }
.le-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; list-style: none; }
.le-chips li { margin: 0; }
.le-chip { display: inline-flex; align-items: center; gap: 8px; }
.le-chip .le-key { width: 16px; height: 3px; border-radius: 2px; flex: none; }
.le-chip .x { color: var(--v-muted); font-size: 1.05em; line-height: 1; }
.le-hit { cursor: crosshair; touch-action: pan-y; }`;

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
  injectStyle("vi-life-style", LIFE_CSS);
  node.classList.add("vi");
  const text = await (await fetch(new URL("../../../data/owid-life-expectancy.csv", import.meta.url))).text();
  const data = new Map();            // name -> 74 values, 1950..2023
  for (const [entity, code, yr, v] of parseCSV(text).slice(1)) {
    const year = +yr;
    if (year < Y0 || year > Y1 || !(code.length === 3 || entity === "World")) continue;
    if (!data.has(entity)) data.set(entity, new Array(Y1 - Y0 + 1).fill(NaN));
    data.get(entity)[year - Y0] = +v;
  }
  const names = [...data.keys()].filter((n) => n !== "World").sort((a, b) => a.localeCompare(b));
  const world = data.get("World"), at = (s, y) => s[y - Y0];
  const dipYear = at(world, 2021) < at(world, 2020) ? 2021 : 2020, dip = at(world, 2019) - at(world, dipYear);

  const slots = new Array(MAX).fill(null);   // a country keeps its slot, and so its colour, while it stays chosen
  DEFAULTS.forEach((n, k) => { if (data.has(n)) slots[k] = n; });
  let P = null, width = 0, hoverYear = null;

  // ---- skeleton: title, subtitle, the controls row, the plot, the footer, the table
  const plot = V.frame(node, { title: " ", subtitle: SUB, footer: `${SOURCE} · assets/js/interactive/${NAME}.js` });
  const titleEl = node.querySelector(".vfig-title");
  const controls = V.el("div", { class: "vfig-controls" });
  plot.before(controls);
  const add = V.el("div", { class: "le-add" }, controls);
  const listId = `${NAME}-countries`;
  V.el("label", { for: `${NAME}-search` }, add, "Add a country");
  const input = V.el("input", { type: "search", id: `${NAME}-search`, list: listId, autocomplete: "off", spellcheck: "false" }, add);
  const dl = V.el("datalist", { id: listId }, add);
  for (const n of names) V.el("option", { value: n }, dl);
  const chips = V.el("ul", { class: "le-chips", "aria-label": "Chosen countries" }, controls);
  let tableNode = null;

  // the claim: the largest and the smallest change since 1950 among the chosen countries, or against the world
  const gain = (n) => at(data.get(n), Y1) - at(data.get(n), Y0);
  const by = (g) => `${g >= 0 ? "rose" : "fell"} ${V.fmt(Math.abs(g))} years`;
  function claim(chosen) {
    const w = gain("World");
    if (!chosen.length) return `Since 1950, life expectancy worldwide ${by(w)}`;
    if (chosen.length === 1) return `Since 1950, life expectancy in ${chosen[0]} ${by(gain(chosen[0]))}, against ${V.fmt(w)} worldwide`;
    const s = chosen.slice().sort((a, b) => gain(b) - gain(a)), a = s[0], b = s[s.length - 1];
    return `Since 1950, life expectancy ${by(gain(a))} in ${a} and ${V.fmt(gain(b))} in ${b}`;
  }

  function choose(n) {
    if (!data.has(n) || n === "World" || slots.includes(n)) return;
    const k = slots.indexOf(null);
    if (k < 0) return;
    slots[k] = n; input.value = ""; render();
  }
  function drop(k) { slots[k] = null; render(); input.focus(); }

  // best match for typed text: exact, then a name that starts with it, then one that contains it
  function match(s) {
    const q = s.trim().toLowerCase();
    if (!q) return null;
    return names.find((n) => n.toLowerCase() === q) || names.find((n) => n.toLowerCase().startsWith(q)) ||
      names.find((n) => n.toLowerCase().includes(q)) || null;
  }
  input.addEventListener("input", () => { if (names.includes(input.value)) choose(input.value); });
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); const m = match(input.value); if (m) choose(m); } });

  function renderControls() {
    V.clear(chips);
    slots.forEach((n, k) => {
      if (!n) return;
      const b = V.el("button", { type: "button", class: "chip le-chip", "aria-label": `Remove ${n}` }, V.el("li", {}, chips));
      V.el("span", { class: "le-key", style: { background: P.tone[k] } }, b);
      V.el("span", {}, b, n);
      V.el("span", { class: "x", "aria-hidden": "true" }, b, "×");
      b.addEventListener("click", () => drop(k));
    });
    const full = !slots.includes(null);
    input.disabled = full;
    input.placeholder = full ? "remove one to add another" : "type a country";
  }

  function render() {
    if (!P) return;
    const chosen = slots.filter(Boolean);
    titleEl.textContent = claim(chosen);
    renderControls();
    draw();
    const open = tableNode?.open;
    tableNode?.remove();
    tableNode = table(node, `Life expectancy at birth in years, every ten years and each year from 2019`, ["year", ...chosen, "World"],
      TABLE_YEARS.map((y) => [V.year(y), ...chosen.map((n) => V.fmt(at(data.get(n), y), 1)), V.fmt(at(world, y), 1)]));
    tableNode.open = !!open;
  }

  // text width in the body face, for the right margin that holds the end labels
  const measure = (() => { const c = document.createElement("canvas").getContext("2d"); return (s, size = 13) => { c.font = `${size}px ${P.fontBody}`; return c.measureText(s).width; }; })();

  function draw() {
    V.clear(plot);
    const series = [{ name: "World", color: P.rule, values: world },
      ...slots.map((n, k) => n && { name: n, color: P.tone[k], values: data.get(n) }).filter(Boolean)];
    let lo = Infinity;
    for (const s of series) for (const v of s.values) lo = Math.min(lo, v);
    lo = Math.min(30, Math.floor(lo / 10) * 10);
    const narrow = width < 560;
    const m = { l: 34, t: 30, b: 34, r: Math.min(Math.max(...series.map((s) => measure(s.name))) + 22, width * 0.42) };
    const H = narrow ? 320 : 420, iw = width - m.l - m.r, ih = H - m.t - m.b;
    const x = V.linear([Y0, Y1], [0, iw]), y = V.linear([lo, 90], [ih, 0]);
    const svg = V.svg(plot, width, H, { title: titleEl.textContent,
      desc: series.map((s) => `${s.name}: ${V.fmt(at(s.values, Y0), 1)} years in 1950, ${V.fmt(at(s.values, Y1), 1)} in 2023`).join("; ") + "." });
    svg.setAttribute("tabindex", 0);
    svg.setAttribute("aria-label", `${titleEl.textContent}. Use the arrow keys to read a year.`);
    const g = V.el("g", { transform: `translate(${m.l},${m.t})` }, svg);
    V.axes(g, P, { x, y, xticks: narrow ? [1960, 1990, 2020] : [1950, 1970, 1990, 2010], yticks: V.ticks(lo, 90, narrow ? 4 : 5),
      xfmt: V.year, unit: `years of life expected at birth · the axis starts at ${lo}`, width: iw, height: ih });
    const pts = (s) => s.values.map((v, i) => [x(Y0 + i), y(v)]);
    for (const s of series) V.line(g, pts(s), s.color);   // the world first, behind the countries

    // the quiet note at the world's dip of 2020–2021: the nearest place below (then above) the dip where no line
    // crosses the text, joined to the dip by a thin muted leader
    const note = `world, 2019–${dipYear}: −${V.fmt(dip, 1)} years`, nw = measure(note, 12) + 6;
    const px = x(dipYear), py = y(at(world, dipYear)), right = px - 18, left = right - nw;
    const clear = (ty) => ty > 8 && ty < ih - 8 && series.every((s) => s.values.every((v, i) => {
      const vx = x(Y0 + i);
      return vx < left - 4 || vx > right + 4 || Math.abs(y(v) - ty) > 11;
    }));
    const offsets = []; for (let d = 30; d < ih; d += 6) offsets.push(d, -d);
    const ty = py + (offsets.find((d) => clear(py + d)) ?? 30);
    V.el("polyline", { points: `${px},${py + (ty > py ? 5 : -5)} ${right + 2},${ty}`, fill: "none", stroke: P.muted, "stroke-width": 0.75 }, g);
    V.note(g, right - 2, ty, note, P, { anchor: "end" });

    for (const s of series) V.dot(g, x(Y1), y(at(s.values, Y1)), s.color, P);
    V.endLabels(g, series.map((s) => ({ x: x(Y1), y: y(at(s.values, Y1)), text: s.name })), P);

    // hover: a crosshair that snaps to the nearest year, ringed dots on every line, one tooltip listing them all
    const hover = V.el("g", { "pointer-events": "none" }, g);
    const tip = V.tooltip(plot);
    const show = (year, py0) => {
      hoverYear = year; V.clear(hover);
      if (year === null) { tip.hide(); return; }
      const hx = x(year);
      V.el("line", { x1: hx, x2: hx, y1: 0, y2: ih, stroke: P.secondary, "stroke-width": 1, opacity: 0.6 }, hover);
      const rows = series.map((s) => ({ v: at(s.values, year), s })).sort((a, b) => b.v - a.v);
      for (const { v, s } of rows) V.dot(hover, hx, y(v), s.color, P);
      tip.show(m.l + hx, py0 ?? m.t + y(rows[0].v), V.year(year),
        rows.map(({ v, s }) => ({ value: V.fmt(v, 1), label: s.name, color: s.color })));
    };
    const hit = V.el("rect", { x: 0, y: 0, width: iw, height: ih, fill: "transparent", class: "le-hit" }, g);
    const yearAt = (e) => { const r = svg.getBoundingClientRect(); return Math.max(Y0, Math.min(Y1, Math.round(x.invert(e.clientX - r.left - m.l)))); };
    hit.addEventListener("pointermove", (e) => show(yearAt(e), e.clientY - svg.getBoundingClientRect().top));
    hit.addEventListener("pointerdown", (e) => show(yearAt(e), e.clientY - svg.getBoundingClientRect().top));
    hit.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") show(null); });
    svg.addEventListener("focus", () => show(hoverYear ?? Y1));
    svg.addEventListener("blur", () => show(null));
    svg.addEventListener("keydown", (e) => {
      const step = { ArrowLeft: -1, ArrowRight: 1, PageDown: -10, PageUp: 10 }[e.key];
      const yr = e.key === "Home" ? Y0 : e.key === "End" ? Y1 : step ? Math.max(Y0, Math.min(Y1, (hoverYear ?? Y1) + step)) : null;
      if (yr === null) { if (e.key === "Escape") show(null); return; }
      e.preventDefault(); show(yr);
    });
  }

  await document.fonts?.ready;
  V.responsive(node, (w, palette) => { width = w; P = palette; render(); });
}
