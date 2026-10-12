// palette_explorer.js: every colour of the current twin from vellum.json, by job, with the checks the palette passes.
//
// Seven neutrals, six families in three steps (tint, tone, deep), four status colours. Each swatch is a button: a click
// copies its hex, hover or focus shows its OKLCH coordinates and its contrast on the surface. Below, the checks computed
// live from the JSON: colour distance between neighbouring tones in slot order (normal vision, protanopia, deuteranopia)
// and each tone's contrast on the surface and on the card, with the smallest of each against its floor.
import * as V from "../vellum-web.js";

const NEUTRAL_JOBS = {
  surface: "page and figure background", card: "panels, tiles, table stripes", grid: "gridlines, the bottom axis",
  rule: "identity line, greyed-out series", muted: "ticks, unit line, footer", secondary: "body text, error bars",
  ink: "titles, claims, labels",
};
const STEPS = [["tint", "areas and bands"], ["tone", "lines, dots, bars"], ["deep", "emphasis and text on a tint"]];
const STATUS_ICON = { good: "✓", warning: "!", serious: "▲", critical: "✕" };
const FLOOR = { nv: 15, cvd: 8, contrast: 3 };

const CSS = `
.vpal .vpal-sec { margin: 0 0 28px; }
.vpal .vpal-head { font-weight: 700; color: var(--v-ink); margin: 0 0 2px; font-size: 1rem; }
.vpal .vpal-sub { color: var(--v-muted); font-size: 0.88rem; margin: 0 0 12px; }
.vpal .vpal-grid { display: grid; gap: 10px; }
.vpal .vpal-neutrals, .vpal .vpal-status { grid-template-columns: repeat(auto-fill, minmax(132px, 1fr)); }
.vpal .swatch { min-height: 68px; padding: 10px 12px; justify-content: space-between; gap: 6px; width: 100%; }
.vpal .swatch > :only-child { margin-top: auto; }
.vpal .swatch .nm { font-size: 0.86rem; line-height: 1.2; }
.vpal .swatch .hex { font-size: 0.86rem; }
.vpal .swatch.large .hex { font-size: 19px; font-weight: 700; }
.vpal .swatch.edge { box-shadow: inset 0 0 0 1px var(--v-grid); }
.vpal .job { color: var(--v-muted); font-size: 0.82rem; line-height: 1.3; margin: 6px 2px 0; }
.vpal .colhead { font-size: 0.95rem; color: var(--v-ink); margin: 0 0 2px; }
.vpal .colhead span, .vpal .rowhead span { color: var(--v-muted); font-size: 0.82rem; }
.vpal .rowhead { font-size: 0.9rem; color: var(--v-ink); align-self: center; line-height: 1.3; }
.vpal .rowhead b { display: block; }
.vpal .famlabel { grid-column: 1 / -1; margin: 6px 0 -4px; font-size: 0.92rem; color: var(--v-ink); }
.vpal .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 0 0 20px; }
.vpal .tile { padding: 18px 20px; }
.vpal .tile .value { font-size: 2.2rem; }
.vpal .verdict { display: inline-flex; align-items: center; gap: 6px; }
.vpal .tables { display: grid; grid-template-columns: minmax(0, 7fr) minmax(0, 5fr); gap: 24px; align-items: start; }
.vpal .tables.narrow { grid-template-columns: minmax(0, 1fr); }
.vpal .table-wrap { margin: 0; }
.vpal .tables.narrow table { font-size: 0.82rem; }
.vpal .tables.narrow th, .vpal .tables.narrow td { padding: 6px 6px; }
.vpal .tables.narrow .pairkey .names { display: block; }
.vpal td.min { font-weight: 700; }
.vpal .pairkey { white-space: nowrap; }
.vpal .pairkey .sw-line { margin-right: 4px; }
.vpal .pairkey .sw-line + .sw-line { margin-left: 2px; }
.vpal .note { color: var(--v-muted); font-size: 0.88rem; margin: 14px 0 0; max-width: 80ch; }
.vpal details.data-table { margin-top: 20px; }
.vpal details.data-table summary { cursor: pointer; color: var(--v-secondary); font-size: 0.92rem; }
`;

function injectCss() {
  if (document.getElementById("vpal-css")) return;
  V.el("style", { id: "vpal-css" }, document.head, CSS);
}

