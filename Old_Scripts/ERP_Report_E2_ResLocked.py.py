#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
CPP Master Analysis Script (Exp 2 - Simultaneous) - REGRESSION ONLY
=============================================================================
Description:
    A robust analysis pipeline for the Response-Locked CPP component (Exp 2).
    
    EXPERIMENTAL DESIGN:
    - Simultaneous Presentation (Face + Offer).
    - Implication: The pre-stimulus baseline (-200ms to 0ms) is pure noise/state,
      independent of the subsequent emotional processing.

    STATISTICAL MODEL (REGRESSION METHOD):
    - Model: Signal ~ Intercept + Emotion + Offer + Emo*Offer + Baseline
    - Interaction Term: The 'Emotion * Baseline' interaction is EXCLUDED.
      Rationale: Unlike Exp 1, the baseline here serves as a simple intercept 
      adjustment (ANCOVA-like) and does not interact with experimental conditions.

    [COVARIATE SOURCE]:
    - Uses 'Baseline_LPP_offer' from E2 Stimulus-Locked Output.
    - Controls for trial-by-trial fluctuation in starting neural state.

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
import gc

# Suppress warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

TARGET_COMPONENT = 'CPP' 

# QC Threshold (Peak-to-Peak uV)
REJECT_PTP_THRESHOLD_UV = 200.0

# Visualization Styling
LINE_WIDTH = 2.0          
SMOOTHING_SIGMA = 1.2     

COLORS = {
    'neu': "#8491B4", 'aff': "#91D1C2", 'dis': "#E64B35", 
    'dom': "#F39B7F", 'enj': "#3C5488"
}
LABELS_MAP = {
    'neu': 'Neutral', 'aff': 'Affiliative', 'dis': 'Disgust', 
    'dom': 'Dominance', 'enj': 'Reward'
}
OFFER_TYPES = ['fair', 'unfair']

# Component Specifications (Response-Locked: 0 = Button Press)
CURR_CFG = {
    'roi': ["Pz", "Cz", "C1", "C2", "CP1", "CP2"],
    'window': (-0.300, 0.050),     
    'plot_xlim': (-800, 200),    
}

PLOT_WINDOW = (CURR_CFG['plot_xlim'][0]/1000, CURR_CFG['plot_xlim'][1]/1000)

ALL_EEG_CHANNELS = [
    "Fp1", "Fpz", "Fp2", "AF7", "AF3", "AFz", "AF4", "AF8", "F9", "F7", "F5", "F3", "Fz", "F4", "F6", "F8", "F10",
    "FT7", "FC5", "FC3", "FC1", "FC2", "FC4", "FC6", "FT8", "T7", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "T8",
    "TP9", "TP7", "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6", "TP8", "TP10", "P7", "P5", "P3", "Pz", "P4",
    "P6", "P8", "PO9", "PO7", "PO3", "POz", "PO4", "PO8", "PO10", "O1", "Oz", "O2"
]

# ==============================================================================
# 2. PATHS (E2 SPECIFIC)
# ==============================================================================

def get_paths():
    """
    Robustly detects the project root and sets paths for Experiment 2.
    """
    script_path = Path(__file__).resolve()
    root = None
    
    # 1. Auto-detect Project Root
    for parent in [script_path.parent] + list(script_path.parents)[:5]:
        if (parent / "data" / "02_Pipeline_Output").exists():
            root = parent
            break
    
    # 2. Fallback
    if root is None:
        if (Path.cwd() / "data").exists(): root = Path.cwd()
        else: root = script_path.parents[2]

    print(f"📍 Detected Project Root: {root}")
    
    pipe_out = root / "data" / "02_Pipeline_Output"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    paths = {
        # OUTPUT: Specifically marked with _E2
        "results": script_path.parent / f"Results_{TARGET_COMPONENT}_E2" / f"Session_{ts}",
        
        # INPUT: Regression Epochs (Response Locked)
        "reg_epochs": pipe_out / "Method_Regression" / "Response_Locked" / "epochs",
        
        # INPUT: Baseline Covariate (Using E2 Stimulus-Locked Pre-Stim Baseline)
        "reg_base": pipe_out / "Baseline_Raw" / "Stimulus_Locked_Values" / "baseline_values.csv",
        
        # Channel Locations
        "locs_source": pipe_out / "Method_Standard" / "Stimulus_Locked" / "channel_locations.csv"
    }
    
    if not pipe_out.exists():
        print(f"❌ CRITICAL: Data folder not found at {pipe_out}")
    
    return paths

