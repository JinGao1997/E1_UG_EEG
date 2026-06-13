# Baseline Balance Pre-Check: P3_explor
Generated: 2026-06-09 09:08:26

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.396

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.70) = 2.75, p = 0.027 |0.001 [0.000, 0.002] |*   | 0.0266|
|offer_type         |F(1, 14148.07) = 0.04, p = 0.838 |0.000 [0.000, 0.000] |ns  | 0.8385|
|emotion:offer_type |F(4, 14148.14) = 1.02, p = 0.396 |0.000 [0.000, 0.001] |ns  | 0.3958|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.094|       6.899|     1416|
|neu     |unfair     |         0.161|       5.978|     1424|
|aff     |fair       |        -0.106|       6.789|     1425|
|aff     |unfair     |        -0.145|       6.501|     1416|
|dis     |fair       |        -0.018|       6.580|     1421|
|dis     |unfair     |        -0.368|       7.064|     1419|
|dom     |fair       |         0.210|       5.849|     1418|
|dom     |unfair     |         0.454|       6.787|     1418|
|enj     |fair       |        -0.049|       6.336|     1418|
|enj     |unfair     |        -0.046|       7.537|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
