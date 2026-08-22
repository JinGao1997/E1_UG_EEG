#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Behavioral Visualization Master Pipeline (v3.1 - Publication Optimized)
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

Date: 2026-05-20 (v3.1 - CNS Typography & Dual Vector Export Patch)
================================================================================
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import hashlib
import sys
import warnings
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
# Global Publication Typography Settings (CNS Standards)
# ==============================================================================
import matplotlib as mpl
mpl.rcParams.update({
    "pdf.fonttype": 42,           # Embed TrueType fonts in PDF (ScholarOne requirement)
    "ps.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none"
})

# ==============================================================================
# 1) Global Configuration
# ==============================================================================
EXPERIMENT_VERSION = "e1"  # Default. Override with --e1, --e2, --integrative.
                            # This is the E1+E2 Integrative behavior viz; the default
                            # targets the Integrative_TwoStage_Bates/ outputs.
ERROR_BAR_TYPE = "SE"
CI_MULTIPLIER = 1.0
RT_Y_MIN = 300
RT_Y_MAX = 1800
# Spaghetti RT axis bounds (ms). 1800 ms upper bound clips ~0.5% of 
# subject-cell means (3/600); the trade-off favors visual compactness 
# in the merged 2x5 figure where vertical space per panel is limited.

LABELS_SINGLE = ["GLMM_Rejection", "LMM_RT_main", "LMM_RT_full", "LMM_RT_unfair"]
LABELS_CROSSEXP = ["GLMM_Rejection", "LMM_RT_main", "LMM_RT_unfair",
                   "CrossExp_GLMM_Rejection",
                   "CrossExp_LMM_RT_main", "CrossExp_LMM_RT_full",
                   "CrossExp_LMM_RT_unfair"]

LABEL_MAP = {
    "dis": "Disgust", "dom": "Dominance", "neu": "Neutral", 
    "aff": "Affiliative", "enj": "Reward", "fair": "Fair", "unfair": "Unfair"
}
EMOTION_ORDER = ["neu", "aff", "dis", "dom", "enj"]

COLOR_MAP = {
    "dis": "#E64B35", "dom": "#F39B7F", "neu": "#8491B4", 
    "aff": "#91D1C2", "enj": "#3C5488"
}

OFFER_COLOR_MAP = {
    "Fair":   "#000000",
    "Unfair": "#7B3294"
}

POSTHOC_SHEET_PREFIXES = (
    "PostHoc_", 
    "SimpleSimple_", 
    "Simple_", 
    "Interaction_Contrast", 
    "Interaction_of_Interactions",  # New: 3-way Integrative cross-Exp contrast
    "JointTests_",                  # New: per-Exp joint tests (Branch A)
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
    beh_root = project_root / "results" / "Behavior"
    if not beh_root.exists():
        beh_root_old = project_root / "results" / "Behavioral"
        if beh_root_old.exists():
            beh_root = beh_root_old
    
    if exp_version in ("Integrative", "CrossExp_E1_vs_E2"):
        cross_dirs = [beh_root / "Integrative_TwoStage_Bates",
                      beh_root / "CrossExp_E1_vs_E2_TwoStage_Bates",
                      beh_root / "CrossExp_E1_vs_E2_Pub_Output_Final",
                      beh_root / "CrossExp_E1_vs_E2_Pub_Output",
                      beh_root / "CrossExp_E1_vs_E2_Debug_Output"]
        for d in cross_dirs:
            if d.exists(): return d
        raise FileNotFoundError(f"Integrative/CrossExp output directory not found in {beh_root}.")

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

def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _log_input(path: Path, label: str) -> None:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
    print(
        f"Info: {label}: {path.resolve()} | "
        f"modified={modified} | bytes={stat.st_size} | md5={_md5(path)}"
    )


def find_trials_csv(project_root: Path, exp_version: str) -> list[Path]:
    versions = ("E1", "E2") if exp_version.lower() in (
        "crossexp_e1_vs_e2", "integrative"
    ) else (exp_version.upper(),)
    if any(version not in ("E1", "E2") for version in versions):
        raise ValueError(f"Unsupported experiment version: {exp_version}")

    paths = [
        project_root / "data" / f"02_Pipeline_Output_{version}"
        / "Method_Regression" / "Stimulus_Locked" / "trials.csv"
        for version in versions
    ]
    for version, path in zip(versions, paths):
        if not path.is_file():
            raise FileNotFoundError(
                f"Canonical behavioral preprocessing output missing for {version}: {path}"
            )
        resolved_lower = path.resolve().as_posix().lower()
        forbidden = ("/previousresults/", "/olderbehaviourresults/", "/older/")
        if any(segment in resolved_lower for segment in forbidden):
            raise RuntimeError(f"Forbidden stale input path: {path.resolve()}")
        _log_input(path, f"canonical {version} trials")
    return paths


_ANALYSIS_NAME_BY_DIR = {
    "GLMM_Rejection": "GLMM_rejection",
    "LMM_RT_main": "LMM_RT_main",
    "LMM_RT_unfair": "LMM_RT_unfair",
}


def select_stats_workbook(label_dir: Path) -> Path:
    stage_dir = label_dir.parent.name
    analysis_name = _ANALYSIS_NAME_BY_DIR.get(label_dir.name)
    if stage_dir.endswith("_TwoStage_Bates") and analysis_name is not None:
        stage = stage_dir.removesuffix("_TwoStage_Bates")
        expected = label_dir / f"STATS_{stage}_{analysis_name}.xlsx"
        if not expected.is_file():
            raise FileNotFoundError(f"Canonical statistics workbook missing: {expected}")
        _log_input(expected, "canonical statistics workbook")
        return expected

    candidates = sorted(label_dir.glob("STATS_*.xlsx"))
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one legacy STATS workbook in {label_dir}; "
            f"found {len(candidates)}: {[p.name for p in candidates]}"
        )
    _log_input(candidates[0], "legacy statistics workbook")
    return candidates[0]

def get_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns: return c
    return None

