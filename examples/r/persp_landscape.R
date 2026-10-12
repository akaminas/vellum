# persp_landscape.R: the shared two-trait landscape (examples/python/_common.py) as a Vellum surface in base R persp(),
# with its 2D twin drawn by image() and contour(): the same gradient (lagoon), the same limits and the same seven levels.
# No data: the landscape is an analytic function, illustrative. Writes docs/figures/tools/persp_landscape_{light,dark}.png,
# the light PDF, and the manifest entry.   Run: Rscript examples/r/persp_landscape.R
source(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1]))), "_common.R"))

landscape <- function(z1, z2) exp(-((z1 - 0.9)^2 + (z2 - 0.7)^2) / 0.6) + 0.72 * exp(-((z1 + 0.8)^2 + (z2 + 0.9)^2) / 0.9)
z1 <- seq(-2, 2, length.out = 90); z2 <- z1                       # 90 by 90, so a facet is about 1 per cent of the width
W <- outer(z1, z2, landscape)
zlim <- c(min(W) - 0.06 * diff(range(W)), max(W))                  # the floor sits 6 per cent below the lowest value
levels <- seq(0, round(max(W), 1), length.out = 9)[2:8]            # seven contour levels
ticks <- c(-1, 0, 1)                                               # three ticks, clear of the shared corner

# The numbers of the claim: the two peaks, and the saddle where the gradient vanishes between them
f <- function(p) landscape(p[1], p[2])
peaks <- lapply(list(c(0.9, 0.7), c(-0.8, -0.9)), function(p0) optim(p0, function(p) -f(p))$par)
grad2 <- function(p, h = 1e-5) sum(c(f(p + c(h, 0)) - f(p - c(h, 0)), f(p + c(0, h)) - f(p - c(0, h)))^2) / (2 * h)^2
saddle <- optim((peaks[[1]] + peaks[[2]]) / 2, grad2, control = list(reltol = 1e-14))$par
num <- function(x) sprintf("%.2f", x)
TITLE <- sprintf("A saddle at w = %s separates the peak of %s from a lower peak of %s", num(f(saddle)), num(f(peaks[[1]])), num(f(peaks[[2]])))
TITLE_MATH <- bquote("A saddle at" ~ italic(w) == .(num(f(saddle))) ~ "separates the peak of" ~ .(num(f(peaks[[1]]))) ~
                       "from a lower peak of" ~ .(num(f(peaks[[2]]))))     # the same claim, with w as an italic variable
SUBTITLE <- "illustrative two-trait landscape in base R persp() · on the right the same values from above, to read them"
minus <- function(x) sub("-", "−", format(x), fixed = TRUE)    # U+2212, not a hyphen

