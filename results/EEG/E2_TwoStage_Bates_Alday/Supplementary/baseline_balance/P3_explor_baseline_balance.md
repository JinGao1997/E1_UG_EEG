# Baseline Balance Pre-Check: P3_explor
Generated: 2026-06-09 09:21:26

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.253

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21308.98) = 0.62, p = 0.651 |0.000 [0.000, 0.000] |ns  | 0.6512|
|offer_type         |F(1, 21309.00) = 0.19, p = 0.667 |0.000 [0.000, 0.000] |ns  | 0.6666|
|emotion:offer_type |F(4, 21309.02) = 1.34, p = 0.253 |0.000 [0.000, 0.001] |ns  | 0.2530|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.122|       7.148|     2130|
|neu     |unfair     |        -0.294|       7.040|     2134|
|aff     |fair       |         0.073|       6.718|     2130|
|aff     |unfair     |         0.181|       6.481|     2134|
|dis     |fair       |        -0.079|       7.514|     2130|
|dis     |unfair     |        -0.044|       6.725|     2139|
|dom     |fair       |        -0.083|       7.054|     2138|
|dom     |unfair     |         0.117|       7.062|     2137|
|enj     |fair       |         0.071|       7.546|     2141|
|enj     |unfair     |        -0.063|       6.844|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
