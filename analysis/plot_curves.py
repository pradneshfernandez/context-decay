"""
Degradation-curve figures from results/fits/*.json (produced by
fit_cliffs.py). Every figure must be reproducible by this single script
invocation from results/fits/ — no hand-edited figures. See
analysis/CLAUDE.md.

Usage:
    python analysis/plot_curves.py results/fits/
    python analysis/plot_curves.py results/fits/run_20260707_fits.json
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import CI_BAND_ALPHA, T50_LINE_STYLE, color_for_model  # noqa: E402

SKIP_STATUSES = {"invalid_truncation_suspected"}


def load_cells(paths: list[Path]) -> list[dict]:
    cells = []
    for p in paths:
        data = json.loads(Path(p).read_text())
        cells.extend(data["cells"])
    return cells


def logistic(x: np.ndarray, intercept: float, slope: float) -> np.ndarray:
    return 1 / (1 + np.exp(-(intercept + slope * x)))


def cell_label(cell: dict) -> str:
    return (f"{cell['model']} | {cell['constraint']} | "
            f"{cell['padding_condition']} | {cell['constraint_position']}")


def plot_cell(cell: dict, out_dir: Path) -> Path | None:
    if cell["status"] in SKIP_STATUSES:
        print(f"Skipping {cell_label(cell)}: {cell['status']}")
        return None

    raw = cell["raw_points"]
    if not raw:
        print(f"Skipping {cell_label(cell)}: no data")
        return None

    xs_raw = [r["prompt_tokens"] for r in raw]
    ys_raw = [r["success_rate"] for r in raw]
    ns = [r["n"] for r in raw]
    underpowered = set(cell.get("underpowered_levels", []))
    levels = [r["padding_level"] for r in raw]

    fig, ax = plt.subplots(figsize=(6, 4))
    color = color_for_model(cell["model"])

    sizes = [max(20, n * 8) for n in ns]
    edge_colors = ["red" if lvl in underpowered else "white" for lvl in levels]
    ax.scatter(xs_raw, ys_raw, s=sizes, color=color, zorder=3,
               label="raw per-level success rate", edgecolor=edge_colors,
               linewidth=1.2)

    if "intercept" in cell:
        x_min, x_max = min(xs_raw), max(xs_raw)
        pad = (x_max - x_min) * 0.05 if x_max > x_min else 10
        x_line = np.linspace(x_min - pad, x_max + pad, 200)
        y_line = logistic(x_line, cell["intercept"], cell["slope"])
        ax.plot(x_line, y_line, color=color, zorder=2, label="logistic fit")

        params = cell.get("bootstrap_params") or []
        if params:
            curves = np.array([logistic(x_line, i, s) for i, s in params])
            lo = np.percentile(curves, 2.5, axis=0)
            hi = np.percentile(curves, 97.5, axis=0)
            ax.fill_between(x_line, lo, hi, color=color, alpha=CI_BAND_ALPHA,
                             zorder=1, label="95% CI (bootstrap)")

        if cell["status"] == "ok" and cell.get("t50") is not None:
            ax.axvline(cell["t50"], **T50_LINE_STYLE)
            ax.text(cell["t50"], 1.03, f"T50={cell['t50']:.0f}",
                    ha="center", va="bottom", fontsize=8)
        elif cell["status"] in ("right_censored", "left_censored"):
            ax.text(0.02, 0.02, cell.get("t50_display", cell["status"]),
                    transform=ax.transAxes, fontsize=8, color="#555555")

    ax.set_xlabel("Prompt tokens (actual, prompt_eval_count)")
    ax.set_ylabel("Success rate")
    ax.set_ylim(-0.05, 1.15)
    ax.set_title(cell_label(cell), fontsize=10)
    ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout()

    stem = "_".join([
        cell["model"].replace(":", "-"), cell["constraint"],
        cell["padding_condition"], cell["constraint_position"],
    ])
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"{stem}.png"
    svg_path = out_dir / f"{stem}.svg"
    fig.savefig(png_path, dpi=150)
    fig.savefig(svg_path)
    plt.close(fig)
    return png_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fits", help="a results/fits/*.json file or a directory of them")
    ap.add_argument("--out", default="results/figures")
    args = ap.parse_args()

    fits_path = Path(args.fits)
    paths = sorted(fits_path.glob("*.json")) if fits_path.is_dir() else [fits_path]
    if not paths:
        print(f"No fit JSON files found at {args.fits}")
        sys.exit(1)

    cells = load_cells(paths)
    out_dir = Path(args.out)
    written = sum(1 for cell in cells if plot_cell(cell, out_dir))
    print(f"Wrote {written} figure(s) to {out_dir}")


if __name__ == "__main__":
    main()
