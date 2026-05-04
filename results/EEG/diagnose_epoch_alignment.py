#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
diagnose_viz_lmm_alignment.py  —  v2.1
=============================================================================
Pre-flight check for the viz pipeline's alignment with the LMM analysis.

Verifies that the trial set used for visualization will exactly match the
trial set used for LMM inference. Runs four layered assertions, ordered
from cheap-and-broad to expensive-and-specific:

  Sanity 1: participant_id encoding consistency (trials.csv vs epoch CSVs)
  Sanity 2: per-subject trial coverage (LMM-valid keys present in epoch)
  Sanity 3: post-join trial count equals LMM N (auto-read from REPRODUCIBILITY.txt)
  Sanity 4: component-window mean from epoch matches trials.csv scalar

A PASS on all four layers establishes that the viz pipeline can read the
same trials as LMM, in the same order, with the same numerical values.

This script uses the same logic as the v2.1 RegressionAnalysis sanity stack
in Visualization_EEG_StiLocked.py. Running it independently is recommended
before launching the full viz pipeline because:
  - It does NOT load full epoch timecourses (only `index` + ROI channels at
    the relevant window). Faster than viz by an order of magnitude.
  - Failure messages are uncluttered by viz output.
  - Independent verification: if it passes here, viz cannot fail at sanity.

USAGE
    # Default: run all components for the chosen experiment+method.
    python diagnose_viz_lmm_alignment.py

    # Edit EXPERIMENT, METHOD, SINGLE_COMPONENT below as needed.

EXIT BEHAVIOR
    Exits 0 if every component passes all four checks.
    Exits 1 with a diagnostic message indicating the failed component(s)
    and sanity layer(s).
