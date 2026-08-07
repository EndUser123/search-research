# Design: Recommendation Validation Capability — Reusable Skill Graph Component

## Design Intent Contract

```
Goal: Any skill that produces an architectural recommendation about external systems must validate it against external evidence before persisting it, via a reusable component rather than per-skill prose rules.
Non-goals: Replacing /www's full research pipeline; validating recommendations about internal workspace state (those need code reading, not web search); building a new search tool.
Success metrics: Reduce unvalidated architectural recommendations by ≥80% within 2 weeks of Unit 2+3 deployment. Baseline: sample last 30 days of handoff/wiki commits for recommendations matching trigger patterns without external citations. Proxy metric: Stop hook block count per session (target: 0 after 2 weeks of tuning).
Failure conditions: The component produces false positives (>20% of blocks are internal recommendations, wasting time) or false negatives (misses >20% of external-system recommendations, same as today).
Success looks like: /tp recommends a pre-commit hook architecture → the component detects "external systems" → /www fires automatically → recommendation ships with external citations.
Failure looks like: The component fires on every recommendation (noise) or never fires (same as no component).
```

## Problem Analysis

The workspace has a prose rule in AGENTS.md: "Are there [INFERENCE]/[UNKNOWN] items that external research could upgrade? If yes, recommend /www." This rule has ~50% compliance under session pressure — it fired conceptually when /tp recommended the pre-commit gate, but the agent didn't execute it. The operator had to explicitly request /www.

The root cause is structural: the rule is behavioral (prose in AGENTS.md), not mechanical (code that runs). The workspace's own wiki documents this: "prose rules for response patterns have a documented ~50% compliance ceiling under session pressure." The fix is mechanical enforcement — the same pattern that works for pre-commit gates, script scanners, and Stop hooks.

## Architecture: Three Layers

**Critical friend revision (REVISE):** the original design framed Layer 2 (/tp SKILL.md step) as "primary enforcement" and Layer 3 (Stop hook) as "backstop." This is backwards. Layer 2 is a prose rule in a SKILL.md — the exact pattern the design criticizes (50% compliance ceiling). Only Layer 3 (Stop hook) is mechanical enforcement. The corrected framing: **Layer 3 is primary enforcement. Layer 1 provides the capability. Layer 2 is a convenience that reduces how often Layer 3 fires (fewer blocks = less friction).** The thin version (ship Units 0+1+3, skip Layer 2 initially) is the recommended rollout.

### Layer 1: Shared Library (`needs_external_validation.py`)

A Python function any skill can import or invoke. This is the reusable component — the capability that makes the determination "does this recommendation need external validation?"

**Location:** `~/.grok/skills/www/__lib/needs_external_validation.py`

**Interface:**
```python
def needs_external_validation(recommendation: str, context: str = "") -> dict:
    """Determine whether a recommendation needs external evidence validation.
    
    Returns:
        {
            "needs_validation": bool,
            "reason": str,  # why or why not
            "detected_signals": list[str],  # what triggered the detection
            "suggested_queries": list[str],  # DDG queries to run
        }
    """
```

**Detection heuristics (mechanical, not LLM-based):**

The function uses keyword/pattern matching + context to classify the recommendation:

**Context schema (F-06 fix):**
```python
context = {
    "target": "internal" | "external" | "unknown",  # caller provides this
    "files_mentioned": [str],   # e.g., ["P:/.claude/hooks/PreToolUse.py"]
    "tools_mentioned": [str],   # e.g., ["pre-commit", "GitHub Actions"]
}
```
The caller (e.g., /tp) passes context from its own knowledge — it knows whether the recommendation is about an external system or a workspace file. Detection logic: `needs_validation = target == "external" OR any(tool in EXTERNAL_SIGNALS for tool in tools_mentioned)`. Internal-only recommendations short-circuit.

**Signal classification (keyword lists in JSON config):**

