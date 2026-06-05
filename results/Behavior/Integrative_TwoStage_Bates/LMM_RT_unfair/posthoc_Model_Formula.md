Table: LMM_RT_unfair -- Model_Formula

|Formula                                                                                                                                                                                                    |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|logRT ~ 1 + Exp + emotion + reaction + emotion:reaction + Exp:emotion +      Exp:reaction + Exp:emotion:reaction + (1 &#124; participant_id_internal) +      (0 + reaction &#124; participant_id_internal) |
