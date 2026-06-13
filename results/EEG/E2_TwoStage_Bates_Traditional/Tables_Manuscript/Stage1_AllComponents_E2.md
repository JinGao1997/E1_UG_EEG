# Stage 1 ANOVA Summary, E2
Generated: 2026-06-09 09:48:54

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

|             |Component  |Status              |Effect             |APA_Report                       |eta2_partial_95CI    |Sig |Method          |
|:------------|:----------|:-------------------|:------------------|:--------------------------------|:--------------------|:---|:---------------|
|FRN_pre.1    |FRN_pre    |confirmatory        |emotion            |F(4, 21308.00) = 3.06, p = 0.016 |0.001 [0.000, 0.001] |*   |Satterthwaite F |
|FRN_pre.2    |FRN_pre    |confirmatory        |offer_type         |F(1, 21308.01) = 1.98, p = 0.159 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_pre.3    |FRN_pre    |confirmatory        |emotion:offer_type |F(4, 21308.01) = 0.82, p = 0.515 |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|LPP_pre.1    |LPP_pre    |confirmatory        |emotion            |F(4, 21279.04) = 4.90, p < .001  |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_pre.2    |LPP_pre    |confirmatory        |offer_type         |F(1, 28.88) = 24.38, p < .001    |0.458 [0.186, 0.645] |*** |Satterthwaite F |
|LPP_pre.3    |LPP_pre    |confirmatory        |emotion:offer_type |F(4, 21278.94) = 1.34, p = 0.253 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN_explor.1 |FRN_explor |exploratory_E2_only |emotion            |F(4, 21279.27) = 2.01, p = 0.091 |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|FRN_explor.2 |FRN_explor |exploratory_E2_only |offer_type         |F(1, 28.88) = 9.50, p = 0.004    |0.247 [0.030, 0.481] |**  |Satterthwaite F |
|FRN_explor.3 |FRN_explor |exploratory_E2_only |emotion:offer_type |F(4, 21279.03) = 1.67, p = 0.155 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|P3_explor.1  |P3_explor  |exploratory_E2_only |emotion            |F(4, 21279.04) = 7.56, p < .001  |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|P3_explor.2  |P3_explor  |exploratory_E2_only |offer_type         |F(1, 28.89) = 26.50, p < .001    |0.478 [0.208, 0.660] |*** |Satterthwaite F |
|P3_explor.3  |P3_explor  |exploratory_E2_only |emotion:offer_type |F(4, 21278.95) = 1.35, p = 0.249 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
