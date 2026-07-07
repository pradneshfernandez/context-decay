# Paper — manuscript and write-up

Loads when working on files in `paper/`. Root rules still apply.

## Key files

- `draft.md` — working manuscript (Markdown; convert to LaTeX/PDF at the end)
- `references.bib` — BibTeX references
- `figures/` — symlinks or copies from `results/figures/` only

## Structure (fixed — do not reorganize without asking)

1. Abstract
2. Introduction & related work (position against "lost in the middle" /
   long-context degradation literature)
3. Methodology (constraint taxonomy, padding conditions, position control,
   decoding controls, validators, models tested)
4. Results (T50 per model/constraint, constraint fragility ranking,
   position control, distractor condition)
5. Discussion: implications for RAG and agent pipelines
6. Limitations & future work

## Writing rules

- Every quantitative claim in the text MUST trace to a value in
  `results/fits/` or a figure in `results/figures/`. If the number isn't in
  a results file, do not write it — say so and ask.
- Never invent, estimate, or "recall" experimental numbers. Placeholder
  syntax for pending results: `[T50: TBD]`.
- Never fabricate citations. If a reference is needed but unknown, insert
  `[CITATION NEEDED: topic]` and list it at the top of the draft.
- Claims scope: results apply to the tested models, sizes, and constraint
  types. Avoid universal claims about "all LLMs".
- Tone: plain technical prose. No hype ("groundbreaking", "revolutionary"),
  no rhetorical questions, minimal adjectives.
- Report negative/null results (e.g., constraints that never decayed) with
  the same prominence as positive ones.
- Keep Methods precise enough that a reader could reproduce the experiment
  from the paper alone (exact instruction strings go in an appendix).
