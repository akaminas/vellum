"""fetch_fishtree.py: the time-calibrated tree of the carps, minnows and loaches (order Cypriniformes) from the Fish Tree of Life.

Downloads the 11,638-species timetree of ray-finned fishes (treePL chronogram), its taxonomy and its fossil calibrations,
cuts out the subtree of the Cypriniformes (all 1,703 of whose species form one clade in the tree) and writes

    data/cypriniformes_timetree.nwk       Newick, branch lengths in millions of years
    data/cypriniformes_fossils.csv        the fossil calibrations inside the clade, with the age of the node each constrains

Source: Rabosky et al. (2018) Nature 559: 392-395, doi:10.1038/s41586-018-0273-1; data at doi:10.5061/dryad.fc71cp4 (CC0),
mirrored at https://fishtreeoflife.org/downloads/. Run once; the figure script reads the two files.
"""
import csv, io, lzma, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import DATA

BASE = "https://fishtreeoflife.org/downloads/"


def get(name):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "vellum-fetch"})
    raw = urllib.request.urlopen(req, timeout=120).read()
    return (lzma.decompress(raw) if name.endswith(".xz") else raw).decode("utf-8")


def parse(s):
    """Newick to parallel lists: parent, branch length, name, children. Iterative, the tree is 23,000 nodes deep in places."""
    parent, length, name, children = [], [], [], []

    def new(p):
        parent.append(p); length.append(0.0); name.append(None); children.append([])
        if p >= 0: children[p].append(len(parent) - 1)
        return len(parent) - 1
    s = s.strip().rstrip(";"); cur = new(-1); i = 0; tok = re.compile(r"([^(),:;]*)(?::([0-9.eE+-]+))?")
    while i < len(s):
        c = s[i]
        if c == "(": cur = new(cur); i += 1
        elif c == ",": cur = new(parent[cur]); i += 1
        elif c == ")":
            cur = parent[cur]; m = tok.match(s, i + 1)
            if m.group(1): name[cur] = m.group(1)
            if m.group(2): length[cur] = float(m.group(2))
            i = m.end()
        else:
            m = tok.match(s, i); name[cur] = m.group(1) or None
            if m.group(2): length[cur] = float(m.group(2))
            i = m.end()
    return parent, length, name, children


def leaves(children, v):
    out, st = [], [v]
    while st:
        x = st.pop()
        if children[x]: st.extend(children[x])
        else: out.append(x)
    return out


def mrca(parent, vs):
    def anc(v):
        a = []
        while v >= 0: a.append(v); v = parent[v]
        return a
    common = set.intersection(*[set(anc(v)) for v in vs])
    return next(a for a in anc(vs[0]) if a in common)


def newick(children, length, name, v, top=True):
    """Subtree at v as Newick (the Cypriniformes subtree is a few hundred levels deep at most, so recursion is fine)."""
    tail = "" if top else f":{length[v]:.6f}"
    if not children[v]: return f"{name[v]}{tail}"
    return "(" + ",".join(newick(children, length, name, c, False) for c in children[v]) + ")" + tail


if __name__ == "__main__":
    tax = {r["genus.species"].replace(" ", "_"): (r["order"], r["family"]) for r in csv.DictReader(io.StringIO(get("PFC_taxonomy.csv.xz")))}
    parent, length, name, children = parse(get("actinopt_12k_treePL.tre.xz"))
    tips = {name[v]: v for v in range(len(parent)) if not children[v]}
    depth = [0.0] * len(parent); order = [0]
    for v in order:
        for c in children[v]: depth[c] = depth[v] + length[c]; order.append(c)
    height = max(depth[t] for t in tips.values())
    cyp = [v for n, v in tips.items() if tax.get(n, ("", ""))[0] == "Cypriniformes"]
    root = mrca(parent, cyp)
    under = leaves(children, root)
    assert len(under) == len(cyp), "the Cypriniformes are one clade in the tree"
    age = lambda v: height - depth[v]
    nwk = newick(children, length, name, root)
    open(os.path.join(DATA, "cypriniformes_timetree.nwk"), "w", encoding="utf-8", newline="\n").write(nwk + "\n")
    inside = set(under)
    rows = []
    for r in csv.DictReader(io.StringIO(get("fossil_data.csv"))):
        a, b = tips.get(r["left"]), tips.get(r["right"])
        if a is None or b is None: continue
        node = mrca(parent, [a, b])
        if all(x in inside for x in leaves(children, node)):
            rows.append(dict(clade=r["clade_pretty"], fossil=r["fossil"], authority=r["authority"], min_age_ma=r["min"], max_age_ma=r["max"],
                             left=r["left"], right=r["right"], node_age_ma=f"{age(node):.2f}"))
    with open(os.path.join(DATA, "cypriniformes_fossils.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(under)} species, crown age {age(root):.1f} Ma, {len(rows)} fossil calibrations")
