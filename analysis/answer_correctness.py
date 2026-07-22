"""
Post-hoc factual-answer-correctness check for query/output_snippet pairs.

Analysis-layer only: does not touch the runner, validators, or CSV schema.
Turns the uppercase/json_schema "formatting holds, factual accuracy decays"
dissociation (docs/claude/handoff.md, "Not yet started") into a second
measurable curve by scanning `output_snippet` for the expected answer to
each fixed QUERIES entry (experiments/constraint_decay_toolkit.py).

Reads from data/raw/ (or any CSV with the experiment schema). Writes only
to data/processed/ — never touches data/raw/.

Usage:
    python analysis/answer_correctness.py data/raw/probe_uppercase_*.csv
    python analysis/answer_correctness.py data/raw/*.csv --out data/processed/answers.csv
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

REQUIRED_COLS = {"query", "output_snippet", "success"}


def _contains_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) is not None


def check_capital_of_france(output: str) -> bool:
    return _contains_word(output, "paris")


def check_planet(output: str) -> bool:
    planets = ["mercury", "venus", "earth", "mars", "jupiter",
               "saturn", "uranus", "neptune"]
    return any(_contains_word(output, p) for p in planets)


def check_banana_color(output: str) -> bool:
    return _contains_word(output, "yellow")


def check_spider_legs(output: str) -> bool:
    return _contains_word(output, "eight") or _contains_word(output, "8")


# Keyed on the exact QUERIES strings in constraint_decay_toolkit.py.
ANSWER_CHECKERS = {
    "What is the capital of France?": check_capital_of_france,
    "Name one planet in our solar system.": check_planet,
    "What color is a ripe banana?": check_banana_color,
    "How many legs does a spider have?": check_spider_legs,
}


def check_answer(query: str, output: str) -> bool | None:
    """None means the query isn't recognized -- caller should exclude it,
    not treat it as a failure."""
    checker = ANSWER_CHECKERS.get(query)
    if checker is None:
        return None
    return checker(output or "")


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add an `answer_correct` column: 1/0 for a recognized query on a
    non-error row, -1 for excluded (runner error row or unrecognized
    query) -- same exclusion convention as `success`."""
    df = df.copy()

    def _row(row) -> int:
        if row["success"] == -1:
            return -1
        result = check_answer(row["query"], row.get("output_snippet", ""))
        if result is None:
            return -1
        return int(result)

    df["answer_correct"] = df.apply(_row, axis=1)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+", help="raw experiment CSV(s)")
    ap.add_argument("--out", default=None,
                     help="output CSV path (default: "
                          "data/processed/<first-csv-stem>_answers.csv)")
    args = ap.parse_args()

    paths = [Path(p) for p in args.csvs]
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        print(f"ERROR: input CSV missing required columns: {sorted(missing)}")
        sys.exit(1)

    annotated = annotate(df)

    unrecognized = annotated[(annotated["success"] != -1) &
                              (~annotated["query"].isin(ANSWER_CHECKERS))]
    if len(unrecognized):
        print(f"WARNING: {len(unrecognized)} row(s) have a query not in "
              f"ANSWER_CHECKERS; recorded as excluded (answer_correct=-1). "
              f"Unrecognized queries: {sorted(unrecognized['query'].unique())}")

    out_path = (Path(args.out) if args.out
                else Path("data/processed") / f"{paths[0].stem}_answers.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    annotated.to_csv(out_path, index=False)

    n_excluded = int((annotated["answer_correct"] == -1).sum())
    n_scored = len(annotated) - n_excluded
    n_correct = int((annotated["answer_correct"] == 1).sum())
    print(f"Wrote {len(annotated)} row(s) to {out_path} "
          f"({n_correct}/{n_scored} correct, {n_excluded} excluded)")


if __name__ == "__main__":
    main()
