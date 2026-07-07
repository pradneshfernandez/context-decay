# Constraint Decay ("Attentional Cliff")

Empirical study of how instruction-following in small local LLMs degrades as
padding tokens separate a system constraint from the user query. Multi-model
comparison run entirely on local hardware via [Ollama](https://ollama.com),
targeting a short research paper / technical blog post.

**Status:** early — the experiment runner and its test suite exist; no
experiment data has been collected yet. See `docs/research_agenda.md` for
the full study roadmap and sequencing.

## How it works

A system-prompt constraint (e.g. "reply only in uppercase") is separated
from the user query by a variable amount of padding text, and we measure
the token count at which the model stops reliably following the constraint
(the "cliff"). See `docs/methodology.md` for the experiment design and
`docs/architecture.md` for the data flow.

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
- `docs/` — architecture, methodology, research agenda, known pitfalls,
  changelog

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

## Contributing / working in this repo

This repo is developed with Claude Code; see `CLAUDE.md` for the operating
rules (data integrity, versioning, statistics conventions) and the nested
`CLAUDE.md` files in `experiments/`, `analysis/`, and `paper/` for
directory-specific conventions. `docs/watchouts.md` lists every known
experimental pitfall — read it before touching validators, padding, or
analysis code.

## Citing

This project is being written up as a paper (draft to live at
`paper/draft.md` once experiment data exists). Citation details will be
added here once a preprint or publication exists.

## License

Code in this repository is licensed under the [MIT License](LICENSE). The
eventual paper text will carry its own license terms, set at publication
(e.g. via arXiv's license selection), independent of this file.
