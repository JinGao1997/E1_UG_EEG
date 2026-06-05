#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Behavioral Visualization Master Pipeline (v3.0)
================================================================================
Description:
    Generates publication-quality figures based on Generalized Linear Mixed Model 
    (GLMM) and Linear Mixed Model (LMM) outputs from upstream R scripts.
    
    Compatible with:
    - Sta_Behaviour_RefAlday_v2.Rmd (current; subdirs GLMM_Rejection,
      LMM_RT_main, LMM_RT_unfair). v2 upgrades reporting layer with 95% CI,
      odds ratios for GLMM, percent RT change for LMM_RT, partial eta-squared.
    - Sta_Behaviour_v1_6.Rmd (legacy; subdirs GLMM_Rejection, LMM_RT_full,
      LMM_RT_unfair).
    - Sta_Behaviour_v1.x (legacy; results/Behavioral/{exp}_Pub_Output_Final/
      with subdirs Type_Rejection_Rate, Type_Response_Time, Unfair_Rejection_RT).
    
    Forward-compat strategy: directory-name candidate lists order new-first,
    legacy-second. The first existing directory wins. Excel column candidates
    use get_first_col() so additional columns from upstream do not break.
    
    Architecture:
    - Data-driven visualization mapping: Dynamically parses Excel sheets generated 
      by the upstream hierarchical statistical gating mechanism.
    - Multi-source data fusion: Accommodates both single-experiment and 
      cross-experiment concatenated raw data (trials.csv).
    - Publication Standards: Implements strict APA-7th typographic conventions, 
      including standard error bar caps (I-bars).
    - Faceted Rain-on-Cloud: Deploys Trellis/Facet design (1x2 grid) to fully separate 
      Fair and Unfair offers. Restores the high-density "Rain-in-Cloud" overlay.
    - Dynamic Bounding Box Layout: Utilizes tight_layout with restricted rect bounds
      to perfectly isolate global legends and suptitles from facet titles.

    Cross-experiment (CrossExp_E1_vs_E2): NOT planned in upstream R pipeline
    per researcher decision (E1/E2 framed as conceptual replication, not 
    pooled analysis). Cross-exp code retained for backward compatibility but
    inactive by default.

