# Experiment changelog

## v1 (initial)
- 5 constraints, 3 padding conditions, before/after position arms
- CSV schema v1 (see experiments/CLAUDE.md invariants)
- Added `EXPERIMENT_VERSION` constant to the toolkit and appended
  `experiment_version` as the final CSV column so every row is
  self-describing. No prior runs exist yet, so this is not a breaking
  change to comparability — future version bumps must append, never
  reorder/rename, existing columns.
