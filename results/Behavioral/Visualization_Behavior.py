#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Sta_Behaviour Downstream Visualization Pipeline (v1.9.1 - Strict Full-Pipeline E1/E2 Isolation)
================================================================================
Description:
    Generates publication-quality figures based on Sta_Behaviour.Rmd outputs.
    
    [UPDATED v1.9.1]: Enforces strict E1/E2 isolation across the ENTIRE pipeline.
    - Stats Data (Excel): Strictly reads folders/files matching the E1/E2 version.
    - Raw Data (trials.csv): Attempts to locate version-specific raw data paths
      before falling back to the standard Method_Regression path.
    - Formatting: Fully expanded logic for maximal readability and maintenance.

Date: 2026-02-27
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
# 1) Configuration
# ==============================================================================

# Target Experiment Version to visualize. 
# Matches the 'experiment_version' variable in Sta_Behaviour.Rmd.
# Overridden via command line (e.g., `python script.py --e1`)
EXPERIMENT_VERSION = "E2"

# Determines the type of error bars rendered in interaction plots.
# Options: "SE" (Standard Error) or "CI" (95% Confidence Interval)
ERROR_BAR_TYPE = "SE"

# Fixed Y-axis limits for Reaction Time (RT) plots.
# Set MAX to None to enable auto-scaling and prevent error bar clipping.
RT_Y_MIN = 600
RT_Y_MAX = None 

LABELS = [
    "Type_Rejection_Rate",
    "Type_Response_Time",
    "Ratio_Rejection_Rate",
    "Ratio_Response_Time",
    "Unfair_Rejection_RT"
]

LABEL_MAP = {
    "dis": "Disgust",
    "dom": "Dominance",
    "neu": "Neutral",
    "aff": "Affiliative",
    "enj": "Reward",
    "fair": "Fair",
    "unfair": "Unfair",
    "Fair": "Fair",
    "Unfair": "Unfair",
}

EMOTION_ORDER = ["dis", "dom", "neu", "aff", "enj"]

# Required emotion palette (semantic mapping = emotion)
COLOR_MAP = {
    "dis": "#E64B35",
    "dom": "#F39B7F",
    "neu": "#8491B4",
    "aff": "#91D1C2",
    "enj": "#3C5488",
}

CI_MULTIPLIER = 1.96


# ==============================================================================
# 2) Utilities: Path Detection (STRICT E1/E2 ROUTING)
# ==============================================================================

def detect_project_root(start: Path) -> Path | None:
    """Climb up directories to find the project root containing 'results'."""
    for parent in [start.parent] + list(start.parents)[:6]:
        if (parent / "results").exists():
            return parent
    return None


def choose_output_root(project_root: Path, exp_version: str, prefer_debug: bool = False) -> Path:
    """Find the Behavioral output directory strictly matching the experiment version."""
    beh_root = project_root / "results" / "Behavioral"
    if not beh_root.exists():
        raise FileNotFoundError(f"Behavioral results directory not found at: {beh_root}")

    pub_dir = beh_root / f"{exp_version}_Pub_Output_Final"
    dbg_dir = beh_root / f"{exp_version}_Debug_Output_Final"

    if prefer_debug and dbg_dir.exists():
        return dbg_dir
    if pub_dir.exists():
        return pub_dir
    if dbg_dir.exists():
        return dbg_dir

    raise FileNotFoundError(
        f"No output root found for {exp_version} in {beh_root}. "
        f"Expected {pub_dir.name} or {dbg_dir.name}."
    )


def find_trials_csv(project_root: Path, exp_version: str) -> Path | None:
    """
    Locate trials.csv strictly enforcing E1/E2 distinction if possible.
    Searches for paths containing both the experiment version AND the Method_Regression pipeline signature.
    """
    all_trials = list(project_root.rglob("trials.csv"))
    if not all_trials:
        return None

    # Priority 1: Exact match containing both version label and standard pipeline path
    strict_matches = [
        p for p in all_trials 
        if exp_version in p.parts and "Method_Regression" in p.parts and "Stimulus_Locked" in p.parts
    ]
    if strict_matches:
        return strict_matches[0]
        
    # Priority 2: Contains the version label anywhere in the path
    version_matches = [p for p in all_trials if exp_version in p.parts]
    if version_matches:
        return version_matches[0]

    # Fallback: The standard pipeline path
    fallback_target = project_root / "data" / "02_Pipeline_Output" / "Method_Regression" / "Stimulus_Locked" / "trials.csv"
    if fallback_target.exists():
        print(f"   [WARN] Could not find '{exp_version}' in the path of trials.csv.")
        print(f"   [WARN] Falling back to default path: {fallback_target.relative_to(project_root)}")
        print(f"   [WARN] Ensure this workspace strictly contains {exp_version} raw data to prevent contamination.")
        return fallback_target

    return all_trials[0]


