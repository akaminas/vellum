# export_data.R: export the public ecology datasets and the vegan / mgcv analyses that the ecology composites draw.
#
# Run from the repository root:
#   "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" examples/python/ecology/export_data.R
# Writes CSV files into data/ecology/ (see data/ecology/SOURCES.md for the citations and licences).
# Every random step is seeded, so a rerun gives the same files.
suppressMessages({ library(vegan); library(mgcv) })
out <- file.path("data", "ecology"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
w <- function(x, name) write.csv(x, file.path(out, name), row.names = FALSE)
cat("vegan", as.character(packageVersion("vegan")), "· mgcv", as.character(packageVersion("mgcv")), "·", R.version.string, "\n")

# ------------------------------------------------------------------ Barro Colorado Island, 50 one-hectare plots
data(BCI); data(BCI.env)
ew <- sort(unique(BCI.env$UTM.EW)); ns <- sort(unique(BCI.env$UTM.NS))
env <- data.frame(plot = seq_len(nrow(BCI)), col = match(BCI.env$UTM.EW, ew) - 1, row = match(BCI.env$UTM.NS, ns) - 1,
                  utm_ew = BCI.env$UTM.EW, utm_ns = BCI.env$UTM.NS, habitat = BCI.env$Habitat, stream = BCI.env$Stream,
                  age = BCI.env$Age.cat, envhet = BCI.env$EnvHet)
env$stems <- rowSums(BCI); env$richness <- specnumber(BCI); env$fisher_alpha <- fisher.alpha(BCI)
env$shannon <- diversity(BCI, "shannon"); env$simpson <- diversity(BCI, "invsimpson")
w(env, "bci_plots.csv")
w(cbind(plot = seq_len(nrow(BCI)), BCI), "bci_counts.csv")

# rank-abundance models (Wilson 1991) fitted to the pooled 50 ha by maximum likelihood (Poisson error)
tot <- sort(colSums(BCI), decreasing = TRUE)
rf <- radfit(tot)
fit <- sapply(rf$models, fitted)
w(data.frame(rank = seq_along(tot), species = names(tot), abundance = as.numeric(tot), fit), "bci_radfit.csv")
w(data.frame(model = names(rf$models), AIC = sapply(rf$models, AIC), BIC = sapply(rf$models, BIC),
             deviance = sapply(rf$models, deviance),
             params = sapply(rf$models, function(m) paste(sprintf("%s=%.5g", names(coef(m)), coef(m)), collapse = ";"))),
  "bci_radfit_models.csv")

# species accumulation by random ordering of plots, 999 permutations
set.seed(20021)
sa <- specaccum(BCI, method = "random", permutations = 999)
q <- apply(sa$perm, 1, quantile, c(0.025, 0.975))
w(data.frame(plots = sa$sites, richness = sa$richness, sd = sa$sd, lo = q[1, ], hi = q[2, ]), "bci_specaccum.csv")
sp <- specpool(BCI)
w(data.frame(observed = sp$Species, chao = sp$chao, chao_se = sp$chao.se, jack1 = sp$jack1, jack1_se = sp$jack1.se,
             jack2 = sp$jack2, boot = sp$boot, boot_se = sp$boot.se, n = sp$n,
             fisher_alpha_all = fisher.alpha(tot)), "bci_specpool.csv")

# distance decay: Mantel test of Bray-Curtis and Sorensen dissimilarity against distance between plot centres
set.seed(20022)
xy <- cbind(env$utm_ew, env$utm_ns)
m_bc <- mantel(vegdist(BCI, "bray"), dist(xy), permutations = 999)
m_so <- mantel(vegdist(BCI, "bray", binary = TRUE), dist(xy), permutations = 999)
w(data.frame(test = c("mantel_bray", "mantel_sorensen"), r = c(m_bc$statistic, m_so$statistic),
             p = c(m_bc$signif, m_so$signif), permutations = 999), "bci_tests.csv")

# ------------------------------------------------------------------ oribatid mites, 70 cores in Lac Geai bog
data(mite); data(mite.env); data(mite.xy)
w(cbind(core = seq_len(nrow(mite)), mite), "mite_counts.csv")
w(cbind(core = seq_len(nrow(mite)), mite.env, mite.xy), "mite_env.csv")
H <- decostand(mite, "hellinger")

# communities: Ward clustering on the Hellinger distance, four groups, numbered by rising mean water content
hc <- hclust(dist(H), method = "ward.D2"); g <- cutree(hc, k = 4)
ord <- order(tapply(mite.env$WatrCont, g, mean)); g <- match(g, ord)

# NMDS on Bray-Curtis of the raw counts (Wisconsin double standardisation off), environment fitted afterwards
set.seed(20031)
nm <- metaMDS(mite, distance = "bray", k = 2, trymax = 200, autotransform = FALSE, trace = 0)
set.seed(20032)
ef <- envfit(nm, mite.env, permutations = 999)
w(data.frame(core = seq_len(nrow(mite)), nmds1 = nm$points[, 1], nmds2 = nm$points[, 2], cluster = g), "mite_nmds_sites.csv")
sc <- scores(nm, "species")
w(data.frame(species = rownames(sc), nmds1 = sc[, 1], nmds2 = sc[, 2], total = colSums(mite)), "mite_nmds_species.csv")
w(data.frame(variable = rownames(ef$vectors$arrows), nmds1 = ef$vectors$arrows[, 1], nmds2 = ef$vectors$arrows[, 2],
             r2 = ef$vectors$r, p = ef$vectors$pvals), "mite_envfit_vectors.csv")
fl <- ef$factors
w(data.frame(level = rownames(fl$centroids), nmds1 = fl$centroids[, 1], nmds2 = fl$centroids[, 2],
             factor = unlist(lapply(names(fl$r), function(f) rep(f, nlevels(mite.env[[f]]))))), "mite_envfit_centroids.csv")
w(data.frame(factor = names(fl$r), r2 = fl$r, p = fl$pvals), "mite_envfit_factors.csv")
w(data.frame(stress = nm$stress, converged = nm$converged, tries = nm$tries), "mite_nmds_fit.csv")

# variation partitioning (Borcard, Legendre and Drapeau 1992): environment against space.
# Space: PCNM eigenfunctions of the truncated distance matrix (Borcard and Legendre 2002), positive eigenvalues only.
# Each set is forward-selected with the double stopping criterion (Blanchet, Legendre and Borcard 2008).
pc <- pcnm(dist(mite.xy)); S <- as.data.frame(pc$vectors)          # pcnm keeps the positive eigenvalues only
E <- mite.env
sel <- function(X) {
  full <- rda(H ~ ., data = X); r2 <- RsquareAdj(full)$adj.r.squared
  set.seed(20033)
  st <- ordiR2step(rda(H ~ 1, data = X), scope = formula(full), R2scope = r2, permutations = 999, trace = FALSE)
  list(vars = attr(terms(st), "term.labels"), r2_full = r2)
}
se <- sel(E); ss <- sel(S)
Esel <- E[, se$vars, drop = FALSE]; Ssel <- S[, ss$vars, drop = FALSE]
vp <- varpart(H, Esel, Ssel)
fr <- vp$part$indfract; fa <- vp$part$fract
set.seed(20034); pa <- anova(rda(H, Esel, Ssel), permutations = 999)        # [a] environment given space
set.seed(20035); pc_ <- anova(rda(H, Ssel, Esel), permutations = 999)       # [c] space given environment
set.seed(20036); pe_ <- anova(rda(H ~ ., data = Esel), permutations = 999)
set.seed(20037); ps_ <- anova(rda(H ~ ., data = Ssel), permutations = 999)
# the fractions are picked by their labels, which changed between vegan versions: X1|X2 is the environment alone,
# X2|X1 space alone, the untestable zero-df row the shared fraction, and Residuals the rest
lab <- rownames(fr); pick <- function(pat) fr$Adj.R.square[grepl(pat, lab, fixed = TRUE)]
shared <- fr$Adj.R.square[!grepl("|", lab, fixed = TRUE) & !grepl("Residuals", lab)]
w(data.frame(fraction = c("env_only", "shared", "space_only", "residual", "env_total", "space_total", "all"),
             adj_r2 = c(pick("X1|X2"), shared, pick("X2|X1"), pick("Residuals"), fa$Adj.R.square[1:3]),
             p = c(pa$`Pr(>F)`[1], NA, pc_$`Pr(>F)`[1], NA, pe_$`Pr(>F)`[1], ps_$`Pr(>F)`[1], NA)),
  "mite_varpart.csv")
w(data.frame(set = c(rep("environment", length(se$vars)), rep("space", length(ss$vars))), variable = c(se$vars, ss$vars),
             r2_full = c(rep(se$r2_full, length(se$vars)), rep(ss$r2_full, length(ss$vars))),
             n_candidates = c(rep(ncol(E), length(se$vars)), rep(ncol(S), length(ss$vars)))), "mite_selected.csv")
# the PCNM scales: the eigenvalue of each selected eigenfunction, so the figure can name broad against fine scales
w(data.frame(pcnm = colnames(S), eigenvalue = pc$values[seq_len(ncol(S))], threshold = pc$threshold), "mite_pcnm.csv")

# species responses to water content: one negative-binomial GAM per species, log link, s(WatrCont, k = 5), REML
wc <- seq(min(mite.env$WatrCont), max(mite.env$WatrCont), length.out = 120)
pred <- list(); tab <- list()
for (s in colnames(mite)) {
  d <- data.frame(y = mite[[s]], x = mite.env$WatrCont)
  m <- gam(y ~ s(x, k = 5), family = nb(), data = d, method = "REML")
  p <- predict(m, data.frame(x = wc), se.fit = TRUE)
  pred[[s]] <- data.frame(species = s, watrcont = wc, fit = exp(p$fit), lo = exp(p$fit - 1.96 * p$se.fit), hi = exp(p$fit + 1.96 * p$se.fit))
  sm <- summary(m)
  tab[[s]] <- data.frame(species = s, total = sum(d$y), occupancy = sum(d$y > 0), edf = sm$edf, p = sm$s.pv,
                         dev_expl = sm$dev.expl, optimum = wc[which.max(p$fit)])
}
w(do.call(rbind, pred), "mite_gam_curves.csv"); w(do.call(rbind, tab), "mite_gam_species.csv")

# ------------------------------------------------------------------ Canadian lynx trappings, 1821-1934
w(data.frame(year = as.integer(time(lynx)), trapped = as.integer(lynx)), "lynx.csv")

# ------------------------------------------------------------------ Doubs river fish, 30 sites x 27 species (ade4::doubs)
# ade4 is installed into the user library if it is missing.
if (!requireNamespace("ade4", quietly = TRUE)) install.packages("ade4", repos = "https://cloud.r-project.org", lib = .libPaths()[1])
data(doubs, package = "ade4")
fish <- doubs$fish; denv <- doubs$env; dxy <- doubs$xy
w(cbind(site = seq_len(nrow(fish)), fish), "doubs_fish.csv")
w(cbind(site = seq_len(nrow(denv)), denv, dxy), "doubs_env.csv")
w(cbind(code = colnames(fish), doubs$species[, c("Scientific", "English")]), "doubs_species.csv")
# site 8 has no fish: it is left out of the transformations and ordinations (as in Borcard, Gillet and Legendre 2018)
keep <- rowSums(fish) > 0
Hf <- decostand(fish[keep, ], "hellinger"); Ez <- as.data.frame(scale(denv[keep, ])); Xy <- dxy[keep, ]
# tb-RDA of the Hellinger-transformed fish on the standardised environment, forward-selected (double stopping criterion)
full <- rda(Hf ~ ., data = Ez); r2full <- RsquareAdj(full)$adj.r.squared
set.seed(20041)
st <- ordiR2step(rda(Hf ~ 1, data = Ez), scope = formula(full), R2scope = r2full, permutations = 999, trace = FALSE)
evars <- attr(terms(st), "term.labels")
rd <- rda(as.formula(paste("Hf ~", paste(evars, collapse = " + "))), data = Ez)
set.seed(20042); prd <- anova(rd, permutations = 999)
ev <- rd$CCA$eig / rd$tot.chi
ss <- scores(rd, display = "sites", choices = 1:2, scaling = 1)
sp <- scores(rd, display = "species", choices = 1:2, scaling = 1)
bp <- scores(rd, display = "bp", choices = 1:2, scaling = 1)
w(data.frame(site = which(keep), rda1 = ss[, 1], rda2 = ss[, 2]), "doubs_rda_sites.csv")
w(data.frame(code = rownames(sp), rda1 = sp[, 1], rda2 = sp[, 2]), "doubs_rda_species.csv")
w(data.frame(variable = rownames(bp), rda1 = bp[, 1], rda2 = bp[, 2]), "doubs_rda_arrows.csv")
w(data.frame(adj_r2 = RsquareAdj(rd)$adj.r.squared, r2 = RsquareAdj(rd)$r.squared, adj_r2_full = r2full, p = prd$`Pr(>F)`[1],
             axis1 = ev[1], axis2 = ev[2], selected = paste(evars, collapse = ";")), "doubs_rda_fit.csv")
# environment (selected) against space: PCNM of the site coordinates, forward-selected the same way
pcd <- pcnm(dist(Xy)); Sd <- as.data.frame(pcd$vectors)
fulls <- rda(Hf ~ ., data = Sd); r2s <- RsquareAdj(fulls)$adj.r.squared
set.seed(20043)
sts <- ordiR2step(rda(Hf ~ 1, data = Sd), scope = formula(fulls), R2scope = r2s, permutations = 999, trace = FALSE)
svars <- attr(terms(sts), "term.labels")
vpd <- varpart(Hf, Ez[, evars, drop = FALSE], Sd[, svars, drop = FALSE])
frd <- vpd$part$indfract; lab <- rownames(frd); pick <- function(pat) frd$Adj.R.square[grepl(pat, lab, fixed = TRUE)]
shd <- frd$Adj.R.square[!grepl("|", lab, fixed = TRUE) & !grepl("Residuals", lab)]
set.seed(20044); pae <- anova(rda(Hf, Ez[, evars, drop = FALSE], Sd[, svars, drop = FALSE]), permutations = 999)
set.seed(20045); pas <- anova(rda(Hf, Sd[, svars, drop = FALSE], Ez[, evars, drop = FALSE]), permutations = 999)
w(data.frame(fraction = c("env_only", "shared", "space_only", "residual", "env_total", "space_total", "all"),
             adj_r2 = c(pick("X1|X2"), shd, pick("X2|X1"), pick("Residuals"), vpd$part$fract$Adj.R.square[1:3]),
             p = c(pae$`Pr(>F)`[1], NA, pas$`Pr(>F)`[1], NA, NA, NA, NA),
             env_vars = paste(evars, collapse = ";"), space_vars = paste(svars, collapse = ";")), "doubs_varpart.csv")
cat("wrote", length(list.files(out, pattern = "csv$")), "csv files to", out, "\n")
