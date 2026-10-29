# LLM extraction from property listings, evaluated against hand labels

Extracts four fields from UK listing descriptions (garden, parking, chain-free,
condition) with Google Gemini, and measures per-class precision and recall against 100
hand-labelled examples. A keyword/regex baseline is scored alongside it, so the
LLM has to earn its cost.

Listings are **synthetic** (LLM-generated from sampled attributes). No portal
was scraped.

## Why the design looks like this
- **The spec is not ground truth.** Each listing is written from a sampled spec, but generators drift from instructions. Hand labels are the truth. Scoring the spec against them measures generator fidelity, reported as `generator_spec`.
- **Blind labelling.** `src/label.py` never shows you the spec or the predictions, so you can't anchor on them.
- **Different models generate and extract** (`gemini-3.8-flash` writes, `gemini-3.1-flash-lite` extracts by default). They share a family, so this reduces, but doesn't remove, the risk of the extractor recognising its own phrasing. Override with `GEN_MODEL` and `EXTRACT_MODEL`.
- **Hard cases on purpose.** A quarter of the listings are written in "tricky" style: a nearby park instead of a garden, a garage converted to a study, "vendor suited", estate-agent praise with no renovation claim.
- **Constrained output plus evidence.** Gemini structured output with an enum-constrained JSON schema, and a verbatim quote for each field. Quotes are checked against the text (grounding rate).
- **Confidence intervals.** With n=100, a rare class has about 10–20 examples. Wilson intervals stop you from over-reading the gaps.

## Run
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...        # free key from Google AI Studio

python -m src.generate        # 300 listings -> data/listings.jsonl (cached)
python -m src.extract_llm     # -> data/pred_llm.jsonl
python -m src.extract_rules   # -> data/pred_rules.jsonl
python -m src.label           # hand-label 100 (resumable, 'q' to quit)
python -m src.evaluate        # -> outputs/report.md, per_class.csv, llm_errors.csv
```
API responses are cached in `data/cache/`, so re-runs are free and deterministic.
The free tier is rate-limited, so calls are spaced 13 s apart (`MIN_INTERVAL_S`). If the
daily quota runs out, re-run the same command the next day and it resumes from the cache.
Offline smoke test: add `--mock` to `generate` and `extract_llm` (the report is stamped MOCK).

Field definitions live in `src/schema.py` and feed the prompt, the labelling guide
and the metrics, so they can't drift apart.

## Results
_From your run: macro-F1 LLM vs rules per field, the weakest class and why,
grounding rate, generator fidelity, and 2–3 error categories from llm_errors.csv._

## Limitations
- Synthetic text is cleaner and more uniform than real listings. Scores are an upper bound.
- There is a single labeller. Re-label 20 listings a week later to estimate your own consistency.
- n=100 can't separate systems that differ by a few points.
