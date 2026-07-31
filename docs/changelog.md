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
- 2026-07-31: Fixed three `analysis/plot_curves.py` figure bugs found while
  reviewing the distractor-grid figures: (1) `results/fits/*.json` glob
  crashed on non-fit files (e.g. `determinism_audit.json`) — now skipped
  with a message instead of raising `KeyError`; (2) the right-censored
  status annotation overlapped the legend in the bottom-left corner —
  moved to bottom-right; (3) figure text (titles, legend, annotations)
  was silently corrupted by this machine's `~/.config/matplotlib/matplotlibrc`
  (`text.usetex: True` turns `_`, `%`, `<`, `>` into LaTeX control
  characters — e.g. `prefix_persona` rendered with `persona` as a
  subscript, `n<5` rendered as `n¡5`). Pinned `text.usetex = False` in
  `analysis/style.py` so figures render identically regardless of the
  host machine's ambient LaTeX config, rather than escaping special
  characters per-label. Also added a legend entry for the
  underpowered/timeout-excluded marker (previously an unexplained red
  scatter-point outline). All affected figures regenerated.
