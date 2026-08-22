# additivity_equivalence_and_floor.R
# ===========================================================================
# INTEGRATED additivity test for the emotion x fairness effect on REJECTION.
# One run over E1 / E2 / Integrative that does BOTH jobs and SAVES everything:
#
#   (job 1, the VERDICT)   LINK-scale TOST equivalence  -- from
#                          tost_additivity_equivalence.R (v1.3)
#   (job 2, the DIAGNOSIS) RESPONSE/population-scale floor diagnostic + the
#                          two-scale side-by-side -- from additivity_full_test.R
#
# Supersedes running those two separately: it keeps tost_*'s saving harness
# (timestamped folder + summary CSV + per-model sensitivity PDF + run log +
# sessionInfo) AND adds full_test's [A] observed cell rates and [E] response/
# population bootstrap. STRICTLY READ-ONLY on the model tree: reads only
# final_model_GLMM_rejection.rds; writes ONLY inside its own new output folder.
#
# ---- WHY TWO SCALES, AND WHICH ONE DECIDES WHAT (read before trusting output) --
# A logit GLMM defines additivity on the LOG-ODDS (link) scale: the
# emotion:offer_type coefficients = 0. Logit is NONLINEAR, so additive-in-log-
# odds != additive-in-probability. The fair cells sit near the FLOOR (rejection
# ~6-17%), so a fixed log-odds interaction maps to a tiny probability difference.
# Consequence for each job:
#   * EQUIVALENCE / the additivity VERDICT is judged on the LINK scale ON PURPOSE.
#     On the response scale the floor would make "equivalent" pass trivially
#     (everything is small near a floor) = self-deception. TOST asks "is it small
#     enough to be negligible?", and near a floor that is answered "yes" for free.
#   * But the link scale has the opposite failure: near the floor a few events +
#     logit's steepness can INFLATE a log-odds interaction that is behaviourally
#     trivial (E2: link -1.11 collapses to response ~-0.09 ~ observed). So the
#     link verdict must ALWAYS be read next to the response-scale EFFECT SIZE.
# => link scale answers "is the process additive / negligible latent moderation?"
#    response scale answers "does any interaction matter for actual behaviour?"
#    Neither alone proves additivity; this script lays both side by side.
# Second axis: CONDITIONAL (emmeans, random effects = 0, 'typical subject') vs
# POPULATION (fitted(m) averaged over the actual subjects). Near the floor
# emmeans can extrapolate BELOW the data while the population average returns to
# the observed rate. Direction is not fixed (E1: observed large&noisy, model
# shrinks; E2: model inflates, observed ~0), so we show both.
# ===========================================================================

suppressPackageStartupMessages({ library(glmmTMB); library(emmeans) })
# ^ glmmTMB loaded on purpose (model class). car is used only namespaced
#   (car::Anova) inside tryCatch so a missing car can't stop the run.
options(contrasts = c("contr.sum", "contr.poly"))   # matches the fit (Type III valid)

## ---- 0. config (EDIT if paths move) ----------------------------------------
PROJ <- "C:/Code/UG_ERP_Project"
MODELS <- c(
  E1          = file.path(PROJ, "results/Behavior/E1_TwoStage_Bates/GLMM_Rejection/final_model_GLMM_rejection.rds"),
  E2          = file.path(PROJ, "results/Behavior/E2_TwoStage_Bates/GLMM_Rejection/final_model_GLMM_rejection.rds"),
  Integrative = file.path(PROJ, "results/Behavior/Integrative_TwoStage_Bates/GLMM_Rejection/final_model_GLMM_rejection.rds")
)
OUT_ROOT <- file.path(PROJ, "results/Behavior/Additivity_Equivalence_and_Floor")
ALPHA    <- 0.05
DELTA_SU <- 0.70   # anchor-3 (Su benchmark) on LOG-ODDS; ILLUSTRATIVE -- recompute
                   # from Su cell acceptance rates (protocol S3.5) before citing.
BOOT     <- 2000   # cluster-bootstrap resamples for the response-scale CI

# theory-axis grouping weights: reward(enj/rew)+affiliative = +.5 (pull to accept),
# dominance+disgust = -.5 (push to reject), neutral = 0. (reward label = 'enj' or 'rew')
WGT <- c(enj = .5, rew = .5, aff = .5, dom = -.5, dis = -.5, neu = 0)
EMO <- c("enj", "aff", "dom", "dis")   # the 4 grouped emotions (neu off the axis)

