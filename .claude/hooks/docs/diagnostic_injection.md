# Diagnostic Injection System

**Version:** 1.1.0
**Added:** 2025-01-19
**Updated:** 2026-01-19 (hedging word expansion)
**Purpose:** Prevent lazy explanations for diagnostic questions

---

## Problem Solved

Claude Code was answering "why" and "how" questions with speculation from training data instead of investigating the actual system state.

Example failure:
```
User: "Why doesn't the hook catch this?"
CC: "Likely because the task system categorizes these as test operations..."
```

This is speculation without evidence.

## Solution: Injection + Enforcement

**Two-part mechanism:**

1. **UserPromptSubmit (injection):** Detects diagnostic questions → injects "investigate first" requirement → writes state file
2. **Stop (enforcement):** Checks if state file exists → blocks response if no investigation tools were used

## Architecture

```
UserPromptSubmit_router.py
├── is_diagnostic_question(prompt) → bool
├── _write_diagnostic_state(prompt) → writes session_data/diagnostic_injection.json
└── run_diagnostic_injection() → returns injection text or None

empirical_claims_gate.py
├── check_diagnostic_compliance(tools) → dict|None
│   ├── Reads diagnostic_injection.json
│   ├── Checks if investigation tools (Read, Bash, Grep, Glob) were used
│   └── Returns violation dict if injection fired but no tools used
└── main() → calls check_diagnostic_compliance() FIRST
```

## Diagnostic Patterns

Questions matching these patterns trigger the injection:

### Explicit Diagnostic Patterns (regex)
- `why is|does|did|are|was...`
- `how does|did|is|are|do...`
- `what causes|caused|triggers|happens...`
- `explain why|how|what`
- `diagnose|diagnostic|debugging`
- `root cause|what went wrong`
- `debug|troubleshoot|investigate`
- `why...fail|error|broken|not work`

### Hedging + Problem Patterns (keyword-based)
Catches word order variations like "seems like broken" or "might actually be failing":

**Hedging words:** `seems, appears, probably, possibly, likely, maybe, perhaps, might, could, looks, sounds, feels`

**Problem states:** `broken, wrong, error, fail, failing, failed, problem, issue, bug, off, incorrect, bad`

**Positive exclusions** (prevents false positives): `right, correct, fine, good, ok, properly, working`

**Examples that trigger:**
- "seems broken" / "seems like it's broken"
- "might be failing" / "could be wrong"
- "appears to have a problem"

**Examples that DON'T trigger:**
- "probably the correct solution" (positive word)
- "seems like the right approach" (positive word)

## Investigation Tools

These tools satisfy the investigation requirement:

- `Read` - file contents
- `Bash` - command execution
- `Grep` - text search
- `Glob` - file listing
- `list_directory` - directory contents
- `WebFetch` - external content

## Configuration

```json
// settings.json
{
  "DIAGNOSTIC_INJECTION_ENABLED": "true"
}
```

## State File

Location: `P:/.claude/hooks/session_data/diagnostic_injection.json`

```json
{
  "injection_fired": true,
  "prompt_snippet": "Why does the hook fail...",
  "timestamp": 1768799988.62
}
```

- Created by UserPromptSubmit when diagnostic question detected
- Read and deleted by Stop hook during compliance check
- 60-second TTL (stale state ignored)

## Test Results

| Scenario | Expected | Actual |
|----------|----------|--------|
| Diagnostic + no tools | BLOCKED | ✓ BLOCKED |
| Diagnostic + Read/Bash used | ALLOWED | ✓ ALLOWED |
| Non-diagnostic question | No injection | ✓ No injection |

## False Positive Handling

False positives (injecting on casual "how" questions) are harmless:
- The injection just says "use tools if you need them"
- Stop hook only enforces if injection actually fired
- Non-diagnostic questions don't create state file

## Related

- `empirical_claims_gate.py` - main enforcement hook
- `CLAUDE.md C.3` - truth verification requirements
- `constraints.md` - excuse pattern definitions
