#!/usr/bin/env python3
"""
Manipulation-check reporting for the three post-task cover-story belief ratings
(Rating_1/2/3), experiments E1 and E2.

Deliverables (written to results/Behavior/Manipulation_Checks/):
  - MANIPULATION_CHECK_Ratings.csv / .md : descriptive stats + one-sample
    Wilcoxon signed-rank tests against the 0-100 VAS scale midpoint (50), and
    E1-vs-E2 Mann-Whitney comparisons per item.
  - ManipulationCheck_Ratings_E1E2.pdf / .png : publication figure.

Ratings: 0-100 VAS with printed anchors "Ueberhaupt nicht" (0), "Neutral" (50),
"Vollstaendig" (100); higher = stronger belief; slider initialized at 50. The one-
sample tests use 50 (the labeled Neutral / slider default) as the reference, NOT 0
(0 is the exclusion criterion, applied during screening). Verbatim German items and
the working English gloss:
  Rating_1  "Inwieweit glauben Sie, dass das Foto des Gegenuebers Ihre
             Entscheidung ueber die Vorschlaege beeinflusst hat?"
             -> perceived influence of the proposer's FACE on one's own decision
                (subjective-impact / awareness item; direction is theory-dependent)
  Rating_2  "Inwieweit glauben Sie, dass die Vorschlaege ... von echten
             Menschen/Individuen gemacht wurden?"
             -> belief the OFFERS were made by REAL people (proposer authenticity)
  Rating_3  "Inwieweit glauben Sie, dass die standardisierten Fotos auf echten
             Menschen/Individuen basieren?"
             -> belief the standardized PHOTOS are based on REAL people (face authenticity)

Rating_2/3 are cover-story authenticity checks (high = cover story believed);
Rating_1 is a subjective-impact item.

Analysis sample = behavioral analysis subjects (matches Method_Regression
trials.csv). E1 excludes the one covariate-file subject (Vp0022) absent from the
analysis sample, giving n = 30 per experiment (aligned with the reported models).

EXPLORATORY manipulation check, n = 30/experiment. The VAS is bounded and skewed,
so nonparametric methods are used throughout.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
MIDPOINT = 50.0
RATINGS = ["Rating_1", "Rating_2", "Rating_3"]
EXPS = ["E1", "E2"]
LABELS = {
    "Rating_1": "Face influenced\nown decision",
    "Rating_2": "Offers from\nreal people",
    "Rating_3": "Photos of\nreal people",
}
COLORS = {"E1": "#0072B2", "E2": "#E69F00"}   # Okabe-Ito blue / orange
BOOT_SEED = 42
N_BOOT = 10000


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "data").is_dir() and (p / ".claude").is_dir():
            return p
    sys.exit("ERROR: project root (a dir containing both 'data/' and '.claude/') not found.")


def digit_id(x):
    m = re.search(r"\d+", str(x))
    return str(int(m.group())) if m else None


def load_exp(root: Path, exp: str):
    covp = root / "data" / f"02_Pipeline_Output_{exp}" / "Covariates" / f"SVO_PID5BF_PostRating_{exp}.xlsx"
    trp = root / "data" / f"02_Pipeline_Output_{exp}" / "Method_Regression" / "Stimulus_Locked" / "trials.csv"
    if not covp.exists():
        sys.exit(f"ERROR: missing covariate file {covp}")
    if not trp.exists():
        sys.exit(f"ERROR: missing trials file {trp}")
    cov = pd.read_excel(covp)
    missing = [c for c in RATINGS if c not in cov.columns]
    if missing:
        sys.exit(f"ERROR [{exp}]: covariate file lacks columns {missing}")
    cov["_id"] = cov[cov.columns[0]].map(digit_id)
    cov = cov.drop_duplicates("_id")
    analyzed = set(pd.read_csv(trp, usecols=["participant_id"])["participant_id"].map(digit_id).dropna())
    dropped = sorted(set(cov["_id"]) - analyzed, key=lambda s: int(s))
    keep = cov[cov["_id"].isin(analyzed)].copy()
    return keep, dropped


def rank_biserial_signed(x, mu):
    """Matched-pairs rank-biserial correlation for a one-sample Wilcoxon vs mu."""
    d = np.asarray(x, float) - mu
    d = d[d != 0]
    if d.size == 0:
        return np.nan
    r = stats.rankdata(np.abs(d))
    w_pos, w_neg = r[d > 0].sum(), r[d < 0].sum()
    return (w_pos - w_neg) / (w_pos + w_neg)


def boot_ci_mean(x, n_boot=N_BOOT, seed=BOOT_SEED):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    means = rng.choice(x, size=(n_boot, x.size), replace=True).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


def df_to_md(df):
    """Minimal GitHub-flavored markdown table (avoids the optional 'tabulate' dep)."""
    cols = list(df.columns)
    head = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


# Belief bands relative to the Neutral anchor (50), symmetric 25-wide steps with a
# dedicated Neutral==50 category (the slider default). Key -> (label, colour).
# Colours: ColorBrewer RdBu (colourblind-safe) with a grey neutral.
BANDS = [
    ("SD", "Strongly disbelieve (0-24)", "#ca0020"),
    ("D",  "Disbelieve (25-49)",         "#f4a582"),
    ("N",  "Neutral (50)",               "#bdbdbd"),
    ("B",  "Believe (51-75)",            "#92c5de"),
    ("SB", "Strongly believe (76-100)",  "#0571b0"),
]
BAND_COL = {k: c for k, _, c in BANDS}


def band_fracs(x):
    """Fraction of responses in each belief band (fractions sum to 1)."""
    x = np.asarray(x, float)
    return {"SD": np.mean(x < 25), "D": np.mean((x >= 25) & (x < 50)),
            "N": np.mean(x == 50), "B": np.mean((x > 50) & (x <= 75)),
            "SB": np.mean(x > 75)}


# --------------------------------------------------------------------------- #
# Load + compute
# --------------------------------------------------------------------------- #
ROOT = find_root(Path(__file__).resolve())
OUT = ROOT / "results" / "Behavior" / "Manipulation_Checks"
OUT.mkdir(parents=True, exist_ok=True)

data, drops = {}, {}
for exp in EXPS:
    data[exp], drops[exp] = load_exp(ROOT, exp)

desc_rows = []
for exp in EXPS:
    for c in RATINGS:
        x = pd.to_numeric(data[exp][c], errors="coerce").dropna().values.astype(float)
        W, p = stats.wilcoxon(x - MIDPOINT, alternative="two-sided", zero_method="wilcox")
        lo, hi = boot_ci_mean(x)
        desc_rows.append(dict(
            Experiment=exp, Rating=c, n=int(x.size),
            Mean=x.mean(), SD=x.std(ddof=1), Mean_CI_low=lo, Mean_CI_high=hi,
            Median=float(np.median(x)), Q1=float(np.percentile(x, 25)), Q3=float(np.percentile(x, 75)),
            Min=float(x.min()), Max=float(x.max()), Pct_above_mid=100 * np.mean(x > MIDPOINT),
            Wilcoxon_W=float(W), Wilcoxon_p=float(p), rank_biserial=rank_biserial_signed(x, MIDPOINT),
        ))
desc = pd.DataFrame(desc_rows)

mw_rows = []
for c in RATINGS:
    x1 = pd.to_numeric(data["E1"][c], errors="coerce").dropna().values.astype(float)
    x2 = pd.to_numeric(data["E2"][c], errors="coerce").dropna().values.astype(float)
    U, p = stats.mannwhitneyu(x1, x2, alternative="two-sided")
    mw_rows.append(dict(Rating=c, E1_median=float(np.median(x1)), E2_median=float(np.median(x2)),
                        MannWhitney_U=float(U), p=float(p),
                        rank_biserial=1 - 2 * U / (x1.size * x2.size)))
mw = pd.DataFrame(mw_rows)

# --------------------------------------------------------------------------- #
# Write tables
# --------------------------------------------------------------------------- #
desc.to_csv(OUT / "MANIPULATION_CHECK_Ratings.csv", index=False)

gloss = {
    "Rating_1": "Perceived influence of the proposer's face on own decision (subjective-impact item)",
    "Rating_2": "Belief the offers were made by real people (proposer authenticity)",
    "Rating_3": "Belief the standardized photos are based on real people (face authenticity)",
}


def fmt_desc(df):
    out = df.copy()
    out["M [95% CI]"] = [f"{m:.1f} [{lo:.1f}, {hi:.1f}]" for m, lo, hi in
                         zip(out.Mean, out.Mean_CI_low, out.Mean_CI_high)]
    out["Mdn [IQR]"] = [f"{md:.0f} [{q1:.0f}, {q3:.0f}]" for md, q1, q3 in zip(out.Median, out.Q1, out.Q3)]
    out["Range"] = [f"{lo:.0f}-{hi:.0f}" for lo, hi in zip(out.Min, out.Max)]
    out["% > 50"] = [f"{v:.0f}%" for v in out.Pct_above_mid]
    out["Wilcoxon vs 50"] = [f"W = {w:.0f}, p {('< .001' if p < .001 else '= %.3f' % p)} {stars(p)}"
                             for w, p in zip(out.Wilcoxon_W, out.Wilcoxon_p)]
    out["r_rb"] = [f"{v:+.2f}" for v in out.rank_biserial]
    out["SD"] = [f"{v:.1f}" for v in out.SD]
    return out[["Experiment", "Rating", "n", "M [95% CI]", "SD", "Mdn [IQR]",
                "Range", "% > 50", "Wilcoxon vs 50", "r_rb"]]

md = []
md.append("# Manipulation check -- post-task cover-story belief ratings (Rating_1/2/3)")
md.append(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}")
md.append("")
md.append("Scale: 0-100 VAS with printed anchors *Ueberhaupt nicht* (0 = not at all), "
          "**Neutral (50)**, and *Vollstaendig* (100 = completely); higher = stronger belief. "
          "The response slider was initialized at the neutral midpoint (50). Analysis sample = "
          f"behavioral analysis subjects (E1 n = {len(data['E1'])}, E2 n = {len(data['E2'])}); "
          f"E1 excludes covariate-file subject(s) {drops['E1']} absent from the analysis sample.")
md.append("")
md.append("Items:")
for c in RATINGS:
    md.append(f"- **{c}** -- {gloss[c]}")
md.append("")
md.append("Rating_2 / Rating_3 are cover-story **authenticity** checks (higher = cover story believed). "
          "Rating_1 is a **subjective-impact** item (perceived face influence); its \"desirable\" "
          "direction is theory-dependent, so it is described, not scored as pass/fail.")
md.append("")
md.append("## Descriptives and one-sample Wilcoxon signed-rank vs the labeled neutral point (50)")
md.append("")
md.append(df_to_md(fmt_desc(desc)))
md.append("")
md.append("- **M [95% CI]** = mean with bootstrap percentile CI (10,000 resamples, seed 42). "
          "**Mdn [IQR]** = median [Q1, Q3]. **% > 50** = percent of participants above the midpoint. "
          "**W** = Wilcoxon signed-rank statistic (two-sided, vs 50). "
          "**r_rb** = matched-pairs rank-biserial effect size (sign relative to 50). "
          "`*** p<.001, ** p<.01, * p<.05, ns not significant`.")
md.append("- The reference value is **50, the VAS's printed 'Neutral' anchor** (and the slider's "
          "start position), so the test asks whether retained participants leaned *above* "
          "(toward belief) or *below* (toward disbelief) the neutral point they began from.")
md.append("- The reference is deliberately **not 0**: 0 (complete disbelief) is the *exclusion* "
          "criterion, so every retained participant is > 0 by construction; testing against 0 "
          "would be circular (trivially significant for every item) and would mislabel "
          "below-neutral items (e.g. Rating_2) as \"believed\". 0 screens participants; 50 "
          "gauges belief direction -- complementary roles.")
md.append("")
md.append("## Floor (exclusion) and default-anchor (Neutral) checks")
md.append("")
md.append("Exclusion rule: participants who rated **0** on Rating_2 (offers real = *Ueberhaupt "
          "nicht*) were treated as disbelieving the cover story and were removed manually during "
          "screening, before the covariate table was compiled. The analysis sample therefore "
          "contains **no 0 responses by construction**. Per-item floor and neutral-anchor counts:")
md.append("")
floor = []
for exp in EXPS:
    for c in RATINGS:
        x = pd.to_numeric(data[exp][c], errors="coerce").dropna().values
        floor.append(dict(Experiment=exp, Rating=c, Min=int(x.min()),
                          **{"n == 0": int((x == 0).sum()), "n == 1": int((x == 1).sum()),
                             "n == 50 (default)": int((x == 50).sum())}))
md.append(df_to_md(pd.DataFrame(floor)))
md.append("")
md.append("- **Floor (0):** no participant scored 0 on any item (minimum = 1); a few sit at the "
          "floor value of 1 and are legitimately retained. The apparent density at/below 0 in a "
          "violin plot is a kernel-smoothing artifact, not real 0 responses, so the profile "
          "figures plot raw values with an explicit floor line at 0.")
md.append("- **Default anchor (50):** because the slider started at the *Neutral* midpoint, a "
          "response left exactly at 50 could be genuine neutrality or an untouched default. "
          "Rating_2 shows the most exact-50 responses (E1 n = 5, E2 n = 4), whereas **Rating_1 "
          "has none in either experiment** -- evidence that participants did move the slider "
          "rather than leave it, which makes the exact-50 responses on Rating_2/3 more likely "
          "genuine than inertial. Note the one-sample Wilcoxon signed-rank test drops "
          "ties with the reference (values exactly 50), so those participants do not contribute "
          "to the test for the affected items (effective n reduced accordingly).")
md.append("")
md.append("## Belief-band distribution (share of participants) -- primary descriptive")
md.append("")
md.append("Responses relative to the Neutral anchor (50). This distribution -- not the "
          "midpoint test -- is the substantive manipulation-check result; see the score-"
          "distribution figure (ManipulationCheck_Ratings_ScoreDist.pdf).")
md.append("")
band_rows = []
for exp in EXPS:
    for c in RATINGS:
        x = pd.to_numeric(data[exp][c], errors="coerce").dropna().values
        f = band_fracs(x)
        band_rows.append({
            "Experiment": exp, "Rating": c,
            "SD%": f"{100*f['SD']:.0f}", "D%": f"{100*f['D']:.0f}",
            "Neu(50)%": f"{100*f['N']:.0f}", "B%": f"{100*f['B']:.0f}",
            "SB%": f"{100*f['SB']:.0f}",
            "below Neu%": f"{100*(f['SD']+f['D']):.0f}",
            "above Neu%": f"{100*(f['B']+f['SB']):.0f}",
        })
md.append(df_to_md(pd.DataFrame(band_rows)))
md.append("")
md.append("- Bands: SD 0-24, D 25-49, Neutral = exactly 50, B 51-75, SB 76-100. "
          "**Rating_3** (photos real): the majority sit above Neutral in both experiments "
          "(believe side). **Rating_2** (offers real): the majority sit below Neutral "
          "(disbelieve side) -- the manipulation limitation. **Rating_1** straddles Neutral.")
md.append("")
md.append("## E1 vs E2 (Mann-Whitney U, two-sided)")
md.append("")
mw_fmt = mw.copy()
mw_fmt["E1 Mdn"] = mw_fmt.E1_median.map(lambda v: f"{v:.0f}")
mw_fmt["E2 Mdn"] = mw_fmt.E2_median.map(lambda v: f"{v:.0f}")
mw_fmt["U"] = mw_fmt.MannWhitney_U.map(lambda v: f"{v:.0f}")
mw_fmt["p"] = [("< .001" if p < .001 else f"{p:.3f}") + f" {stars(p)}" for p in mw_fmt.p]
mw_fmt["r_rb"] = mw_fmt.rank_biserial.map(lambda v: f"{v:+.2f}")
md.append(df_to_md(mw_fmt[["Rating", "E1 Mdn", "E2 Mdn", "U", "p", "r_rb"]]))
md.append("")
md.append("_Exploratory; n = 30/experiment; interpret with caution._")
(OUT / "MANIPULATION_CHECK_Ratings.md").write_text("\n".join(md), encoding="utf-8")

# --------------------------------------------------------------------------- #
# Figures: one per experiment, within-subject profile plot (each participant's
# three ratings connected), no violins (avoids the KDE floor artifact).
# --------------------------------------------------------------------------- #
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8, "axes.labelsize": 9, "axes.titlesize": 9,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.linewidth": 0.8, "pdf.fonttype": 42, "ps.fonttype": 42,
})
EXP_TITLE = {"E1": "E1 (sequential: face precedes offer)",
             "E2": "E2 (simultaneous: face + offer)"}
xs = np.arange(len(RATINGS))


def make_profile_figure(exp):
    df = data[exp]
    M = df[RATINGS].apply(pd.to_numeric, errors="coerce").dropna()  # complete cases for lines
    n = len(M)
    col = COLORS[exp]
    rng = np.random.default_rng(7)                     # one fixed x-offset per subject
    jit = rng.uniform(-0.10, 0.10, size=n)

    fig, ax = plt.subplots(figsize=(4.2, 3.7))

    # individual within-subject profiles (same offset across a subject's 3 points)
    for k, (_, row) in enumerate(M.iterrows()):
        xj = xs + jit[k]
        y = row[RATINGS].values.astype(float)
        ax.plot(xj, y, "-", color="0.6", lw=0.5, alpha=0.40, zorder=2)
        ax.scatter(xj, y, s=11, color=col, alpha=0.55, edgecolor="none", zorder=3)

    # group means + bootstrap 95% CI, connected
    means, los, his = [], [], []
    for c in RATINGS:
        x = pd.to_numeric(df[c], errors="coerce").dropna().values.astype(float)
        m = x.mean(); lo, hi = boot_ci_mean(x)
        means.append(m); los.append(lo); his.append(hi)
    means, los, his = map(np.array, (means, los, his))
    ax.plot(xs, means, "-", color=col, lw=2.2, zorder=5)
    ax.errorbar(xs, means, yerr=[means - los, his - means], fmt="o", ms=6,
                color=col, mec="black", mew=0.8, ecolor="black",
                elinewidth=1.3, capsize=3, zorder=6)

    # reference lines: printed "Neutral" anchor / slider default (50) and exclusion floor (0)
    ax.axhline(MIDPOINT, ls="--", lw=0.9, color="0.45", zorder=1)
    ax.text(xs[-1] + 0.36, MIDPOINT + 1.3, "50 = 'Neutral' (default start)", fontsize=6.3,
            color="0.45", ha="right", va="bottom")
    ax.axhline(0, ls=":", lw=0.9, color="#B22222", zorder=1)
    ax.text(xs[-1] + 0.36, 1.5, "Rating 2 = 0 → excluded (none; min = 1)",
            fontsize=6.3, color="#B22222", ha="right", va="bottom")

    # Wilcoxon-vs-midpoint significance per item
    for i, c in enumerate(RATINGS):
        p = desc[(desc.Experiment == exp) & (desc.Rating == c)].Wilcoxon_p.iloc[0]
        ax.text(i, 106, stars(p), ha="center", va="bottom", fontsize=8, color=col)

    ax.set_xticks(xs)
    ax.set_xticklabels([LABELS[c] for c in RATINGS])
    ax.set_xlim(-0.45, len(RATINGS) - 1 + 0.45)
    ax.set_ylim(-5, 114)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Belief rating (0–100 VAS)")
    ax.set_xlabel("Post-task cover-story rating item")
    ax.set_title(f"{EXP_TITLE[exp]}   ·   n = {n}", fontsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / f"ManipulationCheck_Ratings_{exp}.pdf")
    fig.savefig(OUT / f"ManipulationCheck_Ratings_{exp}.png", dpi=400)
    plt.close(fig)

    caption = (
        f"Post-task cover-story belief ratings for {EXP_TITLE[exp]} (0-100 VAS; higher = stronger "
        f"belief; n = {n}). Thin grey lines connect the three ratings of the same participant "
        "(within-subject profile); coloured dots are individual ratings; the thick line and black-"
        "edged markers are the group means with a bootstrap 95% CI (10,000 resamples). A small "
        "constant horizontal offset per participant is added to separate overlapping profiles. The "
        "dashed line marks the VAS's printed 'Neutral' anchor (50), which was also the slider's "
        "start position; the dotted red line marks 0, the Rating_2 exclusion threshold (0-responders "
        "removed during screening; minimum observed = 1). Asterisks: two-sided one-sample Wilcoxon "
        "signed-rank test vs the neutral point 50 (*** p<.001, ** p<.01, * p<.05, ns). "
        "Rating_1 = perceived influence of the proposer's face on one's decision; Rating_2 = belief "
        "the offers were made by real people; Rating_3 = belief the standardized photos are based on "
        "real people. Exploratory manipulation check."
    )
    (OUT / f"ManipulationCheck_Ratings_{exp}.caption.txt").write_text(caption, encoding="utf-8")
    return n


for exp in EXPS:
    make_profile_figure(exp)


# --------------------------------------------------------------------------- #
# Primary manipulation-check figure: raw score distributions (histograms) per
# item, E1/E2 overlaid, with the Neutral anchor (50) and medians marked.
# Neutral presentation: continuous scores, no belief categories, no valence colours.
# --------------------------------------------------------------------------- #
COMPACT = {"Rating_1": "Face influence", "Rating_2": "Offers real", "Rating_3": "Photos real"}


def make_score_distribution_figure():
    bins = np.arange(0, 101, 10)
    fig, axes = plt.subplots(len(EXPS), len(RATINGS), figsize=(7.4, 4.5),
                             sharex=True, sharey=True)
    for r, exp in enumerate(EXPS):
        for j, c in enumerate(RATINGS):
            ax = axes[r, j]
            x = pd.to_numeric(data[exp][c], errors="coerce").dropna().values.astype(float)
            ax.hist(x, bins=bins, color=COLORS[exp], alpha=0.85,
                    edgecolor="white", linewidth=0.4, zorder=2)
            ax.plot(np.median(x), 0.93, marker="v", ms=5.5, color="0.2",
                    transform=ax.get_xaxis_transform(), clip_on=False, zorder=5)
            ax.axvline(50, ls="--", lw=0.9, color="0.4", zorder=1)
            if r == 0:
                ax.set_title(COMPACT[c], fontsize=9)
            if j == 0:
                ax.set_ylabel(exp, rotation=0, ha="right", va="center",
                              fontweight="bold", fontsize=11, labelpad=18)
            if r == len(EXPS) - 1:
                ax.set_xlabel("Belief rating (0–100 VAS)", fontsize=7.8)
            ax.set_xlim(0, 100)
            ax.set_xticks([0, 50, 100])
            ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].text(48, 0.66, "Neutral (50)", rotation=90,
                    transform=axes[0, 0].get_xaxis_transform(), ha="right", va="center",
                    fontsize=6.2, color="0.4",
                    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=0.4))
    fig.text(0.015, 0.55, "Number of participants", rotation=90, va="center", fontsize=9)
    axes[0, -1].annotate("median", xy=(np.median(pd.to_numeric(data["E1"][RATINGS[-1]],
                         errors="coerce").dropna()), 0.93), xycoords=("data", "axes fraction"),
                         xytext=(6, 0), textcoords="offset points", ha="left", va="center",
                         fontsize=6.5, color="0.2")
    fig.subplots_adjust(left=0.14, right=0.98, top=0.9, bottom=0.11, hspace=0.28, wspace=0.14)
    fig.savefig(OUT / "ManipulationCheck_Ratings_ScoreDist.pdf")
    fig.savefig(OUT / "ManipulationCheck_Ratings_ScoreDist.png", dpi=400)
    plt.close(fig)

    caption = (
        "Score distributions of the three post-task cover-story belief ratings (0-100 VAS; higher = "
        "stronger belief), shown separately for E1 (top, blue) and E2 (bottom, orange); n = 30 each, "
        "10-point bins. The dashed line marks the VAS's printed 'Neutral' anchor (50); the downward "
        "triangle marks each panel's median. Rating_1 = perceived influence of the proposer's face on "
        "one's decision; Rating_2 = belief the offers were made by real people (cover story: offers "
        "pre-generated by a real partner before the session); Rating_3 = belief the standardized "
        "photos are based on real people. Descriptive manipulation check (no inferential test); "
        "responses of exactly 50 -- the slider default -- fall in the 50-60 bin (counts tabulated in "
        "MANIPULATION_CHECK_Ratings.md)."
    )
    (OUT / "ManipulationCheck_Ratings_ScoreDist.caption.txt").write_text(caption, encoding="utf-8")


make_score_distribution_figure()

# Remove superseded figures from earlier versions (combined violin; diverging bar).
for stale in ["ManipulationCheck_Ratings_E1E2.pdf", "ManipulationCheck_Ratings_E1E2.png",
              "ManipulationCheck_Ratings_E1E2.caption.txt",
              "ManipulationCheck_Ratings_Diverging.pdf", "ManipulationCheck_Ratings_Diverging.png",
              "ManipulationCheck_Ratings_Diverging.caption.txt"]:
    fp = OUT / stale
    if fp.exists():
        fp.unlink()

# --------------------------------------------------------------------------- #
# Console summary
# --------------------------------------------------------------------------- #
print("Project root :", ROOT)
print("Output dir   :", OUT)
print("E1 dropped   :", drops["E1"], "| E2 dropped:", drops["E2"])
print()
print(fmt_desc(desc).to_string(index=False))
print()
print("E1 vs E2 (Mann-Whitney U):")
print(mw_fmt[["Rating", "E1 Mdn", "E2 Mdn", "U", "p", "r_rb"]].to_string(index=False))
print()
print("Floor check (n == 0 should be 0 for Rating_2 per the exclusion rule):")
print(pd.DataFrame(floor).to_string(index=False))
print()
print("Wrote:")
for f in ["MANIPULATION_CHECK_Ratings.csv", "MANIPULATION_CHECK_Ratings.md",
          "ManipulationCheck_Ratings_ScoreDist.pdf", "ManipulationCheck_Ratings_ScoreDist.png",
          "ManipulationCheck_Ratings_ScoreDist.caption.txt",
          "ManipulationCheck_Ratings_E1.pdf", "ManipulationCheck_Ratings_E1.png",
          "ManipulationCheck_Ratings_E1.caption.txt",
          "ManipulationCheck_Ratings_E2.pdf", "ManipulationCheck_Ratings_E2.png",
          "ManipulationCheck_Ratings_E2.caption.txt"]:
    print("  ", (OUT / f).relative_to(ROOT))
