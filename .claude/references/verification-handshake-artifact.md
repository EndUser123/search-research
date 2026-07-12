# Verification Handshake Artifact

## Purpose

Prevent redundant re-verification when a document or plan has already been
reviewed by an upstream stage. Any stage that produces verification findings
writes a `.verification-received.json` alongside the reviewed artifact. The
next stage reads this before deciding what to re-verify.

## File Convention

Place a `.verification-received.json` file in the same directory as the
reviewed artifact, named after the artifact:

| Artifact | Verification handshake file |
|----------|---------------------------|
| `ENHANCEMENT_PLAN.md` | `ENHANCEMENT_PLAN.md.verification-received.json` |
| `plans/plan-foo.md` | `plans/plan-foo.md.verification-received.json` |

## Schema

```json
{
  "artifact_path": "<absolute-path>",
  "artifact_hash": "sha256:<hex>",
  "verified_at": "<ISO8601>",
  "verified_by": "<stage-name>",
  "findings_total": 5,
  "findings_resolved": 3,
  "findings_deferred": 2,
  "upstream_stages": [
    {"name": "external-llm-red-team", "status": "completed"},
    {"name": "codebase-verification", "status": "completed"}
  ],
  "unresolved_finding_ids": ["FIND-001", "FIND-002"],
  "consumer_note": "Next stage: check this file before re-running verification. If artifact_hash matches and all block-level findings are resolved, re-verification is not required."
}
```

## Required fields

- `artifact_path`, `artifact_hash` — identify which artifact was verified
- `verified_at`, `verified_by` — when and by whom
- `findings_total` — all findings produced
- `findings_resolved` — findings accepted and fixed
- `findings_deferred` — findings deferred with rationale

## Consumer behavior

The downstream stage (e.g., `/planning` reading an enhancement plan that was
already red-teamed) must:

1. Check for `{artifact}.verification-received.json` alongside the artifact
2. If found, read it
3. If `artifact_hash` matches current file content AND the upstream has no
   unresolved BLOCKER/HIGH findings for the relevant scope, skip re-verification
   and synthesize a one-line summary: "Upstream verification by <verified_by>
   on <verified_at>: N findings, N resolved, N deferred."
4. If hash differs (artifact was edited after verification) or unresolved
   blockers exist, proceed with full re-verification

## Producers

Each verification stage writes this file after completing its review:

- **External LLM red-team** writes after producing findings
- **Codebase verification** (the evidence-gathering pass) writes after confirming findings
- **Plan adversarial agents** write after critic synthesizes — this is covered by
  the existing `workflow_stage.json` pattern, but a `.verification-received.json`
  at the plan level would let downstream `/code` or `/verify` skip redundant review
