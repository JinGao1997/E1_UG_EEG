# Methods Paragraph (Behavioral Analyses, E2)

Generated: 2026-05-03 15:46:37

## Statistical Analysis

Behavioral data were analyzed using mixed-effects models in R (version 4.3.3)
with the lme4 (1.1.38) and lmerTest (3.1.3) packages, with binomial models fitted
via glmmTMB (1.1.14). Categorical predictors used sum-to-zero contrasts (R option
contr.sum) to support valid Type III tests in the presence of interactions
(Schad, Vasishth, Hohenstein, & Kliegl, 2020). Trials were excluded if the
participant did not respond (reaction = 0), if the response time fell outside
300-3000 ms, or if the offer was the medium-fairness filler (Offers_Other = 7).

### Models

We fitted three models on Experiment E2 data:

1. **Rejection rate (GLMM_rejection):** A binomial mixed-effects model on a
   binary rejection outcome with predictors emotion (5 levels), offer type
   (fair vs unfair), and their interaction.

2. **Response time, main analysis (LMM_RT_main):** A linear mixed-effects
   model on log-transformed response time with predictors emotion, offer
   type, and their interaction. Reaction (accept vs reject) was deliberately
   NOT included as a covariate because it is a downstream outcome of
   emotion x offer_type; conditioning on a downstream variable induces
   collider bias and would distort the total emotion-on-RT effect (Rohrer,
   2018).

3. **Response time, unfair-only (LMM_RT_unfair):** A linear mixed-effects
   model on log-transformed response time restricted to unfair offers, with
   predictors emotion, reaction, and their interaction. This stratum
   parallels the HDDM modeling of accept-vs-reject decision dynamics on
   unfair offers.

### Random-effects structure

Random-effects structures were selected following the parsimonious-Bates
protocol (Bates, Kliegl, Vasishth, & Baayen, 2015; Matuschek, Kliegl,
Vasishth, Baayen, & Bates, 2017). Starting from the design-justified
maximal model (random intercepts and slopes for within-subject factors
emotion and offer type by participant), zero-correlation parameter (ZCP)
models were fitted, then non-supported variance components were removed
via likelihood-ratio tests with elimination alpha = 0.20 (Matuschek et al.,
2017) using the buildmer package. Correlation parameters between surviving
slopes were tested in a final step. Random-effects dimensionality was
diagnosed via rePCA (Bates et al., 2015). Stimulus identity was
counterbalanced across participants via a Latin-square design and was not
modeled as a separate random effect; identity-level idiosyncrasies are thus
controlled at the design level rather than statistically partitioned (cf.
Westfall, Kenny, & Judd, 2014).

### Inferential strategy

For linear mixed models, fixed-effect inference used a Type III F-test with
denominator degrees of freedom approximated via a cascading method
preference: Satterthwaite (Kuznetsova, Brockhoff, & Christensen, 2017;
Luke, 2017) was attempted first; on numerical failure, Kenward-Roger
(Kenward & Roger, 1997; via the pbkrtest backend) was attempted next;
Wald chi-square (car::Anova) was used only as a final fallback. The
method actually used per analysis is reported in supplementary tables.
For the binomial model, Wald chi-square tests were used because the
Satterthwaite and Kenward-Roger approximations are not defined for
non-Gaussian likelihoods (the residual variance term they require does
not exist in binomial-likelihood models, where Var(y) is determined by
the mean structure as p(1-p)). Post-hoc contrasts were computed using
the emmeans package (Lenth, 2024) with asymptotic standard errors and
false-discovery-rate (FDR) correction within each effect family.

### Effect-size reporting

For Gaussian models, partial eta-squared with 95% confidence intervals are
reported alongside F-tests (effectsize::eta_squared). For the binomial
model, odds ratios with 95% CIs are reported for fixed-effect contrasts.
For log-RT contrasts, percent RT change is reported as
(exp(b) - 1) x 100. Marginal and conditional R-squared (Nakagawa &
Schielzeth, 2013) are reported for all models.

### Post-hoc gating

Simple-effect decompositions of the omnibus emotion x offer_type (or
emotion x reaction) interaction were performed only when the omnibus
interaction p < 0.05. Effects with 0.05 <= p < 0.10 were computed but
reported only in supplementary materials, never as confirmatory evidence.

## Sample

21477 trials from 30 participants entered the GLMM_rejection and LMM_RT_main
analyses; the LMM_RT_unfair stratum included 10737 trials.

## References (cite as appropriate)

Bates, D., Kliegl, R., Vasishth, S., & Baayen, R. H. (2015).
  Parsimonious mixed models. arXiv:1506.04967.
Halekoh, U., & Hojsgaard, S. (2014). A Kenward-Roger approximation and
  parametric bootstrap methods for tests in linear mixed models -- the R
  package pbkrtest. Journal of Statistical Software, 59(9).
Kenward, M. G., & Roger, J. H. (1997). Small sample inference for fixed
  effects from restricted maximum likelihood. Biometrics, 53, 983-997.
Kuznetsova, A., Brockhoff, P. B., & Christensen, R. H. B. (2017).
  lmerTest package: Tests in linear mixed effects models. Journal of
  Statistical Software, 82(13).
Lenth, R. V. (2024). emmeans: Estimated marginal means.
Luke, S. G. (2017). Evaluating significance in linear mixed-effects models
  in R. Behavior Research Methods, 49, 1494-1502.
Matuschek, H., Kliegl, R., Vasishth, S., Baayen, H., & Bates, D. (2017).
  Balancing Type I error and power in linear mixed models. Journal of
  Memory and Language, 94, 305-315.
Nakagawa, S., & Schielzeth, H. (2013). A general and simple method for
  obtaining R^2 from generalized linear mixed-effects models. Methods in
  Ecology and Evolution, 4, 133-142.
Rohrer, J. M. (2018). Thinking clearly about correlations and causation.
  Advances in Methods and Practices in Psychological Science, 1, 27-42.
Schad, D. J., Vasishth, S., Hohenstein, S., & Kliegl, R. (2020). How to
  capitalize on a priori contrasts in linear (mixed) models. Journal of
  Memory and Language, 110, 104038.
Westfall, J., Kenny, D. A., & Judd, C. M. (2014). Statistical power and
  optimal design in experiments in which samples of participants respond
  to samples of stimuli. Journal of Experimental Psychology: General,
  143, 2020-2045.

