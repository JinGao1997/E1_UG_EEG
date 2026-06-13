# Baseline Balance Pre-Check: FRN_pre
Generated: 2026-06-09 09:06:23

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.779

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.53) = 3.59, p = 0.006 |0.001 [0.000, 0.002] |**  | 0.0062|
|offer_type         |F(1, 14148.03) = 1.07, p = 0.302 |0.000 [0.000, 0.001] |ns  | 0.3020|
|emotion:offer_type |F(4, 14148.08) = 0.44, p = 0.779 |0.000 [0.000, 0.000] |ns  | 0.7785|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.167|       5.464|     1416|
|neu     |unfair     |         0.231|       4.898|     1424|
|aff     |fair       |         0.022|       5.749|     1425|
|aff     |unfair     |         0.001|       5.337|     1416|
|dis     |fair       |        -0.259|       5.328|     1421|
|dis     |unfair     |        -0.273|       5.402|     1419|
|dom     |fair       |         0.067|       4.817|     1418|
|dom     |unfair     |         0.210|       5.315|     1418|
|enj     |fair       |        -0.232|       5.120|     1418|
|enj     |unfair     |         0.065|       6.352|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
