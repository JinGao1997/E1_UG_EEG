#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Behavioral Visualization Master Pipeline
================================================================================
Description:
    Generates publication-quality figures based on General Linear Mixed Model 
    (GLMM) and Linear Mixed Model (LMM) outputs from upstream R scripts.
    
    Architecture:
    - Data-driven visualization mapping: Dynamically parses Excel sheets generated 
      by the upstream hierarchical statistical gating mechanism.
    - Multi-source data fusion: Accommodates both single-experiment and 
      cross-experiment concatenated raw data (trials.csv).
    - Publication Standards: Implements strict APA-7th typographic conventions, 
      including standard error bar caps (I-bars) for traditional academic compliance.
    - Faceted Rain-on-Cloud: Deploys Trellis/Facet design (1x2 grid) to fully separate 
      Fair and Unfair offers. Restores the high-density "Rain-in-Cloud" overlay.
    - Dynamic Bounding Box Layout: Utilizes tight_layout with restricted rect bounds
      to perfectly isolate global legends and suptitles from facet titles.

Date: 2026-03-13
================================================================================
"""

from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

# ==============================================================================
# 1) Global Configuration
# ==============================================================================
EXPERIMENT_VERSION = "E1" #"CrossExp_E1_vs_E2" or "E1" or "E2"
ERROR_BAR_TYPE = "SE"
CI_MULTIPLIER = 1.0  
RT_Y_MIN = 400
RT_Y_MAX = None 

LABELS = [
    "Type_Rejection_Rate", "Type_Response_Time", "Unfair_Rejection_RT",
    "CrossExp_Rejection_Rate", "CrossExp_Response_Time"
]

LABEL_MAP = {
    "dis": "Disgust", "dom": "Dominance", "neu": "Neutral", 
    "aff": "Affiliative", "enj": "Reward", "fair": "Fair", "unfair": "Unfair"
}
EMOTION_ORDER = ["dis", "dom", "neu", "aff", "enj"]
COLOR_MAP = {
    "dis": "#E64B35", "dom": "#F39B7F", "neu": "#8491B4", 
    "aff": "#91D1C2", "enj": "#3C5488"
}

POSTHOC_SHEET_PREFIXES = (
    "PostHoc_", 
    "SimpleSimple_", 
    "Simple_", 
    "Interaction_Contrast", 
    "Joint_2Way_"
)

# ==============================================================================
# 2) Path Resolution & Utilities
# ==============================================================================
def detect_project_root(start: Path) -> Path | None:
    for parent in [start.parent] + list(start.parents)[:6]:
        if (parent / "results").exists() or (parent / "data").exists(): 
            return parent
    return None

def choose_output_root(project_root: Path, exp_version: str, prefer_debug: bool = False) -> Path:
    beh_root = project_root / "results" / "Behavioral"
    if exp_version == "CrossExp_E1_vs_E2":
        cross_dirs = [beh_root / "CrossExp_E1_vs_E2_Pub_Output_Final", beh_root / "CrossExp_E1_vs_E2_Pub_Output", beh_root / "CrossExp_E1_vs_E2_Debug_Output"]
        for d in cross_dirs:
            if d.exists(): return d
        raise FileNotFoundError(f"CrossExp output directory not found in {beh_root}.")

    pub_dirs = [beh_root / f"{exp_version}_Pub_Output_Final", beh_root / f"{exp_version}_Pub_Output"]
    dbg_dirs = [beh_root / f"{exp_version}_Debug_Output_Final", beh_root / f"{exp_version}_Debug_Output"]

    if prefer_debug:
        for d in dbg_dirs: 
            if d.exists(): return d
    for d in pub_dirs:
        if d.exists(): return d
    for d in dbg_dirs:
        if d.exists(): return d

    raise FileNotFoundError(f"Output root for {exp_version} could not be resolved in {beh_root}.")

def find_trials_csv(project_root: Path, exp_version: str) -> list[Path]:
    all_trials = list(project_root.rglob("trials.csv"))
    if not all_trials: return []
    if exp_version == "CrossExp_E1_vs_E2":
        return [p for p in all_trials if "Method_Regression" in str(p) and ("E1" in str(p) or "E2" in str(p))]
    strict = [p for p in all_trials if exp_version in str(p) and "Method_Regression" in str(p)]
    if strict: return strict
    vers = [p for p in all_trials if exp_version in str(p)]
    return vers if vers else [all_trials[0]]

def get_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns: return c
    return None

def normalize_emotion(x): 
    return str(x).strip().lower() if pd.notna(x) else x

def _rgba(hex_color: str, alpha: float) -> tuple:
    r, g, b = mcolors.to_rgb(hex_color)
    return (r, g, b, alpha)

def _nice_ylim(values: pd.Series, lower_q=0.01, upper_q=0.99, pad_ratio=0.08):
    v = pd.to_numeric(values, errors="coerce").dropna()
    if v.empty: return None
    lo, hi = float(v.quantile(lower_q)), float(v.quantile(upper_q))
    if hi <= lo: lo, hi = float(v.min()), float(v.max())
    pad = (hi - lo) * pad_ratio if hi > lo else 1.0
    return lo - pad, hi + pad

# ==============================================================================
# 3) Plotting: GLMM Interactions (Line & Bar) & Forest Plots
# ==============================================================================
def plot_interaction_line(df, y_col, lower_col, upper_col, ylabel, main_title, filename):
    x_axis = "offer_type" if "offer_type" in df.columns else ("offer_ratio" if "offer_ratio" in df.columns else None)
    if not x_axis: return
    
    has_exp = "Exp" in df.columns
    exps = sorted(df["Exp"].dropna().unique()) if has_exp else [None]
    fig, axes = plt.subplots(1, len(exps), figsize=(7 * len(exps), 5), sharey=True, squeeze=False)
    axes = axes.flatten()
    x_levels = ["Fair", "Unfair"] if x_axis == "offer_type" else ["5:5", "4:6", "3:7", "2:8", "1:9"]
    
    for i, exp in enumerate(exps):
        ax = axes[i]
        df_exp = df[df["Exp"] == exp].copy() if has_exp else df.copy()
        for emo in EMOTION_ORDER:
            sub = df_exp[df_exp["emotion"] == emo].copy()
            if sub.empty: continue
            sub = sub.set_index(x_axis).reindex([l for l in x_levels if l in sub[x_axis].values]).reset_index()
            y, yerr = sub[y_col], [sub[y_col] - sub[lower_col], sub[upper_col] - sub[y_col]]
            ax.errorbar(sub[x_axis], y, yerr=yerr, marker="o", label=LABEL_MAP.get(emo, emo), color=COLOR_MAP.get(emo, "black"), capsize=4, capthick=1.5, lw=2, markersize=6)
            
        ax.tick_params(labelleft=True)
        ax.set_ylabel(ylabel, fontsize=12)
        
        if has_exp:
            exp_val = str(exp).replace("E", "") if str(exp).startswith("E") else str(exp)
            ax.set_title(f"Exp. {exp_val}", fontweight="bold", fontsize=14, pad=12)
        else:
            ax.set_title(main_title, fontweight="bold", fontsize=14, pad=12)
            
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        else: ax.set_ylim(0, 1.05)
        sns.despine(ax=ax)
        
    handles, labels = axes[0].get_legend_handles_labels()
    axes[-1].legend(handles, labels, bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, title="Emotion Context", title_fontproperties={'weight':'bold'})
    
    if has_exp:
        fig.suptitle(main_title, fontsize=16, fontweight="bold", y=1.05)
        
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_interaction_bar(df, y_col, lower_col, upper_col, ylabel, main_title, filename):
    x_axis = "offer_type" if "offer_type" in df.columns else ("offer_ratio" if "offer_ratio" in df.columns else None)
    if not x_axis: return
    has_exp = "Exp" in df.columns
    exps = sorted(df["Exp"].dropna().unique()) if has_exp else [None]
    
    fig, axes = plt.subplots(1, len(exps), figsize=(8 * len(exps), 5), sharey=True, squeeze=False)
    axes = axes.flatten()
    levels = [l for l in (["Fair", "Unfair"] if x_axis == "offer_type" else ["5:5", "4:6", "3:7", "2:8", "1:9"]) if l in df[x_axis].unique()]
    x_indices, width = np.arange(len(levels)), 0.15
    
    for ax_i, exp in enumerate(exps):
        ax = axes[ax_i]
        df_exp = df[df["Exp"] == exp].copy() if has_exp else df.copy()
        for i, emo in enumerate(EMOTION_ORDER):
            sub = df_exp[df_exp["emotion"] == emo].copy()
            if sub.empty: continue
            sub = sub.set_index(x_axis).reindex(levels).reset_index()
            y = sub[y_col].fillna(0)
            sub[lower_col], sub[upper_col] = sub[lower_col].fillna(y), sub[upper_col].fillna(y)
            yerr = [y - sub[lower_col], sub[upper_col] - y]
            offset = (i - 2) * width
            ax.bar(x_indices + offset, y, width=width, label=LABEL_MAP.get(emo, emo) if ax_i==0 else "", color=COLOR_MAP.get(emo, "#808080"), edgecolor="black", zorder=3)
            ax.errorbar(x_indices + offset, y, yerr=yerr, fmt="none", ecolor="black", capsize=3, zorder=4)
            
        ax.set_xticks(x_indices)
        ax.set_xticklabels([str(l) for l in levels])
        
        ax.tick_params(labelleft=True)
        ax.set_ylabel(ylabel, fontsize=12)
        
        if has_exp:
            exp_val = str(exp).replace("E", "") if str(exp).startswith("E") else str(exp)
            ax.set_title(f"Exp. {exp_val}", fontweight="bold", fontsize=14, pad=12)
        else:
            ax.set_title(main_title, fontweight="bold", fontsize=14, pad=12)
            
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        else: ax.set_ylim(0, 1.05)
        sns.despine(ax=ax)
        
    handles, labels = axes[0].get_legend_handles_labels()
    axes[-1].legend(handles, labels, bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, title="Emotion Context", title_fontproperties={'weight':'bold'})
    
    if has_exp:
        fig.suptitle(main_title, fontsize=16, fontweight="bold", y=1.05)
        
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_forest_from_posthoc(df: pd.DataFrame, title: str, filename: Path, mode: str):
    if df.empty: return
    est_col = get_first_col(df, ["estimate", "emmean", "value", "odds.ratio"])
    se_col = get_first_col(df, ["SE", "std.error", "SE."])
    p_col = get_first_col(df, ["p.value", "p_val", "p"])
    contrast_col = "contrast" if "contrast" in df.columns else None
    if not est_col or not p_col: return

    labels = pd.Series(df[contrast_col].astype(str) if contrast_col else df.index.astype(str))
    labels = labels.str.replace("fair", "Fair").str.replace("unfair", "Unfair")
    for k, v in LABEL_MAP.items():
        labels = labels.str.replace(fr'\b{k}\b', v, regex=True)
        
    for col in ["Exp", "emotion", "offer_type"]:
        if col in df.columns and col != contrast_col: 
            prefix = df[col].astype(str)
            if col == "Exp":
                prefix = prefix.replace({"E1": "Exp. 1", "E2": "Exp. 2"})
            elif col == "offer_type":
                prefix = prefix.str.capitalize()
            elif col == "emotion":
                prefix = prefix.map(lambda x: LABEL_MAP.get(x, x))
            
            labels = prefix + " | " + labels
            
    df_plot = df.copy().reset_index(drop=True)
    df_plot["label"] = labels

    if mode == "rejection":
        df_plot["x"] = np.exp(df_plot[est_col].astype(float))
        ref, xlab = 1.0, "Odds Ratio"
        if se_col:
            se = df_plot[se_col].astype(float)
            df_plot["x_lo"] = np.exp(df_plot[est_col].astype(float) - CI_MULTIPLIER * se)
            df_plot["x_hi"] = np.exp(df_plot[est_col].astype(float) + CI_MULTIPLIER * se)
    else:
        df_plot["x"] = df_plot[est_col].astype(float)
        ref, xlab = 0.0, "Estimate (Beta)"
        if se_col:
            se = df_plot[se_col].astype(float)
            df_plot["x_lo"], df_plot["x_hi"] = df_plot["x"] - CI_MULTIPLIER * se, df_plot["x"] + CI_MULTIPLIER * se

    fig, ax = plt.subplots(figsize=(10, max(4, len(df_plot) * 0.42 + 2)))
    y_pos = np.arange(len(df_plot))
    colors = ["#d73027" if float(p) < 0.05 else "#bdbdbd" for p in df_plot[p_col]]
    
    ax.scatter(df_plot["x"], y_pos, color=colors, s=60, zorder=3)
    if se_col: 
        ax.errorbar(df_plot["x"], y_pos, xerr=[df_plot["x"] - df_plot["x_lo"], df_plot["x_hi"] - df_plot["x"]], fmt="none", ecolor=colors, capsize=0, zorder=2)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_plot["label"])
    ax.axvline(ref, color="black", linestyle=":", lw=1)
    ax.set_xlabel(xlab)
    ax.set_title(title, pad=15, fontweight="bold", fontsize=14)
    
    sns.despine(); plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

# ==============================================================================
# 4) Statistical Extraction & Advanced Raincloud Plotting
# ==============================================================================
def load_and_clean_trials(trials_paths: list[Path]) -> pd.DataFrame:
    df_list = []
    for path in trials_paths:
        df = pd.read_csv(path)
        path_str = str(path)
        exp_label = "E1" if "E1" in path_str else ("E2" if "E2" in path_str else "E_UNK")
        df["Exp"] = exp_label
        
        if "participant_id" in df.columns:
            def clean_id(x):
                s = str(x)
                if s.startswith("Vp") and len(s) >= 6: return s
                digits = "".join([ch for ch in s if ch.isdigit()])
                return f"Vp{int(digits):04d}" if digits else s
            df["participant_id"] = df["participant_id"].apply(clean_id)
            
        if {"Offers_You", "Offers_Other"}.issubset(df.columns):
            ratio_val = df["Offers_You"] / (df["Offers_You"] + df["Offers_Other"]).replace(0, np.nan)
            df["offer_ratio"] = ratio_val.apply(lambda r: "5:5" if abs(r-0.5)<0.01 else ("4:6" if abs(r-0.4)<0.01 else ("3:7" if abs(r-0.3)<0.01 else ("2:8" if abs(r-0.2)<0.01 else ("1:9" if abs(r-0.1)<0.01 else np.nan)))))
            df["offer_type"] = df["offer_ratio"].apply(lambda r: "fair" if r in ["5:5", "4:6"] else ("unfair" if r in ["2:8", "1:9"] else "drop"))
            df = df[df["offer_type"] != "drop"].copy()
            
        if "emotion" in df.columns:
            df["emotion"] = df["emotion"].apply(normalize_emotion)
            df = df[df["emotion"].isin(EMOTION_ORDER)].copy()
            
        if "reaction" in df.columns:
            df["is_reject"] = (df["reaction"] == 2).astype(int)
            df["rejection_rate"] = df["is_reject"] * 100.0
            
        if "RT" in df.columns: 
            df = df[(df["RT"] >= 150) & (df["RT"] <= 3000)].copy()
            
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

def fetch_lmm_stats(out_root: Path, exp_version: str, y_var: str) -> pd.DataFrame | None:
    label_prefix = "Response_Time" if "RT" in y_var else "Rejection_Rate"
    label_dir_name = f"CrossExp_{label_prefix}" if "CrossExp" in exp_version else f"Type_{label_prefix}"
    label_dir = out_root / label_dir_name
    
    if not label_dir.exists(): return None
    excel_files = list(label_dir.glob("STATS_REPORT_*.xlsx"))
    if not excel_files: return None
    
    try:
        df = pd.read_excel(excel_files[0], sheet_name="Descriptive_Means_SE")
        if "emotion" in df.columns: 
            df["emotion"] = df["emotion"].apply(normalize_emotion)
            
        y_col = get_first_col(df, ["emmean", "Mean", "prob", "response"])
        se_col = get_first_col(df, ["SE", "std.error"])
        lower_col = get_first_col(df, ["lower.CL", "asymp.LCL", "lower", "LCL"])
        upper_col = get_first_col(df, ["upper.CL", "asymp.UCL", "upper", "UCL"])
        
        if not y_col: return None
        
        res = df.copy()
        res["offer_type"] = res.get("offer_type", res.get("offer_ratio", "")).astype(str).str.lower()
        
        mean_numeric = pd.to_numeric(res[y_col], errors="coerce").mean()
        
        if "RT" in y_var and mean_numeric < 20 and se_col:
            res["mean_val"] = np.exp(res[y_col].astype(float))
            se_ms = res["mean_val"] * res[se_col].astype(float)
            res["lower_val"] = res["mean_val"] - (CI_MULTIPLIER * se_ms)
            res["upper_val"] = res["mean_val"] + (CI_MULTIPLIER * se_ms)
        else:
            res["mean_val"] = res[y_col].astype(float)
            if lower_col and upper_col and CI_MULTIPLIER > 1.0:
                res["lower_val"] = res[lower_col].astype(float)
                res["upper_val"] = res[upper_col].astype(float)
            elif se_col:
                res["lower_val"] = res["mean_val"] - CI_MULTIPLIER * res[se_col].astype(float)
                res["upper_val"] = res["mean_val"] + CI_MULTIPLIER * res[se_col].astype(float)
            else:
                res["lower_val"] = res["mean_val"]
                res["upper_val"] = res["mean_val"]
                
        is_rejection = "rejection" in y_var.lower() or "rate" in y_var.lower()
        if is_rejection and res["mean_val"].max() <= 1.05:
            res["mean_val"] *= 100.0
            res["lower_val"] *= 100.0
            res["upper_val"] *= 100.0
            
        return res
    except Exception as e:
        print(f"   [Warn] Could not extract LMM emmeans for {y_var}. Falling back to arithmetic means. Details: {e}")
        return None

def plot_faceted_raincloud(
    df_raw: pd.DataFrame, y_var: str, y_label: str, title: str,
    output_path_png: Path, lmm_stats: pd.DataFrame | None = None,
    subject_col: str = "participant_id", emotion_col: str = "emotion", offer_col: str = "offer_type"
):
    df_agg = df_raw.groupby([subject_col, emotion_col, offer_col], as_index=False)[y_var].mean()
    
    is_0_100 = ("rejection" in y_label.lower()) or (y_var.lower() == "rejection_rate")
    is_rt = ("ms" in y_label.lower() or y_var.lower() == "rt")
    
    if is_0_100: 
        y_min, y_max = 0.0, 100.0
    elif is_rt and RT_Y_MIN is not None and RT_Y_MAX is not None: 
        y_min, y_max = float(RT_Y_MIN), float(RT_Y_MAX)
    else:
        ylim = _nice_ylim(df_agg[y_var])
        if ylim is None: return
        y_min, y_max = float(ylim[0]), float(ylim[1])

    # 1. Height increased to 5.5 to compensate for the top safe-zone, maintaining exact plumpness
    fig, axes = plt.subplots(1, 2, figsize=(16.0, 5.5), sharey=True)

    max_dens_width = 0.42        
    pt_size = 22
    kde_base_offset = 0.0        
    stat_offset = 0.10           

    offers = ["fair", "unfair"]
    titles = ["Fair Offers", "Unfair Offers"]
    
    for ax_i, offer in enumerate(offers):
        ax = axes[ax_i]
        ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.4, zorder=0)

        for emo_idx, emo in enumerate(EMOTION_ORDER):
            color = COLOR_MAP.get(emo, "#808080")
            x_center = float(emo_idx)

            sub = df_agg[(df_agg[emotion_col] == emo) & (df_agg[offer_col] == offer)]
            y_vals = pd.to_numeric(sub[y_var], errors="coerce").dropna().values
            if len(y_vals) < 3: continue

            matched_lmm = False
            if lmm_stats is not None:
                mask = (lmm_stats["emotion"] == emo) & (lmm_stats["offer_type"] == offer)
                if mask.any():
                    row = lmm_stats[mask].iloc[0]
                    mean_val = row["mean_val"]
                    lower_val = row["lower_val"]
                    upper_val = row["upper_val"]
                    matched_lmm = True
                    
            if not matched_lmm:
                mean_val = np.mean(y_vals)
                se_val = np.std(y_vals, ddof=1) / np.sqrt(len(y_vals))
                lower_val, upper_val = mean_val - CI_MULTIPLIER * se_val, mean_val + CI_MULTIPLIER * se_val

            kde_fc = _rgba(color, 0.15) if offer == "fair" else _rgba(color, 0.75)
            kde_ec = color if offer == "fair" else "none"
            scat_fc = "none" if offer == "fair" else color
            scat_ec = color if offer == "fair" else "white"            
            stat_mfc = "white" if offer == "fair" else color

            try:
                y_min_sub, y_max_sub = y_vals.min(), y_vals.max()
                y_range = y_max_sub - y_min_sub if y_max_sub > y_min_sub else 1.0
                eval_min = max(y_min, y_min_sub - y_range * 0.15)
                eval_max = min(y_max, y_max_sub + y_range * 0.15)
                y_grid_sub = np.linspace(eval_min, eval_max, 200)

                kde = gaussian_kde(y_vals, bw_method="scott")
                kde.set_bandwidth(kde.factor * 0.85) 
                
                dens = kde(y_grid_sub)
                dens = (dens / dens.max()) * max_dens_width
                
                x_base_line = x_center + kde_base_offset
                x_curve = x_base_line + dens
                
                ax.fill_betweenx(y_grid_sub, x_base_line, x_curve, facecolor=kde_fc, edgecolor=kde_ec, linewidth=1.5, zorder=2)
            except np.linalg.LinAlgError: pass

            jitter = np.random.uniform(0.02, max_dens_width - 0.04, size=len(y_vals))
            x_scatter = x_center + jitter
            ax.scatter(x_scatter, y_vals, s=pt_size, facecolors=scat_fc, edgecolors=scat_ec, alpha=0.9, linewidths=0.9, zorder=3)

            x_stat = x_center - stat_offset
            y_err_lower, y_err_upper = [[mean_val - lower_val]], [[upper_val - mean_val]]
            ax.errorbar(x_stat, mean_val, yerr=[y_err_lower[0], y_err_upper[0]], fmt='o',
                        mfc=stat_mfc, mec=color, ecolor=color, capsize=4, capthick=1.5, elinewidth=1.8, markersize=7, zorder=5)

        ax.set_xticks(range(len(EMOTION_ORDER)))
        ax.set_xticklabels([LABEL_MAP.get(e, e) for e in EMOTION_ORDER], fontsize=15, fontweight="bold")
        
        ax.set_xlim(-0.45, len(EMOTION_ORDER) - 0.35)
        ax.set_ylim(y_min, y_max)
        ax.set_title(titles[ax_i], fontsize=20, fontweight="bold", pad=15)
        
        if ax_i == 0:
            ax.set_ylabel(y_label, fontsize=16, fontweight="bold")
        sns.despine(ax=ax)

    # 2. Main Title placement
    fig.suptitle(title, fontsize=24, fontweight="bold", y=0.98) 
    
    # 3. Legend placement safely below Suptitle but well above Facet Titles
    legend_elements = [
        mpatches.Patch(facecolor=_rgba("#808080", 0.15), edgecolor="#808080", label="Fair Offer", linewidth=1.5),
        mpatches.Patch(facecolor=_rgba("#808080", 0.75), edgecolor="none", label="Unfair Offer"),
        mlines.Line2D([], [], color='#808080', marker='o', linestyle='-', linewidth=1.5, markersize=7, mfc='black', mec='black', label="Estimated Marginal Mean \u00B1 1 SE")
    ]
    fig.legend(handles=legend_elements, bbox_to_anchor=(0.5, 0.89), loc="center", ncol=3, frameon=False, fontsize=14)
    
    # 4. [THE MAGIC SHIELD]: Forces the entire subplot grid (including "Fair/Unfair Offers" titles)
    # to stay strictly below the 84% height line. This guarantees zero overlap forever.
    plt.tight_layout(rect=[0, 0.0, 1.0, 0.84])
    
    plt.savefig(output_path_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

# ==============================================================================
# 5) Subject Diagnostics & Axiom Validation
# ==============================================================================
def plot_individual_heatmap(df_raw: pd.DataFrame, val_col: str, val_label: str, title: str, output_path: Path):
    if df_raw.empty or val_col not in df_raw.columns: return
    df_agg = df_raw.groupby(["participant_id", "emotion", "offer_type"], as_index=False)[val_col].mean()
    df_agg["condition"] = df_agg["emotion"].astype(str) + "_" + df_agg["offer_type"].astype(str)
    df_pivot = df_agg.pivot(index="participant_id", columns="condition", values=val_col)

    ordered_cols = [f"{emo}_{offer}" for offer in ["fair", "unfair"] for emo in EMOTION_ORDER if f"{emo}_{offer}" in df_pivot.columns]
    df_pivot = df_pivot[ordered_cols]
    
    fair_cols = [c for c in df_pivot.columns if "fair" in c and "unfair" not in c]
    unfair_cols = [c for c in df_pivot.columns if "unfair" in c]
    if fair_cols and unfair_cols:
        df_pivot["sensitivity"] = (df_pivot[unfair_cols].mean(axis=1) - df_pivot[fair_cols].mean(axis=1)) * (1 if "rejection" in val_col.lower() else -1)
        df_pivot = df_pivot.sort_values("sensitivity", ascending=False).drop(columns=["sensitivity"])

    fig, ax = plt.subplots(figsize=(10, max(6.0, len(df_pivot) * 0.28)))
    cmap, vmin, vmax = ("coolwarm", 0, 100) if "rejection" in val_col.lower() else ("viridis", None, None)
    sns.heatmap(df_pivot, cmap=cmap, vmin=vmin, vmax=vmax, linewidths=0.5, linecolor='lightgray', cbar_kws={'label': val_label}, ax=ax)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=20)
    ax.set_ylabel("Participant ID", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_diagnostic_fairness_scatter(df_raw: pd.DataFrame, output_path: Path, title: str):
    if "rejection_rate" not in df_raw.columns: return
    df_agg = df_raw.groupby(["participant_id", "offer_type"], as_index=False)["rejection_rate"].mean()
    df_pivot = df_agg.pivot(index="participant_id", columns="offer_type", values="rejection_rate").fillna(0)
    fair_col, unfair_col = get_first_col(df_pivot, ["fair", "Fair"]), get_first_col(df_pivot, ["unfair", "Unfair"])
    if not fair_col or not unfair_col: return

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_pivot[fair_col], df_pivot[unfair_col], alpha=0.6, edgecolors="white", s=80, c="#3C5488", zorder=3)
    ax.plot([-5, 105], [-5, 105], color="#E64B35", linestyle="--", lw=1.5, alpha=0.5, zorder=1, label="Zero Sensitivity ($y=x$)")
    ax.axvline(25, color="gray", linestyle=":", alpha=0.5); ax.axhline(60, color="gray", linestyle=":", alpha=0.5)
    ax.fill_between([-5, 25], 60, 105, color="#91D1C2", alpha=0.15, zorder=0, label="Rational Behavior Zone")
    
    for subj, row in df_pivot.iterrows():
        f_rej, u_rej = row[fair_col], row[unfair_col]
        if (f_rej > 25) or (u_rej < 60) or ((u_rej - f_rej) < 20):
            ax.annotate(subj, (f_rej, u_rej), xytext=(5, 5), textcoords="offset points", fontsize=8, color="#E64B35", fontweight="bold", bbox=dict(boxstyle="round", fc="white", ec="none", alpha=0.7))

    ax.set_title(title, fontweight="bold", fontsize=15, pad=12)
    ax.set_xlabel("Rejection Rate on FAIR Offers (%)"); ax.set_ylabel("Rejection Rate on UNFAIR Offers (%)")
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend(loc="lower right", frameon=True)
    sns.despine(); plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_diagnostic_emotion_scatter(df_raw: pd.DataFrame, output_path: Path, title: str):
    if "rejection_rate" not in df_raw.columns: return
    df_emo = df_raw.groupby(["participant_id", "emotion"], as_index=False)["rejection_rate"].mean()
    df_range = df_emo.groupby("participant_id")["rejection_rate"].agg(emo_range=lambda x: x.max()-x.min(), mean_rej="mean").reset_index()

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_range["mean_rej"], df_range["emo_range"], alpha=0.6, edgecolors="white", s=80, c="#F39B7F", zorder=3)
    ax.axhline(50, color="#E64B35", linestyle="--", lw=1.5, alpha=0.8, zorder=1, label="Extreme Emotion Bias (>50%)")
    
    for _, row in df_range.iterrows():
        if row["emo_range"] > 50:
            ax.annotate(row["participant_id"], (row["mean_rej"], row["emo_range"]), xytext=(5, 5), textcoords="offset points", fontsize=8, color="#E64B35", fontweight="bold")

    ax.set_title(title, fontweight="bold", fontsize=15, pad=12)
    ax.set_xlabel("Overall Average Rejection Rate (%)"); ax.set_ylabel("Emotion-Driven Volatility (Max - Min %)")
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend(loc="upper right", frameon=True)
    sns.despine(); plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# ==============================================================================
# 6) Automated Documentation Generation
# ==============================================================================
def generate_diagnostics_readme(target_dir: Path):
    readme_path = target_dir / "README_Diagnostics_Guide.txt"
    content = """================================================================================
