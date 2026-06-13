#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Face-Locked ERP Visualization (E1) — self-contained, supplementary.
=============================================================================
Companion to Pipline_UG_FacePhase_E1.Rmd and Sta_EEG_FacePhase_E1.Rmd.
Face phase is E1-only (sequential design); emotion is the SOLE factor (the
offer is not yet shown at face onset), so there is NO fair/unfair dimension.

Produces, per component (P1 / N170 / EPN / LPP_face) and per method:
  1. 5-emotion ROI waveform overlay.
  2. Difference waves: each emotion minus Neutral (overlay).
  3. topomap_data_for_R/<comp>_topomap_data.csv (per-channel window means per
     emotion + emotion-minus-Neutral diffs) consumed by Topo_Master_FaceLocked_E1.Rmd.
  4. <comp>_<method>_roi_waveforms.csv (ROI grand-mean timecourse per emotion).

Methods:
  - Regression  (Method_Regression/Face_Locked/ave.csv) = Alday baseline-as-
    covariate analysis (PRIMARY). The exported ave.csv is NOT baseline-subtracted,
    so for DISPLAY ONLY a pre-stimulus baseline (-200..0 ms) is removed from the
    waveforms/topomaps (clearly labelled). The emotion-minus-Neutral difference
    cancels any shared baseline regardless.
  - Standard    (Method_Standard/Face_Locked/ave.csv) = traditional baseline
    subtraction (SENSITIVITY); already baseline-corrected upstream.

Reads : data/02_Pipeline_Output_E1/Method_{Regression,Standard}/Face_Locked/
            {ave.csv, channel_locations.csv}
Writes: results/EEG/FacePhase_E1/Results_<comp>/Session_<ts>/
            {Regression_Results,Standard_Baseline}/...
