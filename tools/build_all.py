"""build_all.py: regenerate every example and the site, in order, from the data.

    python tools/build_all.py            # everything (about 20 minutes)
    python tools/build_all.py science    # only the steps whose name contains "science"

Commit the inputs (style/, examples/, data/) first: each figure's footer carries the commit it was drawn from, with
-dirty when the inputs had uncommitted changes.
"""
import glob, os, subprocess, sys, time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY = sys.executable
RSCRIPT = r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe" if os.name == "nt" else "Rscript"

steps = [("ecology data", [RSCRIPT, "examples/python/ecology/export_data.R"])]
for group in ("science", "threed", "colour", "ecology", "sustainability", "maps"):
    scripts = sorted(glob.glob(os.path.join(REPO, "examples", "python", group, "*.py")))
    # helpers start with "_"; fetch_* scripts download data, which is committed, so they are run by hand
    steps += [(f"{group}/{os.path.basename(f)}", [PY, f]) for f in scripts
              if not os.path.basename(f).startswith(("_", "fetch"))]
steps += [
    ("report", [PY, "examples/python/report/make_report.py"]),
    ("infographic", [PY, "examples/python/infographic/make_infographics.py"]),
    ("pitch", [PY, "examples/python/pitch/make_pitch.py"]),
    ("latex tools", [PY, "examples/latex/build.py"]),
    ("talk", [PY, "examples/latex/talk/build.py"]),
    ("poster", [PY, "examples/latex/poster/build.py"]),
    ("r tools", [RSCRIPT, "examples/r/build.R"]),
    ("world map data", [PY, "tools/make_world.py"]),
    ("site", [PY, "tools/build_site.py"]),
    ("check", [PY, "tools/check_site.py"]),
]

only = sys.argv[1:]
failed = []
for name, cmd in steps:
    if only and not any(o in name for o in only): continue
    t = time.time()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {name:40s} {time.time() - t:6.1f} s", flush=True)
    if r.returncode:
        failed.append(name); print((r.stdout + r.stderr)[-1500:])
sys.exit(1 if failed else 0)
