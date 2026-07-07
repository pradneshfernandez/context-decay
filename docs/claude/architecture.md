# Architecture at a glance

Runner (experiments/constraint_decay_toolkit.py)
  -> Ollama /api/chat (localhost:11434, temperature 0, seeded)
  -> data/raw/*.csv  (one row per trial, flushed incrementally)

Analysis (analysis/fit_cliffs.py)
  -> logistic fits per (model x constraint x condition)
  -> results/fits/*.json  (T50 + bootstrap CIs)

Plotting (analysis/plot_curves.py)
  -> results/figures/*.{png,svg}

Paper (paper/draft.md) cites only values present in results/fits/.
