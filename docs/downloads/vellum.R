# vellum.R: the Vellum figure style for ggplot2. Generated from vellum.json; do not edit the hex values here.
# Usage:
#   source("vellum.R")
#   ggplot(d, aes(x, y, colour = series)) + geom_line(linewidth = vellum$lw) + scale_colour_vellum() + theme_vellum() +
#     labs(title = "The claim, in one sentence", subtitle = "unit line or settings", caption = "source and git stamp", y = NULL)
# Needs ggplot2 and scales. Fonts: Palatino Linotype and Corbel on Windows; use ragg::agg_png or ggsave(device = ragg::agg_png) so the
# system fonts are found; for PDF use cairo_pdf.

vellum <- list(
  mode = "light",
  surface = "#FFFFFF", card = "#FAF6EE", grid = "#E6E0D4", rule = "#C7C3BD",
  muted = "#8A857C", secondary = "#5A5650", ink = "#2A2825",
  names = c("teal", "terracotta", "indigo", "ochre", "mauve", "moss"),
  tone = c("#419BA0", "#A1644F", "#415688", "#806629", "#AD78A1", "#567E4D"),
  tint = c("#A5D5D7", "#E8C0B2", "#BBCBEC", "#DAC9A6", "#E0BFD8", "#BAD3B4"),
  deep = c("#004C50", "#613425", "#304168", "#533F0D", "#593351", "#2D4B27"),
  diverging = c("#784634", "#995D48", "#B97A65", "#D29C8A", "#E8C0B2", "#E1DDD8", "#A5D5D7", "#73B9BC", "#429CA0", "#1B7D82", "#066166"),
  status = c(good = "#007835", warning = "#DAB327", serious = "#CA6719", critical = "#B02A2D"),
  title_font = "Palatino Linotype", body_font = "Corbel",
  lw = 0.64, thin = 0.28, band_alpha = 0.55
)
vellum$sequential <- list(
  teal = c("#D2EEF0", "#A5D5D7", "#73B9BC", "#429CA0", "#1B7D82", "#066166", "#034649"),
  terracotta = c("#FBE2D9", "#E8C0B2", "#D29C8A", "#B97A65", "#995D48", "#784634", "#583224"),
  indigo = c("#DEE8FD", "#BBCBEC", "#95ABD8", "#738BC0", "#566DA0", "#41547F", "#2E3C5D"),
  ochre = c("#F1E7D2", "#DAC9A6", "#BFA878", "#A4884D", "#856B2F", "#68521E", "#4C3A13"),
  mauve = c("#F5E1F0", "#E0BFD8", "#C79BBD", "#AD78A1", "#8D5B82", "#6F4566", "#50314A"),
  moss = c("#DEEDDA", "#BAD3B4", "#94B68C", "#709967", "#537B4B", "#3E5F37", "#2C4526")
)

vellum_dark <- list(
  mode = "dark",
  surface = "#2A2520", card = "#342F2A", grid = "#413C36", rule = "#5A544D",
  muted = "#A29E96", secondary = "#C9C4BB", ink = "#ECE7DF",
  names = c("teal", "terracotta", "indigo", "ochre", "mauve", "moss"),
  tone = c("#8AE2E7", "#E8A68F", "#8099CF", "#E1C487", "#B984AD", "#93BD89"),
  tint = c("#3F6C6E", "#7D5A4E", "#556380", "#706142", "#76596F", "#546B4F"),
  deep = c("#BFEFF2", "#FFDCD0", "#D8E5FF", "#F4E3BF", "#FBD9F2", "#D4EDCE"),
  diverging = c("#E8C0B2", "#D29C8A", "#B97A65", "#995D48", "#784634", "#585550", "#066166", "#1B7D82", "#429CA0", "#73B9BC", "#A5D5D7"),
  status = c(good = "#5FC27A", warning = "#DAB327", serious = "#F08A3C", critical = "#F06B6B"),
  title_font = "Palatino Linotype", body_font = "Corbel",
  lw = 0.64, thin = 0.28, band_alpha = 0.55
)
vellum_dark$sequential <- list(
  teal = c("#034649", "#066166", "#1B7D82", "#429CA0", "#73B9BC", "#A5D5D7", "#D2EEF0"),
  terracotta = c("#583224", "#784634", "#995D48", "#B97A65", "#D29C8A", "#E8C0B2", "#FBE2D9"),
  indigo = c("#2E3C5D", "#41547F", "#566DA0", "#738BC0", "#95ABD8", "#BBCBEC", "#DEE8FD"),
  ochre = c("#4C3A13", "#68521E", "#856B2F", "#A4884D", "#BFA878", "#DAC9A6", "#F1E7D2"),
  mauve = c("#50314A", "#6F4566", "#8D5B82", "#AD78A1", "#C79BBD", "#E0BFD8", "#F5E1F0"),
  moss = c("#2C4526", "#3E5F37", "#537B4B", "#709967", "#94B68C", "#BAD3B4", "#DEEDDA")
)

# ggplot linewidth is in mm; the style's 1.6 pt line is 0.56 mm.

