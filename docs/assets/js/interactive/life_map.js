// life_map.js: a world choropleth of life expectancy at birth, 1950 to 2023, in the Equal Earth projection.
//
// Outlines from Natural Earth at 1:110 million (docs/data/world-110m.json, made by tools/make_world.py), values from
// Our World in Data. Five classes of the teal ramp at the quintiles of the 2023 values, held fixed when the reader
// moves the year so that a colour means the same in 1950 as in 2023. Land without a value is the card colour with a
// terracotta hatch. Small countries vanish on a world map, so a strip of ringed dots per continent sits under it; a
// hover on either finds the country in both. Keyboard: tab to the map, then the arrow keys step through the countries
// in rank order.
import * as V from "../vellum-web.js";

const WORLD = new URL("../../../data/world-110m.json", import.meta.url);
const DATA = new URL("../../../data/owid-life-expectancy.csv", import.meta.url);
const Y0 = 1950, Y1 = 2023, BASE = 2023, DOMAIN = [10, 90];
const SOURCE = "UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), " +
  "Riley (2005); processed by Our World in Data. Outlines: Natural Earth v5.1.2";

const CSS = `
.vmap .vfig-controls { gap: 8px 14px; }
.vmap .yr { display: flex; align-items: center; gap: 12px; width: 100%; max-width: 560px; }
.vmap .yr label { color: var(--v-muted); font-size: 0.92rem; }
.vmap .yr input[type=range] { flex: 1 1 120px; min-width: 0; -webkit-appearance: none; appearance: none; height: 28px; background: transparent; cursor: pointer; }
.vmap .yr input[type=range]::-webkit-slider-runnable-track { height: 4px; background: var(--v-grid); border-radius: 2px; }
.vmap .yr input[type=range]::-moz-range-track { height: 4px; background: var(--v-grid); border-radius: 2px; }
.vmap .yr input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; margin-top: -8px; border-radius: 50%; background: var(--v-teal); border: 2px solid var(--v-surface); }
.vmap .yr input[type=range]::-moz-range-thumb { width: 16px; height: 16px; border-radius: 50%; background: var(--v-teal); border: 2px solid var(--v-surface); }
.vmap .yr output { font-family: var(--v-font-title); font-size: 1.6rem; color: var(--v-ink); font-variant-numeric: lining-nums; min-width: 3ch; }
.vmap .readout { color: var(--v-secondary); font-size: 0.95rem; margin: 0 0 10px; max-width: 80ch; }
.vmap .ptitle { font-weight: 700; color: var(--v-ink); font-size: 0.95rem; margin: 22px 0 2px; }
.vmap .ptitle b { margin-right: 8px; }
.vmap .psub { color: var(--v-muted); font-size: 0.85rem; margin: 0 0 6px; max-width: 80ch; }
.vmap .mapbox, .vmap .stripbox { position: relative; touch-action: manipulation; }
.vmap .mapg:focus { outline: none; }
.vmap .mapg:focus-visible .focusring { stroke: var(--v-teal); stroke-width: 2; }
.vmap .tables { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.vmap .tables.narrow { grid-template-columns: minmax(0, 1fr); }
.vmap details.data-table { margin-top: 18px; }
.vmap details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; }
.vmap details.data-table .table-wrap { margin: 12px 0 0; }
.vmap .vnote { color: var(--v-muted); font-size: 0.85rem; margin: 6px 0 0; max-width: 80ch; }
`;

// ---------------------------------------------------------------- Equal Earth (Šavrič, Patterson and Jenny 2018)
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2;
function equalEarth(lon, lat) {
  const l = (lon * Math.PI) / 180, t = Math.asin(M * Math.sin((lat * Math.PI) / 180));
  const t2 = t * t, t6 = t2 * t2 * t2;
  return [
    (2 * Math.sqrt(3) * l * Math.cos(t)) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1)),
    t * (A4 * t6 * t2 + A3 * t6 + A2 * t2 + A1),
  ];
}

// ---------------------------------------------------------------- data
let loaded = null;
function parseCsv(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line) continue;
    const out = []; let cur = "", q = false;
    for (const ch of line) {
      if (ch === '"') q = !q; else if (ch === "," && !q) { out.push(cur); cur = ""; } else cur += ch;
    }
    out.push(cur); rows.push(out);
  }
  return rows;
}