DIAGNOSTIC VISUALIZATIONS INTERPRETATION GUIDE
================================================================================
This folder contains orthogonal diagnostic plots designed to identify participants
who violate fundamental economic axioms or task instructions.

1. Subject_Rejection_Heatmap.png / Subject_RT_Heatmap.png
---------------------------------------------------------
- What it is: A matrix where rows are participants and columns are experimental 
  conditions (e.g., neu_fair, dis_unfair).
- How to read:
  * Look for horizontal homogeneity: A subject whose row is entirely red (100% 
    rejection across ALL conditions) or entirely blue (0% rejection) is treating 
    the task as a rigid mechanical response rather than making economic choices.
  * Sorting: Subjects are sorted by their "fairness sensitivity" (Unfair minus Fair). 
    Subjects at the bottom of the heatmap have inverted sensitivity.

2. Subject_Fairness_Scatter.png
---------------------------------------------------------
- What it is: Maps the rejection rate of Fair offers (X-axis) against Unfair 
  offers (Y-axis) for each participant.
- Economic Axiom: Rational behavior dictates that Unfair offers should be 
  rejected significantly more often than Fair offers (Y > X).
- How to read:
  * Green Zone (Top-Left): "Rational Behavior Zone". High rejection of unfair, 
    low rejection of fair.
  * Red Dashed Line (Y = X): "Zero Sensitivity". Subjects near this line ignore 
    the money being offered.
  * Flagged Subjects (Red Labels): The script automatically annotates subjects 
    who violate the axiom (e.g., rejecting Fair > 25%, rejecting Unfair < 60%, 
    or having a margin < 20%). 

