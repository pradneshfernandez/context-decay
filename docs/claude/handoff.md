# Handoff notes

Point-in-time status for resuming work in a fresh session. This is a
snapshot, not a durable doc — update or delete stale sections as work
progresses; don't let it silently rot into a false record. Last updated
2026-07-08.

## Environment (already set up on this machine)
- Ollama installed via the official installer (systemd service, running as
  its own user — required `sudo`, already done).
- `.venv/` created at repo root with `requests pandas numpy scipy
  matplotlib statsmodels pytest ruff` installed.
- Pulled models: `llama3.2:3b` only, so far.

## Phase 0 — done
- `EXPERIMENT_VERSION` constant + `experiment_version` CSV column.
- `experiments/tests/` — 54 tests, all passing.
- `experiments/determinism_audit.py` — written and **run**: PASS
  (byte-identical output across 5 repeats x 3 `num_thread` settings for
  `llama3.2:3b`). Report at `results/fits/determinism_audit.json`.

## Phase 1 — in progress
- `analysis/fit_cliffs.py`, `analysis/plot_curves.py`, `analysis/style.py`
  written and smoke-tested against synthetic data. Caught and fixed a real
  bug during testing: the right-censoring check had the slope sign
  backwards (`slope <= 0` should be `slope >= 0` — a real decaying cliff
  has *negative* slope, that's the expected case, not the censored one).
- Added `--num-ctx` and `--constraints` CLI flags to the runner (see
  `docs/changelog.md` "Tooling" section) — needed once padding levels got
  large enough to approach the default 4096-token context window.
- **Pilot run** (`data/raw/pilot_20260707_203938.csv`): `llama3.2:3b`, all
  5 constraints, levels 0/4/16/32 (~50-1900 tokens), 3 trials each. Result:
  100% success everywhere — no decay in this range. Confirmed the pipeline
  works end-to-end (clean linear token growth, correct CSV schema, fits
  correctly flag `no_variation` + `UNDERPOWERED`).
- **Extended probes** under `prose` (neutral filler) padding, levels
  32/64/96/128/160 (~1900-9300 tokens), `--num-ctx 12000`, 2 trials each,
  one constraint at a time (to keep CPU time bounded):
  - `uppercase` (`data/raw/probe_uppercase_20260707_230839.csv`): 10/10
    pass. Zero decay up to ~9300 tokens. Notably, the model's *factual*
    accuracy degrades at higher levels (wrong/hallucinated answers) but the
    *formatting* constraint (all-caps) never breaks.
  - `json_schema` (`data/raw/probe_json_schema_20260707_235258.csv`): 9/10
    pass, 1 clean timeout at the very top (recorded correctly as
    `success=-1`, did not crash the run). JSON well-formedness never broke;
    only answer content varied.

## Open decision (unresolved when this session ended)
Two constraint types show **no measurable decay** up to ~9300 tokens under
neutral `prose` padding. Before spending more CPU-hours probing, need to
decide direction. Three options were on the table, not yet chosen:

1. **Switch to the `distractor` padding condition** — `prose` is neutral
   filler that never competes with the constraint; `distractor` embeds
   instruction-shaped sentences designed to actively conflict with it
   (e.g. fake style-guide notes). More likely to actually produce a cliff,
   and it's a separate experimental arm we need data for regardless per
   `docs/methodology.md`.
2. **Finish probing the remaining 3 constraints under `prose` first**
   (`negative_the`, `prefix_persona`, `end_token`) before changing the
   padding variable, to fully characterize this condition.
3. **Pause probing and reframe** — the finding that constraint-following
   (vs. answer accuracy) may simply not degrade under neutral padding at
   this model scale could itself be a paper angle worth discussing before
   chasing a cliff that may not exist for this model/condition combination.

**Resume here**: ask the user which direction, or bring back this
three-way framing if picking the conversation back up cold.

## Git
All code + docs + the runs above are committed and pushed to
`origin/main` (4 commits after "Initial Commit"). Nothing uncommitted as
of this writing.
