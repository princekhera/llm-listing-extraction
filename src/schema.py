"""Field definitions shared by the generator, extractors, labeller and evaluator.

One source of truth: if a definition changes here, the prompt, the labelling
guide and the metrics all change with it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "outputs"

NM = "not_mentioned"

FIELDS: dict[str, dict] = {
    "garden": {
        "values": ["private", "communal", "none", NM],
        "definition": (
            "private = garden/yard/patio/terrace for this property's sole use (incl. roof terrace). "
            "communal = shared or communal gardens/grounds. "
            "none = text states there is no outside space. "
            "not_mentioned = no statement about outside space for this property. "
            "Nearby parks or green spaces do NOT count."
        ),
    },
    "parking": {
        "values": ["off_street", "on_street", "none", NM],
        "definition": (
            "off_street = driveway, garage, allocated/private space, carport, gated parking. "
            "on_street = on-street, permit, or unallocated street parking only. "
            "none = text states no parking is available. "
            "not_mentioned = no statement about parking. "
            "A converted garage that is no longer usable for a car is NOT off_street."
        ),
    },
    "chain_free": {
        "values": ["yes", NM],
        "definition": (
            "yes = text says chain free, no onward chain, or vendor has already moved/found. "
            "not_mentioned = anything else, including 'vendor suited' or hopeful language."
        ),
    },
    "condition": {
        "values": ["new_build", "good", "needs_work", NM],
        "definition": (
            "new_build = newly built / never lived in / developer listing. "
            "good = recently renovated, refurbished, modernised, move-in ready, well presented. "
            "needs_work = needs modernisation/updating/renovation, project, refurbishment opportunity. "
            "not_mentioned = no statement about condition. "
            "Generic estate-agent praise ('stunning', 'charming') alone is NOT a condition statement."
        ),
    },
}

POSITIVE_IGNORE = {NM}  # for presence-detection metrics, NM is the negative class


def guide_text() -> str:
    return "\n".join(f"- {f}: {d['definition']}" for f, d in FIELDS.items())
