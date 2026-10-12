# Sustainability data: sources

Downloaded on 2026-10-12 by `examples/python/sustainability/fetch_data.py`, which also writes `fetched.json` (the URL, byte
size and SHA-256 of each raw file, the columns kept and the row counts). Run it again to refresh; the figures assert the
numbers of their claims, so a new release that changes a claim stops the script instead of drawing a wrong title.

| File | What it holds | Source and citation | Licence |
|---|---|---|---|
| `owid-co2.csv` | CO₂ and greenhouse-gas emissions by country, region and year, 1850–2024: territorial (`co2`, by fuel: `coal_co2`, `oil_co2`, `gas_co2`, `cement_co2`, `flaring_co2`, `other_industry_co2`), with land-use change (`co2_including_luc`, `land_use_change_co2`, cumulative columns), consumption-based (`consumption_co2`, `trade_co2`, `trade_co2_share`), per person, per GDP and per unit of energy, `population`, `gdp`, `primary_energy_consumption`, `energy_per_gdp`, other gases and the warming attributed to each gas (36 of 79 columns; rows from 1850, 44 170 of 50 411) | Our World in Data, *Data on CO₂ and Greenhouse Gas Emissions* (Pablo Rosado, Hannah Ritchie, Max Roser, Edouard Mathieu, Bobbie Macdonald), github.com/owid/co2-data, file `owid-co2-data.csv`. Underlying data: Friedlingstein, P. et al. (2025), *Global Carbon Budget 2025*, Global Carbon Project; Jones, M. W. et al. (2023), National contributions to climate change due to historical emissions of carbon dioxide, methane and nitrous oxide, *Scientific Data* 10, 155; Energy Institute (2025), *Statistical Review of World Energy*; U.S. Energy Information Administration, *International Energy Data*; Bolt, J. and van Zanden, J. L. (2024), *Maddison Project Database 2023* (GDP in 2011 international dollars); United Nations, *World Population Prospects 2024*, via OWID's population series | CC BY 4.0 (Our World in Data); third-party data under their own terms, as listed in the OWID codebook |
| `owid-energy.csv` | Primary energy and electricity by country, region and year, 1965–2025: generation by source (`coal_electricity` … `solar_electricity`, `biofuel_electricity`, `other_renewable_exc_biofuel_electricity`), shares (`low_carbon_share_elec`, `fossil_share_elec`, …), `electricity_generation`, `carbon_intensity_elec`, primary energy and its shares (46 of 130 columns; rows from 1965, 15 707 of 23 377) | Our World in Data, *Data on Energy* (Pablo Rosado, Hannah Ritchie, Edouard Mathieu, Max Roser), github.com/owid/energy-data, file `owid-energy-data.csv` (the legacy release, whose electricity mix was last updated with Ember's data on 2026-04-27). Underlying data: Ember (2026), *Yearly Electricity Data*; Energy Institute (2025), *Statistical Review of World Energy*; U.S. EIA, *International Energy Data*; Maddison Project Database 2023; OWID population | CC BY 4.0 (Our World in Data); third-party data under their own terms |
| `co2_mm_mlo.csv` | Monthly mean CO₂ at Mauna Loa, ppm, March 1958 to September 2026, with the deseasonalised series (raw, header kept) | Lan, X., Tans, P. and Thoning, K. W., *Trends in atmospheric carbon dioxide*, NOAA Global Monitoring Laboratory, gml.noaa.gov/ccgg/trends/, file created 9 October 2026; data from March 1958 to April 1974 by C. D. Keeling, Scripps Institution of Oceanography. Measurements from December 2022 to 4 July 2023 come from Maunakea, after the eruption of Mauna Loa | public domain (U.S. Government work); NOAA asks for credit, as above |
| `gistemp_v4.csv` | Global land–ocean surface temperature anomaly, monthly and annual (`J-D`), 1880 to 2026, °C against 1951–1980 (raw) | GISTEMP Team (2026), *GISS Surface Temperature Analysis (GISTEMP), version 4*, NASA Goddard Institute for Space Studies, data.giss.nasa.gov/gistemp/; Lenssen, N. et al. (2019), Improvements in the GISTEMP uncertainty model, *J. Geophys. Res. Atmos.* 124, 6307–6326 | public domain (U.S. Government work) |

Also used, already in `data/`: `ne_110m_admin_0_countries.geojson` (Natural Earth v5.1.2, public domain) for the maps and for
the continent of each country.

## How the figures use them

- `sus_electricity.py` and `sus_infographic.py`: `owid-energy.csv`, 2000–2025 (the source columns are complete from 2000;
  bioenergy is missing before). The country map uses 2024, the last year with near-complete coverage (195 countries; 2025
  has 90).
- `sus_decoupling.py`: `owid-co2.csv`, 2005–2022 (2022 is the last year of the Maddison GDP series); cumulative CO₂ to 2024.
- `sus_kaya.py`: `owid-co2.csv`; world GDP is published only for 1970, 1980, 1990, 2000, 2010 and 2015–2022, so the
  decomposition uses those years and the two GDP factors are drawn through them.
- `sus_carbon_budget.py`: `co2_mm_mlo.csv` (calendar-year means of complete years), `gistemp_v4.csv` (annual `J-D`,
  re-based to 1880–1900) and `owid-co2.csv` (emissions with land-use change, cumulative from 1850).
