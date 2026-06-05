# Behavioral Analysis Summary, Integrative
Generated: 2026-05-20 12:01:26

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

|                 |Analysis       |Effect                 |APA_Report                       |Sig |Method                 |
|:----------------|:--------------|:----------------------|:--------------------------------|:---|:----------------------|
|GLMM_rejection.1 |GLMM_rejection |(Intercept)            |χ²(1) = 17.22, p < .001          |*** |Wald chi-square (GLMM) |
|GLMM_rejection.2 |GLMM_rejection |Exp                    |χ²(1) = 2.18, p = 0.140          |ns  |Wald chi-square (GLMM) |
|GLMM_rejection.3 |GLMM_rejection |offer_type             |χ²(1) = 7645.32, p < .001        |*** |Wald chi-square (GLMM) |
|GLMM_rejection.4 |GLMM_rejection |emotion                |χ²(4) = 1173.92, p < .001        |*** |Wald chi-square (GLMM) |
|GLMM_rejection.5 |GLMM_rejection |Exp:offer_type         |χ²(1) = 7.16, p = 0.007          |**  |Wald chi-square (GLMM) |
|GLMM_rejection.6 |GLMM_rejection |Exp:emotion            |χ²(4) = 53.53, p < .001          |*** |Wald chi-square (GLMM) |
|GLMM_rejection.7 |GLMM_rejection |offer_type:emotion     |χ²(4) = 35.37, p < .001          |*** |Wald chi-square (GLMM) |
|GLMM_rejection.8 |GLMM_rejection |Exp:offer_type:emotion |χ²(4) = 62.84, p < .001          |*** |Wald chi-square (GLMM) |
|LMM_RT_main.1    |LMM_RT_main    |Exp                    |F(1, 57.97) = 1.30, p = 0.259    |ns  |Satterthwaite F        |
|LMM_RT_main.2    |LMM_RT_main    |offer_type             |F(1, 58.23) = 64.67, p < .001    |*** |Satterthwaite F        |
|LMM_RT_main.3    |LMM_RT_main    |emotion                |F(4, 35566.54) = 13.43, p < .001 |*** |Satterthwaite F        |
|LMM_RT_main.4    |LMM_RT_main    |Exp:offer_type         |F(1, 58.23) = 3.17, p = 0.080    |.   |Satterthwaite F        |
|LMM_RT_main.5    |LMM_RT_main    |offer_type:emotion     |F(4, 35566.89) = 34.48, p < .001 |*** |Satterthwaite F        |
|LMM_RT_unfair.1  |LMM_RT_unfair  |Exp                    |F(1, 54.99) = 0.97, p = 0.328    |ns  |Satterthwaite F        |
|LMM_RT_unfair.2  |LMM_RT_unfair  |emotion                |F(4, 17747.01) = 3.52, p = 0.007 |**  |Satterthwaite F        |
|LMM_RT_unfair.3  |LMM_RT_unfair  |reaction               |F(1, 53.36) = 2.12, p = 0.152    |ns  |Satterthwaite F        |
|LMM_RT_unfair.4  |LMM_RT_unfair  |emotion:reaction       |F(4, 17746.82) = 19.90, p < .001 |*** |Satterthwaite F        |
|LMM_RT_unfair.5  |LMM_RT_unfair  |Exp:emotion            |F(4, 17747.01) = 0.21, p = 0.933 |ns  |Satterthwaite F        |
|LMM_RT_unfair.6  |LMM_RT_unfair  |Exp:reaction           |F(1, 53.36) = 0.52, p = 0.475    |ns  |Satterthwaite F        |
|LMM_RT_unfair.7  |LMM_RT_unfair  |Exp:emotion:reaction   |F(4, 17746.82) = 3.65, p = 0.006 |**  |Satterthwaite F        |
