# Methods Paragraph (EEG Sensitivity Analysis: Traditional Baseline Subtraction, E2)

Generated: 2026-05-04 16:37:41

## Sensitivity Analysis Statement

This script reports a SENSITIVITY ANALYSIS, not the primary analysis.
The primary analysis used the Alday (2019) baseline-as-covariate
framework (see companion script Sta_EEG_OfferPhase_RefAlday_v2 and the
results in directory '<EXP>_TwoStage_Bates_Alday/'). This sensitivity
analysis was conducted to verify that substantive conclusions do not
depend on the choice of baseline-correction approach. Substantive
interpretations in the manuscript should be based on the primary
(Alday) analysis; this output is provided for transparency and
robustness checking only.

## Statistical Analysis (Sensitivity Specification)

Single-trial ERP amplitudes were baseline-corrected upstream in the
preprocessing pipeline by subtracting the mean of the -200 to 0 ms
pre-stimulus interval from the entire epoch (traditional baseline
subtraction; cf. Luck, 2014, Chap. 8). The resulting baseline-corrected
amplitudes were then analyzed as the dependent variable in mixed-
effects models. NO baseline covariate was included in the model, in
contrast to the primary Alday-framework analysis.

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

### Components and confirmatory framing

Experiment 2 used a simultaneous design: face and offer were presented together. Offer-phase EEG epochs therefore contain both face-evoked early components (N170, EPN) and offer-evoked components (FRN, N400, LPP_offer).

Components fitted as confirmatory analyses (present in both E1 and E2): FRN, N400, LPP_offer.
Components fitted as exploratory analyses: N170, EPN.
Confirmatory/exploratory framing matches the primary Alday analysis.

### Fixed-effect specification

For each component, the fixed-effect model was the simple two-way
design: amplitude ~ emotion * offer_type. Theoretically core terms
(emotion, offer_type, emotion:offer_type) were forced to be retained
via buildmer's 'include' argument. Because baseline subtraction was
performed upstream and no baseline covariate is in the model, no
baseline-by-condition interactions are tested.

Note: the primary Alday analysis demonstrated significant emotion-by-
baseline interactions in several components (N170, EPN, LPP_offer in
E2; see companion Methods_paragraph). Under such conditions of
condition-dependent baseline drift, traditional baseline subtraction
imposes a uniform pre-stimulus correction across conditions when the
data require condition-specific weighting (Alday, 2019, Eq. 9-10).
Discrepancies between this sensitivity analysis and the primary Alday
analysis (if any) should be interpreted in light of this
methodological asymmetry.

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

### Stage 2: deliberately not run

Stage 2 (BLUP-based individual-difference correlations) is run only
in the primary Alday analysis. In this sensitivity analysis, Stage 2
is skipped because (a) BLUPs from a model with traditional baseline
subtraction reflect a different latent quantity than BLUPs from the
Alday baseline-as-covariate model and should not be directly compared,
and (b) the purpose of this sensitivity analysis is to verify Stage 1
(fixed-effect) conclusions, not to reanalyze individual differences.
Re-running Stage 2 here would inflate the family-wise FDR burden
without contributing interpretable information.

## Sample

21347 trials from 30 participants entered Stage 1 analysis (E2).

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
Luck, S. J. (2014). An Introduction to the Event-Related Potential
  Technique (2nd ed.). MIT Press.
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
