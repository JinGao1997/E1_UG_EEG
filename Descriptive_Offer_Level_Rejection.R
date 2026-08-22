# ---------------------------------------------------------------------------
# Descriptive_Offer_Level_Rejection.R
#
# PURPOSE (descriptive only - NO modelling)
#   Rejection rate by emotion x individual offer level (5, 6, 8, 9), for E1 and E2.
#   The canonical analyses pool Offers_Other into offer_type (fair = {5,6},
#   unfair = {8,9}). This script un-pools that factor to show the per-offer
#   breakdown - specifically, whether the emotion effect inside the "fair" cell
#   is carried by the 5:5 even split or by the 6:4 split.
#
# STATUS
#   Exploratory descriptive cross-tab. Proportions and counts only.
#   NO inferential test is computed here, deliberately: at 5:5 the number of
#   rejection events is expected to be very low in several emotion cells, which
#   would make a per-offer GLMM unstable (quasi-complete separation). The
#   N_subj_with_any_reject column lets that be checked directly - if most
#   subjects contribute zero rejections in a cell, that cell cannot support a
#   mixed model, and this table is the appropriate level of description.
#
# SAFETY
#   Reads only. Does not modify, re-run, or depend on the output of any existing
#   script. Writes to a NEW directory (results/Behavior/Descriptive_Offer_Level/)
#   with timestamped filenames - never overwrites a previous run.
#
# PROVENANCE
#   Trial-inclusion filters and factor coding are copied verbatim from the
#   canonical script Sta_Behaviour_E1_E2_Integrative.Rmd:
#     rt bounds            -> L68-69
#     data path            -> L2582-2584
#     filter Offers_Other  -> L755
#     filter reaction != 0 -> L761
#     filter RT range      -> L767
#     emotion factor       -> L782
#     reaction recode      -> L783-789
#     reject_binary        -> L790
#   If those filters change in the canonical script, update them here to match.
#
#   N_subjects uses the raw `participant_id`, not the canonical
#   `participant_id_internal`. Within a single experiment the raw ids have
#   consistent case (E1 "Vp00NN", E2 "VP00NN"), so the distinct count is
#   identical; the standardisation only matters when pooling E1 + E2, which
#   this script does not do.
#
# RUN
#   Rscript Descriptive_Offer_Level_Rejection.R      (or source() in RStudio)
# ---------------------------------------------------------------------------

if (!requireNamespace("pacman", quietly = TRUE)) install.packages("pacman")
pacman::p_load(here, dplyr, readr)

# --- Canonical constants (must match Sta_Behaviour_E1_E2_Integrative.Rmd) ----
rt_lower_ms <- 300    # Rmd L68
rt_upper_ms <- 3000   # Rmd L69

out_dir <- here::here("results", "Behavior", "Descriptive_Offer_Level")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

trials_path <- function(exp_label) {
  here::here("data", paste0("02_Pipeline_Output_", exp_label),
             "Method_Regression", "Stimulus_Locked", "trials.csv")
}

# Minimal reproduction of clean_and_filter() from the canonical Rmd, restricted
# to the columns this descriptive needs.
clean_and_filter_min <- function(df, label) {
  required_cols <- c("participant_id", "Offers_Other", "emotion", "reaction", "RT")
  missing_cols <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop(sprintf("Required columns missing in %s: %s",
                 label, paste(missing_cols, collapse = ", ")))
  }

  n0 <- nrow(df)
  df <- dplyr::filter(df, Offers_Other %in% c(5, 6, 8, 9))          # Rmd L755
  df <- dplyr::filter(df, reaction != 0)                            # Rmd L761
  df <- dplyr::filter(df, RT >= rt_lower_ms, RT <= rt_upper_ms)     # Rmd L767

  df <- dplyr::mutate(
    df,
    emotion  = factor(emotion, levels = c("neu", "aff", "dis", "dom", "enj")),  # Rmd L782
    reaction = factor(                                                          # Rmd L783-789
      dplyr::case_when(
        reaction == 1 ~ "accept",
        reaction == 2 ~ "reject"
      ),
      levels = c("accept", "reject")
    ),
    reject_binary = ifelse(reaction == "reject", 1, 0)                          # Rmd L790
  )

  if (any(is.na(df$emotion)) || any(is.na(df$reaction))) {
    stop(sprintf("Unexpected NA in emotion/reaction after recoding in %s - ",
                 label),
         "check that the raw levels still match the canonical coding.")
  }

  cat(sprintf("[%s] %d -> %d trials retained, %d subjects.\n",
              label, n0, nrow(df), dplyr::n_distinct(df$participant_id)))
  df
}

summarise_by_offer <- function(df, exp_label) {
  df %>%
    dplyr::group_by(emotion, Offers_Other) %>%
    dplyr::summarise(
      N_subjects             = dplyr::n_distinct(participant_id),
      N_trials               = dplyr::n(),
      N_reject               = sum(reject_binary),
      Rejection_rate         = mean(reject_binary),
      N_subj_with_any_reject = dplyr::n_distinct(participant_id[reject_binary == 1]),
      .groups = "drop"
    ) %>%
    dplyr::mutate(Exp = exp_label, .before = 1) %>%
    dplyr::arrange(Offers_Other, emotion)
}

# --- Run -------------------------------------------------------------------
res <- lapply(c("E1", "E2"), function(exp_label) {
  p <- trials_path(exp_label)
  if (!file.exists(p)) stop(sprintf("Data file missing for %s: %s", exp_label, p))
  df <- readr::read_csv(p, show_col_types = FALSE)
  df <- clean_and_filter_min(df, exp_label)
  summarise_by_offer(df, exp_label)
})
out <- dplyr::bind_rows(res)

stamp    <- format(Sys.time(), "%Y%m%d_%H%M%S")
csv_path <- file.path(out_dir, sprintf("Rejection_by_emotion_x_offer_%s.csv", stamp))
md_path  <- file.path(out_dir, sprintf("Rejection_by_emotion_x_offer_%s.md",  stamp))

readr::write_csv(out, csv_path)

md <- c(
  "# Rejection rate by emotion x offer level (descriptive)",
  "",
  sprintf("Generated: %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "Descriptive cross-tab only - no inferential test (see script header).",
  "Offer 5 = 5:5 even split; 6 = 6:4; 8 = 8:2; 9 = 9:1. 7:3 filler excluded,",
  "matching the canonical filter Offers_Other %in% c(5, 6, 8, 9).",
  "Canonical pooling for the main analyses: fair = {5, 6}, unfair = {8, 9}.",
  "",
  "`N_subj_with_any_reject` = number of subjects contributing >= 1 rejection in",
  "that cell (out of N_subjects). A low value means the cell cannot support a",
  "mixed model - it is the separation diagnostic.",
  "",
  paste0("| ", paste(names(out), collapse = " | "), " |"),
  paste0("|", paste(rep(":---", ncol(out)), collapse = "|"), "|"),
  apply(out, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
)
writeLines(md, md_path)

cat("\n")
print(as.data.frame(out), row.names = FALSE)
cat(sprintf("\nWritten:\n  %s\n  %s\n", csv_path, md_path))
