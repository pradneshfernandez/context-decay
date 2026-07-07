# CLAUDE.md index

This repo uses Claude Code's directory-scoped `CLAUDE.md` convention:
Claude Code auto-loads the root `CLAUDE.md` plus the `CLAUDE.md` in
whichever directory it's currently working in. Because of that
auto-loading behavior, these files must stay at the repo root and inside
each directory they govern — they are not collected here. This page is
just an index of what exists and what each one covers, kept alongside the
architecture notes for anyone who wants the full picture in one place.

| File | Scope |
|---|---|
| `/CLAUDE.md` | Root rules: project layout, environment, commands, data-integrity and versioning rules, code style, workflow. Always loaded. |
| `/experiments/CLAUDE.md` | Runner/validator/padding invariants, Ollama call specifics, test command. Loaded when working in `experiments/`. |
| `/analysis/CLAUDE.md` | Statistical conventions (T50, bootstrap CIs, censoring), plotting conventions, read/write boundaries. Loaded when working in `analysis/`. |
| `/paper/CLAUDE.md` | Manuscript structure, sourcing rules (every number traces to `results/fits/`), tone, citation rules. Loaded when working in `paper/`. |

See also, referenced from the root `CLAUDE.md`:

- `docs/claude/architecture.md` — data flow at a glance
- `docs/methodology.md` — experiment design rationale
- `docs/research_agenda.md` — full study roadmap
- `docs/watchouts.md` — known pitfalls, checked before any task
- `docs/changelog.md` — experiment version history
