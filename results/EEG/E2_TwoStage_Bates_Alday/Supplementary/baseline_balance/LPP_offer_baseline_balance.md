# Baseline Balance Pre-Check: LPP_offer
Generated: 2026-05-19 09:56:33

## Purpose
Diagnostic test of whether mean baseline amplitude differs across
emotion x offer_type cells. PURE DIAGNOSTIC: does NOT gate or modify
the main analysis. The Alday baseline-as-covariate framework allows
baseline-condition interactions and tests them in the main model.

## Test
Model: Baseline_c ~ emotion * offer_type + (1 | participant_id)

Omnibus emotion:offer_type interaction: p = 0.236

## Type III ANOVA
|Effect             |APA_Report                       |eta2_partial_95CI    |Sig |  p_val|
|:------------------|:--------------------------------|:--------------------|:---|------:|
|emotion            |F(4, 21308.97) = 0.39, p = 0.817 |0.000 [0.000, 0.000] |ns  | 0.8171|
|offer_type         |F(1, 21308.99) = 0.13, p = 0.721 |0.000 [0.000, 0.000] |ns  | 0.7212|
|emotion:offer_type |F(4, 21309.02) = 1.39, p = 0.236 |0.000 [0.000, 0.001] |ns  | 0.2359|

## Cell means (microvolts)
|emotion |offer_type | mean_baseline| sd_baseline| n_trials|
|:-------|:----------|-------------:|-----------:|--------:|
|neu     |fair       |         0.088|       6.850|     2130|
|neu     |unfair     |        -0.284|       6.658|     2134|
|aff     |fair       |         0.020|       6.453|     2130|
|aff     |unfair     |         0.135|       6.161|     2134|
|dis     |fair       |        -0.028|       7.277|     2130|
|dis     |unfair     |         0.010|       6.384|     2139|
|dom     |fair       |        -0.092|       6.752|     2138|
|dom     |unfair     |         0.126|       6.707|     2137|
|enj     |fair       |         0.096|       7.307|     2141|
|enj     |unfair     |        -0.070|       6.449|     2135|

## Interpretation
If interaction p > 0.05: baseline is balanced across conditions; no
concern. If p < 0.05: condition-dependent baseline detected. The main
analysis tests Baseline_c:emotion and Baseline_c:offer_type
interactions in fit_stage1_bates Step 3 (LRT-based inclusion); a
significant baseline-condition coupling will be retained automatically
in the final model and reported in REPRODUCIBILITY.txt.
