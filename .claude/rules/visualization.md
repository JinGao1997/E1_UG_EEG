---
globs: scripts/**, analysis/**, figures/**, **/*.py, **/*.R, **/*.Rmd, **/*.ipynb
---
# Visualization standards

Loaded when working on analysis or figure files.

## Defaults
- Target style [USER: e.g. APA 7th / Nature]: figure dimensions, font family
  (e.g. Arial/Helvetica), and minimum font size [USER].
- Use colorblind-safe, perceptually uniform palettes (e.g. viridis). Don't rely on
  red/green as the only distinction.
- Show the data, not just summaries: overlay individual points or distributions on
  bar/box summaries where feasible.

## ERP / time-series figures
- Clear baseline and time axis in ms; mark stimulus onset.
- Show uncertainty (SEM or CI ribbons) and state which in the caption.
- Mark significant clusters / time windows explicitly and tie them to the statistics.

## Hygiene
- Centralize style once (matplotlib rcParams / ggplot theme); don't hand-tweak per figure.
- Save vector format (PDF/SVG) for publication plus a raster preview; never overwrite a
  prior figure silently - version the output names.
- Label axes with units. No chartjunk.
