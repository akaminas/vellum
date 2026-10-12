# build.R: run every R example in examples/r/ (each script whose name does not start with "_" or "build"), each in its
# own R session, so every figure is drawn from a clean state. Each script writes its twins into docs/figures/<group>/
# and records itself in that group's manifest.json.   Run: Rscript examples/r/build.R
here <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1])))
rscript <- file.path(R.home("bin"), "Rscript")
scripts <- Filter(function(f) !grepl("^(_|build)", basename(f)), list.files(here, pattern = "\\.R$", full.names = TRUE))
for (s in scripts) if (system2(rscript, shQuote(s)) != 0) stop("failed: ", basename(s))
