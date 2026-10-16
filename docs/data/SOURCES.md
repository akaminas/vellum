# Data used by the examples

Every example figure is drawn from one of these files. Where a figure uses invented or toy numbers, its subtitle or footer says "illustrative".

| file | what it is | source | licence |
|---|---|---|---|
| `penguins.json` | Body measurements of 344 penguins of three species on three islands of the Palmer Archipelago, 2007–2009 | Gorman, Williams and Fraser (2014), *PLoS ONE* 9(3): e90081; Palmer Station LTER; via the `palmerpenguins` R package and vega-datasets 2.8.0 | CC0 |
| `co2-concentration.csv` | Monthly mean atmospheric CO₂ at Mauna Loa, March 1958 to April 2020, in ppm, raw and seasonally adjusted | NOAA Global Monitoring Laboratory and Scripps Institution of Oceanography; via vega-datasets 2.8.0 | public domain (US Government work) |
| `owid-life-expectancy.csv` | Period life expectancy at birth by country and region, to 2023 | UN World Population Prospects (2024), Human Mortality Database (2024), Zijdeman and Ribeira da Silva (2015), Riley (2005); processed by Our World in Data, downloaded 2026-10-12 | CC BY 4.0 |
| `disasters.csv` | Global deaths from natural disasters by type of disaster and year, 1900–2017 | EM-DAT, CRED / UCLouvain; processed by Our World in Data; via vega-datasets 2.8.0 | CC BY 4.0 (Our World in Data) |
| `gapminder.json` | Life expectancy, fertility and population of 63 countries every five years, 1955–2005 | Gapminder Foundation; via vega-datasets 2.8.0 | CC BY 4.0 |
| `cars.json` | Fuel economy, cylinders, displacement, horsepower, weight and acceleration of 406 cars, 1970–1982 | UCI Machine Learning Repository, Auto MPG data set (Quinlan 1993); via vega-datasets 2.8.0 | CC BY 4.0 |
| `driving.json` | Miles driven per capita and the price of a gallon of petrol in the United States, 1956–2010 | Hannah Fairfield, "Driving Shifts Into Reverse", *The New York Times*, 2 May 2010; via vega-datasets 2.8.0 | as published by vega-datasets (BSD-3-Clause package) |
| `miserables.json` | Co-occurrence of 77 characters in the chapters of *Les Misérables* | Donald Knuth, *The Stanford GraphBase* (1993); via vega-datasets 2.8.0 | public domain |
| `population.json` | United States population by age group and sex, every ten years, 1850–2000 | IPUMS USA, Minnesota Population Center; via vega-datasets 2.8.0 | as published by vega-datasets (BSD-3-Clause package) |
| `ne_110m_admin_0_countries.geojson` | Country outlines at 1:110 million | Natural Earth v5.1.2 | public domain |
| `eia_petroleum.csv` | Annual US petroleum supply, products supplied and consumption by sector and product, 1949–2025, thousand barrels a day; every annual row of tables 3.1, 3.5 and 3.7a–c, written long by `examples/python/science/fetch_eia_petroleum.py`, downloaded 2026-10-15 | U.S. Energy Information Administration, *Monthly Energy Review*, via the MER data browser | public domain (US Government work) |
| `canids_freedman2014.csv` | Effective population sizes, split times and total migration rates of dogs, wolves and the golden jackal from the main G-PhoCS model, raw (×10⁴) and calibrated (μ = 1 × 10⁻⁸ per generation, three-year generations), with 95 % intervals; transcribed from Table S12 | Freedman, Gronau, Schweizer et al. (2014), *Genome sequencing highlights the dynamic early history of dogs*, *PLOS Genetics* 10(1): e1004016, Table S12, doi:10.1371/journal.pgen.1004016.s018 | CC0 |
| `cypriniformes_timetree.nwk` | Time-calibrated phylogeny of the 1,703 species of the order Cypriniformes (carps, minnows, loaches, suckers), branch lengths in millions of years; the Cypriniformes subtree of the 11,638-species treePL chronogram, cut out by `examples/python/science/fetch_fishtree.py`, downloaded 2026-10-16 | Rabosky et al. (2018), *An inverse latitudinal gradient in speciation rate for marine fishes*, *Nature* 559: 392–395, doi:10.1038/s41586-018-0273-1; data doi:10.5061/dryad.fc71cp4, mirrored by the Fish Tree of Life (fishtreeoflife.org) | CC0 |
| `cypriniformes_fossils.csv` | The three fossil calibrations inside the Cypriniformes (†*Amyzon aggregatum*, †*Cyprinus maomingensis*, †*Huashancyprinus robustispinus*), with minimum and maximum ages and the age of the node each constrains; from the Fish Tree of Life fossil table | Near et al. (2012), Chen et al. (2015) and Chen and Chang (2011), as compiled in Rabosky et al. (2018); fishtreeoflife.org/downloads/fossil_data.csv | CC0 |

The two-trait adaptive landscape used by every 3D example is not data. It is the analytic function `landscape(z1, z2)` in `examples/python/_common.py`, illustrative by construction.

## Composite figures and maps

The ecology, sustainability and map examples keep their sources next to their data, with full citations, licences and
download dates:

- [`data/ecology/SOURCES.md`](ecology/SOURCES.md): Barro Colorado Island trees, oribatid mites, Canadian lynx, Doubs river fish
- [`data/sustainability/SOURCES.md`](sustainability/SOURCES.md): Our World in Data CO₂ and energy, NOAA Mauna Loa CO₂, NASA GISTEMP
- [`data/maps/SOURCES.md`](maps/SOURCES.md): the Netherlands map layers
