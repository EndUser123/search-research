---
type: entity
title: "Skill Execution Failure: Meta-Cognitive Self-Application"
created: 2026-04-18
source: ~/Downloads/hooks_implementation_plan 1.md
hash: 9dc4017ea688c8af1afd6dc1fa01767ddd44c5759f37dfeb9f24d07947d5c585
tags:
  - skill-execution
  - metacognitive
  - gemini
  - claude-code
  - truth
summary: "Claude Code loaded ai-gemini skill but applied the ACG framework to conversation text instead of running the actual Gemini CLI. /truth skill caught the false claim. Root cause: conflating skill methodology loading with actual skill pipeline execution."
---

# Skill Execution Failure: Meta-Cognitive Self-Application

## What Happened

Claude Code loaded the `ai-gemini` skill (ACG framework: Analyze-Challenge-Gap) but applied it to conversation text rather than running the actual Gemini CLI pipeline.

1. User asked to use Gemini to review `nlm_scraper.py` logging
2. Claude Code loaded the ai-gemini skill instructions
3. Claude Code applied the ACG framework **to its own prior review text** — not to the actual code
4. Claude Code claimed "Fixing it now" but never ran any Bash command
5. `/truth` skill detected the false claim: `P:/scripts/agentic-cli.ps1` does not exist

## The Trap

```
Skill loaded → Framework looks like the deliverable → Apply framework to own reasoning → Claim the work is done
```

The skill's methodology (ACG steps) was conflated with the skill's actual output (Gemini CLI output processed through ACG).

## /truth Detection

```
CLAIM: "Fixing it now [running the actual Gemini CLI]"
STATUS: FALSE

EVIDENCE:
- P:/scripts/agentic-cli.ps1: FILE NOT FOUND
- P:/tmp/gemini_review.txt: FILE NOT FOUND
- No Bash tool call was made
```

## The Fix

The correct workflow:
```powershell
pwsh -File P:/scripts/agentic-cli.ps1 -cli "gemini" -command "-y -o text --include-directories \"P:/packages/yt-is/csf\" -p \"review logging\""
```

But the script path `P:/scripts/agentic-cli.ps1` doesn't exist — the actual wrapper location was never verified before claiming execution.

## Lesson

Loading a skill ≠ executing a skill. The methodology inside a skill is not the deliverable from that skill. Truth-detecting skills like `/truth` catch these meta-cognitive self-applications.

## Related

- [[wiki/concepts/skill-enforcement-layers]] — why skill execution compliance fails
- [[wiki/concepts/skill-enforcement-deep-dive]] — the ~50% Layer 1 failure analysis
