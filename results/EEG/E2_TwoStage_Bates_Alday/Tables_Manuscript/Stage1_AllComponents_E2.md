# Stage 1 ANOVA Summary, E2
Generated: 2026-06-09 09:23:24

Type III ANOVA tests. LMM analyses use a Satterthwaite -> 
Kenward-Roger -> Wald cascade (lmerTest, pbkrtest, car). All EEG
analyses are LMM (Gaussian on amplitude); GLMM is not used.
Component Status indicates confirmatory (present in both E1 and
E2) vs exploratory (E2-only or E1 offer-locked).

## Methods used per component:
- FRN_pre: Satterthwaite F
- LPP_pre: Satterthwaite F
- FRN_explor: Satterthwaite F
- P3_explor: Satterthwaite F

Table: Stage 1 fixed-effect tests across 4 ERP components.

|             |Component  |Status              |Effect                |APA_Report                          |eta2_partial_95CI    |Sig |Method          |
|:------------|:----------|:-------------------|:---------------------|:-----------------------------------|:--------------------|:---|:---------------|
|FRN_pre.1    |FRN_pre    |confirmatory        |emotion               |F(4, 21308.00) = 4.47, p = 0.001    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|FRN_pre.2    |FRN_pre    |confirmatory        |offer_type            |F(1, 21308.00) = 2.05, p = 0.152    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_pre.3    |FRN_pre    |confirmatory        |Baseline_c            |F(1, 21314.10) = 24492.35, p < .001 |0.535 [0.527, 0.542] |*** |Satterthwaite F |
|FRN_pre.4    |FRN_pre    |confirmatory        |emotion:offer_type    |F(4, 21308.01) = 0.89, p = 0.471    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|LPP_pre.1    |LPP_pre    |confirmatory        |emotion               |F(4, 21274.04) = 5.35, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_pre.2    |LPP_pre    |confirmatory        |offer_type            |F(1, 28.88) = 25.77, p < .001       |0.472 [0.201, 0.655] |*** |Satterthwaite F |
|LPP_pre.3    |LPP_pre    |confirmatory        |Baseline_c            |F(1, 21288.51) = 27644.45, p < .001 |0.565 [0.557, 0.572] |*** |Satterthwaite F |
|LPP_pre.4    |LPP_pre    |confirmatory        |emotion:offer_type    |F(4, 21273.95) = 2.36, p = 0.051    |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|LPP_pre.5    |LPP_pre    |confirmatory        |emotion:Baseline_c    |F(4, 21282.75) = 6.19, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_pre.6    |LPP_pre    |confirmatory        |offer_type:Baseline_c |F(1, 21281.24) = 4.12, p = 0.042    |0.000 [0.000, 0.001] |*   |Satterthwaite F |
|FRN_explor.1 |FRN_explor |exploratory_E2_only |emotion               |F(4, 21303.01) = 1.76, p = 0.134    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_explor.2 |FRN_explor |exploratory_E2_only |offer_type            |F(1, 21303.01) = 29.04, p < .001    |0.001 [0.001, 0.003] |*** |Satterthwaite F |
|FRN_explor.3 |FRN_explor |exploratory_E2_only |Baseline_c            |F(1, 21312.43) = 21713.97, p < .001 |0.505 [0.496, 0.513] |*** |Satterthwaite F |
|FRN_explor.4 |FRN_explor |exploratory_E2_only |emotion:offer_type    |F(4, 21303.01) = 1.78, p = 0.130    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_explor.5 |FRN_explor |exploratory_E2_only |offer_type:Baseline_c |F(1, 21303.44) = 3.15, p = 0.076    |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|FRN_explor.6 |FRN_explor |exploratory_E2_only |emotion:Baseline_c    |F(4, 21303.81) = 1.67, p = 0.153    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.1  |P3_explor  |exploratory_E2_only |emotion               |F(4, 21274.03) = 7.28, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|P3_explor.2  |P3_explor  |exploratory_E2_only |offer_type            |F(1, 28.89) = 27.69, p < .001       |0.489 [0.220, 0.667] |*** |Satterthwaite F |
|P3_explor.3  |P3_explor  |exploratory_E2_only |Baseline_c            |F(1, 21291.06) = 20026.92, p < .001 |0.485 [0.476, 0.493] |*** |Satterthwaite F |
|P3_explor.4  |P3_explor  |exploratory_E2_only |emotion:offer_type    |F(4, 21273.96) = 1.97, p = 0.095    |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|P3_explor.5  |P3_explor  |exploratory_E2_only |emotion:Baseline_c    |F(4, 21282.83) = 5.60, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|P3_explor.6  |P3_explor  |exploratory_E2_only |offer_type:Baseline_c |F(1, 21280.03) = 1.73, p = 0.189    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