3. Subject_Emotion_Scatter.png
---------------------------------------------------------
- What it is: Evaluates how much a participant's decision is driven EXCLUSIVELY 
  by the emotional face, regardless of the financial offer.
- How to read:
  * Y-axis represents "Volatility": The maximum difference in rejection rates 
    caused solely by changing the emotion.
  * Flagged Subjects: Any subject above the 50% dashed line is flagged.

NOTE: Do not blindly exclude flagged subjects. These plots provide empirical 
justification for sensitivity analyses.
================================================================================"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

# ==============================================================================
# 7) Main Execution Pipeline
# ==============================================================================
def format_academic_sheet_name(sheet: str) -> str:
    s = sheet.replace("PostHoc_Main_", "Main Effect: ")
    s = s.replace("PostHoc_", "Pairwise: ")
    s = s.replace("SimpleSimple_", "Simple Simple: ")
    s = s.replace("Simple_", "Simple: ")
    s = s.replace("Interaction_Contrast", "Interaction Contrasts")
    s = s.replace("Joint_2Way_", "Joint 2-Way: ")
    s = s.replace("_", " ").strip()
    replacements = {"offer type": "Offer Fairness", "emotion": "Emotion", "Exp": "Experiment", "Emo": "Emotion", "by": "across"}
    for old, new in replacements.items(): s = s.replace(old, new)
    return s

