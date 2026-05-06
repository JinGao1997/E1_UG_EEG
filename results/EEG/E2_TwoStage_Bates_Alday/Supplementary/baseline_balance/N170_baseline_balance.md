# Baseline Balance Pre-Check: N170
Generated: 2026-05-05 12:06:31

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.721

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21309.02) = 1.47, p = 0.210 |0.000 [0.000, 0.001] |ns  | 0.2097|
|offer_type         |F(1, 21309.02) = 0.94, p = 0.332 |0.000 [0.000, 0.000] |ns  | 0.3321|
|emotion:offer_type |F(4, 21309.03) = 0.52, p = 0.721 |0.000 [0.000, 0.000] |ns  | 0.7212|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.087|       5.440|     2130|
|neu     |unfair     |         0.241|       6.323|     2134|
|aff     |fair       |         0.022|       5.506|     2130|
|aff     |unfair     |        -0.051|       5.092|     2134|
|dis     |fair       |        -0.222|       5.470|     2130|
|dis     |unfair     |        -0.037|       5.511|     2139|
|dom     |fair       |         0.016|       5.700|     2138|
|dom     |unfair     |        -0.026|       5.969|     2137|
|enj     |fair       |        -0.091|       6.293|     2141|
|enj     |unfair     |         0.063|       5.764|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
