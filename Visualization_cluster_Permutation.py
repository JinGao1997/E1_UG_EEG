import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mne
from pathlib import Path
import warnings

def set_publication_style():
    plt.rcParams.update({
        'font.size': 11, 'axes.labelsize': 11, 'axes.titlesize': 13,
        'legend.fontsize': 10, 'xtick.labelsize': 10, 'ytick.labelsize': 10,
        'axes.spines.top': False, 'axes.spines.right': False
    })

def reconstruct_conditions(grand_ave_csv_path, cond1, cond2):
    """ Reconstructs separate conditions, with automatic Time-Unit correction. """
    df_erp = pd.read_csv(grand_ave_csv_path)
    df_cond1 = df_erp[df_erp['label'] == cond1].copy()
    df_cond2 = df_erp[df_erp['label'] == cond2].copy()
    
    if df_cond1.empty or df_cond2.empty:
        raise ValueError(f"Conditions '{cond1}' or '{cond2}' missing in data.")

    cols_to_drop = ['label', 'query', 'time'] + [c for c in df_erp.columns if 'Baseline_' in c or c in ['N170', 'EPN', 'FRN', 'N400', 'LPP_offer']]
    
    df_cond1 = df_cond1.set_index('time').drop(columns=cols_to_drop, errors='ignore').sort_index()
    df_cond2 = df_cond2.set_index('time').drop(columns=cols_to_drop, errors='ignore').sort_index()
    
    # Auto-detect ms vs seconds to align 0-point
    if df_cond1.index.max() > 10: 
        df_cond1.index = df_cond1.index / 1000.0
        df_cond2.index = df_cond2.index / 1000.0
        
    times = df_cond1.index.values
    ch_names = df_cond1.columns.tolist()
    sfreq = 1 / np.diff(times)[0]
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    info.set_montage(mne.channels.make_standard_montage('standard_1020'), match_case=False, on_missing='ignore')
    
    evoked1 = mne.EvokedArray(df_cond1.values.T / 1e6, info, tmin=times[0], comment=cond1)
    evoked2 = mne.EvokedArray(df_cond2.values.T / 1e6, info, tmin=times[0], comment=cond2)
    evoked_diff = mne.combine_evoked([evoked1, evoked2], weights=[1, -1])
    
    return evoked1, evoked2, evoked_diff

def reconstruct_stat_map(stats_csv_path, contrast_name, n_subjects=None):
    """ Reconstructs the statistical effect size spatiotemporal matrix. """
    df_stats = pd.read_csv(stats_csv_path)
    df_contrast = df_stats[df_stats['contrast'] == contrast_name].copy()
    
    df_pivot = df_contrast.pivot(index='channel', columns='time', values='t_obs').sort_index(axis=1)
    data_mat = df_pivot.values
    
    if n_subjects is not None:
        data_mat = data_mat / np.sqrt(n_subjects)
        
    times = df_pivot.columns.values
    sfreq = 1 / np.diff(times)[0]
    info = mne.create_info(ch_names=df_pivot.index.tolist(), sfreq=sfreq, ch_types='eeg')
    info.set_montage(mne.channels.make_standard_montage('standard_1020'), match_case=False, on_missing='ignore')
    return mne.EvokedArray(data_mat, info, tmin=times[0])

