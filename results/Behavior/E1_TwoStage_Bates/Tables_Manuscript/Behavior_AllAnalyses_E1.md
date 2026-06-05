# Behavioral Analysis Summary, E1
Generated: 2026-06-02 17:53:22

Type III ANOVA tests. LMM analyses use a Satterthwaite -> 
Kenward-Roger -> Wald cascade (lmerTest, pbkrtest, car). GLMM 
analyses use Wald chi-square (car::Anova) as the only valid 
method (Satterthwaite is undefined for non-Gaussian likelihoods). 
The actual method used per analysis is shown in the Method column.

## Methods used per analysis:
- LMM_RT_unfair: Satterthwaite F

Table: Behavioral fixed-effect tests across 1 analyses.

|                |Analysis      |Effect           |APA_Report                      |Sig |Method          |
|:---------------|:-------------|:----------------|:-------------------------------|:---|:---------------|
|LMM_RT_unfair.1 |LMM_RT_unfair |emotion          |F(4, 7052.93) = 2.14, p = 0.073 |.   |Satterthwaite F |
|LMM_RT_unfair.2 |LMM_RT_unfair |reaction         |F(1, 28.59) = 0.31, p = 0.585   |ns  |Satterthwaite F |
|LMM_RT_unfair.3 |LMM_RT_unfair |emotion:reaction |F(4, 7051.64) = 17.72, p < .001 |*** |Satterthwaite F |
