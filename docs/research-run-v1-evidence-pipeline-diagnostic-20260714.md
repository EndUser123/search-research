# Evidence-to-claim pipeline diagnostic — 2026-07-14

Verdict: `PASS_DIAGNOSTIC_ONLY`

## Finding

The primary bottleneck is downstream of query planning. Normal Phase 1 opens
candidate sources and preserves their raw bodies, but it does not form a
claim-specific assessment from ordinary opened passages. The contribution
metric then correctly reports zero useful sources because usefulness is bound
to claim/assessment source IDs.

This is not evidence that the sources were useless. It is evidence that the
current runtime does not complete the evidence-to-claim conversion for normal
`/all` research.

## Runtime map

```text
question/query
  -> /all signal extraction
  -> router recommendation
  -> provider/QMD normalized candidates
  -> source opening
       writes raw bytes to run-scoped sources/<lane>/<result>.source
  -> build_artifact
       writes source metadata and opened status
       creates claims only for explicit anchor confirmation or authority candidate mode
  -> assessment.py
       aggregates explicitly supplied EvidenceAssessment records
  -> quality.py
       counts only claim/assessment-linked source IDs as useful
  -> conservative stopping
```

Authority and data-flow observations:

- Candidate writer: `phase1.py` normalization and `build_artifact`.
- Opened-body writer: `open_source` / `_open_qmd_source`; scope is the immutable
  run directory and lifetime is run retention.
- Source metadata reader: `build_artifact`, validator, quality telemetry.
- Assessment writer: `build_artifact` only for anchor-confirmed sources or
  authority-candidate mode; broader assessment helpers accept explicit records.
- Claim writer: `build_artifact`; there is no ordinary passage-to-claim branch.
- Contribution reader: `quality.assess_source_contribution`; it trusts exact
  source IDs referenced by supported/partial/contradicted claims or direct
  assessments.
- Failure behavior: failed/empty lanes and unopened sources remain visible;
  no silent promotion occurs.
- Freshness: retrieved/opened timestamps are retained, but no general claim
  freshness assessment is created for ordinary opened sources.

## Representative evidence

The diagnostic record contains ten manually reviewed cases:

[research-quality-evidence-diagnostic-20260714.json](P:/tmp/research-quality-evidence-diagnostic-20260714.json)

Representative findings:

- The opened Python documentation body contains the passage warning that
  `wait()` can deadlock with `stdout=PIPE` or `stderr=PIPE` when output fills
  the OS pipe buffer. The artifact creates only an unverified authority-
  candidate claim with `contextual_only` assessment; it does not create the
  behavioral claim about deadlock.
- The opened GitHub Blog body contains a description of coding-agent
  automations. No claim or passage assessment is created for the repository-
  adoption question.
- Local-plus-external evaluation can have an empty QMD lane before any source
  is opened. That is a separate lane/input availability issue, not evidence of
  over-conservative claim assessment.

## Hypothesis evaluation

### H1 — assessment is too conservative

Not established as the primary cause. The assessment layer is conservative by
design, but ordinary opened passages are not submitted as claim-specific
assessments in the first place. The authority-candidate assessment is
intentionally `contextual_only` and correctly remains unverified.

### H2 — claims are underspecified or absent

Supported. Normal `/all` questions have expected decision claims, but
`build_artifact` creates claims only for anchor confirmation or authority
candidate bookkeeping. Six of the ten diagnostic cases had opened evidence and
zero claims; the official lookup produced only the authority-candidate claim,
not the requested behavioral claim.

### H3 — source opening/extraction is insufficient

Partially supported. Raw HTML is preserved and useful passages are present, but
no text extraction or passage selection is passed into assessment. This limits
the system's ability to form a claim; it does not show that bytes were lost at
capture time.

### H4 — corpus tasks are not claim-friendly

Not supported as the main explanation. The corpus includes concrete official,
compatibility, maintenance, adoption, and failure questions with specific
expected claims. The Python documentation case is directly claim-friendly.

### H5 — contribution tracking is wrong

Not supported. The tracker accurately reflects the current contract: no claim
or direct assessment means no useful source. A useful passage that is not
linked cannot safely be counted as useful evidence. The measurement is
incomplete for research quality, but not internally inconsistent.

## Narrow fixes

No production fix was made. The defect is real, but adding automatic claim
formation or HTML extraction would change evidence semantics and requires a
separate design/evaluation decision. The diagnostic preserves the safer
behavior rather than inventing claims from snippets or raw HTML.

## Verification

- Ten diagnostic artifact facts were checked against their source JSON files:
  opened-source and claim counts matched.
- Existing canonical suite result remains `72 passed, 3 failed`; the three
  failures are the previously attributed unrelated router-policy/corpus
  failures.
- No providers, routing, command topology, Phase 2A, `/go`, `/search`, or
  `agy` were changed or invoked.

## Authorization

Authorized:

- continue manual diagnostic inspection of opened evidence;
- retain claim formation as an explicit evidence-gathering boundary;
- use the current `/all` path with conservative stopping.

Not authorized:

- treating opened sources as useful without a claim-specific assessment;
- automatically synthesizing claims from snippets or HTML;
- integrating quality-guided execution into `/all`;
- adding providers, changing routing, enabling Phase 2A, or invoking `agy`.

Recommended next step: design a separate, claim-specified diagnostic where the
caller supplies an expected claim and an evidence passage is assessed against
that claim. Keep it experimental until claim linkage can be shown without
unsupported inference.