# ==============================================================================
# 3) Helpers: Columns & Normalization
# ==============================================================================

def get_first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_emotion(x):
    if pd.isna(x):
        return x
    return str(x).strip().lower()


# ==============================================================================
# 4) Plotting: Interaction Plots (Line & Bar)
# ==============================================================================

def plot_interaction_line(df, y_col, lower_col, upper_col, ylabel, title, filename):
    """Standard interaction line plot with error bars."""
    x_axis = "offer_ratio" if "offer_ratio" in df.columns else ("offer_type" if "offer_type" in df.columns else None)
    if x_axis is None:
        return

    fig, ax = plt.subplots(figsize=(7, 5))

    if x_axis == "offer_ratio":
        x_levels = ["5:5", "4:6", "3:7", "2:8", "1:9"]
    else:
        x_levels = ["Fair", "Unfair"]

    for emo in EMOTION_ORDER:
        sub = df[df["emotion"] == emo].copy()
        if sub.empty:
            continue

        sub = sub.set_index(x_axis).reindex([l for l in x_levels if l in sub[x_axis].values]).reset_index()
        y = sub[y_col]
        yerr = [y - sub[lower_col], sub[upper_col] - y]

        ax.errorbar(
            sub[x_axis], y, yerr=yerr,
            marker="o",
            label=LABEL_MAP.get(emo, emo),
            color=COLOR_MAP.get(emo, "black"),
            capsize=4, lw=2, markersize=6
        )

    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, title="Emotion")

    if "Time" in ylabel or "ms" in ylabel:
        if RT_Y_MIN is not None and RT_Y_MAX is not None:
            ax.set_ylim(RT_Y_MIN, RT_Y_MAX)
        elif RT_Y_MIN is not None:
            ax.set_ylim(bottom=RT_Y_MIN)
    else:
        ax.set_ylim(0, 1.05)

    sns.despine()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close(fig)
    print(f"   -> Saved Line Plot: {filename.name}")


def plot_interaction_bar(df, y_col, lower_col, upper_col, ylabel, title, filename):
    """Grouped bar plot for interaction effects."""
    x_axis = "offer_ratio" if "offer_ratio" in df.columns else ("offer_type" if "offer_type" in df.columns else None)
    if x_axis is None:
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    if x_axis == "offer_ratio":
        levels = [l for l in ["5:5", "4:6", "3:7", "2:8", "1:9"] if l in df[x_axis].unique()]
    else:
        levels = [l for l in ["Fair", "Unfair"] if l in df[x_axis].unique()]

    x_indices = np.arange(len(levels))
    width = 0.15

    for i, emo in enumerate(EMOTION_ORDER):
        sub = df[df["emotion"] == emo].copy()
        if sub.empty:
            continue

        sub = sub.set_index(x_axis).reindex(levels).reset_index()
        offset = (i - 2) * width
        y = sub[y_col].fillna(0)

        sub[lower_col] = sub[lower_col].fillna(y)
        sub[upper_col] = sub[upper_col].fillna(y)
        yerr = [y - sub[lower_col], sub[upper_col] - y]

        ax.bar(
            x_indices + offset, y,
            width=width,
            label=LABEL_MAP.get(emo, emo),
            color=COLOR_MAP.get(emo, "#808080"),
            edgecolor="black", linewidth=0.5,
            zorder=3
        )
        ax.errorbar(
            x_indices + offset, y,
            yerr=yerr,
            fmt="none", ecolor="black", capsize=3, zorder=4
        )

    ax.set_xticks(x_indices)
    ax.set_xticklabels([str(l) for l in levels])
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, title="Emotion")

    if "Time" in ylabel or "ms" in ylabel:
        if RT_Y_MIN is not None and RT_Y_MAX is not None:
            ax.set_ylim(RT_Y_MIN, RT_Y_MAX)
        elif RT_Y_MIN is not None:
            ax.set_ylim(bottom=RT_Y_MIN)
        else:
            min_val = float(df[lower_col].min())
            ax.set_ylim(bottom=max(0, min_val - 100))
    else:
        ax.set_ylim(0, 1.05)

    sns.despine()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close(fig)
    print(f"   -> Saved Bar Plot: {filename.name}")


