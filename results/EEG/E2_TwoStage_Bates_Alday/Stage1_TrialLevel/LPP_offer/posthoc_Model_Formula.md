Table: LPP_offer -- Model_Formula

|Formula                                                                                                                                                                                            |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|LPP_offer ~ 1 + emotion + offer_type + Baseline_c + emotion:offer_type +      emotion:Baseline_c + offer_type:Baseline_c + (1 &#124; participant_id) +      (0 + offer_type &#124; participant_id) |
