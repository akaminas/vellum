// network.js: the co-occurrence network of Les Misérables as a force-directed graph.
//
// 77 characters, linked when they appear in the same chapter (Knuth's Stanford GraphBase, via vega-datasets). The
// layout is a force simulation computed here, seeded and run to rest before the first paint, with no animation. Nodes
// are ringed dots sized modestly by degree and coloured by the six largest groups of the data set in slot order (the
// rest in rule grey); edges are 0.4 px rule grey at 0.6 opacity, a little wider for pairs that meet in many chapters.
// Hover, tap or search a character: it and its neighbours turn terracotta, the rest fades to the grid colour, and
// their names appear. Keyboard: tab to the graph, then the arrow keys step through the characters by degree.
import * as V from "../vellum-web.js";

const DATA = new URL("../../../data/miserables.json", import.meta.url);
const SOURCE = "Donald Knuth, The Stanford GraphBase (1993); via vega-datasets 2.8.0";
const NAMES = { CountessdeLo: "Countess de Lo", "Mme.deR": "Mme. de R" };   // the data set runs a few names together

const CSS = `
.vnet .vfig-controls { gap: 8px 12px; }
.vnet .vfig-controls label { color: var(--v-muted); font-size: 0.92rem; }
.vnet .vfig-controls input[type=search] { width: 220px; max-width: 60vw; border-radius: 8px; cursor: text; }
.vnet .status { color: var(--v-muted); font-size: 0.88rem; }
.vnet .legend { display: flex; flex-wrap: wrap; gap: 4px 18px; margin: 0 0 6px; padding: 0; list-style: none; max-width: none; font-size: 0.9rem; color: var(--v-ink); }
.vnet .legend li { margin: 0; display: inline-flex; align-items: center; gap: 6px; }
.vnet .legend svg { flex: none; }
.vnet .graph { position: relative; touch-action: manipulation; }
.vnet .graph .vtip { left: auto; }
.vnet .gg:focus { outline: none; }
.vnet .gg:focus-visible .focusring { stroke: var(--v-teal); stroke-width: 2; }
.vnet details.data-table { margin-top: 14px; }
.vnet details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; }
.vnet details.data-table .table-wrap { margin: 12px 0 0; max-width: 560px; }
`;

const display = (n) => NAMES[n] || n.replace(/\.(?=\S)/g, ". ").replace(/([a-z])([A-Z0-9])/g, "$1 $2");

let loaded = null;
function load() {
  if (!loaded) loaded = fetch(DATA).then((r) => r.json()).then((d) => {
    const nodes = d.nodes.map((n, i) => ({ i, name: display(n.name), group: n.group, nb: new Set() }));
    const links = d.links.map((l) => ({ s: l.source, t: l.target, w: l.value }));
    for (const l of links) { nodes[l.s].nb.add(l.t); nodes[l.t].nb.add(l.s); }
    for (const n of nodes) n.deg = n.nb.size;
    // the six largest groups take the tones in slot order (ties by group number); each is named after its hub
    const size = new Map();
    for (const n of nodes) size.set(n.group, (size.get(n.group) || 0) + 1);
    const order = [...size.keys()].sort((a, b) => size.get(b) - size.get(a) || a - b);
    const groups = order.map((g, k) => {
      const mem = nodes.filter((n) => n.group === g);
      const hub = mem.reduce((m, n) => (n.deg > m.deg ? n : m), mem[0]);
      return { g, k, size: mem.length, hub };
    });
    const slot = new Map(groups.slice(0, 6).map((G) => [G.g, G.k]));
    for (const n of nodes) n.slot = slot.has(n.group) ? slot.get(n.group) : -1;
    const byDeg = nodes.slice().sort((a, b) => b.deg - a.deg || a.i - b.i);
    return { nodes, links, groups, byDeg };
  });
  return loaded;
}

