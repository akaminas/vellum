// surface3d.js: the illustrative adaptive landscape of examples/python/_common.py as a rotatable 3D surface beside
// its flat twin.
//
// The 3D panel follows "Vellum - 3D figures" (1339.04 to 1339.10): it opens at the default view (orthographic,
// elevation 24°, azimuth −58°, box aspect 1 : 1 : 0.62), turns by drag or arrow keys, and goes back with "Reset view".
// The surface is flat shaded, each quad in the lagoon colour of the mean height of its corners (no light source, no
// mesh lines), drawn back to front over transparent panes with hairline grids, three ticks per axis and seven contour
// lines on a floor 6 % below the lowest value. The twin is a heat map of the same values, gradient and limits, where
// values are read: pointing at it marks the same point on the surface, and pointing at the surface marks the twin.

import * as V from "../vellum-web.js";

const NAME = "surface3d";
const SOURCE = "Illustrative landscape w(z₁, z₂) from examples/python/_common.py";
const D0 = -2, D1 = 2;                   // the domain of both traits
const N = 60;                            // quads per side of the surface
const M = 120;                           // cells per side for the contour lines
const R = 240;                           // pixels per side of the heat map image (smoothed when drawn)
const LEVELS = [1, 2, 3, 4, 5, 6, 7].map((k) => k / 8);   // seven contour levels, on the floor and on the twin
const ASPECT = 0.62;                     // box aspect 1 : 1 : 0.62
const HOME = { el: 24, az: -58 };
const TICKS = [-1, 0, 1], WTICKS = [0, 0.5, 1];          // three ticks per axis, away from the shared corner
const SUB = "Illustrative landscape. Drag to turn it; the flat twin is where values are read.";

// w(z₁, z₂) = exp(−((z₁ − 0.9)² + (z₂ − 0.7)²) / 0.6) + 0.72 exp(−((z₁ + 0.8)² + (z₂ + 0.9)²) / 0.9)
const fit = (a, b) => Math.exp(-((a - 0.9) ** 2 + (b - 0.7) ** 2) / 0.6) + 0.72 * Math.exp(-((a + 0.8) ** 2 + (b + 0.9) ** 2) / 0.9);
const at = (t) => D0 + t * (D1 - D0);    // grid fraction to trait value

// ---------------------------------------------------------------- the shape, computed

// Newton's method on the gradient: converges to the critical point (peak or saddle) nearest the start.
function critical(a, b) {
  const h = 1e-4, g = (x, y) => [(fit(x + h, y) - fit(x - h, y)) / (2 * h), (fit(x, y + h) - fit(x, y - h)) / (2 * h)];
  let det = 0;
  for (let k = 0; k < 60; k++) {
    const [gx, gy] = g(a, b), xp = g(a + h, b), xm = g(a - h, b), yp = g(a, b + h), ym = g(a, b - h);
    const hxx = (xp[0] - xm[0]) / (2 * h), hxy = (yp[0] - ym[0]) / (2 * h), hyy = (yp[1] - ym[1]) / (2 * h);
    det = hxx * hyy - hxy * hxy;
    const da = (hyy * gx - hxy * gy) / det, db = (hxx * gy - hxy * gx) / det;
    a -= da; b -= db;
    if (Math.hypot(da, db) < 1e-10) break;
  }
  return { z1: a, z2: b, w: fit(a, b), det };
}

// Peaks are the local maxima of a fine grid, refined; the saddle is the critical point on the best path between the
// two peaks, found from the lowest point of the straight path between them (its Hessian determinant is negative).
function features() {
  const n = 200, F = new Float64Array((n + 1) ** 2);
  for (let j = 0; j <= n; j++) for (let i = 0; i <= n; i++) F[j * (n + 1) + i] = fit(at(i / n), at(j / n));
  const peaks = [];
  for (let j = 1; j < n; j++) for (let i = 1; i < n; i++) {
    const c = F[j * (n + 1) + i];
    let top = true;
    for (let dj = -1; dj <= 1 && top; dj++) for (let di = -1; di <= 1; di++) {
      if ((di || dj) && F[(j + dj) * (n + 1) + i + di] >= c) { top = false; break; }
    }
    if (top) peaks.push(critical(at(i / n), at(j / n)));
  }
  peaks.sort((p, q) => q.w - p.w);
  const [p, q] = peaks;
  let best = { t: 0, w: Infinity };
  for (let k = 0; k <= 400; k++) {
    const t = k / 400, w = fit(p.z1 + t * (q.z1 - p.z1), p.z2 + t * (q.z2 - p.z2));
    if (w < best.w) best = { t, w };
  }
  const saddle = critical(p.z1 + best.t * (q.z1 - p.z1), p.z2 + best.t * (q.z2 - p.z2));
  if (!(saddle.det < 0)) throw new Error("surface3d: the critical point between the peaks is not a saddle");
  return { peaks, saddle };
}