# ==============================================================================
# 5) Plotting: Forest Plots
# ==============================================================================

def plot_forest_from_posthoc(df: pd.DataFrame, title: str, filename: Path, mode: str):
    """Forest plot for post-hoc contrasts."""
    if df.empty:
        return

    est_col = get_first_existing_col(df, ["estimate", "emmean", "value", "odds.ratio"])
    se_col = get_first_existing_col(df, ["SE", "std.error", "SE."])
    p_col = get_first_existing_col(df, ["p.value", "p_val", "p"])
    contrast_col = "contrast" if "contrast" in df.columns else None

    if est_col is None or p_col is None:
        return

    # Create Labels
    if contrast_col:
        if "emotion" in df.columns:
            labels = df["emotion"].astype(str) + ": " + df[contrast_col].astype(str)
        elif "offer_type" in df.columns:
            labels = df["offer_type"].astype(str) + ": " + df[contrast_col].astype(str)
        else:
            labels = df[contrast_col].astype(str)
    else:
        labels = df.index.astype(str)

    df_plot = df.copy().reset_index(drop=True)
    df_plot["label"] = labels

    if mode == "rejection":
        df_plot["x"] = np.exp(df_plot[est_col].astype(float))
        ref = 1.0
        xlab = "Odds Ratio"
        if se_col:
            se = df_plot[se_col].astype(float)
            df_plot["x_lo"] = np.exp(df_plot[est_col].astype(float) - CI_MULTIPLIER * se)
            df_plot["x_hi"] = np.exp(df_plot[est_col].astype(float) + CI_MULTIPLIER * se)
    else:
        df_plot["x"] = df_plot[est_col].astype(float)
        ref = 0.0
        xlab = "Estimate (Beta)"
        if se_col:
            se = df_plot[se_col].astype(float)
            df_plot["x_lo"] = df_plot["x"] - CI_MULTIPLIER * se
            df_plot["x_hi"] = df_plot["x"] + CI_MULTIPLIER * se

    fig, ax = plt.subplots(figsize=(9, max(4, len(df_plot) * 0.42 + 2)))
    y_pos = np.arange(len(df_plot))

    colors = ["#d73027" if float(p) < 0.05 else "#bdbdbd" for p in df_plot[p_col]]

    ax.scatter(df_plot["x"], y_pos, color=colors, s=60, zorder=3)

    if se_col:
        xerr_left = df_plot["x"] - df_plot["x_lo"]
        xerr_right = df_plot["x_hi"] - df_plot["x"]
        ax.errorbar(
            df_plot["x"], y_pos,
            xerr=[xerr_left, xerr_right],
            fmt="none", ecolor=colors, capsize=0, zorder=2
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_plot["label"])
    ax.axvline(ref, color="black", linestyle=":", lw=1)

    ax.set_xlabel(xlab)
    ax.set_title(title)

    sns.despine()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close(fig)
    print(f"   -> Saved Forest Plot: {filename.name}")


# ==============================================================================
# 6) Trials Loading & Cleaning
# ==============================================================================

