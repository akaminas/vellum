// site.js: the few behaviours every page shares. The theme itself is set before first paint by the inline script in
// each page's <head>; this file wires the toggle, the current nav link, the lightbox, the code tabs and copy buttons.

const root = document.documentElement;

function store(key, value) {
  try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch { return null; }
  return null;
}

// ---- theme: light or dark twin, remembered per viewer, following the system until the viewer chooses
const toggle = document.querySelector(".theme-toggle");
if (toggle) {
  const label = () => toggle.setAttribute("aria-label", root.dataset.theme === "dark" ? "Switch to the light twin" : "Switch to the dark twin");
  label();
  toggle.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    store("vellum-theme", root.dataset.theme);
    label();
  });
  const mq = matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", (e) => { if (!store("vellum-theme")) { root.dataset.theme = e.matches ? "dark" : "light"; label(); } });
}

// ---- the current page in the nav
const here = location.pathname.split("/").pop() || "index.html";
for (const a of document.querySelectorAll(".nav a, .footer-nav a")) {
  if (a.getAttribute("href") === here) a.setAttribute("aria-current", "page");
}

// ---- lightbox for zoomable figures: shows the twin that matches the theme
let box = null;
function lightbox(img) {
  if (!box) {
    box = document.createElement("dialog");
    box.className = "lightbox";
    box.innerHTML = '<div class="lb-bar"><span class="lb-cap"></span><span class="lb-links fig-links"></span><button class="icon-btn" aria-label="Close" autofocus><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div><img alt="">';
    box.querySelector("button").addEventListener("click", () => box.close());
    box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
    document.body.appendChild(box);
  }
  const big = box.querySelector("img");
  big.src = img.dataset.full || img.currentSrc || img.src;
  big.alt = img.alt;
  box.querySelector(".lb-cap").textContent = img.dataset.caption || "";
  const links = box.querySelector(".lb-links");
  links.replaceChildren();
  let list = [];
  try { list = JSON.parse(img.dataset.links || "[]"); } catch { list = []; }
  for (const [label, href] of list) {
    const a = document.createElement("a");
    a.href = href; a.textContent = label;
    links.appendChild(a);
  }
  box.showModal();
}
document.addEventListener("click", (e) => {
  const img = e.target.closest("img.zoom");
  if (img) { e.preventDefault(); lightbox(img); }
});
document.addEventListener("keydown", (e) => {
  const img = e.target.closest?.("img.zoom");
  if (img && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); lightbox(img); }
});
for (const img of document.querySelectorAll("img.zoom")) { img.tabIndex = 0; img.setAttribute("role", "button"); }

// ---- code tabs
for (const tabs of document.querySelectorAll(".tabs")) {
  const buttons = [...tabs.querySelectorAll('[role="tab"]')];
  const panels = [...tabs.querySelectorAll('[role="tabpanel"]')];
  const pick = (i) => buttons.forEach((b, k) => { b.setAttribute("aria-selected", k === i); b.tabIndex = k === i ? 0 : -1; panels[k].hidden = k !== i; });
  buttons.forEach((b, i) => {
    b.addEventListener("click", () => pick(i));
    b.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        const j = (i + (e.key === "ArrowRight" ? 1 : buttons.length - 1)) % buttons.length;
        pick(j); buttons[j].focus();
      }
    });
  });
  pick(0);
}

// ---- copy buttons on code blocks
for (const pre of document.querySelectorAll("pre[data-copy]")) {
  const btn = document.createElement("button");
  btn.className = "btn btn-ghost copy-btn";
  btn.type = "button";
  btn.textContent = "Copy";
  btn.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(pre.innerText); btn.textContent = "Copied"; } catch { btn.textContent = "Select and copy"; }
    setTimeout(() => (btn.textContent = "Copy"), 1200);
  });
  const wrap = document.createElement("div");
  wrap.className = "pre-wrap";
  pre.replaceWith(wrap); wrap.append(pre, btn);
}

// ---- slide viewers: <div class="viewer" data-pages='["a.png", ...]' data-alt="...">
for (const v of document.querySelectorAll(".viewer[data-pages]")) {
  const pages = JSON.parse(v.dataset.pages);
  const stage = v.querySelector(".viewer-stage img"), count = v.querySelector(".viewer-count");
  const strip = v.querySelector(".viewer-strip");
  let i = 0;
  const show = (k) => {
    i = (k + pages.length) % pages.length;
    stage.src = pages[i];
    stage.alt = `${v.dataset.alt || "Slide"} ${i + 1} of ${pages.length}`;
    count.textContent = `${i + 1} / ${pages.length}`;
    strip?.querySelectorAll("button").forEach((b, k2) => b.setAttribute("aria-current", k2 === i));
  };
  if (strip) pages.forEach((p, k) => {
    const b = document.createElement("button");
    b.type = "button"; b.setAttribute("aria-label", `Go to ${k + 1}`);
    const im = document.createElement("img"); im.src = p; im.alt = ""; im.loading = "lazy";
    b.appendChild(im); b.addEventListener("click", () => show(k)); strip.appendChild(b);
  });
  v.querySelector(".prev")?.addEventListener("click", () => show(i - 1));
  v.querySelector(".next")?.addEventListener("click", () => show(i + 1));
  v.tabIndex = 0;
  v.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { e.preventDefault(); show(i + 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); show(i - 1); }
  });
  show(0);
}

// ---- interactive figures: <div data-interactive="name"> loads assets/js/interactive/name.js and calls mount(el)
const base = new URL("./interactive/", import.meta.url);
for (const node of document.querySelectorAll("[data-interactive]")) {
  import(new URL(node.dataset.interactive + ".js", base).href)
    .then((m) => m.mount(node))
    .catch((err) => {
      console.error(err);
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = "This interactive figure could not load. The static figures on this page show the same data.";
      node.appendChild(p);
    });
}
