"""Scores one set up of the chapter 14.5 duty assistant eval.

Usage: python3 score_eval.py responses.csv
responses.csv has columns id, answer, rate_version: one row per question,
written by the set up under test (the model alone, or the model with the
calculator as a tool). A pass needs the figure to the paisa and the right
rate version; a refusal question passes only on REFUSE. Traps are scored on
their own line. A set up that fails one trap is not ready, whatever its total.

No score is quoted in the book or here. `python3 score_eval.py --self-test`
feeds the calculator's own answers back in, which only proves the scorer works.
"""
import sys
from pathlib import Path

import pandas as pd

KEY = Path(__file__).resolve().parent / "duty-eval-20.csv"


def passes(key_row, resp_row):
    if key_row.answer == "REFUSE":
        return str(resp_row.answer).strip().upper() == "REFUSE"
    try:
        figure_ok = round(float(str(resp_row.answer).replace(",", "")), 2) == round(float(key_row.answer), 2)
    except ValueError:
        return False
    return figure_ok and str(resp_row.rate_version).strip() == key_row.rate_version


def score(responses):
    key = pd.read_csv(KEY, dtype={"answer": str}).set_index("id")
    resp = responses.set_index("id")
    result = {qid: (qid in resp.index and passes(k, resp.loc[qid])) for qid, k in key.iterrows()}
    traps = key[key.trap != "no"].index
    total = sum(result.values())
    trap_pass = sum(result[t] for t in traps)
    print(f"passes: {total} out of {len(key)}")
    print(f"traps: {trap_pass} out of {len(traps)}" + ("" if trap_pass == len(traps) else "  NOT READY"))
    for qid, ok in result.items():
        if not ok:
            print(f"  fail {qid}: {key.loc[qid, 'question']}")
    return total, trap_pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--self-test":
        key = pd.read_csv(KEY, dtype={"answer": str})
        assert score(key[["id", "answer", "rate_version"]]) == (20, 4)
    else:
        score(pd.read_csv(sys.argv[1], dtype={"answer": str}))