def load_and_clean_trials(trials_path: Path) -> pd.DataFrame:
    """Best-effort replication of Sta_Behaviour.Rmd cleaning logic."""
    df = pd.read_csv(trials_path)

    if "participant_id" in df.columns:
        def clean_id(x):
            if pd.isna(x): return x
            s = str(x)
            if s.startswith("Vp") and len(s) >= 6: return s
            digits = "".join([ch for ch in s if ch.isdigit()])
            if digits == "": return s
            return f"Vp{int(digits):04d}"
        df["participant_id"] = df["participant_id"].apply(clean_id)

    if {"Offers_You", "Offers_Other"}.issubset(df.columns):
        denom = (df["Offers_You"] + df["Offers_Other"]).replace(0, np.nan)
        ratio_val = df["Offers_You"] / denom

        def map_ratio(r):
            if pd.isna(r): return np.nan
            if abs(r - 0.5) < 0.01: return "5:5"
            if abs(r - 0.4) < 0.01: return "4:6"
            if abs(r - 0.3) < 0.01: return "3:7"
            if abs(r - 0.2) < 0.01: return "2:8"
            if abs(r - 0.1) < 0.01: return "1:9"
            return np.nan

        df["offer_ratio"] = ratio_val.apply(map_ratio)

        def map_type(oratio):
            if pd.isna(oratio): return "drop"
            if oratio in ["5:5", "4:6"]: return "fair"
            if oratio in ["2:8", "1:9"]: return "unfair"
            return "drop"

        df["offer_type"] = df["offer_ratio"].apply(map_type)
        df = df[df["offer_type"] != "drop"].copy()

    if "emotion" in df.columns:
        df["emotion"] = df["emotion"].apply(normalize_emotion)
        df = df[df["emotion"].isin(EMOTION_ORDER)].copy()

    if "reaction" in df.columns:
        df["is_reject"] = (df["reaction"] == 2).astype(int)
        df["rejection_rate"] = df["is_reject"] * 100.0

    if "RT" in df.columns:
        df = df[(df["RT"] >= 150) & (df["RT"] <= 3000)].copy()

    required = {"participant_id", "emotion", "offer_type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Trials file missing required columns: {sorted(missing)}")

    return df


# ==============================================================================
# 7) Distribution Plots
# ==============================================================================

def _rgba(hex_color: str, alpha: float) -> tuple:
    r, g, b = mcolors.to_rgb(hex_color)
    return (r, g, b, alpha)

def _nice_ylim(values: pd.Series, lower_q=0.01, upper_q=0.99, pad_ratio=0.08):
    v = pd.to_numeric(values, errors="coerce").dropna()
    if v.empty: return None
    lo = float(v.quantile(lower_q))
    hi = float(v.quantile(upper_q))
    if hi <= lo: 
        lo, hi = float(v.min()), float(v.max())
    pad = (hi - lo) * pad_ratio if hi > lo else 1.0
    return lo - pad, hi + pad

