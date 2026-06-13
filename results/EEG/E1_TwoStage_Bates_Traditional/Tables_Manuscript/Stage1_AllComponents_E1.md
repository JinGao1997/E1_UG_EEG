# Stage 1 ANOVA Summary, E1
Generated: 2026-06-09 09:35:56

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

|             |Component  |Status                   |Effect             |APA_Report                        |eta2_partial_95CI    |Sig |Method          |
|:------------|:----------|:------------------------|:------------------|:---------------------------------|:--------------------|:---|:---------------|
|FRN_pre.1    |FRN_pre    |confirmatory             |emotion            |F(4, 14146.15) = 3.09, p = 0.015  |0.001 [0.000, 0.002] |*   |Satterthwaite F |
|FRN_pre.2    |FRN_pre    |confirmatory             |offer_type         |F(1, 14146.02) = 1.48, p = 0.224  |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_pre.3    |FRN_pre    |confirmatory             |emotion:offer_type |F(4, 14146.03) = 0.41, p = 0.799  |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|LPP_pre.1    |LPP_pre    |confirmatory             |emotion            |F(4, 14117.72) = 1.83, p = 0.120  |0.001 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_pre.2    |LPP_pre    |confirmatory             |offer_type         |F(1, 29.13) = 47.55, p < .001     |0.620 [0.380, 0.756] |*** |Satterthwaite F |
|LPP_pre.3    |LPP_pre    |confirmatory             |emotion:offer_type |F(4, 14119.80) = 1.42, p = 0.224  |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_explor.1 |FRN_explor |exploratory_offer_locked |emotion            |F(4, 14146.13) = 4.06, p = 0.003  |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|FRN_explor.2 |FRN_explor |exploratory_offer_locked |offer_type         |F(1, 14146.02) = 13.69, p < .001  |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN_explor.3 |FRN_explor |exploratory_offer_locked |emotion:offer_type |F(4, 14146.03) = 0.97, p = 0.425  |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.1  |P3_explor  |exploratory_offer_locked |emotion            |F(4, 14146.12) = 1.92, p = 0.105  |0.001 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.2  |P3_explor  |exploratory_offer_locked |offer_type         |F(1, 14146.01) = 106.90, p < .001 |0.008 [0.005, 0.011] |*** |Satterthwaite F |
|P3_explor.3  |P3_explor  |exploratory_offer_locked |emotion:offer_type |F(4, 14146.02) = 1.25, p = 0.288  |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
