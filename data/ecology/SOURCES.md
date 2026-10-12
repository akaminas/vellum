# Ecology data: sources and licences

All files in this folder are written by `examples/python/ecology/export_data.R` (R 4.6.1, vegan 2.7.5, mgcv 1.9.4, ade4 1.7.24)
from datasets that ship with R packages. Rerun it from the repository root to regenerate them; every random step is seeded.

    "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" examples/python/ecology/export_data.R

## Barro Colorado Island trees: `bci_*.csv`

Tree counts (stems ≥ 10 cm dbh) of 225 species in 50 one-hectare plots of the 50-ha forest dynamics plot on Barro Colorado
Island, Panama, 1982 census; plot environment (`BCI.env`).

- Condit, R., Pitman, N., Leigh, E. G., Chave, J., Terborgh, J., Foster, R. B., Núñez, P., Aguilar, S., Valencia, R., Villa, G.,
  Muller-Landau, H. C., Losos, E. and Hubbell, S. P. (2002). Beta-diversity in tropical forest trees. *Science* 295, 666–669.
- Distributed as `BCI` and `BCI.env` in the R package vegan (Oksanen et al., https://CRAN.R-project.org/package=vegan), GPL-2.
  The census belongs to the Smithsonian Tropical Research Institute / ForestGEO; cite Condit et al. (2002) when reusing it.
- Derived files: `bci_radfit*.csv` (vegan `radfit`; Wilson, J. B. 1991, *Journal of Vegetation Science* 2, 35–46),
  `bci_specaccum.csv` (`specaccum`, random, 999 permutations), `bci_specpool.csv` (`specpool`: Chao1, jackknife, bootstrap),
  `bci_tests.csv` (Mantel tests, 999 permutations), `bci_plots.csv` (grid position, richness, Fisher's α, diversity).

## Oribatid mites of Lac Geai bog: `mite_*.csv`

70 cores of Sphagnum peat (10 × 2.6 m plot) × 35 mite species, with substrate density, water content, substrate, shrub cover,
topography and core coordinates.

- Borcard, D. and Legendre, P. (1994). Environmental control and spatial structure in ecological communities: an example using
  oribatid mites (Acari, Oribatei). *Environmental and Ecological Statistics* 1, 37–61.
- Borcard, D., Legendre, P. and Drapeau, P. (1992). Partialling out the spatial component of ecological variation. *Ecology* 73,
  1045–1055.
- Distributed as `mite`, `mite.env` and `mite.xy` in vegan, GPL-2.
- Methods behind the derived files: PCNM, Borcard, D. and Legendre, P. (2002), *Ecological Modelling* 153, 51–68; forward selection
  with the double stopping criterion, Blanchet, F. G., Legendre, P. and Borcard, D. (2008), *Ecology* 89, 2623–2632; GAMs by REML,
  Wood, S. N. (2011), *Journal of the Royal Statistical Society B* 73, 3–36.

## Canadian lynx: `lynx.csv`

Annual numbers of lynx trapped in the Mackenzie River district of north-west Canada (Hudson's Bay Company records), 1821–1934.

- Elton, C. and Nicholson, M. (1942). The ten-year cycle in numbers of the lynx in Canada. *Journal of Animal Ecology* 11, 215–244.
- Campbell, M. J. and Walker, A. M. (1977). A survey of statistical work on the Mackenzie River series of annual Canadian lynx
  trappings for the years 1821–1934 and a new analysis. *Journal of the Royal Statistical Society A* 140, 411–431.
- Distributed as `datasets::lynx` in base R (R Core Team), GPL-2 or later.
- The AR(2) model of the figure follows Moran, P. A. P. (1953). The statistical analysis of the Canadian lynx cycle. *Australian
  Journal of Zoology* 1, 163–173.

## Doubs river fish: `doubs_*.csv`

30 sites along the Doubs (France and Switzerland) × 27 fish species (abundance classes 0–5), 11 environmental variables
(distance from the source in tenths of a km, altitude, slope, flow, pH, hardness, phosphate, nitrate, ammonium, oxygen, BOD) and
site coordinates (km).

- Verneaux, J. (1973). *Cours d'eau de Franche-Comté (Massif du Jura). Recherches écologiques sur le réseau hydrographique du
  Doubs. Essai de biotypologie.* Thèse d'État, Université de Besançon.
- Distributed as `doubs` in the R package ade4 (Dray, S. and Dufour, A.-B. 2007, *Journal of Statistical Software* 22(4), 1–20;
  https://CRAN.R-project.org/package=ade4), GPL-2 or later.
- Analyses follow Borcard, D., Gillet, F. and Legendre, P. (2018). *Numerical Ecology with R*, 2nd edn. Springer. Beta-diversity
  partition (computed in `doubs_fish.py`): Baselga, A. (2010). Partitioning the turnover and nestedness components of beta
  diversity. *Global Ecology and Biogeography* 19, 134–143.
