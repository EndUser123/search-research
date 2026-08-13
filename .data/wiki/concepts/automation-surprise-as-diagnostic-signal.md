---
title: "Automation Surprise as a Diagnostic Signal"
date: 2026-08-13
tags: [adaptive-automation, hooks, trust-calibration, diagnostic-framing]
host: both
confidence: INFERENCE
source_quality: single-source
---

# Automation Surprise as a Diagnostic Signal

## Context

Derived from session 019ffb95 /tp improve analysis and the
[[adaptive-automation-landscape-for-llm-agent-orchestration]] research.
The modern adaptive automation literature (Bernabei 2024) identifies
"automation surprise" as a key concept: mismatch between expected and
observed system behavior.

## The reframing

In this workspace, hooks fire and the agent didn't expect them. The
current default posture treats these as friction to suppress — the agent
works around the hook or the operator disables it.

The adaptive automation literature suggests a different framing: **an
automation surprise is a trust calibration signal.** The agent's model of
the system was wrong, and the hook detected it. That mismatch is
information — not noise.

## What this means concretely

When a hook fires unexpectedly:
1. The agent's model of what would happen was incorrect
2. The hook is the system working as designed (detecting the mismatch)
3. Suppressing the hook removes the signal without fixing the model

Instead: log the surprise, examine whether the agent's model needs
updating, and decide whether the hook threshold is right.

## Relationship to existing concepts

- [[value-conditional-automation-escalation]] — the pattern for deciding
  when to escalate automation. Automation surprises are the feedback
  signal that calibrates those decisions.
- [[advisory-vs-blocking-enforcement-decision-2026]] — measurement-first
  graduated enforcement. Automation surprises are the measurements.
- [[adaptive-automation-landscape-for-llm-agent-orchestration]] — the
  research landscape that introduced the term.

## Status

[INFERENCE] — derived from research, not yet operationalized in the
workspace. Needs a concrete implementation (hook logging, surprise
detection, calibration feedback loop) before it can be promoted to
SUPPORTED.
