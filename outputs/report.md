# Listing extraction evaluation (n = 100 hand-labelled, 3 flagged ambiguous)

## Macro-F1 by field (excluding not_mentioned as a class)

| field | generator_spec | llm | rules |
|---|---|---|---|
| chain_free | 0.78 | 0.82 | 0.81 |
| condition | 0.96 | 0.96 | 0.64 |
| garden | 0.81 | 0.84 | 0.70 |
| parking | 0.96 | 0.95 | 0.70 |

`generator_spec` = what the generator was told to write. Its gap from 1.0 is generator infidelity, i.e. why hand labels were needed.

## Per-class precision / recall (95% Wilson CI)

### llm

| field | class | support | precision | P CI | recall | R CI |
|---|---|---|---|---|---|---|
| garden | private | 39 | 0.95 | 0.83-0.99 | 0.97 | 0.87-1.00 |
| garden | communal | 18 | 0.92 | 0.67-0.99 | 0.67 | 0.44-0.84 |
| garden | none | 7 | 0.64 | 0.35-0.85 | 1.00 | 0.65-1.00 |
| parking | off_street | 28 | 1.00 | 0.88-1.00 | 1.00 | 0.88-1.00 |
| parking | on_street | 20 | 0.91 | 0.72-0.97 | 1.00 | 0.84-1.00 |
| parking | none | 9 | 0.89 | 0.56-0.98 | 0.89 | 0.56-0.98 |
| chain_free | yes | 14 | 0.70 | 0.48-0.85 | 1.00 | 0.78-1.00 |
| condition | new_build | 14 | 1.00 | 0.78-1.00 | 1.00 | 0.78-1.00 |
| condition | good | 33 | 0.92 | 0.78-0.97 | 1.00 | 0.90-1.00 |
| condition | needs_work | 16 | 0.84 | 0.62-0.94 | 1.00 | 0.81-1.00 |

### rules

| field | class | support | precision | P CI | recall | R CI |
|---|---|---|---|---|---|---|
| garden | private | 39 | 0.64 | 0.52-0.75 | 0.97 | 0.87-1.00 |
| garden | communal | 18 | 0.92 | 0.67-0.99 | 0.67 | 0.44-0.84 |
| garden | none | 7 | 0.75 | 0.30-0.95 | 0.43 | 0.16-0.75 |
| parking | off_street | 28 | 0.86 | 0.69-0.95 | 0.89 | 0.73-0.96 |
| parking | on_street | 20 | 0.83 | 0.63-0.93 | 0.95 | 0.76-0.99 |
| parking | none | 9 | 0.67 | 0.21-0.94 | 0.22 | 0.06-0.55 |
| chain_free | yes | 14 | 0.72 | 0.49-0.88 | 0.93 | 0.69-0.99 |
| condition | new_build | 14 | 0.82 | 0.59-0.94 | 1.00 | 0.78-1.00 |
| condition | good | 33 | 1.00 | 0.77-1.00 | 0.39 | 0.25-0.56 |
| condition | needs_work | 16 | 0.83 | 0.44-0.97 | 0.31 | 0.14-0.56 |

## Evidence grounding (LLM)

Share of LLM evidence quotes found verbatim in the listing:

- garden: 100%
- parking: 100%
- chain_free: 100%
- condition: 96%

## Confusion matrices (LLM vs gold)

### garden

| gold          |   communal |   none |   not_mentioned |   private |
|:--------------|-----------:|-------:|----------------:|----------:|
| communal      |         12 |      3 |               2 |         1 |
| none          |          0 |      7 |               0 |         0 |
| not_mentioned |          0 |      1 |              34 |         1 |
| private       |          1 |      0 |               0 |        38 |

### parking

| gold          |   none |   not_mentioned |   off_street |   on_street |
|:--------------|-------:|----------------:|-------------:|------------:|
| none          |      8 |               0 |            0 |           1 |
| not_mentioned |      1 |              41 |            0 |           1 |
| off_street    |      0 |               0 |           28 |           0 |
| on_street     |      0 |               0 |            0 |          20 |

### chain_free

| gold          |   not_mentioned |   yes |
|:--------------|----------------:|------:|
| not_mentioned |              80 |     6 |
| yes           |               0 |    14 |

### condition

| gold          |   good |   needs_work |   new_build |   not_mentioned |
|:--------------|-------:|-------------:|------------:|----------------:|
| good          |     33 |            0 |           0 |               0 |
| needs_work    |      0 |           16 |           0 |               0 |
| new_build     |      0 |            0 |          14 |               0 |
| not_mentioned |      3 |            3 |           0 |              31 |

## Error analysis (author)

_Read outputs/llm_errors.csv. Group the errors into causes (definition ambiguity, distractor, negation, label error) before writing this._
