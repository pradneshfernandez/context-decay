# Experiment design rationale (summary)

- Treatment: [constraint] -> [padding: 0..N blocks] -> [query]
- Control: [padding] -> [constraint adjacent to query] (isolates positional decay)
- Padding conditions: lorem (low entropy), prose (neutral), distractor (RAG analogue)
- 5 constraint types: uppercase, negative_the, json_schema, prefix_persona, end_token
- >=10 trials per cell, temperature 0, per-trial seeds, real token counts
  from Ollama prompt_eval_count
- Primary metric: T50 (logistic fit crossing point), not "first zero"
