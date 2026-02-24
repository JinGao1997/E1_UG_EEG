"""
Unified Visualization Pipeline for Cluster-Based Permutation Tests.

Description:
    This module integrates spatial (Topomaps) and temporal (ERP Waveforms) 
    visualizations for cluster-based permutation test outcomes. 
    
    Pipeline Steps:
    1. Parses pooled contrast conditions and identifies significant spatiotemporal clusters.
    2. Computes grand-averaged difference waves and maps topographical distributions.
    3. Identifies the spatial peak (electrode) strictly within the surviving cluster bounds.
    4. Dynamically generates publication-ready, dual-panel ERP waveforms for both 
       a-priori ROIs (e.g., Pz) and empirically derived peak electrodes, applying 
       cluster-specific temporal shading to highlight significant effects.

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
    """
    Standard output redirector for dual-logging.
    Simultaneously writes print statements to the console and a text-based log file 
    to ensure reproducibility and tracking of statistical parameters.
    """
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
    # I/O Paths
    "input_wave": Path("data/02_Pipeline_Output/Method_Standard/Stimulus_Locked/grand_ave.csv"),
    "input_stats": Path("data/02_Pipeline_Output/Method_Standard/Stimulus_Locked/clusters.csv"),
    "output_dir_topo": Path("results/ClusterVisual/Topomaps"),
    "output_dir_wave": Path("results/ClusterVisual/Waveforms"),
    "log_filename": "cluster_stats_report.txt", 
    
    # Spatial Montage & Exclusion Settings
    "montage_name": "easycap-M1", 
    "exclude_channels": [
        "FRN", "N400", "LPP_offer",                 
        "Baseline_FRN", "Baseline_N400", "Baseline_LPP_offer", 
        "A2", "M2", "TP9", "TP10",                  
        "query", "event_id", "average_by"           
    ],

    # Topomap Threshold & Styling Settings
    "p_threshold": 0.05,        
    "fig_format": "png",        
    "dpi": 300,                 
    "cmap": "RdBu_r",           
    "contours": 0,              
    "mask_params": dict(
        marker='o',             
        markerfacecolor='white',
        markeredgecolor='black',
        linewidth=0.5,          
        markersize=6            
    ),

    # Waveform Specific Settings
    "default_electrodes": ["Pz"], # A-priori ROIs generated regardless of clusters
    "plot_xlim": (-200, 800),     
    "plot_ylim": (-6.0, 8.0),     
    "y_tick_step": 2.0,           
    "line_width": 2.0,
    "smoothing_sigma": 1.2,       
    "colors": {
        'neu': "#8491B4", 'aff': "#91D1C2", 'dis': "#E64B35", 
        'dom': "#F39B7F", 'enj': "#3C5488"
    },
    "labels_map": {
        'neu': 'Neutral', 'aff': 'Affiliative', 'dis': 'Disgust', 
        'dom': 'Dominance', 'enj': 'Reward'
    },
    "contexts": ['Fair', 'Unfair']
}

# ==============================================================================
# 2. Data Processing Functions (Topography & ERP)
# ==============================================================================

def load_data(wave_path, stats_path):
    """Loads grand-averaged waveforms and permutation statistics."""
    if not wave_path.exists():
        raise FileNotFoundError(f"Waveform file missing: {wave_path}")
    if not stats_path.exists():
        raise FileNotFoundError(f"Statistics file missing: {stats_path}")

    print(f"Loading waveforms: {wave_path.name}")
    df_wave = pd.read_csv(wave_path)
    
    print(f"Loading statistics: {stats_path.name}")
    df_stats = pd.read_csv(stats_path)
    
    return df_wave, df_stats

def dataframe_to_evoked(df, condition_name, montage_name, exclude_list=[]):
    """Converts a specific condition subset into an MNE EvokedArray object."""
    cond_col = next((c for c in ['label', 'condition', 'average_by'] if c in df.columns), None)
    if not cond_col:
        raise ValueError("Metadata column for condition labels not found in dataset.")

    subset = df[df[cond_col] == condition_name].copy()
    if subset.empty:
        raise ValueError(f"Condition '{condition_name}' not found in the dataset.")

    if 'time' not in subset.columns:
        raise ValueError("Critical: 'time' column missing from dataset.")
        
    subset = subset.sort_values('time').set_index('time')
    
    meta_cols = ['participant_id', 'event_id', cond_col]
    cols_to_drop = [c for c in subset.columns if c in meta_cols or c in exclude_list or 'Unnamed' in c]
    data_subset = subset.drop(columns=cols_to_drop, errors='ignore')
    
    pivot_df = data_subset.groupby('time').mean().T 

    ch_names = pivot_df.index.tolist()
    times = pivot_df.columns.values
    sfreq = 1000.0 if len(times) < 2 else 1.0 / np.mean(np.diff(times))
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    try:
        montage = mne.channels.make_standard_montage(montage_name)
        info.set_montage(montage, match_case=False, on_missing='ignore')
    except Exception as e:
        print(f"  [Warning] Montage application failed: {e}")

    data = pivot_df.values
    if np.max(np.abs(data)) > 1.0: 
        data = data * 1e-6 

    evoked = mne.EvokedArray(data, info, tmin=times[0], comment=condition_name, nave=1)
    return evoked

def calculate_difference_wave(df, contrast_str, montage_name, exclude_list):
    """Computes the Difference Wave (Condition A - Condition B) based on contrast strings."""
    try:
        cond_a, cond_b = contrast_str.split(' - ')
    except ValueError:
        parts = contrast_str.replace('_vs_', ' - ').split(' - ')
        if len(parts) == 2:
            cond_a, cond_b = parts
        else:
            raise ValueError(f"Invalid contrast string format: '{contrast_str}'")

    ev_a = dataframe_to_evoked(df, cond_a, montage_name, exclude_list)
    ev_b = dataframe_to_evoked(df, cond_b, montage_name, exclude_list)
    
    diff = mne.combine_evoked([ev_a, ev_b], weights=[1, -1])
    diff.comment = f"{cond_a} - {cond_b}"
    return diff

def plot_electrode_waveform(df, cond_col, channel, config, shade_window=None, filename_suffix=""):
    """
    Generates a dual-panel waveform plot (Fair vs Unfair) for a specific electrode,
    incorporating dynamic shading for significant spatiotemporal clusters.
    """
    if channel not in df.columns:
        print(f"  [Warning] Electrode '{channel}' not found in data. Skipping waveform plot.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor='white', dpi=config["dpi"])
    plt.rcParams.update({
        'font.size': 14, 
        'font.family': 'sans-serif', 
        'font.sans-serif': ['Arial']
    })

    y_min, y_max = config["plot_ylim"]
    legend_handles = []
    legend_labels = []

    for idx, context in enumerate(config["contexts"]):
        ax = axes[idx]
        draw_order = ['neu', 'aff', 'enj', 'dom', 'dis'] 
        
        for emo in draw_order:
            condition_name = f"Face_{emo}_{context}"
            subset = df[df[cond_col] == condition_name].sort_values('time')
            
            if subset.empty:
                continue
                
            times_ms = subset['time'].values * 1000
            amplitudes = subset[channel].values
            
            if np.max(np.abs(amplitudes)) < 1e-3:
                amplitudes = amplitudes * 1e6
                
            valid_idx = (times_ms >= config["plot_xlim"][0]) & (times_ms <= config["plot_xlim"][1])
            times_plot = times_ms[valid_idx]
            amps_plot = amplitudes[valid_idx]
            amps_smoothed = gaussian_filter1d(amps_plot, sigma=config["smoothing_sigma"])
            
            line, = ax.plot(times_plot, amps_smoothed, 
                            color=config["colors"][emo], 
                            lw=config["line_width"], 
                            alpha=0.9, 
                            label=config["labels_map"][emo])
            
            if idx == 0:
                legend_handles.append(line)
                legend_labels.append(config["labels_map"][emo])

        # Cluster Shading Application
        if shade_window:
            shade_start, shade_end = shade_window
            ax.axvspan(shade_start, shade_end, color='#E5E5E5', alpha=0.6, lw=0, zorder=0)
            
        # Reference Lines and Axes Formatting
        ax.axvline(0, ls='-', color='black', lw=1.0, zorder=1)
        ax.axhline(0, ls=':', color='black', lw=1.0, zorder=1)
        
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.2)
            spine.set_color('black')

        ax.set_xlim(config["plot_xlim"])
        ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
        ax.set_ylim(y_min, y_max)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(config["y_tick_step"]))
        ax.tick_params(axis='both', which='major', labelsize=14, length=6, width=1.2, direction='out')
        ax.set_xlabel('Time (ms)', fontsize=16, weight='bold')
        
        if idx == 0:
            ax.set_ylabel(f"Amplitude (µV)", fontsize=16, weight='bold')
        
        ax.set_title(f"{context} Context", fontsize=16, weight='bold', pad=12)

    leg = fig.legend(legend_handles, legend_labels, title='Emotion', loc='center right', 
                     bbox_to_anchor=(0.99, 0.5), fontsize=12, frameon=True)
    leg.get_frame().set_edgecolor('#AAAAAA')
    leg.get_frame().set_linewidth(1.2)
    
    shade_info = f" | Shaded: {shade_window[0]:.0f}-{shade_window[1]:.0f}ms" if shade_window else ""
    plt.suptitle(f"Electrode: {channel}{shade_info}", fontsize=20, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.03, 0.88, 0.95])
    
    out_name = f"Waveform_{channel}{filename_suffix}.{config['fig_format']}"
    out_path = config["output_dir_wave"] / out_name
    plt.savefig(out_path, dpi=config["dpi"], bbox_inches='tight')
    plt.close()
    print(f"  > Output Exported: {out_path.name}")

# ==============================================================================
# 3. Main Execution Workflow
# ==============================================================================

def main():
    CONFIG["output_dir_topo"].mkdir(parents=True, exist_ok=True)
    CONFIG["output_dir_wave"].mkdir(parents=True, exist_ok=True)
    
    log_path = CONFIG["output_dir_topo"] / CONFIG["log_filename"]
    sys.stdout = Logger(log_path) 
    
    print(f"\n{'='*70}\nUnified Cluster Visualization Pipeline (Topomaps & Waveforms)\n{'='*70}")
    print(f"Log Output: {log_path}\n")

    try:
        df_wave, df_stats = load_data(CONFIG["input_wave"], CONFIG["input_stats"])
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # Identify metadata column for conditions
    cond_col = next((c for c in ['label', 'condition', 'average_by'] if c in df_wave.columns), None)
    if not cond_col:
        print("[Error] Missing condition metadata column in waveform data.")
        return

    sig_df = df_stats[df_stats["p_val"] < CONFIG["p_threshold"]].copy()
    
    if sig_df.empty:
        print(f"\n[Info] No significant clusters identified (p < {CONFIG['p_threshold']}).")
        return

    unique_effects = sig_df.groupby(['contrast', 'cluster', 'p_val'])
    print(f"\nIdentified {len(unique_effects)} significant clusters. Commencing Topomap generation...\n")

    # Storage for empirical peaks to generate dynamic waveforms later
    dynamic_waveform_targets = []

    # --- Phase 1: Topomap Generation & Peak Identification ---
    for (contrast, cluster_id, p_val), cluster_data in unique_effects:
        
        t_min = cluster_data['time'].min()
        t_max = cluster_data['time'].max()
        duration = (t_max - t_min) * 1000
        sig_channels = cluster_data['channel'].unique()
        
        print(f"Contrast Analysis: [{contrast}] | Cluster ID: {cluster_id}")
        print(f"  > P-value : {p_val:.4f}")
        print(f"  > Window  : {t_min*1000:.0f} - {t_max*1000:.0f} ms")
        
        try:
            diff_evoked = calculate_difference_wave(
                df_wave, contrast, CONFIG["montage_name"], CONFIG["exclude_channels"]
            )
            cropped = diff_evoked.copy().crop(tmin=t_min, tmax=t_max)
            
            if cropped.times.size == 0:
                print(f"  [Error] No valid data points found within the cluster window.")
                continue

            mean_data_v = np.mean(cropped.data, axis=1)
            mean_data_uv = mean_data_v * 1e6 
            
            # Constrain peak search strictly to the surviving cluster bounds
            sig_indices = [i for i, ch in enumerate(cropped.ch_names) if ch in sig_channels]
            
            safe_contrast = contrast.replace(' ', '').replace('-', '_vs_')
            
            if sig_indices:
                sig_amps = mean_data_uv[sig_indices]
                local_max_idx = np.argmax(np.abs(sig_amps))
                peak_ch = cropped.ch_names[sig_indices[local_max_idx]]
                peak_val = sig_amps[local_max_idx]
                print(f"  > Peak (In Cluster): {peak_val:.2f} µV at {peak_ch}")
                
                # Register target for Phase 2 Waveform generation
                dynamic_waveform_targets.append({
                    "channel": peak_ch,
                    "shade_window": (t_min * 1000, t_max * 1000),
                    "suffix": f"_{safe_contrast}_Clust{cluster_id}"
                })
            else:
                print("  > Peak: N/A (No matching channels)")

            # Topomap Rendering
            evoked_ch_names = np.array(cropped.info['ch_names'])
            mask = np.isin(evoked_ch_names, sig_channels)
            
            if not np.any(mask):
                continue

            fig, ax = plt.subplots(figsize=(6, 5))
            v_max = np.max(np.abs(mean_data_uv))
            v_range = v_max * 1.1 
            
            im, _ = plot_topomap(
                mean_data_uv, cropped.info, axes=ax, mask=mask,
                mask_params=CONFIG["mask_params"], cmap=CONFIG["cmap"],
                vlim=(-v_range, v_range), contours=CONFIG["contours"],
                sensors=True, show=False
            )
            
            cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.05)
            cbar.set_label('Difference Amplitude (µV)', fontsize=10)
            
            title_str = (f"{contrast}\nCluster: {cluster_id} (p={p_val:.3f})\n"
                         f"Mean: {t_min*1000:.0f} - {t_max*1000:.0f} ms")
            ax.set_title(title_str, fontsize=11, fontweight='bold')
            
            filename = f"{safe_contrast}_{cluster_id}_{t_min*1000:.0f}ms.{CONFIG['fig_format']}"
            out_path = CONFIG["output_dir_topo"] / filename
            plt.savefig(out_path, dpi=CONFIG["dpi"], bbox_inches='tight')
            plt.close(fig)
            
        except Exception as e:
            print(f"  [Error] Processing failed for cluster {cluster_id}: {e}")

    # --- Phase 2: ERP Waveform Generation ---
    print(f"\nCommencing Dynamic Waveform Generation...\n")

    # 2.1 Plot predefined A-Priori ROIs (No specific cluster shading)
    for target_ch in CONFIG["default_electrodes"]:
        print(f"Processing A-Priori Electrode: {target_ch}...")
        try:
            plot_electrode_waveform(df_wave, cond_col, target_ch, CONFIG, 
                                    shade_window=None, filename_suffix="_Apriori")
        except Exception as e:
            print(f"  [Error] Failed to render {target_ch}: {e}")

    # 2.2 Plot empirical peaks derived from significant clusters (With shading)
    for target in dynamic_waveform_targets:
        print(f"Processing Empirical Peak Electrode: {target['channel']} (Cluster specific)...")
        try:
            plot_electrode_waveform(
                df_wave, cond_col, target['channel'], CONFIG,
                shade_window=target['shade_window'],
                filename_suffix=target['suffix']
            )
        except Exception as e:
            print(f"  [Error] Failed to render {target['channel']}: {e}")

    print(f"\n{'='*70}\nProcessing Completed. Execution log archived.\n{'='*70}")

if __name__ == "__main__":
    main()