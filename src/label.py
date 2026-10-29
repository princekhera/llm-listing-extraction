"""Blind hand-labelling in the terminal. You never see the spec or any model
prediction while labelling - otherwise you anchor on them and the evaluation
measures agreement with yourself, not accuracy.

    python -m src.label              # resumes where you left off
    python -m src.label --n 100

Type the number shown for each field. After the fields you are asked whether the
listing is genuinely ambiguous (kept, flagged in the report). 'q' saves and quits.
"""
import argparse
import csv
import json
import random
import textwrap

from .schema import DATA, FIELDS, guide_text

LABELS = DATA / "labels.csv"
COLS = ["id", *FIELDS, "ambiguous", "note"]


def pick_ids(n: int, seed: int = 2026) -> list[str]:
    specs = [json.loads(l) for l in (DATA / "specs.jsonl").read_text().splitlines()]
    by_style: dict[str, list[str]] = {}
    for s in specs:
        by_style.setdefault(s["style"], []).append(s["id"])
    r = random.Random(seed)
    ids = []
    for style, group in sorted(by_style.items()):  # stratify so 'tricky' is represented
        k = round(n * len(group) / len(specs))
        ids += r.sample(group, min(k, len(group)))
    r.shuffle(ids)
    return ids[:n]


def ask(field: str) -> str | None:
    vals = FIELDS[field]["values"]
    opts = "  ".join(f"[{i}] {v}" for i, v in enumerate(vals, 1))
    while True:
        k = input(f"  {field:<11} {opts}  > ").strip().lower()
        if k == "q":
            return None
        if k.isdigit() and 1 <= int(k) <= len(vals):
            return vals[int(k) - 1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    texts = {json.loads(l)["id"]: json.loads(l)["text"]
             for l in (DATA / "listings.jsonl").read_text().splitlines()}
    done = set()
    if LABELS.exists():
        done = {r["id"] for r in csv.DictReader(LABELS.open())}
    todo = [i for i in pick_ids(a.n) if i not in done]
    print("Labelling guide:\n" + guide_text() + "\n")
    print(f"{len(done)} done, {len(todo)} to go.\n")

    new_file = not LABELS.exists()
    with LABELS.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if new_file:
            w.writeheader()
        for n, lid in enumerate(todo, 1):
            print("=" * 78 + f"\n{lid}  ({n}/{len(todo)})\n")
            print(textwrap.fill(texts[lid], 78) + "\n")
            row = {"id": lid}
            for f in FIELDS:
                v = ask(f)
                if v is None:
                    print("Saved. Bye."); return
                row[f] = v
            amb = input("  ambiguous? [y/N] > ").strip().lower() == "y"
            row["ambiguous"] = int(amb)
            row["note"] = input("  note (optional) > ").strip() if amb else ""
            w.writerow(row); fh.flush()
    print("All done.")


if __name__ == "__main__":
    main()
