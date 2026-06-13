# Baseline Balance Pre-Check: FRN_explor
Generated: 2026-06-09 09:07:49

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.699

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.48) = 3.28, p = 0.011 |0.001 [0.000, 0.002] |*   | 0.0106|
|offer_type         |F(1, 14148.01) = 0.83, p = 0.363 |0.000 [0.000, 0.001] |ns  | 0.3634|
|emotion:offer_type |F(4, 14148.06) = 0.55, p = 0.699 |0.000 [0.000, 0.001] |ns  | 0.6995|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.177|       6.215|     1416|
|neu     |unfair     |         0.221|       5.506|     1424|
|aff     |fair       |         0.013|       6.388|     1425|
|aff     |unfair     |         0.004|       5.989|     1416|
|dis     |fair       |        -0.243|       6.082|     1421|
|dis     |unfair     |        -0.329|       6.224|     1419|
|dom     |fair       |         0.073|       5.455|     1418|
|dom     |unfair     |         0.265|       6.051|     1418|
|enj     |fair       |        -0.254|       5.761|     1418|
|enj     |unfair     |         0.073|       7.072|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