def process_label_folder(label_dir: Path, figures_dir: Path, exp_version: str):
    print(f"\n>>> Processing Label: {label_dir.name} [{exp_version}]")
    excel_candidates = list(label_dir.glob(f"STATS_REPORT_*.xlsx"))
    if not excel_candidates: return
    xls = pd.ExcelFile(excel_candidates[0])

    is_cross_exp = "CrossExp" in exp_version
    if exp_version.startswith("E") and exp_version[1:].isdigit():
        global_exp_str = f"Exp. {exp_version[1:]}"
    elif is_cross_exp:
        global_exp_str = "Cross-Experiment"
    else:
        global_exp_str = str(exp_version)

    interaction_title = "Emotion \u00D7 Offer Fairness" if is_cross_exp else f"Emotion \u00D7 Offer Fairness ({global_exp_str})"

    if "Descriptive_Means_SE" in xls.sheet_names:
        df_desc = pd.read_excel(xls, sheet_name="Descriptive_Means_SE")
        if "emotion" in df_desc.columns: df_desc["emotion"] = df_desc["emotion"].apply(normalize_emotion)
        y_col = "Mean" if "Mean" in df_desc.columns else get_first_col(df_desc, ["prob", "response", "emmean"])
        
        if y_col:
            se_col = get_first_col(df_desc, ["SE", "std.error"])
            lower_col = get_first_col(df_desc, ["asymp.LCL", "lower.CL", "lower", "LCL"])
            upper_col = get_first_col(df_desc, ["asymp.UCL", "upper.CL", "upper", "UCL"])

            if se_col:
                is_rt = ("Response_Time" in label_dir.name) or ("RT" in label_dir.name)
                mean_numeric = float(pd.to_numeric(df_desc[y_col], errors="coerce").dropna().mean()) if not df_desc.empty else np.nan
                
                if is_rt and np.isfinite(mean_numeric) and mean_numeric < 20:
                    df_desc["RT_ms"] = np.exp(df_desc[y_col].astype(float))
                    se_ms = df_desc["RT_ms"] * df_desc[se_col].astype(float)
                    mult = 1.0 if ERROR_BAR_TYPE == "SE" else CI_MULTIPLIER
                    df_desc["lower_ms"], df_desc["upper_ms"] = df_desc["RT_ms"] - (mult * se_ms), df_desc["RT_ms"] + (mult * se_ms)
                    y_use, l_use, u_use, ylab = "RT_ms", "lower_ms", "upper_ms", f"Reaction Time (ms, \u00B1 {ERROR_BAR_TYPE})"
                else:
                    if ERROR_BAR_TYPE == "SE":
                        df_desc["__LCL_SE"], df_desc["__UCL_SE"] = df_desc[y_col] - df_desc[se_col], df_desc[y_col] + df_desc[se_col]
                        l_use, u_use = "__LCL_SE", "__UCL_SE"
                    else:
                        df_desc["__LCL"], df_desc["__UCL"] = df_desc[y_col] - CI_MULTIPLIER * df_desc[se_col], df_desc[y_col] + CI_MULTIPLIER * df_desc[se_col]
                        l_use, u_use = lower_col if lower_col else "__LCL", upper_col if upper_col else "__UCL"
                    y_use, ylab = y_col, f"Rejection Rate (\u00B1 {ERROR_BAR_TYPE})"

                tag = f"{exp_version}_{label_dir.name}"
                plot_interaction_line(df_desc, y_use, l_use, u_use, ylab, interaction_title, figures_dir / f"{tag}_Interaction_Line.png")
                plot_interaction_bar(df_desc, y_use, l_use, u_use, ylab, interaction_title, figures_dir / f"{tag}_Interaction_Bar.png")

    for sheet in [s for s in xls.sheet_names if s.startswith(POSTHOC_SHEET_PREFIXES)]:
        try:
            df_ph = pd.read_excel(xls, sheet_name=sheet)
            if "emotion" in df_ph.columns: df_ph["emotion"] = df_ph["emotion"].apply(normalize_emotion)
            plot_forest_from_posthoc(df_ph, f"{format_academic_sheet_name(sheet)} ({global_exp_str})", figures_dir / f"{exp_version}_{label_dir.name}_{sheet}_Forest.png", "rejection" if "Rejection" in label_dir.name else "rt")
        except Exception as e:
            pass

