Table: LMM_RT_main -- Model_Formula

|Formula                                                                                                                         |
|:-------------------------------------------------------------------------------------------------------------------------------|
|logRT ~ 1 + emotion + offer_type + emotion:offer_type + (1 &#124;      participant_id) + (0 + offer_type &#124; participant_id) |
