"""
Unified Visualization Pipeline for Cluster-Based Permutation Tests.

Description:
    This module integrates spatial (Topomaps) and temporal (ERP Waveforms) 
    visualizations for cluster-based permutation test outcomes. 
    It includes a global 'experiment_id' toggle to dynamically route outputs 
    for specific experiments (e.g., E1 vs E2) without altering the underlying 
    condition strings in the dataset.

Dependencies:
    - mne, pandas, matplotlib, numpy, scipy, pathlib
"""

import sys
import warnings
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.ndimage import gaussian_filter1d
from mne.viz import plot_topomap

warnings.filterwarnings('ignore')

# ==============================================================================
# 0. Utility Classes
# ==============================================================================

class Logger(object):
    """Standard output redirector for dual-logging."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() 

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# ==============================================================================
# 1. Global Configuration
# ==============================================================================

CONFIG = {
    # ---------------------------------------------------------
    # EXPERIMENT CONTROL
    # ---------------------------------------------------------
    "experiment_id": "E2",  

    # I/O Paths
    "input_wave": Path("data/02_Pipeline_Output/Method_Regression/Stimulus_Locked/ave.csv"),
    "input_stats": Path("data/02_Pipeline_Output/Method_Regression/Stimulus_Locked/clusters.csv"),
    
    # Base Results Directory
    "base_results_dir": Path("results"),
    "log_filename": "cluster_stats_report.txt", 
    
    # Spatial Montage & Exclusion Settings
    "montage_name": "easycap-M1", 
    "exclude_channels": [
        "query", "event_id", "average_by", "participant_id",
        "N170", "FRN", "P2", "N400", "LPP_offer", 
        "Baseline_N170", "Baseline_FRN", "Baseline_P2", "Baseline_N400", "Baseline_LPP_offer", 
        "A2", "M2", "TP9", "TP10"           
    ],
    
    # Peak selection constraints to prevent artifacts from dominating waveform visualizations
    "peak_exclude_channels": [
        "Fp1", "Fp2", "Fpz", "AF3", "AF4", "AF7", "AF8", "AFz", 
        "F7", "F8", "FT9", "FT10", "T7", "T8"                   
    ],

    # Topomap & Waveform Settings
    "p_threshold": 0.05,        
    "fig_format": "png",        
    "dpi": 300,                 
    "cmap": "RdBu_r",           
    "contours": 0,              
    "mask_params": dict(marker='o', markerfacecolor='white', markeredgecolor='black', linewidth=0.5, markersize=6),
    "default_electrodes": ["Pz", "FCz"], 
    "plot_xlim": (-200, 800),     
    "plot_ylim": (-6.0, 8.0),     
    "y_tick_step": 2.0,           
    "line_width": 2.0,
    "smoothing_sigma": 1.2,       
    "colors": {'neu': "#8491B4", 'aff': "#91D1C2", 'dis': "#E64B35", 'dom': "#F39B7F", 'enj': "#3C5488"},
    "labels_map": {'neu': 'Neutral', 'aff': 'Affiliative', 'dis': 'Disgust', 'dom': 'Dominance', 'enj': 'Reward'},
    "contexts": ['Fair', 'Unfair']
}

# ------------------------------------------------------------------------------
# Dynamic Output Directory Construction
# ------------------------------------------------------------------------------
exp_suffix = f"_{CONFIG['experiment_id']}" if CONFIG['experiment_id'] else ""
CONFIG["output_dir_topo"] = CONFIG["base_results_dir"] / f"ClusterVisual{exp_suffix}" / "Topomaps"
CONFIG["output_dir_wave"] = CONFIG["base_results_dir"] / f"ClusterVisual{exp_suffix}" / "Waveforms"

# ==============================================================================
# 2. Data Processing Functions
# ==============================================================================

def load_data(wave_path, stats_path):
    if not wave_path.exists(): raise FileNotFoundError(f"Waveform missing: {wave_path}")
    if not stats_path.exists(): raise FileNotFoundError(f"Stats missing: {stats_path}")
    return pd.read_csv(wave_path), pd.read_csv(stats_path)

def dataframe_to_evoked(df, condition_name, montage_name, exclude_list=[]):
    cond_col = next((c for c in ['label', 'condition', 'average_by'] if c in df.columns), None)
    subset = df[df[cond_col] == condition_name].copy()
    if subset.empty: raise ValueError(f"Condition '{condition_name}' not found.")
    
    subset = subset.sort_values('time').set_index('time')
    cols_to_drop = [c for c in subset.columns if c in ['participant_id', 'event_id', cond_col] or c in exclude_list or 'Unnamed' in c]
    data_subset = subset.drop(columns=cols_to_drop, errors='ignore')
    
    pivot_df = data_subset.groupby('time').mean().T 
    ch_names = pivot_df.index.tolist()
    times = pivot_df.columns.values
    sfreq = 1000.0 if len(times) < 2 else 1.0 / np.mean(np.diff(times))
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    try: info.set_montage(mne.channels.make_standard_montage(montage_name), match_case=False, on_missing='ignore')
    except: pass

    data = pivot_df.values * 1e-6 if np.max(np.abs(pivot_df.values)) > 1.0 else pivot_df.values
    return mne.EvokedArray(data, info, tmin=times[0], comment=condition_name, nave=1)

def calculate_difference_wave(df, contrast_str, montage_name, exclude_list):
    try: cond_a, cond_b = contrast_str.split(' - ')
    except: cond_a, cond_b = contrast_str.replace('_vs_', ' - ').split(' - ')
    ev_a = dataframe_to_evoked(df, cond_a, montage_name, exclude_list)
    ev_b = dataframe_to_evoked(df, cond_b, montage_name, exclude_list)
    return mne.combine_evoked([ev_a, ev_b], weights=[1, -1])

def plot_electrode_waveform(df, cond_col, channel, config, shade_window=None, filename_suffix=""):
    if channel not in df.columns: return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor='white', dpi=config["dpi"])
    plt.rcParams.update({'font.size': 14, 'font.family': 'sans-serif'})

    for idx, context in enumerate(config["contexts"]):
        ax = axes[idx]
        for emo in ['neu', 'aff', 'enj', 'dom', 'dis']:
            condition_name = f"Face_{emo}_{context}"
            subset = df[df[cond_col] == condition_name]
            if subset.empty: continue
            
            agg_subset = subset.groupby('time')[channel].mean().reset_index()
            times_ms = agg_subset['time'].values * 1000
            amplitudes = agg_subset[channel].values * (1e6 if np.max(np.abs(agg_subset[channel].values)) < 1e-3 else 1.0)
                
            valid_idx = (times_ms >= config["plot_xlim"][0]) & (times_ms <= config["plot_xlim"][1])
            ax.plot(times_ms[valid_idx], gaussian_filter1d(amplitudes[valid_idx], sigma=config["smoothing_sigma"]), 
                    color=config["colors"][emo], lw=config["line_width"], alpha=0.9, label=config["labels_map"][emo])

        if shade_window: ax.axvspan(*shade_window, color='#E5E5E5', alpha=0.6, lw=0, zorder=0)
        ax.axvline(0, ls='-', color='black', lw=1.0, zorder=1)
        ax.axhline(0, ls=':', color='black', lw=1.0, zorder=1)
        ax.set_xlim(config["plot_xlim"])
        ax.set_ylim(config["plot_ylim"])
        ax.set_xlabel('Time (ms)', fontsize=16, weight='bold')
        if idx == 0: ax.set_ylabel("Amplitude (µV)", fontsize=16, weight='bold')
        ax.set_title(f"{context} Context", fontsize=16, weight='bold', pad=12)

    leg = fig.legend(*axes[0].get_legend_handles_labels(), title='Emotion', loc='center right', bbox_to_anchor=(0.99, 0.5), frameon=True)
    
    exp_prefix = f"[{config['experiment_id']}] " if config['experiment_id'] else ""
    file_prefix = f"{config['experiment_id']}_" if config['experiment_id'] else ""
    shade_info = f" | Shaded: {shade_window[0]:.0f}-{shade_window[1]:.0f}ms" if shade_window else ""
    
    plt.suptitle(f"{exp_prefix}Electrode: {channel}{shade_info}", fontsize=20, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.03, 0.88, 0.95])
    
    out_path = config["output_dir_wave"] / f"{file_prefix}Waveform_{channel}{filename_suffix}.{config['fig_format']}"
    plt.savefig(out_path, dpi=config["dpi"], bbox_inches='tight')
    plt.close()

# ==============================================================================
# 3. Main Workflow
# ==============================================================================

def main():
    CONFIG["output_dir_topo"].mkdir(parents=True, exist_ok=True)
    CONFIG["output_dir_wave"].mkdir(parents=True, exist_ok=True)
    sys.stdout = Logger(CONFIG["output_dir_topo"] / CONFIG["log_filename"])
    
    print(f"\n{'='*70}\nUnified Cluster Visualization Pipeline\n{'='*70}")
    print(f"Active Experiment Context: {CONFIG['experiment_id'] if CONFIG['experiment_id'] else 'None (Merged)'}")
    print(f"Output Directory: {CONFIG['output_dir_topo'].parent}\n")

    df_wave, df_stats = load_data(CONFIG["input_wave"], CONFIG["input_stats"])
    cond_col = next((c for c in ['label', 'condition', 'average_by'] if c in df_wave.columns), None)
    
    sig_df = df_stats[df_stats["p_val"] < CONFIG["p_threshold"]].copy()
    if sig_df.empty: return print("[Info] No significant clusters identified.")

    dynamic_waveform_targets = []

    for (contrast, cluster_id, p_val), cluster_data in sig_df.groupby(['contrast', 'cluster', 'p_val']):
        t_min, t_max = cluster_data['time'].min(), cluster_data['time'].max()
        sig_channels = cluster_data['channel'].unique()
        
        # --- NEW: Explicit Boundary Logging ---
        print(f"\nContrast Analysis: [{contrast}] | Cluster ID: {cluster_id} (p={p_val:.4f})")
        print(f"  > Temporal Extent: {t_min*1000:.0f} ms to {t_max*1000:.0f} ms (Duration: {(t_max-t_min)*1000:.0f} ms)")
        print(f"  > Spatial Extent : {len(sig_channels)} Channels involved")
        print(f"    [{', '.join(sig_channels)}]")
        
        try:
            diff_evoked = calculate_difference_wave(df_wave, contrast, CONFIG["montage_name"], CONFIG["exclude_channels"])
            cropped = diff_evoked.copy().crop(tmin=t_min, tmax=t_max)
            mean_data_uv = np.mean(cropped.data, axis=1) * 1e6
            
            valid_sig_channels = [ch for ch in sig_channels if ch not in CONFIG.get("peak_exclude_channels", [])]
            if not valid_sig_channels:
                valid_sig_channels = sig_channels 

            sig_indices = [i for i, ch in enumerate(cropped.ch_names) if ch in valid_sig_channels]
            safe_contrast = contrast.replace(' ', '').replace('-', '_vs_')
            
            if sig_indices:
                peak_ch = cropped.ch_names[sig_indices[np.argmax(np.abs(mean_data_uv[sig_indices]))]]
                dynamic_waveform_targets.append({
                    "channel": peak_ch, "shade_window": (t_min * 1000, t_max * 1000),
                    "suffix": f"_{safe_contrast}_Clust{cluster_id}"
                })
                print(f"  > Selected Peak  : {peak_ch} (for visualization)")

            fig, ax = plt.subplots(figsize=(6, 5))
            v_range = np.max(np.abs(mean_data_uv)) * 1.1 
            im, _ = plot_topomap(mean_data_uv, cropped.info, axes=ax, mask=np.isin(np.array(cropped.info['ch_names']), sig_channels),
                                 mask_params=CONFIG["mask_params"], cmap=CONFIG["cmap"], vlim=(-v_range, v_range), show=False)
            plt.colorbar(im, ax=ax, shrink=0.75, pad=0.05).set_label('Difference Amplitude (µV)', fontsize=10)
            
            exp_prefix = f"[{CONFIG['experiment_id']}] " if CONFIG['experiment_id'] else ""
            title_str = (f"{exp_prefix}{contrast}\nCluster: {cluster_id} (p={p_val:.3f})\n"
                         f"Mean: {t_min*1000:.0f} - {t_max*1000:.0f} ms")
            ax.set_title(title_str, fontsize=11, fontweight='bold')
            
            file_prefix = f"{CONFIG['experiment_id']}_" if CONFIG['experiment_id'] else ""
            plt.savefig(CONFIG["output_dir_topo"] / f"{file_prefix}{safe_contrast}_C{cluster_id}.{CONFIG['fig_format']}", dpi=CONFIG["dpi"], bbox_inches='tight')
            plt.close(fig)
        except Exception as e: print(f"  [Error] Processing failed: {e}")

    print(f"\nCommencing Dynamic Waveform Generation...\n")
    
    for target_ch in CONFIG["default_electrodes"]:
        plot_electrode_waveform(df_wave, cond_col, target_ch, CONFIG, filename_suffix="_Apriori")

    for target in dynamic_waveform_targets:
        plot_electrode_waveform(df_wave, cond_col, target['channel'], CONFIG, 
                                shade_window=target['shade_window'], filename_suffix=target['suffix'])

if __name__ == "__main__":
    main()