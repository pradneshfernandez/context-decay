"""
Constraint Decay ("Attentional Cliff") Experiment Toolkit
=========================================================
Measures how constraint-following degrades as padding tokens separate
a system constraint from the user query, across local Ollama models.

Usage:
    python constraint_decay_toolkit.py --models gemma3:12b llama3.2:3b \
        --trials 10 --out results.csv

Requires: pip install requests
Ollama must be running locally (default http://localhost:11434).
"""

import argparse
import csv
import itertools
import json
import random
import re
import time
from dataclasses import dataclass
from typing import Callable

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

# Bump on any change to a validator, an instruction string, the padding
# seed formula, or the CSV column order/set. Log the bump in
# docs/changelog.md — results across versions are not comparable.
EXPERIMENT_VERSION = "v1"

# ----------------------------------------------------------------------
# 1. CONSTRAINTS + STRICT VALIDATORS
#    Every validator is deterministic: (output: str) -> bool
# ----------------------------------------------------------------------

def validate_uppercase(output: str) -> bool:
    """Pass iff every alphabetic character is uppercase (and letters exist)."""
    letters = [c for c in output if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() for c in letters)


def validate_no_the(output: str) -> bool:
    """Pass iff the word 'the' never appears (word-boundary, case-insensitive)."""
    return re.search(r"\bthe\b", output, flags=re.IGNORECASE) is None


def validate_json_schema(output: str) -> bool:
    """Pass iff output is ONLY a valid JSON object with exactly the keys
    {'answer': str, 'confidence': number in [0,1]}. Tolerates markdown fences,
    since 'JSON-ness' is what we test, not fence discipline. Tighten if desired."""
    text = output.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(obj, dict) or set(obj.keys()) != {"answer", "confidence"}:
        return False
    if not isinstance(obj["answer"], str):
        return False
    conf = obj["confidence"]
    return isinstance(conf, (int, float)) and not isinstance(conf, bool) and 0 <= conf <= 1


def validate_prefix(output: str) -> bool:
    """Pass iff response begins with the exact persona tag."""
    return output.lstrip().startswith("[AGENT-7]:")


def validate_end_token(output: str) -> bool:
    """Pass iff response ends with the exact termination string."""
    return output.rstrip().endswith("##END##")


@dataclass(frozen=True)
class Constraint:
    name: str
    instruction: str
    validator: Callable[[str], bool]


CONSTRAINTS = [
    Constraint(
        "uppercase",
        "STRICT RULE: You must reply using ONLY capital letters. "
        "Every single letter in your response must be uppercase.",
        validate_uppercase,
    ),
    Constraint(
        "negative_the",
        "STRICT RULE: You must NEVER use the word 'the' anywhere in your "
        "response, in any capitalization.",
        validate_no_the,
    ),
    Constraint(
        "json_schema",
        "STRICT RULE: You must respond ONLY with a valid JSON object with "
        'exactly two keys: "answer" (a string) and "confidence" (a number '
        "between 0 and 1). No other text before or after the JSON.",
        validate_json_schema,
    ),
    Constraint(
        "prefix_persona",
        "STRICT RULE: You are AGENT-7. Every response you give must begin "
        "with the exact tag [AGENT-7]: followed by your answer.",
        validate_prefix,
    ),
    Constraint(
        "end_token",
        "STRICT RULE: Every response must end with the exact string ##END## "
        "as the final characters of your reply.",
        validate_end_token,
    ),
]

# ----------------------------------------------------------------------
# 2. PADDING GENERATORS (three conditions)
#    Each returns ~1 "block" (~55-65 tokens) of text; blocks are stacked.
# ----------------------------------------------------------------------

NEUTRAL_SENTENCES = [
    "The migration patterns of Arctic terns cover distances exceeding seventy thousand kilometers annually.",
    "Volcanic basalt columns form through the slow cooling and contraction of lava flows.",
    "Medieval trade routes connected Baltic amber merchants with Mediterranean glassmakers.",
    "Photosynthesis in deep-water algae relies on accessory pigments absorbing blue-green light.",
    "The construction of aqueducts required precise gradient calculations over long distances.",
    "Sedimentary rock layers preserve records of ancient climate fluctuations over millennia.",
    "Honeybee colonies regulate hive temperature through coordinated wing-fanning behavior.",
    "Early cartographers relied on celestial navigation and dead reckoning for coastline surveys.",
]

DISTRACTOR_SENTENCES = [
    "The style guide notes that all summaries should be written in lowercase for consistency.",
    "According to the manual, responses ought to be formatted as plain prose paragraphs.",
    "The archived memo suggested that answers be given in French whenever possible.",
    "One reviewer commented that bullet points are preferable to JSON in reports.",
]

