# Stage 1 ANOVA Summary, E1
Generated: 2026-05-19 11:47:58

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

|            |Component |Status                   |Effect                |APA_Report                          |eta2_partial_95CI    |Sig |Method          |
|:-----------|:---------|:------------------------|:---------------------|:-----------------------------------|:--------------------|:---|:---------------|
|FRN.1       |FRN       |confirmatory             |emotion               |F(4, 14142.14) = 1.70, p = 0.148    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN.2       |FRN       |confirmatory             |offer_type            |F(1, 14142.01) = 0.48, p = 0.489    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|FRN.3       |FRN       |confirmatory             |Baseline_c            |F(1, 14154.16) = 12732.31, p < .001 |0.474 [0.463, 0.484] |*** |Satterthwaite F |
|FRN.4       |FRN       |confirmatory             |emotion:offer_type    |F(4, 14142.03) = 0.42, p = 0.791    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|FRN.5       |FRN       |confirmatory             |offer_type:Baseline_c |F(1, 14142.95) = 12.94, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN.6       |FRN       |confirmatory             |emotion:Baseline_c    |F(4, 14143.18) = 4.08, p = 0.003    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|N400.1      |N400      |confirmatory             |emotion               |F(4, 14146.10) = 4.26, p = 0.002    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|N400.2      |N400      |confirmatory             |offer_type            |F(1, 14146.00) = 105.67, p < .001   |0.007 [0.005, 0.010] |*** |Satterthwaite F |
|N400.3      |N400      |confirmatory             |Baseline_c            |F(1, 14154.04) = 15706.66, p < .001 |0.526 [0.516, 0.536] |*** |Satterthwaite F |
|N400.4      |N400      |confirmatory             |emotion:offer_type    |F(4, 14146.01) = 1.76, p = 0.134    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N400.5      |N400      |confirmatory             |offer_type:Baseline_c |F(1, 14146.46) = 12.69, p < .001    |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_offer.1 |LPP_offer |confirmatory             |emotion               |F(4, 14142.13) = 0.84, p = 0.498    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_offer.2 |LPP_offer |confirmatory             |offer_type            |F(1, 14142.00) = 38.43, p < .001    |0.003 [0.001, 0.005] |*** |Satterthwaite F |
|LPP_offer.3 |LPP_offer |confirmatory             |Baseline_c            |F(1, 14153.48) = 15131.75, p < .001 |0.517 [0.507, 0.526] |*** |Satterthwaite F |
|LPP_offer.4 |LPP_offer |confirmatory             |emotion:offer_type    |F(4, 14142.01) = 2.06, p = 0.083    |0.001 [0.000, 0.001] |.   |Satterthwaite F |
|LPP_offer.5 |LPP_offer |confirmatory             |offer_type:Baseline_c |F(1, 14142.54) = 16.38, p < .001    |0.001 [0.000, 0.003] |*** |Satterthwaite F |
|LPP_offer.6 |LPP_offer |confirmatory             |emotion:Baseline_c    |F(4, 14143.13) = 4.54, p = 0.001    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
|EPN.1       |EPN       |exploratory_offer_locked |emotion               |F(4, 14142.06) = 4.86, p < .001     |0.001 [0.000, 0.003] |*** |Satterthwaite F |
|EPN.2       |EPN       |exploratory_offer_locked |offer_type            |F(1, 14142.00) = 0.60, p = 0.440    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|EPN.3       |EPN       |exploratory_offer_locked |Baseline_c            |F(1, 14152.44) = 8941.24, p < .001  |0.387 [0.376, 0.398] |*** |Satterthwaite F |
|EPN.4       |EPN       |exploratory_offer_locked |emotion:offer_type    |F(4, 14142.00) = 1.50, p = 0.198    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|EPN.5       |EPN       |exploratory_offer_locked |emotion:Baseline_c    |F(4, 14142.62) = 8.28, p < .001     |0.002 [0.001, 0.004] |*** |Satterthwaite F |
|EPN.6       |EPN       |exploratory_offer_locked |offer_type:Baseline_c |F(1, 14142.29) = 9.34, p = 0.002    |0.001 [0.000, 0.002] |**  |Satterthwaite F |