// Marching squares: the segments of one level of a (m+1) x (m+1) grid, in grid units, pushed to `out` as x0 y0 x1 y1.
// The two ambiguous cases are split by the value at the cell centre.
function contour(F, m, level, out) {
  const s = m + 1, t = (u, v) => (level - u) / (v - u);
  for (let j = 0; j < m; j++) for (let i = 0; i < m; i++) {
    const a = F[j * s + i], b = F[j * s + i + 1], c = F[(j + 1) * s + i + 1], d = F[(j + 1) * s + i];
    const code = (a > level) | ((b > level) << 1) | ((c > level) << 2) | ((d > level) << 3);
    if (code === 0 || code === 15) continue;
    const e = [() => [i + t(a, b), j], () => [i + 1, j + t(b, c)], () => [i + t(d, c), j + 1], () => [i, j + t(a, d)]];
    const mid = (a + b + c + d) / 4 > level;
    const pairs = {
      1: [[3, 0]], 2: [[0, 1]], 3: [[3, 1]], 4: [[1, 2]], 5: mid ? [[0, 1], [2, 3]] : [[3, 0], [1, 2]], 6: [[0, 2]],
      7: [[3, 2]], 8: [[2, 3]], 9: [[0, 2]], 10: mid ? [[3, 0], [1, 2]] : [[0, 1], [2, 3]], 11: [[1, 2]], 12: [[1, 3]],
      13: [[0, 1]], 14: [[3, 0]],
    }[code];
    for (const [p, q] of pairs) out.push(...e[p](), ...e[q]());
  }
  return out;
}

// ---------------------------------------------------------------- canvas helpers

function sized(canvas, w, h) {
  const r = window.devicePixelRatio || 1;
  canvas.width = Math.round(w * r); canvas.height = Math.round(h * r);
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  const ctx = canvas.getContext("2d");
  ctx.setTransform(r, 0, 0, r, 0, 0);
  return ctx;
}

function label(ctx, s, x, y, P, { size = 12, color = P.muted, align = "left", base = "middle", halo = false } = {}) {
  ctx.font = `${size}px ${P.fontBody}`;
  ctx.textAlign = align; ctx.textBaseline = base;
  if (halo) { ctx.lineWidth = 3; ctx.lineJoin = "round"; ctx.strokeStyle = P.surface; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y);
}

function seg(ctx, x0, y0, x1, y1) { ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); }

function ringed(ctx, x, y, color, P, r = 4.5) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI);
  ctx.fillStyle = color; ctx.fill();
  ctx.lineWidth = 1.8; ctx.strokeStyle = P.surface; ctx.stroke();
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

const S3D_CSS = `
.s3d-grid { display: grid; gap: 28px; align-items: start; }
.s3d-over { position: absolute; left: 0; top: 0; cursor: grab; touch-action: none; }
.s3d-over:active { cursor: grabbing; }
.s3d-twin { position: absolute; left: 0; top: 0; cursor: crosshair; touch-action: pan-y; }`;

// The data under the figure: a <details> with one or more compact tables, the first column a row label.
function details(parent) {
  const det = V.el("details", { class: "data-table" }, parent);
  V.el("summary", {}, det, "Show the data as a table");
  return det;
}

function table(det, caption, head, rows) {
  const t = V.el("table", {}, V.el("div", { class: "table-wrap" }, det));
  V.el("caption", {}, t, caption);
  const hr = V.el("tr", {}, V.el("thead", {}, t));
  head.forEach((h, k) => V.el("th", { class: k ? "r" : null, scope: "col" }, hr, h));
  const body = V.el("tbody", {}, t);
  for (const r of rows) {
    const tr = V.el("tr", {}, body);
    r.forEach((c, k) => V.el(k ? "td" : "th", { class: k ? "r" : null, scope: k ? null : "row" }, tr, c));
  }
  return t;
}

// ---------------------------------------------------------------- the figure

