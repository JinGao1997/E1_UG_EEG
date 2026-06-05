---
globs: scripts/**, analysis/**, **/*.py, **/*.R, **/*.Rmd, **/*.ipynb
---
# Statistical diagnostics

Loaded when working on analysis files. Method-level checklists only -
grounding and no-fabrication rules are global and not repeated here.

## Mixed-effects models (LMM/GLMM)
- State the fixed- and random-effects structure and justify it (e.g. maximal per
  Barr et al. 2013; simplify deliberately on singular fit or non-convergence).
- Report convergence / singularity status; never interpret a non-converged fit.
- For GLMM, state the family and link; check overdispersion where relevant.
- Report fixed-effect estimates with confidence intervals and an effect-size measure,
  not just p-values.

## ANOVA
- State the design (within / between factors). Check sphericity and apply a correction
  (Greenhouse-Geisser / Huynh-Feldt) when violated.
- Report effect sizes (partial eta^2 / generalized eta^2) alongside F and p.

## Mass-univariate EEG (time x channel)
- Use and name a multiple-comparison correction. [USER: which - e.g. cluster-based
  permutation, TFCE, FDR - and its parameters]
- Report the test statistic, cluster-forming threshold, number of permutations, and
  the corrected p-value.
- Never present uncorrected maps as findings.

## General
- Report exact n (participants, and trials per condition/cell) and all exclusions with reasons.
- Distinguish confirmatory from exploratory analyses; never present post-hoc tests as planned.