# grounded omnibus emotion:offer_type (Type III Wald chi2) from each model's
# GLMM_Rejection/anova_apa.md (authoritative; p kept as character so E2's "<.001"
# is not given a fabricated precise value). car::Anova is run live as a cross-check.
OMNIBUS <- list(
  E1          = list(chisq = 6.35,  p = "0.175"),
  E2          = list(chisq = 35.85, p = "<.001"),
  Integrative = list(chisq = 7.27,  p = "0.122")
)

## ---- output folder (timestamped; NEVER overwrites earlier runs) -------------
STAMP <- format(Sys.time(), "%Y%m%d_%H%M%S")
OUT   <- file.path(OUT_ROOT, paste0("run_", STAMP))
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
LOG <- file.path(OUT, "run_log.txt")
say <- function(...) { s <- sprintf(...); cat(s); cat(s, file = LOG, append = TRUE) }
say("additivity equivalence + floor diagnostic -- run %s\n", STAMP)
say("output folder: %s\n", OUT)
say("delta_Su (anchor-3, ILLUSTRATIVE) = %.3f log-odds | alpha = %.2f | boot = %d\n\n",
    DELTA_SU, ALPHA, BOOT)

if (!any(file.exists(MODELS)))
  stop("None of the model .rds files were found. Check PROJ / results paths.")

## ---- helpers ---------------------------------------------------------------
# TOST: two one-sided z-tests; equivalent iff the 90% CI (1-2*alpha) lies in [-D,D]
tost <- function(est, se, D, alpha = 0.05) {
  p_lo <- pnorm((est + D) / se, lower.tail = FALSE)   # H0: theta <= -D
  p_hi <- pnorm((est - D) / se, lower.tail = TRUE)    # H0: theta >=  D
  ci   <- est + c(-1, 1) * qnorm(1 - alpha) * se
  list(D = D, p = max(p_lo, p_hi), equivalent = max(p_lo, p_hi) < alpha,
       ci_low = ci[1], ci_high = ci[2])
}
verdict <- function(est, se, D) if (tost(est, se, D)$equivalent) "EQUIVALENT" else "not equiv/inconclusive"

# grouping x fairness interaction from a 5x2 matrix of logits (response-scale path)
grp_int <- function(L)
  (mean(L[c("enj","aff"),"fair"])   - mean(L[c("dom","dis"),"fair"])) -
  (mean(L[c("enj","aff"),"unfair"]) - mean(L[c("dom","dis"),"unfair"]))
lg <- function(p) qlogis(pmin(pmax(p, 1e-4), 1 - 1e-4))   # safe logit

