// gradient_explorer.js: a colour scale taken apart into its 256 steps, its greyscale, and its OKLCH lightness and chroma.
//
// Five Vellum scales (lagoon, ember, shore, the single-family teal ramp, the diverging scale; the current twin's stops
// from vellum.json) and two counterexamples: jet, the rainbow, defined piecewise-linearly as matplotlib defines it, and
// teal joined straight to terracotta in RGB. The verdict under the controls is computed from the scale: lightness in
// order or not, the smallest lightness step between stored stops, and where the chroma goes.
import * as V from "../vellum-web.js";

// matplotlib's jet (_cm._jet_data): sRGB channels as piecewise-linear functions of t
const JET = {
  r: [[0, 0], [0.35, 0], [0.66, 1], [0.89, 1], [1, 0.5]],
  g: [[0, 0], [0.125, 0], [0.375, 1], [0.64, 1], [0.91, 0], [1, 0]],
  b: [[0, 0.5], [0.11, 1], [0.34, 1], [0.65, 0], [1, 0]],
};
const N = 256;
const TOL = 0.005;   // lightness steps smaller than this count as flat, not as a reversal

const CSS = `
.vgrad .vfig-controls { gap: 8px 10px; }
.vgrad .grp { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.vgrad .grp .label { color: var(--v-muted); font-size: 0.88rem; margin-right: 2px; }
.vgrad .verdict { display: flex; align-items: flex-start; gap: 8px; color: var(--v-ink); font-size: 0.98rem; margin: 0 0 6px; max-width: 80ch; }
.vgrad .verdict svg { flex: none; margin-top: 4px; }
.vgrad .vplot { position: relative; }
.vgrad .hit:focus { outline: none; }
.vgrad .hit:focus-visible .focusring { stroke: var(--v-teal); stroke-width: 2; }
.vgrad details.data-table { margin-top: 16px; }
.vgrad details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; }
.vgrad details.data-table .table-wrap { margin: 12px 0 0; }
`;

const interp = (pts, t) => {
  for (let i = 1; i < pts.length; i++) if (t <= pts[i][0]) {
    const [t0, v0] = pts[i - 1], [t1, v1] = pts[i];
    return v0 + ((v1 - v0) * (t - t0)) / (t1 - t0);
  }
  return pts[pts.length - 1][1];
};
// sRGB of a stop list at t, interpolated between neighbouring stops as V.ramp does, but not rounded to 8 bits
const rampRgb = (stops, t) => {
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(x)), f = x - i;
  const a = V.hexToRgb(stops[i]), b = V.hexToRgb(stops[i + 1]);
  return a.map((c, k) => c + (b[k] - c) * f);
};
const lch = (rgb) => { const [L, a, b] = V.linToOklab(rgb.map(V.toLinear)); return [L, Math.hypot(a, b)]; };

// The seven scales of the current twin. rgb(t) is exact; the strip is drawn from it.
function scales(P) {
  const st = (id, label, group, stops, kind = "seq") => ({ id, label, group, stops, kind, rgb: (t) => rampRgb(stops, t) });
  return [
    st("lagoon", "lagoon", "vellum", P.gradients.lagoon),
    st("ember", "ember", "vellum", P.gradients.ember),
    st("shore", "shore", "vellum", P.gradients.shore),
    st("teal", "teal ramp", "vellum", P.sequential.teal),
    st("diverging", "diverging", "vellum", P.diverging, "div"),
    { id: "jet", label: "jet", group: "counter", kind: "jet", stops: null, rgb: (t) => ["r", "g", "b"].map((k) => interp(JET[k], t)) },
    st("join", "teal straight to terracotta", "counter", [P.tone[0], P.tone[1]], "join"),
  ];
}

