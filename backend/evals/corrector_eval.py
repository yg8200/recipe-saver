"""Measures how well correct_recipe_text fixes OCR typos without touching correct text.

Needs real API keys in backend/.env (it calls the OpenAI corrector). Costs a few cents at most.

    cd backend && PYTHONPATH=. .venv/bin/python evals/corrector_eval.py [runs]

For every line we compare the OCR text, the guardrail's output and the known-correct "gold" text:
  fixed       a typo line that now equals gold
  missed      a typo line that is unchanged
  wrong edit  a typo line changed to something that is NOT gold (it invented or rewrote)
  false edit  a correct line that was changed (the guardrail "thought too much")
"""
import sys

from evals.corrector_cases import CASES, JUNK_TITLE_OCR
from src.services.recipe_corrector import correct_recipe_text

SECTIONS = ("ingredients", "instructions")


def score(ocr: dict, gold: dict, out: dict, verbose: bool) -> dict:
    result = dict(typo_lines=0, fixed=0, missed=0, wrong_edit=0, false_edit=0, lines=0)
    pairs = [("title", ocr["title"], gold["title"], out["title"])]
    for section in SECTIONS:
        pairs += [(section, i, g, o) for i, g, o in zip(ocr[section], gold[section], out[section])]
    for section, original, expected, actual in pairs:
        result["lines"] += 1
        if original != expected:
            result["typo_lines"] += 1
            if actual == expected:
                result["fixed"] += 1
            elif actual == original:
                result["missed"] += 1
                if verbose: print(f"      missed    : {original!r} (want {expected!r})")
            else:
                result["wrong_edit"] += 1
                if verbose: print(f"      wrong edit: {original!r} -> {actual!r} (want {expected!r})")
        elif actual != original:
            result["false_edit"] += 1
            if verbose: print(f"      false edit: {original!r} -> {actual!r}")
    return result


def main(runs: int) -> None:
    totals = dict(typo_lines=0, fixed=0, missed=0, wrong_edit=0, false_edit=0, lines=0)
    for run in range(runs):
        for name, ocr, gold in CASES:
            out = correct_recipe_text(ocr)
            r = score(ocr, gold, out, verbose=False)
            flag = "" if not (r["missed"] or r["wrong_edit"] or r["false_edit"]) else "  <-- problems"
            print(f"run {run + 1} | {name:45} fixed {r['fixed']}/{r['typo_lines']}  "
                  f"missed {r['missed']}  wrong {r['wrong_edit']}  false {r['false_edit']}{flag}")
            if flag:
                score(ocr, gold, out, verbose=True)
            for key in totals:
                totals[key] += r[key]
        # The junk-title case has no single right answer: it passes if the title was replaced
        # by something else while every other line stayed the same.
        out = correct_recipe_text(JUNK_TITLE_OCR)
        others_same = out["ingredients"] == JUNK_TITLE_OCR["ingredients"] and out["instructions"] == JUNK_TITLE_OCR["instructions"]
        print(f"run {run + 1} | {'junk title (site name)':45} title -> {out['title']!r}  other lines untouched: {others_same}")
    print("-" * 100)
    print(f"TOTAL over {runs} run(s): typo lines {totals['typo_lines']}  fixed {totals['fixed']}  missed {totals['missed']}  "
          f"wrong edits {totals['wrong_edit']}  false edits {totals['false_edit']}  (of {totals['lines']} lines)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
