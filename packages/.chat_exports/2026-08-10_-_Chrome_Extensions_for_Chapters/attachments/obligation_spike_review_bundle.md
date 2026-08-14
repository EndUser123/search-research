# Obligation-Ledger Spike — Complete Review Bundle

Generated: 2026-08-10T03:41:53Z
Session: 019fe88b-af8e-77b2-87cd-04711b7f8257
Repository: ~/.grok

---

## Table of Contents

1. Commit log (5 spike commits)
2. Unified diff (all changes across 5 commits)
3. Final file states (4 modified/new files)
4. Retired file (equivalence-bypass-gate.json)
5. Test harnesses (3 test files)
6. Runtime receipts (shadow log, cond-freshness, verification receipts)
7. /review artifacts (FINDINGS.md, findings.json, _run.json)

---

## 1. Commit Log

```
319845a retire equivalence_bypass_gate — replaced by structural conditional obligation
eb07a80 pool_test: add --provider mode for full API discovery testing
533df93 fleet-models: registry cleanup — normalize nim->nvidia, retire dead models, add replacement
88fff65 ship-py: extract shared dispatch primitives, eliminating 690 lines of duplication
d446b54 maintain: properly integrate /config-audit for AGENTS.md optimization
955bdc1 pool_suites: improve exact-match scorer with JSON extraction + structural comparison
67635d7 maintain: AGENTS.md fix routes to /config-audit (not /brain+/go)
d33d5d9 maintain: AGENTS.md size breach is NOW action, not LATER
c0c0f88 pool_suites: fix exact-match scorer for verbose reasoning models
f41c3fe fleet_health: disk forecasting, recovery tracking, threshold trigger
63ff276 ship-py: convert check, review, refactor, trace to orchestrator-controlled dispatch
888fdfb ship-py: convert risk phase to orchestrator-controlled dispatch
4a2e4d3 model_router: add provider alias map — 13/20 active candidates now have evidence
85b83c2 fix(todo): remove unnecessary session-marker hook; agent passes literal session ID
b690c47 ship-py: 6 fixes from /tp review + /risk scan + /refactor plan
2309233 fix INT-001: freshness binding uses receipt timestamp not Stop-fire time
34c2e5b spike v3: transcript as root authority for hooks mutation detection
8a8a258 fix(todo): session-scope transcript scanners to prevent sibling contamination
cd61841 spike v2: fix all 3 authority gaps (trigger coverage, state tampering, freshness)
fb19ba8 ship-py: replace trace auto-skip with gate-block + clear guidance
34efa56 agy: remove wrong depends_on debrief declaration
747e04d model-web+todo: wrap cmd_release in _claim_lock + todo skill recommends on A/B decisions
f9ca5e9 spike: conditional-obligation prototype for hooks/** -> /review REQUIRED
```

## 2. Unified Diff

