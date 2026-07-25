# Extraction prompts

The default prompts used by `extract.py`, inlined here for transparency and
editing. Tunable per corpus.

## Report prompt (concept extraction)

Default `REPORT_PROMPT` in `extract.py`:

```
For each major concept in this notebook's sources, extract:
1. Concept name (concise, 2-6 words)
2. Definition (1-3 sentences — what it IS, grounded only in the sources)
3. Operational details (thresholds, parameters, mechanisms, named components)
4. Relationships to other concepts in the notebook (named explicitly)
5. Verifiable values (numbers, defaults, ratios, version numbers)
6. Source citations (cite the specific source for each claim)

Format as Markdown with ## for each concept. Aim for 5-20 major concepts.
A major concept is a distinct topic, technique, tool, or architectural pattern.
Ignore minor mentions, tangents, and generic background.

Grounding constraint: use ONLY uploaded sources. Do not invent statistics,
quotes, or examples not in the sources. If a concept has no direct support,
omit it.
```

The grounding constraint is critical — without it, NotebookLM will extrapolate
from training data and the resulting wiki pages will have fabricated content.
This is the same pattern as `~/.grok/skills/wiki/SKILL.md` "Grounding anchor
(every prompt)": "Use only uploaded sources. Do not invent statistics, quotes,
or examples not in the sources."

## Data-Table prompt (tabular facts)

Default `DATA_TABLE_DESC` in `extract.py`:

```
Extract a row per concept with columns:
- concept_name (short)
- definition (1 sentence)
- key_values (semicolon-separated thresholds/numbers/defaults)
- related_concepts (semicolon-separated names from this notebook)
- primary_source_id (the source UUID that most directly supports this concept)
- supporting_quote (one short verbatim quote from that source)
```

The Data-Table artifact is the **structured cross-check** on the Report. Where
the Report gives narrative, the Data-Table gives facts. The parser merges both:
each concept absorbs matching values from the table (matched by name).

## When to tune

| Corpus type | Tune how |
|---|---|
| Technical (programming, math, science) | Lower concept count ("Aim for 5-10"); emphasize verifiable values |
| Conceptual (philosophy, business, design) | Raise concept count ("Aim for 15-25"); emphasize relationships |
| News / current events | Add date field to Data-Table; emphasize `primary_source_id` |
| Multi-author (discordant sources) | Add "note disagreements between sources" to Report prompt |

## Editing the prompts

The prompts are inlined in `extract.py` as `REPORT_PROMPT` and
`DATA_TABLE_DESC`. Edit there for permanent changes, or pass a custom prompt
via `--prompt` if added (not currently exposed at the CLI surface).

## Why Report + Data-Table, not chat

Three reasons (also documented in SKILL.md decision #2):

1. **Persistent artifacts.** Both Reports and Data-Tables are downloadable
   artifacts you can re-download weeks later. Chat responses are ephemeral.
2. **Structured citations.** Reports include source citations inline;
   Data-Tables include `primary_source_id` directly.
3. **Reproducibility.** Re-running sync produces the same artifacts (modulo
   NotebookLM's stochasticity), enabling honest comparison across runs.

Chat (`nlm notebook query`) is faster (~30s vs 5-15min) but produces
unstructured, uncited, ephemeral output. Use for exploration only.
