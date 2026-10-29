"""LLM extraction with Gemini structured output (JSON schema): enums constrain the output, and each
field must quote its evidence so we can check the model isn't inventing support.

    python -m src.extract_llm [--mock]
"""
import argparse
import json
import random

from . import llm
from .schema import DATA, FIELDS, NM, guide_text

# JSON schema enforced by Gemini's structured-output mode: enums constrain the
# values, and each field must quote its evidence so we can check grounding.
SCHEMA = {
    "type": "object",
    "properties": {
        f: {
            "type": "object",
            "properties": {
                "value": {"type": "string", "enum": d["values"]},
                "evidence": {"type": "string",
                             "description": "Exact quote from the listing supporting the value; "
                                            "empty string if not_mentioned."},
            },
            "required": ["value", "evidence"],
        }
        for f, d in FIELDS.items()
    },
    "required": list(FIELDS),
}

SYSTEM = f"""You extract facts from UK property listings. Only record what the text states
about THIS property. When the text is silent or ambiguous, use not_mentioned.

Definitions:
{guide_text()}"""


def mock(payload: dict) -> dict:
    txt = payload["prompt"].lower()
    r = random.Random(txt)
    def pick(rules):
        for kw, v in rules:
            if kw in txt and r.random() > 0.08:
                return v
        return NM
    out = {
        "garden": pick([("communal", "communal"), ("no outside", "none"), ("garden", "private")]),
        "parking": pick([("permit", "on_street"), ("on-street", "on_street"),
                         ("no parking", "none"), ("driveway", "off_street"), ("garage", "off_street")]),
        "chain_free": pick([("chain", "yes")]),
        "condition": pick([("brand-new", "new_build"), ("modernisation", "needs_work"),
                           ("renovat", "good")]),
    }
    return {"text": json.dumps({f: {"value": v, "evidence": ""} for f, v in out.items()})}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    listings = [json.loads(l) for l in (DATA / "listings.jsonl").read_text().splitlines()]
    preds = []
    for x in listings:
        payload = {"model": llm.EXTRACT_MODEL, "max_tokens": 4000, "temperature": 0,
                   "system": SYSTEM, "json_schema": SCHEMA,
                   "prompt": f"Listing:\n\n{x['text']}"}
        try:
            out = json.loads(llm.call(payload, mock if a.mock else None)["text"])
        except json.JSONDecodeError:
            out = {}  # counted as not_mentioned for every field; logged below
            print(f"  {x['id']}: unparseable JSON")
        row = {"id": x["id"]}
        for f in FIELDS:
            v = out.get(f, {})
            ev = (v.get("evidence") or "").strip()
            row[f] = v.get("value", NM)
            row[f"{f}_evidence"] = ev
            # Grounding check: a non-empty quote must appear verbatim in the listing.
            row[f"{f}_grounded"] = (ev == "") or (ev.lower() in x["text"].lower())
        preds.append(row)
    (DATA / "pred_llm.jsonl").write_text("\n".join(json.dumps(p) for p in preds) + "\n")
    print(f"{len(preds)} predictions -> {DATA / 'pred_llm.jsonl'}")


if __name__ == "__main__":
    main()
