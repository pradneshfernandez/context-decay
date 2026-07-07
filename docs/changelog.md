# Experiment changelog

## v1 (initial)
- 5 constraints, 3 padding conditions, before/after position arms
- CSV schema v1 (see experiments/CLAUDE.md invariants)
- Added `EXPERIMENT_VERSION` constant to the toolkit and appended
  `experiment_version` as the final CSV column so every row is
  self-describing. No prior runs exist yet, so this is not a breaking
  change to comparability — future version bumps must append, never
  reorder/rename, existing columns.

## Tooling (no version bump — CLI-only, no validator/instruction/schema change)
- 2026-07-07: Added `--num-ctx` (raise the Ollama context window for high
  padding levels) and `--constraints NAME [NAME ...]` (run a subset of the
  registry, for exploratory probes) flags to
  `experiments/constraint_decay_toolkit.py`.
- 2026-07-07: Added `experiments/determinism_audit.py`, `analysis/fit_cliffs.py`,
  `analysis/plot_curves.py`, `analysis/style.py`.
