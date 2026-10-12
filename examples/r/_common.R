# _common.R: what every R example shares, the counterpart of examples/python/_common.py.
# The repository paths, style/vellum.R and the fonts, the git stamp for the footer, `save_twin`, which writes a figure
# into docs/figures/<group>/, and `record`, which merges its entry into that group's manifest.json with the same keys
# as _common.record in Python. Every example draws each figure twice, once per twin, from one function of V:
#
#   source(file.path(dirname(this_script()), "_common.R"))
#   draw <- function(V) ggplot(...) + theme_vellum(V = V)
#   for (V in list(vellum, vellum_dark)) save_twin(function() print(draw(V)), "tools", "name", V)

this_script <- function() normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1]))
REPO <- normalizePath(file.path(dirname(this_script()), "..", ".."), winslash = "/")
FIGURES <- file.path(REPO, "docs", "figures")
source(file.path(REPO, "style", "vellum.R"))
suppressPackageStartupMessages(library(ggplot2))
vellum_fonts()                           # registers Palatino Linotype and Corbel for the base png device on Windows

# Short sha of the last commit that touched the inputs, with -dirty when they have uncommitted changes (as in Python)
stamp <- function() {
  git <- function(...) tryCatch(suppressWarnings(system2("git", c("-C", shQuote(REPO), ...), stdout = TRUE, stderr = FALSE)),
                                error = function(e) character(0))
  sha <- git("log", "-1", "--format=%h", "--", "style", "examples", "data")
  dirty <- length(git("status", "--porcelain", "--", "style", "examples", "data")) > 0
  paste0(if (length(sha) && nzchar(sha[1])) sha[1] else "unstamped", if (dirty) "-dirty" else "")
}

footer <- function(source) paste(source, basename(this_script()), paste("git", stamp()), sep = " · ")
rel <- function() sub(paste0(REPO, "/"), "", normalizePath(this_script(), winslash = "/"), fixed = TRUE)

# Write <name>_<mode>.png at 300 dpi (and the .pdf of the light twin with cairo_pdf, fonts embedded) at the printed size.
# plot is a function that draws the figure on the open device.
save_twin <- function(plot, group, name, V, width = 7.2, height = 3.6) {
  out <- file.path(FIGURES, group); dir.create(out, showWarnings = FALSE, recursive = TRUE)
  grDevices::png(file.path(out, sprintf("%s_%s.png", name, V$mode)), width = width, height = height, units = "in",
                 res = 300, bg = V$surface, antialias = "gray")
  plot(); invisible(grDevices::dev.off())
  if (V$mode == "light") {
    grDevices::cairo_pdf(file.path(out, sprintf("%s_light.pdf", name)), width = width, height = height, bg = V$surface,
                         family = V$body_font)
    plot(); invisible(grDevices::dev.off())
  }
}

# Merge one figure's metadata into docs/figures/<group>/manifest.json, keyed by id, order kept (as _common.record)
record <- function(group, name, meta) {
  path <- file.path(FIGURES, group, "manifest.json")
  items <- if (file.exists(path)) jsonlite::fromJSON(path, simplifyVector = FALSE) else list()
  entry <- c(list(id = name, group = group), meta)
  if (is.null(entry$files)) entry$files <- list(light = sprintf("figures/%s/%s_light.png", group, name),
                                                dark = sprintf("figures/%s/%s_dark.png", group, name),
                                                pdf = sprintf("figures/%s/%s_light.pdf", group, name))
  items <- c(Filter(function(e) e$id != name, items), list(entry))
  con <- file(path, "wb"); on.exit(close(con))                # UTF-8 bytes, LF line ends, as Python writes it
  writeLines(jsonlite::toJSON(items, auto_unbox = TRUE, pretty = TRUE), con, useBytes = TRUE)
}
