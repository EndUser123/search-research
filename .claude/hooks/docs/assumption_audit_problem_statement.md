# Assumption Audit: Problem Statement

## The Problem

**Core failure mode:** Claude Code makes claims about code state without verification.

Examples:
- "Tests pass" (without running pytest)
- "File contains X" (without reading file)
- "Bug is fixed" (without executing verification)

**Why it matters:** False confidence leads to shipped bugs, wasted debugging time, eroded trust.

---

## Solution Attempts

### v1.0: Soft Warning Injection

**Mechanism:** Detect claims without tool usage → inject warning into response.

**Result:** ❌ Failed. Warnings easily ignored. No behavioral change.

---

### v2.0: Blocking Mode

**Mechanism:** Detect claims without tool usage → block response entirely.

**Result:** ⚠️ Partial success. Blocked obvious cases but too coarse:
- Blocked general knowledge responses
- Blocked responses where tools WERE used earlier in conversation

---

### v2.2: Evidence Window

**Mechanism:** Track tool sequence. State-changing tools invalidate prior observations. Only count "fresh" evidence.

**Result:** ✅ Improved. Handled the "used tools earlier" case. But still couldn't distinguish:
- Claim about file A with evidence from file B
- Generic discussion vs. specific claims

---

### v2.3: Entity Overlap (Claim-Scope Verification)

**Mechanism:** 
1. Extract "entities" from claims (file paths, function names, class names)
2. Extract "entities" from tool evidence (files read, paths checked)
3. Require configurable % overlap (default 50%)

**Result:** ❌ Failed. Entity extraction too noisy:
- Extracts generic words: "framework", "verification", "phase", "ritual"
- Blocks responses discussing concepts (no specific file claims)
- 12% block rate with many false positives

**Evidence from logs:**
```
Claims: ["tests pass"]
Uncovered: ["sha256", "integrity", "checkpoint"]  # Generic words, not entities

Claims: ["was changed"]  
Uncovered: ["source", "conclusion", "documents", "rationale", "git", "answer"...]
```

---

### v2.3.1: Coverage Threshold Adjustment

**Mechanism:** Lower CLAIM_COVERAGE_THRESHOLD from 0.5 to 0.3.

**Result:** ⚠️ Band-aid. Reduces blocks but doesn't fix root cause:
- Still extracts noise as "entities"
- Just tolerates more unmatched noise
- Unclear optimal threshold

---

### v2.4: Verification Theater Detection

**Mechanism:** Detect "success claims + only trivial evidence":
- Success patterns: "fixed", "working", "tests pass"
- Trivial commands: echo, mkdir, ls (no diagnostic value)
- Diagnostic commands: pytest, cat, grep (actual verification)

Block if: success claim + only trivial/weak evidence

**Result:** ✅ Targeted. Catches the main failure mode (claiming "fixed" after running `echo "done"`). Doesn't suffer from entity extraction noise.

---

## Current State

**What's enabled:**
- v2.4 Theater Detection ✅ (working well)
- v2.3 Entity Overlap ⚠️ (noisy, causing false positives)
- Threshold at 0.3 (lowered from 0.5 as band-aid)

**Block rate:** ~12% overall, but includes false positives on:
- Conceptual discussions
- Stop hook operational output
- Responses with generic terminology

---

## Root Cause Analysis

The entity extraction approach is fundamentally flawed:

1. **Pattern problem:** NAME_PATTERNS match too broadly
   - `r'\b([a-z_][a-z0-9_]*)\s*\('` catches "was changed ("
   - `r'\b([A-Z][a-zA-Z0-9]+)\b'` catches "Valid", "Component"

2. **Context blindness:** Can't distinguish:
   - "The verification framework" (concept) vs.
   - "verification.py contains" (file claim)

3. **Noise amplification:** COMMON_WORDS filter incomplete → generic words become "entities" → flagged as uncovered → false block

---

## Options Forward

### Option A: Disable Entity Overlap

Set `CLAIM_SCOPE_CHECK_ENABLED=false`. Rely on:
- Basic tool presence check (v2.0)
- Evidence window (v2.2)
- Theater detection (v2.4)

**Loses:** Detection of "claim about A, evidence from B"
**Gains:** Eliminates false positives from noisy extraction

### Option B: Rewrite Entity Extraction

Fix NAME_PATTERNS to only match actual identifiers:
- Require file extensions for paths
- Require snake_case or specific patterns for functions
- Expand COMMON_WORDS significantly

**Risk:** May still miss edge cases; ongoing maintenance burden

### Option C: Different Architecture

Replace entity overlap with:
- LLM-based claim extraction (expensive)
- AST-based verification for code claims
- Explicit claim tagging by Claude Code

**Risk:** Complexity increase; may not be worth it for solo dev context

---

## Recommendation

**Option A: Disable Entity Overlap**

Rationale:
- Theater detection (v2.4) catches the main failure mode
- Entity overlap causes more harm (false positives) than good
- Simpler system = easier maintenance
- Reversibility: 1.0 (one config change)

The "claim about A, evidence from B" case is real but rare. The false positive cost exceeds the missed detection benefit.

---

## Decision Needed

Disable entity overlap check? (CLAIM_SCOPE_CHECK_ENABLED=false)