PATHS = get_paths()
if not PATHS["results"].exists():
    try: PATHS["results"].mkdir(parents=True, exist_ok=True)
    except: pass

# ==============================================================================
# 3. VISUALIZATION ENGINE
# ==============================================================================

class VisualizationEngine:
    @staticmethod
    def calc_auto_ylim(data_series):
        if isinstance(data_series, (list, np.ndarray)):
            data_series = pd.Series(data_series)
        
        valid_data = data_series[np.isfinite(data_series)]
        if valid_data.empty: return (-5.0, 5.0)
            
        dmin, dmax = valid_data.min(), valid_data.max()
        padding = max(0.5, (dmax - dmin) * 0.1)
        y_min = np.floor((dmin - padding) * 2) / 2
        y_max = np.ceil((dmax + padding) * 2) / 2
        return (y_min, y_max)

    @staticmethod
    def plot_unified_panels(data_dict, time_ms, title_suffix, save_path):
        fig, axes = plt.subplots(1, 2, figsize=(18, 6), facecolor='white', dpi=300)
        
        win_start_ms = CURR_CFG['window'][0] * 1000
        win_end_ms = CURR_CFG['window'][1] * 1000
        plot_xlim = CURR_CFG['plot_xlim']

        all_vals = np.concatenate([v for v in data_dict.values() if not np.isnan(v).all()])
        ylim = VisualizationEngine.calc_auto_ylim(all_vals)

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
                                        color=COLORS[emo], lw=LINE_WIDTH, alpha=0.9, 
                                        label=LABELS_MAP[emo])
                        if idx == 0:
                            legend_handles.append(line)
                            legend_labels.append(LABELS_MAP[emo])
            
            ax.axvspan(win_start_ms, win_end_ms, color='#f0f0f0', alpha=1.0, lw=0, zorder=0)
            ax.axvline(0, ls='-', color='black', lw=1.0, zorder=1) 
            ax.axhline(0, ls=':', color='black', lw=1.0, zorder=1)
            for spine in ax.spines.values():
                spine.set_visible(True); spine.set_linewidth(1.2); spine.set_color('black')

            ax.set_xlim(plot_xlim)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
            ticks = ax.get_xticks()
            ax.set_xticklabels([str(int(x)) if x % 200 == 0 else "" for x in ticks])
            ax.set_ylim(ylim)
            ax.tick_params(axis='both', which='major', labelsize=14, length=6, width=1.2, direction='out')
            ax.set_xlabel('Time (ms)', fontsize=16, weight='bold')
            if idx == 0: ax.set_ylabel(f"{TARGET_COMPONENT} (µV)", fontsize=16, weight='bold')
            
            clean_suffix = title_suffix.replace(" (Exp 2 Model)", "")
            ax.set_title(f'{TARGET_COMPONENT} ROI: {offer.capitalize()} ({clean_suffix})', fontsize=16, weight='bold', pad=12)

        leg = fig.legend(legend_handles, legend_labels, title='Emotion', loc='center right', 
                         bbox_to_anchor=(0.99, 0.5), fontsize=12, frameon=True)
        leg.get_frame().set_edgecolor('#AAAAAA')
        leg.get_frame().set_linewidth(1.2)

        plt.suptitle(f"{TARGET_COMPONENT} Waveforms - Exp 2", fontsize=20, weight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0.03, 0.88, 0.95])
        
        plt.savefig(save_path, dpi=300, format='tiff')
        plt.close()

# ==============================================================================
# 4. HELPERS
# ==============================================================================

def prep_conditions(df):
    if 'Offers_Other' in df.columns:
        f = ((df['Offers_Other'].isin([5,6])) & (df['Offers_You'].isin([5,4])))
        u = ((df['Offers_Other'].isin([8,9])) & (df['Offers_You'].isin([2,1])))
        df['offer_type'] = np.where(f, 'fair', np.where(u, 'unfair', None))
    if 'offer_type' not in df.columns: return df
    return df.dropna(subset=['offer_type', 'emotion'])

