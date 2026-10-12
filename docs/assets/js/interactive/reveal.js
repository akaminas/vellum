// reveal.js: the progressive reveal of "Vellum - presentations" (1329.04 and 1329.05) as an interactive figure.
// Life expectancy at birth of the four income groups, 1950–2023, from docs/data/owid-life-expectancy.csv (Our World in
// Data). Four steps add one series each, in its slot colour and with its end label, while the earlier ones stay; a
// fifth step highlights the series the claim is about in terracotta and greys the rest. The axes, the label places
// and the layout are fixed from the first step, so nothing jumps; a line under the chart says what each step adds,
// with numbers computed from the data. The figure opens on the full chart (step 4) so it reads with no interaction.

import * as V from "../vellum-web.js";

const NAME = "reveal";
const SOURCE = "UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), " +
  "Riley (2005); processed by Our World in Data";
const Y0 = 1950, Y1 = 2023;
// reveal order = slot order: the two ends of the gap first, then the two groups between them
const GROUPS = [["High-income countries", "High income"], ["Low-income countries", "Low income"],
  ["Upper-middle-income countries", "Upper-middle income"], ["Lower-middle-income countries", "Lower-middle income"]];
const FOCUS = 1;                         // the series the claim is about: low income
const TABLE_YEARS = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2019, 2020, 2021, 2022, 2023];
const SUB = "Life expectancy at birth by income group, 1950–2023. The full figure shows first; press 1, then Next or the " +
  "arrow keys, to build it one series per step as a talk would. Step 5 highlights the group the claim is about.";

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

