---
globs: scripts/**, analysis/**, **/*.Rmd, **/*.R, **/*.py, **/*.ipynb
---
# Coding style (UG_ERP_Project)

Repo-specific conventions, seeded from the existing scripts - refine as needed. Global
~/.claude/CLAUDE.md already covers general coding behavior (simplicity, surgical changes,
grounding); not repeated here. Match the surrounding script's style.

## R (analysis `.Rmd`)
- Paths: use `here::here(...)` so scripts stay position-independent. Do NOT add new hardcoded
  absolute paths (only two legacy ones exist - see `docs/README_Project_Structure.md` section 5).
- Put run-controlling toggles at the top as a SINGLE SOURCE OF TRUTH (`experiment_version`,
  `use_baseline_correction`); derive downstream paths/config from them.
- Load packages via `pacman::p_load(...)`. Environment is renv-managed - don't add deps casually.
- Stats: keep `options(contrasts = c("contr.sum", "contr.poly"))` (valid Type III ANOVA with
  interactions).
- Add defensive checks (dir/file existence, required columns) and fail fast with a clear
  `stop()` message, mirroring the existing pipeline.
- Each stats script writes `REPRODUCIBILITY.txt` + `Methods_paragraph_<EXP>.md` to its output
  dir - preserve that contract when adding analyses.

## Python (visualization)
- Auto-detect the project root (search upward); don't hardcode absolute paths.
- Expose run toggles as CLI flags where the script already does (`--e1/--e2/--crossexp`).

## Both
- Never modify raw data; never silently recode condition labels or participant/trial IDs.
- Version output filenames; don't overwrite prior figures/results silently.
