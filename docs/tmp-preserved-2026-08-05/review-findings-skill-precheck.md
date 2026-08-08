# Review findings: UserPromptSubmit skill precheck hook

**Review target:** commits 5869b92..d5fbf56 in `C:/Users/brsth/.grok` (4 commits)
**Files reviewed:**
- `hooks/UserPromptSubmit_skill_precheck.py` (new, 445 lines) — primary review target
- `hooks/skill-precheck.json` (new, 11 lines) — registration
- `skills/go/SKILL.md` — stale `ship/` path fix (line 808)
- `skills/ship-py/SKILL.md` — added post-ship wiki step (lines 83-91, 95)
- `skills/ship-rhai/SKILL.md` — added post-ship wiki step (lines 74-82, 86)
- `skills/ship-rhai/tests/test_ship_receipt.py` — stale test path fix (line 7)

**Review date:** 2026-08-05
**Reviewer stance:** fresh-eyes; no prior session knowledge.

---

## Findings

### BUG-1: Path-skip heuristic in `find_skill_invocations` is broken for mid-prompt paths

**Severity:** bug
**File:** `hooks/UserPromptSubmit_skill_precheck.py:135-138`
**Symptom:** When a prompt contains a Windows file path with a drive letter followed later by a `/<word>`, the word is incorrectly detected as a skill invocation. The heuristic only catches paths where `/` immediately follows `:`.

**Evidence (verified by execution):**

```python
# In find_skill_invocations:
if start >= 2 and prompt_text[start - 2:start].endswith(":"):
    continue
```

Test runs:
```
'P:/Users/x/y.md /also'  →  detected: ['also']   (FALSE POSITIVE)
'C:/file.json do /something'  →  detected: ['something']   (FALSE POSITIVE)
'P:/foo/bar /baz'  →  detected: ['baz']   (FALSE POSITIVE)
'P:/foo uses /ship'  →  detected: ['ship']   (correct)
'P:/foo'  →  detected: []   (correct — drive letter immediately precedes /)
```

The check `prompt_text[start - 2:start].endswith(":")` only succeeds when `/` is exactly two characters after the drive-letter colon (e.g., `P:/foo`). Real-world paths almost always have directories between the drive letter and the trailing `/word`.

**Same bug exists in sibling module:** `hooks/scripts/quality_gates_frontmatter.py:474-476` (`scan_invoked_skills`) has the identical broken heuristic. Confirmed by `python -c "..."` test: `scan_invoked_skills(['{"type":"user","content":"see P:/Users/x/y.md /also"}'])` returns `{'also', 'ship'}` — the `/also` is a false positive.

**Impact:**
- The hook may emit false `critical: skill '/<word>' not found` warnings for any prompt containing a Windows path followed by `/<word>`.
- Worse, the Stop hook's `scan_invoked_skills` may trigger quality-gate scans for non-skill words (mitigated there by `SKIP_SKILL_NAMES`, but still a quality-of-life problem).

**Suggestion:** Improve the heuristic to look backward from the match position for the closest `:` preceded only by `[A-Za-z]` and not preceded by `/` or `\\`. Or simpler: detect Windows-path-shaped substrings before the match and skip if the `/` is part of one. A safer rule: if any `/` or `\\` appears between the last whitespace and this `/`, treat it as path-like.

```python
# Suggested replacement:
preceding = prompt_text[:start]
last_ws = max(preceding.rfind(' '), preceding.rfind('\n'), preceding.rfind('\t'))
segment = preceding[last_ws + 1:]
if ':' in segment and re.match(r'^[A-Za-z]:', segment):
    continue
```

---

### BUG-2: Hook silently exits 0 when stdin has a UTF-8 BOM

