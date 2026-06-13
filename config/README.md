# `config/erp_components.csv` — single source of truth for offer-locked ERP components

Every offer-locked analysis/visualization script reads this file at startup, so the
component time windows, ROIs, and the component list live in exactly ONE place.
To change a window/ROI, or add/remove a component, edit ONLY this CSV and re-run.

## Consumers
- `Pipline_UG_OfferPhase.Rmd` (A) — builds `erp_config` (extraction windows + ROIs).
- `Sta_EEG_OfferPhase_RefAlday.Rmd` / `Sta_EEG_OfferPhase_RefTraditional.Rmd` (B2) —
  read the component list via the `role` column.
- `results/EEG/Visualization_EEG_StiLocked_RefAlday.py` (C) — waveform plots.
- `Topo_Master_StiLocked_RefAlday.Rmd` (D) — topographies + time-course grids.

## Column schema
| column      | unit / format        | used by | meaning |
|-------------|----------------------|---------|---------|
| `experiment`| `E1` / `E2`          | A,B2,C,D | which experiment this row applies to; every loader filters on it (FRN windows differ E1 vs E2) |
| `comp_name` | string               | A,B2,C,D | component label; drives output column/folder names + `Baseline_<comp_name>`. MUST be unique and MUST NOT equal an electrode name (e.g. bare `P3` collides — use `P3_explor`) |
| `t_min`     | **seconds**          | A,C,D   | component window start |
| `t_max`     | **seconds**          | A,C,D   | component window end |
| `roi`       | `Ch1\|Ch2\|...` (pipe) | A,C,D | ROI channel names, pipe-delimited |
| `role`      | `confirmatory` / `exploratory` | B2 | reporting tier. **confirmatory = preregistered, exploratory = exploratory** (Werner: report preregistered first, then exploratory) |
| `scale_min` | µV (float)           | C       | waveform Y-axis minimum |
| `scale_max` | µV (float)           | C       | waveform Y-axis maximum |
| `scale_step`| µV (float)           | C       | waveform Y-axis tick step |
| `test_tmin` | **seconds**          | D       | wide exploratory sweep start (`test<Comp>` topo / time-course grid) |
| `test_tmax` | **seconds**          | D       | wide exploratory sweep end |

## Notes
- The baseline covariate columns (`Baseline_<comp_name>`, fixed −0.200–0.000 s) are
  auto-derived in the pipeline — do NOT list them here.
- Changing a window here does NOT retro-fit existing `trials.csv` amplitudes: the
  pipeline (A) must be re-run to regenerate them. The C script's "Sanity 4" check
  flags a config-vs-data window mismatch if a stale `trials.csv` is used.
- Current set = two tiers × two components × two experiments (8 rows):
  preregistered `FRN_pre` / `LPP_pre` (role=confirmatory) and exploratory `FRN_explor` /
  `P3_explor` (role=exploratory). FRN windows are experiment-specific; LPP/P3 are shared.
  One pipeline run extracts all four for a given experiment (loaders filter on
  `experiment`); the stats scripts split them into confirmatory(=preregistered) vs
  exploratory via `role`.
- `FRN_pre` window was derived by a collapsed-localizer peak (all-condition grand
  average, preregistered FRN ROI, most-negative peak in 200–300 ms, ±25 ms):
  E1 peak 278 → 253–303 ms; E2 peak 218 → 193–243 ms (E2 peak is an early visual
  negativity — reported as the preregistered result per agreement with Werner).
  The ±25 ms edges (odd ms) are rounded OUTWARD to the 500 Hz sampling grid
  (even ms) so the stated window equals the samples actually averaged:
  E1 252–304, E2 192–244 (the realized window MNE already produced from the
  ±25 ms spec; the rounding is a numeric no-op). Likewise `FRN_explor` E2
  325–375 → 324–376.
- **Window-edge convention: keep `t_min`/`t_max` on EVEN ms.** The epochs are
  sampled at 500 Hz on an even-ms grid (epoch start at an even ms). An even-ms
  edge lands exactly on a sample, so "stated window == averaged samples" with no
  half-sample ambiguity; an odd-ms edge falls between two samples and relies on
  MNE's ±0.5-sample crop tolerance (which the viz's strict `>=/<=` mask does NOT
  apply — the source of a past Sanity-4 mismatch). Even edges sidestep this.
