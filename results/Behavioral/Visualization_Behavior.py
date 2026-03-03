#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Behavioral Visualization Master Pipeline (v3.0.0 - Ultimate Edition)
================================================================================
Description:
    Generates publication-quality figures based on General Linear Mixed Model 
    (GLMM) outputs from upstream R scripts (`Sta_Behaviour_Master.Rmd`).
    
    Features:
    - 3-Way Interaction Faceting: Automatically splits E1 vs E2 for CrossExp data.
    - Advanced Rainclouds: Paired half-violins with jittered raw data and boxplots.
    - Diagnostics Module: Heatmaps and Axiom-violation scatter plots.
    - Automated Documentation: Generates interpretation guides for diagnostics.

Date: 2026-03-03
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
from matplotlib.ticker import MaxNLocator

# ==============================================================================
# 1) Global Configuration
# ==============================================================================
EXPERIMENT_VERSION = "E1"
ERROR_BAR_TYPE = "SE"
CI_MULTIPLIER = 1.96
RT_Y_MIN = 600
RT_Y_MAX = None 

LABELS = [
    "Type_Rejection_Rate", "Type_Response_Time", "Unfair_Rejection_RT",
    "CrossExp_Rejection_Rate", "CrossExp_Response_Time"
]

LABEL_MAP = {"dis": "Disgust", "dom": "Dominance", "neu": "Neutral", "aff": "Affiliative", "enj": "Reward", "fair": "Fair", "unfair": "Unfair"}
EMOTION_ORDER = ["dis", "dom", "neu", "aff", "enj"]
COLOR_MAP = {"dis": "#E64B35", "dom": "#F39B7F", "neu": "#8491B4", "aff": "#91D1C2", "enj": "#3C5488"}

# ==============================================================================
# 2) Path Resolution & Utilities
# ==============================================================================
def detect_project_root(start: Path) -> Path | None:
    for parent in [start.parent] + list(start.parents)[:6]:
        if (parent / "results").exists() or (parent / "data").exists(): return parent
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

def find_trials_csv(project_root: Path, exp_version: str) -> Path | None:
    all_trials = list(project_root.rglob("trials.csv"))
    if not all_trials: return None
    strict = [p for p in all_trials if exp_version in p.parts and "Method_Regression" in p.parts]
    if strict: return strict[0]
    vers = [p for p in all_trials if exp_version in p.parts]
    return vers[0] if vers else all_trials[0]

def get_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns: return c
    return None

def normalize_emotion(x): return str(x).strip().lower() if pd.notna(x) else x

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
def plot_interaction_line(df, y_col, lower_col, upper_col, ylabel, title, filename):
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
            ax.errorbar(sub[x_axis], y, yerr=yerr, marker="o", label=LABEL_MAP.get(emo, emo), color=COLOR_MAP.get(emo, "black"), capsize=4, lw=2, markersize=6)
            
        if i == 0: ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(f"{title} ({exp})" if has_exp else title, fontweight="bold")
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        else: ax.set_ylim(0, 1.05)
        sns.despine(ax=ax)
        
    axes[-1].legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    plt.tight_layout(); plt.savefig(filename, dpi=300); plt.close(fig)

def plot_interaction_bar(df, y_col, lower_col, upper_col, ylabel, title, filename):
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
        if ax_i == 0: ax.set_ylabel(ylabel)
        ax.set_title(f"{title} ({exp})" if has_exp else title, fontweight="bold")
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        else: ax.set_ylim(0, 1.05)
        sns.despine(ax=ax)
        
    axes[-1].legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    plt.tight_layout(); plt.savefig(filename, dpi=300); plt.close(fig)

def plot_forest_from_posthoc(df: pd.DataFrame, title: str, filename: Path, mode: str):
    if df.empty: return
    est_col = get_first_col(df, ["estimate", "emmean", "value", "odds.ratio"])
    se_col = get_first_col(df, ["SE", "std.error", "SE."])
    p_col = get_first_col(df, ["p.value", "p_val", "p"])
    contrast_col = "contrast" if "contrast" in df.columns else None
    if not est_col or not p_col: return

    labels = df[contrast_col].astype(str) if contrast_col else df.index.astype(str)
    for col in ["Exp", "emotion", "offer_type"]:
        if col in df.columns and col != contrast_col: labels = df[col].astype(str) + " | " + labels
            
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
    if se_col: ax.errorbar(df_plot["x"], y_pos, xerr=[df_plot["x"] - df_plot["x_lo"], df_plot["x_hi"] - df_plot["x"]], fmt="none", ecolor=colors, capsize=0, zorder=2)
    ax.set_yticks(y_pos); ax.set_yticklabels(df_plot["label"])
    ax.axvline(ref, color="black", linestyle=":", lw=1)
    ax.set_xlabel(xlab); ax.set_title(title)
    sns.despine(); plt.tight_layout(); plt.savefig(filename, dpi=300); plt.close(fig)

    # ==============================================================================