## ---- per-model analysis (returns one summary row, or NULL if skipped) -------
run_one <- function(tag, model_path) {
  say("========================= %s =========================\n", tag)
  if (!file.exists(model_path)) { say("  file not found -> skip: %s\n\n", model_path); return(NULL) }
  m   <- readRDS(model_path)
  dat <- if (!is.null(m$frame)) m$frame else model.frame(m)
  stopifnot(all(c("reject_binary", "emotion", "offer_type") %in% names(dat)))
  say("  model class: %s\n", paste(class(m), collapse = "/"))

  ## [A] observed cell rejection rates -- shows the near-floor fair cells --------
  raw <- tapply(dat$reject_binary, list(dat$emotion, dat$offer_type), mean)
  say("  [A] OBSERVED rejection rate per cell (fair / unfair):\n")
  for (e in c("enj","aff","dom","dis","neu"))
    if (e %in% rownames(raw))
      say("        %-4s  %.3f / %.3f\n", e, raw[e, "fair"], raw[e, "unfair"])

  ## [B] focal grouping contrast on the LINK (log-odds) scale -- the VERDICT input
  emm <- emmeans(m, ~ emotion * offer_type)      # link (log-odds); averages over Exp if present (pooled)
  g   <- as.data.frame(emm@grid)
  wv  <- as.numeric(WGT[as.character(g$emotion)]) * ifelse(as.character(g$offer_type) == "fair", 1, -1)
  wv[is.na(wv)] <- 0
  stopifnot(abs(sum(wv)) < 1e-9)                 # valid contrast, weights sum to 0
  ic  <- summary(contrast(emm, method = list(group_x_fairness = wv)), infer = c(TRUE, TRUE))
  est <- ic$estimate ; se <- ic$SE ; pc <- ic$p.value
  say("  [B] focal grouping x fairness, LINK/conditional: est=%+.3f log-odds  SE=%.3f  z=%.2f  p=%.3g\n",
      est, se, est/se, pc)
  say("      (+ = the [(reward+aff)-(dom+dis)] effect is LARGER at fair than unfair)\n")

  ## [C] omnibus emotion:offer_type -- confirmatory (grounded) + live cross-check -
  gv <- OMNIBUS[[tag]]
  say("  [C] omnibus emotion:offer_type (anova_apa.md): chisq=%.2f  p=%s\n", gv$chisq, gv$p)
  om <- tryCatch(car::Anova(m, type = 3), error = function(e) NULL)
  if (!is.null(om)) {
    r <- om[grep("emotion:offer_type", rownames(om)), , drop = FALSE]
    say("      live car::Anova(type=3) cross-check: chisq=%.2f  p=%.3g\n", r[1, 1], r[1, ncol(r)])
  } else say("      (car::Anova unavailable here; using grounded values above)\n")

  ## [D] LINK-scale equivalence (the VERDICT): is the log-odds interaction negligible?
  DELTA4 <- 1.52 * se                            # own-design 33%-power detectable interaction (Simonsohn)
  Dstar  <- abs(est) + qnorm(1 - ALPHA) * se     # smallest bound giving equivalence
  say("  [D] LINK equivalence: Delta* (min equiv bound) = %.3f | anchor-4 (1.52*SE) = %.3f | anchor-3 (Su) = %.3f\n",
      Dstar, DELTA4, DELTA_SU)
  v4 <- verdict(est, se, DELTA4); vsu <- verdict(est, se, DELTA_SU)
  say("      TOST: anchor-4 Delta4=%.3f -> %s | anchor-3 Delta_Su=%.3f -> %s\n",
      DELTA4, v4, DELTA_SU, vsu)

  ## [E] SAME interaction on the RESPONSE/POPULATION scale -- the FLOOR DIAGNOSTIC -
  ##     fitted(m): response scale, random effects INCLUDED, NO newdata -> no design-
  ##     matrix reconstruction (saved glmmTMB cannot rebuild it). CI via cluster
  ##     bootstrap over subjects (also reconstruction-free). This is a DIAGNOSTIC of
  ##     whether a significant LINK interaction is behaviourally trivial -- it does
  ##     NOT feed the equivalence verdict (see header: response-scale equivalence
  ##     passes trivially near a floor).
  pa    <- fitted(m)
  cellP <- tapply(pa, list(dat$emotion, dat$offer_type), mean)
  estP  <- grp_int(lg(cellP))
  gvars <- names(m$modelInfo$reTrms$cond$flist)
  ciP   <- c(NA_real_, NA_real_)
  if (length(gvars) >= 1 && gvars[1] %in% names(dat)) {
    idx  <- split(seq_len(nrow(dat)), as.character(dat[[gvars[1]]]))
    subs <- names(idx) ; set.seed(1)
    bt   <- vapply(seq_len(BOOT), function(b) {
      r <- unlist(idx[sample(subs, replace = TRUE)], use.names = FALSE)
      grp_int(lg(tapply(pa[r], list(dat$emotion[r], dat$offer_type[r]), mean)))
    }, numeric(1))
    ciP <- quantile(bt, c(.025, .975), na.rm = TRUE)
  }
  say("  [E] grouping x fairness, RESPONSE/population (fitted, RE-averaged): est=%+.3f  95%%CI [%+.3f, %+.3f]\n",
      estP, ciP[1], ciP[2])
  say("      population fair-cell prob vs OBSERVED [A]:  %s\n",
      paste(sprintf("%s %.3f/%.3f", EMO, cellP[EMO,"fair"], raw[EMO,"fair"]), collapse = "  "))

  ## [F] two-scale one-liner + floor flag ---------------------------------------
  # floor flag: response interaction collapsed to a small fraction of the link one
  collapse <- if (is.finite(estP) && abs(est) > 1e-6) abs(estP) / abs(est) else NA_real_
  floor_flag <- isTRUE(pc < ALPHA && !is.na(collapse) && collapse < 0.25)  # sig link but resp << link
  say("  [F] SCALES  link/cond=%+.3f | resp/pop=%+.3f | ratio(resp/link)=%.2f | Delta*=%.3f | omnibus chisq=%.2f p=%s%s\n\n",
      est, estP, collapse, Dstar, gv$chisq, gv$p,
      if (floor_flag) "  <== sig link interaction is FLOOR-INFLATED (collapses on response scale)" else "")

  ## sensitivity curve -> PDF (unchanged logic from tost_*) ----------------------
  grid  <- seq(0, max(DELTA_SU, Dstar) * 1.2, length.out = 400)
  equiv <- vapply(grid, function(D) tost(est, se, D)$equivalent, logical(1))
  pdf(file.path(OUT, sprintf("sensitivity_%s.pdf", tag)), width = 7, height = 4.6)
  op <- par(mar = c(4.2, 4.4, 2.6, 1))
  plot(grid, as.integer(equiv), type = "s", lwd = 2, yaxt = "n",
       xlab = "Equivalence bound  Delta  (log-odds)", ylab = "",
       main = sprintf("TOST sensitivity: emotion x fairness (%s, focal grouping contrast)", tag))
  axis(2, at = c(0, 1), labels = c("not equiv.", "equivalent"))
  abline(v = c(Dstar, DELTA4, DELTA_SU), lty = c(1, 2, 3), col = c("black", "blue", "red"))
  legend("right", bty = "n", lty = c(1, 2, 3), col = c("black", "blue", "red"),
         legend = c(sprintf("Delta* = %.2f", Dstar),
                    sprintf("anchor-4 own-design = %.2f", DELTA4),
                    sprintf("anchor-3 Su = %.2f", DELTA_SU)))
  par(op); dev.off()
  say("  saved sensitivity_%s.pdf\n\n", tag)

  data.frame(model = tag,
             est_link = round(est, 4), se_link = round(se, 4), z_link = round(est/se, 3),
             p_link = signif(pc, 4),
             omnibus_chisq = gv$chisq, omnibus_p = gv$p,
             est_response = round(estP, 4),
             resp_ci_lo = round(ciP[1], 4), resp_ci_hi = round(ciP[2], 4),
             resp_link_ratio = round(collapse, 3), floor_inflated = floor_flag,
             delta4_own = round(DELTA4, 4), delta_su = DELTA_SU, delta_star = round(Dstar, 4),
             tost_delta4 = v4, tost_delta_su = vsu, stringsAsFactors = FALSE)
}

