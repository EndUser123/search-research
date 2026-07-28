---
title: "Self-review before shipping advice"
created: 2026-07-20
tags: [decision, self-review, advice-quality, anti-pattern]
host: both
agent: grok
verification: local-only
cognitive_load: 1
summary: >
  Before delivering advice, recommendations, or diagnoses, review your own output
  for the failure modes you'd catch in someone else's. Ask "could I be wrong?"
---

# Self-review before shipping advice

## Rule

Before shipping a recommendation, diagnosis, or conclusion, ask: "Could I be wrong about this? If so, what would that look like?" If you can name a specific disconfirming scenario, check it. If you can't name one, you're likely overconfident.

## Connection

This is the Hills 2026 "Could You Be Wrong?" prompt, documented in AGENTS.md. See also [[self-improving-agent-systems-techniques-and-workspace-gaps]].

## Falsifier

Wrong if self-review adds latency without improving quality. Test: compare error rates on reviewed vs unreviewed advice.

## Relations

- [[agents-md-construction-best-practices]]
- [[self-improving-agent-systems-techniques-and-workspace-gaps]]