function load() {
  if (loaded) return loaded;
  loaded = Promise.all([fetch(WORLD).then((r) => r.json()), fetch(DATA).then((r) => r.text())]).then(([world, csv]) => {
    const byCode = new Map();
    for (const [, code, yr, v] of parseCsv(csv).slice(1)) {
      const y = +yr;
      if (!code || y < Y0 || y > Y1) continue;
      if (!byCode.has(code)) byCode.set(code, new Map());
      byCode.get(code).set(y, +v);
    }
    const countries = world.features.map((f, i) => {
      const code = f.iso !== "-99" ? f.iso : f.a3;
      const values = byCode.get(code) || byCode.get("OWID_" + f.a3) || new Map();   // OWID codes Kosovo OWID_KOS
      const rings = f.rings.map((r) => r.map(([lon, lat]) => equalEarth(lon, lat)));
      return { i, name: f.name, continent: f.continent, values, rings };
    });
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const c of countries) for (const r of c.rings) for (const [x, y] of r) {
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    // classes: quintiles of the 2023 values (linear interpolation between order statistics), rounded to 0.1 year
    const base = countries.map((c) => c.values.get(BASE)).filter(Number.isFinite).sort((a, b) => a - b);
    const q = (p) => { const h = (base.length - 1) * p, lo = Math.floor(h); return base[lo] + (base[Math.min(lo + 1, base.length - 1)] - base[lo]) * (h - lo); };
    const breaks = [0.2, 0.4, 0.6, 0.8].map((p) => Math.round(q(p) * 10) / 10);
    return { countries, bounds: [x0, x1, y0, y1], breaks };
  });
  return loaded;
}

const classOf = (v, breaks) => breaks.filter((b) => v >= b).length;

// The countries with a value in year y, ranked from the highest.
function ranked(D, y) {
  return D.countries.filter((c) => Number.isFinite(c.values.get(y))).sort((a, b) => b.values.get(y) - a.values.get(y));
}

