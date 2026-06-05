# CLAUDE.md - UG_ERP_Project

> Global ~/.claude/CLAUDE.md already covers how I work (grounding, data safety, git,
> language, coding behavior). This file holds ONLY facts specific to this study.
> HDDM work lives in a separate project - keep it out of here.
>
> Canonical structure/reproducibility reference: `docs/README_Project_Structure.md`.
> This file is the quick fact-card; that file has the full per-script I/O and directory tree.

## Project overview
ERP study of an Ultimatum Game (responder role; EEG recorded during offer viewing). Core
question: how a proposer's **facial emotion** shapes the responder's **fairness perception
of, and response to (accept/reject), the proposer's offer**. Offer fairness is an a-priori
factor set by the split (Fair vs Unfair, per prior UG research) - there is NO subjective
fairness rating; the emotion x fairness effect is read out from offer-phase ERPs
(FRN, N400, LPP; plus N170/EPN) and trial-level accept/reject + RT behavior. The two
experiments differ mainly in the timing of the proposer's face relative to the offer:
**E1** = sequential (face precedes offer); **E2** = simultaneous (face + offer). E2 has more
trials per condition than E1 - per-participant design: 36 (E2) vs 24 (E1) trials for each
fair/unfair cell (offers 5,6,8,9), and 24 vs 12 for the 7:3 filler (filler is half-weighted
in both); ~840 vs ~540 trials/participant total (n=30 behavioral logs each, pre EEG rejection).

Two crossing toggles drive most scripts (see `docs/README_Project_Structure.md`):
`experiment_version` (E1/E2), and the baseline-handling method set by
`use_baseline_correction` in `Pipline_UG_OfferPhase.Rmd`. The method is NOT a free knob -
each value maps to its own downstream tree and stats script:

- `use_baseline_correction <- FALSE` (**the current setting**) -> `Method_Regression/`
  (folder tag `No_Baseline`): baseline is NOT subtracted, kept as `Baseline_<comp>`
  covariate columns -> **Alday (2019) baseline-as-covariate** -> consumed by
  `Sta_EEG_OfferPhase_RefAlday.Rmd` -> `<EXP>_TwoStage_Bates_Alday/` = **PRIMARY** analysis
  (model `amplitude ~ emotion * offer_type` with `Baseline_c` as a fitted covariate).
- `use_baseline_correction <- TRUE` -> `Method_Standard/` (folder tag `Standard_Baseline`):
  baseline mean (-200-0 ms) subtracted from each epoch -> traditional subtraction ->
  consumed by `Sta_EEG_OfferPhase_RefTraditional.Rmd` -> `<EXP>_TwoStage_Bates_Traditional/`
  = **SENSITIVITY** analysis (no baseline covariate; Stage 2 disabled).

Counterintuitive naming: `FALSE` selects the *Regression/Alday* method (the primary one),
not "no baseline handling". To reproduce both trees, run preprocessing twice (FALSE, then TRUE).

