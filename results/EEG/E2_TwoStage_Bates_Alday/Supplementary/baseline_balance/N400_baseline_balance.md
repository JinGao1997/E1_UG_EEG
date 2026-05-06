# Baseline Balance Pre-Check: N400
Generated: 2026-05-05 12:03:01

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.295

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21309.00) = 0.30, p = 0.880 |0.000 [0.000, 0.000] |ns  | 0.8803|
|offer_type         |F(1, 21309.01) = 0.21, p = 0.647 |0.000 [0.000, 0.000] |ns  | 0.6473|
|emotion:offer_type |F(4, 21309.04) = 1.23, p = 0.295 |0.000 [0.000, 0.001] |ns  | 0.2946|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.177|       7.282|     2130|
|neu     |unfair     |        -0.239|       7.203|     2134|
|aff     |fair       |         0.075|       6.835|     2130|
|aff     |unfair     |         0.092|       6.543|     2134|
|dis     |fair       |        -0.125|       7.632|     2130|
|dis     |unfair     |        -0.020|       6.788|     2139|
|dom     |fair       |        -0.075|       7.205|     2138|
|dom     |unfair     |         0.113|       7.169|     2137|
|enj     |fair       |         0.061|       7.659|     2141|
|enj     |unfair     |        -0.059|       7.081|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
