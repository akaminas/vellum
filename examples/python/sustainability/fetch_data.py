"""fetch_data.py: download the two Our World in Data sustainability datasets (CC BY 4.0) and keep a trimmed copy.

    python examples/python/sustainability/fetch_data.py

Writes into data/sustainability/:
  owid-co2.csv      CO2 and greenhouse-gas emissions by country and year (github.com/owid/co2-data), trimmed to the
                    columns below and the years 1850 onward
  owid-energy.csv   primary energy and electricity by source (github.com/owid/energy-data), trimmed to the columns
                    below and the years 1965 onward
  co2_mm_mlo.csv    monthly mean CO2 at Mauna Loa, NOAA Global Monitoring Laboratory (public domain), kept raw with
                    its header of use and citation
  gistemp_v4.csv    monthly and annual global surface temperature anomaly, NASA GISS GISTEMP v4 (public domain), raw
  fetched.json      the URLs, download date, byte size and SHA-256 of each raw file, the columns kept and the row counts

The two OWID raw files are 14 MB and 9 MB; the trim keeps what the composite figures read, nothing is recomputed or rounded.
"""
import csv, datetime, hashlib, io, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "data", "sustainability"))

SETS = {
    "owid-co2.csv": dict(
        url="https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv", year_from=1850,
        cols=["country", "year", "iso_code", "population", "gdp",
              "co2", "co2_per_capita", "co2_per_gdp", "co2_per_unit_energy", "consumption_co2", "consumption_co2_per_capita",
              "trade_co2", "trade_co2_share", "cumulative_co2", "share_global_cumulative_co2", "share_global_co2",
              "coal_co2", "oil_co2", "gas_co2", "cement_co2", "flaring_co2", "other_industry_co2",
              "co2_including_luc", "land_use_change_co2", "cumulative_luc_co2", "cumulative_co2_including_luc",
              "primary_energy_consumption", "energy_per_capita", "energy_per_gdp",
              "total_ghg", "methane", "nitrous_oxide", "temperature_change_from_ghg", "temperature_change_from_co2",
              "temperature_change_from_ch4", "temperature_change_from_n2o"]),
    "owid-energy.csv": dict(
        url="https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv", year_from=1965,
        cols=["country", "year", "iso_code", "population", "gdp",
              "electricity_generation", "electricity_demand", "per_capita_electricity", "carbon_intensity_elec",
              "coal_electricity", "gas_electricity", "oil_electricity", "nuclear_electricity", "hydro_electricity",
              "wind_electricity", "solar_electricity", "biofuel_electricity", "other_renewable_exc_biofuel_electricity",
              "fossil_electricity", "low_carbon_electricity", "renewables_electricity",
              "coal_share_elec", "gas_share_elec", "oil_share_elec", "nuclear_share_elec", "hydro_share_elec",
              "wind_share_elec", "solar_share_elec", "fossil_share_elec", "low_carbon_share_elec", "renewables_share_elec",
              "primary_energy_consumption", "energy_per_capita", "energy_per_gdp",
              "fossil_share_energy", "low_carbon_share_energy", "renewables_share_energy",
              "coal_consumption", "oil_consumption", "gas_consumption", "nuclear_consumption", "hydro_consumption",
              "wind_consumption", "solar_consumption", "other_renewable_consumption", "biofuel_consumption"]),
}


RAW = {"co2_mm_mlo.csv": ("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv", "public domain (NOAA GML)"),
       "gistemp_v4.csv": ("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv", "public domain (NASA GISS)")}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "vellum-examples/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    os.makedirs(OUT, exist_ok=True)
    log = dict(downloaded=datetime.date.today().isoformat(), licence="CC BY 4.0 (Our World in Data)", files={})
    for name, s in SETS.items():
        try:
            raw = fetch(s["url"])
        except Exception as e:                                  # no network: say so and stop, the figures need these files
            sys.exit(f"could not download {s['url']}: {e}")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        missing = [c for c in s["cols"] if c not in rows[0]]
        cols = [c for c in s["cols"] if c in rows[0]]
        kept = [r for r in rows if int(r["year"]) >= s["year_from"]]
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols)
            for r in kept: w.writerow([r[c] for c in cols])
        log["files"][name] = dict(url=s["url"], raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                                  raw_rows=len(rows), raw_columns=len(rows[0]), kept_rows=len(kept), year_from=s["year_from"],
                                  columns=cols, missing_columns=missing,
                                  last_year=max(int(r["year"]) for r in rows))
        print(f"{name}: {len(kept)} of {len(rows)} rows, {len(cols)} of {len(rows[0])} columns"
              + (f"; not in the file: {', '.join(missing)}" if missing else ""))
    for name, (url, licence) in RAW.items():                    # small files, kept raw: their headers carry their terms
        try:
            raw = fetch(url)
        except Exception as e:
            sys.exit(f"could not download {url}: {e}")
        open(os.path.join(OUT, name), "wb").write(raw)
        last = [l for l in raw.decode("utf-8").splitlines() if l and l[0].isdigit()][-1].split(",")[:2]
        log["files"][name] = dict(url=url, raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(), licence=licence,
                                  last_row=",".join(last))
        print(f"{name}: last row starts {','.join(last)}")
    json.dump(log, open(os.path.join(OUT, "fetched.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
