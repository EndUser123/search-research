---
title: "OpenTelemetry W3C Context Propagation"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, https]
summary: >
  A technique defined by the W3C TraceContext specification that enables OpenTelemetry to carry trace context across service boundaries, distributed systems, and process boundaries, supporting end-to-end request tracing and correlation.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 83d187f3-8f8a-4fbe-af21-2b1840c87960" (Transcripts and Logs of AI Coding Sessions, synced 2026-07-27)
  - "Microsoft Presidio Community Version: Open-Source PII Detection and Anonymization Tool" (https://hoop.dev/blog/microsoft-presidio-community-version-open-source-pii-detection-and-anonymization-tool/, transcript synced 2026-07-27)
  - "How to Build OpenTelemetry W3C Context Propagation - OneUptime" (https://oneuptime.com/blog/post/2026-01-30-opentelemetry-w3c-context-propagation/view, transcript synced 2026-07-27)
  - "Propagation - OpenTelemetry" (https://opentelemetry.io/docs/languages/js/propagation/, transcript synced 2026-07-27)
  - "How to Trace Node.js Child Processes with OpenTelemetry Context Propagation" (https://oneuptime.com/blog/post/2026-02-06-trace-nodejs-child-processes-opentelemetry-context-propagation/view, transcript synced 2026-07-27)
  - "OpenTelemetry Trace Context Propagation [JavaScript] - Uptrace" (https://uptrace.dev/get/opentelemetry-js/propagation, transcript synced 2026-07-27)
  - "Context propagation - OpenTelemetry" (https://opentelemetry.io/docs/concepts/context-propagation/, transcript synced 2026-07-27)
  - "How to Use OpenTelemetry Context Propagation - OneUptime" (https://oneuptime.com/blog/post/2026-02-02-opentelemetry-context-propagation/view, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: opentelemetry-w3c-context-propagation
    - level: notebook
      id: 83d187f3-8f8a-4fbe-af21-2b1840c87960
      title: Transcripts and Logs of AI Coding Sessions
      url: https://notebooklm.google.com/notebook/83d187f3-8f8a-4fbe-af21-2b1840c87960
    - level: cluster
      id: 3
      name: https-opentelemetry-propagation
    - level: source_url
      url: https://hoop.dev/blog/microsoft-presidio-community-version-open-source-pii-detection-and-anonymization-tool/
      title: Microsoft Presidio Community Version: Open-Source PII Detection and Anonymization Tool
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-01-30-opentelemetry-w3c-context-propagation/view
      title: How to Build OpenTelemetry W3C Context Propagation - OneUptime
    - level: source_url
      url: https://opentelemetry.io/docs/languages/js/propagation/
      title: Propagation - OpenTelemetry
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-trace-nodejs-child-processes-opentelemetry-context-propagation/view
      title: How to Trace Node.js Child Processes with OpenTelemetry Context Propagation
    - level: source_url
      url: https://uptrace.dev/get/opentelemetry-js/propagation
      title: OpenTelemetry Trace Context Propagation [JavaScript] - Uptrace
    - level: source_url
      url: https://opentelemetry.io/docs/concepts/context-propagation/
      title: Context propagation - OpenTelemetry
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-02-opentelemetry-context-propagation/view
      title: How to Use OpenTelemetry Context Propagation - OneUptime
relations:
  - target: wiki/concepts/distributed-tracing.md
    type: related
  - target: wiki/concepts/w3c-tracecontext.md
    type: related
  - target: wiki/concepts/opentelemetry-propagators.md
    type: related
---

# OpenTelemetry W3C Context Propagation

## Decision context

**Definition:** A technique defined by the W3C TraceContext specification that enables OpenTelemetry to carry trace context across service boundaries, distributed systems, and process boundaries, supporting end-to-end request tracing and correlation.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *Transcripts and Logs of AI Coding Sessions*, clustered into the "https-opentelemetry-propagation" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The W3C TraceContext specification standardizes the format for propagating trace context across different services and systems
- Propagators handle the injection of context into carriers (such as HTTP headers) and extraction of context from incoming requests
- Context propagation enables correlation of individual spans into a complete distributed trace across multiple services
- The approach supports tracing across Node.js child processes by propagating context through inter-process communication boundaries
- JavaScript implementations provide language-specific APIs for configuring and using context propagation in applications
- Multiple propagation formats exist beyond W3C TraceContext, including B3 and others, though W3C TraceContext serves as the standard approach

## Related concepts

- distributed-tracing — Distributed Tracing
- w3c-tracecontext — W3C TraceContext
- opentelemetry-propagators — OpenTelemetry Propagators
- trace-context — Trace Context
- span-correlation — Span Correlation

## Citations (from contributing transcripts)

- **Claim:** W3C TraceContext is a standard for context propagation in OpenTelemetry
  - Source: How to Build OpenTelemetry W3C Context Propagation - OneUptime (`5c17afac-b5eb-4974-9b25-4d5678b8b110`)
  - Context: How to Build OpenTelemetry W3C Context Propagation
- **Claim:** Context propagation enables distributed tracing across service boundaries
  - Source: Context propagation - OpenTelemetry (`d34a7963-9276-426c-bbe4-bf7862c30e42`)
  - Context: Context propagation | OpenTelemetry
- **Claim:** JavaScript-specific implementations cover context propagation approaches
  - Source: OpenTelemetry Trace Context Propagation [JavaScript] - Uptrace (`bdc503cc-fd58-472a-9205-7b12465b494c`)
  - Context: OpenTelemetry Trace Context Propagation [JavaScript]
- **Claim:** Context propagation supports tracing across child processes in Node.js
  - Source: How to Trace Node.js Child Processes with OpenTelemetry Context Propagation (`87bb58a6-775c-4f3c-96d6-cc8e47fce358`)
  - Context: How to Trace Node.js Child Processes with OpenTelemetry Context Propagation

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `83d187f3-8f8a-4fbe-af21-2b1840c87960`
(cluster `https-opentelemetry-propagation`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Transcripts and Logs of AI Coding Sessions](https://notebooklm.google.com/notebook/83d187f3-8f8a-4fbe-af21-2b1840c87960)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
