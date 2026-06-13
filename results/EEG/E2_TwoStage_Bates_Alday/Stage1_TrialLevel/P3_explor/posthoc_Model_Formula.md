Table: P3_explor -- Model_Formula

|Formula                                                                                                                                                                                            |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|P3_explor ~ 1 + emotion + offer_type + Baseline_c + emotion:offer_type +      emotion:Baseline_c + offer_type:Baseline_c + (1 &#124; participant_id) +      (0 + offer_type &#124; participant_id) |
