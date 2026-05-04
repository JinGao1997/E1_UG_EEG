# Methods Paragraph (EEG Single-trial LMM, E2)

Generated: 2026-05-04 15:58:26

## Statistical Analysis

Single-trial ERP amplitudes were analyzed using the Alday (2019)
baseline-as-covariate framework, in which baseline amplitude is
fitted as a fixed-effect covariate rather than subtracted from the
epoch. This approach permits the data to determine the optimal
baseline-target relationship and supports interactions between
baseline drift and experimental conditions when the data warrant.

Mixed-effects models were fitted in R with the lme4
(1.1.38) and lmerTest (3.1.3) packages.
Categorical predictors used sum-to-zero contrasts (R option contr.sum)
to support valid Type III tests in the presence of interactions
(Schad, Vasishth, Hohenstein, & Kliegl, 2020). Trials were excluded
if |amplitude| > 200 microvolts at any electrode (HU pipeline
peak-to-peak rejection, marked as NaN in the single-trial data),
if the offer was the medium-fairness filler (Offers_Other == 7),
if the participant did not respond (reaction == 0), or if the
response time fell outside [300, 3000] ms. The latter three
criteria were applied at the analysis layer rather than in upstream
preprocessing, to keep the canonical trials.csv as a single source
of truth and to maintain identical inclusion logic across the
parallel behavioral analysis (Sta_Behaviour_RefAlday.Rmd) and the
Stage 1 EEG analysis reported here.
Baseline amplitude was mean-centered (per Alday 2019) but kept on the
microvolt scale to preserve direct interpretation as voltage drift.

### Components and confirmatory framing

Experiment 2 used a simultaneous design: face and offer were presented together. Offer-phase EEG epochs therefore contain both face-evoked early components (N170, EPN) and offer-evoked components (FRN, N400, LPP_offer).

Components fitted as confirmatory analyses (present in both E1 and E2): FRN, N400, LPP_offer.
Components fitted as exploratory analyses: N170, EPN.
Cross-experiment conceptual replication is based on the confirmatory
set; exploratory components are reported descriptively only and are
not interpreted as evidence for or against pre-registered hypotheses.

### Fixed-effect specification (Alday Tier 2.5)

For each component, the fixed-effect search space was the pairwise
interaction model: amplitude ~ (emotion + offer_type + Baseline_c)^2.
Theoretically core terms (emotion, offer_type, Baseline_c, and the
emotion:offer_type interaction) were forced to be retained via
buildmer's 'include' argument; baseline-by-condition interactions
(Baseline_c:emotion, Baseline_c:offer_type) were subjected to LRT-
based inclusion testing within the same buildmer call. The final
fixed structure may therefore differ across components, reflecting
genuine differences in baseline-condition coupling.

### Random-effects structure

Random-effects structures were selected following the parsimonious-
Bates protocol (Bates, Kliegl, Vasishth, & Baayen, 2015; Matuschek,
Kliegl, Vasishth, Baayen, & Bates, 2017). For each component:
Step 1 specified a maximal model with main-effect random slopes and
full correlations (interaction random slopes were omitted because
cell-level variance components rarely identify in single-trial EEG
with typical N). Step 2 fitted a zero-correlation-parameter (ZCP)
model. Step 3 used buildmer LRT-based backward elimination at
alpha = 0.20 (Matuschek et al., 2017). Step 4 tested whether adding
correlation parameters improved fit. Step 5 ran rePCA dimensionality
diagnostics to confirm that the final structure was data-supported.
Stimulus identity was counterbalanced via Latin-square design and
was not modeled as a separate random effect (cf. Westfall, Kenny, &
Judd, 2014).

### Inferential strategy

Fixed-effect inference used a Type III F-test with denominator
degrees of freedom approximated via a cascading method preference:
Satterthwaite (Kuznetsova, Brockhoff, & Christensen, 2017; Luke,
2017) was attempted first; on numerical failure, Kenward-Roger
(Kenward & Roger, 1997; via the pbkrtest backend) was attempted
next; Wald chi-square (car::Anova) was used only as a final
fallback. The method actually used per component is reported in
supplementary tables. Post-hoc contrasts were computed using emmeans
(Lenth, 2024) with asymptotic standard errors and false-discovery-
rate (FDR) correction within each effect family.

### Effect-size reporting

Partial eta-squared with 95% confidence intervals are reported
alongside F-tests (effectsize::eta_squared). Marginal and conditional
R-squared (Nakagawa & Schielzeth, 2013) are reported per component.
All contrast estimates are reported in microvolts with 95% CIs.

### Post-hoc gating

Simple-effect decompositions of the omnibus emotion x offer_type
interaction were performed and reported as confirmatory only when
the omnibus interaction p < 0.05. Effects with 0.05 <= p < 0.10
were computed but reported only in supplementary materials, never
as confirmatory evidence.

### Stage 2: BLUP-based individual differences

Per-participant best linear unbiased predictors (BLUPs) for the
emotion x offer_type interaction term were extracted from each
component's Stage 1 fit and weighted-regressed against personality
and trust covariates (weights 1/SE^2). FDR correction was applied
independently within each pre-registered trait group. Stage 2
analyses are exploratory across all components: the BLUP procedure
is post-hoc inference on subject-specific deviations from the
fixed-effect mean, with shrinkage that complicates standard error
interpretation. We report Stage 2 findings to surface candidate
individual-difference patterns for future pre-registration, not as
confirmatory evidence in this manuscript.

## Sample

21348 trials from 30 participants entered Stage 1 analysis (E2).

## References (cite as appropriate)

Alday, P. M. (2019). How much baseline correction do we need in ERP
  research? Extended GLM model can replace baseline correction while
  lifting its limits. Psychophysiology, 56, e13451.
Bates, D., Kliegl, R., Vasishth, S., & Baayen, R. H. (2015).
  Parsimonious mixed models. arXiv:1506.04967.
Halekoh, U., & Hojsgaard, S. (2014). A Kenward-Roger approximation
  and parametric bootstrap methods for tests in linear mixed models
  -- the R package pbkrtest. Journal of Statistical Software, 59(9).
Kenward, M. G., & Roger, J. H. (1997). Small sample inference for
  fixed effects from restricted maximum likelihood. Biometrics, 53,
  983-997.
Kuznetsova, A., Brockhoff, P. B., & Christensen, R. H. B. (2017).
  lmerTest package: Tests in linear mixed effects models. Journal of
  Statistical Software, 82(13).
Lenth, R. V. (2024). emmeans: Estimated marginal means.
Luke, S. G. (2017). Evaluating significance in linear mixed-effects
  models in R. Behavior Research Methods, 49, 1494-1502.
Matuschek, H., Kliegl, R., Vasishth, S., Baayen, H., & Bates, D.
  (2017). Balancing Type I error and power in linear mixed models.
  Journal of Memory and Language, 94, 305-315.
Nakagawa, S., & Schielzeth, H. (2013). A general and simple method
  for obtaining R^2 from generalized linear mixed-effects models.
  Methods in Ecology and Evolution, 4, 133-142.
Schad, D. J., Vasishth, S., Hohenstein, S., & Kliegl, R. (2020).
  How to capitalize on a priori contrasts in linear (mixed) models.
  Journal of Memory and Language, 110, 104038.
Westfall, J., Kenny, D. A., & Judd, C. M. (2014). Statistical power
  and optimal design in experiments in which samples of participants
  respond to samples of stimuli. Journal of Experimental Psychology:
  General, 143, 2020-2045.