| Signal pattern | Example | Classification |
|---|---|---|
| External tool names (library, framework, CLI, service) | "pre-commit hook", "GitHub Actions", "Docker" | needs_validation = True |
| Architectural pattern names | "event sourcing", "CQRS", "pre-commit gate" | needs_validation = True |
| "optimal", "best approach", "should use" + external noun | "optimal approach is pre-commit hooks" | needs_validation = True |
| "nobody does X" / "everyone does X" claims | "other people never check their usage" | needs_validation = True |
| Internal file paths, workspace rules, code references | "P:/.claude/hooks/PreToolUse.py" | needs_validation = False (check the code) |
| Pure reasoning, logic, math | "the sort order should be family→window" | needs_validation = False |
| Operator preferences, workspace conventions | "auto-commit is standing policy" | needs_validation = False |

**Query generation (F-07 fix):**
`suggested_queries` are generated by extracting noun phrases from the recommendation and appending search qualifiers:
```python
def _generate_queries(recommendation: str) -> list[str]:
    # Extract key nouns (simple: words >4 chars, not stopwords)
    nouns = [w for w in recommendation.split() if len(w) > 4 and w.lower() not in STOPWORDS]
    # Build 2-3 targeted queries
    queries = [
        f"{' '.join(nouns[:3])} best practices 2026",
        f"{' '.join(nouns[:2])} vs alternatives comparison",
        f"{' '.join(nouns[:3])} pitfalls limitations",
    ]
    return [q for q in queries if len(q) <= 80]
```

**Config security (F-11 fix):** Keywords load from JSON at import time (frozen). If JSON is missing/corrupt/empty, fall back to built-in defaults (hardcoded in Python). Startup assertion: keyword list must have ≥10 entries, else use defaults.

The keyword lists are configurable (a JSON file at `~/.grok/skills/www/__lib/external_validation_signals.json`) so new patterns can be added without code changes.

### Layer 2: /tp Auto-fire Gate (SKILL.md edit)

When /tp produces a recommendation in its output, Step 5 (recommendation output) runs `needs_external_validation()` on the recommendation text. If it returns `needs_validation = True`:

1. /tp auto-invokes /www with the `suggested_queries` as search terms
2. /www runs its standard wiki→web→wiki pipeline (Light ceremony for single-claim validation)
3. The recommendation ships with external citations or gets qualified/refuted

**Failure path (F-03 fix):** If /www fails (timeout after 90s, network error, DDG rate-limited), /tp does NOT hang. It returns the recommendation labeled `[INFERENCE — external validation attempted but failed: <reason>]. Operator should validate before persisting.` This preserves the epistemic label honestly and lets the Stop hook (Layer 3) still see the unvalidated claim.

**Timeout:** 90 seconds. If /www hasn't returned by then, the fallback fires.

This is a mandatory step in /tp's output flow, not a suggestion. The /tp SKILL.md gets a new subsection after the current recommendation output section:

```markdown
### Step 5.1 — External validation gate (mandatory for architectural recommendations)

After producing recommendations, run:
    python ~/.grok/skills/www/__lib/needs_external_validation.py "<recommendation text>"

If needs_validation is True:
  1. Auto-invoke /www with the suggested_queries (Light ceremony, 90s timeout)
  2. Do NOT report the recommendation until /www returns or times out
  3. On success: incorporate findings (upgrade [INFERENCE] to [FACT] with citations, or qualify/refute)
  4. On failure/timeout: label as [INFERENCE — external validation failed: <reason>]
```

### Layer 3: Stop Hook Backstop (`validate_recommendations.py`)

A Stop hook that scans the session's output text for architectural recommendation patterns that lack external citations.

**Location:** `~/.grok/hooks/Stop_validate_recommendations.py` (Grok Build hook scope — per `~/.grok/docs/user-guide/10-hooks.md`, all hook scopes merge)

**Registration:** `~/.grok/config.toml` under `[hooks]` Stop section (single canonical path on Grok Build).

**Hook input (F-02 fix):** The hook reads `lastAssistantMessage` from the stdin JSON payload. Per `~/.grok/docs/user-guide/10-hooks.md:262`: *"The hook input includes `stopHookActive` and `lastAssistantMessage`. `lastAssistantMessage` carries the text of the agent's final response this turn, so hooks can act on it without parsing the transcript."* Hook type is `command` (confirmed supported for Stop hooks on Grok Build). The hook also checks `stopHookActive` to avoid infinite loops (skip if already in a continuation from a prior block). Check `reason == "end_turn"` to skip session-end fires.

