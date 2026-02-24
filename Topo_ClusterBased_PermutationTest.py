"""
Visualization Module for Cluster-Based Permutation Test Results.
Version: 1.2 (Robust Plotting + Auto-Logging)

Updates:
    - Added 'Logger' class to save console output to a text file automatically.
    - Keeps all previous robust plotting and diagnostic features.

Dependencies:
    - mne, pandas, matplotlib, numpy, pathlib
"""

import matplotlib.pyplot as plt
import mne
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from mne.viz import plot_topomap

# ==============================================================================
# 0. Utilities: Dual Logger
# ==============================================================================

class Logger(object):
    """
    Helper class to redirect stdout to both the terminal and a log file.
    """
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure it's written immediately

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# ==============================================================================
# 1. Configuration
# ==============================================================================

CONFIG = {
    # Input File Paths
    "input_wave": Path("data/02_Pipeline_Output/Method_Standard/Stimulus_Locked/grand_ave.csv"),
    "input_stats": Path("data/02_Pipeline_Output/Method_Standard/Stimulus_Locked/clusters.csv"),
    
    # Output Directory
    "output_dir": Path("results/ClusterVisual/Topomaps"),
    "log_filename": "cluster_stats_report.txt", # New log file name
    
    # EEG Montage
    "montage_name": "easycap-M1", 
    
    # Exclusion List
    "exclude_channels": [
        "FRN", "N400", "LPP", "LPP_offer",  
        "Baseline_FRN", "Baseline_N400",    
        "A2", "M2", "TP9", "TP10",          
        "query", "event_id"                 
    ],

    # Visualization Settings
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
    )
}

# ==============================================================================
# 2. Data Loading & Helper Functions
# ==============================================================================

def load_data(wave_path, stats_path):
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
    # 1. Identify condition column
    cond_col = next((c for c in ['label', 'condition', 'average_by'] if c in df.columns), None)
    if not cond_col:
        raise ValueError("Metadata column for condition labels not found.")

    subset = df[df[cond_col] == condition_name].copy()
    if subset.empty:
        raise ValueError(f"Condition '{condition_name}' not found.")

    # 2. Reshape
    if 'time' not in subset.columns:
        raise ValueError("Critical: 'time' column missing.")
        
    subset = subset.sort_values('time').set_index('time')
    
    meta_cols = ['participant_id', 'event_id', cond_col]
    cols_to_drop = [c for c in subset.columns if c in meta_cols or c in exclude_list or 'Unnamed' in c]
    data_subset = subset.drop(columns=cols_to_drop, errors='ignore')
    
    # 3. Aggregate
    pivot_df = data_subset.groupby('time').mean().T 

    # 4. Info Object
    ch_names = pivot_df.index.tolist()
    times = pivot_df.columns.values
    sfreq = 1000.0 if len(times) < 2 else 1.0 / np.mean(np.diff(times))
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    # 5. Montage
    try:
        montage = mne.channels.make_standard_montage(montage_name)
        info.set_montage(montage, match_case=False, on_missing='ignore')
    except Exception as e:
        print(f"  [Warning] Montage application failed: {e}")

    # 6. Units
    data = pivot_df.values
    if np.max(np.abs(data)) > 1.0: 
        data = data * 1e-6 

    evoked = mne.EvokedArray(data, info, tmin=times[0], comment=condition_name, nave=1)
    return evoked

def calculate_difference_wave(df, contrast_str, montage_name, exclude_list):
    try:
        cond_a, cond_b = contrast_str.split(' - ')
    except ValueError:
        parts = contrast_str.replace('_vs_', ' - ').split(' - ')
        if len(parts) == 2:
            cond_a, cond_b = parts
        else:
            raise ValueError(f"Invalid contrast format: '{contrast_str}'")

    ev_a = dataframe_to_evoked(df, cond_a, montage_name, exclude_list)
    ev_b = dataframe_to_evoked(df, cond_b, montage_name, exclude_list)
    
    diff = mne.combine_evoked([ev_a, ev_b], weights=[1, -1])
    diff.comment = f"{cond_a} - {cond_b}"
    return diff

# ==============================================================================
# 3. Main Execution
# ==============================================================================