# 4) Raw Data Loading & Advanced Raincloud Plotting
# ==============================================================================
def load_and_clean_trials(trials_path: Path) -> pd.DataFrame:
    df = pd.read_csv(trials_path)
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
    return df

def plot_facet_paired_box_violin(
    df_raw: pd.DataFrame, y_var: str, y_label: str, title: str,
    output_path_png: Path, output_path_pdf: Path | None = None,
    subject_col: str = "participant_id", emotion_col: str = "emotion",
    offer_col: str = "offer_type", offer_order=("fair", "unfair"),
    label_map=None, color_map=None,
    violin_alpha=0.25, box_alpha=0.45, point_alpha=0.75, point_size=28,
    jitter=0.12, pair_gap=0.55, group_gap=0.95, bw_adjust=0.85
):
    if label_map is None: label_map = {}
    if color_map is None: color_map = {}
    df_agg = df_raw.groupby([subject_col, emotion_col, offer_col], as_index=False)[y_var].mean()
    df_agg = df_agg[df_agg[offer_col].isin(list(offer_order))].copy()

    is_0_100 = ("rejection" in y_label.lower()) or (y_var.lower() == "rejection_rate")
    is_rt = ("ms" in y_label.lower() or y_var.lower() == "rt")
    
    if is_0_100: y_min, y_max = 0.0, 100.0
    elif is_rt and RT_Y_MIN is not None and RT_Y_MAX is not None: y_min, y_max = float(RT_Y_MIN), float(RT_Y_MAX)
    else:
        ylim = _nice_ylim(df_agg[y_var])
        if ylim is None: return
        y_min, y_max = float(ylim[0]), float(ylim[1])

    y_grid = np.linspace(y_min, y_max, 250)
    positions, tick_positions, x = [], [], 0.0
    for _ in EMOTION_ORDER:
        positions.append((x, x + pair_gap))
        tick_positions.append(x + pair_gap/2)
        x = x + pair_gap + group_gap

    fig, axes = plt.subplots(1, 2, figsize=(14.8, 5.3), sharey=True)
    axes = np.array(axes).ravel()

    for ax_i, offer in enumerate(offer_order):
        ax = axes[ax_i]
        sub_offer = df_agg[df_agg[offer_col] == offer].copy()
        if sub_offer.empty: continue
        ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.35, zorder=0)

        for emo_idx, emo in enumerate(EMOTION_ORDER):
            box_pos, vio_pos = positions[emo_idx]
            sub_emo = sub_offer[sub_offer[emotion_col] == emo]
            y_vals = pd.to_numeric(sub_emo[y_var], errors="coerce").dropna().values
            if len(y_vals) < 2: continue
            color = color_map.get(emo, "#808080")

            # Boxplot
            ax.boxplot(y_vals, positions=[box_pos], widths=0.42, patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor=_rgba(color, box_alpha), edgecolor="#3A3A3A", linewidth=1.25),
                       medianprops=dict(color="#1F1F1F", linewidth=1.7), zorder=2)
            # Scatter
            ax.scatter(box_pos + np.random.uniform(-jitter, jitter, size=len(y_vals)), y_vals, 
                       s=point_size, c=[_rgba(color, point_alpha)], edgecolors="white", linewidths=0.75, zorder=3)
            # Violin
            kde_data = np.concatenate([y_vals, -y_vals, 200.0 - y_vals]) if is_0_100 else y_vals
            try:
                kde = gaussian_kde(kde_data[(kde_data >= -50)&(kde_data <= 150)] if is_0_100 else kde_data, bw_method="scott")
                kde.set_bandwidth(kde.factor * bw_adjust)
                dens = kde(y_grid)
                dens = dens / dens.max() if dens.max() > 0 else dens
                x_right = vio_pos + dens * 0.55
                ax.fill(np.concatenate([np.full_like(x_right, vio_pos), x_right[::-1]]), 
                        np.concatenate([y_grid, y_grid[::-1]]), facecolor=_rgba(color, violin_alpha), zorder=1)
                ax.plot(x_right, y_grid, color=_rgba(color, 0.65), linewidth=1.2, zorder=2)
            except: pass

        ax.set_title("Fair" if offer == "fair" else "Unfair", fontsize=14, fontweight="bold")
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([label_map.get(e, e) for e in EMOTION_ORDER])
        ax.set_xlim(positions[0][0] - 0.75, positions[-1][1] + 0.75)
        ax.set_ylim(y_min, y_max)
        if ax_i == 0: ax.set_ylabel(y_label, fontsize=13, fontweight="bold")
        sns.despine(ax=ax)

    fig.suptitle(title, fontsize=18, fontweight="bold", y=1.03)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path_png, dpi=300, bbox_inches="tight")
    if output_path_pdf: plt.savefig(output_path_pdf, transparent=True, bbox_inches="tight")
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
    plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close(fig)