def parse_display_p(value) -> float:
    """Parse numeric or APA-formatted p values used in exported workbooks."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace("=", "").strip()
    if text.startswith("<"):
        text = text[1:].strip()
    return float(text)

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
def _render_dot_summary_figure(
    df_emm: pd.DataFrame,
    df_subj: pd.DataFrame,
    value_col_subj: str,
    ylabel: str,
    ylim_low: float,
    ylim_high: float,
    main_title: str,
    filename: Path,
    out_root: Path | None,
    exp_version: str | None,
    dv_key: str,                       # "rejection" or "rt"
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
):
    # Spaghetti renderer (v3.4). Standard raincloud per Allen et al. 2019, but
    # applied to a paired design: each emotion houses TWO mirror rainclouds,
    # Fair on the left, Unfair on the right. The three raincloud layers
    # (cloud / rain / lightning) occupy strictly DISJOINT x-sub-bands so they
    # never overlap visually. Same emotion hue is used for Fair and Unfair;
    # alpha alone separates them (Fair = 0.30 fill, Unfair = 0.80). The
    # emmean +/- 95% CI marker and its caps are pure black so the inferential
    # anchor reads crisply against any emotion.
    #
    # Sub-band geometry for each cluster, anchored to the emotion tick at x = i:
    #     Fair side (sign s = -1):    Unfair side (sign s = +1):
    #     - half-violin at x = i + s*0.32  (KDE opens outward)
    #     - dot lane    at x = i + s*0.18  (jitter +/- 0.06)
    #     - emmean+CI   at x = i + s*0.06  (black diamond + caps)
    df_emm = df_emm.copy()
    df_emm[offer_col] = df_emm[offer_col].astype(str).str.strip().str.capitalize()
    df_subj = df_subj.copy()
    df_subj[offer_col] = df_subj[offer_col].astype(str).str.strip().str.capitalize()

    n_emo = len(EMOTION_ORDER)
    x_pos = np.arange(n_emo)
    n_subj = int(df_subj[subject_col].nunique()) if not df_subj.empty else 0

    SIDE = {"Fair": -1, "Unfair": +1}
    X_VIOLIN_OFFSET = 0.24
    X_DOT_OFFSET    = 0.14
    X_EMM_OFFSET    = 0.04
    VIOLIN_MAX_W    = 0.18
    DOT_JITTER_HW   = 0.045
    ALPHA_FILL      = {"Fair": 0.30, "Unfair": 0.80}
    ALPHA_DOT       = {"Fair": 0.55, "Unfair": 0.90}
    # Tighter bandwidth shows more local structure than Scott/Silverman defaults;
    # 0.6/0.7 (vs default 1.0) keeps RT modes/asymmetries visible and avoids
    # over-smoothing each cell into a featureless bell shape.
    KDE_BW_FACTOR   = 0.6 if dv_key == "rejection" else 0.7
    rng = np.random.default_rng(42)

    fig_w_in = 155 / 25.4
    fig_h_in = 88 / 25.4
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))

    yr = float(ylim_high - ylim_low)

    # Pre-compute KDE per cell. Each violin will be PER-CELL normalised below
    # (kde / kde.max() * VIOLIN_MAX_W) so every violin uses the full available
    # width regardless of how peaky its density is. This is the standard
    # violin-plot convention (seaborn.violinplot default); it surfaces the
    # SHAPE of each cell's distribution at the cost of cross-cell density
    # comparability. The caption notes this so reviewers are not misled.
    y_clip = (ylim_low, ylim_high)
    kde_store = {}
    for emo in EMOTION_ORDER:
        for offer in ("Fair", "Unfair"):
            d = df_subj[(df_subj[emotion_col] == emo)
                        & (df_subj[offer_col] == offer)][value_col_subj]
            d = pd.to_numeric(d, errors="coerce").dropna().values
            if len(d) < 2 or np.std(d) < 1e-8:
                continue
            try:
                kde = gaussian_kde(d)
                kde.set_bandwidth(kde.factor * KDE_BW_FACTOR)
            except Exception:
                continue
            lo = max(y_clip[0], float(np.min(d)))
            hi = min(y_clip[1], float(np.max(d)))
            if hi <= lo:
                continue
            kde_store[(emo, offer)] = (kde, lo, hi)

    for i, emo in enumerate(EMOTION_ORDER):
        emo_color = COLOR_MAP.get(emo, "#888888")
        emo_rgb = mcolors.to_rgb(emo_color)

        for offer in ("Fair", "Unfair"):
            sign = SIDE[offer]
            alpha_fill = ALPHA_FILL[offer]
            alpha_dot = ALPHA_DOT[offer]

            x_violin_flat = x_pos[i] + sign * X_VIOLIN_OFFSET
            x_dot_center  = x_pos[i] + sign * X_DOT_OFFSET
            x_emm         = x_pos[i] + sign * X_EMM_OFFSET

            # 1. Half-violin (cloud) on the outer side, PER-CELL normalised
            #    so each violin uses the full VIOLIN_MAX_W at its own density
            #    peak. The flat side sits at x_violin_flat; the curve extends
            #    outward.
            if (emo, offer) in kde_store:
                kde, lo_e, hi_e = kde_store[(emo, offer)]
                y_eval = np.linspace(lo_e, hi_e, 300)
                d_vals = kde(y_eval)
                cell_peak = float(d_vals.max())
                if cell_peak > 0:
                    density = d_vals / cell_peak * VIOLIN_MAX_W
                    edge_alpha = min(alpha_fill + 0.45, 1.0)
                    ax.fill_betweenx(y_eval, x_violin_flat,
                                     x_violin_flat + sign * density,
                                     facecolor=(*emo_rgb, alpha_fill),
                                     edgecolor=(*emo_rgb, edge_alpha),
                                     linewidth=0.7, zorder=2)

            # 2. Dots (rain) in a dedicated lane, no overlap with violin or
            #    emmean.
            data = df_subj[(df_subj[emotion_col] == emo)
                           & (df_subj[offer_col] == offer)][value_col_subj]
            data = pd.to_numeric(data, errors="coerce").dropna().values
            if len(data) > 0:
                x_jit = x_dot_center + rng.uniform(-DOT_JITTER_HW,
                                                    DOT_JITTER_HW,
                                                    size=len(data))
                ax.scatter(x_jit, data,
                           s=9, facecolor=(*emo_rgb, alpha_dot),
                           edgecolor="none", zorder=3)

            # 3. emmean +/- 95% CI (lightning) in BLACK, dedicated lane between
            #    the dot lane and the emotion tick. Fair = open diamond
            #    (white-filled); Unfair = closed diamond (black-filled); both
            #    use black caps that clearly extend past the small marker.
            row = df_emm[(df_emm[emotion_col] == emo)
                         & (df_emm[offer_col] == offer)]
            if not row.empty:
                mv = pd.to_numeric(row["mean_val"].iloc[0], errors="coerce")
                lo = pd.to_numeric(row["lower_val"].iloc[0], errors="coerce")
                hi = pd.to_numeric(row["upper_val"].iloc[0], errors="coerce")
                if pd.notna(mv):
                    yerr = [[max(0.0, float(mv - lo))],
                            [max(0.0, float(hi - mv))]]
                    em_face = "white" if offer == "Fair" else "#111111"
                    em_edge_w = 0.9 if offer == "Fair" else 0.5
                    ax.errorbar(x_emm, mv, yerr=yerr,
                                fmt="D", markersize=3.5,
                                markerfacecolor=em_face,
                                markeredgecolor="#111111",
                                markeredgewidth=em_edge_w,
                                ecolor="#111111",
                                elinewidth=1.0, capsize=3.5, capthick=1.0,
                                zorder=6)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([LABEL_MAP.get(e, e) for e in EMOTION_ORDER])
    ax.set_xlim(-0.55, n_emo - 0.45)
    ax.set_ylim(ylim_low, ylim_high)
    ax.set_xlabel("Emotion", fontsize=7)
    ax.set_ylabel(ylabel, fontsize=7)
    if dv_key == "rejection":
        ax.set_yticks(np.arange(0, 101, 10))
    else:
        ax.set_yticks(np.arange(300, 1801, 200))
    ax.tick_params(axis="both", which="major", labelsize=7, length=3, width=0.7)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.7)
    sns.despine(ax=ax)

    # Bottom-of-figure legend in a single row. Patches encode the fill-alpha
    # scheme (the actual hue varies by emotion); emmean entries are real
    # ErrorbarContainers drawn off-screen so matplotlib's default handler
    # renders them with vertical CI bars and caps -- matching the data area.
    grey_rgb = (0.35, 0.35, 0.35)
    fair_patch = mpatches.Patch(
        facecolor=(*grey_rgb, ALPHA_FILL["Fair"]),
        edgecolor=(*grey_rgb, 0.70),
        linewidth=0.7, label="Fair offer")
    unfair_patch = mpatches.Patch(
        facecolor=(*grey_rgb, ALPHA_FILL["Unfair"]),
        edgecolor=(*grey_rgb, 0.95),
        linewidth=0.7, label="Unfair offer")
    off_x = n_emo + 100
    emm_fair_h = ax.errorbar([off_x], [ylim_low], yerr=[[0.0], [0.0]],
                              fmt="D", markersize=3.5,
                              markerfacecolor="white",
                              markeredgecolor="#111111", markeredgewidth=0.9,
                              ecolor="#111111", elinewidth=1.0,
                              capsize=3.5, capthick=1.0,
                              label="Fair emmean ± 95% CI")
    emm_unfair_h = ax.errorbar([off_x], [ylim_low], yerr=[[0.0], [0.0]],
                                fmt="D", markersize=3.5,
                                markerfacecolor="#111111",
                                markeredgecolor="#111111", markeredgewidth=0.5,
                                ecolor="#111111", elinewidth=1.0,
                                capsize=3.5, capthick=1.0,
                                label="Unfair emmean ± 95% CI")
    fig.legend(handles=[fair_patch, unfair_patch, emm_fair_h, emm_unfair_h],
               loc="lower center", bbox_to_anchor=(0.5, 0.012), ncol=4,
               frameon=False, fontsize=6.5,
               handlelength=2.0, columnspacing=2.0, handletextpad=0.6)

    fig.suptitle(main_title, fontsize=8.5, fontweight="bold",
                 x=0.075, ha="left", y=0.985)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.94, bottom=0.165)

    png_path = filename.with_suffix(".png")
    pdf_path = filename.with_suffix(".pdf")
    svg_path = filename.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight", transparent=True)
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight", transparent=True)
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    if dv_key == "rejection":
        err_desc = ("from the generalised linear mixed model (logistic link) "
                    "with delta-method back-transformation to the probability scale")
        cloud_caveat = (" The half-violin (KDE) shows the participant-mean "
                        "density and is compressed against the axis bounds "
                        "under the inherent floor (Fair near 0%) and ceiling "
                        "(Unfair near 100%) of this measure.")
    else:
        err_desc = ("from the linear mixed model on log-transformed RT, "
                    "back-transformed to milliseconds")
        cloud_caveat = ""
    caption_text = (
        f"Figure caption -- {main_title}\n"
        f"-------------------------------------------------------------\n"
        f"{ylabel} across five emotion contexts. Within each emotion column, "
        f"the fair-offer raincloud (left of the emotion tick) and the unfair-"
        f"offer raincloud (right) share a single hue; the unfair fill is "
        f"deeper than the fair fill. N = {n_subj} participants. "
        f"Each raincloud has three horizontally separated sub-bands: the half-"
        f"violin (kernel-density estimate, Silverman bandwidth; each violin is "
        f"normalised independently so its width reflects the shape of that "
        f"cell's distribution, not its cross-cell density) on the outer side, "
        f"jittered "
        f"subject-mean dots in the middle, and the model emmean ± 95% "
        f"confidence interval (open diamond for fair, filled diamond for "
        f"unfair; both with black caps) on the inner side, {err_desc}."
        f"{cloud_caveat}\n"
    )
    try:
        with open(filename.with_suffix(".caption.txt"), "w", encoding="utf-8") as f:
            f.write(caption_text)
    except Exception:
        pass


def plot_rejection_raincloud_combined(
    df_emm: pd.DataFrame,
    df_subj: pd.DataFrame,
    main_title: str,
    filename: Path,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
    out_root: Path | None = None,
    exp_version: str | None = None,
):
    _render_dot_summary_figure(
        df_emm=df_emm,
        df_subj=df_subj,
        value_col_subj="rejection_rate",
        ylabel="Rejection rate (%)",
        ylim_low=-5.0, ylim_high=115.0,
        main_title=main_title,
        filename=filename,
        out_root=out_root,
        exp_version=exp_version,
        dv_key="rejection",
        subject_col=subject_col,
        emotion_col=emotion_col,
        offer_col=offer_col,
    )


def plot_rt_raincloud_combined(
    df_emm: pd.DataFrame,
    df_subj: pd.DataFrame,
    main_title: str,
    filename: Path,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
    out_root: Path | None = None,
    exp_version: str | None = None,
):
    rt_lo = float(RT_Y_MIN) if RT_Y_MIN is not None else 400.0
    rt_hi = float(RT_Y_MAX) if RT_Y_MAX is not None else 1800.0
    _render_dot_summary_figure(
        df_emm=df_emm,
        df_subj=df_subj,
        value_col_subj="RT",
        ylabel="Reaction time (ms)",
        ylim_low=rt_lo, ylim_high=rt_hi,
        main_title=main_title,
        filename=filename,
        out_root=out_root,
        exp_version=exp_version,
        dv_key="rt",
        subject_col=subject_col,
        emotion_col=emotion_col,
        offer_col=offer_col,
    )


def plot_interaction_spaghetti_combined(
    df_emm_rt: pd.DataFrame,
    df_subj_rt: pd.DataFrame,
    df_emm_rej: pd.DataFrame,
    df_subj_rej: pd.DataFrame,
    main_title: str,
    filename: Path,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
    out_root: Path | None = None,
    exp_version: str | None = None,
    exp_filter: str | None = None,
):
    p = Path(filename)
    parent, stem, suffix = p.parent, p.stem, p.suffix
    if "Combined" in stem:
        rej_name = parent / (stem.replace("Combined", "Rejection") + suffix)
        rt_name = parent / (stem.replace("Combined", "RT") + suffix)
    else:
        rej_name = parent / (stem + "_Rejection" + suffix)
        rt_name = parent / (stem + "_RT" + suffix)
    
    sig_exp = exp_filter or exp_version
    plot_rejection_raincloud_combined(
        df_emm=df_emm_rej, df_subj=df_subj_rej,
        main_title=f"Rejection Rate \u2014 {main_title}",
        filename=rej_name,
        subject_col=subject_col, emotion_col=emotion_col, offer_col=offer_col,
        out_root=out_root, exp_version=sig_exp,
    )
    plot_rt_raincloud_combined(
        df_emm=df_emm_rt, df_subj=df_subj_rt,
        main_title=f"Reaction Time \u2014 {main_title}",
        filename=rt_name,
        subject_col=subject_col, emotion_col=emotion_col, offer_col=offer_col,
        out_root=out_root, exp_version=sig_exp,
    )


def _load_neutral_contrasts(
    out_root: Path | None,
    exp_version: str | None,
    dv: str,
) -> dict:
    # Returns {(target_emotion_lower, offer_lower): sig_string} for "neu - X"
    # contrasts read from Simple_emotion_by_offer_type sheet of the matching
    # STATS_*.xlsx. If the file is integrative (sheet has an Exp column),
    # filters to exp_version when it is "E1"/"E2".
    if out_root is None:
        return {}
    if dv == "rejection":
        candidate_dirs = ["GLMM_Rejection", "Type_Rejection_Rate",
                          "CrossExp_GLMM_Rejection"]
    else:
        candidate_dirs = ["LMM_RT_main", "LMM_RT_full", "Type_Response_Time",
                          "CrossExp_LMM_RT_main", "CrossExp_LMM_RT_full"]
    label_dir = None
    for c in candidate_dirs:
        if (out_root / c).exists():
            label_dir = out_root / c
            break
    if label_dir is None:
        return {}
    stats_workbook = select_stats_workbook(label_dir)
    try:
        sheets = pd.ExcelFile(stats_workbook).sheet_names
        # Try exact name first, then any sheet starting with that prefix
        target = None
        preferred = ["Simple_emotion_by_offer_type",
                     "Simple_emotion_by_offer_type_x_Exp",
                     "Simple_emotion_by_offer_type_x_"]
        for cand in preferred:
            if cand in sheets:
                target = cand
                break
        if target is None:
            for s in sheets:
                if s.startswith("Simple_emotion_by_offer_type"):
                    target = s
                    break
        if target is None:
            return {}
        df = pd.read_excel(stats_workbook, sheet_name=target)
    except Exception:
        return {}

    if "contrast" not in df.columns or "offer_type" not in df.columns:
        return {}

    out = {}
    for _, row in df.iterrows():
        c = str(row["contrast"]).strip()
        parts = [p.strip().lower() for p in c.split("-")]
        if len(parts) != 2:
            continue
        # Accept either "neu - X" (target = X) or "X - neu" (target = X, sign flips
        # but Sig label is symmetric)
        if parts[0] == "neu":
            target_emo = parts[1]
        elif parts[1] == "neu":
            target_emo = parts[0]
        else:
            continue
        offer = str(row["offer_type"]).strip().lower()
        sig = str(row.get("Sig", "")).strip()
        if "Exp" in df.columns and exp_version in ("E1", "E2"):
            if str(row["Exp"]).strip() != exp_version:
                continue
        out[(target_emo, offer)] = sig
    return out


def plot_interaction_profile_combined(
    df_emm_rt: pd.DataFrame,
    df_emm_rej: pd.DataFrame,
    main_title: str,
    filename: Path,
    df_subj_rt: pd.DataFrame | None = None,
    df_subj_rej: pd.DataFrame | None = None,
    out_root: Path | None = None,
    exp_version: str | None = None,
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
):
    # Publication-grade interaction profile (v3.2).
    # Layout: 1x2 panels, x = emotion, two series per panel (Fair / Unfair).
    # Layers, back-to-front: per-subject thin grey lines, model emmean line,
    # 95% CI error bars, emotion-coloured markers, vs-Neutral significance stars.
    # Page: 183 mm x 80 mm (double-column landscape, Nature/Nature Comm style).
    # Triple export: SVG (designer-editable), PDF (publication), PNG 300 dpi (preview).
    n_emo = len(EMOTION_ORDER)
    x_pos = np.arange(n_emo)
    x_offset = 0.11

    df_emm_rt = df_emm_rt.copy()
    df_emm_rej = df_emm_rej.copy()
    for df in (df_emm_rt, df_emm_rej):
        df[offer_col] = df[offer_col].astype(str).str.strip().str.capitalize()

    sub_rt = sub_rej = None
    if df_subj_rt is not None and not df_subj_rt.empty:
        sub_rt = df_subj_rt.copy()
        sub_rt[offer_col] = sub_rt[offer_col].astype(str).str.strip().str.capitalize()
    if df_subj_rej is not None and not df_subj_rej.empty:
        sub_rej = df_subj_rej.copy()
        sub_rej[offer_col] = sub_rej[offer_col].astype(str).str.strip().str.capitalize()

    sig_rej = _load_neutral_contrasts(out_root, exp_version, "rejection")
    sig_rt = _load_neutral_contrasts(out_root, exp_version, "rt")

    fig_w_in = 183 / 25.4
    fig_h_in = 80 / 25.4
    fig, axes = plt.subplots(1, 2, figsize=(fig_w_in, fig_h_in))

    OFFER_STYLE = {
        "Fair":   dict(color="#000000",                ls=(0, (3, 1.6)), shift=-x_offset),
        "Unfair": dict(color=OFFER_COLOR_MAP["Unfair"], ls="-",            shift=+x_offset),
    }

    def draw_panel(ax, df_emm, df_subj, value_col_subj, ylabel,
                   ylim_low, ylim_high, sig_map, panel_letter):
        # Layer 1: per-subject thin grey lines (one per subject per offer)
        if df_subj is not None and not df_subj.empty:
            for offer_lvl, st in OFFER_STYLE.items():
                sub_offer = df_subj[df_subj[offer_col] == offer_lvl]
                if sub_offer.empty:
                    continue
                for pid, g in sub_offer.groupby("participant_id"):
                    g = (g.set_index(emotion_col)
                           .reindex(EMOTION_ORDER)
                           .reset_index())
                    yv = pd.to_numeric(g[value_col_subj], errors="coerce").values
                    if pd.Series(yv).notna().sum() < 2:
                        continue
                    ax.plot(x_pos + st["shift"], yv, color="#888888",
                            lw=0.35, alpha=0.15, zorder=1,
                            solid_capstyle="round")

        # Layer 2-4: model line + CI + emotion-coloured markers
        for offer_lvl, st in OFFER_STYLE.items():
            sub = df_emm[df_emm[offer_col] == offer_lvl]
            if sub.empty:
                continue
            sub = sub.set_index(emotion_col).reindex(EMOTION_ORDER).reset_index()
            mv = pd.to_numeric(sub["mean_val"], errors="coerce").values
            lo = pd.to_numeric(sub["lower_val"], errors="coerce").values
            hi = pd.to_numeric(sub["upper_val"], errors="coerce").values
            yerr_low = np.clip(mv - lo, a_min=0, a_max=None)
            yerr_high = np.clip(hi - mv, a_min=0, a_max=None)
            xs = x_pos + st["shift"]
            ax.plot(xs, mv, linestyle=st["ls"], color=st["color"],
                    lw=1.3, zorder=4, dash_capstyle="round")
            ax.errorbar(xs, mv, yerr=[yerr_low, yerr_high],
                        fmt="none", ecolor=st["color"],
                        capsize=2.2, capthick=0.9, elinewidth=0.9, zorder=5)
            for i, emo in enumerate(EMOTION_ORDER):
                ax.plot(xs[i], mv[i], marker="o", markersize=5.0,
                        markerfacecolor=COLOR_MAP.get(emo, st["color"]),
                        markeredgecolor=st["color"], markeredgewidth=0.9,
                        linestyle="None", zorder=6)

        # Layer 5: significance stars vs Neutral (per offer)
        if sig_map:
            yr = ylim_high - ylim_low
            for offer_lvl, st in OFFER_STYLE.items():
                sub = df_emm[df_emm[offer_col] == offer_lvl]
                if sub.empty:
                    continue
                sub = sub.set_index(emotion_col).reindex(EMOTION_ORDER).reset_index()
                for i, emo in enumerate(EMOTION_ORDER):
                    if emo == "neu":
                        continue
                    sig = sig_map.get((emo, offer_lvl.lower()), "")
                    if sig not in ("*", "**", "***"):
                        continue
                    upper_val = pd.to_numeric(sub["upper_val"].iloc[i], errors="coerce")
                    if pd.isna(upper_val):
                        continue
                    text_y = float(upper_val) + 0.035 * yr
                    text_y = min(text_y, ylim_high - 0.01 * yr)
                    ax.text(x_pos[i] + st["shift"], text_y, sig,
                            ha="center", va="bottom", fontsize=7,
                            color=st["color"], fontweight="bold", zorder=7)

        ax.set_xticks(x_pos)
        ax.set_xticklabels([LABEL_MAP.get(e, e) for e in EMOTION_ORDER])
        ax.set_xlim(-0.5, n_emo - 0.5)
        ax.set_ylim(ylim_low, ylim_high)
        ax.set_xlabel("Emotion context", fontsize=7)
        ax.set_ylabel(ylabel, fontsize=7)
        ax.tick_params(axis="both", which="major", labelsize=7, length=3, width=0.7)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_linewidth(0.7)
        sns.despine(ax=ax)
        ax.text(-0.16, 1.04, panel_letter, transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="top", ha="left")

    draw_panel(
        axes[0], df_emm_rej, sub_rej, "rejection_rate",
        "Rejection rate (%)", 0, 105, sig_rej, "a"
    )
    rt_lo = RT_Y_MIN if RT_Y_MIN is not None else 400
    rt_hi = RT_Y_MAX if RT_Y_MAX is not None else 1800
    draw_panel(
        axes[1], df_emm_rt, sub_rt, "RT",
        "Reaction time (ms)", rt_lo, rt_hi, sig_rt, "b"
    )

    # Compact legend in the lower-right of the rejection panel where the line
    # sits near zero and there is plenty of free space.
    legend_handles = [
        mlines.Line2D([], [], color="#000000", linestyle=(0, (3, 1.6)),
                      marker="o", markersize=5.0,
                      markerfacecolor="#cccccc", markeredgecolor="#000000",
                      markeredgewidth=0.9, lw=1.3, label="Fair"),
        mlines.Line2D([], [], color=OFFER_COLOR_MAP["Unfair"], linestyle="-",
                      marker="o", markersize=5.0,
                      markerfacecolor="#cccccc",
                      markeredgecolor=OFFER_COLOR_MAP["Unfair"],
                      markeredgewidth=0.9, lw=1.3, label="Unfair"),
        mlines.Line2D([], [], color="#888888", lw=0.7, alpha=0.55,
                      label="Per participant"),
    ]
    axes[0].legend(handles=legend_handles, loc="center left",
                   bbox_to_anchor=(0.02, 0.55), frameon=False,
                   fontsize=6.5, handlelength=2.0, labelspacing=0.35,
                   borderaxespad=0.0)

    fig.suptitle(main_title, fontsize=8.5, fontweight="bold", y=0.995)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90,
                        bottom=0.16, wspace=0.30)

    # Triple export: PNG (preview, 300 dpi), PDF (publication), SVG (editable).
    png_path = filename.with_suffix(".png")
    pdf_path = filename.with_suffix(".pdf")
    svg_path = filename.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight", transparent=True)
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight", transparent=True)
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Caption written next to the figure so it can be pasted into the
    # manuscript without retyping; keeps the figure itself free of in-axes
    # methodological footnotes (journals strip those at typesetting).
    n_subj_str = ""
    if sub_rej is not None and "participant_id" in sub_rej.columns:
        n_val = sub_rej["participant_id"].nunique()
        n_subj_str = f" N = {n_val} participants."
    caption_path = filename.with_suffix(".caption.txt")
    caption_text = (
        f"Figure caption -- {main_title}\n"
        f"-------------------------------------------------------------\n"
        f"a, Rejection rate (%) and b, reaction time (ms) for fair "
        f"(black, dashed) and unfair (purple, solid) offers across five emotion "
        f"contexts.{n_subj_str} Marker fill encodes emotion identity (Neutral, "
        f"Affiliative, Disgust, Dominance, Reward). Thin grey lines show "
        f"individual-participant condition means. Error bars denote 95% "
        f"confidence intervals on the response scale: in a from the generalised "
        f"linear mixed model (logistic link) with delta-method back-"
        f"transformation; in b from the linear mixed model on log-transformed "
        f"RT (back-transformed to milliseconds). Asterisks mark FDR-adjusted "
        f"(Benjamini--Hochberg) emmeans contrasts against the Neutral level "
        f"within each offer condition "
        f"(* p < .05, ** p < .01, *** p < .001). Connecting lines are visual "
        f"aids; emotion is a categorical factor.\n"
    )
    try:
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(caption_text)
    except Exception:
        pass


def _render_spaghetti_by_fairness(
    df_emm: pd.DataFrame,
    df_subj: pd.DataFrame,
    value_col_subj: str,
    ylabel: str,
    ylim_low: float,
    ylim_high: float,
    main_title: str,
    filename: Path,
    dv_key: str,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
):
    # By-FAIRNESS transpose of _render_dot_summary_figure. The x-axis carries the
    # two fairness clusters (Fair, Unfair); WITHIN each cluster the five emotions
    # are shown side-by-side as rainclouds (half-violin KDE of subject means +
    # jittered subject-mean dots + emmean +/- 95% CI diamond), coloured by
    # emotion. No connecting lines are drawn (mirrors the original raincloud);
    # the interaction is read by comparing the emotion spread/ordering between
    # the Fair and Unfair clusters.
    df_emm = df_emm.copy()
    df_emm[offer_col] = df_emm[offer_col].astype(str).str.strip().str.capitalize()
    df_subj = df_subj.copy()
    df_subj[offer_col] = df_subj[offer_col].astype(str).str.strip().str.capitalize()

    n_emo = len(EMOTION_ORDER)
    n_subj = int(df_subj[subject_col].nunique()) if not df_subj.empty else 0

    EMO_SLOT = 0.5
    EMO_OFF = {e: (j - (n_emo - 1) / 2.0) * EMO_SLOT
               for j, e in enumerate(EMOTION_ORDER)}
    cluster_span = (n_emo - 1) * EMO_SLOT
    CLUSTER_X = {"Fair": 0.0, "Unfair": cluster_span + 1.1}

    X_EMM_OFF = -0.155
    X_DOT_OFF = 0.0
    X_VIOLIN_OFF = 0.115
    VIOLIN_MAX_W = 0.155
    DOT_JITTER_HW = 0.055
    KDE_BW_FACTOR = 0.6 if dv_key == "rejection" else 0.7
    rng = np.random.default_rng(42)

    fig_w_in = 183 / 25.4
    fig_h_in = 100 / 25.4
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))

    for emo in EMOTION_ORDER:
        emo_rgb = mcolors.to_rgb(COLOR_MAP.get(emo, "#888888"))
        for offer in ("Fair", "Unfair"):
            cx = CLUSTER_X[offer] + EMO_OFF[emo]

            d = df_subj[(df_subj[emotion_col] == emo)
                        & (df_subj[offer_col] == offer)][value_col_subj]
            d = pd.to_numeric(d, errors="coerce").dropna().values

            # 1. half-violin (cloud), opening to the right of the slot
            if len(d) >= 2 and np.std(d) > 1e-8:
                try:
                    kde = gaussian_kde(d)
                    kde.set_bandwidth(kde.factor * KDE_BW_FACTOR)
                    lo = max(ylim_low, float(np.min(d)))
                    hi = min(ylim_high, float(np.max(d)))
                    if hi > lo:
                        yy = np.linspace(lo, hi, 256)
                        dd = kde(yy)
                        peak = float(dd.max())
                        if peak > 0:
                            w = dd / peak * VIOLIN_MAX_W
                            ax.fill_betweenx(yy, cx + X_VIOLIN_OFF,
                                             cx + X_VIOLIN_OFF + w,
                                             facecolor=(*emo_rgb, 0.30),
                                             edgecolor=(*emo_rgb, 0.85),
                                             linewidth=0.6, zorder=2)
                except Exception:
                    pass

            # 2. jittered subject-mean dots (rain)
            if len(d) > 0:
                xj = cx + X_DOT_OFF + rng.uniform(-DOT_JITTER_HW, DOT_JITTER_HW,
                                                  size=len(d))
                ax.scatter(xj, d, s=7, facecolor=(*emo_rgb, 0.55),
                           edgecolor="none", zorder=3)

            # 3. emmean +/- 95% CI (lightning), emotion-coloured filled diamond
            row = df_emm[(df_emm[emotion_col] == emo)
                         & (df_emm[offer_col] == offer)]
            if not row.empty:
                mv = pd.to_numeric(row["mean_val"].iloc[0], errors="coerce")
                lo_ = pd.to_numeric(row["lower_val"].iloc[0], errors="coerce")
                hi_ = pd.to_numeric(row["upper_val"].iloc[0], errors="coerce")
                if pd.notna(mv):
                    ex = cx + X_EMM_OFF
                    yerr = [[max(0.0, float(mv - lo_))],
                            [max(0.0, float(hi_ - mv))]]
                    ax.errorbar(ex, mv, yerr=yerr, fmt="D", markersize=4.0,
                                markerfacecolor=COLOR_MAP.get(emo, "#888888"),
                                markeredgecolor="#111111", markeredgewidth=0.5,
                                ecolor="#111111", elinewidth=1.0, capsize=3.0,
                                capthick=1.0, zorder=6)

    ax.set_xticks([CLUSTER_X["Fair"], CLUSTER_X["Unfair"]])
    ax.set_xticklabels(["Fair offer", "Unfair offer"])
    xpad = cluster_span / 2.0 + 0.5
    ax.set_xlim(CLUSTER_X["Fair"] - xpad, CLUSTER_X["Unfair"] + xpad)
    ax.set_ylim(ylim_low, ylim_high)
    ax.set_xlabel("Offer fairness", fontsize=7)
    ax.set_ylabel(ylabel, fontsize=7)
    if dv_key == "rejection":
        ax.set_yticks(np.arange(0, 101, 10))
    else:
        ax.set_yticks(np.arange(300, int(ylim_high) + 1, 200))
    ax.tick_params(axis="both", which="major", labelsize=7, length=3, width=0.7)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.7)
    sns.despine(ax=ax)

    # --- Two-row legend: (1) emotion colour key, (2) raincloud element key.
    # Row 1 maps hue -> emotion (the only cue distinguishing emotions here);
    # row 2 defines the three layers, including a real ErrorbarContainer handle
    # drawn off-screen so the legend shows the emmean diamond WITH its CI caps.
    emotion_handles = [
        mlines.Line2D([], [], marker="D", linestyle="None", markersize=4.5,
                      markerfacecolor=COLOR_MAP.get(e, "#888888"),
                      markeredgecolor="#111111", markeredgewidth=0.5,
                      label=LABEL_MAP.get(e, e))
        for e in EMOTION_ORDER
    ]
    grey = (0.35, 0.35, 0.35)
    density_patch = mpatches.Patch(facecolor=(*grey, 0.30),
                                   edgecolor=(*grey, 0.85), linewidth=0.6,
                                   label="Participant-mean density (KDE)")
    dots_handle = mlines.Line2D([], [], marker="o", linestyle="None",
                                markerfacecolor=(*grey, 0.55),
                                markeredgecolor="none", markersize=4.0,
                                label="Participant means")
    off_x = CLUSTER_X["Unfair"] + 100.0   # off-screen anchor; only used for the handle
    emm_handle = ax.errorbar([off_x], [ylim_low], yerr=[[0.0], [0.0]], fmt="D",
                             markersize=4.0, markerfacecolor=grey,
                             markeredgecolor="#111111", markeredgewidth=0.5,
                             ecolor="#111111", elinewidth=1.0, capsize=3.0,
                             capthick=1.0, label="Model emmean ± 95% CI")

    leg1 = fig.legend(handles=emotion_handles, loc="lower center",
                      bbox_to_anchor=(0.5, 0.085), ncol=n_emo, frameon=False,
                      fontsize=6.5, handlelength=1.2, columnspacing=1.3,
                      handletextpad=0.3, title="Proposer emotion",
                      title_fontsize=6.5)
    fig.add_artist(leg1)
    fig.legend(handles=[density_patch, dots_handle, emm_handle],
               loc="lower center", bbox_to_anchor=(0.5, 0.014), ncol=3,
               frameon=False, fontsize=6.5, handlelength=1.8,
               columnspacing=2.0, handletextpad=0.4)

    fig.suptitle(main_title, fontsize=8.5, fontweight="bold",
                 x=0.075, ha="left", y=0.985)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.93, bottom=0.28)

    png_path = filename.with_suffix(".png")
    pdf_path = filename.with_suffix(".pdf")
    svg_path = filename.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight", transparent=True)
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight", transparent=True)
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    if dv_key == "rejection":
        err_desc = ("from the generalised linear mixed model (logistic link) "
                    "with delta-method back-transformation to the probability scale")
        cloud_caveat = (" The half-violins are compressed under the floor (Fair "
                        "near 0%) and ceiling (Unfair near 100%) of this measure.")
    else:
        err_desc = ("from the linear mixed model on log-transformed RT, "
                    "back-transformed to milliseconds")
        cloud_caveat = ""
    caption_text = (
        f"Figure caption -- {main_title}\n"
        f"-------------------------------------------------------------\n"
        f"{ylabel} grouped by offer fairness (two clusters: fair vs unfair). Within "
        f"each cluster the five emotion contexts are shown side by side as "
        f"rainclouds, coloured by emotion (Neutral, Affiliative, Disgust, "
        f"Dominance, Reward). N = {n_subj} participants. Each raincloud comprises a "
        f"half-violin (kernel-density estimate of participant means, normalised "
        f"independently), jittered subject-mean dots, and the model emmean +/- 95% "
        f"confidence interval (emotion-coloured diamond, black caps), {err_desc}. "
        f"No lines connect the clusters (matching the emotion-x raincloud); the "
        f"emotion x fairness interaction is read by comparing the spread and "
        f"ordering of emotions between the fair and unfair clusters.{cloud_caveat}\n"
    )
    try:
        with open(filename.with_suffix(".caption.txt"), "w", encoding="utf-8") as f:
            f.write(caption_text)
    except Exception:
        pass


def plot_spaghetti_by_fairness_combined(
    df_emm_rt: pd.DataFrame,
    df_subj_rt: pd.DataFrame,
    df_emm_rej: pd.DataFrame,
    df_subj_rej: pd.DataFrame,
    main_title: str,
    filename: Path,
    subject_col: str = "participant_id",
    emotion_col: str = "emotion",
    offer_col: str = "offer_type",
    out_root: Path | None = None,
    exp_version: str | None = None,
    exp_filter: str | None = None,
):
    # Two figures (Rejection, RT) mirroring plot_interaction_spaghetti_combined,
    # but with fairness on the x-axis. out_root/exp_version/exp_filter are accepted
    # for call-site symmetry with the emotion-x version and are not used here.
    p = Path(filename)
    parent, stem, suffix = p.parent, p.stem, p.suffix
    if "Combined" in stem:
        rej_name = parent / (stem.replace("Combined", "Rejection") + suffix)
        rt_name = parent / (stem.replace("Combined", "RT") + suffix)
    else:
        rej_name = parent / (stem + "_Rejection" + suffix)
        rt_name = parent / (stem + "_RT" + suffix)
    _render_spaghetti_by_fairness(
        df_emm=df_emm_rej, df_subj=df_subj_rej,
        value_col_subj="rejection_rate", ylabel="Rejection rate (%)",
        ylim_low=-5.0, ylim_high=115.0,
        main_title=f"Rejection Rate — {main_title}",
        filename=rej_name, dv_key="rejection",
        subject_col=subject_col, emotion_col=emotion_col, offer_col=offer_col,
    )
    rt_lo = float(RT_Y_MIN) if RT_Y_MIN is not None else 400.0
    rt_hi = float(RT_Y_MAX) if RT_Y_MAX is not None else 1800.0
    _render_spaghetti_by_fairness(
        df_emm=df_emm_rt, df_subj=df_subj_rt,
        value_col_subj="RT", ylabel="Reaction time (ms)",
        ylim_low=rt_lo, ylim_high=rt_hi,
        main_title=f"Reaction Time — {main_title}",
        filename=rt_name, dv_key="rt",
        subject_col=subject_col, emotion_col=emotion_col, offer_col=offer_col,
    )


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
    x_levels = ["Fair", "Unfair"]
    df_emm = df_emm.copy()
    df_subj = df_subj.copy()
    df_emm["offer_type"] = df_emm["offer_type"].astype(str).str.strip().str.capitalize()
    df_subj["offer_type"] = df_subj["offer_type"].astype(str).str.strip().str.capitalize()
    
    n_emo = len(EMOTION_ORDER)
    fig, axes = plt.subplots(
        1, n_emo,
        figsize=(2.4 * n_emo + 0.8, 4.4),
        sharey=True
    )
    if n_emo == 1:
        axes = [axes]
    
    is_pct = "%" in ylabel
    is_rt = "Time" in ylabel or "ms" in ylabel
    
    alpha_indiv_line = 0.28
    alpha_indiv_dot = 0.30
    
    for ax_i, emo in enumerate(EMOTION_ORDER):
        ax = axes[ax_i]
        
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
        ax.set_xlim(-0.35, 1.35)
        
        if is_rt:
            if RT_Y_MIN is not None:
                ax.set_ylim(bottom=RT_Y_MIN)
            if RT_Y_MAX is not None:
                ax.set_ylim(top=RT_Y_MAX)
        elif is_pct:
            ax.set_ylim(0, 100)
        sns.despine(ax=ax)
    
    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=1.02)
    
    if is_pct:
        method_note = "Thin gray lines = individual subjects. Colored line = GLMM emmean \u00B1 1 SE (delta method on response scale)."
    else:
        method_note = "Thin gray lines = individual subjects. Colored line = LMM emmean \u00B1 1 SE (delta method, exp transform)."
    fig.text(0.5, -0.02, method_note, ha="center", va="top", fontsize=9, color="#555555", style="italic")
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.18)
    
    pdf_path = filename.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_interaction_line(df, y_col, lower_col, upper_col, ylabel, main_title, filename):
    x_axis = "offer_type" if "offer_type" in df.columns else ("offer_ratio" if "offer_ratio" in df.columns else None)
    if not x_axis: return
    
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
    pdf_path = filename.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_interaction_bar(df, y_col, lower_col, upper_col, ylabel, main_title, filename):
    x_axis = "offer_type" if "offer_type" in df.columns else ("offer_ratio" if "offer_ratio" in df.columns else None)
    if not x_axis: return
    
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
    pdf_path = filename.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_forest_from_posthoc(df: pd.DataFrame, title: str, filename: Path, mode: str):
    if df.empty: return
    est_col = get_first_col(df, ["estimate", "emmean", "value", "odds.ratio"])
    se_col = get_first_col(df, ["SE", "std.error", "SE."])
    p_col = get_first_col(df, ["p.value", "p_val", "p"])
    
    contrast_col = get_first_col(df, ["contrast", "emotion_pairwise", "reaction_pairwise"])
    if not est_col or not p_col: return

    if contrast_col is not None:
        labels = pd.Series(df[contrast_col].astype(str)).reset_index(drop=True)
    else:
        labels = pd.Series(df.index.astype(str))
    labels = labels.str.replace("fair", "Fair").str.replace("unfair", "Unfair")
    for k, v in LABEL_MAP.items():
        labels = labels.str.replace(fr'\b{k}\b', v, regex=True)
    
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
    colors = ["#d73027" if parse_display_p(p) < 0.05 else "#bdbdbd"
              for p in df_plot[p_col]]
    
    ax.scatter(df_plot["x"], y_pos, color=colors, s=60, zorder=3)
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
    
    if mode == "rejection":
        x_vals = df_plot["x"].dropna()
        if not x_vals.empty:
            x_min, x_max = float(x_vals.min()), float(x_vals.max())
            extreme = (x_min > 0) and ((x_max / x_min >= 100) or (x_min <= 0.05))
            if extreme:
                ax.set_xscale("log")
                ax.set_xlabel("Odds Ratio (log scale)")
    
    sns.despine(); plt.tight_layout()
    pdf_path = filename.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
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
                if len(s) >= 6 and s[:2].lower() == "vp":
                    return s
                digits = "".join([ch for ch in s if ch.isdigit()])
                if not digits:
                    return s
                prefix = "VP" if any(ch.isupper() for ch in s[:2]) else "Vp"
                return f"{prefix}{int(digits):04d}"
            df["participant_id"] = df["participant_id"].apply(clean_id)
            
        required = {"Offers_You", "Offers_Other", "emotion", "reaction", "RT"}
        missing = sorted(required.difference(df.columns))
        if missing:
            raise ValueError(f"Required columns missing from {path}: {missing}")

        # Match the behavioral analysis filters exactly and in the same order.
        df = df[df["Offers_Other"].isin([5, 6, 8, 9])].copy()
        df = df[df["reaction"] != 0].copy()
        df = df[(df["RT"] >= 300) & (df["RT"] <= 3000)].copy()

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
            
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()


def fetch_lmm_stats(out_root: Path, exp_version: str, y_var: str,
                    exp_filter: str | None = None) -> pd.DataFrame | None:
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
    
    try:
        stats_workbook = select_stats_workbook(label_dir)
        xls = pd.ExcelFile(stats_workbook)
        target_sheet = None
        for cand in ["Descriptive_Means", "Descriptive_Means_SE"]:
            if cand in xls.sheet_names:
                target_sheet = cand
                break
        if target_sheet is None: return None
        
        df = pd.read_excel(stats_workbook, sheet_name=target_sheet)
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
        
        is_rejection_var = ("rejection" in y_var.lower() or "rate" in y_var.lower())
        is_logit_scale = is_rejection_var and (mean_numeric is not np.nan) and \
                         (abs(mean_numeric) > 1.05 or res[y_col].min() < -0.5)
        
        if "RT" in y_var and mean_numeric < 20 and se_col:
            res["mean_val"] = np.exp(res[y_col].astype(float))
            if lower_col and upper_col:
                # Back-transform the emmeans 95% CI endpoints (log -> ms).
                res["lower_val"] = np.exp(res[lower_col].astype(float))
                res["upper_val"] = np.exp(res[upper_col].astype(float))
            else:
                se_ms = res["mean_val"] * res[se_col].astype(float)
                res["lower_val"] = res["mean_val"] - (CI_MULTIPLIER * se_ms)
                res["upper_val"] = res["mean_val"] + (CI_MULTIPLIER * se_ms)
        elif is_logit_scale:
            res["mean_val"] = expit(res[y_col].astype(float))
            if lower_col and upper_col:
                # Back-transform the emmeans 95% CI endpoints (logit -> prob).
                res["lower_val"] = expit(res[lower_col].astype(float))
                res["upper_val"] = expit(res[upper_col].astype(float))
            elif se_col:
                p = res["mean_val"]
                se_p = p * (1 - p) * res[se_col].astype(float)
                res["lower_val"] = p - CI_MULTIPLIER * se_p
                res["upper_val"] = p + CI_MULTIPLIER * se_p
            else:
                res["lower_val"] = res["mean_val"]
                res["upper_val"] = res["mean_val"]
        else:
            res["mean_val"] = res[y_col].astype(float)
            if lower_col and upper_col:
                res["lower_val"] = res[lower_col].astype(float)
                res["upper_val"] = res[upper_col].astype(float)
            elif se_col:
                res["lower_val"] = res["mean_val"] - CI_MULTIPLIER * res[se_col].astype(float)
                res["upper_val"] = res["mean_val"] + CI_MULTIPLIER * res[se_col].astype(float)
            else:
                res["lower_val"] = res["mean_val"]
                res["upper_val"] = res["mean_val"]
                
        if is_rejection_var and res["mean_val"].max() <= 1.05:
            res["mean_val"] *= 100.0
            res["lower_val"] *= 100.0
            res["upper_val"] *= 100.0
        
        if exp_filter is not None and "Exp" in res.columns:
            res = res[res["Exp"].astype(str) == str(exp_filter)].copy()
            if res.empty:
                print(f"   [Warn] No rows after Exp filter '{exp_filter}' in {target_sheet}.")
                return None
        
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
                mean_val = float(np.mean(y_vals))
                lower_val = mean_val
                upper_val = mean_val

            kde_fc = _rgba(color, 0.15) if offer == "fair" else _rgba(color, 0.75)
            kde_ec = color if offer == "fair" else "none"
            scat_fc = "none" if offer == "fair" else color
            scat_ec = color if offer == "fair" else "white"            
            stat_mfc = "white" if offer == "fair" else color

            try:
                # Defensive check: prevent KDE from failing on zero variance (identical subject means)
                if np.std(y_vals) < 1e-8:
                    raise np.linalg.LinAlgError("Zero variance in data, skipping KDE")

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

    fig.suptitle(title, fontsize=24, fontweight="bold", y=0.98) 
    
    legend_elements = [
        mpatches.Patch(facecolor=_rgba("#808080", 0.15), edgecolor="#808080", label="Fair Offer", linewidth=1.5),
        mpatches.Patch(facecolor=_rgba("#808080", 0.75), edgecolor="none", label="Unfair Offer"),
        mlines.Line2D([], [], color='#808080', marker='o', linestyle='-',
                      linewidth=1.5, markersize=7, mfc='black', mec='black',
                      label="Estimated marginal mean \u00B1 1 SE (delta method)")
    ]
    fig.legend(handles=legend_elements, bbox_to_anchor=(0.5, 0.89), loc="center", ncol=3, frameon=False, fontsize=14)
    
    plt.tight_layout(rect=[0, 0.0, 1.0, 0.92])
    
    # Dual Export: PDF for publication, PNG for preview
    pdf_path = output_path_png.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
    plt.savefig(output_path_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

# ==============================================================================
# 5) Subject Diagnostics & Axiom Validation
# ==============================================================================
def plot_individual_heatmap(df_raw: pd.DataFrame, val_col: str, val_label: str,
                             title: str, output_path: Path,
                             figure_caption: str | None = None):
    if df_raw.empty or val_col not in df_raw.columns:
        return
    
    df_agg = df_raw.groupby(
        ["participant_id", "emotion", "offer_type"], as_index=False
    )[val_col].mean()
    df_agg["condition"] = df_agg["emotion"].astype(str) + "_" + df_agg["offer_type"].astype(str)
    df_pivot = df_agg.pivot(index="participant_id", columns="condition", values=val_col)
    
    ordered_cols = [f"{emo}_{offer}" for offer in ["fair", "unfair"]
                                       for emo in EMOTION_ORDER
                                       if f"{emo}_{offer}" in df_pivot.columns]
    df_pivot = df_pivot[ordered_cols]
    
    fair_cols = [c for c in df_pivot.columns if c.endswith("_fair")]
    unfair_cols = [c for c in df_pivot.columns if c.endswith("_unfair")]
    is_rejection = "rejection" in val_col.lower()
    sort_description = ""
    if fair_cols and unfair_cols:
        if is_rejection:
            df_pivot["_sort"] = df_pivot[unfair_cols].mean(axis=1) - df_pivot[fair_cols].mean(axis=1)
            sort_description = "Rows sorted by fairness sensitivity (mean unfair rejection - mean fair rejection), descending"
        else:
            df_pivot["_sort"] = df_pivot[unfair_cols].mean(axis=1)
            sort_description = "Rows sorted by mean RT on unfair trials, descending"
        df_pivot = df_pivot.sort_values("_sort", ascending=False).drop(columns=["_sort"])
    
    def col_label(c):
        emo, offer = c.split("_", 1)
        emo_short = {"neu": "Neu", "aff": "Aff", "dis": "Dis",
                     "dom": "Dom", "enj": "Rew"}.get(emo, emo.capitalize())
        offer_long = "Fair" if offer == "fair" else "Unfair"
        return f"{emo_short}\n{offer_long}"
    pretty_labels = [col_label(c) for c in df_pivot.columns]
    
    n_rows = len(df_pivot)
    fig_height = max(6.0, min(n_rows * 0.28, 14.0))
    fig, ax = plt.subplots(figsize=(10, fig_height))
    
    if is_rejection:
        cmap, vmin, vmax = "coolwarm", 0, 100
    else:
        cmap, vmin, vmax = "viridis", None, None
    
    sns.heatmap(
        df_pivot, cmap=cmap, vmin=vmin, vmax=vmax,
        linewidths=0.4, linecolor='white',
        cbar_kws={'label': val_label, 'shrink': 0.85},
        ax=ax
    )
    ax.set_xticklabels(pretty_labels, rotation=0, ha='center', fontsize=10)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=9)
    
    n_fair = len(fair_cols)
    if n_fair > 0 and n_fair < df_pivot.shape[1]:
        ax.axvline(x=n_fair, color="white", lw=4.0, zorder=10)
        ax.axvline(x=n_fair, color="black", lw=1.5, zorder=11)
    
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel("Participant ID", fontsize=11)
    ax.set_xlabel("")
    
    if figure_caption is None:
        offer_grp = "Fair offers (left 5 columns) vs Unfair offers (right 5 columns)"
        figure_caption = (
            f"Each cell shows the mean {val_label.lower()} for one participant "
            f"(row) in one emotion x offer condition (column). "
            f"{offer_grp}, separated by black divider. "
            f"Emotions: Neu = Neutral, Aff = Affiliative, Dis = Disgust, "
            f"Dom = Dominance, Rew = Reward. {sort_description}."
        )
    fig.text(0.5, -0.02, figure_caption, ha="center", va="top",
             fontsize=9, color="#444444", style="italic", wrap=True)
    
    plt.tight_layout()
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
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
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
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
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', transparent=True)
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
... [Readme content unchanged] ...
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
    stats_workbook = select_stats_workbook(label_dir)
    xls = pd.ExcelFile(stats_workbook)

    is_cross_exp = "CrossExp" in exp_version
    if exp_version.startswith("E") and exp_version[1:].isdigit():
        global_exp_str = f"Exp. {exp_version[1:]}"
    elif is_cross_exp:
        global_exp_str = "Cross-Experiment"
    else:
        global_exp_str = str(exp_version)

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
                is_glmm_rejection = (("GLMM_Rejection" in label_dir.name) or
                                     ("Rejection_Rate" in label_dir.name))
                is_rt = (("Response_Time" in label_dir.name) or
                         ("LMM_RT" in label_dir.name)) and not is_glmm_rejection
                mean_numeric = float(pd.to_numeric(df_desc[y_col], errors="coerce").dropna().mean()) if not df_desc.empty else np.nan
                
                if is_glmm_rejection:
                    df_desc["__prob"] = expit(df_desc[y_col].astype(float))
                    df_desc["__prob_pct"] = df_desc["__prob"] * 100.0
                    if lower_col and upper_col:
                        df_desc["__prob_lo_pct"] = expit(df_desc[lower_col].astype(float)) * 100.0
                        df_desc["__prob_hi_pct"] = expit(df_desc[upper_col].astype(float)) * 100.0
                    else:
                        p = df_desc["__prob"]
                        se_p = p * (1 - p) * df_desc[se_col].astype(float)
                        mult = 1.0 if ERROR_BAR_TYPE == "SE" else CI_MULTIPLIER
                        df_desc["__prob_lo_pct"] = (p - mult * se_p) * 100.0
                        df_desc["__prob_hi_pct"] = (p + mult * se_p) * 100.0
                
                elif is_rt and np.isfinite(mean_numeric) and mean_numeric < 20:
                    df_desc["RT_ms"] = np.exp(df_desc[y_col].astype(float))
                    se_ms = df_desc["RT_ms"] * df_desc[se_col].astype(float)
                    mult = 1.0 if ERROR_BAR_TYPE == "SE" else CI_MULTIPLIER
                    df_desc["lower_ms"], df_desc["upper_ms"] = df_desc["RT_ms"] - (mult * se_ms), df_desc["RT_ms"] + (mult * se_ms)
                
                else:
                    if ERROR_BAR_TYPE == "SE":
                        df_desc["__LCL_SE"], df_desc["__UCL_SE"] = df_desc[y_col] - df_desc[se_col], df_desc[y_col] + df_desc[se_col]
                    else:
                        df_desc["__LCL"], df_desc["__UCL"] = df_desc[y_col] - CI_MULTIPLIER * df_desc[se_col], df_desc[y_col] + CI_MULTIPLIER * df_desc[se_col]

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
        if exp_version in ("Integrative", "CrossExp_E1_vs_E2"):
            tag = f"{exp_version}_{exp}"
        else:
            tag = exp_version
        exp_display = f"Exp. {exp[1:]}" if isinstance(exp, str) and exp.startswith("E") and exp[1:].isdigit() else (str(exp) if exp else "Overall")
        title_suffix = f" ({exp_display})"
        
        if "RT" in df_exp.columns:
            plot_individual_heatmap(
                df_exp, "RT", "Mean RT (ms)",
                f"Individual Subject Reaction Times{title_suffix}",
                heat_dir / f"SubjectMatrix_{tag}_RT.png"
            )
        if "rejection_rate" in df_exp.columns:
            plot_individual_heatmap(
                df_exp, "rejection_rate", "Rejection Rate (%)",
                f"Individual Subject Rejection Patterns{title_suffix}",
                heat_dir / f"SubjectMatrix_{tag}_Rejection.png"
            )
            plot_diagnostic_fairness_scatter(df_exp, heat_dir / f"Diag_{tag}_Fairness_Scatter.png", f"Diagnostic: Fairness Sensitivity{title_suffix}")
            plot_diagnostic_emotion_scatter(df_exp, heat_dir / f"Diag_{tag}_Emotion_Scatter.png", f"Diagnostic: Emotion Volatility{title_suffix}")
        
        has_rt = ("RT" in df_exp.columns)
        has_rej = ("rejection_rate" in df_exp.columns)
        
        exp_filter_arg = exp if exp_version in ("Integrative", "CrossExp_E1_vs_E2") else None
        lmm_stats_rt = fetch_lmm_stats(out_root, exp_version, "RT", exp_filter=exp_filter_arg) if has_rt else None
        lmm_stats_rej = fetch_lmm_stats(out_root, exp_version, "rejection_rate", exp_filter=exp_filter_arg) if has_rej else None
        
        if has_rt and has_rej and lmm_stats_rt is not None and lmm_stats_rej is not None:
            df_subj_rt = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["RT"].mean()
            df_subj_rej = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["rejection_rate"].mean()
            plot_interaction_spaghetti_combined(
                df_emm_rt=lmm_stats_rt, df_subj_rt=df_subj_rt,
                df_emm_rej=lmm_stats_rej, df_subj_rej=df_subj_rej,
                main_title=f"Behavior{title_suffix}",
                filename=spag_dir / f"Spag_{tag}_Combined.png",
                out_root=out_root, exp_version=exp_version,
                exp_filter=exp_filter_arg
            )
        else:
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
        
        if has_rt and has_rej and lmm_stats_rt is not None and lmm_stats_rej is not None:
            df_subj_rt_p = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["RT"].mean()
            df_subj_rej_p = df_exp.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["rejection_rate"].mean()
            plot_interaction_profile_combined(
                df_emm_rt=lmm_stats_rt,
                df_emm_rej=lmm_stats_rej,
                df_subj_rt=df_subj_rt_p,
                df_subj_rej=df_subj_rej_p,
                out_root=out_root,
                exp_version=exp if exp_version in ("Integrative", "CrossExp_E1_vs_E2") else exp_version,
                main_title=f"Interaction Profile{title_suffix}",
                filename=prof_dir / f"Profile_{tag}_Combined.png"
            )
            # By-fairness raincloud (transpose of the spaghetti): x = Fair/Unfair,
            # five emotions as side-by-side rainclouds within each cluster, with a
            # faint emotion line joining each emotion's fair and unfair emmean.
            plot_spaghetti_by_fairness_combined(
                df_emm_rt=lmm_stats_rt, df_subj_rt=df_subj_rt_p,
                df_emm_rej=lmm_stats_rej, df_subj_rej=df_subj_rej_p,
                main_title=f"Behavior by Fairness{title_suffix}",
                filename=spag_dir / f"SpagByFairness_{tag}_Combined.png",
                out_root=out_root, exp_version=exp_version, exp_filter=exp_filter_arg
            )
    
    if exp_version in ("Integrative", "CrossExp_E1_vs_E2") and len(exps) > 1:
        print(f"   -> Generating MERGED spaghetti (all experiments)")
        df_merged = df_trials.copy()
        has_rt_m = ("RT" in df_merged.columns)
        has_rej_m = ("rejection_rate" in df_merged.columns)
        
        def _marginalize_over_exp(df_emm):
            if df_emm is None or "Exp" not in df_emm.columns:
                return df_emm
            return (df_emm.groupby(["emotion", "offer_type"], as_index=False)
                          [["mean_val", "lower_val", "upper_val"]].mean())
        
        lmm_stats_rt_m = fetch_lmm_stats(out_root, exp_version, "RT", exp_filter=None) if has_rt_m else None
        lmm_stats_rej_m = fetch_lmm_stats(out_root, exp_version, "rejection_rate", exp_filter=None) if has_rej_m else None
        lmm_stats_rt_m = _marginalize_over_exp(lmm_stats_rt_m)
        lmm_stats_rej_m = _marginalize_over_exp(lmm_stats_rej_m)
        
        if has_rt_m and has_rej_m and lmm_stats_rt_m is not None and lmm_stats_rej_m is not None:
            df_subj_rt_m = df_merged.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["RT"].mean()
            df_subj_rej_m = df_merged.groupby(["participant_id", "emotion", "offer_type"], as_index=False)["rejection_rate"].mean()
            plot_interaction_spaghetti_combined(
                df_emm_rt=lmm_stats_rt_m, df_subj_rt=df_subj_rt_m,
                df_emm_rej=lmm_stats_rej_m, df_subj_rej=df_subj_rej_m,
                main_title=f"Behavior (Merged across Experiments)",
                filename=spag_dir / f"Spag_{exp_version}_Merged.png",
                out_root=None, exp_version=None, exp_filter=None
            )
            plot_spaghetti_by_fairness_combined(
                df_emm_rt=lmm_stats_rt_m, df_subj_rt=df_subj_rt_m,
                df_emm_rej=lmm_stats_rej_m, df_subj_rej=df_subj_rej_m,
                main_title=f"Behavior by Fairness (Merged across Experiments)",
                filename=spag_dir / f"SpagByFairness_{exp_version}_Merged.png",
                out_root=None, exp_version=None, exp_filter=None
            )

if __name__ == "__main__":
    run_version = EXPERIMENT_VERSION
    if "--e1" in sys.argv: run_version = "E1"
    elif "--e2" in sys.argv: run_version = "E2"
    elif "--integrative" in sys.argv: run_version = "Integrative"

    # Canonicalise the version so a lowercase EXPERIMENT_VERSION (e.g. "integrative",
    # "e2") still selects the correct case-sensitive code paths and output dirs.
    _CANON = {"e1": "E1", "e2": "E2", "integrative": "Integrative",
              "crossexp_e1_vs_e2": "CrossExp_E1_vs_E2"}
    run_version = _CANON.get(run_version.lower(), run_version)

    root = detect_project_root(Path(__file__).resolve())
    if not root: raise FileNotFoundError("Project root not found.")

    out_root = choose_output_root(root, exp_version=run_version, prefer_debug=("--debug" in sys.argv))
    figures_dir = out_root / "Figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Info: Experiment Version: {run_version}")
    print(f"Info: Output Root:        {out_root}")

    if run_version in ("Integrative", "CrossExp_E1_vs_E2"):
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