# Fonts. With ragg installed, ggsave(device = ragg::agg_png) finds the system fonts by name. Without it, on Windows, the base
# png() device needs the families registered once per session; vellum_fonts() does that and is safe to call anywhere.
vellum_fonts <- function(V = vellum) {
  if (.Platform$OS.type == "windows" && !requireNamespace("ragg", quietly = TRUE)) {
    grDevices::windowsFonts(); args <- list()
    args[[V$title_font]] <- grDevices::windowsFont(V$title_font)
    args[[V$body_font]] <- grDevices::windowsFont(V$body_font)
    do.call(grDevices::windowsFonts, args)
  }
  invisible(NULL)
}

theme_vellum <- function(base_size = 9, V = vellum) {
  ggplot2::theme_minimal(base_size = base_size, base_family = V$body_font) +
    ggplot2::theme(
      plot.background = ggplot2::element_rect(fill = V$surface, colour = NA),
      panel.background = ggplot2::element_rect(fill = V$surface, colour = NA),
      panel.grid.major.x = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.y = ggplot2::element_line(colour = V$grid, linewidth = 0.25),
      axis.line.x = ggplot2::element_line(colour = V$grid, linewidth = 0.3),
      axis.ticks = ggplot2::element_blank(),
      axis.text = ggplot2::element_text(colour = V$muted, size = base_size - 1),
      axis.title = ggplot2::element_text(colour = V$muted, size = base_size),
      axis.title.y = ggplot2::element_blank(),   # the unit goes in the subtitle or a unit line
      plot.title = ggplot2::element_text(family = V$title_font, colour = V$ink, size = base_size + 4, hjust = 0),
      plot.subtitle = ggplot2::element_text(colour = V$muted, size = base_size, margin = ggplot2::margin(b = 10)),
      plot.caption = ggplot2::element_text(colour = V$muted, size = base_size - 2.5, hjust = 0),
      plot.title.position = "plot", plot.caption.position = "plot",
      strip.text = ggplot2::element_text(colour = V$ink, face = "bold", hjust = 0, size = base_size),
      legend.position = "none",   # direct labels instead; set legend.position in labs() when there are more than four series
      legend.title = ggplot2::element_blank(),
      legend.text = ggplot2::element_text(colour = V$ink),
      plot.margin = ggplot2::margin(12, 16, 10, 12)
    )
}

scale_colour_vellum <- function(V = vellum, ...) ggplot2::scale_colour_manual(values = V$tone, ...)
scale_fill_vellum   <- function(V = vellum, ...) ggplot2::scale_fill_manual(values = V$tint, ...)
scale_fill_vellum_tone <- function(V = vellum, ...) ggplot2::scale_fill_manual(values = V$tone, ...)
scale_colour_vellum_seq <- function(family = "teal", V = vellum, ...) ggplot2::scale_colour_gradientn(colours = c(V$surface, V$sequential[[family]]), ...)
scale_fill_vellum_seq   <- function(family = "teal", V = vellum, ...) ggplot2::scale_fill_gradientn(colours = c(V$surface, V$sequential[[family]]), ...)
scale_fill_vellum_div   <- function(V = vellum, ...) ggplot2::scale_fill_gradientn(colours = V$diverging, ...)
scale_colour_vellum_div <- function(V = vellum, ...) ggplot2::scale_colour_gradientn(colours = V$diverging, ...)

# A ringed point: draw the surface ring under the point.
geom_point_vellum <- function(mapping = NULL, data = NULL, size = 2, V = vellum, ...) {
  list(ggplot2::geom_point(mapping, data, size = size + 0.8, colour = V$surface, ...),
       ggplot2::geom_point(mapping, data, size = size, ...))
}

# Direct labels at the line ends (needs the last point per series; ggrepel is optional).
label_ends_vellum <- function(d, x, y, label, V = vellum, nudge = 0.01) {
  ggplot2::geom_text(data = d, ggplot2::aes(x = {{ x }}, y = {{ y }}, label = {{ label }}), hjust = 0, nudge_x = nudge,
                     colour = V$ink, family = V$body_font, size = 2.6)
}

# Gradients: multi-hue sequential scales, nine stops, lightness monotone. Use for magnitude only, never as a decoration.
vellum$gradients <- list(
  lagoon = c("#E4EFE2", "#BADEC5", "#8FCBB5", "#66B6AC", "#459FA4", "#378598", "#386C86", "#3A536B", "#383D48"),
  ember = c("#F1EADC", "#E8CFB0", "#DDB38E", "#CF9777", "#BC7D67", "#A46662", "#87545D", "#664554", "#443941"),
  shore = c("#F1EADC", "#DBD5AF", "#BCC18E", "#98AF77", "#739C6A", "#508864", "#37725F", "#2D5A54", "#314041")
)
vellum_dark$gradients <- list(
  lagoon = c("#333B31", "#34533E", "#2F6A58", "#2D8178", "#3B969A", "#5BA8BC", "#84B9D6", "#AFCBE7", "#D7DEEC"),
  ember = c("#3D372C", "#5B462B", "#7A5533", "#976344", "#B2745F", "#C98883", "#D99FA9", "#E2BBCB", "#E7D9E3"),
  shore = c("#3D372C", "#514B2A", "#5E6232", "#657A45", "#6A9362", "#72AB85", "#84C0AA", "#A3D2CB", "#D0E2E3")
)
scale_fill_vellum_grad   <- function(name = "lagoon", V = vellum, ...) ggplot2::scale_fill_gradientn(colours = V$gradients[[name]], ...)
scale_colour_vellum_grad <- function(name = "lagoon", V = vellum, ...) ggplot2::scale_colour_gradientn(colours = V$gradients[[name]], ...)