// Colour distance under a simulated deficiency, from the unrounded linear values, exactly as generators/colorlab.py
// computes it (V.simulate rounds to an 8-bit hex first, which moves a distance by up to 0.14).
function cvdLab(hex, kind) {
  const lin = V.hexToRgb(hex).map(V.toLinear);
  return V.linToOklab(V.CVD[kind].map((r) => Math.min(1, Math.max(0, r[0] * lin[0] + r[1] * lin[1] + r[2] * lin[2]))));
}
const deCvd = (h1, h2, kind) => {
  const a = cvdLab(h1, kind), b = cvdLab(h2, kind);
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) * 100;
};

// Text on a swatch: the family's deep step on a tint; otherwise ink or surface, whichever reaches 4.5:1. When neither
// does, the higher one at the large-text size (14 pt bold), where 3:1 is the WCAG floor.
function textOn(bg, P, deep) {
  if (deep) return { color: deep, name: "deep", ratio: V.contrast(deep, bg), large: false };
  const ci = V.contrast(P.ink, bg), cs = V.contrast(P.surface, bg);
  if (ci >= 4.5) return { color: P.ink, name: "ink", ratio: ci, large: false };
  if (cs >= 4.5) return { color: P.surface, name: "surface", ratio: cs, large: false };
  return ci >= cs ? { color: P.ink, name: "ink", ratio: ci, large: true } : { color: P.surface, name: "surface", ratio: cs, large: true };
}

const oklchText = (hex) => {
  const [L, C, H] = V.hexToOklch(hex);
  return `${V.fmt(L, 2)}  ${V.fmt(C, 3)}  ${V.fmt(H, 0)}°`;
};

// Every value the page shows, computed once per twin from the palette.
function checks(P, S) {
  const T = P.tone, names = P.names;
  const pairs = T.slice(0, -1).map((a, i) => {
    const b = T[i + 1], prot = deCvd(a, b, "protanopia"), deut = deCvd(a, b, "deuteranopia");
    return { i, a, b, nv: V.deltaE(a, b), prot, deut, cvd: Math.min(prot, deut), kind: prot < deut ? "protanopia" : "deuteranopia" };
  });
  const tones = T.map((h, i) => ({ i, h, surf: V.contrast(h, P.surface), card: V.contrast(h, P.card) }));
  const argmin = (arr, k) => arr.reduce((m, d) => (d[k] < m[k] ? d : m), arr[0]);
  const all3 = [[0, 1], [0, 2], [1, 2]];   // the first three slots, every pair: what a scatter of three groups needs
  const three = {
    nv: Math.min(...all3.map(([i, j]) => V.deltaE(T[i], T[j]))),
    cvd: Math.min(...all3.map(([i, j]) => Math.min(deCvd(T[i], T[j], "protanopia"), deCvd(T[i], T[j], "deuteranopia")))),
  };
  return {
    pairs, tones, names, three, published: S[P.mode].checks,
    nv: argmin(pairs, "nv"), cvd: argmin(pairs, "cvd"), surf: argmin(tones, "surf"), card: argmin(tones, "card"),
  };
}

function swatch(parent, hex, P, tip, plot, { label, nameText, deep, cls = "" } = {}) {
  const t = textOn(hex, P, deep);
  const edge = V.contrast(hex, P.surface) < 1.25 ? " edge" : "";
  const b = V.el("button", {
    type: "button", class: `swatch${t.large ? " large" : ""}${edge} ${cls}`,
    "aria-label": `${label} ${hex}: copy the hex. OKLCH ${oklchText(hex)}, contrast ${V.fmt(V.contrast(hex, P.surface), 2)} to 1 on the surface`,
  }, parent);
  b.style.background = hex; b.style.color = t.color;
  if (nameText) V.el("span", { class: "nm" }, b, nameText);
  V.el("span", { class: "hex" }, b, hex);
  const show = () => {
    const pr = plot.getBoundingClientRect(), r = b.getBoundingClientRect();
    tip.show(r.left - pr.left + r.width / 2, r.top - pr.top, label, [
      { value: oklchText(hex), label: "OKLCH L C H", color: hex, kind: "rect" },
      { value: `${V.fmt(V.contrast(hex, P.surface), 2)}:1`, label: "on the surface" },
      { value: `${t.name} ${V.fmt(t.ratio, 2)}:1`, label: t.large ? "text, large size" : "text on it" },
    ]);
  };
  b.addEventListener("pointerenter", show);
  b.addEventListener("focus", show);
  b.addEventListener("pointerleave", () => tip.hide());
  b.addEventListener("blur", () => tip.hide());
  b.addEventListener("click", async () => {
    await V.copy(hex, b);
    if (!b.hasAttribute("data-copied")) {               // clipboard refused (no permission): say so instead of nothing
      b.setAttribute("data-copied", "copy blocked");
      setTimeout(() => b.removeAttribute("data-copied"), 1400);
    }
    show();
  });
  return { b, t };
}