## ---- loop over the three models + save -------------------------------------
rows <- Map(run_one, names(MODELS), MODELS)
res  <- do.call(rbind, Filter(Negate(is.null), rows))
csv  <- file.path(OUT, "additivity_summary.csv")
write.csv(res, csv, row.names = FALSE)
say("saved summary CSV: %s\n\n", csv)
cat("\n==== additivity summary (also saved to CSV) ====\n"); print(res)

writeLines(capture.output(sessionInfo()), file.path(OUT, "sessionInfo.txt"))

## ---- OVERALL honest read + reporting reminders -----------------------------
say("\n================= OVERALL (predominantly-additive read) =================\n")
say("* CONFIRMATORY omnibus decides additivity: E1 ns (chisq=6.35), Integrative ns (chisq=7.27)\n")
say("  -> NO evidence against additivity; E2 SIGNIFICANT (chisq=35.85) but LINK scale only.\n")
say("* FLOOR DIAGNOSTIC [E]: E2's link interaction collapses on the response/population scale\n")
say("  (~observed) -> the significant LINK term is floor-inflated, not a large behavioural interaction.\n")
say("* HONEST LIMITS -- not a clean single-scale proof:\n")
say("    (1) near the floor the interaction is not robustly estimable on ANY scale (E1 observed large&noisy,\n")
say("        model shrinks; E2 model inflates, observed ~0) -> nothing is BOTH large AND robust.\n")
say("    (2) LINK equivalence needs a PRE-SET SESOI >= Delta*; where Delta* is large, link additivity is\n")
say("        NOT supported at a small SESOI -> additivity leans on the response/floor argument there.\n")
say("    (3) response-scale smallness is partly MECHANICAL (floor compression) -> CONSISTENT WITH, not\n")
say("        hard proof of, additivity. anchor-4 own-design SESOI is weak; anchor-3 Su is ILLUSTRATIVE.\n")
say("* REPORTING (protocol S2.8/S2.9): additivity is a CHOICE-level claim, label EXPLORATORY (Deviations);\n")
say("  the claim rests on the OMNIBUS (E1/pooled ns), NOT the focal contrast; RT has a congruency\n")
say("  interaction -> report it, do NOT hide E2; Delta is external/deterministic, NEVER tuned to est;\n")
say("  recompute anchor-3 DELTA_SU from Su cell rates before citing.\n")
say("========================================================================\n")