Date: 2026-05-03 (v3.0 release for v2 statistical script alignment)
================================================================================
"""

from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from scipy.special import expit  # plogis equivalent: logit -> probability
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
EXPERIMENT_VERSION = "E1"  # Default. Override with --e1, --e2, --crossexp.
                            # Cross-experiment is not yet implemented in
                            # the upstream R pipeline (planned for next round).
ERROR_BAR_TYPE = "SE"
CI_MULTIPLIER = 1.0  
RT_Y_MIN = 400
RT_Y_MAX = 1800
# Spaghetti RT axis bounds (ms). 1800 ms upper bound clips ~0.5% of 
# subject-cell means (3/600); the trade-off favors visual compactness 
# in the merged 2x5 figure where vertical space per panel is limited.
# Earlier 2100 ms range (0% clip) wasted ~15% vertical space on the 
# rarely-used 1800-2100 region.

# Single-experiment label dirs.
# Order: NEW FIRST (LMM_RT_main from v2 statistical script), LEGACY SECOND
# (LMM_RT_full from v1.6 era). The main loop in __main__ iterates this list
# and processes each existing directory; both will be processed if a project
# has output from both eras side-by-side.
LABELS_SINGLE = ["GLMM_Rejection", "LMM_RT_main", "LMM_RT_full", "LMM_RT_unfair"]
LABELS_CROSSEXP = ["CrossExp_GLMM_Rejection",
                   "CrossExp_LMM_RT_main", "CrossExp_LMM_RT_full",
                   "CrossExp_LMM_RT_unfair"]

LABEL_MAP = {
    "dis": "Disgust", "dom": "Dominance", "neu": "Neutral", 
    "aff": "Affiliative", "enj": "Reward", "fair": "Fair", "unfair": "Unfair"
}
EMOTION_ORDER = ["neu", "aff", "dis", "dom", "enj"]
# Order rationale: Neutral first as baseline reference, followed by 
# positive-valence (aff = Affiliative), negative-valence (dis = Disgust),
# threat (dom = Dominance), and outcome-valence (enj = Reward).
# Used consistently across spaghetti panels, forest plot rows, and 
# legend entries.
COLOR_MAP = {
    "dis": "#E64B35", "dom": "#F39B7F", "neu": "#8491B4", 
    "aff": "#91D1C2", "enj": "#3C5488"
}

# Offer-type color map for Profile plot (interaction visualization).
# Selection rationale: must be visually distinct from every entry in 
# COLOR_MAP (red/orange/blue-gray/teal/dark-blue) to avoid emotion-vs-
# fairness color collision. Black + dark-purple are off the emotion 
# color wheel, colorblind-safe (deuteranopia/protanopia/tritanopia 
# checked), and remain distinguishable in grayscale print.
OFFER_COLOR_MAP = {
    "Fair":   "#000000",
    "Unfair": "#7B3294"
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
    # v1.6 uses results/Behavior/ (singular) and {exp}_TwoStage_Bates suffix.
    # Earlier viz versions assumed results/Behavioral/ + _Pub_Output_Final.
    beh_root = project_root / "results" / "Behavior"
    if not beh_root.exists():
        # Backward-compat: try old plural-form path.
        beh_root_old = project_root / "results" / "Behavioral"
        if beh_root_old.exists():
            beh_root = beh_root_old
    
    if exp_version == "CrossExp_E1_vs_E2":
        cross_dirs = [beh_root / "CrossExp_E1_vs_E2_TwoStage_Bates",
                      beh_root / "CrossExp_E1_vs_E2_Pub_Output_Final",
                      beh_root / "CrossExp_E1_vs_E2_Pub_Output",
                      beh_root / "CrossExp_E1_vs_E2_Debug_Output"]
        for d in cross_dirs:
            if d.exists(): return d
        raise FileNotFoundError(f"CrossExp output directory not found in {beh_root}.")

    # v1.6 produces {exp}_TwoStage_Bates; older versions produced *_Pub_Output_*.
    pub_dirs = [beh_root / f"{exp_version}_TwoStage_Bates",
                beh_root / f"{exp_version}_Pub_Output_Final",
                beh_root / f"{exp_version}_Pub_Output"]
    dbg_dirs = [beh_root / f"{exp_version}_Debug_Output_Final",
                beh_root / f"{exp_version}_Debug_Output"]

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
def plot_interaction_spaghetti_combined(
    df_emm_rt: pd.DataFrame,
    df_subj_rt: pd.DataFrame,
    df_emm_rej: pd.DataFrame,
    df_subj_rej: pd.DataFrame,
    main_title: str,
    filename: Path,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type"
):
    """
    Combined 2-row x 5-emotion spaghetti figure.
    
    Row 1: Rejection Rate (%, GLMM emmean + delta-method SE).
    Row 2: Reaction Time (ms, LMM emmean + delta-method SE).
    Each cell: 30 thin gray subject lines + 1 colored group emmean line 
    with error bars.
    
    Layout choices for journal-figure compactness:
      - Emotion title appears only in row 1; row 2 reuses the same column.
      - X-axis (Fair/Unfair) labels appear only in row 2 (bottom row).
      - Y axis labels appear only on the leftmost panel of each row.
      - sharex per column, sharey per row.
      - wspace=0.18 keeps Fair/Unfair labels of adjacent columns clear.
      - hspace=0.12 keeps row 2 emotion-title-free top close to row 1's
        bottom panel without overlapping x-tick labels of row 1 (which 
        we hide).
    """
    n_emo = len(EMOTION_ORDER)
    
    # Normalize offer_type case in all 4 input frames.
    for df in (df_emm_rt, df_subj_rt, df_emm_rej, df_subj_rej):
        df[offer_col] = df[offer_col].astype(str).str.strip().str.capitalize()
    
    # 2 rows x N columns. Each row independently shares Y; each column
    # shares X (so middle column tick labels cleanly align).
    fig, axes = plt.subplots(
        2, n_emo,
        figsize=(2.7 * n_emo + 0.8, 7.4),
        sharex="col",
        gridspec_kw=dict(height_ratios=[1.0, 1.0])
    )
    # Per-row sharey: row 0 shares range among themselves, row 1 likewise.
    # v11.1: Y-tick labels are intentionally KEPT VISIBLE on all panels 
    # (not just leftmost) so each emotion panel reads as an independent
    # plot. The sharey link still enforces a unified scale; only the 
    # tick label visibility differs from the journal-tight v11 default.
    for ax in axes[0, 1:]:
        ax.sharey(axes[0, 0])
    for ax in axes[1, 1:]:
        ax.sharey(axes[1, 0])
    
    x_levels = ["Fair", "Unfair"]
    alpha_indiv_line = 0.28
    alpha_indiv_dot = 0.30
    
    def draw_one_row(row_axes, df_emm, df_subj, y_col_subj,
                     ylabel, is_rt_row, is_pct_row):
        """Render one row (5 panels) with shared logic."""
        for ax_i, emo in enumerate(EMOTION_ORDER):
            ax = row_axes[ax_i]
            
            # Gray individual subject lines.
            sub_emo = df_subj[df_subj[emotion_col] == emo]
            for pid, g in sub_emo.groupby(subject_col):
                g = g.set_index(offer_col).reindex(
                    [l for l in x_levels if l in g[offer_col].values]
                ).reset_index()
                if len(g) < 2:
                    continue
                ax.plot(
                    g[offer_col], g[y_col_subj],
                    color="#666666", lw=0.55, alpha=alpha_indiv_line, zorder=2
                )
                ax.scatter(
                    g[offer_col], g[y_col_subj],
                    color="#666666", s=8, alpha=alpha_indiv_dot, zorder=2
                )
            
            # Group emmean line in emotion-specific color.
            emm_emo = df_emm[df_emm[emotion_col] == emo]
            emm_emo = emm_emo.set_index(offer_col).reindex(
                [l for l in x_levels if l in emm_emo[offer_col].values]
            ).reset_index()
            if not emm_emo.empty:
                color = COLOR_MAP.get(emo, "black")
                yerr = [
                    emm_emo["mean_val"] - emm_emo["lower_val"],
                    emm_emo["upper_val"] - emm_emo["mean_val"]
                ]
                ax.errorbar(
                    emm_emo[offer_col], emm_emo["mean_val"],
                    yerr=yerr,
                    color=color, lw=2.6, marker="o", markersize=8,
                    capsize=4, capthick=1.6, elinewidth=1.8, zorder=5
                )
            
            if ax_i == 0:
                ax.set_ylabel(ylabel, fontsize=11)
            
            # X-axis padding: data points off the panel edges.
            ax.set_xlim(-0.35, 1.35)
            
            if is_rt_row:
                if RT_Y_MIN is not None:
                    ax.set_ylim(bottom=RT_Y_MIN)
                if RT_Y_MAX is not None:
                    ax.set_ylim(top=RT_Y_MAX)
            elif is_pct_row:
                ax.set_ylim(0, 100)
            sns.despine(ax=ax)
    
    # ===== Row 1: Rejection Rate =====
    draw_one_row(
        row_axes=axes[0, :],
        df_emm=df_emm_rej, df_subj=df_subj_rej,
        y_col_subj="rejection_rate",
        ylabel="Rejection Rate (%)",
        is_rt_row=False, is_pct_row=True
    )
    # Emotion titles on row 1 only.
    for ax_i, emo in enumerate(EMOTION_ORDER):
        axes[0, ax_i].set_title(
            LABEL_MAP.get(emo, emo),
            fontweight="bold", fontsize=12,
            color=COLOR_MAP.get(emo, "black"),
            pad=8
        )
    
    # ===== Row 2: Reaction Time =====
    draw_one_row(
        row_axes=axes[1, :],
        df_emm=df_emm_rt, df_subj=df_subj_rt,
        y_col_subj="RT",
        ylabel="Reaction Time (ms)",
        is_rt_row=True, is_pct_row=False
    )
    
    # Footnote.
    method_note = (
        "Thin gray lines = individual subjects. Colored line = "
        "GLMM/LMM emmean \u00B1 1 SE (delta method on response scale). "
        "Top row: Rejection Rate; Bottom row: Reaction Time."
    )
    fig.text(0.5, -0.01, method_note, ha="center", va="top",
             fontsize=9, color="#555555", style="italic")
    
    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=1.00)
    
    # Layout: tight_layout first to compute base, then nudge spacing.
    # wspace=0.32 (vs 0.18 in v11) leaves room for the Y-tick numbers 
    # of each panel without those numbers crowding the spine of the 
    # panel to its left. hspace=0.15 keeps the two outcome rows close.
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.32, hspace=0.15)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_interaction_profile_combined(
    df_emm_rt: pd.DataFrame,
    df_emm_rej: pd.DataFrame,
    main_title: str,
    filename: Path,
    emotion_col: str = "emotion",
    offer_col: str = "offer_type"
):
    """
    Combined 1-row x 2-panel interaction Profile figure.
    
    Panel layout:
      Left  : Rejection Rate (%, GLMM emmean + delta-method CI)
      Right : Reaction Time  (ms, LMM emmean + delta-method CI)
    
    Within each panel:
      X-axis: emotion (5 categorical ticks, ordered per EMOTION_ORDER)
      Y-axis: outcome on response scale
      Two overlaid lines: Fair (black) and Unfair (dark purple)
      Error bars: marginal SE/CI from upstream emmeans output
    
    Visual rationale:
      Profile plot is the canonical interaction-detection geometry: 
      non-parallel lines = interaction. Spaghetti panels (separate
      function) require cross-panel slope comparison, which is a 
      lower-efficiency perceptual task per Cleveland & McGill (1984).
      This figure complements rather than replaces spaghetti: spaghetti
      shows individual heterogeneity, profile shows interaction signal.
    
    Logit-scale interaction caveat:
      Rejection rate is plotted on the probability scale for 
      interpretability. A model with no interaction on the logit scale 
      may still show non-parallel lines on the % scale due to link 
      function nonlinearity. Statistical inference for the interaction 
      term must be drawn from the model summary (logit scale), not from 
      visual parallelism on this figure.
    """
    n_emo = len(EMOTION_ORDER)
    
    # Normalize offer_type case in both input frames.
    for df in (df_emm_rt, df_emm_rej):
        df[offer_col] = df[offer_col].astype(str).str.strip().str.capitalize()
    
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    
    # X-axis numeric positions: emotion treated as ordinal for plotting
    # purposes only. Caption clarifies that emotion is a categorical 
    # factor and lines connect adjacent levels for visual reference.
    x_pos = np.arange(n_emo)
    # Small horizontal jitter between Fair and Unfair lines to prevent 
    # error bar overlap when CIs are wide. Magnitude (0.08) is small 
    # enough not to imply the conditions occur at different x values.
    x_offset = 0.08
    
    def draw_one_panel(ax, df_emm, y_col, lower_col, upper_col,
                       ylabel, ylim_low, ylim_high, panel_title):
        """Render one outcome panel with Fair/Unfair line overlay."""
        for offer_lvl, x_shift in [("Fair", -x_offset), ("Unfair", +x_offset)]:
            sub = df_emm[df_emm[offer_col] == offer_lvl].copy()
            if sub.empty:
                continue
            
            # Reorder rows to match EMOTION_ORDER. Missing emotions in 
            # the emmeans output produce NaN slots, which matplotlib 
            # silently skips on the line; this is acceptable behavior.
            sub = sub.set_index(emotion_col).reindex(EMOTION_ORDER).reset_index()
            
            color = OFFER_COLOR_MAP[offer_lvl]
            yerr = [
                sub[y_col] - sub[lower_col],
                sub[upper_col] - sub[y_col]
            ]
            
            ax.errorbar(
                x_pos + x_shift, sub[y_col],
                yerr=yerr,
                color=color,
                lw=2.2,
                marker="o", markersize=8, markerfacecolor=color,
                markeredgecolor="white", markeredgewidth=0.8,
                capsize=4, capthick=1.4, elinewidth=1.4,
                label=offer_lvl,
                zorder=5
            )
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(
            [LABEL_MAP.get(e, e) for e in EMOTION_ORDER],
            fontsize=10
        )
        ax.set_xlabel("Emotion", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(panel_title, fontsize=12, fontweight="bold", pad=8)
        if ylim_low is not None or ylim_high is not None:
            ax.set_ylim(ylim_low, ylim_high)
        ax.set_xlim(-0.5, n_emo - 0.5)
        ax.legend(
            loc="best", frameon=False, fontsize=10,
            title="Offer Type", title_fontsize=10
        )
        sns.despine(ax=ax)
    
    # ===== Panel 1: Rejection Rate =====
    draw_one_panel(
        ax=axes[0],
        df_emm=df_emm_rej,
        y_col="mean_val", lower_col="lower_val", upper_col="upper_val",
        ylabel="Rejection Rate (%)",
        ylim_low=0, ylim_high=100,
        panel_title="Rejection Rate"
    )
    
    # ===== Panel 2: Reaction Time =====
    draw_one_panel(
        ax=axes[1],
        df_emm=df_emm_rt,
        y_col="mean_val", lower_col="lower_val", upper_col="upper_val",
        ylabel="Reaction Time (ms)",
        ylim_low=RT_Y_MIN, ylim_high=RT_Y_MAX,
        panel_title="Reaction Time"
    )
    
    method_note = (
        "Lines connect adjacent emotion levels for visual reference; "
        "emotion is a categorical factor. Error bars show GLMM/LMM "
        "marginal 95% CI on the response scale (delta method). "
        "Non-parallel lines indicate interaction; statistical inference "
        "is drawn from the model summary, not visual parallelism."
    )
    fig.text(0.5, -0.02, method_note, ha="center", va="top",
             fontsize=8.5, color="#555555", style="italic", wrap=True)
    
    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=1.00)
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.25)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_interaction_spaghetti(
    df_emm: pd.DataFrame,
    df_subj: pd.DataFrame,
    y_col_emm: str,
    lower_col: str,
    upper_col: str,
    y_col_subj: str,
    ylabel: str,
    main_title: str,
    filename: Path
):
    """
    5-facet spaghetti + group emmean overlay.
    
    Each facet (one per emotion):
      - Gray thin lines: each subject's individual mean across offer_type 
        (fair vs unfair) for that emotion.
      - Colored thick line: GLMM/LMM emmean +/- delta-method symmetric SE,
        from the model output. Color = emotion-specific from COLOR_MAP.
    
    Inputs:
      df_emm   model emmean table on response scale, with columns 
               [emotion, offer_type, mean_val, lower_val, upper_val].
               Already in % for GLMM (post-plogis), in ms for LMM-RT.
               Generated by fetch_lmm_stats() with delta-method SE.
      df_subj  subject-level aggregated raw data, with columns
               [participant_id, emotion, offer_type, <y_col_subj>] where
               y_col_subj is the response-scale variable (rejection_rate or RT).
    
    Replaces the previous plot_interaction_line + Raincloud combination:
      - Subject-level lines absorb the distribution-display role of the 
        raincloud (each line shows that subject's level + how it changes 
        from fair to unfair).
      - Group emmean overlay shows the inferential summary.
      - Single figure satisfies "one chart shows distribution + statistics."
    """
    x_levels = ["Fair", "Unfair"]
    df_emm = df_emm.copy()
    df_subj = df_subj.copy()
    df_emm["offer_type"] = df_emm["offer_type"].astype(str).str.strip().str.capitalize()
    df_subj["offer_type"] = df_subj["offer_type"].astype(str).str.strip().str.capitalize()
    
    n_emo = len(EMOTION_ORDER)
    # Layout for 1xN horizontal spaghetti panels.
    # - figsize: 2.4 in per panel + 0.8 in for left Y-axis label gutter.
    #   Total width ~12.8 inches at n_emo=5, height 4.4 inches: aspect ~2.9:1
    #   matches Nature/Science multi-panel figure proportions.
    # - sharey=True so cross-emotion comparisons read directly.
    fig, axes = plt.subplots(
        1, n_emo,
        figsize=(2.4 * n_emo + 0.8, 4.4),
        sharey=True
    )
    if n_emo == 1:
        axes = [axes]
    
    # Determine global y-limits.
    # We expand a little beyond observed data so error bars and individual 
    # lines stay inside the panel.
    is_pct = "%" in ylabel
    is_rt = "Time" in ylabel or "ms" in ylabel
    
    # Visual style constants.
    # alpha_indiv chosen at 0.28 to reduce visual clutter of 30 overlapping 
    # gray lines while still letting individual trajectories be perceived.
    alpha_indiv_line = 0.28
    alpha_indiv_dot = 0.30
    
    for ax_i, emo in enumerate(EMOTION_ORDER):
        ax = axes[ax_i]
        
        # Gray individual subject lines.
        sub_emo = df_subj[df_subj["emotion"] == emo]
        for pid, g in sub_emo.groupby("participant_id"):
            g = g.set_index("offer_type").reindex(
                [l for l in x_levels if l in g["offer_type"].values]
            ).reset_index()
            if len(g) < 2:
                continue
            ax.plot(
                g["offer_type"], g[y_col_subj],
                color="#666666", lw=0.55, alpha=alpha_indiv_line, zorder=2
            )
            ax.scatter(
                g["offer_type"], g[y_col_subj],
                color="#666666", s=8, alpha=alpha_indiv_dot, zorder=2
            )
        
        # Group emmean line in emotion-specific color.
        emm_emo = df_emm[df_emm["emotion"] == emo]
        emm_emo = emm_emo.set_index("offer_type").reindex(
            [l for l in x_levels if l in emm_emo["offer_type"].values]
        ).reset_index()
        if not emm_emo.empty:
            color = COLOR_MAP.get(emo, "black")
            yerr = [
                emm_emo[y_col_emm] - emm_emo[lower_col],
                emm_emo[upper_col] - emm_emo[y_col_emm]
            ]
            ax.errorbar(
                emm_emo["offer_type"], emm_emo[y_col_emm],
                yerr=yerr,
                color=color, lw=2.6, marker="o", markersize=8,
                capsize=4, capthick=1.6, elinewidth=1.8, zorder=5
            )
        
        ax.set_title(LABEL_MAP.get(emo, emo), fontweight="bold", fontsize=12, color=COLOR_MAP.get(emo, "black"))
        if ax_i == 0:
            ax.set_ylabel(ylabel, fontsize=11)
        else:
            ax.tick_params(labelleft=False)
        ax.set_xlabel("")
        
        # Add small horizontal padding so the leftmost ('Fair') and 
        # rightmost ('Unfair') data points / error bars don't sit flush 
        # against the panel spines.
        ax.set_xlim(-0.35, 1.35)
        
        # Y-limits
        if is_rt:
            if RT_Y_MIN is not None:
                ax.set_ylim(bottom=RT_Y_MIN)
            if RT_Y_MAX is not None:
                ax.set_ylim(top=RT_Y_MAX)
        elif is_pct:
            ax.set_ylim(0, 100)
        sns.despine(ax=ax)
    
    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=1.02)
    
    # Footnote with method note.
    if is_pct:
        method_note = "Thin gray lines = individual subjects. Colored line = GLMM emmean \u00B1 1 SE (delta method on response scale)."
    else:
        method_note = "Thin gray lines = individual subjects. Colored line = LMM emmean \u00B1 1 SE (delta method, exp transform)."
    fig.text(0.5, -0.02, method_note, ha="center", va="top", fontsize=9, color="#555555", style="italic")
    
    # Layout: tight_layout first to compute base, then nudge wspace tighter.
    # Empirically wspace=0.18 keeps "Unfair" and the next panel's "Fair" 
    # x-tick labels clear of each other while keeping the figure compact 
    # enough for a journal column figure (Nature Hum Behav, JEP target).
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.18)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_interaction_line(df, y_col, lower_col, upper_col, ylabel, main_title, filename):
    x_axis = "offer_type" if "offer_type" in df.columns else ("offer_ratio" if "offer_ratio" in df.columns else None)
    if not x_axis: return
    
    # Bug 1 fix: case-insensitive matching. Real emmeans output has lowercase
    # offer_type ("fair","unfair") but viz historically expected ["Fair","Unfair"].
    # Normalize to capitalized form for both data and lookup levels.
    df = df.copy()
    if x_axis == "offer_type":
        df[x_axis] = df[x_axis].astype(str).str.strip().str.capitalize()
    
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
        
        # Y-limit logic:
        # - "Time"/"ms" in label -> RT axis, fixed lower bound, free upper.
        # - "%" in label -> percentage axis [0, 100].
        # - "Rate"/probability axis -> [0, 1.05].
        # - Otherwise -> auto-fit (don't force [0, 1.05] which crops logit scale).
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        elif "%" in ylabel:
            ax.set_ylim(0, 100)
        elif "Rate" in ylabel and "%" not in ylabel:
            ax.set_ylim(0, 1.05)
        # else: leave auto-fit (covers logit, log, etc.)
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
    
    # Bug 1 fix: case-insensitive matching (see plot_interaction_line note).
    df = df.copy()
    if x_axis == "offer_type":
        df[x_axis] = df[x_axis].astype(str).str.strip().str.capitalize()
    
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
        
        # Y-limit logic (matches plot_interaction_line).
        if "Time" in ylabel or "ms" in ylabel:
            if RT_Y_MIN: ax.set_ylim(bottom=RT_Y_MIN)
        elif "%" in ylabel:
            ax.set_ylim(0, 100)
        elif "Rate" in ylabel and "%" not in ylabel:
            ax.set_ylim(0, 1.05)
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
    
    # Bug A fix: support multiple contrast column conventions.
    # - "contrast"          -> simple posthoc (e.g. neu - aff)
    # - "emotion_pairwise"  -> Interaction_Contrasts: emotion contrast component
    # - "reaction_pairwise" -> Interaction_Contrasts: reaction-by-emotion variant
    # When a *_pairwise column is present, the row label needs to combine both
    # pairwise components (emotion_pairwise + offer_type_pairwise).
    contrast_col = get_first_col(df, ["contrast", "emotion_pairwise", "reaction_pairwise"])
    if not est_col or not p_col: return

    if contrast_col is not None:
        labels = pd.Series(df[contrast_col].astype(str)).reset_index(drop=True)
    else:
        labels = pd.Series(df.index.astype(str))
    labels = labels.str.replace("fair", "Fair").str.replace("unfair", "Unfair")
    for k, v in LABEL_MAP.items():
        labels = labels.str.replace(fr'\b{k}\b', v, regex=True)
    
    # Bug A continuation: for Interaction_Contrasts, the second pairwise column
    # (offer_type_pairwise or reaction_pairwise) should be appended rather than
    # used as a categorical prefix. This produces labels like
    # "neu - aff | Fair - Unfair".
    second_pair_col = None
    if contrast_col == "emotion_pairwise":
        for cand in ["offer_type_pairwise", "reaction_pairwise"]:
            if cand in df.columns and cand != contrast_col:
                second_pair_col = cand
                break
    elif contrast_col == "reaction_pairwise":
        for cand in ["emotion_pairwise", "offer_type_pairwise"]:
            if cand in df.columns and cand != contrast_col:
                second_pair_col = cand
                break
    if second_pair_col is not None:
        sp = df[second_pair_col].astype(str).reset_index(drop=True)
        sp = sp.str.replace("fair", "Fair").str.replace("unfair", "Unfair")
        labels = labels + " | " + sp
    
    # Bug B fix: include "reaction" (and any *_pairwise siblings already
    # consumed are skipped) in the prefix candidate list. This ensures that
    # Simple_emotion_by_reaction sheets get accept/reject prefixes attached.
    prefix_cols = ["Exp", "emotion", "offer_type", "reaction"]
    consumed = {contrast_col, second_pair_col}
    for col in prefix_cols:
        if col in df.columns and col not in consumed: 
            prefix = df[col].astype(str).reset_index(drop=True)
            if col == "Exp":
                prefix = prefix.replace({"E1": "Exp. 1", "E2": "Exp. 2"})
            elif col == "offer_type":
                prefix = prefix.str.capitalize()
            elif col == "emotion":
                prefix = prefix.map(lambda x: LABEL_MAP.get(x, x))
            elif col == "reaction":
                prefix = prefix.str.capitalize()
            
            labels = prefix + " | " + labels
            
    df_plot = df.copy().reset_index(drop=True)
    df_plot["label"] = labels

    if mode == "rejection":
        # Prefer pre-computed OR + 95% CI columns (v2 statistical output);
        # fall back to manual exp(beta) +/- 1.96*SE (v1.6 and earlier).
        has_or_cols = all(c in df_plot.columns for c in ("OR", "OR_CI_low", "OR_CI_high"))
        if has_or_cols:
            df_plot["x"]    = df_plot["OR"].astype(float)
            df_plot["x_lo"] = df_plot["OR_CI_low"].astype(float)
            df_plot["x_hi"] = df_plot["OR_CI_high"].astype(float)
        else:
            df_plot["x"] = np.exp(df_plot[est_col].astype(float))
            if se_col:
                se = df_plot[se_col].astype(float)
                df_plot["x_lo"] = np.exp(df_plot[est_col].astype(float) - CI_MULTIPLIER * se)
                df_plot["x_hi"] = np.exp(df_plot[est_col].astype(float) + CI_MULTIPLIER * se)
        ref, xlab = 1.0, "Odds Ratio"
    else:
        # LMM contrasts. For logRT outputs, prefer pre-computed percent-change
        # columns (v2 statistical output). Default beta-on-log-scale display
        # is unintuitive ("b = -0.04 logRT" tells nobody anything); percent
        # change ("4% faster") is publication-readable.
        has_pct_cols = all(c in df_plot.columns
                           for c in ("PctChange", "PctChange_low", "PctChange_high"))
        if has_pct_cols:
            df_plot["x"]    = df_plot["PctChange"].astype(float)
            df_plot["x_lo"] = df_plot["PctChange_low"].astype(float)
            df_plot["x_hi"] = df_plot["PctChange_high"].astype(float)
            ref, xlab = 0.0, "RT change (%)"
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
    # Draw error bars whenever CI bounds are available. Three sources, in
    # priority order:
    #   1. Pre-computed OR_CI_low/high or PctChange_low/high (v2 statistical
    #      script): exact emmeans asymptotic CI, used directly above.
    #   2. SE column + Wald approximation: x +/- 1.96*SE (legacy fallback).
    #   3. None of the above: scatter only, no error bars.
    has_ci = ("x_lo" in df_plot.columns) and ("x_hi" in df_plot.columns)
    if has_ci:
        ax.errorbar(df_plot["x"], y_pos,
                    xerr=[df_plot["x"] - df_plot["x_lo"],
                          df_plot["x_hi"] - df_plot["x"]],
                    fmt="none", ecolor=colors, capsize=0, zorder=2)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_plot["label"])
    ax.axvline(ref, color="black", linestyle=":", lw=1)
    ax.set_xlabel(xlab)
    ax.set_title(title, pad=15, fontweight="bold", fontsize=14)
    
    # Bug C fix: switch to log scale for odds ratio when the dynamic range is
    # extreme (e.g. fair vs unfair contrasts: OR ~ 0.001-0.004 cluster at 0
    # under linear scale, making the plot unreadable). Trigger when:
    #   - mode is rejection (so x is OR), AND
    #   - x range spans >= 2 orders of magnitude OR min(x) <= 0.05.
    # On log scale, ax.axvline(1.0) still marks OR=1 reference.
    if mode == "rejection":
        x_vals = df_plot["x"].dropna()
        if not x_vals.empty:
            x_min, x_max = float(x_vals.min()), float(x_vals.max())
            extreme = (x_min > 0) and ((x_max / x_min >= 100) or (x_min <= 0.05))
            if extreme:
                ax.set_xscale("log")
                ax.set_xlabel("Odds Ratio (log scale)")
                # Rebuild the error bars on log scale: errorbar() with linear
                # x-coords already drew the bars correctly because matplotlib
                # transforms after drawing. No re-draw needed.
    
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
    # Map y_var (RT or rejection_rate) to the upstream R output dir.
    # v2 dirs (current): GLMM_Rejection, LMM_RT_main, LMM_RT_unfair.
    # v1.6 dirs (legacy): GLMM_Rejection, LMM_RT_full, LMM_RT_unfair.
    # Order new-first so v2 wins when both coexist.
    if "RT" in y_var or "rt" in y_var:
        candidate_dirs = ["LMM_RT_main", "LMM_RT_full", "LMM_RT_unfair",
                          "Type_Response_Time",
                          "CrossExp_LMM_RT_main", "CrossExp_LMM_RT_full",
                          "CrossExp_Response_Time"]
    else:
        candidate_dirs = ["GLMM_Rejection", "Type_Rejection_Rate",
                          "CrossExp_GLMM_Rejection", "CrossExp_Rejection_Rate"]
    
    label_dir = None
    for cand in candidate_dirs:
        if (out_root / cand).exists():
            label_dir = out_root / cand
            break
    if label_dir is None: return None
    
    # v1.6 file pattern: STATS_{exp}_{analysis}.xlsx
    # Older: STATS_REPORT_*.xlsx
    excel_files = list(label_dir.glob("STATS_*.xlsx"))
    if not excel_files: return None
    
    try:
        # v1.6 sheet name is "Descriptive_Means" (no _SE suffix).
        # Older versions used "Descriptive_Means_SE".
        xls = pd.ExcelFile(excel_files[0])
        target_sheet = None
        for cand in ["Descriptive_Means", "Descriptive_Means_SE"]:
            if cand in xls.sheet_names:
                target_sheet = cand
                break
        if target_sheet is None: return None
        
        df = pd.read_excel(excel_files[0], sheet_name=target_sheet)
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
        
        # Bug 6 fix: detect GLMM-rejection (logit emmean) and plogis-transform.
        # For raincloud overlay, the EMM marker should be on the same scale as
        # the raw distribution (rejection_rate in %, RT in ms).
        is_rejection_var = ("rejection" in y_var.lower() or "rate" in y_var.lower())
        is_logit_scale = is_rejection_var and (mean_numeric is not np.nan) and \
                         (abs(mean_numeric) > 1.05 or res[y_col].min() < -0.5)
        
        if "RT" in y_var and mean_numeric < 20 and se_col:
            # logRT -> ms.
            res["mean_val"] = np.exp(res[y_col].astype(float))
            se_ms = res["mean_val"] * res[se_col].astype(float)
            res["lower_val"] = res["mean_val"] - (CI_MULTIPLIER * se_ms)
            res["upper_val"] = res["mean_val"] + (CI_MULTIPLIER * se_ms)
        elif is_logit_scale:
            # GLMM logit -> probability via plogis, with **delta-method SYMMETRIC SE**
            # on the response scale.
            #
            # Rationale: applying plogis() directly to logit-scale asymp.LCL/UCL
            # produces visually asymmetric error bars due to end-point compression
            # (e.g. for p=0.96 with logit SE=0.33, the upper interval compresses
            # to ~2pp while the lower extends to ~5pp; for p=0.88 with logit
            # SE=0.56, both extend ~7pp, making conditions look like they have
            # very different precision when the underlying logit-scale precision
            # is comparable). Delta-method gives a first-order Taylor approximation
            # of the standard error on the response scale:
            #   SE_p = p * (1 - p) * SE_logit
            # This produces SYMMETRIC bars on the % scale, while preserving the
            # logit-scale information (cells with similar logit SE get visually
            # similar bars).
            #
            # Trade-off: at extreme p (close to 0 or 1), delta-method may produce
            # CI that crosses 0% or 100%; this is clipped at display time.
            # Reported per Allen et al. (2019, Wellcome Open Res) recommendation
            # for raincloud-style figures with GLMM emmeans.
            res["mean_val"] = expit(res[y_col].astype(float))
            if se_col:
                p = res["mean_val"]
                se_p = p * (1 - p) * res[se_col].astype(float)
                res["lower_val"] = p - CI_MULTIPLIER * se_p
                res["upper_val"] = p + CI_MULTIPLIER * se_p
            else:
                # Fallback: if no SE column, use plogis on CI bounds
                # (asymmetric, but better than nothing).
                if lower_col and upper_col:
                    res["lower_val"] = expit(res[lower_col].astype(float))
                    res["upper_val"] = expit(res[upper_col].astype(float))
                else:
                    res["lower_val"] = res["mean_val"]
                    res["upper_val"] = res["mean_val"]
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
                
        # If on probability scale (0-1), scale to percentage to match raincloud y-axis.
        if is_rejection_var and res["mean_val"].max() <= 1.05:
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
    
    # v6 raincloud strategy: model-based mean + delta-method symmetric SE.
    #   - Mean marker = GLMM/LMM emmean (transformed to response scale via 
    #     plogis for GLMM, exp for LMM-logRT). This guarantees consistency 
    #     with the companion Interaction_Line figure.
    #   - Error bar = +/- 1 SE on response scale, computed by delta method:
    #         SE_p_response = |df/dlink| * SE_link
    #     For logit link: |df/dlink| = p * (1-p), so SE_p = p(1-p) * SE_logit.
    #     For log link (logRT->RT): |df/dlink| = exp(logRT) = RT, so 
    #     SE_RT = RT * SE_logRT.
    #   - Symmetric error bars avoid the visual misimpression that conditions
    #     near response-scale endpoints (e.g. 96% rejection) have higher
    #     precision than mid-range conditions (e.g. 88%) -- the underlying
    #     logit-scale precision is comparable.
    # The values are precomputed in fetch_lmm_stats() and looked up below.
    
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

            # Mean and SE for the mean marker.
            # Lookup model-based estimates from lmm_stats (precomputed by 
            # fetch_lmm_stats() with delta-method symmetric SE on response 
            # scale). Falls back to arithmetic mean if lookup fails.
            mean_val = None
            lower_val = None
            upper_val = None
            if lmm_stats is not None:
                mask = ((lmm_stats[emotion_col] == emo) & 
                        (lmm_stats[offer_col].astype(str).str.lower() == offer))
                if mask.any():
                    row = lmm_stats[mask].iloc[0]
                    mean_val = float(row["mean_val"])
                    lower_val = float(row["lower_val"])
                    upper_val = float(row["upper_val"])
            
            if mean_val is None:
                # Fallback: arithmetic subject-aggregated mean (no errorbar).
                mean_val = float(np.mean(y_vals))
                lower_val = mean_val
                upper_val = mean_val

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

            # Mean marker + delta-method symmetric SE error bar on response 
            # scale. Clip CI to display-relevant bounds (e.g. 0%, 100% for
            # rejection_rate) so error bars never extend visibly outside the
            # plotted axis when the model emmean is near response-scale 
            # endpoints.
            x_stat = x_center - stat_offset
            if is_0_100:
                lower_val = max(0.0, lower_val)
                upper_val = min(100.0, upper_val)
            yerr_low = max(0.0, mean_val - lower_val)
            yerr_high = max(0.0, upper_val - mean_val)
            ax.errorbar(x_stat, mean_val,
                        yerr=[[yerr_low], [yerr_high]],
                        fmt='o', mfc=stat_mfc, mec=color,
                        ecolor=color, capsize=4, capthick=1.5,
                        elinewidth=1.8, markersize=7, zorder=5)

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
    
    # Legend: marker = model-based mean + delta-method symmetric SE on
    # response scale.
    legend_elements = [
        mpatches.Patch(facecolor=_rgba("#808080", 0.15), edgecolor="#808080", label="Fair Offer", linewidth=1.5),
        mpatches.Patch(facecolor=_rgba("#808080", 0.75), edgecolor="none", label="Unfair Offer"),
        mlines.Line2D([], [], color='#808080', marker='o', linestyle='-',
                      linewidth=1.5, markersize=7, mfc='black', mec='black',
                      label="Estimated marginal mean \u00B1 1 SE (delta method)")
    ]
    fig.legend(handles=legend_elements, bbox_to_anchor=(0.5, 0.89), loc="center", ncol=3, frameon=False, fontsize=14)
    
    # 4. [THE MAGIC SHIELD]: Forces the entire subplot grid (including "Fair/Unfair Offers" titles)
    # to stay strictly below the 84% height line. This guarantees zero overlap forever.
    plt.tight_layout(rect=[0, 0.0, 1.0, 0.92])
    
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
    # v1.6 glob: STATS_*.xlsx (covers STATS_E2_GLMM_rejection.xlsx etc.).
    # Falls back to legacy STATS_REPORT_*.xlsx if v1.6 not present.
    excel_candidates = list(label_dir.glob("STATS_*.xlsx"))
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

    # v1.6 sheet name is "Descriptive_Means"; fall back to legacy if needed.
    desc_sheet = None
    for cand in ["Descriptive_Means", "Descriptive_Means_SE"]:
        if cand in xls.sheet_names:
            desc_sheet = cand
            break
    
    if desc_sheet is not None:
        df_desc = pd.read_excel(xls, sheet_name=desc_sheet)
        if "emotion" in df_desc.columns: df_desc["emotion"] = df_desc["emotion"].apply(normalize_emotion)
        y_col = "Mean" if "Mean" in df_desc.columns else get_first_col(df_desc, ["prob", "response", "emmean"])
        
        if y_col:
            se_col = get_first_col(df_desc, ["SE", "std.error"])
            lower_col = get_first_col(df_desc, ["asymp.LCL", "lower.CL", "lower", "LCL"])
            upper_col = get_first_col(df_desc, ["asymp.UCL", "upper.CL", "upper", "UCL"])

            if se_col:
                # Bug 2 fix: detect output type by directory name and apply
                # the correct link inverse transform.
                #
                # Directory conventions (v2 current / v1.6 legacy):
                #   GLMM_Rejection  -> binomial logit-link, emmean is on logit
                #                      scale and must be plogis()-transformed.
                #   LMM_RT_main     -> Gaussian on logRT, exp() to get ms. (v2)
                #   LMM_RT_full     -> same; legacy alias (v1.6).
                #   LMM_RT_unfair   -> Gaussian on logRT, exp() to get ms.
                # Legacy dirs (Type_Response_Time, Type_Rejection_Rate) handled
                # by the same matching logic. The is_rt prefix-match below
                # ("LMM_RT" in label_dir.name) covers all three RT variants.
                is_glmm_rejection = (("GLMM_Rejection" in label_dir.name) or
                                     ("Rejection_Rate" in label_dir.name))
                is_rt = (("Response_Time" in label_dir.name) or
                         ("LMM_RT" in label_dir.name)) and not is_glmm_rejection
                mean_numeric = float(pd.to_numeric(df_desc[y_col], errors="coerce").dropna().mean()) if not df_desc.empty else np.nan
                
                if is_glmm_rejection:
                    # logit -> probability (-Inf, +Inf) -> (0, 1).
                    # SE on logit scale does NOT linearly carry over to
                    # probability scale; we use the delta-method approximation:
                    #   SE_p = p * (1 - p) * SE_logit
                    # asymp.LCL / asymp.UCL on logit scale, when present, can
                    # also be plogis-transformed exactly (preferred over SE).
                    df_desc["__prob"] = expit(df_desc[y_col].astype(float))
                    df_desc["__prob_pct"] = df_desc["__prob"] * 100.0
                    if lower_col and upper_col:
                        df_desc["__prob_lo_pct"] = expit(df_desc[lower_col].astype(float)) * 100.0
                        df_desc["__prob_hi_pct"] = expit(df_desc[upper_col].astype(float)) * 100.0
                    else:
                        # Delta-method fallback if no CI columns.
                        p = df_desc["__prob"]
                        se_p = p * (1 - p) * df_desc[se_col].astype(float)
                        mult = 1.0 if ERROR_BAR_TYPE == "SE" else CI_MULTIPLIER
                        df_desc["__prob_lo_pct"] = (p - mult * se_p) * 100.0
                        df_desc["__prob_hi_pct"] = (p + mult * se_p) * 100.0
                    y_use = "__prob_pct"
                    l_use = "__prob_lo_pct"
                    u_use = "__prob_hi_pct"
                    err_label = "95% CI" if (lower_col and upper_col) else f"\u00B1 {ERROR_BAR_TYPE}"
                    ylab = f"Rejection Rate (%, {err_label})"
                
                elif is_rt and np.isfinite(mean_numeric) and mean_numeric < 20:
                    # logRT -> RT (ms).
                    df_desc["RT_ms"] = np.exp(df_desc[y_col].astype(float))
                    # SE on log scale -> SE on raw scale via delta method:
                    #   SE_raw ~= RT_ms * SE_log.
                    se_ms = df_desc["RT_ms"] * df_desc[se_col].astype(float)
                    mult = 1.0 if ERROR_BAR_TYPE == "SE" else CI_MULTIPLIER
                    df_desc["lower_ms"], df_desc["upper_ms"] = df_desc["RT_ms"] - (mult * se_ms), df_desc["RT_ms"] + (mult * se_ms)
                    y_use, l_use, u_use, ylab = "RT_ms", "lower_ms", "upper_ms", f"Reaction Time (ms, \u00B1 {ERROR_BAR_TYPE})"
                
                else:
                    # Generic Gaussian: keep raw emmean, draw \u00B1 SE or CI band.
                    if ERROR_BAR_TYPE == "SE":
                        df_desc["__LCL_SE"], df_desc["__UCL_SE"] = df_desc[y_col] - df_desc[se_col], df_desc[y_col] + df_desc[se_col]
                        l_use, u_use = "__LCL_SE", "__UCL_SE"
                    else:
                        df_desc["__LCL"], df_desc["__UCL"] = df_desc[y_col] - CI_MULTIPLIER * df_desc[se_col], df_desc[y_col] + CI_MULTIPLIER * df_desc[se_col]
                        l_use, u_use = lower_col if lower_col else "__LCL", upper_col if upper_col else "__UCL"
                    y_use, ylab = y_col, f"Estimated Marginal Mean (\u00B1 {ERROR_BAR_TYPE})"

                tag = f"{exp_version}_{label_dir.name}"
                # v7: plot_interaction_line is no longer invoked here.
                # The new plot_interaction_spaghetti combines individual-subject
                # trajectories with the model emmean overlay, replacing both
                # the Line plot and the standalone Raincloud. It is called from
                # plot_distributions_from_trials() because it requires trial-
                # level data (subject means) which is not available in this scope.
                # 
                # If you want a quick group-level summary without trials.csv,
                # uncomment the call below:
                # plot_interaction_line(df_desc, y_use, l_use, u_use, ylab, interaction_title, figures_dir / f"{tag}_Interaction_Line.png")

    for sheet in [s for s in xls.sheet_names if s.startswith(POSTHOC_SHEET_PREFIXES)]:
        try:
            df_ph = pd.read_excel(xls, sheet_name=sheet)
            if "emotion" in df_ph.columns: df_ph["emotion"] = df_ph["emotion"].apply(normalize_emotion)
            plot_forest_from_posthoc(df_ph, f"{format_academic_sheet_name(sheet)} ({global_exp_str})", figures_dir / f"{exp_version}_{label_dir.name}_{sheet}_Forest.png", "rejection" if "Rejection" in label_dir.name else "rt")
        except Exception as e:
            pass

def plot_distributions_from_trials(trials_paths: list[Path], figures_dir: Path, exp_version: str, out_root: Path):
    print(f"\n>>> Processing Raw Data for Spaghetti & Diagnostics [{exp_version}]...")
    df_trials = load_and_clean_trials(trials_paths)
    if df_trials.empty: return
        
    exps = df_trials["Exp"].unique()
    spag_dir = figures_dir / "Spaghetti"
    heat_dir = figures_dir / "Diagnostics"
    prof_dir = figures_dir / "Interaction"
    for d in (spag_dir, heat_dir, prof_dir):
        d.mkdir(parents=True, exist_ok=True)
    generate_diagnostics_readme(heat_dir)
    
    for exp in exps:
        print(f"   -> Generating sub-renderings for batch: {exp}")
        df_exp = df_trials[df_trials["Exp"] == exp].copy()
        tag = f"CrossExp_{exp}" if exp_version == "CrossExp_E1_vs_E2" else exp_version
        exp_display = f"Exp. {exp[1:]}" if isinstance(exp, str) and exp.startswith("E") and exp[1:].isdigit() else (str(exp) if exp else "Overall")
        title_suffix = f" ({exp_display})"
        
        # Diagnostics (always generated, independent of spaghetti).
        if "RT" in df_exp.columns:
            plot_individual_heatmap(df_exp, "RT", "Mean RT (ms)", f"Diagnostic: RT Matrix{title_suffix}", heat_dir / f"Diag_{tag}_RT_Heatmap.png")
        if "rejection_rate" in df_exp.columns:
            plot_individual_heatmap(df_exp, "rejection_rate", "Rejection Rate (%)", f"Diagnostic: Rejection Rate Matrix{title_suffix}", heat_dir / f"Diag_{tag}_Rejection_Heatmap.png")
            plot_diagnostic_fairness_scatter(df_exp, heat_dir / f"Diag_{tag}_Fairness_Scatter.png", f"Diagnostic: Fairness Sensitivity{title_suffix}")
            plot_diagnostic_emotion_scatter(df_exp, heat_dir / f"Diag_{tag}_Emotion_Scatter.png", f"Diagnostic: Emotion Volatility{title_suffix}")
        
        # Combined 2x5 spaghetti (Rejection + RT in one figure).
        # Both lmm_stats lookups must succeed, else fall back to per-outcome 
        # individual figures (legacy plot_interaction_spaghetti).
        has_rt = ("RT" in df_exp.columns)
        has_rej = ("rejection_rate" in df_exp.columns)
        
        lmm_stats_rt = fetch_lmm_stats(out_root, exp_version, "RT") if has_rt else None
        lmm_stats_rej = fetch_lmm_stats(out_root, exp_version, "rejection_rate") if has_rej else None
        
        if has_rt and has_rej and lmm_stats_rt is not None and lmm_stats_rej is not None:
            df_subj_rt = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["RT"].mean()
            df_subj_rej = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["rejection_rate"].mean()
            plot_interaction_spaghetti_combined(
                df_emm_rt=lmm_stats_rt, df_subj_rt=df_subj_rt,
                df_emm_rej=lmm_stats_rej, df_subj_rej=df_subj_rej,
                main_title=f"Behavior{title_suffix}",
                filename=spag_dir / f"Spag_{tag}_Combined.png"
            )
        else:
            # Fallback: separate single-outcome spaghetti figures.
            if has_rt and lmm_stats_rt is not None:
                df_subj_rt = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["RT"].mean()
                plot_interaction_spaghetti(
                    df_emm=lmm_stats_rt, df_subj=df_subj_rt,
                    y_col_emm="mean_val", lower_col="lower_val", upper_col="upper_val",
                    y_col_subj="RT",
                    ylabel="Reaction Time (ms)",
                    main_title=f"Reaction Time{title_suffix}",
                    filename=spag_dir / f"Spag_{tag}_RT.png"
                )
            if has_rej and lmm_stats_rej is not None:
                df_subj_rej = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["rejection_rate"].mean()
                plot_interaction_spaghetti(
                    df_emm=lmm_stats_rej, df_subj=df_subj_rej,
                    y_col_emm="mean_val", lower_col="lower_val", upper_col="upper_val",
                    y_col_subj="rejection_rate",
                    ylabel="Rejection Rate (%)",
                    main_title=f"Rejection Rate{title_suffix}",
                    filename=spag_dir / f"Spag_{tag}_Rejection.png"
                )
        
        # ===== Interaction Profile (emotion in x, Fair/Unfair overlay) =====
        # Independent of spaghetti success/failure: profile only requires
        # emmeans output, not trial-level subject means. Both lmm_stats 
        # must be present to produce the combined 1x2 figure. Output is
        # placed in figures_dir/Interaction/, parallel to Spaghetti/.
        if has_rt and has_rej and lmm_stats_rt is not None and lmm_stats_rej is not None:
            plot_interaction_profile_combined(
                df_emm_rt=lmm_stats_rt,
                df_emm_rej=lmm_stats_rej,
                main_title=f"Interaction Profile{title_suffix}",
                filename=prof_dir / f"Profile_{tag}_Combined.png"
            )

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

    # Choose label list based on run version.
    if run_version == "CrossExp_E1_vs_E2":
        labels_to_process = LABELS_CROSSEXP
    else:
        labels_to_process = LABELS_SINGLE

    for label in labels_to_process:
        if (out_root / label).exists(): process_label_folder(out_root / label, figures_dir, run_version)
        else: print(f"   [Skip] Label missing: {label}")
    
    trials_paths = find_trials_csv(root, exp_version=run_version)
    if trials_paths:
        try: plot_distributions_from_trials(trials_paths, figures_dir, run_version, out_root)
        except Exception as e: print(f"   [Warn] Distribution pipeline failed: {e}")
    else: print("\n>>> [Skip] trials.csv not found.")

    print("\n>>> Visualization Complete!")