export async function mount(node) {
  injectStyle("vi-s3d-style", S3D_CSS);
  node.classList.add("vi");
  const { peaks, saddle } = features();
  const [hi, lo] = peaks;
  const n1 = N + 1, m1 = M + 1;

  // values on the surface grid and on the contour grid; colour limits as the static figure: grid minimum to the peak
  const Wsurf = new Float64Array(n1 * n1), Wfine = new Float64Array(m1 * m1);
  for (let j = 0; j < n1; j++) for (let i = 0; i < n1; i++) Wsurf[j * n1 + i] = fit(at(i / N), at(j / N));
  for (let j = 0; j < m1; j++) for (let i = 0; i < m1; i++) Wfine[j * m1 + i] = fit(at(i / M), at(j / M));
  let wmin = Infinity;
  for (const v of Wfine) wmin = Math.min(wmin, v);
  const lim = [wmin, hi.w], floorW = wmin - 0.06 * (hi.w - wmin);   // the floor sits 6 % below the lowest value
  const iso = []; for (const L of LEVELS) contour(Wfine, M, L, iso);
  const isoSeg = Float32Array.from(iso);

  // box coordinates: x and y in −0.5..0.5, z in −0.31..0.31
  const bx = (t) => (t - D0) / (D1 - D0) - 0.5;
  const bz = (w) => ((w - floorW) / (hi.w - floorW) - 0.5) * ASPECT;
  const ZB = -ASPECT / 2, ZT = ASPECT / 2;
  const VX = new Float32Array(n1 * n1), VY = new Float32Array(n1 * n1), VZ = new Float32Array(n1 * n1);
  for (let j = 0; j < n1; j++) for (let i = 0; i < n1; i++) {
    const k = j * n1 + i; VX[k] = i / N - 0.5; VY[k] = j / N - 0.5; VZ[k] = bz(Wsurf[k]);
  }
  // two levels of detail: the full 60 x 60 quads at rest, every other vertex (30 x 30) while the view is turning.
  // Each quad keeps its first vertex and the colour position of the mean height of its four corners.
  const lods = [1, 2].map((st) => {
    const n = N / st, t = new Float32Array(n * n), first = new Uint32Array(n * n);
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const v = j * st * n1 + i * st, d = st * n1;
      t[j * n + i] = ((Wsurf[v] + Wsurf[v + st] + Wsurf[v + d] + Wsurf[v + d + st]) / 4 - lim[0]) / (lim[1] - lim[0]);
      first[j * n + i] = v;
    }
    return { st, n, t, first, order: new Uint32Array(n * n).map((_, k) => k), depth: new Float32Array(n * n), colours: [] };
  });
  const SX = new Float32Array(n1 * n1), SY = new Float32Array(n1 * n1);

  const f2 = (v) => V.fmt(v, 2);
  const title = `Two adaptive peaks, at w = ${f2(hi.w)} and ${f2(lo.w)}, are joined by a saddle at w = ${f2(saddle.w)}`;
  const desc = `A surface of fitness w over two traits z₁ and z₂ in −2 to 2. The higher peak is ${f2(hi.w)} at z₁ = ${f2(hi.z1)}, ` +
    `z₂ = ${f2(hi.z2)}; the lower peak is ${f2(lo.w)} at z₁ = ${f2(lo.z1)}, z₂ = ${f2(lo.z2)}; the saddle between them is ` +
    `${f2(saddle.w)} at z₁ = ${f2(saddle.z1)}, z₂ = ${f2(saddle.z2)}.`;

  // ---- the page skeleton, built once
  const plot = V.frame(node, { title, subtitle: SUB, footer: `${SOURCE} · assets/js/interactive/${NAME}.js` });
  const controls = V.el("div", { class: "vfig-controls" });
  plot.before(controls);
  const resetBtn = V.el("button", { class: "btn btn-ghost", type: "button" }, controls, "Reset view");
  const readout = V.el("span", { class: "vi-readout", "aria-live": "polite" }, controls);
  plot.classList.add("s3d-grid");
  const panelA = V.el("div", {}, plot), panelB = V.el("div", {}, plot);
  V.el("p", { class: "vi-head" }, panelA, "a The shape: two peaks and the saddle between them");
  V.el("p", { class: "vi-head" }, panelB, "b The same values, flat, where they are read");
  const stageA = V.el("div", { class: "vi-stage" }, panelA), stageB = V.el("div", { class: "vi-stage" }, panelB);
  const cScene = V.el("canvas", { role: "img", "aria-label": desc }, stageA);
  const cOver = V.el("canvas", { class: "s3d-over", tabindex: 0, "aria-label": "Surface view: drag or use the arrow keys to turn it, Home to reset" }, stageA);
  const cHeat = V.el("canvas", { role: "img", "aria-label": "Heat map twin. " + desc }, stageB);
  const cProbe = V.el("canvas", { class: "s3d-twin", tabindex: 0, "aria-label": "Heat map: point, touch or use the arrow keys to read a value" }, stageB);
  const tip = V.tooltip(stageB);
  const grid = [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2], det = details(node);
  table(det, "The two peaks and the saddle between them", ["", "z₁", "z₂", "w"],
    [["higher peak", f2(hi.z1), f2(hi.z2), f2(hi.w)], ["lower peak", f2(lo.z1), f2(lo.z2), f2(lo.w)],
     ["saddle", f2(saddle.z1), f2(saddle.z2), f2(saddle.w)]]);
  table(det, "Fitness w at every half unit of both traits: z₂ down the rows, z₁ across", ["z₂ \\ z₁", ...grid.map((v) => V.fmt(v, 1))],
    grid.slice().reverse().map((b) => [V.fmt(b, 1), ...grid.map((a) => f2(fit(a, b)))]));

  // ---- state
  const view = { ...HOME };
  let P = null, lut = [], probe = null, L3 = null, L2 = null, pending = 0, settle = 0, dragging = null;

  // ---- 3D: projection, the scene, and the marker
  function basis() {
    const e = (view.el * Math.PI) / 180, a = (view.az * Math.PI) / 180;
    return { ex: Math.cos(e) * Math.cos(a), ey: Math.cos(e) * Math.sin(a), rx: -Math.sin(a), ry: Math.cos(a),
             ux: -Math.sin(e) * Math.cos(a), uy: -Math.sin(e) * Math.sin(a), uz: Math.cos(e), se: Math.sin(e) };
  }

  function projector(b) {
    const { w, h, m } = L3;
    // the scale fits the widest floor diagonal (any azimuth) and the tallest box at this elevation
    const s = Math.min((w - m.l - m.r) / Math.SQRT2, (h - m.t - m.b) / (b.se * Math.SQRT2 + b.uz * ASPECT));
    const cx = m.l + (w - m.l - m.r) / 2, cy = m.t + (h - m.t - m.b) / 2;
    return (x, y, z) => [cx + s * (x * b.rx + y * b.ry), cy - s * (x * b.ux + y * b.uy + z * b.uz)];
  }

  function drawScene(coarse = false) {
    const ctx = L3.scene, b = basis(), pr = projector(b);
    ctx.clearRect(0, 0, L3.w, L3.h);
    const xb = b.ex > 0 ? -0.5 : 0.5, yb = b.ey > 0 ? -0.5 : 0.5, xf = -xb, yf = -yb;   // back panes face away from the eye
    const line = (pts, color, width) => {
      ctx.beginPath(); pts.forEach((p, k) => { const [x, y] = pr(...p); k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
    };
    ctx.lineCap = "round";
    // transparent panes: their edges and a hairline grid at the ticks, in the grid colour
    line([[-0.5, -0.5, ZB], [0.5, -0.5, ZB], [0.5, 0.5, ZB], [-0.5, 0.5, ZB], [-0.5, -0.5, ZB]], P.grid, 0.75);
    line([[xb, -0.5, ZB], [xb, -0.5, ZT], [xb, 0.5, ZT], [xb, 0.5, ZB]], P.grid, 0.75);
    line([[-0.5, yb, ZB], [-0.5, yb, ZT], [0.5, yb, ZT], [0.5, yb, ZB]], P.grid, 0.75);
    for (const t of TICKS) {
      const u = bx(t);
      line([[u, -0.5, ZB], [u, 0.5, ZB]], P.grid, 0.75); line([[-0.5, u, ZB], [0.5, u, ZB]], P.grid, 0.75);
      line([[u, yb, ZB], [u, yb, ZT]], P.grid, 0.75); line([[xb, u, ZB], [xb, u, ZT]], P.grid, 0.75);
    }
    for (const t of WTICKS) {
      const u = bz(t);
      line([[xb, -0.5, u], [xb, 0.5, u]], P.grid, 0.75); line([[-0.5, yb, u], [0.5, yb, u]], P.grid, 0.75);
    }
    // seven contour lines on the floor, rule grey, 0.5 pt
    ctx.beginPath();
    for (let k = 0; k < isoSeg.length; k += 4) {
      const [x0, y0] = pr(isoSeg[k] / M - 0.5, isoSeg[k + 1] / M - 0.5, ZB), [x1, y1] = pr(isoSeg[k + 2] / M - 0.5, isoSeg[k + 3] / M - 0.5, ZB);
      seg(ctx, x0, y0, x1, y1);
    }
    ctx.strokeStyle = P.rule; ctx.lineWidth = 0.7; ctx.stroke();
    // the three outer axis lines in the rule colour: two front floor edges and the z axis at the side corner on the right
    const corners = [[xf, yb], [xb, yf]].map(([x, y]) => ({ x, y, sx: pr(x, y, ZB)[0] }));
    const zc = corners[0].sx >= corners[1].sx ? corners[0] : corners[1];
    line([[-0.5, yf, ZB], [0.5, yf, ZB]], P.rule, 1.1);
    line([[xf, -0.5, ZB], [xf, 0.5, ZB]], P.rule, 1.1);
    line([[zc.x, zc.y, ZB], [zc.x, zc.y, ZT]], P.rule, 1.1);

    // the surface: project every vertex, sort quads far to near by horizontal depth (exact for a height field seen
    // from above), fill each in its own colour and stroke it in the same colour at 0.6 px to close the seams
    const s0 = pr(0, 0, 0), sxx = pr(1, 0, 0), syy = pr(0, 1, 0), szz = pr(0, 0, 1);
    const ax = [sxx[0] - s0[0], sxx[1] - s0[1]], ay = [syy[0] - s0[0], syy[1] - s0[1]], az = [szz[0] - s0[0], szz[1] - s0[1]];
    for (let k = 0; k < SX.length; k++) {
      SX[k] = s0[0] + VX[k] * ax[0] + VY[k] * ay[0] + VZ[k] * az[0];
      SY[k] = s0[1] + VX[k] * ax[1] + VY[k] * ay[1] + VZ[k] * az[1];
    }
    const lod = lods[coarse ? 1 : 0], { st, n, first, order, depth, colours } = lod, dn = st * n1;
    for (let q = 0; q < n * n; q++) depth[q] = ((q % n) + 0.5) * b.ex + (((q / n) | 0) + 0.5) * b.ey;
    order.sort((p, q) => depth[p] - depth[q]);
    ctx.lineWidth = 0.6; ctx.lineJoin = "round";
    for (let k = 0; k < order.length; k++) {
      const q = order[k], v = first[q], c = colours[q];
      ctx.beginPath();
      ctx.moveTo(SX[v], SY[v]); ctx.lineTo(SX[v + st], SY[v + st]); ctx.lineTo(SX[v + dn + st], SY[v + dn + st]); ctx.lineTo(SX[v + dn], SY[v + dn]);
      ctx.closePath();
      ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = c; ctx.stroke();
    }
    // the peaks and the saddle, ringed in ink, so the shape named in the title can be found
    for (const p of [hi, lo, saddle]) ringed(ctx, ...pr(bx(p.z1), bx(p.z2), bz(p.w)), P.ink, P, 3.6);

    // tick labels in muted, outside the box, and the axis names
    const out = (dx, dy, dz) => { const a = pr(0, 0, 0), c = pr(dx, dy, dz), l = Math.hypot(c[0] - a[0], c[1] - a[1]) || 1; return [(c[0] - a[0]) / l, (c[1] - a[1]) / l]; };
    const align = (d) => (d < -0.35 ? "right" : d > 0.35 ? "left" : "center");
    const axisText = (t0, t1, tickPts, dir, name) => {
      for (const [p, s] of tickPts) { const [x, y] = pr(...p); label(ctx, s, x + dir[0] * 12, y + dir[1] * 12, P, { align: align(dir[0]) }); }
      const [x, y] = pr(...t0.map((v, k) => (v + t1[k]) / 2));
      label(ctx, name, x + dir[0] * 32, y + dir[1] * 32, P, { size: 13, align: align(dir[0]) });
    };
    axisText([-0.5, yf, ZB], [0.5, yf, ZB], TICKS.map((t) => [[bx(t), yf, ZB], V.fmt(t)]), out(0, Math.sign(yf), 0), "trait z₁");
    axisText([xf, -0.5, ZB], [xf, 0.5, ZB], TICKS.map((t) => [[xf, bx(t), ZB], V.fmt(t)]), out(Math.sign(xf), 0, 0), "trait z₂");
    const side = Math.sign(zc.sx - pr(0, 0, ZB)[0]) || 1;
    for (const t of WTICKS) { const [x, y] = pr(zc.x, zc.y, bz(t)); label(ctx, V.fmt(t, 1), x + side * 8, y, P, { align: side > 0 ? "left" : "right" }); }
    const [tx, ty] = pr(zc.x, zc.y, ZT);
    label(ctx, "fitness w", Math.min(L3.w - 4, Math.max(4, tx)), ty - 14, P, { size: 13, align: side > 0 ? "right" : "left" });
    L3.pr = pr; L3.lod = lod;
    readout.textContent = `elevation ${Math.round(view.el)}°, azimuth ${V.fmt(Math.round(view.az))}°`;
  }

  function drawMarker() {
    const ctx = L3.over;
    ctx.clearRect(0, 0, L3.w, L3.h);
    if (!probe) return;
    const w = fit(probe.z1, probe.z2), [x, y] = L3.pr(bx(probe.z1), bx(probe.z2), bz(w)), [fx, fy] = L3.pr(bx(probe.z1), bx(probe.z2), ZB);
    ctx.beginPath(); seg(ctx, fx, fy, x, y);   // a dotted drop line to the floor, rule grey
    ctx.setLineDash([0.01, 3]); ctx.lineCap = "round"; ctx.lineWidth = 1.2; ctx.strokeStyle = P.rule; ctx.stroke(); ctx.setLineDash([]);
    // a point hidden behind a ridge is drawn as an open ring, so the marker never seems to sit on the ridge in front
    const front = pick(x, y);
    if (front && Math.hypot(front.z1 - probe.z1, front.z2 - probe.z2) > 0.2) {
      ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 2 * Math.PI); ctx.lineWidth = 1.6; ctx.strokeStyle = P.tone[1]; ctx.stroke();
    } else ringed(ctx, x, y, P.tone[1], P, 5);
  }

  // the quad under a point of the 3D panel: the nearest one whose projection contains it, read off by barycentric weights
  function pick(px, py) {
    const { order, first, st } = L3.lod, dn = st * n1;
    for (let k = order.length - 1; k >= 0; k--) {
      const v = first[order[k]];
      for (const [a, b, c] of [[v, v + st, v + dn + st], [v, v + dn + st, v + dn]]) {
        const d = (SY[b] - SY[c]) * (SX[a] - SX[c]) + (SX[c] - SX[b]) * (SY[a] - SY[c]);
        if (!d) continue;
        const l1 = ((SY[b] - SY[c]) * (px - SX[c]) + (SX[c] - SX[b]) * (py - SY[c])) / d;
        const l2 = ((SY[c] - SY[a]) * (px - SX[c]) + (SX[a] - SX[c]) * (py - SY[c])) / d, l3 = 1 - l1 - l2;
        if (l1 < 0 || l2 < 0 || l3 < 0) continue;
        const gx = (n) => (n % n1) / N, gy = (n) => ((n / n1) | 0) / N;
        return { z1: at(l1 * gx(a) + l2 * gx(b) + l3 * gx(c)), z2: at(l1 * gy(a) + l2 * gy(b) + l3 * gy(c)) };
      }
    }
    return null;
  }

  // ---- the twin: heat map, contours, the three points, the gradient bar
  function drawTwin() {
    const { heat: ctx, sq, ml, mt } = L2;
    ctx.clearRect(0, 0, L2.w, L2.h);
    const img = document.createElement("canvas"); img.width = R; img.height = R;
    const ic = img.getContext("2d"), data = ic.createImageData(R, R), rgb = lut.map(V.hexToRgb);
    for (let j = 0; j < R; j++) for (let i = 0; i < R; i++) {
      const w = fit(at((i + 0.5) / R), at(1 - (j + 0.5) / R));
      const c = rgb[Math.max(0, Math.min(255, Math.round(((w - lim[0]) / (lim[1] - lim[0])) * 255)))], o = (j * R + i) * 4;
      data.data[o] = c[0] * 255; data.data[o + 1] = c[1] * 255; data.data[o + 2] = c[2] * 255; data.data[o + 3] = 255;
    }
    ic.putImageData(data, 0, 0);
    ctx.imageSmoothingEnabled = true; ctx.drawImage(img, ml, mt, sq, sq);
    const X = (z1) => ml + ((z1 - D0) / (D1 - D0)) * sq, Y = (z2) => mt + sq - ((z2 - D0) / (D1 - D0)) * sq;
    L2.X = X; L2.Y = Y;
    // contour lines in the surface colour, at the floor's seven levels
    ctx.beginPath();
    for (let k = 0; k < isoSeg.length; k += 4) seg(ctx, ml + (isoSeg[k] / M) * sq, mt + sq - (isoSeg[k + 1] / M) * sq, ml + (isoSeg[k + 2] / M) * sq, mt + sq - (isoSeg[k + 3] / M) * sq);
    ctx.strokeStyle = P.surface; ctx.lineWidth = 0.9; ctx.lineCap = "round"; ctx.stroke();
    // axes: muted ticks without marks, the unit line above the y axis, the x label below
    for (const t of [-2, -1, 0, 1, 2]) {
      label(ctx, V.fmt(t), ml - 8, Y(t), P, { align: "right" });
      label(ctx, V.fmt(t), X(t), mt + sq + 14, P, { align: "center" });
    }
    label(ctx, "trait z₂", ml, mt - 12, P, { size: 12.5 });
    label(ctx, "trait z₁", ml + sq / 2, mt + sq + 36, P, { size: 13, align: "center" });
    // the peaks and the saddle: ringed dots with short labels on a surface-coloured halo
    for (const [p, name] of [[hi, "peak"], [lo, "peak"], [saddle, "saddle"]]) {
      const x = X(p.z1), y = Y(p.z2), right = x < ml + sq * 0.62;
      ringed(ctx, x, y, P.ink, P);
      label(ctx, `${name}, w = ${f2(p.w)}`, x + (right ? 9 : -9), y, P, { size: 12.5, color: P.ink, align: right ? "left" : "right", halo: true });
    }
    // the gradient bar spans the plot height: labelled ends, five ticks, the quantity above it
    const bxl = ml + sq + 16, g = ctx.createLinearGradient(0, mt + sq, 0, mt);
    lut.forEach((c, k) => { if (k % 8 === 0 || k === 255) g.addColorStop(k / 255, c); });
    ctx.fillStyle = g; ctx.fillRect(bxl, mt, 8, sq);
    const by = (w) => mt + sq - ((w - lim[0]) / (lim[1] - lim[0])) * sq;
    for (const t of [0, 0.25, 0.5, 0.75, 1]) label(ctx, V.fmt(t, 2), bxl + 14, Math.max(mt + 5, Math.min(mt + sq - 5, by(t))), P);
    label(ctx, "fitness w", bxl + 8, mt - 12, P, { size: 12.5, align: "right" });
    L2.by = by; L2.bxl = bxl;
  }

  function drawProbe() {
    const { probe: ctx, sq, ml, mt, X, Y } = L2;
    ctx.clearRect(0, 0, L2.w, L2.h);
    if (!probe) { tip.hide(); return; }
    const w = fit(probe.z1, probe.z2), x = X(probe.z1), y = Y(probe.z2);
    ctx.beginPath(); seg(ctx, x, mt, x, mt + sq); seg(ctx, ml, y, ml + sq, y);   // the crosshair
    ctx.strokeStyle = P.ink; ctx.globalAlpha = 0.55; ctx.lineWidth = 1; ctx.stroke(); ctx.globalAlpha = 1;
    ringed(ctx, x, y, P.tone[1], P, 5);
    const yy = L2.by(w);   // the value on the gradient bar
    ctx.beginPath(); ctx.moveTo(L2.bxl - 1, yy); ctx.lineTo(L2.bxl - 7, yy - 4.5); ctx.lineTo(L2.bxl - 7, yy + 4.5); ctx.closePath();
    ctx.fillStyle = P.ink; ctx.fill();
    tip.show(x, y, `z₁ = ${f2(probe.z1)}, z₂ = ${f2(probe.z2)}`,
      [{ value: f2(w), label: "fitness w", color: lut[Math.round(((w - lim[0]) / (lim[1] - lim[0])) * 255)], kind: "rect" }]);
  }

  function setProbe(p) { probe = p; if (L3) { drawMarker(); drawProbe(); } }

  // one draw per animation frame; coarse while the view is turning, full detail once it rests
  function frame(coarse = false) {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(() => { drawScene(coarse); drawMarker(); });
  }

  // ---- layout: side by side when there is room, stacked on a phone
  function layout(width, palette) {
    P = palette;
    lut = Array.from({ length: 256 }, (_, k) => V.ramp(P.gradients.lagoon, k / 255));
    const wide = width >= 720, gap = 28;
    plot.style.gridTemplateColumns = wide ? `minmax(0, 56fr) minmax(0, 44fr)` : "minmax(0, 1fr)";
    const wB = wide ? Math.floor((width - gap) * 0.44) : Math.min(width, 520);
    const sq = Math.max(160, wB - 36 - 66), hB = sq + 26 + 48;
    const wA = wide ? width - gap - wB : width, hA = wide ? hB : Math.round(Math.min(wA * 0.78, 460));
    L3 = { w: wA, h: hA, m: { l: 50, r: 58, t: 34, b: 44 }, scene: sized(cScene, wA, hA), over: sized(cOver, wA, hA) };
    for (const l of lods) l.colours = Array.from(l.t, (t) => lut[Math.max(0, Math.min(255, Math.round(t * 255)))]);
    L2 = { w: wB, h: hB, sq, ml: 36, mt: 26, heat: sized(cHeat, wB, hB), probe: sized(cProbe, wB, hB) };
    drawScene(); drawMarker(); drawTwin(); drawProbe();
  }

  // ---- interaction: drag and keys turn the surface; pointing at either panel marks the same point in both
  const local = (e, c) => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  cOver.addEventListener("pointerdown", (e) => {
    cOver.setPointerCapture(e.pointerId);
    dragging = { x: e.clientX, y: e.clientY, el: view.el, az: view.az };
  });
  cOver.addEventListener("pointermove", (e) => {
    if (dragging) {
      view.az = ((dragging.az - (e.clientX - dragging.x) * 0.45 + 540) % 360) - 180;
      view.el = Math.max(5, Math.min(85, dragging.el + (e.clientY - dragging.y) * 0.35));
      frame(true);
    } else if (e.pointerType === "mouse") setProbe(pick(...local(e, cOver)));
  });
  const stop = () => { if (dragging) frame(); dragging = null; };
  cOver.addEventListener("pointerup", stop);
  cOver.addEventListener("pointercancel", stop);
  cOver.addEventListener("pointerleave", (e) => { if (!dragging && e.pointerType === "mouse") setProbe(null); });
  cOver.addEventListener("keydown", (e) => {
    const k = { ArrowLeft: [0, 5], ArrowRight: [0, -5], ArrowUp: [5, 0], ArrowDown: [-5, 0] }[e.key];
    if (k) { view.el = Math.max(5, Math.min(85, view.el + k[0])); view.az = ((view.az + k[1] + 540) % 360) - 180; }
    else if (e.key === "Home") Object.assign(view, HOME);
    else return;
    e.preventDefault(); frame(true);
    clearTimeout(settle); settle = setTimeout(frame, 200);
  });
  resetBtn.addEventListener("click", () => { Object.assign(view, HOME); frame(); });

  const twinAt = (e) => {
    const [x, y] = local(e, cProbe), { ml, mt, sq } = L2;
    if (x < ml || x > ml + sq || y < mt || y > mt + sq) return null;
    return { z1: at((x - ml) / sq), z2: at(1 - (y - mt) / sq) };
  };
  cProbe.addEventListener("pointermove", (e) => setProbe(twinAt(e)));
  cProbe.addEventListener("pointerdown", (e) => setProbe(twinAt(e)));
  cProbe.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") setProbe(null); });
  cProbe.addEventListener("focus", () => setProbe(probe || { z1: hi.z1, z2: hi.z2 }));
  cProbe.addEventListener("blur", () => setProbe(null));
  cProbe.addEventListener("keydown", (e) => {
    const k = { ArrowLeft: [-0.1, 0], ArrowRight: [0.1, 0], ArrowUp: [0, 0.1], ArrowDown: [0, -0.1] }[e.key];
    if (e.key === "Escape") { setProbe(null); return; }
    if (!k) return;
    e.preventDefault();
    const p = probe || { z1: 0, z2: 0 }, c = (v) => Math.max(D0, Math.min(D1, Math.round(v * 10) / 10));
    setProbe({ z1: c(p.z1 + k[0]), z2: c(p.z2 + k[1]) });
  });

  await document.fonts?.ready;
  V.responsive(node, layout);
}