def plot_distributions_from_trials(trials_paths: list[Path], figures_dir: Path, exp_version: str, out_root: Path):
    print(f"\n>>> Processing Raw Data for Rainclouds & Diagnostics [{exp_version}]...")
    df_trials = load_and_clean_trials(trials_paths)
    if df_trials.empty: return
        
    exps = df_trials["Exp"].unique()
    rain_dir, heat_dir = figures_dir / "Raincloud", figures_dir / "Diagnostics"
    rain_dir.mkdir(parents=True, exist_ok=True); heat_dir.mkdir(parents=True, exist_ok=True)
    generate_diagnostics_readme(heat_dir)
    
    for exp in exps:
        print(f"   -> Generating sub-renderings for batch: {exp}")
        df_exp = df_trials[df_trials["Exp"] == exp].copy()
        tag = f"CrossExp_{exp}" if exp_version == "CrossExp_E1_vs_E2" else exp_version
        exp_display = f"Exp. {exp[1:]}" if isinstance(exp, str) and exp.startswith("E") and exp[1:].isdigit() else (str(exp) if exp else "Overall")
        title_suffix = f" ({exp_display})"
        
        if "RT" in df_exp.columns: 
            lmm_stats = fetch_lmm_stats(out_root, exp_version, "RT")
            plot_faceted_raincloud(df_exp, "RT", "Reaction Time (ms)", f"Reaction Time{title_suffix}", rain_dir / f"Dist_{tag}_RT_SplitRain.png", lmm_stats=lmm_stats)
            plot_individual_heatmap(df_exp, "RT", "Mean RT (ms)", f"Diagnostic: RT Matrix{title_suffix}", heat_dir / f"Diag_{tag}_RT_Heatmap.png")
            
        if "rejection_rate" in df_exp.columns: 
            lmm_stats = fetch_lmm_stats(out_root, exp_version, "rejection_rate")
            plot_faceted_raincloud(df_exp, "rejection_rate", "Rejection Rate (%)", f"Rejection Rate{title_suffix}", rain_dir / f"Dist_{tag}_Rejection_SplitRain.png", lmm_stats=lmm_stats)
            plot_individual_heatmap(df_exp, "rejection_rate", "Rejection Rate (%)", f"Diagnostic: Rejection Rate Matrix{title_suffix}", heat_dir / f"Diag_{tag}_Rejection_Heatmap.png")
            plot_diagnostic_fairness_scatter(df_exp, heat_dir / f"Diag_{tag}_Fairness_Scatter.png", f"Diagnostic: Fairness Sensitivity{title_suffix}")
            plot_diagnostic_emotion_scatter(df_exp, heat_dir / f"Diag_{tag}_Emotion_Scatter.png", f"Diagnostic: Emotion Volatility{title_suffix}")

if __name__ == "__main__":
    run_version = EXPERIMENT_VERSION
    if "--e1" in sys.argv: run_version = "E1"
    elif "--e2" in sys.argv: run_version = "E2"
    elif "--crossexp" in sys.argv: run_version = "CrossExp_E1_vs_E2"

    root = detect_project_root(Path(__file__).resolve())
    if not root: raise FileNotFoundError("Project root not found.")

    out_root = choose_output_root(root, exp_version=run_version, prefer_debug=("--debug" in sys.argv))
    figures_dir = out_root / "Figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Info: Experiment Version: {run_version}")
    print(f"Info: Output Root:        {out_root}")

    for label in LABELS:
        if (out_root / label).exists(): process_label_folder(out_root / label, figures_dir, run_version)
        else: print(f"   [Skip] Label missing: {label}")
    
    trials_paths = find_trials_csv(root, exp_version=run_version)
    if trials_paths:
        try: plot_distributions_from_trials(trials_paths, figures_dir, run_version, out_root)
        except Exception as e: print(f"   [Warn] Distribution pipeline failed: {e}")
    else: print("\n>>> [Skip] trials.csv not found.")

    print("\n>>> Visualization Complete!")