function verdict(parent, ok, P) {
  const v = V.el("span", { class: "verdict" }, parent);
  const s = V.svg(v, 14, 14);
  s.setAttribute("aria-hidden", "true");
  V.el("circle", { cx: 7, cy: 7, r: 7, fill: ok ? P.status.good : P.status.critical }, s);
  V.el("path", { d: ok ? "M3.8 7.2 6.1 9.4 10.3 4.8" : "M4.5 4.5 9.5 9.5M9.5 4.5 4.5 9.5", fill: "none", stroke: P.surface, "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
  V.el("span", {}, v, ok ? "passes" : "fails");
  return v;
}

function draw(node, width, P, S) {
  const K = checks(P, S), narrow = width < 640;
  const f1 = (v) => V.fmt(v, 1), f2 = (v) => V.fmt(v, 2);
  const plot = V.frame(node, {
    title: `Neighbouring tones stay ${f1(K.nv.nv)} apart, and ${f1(K.cvd.cvd)} under colour-vision deficiency`,
    subtitle: `Every colour of the ${P.mode} twin, by job, from vellum.json. Distance is ΔE in OKLab × 100 between series ` +
      `in slot order. Click a swatch to copy its hex; hover or focus it for its OKLCH coordinates and contrast.`,
    footer: "style/vellum.json · assets/js/interactive/palette_explorer.js",
  });
  plot.classList.add("vpal-plot");
  const tip = V.tooltip(plot);
  const rows = [];   // the data table: every colour, every value the tooltips show

  // ---- neutrals
  let sec = V.el("section", { class: "vpal-sec", "aria-label": "Neutrals" }, plot);
  V.el("p", { class: "vpal-head" }, sec, "Seven neutrals");
  V.el("p", { class: "vpal-sub" }, sec, "White (or charcoal) and six warm greys on hue 80: the page, and every line and label on it");
  let grid = V.el("div", { class: "vpal-grid vpal-neutrals" }, sec);
  for (const [k, job] of Object.entries(NEUTRAL_JOBS)) {
    const cell = V.el("div", {}, grid);
    const { t } = swatch(cell, P[k], P, tip, plot, { label: k, nameText: k });
    V.el("p", { class: "job" }, cell, job);
    rows.push(["neutral", k, P[k], t]);
  }

  // ---- six families: columns of tint, tone, deep (rows of three on a phone)
  sec = V.el("section", { class: "vpal-sec", "aria-label": "Six families" }, plot);
  V.el("p", { class: "vpal-head" }, sec, "Six families, three steps of one hue angle each");
  V.el("p", { class: "vpal-sub" }, sec, "Columns in slot order: series one is teal, series two terracotta, and so on");
  const hueOf = (name) => S.families.find((f) => f.name === name).hue;
  if (!narrow) {
    grid = V.el("div", { class: "vpal-grid", style: { gridTemplateColumns: "minmax(120px, 0.9fr) repeat(6, minmax(0, 1fr))" } }, sec);
    V.el("div", {}, grid);
    P.names.forEach((n) => {
      const h = V.el("p", { class: "colhead" }, grid, n + " ");
      V.el("span", {}, h, `${hueOf(n)}°`);
    });
    for (const [step, job] of STEPS) {
      const rh = V.el("div", { class: "rowhead" }, grid);
      V.el("b", {}, rh, step);
      V.el("span", {}, rh, job);
      P.names.forEach((n, i) => {
        const hex = P[step][i];
        const { t } = swatch(grid, hex, P, tip, plot, { label: `${n} ${step}`, deep: step === "tint" ? P.deep[i] : null });
        rows.push([step, n, hex, t]);
      });
    }
  } else {
    grid = V.el("div", { class: "vpal-grid", style: { gridTemplateColumns: "repeat(3, minmax(0, 1fr))" } }, sec);
    for (const [step, job] of STEPS) {
      const rh = V.el("div", { class: "rowhead" }, grid);
      V.el("b", {}, rh, step);
      V.el("span", {}, rh, job);
    }
    P.names.forEach((n, i) => {
      const lab = V.el("p", { class: "famlabel" }, grid, n + " ");
      V.el("span", { class: "muted" }, lab, `${hueOf(n)}°`);
      for (const [step] of STEPS) {
        const hex = P[step][i];
        const { t } = swatch(grid, hex, P, tip, plot, { label: `${n} ${step}`, deep: step === "tint" ? P.deep[i] : null });
        rows.push([step, n, hex, t]);
      }
    });
  }

  // ---- status
  sec = V.el("section", { class: "vpal-sec", "aria-label": "Status colours" }, plot);
  V.el("p", { class: "vpal-head" }, sec, "Four status colours");
  V.el("p", { class: "vpal-sub" }, sec, "Reserved, always with an icon and a label, never a series");
  grid = V.el("div", { class: "vpal-grid vpal-status" }, sec);
  for (const [k, hex] of Object.entries(P.status)) {
    const { t } = swatch(grid, hex, P, tip, plot, { label: `status ${k}`, nameText: `${STATUS_ICON[k]}  ${k}` });
    rows.push(["status", k, hex, t]);
  }

  // ---- the checks
  sec = V.el("section", { class: "vpal-sec", "aria-label": "Checks" }, plot);
  V.el("p", { class: "vpal-head" }, sec, "The checks, computed from the JSON as you read them");
  V.el("p", { class: "vpal-sub" }, sec, "Colour-vision deficiency simulated with the Machado, Oliveira and Fernandes (2009) matrices at full severity; contrast is the WCAG ratio");
  const tiles = V.el("div", { class: "tiles" }, sec);
  const tile = (value, label, compare, ok) => {
    const d = V.el("div", { class: "tile" }, tiles);
    V.el("span", { class: "value" }, d, value);
    V.el("span", { class: "label" }, d, label);
    const c = V.el("span", { class: "compare" }, d, compare + " · ");
    verdict(c, ok, P);
  };
  const nm = K.names;
  tile(f1(K.nv.nv), `smallest distance between neighbouring tones (${nm[K.nv.i]} and ${nm[K.nv.i + 1]})`, `floor ${FLOOR.nv}`, K.nv.nv >= FLOOR.nv);
  tile(f1(K.cvd.cvd), `smallest under colour-vision deficiency (${nm[K.cvd.i]} and ${nm[K.cvd.i + 1]}, ${K.cvd.kind})`, `target ${FLOOR.cvd}`, K.cvd.cvd >= FLOOR.cvd);
  tile(`${f2(K.surf.surf)}:1`, `lowest contrast of a tone on the surface ${P.surface} (${nm[K.surf.i]})`, `floor ${FLOOR.contrast}:1`, K.surf.surf >= FLOOR.contrast);

  const tables = V.el("div", { class: "tables" + (narrow ? " narrow" : "") }, sec);
  // neighbouring pairs
  let wrap = V.el("div", { class: "table-wrap" }, tables);
  let tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, "Neighbouring tones in slot order, ΔE (OKLab × 100); the smallest of each column in bold");
  let tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["pair", 0], ["normal", 1], ["protanopia", 1], ["deuteranopia", 1]]) V.el("th", { class: r ? "r" : null }, tr, h);
  let body = V.el("tbody", {}, tb);
  const minProt = Math.min(...K.pairs.map((d) => d.prot)), minDeut = Math.min(...K.pairs.map((d) => d.deut));
  for (const d of K.pairs) {
    tr = V.el("tr", {}, body);
    const td = V.el("td", { class: "pairkey" }, tr);
    V.el("span", { class: "sw-line", style: { background: d.a } }, td);
    V.el("span", { class: "sw-line", style: { background: d.b } }, td);
    V.el("span", { class: "names" }, td, `${nm[d.i]}, ${nm[d.i + 1]}`);
    V.el("td", { class: "r" + (d === K.nv ? " min" : "") }, tr, f1(d.nv));
    V.el("td", { class: "r" + (d.prot === minProt ? " min" : "") }, tr, f1(d.prot));
    V.el("td", { class: "r" + (d.deut === minDeut ? " min" : "") }, tr, f1(d.deut));
  }
  // tones on surface and card
  wrap = V.el("div", { class: "table-wrap" }, tables);
  tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, "Each tone's contrast; the lowest of each column in bold");
  tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["tone", 0], [`on surface ${P.surface}`, 1], [`on card ${P.card}`, 1]]) V.el("th", { class: r ? "r" : null }, tr, h);
  body = V.el("tbody", {}, tb);
  for (const d of K.tones) {
    tr = V.el("tr", {}, body);
    const td = V.el("td", {}, tr);
    V.el("span", { class: "sw-line", style: { background: d.h } }, td);
    td.appendChild(document.createTextNode(nm[d.i]));
    V.el("td", { class: "r" + (d === K.surf ? " min" : "") }, tr, `${f2(d.surf)}:1`);
    V.el("td", { class: "r" + (d === K.card ? " min" : "") }, tr, `${f2(d.card)}:1`);
  }
  // what vellum.json records, against what is computed here
  const pub = K.published, onCard = Math.abs(pub.min_contrast - K.card.card) < 0.006, onSurf = Math.abs(pub.min_contrast - K.surf.surf) < 0.006;
  const nvOk = f1(pub.min_nv) === f1(K.nv.nv) && f1(pub.min_cvd) === f1(K.cvd.cvd);
  let msg = `vellum.json (key checks) records ${f1(pub.min_nv)}, ${f1(pub.min_cvd)} and ${f2(pub.min_contrast)}:1 for this twin. ` +
    (nvOk ? "The two distances match the tables. " : "The distances differ from the tables above, which are computed from the current values. ");
  if (onCard) msg += `Its contrast floor was checked on the card ${P.card}, the harder case (${f2(K.card.card)}:1); on the surface ${P.surface} the lowest is ${f2(K.surf.surf)}:1.`;
  else if (onSurf) msg += `Its contrast floor was checked on the surface ${P.surface}; on the card ${P.card} the lowest is ${f2(K.card.card)}:1.`;
  else msg += `Computed here: ${f2(K.surf.surf)}:1 on the surface and ${f2(K.card.card)}:1 on the card.`;
  if (K.three.nv >= FLOOR.nv && K.three.cvd >= FLOOR.cvd) {
    msg += ` The first three tones also pass as every pair (smallest ${f1(K.three.nv)}, and ${f1(K.three.cvd)} under deficiency), so a scatter or map may carry three series without labels.`;
  }
  V.el("p", { class: "note" }, sec, msg);

  // ---- every colour as a table
  const det = V.el("details", { class: "data-table" }, plot);
  V.el("summary", {}, det, "Show the data as a table");
  wrap = V.el("div", { class: "table-wrap" }, det);
  tb = V.el("table", {}, wrap);
  V.el("caption", {}, tb, `All ${rows.length} colours of the ${P.mode} twin with their OKLCH coordinates and contrast`);
  tr = V.el("tr", {}, V.el("thead", {}, tb));
  for (const [h, r] of [["job", 0], ["name", 0], ["hex", 0], ["L", 1], ["C", 1], ["H", 1], ["on surface", 1], ["text on swatch", 0]]) V.el("th", { class: r ? "r" : null }, tr, h);
  body = V.el("tbody", {}, tb);
  for (const [job, name, hex, t] of rows) {
    const [L, C, H] = V.hexToOklch(hex);
    tr = V.el("tr", {}, body);
    V.el("td", {}, tr, job);
    const td = V.el("td", {}, tr);
    V.el("span", { class: "sw", style: { background: hex, boxShadow: `inset 0 0 0 1px ${P.grid}` } }, td);
    td.appendChild(document.createTextNode(name));
    V.el("td", { class: "num" }, tr, hex);
    V.el("td", { class: "r" }, tr, V.fmt(L, 2));
    V.el("td", { class: "r" }, tr, V.fmt(C, 3));
    V.el("td", { class: "r" }, tr, V.fmt(H, 0));
    V.el("td", { class: "r" }, tr, `${f2(V.contrast(hex, P.surface))}:1`);
    V.el("td", {}, tr, `${t.name} ${f2(t.ratio)}:1${t.large ? ", large" : ""}`);
  }
}

export async function mount(node) {
  injectCss();
  node.classList.add("vpal");
  const S = await V.spec();
  V.responsive(node, (w, P) => draw(node, w, P, S));
}
