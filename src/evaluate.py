"""Score LLM and rule baseline against hand labels; also score the generator's
spec against hand labels (how faithfully did the generator follow instructions?).

    python -m src.evaluate
"""
import json
import math

import pandas as pd

from .schema import DATA, FIELDS, NM, OUT


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _ci(lo: float, hi: float) -> str:
    return "-" if math.isnan(lo) else f"{lo:.2f}-{hi:.2f}"


def per_class(y: pd.Series, p: pd.Series, field: str) -> pd.DataFrame:
    rows = []
    for c in FIELDS[field]["values"]:
        if c == NM:
            continue
        tp = int(((p == c) & (y == c)).sum())
        fp = int(((p == c) & (y != c)).sum())
        fn = int(((p != c) & (y == c)).sum())
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec and rec and prec + rec else float("nan")
        plo, phi = wilson(tp, tp + fp); rlo, rhi = wilson(tp, tp + fn)
        rows.append({"field": field, "class": c, "support": tp + fn, "tp": tp, "fp": fp, "fn": fn,
                     "precision": prec, "precision_ci": _ci(plo, phi),
                     "recall": rec, "recall_ci": _ci(rlo, rhi), "f1": f1})
    return pd.DataFrame(rows)


def field_summary(y: pd.Series, p: pd.Series, pc: pd.DataFrame) -> dict:
    # Presence: did the system notice the field was mentioned at all?
    ym, pm = y != NM, p != NM
    tp = int((ym & pm).sum())
    return {"accuracy": float((y == p).mean()),
            "macro_f1": float(pc["f1"].fillna(0).mean()),
            "presence_precision": tp / pm.sum() if pm.sum() else float("nan"),
            "presence_recall": tp / ym.sum() if ym.sum() else float("nan")}


def score_system(name: str, gold: pd.DataFrame, pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = gold.merge(pred, on="id", suffixes=("_gold", "_pred"))
    pcs, sums = [], []
    for f in FIELDS:
        pc = per_class(m[f"{f}_gold"], m[f"{f}_pred"], f)
        pcs.append(pc.assign(system=name))
        sums.append({"system": name, "field": f, "n": len(m),
                     **field_summary(m[f"{f}_gold"], m[f"{f}_pred"], pc)})
    return pd.concat(pcs), pd.DataFrame(sums)


def load(p):
    return pd.DataFrame([json.loads(l) for l in (DATA / p).read_text().splitlines()])


def main() -> None:
    OUT.mkdir(exist_ok=True)
    gold = pd.read_csv(DATA / "labels.csv", dtype=str)
    if len(gold) < 100:
        print(f"WARNING: only {len(gold)} hand labels - CIs will be very wide.")
    cols = ["id", *FIELDS]
    systems = {"llm": load("pred_llm.jsonl"), "rules": load("pred_rules.jsonl"),
               "generator_spec": load("specs.jsonl")}
    pcs, sums = zip(*(score_system(n, gold[cols], d[cols]) for n, d in systems.items()))
    pc, summ = pd.concat(pcs), pd.concat(sums)
    pc.to_csv(OUT / "per_class.csv", index=False)
    summ.to_csv(OUT / "field_summary.csv", index=False)

    llm = systems["llm"]
    ground = {f: float(llm.loc[llm["id"].isin(gold["id"]), f"{f}_grounded"].mean()) for f in FIELDS}

    # Error table for analysis: every disagreement, with text and the LLM's quote.
    texts = load("listings.jsonl")[["id", "text"]]
    m = gold.merge(llm, on="id", suffixes=("_gold", "_llm")).merge(
        systems["rules"][cols], on="id").merge(texts, on="id")
    errs = []
    for f in FIELDS:
        bad = m[m[f"{f}_gold"] != m[f"{f}_llm"]]
        for _, r in bad.iterrows():
            errs.append({"id": r["id"], "field": f, "gold": r[f"{f}_gold"], "llm": r[f"{f}_llm"],
                         "rules": r[f], "llm_evidence": r[f"{f}_evidence"],
                         "ambiguous": r.get("ambiguous", ""), "text": r["text"]})
    pd.DataFrame(errs).to_csv(OUT / "llm_errors.csv", index=False)

    conf = {f: pd.crosstab(m[f"{f}_gold"], m[f"{f}_llm"], rownames=["gold"], colnames=["llm"])
            for f in FIELDS}
    _report(pc, summ, ground, conf, len(gold), int(gold.get("ambiguous", pd.Series()).astype(int).sum()),
            bool(load("listings.jsonl")["mock"].any()))
    print(f"Report -> {OUT / 'report.md'}")


def _report(pc, summ, ground, conf, n, n_amb, mock):
    f = lambda x: "-" if pd.isna(x) else f"{x:.2f}"
    wide = summ.pivot(index="field", columns="system", values="macro_f1")
    lines = []
    if mock:
        lines += ["> **MOCK RUN - offline test output, not results.**", ""]
    lines += [f"# Listing extraction evaluation (n = {n} hand-labelled, {n_amb} flagged ambiguous)", "",
              "## Macro-F1 by field (excluding not_mentioned as a class)", "",
              "| field | " + " | ".join(wide.columns) + " |", "|---" * (len(wide.columns) + 1) + "|"]
    for fld, r in wide.iterrows():
        lines.append(f"| {fld} | " + " | ".join(f(v) for v in r) + " |")
    lines += ["", "`generator_spec` = what the generator was told to write. Its gap from 1.0 is "
              "generator infidelity, i.e. why hand labels were needed.", "",
              "## Per-class precision / recall (95% Wilson CI)", ""]
    for sysname in ["llm", "rules"]:
        lines += [f"### {sysname}", "", "| field | class | support | precision | P CI | recall | R CI |",
                  "|---|---|---|---|---|---|---|"]
        for _, r in pc[pc["system"] == sysname].iterrows():
            lines.append(f"| {r['field']} | {r['class']} | {r['support']} | {f(r['precision'])} | "
                         f"{r['precision_ci']} | {f(r['recall'])} | {r['recall_ci']} |")
        lines.append("")
    lines += ["## Evidence grounding (LLM)", "", "Share of LLM evidence quotes found verbatim in the listing:", ""]
    lines += [f"- {k}: {v:.0%}" for k, v in ground.items()]
    lines += ["", "## Confusion matrices (LLM vs gold)", ""]
    for fld, c in conf.items():
        lines += [f"### {fld}", "", c.to_markdown(), ""]
    lines += ["## Error analysis (author)", "",
              "_Read outputs/llm_errors.csv. Group the errors into causes "
              "(definition ambiguity, distractor, negation, label error) before writing this._"]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
