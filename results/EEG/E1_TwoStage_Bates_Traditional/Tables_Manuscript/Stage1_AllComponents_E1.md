# Stage 1 ANOVA Summary, E1
Generated: 2026-05-04 16:19:33

Type III ANOVA tests. LMM analyses use a Satterthwaite -> 
Kenward-Roger -> Wald cascade (lmerTest, pbkrtest, car). All EEG
analyses are LMM (Gaussian on amplitude); GLMM is not used.
Component Status indicates confirmatory (present in both E1 and
E2) vs exploratory (E2-only or E1 offer-locked).

## Methods used per component:
- FRN: Satterthwaite F
- N400: Satterthwaite F
- LPP_offer: Satterthwaite F
- EPN: Satterthwaite F

Table: Stage 1 fixed-effect tests across 4 ERP components.

|            |Component |Status                   |Effect             |APA_Report                       |eta2_partial_95CI    |Sig |Method          |
|:-----------|:---------|:------------------------|:------------------|:--------------------------------|:--------------------|:---|:---------------|
|FRN.1       |FRN       |confirmatory             |emotion            |F(4, 14146.15) = 2.94, p = 0.019 |0.001 [0.000, 0.002] |*   |Satterthwaite F |
|FRN.2       |FRN       |confirmatory             |offer_type         |F(1, 14146.02) = 1.35, p = 0.245 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN.3       |FRN       |confirmatory             |emotion:offer_type |F(4, 14146.03) = 0.36, p = 0.838 |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|N400.1      |N400      |confirmatory             |emotion            |F(4, 14118.10) = 3.59, p = 0.006 |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|N400.2      |N400      |confirmatory             |offer_type         |F(1, 29.33) = 52.49, p < .001    |0.642 [0.411, 0.770] |*** |Satterthwaite F |
|N400.3      |N400      |confirmatory             |emotion:offer_type |F(4, 14121.28) = 2.01, p = 0.091 |0.001 [0.000, 0.001] |.   |Satterthwaite F |
|LPP_offer.1 |LPP_offer |confirmatory             |emotion            |F(4, 14117.58) = 2.31, p = 0.055 |0.001 [0.000, 0.001] |.   |Satterthwaite F |
|LPP_offer.2 |LPP_offer |confirmatory             |offer_type         |F(1, 29.08) = 8.65, p = 0.006    |0.229 [0.022, 0.464] |**  |Satterthwaite F |
|LPP_offer.3 |LPP_offer |confirmatory             |emotion:offer_type |F(4, 14119.10) = 2.52, p = 0.039 |0.001 [0.000, 0.002] |*   |Satterthwaite F |
|EPN.1       |EPN       |exploratory_offer_locked |emotion            |F(4, 14146.07) = 5.48, p < .001  |0.002 [0.000, 0.003] |*** |Satterthwaite F |
|EPN.2       |EPN       |exploratory_offer_locked |offer_type         |F(1, 14146.01) = 1.25, p = 0.263 |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|EPN.3       |EPN       |exploratory_offer_locked |emotion:offer_type |F(4, 14146.02) = 1.96, p = 0.098 |0.001 [0.000, 0.001] |.   |Satterthwaite F |
