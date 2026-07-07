# Constraint Decay ("Attentional Cliff") Research Project

Empirical study of how instruction-following in small local LLMs degrades as
padding tokens separate a system constraint from the user query. Multi-model
comparison via Ollama, targeting a short research paper / technical blog post.

## Project layout

- `experiments/` — experiment runner, constraint validators, padding generators
- `analysis/` — logistic-fit + T50 estimation, plotting scripts
- `paper/` — manuscript drafts, figures, references
- `data/raw/` — raw experiment CSVs (IMMUTABLE — see rules below)
- `data/processed/` — cleaned/aggregated datasets derived from raw
- `results/figures/` — generated plots (PNG + SVG, regenerable)
- `results/fits/` — fitted model parameters (JSON)

Architecture details: @docs/claude/architecture.md
Experiment design rationale: @docs/methodology.md
Research agenda (all studies): @docs/research_agenda.md
Known pitfalls — check before any task: @docs/watchouts.md

## Environment

- Ubuntu Linux, 32GB RAM, CPU-only inference
- Python 3.11+, venv at `.venv/` — activate before running anything
- Ollama serving at `http://localhost:11434` (check with `ollama list`)

## Commands

```bash
source .venv/bin/activate                          # always first
python experiments/constraint_decay_toolkit.py --help
python experiments/constraint_decay_toolkit.py \
  --models gemma3:12b --trials 10 --out data/raw/run_$(date +%Y%m%d_%H%M).csv
python analysis/fit_cliffs.py data/raw/<run>.csv   # T50 fits -> results/fits/
python analysis/plot_curves.py results/fits/       # figures -> results/figures/
pytest experiments/tests/ -x -q                    # validator unit tests
ruff check . && ruff format --check .              # lint before committing
```

## Critical rules

- IMPORTANT: NEVER modify, overwrite, or delete anything in `data/raw/`.
  Raw CSVs are the primary scientific record. Derived data goes to
  `data/processed/` with a script that regenerates it.
- IMPORTANT: NEVER change validator logic or constraint instruction strings
  without bumping `EXPERIMENT_VERSION` in the toolkit and noting it in
  `docs/changelog.md`. Results from different versions are not comparable.
- All experiment runs MUST use temperature 0.0 and an explicit seed.
  Non-deterministic runs are invalid.
- Do not lower `num_ctx` below the longest prompt in the grid. Silent
  front-truncation drops the constraint and fabricates a fake cliff.
- Long experiment runs take hours on CPU. Never kill or relaunch a running
  experiment without asking first.
- Make minimal changes — do not refactor code unrelated to the task.
- One logical change per commit. Never commit `data/raw/` files larger
  than 50MB or anything in `.venv/`.

## Code style

- Python: ruff defaults, type hints on public functions, dataclasses over dicts
  for structured records.
- Validators must be pure, deterministic functions `(str) -> bool` with unit
  tests covering pass, fail, and edge cases (empty string, whitespace, fences).
- No new dependencies without asking. Current allowed: requests, pandas,
  numpy, scipy, matplotlib, statsmodels, pytest, ruff.

## Workflow

- Run `pytest experiments/tests/` after any change to validators or padding
  generators, before anything else.
- When unsure between two statistical or design approaches, present both
  with trade-offs and let me choose. Do not make methodology decisions
  unilaterally — they affect the paper's claims.
