---
title: "Hook regex false positives on pasted terminal output: the skill-precheck incident"
concept_type: "failure-mode"
created: 2026-08-05
source: session-019fcd47 (skill-precheck hook fired exit 1 on pasted Codex CLI output)
tags: [hook-design, false-positive, regex-scope, skill-precheck, terminal-output, predictable-failure, transferable-pattern]
agent: grok
host: both
cognitive_load: 1
verification: session-verified
summary: >
  A UserPromptSubmit hook that detects /skill-name invocations via regex
  matched /word patterns in pasted terminal output from other CLIs (Codex,
  Claude, Grok Build TUI). When the operator pasted Codex's banner containing
  "/model to change" and "Use /skills to list available skills," the hook
  treated /model, /skills, and /usage as Grok skill invocations, found they
  didn't exist, and fired critical warnings with exit 1. This is a
  predictable failure: any regex that matches command patterns in free text
  will match those same patterns in quoted/pasted output. The fix
  (detect terminal-output markers and skip) is a heuristic, not a structural
  solution. This incident is a case study in the broader pattern: hooks
  that pattern-match user input must account for non-command text that
  contains command-like patterns.
relations:
  - target: wiki/concepts/scanner-regex-scope-discipline
    type: extends
  - target: wiki/concepts/llm-judgment-hooks
    type: related
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity
    type: related
---

# Hook regex false positives on pasted terminal output

## The incident

The skill-precheck hook (`UserPromptSubmit_skill_precheck.py`) detects
`/<skill-name>` patterns in the user's prompt to warn about missing skills,
stale SKILL.md files, or missing dependencies. Its regex is:

```python
SKILL_INVOCATION_RE = re.compile(r"(?:^|\s)/([a-z][a-z0-9-]{1,40})\b", re.MULTILINE)
```

When the operator pasted Codex CLI output containing:

```
╭─────────────────────────────────────────────────────╮
│ model:       gpt-5.6-luna medium   /model to change │
│                                                     │
│ Use /skills to list available skills                │
╰─────────────────────────────────────────────────────╯
```

The regex matched `/model`, `/skills`, and `/usage` — none of which are
Grok skills. The hook fired three critical "Skill not found" warnings
and exited 1, blocking the prompt.

## Why this was predictable

The operator was right: this should never have passed initial coding.
The failure mode is inherent in the design:

1. **The regex matches /word in ANY text** — it has no context awareness.
   It cannot distinguish `/tp` as the first word of a command from
   `/model` buried in pasted output.

2. **The workspace has multiple CLIs** (Codex, Claude, Grok Build TUI,
   agy, mmx) that all use `/command` syntax in their output. Pasting
   their output into a prompt is a common operator workflow.

3. **UserPromptSubmit fires on EVERY prompt** — there's no scope
   limitation to "prompts that look like commands."

## Why it wasn't caught

The hook was tested against:
- Prompts with real skill invocations (`/go fix this`) → worked
- Prompts with no skill invocations (`fix this bug`) → worked (fast path)
- Prompts with Windows paths (`P:/tmp/foo`) → worked (path exclusion)

But it was NOT tested against:
- Prompts containing pasted terminal output with `/word` patterns
- Prompts containing code examples with `/command` syntax
- Prompts containing documentation quoting CLI usage

This is a test coverage gap: the test cases covered the intended use
pattern but not the adversarial/non-command patterns that contain
the same syntactic structure.

## The fix (heuristic, not structural)

Detect terminal-output markers and skip skill detection:

```python
TERMINAL_OUTPUT_MARKERS = (
    "│", "╭", "╰", "─",  # box-drawing borders
    "›", ">_",            # CLI prompt markers
    "◆", "✓", "✗",       # Grok Build hook output markers
)
if any(marker in prompt_text for marker in TERMINAL_OUTPUT_MARKERS):
    sys.exit(0)  # Pasted terminal output — skip skill detection
```

**Why this is a heuristic, not a structural fix:** the operator could
paste terminal output without box-drawing characters (plain text log),
or could invoke a real skill in a prompt that also contains box-drawing
characters (unlikely but possible). The heuristic covers the observed
failure mode but doesn't solve the general problem.

## The general problem

Any hook that pattern-matches user input faces the **quoted-command
problem**: the same syntax that indicates a real command also appears
in quoted commands, documentation, code examples, and pasted output.
Distinguishing them requires either:

1. **Syntactic context** (is the /word at the start of a line, or
   buried in other text?) — fragile, easily defeated
2. **Semantic understanding** (does this /word mean "invoke this skill"
   or "discuss this command"?) — requires LLM judgment, not regex
3. **Structural separation** (the platform distinguishes commands from
   content) — requires platform support, not available on Grok Build

This is the same problem as email filtering: a regex that catches spam
also catches legitimate emails that quote spam. The general solution is
LLM-based classification (see [[llm-judgment-hooks]]), but that adds
latency to every prompt.

## Design lesson

When building hooks that pattern-match user input:

1. **Enumerate non-command contexts** that contain command-like patterns:
   pasted output, code examples, documentation quotes, error messages.
2. **Test against those contexts** before shipping.
3. **Prefer exclusion heuristics** (detect and skip non-command text)
   over inclusion regexes (try to match only real commands).
4. **Accept that regex-based detection is Layer 1** — it will have
   false positives and false negatives. Design for graceful degradation,
   not perfection.

## Cross-references

- [[scanner-regex-scope-discipline]] — the same principle applied to scanner
  output validation: scope regex to the data field, not the full input
- [[llm-judgment-hooks]] — the two-layer regex+LLM pattern that handles
  ambiguous cases regex alone cannot
- [[multi-terminal-isolation-stale-data-immunity]] — the broader context
  of hook safety on this multi-agent host
