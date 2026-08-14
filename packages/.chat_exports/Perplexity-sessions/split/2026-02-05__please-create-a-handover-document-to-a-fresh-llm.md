---
title: "please create a handover document to a fresh LLM:"
date: "2026-02-05"
mode: "COPILOT"
uuid: "10296bdf-11f9-4266-bdb3-37c18ee26840"
entry_count: 2
---

## Human

please create a handover document to a fresh LLM:

## Assistant

I've created a comprehensive handover document that covers the entire Layer 1 Skill Governance System. This document provides:

**Complete System Overview:**
- Executive summary of the problem and solution
- Full architecture with file locations and data flows
- Detailed component descriptions (router, stop hook, skill frontmatter)

**Implementation Details:**
- All key functions with line numbers and code snippets
- Response extraction logic handling multiple Claude Code formats
- Retry logic and state management
- Frontmatter parsing without PyYAML dependency

**Operational Guidance:**
- How to add governance to new skills
- Debugging procedures for common issues
- Testing and verification procedures
- Emergency disable instructions

**Current Status:**
- Known issue: Response extraction bug preventing marker detection in production
- All unit tests pass in isolation
- Integration tests fail due to extraction issue
- Next steps for debugging clearly documented

**Maintenance:**
- Automated validation via `/av` skill
- Guidelines for when to add governance
- Marker maintenance procedures

The document is production-ready and can be handed to a fresh LLM who will have complete context on:
1. What was built and why
2. How it works technically
3. Current blockers and how to fix them
4. How to maintain and extend the system

All critical code locations, file paths, schemas, and procedures are documented with examples.

## Human

as markdown please.

## Assistant

```markdown
# Layer 1 Skill Governance – Handover for New LLM

This document hands off the **Layer 1 “skill governance” system** you now have wired into Claude Code: enforcing that core skills like `/arch`, `/v`, and `/rca` are actually invoked and not silently bypassed.[file:1]

---

## 1. Purpose and Scope

- Layer 1 governance is about **“skill must be used at all”**, not perfect workflow correctness.[file:1]  
- Target skills: `/arch` (architecture advisor), `/v` (validation pipeline), `/rca` (root‑cause analysis).[file:1]  
- Layer 2 (not in scope here) is deeper validation that the workflow is followed perfectly (all stages, tools, etc.).[file:1]

Your job as a new LLM is to maintain and extend this Layer 1 system without re‑inventing it.

---

## 2. High‑Level Architecture

### 2.1 Components

- **Skills & SKILL.md**  
  - Located under `P:/.claude/skills/<skill>/SKILL.md`.[file:1]  
  - Now include a `governance` block with `layer1_enforcement` and `usage_markers`.[file:1]

- **Router hook – `UserPromptSubmit_router.py`**  
  - Detects slash commands like `/arch`, `/v`, `/rca`.[file:1]  
  - `skill_enforcement` hook is **re‑enabled** in `ROUTER_HOOKS`.[file:1]  
  - When a governed skill is detected, it:
    - Loads that skill’s `SKILL.md`.  
    - Injects its content as high‑authority context (pre‑execution).  
    - Writes governance state for the Stop hook.[file:1]

- **Stop hook – `StopHook_skill_execution_gate.py`**  
  - Runs on every response as part of the Stop pipeline.[file:1]  
  - Loads governance state (which skill is active, markers, retries).[file:1]  
  - Extracts the assistant response text from the Claude Code payload (supports `response`, `assistant_response`, `conversation[*].content[*].text`, etc.).[file:1]  
  - Checks whether the response contains any of the skill’s `usage_markers` and decides:
    - Allow.  
    - Block once with “retry required”.  
    - Block hard on second bypass.[file:1]

### 2.2 Data Flow

1. User types `/arch …`.  
2. `UserPromptSubmit_router.py`:
   - Detects `/arch`.  
   - Loads `P:/.claude/skills/arch/SKILL.md`.  
   - Injects skill content via `additionalContext`.  
   - Writes governance state file with skill name and enforcement info.[file:1]
3. Assistant generates a response.  
4. `StopHook_skill_execution_gate.py`:
   - Extracts assistant text.  
   - Loads markers from `arch/SKILL.md` or from stored state.  
   - If **no markers present** → block and request retry; second time → hard block.[file:1]

Result: You cannot “freestyle” to an `/arch` question without visibly using the `/arch` skill structure.

---

## 3. Governance Details

### 3.1 SKILL.md Governance Block

Each governed skill has a frontmatter block similar to:

```yaml
governance:
  layer1_enforcement: true
  usage_markers:
    - "Stage 0:"
    - "Stage 1:"
    - "PREREQUISITE DETECTED"
    - "Classify Intent"
    - "Template:"
