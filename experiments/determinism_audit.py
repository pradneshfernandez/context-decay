"""
CPU Determinism Audit
======================
Appendix study required before trusting any result in this repo: verifies
that temperature=0.0 + a fixed seed reproduces byte-identical Ollama output
on repeated calls, and across different `num_thread` settings, on CPU.
See docs/research_agenda.md ("Appendix study") and docs/watchouts.md
("Non-determinism invalidates runs").

This does not touch data/raw/ — it writes its own report only.

Usage:
    python experiments/determinism_audit.py --model gemma3:12b \
        --repeats 5 --num-threads 4 8 --out results/fits/determinism_audit.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_decay_toolkit import EXPERIMENT_VERSION, run_ollama  # noqa: E402

AUDIT_SYSTEM = (
    "STRICT RULE: You must reply using ONLY capital letters. "
    "Every single letter in your response must be uppercase."
)
AUDIT_USER = "What is the capital of France?"
AUDIT_SEED = 1000


def run_repeats(model: str, n: int, num_thread: int | None):
    outputs = []
    prompt_tokens = []
    for i in range(n):
        output, ptok, elapsed = run_ollama(
            model, AUDIT_SYSTEM, AUDIT_USER, AUDIT_SEED, num_thread=num_thread
        )
        outputs.append(output)
        prompt_tokens.append(ptok)
        print(f"  [{i + 1}/{n}] num_thread={num_thread} tokens={ptok} "
              f"{elapsed:.1f}s")
    identical = len(set(outputs)) == 1
    tokens_stable = len(set(prompt_tokens)) == 1
    return {
        "num_thread": num_thread,
        "n": n,
        "outputs_identical": identical,
        "prompt_tokens_stable": tokens_stable,
        "distinct_outputs": len(set(outputs)),
        "outputs": outputs,
        "prompt_tokens": prompt_tokens,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma3:12b")
    ap.add_argument("--repeats", type=int, default=5,
                     help="calls per num_thread setting")
    ap.add_argument("--num-threads", nargs="+", type=int, default=[],
                     help="explicit num_thread values to test, in addition "
                          "to the Ollama default (unset)")
    ap.add_argument("--out", default="results/fits/determinism_audit.json")
    args = ap.parse_args()

    settings = [None] + list(args.num_threads)
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "model": args.model,
        "seed": AUDIT_SEED,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "runs": [],
    }

    all_pass = True
    for nt in settings:
        print(f"Running {args.repeats} repeats at num_thread={nt} ...")
        result = run_repeats(args.model, args.repeats, nt)
        report["runs"].append(result)
        if not (result["outputs_identical"] and result["prompt_tokens_stable"]):
            all_pass = False

    # Cross-num_thread comparison: same seed should give identical output
    # regardless of thread count, if determinism holds fully.
    first_outputs = {r["num_thread"]: r["outputs"][0] for r in report["runs"]}
    cross_thread_identical = len(set(first_outputs.values())) == 1
    report["cross_num_thread_identical"] = cross_thread_identical
    if not cross_thread_identical:
        all_pass = False

    report["overall_pass"] = all_pass

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print()
    print(f"Overall determinism audit: {'PASS' if all_pass else 'FAIL'}")
    print(f"Report written to {out_path}")
    if not all_pass:
        print("Do NOT trust results until this is resolved — see "
              "docs/watchouts.md.")
        sys.exit(1)


if __name__ == "__main__":
    main()
