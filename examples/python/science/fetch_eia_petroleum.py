"""fetch_eia_petroleum.py: download the petroleum tables of the EIA Monthly Energy Review behind petroleum_sankey.py.

    python examples/python/science/fetch_eia_petroleum.py

Tables 3.1 (petroleum overview), 3.5 (products supplied by type) and 3.7a-c (petroleum consumption by sector and
product), from the MER data browser as CSV. Keeps the annual rows (YYYY13) of every series and writes them, long, to
data/eia_petroleum.csv. Source: U.S. Energy Information Administration, Monthly Energy Review; public domain.
"""
import csv, io, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "data", "eia_petroleum.csv")
URL = "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl={t}"
TABLES = ("T03.01", "T03.05", "T03.07A", "T03.07B", "T03.07C")
UA = {"User-Agent": "vellum-figure-style/1.0 (https://github.com/akaminas/vellum)"}


def main():
    rows = []
    for t in TABLES:
        with urllib.request.urlopen(urllib.request.Request(URL.format(t=t), headers=UA), timeout=120) as r:
            text = r.read().decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(text)):
            if not row["YYYYMM"].endswith("13") or row["Value"] in ("", "Not Available", "Not Meaningful"):
                continue
            rows.append(dict(table=t, msn=row["MSN"], year=row["YYYYMM"][:4], value=row["Value"],
                             description=row["Description"], unit=row["Unit"]))
    with open(os.path.abspath(OUT), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} annual values, {min(r['year'] for r in rows)}-{max(r['year'] for r in rows)}")


if __name__ == "__main__":
    main()
