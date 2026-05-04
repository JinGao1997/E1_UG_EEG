# Stage 2 Disabled: Sensitivity Analysis

Generated: 2026-05-04 16:19:34

Stage 2 BLUP-based individual-difference correlations are NOT run in this
traditional-baseline-subtraction sensitivity analysis. They are reported
only from the companion primary analysis (directory:
'E1_TwoStage_Bates_Alday/Stage2_BLUP_Correlations/').

Rationale:
1. BLUPs from traditional baseline subtraction and BLUPs from the Alday
   baseline-as-covariate framework index different latent quantities and
   should not be directly compared.
2. This sensitivity analysis exists to verify Stage 1 (fixed-effect)
   conclusions, not to reanalyze individual differences.
3. Re-running Stage 2 here would inflate the family-wise FDR burden
   without contributing interpretable information.

If you need a sensitivity check on the Stage 2 conclusions specifically,
consider a different methodological comparison (e.g., raw vs Spearman
correlation, with vs without trait-Z standardization). Such checks belong
in their own dedicated supplementary analysis, not as a side effect of
the baseline-correction sensitivity script.