LOREM_BLOCK = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip. "
)


def make_padding(condition: str, n_blocks: int, rng: random.Random) -> str:
    """Build padding text. condition in {'lorem', 'prose', 'distractor'}."""
    if n_blocks == 0:
        return ""
    blocks = []
    for i in range(n_blocks):
        if condition == "lorem":
            blocks.append(LOREM_BLOCK)
        elif condition == "prose":
            blocks.append(" ".join(rng.sample(NEUTRAL_SENTENCES, 4)))
        elif condition == "distractor":
            # mostly neutral prose, one instruction-shaped distractor per block
            sents = rng.sample(NEUTRAL_SENTENCES, 3) + [rng.choice(DISTRACTOR_SENTENCES)]
            rng.shuffle(sents)
            blocks.append(" ".join(sents))
        else:
            raise ValueError(f"unknown padding condition: {condition}")
    return "\n\n".join(blocks)

# ----------------------------------------------------------------------
# 3. QUERIES (rotate to avoid overfitting to one question)
# ----------------------------------------------------------------------

QUERIES = [
    "What is the capital of France?",
    "Name one planet in our solar system.",
    "What color is a ripe banana?",
    "How many legs does a spider have?",
]

# ----------------------------------------------------------------------
# 4. OLLAMA RUNNER
# ----------------------------------------------------------------------

def run_ollama(model: str, system: str, user: str, seed: int, timeout: int = 600,
                num_thread: int | None = None):
    """Single non-streaming chat call. Returns (output, prompt_tokens, seconds)."""
    options = {"temperature": 0.0, "seed": seed, "num_ctx": 4096}
    if num_thread is not None:
        options["num_thread"] = num_thread
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": options,
    }
    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    elapsed = time.time() - t0
    output = data["message"]["content"]
    prompt_tokens = data.get("prompt_eval_count", -1)  # ACTUAL token count
    return output, prompt_tokens, elapsed

# ----------------------------------------------------------------------
# 5. EXPERIMENT GRID
# ----------------------------------------------------------------------

def run_experiment(models, trials, padding_levels, conditions, position, out_path):
    fieldnames = [
        "model", "constraint", "padding_condition", "constraint_position",
        "padding_level", "prompt_tokens", "trial", "seed",
        "success", "time_taken", "query", "output_snippet",
        "experiment_version",
    ]
    grid = list(itertools.product(models, CONSTRAINTS, conditions, padding_levels))
    total = len(grid) * trials
    done = 0

    print(f"EXPERIMENT_VERSION={EXPERIMENT_VERSION}")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for model, constraint, cond, level in grid:
            for trial in range(trials):
                seed = 1000 + trial
                rng = random.Random(seed * 7919 + level)  # reproducible padding
                padding = make_padding(cond, level, rng)
                query = QUERIES[trial % len(QUERIES)]

                if position == "before":  # constraint -> padding -> query
                    system = constraint.instruction
                    user = (padding + "\n\n" + query) if padding else query
                else:  # control: padding -> constraint adjacent to query
                    system = "You are a helpful assistant."
                    user = (padding + "\n\n" if padding else "") + \
                           constraint.instruction + "\n\n" + query

                try:
                    output, ptok, elapsed = run_ollama(model, system, user, seed)
                    success = int(constraint.validator(output))
                except Exception as e:
                    output, ptok, elapsed, success = f"ERROR: {e}", -1, -1, -1

                writer.writerow({
                    "model": model,
                    "constraint": constraint.name,
                    "padding_condition": cond,
                    "constraint_position": position,
                    "padding_level": level,
                    "prompt_tokens": ptok,
                    "trial": trial,
                    "seed": seed,
                    "success": success,
                    "time_taken": round(elapsed, 2),
                    "query": query,
                    "output_snippet": output[:200].replace("\n", " "),
                    "experiment_version": EXPERIMENT_VERSION,
                })
                f.flush()
                done += 1
                print(f"[{done}/{total}] {model} | {constraint.name} | {cond} "
                      f"| level={level} | tokens={ptok} | pass={success} "
                      f"| {elapsed:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["gemma3:12b"])
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--levels", nargs="+", type=int,
                    default=[0, 2, 4, 8, 12, 16, 24, 32])
    ap.add_argument("--conditions", nargs="+",
                    default=["prose"],
                    choices=["lorem", "prose", "distractor"])
    ap.add_argument("--position", default="before", choices=["before", "after"],
                    help="'before' = constraint separated from query (treatment); "
                         "'after' = constraint adjacent to query (control)")
    ap.add_argument("--out", default="results.csv")
    args = ap.parse_args()
    run_experiment(args.models, args.trials, args.levels,
                   args.conditions, args.position, args.out)
