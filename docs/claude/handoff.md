# Handoff notes

Point-in-time status for resuming work in a fresh session. This is a
snapshot, not a durable doc — update or delete stale sections as work
progresses; don't let it silently rot into a false record. Last updated
2026-07-31.

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

### Step 3 — distractor grid: DONE (option 1 scope), 2026-07-30
Launched `llama3.2:3b` only, full levels (0/32/64/96/128/160), n=10,
`distractor` padding, `before` position, `--num-ctx 12000`, via
`nohup`/`disown` (~13h wall clock, finished clean, 300/300 trials).
Output: `data/raw/distractor_grid_3b_20260729_2309.csv` +
`logs/distractor_grid_3b_20260729_2309.log`.

**Note**: an earlier attempt at this same grid
(`data/raw/distractor_grid_3b_20260722_1912.csv`, 2026-07-22) died
partway through — mtime evidence pointed to a machine reboot/power loss
around trial 38/300, not an application bug. That file was uncommitted
and was deleted rather than kept as scientific record (agreed with user).

Result: `python analysis/fit_cliffs.py
data/raw/distractor_grid_3b_20260729_2309.csv` ->
`results/fits/distractor_grid_3b_20260729_2309_fits.json`, figures in
`results/figures/`.
- `negative_the`: real fitted cliff, T50 = 7988 tokens.
- `uppercase`, `end_token`: right-censored (never dropped below 50% in
  range tested, up to ~9290 tokens) — same formatting-survives-longer
  pattern seen in the earlier prose probes, now confirmed under
  `distractor` padding too.
- `json_schema`: no_variation (100% pass throughout — well-formedness
  never broke).
- `prefix_persona`: right-censored but flagged **UNDERPOWERED** at
  levels 128/160 — those cells took repeated hits from the runner's
  hardcoded 600s read-timeout (`constraint_decay_toolkit.py:183`) as
  per-call generation time grew with padding; some sub-cells recovered
  to n>=7, but treat this constraint's top-level result cautiously
  until/unless rerun with a longer timeout. New watchout candidate for
  `docs/watchouts.md`, not yet written up: **timeout-driven right-
  censoring at high `distractor` padding levels**, distinct from the
  already-documented refusal-boilerplate collision.

**Resume here**: decide whether to (a) accept the `prefix_persona`
top-level cells as-is, (b) rerun just levels 128/160 for
`prefix_persona` (and preemptively `end_token`) with a bumped timeout,
or (c) move on to `gemma3:12b` on the same grid now that cliff location
is roughly known (per the original option-1 rationale — 12B call times
will be much longer, so decide before committing that CPU budget).

## Not yet started
- Decision on `prefix_persona` rerun (levels 128/160) and on launching
  `gemma3:12b` over the same distractor grid (Study 1 -> Study 2 bridge).

## Session close, 2026-07-31
This session: launched and completed the `llama3.2:3b` distractor grid
(Step 3 above), fitted + plotted it, and did a docs/tooling pass:
- `docs/watchouts.md`: added the timeout-driven right-censoring watchout
  (see Step 3 above for the finding it's based on).
- `docs/changelog.md`: logged the `plot_curves.py`/`style.py` fixes below
  under Tooling (no `EXPERIMENT_VERSION` bump — plotting only).
- `analysis/plot_curves.py` + `analysis/style.py`: fixed a directory-glob
  crash on non-fit JSON files, a legend/annotation overlap, and label
  corruption from this machine's LaTeX-enabled matplotlibrc (pinned
  `text.usetex = False` rather than escaping per-label). All figures in
  `results/figures/` regenerated with these fixes — if you spot an old
  copy of a figure elsewhere (e.g. pasted into a draft), regenerate it.
- `README.md`: status section updated off the stale "no data yet" claim.
- Committed: distractor-grid CSV + log, fit JSON, figures, and all doc
  updates above (see `git log` from this session for exact commits).

Nothing is running right now. Everything is committed. Resume at the
"Not yet started" item above, or pick up Study 2 (quantization) per
`docs/research_agenda.md`.
