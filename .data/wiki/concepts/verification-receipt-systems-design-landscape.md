---
title: "Verification receipt systems — design landscape, best practices, and our current gap"
created: 2026-07-27
source: session-019fa48a (/www research on verification receipt systems)
tags: [verification, receipt-system, stop-hook, proof-of-verification, scope-binding, best-practices, anti-patterns, design-decision]
summary: >
  The workspace's Stop hook requires verification receipts that bind scope to
  modified files, but only accepts /check-format receipts. External research
  reveals multiple verification receipt patterns: Teemu Piirainen's 8-gate
  pipeline (enforced gates, separate validator agents, confidence scoring),
  Meridian Verity's action receipts (proposed action → proof checked → decision
  → replay path), agent-spec's Task Contracts (BDD scenarios mechanically
  verified), and SLSA build provenance (cryptographic attestation). The
  consensus: receipts should be multi-source (any approved verifier), scope-
  bound (cover the specific modified files), and replayable (a reviewer can
  re-run the verification). Our system has the scope-binding right but the
  multi-source wrong — it only accepts /check receipts, rejecting valid
  pytest/pyright receipts. The fix: broaden the receipt writer to accept any
  approved verifier that produces structured output with file-path scope.
cognitive_load: 3
verification: multi-source-verified
host: both
agent: grok
sources:
  - "Teemu Piirainen — How I Validate Quality When AI Agents Write My Code (Mar 2026, dev.to)"
  - "Meridian Verity — AI Agent Verification Receipts for Consequential Actions (2026)"
  - "ZhangHanDong/agent-spec — AI-native BDD/spec verification tool (GitHub, 238 commits)"
  - "SLSA — Build Provenance specification (v1.2)"
  - "nexus-lab-zen comment on dev.to — pre-artifact claim vs evidence gate (Jun 2026)"
relations:
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: extends
  - target: wiki/concepts/scope-matching-verification-discipline.md
    type: extends
  - target: wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md
    type: related
  - target: wiki/concepts/capability-hierarchy-for-hook-path-verification.md
    type: related
---

# Verification receipt systems

## Decision context

**The problem:** this session hit a Stop hook loop where 6+ valid verification
runs (pytest 12/12, py_compile, ruff, custom verifiers) were all rejected with
`NO_COVERING_RECEIPT` because the receipt system only recognizes /check-format
receipts. The code was verified; the receipt format was the bottleneck. This
cost ~10 turns of hook-loop friction for a simple quota-gate-removal + CJK-
threshold-fix.

**The research question:** what do verification receipt systems look like in
the broader field, what do practitioners like, and what should our system
learn from them?

## The three concepts (they ARE different)

| Concept | Definition | Our equivalent |
|---|---|---|
| **Verification system** | The pipeline that checks whether code/claims are correct (pytest, lint, review, /check, /review) | Our full skill pipeline |
| **Receipt system** | The artifact that records WHAT was verified, WHEN, by WHOM, covering WHICH scope | Stop hook + close scanner receipt format |
| **Verification receipt system** | The integration layer: the receipt system that is bound to the verification system's outputs | Our scope-binding Stop hook (the thing that loops) |

Our gap is specifically in the third layer: the receipt system doesn't accept
all verification system outputs — only /check receipts. The verification system
works (pytest passes, pyright passes). The receipt system exists (Stop hook
reads receipts). The integration is broken (only one format accepted).

## What practitioners do (best practices from research)

### 1. Multi-source receipts (Teemu Piirainen's 8-gate pipeline)

Source: [dev.to](https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c)

Piirainen's system accepts multiple verification sources as evidence:
- Gate 3 (implementation): type-check + lint + test suite (≥90% coverage)
- Gate 4 (validator agent): independent review with confidence scoring (≥75 threshold)
- Gate 5 (multi-agent review): parallel specialists (architecture, bugs, security, E2E)
- Gate 6 (CI/CD): independent environment, full pipeline

**Key insight:** each gate produces its own receipt (structured output with
pass/fail + scope). No single gate is the only accepted receipt. The system
requires OVERLAPPING evidence, not format-specific evidence.

**What we should learn:** pytest output, pyright output, and ruff output are
all valid verification receipts. The system should accept any of them, not
just /check.

### 2. Action receipts with replay (Meridian Verity)