```diff
diff --git a/hooks/PostToolUse_conditional_obligation_writer.py b/hooks/PostToolUse_conditional_obligation_writer.py
new file mode 100644
index 0000000..536b976
--- /dev/null
+++ b/hooks/PostToolUse_conditional_obligation_writer.py
@@ -0,0 +1,159 @@
+#!/usr/bin/env python3
+"""
+PostToolUse hook: conditional obligation writer for skill requirements.
+
+SPIKE PROTOTYPE (2026-08-09): demonstrates the conditional-rule writer
+for the obligation-ledger direction. When a file under hooks/** is modified,
+this hook appends a conditional skill obligation (/review REQUIRED) to a
+session-scoped state file. The quality_gate/main.py Stop hook reads this
+state and merges the obligated skill into invoked_skills, causing the
+existing quality_gates evidence check to fire.
+
+Rule prototyped:
+    IF file under hooks/** is modified
+    THEN /review becomes REQUIRED for this session
+
+Trigger: observable PostToolUse event (search_replace|write), NOT model prose.
+The constrained model has no normal call path to create or remove this state.
+
+Limitations (honest):
+- The obligation state file is model-deletable via run_terminal_command
+  (deliberate circumvention, not a normal path). A future version can
+  add transcript-cross-check: if the transcript shows a hooks/ write but
+  no state file exists at Stop time, treat as tampering.
+- Satisfaction relies on existing /review evidence glob (_run.json),
+  which is model-writable (workflow evidence, NOT unforgeable receipt).
+
+Registration: quality-gate.json ΓåÆ PostToolUse ΓåÆ matcher search_replace|write
+"""
+from __future__ import annotations
+
+import json
+import os
+import re
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+
+STATE_DIR = Path.home() / ".grok" / "hooks" / "state"
+
+#: Paths that trigger the conditional obligation.
+#: Matches any file inside a hooks/ directory under .grok or .claude roots.
+HOOKS_PATH_RE = re.compile(
+    r"(?:^|/)(?:\.grok|\.claude)/hooks/",
+    re.IGNORECASE,
+)
+
+#: The skill obligated when the trigger fires.
+OBLIGATED_SKILL = "review"
+
+
+def _state_file(session_id: str) -> Path:
+    return STATE_DIR / f"conditional-skill-obligation-{session_id}.json"
+
+
+def _read_existing(path: Path) -> dict:
+    if not path.exists():
+        return {"session_id": "", "obligations": []}
+    try:
+        data = json.loads(path.read_text(encoding="utf-8"))
+        if isinstance(data, dict) and "obligations" in data:
+            return data
+    except (json.JSONDecodeError, OSError):
+        pass
+    return {"session_id": "", "obligations": []}
+
+
+def _write_obligation(session_id: str, file_path: str, tool_name: str) -> dict:
+    """Append (idempotently) a conditional skill obligation to the state file."""
+    STATE_DIR.mkdir(parents=True, exist_ok=True)
+    path = _state_file(session_id)
+
+    data = _read_existing(path)
+    data["session_id"] = session_id
+
+    # Idempotency: don't duplicate if /review obligation already exists
+    existing_skills = {
+        o.get("skill_name", "").lstrip("/")
+        for o in data.get("obligations", [])
+        if o.get("status") == "REQUIRED"
+    }
+    if OBLIGATED_SKILL in existing_skills:
+        # Already obligated ΓÇö just update the last-trigger provenance
+        for o in data["obligations"]:
+            if o.get("skill_name", "").lstrip("/") == OBLIGATED_SKILL:
+                o["trigger_count"] = o.get("trigger_count", 1) + 1
+                o["last_trigger_provenance"] = (
+                    f"{tool_name} on {file_path} at "
+                    f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
+                )
+                break
+    else:
+        data["obligations"].append({
+            "skill_name": f"/{OBLIGATED_SKILL}",
+            "trigger_source": "conditional_rule:hooks_modified_requires_review",
+            "trigger_provenance": (
+                f"{tool_name} on {file_path} at "
+                f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
+            ),
+            "last_trigger_provenance": (
+                f"{tool_name} on {file_path} at "
+                f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
+            ),
+            "trigger_count": 1,
+            "created_at": datetime.now(timezone.utc).isoformat()[:19] + "Z",
+            "status": "REQUIRED",
+            "satisfied_by": None,
+            "note": "Conditional obligation from hooks/** modification. "
+                    "Satisfaction via existing quality_gates evidence glob "
+                    "(workflow evidence, not unforgeable receipt).",
+        })
+
+    # Atomic write
+    tmp = path.with_suffix(".tmp")
+    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
+    os.replace(str(tmp), str(path))
+    return data
+
+
+def main() -> int:
+    try:
+        data = json.load(sys.stdin)
+    except Exception:
+        return 0  # fail-open
+
+    session_id = data.get("sessionId", "")
+    tool_name = data.get("toolName", "")
+    tool_input = data.get("toolInput", {})
+
+    # Validate session ID (UUID format)
+    if not re.match(r"^[0-9a-f-]{36}$", session_id):
+        return 0
+
+    # Extract file path from tool input
+    file_path = (
+        tool_input.get("file_path")
+        or tool_input.get("path")
+        or ""
+    )
+    if not file_path or not isinstance(file_path, str):
+        return 0
+
+    # Normalize for matching
+    norm = file_path.replace("\\", "/")
+
+    # Check if this is a hooks/** modification
+    if not HOOKS_PATH_RE.search(norm):
+        return 0  # not a hooks/ file ΓÇö no obligation
+
+    # Write the conditional obligation
+    try:
+        _write_obligation(session_id, norm, tool_name)
+    except Exception:
+        pass  # fail-open
+
+    return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
diff --git a/hooks/equivalence-bypass-gate.json b/hooks/equivalence-bypass-gate.json
index d964c73..4d8ff3a 100644
--- a/hooks/equivalence-bypass-gate.json
+++ b/hooks/equivalence-bypass-gate.json
@@ -1,12 +1,5 @@
 {
   "hooks": {
-    "Stop": [
-      {
-        "matcher": "",
-        "hooks": [
-          { "type": "command", "command": "python C:/Users/brsth/.grok/hooks/scripts/equivalence_bypass_gate.py", "timeout": 3 }
-        ]
-      }
-    ]
+    "Stop": []
   }
 }
diff --git a/hooks/quality-gate.json b/hooks/quality-gate.json
index 1af1f2b..86c2cfd 100644
--- a/hooks/quality-gate.json
+++ b/hooks/quality-gate.json
@@ -50,6 +50,11 @@
             "type": "command",
             "command": "python \"C:/Users/brsth/.grok/hooks/PostToolUse_auto_verify.py\"",
             "timeout": 15
+          },
+          {
+            "type": "command",
+            "command": "python \"C:/Users/brsth/.grok/hooks/PostToolUse_conditional_obligation_writer.py\"",
+            "timeout": 5
           }
         ]
       },
diff --git a/hooks/scripts/equivalence_bypass_gate.retired.md b/hooks/scripts/equivalence_bypass_gate.retired.md
new file mode 100644
index 0000000..03648c4
--- /dev/null
+++ b/hooks/scripts/equivalence_bypass_gate.retired.md
@@ -0,0 +1,30 @@
+# equivalence_bypass_gate ΓÇö RETIRED 2026-08-09
+
+Replaced by structural conditional-obligation mechanism in `quality_gate/main.py`.
+
+## Why retired
+
+The old gate used prose-semantic regex to detect skill-equivalence bypass claims.
+It produced **255 false blocks on 2026-08-09 alone** (`hook_failures.jsonl`) ΓÇö
+it could not distinguish DISCUSSING a bypass from COMMITTING one.
+
+## What replaced it
+
+The replacement enforces the **OBLIGATION, not the JUSTIFICATION**:
+
+- hooks/** modified ΓåÆ `/review` REQUIRED (detected from transcript + mutation receipts)
+- `quality_gate/main.py` blocks until `/review` evidence satisfies the obligation
+- Prose is irrelevant ΓÇö the mechanism reads state, not text
+
+See commits `f9ca5e9` through `2309233` for the full implementation.
+Live acceptance: cases C, D, E, F, H confirmed through real runtime.
+
+## Threat model
+
+This mechanism prevents semantic self-exemption, alternate ordinary mutation
+paths (via receipt corroboration), stale evidence (via freshness binding), and
+tampering with derived obligation state. It assumes the runtime's
+transcript/control-plane files are not deliberately destroyed or rewritten to
+defeat enforcement. Because hooks and the model operate within the same
+host/user trust domain, cryptographic or malicious-control-plane tamper
+resistance is not claimed.
diff --git a/hooks/scripts/quality_gate/main.py b/hooks/scripts/quality_gate/main.py
index 8362977..220fd96 100644
--- a/hooks/scripts/quality_gate/main.py
+++ b/hooks/scripts/quality_gate/main.py
@@ -68,6 +68,70 @@ from quality_gate.receipt_validator import (  # noqa: E402
 )
 
 
+# --- Conditional obligation helpers (spike 2026-08-09) ---
+#
+# Replaces equivalence_bypass_gate (retired 2026-08-09). Enforces the
+# OBLIGATION, not the prose JUSTIFICATION: hooks/** modified ΓåÆ /review
+# REQUIRED ΓåÆ quality_gate blocks until evidence satisfies.
+#
+# Threat model:
+#   Prevents: semantic self-exemption, stale evidence, tampering with
+#   derived obligation state (cache), alternate mutation paths (via
+#   receipt corroboration).
+#   Does NOT prevent: deliberate control-plane sabotage (model destroys
+#   transcript/receipts to erase evidence). Hooks and the model operate
+#   within the same host/user trust domain ΓÇö no file-based mechanism can
+#   claim cryptographic tamper resistance under that constraint.
+#   This is a consciously accepted trust-model boundary, not a bug.
+
+#: Paths that trigger /review obligation when modified.
+import re as _re_cond
+_HOOKS_PATH_RE = _re_cond.compile(
+    r"(?:^|/)(?:\.grok|\.claude)/hooks/",
+    _re_cond.IGNORECASE,
+)
+
+
+def _detect_hooks_mutation_from_receipts(session_id: str) -> str | None:
+    """Check mutation receipts for hooks/** modifications.
+
+    Returns the timestamp of the LATEST hooks/** mutation, or None if no
+    hooks/** mutation was found. The timestamp is used for freshness binding
+    (evidence must post-date it).
+
+    Authority source: P:/.artifacts/{session_id}/mutation/mutation-receipts.jsonl
+    Written by: mutation_post.py (PostToolUse hook, runtime-written)
+    Model-editable: yes (model can rm the file), but deletion is itself a
+    mutation event, and the receipts are append-only within a session.
+    """
+    receipt_path = Path(f"P:/.artifacts/{session_id}/mutation/mutation-receipts.jsonl")
+    if not receipt_path.exists():
+        return None
+
+    latest_ts = None
+    try:
+        for line in receipt_path.read_text(encoding="utf-8").strip().split("\n"):
+            if not line:
+                continue
+            try:
+                receipt = json.loads(line)
+            except json.JSONDecodeError:
+                continue
+            # Check changed_files for hooks/** paths
+            for cf in receipt.get("changed_files", []):
+                fp = cf.get("path", "")
+                norm = fp.replace("\\", "/")
+                if _HOOKS_PATH_RE.search(norm):
+                    ts = receipt.get("completed_at", "")
+                    if ts and (latest_ts is None or ts > latest_ts):
+                        latest_ts = ts
+                    break  # one hooks path in this receipt is enough
+    except OSError:
+        pass
+
+    return latest_ts
+
+
 def main():
     hook_started = time.perf_counter()
     # Step 1: Read payload
@@ -165,6 +229,16 @@ def main():
     # Track skills invoked this session (carried across Stop fires)
     invoked_skills = prev_invoked_skills
 
+    # Track hooks/** mutations from transcript (primary operational evidence,
+    # spike 2026-08-09). The transcript is runtime-written, append-only, and
+    # already trusted for invoked_skills scanning. It is NOT tamper-proof
+    # "root authority" ΓÇö it is the strongest available operational evidence
+    # source within the current trust boundary. We use it as a BOOLEAN
+    # trigger (did a hooks edit happen?) ΓÇö the actual timestamp for freshness
+    # binding comes from mutation receipts (which record completed_at at
+    # PostToolUse fire time, close to the actual edit time).
+    _transcript_hooks_mutation_detected = False
+
     with open(chat_file, "r", encoding="utf-8") as f:
         for line in f:
             current_line += 1
@@ -211,6 +285,9 @@ def main():
                             code_modified_after_verification = True
                         if file_path not in modified_files:
                             modified_files.append(file_path)
+                    # Detect hooks/** mutations from transcript (primary trigger)
+                    if file_path and _HOOKS_PATH_RE.search(file_path.replace("\\", "/")):
+                        _transcript_hooks_mutation_detected = True
 
                 if tool_name == "run_terminal_command":
                     cmd = args.get("command", "")
@@ -222,6 +299,41 @@ def main():
                     if _has_shell_write_signal(cmd):
                         unclassified_write_observed = True
 
+    # --- Conditional skill obligations (spike 2026-08-09, revised) ---
+    # PRIMARY EVIDENCE: transcript (chat_history.jsonl) ΓÇö runtime-written,
+    # append-only, already trusted for invoked_skills scanning. Provides
+    # boolean trigger detection (did a hooks edit happen?).
+    # SECONDARY: mutation receipts ΓÇö provide the actual trigger timestamp
+    # for freshness binding (completed_at at PostToolUse fire time).
+    # Rule: if the transcript shows a search_replace/write to a hooks/** path,
+    # OR mutation receipts show a hooks/** change, /review becomes REQUIRED.
+    # Freshness binding uses the receipt timestamp when available (correct
+    # edit time). When only the transcript detects it (receipts deleted),
+    # no freshness binding is applied (evidence from any time in-session
+    # satisfies ΓÇö conservative but not Stop-fire-time-biased).
+    _receipt_hooks_ts = _detect_hooks_mutation_from_receipts(session_id)
+    _hooks_mutation_ts = _receipt_hooks_ts  # receipt has the real timestamp
+    if not _hooks_mutation_ts and _transcript_hooks_mutation_detected:
+        # Transcript detected hooks mutation but receipts unavailable.
+        # Trigger the obligation without freshness binding.
+        _hooks_mutation_ts = None  # trigger fires, but no min_timestamp
+    if _transcript_hooks_mutation_detected or _receipt_hooks_ts:
+        invoked_skills.add("review")
+        # Record the latest trigger timestamp for freshness binding.
+        # Written to a session-scoped state file that check_quality_gates reads.
+        _cond_freshness_path = (
+            Path.home() / ".grok" / "hooks" / "state"
+            / f"cond-freshness-{session_id}.json"
+        )
+        try:
+            _cond_freshness_path.parent.mkdir(parents=True, exist_ok=True)
+            _cond_freshness_path.write_text(
+                json.dumps({"review": _hooks_mutation_ts}),
+                encoding="utf-8",
+            )
+        except OSError:
+            pass
+
     # Update state file with (mtime, size, last_line) for compaction-safe tracking
     # plus verification state carried across Stop hook fires.
     try:
diff --git a/hooks/scripts/quality_gates_frontmatter.py b/hooks/scripts/quality_gates_frontmatter.py
index 3ac1a88..91bfad0 100644
--- a/hooks/scripts/quality_gates_frontmatter.py
+++ b/hooks/scripts/quality_gates_frontmatter.py
@@ -405,7 +405,8 @@ def get_quality_gates(skill_name: str) -> list[dict]:
 # ---------------------------------------------------------------------------
 
 def check_evidence(pattern: str, workspace_root: str = "",
-                   session_id: str = "", session_field: str = "") -> tuple[bool, str, bool]:
+                   session_id: str = "", session_field: str = "",
+                   min_timestamp: str = "") -> tuple[bool, str, bool]:
     """Check whether an evidence glob pattern matches any file on disk.
 
     Expands ``~`` and ``{workspace}`` in the pattern.  Uses recursive glob.
@@ -415,6 +416,10 @@ def check_evidence(pattern: str, workspace_root: str = "",
     This prevents cross-session evidence contamination on multi-agent hosts
     where multiple sessions write evidence artifacts to the same directory tree.
 
+    When ``min_timestamp`` is provided (ISO-8601 UTC), only files whose mtime
+    is at or after that timestamp are accepted. This implements freshness
+    binding for conditional obligations: evidence must post-date the trigger.
+
     Returns ``(found, path, stale)`` where:
     - ``found``: True if at least one file matches (and passes session filter if set)
     - ``path``: the most recent matching file path (empty if none)
@@ -452,6 +457,29 @@ def check_evidence(pattern: str, workspace_root: str = "",
     if not matches:
         return False, "", False
 
+    # Freshness binding for conditional obligations (spike 2026-08-09):
+    # reject evidence whose mtime predates the obligation trigger.
+    if min_timestamp:
+        try:
+            from datetime import datetime as _dt
+            min_dt = _dt.fromisoformat(min_timestamp.replace("Z", "+00:00"))
+            filtered = []
+            for m in matches:
+                try:
+                    file_dt = _dt.fromtimestamp(
+                        os.path.getmtime(m), tz=min_dt.tzinfo
+                    )
+                    if file_dt >= min_dt:
+                        filtered.append(m)
+                except OSError:
+                    continue
+            matches = filtered if filtered else []
+        except (ValueError, TypeError):
+            pass  # invalid timestamp format ΓÇö don't filter
+
+    if not matches:
+        return False, "", False
+
     # Find the most recent match
     matches.sort(
         key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
@@ -753,6 +781,11 @@ def check_quality_gates(
     (marked as satisfied) ΓÇö e.g. /wiki gate only blocks sessions that
     actually produced durable findings.
 
+    For conditionally-obligated skills (e.g. /review required because
+    hooks/** was modified), reads the ``required_after`` timestamp from
+    a session-scoped state file and applies freshness binding: evidence
+    must post-date the obligation trigger.
+
     Returns a QualityGateReport with the aggregated result.
     """
     missing_gates: list[GateResult] = []
@@ -765,6 +798,17 @@ def check_quality_gates(
     waiver = read_waiver(session_id)
     waived = set(waiver.get("waived_skills", []))
 
+    # Read conditional-obligation freshness binding (spike 2026-08-09).
+    # Written by quality_gate/main.py when it detects hooks/** mutations.
+    # Keyed by skill_name ΓåÆ required_after timestamp.
+    _cond_freshness: dict[str, str] = {}
+    _cond_path = Path.home() / ".grok" / "hooks" / "state" / f"cond-freshness-{session_id}.json"
+    if _cond_path.exists():
+        try:
+            _cond_freshness = json.loads(_cond_path.read_text(encoding="utf-8"))
+        except (json.JSONDecodeError, OSError):
+            pass
+
     for skill_name in sorted(invoked_skills):
         if skill_name in waived:
             waived_skills.append(skill_name)
@@ -796,8 +840,13 @@ def check_quality_gates(
                     ))
                     continue
 
+            # Freshness binding: if this skill has a conditional obligation
+            # with a required_after timestamp, pass it to check_evidence.
+            _min_ts = _cond_freshness.get(skill_name, "")
+
             found, found_path, stale = check_evidence(
-                pattern, workspace_root, session_id, session_field)
+                pattern, workspace_root, session_id, session_field,
+                min_timestamp=_min_ts)
 
             # contains_all gate: also check a field has all required values
             contains_all_spec = gate.get("contains_all", {})
```