def plot_facet_paired_box_violin(
    df_raw: pd.DataFrame, y_var: str, y_label: str, title: str,
    output_path_png: Path, output_path_pdf: Path | None = None,
    subject_col: str = "participant_id", emotion_col: str = "emotion",
    offer_col: str = "offer_type", offer_order=("fair", "unfair"),
    emotion_order=("dis", "dom", "neu", "aff", "enj"),
    label_map=None, color_map=None,
    violin_alpha=0.22, box_alpha=0.45, point_alpha=0.80, point_size=28,
    jitter=0.12, pair_gap=0.55, group_gap=0.95, bw_adjust=0.85,
    max_violin_width=0.55, outline_alpha=0.65, outline_lw=1.2, n_grid=250,
):
    """Draws raincloud-style distribution plots."""
    if label_map is None: label_map = {}
    if color_map is None: color_map = {}

    df_agg = df_raw.groupby([subject_col, emotion_col, offer_col], as_index=False)[y_var].mean()
    df_agg = df_agg[df_agg[offer_col].isin(list(offer_order))].copy()
    df_agg[emotion_col] = pd.Categorical(df_agg[emotion_col], categories=list(emotion_order), ordered=True)
    df_agg[offer_col] = pd.Categorical(df_agg[offer_col], categories=list(offer_order), ordered=True)

    is_bounded_0_100 = ("rejection" in y_label.lower()) or (y_var.lower() == "rejection_rate")
    is_rt = ("ms" in y_label.lower() or y_var.lower() == "rt")
    
    if is_bounded_0_100:
        y_min, y_max = 0.0, 100.0
    elif is_rt and RT_Y_MIN is not None and RT_Y_MAX is not None:
        y_min, y_max = float(RT_Y_MIN), float(RT_Y_MAX)
    else:
        ylim = _nice_ylim(df_agg[y_var])
        if ylim is None: return
        y_min, y_max = float(ylim[0]), float(ylim[1])
        if is_rt and y_min < 0: y_min = 0.0

    y_grid = np.linspace(y_min, y_max, n_grid)
    positions = []
    tick_positions = []
    x = 0.0
    for _ in emotion_order:
        box_pos = x
        vio_pos = x + pair_gap
        positions.append((box_pos, vio_pos))
        tick_positions.append((box_pos + vio_pos) / 2.0)
        x = vio_pos + group_gap

    x_min = positions[0][0] - 0.75
    x_max = positions[-1][1] + 0.75

    fig, axes = plt.subplots(1, 2, figsize=(14.8, 5.3), sharey=True)
    axes = np.array(axes).ravel()

    for ax_i, offer in enumerate(offer_order):
        ax = axes[ax_i]
        sub_offer = df_agg[df_agg[offer_col] == offer].copy()
        if sub_offer.empty:
            ax.set_axis_off()
            continue

        ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.35, zorder=0)

        for emo_idx, emo in enumerate(emotion_order):
            box_pos, vio_pos = positions[emo_idx]
            sub_emo = sub_offer[sub_offer[emotion_col] == emo]
            if sub_emo.empty: continue

            color = color_map.get(emo, "#808080")
            y_vals = pd.to_numeric(sub_emo[y_var], errors="coerce").dropna().values
            if len(y_vals) < 2: continue

            ax.boxplot(
                y_vals, positions=[box_pos], widths=0.42, patch_artist=True, showfliers=False,
                boxprops=dict(facecolor=_rgba(color, box_alpha), edgecolor="#3A3A3A", linewidth=1.25),
                whiskerprops=dict(color="#3A3A3A", linewidth=1.05),
                capprops=dict(color="#3A3A3A", linewidth=1.05),
                medianprops=dict(color="#1F1F1F", linewidth=1.7), zorder=2,
            )

            x_jit = box_pos + np.random.uniform(-jitter, jitter, size=len(y_vals))
            ax.scatter(
                x_jit, y_vals, s=point_size, c=[_rgba(color, point_alpha)],
                edgecolors="white", linewidths=0.75, zorder=3,
            )

            kde_data = y_vals.copy()
            if is_bounded_0_100:
                kde_data = np.concatenate([kde_data, -kde_data, 200.0 - kde_data])
                kde_data = kde_data[(kde_data >= -50) & (kde_data <= 150)]

            try:
                kde = gaussian_kde(kde_data, bw_method="scott")
                kde.set_bandwidth(kde.factor * bw_adjust)
                dens = kde(y_grid)
            except Exception:
                continue

            dens = dens / dens.max() if dens.max() > 0 else dens
            half_width = dens * max_violin_width

            x_right = vio_pos + half_width
            x_left = np.full_like(x_right, vio_pos)
            xs = np.concatenate([x_left, x_right[::-1]])
            ys = np.concatenate([y_grid, y_grid[::-1]])

            ax.fill(xs, ys, facecolor=_rgba(color, violin_alpha), edgecolor="none", zorder=1)
            ax.plot(x_right, y_grid, color=_rgba(color, outline_alpha), linewidth=outline_lw, zorder=2)

        facet_title = "Fair" if offer == "fair" else "Unfair"
        ax.set_title(facet_title, fontsize=14, fontweight="bold", pad=10)

        xt_labels = [label_map.get(e, e) for e in emotion_order]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(xt_labels, rotation=0)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.set_xlabel("")
        if ax_i == 0: 
            ax.set_ylabel(y_label, fontsize=13, fontweight="bold")
        else: 
            ax.set_ylabel("")
        sns.despine(ax=ax)

    fig.suptitle(title, fontsize=18, fontweight="bold", y=1.03)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    plt.savefig(output_path_png, dpi=300, bbox_inches="tight")
    if output_path_pdf is not None:
        plt.savefig(output_path_pdf, transparent=True, bbox_inches="tight")
    plt.close(fig)
    print(f"   -> Saved Distribution Figure: {output_path_png.name}")


# ==============================================================================
# 8) Main Execution Iteration
# ==============================================================================

