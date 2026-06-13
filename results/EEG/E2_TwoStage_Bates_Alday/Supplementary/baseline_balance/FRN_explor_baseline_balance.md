# Baseline Balance Pre-Check: FRN_explor
Generated: 2026-06-09 09:20:13

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.472

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21308.99) = 0.83, p = 0.504 |0.000 [0.000, 0.000] |ns  | 0.5040|
|offer_type         |F(1, 21309.01) = 0.02, p = 0.890 |0.000 [0.000, 0.000] |ns  | 0.8901|
|emotion:offer_type |F(4, 21309.03) = 0.89, p = 0.472 |0.000 [0.000, 0.000] |ns  | 0.4718|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |        -0.004|       6.818|     2130|
|neu     |unfair     |        -0.231|       6.800|     2134|
|aff     |fair       |        -0.093|       6.389|     2130|
|aff     |unfair     |        -0.058|       6.067|     2134|
|dis     |fair       |         0.058|       6.942|     2130|
|dis     |unfair     |         0.147|       6.373|     2139|
|dom     |fair       |        -0.087|       6.664|     2138|
|dom     |unfair     |         0.128|       6.796|     2137|
|enj     |fair       |         0.160|       7.070|     2141|
|enj     |unfair     |        -0.021|       6.771|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