def main():
    # Setup Output Directory
    CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
    
    # --- Setup Logging ---
    log_path = CONFIG["output_dir"] / CONFIG["log_filename"]
    sys.stdout = Logger(log_path) # Redirect print to file + terminal
    
    print(f"\n{'='*60}\nCluster Visualization Pipeline (Robust + Logging)\n{'='*60}")
    print(f"Log file location: {log_path}\n")

    # 1. Load Data
    try:
        df_wave, df_stats = load_data(CONFIG["input_wave"], CONFIG["input_stats"])
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # 2. Filter Clusters
    sig_df = df_stats[df_stats["p_val"] < CONFIG["p_threshold"]].copy()
    
    if sig_df.empty:
        print(f"\n[Info] No clusters found (p < {CONFIG['p_threshold']}).")
        return

    unique_effects = sig_df.groupby(['contrast', 'cluster', 'p_val'])
    print(f"\nIdentified {len(unique_effects)} significant clusters.\n")

    for (contrast, cluster_id, p_val), cluster_data in unique_effects:
        
        # Diagnostics
        t_min = cluster_data['time'].min()
        t_max = cluster_data['time'].max()
        duration = (t_max - t_min) * 1000
        sig_channels = cluster_data['channel'].unique()
        
        print(f"Processing: [{contrast}] | Cluster: {cluster_id}")
        print(f"  > P-value : {p_val:.4f}")
        print(f"  > Window  : {t_min*1000:.0f} - {t_max*1000:.0f} ms (Duration: {duration:.0f} ms)")
        print(f"  > Channels: {len(sig_channels)} significant sensors")

        # Compute Data
        try:
            diff_evoked = calculate_difference_wave(
                df_wave, contrast, CONFIG["montage_name"], CONFIG["exclude_channels"]
            )
            
            cropped = diff_evoked.copy().crop(tmin=t_min, tmax=t_max)
            
            if cropped.times.size == 0:
                print(f"  [Error] No data in time window.")
                continue

            # Mean Amplitude
            mean_data_v = np.mean(cropped.data, axis=1)
            mean_data_uv = mean_data_v * 1e6 
            
            # Peak Detection
            abs_max_idx = np.argmax(np.abs(mean_data_uv))
            peak_ch = cropped.ch_names[abs_max_idx]
            peak_val = mean_data_uv[abs_max_idx]
            print(f"  > Peak    : {peak_val:.2f} µV at {peak_ch} (Mean over window)")

        except Exception as e:
             print(f"  [Error] Processing failed: {e}")
             continue
        
        # Plotting
        try:
            # Mask
            evoked_ch_names = np.array(cropped.info['ch_names'])
            mask = np.isin(evoked_ch_names, sig_channels)
            
            if not np.any(mask):
                print("  [Warning] No significant channels in montage match.")
                continue

            fig, ax = plt.subplots(figsize=(6, 5))
            
            # Symmetric Scale
            v_max = np.max(np.abs(mean_data_uv))
            v_range = v_max * 1.1 
            
            im, _ = plot_topomap(
                mean_data_uv,
                cropped.info,
                axes=ax,
                mask=mask,
                mask_params=CONFIG["mask_params"],
                cmap=CONFIG["cmap"],
                vlim=(-v_range, v_range),
                contours=CONFIG["contours"],
                sensors=True,
                show=False
            )
            
            cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.05)
            cbar.set_label('Difference Amplitude (µV)', fontsize=10)
            
            safe_contrast = contrast.replace(' ', '').replace('-', '_vs_')
            title_str = (f"{contrast}\nCluster: {cluster_id} (p={p_val:.3f})\n"
                         f"Mean: {t_min*1000:.0f}-{t_max*1000:.0f} ms")
            ax.set_title(title_str, fontsize=11, fontweight='bold')
            
            filename = f"{safe_contrast}_{cluster_id}_{t_min*1000:.0f}ms.{CONFIG['fig_format']}"
            out_path = CONFIG["output_dir"] / filename
            
            plt.savefig(out_path, dpi=CONFIG["dpi"], bbox_inches='tight')
            plt.close(fig)
            print(f"  > Saved Plot: {out_path.name}\n")
            
        except Exception as e:
            print(f"  [Error] Plotting failed: {e}")

    print(f"{'='*60}\nProcessing Complete. Log saved.\n{'='*60}")

if __name__ == "__main__":
    main()