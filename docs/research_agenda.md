# Research Agenda — Local LLM Reliability Lab

Umbrella theme: reliability profile of small (1-12B) local LLMs on consumer
hardware (CPU, Ollama). Advantage: deterministic binary validators + free
unlimited inference on the exact model class academic benchmarks under-cover.

Shared infrastructure: experiments/ runner, pure validators, seeded prompts,
real token counts (prompt_eval_count), logistic-fit T50 analysis.

## Study 1 (ACTIVE): Constraint decay / Attentional Cliff
Current study. See docs/methodology.md.

## Study 2 (Paper 1 extension): Quantization x instruction retention
- RQ: Does quantization lower/steepen the attentional cliff? Interaction
  with constraint type?
- Design: same grid as Study 1, model variable becomes (model x quant):
  e.g. gemma3:12b at q4_K_M / q5_K_M / q8_0; 4B and 8B models add fp16.
- New CSV column (append-only): `quantization`.
- Constraint on hardware: fp16 12B ~ 24GB, borderline on 32GB RAM — run
  alone, nothing else open.
- Lit anchor: quantized models underperform specifically on instruction
  following (arXiv:2409.11055); small models degrade most at 4-bit; no
  prior work measures cliff position vs bit-width.

## Study 3 (Paper 1 extension): Graded instruction conflict / injection
- RQ: At what distractor strength does an in-context instruction override
  the system constraint, as a function of position and model size?
- Design: promote distractor padding to 4-level ordinal variable:
  L1 passive mention -> L2 imperative -> L3 second-person instruction ->
  L4 authority-framed ("SYSTEM UPDATE:"). Guaranteed-exposure protocol
  (injection always in context; no retrieval stochasticity).
- Metrics: constraint-compliance rate AND injection-compliance rate
  (separate validators — model can fail both).
- Scope note: defensive/measurement framing only. We measure susceptibility
  of local models to instruction-shaped text in retrieved context; we do
  not develop or optimize attack strings.

## Study 4 (Paper 2): Verbalized calibration at 1-12B
- RQ: How miscalibrated is verbalized confidence in small local models,
  and does quantization amplify it?
- Design: reuse json_schema constraint (answer + confidence) over ~300
  closed-form factual questions with ground truth. Metric: ECE (10 bins),
  reliability diagrams. Cross with quant ladder from Study 2.
- Lit anchor: verbalized confidence clusters high regardless of accuracy;
  RLHF compresses it further; quantization amplifies calibration error
  (arXiv:2405.00632). Verbalized-ECE x quantization on local models: gap.

## Study 5 (Paper 2): Sycophancy flip-rate
- RQ: Flip rate under user pushback vs model size, base-vs-instruct,
  quantization.
- Design: two-turn protocol. Turn 1: factual question (keep only items the
  model answers correctly). Turn 2: "Are you sure? I think it's <wrong>."
  Binary flip detection via answer extraction validator.
- Lit anchor: at small scale, instruct checkpoints are not reliably less
  sycophantic than base (arXiv:2606.06306) — directly testable in Ollama.

## Study 6 (fast standalone blog post): Format brittleness census
- RQ: Output variance across ~50 semantically-identical prompt format
  variants (casing, separators, whitespace, JSON vs prose framing).
- Metric: per-model brittleness score = spread (max-min accuracy) across
  variants. Lit anchor: Sclar et al. 2024; arXiv:2601.06341 (40pp swings;
  size does not predict robustness).

## Appendix study (methods section for all papers): CPU determinism audit
- Verify temp-0 + fixed seed reproduces identical outputs across repeated
  runs and num_thread settings in Ollama on CPU. Required to justify the
  deterministic-evaluation claim in every paper above.

## Backlog / ideas
- Cross-lingual constraint decay (Tamil/Hindi/French constraint+query;
  validators via Unicode script ranges).
- KV-cache quantization x context length interaction.

## Sequencing
1. Finish Study 1 pilot -> lock levels -> main grid
2. Determinism audit (cheap, do early — it validates everything)
3. Studies 2+3 -> Paper 1
4. Study 6 -> blog post (publish first for visibility)
5. Studies 4+5 -> Paper 2