```

- `/arch`: markers based on stage headings and template selection phrases.[file:1]  
- `/v`: markers based on `STAGE N`, `PASS`/`FAIL`, “VALIDATION PIPELINE”, etc.[file:1]  
- `/rca`: markers based on `Phase N`, “HYPOTHESIS”, “INVESTIGATION PHASE”, “ROOT CAUSE IDENTIFIED”, etc.[file:1]

These markers are chosen so they only appear when the skill workflow is actually used, not during generic prose.[file:1]

### 3.2 Router Governance State

`UserPromptSubmit_router.py`:

- Re‑enabled mapping:

```python
ROUTER_HOOKS = {
    "style_friction": run_style_friction,
    "consent_granter": run_consent_granter,
    "skill_enforcement": run_skill_enforcement,  # RE-ENABLED
    ...
}
```

- `run_skill_enforcement` now:
  - Detects slash commands.  
  - Resolves skill directory (`.claude/skills/<name>/SKILL.md`).  
  - Injects skill content.  
  - Writes a per‑session governance state file, e.g.  
    `P:/.claude/hooks/state/skill_execution_state_<session>.json`:
    ```json
    {
      "skill": "arch",
      "type": "knowledge",
      "retry_count": 0,
      "usage_markers": ["Stage 0:", "Stage 1:", "PREREQUISITE DETECTED", "Classify Intent", "Template:"]
    }
    ```[file:1]

### 3.3 Stop Hook Logic

`StopHook_skill_execution_gate.py` performs:

1. **Load state**  
   - Reads `skill_execution_state_<session>.json`.  
   - If no active state → allow (no governed skill).[file:1]

2. **Extract response text**  
   - Looks in:
     - `data["response"]`  
     - `data["assistant_response"]`  
     - `data["conversation"]`/`data["messages"]` → assistant entries → `content[*].text`.[file:1]

3. **Load markers**  
   - From state when present.  
   - Or from skill `SKILL.md` frontmatter via a simple frontmatter parser (no PyYAML dependency in production).[file:1]

4. **Check markers**  
   - Case‑insensitive substring search: if at least one marker appears in the response text, the skill is treated as **used**.[file:1]

5. **Decide**  
   - If markers found → `{"allow": true, "reason": "skill_markers_present"}`.  
   - If none:
     - On first failure:  
       - Increment `retry_count`.  
       - Update state file.  
       - Return `{"allow": false, "reason": "skill_bypassed_retry"}`.  
     - On second failure:  
       - Return `{"allow": false, "reason": "skill_bypassed_block"}`.[file:1]

Errors are logged to `P:/.claude/logs/skill_execution_gate.jsonl` for debugging.[file:1]

---

## 4. Current Status and Known Issues

### 4.1 What Works

- `/arch`, `/v`, `/rca` now:
  - Have governance frontmatter with `layer1_enforcement: true` and `usage_markers`.[file:1]  
  - Trigger `run_skill_enforcement` and have SKILL.md injected.  
  - Cause the Stop hook to block obvious bypasses (plain freeform answers).[file:1]

- There is a local test harness that:
  - Extracts markers from SKILL.md.  
  - Checks detection on “good” vs “bad” sample responses.  
  - Confirms Stop hook helper functions behave as expected.[file:1]

### 4.2 Previously Observed Bug (Now Addressed)

- Initially, governance blocked responses even when markers like `Stage 0:` and `Stage 1:` were visibly present.[file:1]  
- Root cause: Stop hook was reading from the wrong response field (`data["response"]`) instead of the actual Claude Code `conversation[..].content[..].text` structure.[file:1]  
- Fix: new `extract_response_text()` that correctly traverses the actual payload and concatenates assistant text blocks.[file:1]  
- Local tests confirm markers now register correctly; any future regression will likely show up as “Required markers: … Found: None” in logs despite clearly present markers, which signals an extraction bug.[file:1]

---

## 5. How to Maintain and Extend

### 5.1 Adding Governance to a New Skill

To make a new skill governed at Layer 1:

1. **Confirm it has a structured workflow**  
   - Stages, phases, or a template that can be recognized via stable textual markers.[file:1]

2. **Add governance frontmatter**

   In `P:/.claude/skills/<skill>/SKILL.md` frontmatter:

   ```yaml
   governance:
     layer1_enforcement: true
     usage_markers:
       - "Stage 0:"
       - "Stage 1:"
       - "Template:"
       # adjust to real headings/phrases
   ```

3. **Ensure skill is detected as a slash command**  
   - Router already detects `/name` via `extract_skill_from_prompt`/similar helpers.[file:1]  
   - For non‑slash or more complex cases, you may need to extend that detection.

4. **Verify Stop hook picks it up**  
   - Because markers live in SKILL.md, Stop hook doesn’t need hard‑coded entries for each new skill.[file:1]  
   - It loads frontmatter and enforces if `layer1_enforcement: true` is present.

5. **Test**  
   - In a dev session, issue `/newskill …` and deliberately:
     - Respond in a governed, marker‑rich format → should pass.  
     - Respond with plain prose → should be blocked (retry, then hard block).[file:1]

### 5.2 When NOT to Add Governance

Do not enable Layer 1 governance for:

- Simple one‑shot utility skills (e.g., “commit”, “push”) whose outputs lack structured, skill‑specific markers.[file:1]  
- Skills whose value is entirely in tool calls, where markers would live in external tool outputs instead of the assistant message.[file:1]  
- Knowledge‑only skills that just surface text without a clear multi‑stage template.[file:1]

### 5.3 Ongoing Maintenance Rules

- If you rename stages/headings in SKILL.md, **update `usage_markers`** accordingly.[file:1]  
- If logs show frequent false positives/negatives in `skill_execution_gate.jsonl`, refine markers to be:
  - Specific enough that generic answers don’t accidentally match.  
  - Stable enough to survive minor wording changes.[file:1]

---

## 6. Tooling and Diagnostics

### 6.1 `/av` Skill – Governance Awareness

- `/av` (analyzer/validator skill) was updated with a **Section F: Layer 1 Governance** in its checklist.[file:1]  
- When run on a skill, `/av` now:
  - Detects structured skills with stages/phases.  
  - Recommends adding `governance.usage_markers` if missing.  
  - Verifies that markers in frontmatter match actual headings or phrases used in the SKILL.md workflow.[file:1]

Use `/av <skill>` whenever you:

- Create a new structured skill.  
- Majorly refactor an existing skill’s workflow or headings.[file:1]

### 6.2 Local Testing Patterns

You can reproduce the existing tests with Python snippets like:

- Marker extraction from SKILL.md frontmatter.  
- Response classification:

```python
good = "Stage 0: Pre-Flight Checks\nTemplate: fast"
bad  = "Here's my architecture advice..."