=============================================================================
"""

import re
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# Configuration
# ==============================================================================
# USER: adjust paths to your local environment.
PROJECT_ROOT = Path(r"C:\Code\UG_ERP_Project")

# Experiment and method.
EXPERIMENT = "E1"                  # "E1" or "E2"
METHOD     = "Method_Regression"   # "Method_Regression" (Alday) or "Method_Standard" (Traditional)

# Components to check. Set SINGLE_COMPONENT to a name (e.g., "FRN") to run
# only that one; leave as None to run all components valid for EXPERIMENT.
SINGLE_COMPONENT = None

# Whether to run Sanity 4 (the slowest layer). Disable only if you have
# already verified Sanity 4 once and want a quick re-check of 1-3.
RUN_SANITY_4 = True

# Trial inclusion criteria — must match upstream LMM scripts:
#   Sta_EEG_OfferPhase_RefAlday.Rmd v2.1
#   Sta_EEG_OfferPhase_RefTraditional.Rmd v2.1
#   Sta_Behaviour_RefAlday.Rmd
INCL_OFFERS    = [5, 6, 8, 9]
INCL_RT_MIN_MS = 300
INCL_RT_MAX_MS = 3000

# Component window and ROI specs — must match upstream HU pipeline component
# definition (Pipline_UG_OfferPhase.Rmd). FRN window differs by experiment.
COMPONENT_WINDOWS_E2 = {
    "N170":      (0.150, 0.200),
    "EPN":       (0.250, 0.350),
    "FRN":       (0.200, 0.250),
    "N400":      (0.350, 0.450),
    "LPP_offer": (0.500, 0.800),
}
COMPONENT_WINDOWS_E1 = {
    "EPN":       (0.250, 0.350),
    "FRN":       (0.250, 0.300),
    "N400":      (0.350, 0.450),
    "LPP_offer": (0.500, 0.800),
}
COMPONENT_ROIS = {
    "N170":      ["P7", "P8", "PO7", "PO8"],
    "EPN":       ["PO7", "PO8", "P7", "P8", "O1", "O2"],
    "FRN":       ["F3", "Fz", "F4", "FC1", "FC2", "Cz"],
    "N400":      ["Cz", "CPz", "Pz"],
    "LPP_offer": ["Pz", "Cz", "C1", "C2", "CP1", "CP2"],
}

# Tolerance for Sanity 4. Floating-point recomputation of a mean over the
# component window differs from the precomputed scalar by float rounding
# only (~1e-7 uV). 0.01 uV is conservative; values near 1 uV indicate a real
# ROI/window mismatch.
SCALAR_TOLERANCE_UV = 0.01


def make_paths(experiment, method):
    """Path layout (mirrors Visualization_EEG_StiLocked.py v2.1 PATHS dict)."""
    pipe = PROJECT_ROOT / "data" / f"02_Pipeline_Output_{experiment}" / method / "Stimulus_Locked"
    method_tag = "Alday" if method == "Method_Regression" else "Traditional"
    repro_root = (PROJECT_ROOT / "results" / "EEG"
                  / f"{experiment}_TwoStage_Bates_{method_tag}"
                  / "Stage1_TrialLevel")
    return {
        "trials":     pipe / "trials.csv",
        "epochs":     pipe / "epochs",
        "repro_root": repro_root,
    }


# ==============================================================================
# Helpers (kept in sync with viz main script v2.1)
# ==============================================================================

def standardize_participant_id(pid):
    """Normalize to canonical 'VPxxxx'. Mirrors R-side standardize_id()."""
    if pd.isna(pid):
        return pid
    s = str(pid).strip()
    m = re.search(r'(\d+)', s)
    if not m:
        return s
    return f"VP{int(m.group(1)):04d}"


def parse_lmm_n(repro_root, component_name):
    """
    Read <repro_root>/<component>/REPRODUCIBILITY.txt and extract Observations
    (the LMM N) and the generated timestamp. Returns (None, None) if missing.
    """
    repro_file = Path(repro_root) / component_name / "REPRODUCIBILITY.txt"
    if not repro_file.exists():
        return None, None
    text = repro_file.read_text(encoding='utf-8')
    m_obs = re.search(r"Observations:\s*(\d+)", text)
    m_gen = re.search(r"Generated:\s*([^\n]+)", text)
    n_obs = int(m_obs.group(1)) if m_obs else None
    gen   = m_gen.group(1).strip() if m_gen else None
    return n_obs, gen


def banner(text, ch="="):
    bar = ch * 70
    print(f"\n{bar}\n{text}\n{bar}")


# ==============================================================================
# Per-component check
# ==============================================================================

def check_component(experiment, method, component, paths):
    """
    Run all four sanity checks for one component. Returns (passed, summary).
    Raises AssertionError on hard failure.
    """
    summary = {
        'experiment': experiment, 'method': method, 'component': component,
        'sanity_1': None, 'sanity_2': None, 'sanity_3': None, 'sanity_4': None,
        'lmm_n': None, 'aligned_n': None, 'max_diff_uv': None,
    }
    
    trials_file = paths["trials"]
    epoch_dir   = paths["epochs"]
    repro_root  = paths["repro_root"]
    
    if not trials_file.exists():
        raise AssertionError(f"trials.csv not found at {trials_file}")
    if not epoch_dir.exists():
        raise AssertionError(f"epoch directory not found at {epoch_dir}")
    
    epoch_files = sorted(epoch_dir.glob("Vp*_epo.csv"))
    if not epoch_files:
        raise AssertionError(f"No Vp*_epo.csv under {epoch_dir}")
    
    windows = COMPONENT_WINDOWS_E1 if experiment == "E1" else COMPONENT_WINDOWS_E2
    if component not in windows:
        raise AssertionError(f"Component '{component}' not defined for {experiment}")
    tmin, tmax = windows[component]
    roi = COMPONENT_ROIS[component]
    
    print(f"  Trials file:          {trials_file}")
    print(f"  Epoch dir:            {epoch_dir} ({len(epoch_files)} files)")
    print(f"  REPRODUCIBILITY root: {repro_root}")
    print(f"  Window:               [{tmin}, {tmax}] s")
    print(f"  ROI:                  {roi}")
    
    # ----------------------------------------------------------------------
    # Load trials.csv and apply LMM-equivalent filter chain
    # ----------------------------------------------------------------------
    trials_df = pd.read_csv(trials_file)
    trials_df['participant_id'] = trials_df['participant_id'].apply(standardize_participant_id)
    
    baseline_col = f"Baseline_{component}"
    if component not in trials_df.columns:
        raise AssertionError(f"Column '{component}' missing from trials.csv")
    
    require_baseline = (method == "Method_Regression")
    if require_baseline and baseline_col not in trials_df.columns:
        raise AssertionError(
            f"Column '{baseline_col}' missing from trials.csv (Alday requires baseline)"
        )
    
    mask = (
        trials_df['Offers_Other'].isin(INCL_OFFERS) &
        trials_df[component].notna() &
        (trials_df['reaction'] != 0) &
        (trials_df['RT'] >= INCL_RT_MIN_MS) &
        (trials_df['RT'] <= INCL_RT_MAX_MS)
    )
    if require_baseline:
        mask = mask & trials_df[baseline_col].notna()
    
    valid_trials = trials_df.loc[mask].copy()
    valid_keys = valid_trials[['participant_id', 'index']].drop_duplicates()
    n_lmm_actual = len(valid_keys)
    summary['aligned_n'] = n_lmm_actual
    print(f"  trials.csv after filter chain: {n_lmm_actual} rows, "
          f"{valid_keys['participant_id'].nunique()} subjects")
    
    # ----------------------------------------------------------------------
    # Sanity 1: participant_id consistency
    # ----------------------------------------------------------------------
    banner("Sanity 1: participant_id consistency", ch="-")
    trials_pids = set(trials_df['participant_id'].unique())
    epoch_pids  = set()
    for f in epoch_files:
        pid = standardize_participant_id(f.name.split('_')[0])
        epoch_pids.add(pid)
    
    only_in_trials = trials_pids - epoch_pids
    only_in_epoch  = epoch_pids - trials_pids
    if only_in_trials or only_in_epoch:
        msg = (f"Sanity 1 FAIL\n"
               f"  In trials.csv only: {sorted(only_in_trials)}\n"
               f"  In epoch dir only:  {sorted(only_in_epoch)}")
        summary['sanity_1'] = 'FAIL'
        raise AssertionError(msg)
    print(f"  PASS: {len(trials_pids)} subjects consistent")
    summary['sanity_1'] = 'PASS'
    
    # ----------------------------------------------------------------------
    # Sanity 2: per-subject trial coverage
    # ----------------------------------------------------------------------
    banner("Sanity 2: per-subject trial coverage", ch="-")
    per_sub_missing = []
    for f in epoch_files:
        pid = standardize_participant_id(f.name.split('_')[0])
        expected = set(valid_keys.loc[valid_keys['participant_id'] == pid, 'index'])
        if not expected:
            continue
        epoch_idx = set(pd.read_csv(f, usecols=['index'])['index'].unique())
        missing = expected - epoch_idx
        if missing:
            per_sub_missing.append((pid, len(missing), sorted(missing)[:5]))
    if per_sub_missing:
        msg = "Sanity 2 FAIL: trials in valid_keys absent from epoch CSV:\n" + "\n".join(
            f"  {pid}: {n} missing, e.g. {sample}"
            for pid, n, sample in per_sub_missing
        )
        summary['sanity_2'] = 'FAIL'
        raise AssertionError(msg)
    print(f"  PASS: every LMM-valid trial has corresponding epoch data")
    summary['sanity_2'] = 'PASS'
    
    # ----------------------------------------------------------------------
    # Sanity 3: viz N == LMM N
    # ----------------------------------------------------------------------
    banner("Sanity 3: viz N == LMM N", ch="-")
    n_lmm_expected, lmm_gen = parse_lmm_n(repro_root, component)
    summary['lmm_n'] = n_lmm_expected
    if n_lmm_expected is None:
        print(f"  SKIP: REPRODUCIBILITY.txt not found under {repro_root}/{component}/")
        print(f"       Has the LMM analysis been run for {component}?")
        summary['sanity_3'] = 'SKIP'
    else:
        print(f"  LMM Observations (REPRODUCIBILITY.txt, generated {lmm_gen}): {n_lmm_expected}")
        print(f"  viz post-filter N (from trials.csv):                     {n_lmm_actual}")
        if n_lmm_actual != n_lmm_expected:
            summary['sanity_3'] = 'FAIL'
            raise AssertionError(
                f"Sanity 3 FAIL: viz N ({n_lmm_actual}) != LMM N ({n_lmm_expected}). "
                f"Inclusion criteria have drifted between viz and LMM. "
                f"Check INCL_OFFERS, INCL_RT_MIN_MS, INCL_RT_MAX_MS, and the "
                f"upstream LMM script's load_and_prep filter chain."
            )
        print(f"  PASS")
        summary['sanity_3'] = 'PASS'
    
    # ----------------------------------------------------------------------
    # Sanity 4: epoch-window mean = trials.csv scalar
    # ----------------------------------------------------------------------
    if not RUN_SANITY_4:
        banner("Sanity 4: SKIPPED (RUN_SANITY_4 = False)", ch="-")
        summary['sanity_4'] = 'SKIP'
        return True, summary
    
    banner("Sanity 4: epoch-window mean vs trials.csv scalar", ch="-")
    valid_set = set(zip(valid_keys['participant_id'].astype(str),
                        valid_keys['index'].astype(int)))
    
    recomputed_rows = []
    for f in epoch_files:
        pid = standardize_participant_id(f.name.split('_')[0])
        try:
            df = pd.read_csv(f, usecols=lambda c: c in (['index', 'time'] + roi))
        except ValueError as e:
            raise AssertionError(
                f"Sanity 4 FAIL: cannot read required columns from {f.name}: {e}. "
                f"Likely cause: ROI channel not present in epoch CSV."
            )
        df['participant_id'] = pid
        expected_idx = {idx for (p, idx) in valid_set if p == pid}
        if not expected_idx:
            continue
        df = df[df['index'].isin(expected_idx)]
        df = df[(df['time'] >= tmin) & (df['time'] <= tmax)]
        if df.empty:
            continue
        df['roi_mean'] = df[roi].mean(axis=1)
        agg = df.groupby(['participant_id', 'index'])['roi_mean'].mean().reset_index()
        recomputed_rows.append(agg)
    
    if not recomputed_rows:
        raise AssertionError(f"Sanity 4 FAIL: no recomputed values (epoch data empty after filtering)")
    
    recomputed = pd.concat(recomputed_rows, ignore_index=True)
    check_df = recomputed.merge(
        valid_trials[['participant_id', 'index', component]],
        on=['participant_id', 'index'], how='inner'
    )
    if check_df.empty:
        raise AssertionError(f"Sanity 4 FAIL: no overlapping (participant_id, index) keys")
    
    check_df['diff'] = (check_df['roi_mean'] - check_df[component]).abs()
    max_diff  = check_df['diff'].max()
    mean_diff = check_df['diff'].mean()
    n_above   = (check_df['diff'] > SCALAR_TOLERANCE_UV).sum()
    summary['max_diff_uv'] = float(max_diff)
    
    print(f"  Trials checked:           {len(check_df)}")
    print(f"  Max abs diff:             {max_diff:.6f} uV")
    print(f"  Mean abs diff:            {mean_diff:.6f} uV")
    print(f"  Trials > {SCALAR_TOLERANCE_UV:.2f} uV diff:    {n_above}")
    
    if max_diff > SCALAR_TOLERANCE_UV:
        worst = check_df.nlargest(5, 'diff')[
            ['participant_id', 'index', component, 'roi_mean', 'diff']
        ].rename(columns={component: 'trials.csv_value', 'roi_mean': 'recomputed'})
        print(f"\n  Five worst-aligned trials:\n{worst.to_string(index=False)}")
        summary['sanity_4'] = 'FAIL'
        raise AssertionError(
            f"Sanity 4 FAIL: max diff = {max_diff:.4f} uV > tolerance = {SCALAR_TOLERANCE_UV}. "
            f"Likely cause: ROI/window mismatch, or epoch CSV and trials.csv "
            f"are from different preprocessing runs."
        )
    print(f"  PASS")
    summary['sanity_4'] = 'PASS'
    return True, summary


# ==============================================================================
# Main
# ==============================================================================

def main():
    paths = make_paths(EXPERIMENT, METHOD)
    
    banner(f"Diagnostic run: {EXPERIMENT} | {METHOD}")
    print(f"  Project root: {PROJECT_ROOT}")
    
    windows = COMPONENT_WINDOWS_E1 if EXPERIMENT == "E1" else COMPONENT_WINDOWS_E2
    if SINGLE_COMPONENT is not None:
        if SINGLE_COMPONENT not in windows:
            print(f"\n[ERROR] SINGLE_COMPONENT = '{SINGLE_COMPONENT}' "
                  f"not defined for {EXPERIMENT}. Valid: {list(windows.keys())}")
            sys.exit(1)
        components = [SINGLE_COMPONENT]
    else:
        components = list(windows.keys())
    print(f"  Components: {components}")
    
    all_summaries = []
    failures = []
    for comp in components:
        banner(f"COMPONENT: {comp}")
        try:
            passed, summary = check_component(EXPERIMENT, METHOD, comp, paths)
            all_summaries.append(summary)
            if not passed:
                failures.append(comp)
        except AssertionError as e:
            print(f"\n[FAIL] {comp}\n{e}")
            failures.append(comp)
            all_summaries.append({
                'experiment': EXPERIMENT, 'method': METHOD, 'component': comp,
                'error': str(e),
            })
            continue
    
    # ----------------------------------------------------------------------
    # Final summary table
    # ----------------------------------------------------------------------
    banner("SUMMARY")
    print(f"  {'Component':<12} {'San1':<6} {'San2':<6} {'San3':<6} {'San4':<6} "
          f"{'LMM N':<8} {'viz N':<8} {'Max diff (uV)':<14}")
    print(f"  {'-'*12} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*8} {'-'*8} {'-'*14}")
    for s in all_summaries:
        comp = s['component']
        if 'error' in s:
            print(f"  {comp:<12} ERROR: see message above")
            continue
        lmm_n = s.get('lmm_n')
        aligned_n = s.get('aligned_n')
        diff = s.get('max_diff_uv')
        print(f"  {comp:<12} "
              f"{(s.get('sanity_1') or 'N/A'):<6} "
              f"{(s.get('sanity_2') or 'N/A'):<6} "
              f"{(s.get('sanity_3') or 'N/A'):<6} "
              f"{(s.get('sanity_4') or 'N/A'):<6} "
              f"{(str(lmm_n) if lmm_n is not None else 'N/A'):<8} "
              f"{(str(aligned_n) if aligned_n is not None else 'N/A'):<8} "
              f"{(f'{diff:.4f}' if diff is not None else 'N/A'):<14}")
    
    if failures:
        print(f"\n[OVERALL] {len(failures)} of {len(components)} components FAILED: {failures}")
        sys.exit(1)
    
    print(f"\n[OVERALL] All {len(components)} components PASS. "
          f"viz pipeline can safely consume trials.csv + epoch CSVs for {EXPERIMENT} {METHOD}.")
    sys.exit(0)


if __name__ == "__main__":
    main()