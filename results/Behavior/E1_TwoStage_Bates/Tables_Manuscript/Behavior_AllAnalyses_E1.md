# Behavioral Analysis Summary, E1
Generated: 2026-05-04 10:13:26

Type III ANOVA tests. LMM analyses use a Satterthwaite -> 
Kenward-Roger -> Wald cascade (lmerTest, pbkrtest, car). GLMM 
analyses use Wald chi-square (car::Anova) as the only valid 
method (Satterthwaite is undefined for non-Gaussian likelihoods). 
The actual method used per analysis is shown in the Method column.

## Methods used per analysis:
- GLMM_rejection: Wald chi-square (GLMM)
- LMM_RT_main: Satterthwaite F
- LMM_RT_unfair: Satterthwaite F

Table: Behavioral fixed-effect tests across 3 analyses.

|                 |Analysis       |Effect             |APA_Report                       |Sig |Method                 |
|:----------------|:--------------|:------------------|:--------------------------------|:---|:----------------------|
|GLMM_rejection.1 |GLMM_rejection |(Intercept)        |χ²(1) = 27.06, p < .001          |*** |Wald chi-square (GLMM) |
|GLMM_rejection.2 |GLMM_rejection |emotion            |χ²(4) = 612.79, p < .001         |*** |Wald chi-square (GLMM) |
|GLMM_rejection.3 |GLMM_rejection |offer_type         |χ²(1) = 2858.88, p < .001        |*** |Wald chi-square (GLMM) |
|GLMM_rejection.4 |GLMM_rejection |emotion:offer_type |χ²(4) = 64.59, p < .001          |*** |Wald chi-square (GLMM) |
|LMM_RT_main.1    |LMM_RT_main    |emotion            |F(4, 14149.15) = 6.92, p < .001  |*** |Satterthwaite F        |
|LMM_RT_main.2    |LMM_RT_main    |offer_type         |F(1, 29.00) = 61.98, p < .001    |*** |Satterthwaite F        |
|LMM_RT_main.3    |LMM_RT_main    |emotion:offer_type |F(4, 14149.57) = 21.92, p < .001 |*** |Satterthwaite F        |
|LMM_RT_unfair.1  |LMM_RT_unfair  |emotion            |F(4, 7062.65) = 0.56, p = 0.694  |ns  |Satterthwaite F        |
|LMM_RT_unfair.2  |LMM_RT_unfair  |reaction           |F(1, 7086.02) = 0.01, p = 0.903  |ns  |Satterthwaite F        |
|LMM_RT_unfair.3  |LMM_RT_unfair  |emotion:reaction   |F(4, 7063.49) = 8.78, p < .001   |*** |Satterthwaite F        |
