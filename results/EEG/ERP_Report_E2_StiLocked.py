#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Experiment 2 Master Analysis Script: Stimulus-Locked Components (FRN, LPP, N400)
=============================================================================
Description:
    The complete analysis and visualization pipeline for Experiment 2 (E2).
    
    EXPERIMENTAL DESIGN:
    - Simultaneous/Short-interval design (Distinct from E1).
    - Implication: The pre-offer baseline is treated as a stable covariate 
      independent of the offer-phase emotion interaction.

    STATISTICAL MODEL (REGRESSION METHOD):
    - Model: Signal ~ Intercept + Emotion + Offer + Emo*Offer + Baseline
    - Interaction Term: The 'Emotion * Baseline' interaction is EXCLUDED.
      Rationale: In Exp 2, we assume the baseline accounts for trial-to-trial 
      variability but acts as a main effect (intercept shift) rather than 
      modulating the slope of the emotion effect.

    MODULES:
    1. RegressionAnalysis: LMM-corrected waveforms (Exp 2 Model: No Emo*BL).
    2. StandardAnalysis: Traditional subtraction-based baseline (for reference).
    3. QC_Pipeline_Uncorrected: MNE-generated raw averages.
    4. QC_Manual_Uncorrected: Manually computed raw averages from epochs.

    INPUTS:
    - Epochs: data/02_Pipeline_Output/Method_Regression/Stimulus_Locked/epochs/
    - Baseline: data/02_Pipeline_Output/Baseline_Raw/Stimulus_Locked_Values/