def plot_ultimate_meyer_clusters(
    stats_csv_path, grand_ave_csv_path, contrast_name, p_threshold=0.05, 
    topo_step=0.1, n_subjects=None, save_dir=None
):
    set_publication_style()
    
    stats_csv = Path(stats_csv_path)
    df_stats = pd.read_csv(stats_csv)
    df_contrast = df_stats[df_stats['contrast'] == contrast_name].copy()
    df_sig = df_contrast[df_contrast['p_val'] < p_threshold]
    
    if df_sig.empty:
        return

    cond1, cond2 = [c.strip() for c in contrast_name.split('-')]
    evoked1, evoked2, evoked_diff = reconstruct_conditions(grand_ave_csv_path, cond1, cond2)
    stat_map = reconstruct_stat_map(stats_csv_path, contrast_name, n_subjects)
    
    ch_names_evoked = evoked1.ch_names
    ch_names_stat = stat_map.ch_names
    cbar_label_stat = "Cohen's $d_z$" if n_subjects else "Statistical $t$-value"
    
    for cluster_id in df_sig['cluster'].unique():
        if pd.isna(cluster_id): continue
            
        c_df = df_sig[df_sig['cluster'] == cluster_id]
        tmin_c, tmax_c, p_val_c = c_df['time'].min(), c_df['time'].max(), c_df['p_val'].iloc[0]
        
        # ABSOLUTE PEAK DETECTION (Strictly Data-Driven)
        peak_row = c_df.loc[c_df['t_obs'].abs().idxmax()]
        peak_channel, peak_time, peak_t_val = peak_row['channel'], peak_row['time'], peak_row['t_obs']
        
        bins = np.arange(tmin_c, tmax_c, topo_step)
        if len(bins) == 0: bins = np.array([tmin_c, tmax_c])
        elif tmax_c > bins[-1] + 0.005: bins = np.append(bins, tmax_c)
        elif len(bins) == 1: bins = np.append(bins, tmax_c)
        n_bins = len(bins) - 1
        
        fig = plt.figure(figsize=(max(11, 3.5 * n_bins), 10))
        gs_top = fig.add_gridspec(1, 2, bottom=0.55, top=0.92, wspace=0.3)
        gs_bottom = fig.add_gridspec(1, n_bins, bottom=0.08, top=0.42, wspace=0.1)
        
        # --------------------------------------------------------------
        # PANEL A: Overlaid Waveforms at Absolute Peak Channel
        # --------------------------------------------------------------
        ax_erp = fig.add_subplot(gs_top[0])
        if peak_channel in ch_names_evoked:
            data1 = evoked1.copy().pick([peak_channel]).data[0] * 1e6
            data2 = evoked2.copy().pick([peak_channel]).data[0] * 1e6
            
            ax_erp.plot(evoked1.times, data1, color='#0077B6', linewidth=2.5, label=cond1)
            ax_erp.plot(evoked2.times, data2, color='#D62828', linewidth=2.5, label=cond2)
            
            ax_erp.axvspan(tmin_c, tmax_c, color='gray', alpha=0.15, label=f"Cluster Extent")
            ax_erp.axvline(peak_time, color='black', linestyle=':', alpha=0.6, label=f"Peak Effect")
            ax_erp.axhline(0, color='black', linewidth=0.8); ax_erp.axvline(0, color='black', linewidth=0.8)
            
            ax_erp.set_title(f"A. Waveforms at Peak Channel ({peak_channel})", fontweight='bold')
            ax_erp.set_xlabel("Time (s)"); ax_erp.set_ylabel("Amplitude (\u03BCV)")
            ax_erp.invert_yaxis(); ax_erp.legend(loc='best', frameon=False)
            
        # --------------------------------------------------------------
        # PANEL B: Overall Effect Size Topography (WITH CHANNEL NAMES)
        # --------------------------------------------------------------
        ax_stat = fig.add_subplot(gs_top[1])
        safe_tmin, safe_tmax = max(tmin_c, stat_map.times[0]), min(tmax_c, stat_map.times[-1])
        
        if safe_tmin < safe_tmax:
            stat_data = stat_map.copy().crop(tmin=safe_tmin, tmax=safe_tmax).data.mean(axis=1)
        else:
            stat_data = np.zeros(len(ch_names_stat))
            
        mask_stat = np.zeros(len(ch_names_stat), dtype=bool)
        cluster_channels = c_df['channel'].unique()
        mask_stat[[ch_names_stat.index(ch) for ch in cluster_channels if ch in ch_names_stat]] = True
        
        vmax_stat = np.abs(stat_data).max() if np.abs(stat_data).max() > 0 else 1.0
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Added `names=ch_names_stat` to plot labels, and `extrapolate='local'` to prevent color spillage
            im_stat, _ = mne.viz.plot_topomap(
                stat_data, stat_map.info, axes=ax_stat, cmap='RdBu_r', vlim=(-vmax_stat, vmax_stat), 
                mask=mask_stat, mask_params=dict(marker='*', markerfacecolor='black', markeredgecolor='white', linewidth=0, markersize=10), 
                contours=6, extrapolate='local', names=ch_names_stat, show=False
            )
            
        # Post-processing text properties to prevent visual clutter
        for txt in ax_stat.texts:
            txt.set_fontsize(6)          # Very small, neat font size
            txt.set_alpha(0.7)           # Slightly transparent so it blends into the background
            pos = txt.get_position()
            # Shift text slightly upwards (0.02 units) so it doesn't overlap the electrode dot/star
            txt.set_position((pos[0], pos[1] + 0.02)) 
            
        ax_stat.set_title(f"B. Cluster Effect Size ({tmin_c*1000:.0f} - {tmax_c*1000:.0f} ms)", fontweight='bold')
        cbar_stat = fig.colorbar(im_stat, ax=ax_stat, fraction=0.046, pad=0.04)
        cbar_stat.set_label(cbar_label_stat, rotation=270, labelpad=15)

        # --------------------------------------------------------------
        # PANEL C: Dynamic Topomaps (Voltage Diff)
        # --------------------------------------------------------------
        global_vmax = 0
        for i in range(n_bins):
            st_tmin, st_tmax = max(bins[i], evoked_diff.times[0]), min(bins[i+1], evoked_diff.times[-1])
            if st_tmin < st_tmax:
                topo_data = evoked_diff.copy().crop(tmin=st_tmin, tmax=st_tmax).data.mean(axis=1) * 1e6
                global_vmax = max(global_vmax, np.abs(topo_data).max())
        symmetric_vlim = (-global_vmax, global_vmax) if global_vmax > 0 else (-1, 1)

        for i in range(n_bins):
            ax_topo = fig.add_subplot(gs_bottom[0, i])
            st_tmin, st_tmax = max(bins[i], evoked_diff.times[0]), min(bins[i+1], evoked_diff.times[-1])
            
            if st_tmin < st_tmax:
                topo_data = evoked_diff.copy().crop(tmin=st_tmin, tmax=st_tmax).data.mean(axis=1) * 1e6
            else:
                topo_data = np.zeros(len(ch_names_evoked))
            
            bin_df = c_df[(c_df['time'] >= bins[i]) & (c_df['time'] <= bins[i+1])]
            mask_dyn = np.zeros(len(ch_names_evoked), dtype=bool)
            if not bin_df.empty:
                sig_chans = bin_df['channel'].unique()
                mask_dyn[[ch_names_evoked.index(ch) for ch in sig_chans if ch in ch_names_evoked]] = True
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # extrapolate='local' guarantees crisp boundaries without spillage
                im_dyn, _ = mne.viz.plot_topomap(
                    topo_data, evoked_diff.info, axes=ax_topo, cmap='RdBu_r', vlim=symmetric_vlim, 
                    mask=mask_dyn, mask_params=dict(marker='*', markerfacecolor='black', markeredgecolor='white', linewidth=0, markersize=8), 
                    contours=6, extrapolate='local', show=False
                )
            if i == 0:
                ax_topo.set_title(f"C. Dynamic Voltage Map\n{bins[i]*1000:.0f}-{bins[i+1]*1000:.0f} ms", fontsize=11, fontweight='bold')
            else:
                ax_topo.set_title(f"{bins[i]*1000:.0f}-{bins[i+1]*1000:.0f} ms", fontsize=11)

        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.25])
        cbar = fig.colorbar(im_dyn, cax=cbar_ax)
        cbar.set_label('Difference Amplitude (\u03BCV)', fontsize=11)
        
        fig.suptitle(f"Cluster-based Permutation Test: {contrast_name} | {cluster_id} (p = {p_val_c:.4f})", fontsize=16, fontweight='bold', y=0.98)
        
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            out_file = save_dir / f"Ultimate_Meyer2021_{cluster_id}_{contrast_name.replace(' ', '')}.png"
            fig.savefig(out_file, dpi=300, bbox_inches='tight', transparent=False)
            print(f"[Export] Saved {cluster_id} visualization to: {out_file}")
            
        plt.show()