## 3. Final File States

### PostToolUse_conditional_obligation_writer.py (NEW — cache writer)
Path: `hooks/PostToolUse_conditional_obligation_writer.py`

```python
#!/usr/bin/env python3
"""
PostToolUse hook: conditional obligation writer for skill requirements.

SPIKE PROTOTYPE (2026-08-09): demonstrates the conditional-rule writer
for the obligation-ledger direction. When a file under hooks/** is modified,
this hook appends a conditional skill obligation (/review REQUIRED) to a
session-scoped state file. The quality_gate/main.py Stop hook reads this
state and merges the obligated skill into invoked_skills, causing the
existing quality_gates evidence check to fire.

Rule prototyped:
    IF file under hooks/** is modified
    THEN /review becomes REQUIRED for this session

Trigger: observable PostToolUse event (search_replace|write), NOT model prose.
The constrained model has no normal call path to create or remove this state.

Limitations (honest):
- The obligation state file is model-deletable via run_terminal_command
  (deliberate circumvention, not a normal path). A future version can
  add transcript-cross-check: if the transcript shows a hooks/ write but
  no state file exists at Stop time, treat as tampering.
- Satisfaction relies on existing /review evidence glob (_run.json),
  which is model-writable (workflow evidence, NOT unforgeable receipt).

Registration: quality-gate.json → PostToolUse → matcher search_replace|write
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path.home() / ".grok" / "hooks" / "state"

#: Paths that trigger the conditional obligation.
#: Matches any file inside a hooks/ directory under .grok or .claude roots.
HOOKS_PATH_RE = re.compile(
    r"(?:^|/)(?:\.grok|\.claude)/hooks/",
    re.IGNORECASE,
)

#: The skill obligated when the trigger fires.
OBLIGATED_SKILL = "review"


def _state_file(session_id: str) -> Path:
    return STATE_DIR / f"conditional-skill-obligation-{session_id}.json"


def _read_existing(path: Path) -> dict:
    if not path.exists():
        return {"session_id": "", "obligations": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "obligations" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"session_id": "", "obligations": []}


def _write_obligation(session_id: str, file_path: str, tool_name: str) -> dict:
    """Append (idempotently) a conditional skill obligation to the state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = _state_file(session_id)

    data = _read_existing(path)
    data["session_id"] = session_id

    # Idempotency: don't duplicate if /review obligation already exists
    existing_skills = {
        o.get("skill_name", "").lstrip("/")
        for o in data.get("obligations", [])
        if o.get("status") == "REQUIRED"
    }
    if OBLIGATED_SKILL in existing_skills:
        # Already obligated — just update the last-trigger provenance
        for o in data["obligations"]:
            if o.get("skill_name", "").lstrip("/") == OBLIGATED_SKILL:
                o["trigger_count"] = o.get("trigger_count", 1) + 1
                o["last_trigger_provenance"] = (
                    f"{tool_name} on {file_path} at "
                    f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
                )
                break
    else:
        data["obligations"].append({
            "skill_name": f"/{OBLIGATED_SKILL}",
            "trigger_source": "conditional_rule:hooks_modified_requires_review",
            "trigger_provenance": (
                f"{tool_name} on {file_path} at "
                f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
            ),
            "last_trigger_provenance": (
                f"{tool_name} on {file_path} at "
                f"{datetime.now(timezone.utc).isoformat()[:19]}Z"
            ),
            "trigger_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat()[:19] + "Z",
            "status": "REQUIRED",
            "satisfied_by": None,
            "note": "Conditional obligation from hooks/** modification. "
                    "Satisfaction via existing quality_gates evidence glob "
                    "(workflow evidence, not unforgeable receipt).",
        })

    # Atomic write
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(path))
    return data


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open

    session_id = data.get("sessionId", "")
    tool_name = data.get("toolName", "")
    tool_input = data.get("toolInput", {})

    # Validate session ID (UUID format)
    if not re.match(r"^[0-9a-f-]{36}$", session_id):
        return 0

    # Extract file path from tool input
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or ""
    )
    if not file_path or not isinstance(file_path, str):
        return 0

    # Normalize for matching
    norm = file_path.replace("\\", "/")

    # Check if this is a hooks/** modification
    if not HOOKS_PATH_RE.search(norm):
        return 0  # not a hooks/ file — no obligation

    # Write the conditional obligation
    try:
        _write_obligation(session_id, norm, tool_name)
    except Exception:
        pass  # fail-open

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### quality_gate/main.py (MODIFIED — conditional obligation reader + trigger detection)
Path: `hooks/scripts/quality_gate/main.py`

```python
#!/usr/bin/env python3
"""Stop hook entry point for the quality_gate package.

Reads the Stop hook payload from stdin, scans the session transcript,
determines whether completion was over-claimed (modification + claim without
verification), and either emits a structured JSON-block decision or exits
silently (fail-open allow).

The decision logic is split across three focused modules:
  - receipt_validator: receipt parsing, scope binding, fingerprint checks
  - obligation_manager: continuation-obligation lifecycle and satisfaction
  - gate_diagnostics: pattern catalogues, file hints, transcript discovery,
                        trace logging, and the stable enforcement-health API

This module is the routing layer. It does not own any persistence or
diagnostic logic — it composes the three modules into the Stop decision.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# Bootstrap sys.path so this module works both as part of the package and
# standalone (loaded by tests via subprocess).
_THIS_DIR = Path(__file__).resolve().parent
_PARENT = _THIS_DIR.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

import worktree_identity as _wt_id  # noqa: E402
import quality_gates_frontmatter as _qg  # noqa: E402

from quality_gate.gate_diagnostics import (  # noqa: E402
    _build_file_hints,
    _claim_made,
    _cleanup_nudge_state,
    _effective_block_decision,
    _find_transcript,
    _has_shell_write_signal,
    _has_verification_signal,
    _is_code_file,
    _is_excluded_path,
    _is_verification_stale,
    _quality_gate_check,
    _read_nudge_state,
    _receipt_gate_mode,
    _write_hook_error,
    _write_trace_log,
)
from quality_gate.obligation_manager import (  # noqa: E402
    _check_obligation_satisfied,
    _clear_obligation,
    _format_obligation_scope,
    _obligation_block_message,
    _read_obligation,
    _write_obligation,
)
from quality_gate.receipt_validator import (  # noqa: E402
    _check_receipt_coverage,
    _normalize_path,
    _normalize_workspace,
    _read_receipts,
    _shadow_log_file,
)


# --- Conditional obligation helpers (spike 2026-08-09) ---
#
# Replaces equivalence_bypass_gate (retired 2026-08-09). Enforces the
# OBLIGATION, not the prose JUSTIFICATION: hooks/** modified → /review
# REQUIRED → quality_gate blocks until evidence satisfies.
#
# Threat model:
#   Prevents: semantic self-exemption, stale evidence, tampering with
#   derived obligation state (cache), alternate mutation paths (via
#   receipt corroboration).
#   Does NOT prevent: deliberate control-plane sabotage (model destroys
#   transcript/receipts to erase evidence). Hooks and the model operate
#   within the same host/user trust domain — no file-based mechanism can
#   claim cryptographic tamper resistance under that constraint.
#   This is a consciously accepted trust-model boundary, not a bug.

#: Paths that trigger /review obligation when modified.
import re as _re_cond
_HOOKS_PATH_RE = _re_cond.compile(
    r"(?:^|/)(?:\.grok|\.claude)/hooks/",
    _re_cond.IGNORECASE,
)


def _detect_hooks_mutation_from_receipts(session_id: str) -> str | None:
    """Check mutation receipts for hooks/** modifications.

    Returns the timestamp of the LATEST hooks/** mutation, or None if no
    hooks/** mutation was found. The timestamp is used for freshness binding
    (evidence must post-date it).

    Authority source: P:/.artifacts/{session_id}/mutation/mutation-receipts.jsonl
    Written by: mutation_post.py (PostToolUse hook, runtime-written)
    Model-editable: yes (model can rm the file), but deletion is itself a
    mutation event, and the receipts are append-only within a session.
    """
    receipt_path = Path(f"P:/.artifacts/{session_id}/mutation/mutation-receipts.jsonl")
    if not receipt_path.exists():
        return None

    latest_ts = None
    try:
        for line in receipt_path.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                receipt = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Check changed_files for hooks/** paths
            for cf in receipt.get("changed_files", []):
                fp = cf.get("path", "")
                norm = fp.replace("\\", "/")
                if _HOOKS_PATH_RE.search(norm):
                    ts = receipt.get("completed_at", "")
                    if ts and (latest_ts is None or ts > latest_ts):
                        latest_ts = ts
                    break  # one hooks path in this receipt is enough
    except OSError:
        pass

    return latest_ts


def main():
    hook_started = time.perf_counter()
    # Step 1: Read payload
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    stop_active = data.get("stopHookActive", False)
    reason = data.get("reason", "")
    last_message = data.get("lastAssistantMessage", "")
    session_id = data.get("sessionId", "")
    workspace_root = data.get("workspaceRoot", "")

    # Step 2: Termination conditions
    if reason != "end_turn":
        sys.exit(0)

    if not re.match(r"^[0-9a-f-]{36}$", session_id):
        sys.exit(0)

    # Step 3: Claim detection from lastAssistantMessage (with negation check)
    claim = _claim_made(last_message)

    # ship-py pipeline completion is now enforced by the generalized quality_gates
    # frontmatter (contains_all gate). No hardcoded check needed here.

    if not claim and not stop_active:
        sys.exit(0)

    # Step 4: Locate transcript
    chat_file = _find_transcript(workspace_root, session_id)
    if chat_file is None:
        sys.exit(0)

    # Step 5: State file for turn-window tracking
    # FIX (Bug 3): Track (mtime, size, last_line) instead of just last_line.
    # If mtime or size decreased (compaction rewrote the file), reset to fresh scan.
    state_dir = Path.home() / ".grok" / "hooks" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"quality-gate-{session_id}.json"

    last_line = 0
    # Carry verification state across Stop hook fires. Without this, a
    # verification command from 2 turns ago is invisible to the current scan
    # window, causing false-positive blocks. The state is:
    #   verification_ran — True if a verifier ran in or before this scan window
    #   code_modified_after_verification — True if code was modified after the
    #     last verification (stale verification)
    prev_verification_ran = False
    prev_code_modified_after_verification = False
    prev_invoked_skills: set = set()
    try:
        file_stat = chat_file.stat()
        file_mtime = file_stat.st_mtime_ns
        file_size = file_stat.st_size
    except OSError:
        file_mtime = 0
        file_size = 0

    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            saved_mtime = state.get("mtime", 0)
            saved_size = state.get("size", 0)
            saved_last_line = state.get("last_line", 0)

            # FIX (Bug 3): if file shrank or mtime went backward, transcript was
            # compacted/rewritten — reset to scan everything fresh
            if file_size < saved_size or file_mtime < saved_mtime:
                last_line = 0
            else:
                last_line = saved_last_line

            # Always carry verification state — compaction doesn't invalidate
            # prior verification (file state is unchanged).
            prev_verification_ran = state.get("verification_ran", False)
            prev_code_modified_after_verification = state.get(
                "code_modified_after_verification", False
            )
            prev_invoked_skills = set(state.get("invoked_skills", []))
        except (json.JSONDecodeError, OSError):
            pass

    # Step 6: Scan transcript (only new lines since last fire)
    code_modified = False
    # Carry verification state from prior Stop fire — a verifier that ran
    # in a previous turn should still count if no code was modified since.
    verification_ran = prev_verification_ran
    code_modified_after_verification = prev_code_modified_after_verification
    unclassified_write_observed = False  # shell-write detection
    modified_files = []
    verification_commands = []
    current_line = 0
    # Track skills invoked this session (carried across Stop fires)
    invoked_skills = prev_invoked_skills

    # Track hooks/** mutations from transcript (primary operational evidence,
    # spike 2026-08-09). The transcript is runtime-written, append-only, and
    # already trusted for invoked_skills scanning. It is NOT tamper-proof
    # "root authority" — it is the strongest available operational evidence
    # source within the current trust boundary. We use it as a BOOLEAN
    # trigger (did a hooks edit happen?) — the actual timestamp for freshness
    # binding comes from mutation receipts (which record completed_at at
    # PostToolUse fire time, close to the actual edit time).
    _transcript_hooks_mutation_detected = False

    with open(chat_file, "r", encoding="utf-8") as f:
        for line in f:
            current_line += 1
            if current_line <= last_line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Detect skill invocations from user messages (for quality gates)
            # Grok Build transcripts use "type" field; Claude Code uses "role"
            if entry.get("type") == "user" or entry.get("role") == "user":
                content = entry.get("content", "")
                if isinstance(content, str):
                    new_skills = _qg.scan_invoked_skills([line])
                    if new_skills:
                        invoked_skills = invoked_skills | new_skills

            tool_calls = entry.get("tool_calls", [])
            if not isinstance(tool_calls, list):
                continue

            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue

                tool_name = tc.get("name", "")
                args_raw = tc.get("arguments", "{}")

                try:
                    args = (
                        json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    )
                except json.JSONDecodeError:
                    args = {}

                if tool_name in ("search_replace", "write"):
                    file_path = args.get("file_path", "")
                    if _is_code_file(file_path) and not _is_excluded_path(file_path):
                        code_modified = True
                        if verification_ran:
                            code_modified_after_verification = True
                        if file_path not in modified_files:
                            modified_files.append(file_path)
                    # Detect hooks/** mutations from transcript (primary trigger)
                    if file_path and _HOOKS_PATH_RE.search(file_path.replace("\\", "/")):
                        _transcript_hooks_mutation_detected = True

                if tool_name == "run_terminal_command":
                    cmd = args.get("command", "")
                    if _has_verification_signal(cmd):
                        verification_ran = True
                        code_modified_after_verification = False
                        verification_commands.append(cmd)
                    # Shell-write detection: if a shell command looks like it writes to a file
                    if _has_shell_write_signal(cmd):
                        unclassified_write_observed = True

    # --- Conditional skill obligations (spike 2026-08-09, revised) ---
    # PRIMARY EVIDENCE: transcript (chat_history.jsonl) — runtime-written,
    # append-only, already trusted for invoked_skills scanning. Provides
    # boolean trigger detection (did a hooks edit happen?).
    # SECONDARY: mutation receipts — provide the actual trigger timestamp
    # for freshness binding (completed_at at PostToolUse fire time).
    # Rule: if the transcript shows a search_replace/write to a hooks/** path,
    # OR mutation receipts show a hooks/** change, /review becomes REQUIRED.
    # Freshness binding uses the receipt timestamp when available (correct
    # edit time). When only the transcript detects it (receipts deleted),
    # no freshness binding is applied (evidence from any time in-session
    # satisfies — conservative but not Stop-fire-time-biased).
    _receipt_hooks_ts = _detect_hooks_mutation_from_receipts(session_id)
    _hooks_mutation_ts = _receipt_hooks_ts  # receipt has the real timestamp
    if not _hooks_mutation_ts and _transcript_hooks_mutation_detected:
        # Transcript detected hooks mutation but receipts unavailable.
        # Trigger the obligation without freshness binding.
        _hooks_mutation_ts = None  # trigger fires, but no min_timestamp
    if _transcript_hooks_mutation_detected or _receipt_hooks_ts:
        invoked_skills.add("review")
        # Record the latest trigger timestamp for freshness binding.
        # Written to a session-scoped state file that check_quality_gates reads.
        _cond_freshness_path = (
            Path.home() / ".grok" / "hooks" / "state"
            / f"cond-freshness-{session_id}.json"
        )
        try:
            _cond_freshness_path.parent.mkdir(parents=True, exist_ok=True)
            _cond_freshness_path.write_text(
                json.dumps({"review": _hooks_mutation_ts}),
                encoding="utf-8",
            )
        except OSError:
            pass

    # Update state file with (mtime, size, last_line) for compaction-safe tracking
    # plus verification state carried across Stop hook fires.
    try:
        tmp = state_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "last_line": current_line,
                    "mtime": file_mtime,
                    "size": file_size,
                    "transcript_path": str(chat_file),
                    "verification_ran": verification_ran,
                    "code_modified_after_verification": code_modified_after_verification,
                    "invoked_skills": sorted(invoked_skills),
                }
            ),
            encoding="utf-8",
        )
        os.replace(str(tmp), str(state_file))
    except OSError:
        pass

    # Step 7: Trace log deferred to after decision variables are computed

    # Time-window tracking: was code modified after verification?

    # Step 8: Decision logic.  Shadow mode remains the safe default; the
    # authoritative modes are explicitly opt-in for integration testing.
    #
    # OLD gate: "verification must have run in current scan window"
    # RECEIPT gate: "verification receipt must cover current relevant state"

    nudge_entries = _read_nudge_state(session_id)
    stale_by_time = _is_verification_stale(nudge_entries)

    # --- Compute OLD gate decision (authoritative) ---
    if verification_ran and not code_modified_after_verification:
        old_verification_insufficient = False
    else:
        old_verification_insufficient = (
            not verification_ran or code_modified_after_verification or stale_by_time
        )
    old_block = claim and code_modified and old_verification_insufficient

    # --- Compute NEW receipt gate decision (shadow) ---
    norm_ws = _normalize_workspace(workspace_root)
    # Receipt/worktree inspection is only useful for a claimed completion or
    # an active continuation obligation. Avoid Git and receipt-directory I/O
    # on ordinary Stop events.
    needs_receipt_state = bool(claim and modified_files) or stop_active
    all_receipts = _read_receipts(session_id) if needs_receipt_state else []
    # A Git subprocess is unnecessary when there are no receipts to validate.
    # This is the common first-block path; defer identity resolution until the
    # receipt set proves that identity comparison is actually needed.
    current_wt = _wt_id.resolve_identity(workspace_root) if all_receipts else None
    if claim and modified_files:
        receipt_uncovered, receipt_reason, consumed_ids = _check_receipt_coverage(
            session_id,
            modified_files,
            claim,
            all_receipts,
            norm_ws,
            current_wt,
        )
        receipt_covered = [
            f for f in modified_files if _normalize_path(f) not in receipt_uncovered
        ]
    else:
        receipt_uncovered = []
        receipt_covered = []
        receipt_reason = "NO_CLAIM"
        consumed_ids = []

    # receipt_backed: true only when a genuine SUCCEEDED receipt covered nonempty scope
    receipt_backed = (
        receipt_reason == "VALID_RECEIPT_REUSE"
        and len(consumed_ids) > 0
        and len(receipt_covered) > 0
    )

    # Conservative: unclassified shell write → receipt reuse unavailable
    if unclassified_write_observed:
        receipt_uncovered = [_normalize_path(f) for f in modified_files]
        receipt_covered = []

    receipt_block = claim and code_modified and len(receipt_uncovered) > 0
    receipt_mode = _receipt_gate_mode()
    receipt_state_available = bool(all_receipts)
    receipt_valid = receipt_reason == "VALID_RECEIPT_REUSE" and not receipt_uncovered

    effective_block = _effective_block_decision(
        old_block, receipt_block, receipt_state_available, receipt_mode
    )

    # Shadow-mode receipt relief: in shadow mode the old gate is authoritative,
    # but its per-turn scan window can miss verification from prior turns.
    # If a VERIFICATION_SUCCEEDED receipt covers all modified files, the
    # verification happened — allow instead of blocking. This bridges the
    # scan-window gap without switching to full receipt-authoritative mode.
    if effective_block and receipt_mode == "shadow":
        if receipt_reason == "VALID_RECEIPT_REUSE" and not receipt_uncovered:
            effective_block = False

    # --- Shadow comparison log ---
    from datetime import datetime as _dt, timezone as _tz

    try:
        sl = _shadow_log_file(session_id)
        sl.parent.mkdir(parents=True, exist_ok=True)
        shadow_entry = {
            "ts": _dt.now(_tz.utc).isoformat()[:19] + "Z",
            "session_id": session_id,
            "workspace_id": norm_ws,
            "repository_id": current_wt.repository_id if current_wt else "",
            "worktree_id": current_wt.worktree_id if current_wt else "",
            "is_git": current_wt.is_git if current_wt else False,
            "old_gate_decision": "block" if old_block else "allow",
            "receipt_gate_decision": "block" if receipt_block else "allow",
            "receipt_gate_mode": receipt_mode,
            "receipt_state_available": receipt_state_available,
            "receipt_valid": receipt_valid,
            "effective_decision": "block" if effective_block else "allow",
            "difference": old_block != receipt_block,
            "reason": receipt_reason,
            "relevant_scope": [Path(f).name for f in modified_files[:10]],
            "covered_scope": [Path(f).name for f in receipt_covered[:10]],
            "uncovered_scope": [Path(f).name for f in receipt_uncovered[:10]],
            "consumed_receipt_ids": consumed_ids[:10],
            "receipt_backed": receipt_backed,
            "reason_codes": {
                "verification_ran": verification_ran,
                "code_modified_after_verification": code_modified_after_verification,
                "stale_by_time": stale_by_time,
                "unclassified_write_observed": unclassified_write_observed,
            },
            "workspace_match": True,  # tracked per-receipt; log overall
            "unclassified_write_observed": unclassified_write_observed,
            "latency_ms": round((time.perf_counter() - hook_started) * 1000, 2),
        }
        with open(sl, "a", encoding="utf-8") as f:
            f.write(json.dumps(shadow_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # Determine stale status for hints message
    stale = code_modified_after_verification or stale_by_time
    file_hints = _build_file_hints(
        nudge_entries, modified_files, stale=stale, receipts=all_receipts
    )

    # Write trace log
    _write_trace_log(
        session_id,
        claim,
        code_modified,
        verification_ran,
        modified_files,
        verification_commands,
        current_line - last_line,
        stop_active,
        code_modified_after_verification,
        stale_by_time,
    )

    # --- Enforce selected rollout mode ---

    # --- 2nd+ pass handling ---
    if stop_active:
        # Continuation obligation check: don't allow based on empty scan window
        # alone. If a previous block created an obligation, require a receipt
        # that covers the blocked paths with matching fingerprints.
        obligation = _read_obligation(session_id)

        if isinstance(obligation, str) and obligation in {"CORRUPT", "UNAVAILABLE"}:
            # Corrupt or unavailable obligation state — fail closed through a
            # controlled decision rather than allowing the fallback gate to run.
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": (
                            "Continuation obligation state is "
                            f"{obligation.lower()}. Enforcement cannot trust the "
                            "previous block state. Preserve the evidence and "
                            "repair the obligation persistence failure before "
                            "claiming completion."
                        ),
                    }
                )
            )
            sys.exit(0)

        has_pending = (
            isinstance(obligation, dict) and obligation.get("status") == "PENDING"
        )

        if has_pending:
            blocked_paths = obligation.get("blocked_paths", [])

            satisfied, obl_reason, receipt_id = _check_obligation_satisfied(
                session_id, obligation, all_receipts
            )

            if satisfied:
                # Receipt covers blocked paths with matching fingerprints
                # But check for NEW modifications in this scan window
                if code_modified:
                    _write_obligation(
                        session_id,
                        modified_files,
                        "NEW_MUTATION_AFTER_VERIFICATION",
                        current_line,
                        identity=current_wt,
                    )
                    print(
                        json.dumps(
                            {
                                "decision": "block",
                                "reason": (
                                    "New code was modified after verification. "
                                    "Re-run verification against the current file state."
                                    + file_hints
                                ),
                            }
                        )
                    )
                    sys.exit(0)
                else:
                    # Obligation satisfied, no new mutations
                    if not _clear_obligation(session_id):
                        print(
                            json.dumps(
                                {
                                    "decision": "block",
                                    "reason": (
                                        "Completion remains blocked because the "
                                        "satisfied obligation could not be cleared "
                                        "durably. Review obligation persistence telemetry."
                                    ),
                                }
                            )
                        )
                        sys.exit(0)
                    _cleanup_nudge_state(session_id)
                    # Quality gate check (declarative frontmatter gates)
                    qg_block, qg_msg = _quality_gate_check(
                        session_id, workspace_root, invoked_skills, claim
                    )
                    if qg_block:
                        print(json.dumps({"decision": "block", "reason": qg_msg}))
                        sys.exit(0)
                    _qg.clear_waiver(session_id)
                    sys.exit(0)
            else:
                # Obligation NOT satisfied — block with explicit reason
                scoped_hints = _build_file_hints(
                    nudge_entries,
                    modified_files,
                    stale=False,
                    receipts=all_receipts,
                    focus_files=blocked_paths,
                )
                print(
                    json.dumps(
                        {
                            "decision": "block",
                            "reason": _obligation_block_message(
                                blocked_paths,
                                obl_reason,
                                scoped_hints,
                                obligation=obligation,
                                receipts=all_receipts,
                            ),
                        }
                    )
                )
                sys.exit(0)

        # No pending obligation — fall through to existing scan-window logic
        if not claim:
            _cleanup_nudge_state(session_id)
            sys.exit(0)
        elif (
            verification_ran
            and not code_modified_after_verification
            and not stale_by_time
        ):
            _cleanup_nudge_state(session_id)
            # Quality gate check (declarative frontmatter gates)
            qg_block, qg_msg = _quality_gate_check(
                session_id, workspace_root, invoked_skills, claim
            )
            if qg_block:
                print(json.dumps({"decision": "block", "reason": qg_msg}))
                sys.exit(0)
            _qg.clear_waiver(session_id)
            sys.exit(0)
        elif code_modified:
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": (
                            "More code was modified since the last block but still "
                            "no verification. Run the modified file or a test command "
                            "and show the output." + file_hints
                        ),
                    }
                )
            )
            sys.exit(0)
        else:
            _cleanup_nudge_state(session_id)
            # Quality gate check (declarative frontmatter gates)
            qg_block, qg_msg = _quality_gate_check(
                session_id, workspace_root, invoked_skills, claim
            )
            if qg_block:
                print(json.dumps({"decision": "block", "reason": qg_msg}))
                sys.exit(0)
            _qg.clear_waiver(session_id)
            sys.exit(0)

    # --- 1st pass: OLD gate enforcement ---
    if effective_block:
        # Write continuation obligation so the next pass validates receipt coverage.
        # BUT: only write receipt-based obligations when the receipt gate is
        # actually authoritative. In shadow mode, the old gate can block, but
        # it should NOT create receipt-based obligations that can't be satisfied
        # (the receipt system isn't authoritative, so the obligation's required
        # capability can never be met via receipt). Instead, shadow-mode blocks
        # are resolved by running any verification command — same as the old gate.
        obligation_paths = receipt_uncovered or [
            _normalize_path(f) for f in modified_files
        ]
        # In shadow mode: don't set required_capability from receipts — use
        # the old gate's resolution model (any verification command clears it).
        # In authoritative mode: derive capability from blocked paths (receipts needed).
        if receipt_mode == "shadow":
            obligation = _write_obligation(
                session_id,
                obligation_paths,
                "STALE_OR_MISSING_VERIFICATION",
                current_line,
                required_capability="syntax",  # lowest bar — any verifier clears it
                identity=current_wt,
            )
        else:
            obligation = _write_obligation(
                session_id,
                obligation_paths,
                "STALE_OR_MISSING_VERIFICATION",
                current_line,
                identity=current_wt,
            )
        stale_note = ""
        if code_modified_after_verification:
            stale_note = " Verification receipt is stale: files were modified after the last verification tool call."
        elif stale_by_time:
            stale_note = " Verification receipt is stale: last code modification is >10 min old with no re-verification."
        elif not verification_ran:
            stale_note = " No verification command was run this turn."

        scoped_hints = _build_file_hints(
            nudge_entries,
            modified_files,
            stale=stale,
            receipts=all_receipts,
            focus_files=obligation_paths,
        )
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "You modified code and claimed completion, but the verification "
                        "receipt does not cover the current required scope.\n"
                        f"Continuation obligation created: {obligation['nonce']}\n"
                        "Required verification scope:\n"
                        f"{_format_obligation_scope(obligation_paths)}\n"
                        "Observed-state fingerprints are recorded for freshness only; "
                        "they are not claimed verifier coverage."
                        + stale_note
                        + scoped_hints
                        + "\n"
                        "Run an approved verifier against the required scope and show the output.\n"
                        "If you are not claiming this work is complete, remove "
                        "words like 'done', 'fixed', or 'complete' from your response."
                    ),
                }
            )
        )
        sys.exit(0)

    # --- Quality gate check (declarative frontmatter gates) ---
    # Runs after code-verification gate passes.  Checks whether invoked skills
    # declared quality_gates and whether the evidence artifacts exist.
    qg_block, qg_message = _quality_gate_check(
        session_id, workspace_root, invoked_skills, claim
    )
    if qg_block:
        print(json.dumps({"decision": "block", "reason": qg_message}))
        sys.exit(0)

    # All checks passed — allow
    _clear_obligation(session_id)
    _cleanup_nudge_state(session_id)
    _qg.clear_waiver(session_id)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _write_hook_error(exc)
        sys.exit(0)
```

### quality_gates_frontmatter.py (MODIFIED — min_timestamp freshness binding)
Path: `hooks/scripts/quality_gates_frontmatter.py`

```python
#!/usr/bin/env python3
"""
Declarative quality gates for Grok Build skills.

Skills declare ``quality_gates`` in their SKILL.md YAML frontmatter.  Each
gate names an evidence artifact (a glob pattern) that must exist on disk
when the agent claims completion after invoking that skill.

The Stop hook (``quality_gate.py``) calls ``check_quality_gates()`` after
its existing code-verification checks pass.  If any gate's evidence is
missing (and not waived), the hook blocks the turn.

Example frontmatter::

    ---
    name: ship
    quality_gates:
      - evidence: "P:/.artifacts/**/check-run.json"
        message: "/check receipt missing — run /check before claiming ship done"
      - evidence: "P:/.artifacts/**/FINDINGS.md"
        message: "/review findings missing — run /review before claiming ship done"
    ---

