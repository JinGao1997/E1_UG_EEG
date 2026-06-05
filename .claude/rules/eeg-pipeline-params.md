---
globs: scripts/**, analysis/**, **/*.Rmd, **/*.R, **/*.py, **/*.ipynb
---
# EEG pipeline parameters & ERP component ROIs — where the values live

Single source of truth for every preprocessing parameter and ERP-component definition is
`Pipline_UG_OfferPhase.Rmd` (the stimulus-locked `group_pipeline()` call). READ the current
values there - never restate or guess them. These knobs get re-tuned, and any copy kept here
would silently drift out of sync.

## Where to look in `Pipline_UG_OfferPhase.Rmd`
- Filter (`highpass_freq`/`lowpass_freq`), `triggers`, ICA (`ica_method`/`ica_n_components`),
  `reject_peak_to_peak`, epoch window (`epochs_tmin`/`epochs_tmax`, else pipeline default),
  baseline arg, cluster-permutation (`perm_tmin`/`perm_tmax`/`perm_contrasts`): the
  `group_pipeline()` calls (stimulus-locked, and the separate CPP call).
- ERP component ROIs / time windows: the `erp_config` tribble - separate `E1` vs `E2` branches.
- Condition cells, fairness pooling, trial-inclusion strings: `common_average_by`.
- Montage / reference / sampling: hu-neuro-pipeline defaults unless overridden in the call.

## Stable structure (orientation only - NOT the tunable values)
- Components: FRN, N400, LPP_offer (all); EPN (both); N170 only in E2 (in E1 it is locked to
  the prior face onset); P2 is globally removed. The FRN window is shifted earlier in E2.
- Regression/Alday baseline-as-covariate columns are named `Baseline_<comp>`.
- Trial inclusion (also enforced in the stats scripts via `rt_lower_ms`/`rt_upper_ms`):
  `reaction != 0` AND RT within the script's RT bounds - read the exact bounds, don't hardcode.

Directory / I-O context: `docs/README_Project_Structure.md`.