const REVEAL_CSS = `
.rv-hit { cursor: crosshair; touch-action: pan-y; }`;

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
  injectStyle("vi-reveal-style", REVEAL_CSS);
  node.classList.add("vi");
  const text = await (await fetch(new URL("../../../data/owid-life-expectancy.csv", import.meta.url))).text();
  const byName = new Map(GROUPS.map(([n]) => [n, new Array(Y1 - Y0 + 1).fill(NaN)]));
  for (const [entity, , yr, v] of parseCSV(text).slice(1)) {
    if (byName.has(entity) && +yr >= Y0 && +yr <= Y1) byName.get(entity)[+yr - Y0] = +v;
  }
  const S = GROUPS.map(([n, label]) => ({ label, values: byName.get(n) }));
  const at = (s, y) => s.values[y - Y0], f1 = (v) => V.fmt(v, 1);
  const [hiG, loG, um, lm] = S;
  const gap = (y) => at(hiG, y) - at(loG, y), gain = (s) => at(s, Y1) - at(s, Y0);
  let dipY = Y0; for (let y = Y0; y <= 1970; y++) if (at(um, y) < at(um, dipY)) dipY = y;

  // the claim and what each step adds, every number computed here
  const title = `The life expectancy gap between high- and low-income countries fell from ${V.fmt(gap(Y0))} to ${V.fmt(gap(Y1))} years`;
  const allMore = [loG, um, lm].every((s) => gain(s) > gain(hiG)), most = S.every((s) => gain(loG) >= gain(s));
  const umGap = (y) => at(hiG, y) - at(um, y);
  const steps = [
    `High-income countries: ${f1(at(hiG, Y0))} years in 1950, ${f1(at(hiG, Y1))} in 2023, a gain of ${f1(gain(hiG))}.`,
    `Low-income countries started ${f1(gap(Y0))} years behind, at ${f1(at(loG, Y0))}; in 2023 they reach ${f1(at(loG, Y1))}, ${f1(gap(Y1))} years behind.`,
    `Upper-middle-income countries ${dipY > Y0 ? `fell to ${f1(at(um, dipY))} in ${dipY}, then ` : ""}closed ${V.fmt(100 * (1 - umGap(Y1) / umGap(Y0)))} % ` +
      `of their gap to high income: ${f1(umGap(Y0))} years in 1950, ${f1(umGap(Y1))} in 2023.`,
    `Lower-middle-income countries sit between, at ${f1(at(lm, Y1))} in 2023` +
      (allMore ? `; every group below high income gained more than its ${f1(gain(hiG))} years.` : "."),
    `Low-income countries gained ${most ? "the most, " : ""}${f1(gain(loG))} years since 1950 against ${f1(gain(hiG))} for high income, ` +
      `and remain ${f1(gap(Y1))} years behind.`,
  ];
  let step = 3, P = null, width = 0, hoverYear = null;   // the full figure first: interaction adds, never gates

  // ---- skeleton
  const plot = V.frame(node, { title, subtitle: SUB, footer: `${SOURCE} · assets/js/interactive/${NAME}.js` });
  const controls = V.el("div", { class: "vfig-controls", role: "group", "aria-label": "Steps" });
  plot.before(controls);
  const back = V.el("button", { type: "button", class: "btn btn-ghost" }, controls, "Back");
  const seg = V.el("div", { class: "seg" }, controls);
  const nums = steps.map((_, k) => {
    const b = V.el("button", { type: "button", "aria-label": k < 4 ? `Step ${k + 1}: ${S[k].label}` : "Step 5: highlight low income" }, seg, String(k + 1));
    b.addEventListener("click", () => go(k));
    return b;
  });
  const next = V.el("button", { type: "button", class: "btn btn-ghost" }, controls, "Next");
  const line = V.el("p", { class: "vi-step", "aria-live": "polite" });
  plot.after(line);
  back.addEventListener("click", () => go(step - 1));
  next.addEventListener("click", () => go(step + 1));
  node.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];   // the chart's own arrow keys read years and stop here
    if (d) { e.preventDefault(); go(step + d); }
  });
  table(node, "Life expectancy at birth in years, by income group, every ten years and each year from 2019",
    ["year", ...S.map((s) => s.label)], TABLE_YEARS.map((y) => [V.year(y), ...S.map((s) => f1(at(s, y)))]));

  function go(k) {
    step = Math.max(0, Math.min(steps.length - 1, k));
    nums.forEach((b, i) => b.setAttribute("aria-pressed", i === step));
    back.disabled = step === 0; next.disabled = step === steps.length - 1;
    line.textContent = steps[step];
    draw();
  }

  const measure = (() => { const c = document.createElement("canvas").getContext("2d"); return (s) => { c.font = `13px ${P.fontBody}`; return c.measureText(s).width; }; })();

  function draw() {
    if (!P) return;
    V.clear(plot);
    const narrow = width < 560, shown = S.slice(0, Math.min(step + 1, 4));
    const colour = (k) => (step === 4 ? (k === FOCUS ? P.tone[1] : P.rule) : P.tone[k]);   // step 5: one in terracotta
    const m = { l: 34, t: 30, b: 34, r: Math.max(...S.map((s) => measure(s.label))) + 22 };
    const H = narrow ? 320 : 400, iw = width - m.l - m.r, ih = H - m.t - m.b;
    const x = V.linear([Y0, Y1], [0, iw]), y = V.linear([30, 90], [ih, 0]);
    const svg = V.svg(plot, width, H, { title, desc: steps[step] });
    svg.setAttribute("tabindex", 0);
    svg.setAttribute("aria-label", `${title}. Step ${step + 1} of 5: ${steps[step]} Focus here and use the arrow keys to read a year.`);
    const g = V.el("g", { transform: `translate(${m.l},${m.t})` }, svg);
    V.axes(g, P, { x, y, xticks: narrow ? [1960, 1990, 2020] : [1950, 1970, 1990, 2010], yticks: [30, 50, 70, 90], xfmt: V.year,
      unit: "years of life expected at birth · the axis starts at 30", width: iw, height: ih });
    // the label places are spread once, over all four series, so a label never moves when another arrives
    const ly = V.spread(S.map((s) => y(at(s, Y1))), 16);
    const order = shown.map((s, k) => k).sort((a, b) => (a === FOCUS && step === 4) - (b === FOCUS && step === 4));
    for (const k of order) V.line(g, S[k].values.map((v, i) => [x(Y0 + i), y(v)]), colour(k));
    for (const k of order) V.dot(g, x(Y1), y(at(S[k], Y1)), colour(k), P);
    shown.forEach((s, k) => {
      const ey = y(at(s, Y1));
      if (Math.abs(ly[k] - ey) > 1.5) V.el("polyline", { points: `${x(Y1) + 6},${ey} ${x(Y1) + 8},${ly[k]}`, fill: "none", stroke: P.muted, "stroke-width": 0.75 }, g);
      V.text(g, x(Y1) + 10, ly[k], s.label, P, { size: 13 });
    });

    // hover: the crosshair snaps to the nearest year; the tooltip lists the series shown at this step
    const hover = V.el("g", { "pointer-events": "none" }, g), tip = V.tooltip(plot);
    const show = (year, py) => {
      hoverYear = year; V.clear(hover);
      if (year === null) { tip.hide(); return; }
      const rows = shown.map((s, k) => ({ v: at(s, year), s, k })).sort((a, b) => b.v - a.v);
      V.el("line", { x1: x(year), x2: x(year), y1: 0, y2: ih, stroke: P.secondary, "stroke-width": 1, opacity: 0.6 }, hover);
      for (const r of rows) V.dot(hover, x(year), y(r.v), colour(r.k), P);
      tip.show(m.l + x(year), py ?? m.t + y(rows[0].v), V.year(year), rows.map((r) => ({ value: f1(r.v), label: r.s.label, color: colour(r.k) })));
    };
    const hit = V.el("rect", { width: iw, height: ih, fill: "transparent", class: "rv-hit" }, g);
    const yearAt = (e) => Math.max(Y0, Math.min(Y1, Math.round(x.invert(e.clientX - svg.getBoundingClientRect().left - m.l))));
    for (const t of ["pointermove", "pointerdown"]) hit.addEventListener(t, (e) => show(yearAt(e), e.clientY - svg.getBoundingClientRect().top));
    hit.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") show(null); });
    svg.addEventListener("focus", () => show(Y1));
    svg.addEventListener("blur", () => show(null));
    svg.addEventListener("keydown", (e) => {
      const d = { ArrowLeft: -1, ArrowRight: 1, PageDown: -10, PageUp: 10 }[e.key];
      if (d) { e.preventDefault(); e.stopPropagation(); show(Math.max(Y0, Math.min(Y1, (hoverYear ?? Y1) + d))); }
      else if (e.key === "Escape") show(null);
    });
  }

  await document.fonts?.ready;
  V.responsive(node, (w, palette) => { width = w; P = palette; go(step); });
}