Waiver escape hatch: write a JSON file to
``~/.grok/hooks/state/quality-gate-waiver-<session_id>.json`` containing
``{"session_id": "...", "waived_skills": ["ship"], "reason": "..."}``.
The waiver is logged to the shadow log, not silent.
"""

from __future__ import annotations

import glob
import json
import os
import re
import time
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Directories searched for ``<skill_name>/SKILL.md`` (in priority order).
SKILL_SEARCH_DIRS: list[Path] = [
    Path.home() / ".grok" / "skills",
    Path.home() / ".grok" / "installed-plugins",
    Path.home() / ".claude" / "plugins" / "cache",
    Path.home() / ".claude" / "plugins" / "marketplaces",
    Path("P:/.grok") / "skills",
    Path("P:/.agents") / "skills",
    Path("P:/packages") / ".claude-marketplace" / "plugins",
]

#: Regex for detecting skill invocations in user messages.
#: Matches ``/word`` at start-of-line or after whitespace, capturing the name.
SKILL_INVOCATION_RE = re.compile(
    r"(?:^|\s)/([a-z][a-z0-9-]{1,40})\b",
    re.MULTILINE,
)

#: Skills that should NOT trigger quality-gate scanning (meta-skills, aliases).
SKIP_SKILL_NAMES = {
    "grok-go", "grok-sdlc",  # aliases for /go
    "grok-parallel", "grok-discovery", "grok-route", "grok-safe-git",
    "grok-verify",  # sub-skills of /go, not independently gated
    "help",  # documentation
}

#: Maximum evidence file age (seconds) for freshness.  Evidence older than
#: this is considered stale and reported as a warning (does not block;
#: absence blocks, staleness warns).
EVIDENCE_FRESHNESS_SECONDS = 7_200  # 2 hours


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class GateResult(NamedTuple):
    """Outcome of checking a single quality gate."""
    skill_name: str
    evidence_pattern: str
    message: str
    satisfied: bool
    found_path: str = ""
    stale: bool = False
    session_field: str = ""
    condition: str = ""
    condition_met: bool = True
    skipped_by_condition: bool = False


class QualityGateReport(NamedTuple):
    """Aggregated result for all invoked skills."""
    blocked: bool
    missing_gates: list[GateResult]
    stale_gates: list[GateResult]
    satisfied_gates: list[GateResult]
    waived_skills: list[str]
    error: str = ""


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(skill_md_path: Path) -> dict:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns a dict (possibly empty).  Uses a lightweight parser — no
    external YAML dependency.  Only handles the flat key-value and
    list-of-dicts shapes that ``quality_gates`` uses.
    """
    try:
        text = skill_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    if not text.startswith("---"):
        return {}

    # Extract frontmatter block
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    fm_text = parts[1].strip()
    return _parse_simple_yaml(fm_text)


