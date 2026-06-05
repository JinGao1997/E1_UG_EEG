# Methods Paragraph (Behavioral Analyses, Stage E2)

Experiment E2 (single-experiment analyses)

Generated: 2026-05-20 11:33:32

## Statistical Analysis

Behavioral data were analyzed using mixed-effects models in R (4.3.3) with the
lme4 (1.1.38) and lmerTest (3.1.3) packages, with binomial models fitted via glmmTMB
(1.1.14). Categorical predictors used sum-to-zero contrasts (R option contr.sum)
to support valid Type III tests in the presence of interactions (Schad,
Vasishth, Hohenstein, & Kliegl, 2020). Trials were excluded if the
participant did not respond (reaction = 0), if response time fell outside
300-3000 ms, or if the offer was the medium-fairness filler (Offers_Other = 7).

Models fitted in this stage:

1. **Rejection rate (GLMM_rejection):** binomial mixed-effects model on reject_binary
   with predictors emotion (5 levels) x offer type (fair, unfair) and their interaction.

2. **Response time, main analysis (LMM_RT_main):** linear mixed-effects model on
   log RT with predictors emotion x offer type and their interaction. Reaction was
   deliberately NOT included as a covariate (collider; Rohrer, 2018).

3. **Response time, unfair-only (LMM_RT_unfair):** linear mixed-effects model
   on log RT restricted to unfair trials, with predictors emotion x reaction
   and their interaction. This stratum parallels HDDM decision-dynamics
   modeling.

### Random-effects structure

Random-effects structures were selected following the parsimonious-Bates
protocol (Bates, Kliegl, Vasishth, & Baayen, 2015; Matuschek, Kliegl,
Vasishth, Baayen, & Bates, 2017). Starting from the design-justified maximal
model (random intercepts and slopes for within-subject factors by
participant), zero-correlation parameter (ZCP) models were fitted, then
non-supported variance components were removed via likelihood-ratio tests
with elimination alpha = 0.20 using the buildmer package. Correlation
parameters between surviving slopes were tested in a final step.
Random-effects dimensionality was diagnosed via rePCA (Bates et al., 2015).

For the Integrative analysis, Experiment was modeled as a between-subjects
factor (each participant belongs to exactly one experiment). Random slopes
for Experiment by participant are unidentifiable by design and were
therefore not included. Participant ids were prefixed by the experiment
label ("E1_", "E2_") to guarantee uniqueness across experiments.

Stimulus identity was counterbalanced across participants via a Latin-square
design and was not modeled as a separate random effect (cf. Westfall, Kenny,
& Judd, 2014).

### Inferential strategy

For linear mixed models, fixed-effect inference used a Type III F-test with
denominator degrees of freedom approximated via a cascading method
preference: Satterthwaite (Kuznetsova, Brockhoff, & Christensen, 2017;
Luke, 2017) was attempted first; on numerical failure, Kenward-Roger
(Kenward & Roger, 1997; via the pbkrtest backend) was attempted; Wald
chi-square (car::Anova) was used only as a final fallback. The method
actually used per analysis is reported in the supplementary REPRODUCIBILITY
log. For the binomial model, Wald chi-square tests were used because
Satterthwaite and Kenward-Roger are not defined for non-Gaussian
likelihoods (the residual variance term they require does not exist in
binomial likelihoods, where Var(y) is determined by the mean structure as
p(1-p)).

Post-hoc contrasts were computed using the emmeans package (Lenth, 2024)
with asymptotic standard errors and false-discovery-rate (FDR) correction
within each effect family.

### Effect-size reporting

For Gaussian models, partial eta-squared with 95% confidence intervals are
reported alongside F-tests (effectsize::eta_squared). For the binomial
model, partial eta-squared is not defined; odds ratios with 95% CIs are
reported for fixed-effect contrasts, and marginal/conditional R-squared
(Nakagawa-Schielzeth, 2013) are reported for overall model fit. For
log-RT contrasts, percent RT change is reported as (exp(b) - 1) x 100.

### Post-hoc gating

For 2-way analyses (single-experiment stages E1 and E2), simple-effect
decompositions of the emotion x offer_type (or emotion x reaction)
interaction were performed only when the omnibus interaction p < 0.05.
Effects with 0.05 <= p < 0.10 were computed but reported only in
supplementary materials, never as confirmatory evidence.

For 3-way analyses (Integrative stage), decomposition was layered:
(a) if the 3-way Experiment x emotion x within-factor interaction was
significant (p < 0.05), simple effects were decomposed per Experiment;
(b) if 0.05 <= 3-way p < 0.10, the same decomposition was performed but
written to Supplementary; (c) if the 3-way was not significant, each 2-way
interaction was evaluated independently and main effects reported only for
factors not participating in any significant 2-way interaction.

## Sample

21477 trials from 30 unique participants entered the main analyses in this stage;
the unfair-only stratum included 10737 trials.