// Lightness and chroma along the scale, and the verdict, all computed.
function analyse(sc) {
  const ts = Array.from({ length: N }, (_, i) => i / (N - 1));
  const rgb = ts.map(sc.rgb), lc = rgb.map(lch);
  const hex = rgb.map(V.rgbToHex);
  const L = lc.map((d) => d[0]), C = lc.map((d) => d[1]);
  const mono = (arr) => {   // monotone within TOL: no step against the overall direction larger than TOL
    const dir = Math.sign(arr[arr.length - 1] - arr[0]);
    return arr.every((v, i) => i === 0 || (v - arr[i - 1]) * dir > -TOL);
  };
  const out = { ts, hex, L, C };
  const stopsL = sc.stops ? sc.stops.map((h) => V.hexToOklch(h)[0]) : null;
  if (stopsL) out.step = Math.min(...stopsL.slice(1).map((v, i) => Math.abs(v - stopsL[i])));
  const iMinC = C.indexOf(Math.min(...C)), iMaxL = L.indexOf(Math.max(...L));
  if (sc.kind === "div") {
    const m = (sc.stops.length - 1) / 2, mid = sc.stops[m];
    out.ok = mono(stopsL.slice(0, m + 1)) && mono(stopsL.slice(m)) && mono(L.slice(0, N / 2)) && mono(L.slice(N / 2));
    const arm = Math.min(...stopsL.slice(1).map((v, i) => (i === m - 1 || i === m ? Infinity : Math.abs(v - stopsL[i]))));
    out.text = `lightness in order on each side of the neutral midpoint: ${out.ok ? "yes" : "no"}; smallest step within an arm ${V.fmt(arm, 3)}; midpoint ${mid} at chroma ${V.fmt(V.hexToOklch(mid)[1], 3)}`;
  } else if (sc.kind === "jet") {
    out.ok = mono(L);
    out.text = `lightness monotone: ${out.ok ? "yes" : "no"}; it climbs from ${V.fmt(L[0], 2)} to ${V.fmt(L[iMaxL], 2)} at t = ${V.fmt(out.ts[iMaxL], 2)}, then falls back to ${V.fmt(L[N - 1], 2)}, so both ends are dark`;
    out.peak = { L: L[iMaxL], t: out.ts[iMaxL], end: L[N - 1], start: L[0] };
  } else if (sc.kind === "join") {
    const ends = Math.min(C[0], C[N - 1]);
    out.ok = mono(L) && C[iMinC] > ends / 2;
    out.text = `lightness monotone: ${mono(L) ? "yes" : "no"}; but chroma falls from ${V.fmt(ends, 3)} at the ends to ${V.fmt(C[iMinC], 3)} at t = ${V.fmt(out.ts[iMinC], 2)}: two complements cancel to grey in the middle`;
    out.minC = { C: C[iMinC], t: out.ts[iMinC] };
  } else {
    out.ok = mono(stopsL) && mono(L);
    out.text = `lightness monotone: ${out.ok ? "yes" : "no"}; smallest step between stops ${V.fmt(out.step, 3)}; chroma ${V.fmt(Math.min(...C), 3)} to ${V.fmt(Math.max(...C), 3)}`;
  }
  return out;
}

