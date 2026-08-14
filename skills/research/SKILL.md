---
name: research
description: "Canonical research workflow using deterministic capability routing, local and external evidence gathering, source opening, assessment, and provenance-bound artifacts."
workflow_steps: []
---
# Research (`/research`)

`/research` is the canonical research capability. It owns research intent,
capability routing, bounded lane execution, source opening, evidence
assessment, research artifacts, and grounded output.

Pipeline:

```text
research question
  -> evidence requirements
  -> capability routing
  -> QMD/MMX/Brave evidence gathering
  -> explicit source opening
  -> conservative assessment
  -> research-run.v1 artifact and output
```

The implementation is the existing Phase 1 engine. Provider output is not
authority; discovery is not evidence; evidence is not a claim; a claim is not
a decision. Unsupported claims remain refused.

Use `/research` for new research requests. `/all` remains a compatibility
wrapper and delegates to this workflow with compatibility caller telemetry.

## Modes

```bash
/research "question" --mode auto
/research "workspace question" --mode local-only
/research "current documentation" --mode unified
```

An experimental complementary lane may be selected explicitly through the
existing execution API or CLI (`--external-provider exa|duckduckgo`). This is
restricted/manual behavior; neither provider is an automatic candidate.

The runtime preserves immutable run-scoped artifacts, source identity,
assessment records, failures, quota/readiness telemetry, and conservative stop
behavior. Phase 2A, `/go`, `/search`, new providers, and `agy` are outside this
workflow's authorization.
