# Baseline Balance Pre-Check: LPP_offer
Generated: 2026-05-05 13:27:49

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.346

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 14148.63) = 2.27, p = 0.059 |0.001 [0.000, 0.001] |.   | 0.0589|
|offer_type         |F(1, 14148.05) = 0.52, p = 0.472 |0.000 [0.000, 0.001] |ns  | 0.4718|
|emotion:offer_type |F(4, 14148.11) = 1.12, p = 0.346 |0.000 [0.000, 0.001] |ns  | 0.3458|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.096|       6.636|     1416|
|neu     |unfair     |         0.174|       5.714|     1424|
|aff     |fair       |        -0.107|       6.632|     1425|
|aff     |unfair     |        -0.047|       6.229|     1416|
|dis     |fair       |        -0.012|       6.296|     1421|
|dis     |unfair     |        -0.351|       6.789|     1419|
|dom     |fair       |         0.155|       5.607|     1418|
|dom     |unfair     |         0.419|       6.554|     1418|
|enj     |fair       |        -0.133|       6.118|     1418|
|enj     |unfair     |        -0.002|       7.253|     1412|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
