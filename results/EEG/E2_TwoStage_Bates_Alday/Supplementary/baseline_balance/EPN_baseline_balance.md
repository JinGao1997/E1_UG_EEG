# Baseline Balance Pre-Check: EPN
Generated: 2026-05-05 12:08:37

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.350

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21309.00) = 1.91, p = 0.106 |0.000 [0.000, 0.001] |ns  | 0.1063|
|offer_type         |F(1, 21309.01) = 1.25, p = 0.264 |0.000 [0.000, 0.000] |ns  | 0.2641|
|emotion:offer_type |F(4, 21309.02) = 1.11, p = 0.350 |0.000 [0.000, 0.001] |ns  | 0.3503|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.082|       6.004|     2130|
|neu     |unfair     |         0.244|       6.398|     2134|
|aff     |fair       |         0.093|       5.770|     2130|
|aff     |unfair     |        -0.025|       5.395|     2134|
|dis     |fair       |        -0.338|       6.338|     2130|
|dis     |unfair     |        -0.042|       5.726|     2139|
|dom     |fair       |         0.047|       5.789|     2138|
|dom     |unfair     |        -0.048|       6.359|     2137|
|enj     |fair       |        -0.113|       6.497|     2141|
|enj     |unfair     |         0.099|       5.728|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