def plot_diagnostic_fairness_scatter(df_raw: pd.DataFrame, output_path: Path):
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

    ax.set_title("Subject Diagnostic: Offer Fairness Sensitivity", fontweight="bold")
    ax.set_xlabel("Rejection Rate on FAIR Offers (%)"); ax.set_ylabel("Rejection Rate on UNFAIR Offers (%)")
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend(loc="lower right", frameon=True)
    sns.despine(); plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close(fig)

def plot_diagnostic_emotion_scatter(df_raw: pd.DataFrame, output_path: Path):
    if "rejection_rate" not in df_raw.columns: return
    df_emo = df_raw.groupby(["participant_id", "emotion"], as_index=False)["rejection_rate"].mean()
    df_range = df_emo.groupby("participant_id")["rejection_rate"].agg(emo_range=lambda x: x.max()-x.min(), mean_rej="mean").reset_index()

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_range["mean_rej"], df_range["emo_range"], alpha=0.6, edgecolors="white", s=80, c="#F39B7F", zorder=3)
    ax.axhline(50, color="#E64B35", linestyle="--", lw=1.5, alpha=0.8, zorder=1, label="Extreme Emotion Bias (>50%)")
    
    for _, row in df_range.iterrows():
        if row["emo_range"] > 50:
            ax.annotate(row["participant_id"], (row["mean_rej"], row["emo_range"]), xytext=(5, 5), textcoords="offset points", fontsize=8, color="#E64B35", fontweight="bold")

    ax.set_title("Subject Diagnostic: Global Emotion Volatility", fontweight="bold")
    ax.set_xlabel("Overall Average Rejection Rate (%)"); ax.set_ylabel("Emotion-driven Volatility (Max - Min %)")
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend(loc="upper right", frameon=True)
    sns.despine(); plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close(fig)

    # ==============================================================================
# 6) Automated Documentation Generation
# ==============================================================================
def generate_diagnostics_readme(target_dir: Path):
    """Generates a detailed txt guide inside the Diagnostics folder."""
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
  * EXAMPLE: If you see "Vp0015" in the bottom right corner (X=80, Y=20), this 
    means Vp0015 rejects 80% of Fair offers but accepts Unfair offers. This 
    participant likely misunderstood the buttons.

3. Subject_Emotion_Scatter.png
---------------------------------------------------------
- What it is: Evaluates how much a participant's decision is driven EXCLUSIVELY 
  by the emotional face, regardless of the financial offer.
- How to read:
  * Y-axis represents "Volatility": The maximum difference in rejection rates 
    caused solely by changing the emotion.
  * Flagged Subjects: Any subject above the 50% dashed line is flagged.
  * EXAMPLE: If a subject has a Y-value of 80%, it means when seeing a 'Reward' 
    face they might reject 10%, but when seeing a 'Disgust' face they reject 90%, 
    completely ignoring whether the offer was 5:5 or 9:1. This indicates an 
    extreme affective bias that overpowers the economic task.

NOTE: Do not blindly exclude flagged subjects. These plots provide empirical 
justification for sensitivity analyses (e.g., running the LMM with and without 
these outliers to prove robustness).
================================================================================"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