// A seeded force layout (link springs, many-body repulsion, collision, a pull to the centre that is stronger in y on a
// wide box so the graph fills it), run to rest: alpha decays from 1 to 0.001 in 300 ticks, as in d3-force.
const layouts = new Map();
function layout(D, aspect, rad) {
  const key = aspect.toFixed(2);
  if (layouts.has(key)) return layouts.get(key);
  const n = D.nodes.length, P = D.nodes.map((d, i) => {
    const r = 10 * Math.sqrt(0.5 + i), a = i * Math.PI * (3 - Math.sqrt(5));   // phyllotaxis start: no randomness
    return { x: r * Math.cos(a), y: r * Math.sin(a), vx: 0, vy: 0 };
  });
  const kx = 0.03, ky = 0.03 * Math.max(1, aspect) ** 1.4, decay = 1 - 0.001 ** (1 / 300);
  const bias = D.links.map((l) => D.nodes[l.s].deg / (D.nodes[l.s].deg + D.nodes[l.t].deg));
  const strength = D.links.map((l) => 1 / Math.min(D.nodes[l.s].deg, D.nodes[l.t].deg));
  let alpha = 1;
  for (let tick = 0; tick < 300; tick++) {
    alpha += (0.001 - alpha) * decay;
    D.links.forEach((l, j) => {   // springs to a rest length of 34
      const a = P[l.s], b = P[l.t];
      let dx = b.x + b.vx - a.x - a.vx, dy = b.y + b.vy - a.y - a.vy;
      const len = Math.hypot(dx, dy) || 1e-6, f = ((len - 34) / len) * alpha * strength[j];
      dx *= f; dy *= f;
      b.vx -= dx * bias[j]; b.vy -= dy * bias[j];
      a.vx += dx * (1 - bias[j]); a.vy += dy * (1 - bias[j]);
    });
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {   // repulsion, exact for 77 nodes
      const a = P[i], b = P[j], dx = b.x - a.x, dy = b.y - a.y, d2 = Math.max(dx * dx + dy * dy, 1);
      const f = (-60 * alpha) / d2;
      a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
    }
    for (const p of P) { p.vx -= p.x * kx * alpha; p.vy -= p.y * ky * alpha; }
    for (const p of P) { p.vx *= 0.6; p.vy *= 0.6; p.x += p.vx; p.y += p.vy; }
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {   // no two dots overlap
      const a = P[i], b = P[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1e-6, m = rad[i] + rad[j] + 3;
      if (d < m) { const s = (m - d) / d / 2; a.x -= dx * s; a.y -= dy * s; b.x += dx * s; b.y += dy * s; }
    }
  }
  const out = P.map((p) => [p.x, p.y]);
  layouts.set(key, out);
  return out;
}

// Labels placed one by one around their dot (right, left, above, below, diagonals), each where it overlaps no label or
// dot placed before. The first label is always placed (its least crowded spot); a later one that fits nowhere is left
// out, and the count of labels placed is returned. Text has a halo in the surface colour.
function labels(g, items, P, W, H, dots) {
  let placed = 0;
  const ctx = labels.ctx || (labels.ctx = document.createElement("canvas").getContext("2d"));
  ctx.font = `12.5px ${P.fontBody}`;
  const boxes = dots.map(([x, y, r]) => [x - r, y - r, x + r, y + r]);
  const hit = (b) => boxes.reduce((s, o) => s + Math.max(0, Math.min(b[2], o[2]) - Math.max(b[0], o[0])) * Math.max(0, Math.min(b[3], o[3]) - Math.max(b[1], o[1])), 0);
  for (const { x, y, r, text } of items) {
    const w = ctx.measureText(text).width, h = 14, gap = r + 3;
    const cand = [[x + gap, y - h / 2], [x - gap - w, y - h / 2], [x - w / 2, y - gap - h], [x - w / 2, y + gap],
      [x + gap * 0.7, y - gap * 0.7 - h], [x - gap * 0.7 - w, y - gap * 0.7 - h], [x + gap * 0.7, y + gap * 0.7], [x - gap * 0.7 - w, y + gap * 0.7]];
    let best = null, bs = Infinity;
    for (const [bx, by] of cand) {
      const b = [bx, by, bx + w, by + h];
      if (b[0] < 0 || b[2] > W || b[1] < 0 || b[3] > H) continue;
      const s = hit(b);
      if (s < bs) { bs = s; best = b; }
      if (s === 0) break;
    }
    if (placed > 0 && bs > 0) continue;
    if (!best) best = [Math.min(W - w, Math.max(0, x + gap)), Math.min(H - h, Math.max(0, y - h / 2)), 0, 0];
    boxes.push([best[0], best[1], best[0] + w, best[1] + h]);
    placed++;
    V.el("text", {
      x: best[0], y: best[1] + h / 2, "dominant-baseline": "middle", "font-size": 12.5, "font-family": P.fontBody, fill: P.ink,
      stroke: P.surface, "stroke-width": 3, "stroke-linejoin": "round", "paint-order": "stroke", "pointer-events": "none",
    }, g, text);
  }
  return placed;
}

function draw(node, width, P, D, state) {
  const top = D.byDeg[0], second = D.byDeg[1], others = D.nodes.length - 1;
  const claim = `${top.name} shares a chapter with ${top.deg} of the other ${others} characters, ${top.deg - second.deg} more than anyone else`;
  const plot = V.frame(node, {
    title: claim,
    subtitle: "Characters of Les Misérables, linked when they appear in the same chapter. Force-directed layout, seeded and run to rest; " +
      "dots sized by the number of characters met and coloured by the six largest groups of the data set, each named after its most connected member. " +
      "Hover, tap or search a character.",
    footer: `${SOURCE} · assets/js/interactive/network.js`,
  });

  // ---- controls and legend
  const ctl = V.el("div", { class: "vfig-controls" }, plot);
  const sid = `vnet-q-${Math.random().toString(36).slice(2, 8)}`;
  V.el("label", { for: sid }, ctl, "Find a character");
  const q = V.el("input", { id: sid, type: "search", autocomplete: "off", spellcheck: "false", list: sid + "-l", value: state.query || "" }, ctl);
  const dl = V.el("datalist", { id: sid + "-l" }, ctl);
  for (const n of D.nodes.slice().sort((a, b) => a.name.localeCompare(b.name))) V.el("option", { value: n.name }, dl);
  const status = V.el("span", { class: "status", role: "status" }, ctl);
  const colour = (n) => (n.slot >= 0 ? P.tone[n.slot] : P.rule);
  const lg = V.el("ul", { class: "legend", "aria-label": "Groups" }, plot);
  const otherN = D.groups.slice(6).reduce((s, G) => s + G.size, 0);
  for (const [c, text] of [...D.groups.slice(0, 6).map((G) => [P.tone[G.k], `${G.hub.name}'s group (${G.size})`]), [P.rule, `other groups (${otherN})`]]) {
    const li = V.el("li", {}, lg), s = V.svg(li, 12, 12);
    s.setAttribute("aria-hidden", "true");
    V.el("circle", { cx: 6, cy: 6, r: 4.5, fill: c, stroke: P.surface, "stroke-width": 1.5 }, s);
    li.appendChild(document.createTextNode(text));
  }

  // ---- the graph
  const narrow = width < 620, H = Math.round(narrow ? width * 1.05 : Math.min(660, width * 0.6));
  const rad = D.nodes.map((n) => 3.2 + 0.9 * Math.sqrt(n.deg));
  const L = layout(D, width / H, rad);
  const x0 = Math.min(...L.map((p, i) => p[0] - rad[i])), x1 = Math.max(...L.map((p, i) => p[0] + rad[i]));
  const y0 = Math.min(...L.map((p, i) => p[1] - rad[i])), y1 = Math.max(...L.map((p, i) => p[1] + rad[i]));
  const pad = { x: narrow ? 8 : 60, y: 18 }, k = Math.min((width - 2 * pad.x) / (x1 - x0), (H - 2 * pad.y) / (y1 - y0));
  const ox = (width - (x1 - x0) * k) / 2 - x0 * k, oy = (H - (y1 - y0) * k) / 2 - y0 * k;
  const pos = L.map(([x, y]) => [ox + x * k, oy + y * k]);
  const box = V.el("div", { class: "graph" }, plot);
  const s = V.svg(box, width, H, { title: claim, desc: `A network of ${D.nodes.length} characters and ${D.links.length} links; ${top.name} has the most links (${top.deg}), then ${second.name} (${second.deg}).` });
  const gg = V.el("g", { class: "gg", tabindex: 0, role: "group", "aria-label": "Network: use the arrow keys to step through the characters from the most connected" }, s);
  V.el("rect", { class: "focusring", x: 1, y: 1, width: width - 2, height: H - 2, rx: 6, fill: "none", stroke: "none" }, gg);
  V.el("rect", { x: 0, y: 0, width, height: H, fill: "transparent" }, gg);
  const eg = V.el("g", {}, gg), ng = V.el("g", {}, gg), lab = V.el("g", {}, gg);
  const ew = (w) => Math.min(1.4, 0.4 + 0.18 * Math.sqrt(w - 1));   // weight widens an edge, modestly
  const edges = D.links.map((l) => V.el("line", {
    x1: pos[l.s][0].toFixed(1), y1: pos[l.s][1].toFixed(1), x2: pos[l.t][0].toFixed(1), y2: pos[l.t][1].toFixed(1),
    stroke: P.rule, "stroke-width": ew(l.w), "stroke-opacity": 0.6,
  }, eg));
  const dots = D.nodes.map((n) => V.dot(ng, pos[n.i][0], pos[n.i][1], colour(n), P, rad[n.i]));
  const dotBoxes = D.nodes.map((n) => [pos[n.i][0], pos[n.i][1], rad[n.i] + 1]);
  const restLabels = () => {
    V.clear(lab);
    labels(lab, D.byDeg.slice(0, 5).map((n) => ({ x: pos[n.i][0], y: pos[n.i][1], r: rad[n.i], text: n.name })), P, width, H, dotBoxes);
  };
  restLabels();

  // ---- focus: the character and its neighbours in terracotta, everything else in the grid colour
  const tip = V.tooltip(box);
  let cur = null;
  const focusOn = (n) => {
    if (cur === n) return;
    cur = n;
    D.links.forEach((l, j) => {
      const on = l.s === n.i || l.t === n.i;
      edges[j].setAttribute("stroke", on ? P.tone[1] : P.grid);
      edges[j].setAttribute("stroke-opacity", on ? 0.8 : 1);
    });
    D.nodes.forEach((m) => dots[m.i].setAttribute("fill", m === n ? P.deep[1] : n.nb.has(m.i) ? P.tone[1] : P.grid));
    for (const m of [...n.nb, n.i]) ng.appendChild(dots[m]);   // the highlighted dots on top
    V.clear(lab);
    const items = [n, ...[...n.nb].map((i) => D.nodes[i]).sort((a, b) => b.deg - a.deg)];
    const placed = labels(lab, items.map((m) => ({ x: pos[m.i][0], y: pos[m.i][1], r: rad[m.i], text: m.name })), P, width, H, items.map((m) => dotBoxes[m.i]));
    const G = D.groups.find((x) => x.g === n.group);
    const rows = [
      { value: `${n.deg} of ${others}`, label: "characters met", color: P.tone[1] },
      { value: G.k < 6 ? `${G.hub.name}'s` : "other", label: "group", color: colour(n) },
    ];
    if (placed - 1 < n.deg) rows.push({ value: `${placed - 1} of ${n.deg}`, label: "named here, for space" });
    tip.show(width, 0, n.name, rows);
  };
  const clearFocus = () => {
    if (!cur) return;
    cur = null;
    edges.forEach((e) => { e.setAttribute("stroke", P.rule); e.setAttribute("stroke-opacity", 0.6); });
    D.nodes.forEach((m) => { dots[m.i].setAttribute("fill", colour(m)); ng.appendChild(dots[m.i]); });
    restLabels(); tip.hide();
  };
  const nearest = (e) => {
    const r = s.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    let best = null, bd = 22;
    for (const n of D.nodes) { const d = Math.hypot(pos[n.i][0] - x, pos[n.i][1] - y) - rad[n.i]; if (d < bd) { bd = d; best = n; } }
    return best;
  };
  gg.addEventListener("pointermove", (e) => { if (e.pointerType !== "mouse" || state.query) return; const n = nearest(e); n ? focusOn(n) : clearFocus(); });
  gg.addEventListener("pointerdown", (e) => { const n = nearest(e); state.query = ""; q.value = ""; status.textContent = ""; n ? focusOn(n) : clearFocus(); });
  gg.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && !state.query) clearFocus(); });
  let kcur = -1;
  gg.addEventListener("keydown", (e) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1, Home: -1e3, End: 1e3 }[e.key];
    if (step === undefined) { if (e.key === "Escape") clearFocus(); return; }
    e.preventDefault();
    kcur = Math.min(D.byDeg.length - 1, Math.max(0, kcur + step));
    focusOn(D.byDeg[kcur]);
  });
  gg.addEventListener("blur", () => { if (!state.query) clearFocus(); });
  const search = () => {
    state.query = q.value.trim();
    const key = state.query.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (!key) { status.textContent = ""; clearFocus(); return; }
    const hit = D.byDeg.find((n) => n.name.toLowerCase().replace(/[^a-z0-9]/g, "").startsWith(key)) ||
      D.byDeg.find((n) => n.name.toLowerCase().replace(/[^a-z0-9]/g, "").includes(key));
    if (hit) { status.textContent = ""; focusOn(hit); } else { status.textContent = "no character by that name"; clearFocus(); }
  };
  q.addEventListener("input", search);
  if (state.query) search();

  // ---- the data: the fifteen most connected characters
  const det = V.el("details", { class: "data-table" }, plot);
  V.el("summary", {}, det, "Show the data as a table");
  const wrap = V.el("div", { class: "table-wrap" }, det), tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, `The 15 most connected of ${D.nodes.length} characters: how many others each shares a chapter with`);
  const tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["rank", 1], ["character", 0], ["characters met", 1], ["group", 0]]) V.el("th", { class: r ? "r" : null }, tr, h);
  const body = V.el("tbody", {}, tb);
  D.byDeg.slice(0, 15).forEach((n, j) => {
    const row = V.el("tr", {}, body), G = D.groups.find((x) => x.g === n.group);
    V.el("td", { class: "r" }, row, String(j + 1));
    V.el("td", {}, row, n.name);
    V.el("td", { class: "r" }, row, String(n.deg));
    const td = V.el("td", {}, row);
    V.el("span", { class: "sw", style: { background: colour(n), borderRadius: "50%" } }, td);
    td.appendChild(document.createTextNode(G.k < 6 ? `${G.hub.name}'s group` : "other"));
  });
}

export async function mount(node) {
  if (!document.getElementById("vnet-css")) V.el("style", { id: "vnet-css" }, document.head, CSS);
  node.classList.add("vnet");
  const D = await load();
  const state = { query: "" };
  V.responsive(node, (w, P) => draw(node, w, P, D, state));
}
