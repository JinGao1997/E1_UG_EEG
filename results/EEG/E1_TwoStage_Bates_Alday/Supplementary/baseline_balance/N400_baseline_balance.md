# Baseline Balance Pre-Check: N400
Generated: 2026-05-05 13:25:41

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.415

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.73) = 2.84, p = 0.023 |0.001 [0.000, 0.002] |*   | 0.0228|
|offer_type         |F(1, 14148.07) = 0.02, p = 0.881 |0.000 [0.000, 0.000] |ns  | 0.8811|
|emotion:offer_type |F(4, 14148.14) = 0.98, p = 0.415 |0.000 [0.000, 0.001] |ns  | 0.4146|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.106|       7.273|     1416|
|neu     |unfair     |         0.212|       6.168|     1424|
|aff     |fair       |        -0.052|       7.072|     1425|
|aff     |unfair     |        -0.125|       6.825|     1416|
|dis     |fair       |        -0.061|       6.785|     1421|
|dis     |unfair     |        -0.399|       7.340|     1419|
|dom     |fair       |         0.245|       6.037|     1418|
|dom     |unfair     |         0.439|       7.080|     1418|
|enj     |fair       |        -0.069|       6.604|     1418|
|enj     |unfair     |        -0.083|       7.842|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
