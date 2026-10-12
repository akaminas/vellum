"""check_site.py: check the built site before it ships.

    python tools/check_site.py

Every local href and src in docs/**/*.html must resolve to a file, every page must have its shared blocks filled, and
no figure or viewer marker may be left without its content. Prints the problems and exits non-zero if there are any.
"""
import html, json, os, re, sys
from urllib.parse import urlparse, unquote

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.join(REPO, "docs")
problems = []

for root, _, files in os.walk(DOCS):
    if os.path.relpath(root, DOCS).startswith("dev"): continue
    for fn in files:
        if not fn.endswith(".html"): continue
        path = os.path.join(root, fn); rel = os.path.relpath(path, DOCS).replace("\\", "/")
        t = open(path, encoding="utf-8").read()
        code_free = re.sub(r"<pre.*?</pre>", "", t, flags=re.S)          # attributes inside code samples are text
        refs = re.findall(r'(?:href|src|data-full)="([^"]+)"', code_free)
        for pages in re.findall(r'data-pages="([^"]+)"', t):
            refs += json.loads(html.unescape(pages))
        for ref in refs:
            u = urlparse(html.unescape(ref))
            if u.scheme or ref.startswith(("#", "mailto:", "data:", "javascript:")): continue
            target = os.path.normpath(os.path.join(root, unquote(u.path)))
            if u.path and not os.path.exists(target):
                problems.append(f"{rel}: missing {ref}")
        if os.path.dirname(rel) == "":
            for block in ("head", "header", "footer"):
                if re.search(rf"<!--#{block}-->\s*<!--/{block}-->", t): problems.append(f"{rel}: {block} block is empty")
            for m in re.finditer(r"<!--#(fig|viewer) ([^>]+?)-->\s*<!--/(fig|viewer)-->", t):
                problems.append(f"{rel}: {m.group(1)} {m.group(2).strip()} has no content")
            for m in re.finditer(r'data-interactive="([^"]+)"', t):
                if not os.path.exists(os.path.join(DOCS, "assets", "js", "interactive", m.group(1) + ".js")):
                    problems.append(f"{rel}: interactive module {m.group(1)}.js does not exist")

for p in problems: print(p)
print(f"{len(problems)} problems")
sys.exit(1 if problems else 0)