def _parse_simple_yaml(text: str) -> dict:
    """Parse a subset of YAML sufficient for SKILL.md frontmatter.

    Handles:
    - ``key: value``
    - ``key: >`` (block scalar)
    - ``- value`` (list items)
    - ``- key: value`` (list of dicts)
    - Nested ``metadata:`` blocks (skipped — we only need top-level + quality_gates)

    Does NOT handle anchors, aliases, or complex nesting beyond what
    frontmatter needs.  Falls back to ``{}`` on any parse issue.
    """
    result: dict = {}
    lines = text.split("\n")
    i = 0

    try:
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # Detect top-level key
            m = re.match(r"^(\w[\w-]*)\s*:\s*(.*)$", stripped)
            if not m:
                i += 1
                continue

            key = m.group(1)
            value = m.group(2).strip()

            if key == "quality_gates":
                # Parse list of dicts
                gates, consumed = _parse_yaml_list_of_dicts(lines, i + 1)
                result["quality_gates"] = gates
                i += consumed + 1
                continue

            if value == ">":
                # Block scalar — consume indented lines
                block_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith(" ") or next_line.startswith("\t"):
                        block_lines.append(next_line.strip())
                        i += 1
                    else:
                        break
                result[key] = " ".join(block_lines)
                continue

            if value == "":
                # Could be a nested block or empty — check next line
                if i + 1 < len(lines) and (
                    lines[i + 1].startswith(" ") or lines[i + 1].startswith("\t")
                ):
                    # Nested block — parse simple key-values
                    nested, consumed = _parse_yaml_dict(lines, i + 1)
                    result[key] = nested
                    i += consumed + 1
                else:
                    result[key] = ""
                    i += 1
                continue

            # Strip quotes from scalar values
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            result[key] = value
            i += 1
    except (IndexError, ValueError):
        pass

    return result


