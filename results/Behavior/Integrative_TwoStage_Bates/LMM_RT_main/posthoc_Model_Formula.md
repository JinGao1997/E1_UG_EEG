Table: LMM_RT_main -- Model_Formula

|Formula                                                                                                                                                                  |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|logRT ~ 1 + Exp + offer_type + Exp:offer_type + emotion + offer_type:emotion +      (1 &#124; participant_id_internal) + (0 + offer_type &#124; participant_id_internal) |