# ==============================================================================
# Execution Entry Point (Automated Batch Mode)
# ==============================================================================
if __name__ == "__main__":
    
    EXP_VERSION = 'E2'            
    ANALYSIS_METHOD = 'Method_Standard' 
    N_SUBJECTS = None 
    
    PROJECT_ROOT = Path.cwd()
    INPUT_DATA_DIR = PROJECT_ROOT / "data" / f"02_Pipeline_Output_{EXP_VERSION}" / ANALYSIS_METHOD / "Stimulus_Locked"
    OUTPUT_PLOT_DIR = PROJECT_ROOT / "results" / "Permutation_Visualization" / EXP_VERSION / ANALYSIS_METHOD
    
    print(f"\n[Environment Setup] Experiment: {EXP_VERSION} | Method: {ANALYSIS_METHOD}")
    
    if not INPUT_DATA_DIR.exists():
        print(f"Error: Directory not found. Please verify the pipeline output path.")
    else:
        available_files = [f.name for f in INPUT_DATA_DIR.iterdir() if f.is_file()]
        stats_file = next((f for f in ["clusters.csv", "perm.csv"] if f in available_files), None)
        
        if stats_file and (INPUT_DATA_DIR / "grand_ave.csv").exists():
            stats_csv_path = INPUT_DATA_DIR / stats_file
            df_stats = pd.read_csv(stats_csv_path)
            all_contrasts = df_stats['contrast'].unique()
            
            print(f"[Status] Detected {len(all_contrasts)} distinct statistical contrasts. Initiating batch rendering...")
            
            for contrast in all_contrasts:
                print(f"\n---> Processing Contrast: {contrast} <---")
                try:
                    plot_ultimate_meyer_clusters(
                        stats_csv_path=stats_csv_path,
                        grand_ave_csv_path=INPUT_DATA_DIR / "grand_ave.csv",
                        contrast_name=contrast,
                        p_threshold=0.05,
                        topo_step=0.1, 
                        n_subjects=N_SUBJECTS,
                        save_dir=OUTPUT_PLOT_DIR
                    )
                except Exception as e:
                    print(f"     [Warning] Could not render {contrast}. Reason: {e}")
                    
            print("\n[Success] Batch processing complete! All plots have been saved.")
        else:
            print(f"Error: Missing essential files in {INPUT_DATA_DIR}.")