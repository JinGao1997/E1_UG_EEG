# Stage 1 ANOVA Summary, E2
Generated: 2026-05-04 16:37:33

Type III ANOVA tests. LMM analyses use a Satterthwaite -> 
Kenward-Roger -> Wald cascade (lmerTest, pbkrtest, car). All EEG
analyses are LMM (Gaussian on amplitude); GLMM is not used.
Component Status indicates confirmatory (present in both E1 and
E2) vs exploratory (E2-only or E1 offer-locked).

## Methods used per component:
- FRN: Satterthwaite F
- N400: Satterthwaite F
- LPP_offer: Satterthwaite F
- N170: Satterthwaite F
- EPN: Satterthwaite F

Table: Stage 1 fixed-effect tests across 5 ERP components.

|            |Component |Status              |Effect             |APA_Report                       |eta2_partial_95CI    |Sig |Method          |
|:-----------|:---------|:-------------------|:------------------|:--------------------------------|:--------------------|:---|:---------------|
|FRN.1       |FRN       |confirmatory        |emotion            |F(4, 21308.00) = 3.38, p = 0.009 |0.001 [0.000, 0.001] |**  |Satterthwaite F |
|FRN.2       |FRN       |confirmatory        |offer_type         |F(1, 21308.01) = 2.17, p = 0.141 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN.3       |FRN       |confirmatory        |emotion:offer_type |F(4, 21308.01) = 0.64, p = 0.634 |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|N400.1      |N400      |confirmatory        |emotion            |F(4, 21279.24) = 1.23, p = 0.297 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N400.2      |N400      |confirmatory        |offer_type         |F(1, 28.89) = 13.11, p = 0.001   |0.312 [0.066, 0.535] |**  |Satterthwaite F |
|N400.3      |N400      |confirmatory        |emotion:offer_type |F(4, 21279.03) = 0.94, p = 0.440 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_offer.1 |LPP_offer |confirmatory        |emotion            |F(4, 21279.11) = 5.57, p < .001  |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_offer.2 |LPP_offer |confirmatory        |offer_type         |F(1, 28.92) = 11.03, p = 0.002   |0.276 [0.044, 0.505] |**  |Satterthwaite F |
|LPP_offer.3 |LPP_offer |confirmatory        |emotion:offer_type |F(4, 21279.00) = 0.51, p = 0.729 |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|N170.1      |N170      |exploratory_E2_only |emotion            |F(4, 21308.00) = 6.23, p < .001  |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|N170.2      |N170      |exploratory_E2_only |offer_type         |F(1, 21308.00) = 7.13, p = 0.008 |0.000 [0.000, 0.001] |**  |Satterthwaite F |
|N170.3      |N170      |exploratory_E2_only |emotion:offer_type |F(4, 21308.00) = 1.27, p = 0.277 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|EPN.1       |EPN       |exploratory_E2_only |emotion            |F(4, 21279.11) = 10.62, p < .001 |0.002 [0.001, 0.003] |*** |Satterthwaite F |
|EPN.2       |EPN       |exploratory_E2_only |offer_type         |F(1, 28.88) = 5.07, p = 0.032    |0.149 [0.000, 0.388] |*   |Satterthwaite F |
|EPN.3       |EPN       |exploratory_E2_only |emotion:offer_type |F(4, 21278.93) = 0.41, p = 0.799 |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