Path style: auto-detect project root (searches upward for config/).
=============================================================================
"""

import matplotlib
matplotlib.use('Agg')

import os
import shutil
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.ndimage import gaussian_filter1d

warnings.filterwarnings('ignore')

# ==============================================================================
# Configuration
# ==============================================================================
EXPERIMENT_VERSION = 'E1'                  # face phase is E1-only
ANALYSIS_METHODS = ['Regression', 'Standard']

LINE_WIDTH = 2.0
SMOOTHING_SIGMA = 1.2
DISPLAY_BASELINE = (-0.200, 0.000)         # display-only baseline for Regression
PLOT_XLIM = (-200, 800)                    # ms

COLORS = {'neu': "#8491B4", 'aff': "#91D1C2", 'dis': "#E64B35",
          'dom': "#F39B7F", 'enj': "#3C5488"}
LABELS_MAP = {'neu': 'Neutral', 'aff': 'Affiliative', 'dis': 'Disgust',
              'dom': 'Dominance', 'enj': 'Reward'}
EMO_ORDER = ['neu', 'aff', 'dis', 'dom', 'enj']
REF_EMO = 'neu'                            # difference-wave reference

ALL_EEG_CHANNELS = [
    "Fp1", "Fpz", "Fp2", "AF7", "AF3", "AFz", "AF4", "AF8", "F9", "F7", "F5", "F3", "Fz", "F4", "F6", "F8", "F10",
    "FT7", "FC5", "FC3", "FC1", "FC2", "FC4", "FC6", "FT8", "T7", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "T8",
    "TP9", "TP7", "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6", "TP8", "TP10", "P7", "P5", "P3", "Pz", "P4",
    "P6", "P8", "PO9", "PO7", "PO3", "POz", "PO4", "PO8", "PO10", "O1", "Oz", "O2"
]


def find_root():
    p = Path(__file__).resolve()
    for parent in [p.parent] + list(p.parents):
        if (parent / 'config' / 'erp_components_face_E1.csv').exists():
            return parent
    raise FileNotFoundError('config/erp_components_face_E1.csv not found above ' + str(p))


ROOT = find_root()
COMP_DF = pd.read_csv(ROOT / 'config' / 'erp_components_face_E1.csv')
COMP_DF = COMP_DF[COMP_DF['experiment'] == EXPERIMENT_VERSION].reset_index(drop=True)

COMPONENT_SPECS = {
    row['comp_name']: {
        'roi': str(row['roi']).split('|'),
        'window': (float(row['t_min']), float(row['t_max'])),
        'scale': (float(row['scale_min']), float(row['scale_max']), float(row['scale_step'])),
    }
    for _, row in COMP_DF.iterrows()
}
BATCH_COMPONENTS = COMP_DF['comp_name'].tolist()

PIPE = ROOT / 'data' / f'02_Pipeline_Output_{EXPERIMENT_VERSION}'
OUT_BASE = ROOT / 'results' / 'EEG' / 'FacePhase_E1'   # face content stored separately


# ==============================================================================
# Data loading
# ==============================================================================
def parse_emotion(label):
    """'Face_enj' -> 'enj' (only the five single-emotion cells; pooled cells dropped)."""
    parts = str(label).split('_')
    if len(parts) >= 2 and parts[1] in EMO_ORDER and len(parts) == 2:
        return parts[1]
    return None


def load_grand_means(ave_path, comp, method):
    """Return (emows, chans) where emows[emo] is a DataFrame(time + channel cols)
    holding the grand mean across participants for that emotion. For the
    Regression method a display-only pre-stimulus baseline is subtracted."""
    df = pd.read_csv(ave_path)
    df['emotion'] = df['label'].map(parse_emotion)
    df = df.dropna(subset=['emotion'])
    if df.empty:
        return None, None
    chans = [c for c in ALL_EEG_CHANNELS if c in df.columns]

    emows = {}
    for emo in EMO_ORDER:
        sub = df[df['emotion'] == emo]
        if sub.empty:
            continue
        g = sub.groupby('time')[chans].mean().reset_index().sort_values('time')
        if method == 'Regression':
            blmask = (g['time'] >= DISPLAY_BASELINE[0]) & (g['time'] <= DISPLAY_BASELINE[1])
            if blmask.any():
                g[chans] = g[chans] - g.loc[blmask, chans].mean()
        emows[emo] = g.reset_index(drop=True)
    return emows, chans


def roi_timecourse(emows, comp):
    """emo -> (time_ms array, ROI-mean array)."""
    roi = [c for c in COMPONENT_SPECS[comp]['roi'] if emows and c in next(iter(emows.values())).columns]
    out = {}
    for emo, g in emows.items():
        if not roi:
            continue
        t_ms = g['time'].values * 1000.0
        out[emo] = (t_ms, g[roi].mean(axis=1).values)
    return out, roi


# ==============================================================================
# Plotting
# ==============================================================================
def _style(ax, win_ms, y):
    ax.axvspan(win_ms[0], win_ms[1], color='#f0f0f0', alpha=1.0, lw=0, zorder=0)
    ax.axvline(0, ls='-', color='black', lw=1.0, zorder=1)
    ax.axhline(0, ls=':', color='black', lw=1.0, zorder=1)
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_linewidth(1.2); sp.set_color('black')
    ax.set_xlim(PLOT_XLIM)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
    ax.set_xticklabels([str(int(x)) if x % 200 == 0 else "" for x in ax.get_xticks()])
    if y is not None:
        ax.set_ylim(y[0], y[1]); ax.yaxis.set_major_locator(ticker.MultipleLocator(y[2]))
    ax.tick_params(axis='both', which='major', labelsize=13, length=6, width=1.2, direction='out')


def _save(fig, save_path):
    fig.savefig(save_path, dpi=300, format='tiff')
    fig.savefig(save_path.with_suffix('.png'), dpi=300, format='png')
    plt.close(fig)


def _sym_scale(arrays, pad=1.15):
    vals = np.concatenate([np.asarray(a, float) for a in arrays
                           if a is not None and not np.all(np.isnan(a))]) if arrays else np.array([])
    if vals.size == 0:
        return (-1.0, 1.0, 0.5)
    lim = np.nanmax(np.abs(vals)) * pad
    step = 10.0
    for s in (0.1, 0.25, 0.5, 1.0, 2.0, 2.5, 5.0, 10.0):
        if (2 * lim) / s <= 8:
            step = s; break
    lim = float(np.ceil(lim / step) * step)
    return (-lim, lim, step)


def plot_overlay(roi_tc, comp, method, title_suffix, save_path):
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white', dpi=300)
    plt.rcParams.update({'font.size': 14, 'font.family': 'sans-serif', 'font.sans-serif': ['Arial']})
    win_ms = tuple(w * 1000 for w in COMPONENT_SPECS[comp]['window'])
    for emo in EMO_ORDER:
        if emo not in roi_tc:
            continue
        t_ms, v = roi_tc[emo]
        ax.plot(t_ms, gaussian_filter1d(v, SMOOTHING_SIGMA), color=COLORS[emo],
                lw=LINE_WIDTH, alpha=0.9, label=LABELS_MAP[emo])
    _style(ax, win_ms, COMPONENT_SPECS[comp]['scale'])
    leg = ax.legend(title='Emotion', loc='upper left', bbox_to_anchor=(1.02, 1.0),
                    fontsize=11, frameon=True); leg.get_frame().set_edgecolor('#AAAAAA')
    ax.set_xlabel('Time (ms)', fontsize=15, weight='bold')
    ax.set_ylabel(f"{comp} (µV)", fontsize=15, weight='bold')
    ax.set_title(f"{comp} ROI: emotion main effect\n{title_suffix}", fontsize=15, weight='bold', pad=10)
    fig.tight_layout(rect=[0, 0, 0.85, 1.0])
    _save(fig, save_path)


def plot_diff(roi_tc, comp, method, title_suffix, save_path):
    """Each emotion minus Neutral, overlaid."""
    if REF_EMO not in roi_tc:
        return
    t_ref, v_ref = roi_tc[REF_EMO]
    diffs = {}
    for emo in EMO_ORDER:
        if emo == REF_EMO or emo not in roi_tc:
            continue
        t_e, v_e = roi_tc[emo]
        if len(v_e) == len(v_ref):
            diffs[emo] = np.asarray(v_e, float) - np.asarray(v_ref, float)
    if not diffs:
        return
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white', dpi=300)
    plt.rcParams.update({'font.size': 14, 'font.family': 'sans-serif', 'font.sans-serif': ['Arial']})
    win_ms = tuple(w * 1000 for w in COMPONENT_SPECS[comp]['window'])
    for emo in EMO_ORDER:
        if emo in diffs:
            ax.plot(t_ref, gaussian_filter1d(diffs[emo], SMOOTHING_SIGMA), color=COLORS[emo],
                    lw=LINE_WIDTH, alpha=0.9, label=f"{LABELS_MAP[emo]} − Neutral")
    _style(ax, win_ms, _sym_scale(list(diffs.values())))
    leg = ax.legend(title='Difference', loc='upper left', bbox_to_anchor=(1.02, 1.0),
                    fontsize=11, frameon=True); leg.get_frame().set_edgecolor('#AAAAAA')
    ax.set_xlabel('Time (ms)', fontsize=15, weight='bold')
    ax.set_ylabel(f"{comp} difference (µV)", fontsize=15, weight='bold')
    ax.set_title(f"{comp}: emotion − Neutral\n{title_suffix}", fontsize=15, weight='bold', pad=10)
    fig.tight_layout(rect=[0, 0, 0.85, 1.0])
    _save(fig, save_path)


# ==============================================================================
# Topomap-data export (consumed by Topo_Master_FaceLocked_E1.Rmd)
# ==============================================================================
def export_topomap_csv(emows, chans, comp, topo_path):
    win = COMPONENT_SPECS[comp]['window']
    win_means = {}                                  # emo -> Series(channel -> mean amplitude in window)
    for emo, g in emows.items():
        mask = (g['time'] >= win[0]) & (g['time'] <= win[1])
        if mask.any():
            win_means[emo] = g.loc[mask, chans].mean()
    if not win_means:
        return
    out = pd.DataFrame({'channel': chans})
    for emo in EMO_ORDER:
        if emo in win_means:
            out[emo] = win_means[emo].reindex(chans).values
    if REF_EMO in win_means:
        for emo in EMO_ORDER:
            if emo != REF_EMO and emo in win_means:
                out[f'diff_{emo}'] = (win_means[emo].reindex(chans).values
                                      - win_means[REF_EMO].reindex(chans).values)
    out.to_csv(topo_path, index=False)


# ==============================================================================
# Orchestration
# ==============================================================================
def run_method(comp, method, ts):
    folder = 'Method_Regression' if method == 'Regression' else 'Method_Standard'
    ave_path = PIPE / folder / 'Face_Locked' / 'ave.csv'
    loc_path = PIPE / folder / 'Face_Locked' / 'channel_locations.csv'
    if not ave_path.exists():
        print(f"   [SKIP] {comp} {method}: ave.csv missing ({ave_path})")
        return

    emows, chans = load_grand_means(ave_path, comp, method)
    if not emows:
        print(f"   [SKIP] {comp} {method}: no emotion conditions parsed.")
        return
    roi_tc, roi = roi_timecourse(emows, comp)
    if not roi:
        print(f"   [WARN] {comp} {method}: no ROI channels present in data.")
        return

    sub = 'Regression_Results' if method == 'Regression' else 'Standard_Baseline'
    out_dir = OUT_BASE / f"Results_{comp}" / f"Session_{ts}" / sub
    topo_dir = out_dir / 'topomap_data_for_R'
    out_dir.mkdir(parents=True, exist_ok=True)
    topo_dir.mkdir(parents=True, exist_ok=True)
    if loc_path.exists():
        try:
            shutil.copy(loc_path, out_dir / 'channel_locations.csv')
        except Exception:
            pass

    suffix = ("Alday (display baseline -200..0 ms)" if method == 'Regression'
              else "Traditional baseline subtraction")

    plot_overlay(roi_tc, comp, method, suffix, out_dir / f"{comp}_{method}_Waveforms.tif")
    plot_diff(roi_tc, comp, method, suffix, out_dir / f"{comp}_{method}_Diff_vs_Neutral.tif")

    # ROI grand-mean timecourse CSV (time + one column per emotion).
    wave_df = None
    for emo in EMO_ORDER:
        if emo not in roi_tc:
            continue
        t_ms, v = roi_tc[emo]
        if wave_df is None:
            wave_df = pd.DataFrame({'time_ms': t_ms})
        if len(v) == len(wave_df):
            wave_df[emo] = v
    if wave_df is not None:
        wave_df.to_csv(out_dir / f"{comp}_{method}_roi_waveforms.csv", index=False)

    export_topomap_csv(emows, chans, comp, topo_dir / f"{comp}_topomap_data.csv")
    print(f"   [OK] {comp} {method}: figures + topomap data -> {out_dir}")


if __name__ == '__main__':
    print(f"Face-Locked Visualization (E1) started {datetime.now().strftime('%H:%M:%S')}")
    print(f"  components: {BATCH_COMPONENTS}")
    print(f"  methods:    {ANALYSIS_METHODS}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for comp in BATCH_COMPONENTS:
        print(f">>> {comp}")
        for method in ANALYSIS_METHODS:
            run_method(comp, method, ts)
    print("Done.")