**Logic:**
1. Read stdin JSON, extract the agent's final response text
2. Split into sentences (handle abbreviations with a simple regex: `re.split(r'(?<=[.!?])\s+', text)`)
3. For each sentence, match recommendation patterns: `r"(?:optimal|best\s+approach|should\s+use|recommend).*(?:hook|gate|pattern|architecture|library|framework|API|endpoint|protocol)"`
4. For each match, check evidence within **±200 chars** (tightened from ±500 per critical friend) of the recommendation sentence:
   - URL: `r'https?://[^\s\)]+'`
   - Markdown link: `r'\[[^\]]+\]\(https?://[^)]+\)'` (must be a real link, not just bracket text)
   - Named source with URL: `r'\b(?:per|according to|source:?)\s+[A-Z][a-z]+.*\d{4}'` (requires author + year)
   - Explicit /www reference: `r'/www\b'` or `r'\[www validated\]'`
5. If recommendation found without evidence: exit 2 with "Architectural recommendation detected without external validation. Run /www on: <extracted claim>"

**Regex note (F-01 fix):** Sentence-level matching avoids the `re.DOTALL` problem entirely — each sentence is scanned independently, so multi-line text is handled by splitting first.

**Evidence check (F-10 fix):** Four pattern types checked in proximity to the recommendation (not just bare URLs).