def _parse_yaml_list_of_dicts(lines: list[str], start: int) -> tuple[list[dict], int]:
    """Parse a YAML list of dicts starting at ``start``.

    Returns (list_of_dicts, lines_consumed).  Stops when indentation
    returns to the same level as the list items or a non-list line appears.
    """
    result: list[dict] = []
    consumed = 0
    i = start
    current_dict: dict | None = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            consumed += 1
            continue

        # List item with dict
        if stripped.startswith("- "):
            content = stripped[2:].strip()
            # Parse "key: value" within the list item
            m = re.match(r"^(\w[\w-]*)\s*:\s*(.*)$", content)
            if m:
                current_dict = {m.group(1): _unquote(m.group(2).strip())}
                result.append(current_dict)
            else:
                # Plain list item (not a dict)
                result.append({"value": _unquote(content)})
                current_dict = None
            i += 1
            consumed += 1
            continue

        # Continuation of current dict (indented key: value)
        if (line.startswith("  ") or line.startswith("\t")) and current_dict is not None:
            m = re.match(r"^(\s+)(\w[\w-]*)\s*:\s*(.*)$", line)
            if m:
                key = m.group(2)
                value = m.group(3).strip()
                if value == "" and i + 1 < len(lines):
                    # Could be a nested dict — check if next lines are more indented
                    indent = len(m.group(1))
                    nested: dict = {}
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        if not next_line.strip() or next_line.strip().startswith("#"):
                            j += 1
                            continue
                        nm = re.match(r"^(\s+)(\w[\w-]*)\s*:\s*(.*)$", next_line)
                        if nm and len(nm.group(1)) > indent:
                            nk = nm.group(2)
                            nv = nm.group(3).strip()
                            if nv.startswith("["):
                                # Parse YAML list: [a, b, c]
                                items = [x.strip().strip("'\"") for x in nv.strip("[]").split(",") if x.strip()]
                                nested[nk] = items
                            else:
                                nested[nk] = _unquote(nv)
                            consumed_extra = j - i
                            i = j
                            consumed += consumed_extra
                            j += 1
                        else:
                            break
                    if nested:
                        current_dict[key] = nested
                        i += 1
                        consumed += 1
                        continue
                current_dict[key] = _unquote(value)
            i += 1
            consumed += 1
            continue

        # Anything else — end of list
        break

    return result, consumed


def _parse_yaml_dict(lines: list[str], start: int) -> tuple[dict, int]:
    """Parse a simple nested YAML dict (indented key: value pairs)."""
    result: dict = {}
    consumed = 0
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            consumed += 1
            continue

        # Must be indented to be part of this dict
        if not (line.startswith(" ") or line.startswith("\t")):
            break

        m = re.match(r"^\s+(\w[\w-]*)\s*:\s*(.*)$", line)
        if m:
            result[m.group(1)] = _unquote(m.group(2).strip())
        i += 1
        consumed += 1

    return result, consumed


def _unquote(s: str) -> str:
    """Remove surrounding quotes from a string."""
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def find_skill_md(skill_name: str) -> Path | None:
    """Find the SKILL.md file for a given skill name.

    Searches known skill directories in priority order.  For plugin
    directories, does a shallow recursive search (max depth 3) since
    plugin skills live at ``<plugin>/skills/<name>/SKILL.md``.
    """
    for base in SKILL_SEARCH_DIRS:
        if not base.exists():
            continue

        # Direct: <base>/<skill_name>/SKILL.md
        direct = base / skill_name / "SKILL.md"
        if direct.exists():
            return direct

        # Plugin/cache: <base>/<plugin>/skills/<skill_name>/SKILL.md
        # Shallow search — max 3 levels deep
        try:
            for candidate in base.glob("*/skills/" + skill_name + "/SKILL.md"):
                return candidate
            # installed-plugins: <base>/<plugin-hash>/skills/<skill_name>/SKILL.md
            for candidate in base.glob("*/*/skills/" + skill_name + "/SKILL.md"):
                return candidate
        except (OSError, PermissionError):
            continue

    return None


def get_quality_gates(skill_name: str) -> list[dict]:
    """Read quality_gates from a skill's SKILL.md frontmatter.

    Returns a list of gate dicts, each with at least ``evidence`` and
    ``message`` keys.  Empty list if the skill has no gates or no SKILL.md.
    """
    skill_md = find_skill_md(skill_name)
    if skill_md is None:
        return []

    fm = parse_frontmatter(skill_md)
    gates = fm.get("quality_gates", [])
    if not isinstance(gates, list):
        return []

    # Validate each gate has required fields
    valid = []
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        evidence = gate.get("evidence", "")
        if not evidence:
            continue
        valid.append({
            "evidence": evidence,
            "message": gate.get("message", f"Evidence missing: {evidence}"),
            "session_field": gate.get("session_field", ""),
            "condition": gate.get("condition", ""),
            "contains_all": gate.get("contains_all", {}),  # {field: ..., required: [...]}
        })
    return valid


# ---------------------------------------------------------------------------
# Evidence checking
# ---------------------------------------------------------------------------

