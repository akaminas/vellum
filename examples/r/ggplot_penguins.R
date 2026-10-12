# ggplot_penguins.R: beak depth against beak length of the Palmer penguins in ggplot2 with theme_vellum(): ringed points
# in the tones, a least-squares fit per species with its 95 % band, the pooled fit in rule grey, direct labels, no legend.
# Data: data/penguins.json (Gorman, Williams and Fraser 2014). Writes docs/figures/tools/ggplot_penguins_{light,dark}.png,
# the light PDF, and the manifest entry.   Run: Rscript examples/r/ggplot_penguins.R
source(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1]))), "_common.R"))

d <- jsonlite::fromJSON(file.path(REPO, "data", "penguins.json"))
d <- data.frame(species = d$Species, len = d$`Beak Length (mm)`, dep = d$`Beak Depth (mm)`)
d <- d[complete.cases(d), ]
d$species <- factor(d$species, levels = c("Adelie", "Chinstrap", "Gentoo"))   # slot order: teal, terracotta, indigo
names <- c(Adelie = "Adélie", Chinstrap = "Chinstrap", Gentoo = "Gentoo")

# The claim rests on the signs of the slopes, so they are computed and checked here, and printed on the labels
fits <- lapply(split(d, d$species), function(s) lm(dep ~ len, s))
pooled <- lm(dep ~ len, d)
slope <- sapply(fits, function(m) coef(m)[["len"]])
stopifnot(all(slope > 0), coef(pooled)[["len"]] < 0)
signed <- function(b) sprintf("%s%.2f", if (b < 0) "−" else "+", abs(b))

# Labels at the free end of each fit line: Adelie at its left end (its right end lies inside the Chinstrap cloud),
# the others and the pooled line at their right ends
ends <- do.call(rbind, lapply(levels(d$species), function(s) {
  x <- if (s == "Adelie") min(d$len[d$species == s]) else max(d$len[d$species == s])
  left <- s == "Adelie"
  data.frame(x = x + if (left) -0.6 else 0.6, y = predict(fits[[s]], data.frame(len = x)), hjust = if (left) 1 else 0,
             label = paste(names[[s]], signed(slope[[s]])))
}))
px <- max(d$len)
pend <- data.frame(x = px + 0.6, y = predict(pooled, data.frame(len = px)), label = paste("all three pooled", signed(coef(pooled)[["len"]])))

TITLE <- "Within each species longer beaks are deeper; pooled, the trend reverses"
SUBTITLE <- sprintf("%d penguins, Palmer Archipelago, 2007–2009 · least-squares fits with 95 %% bands, labelled with their slope in mm per mm",
                    nrow(d))

draw <- function(V) {
  ggplot(d, aes(len, dep, colour = species, fill = species)) +
    geom_smooth(data = d, aes(len, dep), inherit.aes = FALSE, method = "lm", formula = y ~ x, se = FALSE,
                colour = V$rule, linewidth = V$thin) +                                   # pooled: rule grey, not the point
    geom_smooth(method = "lm", formula = y ~ x, colour = NA, alpha = V$band_alpha) +   # 95 % bands in the tints
    geom_point_vellum(size = 1.5, V = V) +
    geom_smooth(aes(group = species), method = "lm", formula = y ~ x, se = FALSE, colour = V$surface,
                linewidth = V$lw * 2.4) +                                                # a surface halo lifts the fit off the points
    geom_smooth(method = "lm", formula = y ~ x, se = FALSE, linewidth = V$lw) +
    geom_text(data = ends, aes(x, y, label = label, hjust = hjust), inherit.aes = FALSE,
              colour = V$ink, family = V$body_font, size = 2.6) +
    geom_text(data = pend, aes(x, y, label = label), inherit.aes = FALSE, hjust = 0,
              colour = V$muted, family = V$body_font, size = 2.6) +
    scale_colour_vellum(V = V) + scale_fill_vellum(V = V) +
    scale_x_continuous(breaks = c(35, 45, 55), expand = expansion(mult = c(0.17, 0.3))) +
    scale_y_continuous(breaks = c(14, 16, 18, 20), expand = expansion(mult = c(0.04, 0.04))) +
    labs(title = TITLE,
         subtitle = SUBTITLE,
         tag = "beak depth, mm", x = "beak length, mm", y = NULL,
         caption = footer("Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0")) +
    theme_vellum(V = V) +
    theme(plot.tag.location = "panel", plot.tag.position = c(0, 1),                        # the unit line above the y axis
          plot.tag = element_text(colour = V$muted, size = 7.5, hjust = 0, vjust = -0.5, family = V$body_font),
          plot.subtitle = element_text(margin = margin(b = 20)))
}

for (V in list(vellum, vellum_dark)) save_twin(function() print(draw(V)), "tools", "ggplot_penguins", V)
record("tools", "ggplot_penguins", list(
  title = TITLE,
  subtitle = SUBTITLE,
  kind = "tools", form = "scatter plot", medium = "paper", tool = "ggplot2",
  data = "Palmer penguins, Gorman, Williams and Fraser (2014), PLoS ONE 9(3): e90081; Palmer Station LTER; via vega-datasets 2.8.0",
  script = rel(),
  alt = sprintf("A scatter plot of beak depth against beak length for %d penguins: within Adélie, Chinstrap and Gentoo the fitted slopes are %s, %s and %s mm per mm, while one line through all three species slopes at %s.",
                nrow(d), signed(slope[[1]]), signed(slope[[2]]), signed(slope[[3]]), signed(coef(pooled)[["len"]])),
  note = "Simpson's paradox: the pooled trend reverses the trend inside every species."))
cat("written ggplot_penguins\n")