def load_data(folder, desc):
    if not folder.exists(): print(f"❌ Missing: {folder}"); return None, None, None
    files = sorted(folder.glob("Vp*_epo.csv"))
    if not files: return None, None, None
    
    topo, wave = [], []
    temp = pd.read_csv(files[0], nrows=1)
    eeg = [c for c in ALL_EEG_CHANNELS if c in temp.columns]
    roi_chs = [c for c in CURR_CFG['roi'] if c in temp.columns]
    
    for f in tqdm(files, desc=desc):
        try:
            df = pd.read_csv(f, low_memory=False)
            if df.empty: continue
            if df[eeg[0]].abs().max() < 1.0: df[eeg] *= 1e6 
            
            raw_id = f.name.split('_')[0] 
            df['participant_id'] = raw_id
            
            ptp = df.groupby('index')[eeg].max() - df.groupby('index')[eeg].min()
            valid = ptp[(ptp < REJECT_PTP_THRESHOLD_UV).all(axis=1)].index
            if len(valid)==0: continue
            df = df[df['index'].isin(valid)]
            
            win_min, win_max = CURR_CFG['window']
            mask = (df['time'] >= win_min) & (df['time'] <= win_max)
            avg = df[mask].groupby(['participant_id','index'])[eeg].mean().reset_index()
            cols_keep = ['participant_id','index','emotion','Offers_Other','Offers_You']
            avail_cols = [c for c in cols_keep if c in df.columns]
            meta = df[mask].groupby(['participant_id','index'])[avail_cols].first().reset_index()
            topo.append(pd.merge(avg, meta, on=['participant_id','index']))
            
            cols_wave = ['participant_id','index','time'] + roi_chs + avail_cols
            cols_wave = [c for c in cols_wave if c in df.columns]
            wave.append(df[cols_wave].copy())
        except: pass
    
    if not topo: return None, None, None
    return pd.concat(topo), pd.concat(wave), eeg

def load_bl(path):
    if not path.exists(): print(f"❌ Missing Baseline File: {path}"); return None
    df = pd.read_csv(path)
    
    tgt_col = 'Baseline_LPP_offer'
    if tgt_col not in df.columns:
        print(f"⚠️ '{tgt_col}' not found. Searching for generic baseline...")
        possibles = [c for c in df.columns if 'Baseline' in c]
        if possibles: tgt_col = possibles[0]
        else: return None
    
    if 'participant_id' not in df.columns and 'sub_id' in df.columns:
        df.rename(columns={'sub_id':'participant_id'}, inplace=True)
    return df[['participant_id','index',tgt_col]].rename(columns={tgt_col:'BL'})

# ==============================================================================
# 5. REGRESSION ANALYSIS MODULE (EXP 2 - NO INTERACTION)
# ==============================================================================

