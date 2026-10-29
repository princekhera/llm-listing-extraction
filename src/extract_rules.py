"""Keyword/regex baseline. The LLM has to beat this to justify its cost.

    python -m src.extract_rules
"""
import json
import re

from .schema import DATA, FIELDS, NM

R = lambda p: re.compile(p, re.I)

RULES = {  # first matching pattern wins, so order matters
    "garden": [
        (R(r"\b(communal|shared) (garden|grounds|courtyard)s?\b"), "communal"),
        (R(r"\bno (private )?(garden|outside space|outdoor space)\b"), "none"),
        (R(r"\b(rear|front|private|south[- ]facing|enclosed|landscaped|lawned)? ?garden\b|\bpatio\b|\b(roof )?terrace\b|\bcourtyard\b"), "private"),
    ],
    "parking": [
        (R(r"\bno (off[- ]street )?parking\b"), "none"),
        (R(r"\b(on[- ]street|permit|resident'?s'? parking)\b"), "on_street"),
        (R(r"\bdriveway\b|\b(allocated|private|off[- ]street|gated) parking\b|\bparking space\b|\bcarport\b|\b(single|double|integral|detached) garage\b"), "off_street"),
    ],
    "chain_free": [
        (R(r"\bchain[- ]free\b|\bno (onward )?chain\b"), "yes"),
    ],
    "condition": [
        (R(r"\bnew[- ]build\b|\bnever (been )?lived in\b|\bbrand[- ]new\b"), "new_build"),
        (R(r"\b(in need of|requires|needs|would benefit from) (some )?(modernis|updat|renovat|refurb)|\bproject\b|\bscope to\b"), "needs_work"),
        (R(r"\b(recently|newly|fully|extensively) (renovated|refurbished|modernised|updated)\b|\bmove[- ]in ready\b|\bready to move into\b"), "good"),
    ],
}


def extract(text: str) -> dict:
    row = {}
    for f, rules in RULES.items():
        row[f] = next((v for pat, v in rules if pat.search(text)), NM)
    return row


def main() -> None:
    listings = [json.loads(l) for l in (DATA / "listings.jsonl").read_text().splitlines()]
    preds = [{"id": x["id"], **extract(x["text"])} for x in listings]
    (DATA / "pred_rules.jsonl").write_text("\n".join(json.dumps(p) for p in preds) + "\n")
    print(f"{len(preds)} predictions -> {DATA / 'pred_rules.jsonl'}")


if __name__ == "__main__":
    main()