**Fail-open:** if the regex pattern matching fails or the hook errors, allow the stop (a buggy hook must never block legitimate work — same principle as IMTI's pre-commit gate).

### Why three layers (not one)

| Layer | What it catches | Enforcement type |
|---|---|---|
| Layer 1 (shared library) | Provides the reusable detection capability | Importable function |
| Layer 2 (/tp auto-fire) | Catches recommendations at production time | Skill protocol (mandatory step) |
| Layer 3 (Stop hook) | Catches anything Layers 1-2 missed | Mechanical backstop |

Layer 2 is the primary enforcement — it fires at the point of recommendation production. Layer 3 is the safety net — it catches the case where the agent skips Layer 2 under session pressure (the documented ~50% prose-rule compliance ceiling). Layer 1 is the shared component that both layers use, plus any other skill that wants to opt in.

## Skills that consume this capability

| Skill | How it invokes | What triggers |
|---|---|---|
| /tp | Step 5.1 auto-fire (mandatory) | Architectural recommendation in output |
| /go | H3-discover pack calls `needs_external_validation()` on discovery conclusions | When comparing approaches or checking if a capability exists |
| /design | Step 0.8 (premise verification): run `needs_external_validation()` only on premises that Step 0.6 did NOT already cover (dedupe by claim hash) | When premises involve external tooling not already researched in Step 0.6 |
| /refine | Call `needs_external_validation()` on task assumptions | When the task depends on external tool behavior |
| /plan-writer | Call `needs_external_validation()` on proposed implementation patterns | When the plan proposes a specific pattern |

Each skill adds one function call + one conditional branch. The heavy lifting (detection logic) lives in the shared library.

## Alternatives

### Option 0: Do Nothing
Keep the AGENTS.md prose rule. Accept ~50% compliance. The operator catches the misses manually (as they did this session). Cost: one operator correction per session where an unvalidated recommendation ships. Not acceptable — the operator's time is the most expensive resource in the system.

### Option 1: /tp SKILL.md edit only (Layer 2 only)
Add the mandatory step to /tp without the shared library or the Stop hook. The /tp SKILL.md already has the auto-research trigger in prose — promote it to a mandatory step. Cost: lower, but doesn't help /go, /design, /refine, or /plan-writer. And /tp's prose rule still has compliance issues under pressure — making it a "mandatory step" helps but doesn't guarantee execution.

### Option 2: Stop hook only (Layer 3 only)
Skip the shared library and the /tp edit. Just scan all output text for unvalidated recommendations. Cost: lower implementation, but the hook can't distinguish between "the agent already validated this" and "the agent is about to validate this in a follow-up." Higher false-positive rate. Also doesn't provide the reusable detection capability to other skills.

### Option 3: Full three-layer (RECOMMENDED)
Shared library + /tp auto-fire + Stop hook backstop. The three layers compose: Layer 1 provides the capability, Layer 2 enforces it at the primary production point, Layer 3 catches misses. Defense in depth — same pattern validated by the /www research on pre-commit gates (IMTI, CircleCI, pydevtools all use multi-layer enforcement).

**Selection criterion:** reliability under session pressure. Layer 2 alone has the same prose-rule compliance problem. Layer 3 alone has false positives. Layer 1 alone is just a function nobody calls. The three-layer approach maximizes reliability.

## Coupling & Code-Smell Inventory

| Module | DRY violations | Param count | Touch-points | Mixed concerns | Assessment |
|---|---|---|---|---|---|
| `needs_external_validation.py` | 0 (new code) | 2 (recommendation, context) | 1 (import + call) | No (detection only) | Clean |
| `/tp` SKILL.md edit | 0 | N/A (prose) | 1 (new subsection) | No | Additive |
| Stop hook | 0 (new code) | 1 (session text) | 1 (registration in settings) | No (scan + exit code) | Clean |
| Consumer skills (/go, /design, /refine, /plan) | 0 | N/A (1 import + 1 call each) | 1 per skill | No | Additive |

No thresholds met. The design is purely additive — no existing code is refactored, no existing interfaces change.

## Failure Mode & Edge Case Analysis

### Problems identified by cross-model critique (DeepSeek + GPT-5.6 lenses)

**P1: "Hook/gate" keyword poison.** This workspace uses "hook," "gate," "PreToolUse," "Stop hook" as its primary architectural vocabulary. Layer 3's regex triggers on these words, but 90% of mentions are internal references. Layer 3 has no context field to disambiguate. **Mitigation:** Layer 3 needs a negative keyword list (`PreToolUse`, `PostToolUse`, `dispatch chain`, `P:/.claude/hooks`, `~/.grok/hooks`) that suppresses the trigger when present.

**P2: Citation presence ≠ evidence quality.** A URL near a recommendation doesn't prove the source supports the claim. The agent can paste any URL to satisfy the hook. **Mitigation:** Replace proximity-based evidence with a structured validation receipt: `[VALIDATED: <claim_hash>, sources: [<urls>], verdict: confirmed|qualified|refuted]`. The Stop hook checks for this marker, not bare URLs.

**P3: Timeout compounds with false-positive rate.** At 20% FP rate and 90s per /www invocation, a session with 10 recommendations wastes ~3 minutes on false positives. Operators disable via bypass env var. **Mitigation:** Layer 2's pre-check (`needs_external_validation()`, <10ms) is the latency gate. Layer 3 only fires when Layer 2 is skipped entirely. Design should state this explicitly.

**P4: Unit 0 tests the wrong premise.** Unit 0 tests "/www value" but not "detection accuracy." Both are load-bearing. **Mitigation:** Split Unit 0 into 0a (detection accuracy over labeled corpus — TP/FP/FN count) and 0b (value retrodiction — /www on true positives). Both must pass.

**P5: Multi-agent concurrency.** Two agents producing recommendations in the same minute both fire /www, DDG rate-limits one. **Mitigation:** Claim-hash deduplication — if /www was invoked for the same claim hash in the last 5 minutes, reuse the result.

### Original FMEA table

| Component | Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|---|
| `needs_external_validation.py` | False positive (fires on internal recommendation) | Keyword overlap (e.g., "hook" appears in both internal and external contexts) | Medium | Context field disambiguates; keyword list is configurable | Monitor false-positive rate; tighten keywords |
| `needs_external_validation.py` | False negative (misses external recommendation) | Novel tool/pattern not in keyword list | Medium | Keyword list is extensible via JSON config; Stop hook backstop catches misses | /www research on "what did we miss" |
| `/tp` auto-fire | Agent skips the step under pressure | Prose-rule compliance ceiling | High | Stop hook backstop (Layer 3) catches it | Stop hook exit code 2 |
| Stop hook | False positive (blocks legitimate completion) | Recommendation pattern matches non-architectural text | Medium | Fail-open on hook errors; 3-attempt cap before allowing stop | Monitor block rate |
| Stop hook | Agent finds workaround (doesn't use recommendation words) | Agent paraphrases to avoid the pattern | Low | Keyword list includes paraphrase patterns; Layer 2 catches most cases before Layer 3 | Compare recommendation quality pre/post hook |
| `/www` invocation | Takes too long (>5 min) | Full pipeline instead of Light ceremony | Low | Use Light ceremony for single-claim validation; cap at 3 searches | Timeout in /www skill |
| `/www` invocation | Returns no results (novel topic) | Genuinely no external coverage | Low | Label as [UNKNOWN] with no sources — that's honest | /www output |
| Concurrent skills | Both /tp and /go fire /www simultaneously | Two skills produce recommendations in same turn | Low | /www handles concurrent invocations (each is independent) | N/A |
| `external_validation_signals.json` | Corrupted or missing | File system issue, concurrent edit | Medium | Code falls back to built-in defaults if JSON parse fails | Error log |
| Stop hook + existing Stop hooks | Interaction with quality-gate Stop hook | Two Stop hooks both fire | Low | Each exits independently; quality-gate checks receipts, this hook checks recommendations | N/A |

## Implementation Plan

| Unit | Title | Files | Deps | Disposition |
|---|---|---|---|---|
| 0a | Detection accuracy test: build 20-item labeled corpus (5 external-architectural, 5 internal-workspace, 5 pure-reasoning, 5 mixed), run keyword classifier, count TP/FP/FN. **Gate: FP rate ≤20% and FN rate ≤20%** | `~/.grok/skills/www/__lib/test_needs_external_validation.py` | None | COMMIT_THIS_SESSION — **MUST PASS BEFORE UNIT 0b** |
| 0b | Value retrodiction: run /www on the true positives from 0a, measure whether /www changed the recommendation (found alternative, added caveat, contradicted, or confirmed). **Gate: ≥1 case where /www materially changed the recommendation** | retrodiction report | Unit 0a | COMMIT_THIS_SESSION — **MUST PASS BEFORE UNIT 1** |
| 1 | Shared detection library | `~/.grok/skills/www/__lib/needs_external_validation.py` + `external_validation_signals.json` | Unit 0 (gate: retrodiction shows /www adds epistemic value) | COMMIT_THIS_SESSION |
| 2 | /tp auto-fire gate | `~/.grok/skills/tp/SKILL.md` (Step 5.1) | Unit 1 | COMMIT_THIS_SESSION |
| 3 | Stop hook backstop | `P:/.claude/hooks/Stop_validate_recommendations.py` + registration in `~/.grok/config.toml` | Unit 1 | HANDOFF |
| 4 | /go consumer wiring | `~/.grok/skills/go/SKILL.md` (H3-discover) | Unit 1 | HANDOFF |
| 5 | /design consumer wiring | `~/.grok/skills/design/SKILL.md` (Step 0.8) | Unit 1 | DEFERRED |
| 6 | /refine consumer wiring | `~/.grok/skills/refine/SKILL.md` | Unit 1 | DEFERRED |
| 7 | /plan-writer consumer wiring | `~/.grok/skills/plan-writer/SKILL.md` | Unit 1 | DEFERRED |
| 8 | Pre-claim wiki check function | `~/.grok/skills/wiki/__lib/check_wiki_before_claim.py` — greps wiki concepts for a claim string, returns matching paths. Called before stating negative capability claims ("X doesn't exist", "we can't do X"). | None | HANDOFF |
| 9 | Stop hook extension for unsupported claims | Extends Unit 3's Stop hook to also check for negative capability claims that lack a wiki grep receipt in the same turn | Units 3, 8 | DEFERRED |

Units 1-2 are the core: the shared library and the /tp gate. Units 3-7 extend the capability to other skills and add the backstop hook. Each is independent and can be shipped separately.

## Traceability Matrix

| REQ/DEC ID | Component | Implementation Unit | Status |
|---|---|---|---|
| REQ-01 | Reusable detection function | Unit 1 | Planned |
| REQ-02 | /tp auto-fires /www on architectural recommendations | Unit 2 | Planned |
| REQ-03 | Stop hook catches misses | Unit 3 | Planned |
| REQ-04 | /go validates discovery conclusions | Unit 4 | Planned |
| REQ-05 | /design validates external premises | Unit 5 | Planned |
| REQ-06 | /refine validates external assumptions | Unit 6 | Planned |
| REQ-07 | /plan-writer validates proposed patterns | Unit 7 | Planned |
| DEC-01 | Three-layer architecture (library + skill gate + hook) | All | Decided |
| DEC-02 | Detection is keyword-based, not LLM-based | Unit 1 | Decided |
| DEC-03 | Keyword lists are JSON-configurable | Unit 1 | Decided |
| DEC-04 | Stop hook is fail-open | Unit 3 | Decided |

## Key Decisions

**[DEC-01] Three-layer architecture.** Steelman of single-layer: simpler, fewer moving parts, faster to ship. Why three layers won: the workspace's own evidence shows prose rules have ~50% compliance under pressure. A single layer (whether library, skill edit, or hook) inherits that ceiling. Three layers compose for defense in depth — same pattern validated by IMTI, CircleCI, and pydevtools for pre-commit enforcement.

**[DEC-02] Keyword-based detection, not LLM-based.** Steelman of LLM-based: more accurate, handles paraphrases and novel patterns. Why keyword-based won: it's deterministic, testable, configurable, and fast (<10ms). LLM-based detection adds latency (5-10s per check), cost (model inference per recommendation), and unreliability (the detection itself is subject to the same compliance ceiling). The keyword list is extensible via JSON — novel patterns are added as they're discovered, not re-trained.

> **⚠️ FALSIFIED (2026-08-07, session 019fdc43).** Retrodiction over 40 real sessions measured 67% false-positive rate — well above the workspace's own falsifier threshold (>50% FP = "entire hook-based approach suspect"). The root cause is structural: regex cannot distinguish assertion ("I recommend Aider") from discussion ("the agent said 'recommend Aider'"). See wiki concept `[[keyword-detection-recommendations-falsified-67percent-fp]]` for the full falsification, retrodiction data, and the 3 genuine catches. If detection is revisited, the LLM-judge two-layer approach (regex pre-filter + LLM classifies assertion-vs-discussion) should be re-evaluated with the data this decision was made without. The code has been deleted; the design doc is preserved as architecture archive.

**[DEC-03] JSON-configurable keyword lists.** Allows extending detection without code changes. New tools, frameworks, and patterns emerge constantly — the config file is the maintenance surface, not the Python code.

**[DEC-04] Stop hook is fail-open.** A buggy hook that blocks legitimate completion is worse than no hook (IMTI's principle). The hook logs warnings on errors but allows the stop. False negatives are caught by improving the keyword list, not by blocking the agent.

## Rollout

1. Ship Unit 1 (shared library) — no behavior change, just a function nobody calls yet
2. Ship Unit 2 (/tp auto-fire) — immediate effect: /tp recommendations about external systems get validated
3. Ship Unit 3 (Stop hook) — backstop for /tp and other skills not yet wired
4. Ship Units 4-7 (consumer wiring) — incremental, one skill at a time
5. Monitor false-positive rate for 2 weeks — tune keyword lists based on observed hits

**Feature flags:** The Stop hook (Unit 3) respects `GROK_DISABLE_RECOMMENDATION_GATE=1` env var for emergency bypass.

**Rollback:** Remove the Stop hook registration (Unit 3) and revert the /tp SKILL.md edit (Unit 2). The shared library (Unit 1) is harmless if unused.

## File Change Inventory

| File | Action | Unit | Est. LOC |
|---|---|---|---|
| `~/.grok/skills/www/__lib/needs_external_validation.py` | New | 1 | ~120 |
| `~/.grok/skills/www/__lib/external_validation_signals.json` | New | 1 | ~50 |
| `~/.grok/skills/tp/SKILL.md` | Modify (add Step 5.1) | 2 | +20 |
| `~/.grok/hooks/Stop_validate_recommendations.py` | New | 3 | ~80 |
| `~/.grok/config.toml` | Modify (hook registration under `[hooks]` Stop section) | 3 | +5 |
| `~/.grok/skills/go/SKILL.md` | Modify (H3-discover) | 4 | +10 |
| `~/.grok/skills/design/SKILL.md` | Modify (Step 0.8) | 5 | +10 |
| `~/.grok/skills/refine/SKILL.md` | Modify | 6 | +10 |
| `~/.grok/skills/plan-writer/SKILL.md` | Modify | 7 | +10 |