class RegressionAnalysis:
    def __init__(self):
        self.out = PATHS["results"] / "Regression_Results"
        self.out.mkdir(parents=True, exist_ok=True)
        self.topo_dir = self.out / "topomap_data_for_R"
        self.topo_dir.mkdir(exist_ok=True)
        self.viz = VisualizationEngine()

    def run(self):
        print(f"\n🚀 Regression Mode (Exp 2 - Simultaneous): {TARGET_COMPONENT}")
        print("   -> Model: Signal ~ Emo + Offer + Emo*Offer + Baseline")
        
        df_topo, df_wave, chans = load_data(PATHS["reg_epochs"], f"{TARGET_COMPONENT} Epochs")
        if df_topo is None: return
        
        print(f"   Loading Baseline from: {PATHS['reg_base'].parent.name}")
        df_base = load_bl(PATHS["reg_base"])
        if df_base is None: return
        
        print("   Aligning data...")
        df_topo['participant_id'] = df_topo['participant_id'].astype(str)
        df_wave['participant_id'] = df_wave['participant_id'].astype(str)
        df_base['participant_id'] = df_base['participant_id'].astype(str)
        
        df_fin_topo = pd.merge(df_topo, df_base, on=['participant_id', 'index'], how='inner')
        df_fin_topo = prep_conditions(df_fin_topo)
        
        df_fin_wave = pd.merge(df_wave, df_base, on=['participant_id', 'index'], how='inner')
        df_fin_wave = prep_conditions(df_fin_wave)
        
        n_match = len(df_fin_topo[['participant_id','index']].drop_duplicates())
        print(f"   Matched Trials: {n_match}")
        if n_match == 0: return

        for e in COLORS: 
            df_fin_topo[f'e_{e}'] = (df_fin_topo['emotion'] == e).astype(int)
        df_fin_topo['oc'] = df_fin_topo['offer_type'].map({'fair': -1, 'unfair': 1})

        self._generate_topomap_csv(df_fin_topo, chans)
        self._save_channel_locations(chans)
        del df_topo, df_fin_topo; gc.collect()
        
        print("   Calculating Waveform Regression...")
        pure_effects, times = self._perform_regression_roi(df_fin_wave)
        
        self.viz.plot_unified_panels(
            pure_effects, np.array(times)*1000, 
            "Regression-Corrected (Exp 2 Model)", 
            self.out/f"{TARGET_COMPONENT}_Regression_Unified.tif"
        )
        self._save_waveform_csv(pure_effects, times)
        print(f"Done. Results at: {self.out}")

    def _generate_topomap_csv(self, df, channels):
        print("   Generating Topomap Data...")
        dt = df.dropna(subset=['BL'])
        X = self._make_design_matrix(dt) 
        
        rows = []
        for ch in tqdm(channels, desc="Channel Reg"):
            if ch not in dt.columns: continue
            y = dt[ch].values
            try:
                b = np.linalg.lstsq(X, y, rcond=None)[0]
                row = {'channel': ch}
                
                # Reconstruction: Evaluate at Average Baseline (BL=0)
                # Model: Int(0) + Emo(1-4) + Offer(5) + Emo*Offer(6-9) + BL(10)
                for ofr in OFFER_TYPES:
                    ov = -1 if ofr == 'fair' else 1
                    for emo in COLORS:
                        v = b[0] 
                        if emo != 'neu':
                            idx = ['aff', 'dis', 'dom', 'enj'].index(emo)
                            v += b[1+idx] + b[6+idx]*ov
                        v += b[5]*ov
                        row[f'raw_{emo}_{ofr}'] = v
                rows.append(row)
            except: pass
        pd.DataFrame(rows).to_csv(self.topo_dir / f"{TARGET_COMPONENT}_topomap_data.csv", index=False)

    def _perform_regression_roi(self, df):
        roi_chs = [c for c in CURR_CFG['roi'] if c in df.columns]
        df['ROI'] = df[roi_chs].mean(axis=1)
        
        times = sorted([t for t in df['time'].unique() if PLOT_WINDOW[0]<=t<=PLOT_WINDOW[1]])
        pure = {f'{o}_{e}':[] for o in OFFER_TYPES for e in COLORS}
        
        for e in ['aff','dis','dom','enj']: df[f'e_{e}'] = (df['emotion']==e).astype(int)
        df['oc'] = df['offer_type'].map({'fair':-1, 'unfair':1})
        
        for t in tqdm(times, desc="Timepoints"):
            dt = df[df['time']==t].dropna(subset=['ROI', 'BL'])
            if len(dt)<20: 
                for k in pure: pure[k].append(np.nan); continue
            
            X = self._make_design_matrix(dt)
            y = dt['ROI'].values
            try:
                b = np.linalg.lstsq(X, y, rcond=None)[0]
                for o in OFFER_TYPES:
                    ov = -1 if o=='fair' else 1
                    for e in COLORS:
                        v = b[0]
                        if e!='neu': 
                            idx = ['aff','dis','dom','enj'].index(e)
                            v += b[1+idx] + b[6+idx]*ov
                        v += b[5]*ov
                        pure[f'{o}_{e}'].append(v)
            except:
                for k in pure: pure[k].append(np.nan)
        return pure, times

    def _make_design_matrix(self, dt):
        """
        [EXP 2 MODEL - SIMULTANEOUS]
        Structure of X (11 columns):
        0: Intercept
        1-4: Emotion
        5: Offer
        6-9: Emo * Offer
        10: Baseline Main Effect (No Interaction)
        """
        X_list = [np.ones(len(dt))] # 0. Intercept
        
        for e in ['aff','dis','dom','enj']: 
            X_list.append(dt[f'e_{e}'].values) # 1-4. Emo
            
        X_list.append(dt['oc'].values) # 5. Offer
        
        for e in ['aff','dis','dom','enj']:
            X_list.append(dt[f'e_{e}'].values * dt['oc'].values) # 6-9. Emo*Offer
            
        X_list.append(dt['BL'].values) # 10. Baseline (Main Only)
        
        return np.column_stack(X_list)

    def _save_waveform_csv(self, pure_data, times):
        df = pd.DataFrame({'time': times})
        for k, v in pure_data.items():
            if len(v) == len(times): df[k] = v
        df.to_csv(self.out / f"{TARGET_COMPONENT}_waveform_values.csv", index=False)
        
    def _save_channel_locations(self, channels):
        src = PATHS["locs_source"]
        if src.exists():
            try: shutil.copy(src, self.out / "channel_locations.csv"); return
            except: pass
        rows = [{'channel': ch, 'x': 0, 'y': 0} for ch in channels]
        pd.DataFrame(rows).to_csv(self.out / "channel_locations.csv", index=False)

if __name__ == "__main__":
    try:
        print(f"=== PROCESSING COMPONENT (Exp 2): {TARGET_COMPONENT} ===")
        print(f"Mode: Regression Only (No Interaction Model)")
        RegressionAnalysis().run()
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()