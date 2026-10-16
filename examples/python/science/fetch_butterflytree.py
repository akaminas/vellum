"""fetch_butterflytree.py: the dated tree of butterfly genera of Chazot et al. (2019).

Downloads the core analysis (median ages, 994 genera of all seven families of Papilionoidea) and the taxon list from the
Zenodo copy of the Dryad deposit, and writes

    data/butterflies_timetree.nwk     Newick, tips Genus_species, branch lengths in millions of years; every internal node
                                      is labelled with its 95 % highest-posterior-density interval of age, "lo_hi" in Ma
    data/butterflies_taxa.csv         genus, species and family of every tip

Source: Chazot N, Wahlberg N, Freitas AVL, Mitter C, Labandeira C, Sohn J-C, Sahoo RK, Seraphim N, de Jong R and
Heikkila M (2019), Priors and posteriors in Bayesian timing of divergence analyses: the age of butterflies revisited,
Systematic Biology 68: 797-813, doi:10.1093/sysbio/syz002; data doi:10.5061/dryad.fb88292, Zenodo record 4968285 (CC0).
"""
import csv, io, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import DATA
from newick import parse, newick

ZENODO = "https://zenodo.org/api/records/4968285/files/{}/content"


def get(name):
    req = urllib.request.Request(ZENODO.format(name), headers={"User-Agent": "vellum-fetch"})
    return urllib.request.urlopen(req, timeout=180).read()


# genera in the tree that the taxon list leaves out, with their families
EXTRA = {"Abisara": "Riodinidae", "Halonympha": "Riodinidae", "Nascus": "Hesperiidae", "Panaropsis": "Riodinidae",
         "Pandemus": "Riodinidae", "Redonda": "Nymphalidae"}

if __name__ == "__main__":
    nexus = get("S_3b_core_analysis_median_ages.tre").decode("utf-8")
    trans = dict(re.findall(r"^\s*(\d+)\s+(\S+?)[,;]?$", nexus.split("Translate")[1].split(";")[0], re.M))
    body = re.search(r"tree TREE1 = \[&R\] (.*);", nexus).group(1)
    hpd = []

    def keep(m):                                                     # each [&...] comment becomes a label holding its HPD
        h = re.search(r"height_95%_HPD=\{([^,]+),([^}]+)\}", m.group(1))
        hpd.append((float(h.group(1)), float(h.group(2))) if h else None)
        return f"#{len(hpd) - 1}"
    body = re.sub(r"\[&([^\]]*)\]", keep, body)
    parent, length, name, children = parse(body)
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(get("S1_List_of_taxa.xlsx")), read_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    head = rows.index(next(r for r in rows if r and r[0] == "Code"))
    fam = {r[2]: r[1] for r in rows[head + 1:] if r[0] and r[2]}
    fam.update(EXTRA)
    taxa = []
    for v in range(len(parent)):
        tag = name[v] or ""
        base, _, idx = tag.partition("#")
        if children[v]:
            lo_hi = hpd[int(idx)] if idx else None
            name[v] = f"{lo_hi[0]:.3f}_{lo_hi[1]:.3f}" if lo_hi else None
        else:
            parts = trans[base].strip("'").split("_")                # a voucher code, then the genus and the species
            k = next(i for i, w in enumerate(parts) if w in fam)
            g, s = parts[k], "_".join(parts[k + 1:]) or "sp"
            name[v] = f"{g}_{s}"; taxa.append((g, s, fam[g]))
    open(os.path.join(DATA, "butterflies_timetree.nwk"), "w", encoding="utf-8", newline="\n").write(newick(children, length, name, 0) + ";\n")

    with open(os.path.join(DATA, "butterflies_taxa.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["genus", "species", "family"]); w.writerows(sorted(taxa))
    tips = taxa
    print(f"{len(tips)} tips, {sum(1 for v in hpd if v)} nodes with an age interval")