def check_evidence(pattern: str, workspace_root: str = "",
                   session_id: str = "", session_field: str = "",
                   min_timestamp: str = "") -> tuple[bool, str, bool]:
    """Check whether an evidence glob pattern matches any file on disk.

    Expands ``~`` and ``{workspace}`` in the pattern.  Uses recursive glob.

    When ``session_id`` and ``session_field`` are both provided, matched JSON
    files are parsed and filtered by the ``session_field`` content field.
    This prevents cross-session evidence contamination on multi-agent hosts
    where multiple sessions write evidence artifacts to the same directory tree.

    When ``min_timestamp`` is provided (ISO-8601 UTC), only files whose mtime
    is at or after that timestamp are accepted. This implements freshness
    binding for conditional obligations: evidence must post-date the trigger.

    Returns ``(found, path, stale)`` where:
    - ``found``: True if at least one file matches (and passes session filter if set)
    - ``path``: the most recent matching file path (empty if none)
    - ``stale``: True if the found file is older than EVIDENCE_FRESHNESS_SECONDS
    """
    # Expand path variables
    expanded = pattern
    expanded = expanded.replace("{workspace}", workspace_root or "P:/")
    expanded = os.path.expanduser(expanded)

    # Normalize separators for glob
    expanded = expanded.replace("\\", "/")

    # Use glob with recursive=True
    matches = glob.glob(expanded, recursive=True)
    if not matches:
        return False, "", False

    # Session-scoped filtering: for JSON files, check session_field content
    if session_id and session_field:
        session_matches = []
        for m in matches:
            if not m.lower().endswith(".json"):
                # Non-JSON files can't be session-filtered; include them
                session_matches.append(m)
                continue
            try:
                data = json.loads(Path(m).read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get(session_field) == session_id:
                    session_matches.append(m)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                continue
        matches = session_matches if session_matches else []

    if not matches:
        return False, "", False

    # Freshness binding for conditional obligations (spike 2026-08-09):
    # reject evidence whose mtime predates the obligation trigger.
    if min_timestamp:
        try:
            from datetime import datetime as _dt
            min_dt = _dt.fromisoformat(min_timestamp.replace("Z", "+00:00"))
            filtered = []
            for m in matches:
                try:
                    file_dt = _dt.fromtimestamp(
                        os.path.getmtime(m), tz=min_dt.tzinfo
                    )
                    if file_dt >= min_dt:
                        filtered.append(m)
                except OSError:
                    continue
            matches = filtered if filtered else []
        except (ValueError, TypeError):
            pass  # invalid timestamp format — don't filter

    if not matches:
        return False, "", False

    # Find the most recent match
    matches.sort(
        key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
        reverse=True,
    )
    best = matches[0]

    # Check freshness
    try:
        age = time.time() - os.path.getmtime(best)
        stale = age > EVIDENCE_FRESHNESS_SECONDS
    except OSError:
        stale = False

    return True, best, stale


def check_contains_all(pattern: str, field: str, required: list,
                       workspace_root: str = "",
                       session_id: str = "", session_field: str = "") -> tuple[bool, str, bool]:
    """Check whether a JSON file matches a glob AND contains all required values in a list field.

    This is the 'file_contains' gate type — it verifies not just that a file
    exists, but that a specific field within the file contains all required
    values. Used for state-machine completion checks (e.g., ship-py's
    completed_phases must contain detect+review+verify+verdict).

    Returns ``(found, path, stale)`` where:
    - ``found``: True if a matching file exists with all required values
    - ``path``: the matching file path (empty if none)
    - ``stale``: True if the found file is older than EVIDENCE_FRESHNESS_SECONDS
    """
    # First: find files matching the glob (reuse check_evidence's logic)
    found, best, stale = check_evidence(pattern, workspace_root, session_id, session_field)
    if not found or not best:
        return False, "", False

    # Then: check the field contains all required values
    try:
        data = json.loads(Path(best).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False, best, stale

    actual = data.get(field, [])
    if not isinstance(actual, list):
        actual = [actual]  # scalar field — check if it's in required

    required_set = set(required)
    actual_set = set(str(x) for x in actual)
    if required_set.issubset(actual_set):
        return True, best, stale
    return False, best, stale


# ---------------------------------------------------------------------------
# Transcript scanning for skill invocations
# ---------------------------------------------------------------------------

def scan_invoked_skills(transcript_lines: list[str]) -> set[str]:
    """Scan transcript lines for skill invocations.

    Looks for ``/skillname`` patterns in user messages.  Returns a set
    of skill names (without the leading slash).

    Filters out file paths (``P:/...``, ``C:/...``) and known non-skill
    patterns.
    """
    invoked = set()
    for line in transcript_lines:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue

        # Only scan user messages (Grok Build uses "type", Claude Code uses "role")
        if entry.get("type") != "user" and entry.get("role") != "user":
            continue

        content = entry.get("content", "")
        if not isinstance(content, str):
            # content might be a list of content blocks
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and "text" in b
                )
            else:
                continue

        for m in SKILL_INVOCATION_RE.finditer(content):
            name = m.group(1).lower()
            # Skip if preceded by a drive letter (file path like P:/)
            start = m.start()
            if start >= 2 and content[start - 2:start].endswith(":"):
                continue
            if name in SKIP_SKILL_NAMES:
                continue
            invoked.add(name)

    return invoked


# ---------------------------------------------------------------------------
# Waiver handling
# ---------------------------------------------------------------------------

def _waiver_file(session_id: str) -> Path:
    """Path to the waiver state file for a session."""
    return Path.home() / ".grok" / "hooks" / "state" / f"quality-gate-waiver-{session_id}.json"


def read_waiver(session_id: str) -> dict:
    """Read the waiver file for a session.

    Returns ``{"session_id": ..., "waived_skills": [...], "reason": ...}``
    or empty dict if no waiver exists.
    """
    path = _waiver_file(session_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("session_id") == session_id:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def write_waiver(session_id: str, waived_skills: list[str], reason: str) -> bool:
    """Write a waiver file for a session.

    The waiver is logged (not silent).  Returns True on success.
    """
    from datetime import datetime, timezone
    path = _waiver_file(session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        waiver = {
            "session_id": session_id,
            "waived_skills": waived_skills,
            "reason": reason,
            "waived_at": datetime.now(timezone.utc).isoformat()[:19] + "Z",
            "waived_by": "operator",
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(waiver, ensure_ascii=False), encoding="utf-8")
        os.replace(str(tmp), str(path))
        return True
    except OSError:
        return False


def clear_waiver(session_id: str):
    """Delete the waiver file after the gate has consumed it."""
    try:
        _waiver_file(session_id).unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Condition checks (conditional gates)
# ---------------------------------------------------------------------------

def _find_session_transcript(session_id: str) -> Path | None:
    """Locate the chat_history.jsonl for a session by scanning the sessions tree."""
    sessions_root = Path.home() / ".grok" / "sessions"
    if not sessions_root.exists():
        return None
    try:
        for candidate in sessions_root.rglob(f"{session_id}/chat_history.jsonl"):
            return candidate
    except (OSError, PermissionError):
        return None
    return None


def _read_session_files(session_id: str) -> list[str]:
    """Read the set of file paths this session modified from hunk_records.jsonl."""
    sessions_root = Path.home() / ".grok" / "sessions"
    if not sessions_root.exists():
        return []
    hunk_path = None
    try:
        for candidate in sessions_root.rglob(f"{session_id}/hunk_records.jsonl"):
            hunk_path = candidate
            break
    except (OSError, PermissionError):
        return []
    if hunk_path is None or not hunk_path.exists():
        return []

    files: set[str] = set()
    try:
        for line in hunk_path.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            if record.get("sessionId") != session_id:
                continue
            file_path = record.get("filePath", "")
            if file_path:
                files.add(file_path.replace("\\", "/").lower())
        return list(files)
    except (OSError, UnicodeDecodeError):
        return []


#: Code file extensions that indicate work producing durable findings
_CODE_EXTENSIONS = {".py", ".ps1", ".sh", ".js", ".ts", ".tsx", ".jsx",
                    ".go", ".rs", ".java", ".rb", ".lua", ".vim"}


def _session_has_durable_findings(session_id: str, workspace_root: str = "") -> bool:
    """Check whether this session produced work likely to have durable findings.

    Heuristic: returns True when the session modified code files (.py, .ps1, etc.)
    OR produced review evidence. These are proxies for "work that generates
    non-obvious knowledge worth capturing in the wiki."
    """
    files = _read_session_files(session_id)
    for f in files:
        suffix = Path(f).suffix.lower()
        if suffix in _CODE_EXTENSIONS:
            return True
    # Also check if review FINDINGS.md exists for this session (review = findings)
    if workspace_root:
        review_pattern = "P:/.artifacts/**/FINDINGS.md"
        review_pattern = review_pattern.replace("P:/", workspace_root.rstrip("/") + "/") if workspace_root != "P:/" else review_pattern
    else:
        review_pattern = "P:/.artifacts/**/FINDINGS.md"
    matches = glob.glob(review_pattern, recursive=True)
    return len(matches) > 0


def _session_has_open_work(session_id: str, workspace_root: str = "") -> bool:
    """Check whether this session has uncommitted or open work needing a handoff.

    Heuristic: returns True when git has uncommitted changes in the workspace
    OR the session modified tracked files. Both indicate work that a future
    session might need to continue.
    """
    import subprocess
    ws = workspace_root or "P:/"
    try:
        result = subprocess.run(
            ["git", "-C", ws, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        pass
    # Fallback: if the session modified any files at all, treat as open work
    files = _read_session_files(session_id)
    return len(files) > 0


#: Registry of named condition checks. Each takes (session_id, workspace_root)
#: and returns True when the condition is met (meaning the gate SHOULD fire).
CONDITION_CHECKS = {
    "session_has_durable_findings": _session_has_durable_findings,
    "session_has_open_work": _session_has_open_work,
}


def evaluate_condition(condition_name: str, session_id: str,
                       workspace_root: str = "") -> bool:
    """Evaluate a named condition. Unknown conditions default to True (fire)."""
    check_fn = CONDITION_CHECKS.get(condition_name)
    if check_fn is None:
        return True  # unknown condition → gate fires (conservative)
    try:
        return bool(check_fn(session_id, workspace_root))
    except Exception:
        return True  # broken condition check → gate fires (conservative)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_quality_gates(
    invoked_skills: set[str],
    session_id: str,
    workspace_root: str = "",
) -> QualityGateReport:
    """Check all quality gates for all invoked skills.

    For each invoked skill that declares ``quality_gates`` in its frontmatter,
    checks whether each evidence artifact exists on disk.

    Gates with a ``condition`` field are only checked when the condition
    evaluates True.  When the condition is False, the gate is skipped
    (marked as satisfied) — e.g. /wiki gate only blocks sessions that
    actually produced durable findings.

    For conditionally-obligated skills (e.g. /review required because
    hooks/** was modified), reads the ``required_after`` timestamp from
    a session-scoped state file and applies freshness binding: evidence
    must post-date the obligation trigger.

    Returns a QualityGateReport with the aggregated result.
    """
    missing_gates: list[GateResult] = []
    stale_gates: list[GateResult] = []
    satisfied_gates: list[GateResult] = []
    waived_skills: list[str] = []
    skipped_gates: list[GateResult] = []

    # Read waiver
    waiver = read_waiver(session_id)
    waived = set(waiver.get("waived_skills", []))

    # Read conditional-obligation freshness binding (spike 2026-08-09).
    # Written by quality_gate/main.py when it detects hooks/** mutations.
    # Keyed by skill_name → required_after timestamp.
    _cond_freshness: dict[str, str] = {}
    _cond_path = Path.home() / ".grok" / "hooks" / "state" / f"cond-freshness-{session_id}.json"
    if _cond_path.exists():
        try:
            _cond_freshness = json.loads(_cond_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    for skill_name in sorted(invoked_skills):
        if skill_name in waived:
            waived_skills.append(skill_name)
            continue

        gates = get_quality_gates(skill_name)
        if not gates:
            continue  # skill has no quality gates declared

        for gate in gates:
            pattern = gate["evidence"]
            message = gate["message"]
            session_field = gate.get("session_field", "")
            condition = gate.get("condition", "")

            # Evaluate condition — skip gate if condition is False
            if condition:
                condition_met = evaluate_condition(
                    condition, session_id, workspace_root)
                if not condition_met:
                    skipped_gates.append(GateResult(
                        skill_name=skill_name,
                        evidence_pattern=pattern,
                        message=message,
                        satisfied=True,
                        condition=condition,
                        condition_met=False,
                        skipped_by_condition=True,
                    ))
                    continue

            # Freshness binding: if this skill has a conditional obligation
            # with a required_after timestamp, pass it to check_evidence.
            _min_ts = _cond_freshness.get(skill_name, "")

            found, found_path, stale = check_evidence(
                pattern, workspace_root, session_id, session_field,
                min_timestamp=_min_ts)

            # contains_all gate: also check a field has all required values
            contains_all_spec = gate.get("contains_all", {})
            if contains_all_spec:
                ca_field = contains_all_spec.get("field", "")
                ca_required = contains_all_spec.get("required", [])
                if ca_field and ca_required:
                    found, found_path, stale = check_contains_all(
                        pattern, ca_field, ca_required,
                        workspace_root, session_id, session_field)

            result = GateResult(
                skill_name=skill_name,
                evidence_pattern=pattern,
                message=message,
                satisfied=found and not stale,
                found_path=found_path,
                stale=stale,
                session_field=session_field,
                condition=condition,
                condition_met=True,
                skipped_by_condition=False,
            )

            if found and not stale:
                satisfied_gates.append(result)
            elif found and stale:
                stale_gates.append(result)
            else:
                missing_gates.append(result)

    blocked = len(missing_gates) > 0

    return QualityGateReport(
        blocked=blocked,
        missing_gates=missing_gates,
        stale_gates=stale_gates,
        satisfied_gates=satisfied_gates,
        waived_skills=waived_skills,
    )


def build_block_message(report: QualityGateReport) -> str:
    """Build a human-readable block message for missing quality gates."""
    parts = [
        "Completion blocked: quality gate evidence is missing.",
        "",
    ]

    for gate in report.missing_gates:
        parts.append(f"  [{gate.skill_name}] {gate.message}")
        parts.append(f"    Expected evidence: {gate.evidence_pattern}")

    if report.stale_gates:
        parts.append("")
        parts.append("Stale evidence (exists but old — consider re-running):")
        for gate in report.stale_gates:
            parts.append(f"  [{gate.skill_name}] {gate.message}")
            parts.append(f"    Found: {gate.found_path}")

    if report.waived_skills:
        parts.append("")
        parts.append(f"Waived skills: {', '.join(report.waived_skills)}")

    parts.append("")
    parts.append("To waive these gates, the operator must authorize it.")
    parts.append("The waiver is logged to the hook state directory.")

    return "\n".join(parts)
```

### quality-gate.json (MODIFIED — writer registration)
Path: `hooks/quality-gate.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "search_replace|write|run_terminal_command",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\mutation_pre.py\"",
            "timeout": 30
          },
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py\"",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "search_replace|write",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/scripts/dead_zone_guard.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "search_replace|write",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\quality_nudge.py\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\mutation_post.py\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py\"",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/PostToolUse_auto_verify.py\"",
            "timeout": 15
          },
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/PostToolUse_conditional_obligation_writer.py\"",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "run_terminal_command",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\mutation_post.py\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python \"C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "search_replace|write|run_terminal_command",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\mutation_post.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\quality_gate\\main.py\"",
            "timeout": 60
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\quality_cleanup.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\quality_cleanup.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## 4. Retired File

### equivalence-bypass-gate.json (RETIRED — empty hooks array)

```json
{
  "hooks": {
    "Stop": []
  }
}
```

### equivalence_bypass_gate.retired.md (NEW — retirement documentation)

```markdown
# equivalence_bypass_gate — RETIRED 2026-08-09

Replaced by structural conditional-obligation mechanism in `quality_gate/main.py`.

## Why retired

The old gate used prose-semantic regex to detect skill-equivalence bypass claims.
It produced **255 false blocks on 2026-08-09 alone** (`hook_failures.jsonl`) —
it could not distinguish DISCUSSING a bypass from COMMITTING one.

## What replaced it

The replacement enforces the **OBLIGATION, not the JUSTIFICATION**:

- hooks/** modified → `/review` REQUIRED (detected from transcript + mutation receipts)
- `quality_gate/main.py` blocks until `/review` evidence satisfies the obligation
- Prose is irrelevant — the mechanism reads state, not text

See commits `f9ca5e9` through `2309233` for the full implementation.
Live acceptance: cases C, D, E, F, H confirmed through real runtime.

## Threat model

This mechanism prevents semantic self-exemption, alternate ordinary mutation
paths (via receipt corroboration), stale evidence (via freshness binding), and
tampering with derived obligation state. It assumes the runtime's
transcript/control-plane files are not deliberately destroyed or rewritten to
defeat enforcement. Because hooks and the model operate within the same
host/user trust domain, cryptographic or malicious-control-plane tamper
resistance is not claimed.
```

## 5. Test Harnesses

### test_conditional_obligation_spike.py (not found)

### test_falsification_matrix_AK.py (not found)

### test_authority_attack.py (not found)

### test_falsification_678.py (not found)

## 6. Runtime Receipts

### quality-shadow log (this session)

```jsonl
{"ts": "2026-08-09T23:25:21Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "", "worktree_id": "", "is_git": false, "old_gate_decision": "allow", "receipt_gate_decision": "block", "receipt_gate_mode": "shadow", "receipt_state_available": false, "receipt_valid": false, "effective_decision": "allow", "difference": true, "reason": "MISSING_RECEIPT", "relevant_scope": ["PostToolUse_conditional_obligation_writer.py", "main.py", "main.py", "quality_gates_frontmatter.py"], "covered_scope": [], "uncovered_scope": ["posttooluse_conditional_obligation_writer.py", "main.py", "main.py", "quality_gates_frontmatter.py"], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 16.68}
{"ts": "2026-08-10T01:48:56Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "block", "receipt_gate_decision": "block", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "block", "difference": false, "reason": "REPOSITORY_ID_MISMATCH", "relevant_scope": ["PostToolUse_conditional_obligation_writer.py", "main.py", "main.py", "quality_gates_frontmatter.py", "_disposable_live_test.py"], "covered_scope": [], "uncovered_scope": ["posttooluse_conditional_obligation_writer.py", "main.py", "main.py", "quality_gates_frontmatter.py", "_disposable_live_test.py"], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": true, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 62.7}
{"ts": "2026-08-10T01:50:56Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": [], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 54.19}
{"ts": "2026-08-10T01:52:15Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": [], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 87.06}
{"ts": "2026-08-10T01:53:51Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": [], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 38.16}
{"ts": "2026-08-10T01:58:13Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": ["PostToolUse_conditional_obligation_writer.py", "main.py", "main.py", "quality_gates_frontmatter.py", "_disposable_live_test.py"], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 57.29}
{"ts": "2026-08-10T02:15:39Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "block", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": true, "reason": "STALE_FILE_STATE", "relevant_scope": ["main.py"], "covered_scope": [], "uncovered_scope": ["main.py"], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 67.27}
{"ts": "2026-08-10T02:16:56Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "is_git": true, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": true, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": [], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": false, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 45.88}
{"ts": "2026-08-10T03:38:13Z", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "p:", "repository_id": "", "worktree_id": "", "is_git": false, "old_gate_decision": "allow", "receipt_gate_decision": "allow", "receipt_gate_mode": "shadow", "receipt_state_available": false, "receipt_valid": false, "effective_decision": "allow", "difference": false, "reason": "NO_CLAIM", "relevant_scope": [], "covered_scope": [], "uncovered_scope": [], "consumed_receipt_ids": [], "receipt_backed": false, "reason_codes": {"verification_ran": true, "code_modified_after_verification": false, "stale_by_time": true, "unclassified_write_observed": false}, "workspace_match": true, "unclassified_write_observed": false, "latency_ms": 23.05}
```

### cond-freshness state (this session)

```json
{"review": "2026-08-10T02:13:39Z"}
```

### Verification receipts (last 5)

#### rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_fdfd265449d347f3ac6bb43e.json

```json
{"receipt_id": "rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_fdfd265449d347f3ac6bb43e", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "P:/", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "git_dir": "p:/.git", "tool_call_id": "call_fdfd265449d347f3ac6bb43e", "record_type": "VERIFICATION_SUCCEEDED", "evidence_state": "BOUND", "verification_command": "python P:/tmp/verify_retirement.py", "verification_command_truncated": false, "actual_exit_status": 0, "verifier_type": "script_verifier", "verifier_capability": "unit_behavior", "observed_state_refs": ["c:/users/brsth/.grok/hooks/scripts/_disposable_live_test.py", "c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "observed_state_identities": [], "scope_fingerprint_at_execution": "4bd169bf124e42fcac174fb5dd59cd2d88ad947159b199d6fc8084cd6f6ae445", "claimed_scope_refs": [], "claimed_scope_identities": [], "scope_basis": "UNKNOWN", "obligation_nonce": null, "started_at": "2026-08-10T02:13:49Z", "completed_at": "2026-08-10T02:13:51Z", "result_ref": "PostToolUse:call_fdfd265449d347f3ac6bb43e", "scope_type": "OBSERVED_ONLY", "scope_refs": []}
```

#### rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_db553c3724444469b569b732.json

```json
{"receipt_id": "rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_db553c3724444469b569b732", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "P:/", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "git_dir": "p:/.git", "tool_call_id": "call_db553c3724444469b569b732", "record_type": "VERIFICATION_FAILED", "evidence_state": "BOUND", "verification_command": "python P:/tmp/verify_retirement.py", "verification_command_truncated": false, "actual_exit_status": 1, "verifier_type": "script_verifier", "verifier_capability": "unit_behavior", "observed_state_refs": ["c:/users/brsth/.grok/hooks/scripts/_disposable_live_test.py", "c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "observed_state_identities": [], "claimed_scope_refs": [], "claimed_scope_identities": [], "scope_basis": "UNKNOWN", "obligation_nonce": null, "started_at": "2026-08-10T02:13:12Z", "scope_fingerprint_at_execution": "4bd169bf124e42fcac174fb5dd59cd2d88ad947159b199d6fc8084cd6f6ae445", "completed_at": "2026-08-10T02:13:13Z", "result_ref": "PostToolUse:call_db553c3724444469b569b732"}
```

#### auto-verify-ast.parse-019fe88b-af8e-77b2-87cd-04711b7f8257-c-users-brsth-.grok-hooks-scripts-quality_gate-main.py.json

```json
{"receipt_id": "auto-verify-ast.parse-019fe88b-af8e-77b2-87cd-04711b7f8257-c:-users-brsth-.grok-hooks-scripts-quality_gate-main.py", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "tool_call_id": "auto-verify-main.py", "record_type": "VERIFICATION_SUCCEEDED", "evidence_state": "BOUND", "verification_command": "ast.parse c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py", "verification_command_truncated": false, "actual_exit_status": 0, "verifier_type": "ast.parse", "verifier_capability": "syntax", "observed_state_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "claimed_scope_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "scope_fingerprint_at_execution": "4a09c1f3c55e7afc6e5ec143d32dd49eda4d1750748cbedd598fd86e56f958eb", "scope_basis": "auto-verify-post-edit", "obligation_nonce": null, "started_at": "2026-08-10T02:12:49Z", "completed_at": "2026-08-10T02:12:49Z", "result_ref": "PostToolUse:auto-verify:main.py", "scope_type": "CLAIMED_SCOPE", "scope_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"]}
```

#### auto-verify-ruff-check-019fe88b-af8e-77b2-87cd-04711b7f8257-c-users-brsth-.grok-hooks-scripts-quality_gate-main.py.json

```json
{"receipt_id": "auto-verify-ruff-check-019fe88b-af8e-77b2-87cd-04711b7f8257-c:-users-brsth-.grok-hooks-scripts-quality_gate-main.py", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "tool_call_id": "auto-verify-main.py", "record_type": "VERIFICATION_SUCCEEDED", "evidence_state": "BOUND", "verification_command": "ruff check c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py", "verification_command_truncated": false, "actual_exit_status": 0, "verifier_type": "ruff check", "verifier_capability": "static_analysis", "observed_state_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "claimed_scope_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"], "scope_fingerprint_at_execution": "4a09c1f3c55e7afc6e5ec143d32dd49eda4d1750748cbedd598fd86e56f958eb", "scope_basis": "auto-verify-post-edit", "obligation_nonce": null, "started_at": "2026-08-10T02:12:49Z", "completed_at": "2026-08-10T02:12:49Z", "result_ref": "PostToolUse:auto-verify:main.py", "scope_type": "CLAIMED_SCOPE", "scope_refs": ["c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py"]}
```

#### rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_83b214e690644b7da1f2f457.json

```json
{"receipt_id": "rcpt-019fe88b-af8e-77b2-87cd-04711b7f8257-call_83b214e690644b7da1f2f457", "session_id": "019fe88b-af8e-77b2-87cd-04711b7f8257", "workspace_id": "P:/", "repository_id": "fd566fe6a60cdfb0", "worktree_id": "fb5371f454f2929c", "git_dir": "p:/.git", "tool_call_id": "call_83b214e690644b7da1f2f457", "record_type": "VERIFICATION_FAILED", "evidence_state": "BOUND", "verification_command": "python -m pytest \"c:/users/brsth/.grok/hooks/posttooluse_conditional_obligation_writer.py\" \"c:/users/brsth/.grok/hooks/scripts/quality_gate/main.py\" \"c:/users/brsth/.grok/hooks/scripts/quality_gates_frontmatter.py\" \"c:/users/brsth/.grok/hooks/scripts/_disposable_live_test.py\" --co 2>&1 | Select-Object -Last 5", "verification_command_truncated": false, "actual_exit_status": 1, "verifier_type": "test_runner", "verifier_capability": "unit_behavior", "observed_state_refs": ["c:/users/brsth/.grok/hooks/scripts/_disposable_live_test.py"], "observed_state_identities": [], "claimed_scope_refs": ["c:/users/brsth/.grok/hooks/scripts/_disposable_live_test.py"], "claimed_scope_identities": [], "scope_basis": "EXPLICIT_PATH_ARGUMENT", "obligation_nonce": "9810c2c4-e320-4576-8762-fe0b58e12791", "started_at": "2026-08-10T01:56:01Z", "scope_fingerprint_at_execution": "12ce382e55b1f348bd6ec2a5154e4a95accca8c6a9ca60b39cd8388560ff8513", "completed_at": "2026-08-10T01:56:08Z", "result_ref": "PostToolUse:call_83b214e690644b7da1f2f457"}
```

## 7. /review Artifacts
