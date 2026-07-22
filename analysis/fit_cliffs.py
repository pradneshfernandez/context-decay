"""
Logistic T50 fits for constraint-decay experiment runs.

For each (model x constraint x padding_condition x constraint_position)
cell, fits success ~ prompt_tokens via logistic regression and extracts
T50 (the 50%-success crossing point) with a bootstrap CI. Never pools
across padding conditions or constraint positions — see analysis/CLAUDE.md
and docs/watchouts.md.

Reads from data/raw/ (or any CSV with the experiment schema). Writes only
to results/fits/.

Usage:
    python analysis/fit_cliffs.py data/raw/run_20260707_1200.csv
    python analysis/fit_cliffs.py data/raw/*.csv --out results/fits/main.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

MIN_TRIALS_PER_LEVEL = 5
N_BOOTSTRAP = 1000
BOOTSTRAP_SEED = 42

GROUP_COLS = ["model", "constraint", "padding_condition", "constraint_position"]
REQUIRED_COLS = {
    "model", "constraint", "padding_condition", "constraint_position",
    "padding_level", "prompt_tokens", "success",
}


def load_runs(paths: list[Path]) -> pd.DataFrame:
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True)


def check_truncation(df: pd.DataFrame) -> bool:
    """True if mean prompt_tokens fails to strictly increase with
    padding_level — the signature of silent front-truncation (the #1
    validity artifact per docs/watchouts.md)."""
    by_level = df.groupby("padding_level")["prompt_tokens"].mean().sort_index()
    if len(by_level) < 2:
        return False
    return bool((by_level.diff().dropna() <= 0).any())


def fit_logistic(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    X = sm.add_constant(x)
    result = sm.Logit(y, X).fit(disp=0)
    intercept, slope = result.params
    return float(intercept), float(slope)


def compute_t50(intercept: float, slope: float) -> float | None:
    if slope == 0:
        return None
    return -intercept / slope


def bootstrap_t50(x_all: np.ndarray, y_all: np.ndarray,
                   n_boot: int = N_BOOTSTRAP, seed: int = BOOTSTRAP_SEED):
    rng = np.random.default_rng(seed)
    n = len(x_all)
    t50s, params = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        xs, ys = x_all[idx], y_all[idx]
        if len(np.unique(ys)) < 2:
            continue
        try:
            intercept, slope = fit_logistic(xs, ys)
        except Exception:
            continue
        t50 = compute_t50(intercept, slope)
        if t50 is None:
            continue
        t50s.append(t50)
        params.append((intercept, slope))
    return t50s, params


def build_raw_points(df: pd.DataFrame, metric_col: str = "success") -> list[dict]:
    points = []
    for level, sub in df.groupby("padding_level"):
        points.append({
            "padding_level": int(level),
            "prompt_tokens": float(sub["prompt_tokens"].mean()),
            "n": int(len(sub)),
            "success_rate": float(sub[metric_col].mean()),
        })
    points.sort(key=lambda r: r["padding_level"])
    return points


def fit_cell(group_df: pd.DataFrame, key: tuple, metric_col: str = "success") -> dict:
    n_total = len(group_df)
    # `success == -1` (runner error rows) are always excluded, even when
    # fitting a different metric column (e.g. answer_correct uses the same
    # -1 exclusion convention and is undefined on error rows).
    n_excluded = int((group_df["success"] == -1).sum())
    df = group_df[group_df["success"] != -1].copy()

    level_counts = df.groupby("padding_level").size()
    underpowered_levels = [int(lvl) for lvl in
                            level_counts[level_counts < MIN_TRIALS_PER_LEVEL].index]

    truncated = check_truncation(df)

    result = {
        "model": key[0],
        "constraint": key[1],
        "padding_condition": key[2],
        "constraint_position": key[3],
        "metric": metric_col,
        "n_total_rows": n_total,
        "n_excluded_errors": n_excluded,
        "underpowered_levels": underpowered_levels,
        "truncation_suspected": truncated,
        "raw_points": build_raw_points(df, metric_col),
    }

    if truncated:
        result["status"] = "invalid_truncation_suspected"
        result["t50"] = None
        return result

    if df.empty or df[metric_col].nunique() < 2:
        result["status"] = "no_variation"
        result["t50"] = None
        return result

    x = df["prompt_tokens"].to_numpy(dtype=float)
    y = df[metric_col].to_numpy(dtype=float)

    try:
        intercept, slope = fit_logistic(x, y)
    except Exception as e:
        result["status"] = f"fit_error: {e}"
        result["t50"] = None
        return result

    result["intercept"] = intercept
    result["slope"] = slope

    t50 = compute_t50(intercept, slope)
    min_tok, max_tok = float(x.min()), float(x.max())

    t50s, params = bootstrap_t50(x, y)
    result["bootstrap_n"] = len(t50s)
    result["bootstrap_params"] = params

    if slope >= 0 or t50 is None or t50 > max_tok:
        # slope >= 0 means success is flat or rising with tokens (no decay
        # observed); t50 > max_tok means the fitted crossing lies past the
        # tested range. Either way: right-censor, never extrapolate.
        result["status"] = "right_censored"
        result["t50"] = None
        result["t50_display"] = f"> {max_tok:.0f} tokens tested"
    elif t50 < min_tok:
        result["status"] = "left_censored"
        result["t50"] = None
        result["t50_display"] = f"< {min_tok:.0f} tokens tested"
    else:
        result["status"] = "ok"
        result["t50"] = t50
        result["t50_display"] = f"{t50:.0f}"
        if t50s:
            lo, hi = np.percentile(t50s, [2.5, 97.5])
            result["t50_ci95"] = [float(lo), float(hi)]

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+", help="raw experiment CSV(s)")
    ap.add_argument("--out", default=None,
                     help="output JSON path (default: "
                          "results/fits/<first-csv-stem>_fits.json, or "
                          "..._<metric>_fits.json for a non-default --metric)")
    ap.add_argument("--metric", default="success",
                     help="binary column to fit T50 against (default: "
                          "success). E.g. answer_correct, from "
                          "analysis/answer_correctness.py, to fit a "
                          "factual-accuracy cliff instead of a "
                          "constraint-compliance cliff.")
    args = ap.parse_args()

    paths = [Path(p) for p in args.csvs]
    df = load_runs(paths)

    missing = (REQUIRED_COLS | {args.metric}) - set(df.columns)
    if missing:
        print(f"ERROR: input CSV missing required columns: {sorted(missing)}")
        sys.exit(1)

    cells = []
    for key, group in df.groupby(GROUP_COLS):
        cell = fit_cell(group, key, args.metric)
        cells.append(cell)
        flags = []
        if cell["underpowered_levels"]:
            flags.append(f"UNDERPOWERED levels={cell['underpowered_levels']}")
        if cell["truncation_suspected"]:
            flags.append("TRUNCATION-SUSPECTED")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"{key} -> {cell['status']} "
              f"T50={cell.get('t50_display', 'n/a')}{flag_str}")

    default_name = (f"{paths[0].stem}_fits.json" if args.metric == "success"
                     else f"{paths[0].stem}_{args.metric}_fits.json")
    out_path = Path(args.out) if args.out else Path("results/fits") / default_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(
        {"cells": cells, "source_files": [str(p) for p in paths]}, indent=2))
    print(f"\nWrote {len(cells)} cell fit(s) to {out_path}")

    truncated = [c for c in cells if c["truncation_suspected"]]
    if truncated:
        print(f"\nWARNING: {len(truncated)} cell(s) show suspected context "
              f"truncation (prompt_tokens does not grow with padding_level). "
              f"These are NOT analyzed. Per docs/watchouts.md: raise num_ctx "
              f"and rerun before trusting any result from this file.")


if __name__ == "__main__":
    main()
