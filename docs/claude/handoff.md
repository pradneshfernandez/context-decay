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
- Pulled models: `llama3.2:3b`, `llama3.2:1b`, `gemma3:12b`.

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
  works end-to-end.
- **Extended probes** under `prose` padding, levels 32/64/96/128/160
  (~1900-9300 tokens), `--num-ctx 12000`, 2 trials each, one constraint at
  a time:
  - `uppercase` (`data/raw/probe_uppercase_20260707_230839.csv`): 10/10
    pass. Zero decay up to ~9300 tokens. Model's *factual* accuracy
    degrades at higher levels but the *formatting* constraint never
    breaks.
  - `json_schema` (`data/raw/probe_json_schema_20260707_235258.csv`): 9/10
    pass, 1 clean timeout at the very top (recorded correctly as
    `success=-1`). JSON well-formedness never broke; only answer content
    varied.

## Decision made 2026-07-08: hybrid sequence
Previous session ended with three options on the table (switch to
`distractor` padding / finish probing remaining constraints under `prose`
/ pause and reframe the null as a paper angle). Resolved as a **hybrid**:
canary probe -> fragility contrast (smaller model) -> distractor grid ->
revisit prose-null statistical power only if needed. Rationale: the
uppercase/json_schema null is a real dissociation (formatting holds while
factual accuracy degrades) but is statistically underpowered as a "no
decay" claim at n=2-3/cell — cheaper to spend CPU finding out whether a
real cliff exists (via the constraint most likely to break, and via
`distractor` padding) than to keep probing a condition that may just not
produce one.

### Step 1 — canary probe: DONE, found a real (but confounded) cliff
`negative_the`, `prose` padding, levels 96 & 160, n=5, `llama3.2:3b`
(`data/raw/canary_negative_the_20260708_0227.csv`). Pass rate: level 96 =
2/5 (40%), level 160 = 2/4 valid (50%, one clean timeout excluded) — a
real drop from the ~100% seen for uppercase/json_schema at similar token
counts.

**Mechanism is not simple forgetting.** The model doesn't slip "the" into
an otherwise-normal answer. Instead, at these padding levels it starts
mis-framing the task as reading-comprehension ("this question is not
related to the provided text") and refuses to answer. The refusal
boilerplate *itself* often (not always) contains "the" — e.g. "not
related to **the** provided text" — which is what trips
`validate_no_the`. When the refusal phrasing happens to avoid "the", it
passes despite still being a refusal. So the failure is really "long
unlabeled context triggers a task-misframing behavior" with "the"-usage
in the refusal boilerplate as an incidental trigger for this specific
validator. Logged as a new watchout in `docs/watchouts.md` ("Refusal-
boilerplate collision").

Decision made in-session: treat this as a real (if mechanistically
unusual) decay signal rather than engineering around it with a task-
framing control prompt — the emergent refusal-under-long-context behavior
is itself part of the phenomenon worth reporting, not a bug to eliminate.
If revisited, the alternative was adding an explicit "the text above is
irrelevant filler" control condition (would require an `EXPERIMENT_VERSION`
bump since it changes the prompt template).

### Step 2 — fragility contrast: DONE, no strong scale effect detected
Same probe config on `llama3.2:1b`
(`data/raw/canary_negative_the_1b_<timestamp>.csv`). Pass rate: level 96 =
2/5 (40%), level 160 = 3/5 (60%). Same refusal-boilerplate mechanism
replicates verbatim (e.g. "I can't answer that question because it's not
relevant to the topic..."). Magnitude is comparable to `llama3.2:3b`, not
worse — 1B does not obviously "crack" more than 3B on this probe.
**Caveat: n=5/cell, well below the >=10 methodology target — this is not
strong evidence of "no scale effect," just insufficient evidence of one.**
Do not cite this as a scale-independence finding without more trials.

### Step 3 — distractor grid: NOT STARTED, scope paused
Budgeted before launching (per `docs/watchouts.md` "budget the grid"
watchout): a full locked grid (5 constraints x 6 levels [0/32/64/96/128/
160] x n=10 x both models) is ~25h of `llama3.2:3b` time and ~100h+ of
`gemma3:12b` time at observed per-call timings — not launchable as one
block. Four scoping options were presented to the user and not yet
decided (paused mid-session, "later"):
1. `llama3.2:3b` only, full levels, n=10 (~25h) — recommended; decide on
   `gemma3:12b` afterward once cliff location is known, to avoid paying
   12B's cost at levels that turn out to be pre- or post-cliff.
2. Both models, fewer levels (0/64/128), n=10 (~12h on 3B, ~50h on 12B).
3. Both models, full levels, n=5 (underpowered vs. methodology's >=10;
   would need explicit flagging).
4. User-specified custom grid.

**Resume here**: ask the user to pick a distractor-grid scope, or default
to option 1 if they just say "go."

## Not yet started
- Task: add `answer_correct` post-hoc check in the analysis layer (scan
  `output_snippet` for the expected answer against the fixed `QUERIES`
  list) to turn the uppercase/json_schema accuracy-vs-formatting
  dissociation into a second measured curve. No runner/schema change
  needed — analysis-layer only.

## Git
Docs updated this session (this file + `docs/watchouts.md`); not yet
committed. New raw CSVs from the canary + fragility-contrast probes
(`data/raw/canary_negative_the_20260708_0227.csv`,
`data/raw/canary_negative_the_1b_*.csv`) also uncommitted as of this
writing.