Author: Project Maintainer
Date: 2026-01-30
=============================================================================
"""

import matplotlib
# Force non-interactive backend for server/headless safety
matplotlib.use('Agg') 

import os
import sys
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
from tqdm import tqdm
import warnings
from datetime import datetime
from scipy.ndimage import gaussian_filter1d

# Suppress runtime warnings for cleaner log output
warnings.filterwarnings('ignore')

# ==============================================================================
# 1. VISUAL CONFIGURATION
# ==============================================================================

# [VISUAL STYLE]
LINE_WIDTH = 2.0          
SMOOTHING_SIGMA = 1.2     

# [MANUAL SCALES] Y-Axis Settings (Microvolts)
# QC plots (Uncorrected) will override these using auto-scaling.
SCALE_CONFIG = {
    'FRN':  (-4.0, 3.0, 0.5),  
    'LPP':  (-4.0, 4.0, 0.5),  
    'N400': (-3.5, 3.5, 0.5)   
}

# ==============================================================================
# 2. SYSTEM CONFIGURATION
# ==============================================================================

BATCH_COMPONENTS = ['FRN', 'LPP', 'N400']

# ANALYSIS_METHOD Options: 'All', 'Regression', 'Standard', 'QC'
ANALYSIS_METHOD = 'All' 

REJECT_PTP_THRESHOLD_UV = 200.0

COLORS = {
    'neu': "#8491B4", 'aff': "#91D1C2", 'dis': "#E64B35", 
    'dom': "#F39B7F", 'enj': "#3C5488"
}

LABELS_MAP = {
    'neu': 'Neutral', 'aff': 'Affiliative', 'dis': 'Disgust', 
    'dom': 'Dominance', 'enj': 'Reward'
}

OFFER_TYPES = ['fair', 'unfair']

# Component Definitions
COMPONENT_SPECS = {
    'FRN': {
        'roi': ["F3", "Fz", "F4", "FC1", "FC2", "Cz"],
        'window': (0.250, 0.300),
        'plot_xlim': (-200, 1000),
        'folder_name': 'Stimulus_Locked'
    },
    'LPP': {
        'roi': ["Pz", "Cz", "C1", "C2", "CP1", "CP2"],
        'window': (0.500, 0.800),
        'plot_xlim': (-200, 1000),
        'folder_name': 'Stimulus_Locked'
    },
    'N400': {
        'roi': ["Fz", "Cz", "CPz", "Pz"],
        'window': (0.350, 0.450),
        'plot_xlim': (-200, 1000),
        'folder_name': 'Stimulus_Locked'
    }
}

# Full channel list for topographic mapping
ALL_EEG_CHANNELS = [
    "Fp1", "Fpz", "Fp2", "AF7", "AF3", "AFz", "AF4", "AF8", "F9", "F7", "F5", "F3", "Fz", "F4", "F6", "F8", "F10",
    "FT7", "FC5", "FC3", "FC1", "FC2", "FC4", "FC6", "FT8", "T7", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "T8",
    "TP9", "TP7", "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6", "TP8", "TP10", "P7", "P5", "P3", "Pz", "P4",
    "P6", "P8", "PO9", "PO7", "PO3", "POz", "PO4", "PO8", "PO10", "O1", "Oz", "O2"
]

TARGET_COMPONENT = None
CURR_CFG = None
PLOT_WINDOW = None
PATHS = None

# ==============================================================================
# 3. PATH MANAGEMENT
# ==============================================================================

def get_paths():
    """
    Dynamically resolves input/output paths based on the script's location.
    Ensures portability across local and server environments.
    """
    script_path = Path(__file__).resolve()
    root = None
    
    # Locate project root by searching for specific data structure
    for parent in [script_path.parent] + list(script_path.parents)[:5]:
        if (parent / "data" / "02_Pipeline_Output").exists():
            root = parent
            break
    if root is None:
        # Fallback logic
        if (Path.cwd() / "data").exists(): root = Path.cwd()
        else: root = script_path.parents[2] 

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pipe_root = root / "data" / "02_Pipeline_Output"
    folder = CURR_CFG['folder_name']
    
    # [E2 Specific] Define Output Directory with _E2 Suffix
    out_dir_base = script_path.parent / f"Results_{TARGET_COMPONENT}_E2" / f"Session_{ts}"
    
    paths = {
        "results": out_dir_base,
        
        # Standard Subtraction Method Outputs
        "std_ave": pipe_root / "Method_Standard" / folder / "ave.csv",
        "std_locs": pipe_root / "Method_Standard" / folder / "channel_locations.csv",
        
        # Regression / Uncorrected Method Outputs
        "reg_ave": pipe_root / "Method_Regression" / folder / "ave.csv",
        "reg_epochs": pipe_root / "Method_Regression" / folder / "epochs",
        
        # CRITICAL: Baseline values must come from the same Stimulus-Locked run
        "reg_base": pipe_root / "Baseline_Raw" / "Stimulus_Locked_Values" / "baseline_values.csv",
        "reg_locs": pipe_root / "Method_Regression" / folder / "channel_locations.csv"
    }
    return paths

# ==============================================================================
# 4. VISUALIZATION ENGINE
# ==============================================================================

class VisualizationEngine:
    @staticmethod
    def get_scale_settings():
        if TARGET_COMPONENT in SCALE_CONFIG:
            return SCALE_CONFIG[TARGET_COMPONENT]
        return (-5.0, 5.0, 1.0)

    @staticmethod
    def plot_unified_panels(data_dict, time_ms, title_suffix, save_path):
        """
        Generates publication-quality 2-panel plots (Fair vs Unfair).
        Standardized styling (Arial font, shaded windows, consistent axes).
        """
        fig, axes = plt.subplots(1, 2, figsize=(18, 6), facecolor='white', dpi=300)
        
        win_start_ms = CURR_CFG['window'][0] * 1000
        win_end_ms = CURR_CFG['window'][1] * 1000
        plot_xlim = CURR_CFG['plot_xlim']
        y_min, y_max, tick_step = VisualizationEngine.get_scale_settings()
        
        # Auto-scale heuristic for QC plots (Uncorrected data)
        if "Uncorrected" in title_suffix:
            all_vals = np.concatenate([v for v in data_dict.values() if not np.isnan(v).all()])
            if len(all_vals) > 0:
                data_range = np.percentile(all_vals, 99) - np.percentile(all_vals, 1)
                mid_point = np.median(all_vals)
                if data_range > (y_max - y_min):
                    y_min = mid_point - (data_range/2) - 2
                    y_max = mid_point + (data_range/2) + 2

        plt.rcParams.update({'font.size': 14, 'font.family': 'sans-serif', 'font.sans-serif': ['Arial']})

        legend_handles = []
        legend_labels = []

        for idx, offer in enumerate(OFFER_TYPES):
            ax = axes[idx]
            
            draw_order = ['neu', 'aff', 'dis', 'dom', 'enj']
            for emo in draw_order:
                key = f'{offer}_{emo}'
                if key in data_dict:
                    raw = data_dict[key]
                    if len(raw) == len(time_ms) and not np.all(np.isnan(raw)):
                        smooth = gaussian_filter1d(raw, sigma=SMOOTHING_SIGMA)
                        line, = ax.plot(time_ms, smooth, 
                                        color=COLORS[emo], 
                                        lw=LINE_WIDTH, 
                                        alpha=0.9, 
                                        label=LABELS_MAP[emo])
                        if idx == 0:
                            legend_handles.append(line)
                            legend_labels.append(LABELS_MAP[emo])

            # Styling
            ax.axvspan(win_start_ms, win_end_ms, color='#f0f0f0', alpha=1.0, lw=0, zorder=0)
            ax.axvline(0, ls='-', color='black', lw=1.0, zorder=1)
            ax.axhline(0, ls=':', color='black', lw=1.0, zorder=1)
            
            for spine in ax.spines.values():
                spine.set_visible(True); spine.set_linewidth(1.2); spine.set_color('black')

            ax.set_xlim(plot_xlim)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
            ticks = ax.get_xticks()
            ax.set_xticklabels([str(int(x)) if x % 200 == 0 else "" for x in ticks])
            
            ax.set_ylim(y_min, y_max)
            # Only use fixed tick steps if within standard range; else auto for QC
            if "Uncorrected" not in title_suffix:
                ax.yaxis.set_major_locator(ticker.MultipleLocator(tick_step))
            
            ax.tick_params(axis='both', which='major', labelsize=14, length=6, width=1.2, direction='out')
            ax.set_xlabel('Time (ms)', fontsize=16, weight='bold')
            if idx == 0:
                ax.set_ylabel(f"{TARGET_COMPONENT} (µV)", fontsize=16, weight='bold')
            
            clean_suffix = title_suffix.replace(" (Exp 2 Model)", "").replace(" (No Interaction)", "")
            ax.set_title(f"{TARGET_COMPONENT} ROI: {offer.capitalize()} Offers", fontsize=16, weight='bold', pad=12)

        leg = fig.legend(legend_handles, legend_labels, title='Emotion', loc='center right', 
                         bbox_to_anchor=(0.99, 0.5), fontsize=12, frameon=True)
        leg.get_frame().set_edgecolor('#AAAAAA')
        leg.get_frame().set_linewidth(1.2)
        
        plt.suptitle(f"{TARGET_COMPONENT} Waveforms - {clean_suffix}", fontsize=20, weight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0.03, 0.88, 0.95])
        
        plt.savefig(save_path, dpi=300, format='tiff')
        plt.savefig(save_path.with_suffix('.png'), dpi=300, format='png')
        plt.close()

# ==============================================================================
# 5. DATA LOADING HELPERS
# ==============================================================================

def prep_conditions(df):
    """
    Parses condition labels or raw columns to extract 'offer_type' and 'emotion'.
    """
    if 'label' in df.columns and 'offer_type' not in df.columns:
        def parse(l):
            try:
                p = l.split('_') 
                if len(p) < 4: return None, None
                emo = p[1]
                if p[2] in ['5','6']: off = 'fair'
                elif p[2] in ['8','9']: off = 'unfair'
                else: off = None
                return emo, off
            except: return None, None
        res = df['label'].apply(parse)
        df['emotion'] = [x[0] for x in res]
        df['offer_type'] = [x[1] for x in res]
        return df.dropna(subset=['offer_type', 'emotion'])
    elif 'Offers_Other' in df.columns:
        f = ((df['Offers_Other'].isin([5,6])) & (df['Offers_You'].isin([5,4])))
        u = ((df['Offers_Other'].isin([8,9])) & (df['Offers_You'].isin([2,1])))
        df['offer_type'] = np.where(f, 'fair', np.where(u, 'unfair', None))
        return df.dropna(subset=['offer_type'])
    return df

def load_data_csv(folder_or_file, desc, is_file=False):
    """
    Versatile loader:
    - If is_file=True: Loads a specific average file (e.g., ave.csv).
    - If is_file=False: Scans folder for Vp*_epo.csv epochs and aggregates them.
    """
    roi_chs = CURR_CFG['roi']
    topo, wave = [], []
    eeg = []

    # MODE A: Single File (Pre-aggregated ave.csv)
    if is_file:
        file_path = folder_or_file
        if not file_path.exists(): return None, None, None
        df = pd.read_csv(file_path)
        eeg = [c for c in ALL_EEG_CHANNELS if c in df.columns]
        return None, df, eeg

    # MODE B: Folder of Single-Trial Epochs
    folder = folder_or_file
    if not folder.exists(): return None, None, None
    files = sorted(folder.glob("Vp*_epo.csv"))
    if not files: return None, None, None
    
    temp = pd.read_csv(files[0], nrows=1)
    eeg = [c for c in ALL_EEG_CHANNELS if c in temp.columns]
    roi_avail = [c for c in roi_chs if c in temp.columns]

    for f in tqdm(files, desc=desc):
        try:
            df = pd.read_csv(f, low_memory=False)
            if df.empty: continue
            
            if df[eeg[0]].abs().max() < 1.0: df[eeg] *= 1e6
            
            # Robust ID extraction
            sub_id = f.name.split('_')[0]
            df['participant_id'] = sub_id
            
            ptp = df.groupby('index')[eeg].max() - df.groupby('index')[eeg].min()
            valid = ptp[(ptp < REJECT_PTP_THRESHOLD_UV).all(axis=1)].index
            if len(valid) == 0: continue
            df = df[df['index'].isin(valid)]
            
            win_min, win_max = CURR_CFG['window']
            mask = (df['time'] >= win_min) & (df['time'] <= win_max)
            
            avg = df[mask].groupby(['participant_id','index'])[eeg].mean().reset_index()
            meta_cols = ['label', 'Offers_Other', 'Offers_You', 'emotion']
            avail = [c for c in meta_cols if c in df.columns]
            meta = df[mask].groupby(['participant_id','index'])[avail].first().reset_index()
            topo.append(pd.merge(avg, meta, on=['participant_id','index']))
            
            cols_wave = ['participant_id','index','time'] + roi_avail + avail
            wave.append(df[cols_wave].copy())
        except: pass
        
    if not topo: return None, None, None
    return pd.concat(topo), pd.concat(wave), eeg

def load_bl(path):
    """
    Loads baseline values with STRICT column matching.
    Critically maps 'LPP' to 'Baseline_LPP_offer' to prevent FRN mismatch.
    """
    if not path.exists(): return None
    df = pd.read_csv(path)
    
    # Precise mapping from Component Name to R-Output Column Name
    mapping = {
        'FRN': 'Baseline_FRN',
        'LPP': 'Baseline_LPP_offer',
        'N400': 'Baseline_N400'
    }
    
    tgt = mapping.get(TARGET_COMPONENT)
    
    if not tgt or tgt not in df.columns:
        print(f"⚠️ Critical Error: Baseline column '{tgt}' for {TARGET_COMPONENT} not found in CSV!")
        print(f"   Available columns: {list(df.columns)}")
        return None

    if 'participant_id' not in df.columns and 'sub_id' in df.columns:
        df.rename(columns={'sub_id':'participant_id'}, inplace=True)
        
    print(f"   -> Successfully loaded baseline column: {tgt}")
    return df[['participant_id', 'index', tgt]].rename(columns={tgt:'BL'})

# ==============================================================================
# 6. QC MODULE A: PIPELINE SOURCE (ave.csv)
# ==============================================================================

class QC_Pipeline_Uncorrected:
    """
    Source: Method_Regression/Stimulus_Locked/ave.csv
    Logic: Generated by MNE pipeline with baseline=NULL. Official uncorrected average.
    """
    def __init__(self):
        self.out = PATHS["results"] / "QC_Uncorrected"
        self.out.mkdir(parents=True, exist_ok=True)
        self.viz = VisualizationEngine()
        self.input = PATHS["reg_ave"]

    def run(self):
        print(f"\n📉 QC Pipeline (ave.csv): {TARGET_COMPONENT}")
        if not self.input.exists(): 
            print(f"❌ Missing {self.input.name} in Regression folder"); return
        
        _, df, _ = load_data_csv(self.input, "", is_file=True)
        df = prep_conditions(df)
        
        roi_chs = [c for c in CURR_CFG['roi'] if c in df.columns]
        df['mean'] = df[roi_chs].mean(axis=1)
        res = df.groupby(['offer_type','emotion','time'])['mean'].mean().reset_index()
        
        self._plot(res, "Pipeline")

    def _plot(self, res, source_name):
        plot_win = CURR_CFG['plot_xlim']
        res_plot = res[(res['time']*1000 >= plot_win[0]) & (res['time']*1000 <= plot_win[1])]
        if res_plot.empty: return
        
        pdata = {}
        t_ms = sorted(res_plot['time'].unique() * 1000)
        
        for ot in OFFER_TYPES:
            for e in COLORS:
                sub = res_plot[(res_plot['offer_type']==ot)&(res_plot['emotion']==e)].sort_values('time')
                ref_df = pd.DataFrame({'time': np.array(t_ms)/1000})
                merged = pd.merge(ref_df, sub, on='time', how='left')
                pdata[f'{ot}_{e}'] = merged['mean'].values
        
        self.viz.plot_unified_panels(
            pdata, np.array(t_ms), 
            f"Uncorrected QC ({source_name})", 
            self.out/f"{TARGET_COMPONENT}_Uncorrected_{source_name}.tif"
        )
        print(f"   -> Saved: {source_name} Plot to {self.out.name}")

# ==============================================================================
# 7. QC MODULE B: MANUAL SOURCE (epochs)
# ==============================================================================

class QC_Manual_Uncorrected:
    """
    Source: Method_Regression/Stimulus_Locked/epochs/
    Logic: Reads raw single trials and computes arithmetic mean.
    """
    def __init__(self):
        self.out = PATHS["results"] / "QC_Uncorrected"
        self.out.mkdir(parents=True, exist_ok=True)
        self.viz = VisualizationEngine()
        self.input = PATHS["reg_epochs"]

    def run(self):
        print(f"\n📉 QC Manual (Epochs): {TARGET_COMPONENT}")
        if not self.input.exists(): print(f"❌ Missing Epochs folder"); return
        
        _, df_wave, _ = load_data_csv(self.input, "Loading Raw Epochs", is_file=False)
        if df_wave is None: return

        df_wave = prep_conditions(df_wave)
        roi_chs = [c for c in CURR_CFG['roi'] if c in df_wave.columns]
        
        df_wave['mean'] = df_wave[roi_chs].mean(axis=1)
        res = df_wave.groupby(['offer_type', 'emotion', 'time'])['mean'].mean().reset_index()
        
        QC_Pipeline_Uncorrected()._plot(res, "Manual")

# ==============================================================================
# 8. STANDARD ANALYSIS MODULE
# ==============================================================================

class StandardAnalysis:
    """
    Source: Method_Standard/Stimulus_Locked/ave.csv
    Logic: Visualizes Standard Subtraction Baseline results.
    """
    def __init__(self):
        self.out = PATHS["results"] / "Standard_Baseline"
        self.out.mkdir(parents=True, exist_ok=True)
        self.viz = VisualizationEngine()
        self.input = PATHS["std_ave"]

    def run(self):
        print(f"\n📊 Standard: {TARGET_COMPONENT}")
        if not self.input.exists(): print(f"❌ Missing"); return
        
        if PATHS["std_locs"].exists(): 
            try: shutil.copy(PATHS["std_locs"], self.out / "channel_locations.csv")
            except: pass
        
        _, df, _ = load_data_csv(self.input, "", is_file=True)
        df = prep_conditions(df)
        df.to_csv(self.out / f"{TARGET_COMPONENT}_ave_labelled.csv", index=False)
        
        roi_chs = [c for c in CURR_CFG['roi'] if c in df.columns]
        df['mean'] = df[roi_chs].mean(axis=1)
        res = df.groupby(['offer_type','emotion','time'])['mean'].mean().reset_index()
        
        plot_win = CURR_CFG['plot_xlim']
        res_plot = res[(res['time']*1000 >= plot_win[0]) & (res['time']*1000 <= plot_win[1])]
        
        if res_plot.empty: return
        pdata = {}
        t_ms = sorted(res_plot['time'].unique() * 1000)
        
        for ot in OFFER_TYPES:
            for e in COLORS:
                sub = res_plot[(res_plot['offer_type']==ot)&(res_plot['emotion']==e)].sort_values('time')
                ref_df = pd.DataFrame({'time': np.array(t_ms)/1000})
                merged = pd.merge(ref_df, sub, on='time', how='left')
                pdata[f'{ot}_{e}'] = merged['mean'].values

        self.viz.plot_unified_panels(
            pdata, np.array(t_ms), 
            "Standard Baseline", 
            self.out / f"{TARGET_COMPONENT}_Standard_Unified.tif"
        )
        print(f"   -> Saved: Standard Plot to {self.out.name}")

# ==============================================================================
# 9. REGRESSION ANALYSIS MODULE (EXP 2 MODEL - NO INTERACTION)
# ==============================================================================

class RegressionAnalysis:
    """
    Source: Method_Regression/Stimulus_Locked/epochs + baseline_values
    
    [EXP 2 STATISTICAL MODEL]:
    Signal ~ Intercept + Emotion + Offer + Emo*Offer + Baseline
    
    KEY DIFFERENCE FROM EXP 1:
    The 'Emo*Baseline' interaction term is EXCLUDED.
    """
    def __init__(self):
        self.out = PATHS["results"] / "Regression_Results"
        self.out.mkdir(parents=True, exist_ok=True)
        self.viz = VisualizationEngine()
        self.topo_dir = self.out / "topomap_data_for_R"
        self.topo_dir.mkdir(exist_ok=True)

    def run(self):
        print(f"\n🚀 Regression: {TARGET_COMPONENT} (Exp 2 - No Interaction Model)")
        if not PATHS["reg_epochs"].exists(): return

        df_topo, df_wave, chans = load_data_csv(PATHS["reg_epochs"], f"Loading", is_file=False)
        if df_topo is None: return
        df_base = load_bl(PATHS["reg_base"])
        if df_base is None: return
        
        print("   Aligning...")
        df_fin_topo = pd.merge(df_topo, df_base, on=['participant_id', 'index'], how='inner')
        df_fin_topo = prep_conditions(df_fin_topo)
        df_fin_wave = pd.merge(df_wave, df_base, on=['participant_id', 'index'], how='inner')
        df_fin_wave = prep_conditions(df_fin_wave)
        
        self._process_topomaps(df_fin_topo, chans)
        
        print("   Calculating Waveforms...")
        roi_chs = [c for c in CURR_CFG['roi'] if c in df_fin_wave.columns]
        pure, times = self._perform_regression_roi(df_fin_wave, roi_chs)
        
        self.viz.plot_unified_panels(
            pure, np.array(times)*1000, 
            "Regression-Corrected (Exp 2 Model)", self.out/f"{TARGET_COMPONENT}_Regression_Unified.tif"
        )
        self._save_waveform_csv(pure, times)

    def _process_topomaps(self, df, channels):
        src = PATHS["reg_locs"] if PATHS["reg_locs"].exists() else PATHS["std_locs"]
        if src.exists(): shutil.copy(src, self.out / "channel_locations.csv")
        
        dt = df.copy()
        for e in ['aff','dis','dom','enj']: dt[f'e_{e}'] = (dt['emotion']==e).astype(int)
        dt['oc'] = dt['offer_type'].map({'fair':-1, 'unfair':1})
        
        # [EXP 2 MODEL]: No Emo*Baseline Interaction
        # 1. Intercept
        X_list = [np.ones(len(dt))] 
        # 2. Emotion Main Effects
        for e in ['aff','dis','dom','enj']: X_list.append(dt[f'e_{e}'].values)
        # 3. Offer Main Effect
        X_list.append(dt['oc'].values)
        # 4. Emo * Offer Interaction
        for e in ['aff','dis','dom','enj']: X_list.append(dt[f'e_{e}'].values * dt['oc'].values)
        
        # 5. Baseline Main Effect Only
        X_list.append(dt['BL'].values) 
        
        X = np.column_stack(X_list)
        
        rows = []
        for ch in tqdm(channels, desc="   Topomaps"):
            if ch not in dt.columns: continue
            try:
                b = np.linalg.lstsq(X, dt[ch].values, rcond=None)[0]
                row = {'channel': ch}
                
                # Reconstruction: Eval at BL=0
                for ofr in OFFER_TYPES:
                    ov = -1 if ofr=='fair' else 1
                    for emo in COLORS:
                        v = b[0] # Intercept
                        if emo != 'neu':
                            idx = ['aff','dis','dom','enj'].index(emo)
                            v += b[1+idx] # Emo Main
                            v += b[6+idx]*ov # Emo*Offer
                        v += b[5]*ov # Offer Main
                        # b[10] (BL) is multiplied by 0, no interaction terms to handle
                        row[f'raw_{emo}_{ofr}'] = v
                rows.append(row)
            except: pass
        pd.DataFrame(rows).to_csv(self.topo_dir / f"{TARGET_COMPONENT}_topomap_data.csv", index=False)

    def _perform_regression_roi(self, df, roi_chs):
        df['ROI'] = df[roi_chs].mean(axis=1)
        times = sorted([t for t in df['time'].unique() if PLOT_WINDOW[0]<=t<=PLOT_WINDOW[1]])
        pure = {f'{o}_{e}':[] for o in OFFER_TYPES for e in COLORS}
        
        for e in ['aff','dis','dom','enj']: df[f'e_{e}'] = (df['emotion']==e).astype(int)
        df['oc'] = df['offer_type'].map({'fair':-1, 'unfair':1})
        
        for t in tqdm(times, desc="   Fitting"):
            dt = df[df['time']==t].dropna(subset=['ROI','BL'])
            if len(dt) < 20: 
                for k in pure: pure[k].append(np.nan); continue
            
            # [EXP 2 MODEL]: No Interaction (Same logic as topomaps)
            X_list = [np.ones(len(dt))]
            for e in ['aff','dis','dom','enj']: X_list.append(dt[f'e_{e}'].values)
            X_list.append(dt['oc'].values)
            for e in ['aff','dis','dom','enj']: X_list.append(dt[f'e_{e}'].values * dt['oc'].values)
            X_list.append(dt['BL'].values)
            
            X = np.column_stack(X_list)
            y = dt['ROI'].values
            try:
                b = np.linalg.lstsq(X, y, rcond=None)[0]
                for ofr in OFFER_TYPES:
                    ov = -1 if ofr=='fair' else 1
                    for emo in COLORS:
                        v = b[0]
                        if emo != 'neu':
                            idx = ['aff','dis','dom','enj'].index(emo)
                            v += b[1+idx] + b[6+idx]*ov
                        v += b[5]*ov
                        pure[f'{ofr}_{emo}'].append(v)
            except:
                for k in pure: pure[k].append(np.nan)
        return pure, times

    def _save_waveform_csv(self, pure_data, times):
        df = pd.DataFrame({'time': times})
        for k, v in pure_data.items():
            if len(v) == len(times): df[k] = v
        df.to_csv(self.out / f"{TARGET_COMPONENT}_reg_waveforms.csv", index=False)

# ==============================================================================
# 10. MAIN EXECUTION
# ==============================================================================

def update_global_config(comp_name):
    global TARGET_COMPONENT, CURR_CFG, PLOT_WINDOW, PATHS
    TARGET_COMPONENT = comp_name
    CURR_CFG = COMPONENT_SPECS[TARGET_COMPONENT]
    PLOT_WINDOW = (CURR_CFG['plot_xlim'][0]/1000, CURR_CFG['plot_xlim'][1]/1000)
    PATHS = get_paths()
    if not PATHS["results"].exists(): 
        PATHS["results"].mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"Analysis Started at {datetime.now().strftime('%H:%M:%S')}")
    
    for comp in BATCH_COMPONENTS:
        update_global_config(comp)
        
        if ANALYSIS_METHOD == 'All':
            # 1. Regression Method (Corrected via LMM)
            RegressionAnalysis().run()
            # 2. Standard Method (Corrected via Subtraction)
            StandardAnalysis().run()
            # 3. QC A: Pipeline Uncorrected (Auto-Average)
            QC_Pipeline_Uncorrected().run()
            # 4. QC B: Manual Uncorrected (Manual Calculation)
            QC_Manual_Uncorrected().run()
            
        elif ANALYSIS_METHOD == 'Regression': 
            RegressionAnalysis().run()
        elif ANALYSIS_METHOD == 'Standard': 
            StandardAnalysis().run()
        elif ANALYSIS_METHOD == 'QC': 
            QC_Pipeline_Uncorrected().run()
            QC_Manual_Uncorrected().run()

    print(f"Analysis Completed at {datetime.now().strftime('%H:%M:%S')}")