Method provenance: the Regression/Alday baseline-as-covariate approach follows Alday (2019),
"How much baseline correction do we need in ERP research?..." (full text in `docs/references/pdf/`,
gitignored - read it when a task needs the exact method or its stated limits). Preprocessing
wraps the HU `hu-neuro-pipeline` (vendored in `python_modules/`;
https://github.com/alexenge/hu-neuro-pipeline , docs https://hu-neuro-pipeline.readthedocs.io/en/stable/).

## Environment & how to run
- R: 4.3.3 (renv-managed; `renv::restore()` on fresh checkout). Python: via `reticulate`
  against conda env `r-reticulate` for preprocessing; standalone Python for the two viz scripts.
- Key packages: R - lme4, lmerTest, emmeans, tidyverse, here, reticulate, fs; Python -
  mne, numpy, pandas, scipy, matplotlib, plus the vendored `hu-neuro-pipeline` (`python_modules/`).
- Setup: `renv::restore()` (R); preprocessing drives MNE via reticulate (conda `r-reticulate`).
- Run order (toggle `experiment_version` / method at the top of each, then Knit/render):
  1. `Pipline_UG_OfferPhase.Rmd` - `use_baseline_correction <- FALSE` for the primary
     Regression/Alday tree; run again with `TRUE` for the Method_Standard sensitivity tree
  2. `Sta_Behaviour_RefAlday.Rmd`, `Sta_EEG_OfferPhase_RefAlday.Rmd` (primary),
     `Sta_EEG_OfferPhase_RefTraditional.Rmd` (sensitivity)
  3. Viz: `results/Behavior/Visualization_Behavior_RefAlday.py` (CLI: `--e1/--e2/--crossexp`),
     `results/EEG/Visualization_EEG_StiLocked_RefAlday.py`, then `Topo_Master_StiLocked*.Rmd`
     (after the EEG viz), `Visualization_Cluster_Permutation*.Rmd`.
- No build/lint/test suite. Each stats script self-documents via `REPRODUCIBILITY.txt` +
  `Methods_paragraph_<EXP>.md` in its output dir.

## Directory layout
raw is READ ONLY. (Full tree in `docs/README_Project_Structure.md`.)
```
data/00_Raw_Input/                 # READ-ONLY raw EEG (.set/.vhdr) + behavioral logs (.txt)
data/01_Preprocessing_Logs_<EXP>/  # regenerable cleaned/summary logs
data/02_Pipeline_Output_<EXP>/     # regenerable: Method_Standard|Method_Regression|Covariates|Baseline_Raw
results/Behavior/ , results/EEG/   # stats outputs (Alday primary / Traditional sensitivity)
python_modules/hu-neuro-pipeline/  # vendored MNE-Python preprocessing module
*.Rmd (project root)               # analysis scripts; Old_Scripts/ = archived, not run
.claude/rules/                     # on-demand conventions (eeg-pipeline-params, stats-diagnostics, visualization, coding-style)
docs/                              # README_Project_Structure.md, gitquick.txt, references/ (PDFs)
```
The integrated trait/rating table `02_Pipeline_Output_<EXP>/Covariates/SVO_PID5BF_PostRating_<EXP>.xlsx`
is MANUALLY prepared (not script-generated) - irreplaceable input for Stage-2 analyses.

## Experiment & data conventions
- Paradigm: single-shot UG, responder role; ERPs time-locked to offer onset (offer phase).
  Response-locked CPP available as a separate phase.
- Factors:
  - emotion (5 facial expressions = 3 smile types + disgust + neutral):
    `enj` = reward/enjoyment smile, `aff` = affiliative smile, `dom` = dominance smile,
    `dis` = disgust, `neu` = neutral. (Smile typology: reward / affiliation / dominance.)
  - offer (`Offers_Other`): 5,6,7,8,9 = splits 5:5, 6:4, 7:3, 8:2, 9:1.
    Fairness pooling (defined per prior UG research): **Fair = {5,6}**, **Unfair = {8,9}**;
    **7:3 is a filler, excluded** from pooled fairness contrasts.
- Trigger / event codes (from `Pipline_UG_OfferPhase.Rmd`):
  - Offer/stimulus-locked epoching triggers: `c(10:89, 150:169)`.
  - Response-locked (CPP) triggers: `c(1, 2)`.
  - `reaction` is coded {0,1,2}: 0 = timeout / no response (excluded); **1 = accept,
    2 = reject** (recoded in `Sta_Behaviour_RefAlday.Rmd`; `reject_binary = 1` for reject).
    The raw behavioral log has no accept/reject text column - the mapping lives in analysis code.
- Recording: **64 channels, 500 Hz** (verified from raw - E2 `.vhdr` SamplingInterval=2000 us;
  E1 `.set` srate=500). No downsampling (`downsample_sfreq=None`), so epochs stay at 500 Hz.
- Montage / reference: `montage='easycap-M1'` (the cap actually used), re-referenced to
  **common average** (hu-neuro-pipeline defaults; not overridden in the call).
- Participant / trial ID: ID = first contiguous digit run (`\d+`) in the filename; EEG and log
  files paired by that ID (the case/format differences below do not affect pairing).
- File naming: **E1** = EEGLAB `.set`/`.fdt`, named `Vp00NN` (e.g. `Vp0001`); **E2** = BrainVision
  `.vhdr`/`.eeg`/`.vmrk`, named `VP00NN` (uppercase P, starts at `VP0000`). Behavioral logs `.txt`.

## Pipeline, ROIs & detailed conventions
Full preprocessing parameters (filter, epoch, ICA, rejection, cluster-permutation) and the
exact ERP component **ROI/time-window table** (reuse EXACTLY - never invent) are NOT
duplicated here - they live in `.claude/rules/eeg-pipeline-params.md` (auto-loads when you
touch analysis scripts) and in `docs/README_Project_Structure.md`.

Always-on essential - trial inclusion (kept aligned across behavior + EEG):
`reaction != 0` (== >0 given {0,1,2}) AND `RT` in **[300, 3000] ms**.

Other `.claude/rules/` (auto-load on matching analysis/figure files):
`eeg-pipeline-params.md`, `stats-diagnostics.md` (LMM/GLMM, ANOVA, mass-univariate),
`visualization.md` (figures), `coding-style.md` (repo coding conventions).
