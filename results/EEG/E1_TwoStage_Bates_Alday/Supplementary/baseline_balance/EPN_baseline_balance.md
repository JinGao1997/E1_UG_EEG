# Baseline Balance Pre-Check: EPN
Generated: 2026-05-05 13:28:33

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.636

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.36) = 2.47, p = 0.042 |0.001 [0.000, 0.002] |*   | 0.0424|
|offer_type         |F(1, 14148.04) = 1.47, p = 0.225 |0.000 [0.000, 0.001] |ns  | 0.2251|
|emotion:offer_type |F(4, 14148.07) = 0.64, p = 0.636 |0.000 [0.000, 0.001] |ns  | 0.6357|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.099|       5.164|     1416|
|neu     |unfair     |        -0.097|       5.485|     1424|
|aff     |fair       |         0.108|       5.919|     1425|
|aff     |unfair     |         0.064|       5.643|     1416|
|dis     |fair       |         0.252|       5.438|     1421|
|dis     |unfair     |        -0.015|       5.015|     1419|
|dom     |fair       |        -0.261|       5.245|     1418|
|dom     |unfair     |        -0.209|       5.182|     1418|
|enj     |fair       |         0.279|       5.721|     1418|
|enj     |unfair     |        -0.023|       6.372|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