def process_label_folder(label_dir: Path, figures_dir: Path, exp_version: str):
    """Processes Excel statistical reports and dispatches to plotting functions."""
    print(f"\n>>> Processing Label: {label_dir.name} [{exp_version}]")
    
    excel_candidates = list(label_dir.glob(f"STATS_REPORT_{exp_version}_*.xlsx"))
    if not excel_candidates:
        print(f"   [Skip] Expected Excel file for {exp_version} not found in: {label_dir.name}")
        return
        
    excel_file = excel_candidates[0]
    print(f"   -> Found Stats Report: {excel_file.name}")

    try:
        xls = pd.ExcelFile(excel_file)
    except Exception as e:
        print(f"   [Error] Could not read Excel file {excel_file.name}: {e}")
        return

    if "Descriptive_Means_SE" in xls.sheet_names:
        df_desc = pd.read_excel(xls, sheet_name="Descriptive_Means_SE")
        
        if "emotion" in df_desc.columns:
            df_desc["emotion"] = df_desc["emotion"].apply(normalize_emotion)
            
        y_col = "Mean" if "Mean" in df_desc.columns else get_first_existing_col(df_desc, ["prob", "response", "emmean"])
        
        if y_col is None:
            print("   [Skip] Descriptive_Means_SE sheet has no recognized mean column.")
        else:
            se_col = get_first_existing_col(df_desc, ["SE", "std.error"])
            lower_col = get_first_existing_col(df_desc, ["asymp.LCL", "lower.CL", "lower", "LCL"])
            upper_col = get_first_existing_col(df_desc, ["asymp.UCL", "upper.CL", "upper", "UCL"])

            if se_col is None:
                print("   [Skip] Descriptive_Means_SE missing standard error column.")
                return

            is_rt_label = ("Response_Time" in label_dir.name) or ("RT" in label_dir.name) or ("Time" in label_dir.name)
            mean_numeric = float(pd.to_numeric(df_desc[y_col], errors="coerce").dropna().mean()) if not df_desc.empty else np.nan
            err_suffix = "(+/- 1 SE)" if ERROR_BAR_TYPE == "SE" else "(95% CI)"

            # Check if values are in log scale (typical for RT LMM outputs)
            if is_rt_label and np.isfinite(mean_numeric) and mean_numeric < 20:
                print("   [Transform] Log-scale detected. Applying Delta Method for symmetric error bars in ms.")
                df_desc["RT_ms"] = np.exp(df_desc[y_col].astype(float))
                se_ms = df_desc["RT_ms"] * df_desc[se_col].astype(float)
                
                if ERROR_BAR_TYPE == "SE":
                    df_desc["lower_ms"] = df_desc["RT_ms"] - se_ms
                    df_desc["upper_ms"] = df_desc["RT_ms"] + se_ms
                else:
                    df_desc["lower_ms"] = df_desc["RT_ms"] - (CI_MULTIPLIER * se_ms)
                    df_desc["upper_ms"] = df_desc["RT_ms"] + (CI_MULTIPLIER * se_ms)
                    
                y_col_use = "RT_ms"
                l_col_use = "lower_ms"
                u_col_use = "upper_ms"
                ylabel = f"Reaction Time (ms) {err_suffix}"
                
            else:
                if ERROR_BAR_TYPE == "SE":
                    df_desc["__LCL_SE"] = df_desc[y_col] - df_desc[se_col]
                    df_desc["__UCL_SE"] = df_desc[y_col] + df_desc[se_col]
                    l_col_use = "__LCL_SE"
                    u_col_use = "__UCL_SE"
                elif lower_col is None or upper_col is None:
                    df_desc["__LCL"] = df_desc[y_col] - CI_MULTIPLIER * df_desc[se_col]
                    df_desc["__UCL"] = df_desc[y_col] + CI_MULTIPLIER * df_desc[se_col]
                    l_col_use = "__LCL"
                    u_col_use = "__UCL"
                else:
                    l_col_use = lower_col
                    u_col_use = upper_col
                    
                y_col_use = y_col
                ylabel = f"Rejection Probability {err_suffix}"

            tag = f"{exp_version}_{label_dir.name}"
            
            plot_interaction_line(
                df_desc, y_col_use, l_col_use, u_col_use, ylabel,
                f"{tag}: Interaction", figures_dir / f"{tag}_Interaction_Line.png"
            )
            
            plot_interaction_bar(
                df_desc, y_col_use, l_col_use, u_col_use, ylabel,
                f"{tag}: Interaction", figures_dir / f"{tag}_Interaction_Bar.png"
            )
    else:
        print("   [Skip] Descriptive_Means_SE sheet not found in Excel report.")

    posthoc_sheets = [s for s in xls.sheet_names if s.startswith("PostHoc_")]
    
    if posthoc_sheets:
        mode = "rejection" if "Rejection" in label_dir.name else "rt"
        for sheet in posthoc_sheets:
            try:
                df_ph = pd.read_excel(xls, sheet_name=sheet)
                if "emotion" in df_ph.columns:
                    df_ph["emotion"] = df_ph["emotion"].apply(normalize_emotion)
                    
                plot_forest_from_posthoc(
                    df_ph, 
                    title=f"{exp_version} - {label_dir.name}: {sheet}",
                    filename=figures_dir / f"{exp_version}_{label_dir.name}_{sheet}_Forest.png",
                    mode=mode
                )
            except Exception as e:
                print(f"   [Warn] Forest plot failed for sheet {sheet}: {e}")


