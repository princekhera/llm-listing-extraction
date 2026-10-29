"""Write ~300 synthetic UK listing descriptions from sampled specs.

    python -m src.generate            # real API (needs GEMINI_API_KEY)
    python -m src.generate --mock     # offline template text, for testing only
"""
import argparse
import json
import random

from . import llm
from .schema import DATA, NM
from .specs import sample

HOW = {
    "garden": {
        "private": "the property has its own private outside space (garden, yard, patio or terrace)",
        "communal": "the property shares communal gardens/grounds, with no private garden",
        "none": "state clearly there is no outside space",
        NM: "say nothing about the property's own outside space",
    },
    "parking": {
        "off_street": "there is off-street parking (driveway, garage or allocated space)",
        "on_street": "parking is on-street or by residents' permit only",
        "none": "state clearly there is no parking",
        NM: "say nothing about parking",
    },
    "chain_free": {
        "yes": "the sale is chain free / has no onward chain",
        NM: "say nothing about the chain",
    },
    "condition": {
        "new_build": "it is a brand-new build, never lived in",
        "good": "it has been recently renovated and is ready to move into",
        "needs_work": "it needs modernisation or renovation",
        NM: "say nothing about its condition or renovation state",
    },
}
STYLE = {
    "explicit": "State each fact plainly using common estate-agent wording.",
    "implicit": ("Convey each fact indirectly, the way a real agent might "
                 "(e.g. 'scope to put your own stamp on it' instead of 'needs modernisation', "
                 "'block-paved frontage' instead of 'driveway')."),
    "tricky": ("Include at least one plausible distractor that could fool a careless reader "
               "without changing the facts (e.g. a nearby park when there is no garden mention, "
               "a garage that has been converted into a study, 'vendor suited' wording, "
               "or praise like 'stunning' with no renovation claim)."),
}


def prompt(s: dict) -> str:
    facts = "\n".join(f"- {HOW[f][s[f]]}" for f in HOW)
    return f"""Write a UK property portal listing description (about {s['length_words']} words) for a
{s['bedrooms']}-bedroom {s['property_type']} in a {s['setting']} location, England.

Facts it must respect:
{facts}

{STYLE[s['style']]}

Invent a plausible street-free location description, room details and local amenities.
Do not use headings, bullet points, prices, agent names or real addresses.
Return only the description text."""


def mock(payload: dict) -> dict:
    txt = payload["prompt"]
    r = random.Random(txt)
    bits = [line[2:] for line in txt.splitlines() if line.startswith("- ")]
    body = " ".join(b[0].upper() + b[1:] + "." for b in bits if not b.startswith("say nothing"))
    filler = r.choice(["A well-proportioned home close to local shops and schools.",
                       "Situated moments from the park and the high street."])
    return {"text": f"{filler} {body}"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    specs = sample(a.n)
    (DATA / "specs.jsonl").write_text("\n".join(json.dumps(s) for s in specs) + "\n")

    out = []
    for i, s in enumerate(specs):
        payload = {"model": llm.GEN_MODEL, "max_tokens": 4000, "temperature": 1.0,
                   "prompt": prompt(s)}
        resp = llm.call(payload, mock if a.mock else None)
        out.append({"id": s["id"], "text": resp["text"].strip(), "mock": a.mock})
        if (i + 1) % 25 == 0:
            print(f"{i + 1}/{len(specs)}")
    (DATA / "listings.jsonl").write_text("\n".join(json.dumps(o) for o in out) + "\n")
    print(f"{len(out)} listings -> {DATA / 'listings.jsonl'}")


if __name__ == "__main__":
    main()