# ==============================================================================
# 7) Main Execution Pipeline
# ==============================================================================
def process_label_folder(label_dir: Path, figures_dir: Path, exp_version: str):
    print(f"\n>>> Processing Label: {label_dir.name} [{exp_version}]")
    excel_candidates = list(label_dir.glob(f"STATS_REPORT_*.xlsx"))
    if not excel_candidates: return
    xls = pd.ExcelFile(excel_candidates[0])

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
                    y_use, l_use, u_use, ylab = "RT_ms", "lower_ms", "upper_ms", f"Reaction Time (ms) ({ERROR_BAR_TYPE})"
                else:
                    if ERROR_BAR_TYPE == "SE":
                        df_desc["__LCL_SE"], df_desc["__UCL_SE"] = df_desc[y_col] - df_desc[se_col], df_desc[y_col] + df_desc[se_col]
                        l_use, u_use = "__LCL_SE", "__UCL_SE"
                    else:
                        df_desc["__LCL"], df_desc["__UCL"] = df_desc[y_col] - CI_MULTIPLIER * df_desc[se_col], df_desc[y_col] + CI_MULTIPLIER * df_desc[se_col]
                        l_use, u_use = lower_col if lower_col else "__LCL", upper_col if upper_col else "__UCL"
                    y_use, ylab = y_col, f"Rejection Probability ({ERROR_BAR_TYPE})"

                tag = f"{exp_version}_{label_dir.name}"
                plot_interaction_line(df_desc, y_use, l_use, u_use, ylab, f"{tag}: Interaction", figures_dir / f"{tag}_Interaction_Line.png")
                plot_interaction_bar(df_desc, y_use, l_use, u_use, ylab, f"{tag}: Interaction", figures_dir / f"{tag}_Interaction_Bar.png")

    for sheet in [s for s in xls.sheet_names if s.startswith("PostHoc_")]:
        try:
            df_ph = pd.read_excel(xls, sheet_name=sheet)
            if "emotion" in df_ph.columns: df_ph["emotion"] = df_ph["emotion"].apply(normalize_emotion)
            plot_forest_from_posthoc(df_ph, f"{exp_version}: {sheet}", figures_dir / f"{exp_version}_{label_dir.name}_{sheet}_Forest.png", "rejection" if "Rejection" in label_dir.name else "rt")
        except: pass

def plot_distributions_from_trials(trials_path: Path, figures_dir: Path, exp_version: str):
    print(f"\n>>> Processing Raw Data for Rainclouds & Diagnostics [{exp_version}]...")
    df_trials = load_and_clean_trials(trials_path)
    
    # Rainclouds
    rain_dir = figures_dir / "Raincloud"
    rain_dir.mkdir(parents=True, exist_ok=True)
    if "RT" in df_trials.columns: plot_facet_paired_box_violin(df_trials, "RT", "Reaction Time (ms)", f"Distribution RT ({exp_version})", rain_dir / f"Dist_{exp_version}_RT_Raincloud.png", color_map=COLOR_MAP, label_map=LABEL_MAP)
    if "rejection_rate" in df_trials.columns: plot_facet_paired_box_violin(df_trials, "rejection_rate", "Rejection Rate (%)", f"Distribution Rejection ({exp_version})", rain_dir / f"Dist_{exp_version}_Rejection_Raincloud.png", color_map=COLOR_MAP, label_map=LABEL_MAP)

    # Diagnostics
    heat_dir = figures_dir / "Diagnostics"
    heat_dir.mkdir(parents=True, exist_ok=True)
    generate_diagnostics_readme(heat_dir)
    
    if "RT" in df_trials.columns: plot_individual_heatmap(df_trials, "RT", "Mean RT (ms)", f"Diagnostic: Subject RT ({exp_version})", heat_dir / f"Diag_{exp_version}_RT_Heatmap.png")
    if "rejection_rate" in df_trials.columns:
        plot_individual_heatmap(df_trials, "rejection_rate", "Rejection Rate (%)", f"Diagnostic: Subject Rejection ({exp_version})", heat_dir / f"Diag_{exp_version}_Rejection_Heatmap.png")
        plot_diagnostic_fairness_scatter(df_trials, heat_dir / f"Diag_{exp_version}_Fairness_Scatter.png")
        plot_diagnostic_emotion_scatter(df_trials, heat_dir / f"Diag_{exp_version}_Emotion_Scatter.png")

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
    
    trials_path = find_trials_csv(root, exp_version=run_version)
    if trials_path and trials_path.exists():
        try: plot_distributions_from_trials(trials_path, figures_dir, exp_version=run_version)
        except Exception as e: print(f"   [Warn] Distribution pipeline failed: {e}")
    else: print("\n>>> [Skip] trials.csv not found.")

    print("\n>>> Visualization Complete!")