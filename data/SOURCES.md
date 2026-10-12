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

The two-trait adaptive landscape used by every 3D example is not data. It is the analytic function `landscape(z1, z2)` in `examples/python/_common.py`, illustrative by construction.
