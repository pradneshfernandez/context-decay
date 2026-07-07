# Analysis — cliff estimation and visualization

Loads when working on files in `analysis/`. Root rules still apply.

## Key files

- `fit_cliffs.py` — logistic regression per (model x constraint x condition),
  outputs T50 estimates + bootstrap CIs to `results/fits/*.json`
- `plot_curves.py` — degradation curves and summary figures to
  `results/figures/`

## Statistical conventions

- Primary metric: T50 = prompt token count at which fitted success
  probability crosses 0.5 (logistic fit on `prompt_tokens` vs `success`).
- Fit with `statsmodels` Logit; report T50 with 95% bootstrap CI
  (>= 1000 resamples, resample at the trial level, seed=42).
- Exclude `success == -1` (error rows) from fits; report exclusion counts.
- If a cell never drops below 50% success, report T50 as right-censored
  ("> max tokens tested"), never extrapolate beyond observed range.
- Group by ACTUAL `prompt_tokens`, not `padding_level` — tokenizers differ
  across models.
- Never aggregate across padding conditions or constraint positions; they
  are separate experimental arms.

## Plotting conventions

- matplotlib only, no seaborn. Save both PNG (150 dpi) and SVG.
- x-axis: prompt tokens (linear). y-axis: success rate 0-1.
- Show raw per-level success rates as scatter + fitted logistic curve as
  line + shaded 95% CI band. Mark T50 with a vertical dashed line.
- One color per model, consistent across ALL figures (define palette once
  in `analysis/style.py` and import it).
- Every figure must be reproducible by a single script invocation from
  files in `results/fits/` or `data/processed/` — no hand-edited figures.

## Rules

- Analysis scripts READ from `data/` and `results/fits/`, WRITE only to
  `results/`. They never touch `data/raw/`.
- Print n (trials per cell) alongside every reported rate. Flag any cell
  with n < 5 as underpowered rather than silently including it.
