"""Sample the latent attributes each synthetic listing is written from.

The spec is the generator's *intended* label. It is NOT ground truth: the
generator may ignore or garble it. Ground truth = your hand labels. The gap
between the two is itself a reported result (generator fidelity).
"""
import json
import random

from .schema import DATA, FIELDS

PTYPES = ["flat", "maisonette", "terraced house", "semi-detached house",
          "detached house", "bungalow", "end-of-terrace house", "cottage"]
SETTINGS = ["inner-city", "suburban", "market town", "village", "coastal town"]
STYLES = ["explicit", "implicit", "tricky"]
# 'tricky' asks the generator for a near-miss distractor, e.g. "close to the park"
# when garden=not_mentioned, or "no onward chain is expected" phrasing.
WEIGHTS = {
    "garden": [0.40, 0.15, 0.10, 0.35],
    "parking": [0.35, 0.20, 0.10, 0.35],
    "chain_free": [0.25, 0.75],
    "condition": [0.12, 0.38, 0.20, 0.30],
}


def sample(n: int = 300, seed: int = 7) -> list[dict]:
    r = random.Random(seed)
    specs = []
    for i in range(n):
        ptype = r.choice(PTYPES)
        s = {"id": f"L{i:04d}", "property_type": ptype,
             "bedrooms": r.choice([1, 2] if ptype in ("flat", "maisonette") else [2, 3, 3, 4, 5]),
             "setting": r.choice(SETTINGS), "style": r.choices(STYLES, [0.4, 0.35, 0.25])[0],
             "length_words": r.choice([60, 90, 120, 160])}
        for f, d in FIELDS.items():
            s[f] = r.choices(d["values"], WEIGHTS[f])[0]
        if ptype in ("flat", "maisonette") and s["garden"] == "private" and r.random() < 0.5:
            s["garden"] = "communal"
        specs.append(s)
    return specs


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    p = DATA / "specs.jsonl"
    p.write_text("\n".join(json.dumps(s) for s in sample()) + "\n")
    print(f"300 specs -> {p}")
