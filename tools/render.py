"""render.py: render an HTML page to PNG or PDF with headless Edge (or Chrome), for the media examples.

    python tools/render.py png  docs/media/infographic/square.html docs/media/infographic/square.png 1080 1080 [scale]
    python tools/render.py pdf  docs/media/report/index.html       docs/media/report/report.pdf
    python tools/render.py png  "http://localhost:8765/dev/harness.html?fig=surface3d&theme=dark" out.png 1200 800

A page that loads ES modules or fetches data must be given as an http URL (serve docs/ with `python -m http.server`).

PNG: the window is width x height CSS pixels; scale (default 1) is the device pixel ratio, so 2 gives a 2x image.
PDF: the page's own @page size and margins apply (use `@page { size: A4; margin: 0 }` in the page CSS).
"""
import os, shutil, subprocess, sys, tempfile

BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]


def browser():
    for b in BROWSERS:
        if os.path.exists(b): return b
    sys.exit("no Edge or Chrome found")


def url(path):
    if path.startswith(("http://", "https://")): return path     # pages with ES modules must be served over http
    return "file:///" + os.path.abspath(path).replace("\\", "/")


def run(args):
    profile = tempfile.mkdtemp(prefix="vellum-render-")   # one profile per call, so parallel renders never collide
    base = [browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
            "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000"]
    try:
        subprocess.run(base + args, check=True, capture_output=True, timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def png(src, out, w, h, scale=1):
    run([f"--window-size={w},{h}", f"--force-device-scale-factor={scale}", f"--screenshot={os.path.abspath(out)}", url(src)])


def pdf(src, out):
    run(["--no-pdf-header-footer", f"--print-to-pdf={os.path.abspath(out)}", url(src)])


if __name__ == "__main__":
    kind, src, out = sys.argv[1:4]
    if kind == "png":
        png(src, out, int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6]) if len(sys.argv) > 6 else 1)
    else:
        pdf(src, out)
    print("wrote", out)