function icon(parent, ok, P) {
  const s = V.svg(parent, 14, 14);
  s.setAttribute("aria-hidden", "true");
  V.el("circle", { cx: 7, cy: 7, r: 7, fill: ok ? P.status.good : P.status.critical }, s);
  V.el("path", { d: ok ? "M3.8 7.2 6.1 9.4 10.3 4.8" : "M4.5 4.5 9.5 9.5M9.5 4.5 4.5 9.5", fill: "none", stroke: P.surface, "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
}

// A 256-step strip at the device's resolution, as an <image> inside the SVG so it shares the charts' x axis.
function strip(g, hexAt, x0, y0, w, h) {
  const dpr = Math.max(1, Math.round(window.devicePixelRatio || 1)), cv = document.createElement("canvas");
  cv.width = Math.round(w * dpr); cv.height = 1;
  const ctx = cv.getContext("2d");
  for (let px = 0; px < cv.width; px++) {
    ctx.fillStyle = hexAt(Math.min(N - 1, Math.floor((px / cv.width) * N)));
    ctx.fillRect(px, 0, 1, 1);
  }
  return V.el("image", { x: x0, y: y0, width: w, height: h, preserveAspectRatio: "none", href: cv.toDataURL(), style: "image-rendering: pixelated" }, g);
}

function draw(node, width, P, state) {
  const all = scales(P), A = Object.fromEntries(all.map((s) => [s.id, analyse(s)]));
  const sc = all.find((s) => s.id === state.id), R = A[sc.id], jet = A.jet.peak;
  const cmp = all.find((s) => s.id === (sc.id === "jet" ? "lagoon" : "jet"));   // the comparison, in rule grey
  const vel = all.filter((s) => s.group === "vellum");
  const allOk = vel.every((s) => A[s.id].ok);
  const claim = `${allOk ? "Vellum's scales keep lightness in order" : "Not every Vellum scale keeps lightness in order"}; jet's climbs to ${V.fmt(jet.L, 2)}, then falls to ${V.fmt(jet.end, 2)}`;
  const plot = V.frame(node, {
    title: claim,
    subtitle: `A scale is ordered for every reader when its OKLCH lightness runs one way (on each side of the midpoint for the diverging scale). ` +
      `Pick a scale: its 256 steps, their greyscale, and lightness and chroma along it. Hover or focus the figure to read any step.`,
    footer: `style/vellum.json (${P.mode} twin); jet as defined in matplotlib · assets/js/interactive/gradient_explorer.js`,
  });

  const ctl = V.el("div", { class: "vfig-controls" }, plot);
  for (const [grp, name] of [["vellum", "Vellum"], ["counter", "Counterexamples"]]) {
    const row = V.el("div", { class: "grp", role: "group", "aria-label": `${name} scales` }, ctl);
    V.el("span", { class: "label" }, row, name);
    for (const s of all.filter((d) => d.group === grp)) {
      const b = V.el("button", { type: "button", class: "chip", "aria-pressed": String(s.id === state.id) }, row, s.label);
      b.addEventListener("click", () => { state.id = s.id; state.focus = s.id; draw(node, width, P, state); });
      if (state.focus === s.id) queueMicrotask(() => b.focus());
    }
  }
  state.focus = null;
  const vd = V.el("p", { class: "verdict" }, plot);
  icon(vd, R.ok, P);
  V.el("span", {}, vd, `${sc.label}: ${R.text}`);

  // ---- the figure: strip, greyscale strip, lightness chart, chroma chart, one x axis
  const narrow = width < 520;
  const m = { l: 44, r: narrow ? 70 : 150 }, w = width - m.l - m.r;
  const y0 = 22, sh = 40, gy = y0 + sh + 30, gh = 16, ly = gy + gh + 52, lh = narrow ? 130 : 150, cy = ly + lh + 52, ch = narrow ? 100 : 120;
  const H = cy + ch + (narrow ? 68 : 46);
  const box = V.el("div", { class: "vplot" }, plot);
  const s = V.svg(box, width, H, {
    title: claim,
    desc: `${sc.label}: 256 steps, its greyscale, and its OKLCH lightness and chroma from t = 0 to 1; ${sc.label} ${R.text}.`,
  });
  const g = V.el("g", { transform: `translate(${m.l},0)` }, s);
  const x = V.linear([0, 1], [0, w]);
  V.text(g, 0, y0 - 8, `${sc.label}, 256 steps`, P, { size: 12.5, color: P.muted, baseline: "auto" });
  strip(g, (i) => R.hex[i], 0, y0, w, sh);
  V.text(g, 0, gy - 8, "the same steps in greyscale (relative luminance)", P, { size: 12.5, color: P.muted, baseline: "auto" });
  const grey = R.hex.map((h) => V.simulate(h, "greyscale"));
  strip(g, (i) => grey[i], 0, gy, w, gh);

  const xt = [0, 0.25, 0.5, 0.75, 1], f2 = (v) => V.fmt(v, 2);
  const chart = (top, h, dom, yticks, key, unit, xticks, yfmt) => {
    const cg = V.el("g", { transform: `translate(0,${top})` }, g);
    const y = V.linear(dom, [h, 0]);
    V.axes(cg, P, { x, y, xticks, yticks, xfmt: f2, yfmt, unit, width: w, height: h, xlabel: xticks.length ? "position along the scale, t" : null });
    return { cg, y, key };
  };
  const Lc = chart(ly, lh, [0, 1], [0, 0.25, 0.5, 0.75, 1], "L", "OKLCH lightness", [], f2);
  const Cc = chart(cy, ch, [0, 0.32], [0, 0.1, 0.2, 0.3], "C", "OKLCH chroma", xt, (v) => V.fmt(v, 1));
  V.reference(Cc.cg, P, { y: Cc.y(0.085), x1: 0, x2: w, label: "chroma of the six tones, 0.085" });
  for (const c of [Lc, Cc]) {
    const arr = (d) => d[c.key];
    const pts = (d) => d.ts.map((t, i) => [x(t), c.y(arr(d)[i])]);
    V.line(c.cg, pts(A[cmp.id]), P.rule, { width: 1.2 });
    V.line(c.cg, pts(R), P.tone[0], { width: 2.2 });
    const ends = [[A[cmp.id], P.rule, cmp.label], [R, P.tone[0], sc.label]];
    ends.forEach(([d, col]) => V.dot(c.cg, x(1), c.y(arr(d)[N - 1]), col, P, 4));
    if (!narrow) V.endLabels(c.cg, ends.map(([d, , label]) => ({ x: x(1), y: c.y(arr(d)[N - 1]), text: label })), P, { gap: 15, size: 12.5 });
  }
  if (narrow) V.note(g, 0, H - 4, `teal line: ${sc.label}; grey line: ${cmp.label}`, P, { baseline: "auto" });

  // ---- crosshair through all panels, snapped to the 256 steps; arrow keys move it
  const tip = V.tooltip(box);
  const cross = V.el("g", { "pointer-events": "none", visibility: "hidden" }, g);
  const capS = V.el("line", { y1: y0 - 3, y2: gy + gh + 3, stroke: P.surface, "stroke-width": 4 }, cross);
  const capI = V.el("line", { y1: y0 - 3, y2: gy + gh + 3, stroke: P.ink, "stroke-width": 1.4 }, cross);
  const hair = V.el("line", { y1: ly, y2: cy + ch, stroke: P.muted, "stroke-width": 0.75 }, cross);
  const dL = V.dot(cross, 0, 0, P.tone[0], P, 4.5), dC = V.dot(cross, 0, 0, P.tone[0], P, 4.5);
  let cur = 0;
  const show = (i) => {
    cur = i;
    const px = x(R.ts[i]);
    for (const l of [capS, capI, hair]) { l.setAttribute("x1", px); l.setAttribute("x2", px); }
    dL.setAttribute("cx", px); dL.setAttribute("cy", ly + Lc.y(R.L[i]));
    dC.setAttribute("cx", px); dC.setAttribute("cy", cy + Cc.y(R.C[i]));
    cross.setAttribute("visibility", "visible");
    tip.show(m.l + px, y0 + sh, `${sc.label}, t = ${f2(R.ts[i])}`, [
      { value: R.hex[i], label: `step ${i + 1} of ${N}`, color: R.hex[i], kind: "rect" },
      { value: f2(R.L[i]), label: "OKLCH lightness" },
      { value: V.fmt(R.C[i], 3), label: "OKLCH chroma" },
    ]);
  };
  const hide = () => { cross.setAttribute("visibility", "hidden"); tip.hide(); };
  const hit = V.el("g", { class: "hit", tabindex: 0, role: "group", "aria-label": `${sc.label}: use the left and right arrow keys to read the steps` }, g);
  V.el("rect", { x: 0, y: y0 - 4, width: w, height: cy + ch - y0 + 8, fill: "transparent" }, hit);
  V.el("rect", { class: "focusring", x: -6, y: y0 - 8, width: w + 12, height: cy + ch - y0 + 16, fill: "none", stroke: "none", rx: 6 }, hit);
  hit.addEventListener("pointermove", (e) => {
    const r = hit.getBoundingClientRect();
    show(Math.min(N - 1, Math.max(0, Math.round(x.invert(e.clientX - r.left) * (N - 1)))));
  });
  hit.addEventListener("pointerleave", hide);
  hit.addEventListener("focus", () => show(cur));
  hit.addEventListener("blur", hide);
  hit.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, PageDown: -32, PageUp: 32, Home: -N, End: N }[e.key];
    if (!step) return;
    e.preventDefault(); show(Math.min(N - 1, Math.max(0, cur + step)));
  });

  // ---- the data: the stored stops, or nine samples for the scales defined without stops
  const det = V.el("details", { class: "data-table" }, plot);
  V.el("summary", {}, det, "Show the data as a table");
  const wrap = V.el("div", { class: "table-wrap" }, det), tb = V.el("table", {}, wrap);
  const rows = sc.stops && sc.stops.length > 2
    ? sc.stops.map((h, i) => [i / (sc.stops.length - 1), h])
    : Array.from({ length: 9 }, (_, i) => [i / 8, V.rgbToHex(sc.rgb(i / 8))]);
  V.el("caption", {}, tb, sc.stops && sc.stops.length > 2 ? `${sc.label}: the ${rows.length} stops in vellum.json (${P.mode} twin)` : `${sc.label}: nine samples along the scale`);
  let tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["t", 1], ["colour", 0], ["L", 1], ["C", 1], ["H", 1], ["greyscale", 0]]) V.el("th", { class: r ? "r" : null }, tr, h);
  const body = V.el("tbody", {}, tb);
  for (const [t, h] of rows) {
    const [L, C, Hh] = V.hexToOklch(h);
    tr = V.el("tr", {}, body);
    V.el("td", { class: "r" }, tr, f2(t));
    const td = V.el("td", {}, tr);
    V.el("span", { class: "sw", style: { background: h } }, td);
    td.appendChild(document.createTextNode(h));
    V.el("td", { class: "r" }, tr, f2(L));
    V.el("td", { class: "r" }, tr, V.fmt(C, 3));
    V.el("td", { class: "r" }, tr, C < 0.01 ? "–" : V.fmt(Hh, 0));
    V.el("td", {}, tr, V.simulate(h, "greyscale"));
  }
}

export async function mount(node) {
  if (!document.getElementById("vgrad-css")) V.el("style", { id: "vgrad-css" }, document.head, CSS);
  node.classList.add("vgrad");
  const state = { id: "lagoon", focus: null };
  V.responsive(node, (w, P) => draw(node, w, P, state));
}
