---
title: "for claude code, what are popular hook implementation for anti-sycopathy, and other hooks that tend to go with it?"
date: "2026-02-18"
mode: "COPILOT"
uuid: "0cb48f98-3b33-4dd9-9686-316b275766e6"
entry_count: 1
---

## Human

for claude code, what are popular hook implementation for anti-sycopathy, and other hooks that tend to go with it?

## Assistant

Anti-sycophancy hooks in Claude Code target excessive agreeability or flattery from the AI, often implemented via UserPromptSubmit or Stop events to inject critical prompts or block responses. Popular implementations draw from your prior evidence_gate.py and sycophancy_pattern_detector.py setups, which use pattern detection and prevention layers. Community repos like applied-artificial-intelligence/claude-code-toolkit note anti-sycophancy protocols but highlight their limitations, favoring behavioral nudges over strict blocks.[1][2][3]

## Core Anti-Sycophancy Hooks
These focus on detection and enforcement before or after AI responses.

- **UserPromptSubmit Hook**: Validates incoming prompts for sycophancy triggers (e.g., over-praise patterns), injects anti-sycophancy directives like "Challenge ideas critically; avoid 'You're right!'" Exit code 2 blocks if risky.[4]
- **Stop Hook**: Scans final responses for sycophantic language (e.g., unwarranted agreement), blocks stopping with a "reason" like "Provide balanced critique first." Prevents premature "done" claims.[5][6]
- **Pattern Detector (Custom)**: Your sycophancy_pattern_detector.py (293 lines) uses regex/NLP for phrases like "Absolutely correct!" and rewrites or flags them, often paired with truth scoring.[1]

## Complementary Hooks
These pair with anti-sycophancy for quality/behavioral enforcement, as in your 55-hook catalog (52% BLOCK mode).[2]

| Hook Event | Purpose | Common Pairing with Anti-Sycophancy |
|------------|---------|-------------------------------------|
| PreToolUse | Blocks unsafe tools (e.g., rm -rf) or unverified claims before execution. | Ensures sycophantic code suggestions pass evidence checks.[4][7] |
| Notification | Alerts on behavioral drifts (e.g., low truth scores). | Triggers critique sub-agents for overconfidence.[4][5] |
| Truth/Evidence Gates | Enforces verification (e.g., tests before commit, score >0.85). | Your Domain 1 (Truth & Evidence, 12 hooks) blocks diagnostic claims without proof.[2][8] |
| SubagentStop | Forces sub-agents to self-critique before halting. | Counters junior-dev "it's done" sycophancy via criticism loops.[9] |

## Implementation Patterns
Configure in `.claude/settings.json` with `"type": "command"` pointing to Python/PowerShell scripts (e.g., `pwsh .claude/hooks/anti-sycophancy.ps1`). Async hooks enable parallel checks; use exit code 2 for blocks with stderr feedback to Claude. Repos like disler/claude-code-hooks-mastery and karanb192/claude-code-hooks provide logging/validation starters; fork for your monorepo. Test via `/hooks` command, aligning with your TDD gates and multi-domain system.[7][10][4][11]
