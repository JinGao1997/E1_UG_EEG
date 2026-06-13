# =============================================================================
# Run this as an RStudio BACKGROUND JOB (see instructions from assistant).
#
# It runs Pipline_UG_OfferPhase for all 4 (experiment x baseline) combos,
# each as a SEPARATE Rscript subprocess (so reticulate use_condaenv() runs once
# per process), sequentially. CPP phase stays OFF. Per-combo logs + SUMMARY.txt.
#
# Orchestrator = this R session, managed by RStudio's Background Jobs (stable,
# not a detached process), so it won't be reaped like the standalone PowerShell
# driver was. Keep RStudio open; machine on; lock screen is fine.
# =============================================================================

setwd("C:/Code/UG_ERP_Project")
root <- getwd()

stamp  <- format(Sys.time(), "%Y%m%d_%H%M%S")
logdir <- file.path(root, paste0("_pipeline_run_", stamp))
dir.create(logdir, showWarnings = FALSE)
summary_file <- file.path(logdir, "SUMMARY.txt")

log_msg <- function(m) {
  line <- paste0(format(Sys.time(), "%H:%M:%S"), "  ", m)
  cat(line, "\n")
  cat(line, "\n", file = summary_file, append = TRUE)
}

log_msg(paste("Background-Job run started. Log dir:", logdir))

# --- purl the Rmd to plain R once ---
code_file <- file.path(logdir, "pipeline_code.R")
knitr::purl("Pipline_UG_OfferPhase.Rmd", code_file, documentation = 0L, quiet = TRUE)
if (!file.exists(code_file)) { log_msg("PURL FAILED. Aborting."); quit(save = "no", status = 1) }
base_code <- readLines(code_file)
log_msg(paste("Purl done,", length(base_code), "lines."))

rscript <- file.path(R.home("bin"), "Rscript.exe")
combos  <- list(c("E1","FALSE"), c("E1","TRUE"), c("E2","FALSE"), c("E2","TRUE"))

for (cb in combos) {
  exp <- cb[1]; bl <- cb[2]; tag <- paste0(exp, "_", bl)

  code <- base_code
  code <- sub('experiment_version *<- *"[^"]*"',
              sprintf('experiment_version <- "%s"', exp), code)
  code <- sub('use_baseline_correction *<- *(TRUE|FALSE)',
              sprintf('use_baseline_correction <- %s', bl), code)

  # sanity: confirm the substitution took (substring match; tolerant of trailing
  # whitespace / inline comments in the purled line)
  if (!any(grepl(sprintf('experiment_version <- "%s"', exp), code, fixed = TRUE)) ||
      !any(grepl(sprintf('use_baseline_correction <- %s', bl), code, fixed = TRUE))) {
    log_msg(sprintf("[%s] SUBSTITUTION FAILED -- skipped", tag)); next
  }

  run_file <- file.path(logdir, paste0("run_", tag, ".R"))
  writeLines(c(sprintf('setwd("%s")', root), code), run_file)
  log_file <- file.path(logdir, paste0(tag, ".log"))

  log_msg(sprintf("[%s] START (exp=%s, use_baseline_correction=%s)", tag, exp, bl))
  t0 <- Sys.time()
  rc <- system2(rscript, shQuote(run_file), stdout = log_file, stderr = log_file, wait = TRUE)
  dur <- round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1)
  if (identical(rc, 0L) || identical(rc, 0)) {
    log_msg(sprintf("[%s] SUCCESS  duration=%smin", tag, dur))
  } else {
    log_msg(sprintf("[%s] FAILED (exit %s)  duration=%smin -- see %s", tag, rc, dur, log_file))
  }
}

log_msg("Background-Job run finished.")
