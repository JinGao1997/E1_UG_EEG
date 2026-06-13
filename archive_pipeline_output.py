#!/usr/bin/env python3
"""
Archive the REGENERABLE pipeline outputs before re-running the FRN/P3 pipeline,
so the old (pre-refactor) outputs are preserved for later comparison and the
re-run starts from a clean slate.

WHAT IT MOVES (whitelist) — for each experiment E1, E2:
    data/02_Pipeline_Output_<EXP>/Method_Regression
    data/02_Pipeline_Output_<EXP>/Method_Standard
    data/02_Pipeline_Output_<EXP>/Baseline_Raw
  -> data/_archive_<timestamp>_pre_FRN_P3/02_Pipeline_Output_<EXP>/<same names>

SAFETY COPY (extra redundancy for the irreplaceable manual inputs):
  Before archiving, copies every *.xlsx in each Covariates folder into
    data/02_Pipeline_Output_<EXP>/Covariates/_manual_backup_<timestamp>/
  The LIVE Covariates files are left exactly in place (same names), so the
  re-run keeps using them; the copy is pure belt-and-suspenders redundancy.

WHAT IT NEVER MOVES:
    data/02_Pipeline_Output_<EXP>/Covariates   (manual, irreplaceable SVO/PID5 xlsx)
    data/00_Raw_Input                          (raw data, read-only)
    anything else

The archive lives under data/ (which is git-ignored), so it creates no git noise.
Moving (not copying) means the original locations are emptied -> a clean re-run.

USAGE (from project root):
    python archive_pipeline_output.py --dry-run     # preview only, moves nothing
    python archive_pipeline_output.py               # actually move

Safe to re-run: once sources are moved, a second run finds nothing and does nothing.
"""

import glob
import os
import shutil
import sys
from datetime import datetime

EXPERIMENTS = ["E1", "E2"]
# Whitelist of regenerable subdirectories to archive. Covariates is deliberately
# absent so it is never moved.
REGENERABLE_SUBDIRS = ["Method_Regression", "Method_Standard", "Baseline_Raw"]
PROTECTED_SUBDIR = "Covariates"


def backup_manual_covariates(data_dir, root, stamp, dry_run):
    """Copy every *.xlsx in each Covariates folder into an in-place
    _manual_backup_<stamp>/ subfolder. Originals are left untouched."""
    print("Step 1/2: redundant copy of manual Covariates inputs (*.xlsx)\n")
    copied = 0
    for exp in EXPERIMENTS:
        cov = os.path.join(data_dir, f"02_Pipeline_Output_{exp}", PROTECTED_SUBDIR)
        if not os.path.isdir(cov):
            print(f"[skip] {os.path.relpath(cov, root)} (not found)")
            continue
        xlsx = sorted(glob.glob(os.path.join(cov, "*.xlsx")))
        if not xlsx:
            print(f"[warn] no *.xlsx in {os.path.relpath(cov, root)}")
            continue
        bdir = os.path.join(cov, f"_manual_backup_{stamp}")
        for src in xlsx:
            dest = os.path.join(bdir, os.path.basename(src))
            print(f"[copy] {os.path.relpath(src, root)}  ->  {os.path.relpath(dest, root)}")
            if not dry_run:
                os.makedirs(bdir, exist_ok=True)
                shutil.copy2(src, dest)
            copied += 1
    print(f"  -> {copied} manual file(s) {'would be copied' if dry_run else 'copied'}.\n")


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root, "data")

    if not os.path.isdir(data_dir):
        sys.exit(f"[ABORT] data/ not found under {root}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_base = os.path.join(data_dir, f"_archive_{stamp}_pre_FRN_P3")

    # Redundant safety copy of irreplaceable manual inputs FIRST.
    backup_manual_covariates(data_dir, root, stamp, dry_run)

    print(f"Step 2/2: archive regenerable pipeline outputs (move)")
    print(f"{'DRY-RUN: ' if dry_run else ''}Archive destination: {archive_base}\n")

    moved, skipped = 0, 0
    for exp in EXPERIMENTS:
        src_exp = os.path.join(data_dir, f"02_Pipeline_Output_{exp}")
        if not os.path.isdir(src_exp):
            print(f"[skip] {src_exp} (not found)")
            continue

        for sub in REGENERABLE_SUBDIRS:
            src = os.path.join(src_exp, sub)
            if not os.path.isdir(src):
                print(f"[skip] {os.path.relpath(src, root)} (not present)")
                skipped += 1
                continue
            dest = os.path.join(archive_base, f"02_Pipeline_Output_{exp}", sub)
            if os.path.exists(dest):
                print(f"[skip] dest already exists, not overwriting: {dest}")
                skipped += 1
                continue
            print(f"[move] {os.path.relpath(src, root)}  ->  {os.path.relpath(dest, root)}")
            if not dry_run:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
            moved += 1

        # Reassure: confirm the manual Covariates folder is still in place.
        cov = os.path.join(src_exp, PROTECTED_SUBDIR)
        status = "present (untouched)" if os.path.isdir(cov) else "NOT FOUND"
        print(f"       Covariates for {exp}: {status}  [{os.path.relpath(cov, root)}]")

    verb = "would be moved" if dry_run else "moved"
    print(f"\nDone. {moved} folder(s) {verb}, {skipped} skipped.")
    if dry_run:
        print("This was a DRY RUN — nothing changed. Re-run without --dry-run to apply.")
    elif moved:
        print("Old pipeline outputs archived. You can now re-run the pipeline cleanly.")


if __name__ == "__main__":
    main()
