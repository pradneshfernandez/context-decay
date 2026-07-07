# Experiments — runner, validators, padding

Loads when working on files in `experiments/`. Root rules still apply.

## Key files

- `constraint_decay_toolkit.py` — CLI runner, `CONSTRAINTS` registry,
  validators, padding generators, Ollama client
- `determinism_audit.py` — CPU determinism audit (appendix study); confirms
  temp-0 + fixed seed gives byte-identical output across repeats and across
  `num_thread` settings. Run before trusting any experiment results.
- `tests/test_validators.py` — unit tests; every validator needs pass/fail/edge cases
- `tests/test_padding.py` — reproducibility tests (same seed -> identical padding)

## Invariants (do not break)

- Every constraint is a `Constraint(name, instruction, validator)` dataclass.
  Adding a constraint = add to `CONSTRAINTS` list + add tests + bump
  `EXPERIMENT_VERSION`. Never edit an existing constraint's instruction
  string in place.
- Validators are deterministic pure functions. No network calls, no LLM-as-
  judge, no randomness inside validators.
- Padding is seeded via `random.Random(seed * 7919 + level)` — changing this
  formula breaks reproducibility of all prior runs.
- CSV schema is append-only: new columns may be added at the end; never
  rename or reorder existing columns (analysis scripts depend on them).
- The runner must write with `newline=""`, flush after every row, and record
  failures as `success = -1` rather than raising — a crash at hour 6 of an
  8-hour CPU run must not lose completed rows.

## Ollama specifics

- Use the `/api/chat` endpoint, `stream: false`.
- Read the real prompt token count from `prompt_eval_count` in the response;
  never estimate tokens with word counts or tiktoken.
- Default `options`: `{"temperature": 0.0, "seed": <trial seed>, "num_ctx": 4096}`.
  `num_ctx` is configurable via `--num-ctx` (default 4096) — raise it before
  testing padding levels whose prompts could approach the default, and
  re-verify no truncation by checking `prompt_tokens` grows linearly with
  `padding_level`.
- `--constraints NAME [NAME ...]` runs a subset of the `CONSTRAINTS` registry
  by name. For exploratory probes (e.g. finding a rough cliff location
  before locking the main grid) only — the locked main grid run should use
  the full constraint set.
- Timeouts: 600s per call minimum (12B on CPU is slow). Retry once on
  connection errors, then record as error row.

## Testing

```bash
pytest experiments/tests/ -x -q
```

Run this after ANY edit in this directory, before running experiments.
