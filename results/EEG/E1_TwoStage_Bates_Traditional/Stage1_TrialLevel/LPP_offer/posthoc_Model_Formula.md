Table: LPP_offer -- Model_Formula

|Formula                                                                                                                             |
|:-----------------------------------------------------------------------------------------------------------------------------------|
|LPP_offer ~ 1 + emotion + offer_type + emotion:offer_type + (1 &#124;      participant_id) + (0 + offer_type &#124; participant_id) |
