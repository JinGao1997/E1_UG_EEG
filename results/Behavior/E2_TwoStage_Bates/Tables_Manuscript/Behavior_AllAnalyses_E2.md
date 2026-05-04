# Behavioral Analysis Summary, E2
Generated: 2026-05-03 15:46:33

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
|GLMM_rejection.1 |GLMM_rejection |(Intercept)        |χ²(1) = 3.52, p = 0.061          |.   |Wald chi-square (GLMM) |
|GLMM_rejection.2 |GLMM_rejection |emotion            |χ²(4) = 21.72, p < .001          |*** |Wald chi-square (GLMM) |
|GLMM_rejection.3 |GLMM_rejection |offer_type         |χ²(1) = 3851.84, p < .001        |*** |Wald chi-square (GLMM) |
|GLMM_rejection.4 |GLMM_rejection |emotion:offer_type |χ²(4) = 35.85, p < .001          |*** |Wald chi-square (GLMM) |
|LMM_RT_main.1    |LMM_RT_main    |emotion            |F(4, 21409.01) = 7.45, p < .001  |*** |Satterthwaite F        |
|LMM_RT_main.2    |LMM_RT_main    |offer_type         |F(1, 29.00) = 16.19, p < .001    |*** |Satterthwaite F        |
|LMM_RT_main.3    |LMM_RT_main    |emotion:offer_type |F(4, 21409.01) = 16.09, p < .001 |*** |Satterthwaite F        |
|LMM_RT_unfair.1  |LMM_RT_unfair  |emotion            |F(4, 10708.42) = 1.14, p = 0.336 |ns  |Satterthwaite F        |
|LMM_RT_unfair.2  |LMM_RT_unfair  |reaction           |F(1, 10677.44) = 0.20, p = 0.653 |ns  |Satterthwaite F        |
|LMM_RT_unfair.3  |LMM_RT_unfair  |emotion:reaction   |F(4, 10709.00) = 6.01, p < .001  |*** |Satterthwaite F        |