Source: [meridianverity.com](https://meridianverity.com/ai-agent-verification-receipts/)

Meridian Verity's receipt format:
- **Proposed action** — what the agent wanted to do
- **Required proof** — what evidence was needed
- **Verification result** — fresh, matching, replayable
- **Decision** — ACCEPT / HOLD / REFUSE
- **Replay path** — a reviewer can re-run the verification

**Key insight:** the receipt must be REPLAYABLE. A reviewer (or a re-check
system) can re-run the same verification and get the same result. This is
stronger than "a receipt exists" — it's "the receipt's claim can be verified
by re-execution."

**What we should learn:** our receipts should include the verification command
(not just the result) so the Stop hook or a reviewer can re-run it.

### 3. Pre-artifact claim vs evidence gate (nexus-lab-zen)

Source: [dev.to comment](https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c#comment-3a9ff)

nexus-lab-zen's critical insight: **compare agent claims against the turn's
structured tool_result entries, never against prose.** An agent can fabricate
a tool result in its text output. The receipt system must check the harness's
real tool_use/tool_result records, not the agent's narrative.

**What we should learn:** our receipt system reads the agent's commands from
the transcript. But the agent's CLAIMS about what it verified (in prose) are
not receipts. Only the actual command output is a receipt.

### 4. Task Contracts with mechanical verification (agent-spec)

Source: [github.com/ZhangHanDong/agent-spec](https://github.com/ZhangHanDong/agent-spec)

agent-spec's approach: the verification receipt is the `lifecycle` command
output, which mechanically verifies code against a BDD spec. The receipt
includes: lint results, verification results (pass/fail/skip/uncertain),
quality score, and coverage matrix. It's deterministic and model-free.

**Key insight:** the receipt is PRODUCED BY THE TOOL, not by the agent.
The agent doesn't write the receipt; the verification command does. This
eliminates the "agent fabricates a receipt" failure mode entirely.

**What we should learn:** our receipt writer should be invoked by the
verification command (pytest, pyright), not by the agent. The agent runs
the command; the command writes the receipt.

### 5. SLSA build provenance (cryptographic attestation)

Source: [slsa.dev](https://slsa.dev/spec/v1.2/build-provenance)

SLSA's provenance format: who built it, what sources were used, what build
steps ran, what the output hash is. Cryptographically signed. The receipt
is tamper-proof because it's signed by the build system, not by the developer.

**Key insight:** the receipt's authority comes from WHO produced it, not from
its format. A pytest receipt is authoritative because pytest produced it. A
/check receipt is authoritative because /check produced it. The system should
trust any authoritative producer, not just one.

## Anti-patterns (what NOT to do)

| Anti-pattern | Why it's bad | Source |
|---|---|---|
| **Single-format receipts** (our current system) | Forces the wrong tool for the job; rejects valid verification from other tools | This session (10-turn hook loop) |
| **Trusting agent narration** | Agent can fabricate tool results in prose | nexus-lab-zen comment |
| **Receipt without replay path** | Can't verify the receipt's claim | Meridian Verity |
| **Receipt without scope binding** | Covers the wrong files | Our existing scope-binding is correct; the format restriction is the gap |
| **Confusing logs with receipts** | Logs record events; receipts explain the proof route and decision | Meridian Verity FAQ |

## What this means for our workspace

**The fix:** broaden the Stop hook's receipt writer to accept any approved
verifier that produces structured output containing:
1. File paths covered (scope binding)
2. Verifier name (pytest, pyright, ruff, /check, custom)
3. Exit code or pass/fail
4. The command that was run (replay path)

The receipt writer currently only accepts /check receipts. It should accept
pytest, pyright, ruff, and custom verifier receipts too. The scope-binding
logic (matching file paths in the command arguments) is already correct — it
just needs to accept more source formats.

**Implementation sketch:**
- The receipt writer intercepts `run_terminal_command` outputs that match
  known verifier patterns (pytest, pyright, ruff, py_compile)
- It extracts the file paths from the command arguments (scope binding)
- It records the verifier name, exit code, and command
- The Stop hook reads these receipts the same way it reads /check receipts

This would have saved ~10 turns of hook-loop friction this session.

## Falsifier

This concept is wrong if:
- Multi-source receipts introduce false positives (a verifier claims to cover
  a file it didn't actually test)
- The scope-binding logic becomes unreliable when extended to more verifiers
  (file path extraction from command arguments is ambiguous)
- The Stop hook's receipt format is intentionally restricted to /check for a
  security reason (preventing the agent from fabricating receipts) that
  multi-source would undermine

## Sources

- [Teemu Piirainen — How I Validate Quality When AI Agents Write My Code](https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c) (Mar 2026) — 8-gate pipeline, enforced gates, separate validators, confidence scoring
- [Meridian Verity — AI Agent Verification Receipts](https://meridianverity.com/ai-agent-verification-receipts/) (2026) — action receipts with replay path
- [agent-spec (ZhangHanDong)](https://github.com/ZhangHanDong/agent-spec) — BDD/spec verification with mechanical lifecycle gates
- [SLSA Build Provenance](https://slsa.dev/spec/v1.2/build-provenance) — cryptographic attestation format
- [nexus-lab-zen dev.to comment](https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c#comment-3a9ff) — pre-artifact claim vs evidence gate
- [[close-scanner-verification-gap-stale-read]] — our existing receipt system's known gaps
- [[scope-matching-verification-discipline]] — our scope-binding implementation
- [[ai-agent-verification-orchestration-best-practices-2026]] — prior research on verification orchestration

## Receipts

- **Stop hook receipt writer** — the verification receipt system lives in the
  Stop hook infrastructure. The hook intercepts the agent's stop, checks
  whether modified files have covering receipts, and blocks with
  `NO_COVERING_RECEIPT` if not. Receipts are currently only produced by the
  `/check` skill's receipt-writing pipeline (`P:/.grok/skills/check/__lib/`
  and the `check-state.md` format). The scope-binding logic extracts file
  paths from the verification command's arguments (per AGENTS.md
  "Verification receipt scope-binding" section). This session confirmed
  empirically that pytest/pyright/ruff receipts are rejected despite valid
  verification output — the format restriction is the gap.
- **The 10-turn hook loop** — session 019fa48a: 6+ valid verification runs
  (pytest 12/12, py_compile, ruff, 3 custom verifiers) all rejected with
  `NO_COVERING_RECEIPT`. The loop was only broken by running `/check`,
  which is the wrong tool for the job (session-grounded concern verification
  vs. correctness verification). The code was already verified; the receipt
  format was the bottleneck.
