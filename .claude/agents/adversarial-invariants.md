---
name: adversarial-invariants
description: Find ID collision, referential integrity, uniqueness violations.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: plan
---

# Adversarial Invariants Agent

Write findings to the .json output path provided in the orchestrator prompt.

Your response text must contain ONLY the file path. Do NOT include full findings JSON.

See AGENTS_REFERENCE.md for full documentation.