draw <- function(V) {
  pt <- function(p) p / par("ps")                                  # cex for a size in points
  lw <- function(p) p * 96 / 72                                    # lwd for a width in points
  pal <- colorRampPalette(V$gradients$lagoon)(256)                 # the dark twin takes the dark stops: brighter is more
  breaks <- seq(0, max(W), length.out = 257)                       # one set of limits for both panels
  inch <- function(x0, x1, y0, y1) c(x0, x1, y0, y1) / c(7.2, 7.2, 3.6, 3.6)
  par(mar = c(0, 0, 0, 0), family = V$body_font, bg = V$surface, ps = 12)

  # a: the surface, as 1339.14 sets it up (theta -58, phi 24, r 1e3 for a near-orthographic view, flat colour by the mean
  # height of a facet's corners, no border, no shading). The panes, the floor contours and the axes are drawn by hand so the
  # text stays horizontal: a first, invisible persp() gives the projection, the panes go behind, the surface over them.
  Wc <- (W[-1, -1] + W[-1, -ncol(W)] + W[-nrow(W), -1] + W[-nrow(W), -ncol(W)]) / 4
  col <- pal[cut(Wc, breaks, include.lowest = TRUE, labels = FALSE)]
  view <- function(...) persp(z1, z2, W, theta = -58, phi = 24, r = 1e3, d = 1, expand = 0.6, zlim = zlim, box = FALSE,
                              axes = FALSE, ...)
  seg <- function(x, y, z, ...) lines(trans3d(x, y, z, pm), ...)
  layer <- function() {                                            # everything behind the text: panes, floor contours, surface
    pm <<- view(col = NA, border = NA)
    pane <- list(col = V$grid, lwd = lw(0.5))
    for (t in ticks) {                                             # hairline grid on the floor and the two back walls
      do.call(seg, c(list(c(t, t), c(-2, 2), zlim[1]), pane)); do.call(seg, c(list(c(-2, 2), c(t, t), zlim[1]), pane))
      do.call(seg, c(list(2, c(t, t), zlim), pane)); do.call(seg, c(list(c(t, t), 2, zlim), pane))
    }
    for (t in c(0, 0.5, 1)) { do.call(seg, c(list(2, c(-2, 2), t), pane)); do.call(seg, c(list(c(-2, 2), 2, t), pane)) }
    for (e in list(list(2, c(-2, 2), zlim[2]), list(c(-2, 2), 2, zlim[2]), list(2, 2, zlim), list(2, -2, zlim),
                   list(c(-2, 2), 2, zlim[1]), list(2, c(-2, 2), zlim[1]))) do.call(seg, c(e, pane))   # pane edges
    for (cl in contourLines(z1, z2, W, levels = levels)) seg(cl$x, cl$y, zlim[1], col = V$rule, lwd = lw(0.5))
    par(new = TRUE); view(col = col, border = NA, shade = NA)
  }
  A <- c(0.05, 4.25, 0.18, 3.02)                                   # panel a, in inches
  par(fig = do.call(inch, as.list(A)))
  if (grepl("pdf", names(dev.cur()))) {
    # in the PDF the layer is a 300 dpi raster under vector text (1339.10): 8000 vector facets show seams in PDF viewers
    f <- tempfile(fileext = ".png"); pdf_dev <- dev.cur()
    grDevices::png(f, width = A[2] - A[1], height = A[4] - A[3], units = "in", res = 300, bg = V$surface)
    par(mar = c(0, 0, 0, 0)); layer(); invisible(dev.off()); dev.set(pdf_dev)
    pm <- view(col = NA, border = NA)
    u <- par("usr"); rasterImage(png::readPNG(f), u[1], u[3], u[2], u[4], interpolate = FALSE)
  } else layer()
  axis3 <- list(col = V$rule, lwd = lw(0.8))                       # the three outer axis lines
  do.call(seg, c(list(c(-2, 2), -2, zlim[1]), axis3)); do.call(seg, c(list(-2, c(-2, 2), zlim[1]), axis3))
  do.call(seg, c(list(-2, 2, zlim), axis3))
  lab <- function(x, y, z, s, adj, cex = pt(8), dx = 0, dy = 0) {
    p <- trans3d(x, y, z, pm); text(p$x + dx * strwidth("m"), p$y + dy * strheight("M"), s, adj = adj, col = V$muted, cex = cex, xpd = NA)
  }
  for (t in ticks) { lab(t, -2.3, zlim[1], minus(t), c(0, 1)); lab(-2.3, t, zlim[1], minus(t), c(1, 1)) }
  for (t in c(0, 0.5, 1)) lab(-2, 2, t, format(t), c(1, 0.5), dx = -0.6)
  lab(0.4, -3.0, zlim[1], quote("trait" ~ italic(z)[1]), c(0, 1), cex = pt(9))
  lab(-3.0, 0.4, zlim[1], quote("trait" ~ italic(z)[2]), c(1, 1), cex = pt(9))
  lab(-2, 2, zlim[2], quote("fitness" ~ italic(w)), c(0.5, 0), cex = pt(9), dy = 1)

  # b: the twin, where values are read. image() with the same gradient and limits, seven contours in the surface colour.
  par(fig = inch(4.75, 6.5, 0.62, 2.37), new = TRUE)
  plot.new(); plot.window(c(-2, 2), c(-2, 2), xaxs = "i", yaxs = "i")
  image(z1, z2, W, col = pal, breaks = breaks, add = TRUE, useRaster = TRUE)
  contour(z1, z2, W, levels = levels, add = TRUE, drawlabels = FALSE, col = V$surface, lwd = lw(0.5))
  text(ticks, -2, minus(ticks), pos = 1, col = V$muted, cex = pt(8), xpd = NA)
  text(-2, ticks, minus(ticks), pos = 2, col = V$muted, cex = pt(8), xpd = NA)
  text(0, -2 - 3.2 * strheight("M", cex = pt(8)), quote("trait" ~ italic(z)[1]), adj = c(0.5, 1), col = V$muted, cex = pt(9), xpd = NA)
  text(-2, 2 + 0.6 * strheight("M"), quote("trait" ~ italic(z)[2]), adj = c(0, 0), col = V$muted, cex = pt(7.5), xpd = NA)  # unit line
  for (p in list(list(peaks[[1]], paste("peak", num(f(peaks[[1]]))), 3), list(peaks[[2]], paste("peak", num(f(peaks[[2]]))), 1),
                 list(saddle, paste("saddle", num(f(saddle))), 4))) {
    xy <- p[[1]]; s <- p[[2]]; cex <- pt(7.5)                     # a ringed dot, and its value on a card off the gradient
    points(xy[1], xy[2], pch = 21, bg = V$ink, col = V$surface, lwd = lw(1.2), cex = 0.85)
    w <- strwidth(s, cex = cex); h <- strheight(s, cex = cex); g <- 0.08
    cx <- xy[1] + c(0, 0, 0, w / 2 + 0.16)[p[[3]]]; cy <- xy[2] + c(-h - 0.2, 0, h + 0.2, 0)[p[[3]]]
    rect(cx - w / 2 - g, cy - h / 2 - g, cx + w / 2 + g, cy + h / 2 + g, col = V$card, border = NA)
    text(cx, cy, s, col = V$ink, cex = cex)
  }
  par(fig = inch(6.62, 6.7, 0.62, 2.37), new = TRUE)              # the legend bar: no outline, three ticks, the quantity above
  plot.new(); plot.window(c(0, 1), range(breaks), xaxs = "i", yaxs = "i")
  rasterImage(as.raster(matrix(rev(pal), ncol = 1)), 0, 0, 1, max(breaks))
  text(1, c(0, 0.5, 1), c("0", "0.5", "1"), pos = 4, col = V$muted, cex = pt(8), xpd = NA)
  text(0, max(breaks) + 1.6 * strheight("M", cex = pt(8)), quote("fitness" ~ italic(w)), adj = c(0, 0),
       col = V$muted, cex = pt(7.5), xpd = NA)

  # the title block and the footer, in inches on the whole figure
  par(fig = c(0, 1, 0, 1), new = TRUE); plot.new(); plot.window(c(0, 7.2), c(0, 3.6), xaxs = "i", yaxs = "i")
  text(0.17, 3.6 - 0.15, TITLE_MATH, adj = c(0, 1), family = V$title_font, col = V$ink, cex = pt(13))
  text(0.17, 3.6 - 0.15 - 13 * 1.45 / 72, SUBTITLE, adj = c(0, 1), col = V$muted, cex = pt(9))
  text(0.17, 0.1, footer("analytic landscape from examples/python/_common.py, illustrative"), adj = c(0, 0), col = V$muted, cex = pt(6.5))
}

for (V in list(vellum, vellum_dark)) save_twin(function() draw(V), "tools", "persp_landscape", V)
record("tools", "persp_landscape", list(
  title = TITLE, subtitle = SUBTITLE, kind = "tools", form = "3D surface with twin", medium = "paper", tool = "base R persp",
  data = "analytic two-trait landscape w(z1, z2) from examples/python/_common.py (illustrative)", script = rel(),
  alt = sprintf("A lagoon-coloured surface drawn with R persp(): a peak of %s at z1 = %s, z2 = %s, a lower peak of %s at z1 = %s, z2 = %s and a saddle of %s between them; beside it the same values from above as an image with seven contour lines and a colour bar.",
                num(f(peaks[[1]])), num(peaks[[1]][1]), num(peaks[[1]][2]), num(f(peaks[[2]])), num(peaks[[2]][1]),
                num(peaks[[2]][2]), num(f(saddle))),
  note = "illustrative: an analytic function, not data. The same surface is drawn in matplotlib and pgfplots."))
cat("written persp_landscape\n")