**Severity:** bug
**File:** `hooks/UserPromptSubmit_skill_precheck.py:387-389`
**Symptom:** When the host passes stdin via a path that includes a UTF-8 BOM (e.g., redirected file written with PowerShell's default encoding, or `python ... <<<` on PowerShell), `json.loads(raw)` raises `JSONDecodeError`. The hook fail-opens to `sys.exit(0)` and produces no stderr, no state file — completely invisible to the operator.

**Evidence (verified by execution):**

```python
try:
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    sys.exit(0)  # Fail-open on parse errors
```

Test runs (`/nonexistent-skill` should produce critical warning):
```
=== Without BOM ===
stderr: "⚠ SKILL PRECHECK: 1 critical issue(s)..."
exit: 1
state file: written

=== With BOM (\ufeff prepended) ===
stderr: ''
exit: 0
state file: not written
```

When invoked via PowerShell `|` pipe on Windows, PowerShell's default encoding emits a BOM. Same applies if Grok Build's dispatcher writes the JSON envelope to a file using Windows-default encoding and then redirects.

**Impact:** On Windows PowerShell hosts, the hook may be silently invisible whenever the producer of the JSON envelope adds a BOM. The operator sees no warnings and may mistakenly believe the hook is not firing.

**Suggestion:** Strip a leading BOM before `json.loads`. One line:
```python
raw = sys.stdin.read()
if raw.startswith('\ufeff'):
    raw = raw[1:]
data = json.loads(raw) if raw.strip() else {}
```
Also consider logging a one-line stderr hint when parse fails so the operator can diagnose: `print(f"[skill-precheck] stdin parse error: {type(e).__name__}: {e}", file=sys.stderr)` before `sys.exit(0)`.

---

### BUG-3: `format_warnings` suppresses the warning-count header when there are also criticals

**Severity:** bug
**File:** `hooks/UserPromptSubmit_skill_precheck.py:316-331`
**Symptom:** When the warnings list contains both critical and non-critical items, the non-critical items are listed without a count header. The operator sees warnings but cannot tell at a glance how many there are.

**Evidence (verified by execution):**

```python
if warns:
    if not critical:
        lines.append(f"⚠ SKILL PRECHECK: {len(warns)} warning(s)")
    for w in warns:
        lines.append(f"  ⚠ [{w['check']}] {w['message']}")
```

Output:
```
=== 1 critical, 1 warning ===
⚠ SKILL PRECHECK: 1 critical issue(s)
  ✗ [c1] crit msg
  ⚠ [w1] warn msg             ← no header, looks orphaned
```

When there are 3 criticals and 5 warnings, the warnings are listed but the operator can't tell if there are 5 or 6 or 7 without counting.

**Impact:** UX issue for operator scanning. The docstring (`- Layer 1 (this hook, pre-response): operator sees warning → can rephrase`) advertises operator visibility — the suppressed header undermines that.

**Suggestion:** Always emit a warning header when warns is non-empty:
```python
if warns:
    lines.append(f"  ⚠ + {len(warns)} warning(s):")
    for w in warns:
        lines.append(f"    ⚠ [{w['check']}] {w['message']}")
```

---

### RISK-1: `_safe_session_id_for_path` accepts Unicode letters despite ASCII-only docstring

**Severity:** risk (low)
**File:** `hooks/UserPromptSubmit_skill_precheck.py:340-350`
**Symptom:** The docstring claims "Accepted: ASCII letters/digits/dashes/dots/underscores" but the whitelist uses `c.isalnum()`, which accepts Unicode letters (Cyrillic, CJK, Arabic, etc.).

**Evidence (verified by execution):**

```python
if not all(c.isalnum() or c in "._-" for c in session_id):
    return None
```

Test runs:
```
safe_sid('id-тест') -> 'id-тест'   (accepted; docstring says ASCII)
safe_sid('ид') -> 'ид'             (accepted)
safe_sid('id-船') -> 'id-船'        (accepted)
```

**Why this matters:**
- The docstring-to-code mismatch is a maintainability hazard: future readers may rely on the docstring.
- Although `session_id` is host-produced (not user-controlled), on a Windows host with mixed-locale session ID generators, this could allow directories with non-ASCII names that are visually ambiguous or that fail to round-trip through ASCII-only tooling (`ls`, `grep`, `git`, CI scripts).
- A homograph in a directory name (`id` with Cyrillic 'i') could silently misroute state to a different directory if two sessions differ by exactly one letter that looks identical.

**Suggestion:** Make the code match the docstring:
```python
# Allow only ASCII letters/digits/dashes/dots/underscores
if not all(
    (c.isascii() and c.isalnum()) or c in "._-"
    for c in session_id
):
    return None
```

---

### RISK-2: `RECENT_EDIT_THRESHOLD_S = 120` triggers a warning every time the operator types `/go`

**Severity:** risk (medium) — repeated false positives
**File:** `hooks/UserPromptSubmit_skill_precheck.py:71`
**Symptom:** The 120-second "concurrent edit" threshold is small enough that the operator editing their own SKILL.md file (which is a routine workflow) and then immediately invoking `/<skill>` will produce a false "another session may have just edited it" warning. Over the course of a session, this may erode the operator's trust in the hook's signal.

**Evidence:**
The threshold was set to 120s. Per the AGENTS.md "auto-commit is authorized" rule, operators commit edits within seconds of writing them. A typical operator flow is: edit SKILL.md → save → commit → type `/<skill>`. If commit takes ~5s, the next 115s of typing `/<skill>` produces a "concurrent edit" warning.

A duplicate check already exists in `hooks/PreToolUse_skill_staleness.py` (per `hooks/skill-staleness.json`) — that hook fires on `read_file` of SKILL.md with no time threshold (it always warns on read of a freshly-edited SKILL.md). The new UserPromptSubmit staleness check overlaps this existing PreToolUse check.

**Impact:** Operator will see duplicate staleness warnings: one when they next read the SKILL.md, and one when they type the next `/<skill>` prompt. The second warning is redundant.

**Suggestion:** Either (a) bump the threshold to 30s or remove the staleness check from UserPromptSubmit (since PreToolUse already covers it), or (b) coordinate with `PreToolUse_skill_staleness.py` so only one fires. The two hooks can race to warn about the same concurrent edit.

---

### RISK-3: Hook writes state files with no cleanup; orphaned state accumulates

**Severity:** risk (medium)
**File:** `hooks/UserPromptSubmit_skill_precheck.py:355-376`
**Symptom:** `STATE_DIR = Path.home() / ".grok" / "state"` accumulates one subdirectory per session ID, with no cleanup mechanism. Each subdir gets a `skill-precheck.json` that is overwritten on every prompt. Multi-session, multi-day operation produces N session directories, each with at most one small JSON file.

**Evidence:** During this review session, multiple state directories appeared under `~/.grok/state/` (`bom_test_001`, `bom_test_002`, `ps_test_*`, `trace_sid_001`, `valid_sid_xyz`, etc.) — all created by hook test runs. After this review ends, those directories persist. The sibling quota hook uses `~/.cache/opencode/quota-injector-state.json` (single file) which avoids this.

**Impact:**
- State directory clutter over time.
- No retention policy — operators can't tell which session produced which state.
- No max-age limit — state files accumulate indefinitely.
- Cross-session confusion if a session_id is reused (unlikely but possible if a UUID generator recycles).

**Suggestion:** Either (a) consolidate into a single `~/.grok/state/skill-precheck.json` with session_id-keyed entries, or (b) document a retention policy (e.g., "delete after 30 days"), or (c) skip writing state entirely — the stderr annotation is the primary operator-visible signal, and the state file is "advisory" per the docstring. The current behavior creates files that no documented consumer reads.

---

### SUGGESTION-1: `has_critical` is computed twice

**Severity:** suggestion
**File:** `hooks/UserPromptSubmit_skill_precheck.py:369, 438`
**Symptom:** The same boolean (`has_critical`) is computed twice — once in `write_state_file` for the payload, once in `main()` to determine the exit code.

**Evidence:**
```python
# Line 369 (inside write_state_file):
"has_critical": any(w["severity"] == "critical" for w in warnings),

# Line 438 (inside main):
has_critical = any(w["severity"] == "critical" for w in all_warnings)
```

**Suggestion:** Compute once in `main()` and pass to `write_state_file` (or vice versa). Minor — readability.

---

### SUGGESTION-2: Duplicated regex and skill-listing constants between hook and `quality_gates_frontmatter`

**Severity:** suggestion
**File:** `hooks/UserPromptSubmit_skill_precheck.py:65-69, 88-94` and `hooks/scripts/quality_gates_frontmatter.py:55-67`

**Symptom:** The hook defines its own `SKILL_INVOCATION_RE`, `GO_SUB_SKILLS`, and `SKILL_ALIASES`. `quality_gates_frontmatter.py` defines its own `SKILL_INVOCATION_RE` and `SKIP_SKILL_NAMES`. The two regexes are identical strings; the two skip-lists are semantically overlapping but named differently.

**Evidence:**
- `UserPromptSubmit_skill_precheck.py:65-69` and `quality_gates_frontmatter.py:55-60`: both define `re.compile(r"(?:^|\s)/([a-z][a-z0-9-]{1,40})\b", re.MULTILINE)`.
- `UserPromptSubmit_skill_precheck.py:88-94` defines `GO_SUB_SKILLS = {grok-parallel, grok-discovery, ...}`. `quality_gates_frontmatter.py:62-67` defines `SKIP_SKILL_NAMES` containing the same set plus `help` and `grok-go`/`grok-sdlc`.

**Impact:** Two definitions to keep in sync. The sibling module's regex is also the one with the broken path-skip heuristic (BUG-1), so fixes to the hook's regex won't propagate.

**Suggestion:** Export `SKILL_INVOCATION_RE` and a `GO_SUB_SKILLS` constant from `quality_gates_frontmatter.py` (the Stop hook's module) and import them in `UserPromptSubmit_skill_precheck.py`. Eliminates drift and shares the (future-fixed) path-skip heuristic.

---

### SUGGESTION-3: No test file for the new hook

**Severity:** suggestion (per AGENTS.md "Execution receipts for executable artifacts")
**File:** `hooks/UserPromptSubmit_skill_precheck.py` (entire file)
**Symptom:** The hook has no tests in `hooks/scripts/tests/` (verified by `ls hooks/scripts/tests/` — the new test files do not include `test_skill_precheck*`). Per AGENTS.md's "Execution receipts for executable artifacts" rule, an executable artifact needs an execution receipt (tests against representative inputs), not just inspection.

**Evidence:** `ls hooks/scripts/tests/` lists `test_continuation_obligation.py`, `test_file_inference_smoke.py`, `test_quality_gate_phase2.py`, `test_scope_capability_nonce.py`, `test_self_correct_loop.py`. No `test_skill_precheck*`.

**Impact:** Future refactors of this hook will not have a regression net. The 5 distinct functions (`extract_prompt_text`, `find_skill_invocations`, `parse_depends_on`, `check_evidence_plausibility`, `check_skill`, `format_warnings`, `_safe_session_id_for_path`) each need positive and negative test cases.

**Suggestion:** Add `hooks/scripts/tests/test_skill_precheck.py` mirroring the structure of `test_hook_output_format.py` — a `_run_hook(script, payload)` helper that uses `subprocess.run` and asserts on exit code / stderr. Test cases:
- Empty stdin → exit 0, no stderr
- Malformed JSON → exit 0, no stderr (fail-open)
- Valid `/ship` → exit 0, no stderr (ship exists)
- Valid `/nonexistent-xyz` → exit 1, stderr contains "critical"
- `GROK_SESSION_ID` set → no session_id warning
- `GROK_SESSION_ID` missing → session_id warning
- Path traversal session_id (`../etc/passwd`) → state file NOT written
- BOM-prefixed stdin → BUG-2 regression test
- Path-followed-by-skill (`P:/foo/bar /also`) → BUG-1 regression test

---

### SUGGESTION-4: `extract_prompt_text` content-block path is unused in practice

**Severity:** suggestion
**File:** `hooks/UserPromptSubmit_skill_precheck.py:104-122`

**Symptom:** The function iterates `("prompt", "message", "content")` and handles list-of-dicts for each key. The `content` key handling is correct, but the iteration order means `prompt` (string) is checked first; if `prompt` is missing, `message` (string) is checked; if that's missing, `content` (list-of-dicts) is checked. For the documented Grok Build UserPromptSubmit envelope, only `prompt` is used (`docs/user-guide/10-hooks.md:218-235`).

**Evidence:** The Grok Build hook envelope example shows the prompt as a top-level `prompt` string. The Claude Code compat path (snake_case) is converted to camelCase by the SDK before reaching the hook. The list-of-dicts path is for Claude multi-block content — already converted by SDK.

**Suggestion:** Either remove the `content` list-of-dicts branch (it's dead code for the documented envelope), or document that the hook accepts Claude-style multi-block envelopes. Currently the branch exists but its correctness against actual envelopes is unverified.

---

### SUGGESTION-5: Skill alias fallback only checks `SKILL_ALIASES`, not reverse

**Severity:** suggestion
**File:** `hooks/UserPromptSubmit_skill_precheck.py:79-83, 218-235`

**Symptom:** `SKILL_ALIASES` maps `grok-go → go`, `grok-sdlc → go`, `research → www`. When the user types `/grok-go`, the hook first checks `find_skill_md("grok-go")` (which exists — `skills/grok-go/SKILL.md` exists on this host per `ls skills/grok-go/`), then never falls back to checking `go`.

But what if the user types `/go` (canonical)? `find_skill_md("go")` returns the canonical SKILL.md. Good. What if user types `/sdlc`? It's NOT in SKILL_ALIASES, so the hook only checks `find_skill_md("sdlc")` which doesn't exist → false "not found" warning.

**Evidence:** `SKILL_ALIASES = {"grok-go": "go", "grok-sdlc": "go", "research": "www"}`. The /go SKILL.md (line 50-52) lists aliases: `/grok-go  /grok-sdlc  /sdlc`. So `/sdlc` is documented as an alias for `/go`, but the hook's SKILL_ALIASES only includes `grok-sdlc`, not `sdlc`.

**Impact:** Typing `/sdlc` (a documented /go alias) produces a false "Skill '/sdlc' not found" warning.

**Suggestion:** Add `"sdlc": "go"` to SKILL_ALIASES. Or better: derive the alias map from a single source (e.g., read from `/go`'s frontmatter or from the skill-catalog).

---

### GAP-1: SKILL.md changes (skills/go, skills/ship-py, skills/ship-rhai, test_ship_receipt) — prose-only, low risk

**Severity:** gap (informational)
**Files:**
- `skills/go/SKILL.md:808` — path fix `ship/SKILL.md` → `ship-rhai/SKILL.md`
- `skills/ship-py/SKILL.md:83-91` — added post-ship wiki capture section
- `skills/ship-py/SKILL.md:95` — added "If durable findings exist, /wiki runs before GO DONE" hard rule
- `skills/ship-rhai/SKILL.md:74-82` — same as ship-py
- `skills/ship-rhai/SKILL.md:86` — same hard rule
- `skills/ship-rhai/tests/test_ship_receipt.py:7` — test path fix `skills/ship/tests/` → `skills/ship-rhai/tests/`

**Review:**
- The path fixes are correct (the previous `ship/` directory no longer exists; `ship-rhai/` is canonical per AGENTS.md `ship-rhai` references).
- The "post-ship knowledge capture" addition is consistent across ship-py and ship-rhai. It is conditional ("if the work produced durable findings") which respects the AGENTS.md "wiki capture: non-obvious + verified + durable + distinct" gate.
- The hard-rule addition ("/wiki runs before GO DONE") is consistent with AGENTS.md's `WIKI:` auto-capture rule for session boundaries.

**No issues found** in the SKILL.md changes. They are mechanical correctness fixes plus a documentation improvement aligned with workspace rules.

---

### GAP-2: `skill-precheck.json` registration uses absolute Windows path

**Severity:** gap (informational)
**File:** `hooks/skill-precheck.json:6`

**Evidence:**
```json
{ "type": "command", "command": "python C:/Users/brsth/.grok/hooks/UserPromptSubmit_skill_precheck.py", "timeout": 3 }
```

This absolute path locks the registration to a single user's home directory. If this hook is meant to be shared (per `~/.grok/hooks/*.json` is "always trusted" per `docs/user-guide/10-hooks.md:62`), the absolute path prevents portability.

**Impact:** Low. The `~/.grok/hooks/*.json` directory is by definition user-scoped (`~`). Sibling hooks like `quota-availability-injector.json` also use absolute paths. This is the convention on this host.

**Suggestion:** No action needed unless hooks are meant to be team-shared. If shared, use `~/.grok/hooks/UserPromptSubmit_skill_precheck.py` (relative to the JSON file's directory).

---

### GAP-3: Hook has no `host:` provenance tag (cross-host applicability)

**Severity:** gap (per AGENTS.md skill authoring convention)

**Symptom:** `UserPromptSubmit_skill_precheck.py` has a docstring but no `host:` field (Python files don't typically have this, but the hook's behavior — JSON envelope parsing, camelCase keys, `GROK_SESSION_ID` — assumes Grok Build). If installed on Claude Code, the hook would fail to find `GROK_SESSION_ID` and would always emit the session_id warning (noise).

**Evidence:** Docstring says "Grok Build uses camelCase keys" (line 102) — explicit Grok Build assumption.

**Suggestion:** Add a one-line comment to the docstring:
```python
"""... (existing docstring) ...
Host applicability: Grok Build only. Claude Code compat may work but emits
constant session_id warnings (no GROK_SESSION_ID env var).
"""
```

---

## Summary

| Severity     | Count |
|--------------|-------|
| bug          | 3     |
| risk         | 3     |
| suggestion   | 5     |
| gap          | 3     |
| **Total**    | **14** |

**Critical findings requiring action before merge:**

1. **BUG-2 (BOM silent failure)** — if Grok Build dispatcher ever emits a BOM-prefixed JSON, the hook is invisible. One-line fix: strip BOM before `json.loads`.
2. **BUG-1 (path-skip heuristic)** — false-positive skill detection on prompts containing Windows paths. Fix improves both the new hook and the sibling `quality_gates_frontmatter.scan_invoked_skills`.
3. **BUG-3 (warning header suppressed)** — minor UX issue; one-line fix in `format_warnings`.

**Recommendations:** fix BUG-1, BUG-2, BUG-3; address RISK-1 (Unicode whitelist) and RISK-2 (staleness duplication) before declaring "done"; add tests (SUGGESTION-3).

---

## Receipts (verification trail)

Findings were verified by:

1. **Direct file reads** (all paths above).
2. **Import test**: `python -c "import ast; ast.parse(open('hooks/UserPromptSubmit_skill_precheck.py').read())"` → OK.
3. **Hook execution tests** (subprocess.run with crafted stdin):
   - Empty stdin → exit 0
   - Valid `/nonexistent-skill` → exit 1, stderr critical warning
   - Valid `/ship` → exit 0, no stderr
   - BOM-prefixed stdin → exit 0, no stderr (BUG-2)
4. **Regex unit tests** (BUG-1): constructed test strings, confirmed false-positive `also` detection after `P:/Users/x/y.md`.
5. **Sibling scan test**: `scan_invoked_skills(['{"type":"user","content":"see P:/Users/x/y.md /also"}'])` returns `{'also', 'ship'}` — confirms same bug exists in `quality_gates_frontmatter.py`.
6. **safe_sid test**: `_safe_session_id_for_path('id-тест')` returns `'id-тест'` — confirms RISK-1.
7. **format_warnings test**: tested all four severity combinations; confirmed BUG-3.
8. **Sibling hook check**: `hooks/PreToolUse_skill_staleness.py` exists (`hooks/skill-staleness.json`) — confirmed RISK-2 overlap.
