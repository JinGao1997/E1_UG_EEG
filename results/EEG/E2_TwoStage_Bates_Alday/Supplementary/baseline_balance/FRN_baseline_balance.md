# Baseline Balance Pre-Check: FRN
Generated: 2026-05-19 09:52:46

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.619

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21308.98) = 1.43, p = 0.221 |0.000 [0.000, 0.001] |ns  | 0.2210|
|offer_type         |F(1, 21308.99) = 0.02, p = 0.901 |0.000 [0.000, 0.000] |ns  | 0.9006|
|emotion:offer_type |F(4, 21309.01) = 0.66, p = 0.619 |0.000 [0.000, 0.000] |ns  | 0.6188|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.025|       5.910|     2130|
|neu     |unfair     |        -0.188|       6.149|     2134|
|aff     |fair       |        -0.125|       5.717|     2130|
|aff     |unfair     |        -0.038|       5.264|     2134|
|dis     |fair       |         0.175|       6.022|     2130|
|dis     |unfair     |         0.145|       5.634|     2139|
|dom     |fair       |        -0.111|       5.841|     2138|
|dom     |unfair     |         0.061|       6.072|     2137|
|enj     |fair       |         0.113|       6.304|     2141|
|enj     |unfair     |        -0.008|       5.985|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