def plot_distributions_from_trials(trials_path: Path, figures_dir: Path, exp_version: str):
    """Processes raw trial-level data to generate distribution visualizations."""
    print(f"\n>>> Processing Raw Data for Distribution Plots [{exp_version}]...")
    print(f"   -> Loading: {trials_path}")
    
    df_trials = load_and_clean_trials(trials_path)
    
    rain_dir = figures_dir / "Raincloud"
    rain_dir.mkdir(parents=True, exist_ok=True)
    emo_label_map = {"dis": "Disgust", "dom": "Dominance", "neu": "Neutral", "aff": "Affiliative", "enj": "Reward"}

    if "RT" in df_trials.columns:
        plot_facet_paired_box_violin(
            df_raw=df_trials, y_var="RT", y_label="Reaction Time (ms)", 
            title=f"Distribution RT ({exp_version})", 
            output_path_png=rain_dir / f"Distribution_{exp_version}_RT_PairedBoxViolin_FacetOffer.png", 
            output_path_pdf=rain_dir / f"Distribution_{exp_version}_RT_PairedBoxViolin_FacetOffer.pdf", 
            label_map=emo_label_map, color_map=COLOR_MAP, 
            violin_alpha=0.32, box_alpha=0.45, point_alpha=0.80
        )
    
    if "rejection_rate" in df_trials.columns:
        plot_facet_paired_box_violin(
            df_raw=df_trials, y_var="rejection_rate", y_label="Rejection Rate (%)", 
            title=f"Distribution Rejection ({exp_version})", 
            output_path_png=rain_dir / f"Distribution_{exp_version}_Rejection_PairedBoxViolin_FacetOffer.png", 
            output_path_pdf=rain_dir / f"Distribution_{exp_version}_Rejection_PairedBoxViolin_FacetOffer.pdf", 
            label_map=emo_label_map, color_map=COLOR_MAP, 
            violin_alpha=0.22, box_alpha=0.45, point_alpha=0.80
        )


if __name__ == "__main__":
    prefer_debug = ("--debug" in sys.argv)
    run_version = EXPERIMENT_VERSION
    
    # CLI Argument Parsing for Version Override
    if "--e1" in sys.argv:
        run_version = "E1"
    elif "--e2" in sys.argv:
        run_version = "E2"

    current_path = Path(__file__).resolve()
    project_root = detect_project_root(current_path)
    
    if project_root is None:
        raise FileNotFoundError("Project root not found (missing 'results' directory in parent paths).")

    out_root = choose_output_root(project_root, exp_version=run_version, prefer_debug=prefer_debug)
    figures_dir = out_root / "Figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print(f"Info: Project Root:       {project_root}")
    print(f"Info: Experiment Version: {run_version}")
    print(f"Info: Output Root:        {out_root}")
    print(f"Info: Figures Dir:        {figures_dir}")

    # Process all statistical reports
    for label in LABELS:
        label_dir = out_root / label
        if label_dir.exists():
            process_label_folder(label_dir, figures_dir, exp_version=run_version)
        else:
            print(f"\n>>> [Skip] Label folder not found: {label_dir}")

    # Process distributions using properly isolated trials.csv
    trials_path = find_trials_csv(project_root, exp_version=run_version)
    if trials_path and trials_path.exists():
        try:
            plot_distributions_from_trials(trials_path, figures_dir, exp_version=run_version)
        except Exception as e:
            print(f"   [Warn] Distribution pipeline failed: {e}")
    else:
        print("\n>>> [Skip] trials.csv not found.")

    print("\nDone! Figures saved to:", figures_dir)