// Ringed dots in one row, each pushed up or down from the centre line until it overlaps no dot already placed.
function swarm(items, r) {
  const placed = [], d = 2 * r + 1;
  for (const it of items.slice().sort((a, b) => a.x - b.x)) {
    let off = 0;
    for (let k = 0; k < 60; k++) {
      off = k === 0 ? 0 : (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (d * 0.55);
      if (placed.every((p) => Math.hypot(p.x - it.x, p.y - off) >= d)) break;
    }
    placed.push({ ...it, y: off });
  }
  return placed;
}

function hatch(defs, id, P) {
  const pat = V.el("pattern", { id, width: 5, height: 5, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
  V.el("rect", { width: 5, height: 5, fill: P.card }, pat);
  V.el("line", { x1: 0, y1: 0, x2: 0, y2: 5, stroke: P.tone[1], "stroke-width": 1.1 }, pat);
}

let uid = 0;

function draw(node, width, P, D, state) {
  const id = `vmap-hatch-${++uid}`, narrow = width < 620;
  const ramp = P.sequential.teal.slice(1, 6);   // five steps of the teal ramp; dark twin: dark (less) to bright (more)
  const fill = (c, y) => { const v = c.values.get(y); return Number.isFinite(v) ? ramp[classOf(v, D.breaks)] : `url(#${id})`; };
  const r23 = ranked(D, BASE), hi = r23[0], lo = r23[r23.length - 1];
  const claim = `In ${BASE} life expectancy at birth ran from ${V.fmt(lo.values.get(BASE), 1)} years in ${lo.name} to ${V.fmt(hi.values.get(BASE), 1)} in ${hi.name}`;
  const noData = D.countries.filter((c) => !Number.isFinite(c.values.get(BASE)));
  const plot = V.frame(node, {
    title: claim,
    subtitle: `Period life expectancy at birth in the ${r23.length} countries on the map with a value, in five classes. Move the year from ${Y0} to ${Y1}; ` +
      `hover or tap a country or a dot, or tab to the map and use the arrow keys.`,
    footer: `${SOURCE} · assets/js/interactive/life_map.js`,
  });
  const tip = V.tooltip(plot);

  // ---- controls
  const ctl = V.el("div", { class: "vfig-controls" }, plot);
  const yr = V.el("div", { class: "yr" }, ctl);
  const sid = `vmap-year-${uid}`;
  V.el("label", { for: sid }, yr, "Year");
  const range = V.el("input", { id: sid, type: "range", min: Y0, max: Y1, step: 1, value: state.year }, yr);
  const out = V.el("output", { for: sid }, yr, V.year(state.year));
  const readout = V.el("p", { class: "readout" }, plot);

  // ---- a: the map
  const [x0, x1, y0, y1] = D.bounds, k = width / (x1 - x0), mh = Math.round((y1 - y0) * k);
  const px = ([x, y]) => [(x - x0) * k, (y1 - y) * k];
  const mapbox = V.el("div", { class: "mapbox" }, plot);
  const ms = V.svg(mapbox, width, mh + 8, { title: claim, desc: `World map of life expectancy at birth in five classes; the ${r23.length} countries with a value and ${noData.length} without.` });
  hatch(V.el("defs", {}, ms), id, P);
  const mapg = V.el("g", { class: "mapg", tabindex: 0, role: "group", "aria-label": "Map: use the arrow keys to step through the countries from the highest life expectancy to the lowest" }, ms);
  V.el("rect", { class: "focusring", x: 1, y: 1, width: width - 2, height: mh + 6, rx: 6, fill: "none", stroke: "none" }, mapg);
  const paths = D.countries.map((c) => {
    const d = c.rings.map((r) => "M" + r.map((p) => px(p).map((v) => v.toFixed(1)).join(",")).join("L") + "Z").join("");
    return V.el("path", { d, "data-i": c.i, "fill-rule": "evenodd", stroke: P.grid, "stroke-width": 0.4, "stroke-linejoin": "round" }, mapg);
  });
  const ring = V.el("path", { fill: "none", stroke: P.ink, "stroke-width": 1.4, "stroke-linejoin": "round", "pointer-events": "none", visibility: "hidden" }, ms);

  // ---- legend: five classes with their break values, and the hatch
  const lg = V.svg(plot, width, 74, { title: "Legend", desc: `Five classes with breaks at ${D.breaks.map((b) => V.fmt(b, 1)).join(", ")} years; hatched land has no value.` });
  const sw = Math.min(64, Math.floor((width - 120) / 5)), lgy = 22;
  V.text(lg, 0, 12, "life expectancy at birth, years", P, { size: 12.5, color: P.muted });
  const marks = ramp.map((c, j) => {
    V.el("rect", { x: j * sw, y: lgy, width: sw - 2, height: 10, fill: c }, lg);
    return V.el("rect", { x: j * sw, y: lgy + 13, width: sw - 2, height: 2.5, fill: P.ink, visibility: "hidden" }, lg);
  });
  D.breaks.forEach((b, j) => V.text(lg, (j + 1) * sw - 1, lgy + 26, V.fmt(b, 1), P, { size: 12, color: P.muted, anchor: "middle" }));
  const nx = 5 * sw + 18;
  V.el("rect", { x: nx, y: lgy, width: 28, height: 10, fill: `url(#${id})` }, lg);
  V.text(lg, nx + 34, lgy + 5, "no value", P, { size: 12, color: P.muted });
  V.text(lg, 0, lgy + 46, `Classes: quintiles of the ${BASE} values, held fixed for every year, so a colour means the same in ${Y0} and ${Y1}`, P, { size: 12, color: P.muted, cls: "lgnote" });
  if (narrow) lg.querySelector(".lgnote").remove();
  const legendNote = narrow ? V.el("p", { class: "vnote" }, plot, `Classes: quintiles of the ${BASE} values, held fixed for every year, so a colour means the same in ${Y0} and ${Y1}.`) : null;
  if (legendNote) { lg.setAttribute("height", 54); lg.setAttribute("viewBox", `0 0 ${width} 54`); }
  V.el("p", { class: "vnote" }, plot, `No value: ${noData.map((c) => c.name).join(", ")} (hatched).`);

  // ---- b: every country as a dot, by continent
  const cont = [...new Set(D.countries.filter((c) => c.values.size).map((c) => c.continent))];
  const med = (arr) => { const s = arr.slice().sort((a, b) => a - b); return s[Math.floor((s.length - 1) / 2)]; };
  cont.sort((a, b) => med(r23.filter((c) => c.continent === b).map((c) => c.values.get(BASE))) - med(r23.filter((c) => c.continent === a).map((c) => c.values.get(BASE))));
  const pt = V.el("p", { class: "ptitle" }, plot);
  V.el("b", {}, pt, "b");
  pt.appendChild(document.createTextNode("Every country as one dot, by continent"));
  V.el("p", { class: "psub" }, plot, "Small countries vanish on a world map; here each is a ringed dot on the same scale of years. Hover a dot to find the country on the map.");
  const sm = { l: narrow ? 92 : 112, r: 14, t: 30 }, sw2 = width - sm.l - sm.r, dr = narrow ? 3.2 : 3.8, CAP = 64;
  const sx = V.linear(DOMAIN, [0, sw2]);
  // row heights fixed across all years (at most CAP), so the strip does not jump when the year moves; a year whose
  // swarm is taller than its row is squeezed to fit, and the rings keep overlapping dots apart
  const rowH = cont.map((ct) => {
    let ext = 0;
    for (let y = Y0; y <= Y1; y++) {
      const items = D.countries.filter((c) => c.continent === ct && Number.isFinite(c.values.get(y))).map((c) => ({ x: sx(c.values.get(y)) }));
      for (const p of swarm(items, dr)) ext = Math.max(ext, Math.abs(p.y));
    }
    return Math.min(CAP, Math.max(26, 2 * ext + 2 * dr + 8));
  });
  const rowY = rowH.reduce((acc, h, j) => (acc.push(j ? acc[j - 1] + rowH[j - 1] : 0), acc), []);
  const sh = rowY[rowY.length - 1] + rowH[rowH.length - 1];
  const stripbox = V.el("div", { class: "stripbox" }, plot);
  const ss = V.svg(stripbox, width, sm.t + sh + 30, { title: "Life expectancy by continent", desc: "One ringed dot per country, by continent, on a common axis from 10 to 90 years." });
  const sg = V.el("g", { transform: `translate(${sm.l},${sm.t})` }, ss);
  for (const t of [20, 40, 60, 80]) V.text(sg, sx(t), sh + 16, V.fmt(t), P, { size: 12, color: P.muted, anchor: "middle" });
  V.el("line", { x1: 0, x2: sw2, y1: sh, y2: sh, stroke: P.grid, "stroke-width": 1.3, "shape-rendering": "crispEdges" }, sg);
  const unit = V.text(sg, -sm.l, -14, "", P, { size: 12.5, color: P.muted, baseline: "auto" });
  cont.forEach((ct, j) => {
    V.el("line", { x1: 0, x2: sw2, y1: rowY[j] + rowH[j] / 2, y2: rowY[j] + rowH[j] / 2, stroke: P.grid, "stroke-width": 1, "shape-rendering": "crispEdges" }, sg);
    V.text(sg, -10, rowY[j] + rowH[j] / 2, ct, P, { size: 12.5, anchor: "end" });
  });
  const dotg = V.el("g", {}, sg);
  const halo = V.el("circle", { r: dr + 1.2, fill: P.tone[1], stroke: P.surface, "stroke-width": 1.8, "pointer-events": "none", visibility: "hidden" }, sg);   // the highlighted country, in terracotta
  let dots = [];   // [{c, x, y}] in strip coordinates, for the nearest-dot hover

  // ---- tables
  const det = V.el("details", { class: "data-table" }, plot);
  V.el("summary", {}, det, "Show the data as a table");
  const tables = V.el("div", { class: "tables" + (narrow ? " narrow" : "") }, det);

  // ---- highlight one country in the map, the strip and the legend
  let cur = null;
  const focusOn = (c, at) => {
    cur = c;
    ring.setAttribute("d", paths[c.i].getAttribute("d")); ring.setAttribute("visibility", "visible");
    const v = c.values.get(state.year), has = Number.isFinite(v), cls = has ? classOf(v, D.breaks) : -1;
    marks.forEach((m, j) => m.setAttribute("visibility", j === cls ? "visible" : "hidden"));
    const dd = dots.find((d) => d.c === c);
    if (dd) { halo.setAttribute("cx", dd.x); halo.setAttribute("cy", dd.y); halo.setAttribute("visibility", "visible"); }
    else halo.setAttribute("visibility", "hidden");
    const rk = ranked(D, state.year);
    let pos = at;
    if (!pos) { const b = paths[c.i].getBBox(); pos = [b.x + b.width / 2, b.y + b.height / 2 + ms.getBoundingClientRect().top - plot.getBoundingClientRect().top]; }
    tip.show(pos[0], pos[1], c.name, has ? [
      { value: `${V.fmt(v, 1)} years`, label: `life expectancy, ${state.year}`, color: ramp[cls], kind: "rect" },
      { value: `${rk.indexOf(c) + 1} of ${rk.length}`, label: "rank, highest first" },
      { value: cls === 0 ? `under ${V.fmt(D.breaks[0], 1)}` : cls === 4 ? `${V.fmt(D.breaks[3], 1)} and over` : `${V.fmt(D.breaks[cls - 1], 1)} to ${V.fmt(D.breaks[cls], 1)}`, label: `class ${cls + 1} of 5` },
    ] : [{ value: "no value", label: `${state.year}` }]);
  };
  const clearFocus = () => {
    cur = null; ring.setAttribute("visibility", "hidden"); halo.setAttribute("visibility", "hidden");
    marks.forEach((m) => m.setAttribute("visibility", "hidden")); tip.hide();
  };
  const rel = (e) => { const r = plot.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  const onMap = (e) => {
    const p = e.target.closest?.("path[data-i]");
    if (p) focusOn(D.countries[+p.dataset.i], rel(e)); else clearFocus();
  };
  mapg.addEventListener("pointermove", (e) => { if (e.pointerType === "mouse") onMap(e); });
  mapg.addEventListener("pointerdown", onMap);
  mapg.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") clearFocus(); });
  let kcur = -1;
  mapg.addEventListener("keydown", (e) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1, Home: -1e3, End: 1e3 }[e.key];
    if (step === undefined) { if (e.key === "Escape") clearFocus(); return; }
    e.preventDefault();
    const rk = ranked(D, state.year);
    kcur = Math.min(rk.length - 1, Math.max(0, kcur + step));
    focusOn(rk[kcur]);
  });
  mapg.addEventListener("blur", clearFocus);
  const onStrip = (e) => {
    const r = sg.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    let best = null, bd = 18;
    for (const d of dots) { const dist = Math.hypot(d.x - x, d.y - y); if (dist < bd) { bd = dist; best = d; } }
    if (best) focusOn(best.c, rel(e)); else clearFocus();
  };
  ss.addEventListener("pointermove", (e) => { if (e.pointerType === "mouse") onStrip(e); });
  ss.addEventListener("pointerdown", onStrip);
  ss.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") clearFocus(); });

  // ---- everything that depends on the year
  const paint = () => {
    const y = state.year, rk = ranked(D, y);
    out.textContent = V.year(y);
    D.countries.forEach((c) => paths[c.i].setAttribute("fill", fill(c, y)));
    const vals = rk.map((c) => c.values.get(y)), mid = vals.length % 2 ? vals[(vals.length - 1) / 2] : (vals[vals.length / 2 - 1] + vals[vals.length / 2]) / 2;
    readout.textContent = `${y}: from ${V.fmt(vals[vals.length - 1], 1)} years (${rk[rk.length - 1].name}) to ${V.fmt(vals[0], 1)} (${rk[0].name}); median ${V.fmt(mid, 1)} across ${rk.length} countries`;
    unit.textContent = `life expectancy at birth in ${y}, years`;
    V.clear(dotg); dots = [];
    cont.forEach((ct, j) => {
      const items = rk.filter((c) => c.continent === ct).map((c) => ({ c, x: sx(c.values.get(y)) }));
      const sw = swarm(items, dr), ext = Math.max(0, ...sw.map((p) => Math.abs(p.y))), room = rowH[j] / 2 - dr - 3;
      const squeeze = ext > room ? room / ext : 1;
      for (const p of sw) {
        const d = { c: p.c, x: p.x, y: rowY[j] + rowH[j] / 2 + p.y * squeeze };
        dots.push(d);
        V.dot(dotg, d.x, d.y, P.tone[0], P, dr);
      }
    });
    V.clear(tables);
    for (const [cap, list, start] of [[`The ten highest in ${y}`, rk.slice(0, 10), 1], [`The ten lowest in ${y}`, rk.slice(-10), rk.length - 9]]) {
      const wrap = V.el("div", { class: "table-wrap" }, tables), tb = V.el("table", {}, wrap);
      V.el("caption", {}, tb, cap);
      const tr = V.el("tr", {}, V.el("thead", {}, tb));
      for (const [h, r] of [["rank", 1], ["country", 0], ["continent", 0], ["years", 1]]) V.el("th", { class: r ? "r" : null }, tr, h);
      const body = V.el("tbody", {}, tb);
      list.forEach((c, j) => {
        const row = V.el("tr", {}, body);
        V.el("td", { class: "r" }, row, String(start + j));
        V.el("td", {}, row, c.name);
        V.el("td", {}, row, c.continent);
        V.el("td", { class: "r" }, row, V.fmt(c.values.get(y), 1));
      });
    }
    if (cur) focusOn(cur);
  };
  range.addEventListener("input", () => { state.year = +range.value; paint(); });
  paint();
}

export async function mount(node) {
  if (!document.getElementById("vmap-css")) V.el("style", { id: "vmap-css" }, document.head, CSS);
  node.classList.add("vmap");
  const D = await load();
  const state = { year: BASE };
  V.responsive(node, (w, P) => draw(node, w, P, D, state));
}
