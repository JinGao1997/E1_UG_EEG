# Stage 1 ANOVA Summary, E2
Generated: 2026-05-05 12:11:11

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

|            |Component |Status              |Effect                |APA_Report                          |eta2_partial_95CI    |Sig |Method          |
|:-----------|:---------|:-------------------|:---------------------|:-----------------------------------|:--------------------|:---|:---------------|
|FRN.1       |FRN       |confirmatory        |emotion               |F(4, 21304.00) = 4.80, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|FRN.2       |FRN       |confirmatory        |offer_type            |F(1, 21304.00) = 2.15, p = 0.143    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|FRN.3       |FRN       |confirmatory        |Baseline_c            |F(1, 21310.20) = 23623.38, p < .001 |0.526 [0.518, 0.534] |*** |Satterthwaite F |
|FRN.4       |FRN       |confirmatory        |emotion:offer_type    |F(4, 21304.01) = 0.69, p = 0.598    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|FRN.5       |FRN       |confirmatory        |emotion:Baseline_c    |F(4, 21304.48) = 1.60, p = 0.171    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N400.1      |N400      |confirmatory        |emotion               |F(4, 21303.00) = 1.07, p = 0.372    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N400.2      |N400      |confirmatory        |offer_type            |F(1, 21303.01) = 46.93, p < .001    |0.002 [0.001, 0.004] |*** |Satterthwaite F |
|N400.3      |N400      |confirmatory        |Baseline_c            |F(1, 21312.20) = 24421.61, p < .001 |0.534 [0.526, 0.542] |*** |Satterthwaite F |
|N400.4      |N400      |confirmatory        |emotion:offer_type    |F(4, 21303.01) = 1.47, p = 0.209    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N400.5      |N400      |confirmatory        |offer_type:Baseline_c |F(1, 21303.56) = 3.66, p = 0.056    |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|N400.6      |N400      |confirmatory        |emotion:Baseline_c    |F(4, 21303.64) = 2.20, p = 0.066    |0.000 [0.000, 0.001] |.   |Satterthwaite F |
|LPP_offer.1 |LPP_offer |confirmatory        |emotion               |F(4, 21274.09) = 6.30, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_offer.2 |LPP_offer |confirmatory        |offer_type            |F(1, 28.92) = 11.67, p = 0.002      |0.287 [0.051, 0.515] |**  |Satterthwaite F |
|LPP_offer.3 |LPP_offer |confirmatory        |Baseline_c            |F(1, 21290.27) = 25038.81, p < .001 |0.540 [0.533, 0.548] |*** |Satterthwaite F |
|LPP_offer.4 |LPP_offer |confirmatory        |emotion:offer_type    |F(4, 21274.00) = 1.42, p = 0.225    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|LPP_offer.5 |LPP_offer |confirmatory        |emotion:Baseline_c    |F(4, 21283.75) = 6.20, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|LPP_offer.6 |LPP_offer |confirmatory        |offer_type:Baseline_c |F(1, 21264.73) = 7.22, p = 0.007    |0.000 [0.000, 0.001] |**  |Satterthwaite F |
|N170.1      |N170      |exploratory_E2_only |emotion               |F(4, 21304.00) = 8.73, p < .001     |0.002 [0.001, 0.003] |*** |Satterthwaite F |
|N170.2      |N170      |exploratory_E2_only |offer_type            |F(1, 21304.00) = 9.04, p = 0.003    |0.000 [0.000, 0.001] |**  |Satterthwaite F |
|N170.3      |N170      |exploratory_E2_only |Baseline_c            |F(1, 21309.00) = 14110.90, p < .001 |0.398 [0.389, 0.407] |*** |Satterthwaite F |
|N170.4      |N170      |exploratory_E2_only |emotion:offer_type    |F(4, 21304.00) = 1.69, p = 0.150    |0.000 [0.000, 0.001] |ns  |Satterthwaite F |
|N170.5      |N170      |exploratory_E2_only |emotion:Baseline_c    |F(4, 21304.23) = 10.09, p < .001    |0.002 [0.001, 0.003] |*** |Satterthwaite F |
|EPN.1       |EPN       |exploratory_E2_only |emotion               |F(4, 21274.11) = 15.29, p < .001    |0.003 [0.001, 0.004] |*** |Satterthwaite F |
|EPN.2       |EPN       |exploratory_E2_only |offer_type            |F(1, 28.85) = 6.04, p = 0.020       |0.173 [0.003, 0.412] |*   |Satterthwaite F |
|EPN.3       |EPN       |exploratory_E2_only |Baseline_c            |F(1, 21291.24) = 13857.63, p < .001 |0.394 [0.385, 0.403] |*** |Satterthwaite F |
|EPN.4       |EPN       |exploratory_E2_only |emotion:offer_type    |F(4, 21273.97) = 0.47, p = 0.758    |0.000 [0.000, 0.000] |ns  |Satterthwaite F |
|EPN.5       |EPN       |exploratory_E2_only |emotion:Baseline_c    |F(4, 21287.25) = 6.67, p < .001     |0.001 [0.000, 0.002] |*** |Satterthwaite F |
|EPN.6       |EPN       |exploratory_E2_only |offer_type:Baseline_c |F(1, 19976.23) = 9.79, p = 0.002    |0.000 [0.000, 0.001] |**  |Satterthwaite F |
