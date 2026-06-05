Table: GLMM_rejection -- Model_Formula

|Formula                                                                                                                                                |
|:------------------------------------------------------------------------------------------------------------------------------------------------------|
|reject_binary ~ 1 + emotion + offer_type + emotion:offer_type +      (1 &#124; participant_id_internal) + (0 + emotion &#124; participant_id_internal) |
