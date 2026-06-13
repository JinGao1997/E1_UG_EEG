# Stage 1 ANOVA Summary, E1
Generated: 2026-06-09 09:10:14

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

|             |Component  |Status                   |Effect                |APA_Report                          |eta2_partial_95CI    |Sig |Method          |
|:------------|:----------|:------------------------|:---------------------|:-----------------------------------|:--------------------|:---|:---------------|
|FRN_pre.1    |FRN_pre    |confirmatory             |emotion               |F(4, 14142.15) = 1.80, p = 0.126    |0.001 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_pre.2    |FRN_pre    |confirmatory             |offer_type            |F(1, 14142.02) = 0.58, p = 0.447    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_pre.3    |FRN_pre    |confirmatory             |Baseline_c            |F(1, 14154.45) = 12736.82, p < .001 |0.474 [0.463, 0.484] |*** |Satterthwaite F |
|FRN_pre.4    |FRN_pre    |confirmatory             |emotion:offer_type    |F(4, 14142.03) = 0.50, p = 0.736    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|FRN_pre.5    |FRN_pre    |confirmatory             |offer_type:Baseline_c |F(1, 14142.97) = 13.57, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN_pre.6    |FRN_pre    |confirmatory             |emotion:Baseline_c    |F(4, 14143.22) = 4.08, p = 0.003    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|LPP_pre.1    |LPP_pre    |confirmatory             |emotion               |F(4, 14113.64) = 1.13, p = 0.340    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_pre.2    |LPP_pre    |confirmatory             |offer_type            |F(1, 29.12) = 44.43, p < .001       |0.604 [0.359, 0.745] |*** |Satterthwaite F |
|LPP_pre.3    |LPP_pre    |confirmatory             |Baseline_c            |F(1, 14131.93) = 16765.24, p < .001 |0.543 [0.533, 0.552] |*** |Satterthwaite F |
|LPP_pre.4    |LPP_pre    |confirmatory             |emotion:offer_type    |F(4, 14115.49) = 1.40, p = 0.232    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_pre.5    |LPP_pre    |confirmatory             |offer_type:Baseline_c |F(1, 13876.19) = 11.59, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_pre.6    |LPP_pre    |confirmatory             |emotion:Baseline_c    |F(4, 14130.80) = 2.21, p = 0.066    |0.001 [0.000, 0.001] |.   |Satterthwaite F |
|FRN_explor.1 |FRN_explor |exploratory_offer_locked |emotion               |F(4, 14142.13) = 2.65, p = 0.032    |0.001 [0.000, 0.002] |*   |Satterthwaite F |
|FRN_explor.2 |FRN_explor |exploratory_offer_locked |offer_type            |F(1, 14142.01) = 15.06, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN_explor.3 |FRN_explor |exploratory_offer_locked |Baseline_c            |F(1, 14154.09) = 12125.38, p < .001 |0.461 [0.451, 0.472] |*** |Satterthwaite F |
|FRN_explor.4 |FRN_explor |exploratory_offer_locked |emotion:offer_type    |F(4, 14142.03) = 1.33, p = 0.256    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_explor.5 |FRN_explor |exploratory_offer_locked |offer_type:Baseline_c |F(1, 14142.93) = 12.45, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN_explor.6 |FRN_explor |exploratory_offer_locked |emotion:Baseline_c    |F(4, 14142.95) = 2.52, p = 0.039    |0.001 [0.000, 0.002] |*   |Satterthwaite F |
|P3_explor.1  |P3_explor  |exploratory_offer_locked |emotion               |F(4, 14113.46) = 1.08, p = 0.366    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.2  |P3_explor  |exploratory_offer_locked |offer_type            |F(1, 29.04) = 24.02, p < .001       |0.453 [0.182, 0.641] |*** |Satterthwaite F |
|P3_explor.3  |P3_explor  |exploratory_offer_locked |Baseline_c            |F(1, 14130.06) = 11899.54, p < .001 |0.457 [0.446, 0.468] |*** |Satterthwaite F |
|P3_explor.4  |P3_explor  |exploratory_offer_locked |emotion:offer_type    |F(4, 14114.83) = 0.80, p = 0.522    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.5  |P3_explor  |exploratory_offer_locked |offer_type:Baseline_c |F(1, 14059.97) = 12.96, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|P3_explor.6  |P3_explor  |exploratory_offer_locked |emotion:Baseline_c    |F(4, 14128.44) = 2.01, p = 0.091    |0.001 [0.000, 0.001] |.   |Satterthwaite F |