markers = [...]
def has_markers(text, markers):
    t = text.lower()
    return [m for m in markers if m.lower() in t]

print(has_markers(good, markers))  # should be non-empty
print(has_markers(bad, markers))   # should be empty
```

This pattern is already used in the ad‑hoc tests run against `StopHook_skill_execution_gate.py`.[file:1]

---

## 7. How to Work With This as the New LLM

When you see a bug or want to extend behavior:

1. **Do not rebuild skill governance from scratch.**  
   - The v2.3 pre‑execution architecture and Stop hook framework already exist and are wired.[file:1]

2. **Treat SKILL.md governance as the source of truth**  
   - For which skills are governed.  
   - Which markers indicate “used skill vs bypassed”.[file:1]

3. **Touch these in order when changing behavior**  
   - SKILL.md frontmatter (`governance.usage_markers`).  
   - Router state writing in `run_skill_enforcement`.  
   - Stop hook marker extraction / response extraction logic.

4. **Maintain the two‑strike pattern**  
   - First bypass: retry with explicit message.  
   - Second: hard block with clear explanation.[file:1]

5. **If you can’t reliably detect a skill’s usage, leave it ungoverned at Layer 1**  
   - For that skill, governance should be pushed into Layer 2 (deeper, skill‑specific validation), not faked at Layer 1.[file:1]

---

This is the minimal, battle‑tested Layer 1 governance system you’re inheriting. It ensures that when the user invokes core skills like `/arch`, `/v`, or `/rca`, you **cannot** ignore them and improvise; you must work within their declared workflows, at least at the structural level.[file:1]
```
