# Constraint Decay ("Attentional Cliff")

Empirical study of how instruction-following in small local LLMs degrades as
padding tokens separate a system constraint from the user query. Multi-model
comparison run entirely on local hardware via [Ollama](https://ollama.com),
targeting a short research paper / technical blog post.

**Status:** Study 1 (constraint decay) in progress on `llama3.2:3b`. Pilot,
prose-padding probes, and a full `distractor`-padding grid (5 constraints x
6 padding levels x n=10) are done; see `docs/claude/handoff.md` for current
results and next steps. `llama3.2:1b` has one small probe (n=5/cell);
`gemma3:12b` is pulled but has no experiment data yet. See
`docs/research_agenda.md` for the full study roadmap.

## Findings so far

All results below are **`llama3.2:3b` only**, `constraint_position=before`,
temperature 0 with per-trial seeds, experiment version `v1`. Token counts
are mean `prompt_tokens` reported by Ollama. They are preliminary: one
model, one position, and the narrower probes are underpowered. Nothing
here generalizes beyond the models and constraints tested.

### Main result: `distractor` padding grid (n=10/cell, 300 trials)

Source: `data/raw/distractor_grid_3b_20260729_2309.csv` ->
`results/fits/distractor_grid_3b_20260729_2309_fits.json`. Pass rate per
padding level (approx. prompt tokens: 0 -> ~55, 32 -> ~1.9k, 64 -> ~3.7k,
96 -> ~5.6k, 128 -> ~7.4k, 160 -> ~9.2k):

| Constraint       | L0   | L32  | L64  | L96  | L128     | L160     | T50 (tokens)                      |
|------------------|------|------|------|------|----------|----------|-----------------------------------|
| `negative_the`   | 1.0  | 0.8  | 0.9  | 0.6  | 0.6      | 0.4      | **7988** (95% CI 6168–11670)      |
| `uppercase`      | 1.0  | 1.0  | 1.0  | 1.0  | 0.9      | 1.0      | > 9290 tested (right-censored)    |
| `end_token`      | 1.0  | 1.0  | 1.0  | 0.9  | 1.0      | 1.0      | > 9291 tested (right-censored)    |
| `json_schema`    | 1.0  | 1.0  | 1.0  | 1.0  | 1.0      | 1.0      | no variation (100% throughout)    |
| `prefix_persona` | 1.0  | 0.7  | 1.0  | 1.0  | 1.0 (n=2)| 1.0 (n=4)| > 9299 tested (right-censored, **underpowered**) |

- **Only `negative_the` shows a fitted cliff.** T50 ≈ 7988 tokens, with a
  wide bootstrap CI (1000 resamples, seed 42) whose upper bound extends
  past the largest context tested (~9.3k). Treat the location as
  approximate.
- **Formatting constraints survive.** `uppercase`, `end_token`, and
  `json_schema` never drop below 50% up to ~9.3k tokens. We report these as
  right-censored and do not extrapolate a T50.
- **`prefix_persona` is inconclusive at the top levels.** 14 of 60 trials
  were excluded (`success=-1`) because the runner's 600s read-timeout fired
  (8 at L128, 6 at L160), which left n=2 and n=4 valid trials. Its fitted
  slope is positive, driven by a 0.7 dip at L32. Don't read this row as a
  "no decay" result until the top levels are rerun with a longer timeout
  (see `docs/watchouts.md`).

### Mechanism: the `negative_the` failures are mostly task misframing

When we inspected `output_snippet`, most failures at high padding were
refusals, not slips. The model treats the task as reading comprehension
("this question is not related to the provided text"). That refusal
boilerplate often contains "the", which is what trips the validator.
"Constraint forgotten" and "task misframed" are different phenomena; see
the refusal-boilerplate watchout in `docs/watchouts.md`.

### Earlier `prose`-padding probes (underpowered, n=2–5/cell)

| Run | Model | Constraint | Levels (≈ tokens) | Result |
|-----|-------|------------|-------------------|--------|
| `pilot_20260707_203938` | 3b | all 5 | 0–32 (≤ ~1.9k), n=3 | 60/60 pass |
| `probe_uppercase_20260707_230839` | 3b | `uppercase` | 32–160 (~1.9k–9.3k), n=2 | 10/10 pass |
| `probe_json_schema_20260707_235258` | 3b | `json_schema` | 32–160, n=2 | 9/9 valid pass, 1 timeout |
| `canary_negative_the_20260708_0227` | 3b | `negative_the` | 96 / 160, n=5 | 2/5 (40%); 2/4 valid (50%), 1 timeout |
| `canary_negative_the_1b_20260708_1542` | 1b | `negative_the` | 96 / 160, n=5 | 2/5 (40%); 3/5 (60%) |

The 1b and 3b canary rates are similar, and the same refusal mechanism
appears in both. At n=5 that is **not** evidence that model scale has no
effect.

### Determinism audit

`results/fits/determinism_audit.json`: `llama3.2:3b`, 5 repeats x 3
`num_thread` settings (default/4/8) produced byte-identical outputs and
stable `prompt_tokens`. Temp-0 + seed is reproducible on this CPU.

### Open items

- Rerun `prefix_persona` L128/L160 with a longer timeout.
- Run the same grid on `gemma3:12b` (and later on quantization variants
  for Study 2).
- Test the `after` (control) position. Every result above is
  `before`-position only, so positional decay has not yet been isolated.

Figures for every cell: `results/figures/llama3.2-3b_<constraint>_<padding>_before.{png,svg}`.

## How it works

A system-prompt constraint (e.g. "reply only in uppercase") is separated
from the user query by a variable amount of padding text, and we measure
the token count at which the model stops reliably following the constraint
(the "cliff"). See `docs/methodology.md` for the experiment design and
`docs/claude/architecture.md` for the data flow.

```
Runner (experiments/constraint_decay_toolkit.py)
  -> Ollama /api/chat (localhost:11434, temperature 0, seeded)
  -> data/raw/*.csv        (one row per trial, immutable)

Analysis (analysis/fit_cliffs.py)
  -> logistic fits per (model x constraint x condition)
  -> results/fits/*.json   (T50 + bootstrap CIs)

Plotting (analysis/plot_curves.py)
  -> results/figures/*.{png,svg}

Paper (paper/draft.md) cites only values present in results/fits/.
```

## Project layout

- `experiments/` — experiment runner, constraint validators, padding
  generators, determinism audit, unit tests
- `analysis/` — logistic-fit + T50 estimation, plotting scripts
- `paper/` — manuscript drafts, figures, references
- `data/raw/` — raw experiment CSVs (**immutable** — never edited in place)
- `data/processed/` — cleaned/aggregated datasets derived from raw
- `results/figures/` — generated plots (PNG + SVG, regenerable)
- `results/fits/` — fitted model parameters (JSON)
- `docs/` — methodology, research agenda, known pitfalls, changelog
  (`docs/claude/` — architecture notes and repo/document index)

## Setup

Requires Python 3.11+ and a local [Ollama](https://ollama.com) install with
at least one model pulled.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas numpy scipy matplotlib statsmodels pytest ruff

ollama serve                    # if not already running
ollama list                     # confirm the model tags you plan to use
```

## Usage

```bash
source .venv/bin/activate

# Run the validator/padding unit tests (do this first, and after any edit
# to experiments/)
pytest experiments/tests/ -x -q

# Verify temp-0 + fixed-seed determinism on your hardware before trusting
# any experiment results
python experiments/determinism_audit.py --model gemma3:12b --repeats 5

# Run an experiment grid
python experiments/constraint_decay_toolkit.py \
  --models gemma3:12b --trials 10 --out data/raw/run_$(date +%Y%m%d_%H%M).csv

# Fit T50 cliffs and generate figures
python analysis/fit_cliffs.py data/raw/<run>.csv
python analysis/plot_curves.py results/fits/

# Lint
ruff check . && ruff format --check .
```

## Citing

This project is being written up as a paper (draft to live at
`paper/draft.md` once experiment data exists). Citation details will be
added here once a preprint or publication exists.

## License

Code in this repository is licensed under the [MIT License](LICENSE). The
eventual paper text will carry its own license terms, set at publication
(e.g. via arXiv's license selection), independent of this file.
