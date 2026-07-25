# Design: Mechanical detection of predictable code problems (Python 3.14 + AI-generated code)

**Status:** Design (not implemented)
**Author:** Grok Build (design subagent)
**Date:** 2026-07-25
**Source research:** `P:/.data/wiki/concepts/predictable-code-problems-detection-python-314-ai-generated.md`
**Scope:** `P:\` workspace on Grok Build (multi-root monorepo, PowerShell 7, Python 3.14.0)

---

## 1. Overview

### Problem in one sentence

This workspace is an **AI generating Python code about AI code quality**, on a Python version with known silent-behavior changes (3.14), yet we rely on the agent's *choice* to run static analysis — there is no mechanical gate, no Python-3.14-specific detector, and no contract test harness at skill boundaries, so the exact "predictable problems" the research catalogues (1.7× defect rate, silent behavior changes, plausible-but-wrong refactors) reach our own skill code uncaught.

### What this design proposes

Wire the **already-installed** static-analysis tools (ruff, pyright, mypy, semgrep, bandit — all verified present) into the existing hook + skill infrastructure so detection fires **mechanically, not by agent choice**. Four components:

| # | Component | Layer | What it does |
|---|-----------|-------|--------------|
| **A** | `static_gate` hook trio | Grok UserPromptSubmit + PostToolUse + Stop | Clears state at turn start; records every `.py` edit; blocks the turn's Stop if ruff+pyright report errors on the touched files. Sub-second to ~1s feedback. |
| **B** | `/static` skill | On-demand CLI skill | Runs ruff + pyright + py314 detectors + semgrep on a target (diff/package/path); emits `findings.json` compatible with `/review`'s schema. |
| **C** | `py314_audit` detector module | Reusable Python lib | Encodes the 8 Python-3.14 gotchas as deterministic AST checks; version-aware (3.14.0 vs 3.14.5+). Plugs into B and optionally A. |
| **D** | Wiring into `/check` + `/review` + contract harness | SKILL.md edits + runner | Makes `/check` Phase B *require* ruff+pyright on Python scope; adds a deterministic static pass to `/review`; adds a `contract_runner` that exercises existing `validate_*.py` against golden inputs. |

The design follows the research's central finding directly: *"The fix is not 'review harder.' It's 'automate the verification that humans skip.'"* In our substrate, "humans skip" → "the agent doesn't choose to run ruff." The structural fix is a hook that runs it regardless of choice, at turn-end latency (the Stop event), not at commit latency.

---

## 2. Background (current state — verified)

### 2.1 What is already installed (OBSERVED)

```
ruff 0.14.7     C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\ruff.exe
pyright 1.1.409 C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pyright.exe
mypy 1.19.0     C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\mypy.exe
semgrep         ...\Scripts\semgrep.exe
bandit 1.9.2    ...\Scripts\bandit.exe
uv 0.9.13       ...\Scripts\uv.exe
python 3.14.0   (tags/v3.14.0:ebf955d, Oct 7 2025)
```

The tooling gap is **zero**. The gap is **wiring**.

### 2.2 What is already wired (OBSERVED)

- **`/check`** (`P:/.grok/skills/check/SKILL.md`) — multi-concern session verification. Has a deterministic preprocessor (`__lib/preprocessor.py`) extracting 10 detector buckets from the transcript. Phase B Step 6 *permits* verifiers to "run linters/type-checkers if configured (cargo clippy, eslint, mypy, tsc)" — but it is **optional**, and there is no requirement to surface static findings as `bug` severity. Auto-escalates to `/review` on load-bearing triggers.
- **`/review`** (`~/.grok/skills/review/SKILL.md`) — multi-lens review with specialists, independent verify, root-cause clustering, durable FINDINGS.md. Has lenses: correctness, security, integrity, concurrency, architecture, maintainability. **No `static` lens.** Specialists hunt blind; no deterministic pre-pass seeds findings.
- **Validators** (`~/.grok/skills/www/scripts/validate_verdict_consistency.py`, `validate_disconfirmation.py`; `~/.grok/skills/close/__lib/validate_close_receipt.py`) — standalone deterministic Python scripts, exit 0/1/2. These are the proven "code-over-prose" enforcement pattern. They are **output-contract tests** but have no runner / golden-input regression harness.
- **Hook infrastructure** (`~/.grok/hooks/`) — confirmed contract (user-guide `10-hooks.md`):
  - `PreToolUse`: blocking via stdout `{"decision":"deny","reason":...}` or exit 2.
  - `Stop`: blocking via stdout `{"decision":"block","reason":...}` or exit 2 with stderr feedback.
  - `PostToolUse`: non-blocking; stdout ignored; used to record state.
  - Proven precedent: `quality_nudge.py` (PostToolUse on `search_replace|write`) writes a per-session JSONL state file → `quality_gate.py` (Stop) reads it and blocks with specific messages. **This is the exact pattern Component A reuses.**

### 2.3 What is missing (the three research gaps + one)

| Gap (from wiki) | Evidence | Impact |
|---|---|---|
| **No static analysis gate** | No workspace-wide `ruff.toml`/`pyproject.toml [tool.ruff]` (only narrow `P:/.claude/hooks/pyproject.toml`: security rules, test files only, `target-version="py312"`). Root `P:/pyrightconfig.json` targets 3.14 but has no lint rules. | Type errors, undefined names, dead code, removed-feature usage reach skill code uncaught. |
| **No Python-3.14-specific detector** | The 8 gotchas (PEP 649 deferred annotations, PEP 667 `locals()`, `int()`/`__trunc__`, `NotImplemented` truthiness, GC reversion, pickle proto 5, removed features, free-threaded overhead) are not encoded as checks anywhere. | Silent behavior changes — the highest-risk class per research — pass all tests and review. |
| **No contract testing at skill boundaries** | Validators exist per-skill but have no shared runner, no golden-input fixtures, no regression suite. | Research Pattern 2 ("confident refactoring breaks callers") applies to our own skills: a `/check` preprocessor change can silently break `/review`'s session-aware hint injection with no test catching it. |
| **Behavioral testing framework** (partial gap) | `/check` verifiers DO run tests (Phase B) — this is closer to covered than the wiki implies. The real residual gap is **contract** tests, not behavioral. | Reclassified: behavioral is covered by `/check`; contract is not. |

### 2.4 The reflexive risk

The research's Part 3 applies to **our own code**: the `/check`, `/review`, `/aar`, `/close` skills are AI-generated Python that other agents depend on. A "plausible but wrong logic" bug in `validate_verdict_consistency.py` would silently let closure-pressure minimizations through. The detection infrastructure this design proposes is itself the highest-value target for the detection infrastructure.

---

## 3. Architecture

### 3.1 Component map and data flow

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │              NEW USER PROMPT (turn boundary)                        │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ UserPromptSubmit
                                 ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ UserPromptSubmit: static_turn_clear.py  (Component A — turn reset)   │
  │   - delete ~/.grok/hooks/state/static-<sid>.jsonl                    │
  │   - makes the gate's input per-TURN (Issue 15): after an 8-cap       │
  │     force-stop, the next turn starts with empty state, so the gate   │
  │     never re-blocks on prior-turn files                              │
  │   - does NOT fire between Stop continuations (only on new prompt) →  │
  │     Issue 1 within-turn invariant preserved                         │
  │   - non-blocking; fail-open                                          │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ (agent begins turn)
                                 ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                        AGENT EDITS A .py FILE                       │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ search_replace / write
                                 ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ PostToolUse: static_nudge.py   (Component A — recording arm, <1ms)   │
  │   - filter: tool_input file_path ends in .py                         │
  │   - append {file, mtime, tool} to ~/.grok/hooks/state/static-<sid>.jsonl │
  │   - NO tool invocation (Issue 2: an earlier draft ran ruff here, but │
  │     PostToolUse stdout is ignored on Grok so the result had no       │
  │     consumer; the Stop arm re-runs ruff+pyright anyway)              │
  │   - fail-open on any error                                           │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ (turn continues; more edits may accumulate)
                                 ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Stop: static_gate.py   (Component A — blocking arm)                  │
  │   - read static-<sid>.jsonl → dedupe file set                        │
  │   - skip only if no .py files OR reason != "end_turn"                │
  │   - run `ruff check --select E,F <files>` + `pyright <files>`        │
  │   - on ERROR-class findings (not style/warning):                     │
  │       stdout {"decision":"block","reason":"<table of findings>"}     │
  │       (re-blocks on stopHookActive==true if errors persist;          │
  │        8-continuation cap is the loop bound — see Issue 1 fix)       │
  │   - on clean: exit 0 AND delete state file (allow-path cleanup)      │
  │   - state file KEPT on block (needed for re-verification)            │
  │   - append trace entry to static-gate-<sid>.log (observability)      │
  │   - fail-open (timeout/crash → exit 0)                               │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ (agent fixes, re-edits, Stop re-fires;
                                 │   gate re-runs ruff+pyright each time)
                                 ▼
                            TURN ENDS (or 8-continuation cap forces stop)
```

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ ON-DEMAND (Component B: /static skill)                              │
  │   /static                 → dirty tree (like /review local)         │
  │   /static yt-is           → package                                │
  │   /static --py314         → only the 3.14 detector (Component C)    │
  │   /static --security      → add semgrep + bandit                   │
  │   /static --seed-review   → write findings.json into a /review run_dir │
  │                                                                      │
  │   pipeline: ruff → pyright → py314_audit → (semgrep|bandit)          │
  │   output: findings.json  (/review-compatible schema) + STATIC.md     │
  └─────────────────────────────────────────────────────────────────────┘
```

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ INTEGRATION (Component D)                                           │
  │   /check Phase B:  REQUIRE ruff+pyright on scope_files ∩ *.py        │
  │                    surface errors as severity=bug (auto-FAIL)        │
  │   /review:         new deterministic "static pre-pass" (Step 3.6)    │
  │                    seeds findings.json before specialists;          │
  │                    specialists VERIFY + hunt what static misses      │
  │   contract_runner: discovers validate_*.py across skills, runs      │
  │                     each against its fixtures/, reports pass/fail    │
  └─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Design principles applied

1. **Reuse the proven pattern.** Component A is `quality_nudge.py`→`quality_gate.py` with ruff+pyright substituted for the quality gate's claim/verification check, and — critically — mirroring its 2nd-pass re-block logic (not the per-hook give-up an earlier draft used; see Issue 1). No new hook contract; just new state semantics.
2. **Cost-ordered pipeline** (research §1): ruff+pyright (turn-end, at Stop) → on-demand deep tools (semgrep/bandit, `/static` only). Both analyzers run once at turn-end on the stable change set, not per-edit (Issue 2: a per-edit ruff had no consumer since PostToolUse stdout is ignored).
3. **Fail-open is the Grok default** — the hook never blocks the agent on its own crash/timeout. Only *explicit error findings* block. This respects the multi-agent-host invariant (a broken hook must not stall 5 concurrent sessions).
4. **`findings.json` as the lingua franca.** Component B and C emit the same schema `/review` uses (`P:/.artifacts/<term>/grok-review/<slug>/<ts>/findings.json`), so static findings compose into the existing review pipeline without a translation layer.
5. **Version-aware, not version-blind.** Component C reads `sys.version_info` and the installed patch version; gotcha #5 (GC reversion) is gated to 3.14.5+ so it doesn't false-fire on our 3.14.0 build.

---

## 4. Implementation Sketch

All paths are absolute. New files marked **(new)**; edits marked **(edit)**.

### 4.1 Component A — `static_gate` hook trio

**(new)** `C:/Users/brsth/.grok/hooks/scripts/static_nudge.py` — PostToolUse, recording arm (<1ms; no tool invocation).

```python
#!/usr/bin/env python3
"""PostToolUse: record .py edits (file path + mtime only).

Mirrors quality_nudge.py. Non-blocking (PostToolUse stdout ignored on
Grok — verified 10-hooks.md:303). Writes only the minimal record needed
by static_gate.py: {file, mtime, tool}. Does NOT run ruff here — the
Stop arm re-runs ruff+pyright on the deduped set, so a per-edit ruff
call would be computed and discarded (the PostToolUse→Stop split means
advisory per-edit results have no consumer). Keeping the arm cheap
bounds per-edit latency to <1ms regardless of file size.

Writes ~/.grok/hooks/state/static-<sid>.jsonl consumed by static_gate.py.
Fail-open: any error exits 0 silently.
"""
import json, re, sys, time
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("toolName") not in ("search_replace", "write"):
        sys.exit(0)
    sid = data.get("sessionId", "")
    if not re.match(r'^[0-9a-f-]{36}$', sid):
        sys.exit(0)
    # Read both snake_case and camelCase for parity with quality_nudge.py:123
    # (defensive against any tool variant that emits camelCase).
    ti = data.get("toolInput", {}) or {}
    fp = ti.get("file_path", "") or ti.get("filePath", "")
    if not fp or not fp.lower().endswith(".py"):
        sys.exit(0)
    if not Path(fp).exists():
        sys.exit(0)  # deleted file; nothing to lint later

    entry = {"file": fp, "mtime": time.time(), "tool": data["toolName"]}
    state = Path.home() / ".grok" / "hooks" / "state"
    state.mkdir(parents=True, exist_ok=True)
    with open(state / f"static-{sid}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    sys.exit(0)

if __name__ == "__main__":
    try: main()
    except Exception: sys.exit(0)
```

**(new)** `C:/Users/brsth/.grok/hooks/scripts/static_gate.py` — Stop, blocking arm.

```python
#!/usr/bin/env python3
"""Stop gate: block turn-end if ruff+pyright report ERRORS on touched .py files.

Reads ~/.grok/hooks/state/static-<sid>.jsonl (written by static_nudge.py).
Runs ruff (E,F) + pyright on the deduped file set. Blocks via
{"decision":"block","reason":...} on stdout.

Loop model (mirrors the proven quality_gate.py:832-848 2nd-pass logic):
  - On EVERY Stop fire with .py files in state, re-run ruff+pyright.
  - If errors persist, block AGAIN (including on stopHookActive==true).
  - The 8-continuation cap (10-hooks.md:265) is the loop bound, NOT a
    per-hook give-up. A gate that only checks once per turn is not
    mechanical — the agent could "fix" by introducing a new error.
  - State file is deleted ONLY when the gate allows (errors cleared),
    matching quality_gate.py which cleans up only on allow (lines
    836/848/872). Deleting on block would discard the file list needed
    for re-verification on the next Stop fire.

Skip conditions (these are genuine no-ops, not loop-avoidance):
  - reason != "end_turn"     (session-end Stop must not block)
  - no .py files in state
  - state file missing/empty
Fail-open on any exception: exit 0.
"""
import json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

RUFF = Path(os.environ.get("RUFF_PATH", r"C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\ruff.exe"))
PYRIGHT = Path(os.environ.get("PYRIGHT_PATH", r"C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pyright.exe"))
MAX_FILES = 40  # cap to bound Stop-hook latency on big turns
STATE_DIR = Path.home() / ".grok" / "hooks" / "state"

def collect_files(sid):
    f = STATE_DIR / f"static-{sid}.jsonl"
    if not f.exists():
        return [], 0
    seen, files = {}, []
    for line in f.read_text(encoding="utf-8").splitlines():
        try: e = json.loads(line)
        except Exception: continue
        p = e.get("file")
        if p and p not in seen and Path(p).exists():
            seen[p] = 1
            files.append(p)
    return files[:MAX_FILES], len(files)  # (checked, total)

def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception:
        return None

def write_trace(sid, decision, file_count, total_files, finding_count,
                finding_codes, stop_active, reason_skipped):
    """Append one-line JSON trace. Mirrors quality_gate.py:_write_trace_log
    (lines 538-566). Gives the operator data to tune MAX_FILES (Open Q1)
    and the E/F select set, and to answer 'did the gate ever false-block?'."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat()[:19] + "Z",
            "decision": decision,                # block | allow | skip
            "file_count": file_count,            # files actually checked
            "total_files": total_files,          # before MAX_FILES cap
            "capped": total_files > MAX_FILES,
            "finding_count": finding_count,
            "finding_codes": finding_codes[:20],
            "stop_hook_active": stop_active,
            "reason_skipped": reason_skipped,    # "" when not skipped
        }
        with open(STATE_DIR / f"static-gate-{sid}.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def cleanup_state(sid):
    try: (STATE_DIR / f"static-{sid}.jsonl").unlink()
    except Exception: pass

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    # Session-end Stop (and other non-end_turn reasons) must not block.
    if data.get("reason") and data["reason"] != "end_turn":
        sys.exit(0)
    sid = data.get("sessionId", "")
    if not re.match(r'^[0-9a-f-]{36}$', sid):
        sys.exit(0)
    stop_active = bool(data.get("stopHookActive"))
    files, total = collect_files(sid)
    if not files:
        # No .py edits this turn — nothing to gate. (Not a skip-on-active.)
        write_trace(sid, "skip", 0, total, 0, [], stop_active, "no_py_files")
        sys.exit(0)

    findings = []
    # Ruff: E,F (errors/unused), excluding pure style
    r = run([str(RUFF), "check", "--select", "E,F", "--output-format=json"] + files)
    if r and r.returncode != 0:
        for item in (json.loads(r.stdout or "[]")):
            findings.append(("ruff", item.get("filename",""), item.get("location",{}).get("row","?"),
                             item.get("code",""), item.get("message","")))
    # Pyright: errors only (--outputjson, filter severity=="error")
    r = run([str(PYRIGHT), "--outputjson"] + files)
    if r:
        try:
            for d in json.loads(r.stdout or "{}").get("generalDiagnostics", []):
                if d.get("severity") == "error":
                    findings.append(("pyright", d.get("file",""),
                                     d.get("range",{}).get("start",{}).get("line",0)+1,
                                     d.get("rule","pyright"),
                                     d.get("message","")))
        except Exception:
            pass

    codes = sorted({c for _,_,_,c,_ in findings})

    if not findings:
        # Errors cleared — allow AND clean up state (matches quality_gate.py
        # allow-path cleanup at lines 836/848/872).
        write_trace(sid, "allow", len(files), total, 0, [], stop_active, "")
        cleanup_state(sid)
        sys.exit(0)

    # Errors present — block. Re-blocks on stopHookActive==true too; the
    # 8-continuation cap is the loop bound, exactly as quality_gate.py does.
    lines = [f"  - {tool} {Path(f).name}:{row} [{code}] {msg}"
             for tool,f,row,code,msg in findings[:15]]
    extra = f"\n  ...and {len(findings)-15} more" if len(findings) > 15 else ""
    cap_note = ""
    if total > MAX_FILES:
        cap_note = (f"\n  NOTE: {total - MAX_FILES} additional file(s) not checked "
                    f"(exceeded MAX_FILES={MAX_FILES} cap); run `/static` for full coverage.")
    reason = (f"Static analysis found {len(findings)} error(s) in Python files edited this turn. "
              f"Fix or run `/static` for detail.\n" + "\n".join(lines) + extra + cap_note)
    # Do NOT delete state on block — needed for re-verification next Stop fire.
    write_trace(sid, "block", len(files), total, len(findings), codes, stop_active, "")
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)

if __name__ == "__main__":
    try: main()
    except Exception: sys.exit(0)
```

**(new)** `C:/Users/brsth/.grok/hooks/scripts/static_turn_clear.py` — UserPromptSubmit, turn-boundary reset (Issue 15 fix).

```python
#!/usr/bin/env python3
"""UserPromptSubmit: truncate the per-session static state file at turn start.

Makes static-<sid>.jsonl per-TURN by construction (vs per-session). Without
this, the file accumulates across all turns in a session; after an 8-cap
force-stop (10-hooks.md:265) with an unresolved error, the block path
(correctly, per Issue 1) preserves state, so the NEXT turn's nudge would
append to the stale file and the gate would re-block on prior-turn files
— a cross-turn false block with a misattributed "files edited this turn"
message (Issue 15).

UserPromptSubmit fires only on a NEW user prompt — NOT between Stop
continuations within a turn (10-hooks.md:89 "You submit a prompt") — so
truncating here does NOT disturb the Issue 1 invariant: within a turn,
state persists across Stop re-blocks so the gate can re-verify.

Non-blocking (10-hooks.md:89 confirms UserPromptSubmit is "No" / non-blocking;
stdout is ignored). Fail-open: any error exits 0 silently.

Note: this truncates only the gate INPUT (static-<sid>.jsonl). The gate
OUTPUT trace (static-gate-<sid>.log) is append-only across the whole session
for post-hoc analysis and is intentionally NOT cleared here.
"""
import json, re, sys
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    sid = data.get("sessionId", "")
    if not re.match(r'^[0-9a-f-]{36}$', sid):
        sys.exit(0)
    state = Path.home() / ".grok" / "hooks" / "state" / f"static-{sid}.jsonl"
    try:
        state.unlink()  # truncate == delete; static_nudge recreates on first edit
    except FileNotFoundError:
        pass  # first turn, or no edits yet — nothing to clear
    except Exception:
        pass  # fail-open
    sys.exit(0)

if __name__ == "__main__":
    try: main()
    except Exception: sys.exit(0)
```

**(edit)** `C:/Users/brsth/.grok/hooks/quality-gate.json` — add the three new hook entries alongside the existing `quality_nudge`/`quality_gate` (additive; existing hooks untouched).

Add a new top-level `UserPromptSubmit` array (verified: no `UserPromptSubmit` hook exists in the workspace today; `10-hooks.md:89` confirms the event is non-blocking and "always fires"):
```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\static_turn_clear.py\"",
        "timeout": 5
      }
    ]
  }
]
```
> The UserPromptSubmit hook is the **turn-boundary reset** (Issue 15 fix). It makes `static-<sid>.jsonl` per-turn by construction so the gate never re-blocks on a prior turn's files after an 8-cap force-stop. It fires only on a NEW user prompt — NOT between Stop continuations within a turn — so the Issue 1 within-turn invariant (state persists across re-blocks) is preserved.

Add to the existing `PostToolUse` array (matcher `search_replace|write`):
```json
{
  "type": "command",
  "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\static_nudge.py\"",
  "timeout": 15
}
```
Add a new top-level `Stop` hook alongside the existing `quality_gate.py` entry:
```json
{
  "type": "command",
  "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\static_gate.py\"",
  "timeout": 60
}
```
> Note: multiple Stop hooks all run; each can independently block. `static_gate` fails open, so it cannot deadlock the turn.

**(new)** workspace ruff config `P:/ruff.toml` (the workspace has none today):
```toml
line-length = 120
target-version = "py314"          # CRITICAL: current is py312 in the only existing config
extend-exclude = ["worktrees", ".worktrees", ".artifacts", "tmp", "__pycache__"]

[lint]
# E/F = errors + pyflakes (undefined names, unused imports) — the blocking set.
# Plus a curated subset that catches AI-code patterns from the research:
#   SIM  (simflakes — simplifications; catches copy-paste drift)
#   B    (bugbear — common logic errors; catches plausible-but-wrong)
#   RUF  (ruff-specific; includes RUF013 implicit-optional)
#   U    (pyupgrade — flags removed 3.10-3.12 features → 3.14 gotcha #7)
select = ["E", "F", "SIM", "B", "RUF", "U"]
ignore = ["E501"]  # line length handled by formatter, not blocking

[lint.per-file-ignores]
"tests/**" = ["S101"]  # assert allowed in tests
```
> `target-version = "py314"` is load-bearing: it makes ruff's `U` (pyupgrade) rules flag constructs removed in the 3.10→3.14 window — directly encoding gotcha #7 from the research.

**(edit)** `P:/pyrightconfig.json` — the existing config is:
```json
{ "pythonVersion": "3.14", "extraPaths": ["../../packages/handoff"] }
```
The additive edit (safe) is to add `typeCheckingMode` and `exclude` **without touching `extraPaths`**:
```json
{
  "pythonVersion": "3.14",
  "typeCheckingMode": "standard",
  "extraPaths": ["../../packages/handoff"],
  "exclude": ["worktrees", ".worktrees", "**/.artifacts", "**/__pycache__"]
}
```
> **`extraPaths` is preserved verbatim** — the prior draft silently changed it to `["packages/handoff"]`, a behavioral edit with no justification. Pyright resolves `extraPaths` relative to the config file, so changing the path changes resolution. **Investigation (verified): `P:/packages/handoff` does NOT exist** (`Test-Path = False`; no `handoff` dir under `packages/`). The existing entry is a **dead reference** in both forms — the path resolves to nothing. This is a pre-existing latent bug, not something this design should fix in passing. Open Question (new, §9 Q7): should the dead `extraPaths` entry be removed entirely? That is a separate behavioral change and is **out of scope for this design** unless the operator confirms. The additive edit above leaves it exactly as-is.

### 4.2 Component B — `/static` skill

**(new)** `P:/.grok/skills/static/SKILL.md` — minimal orchestrator skill (following the `/review`/`/check` shell pattern; the heavy lifting is the lib below).

**(new)** `P:/.grok/skills/static/__lib/runners.py` — thin subprocess wrappers around ruff/pyright/semgrep/bandit returning normalized finding dicts.

**(new)** `P:/.grok/skills/static/__lib/static_pipeline.py` — the orchestrator:

```python
"""Static analysis pipeline. Emits /review-compatible findings.json.

Stages (cost-ordered, short-circuit optional via --fail-fast):
  1. ruff check        (always)
  2. pyright           (always)
  3. py314_audit       (always; Component C)
  4. semgrep --config auto  (--security only)
  5. bandit -r               (--security only)

Finding shape matches /review Step 4:
  {id, severity, priority, location, line_range, title, detail,
   evidence, fix, confidence_score, introduced_by_change, claim_type, source}
`source` field = "ruff"|"pyright"|"py314"|"semgrep"|"bandit".

NOTE on `source`: this field is an EXTENSION to /review's documented
finding shape (SKILL.md Step 4 lines 476-489 list the canonical fields
without `source`). It is NOT invented here — /review already uses `source`
ad hoc in the adversarial-critic path (`source: adversarial_critic`,
SKILL.md line 673). We adopt the same convention. PR 5 includes a
one-line schema-doc update to /review Step 4 making `source` first-class.

Target resolution:
  - empty arg       → dirty tree: `git diff --name-only HEAD` (tracked,
                      modified) UNION `git ls-files --others --exclude-standard`
                      (untracked), filtered to *.py. Reuses /review's notion
                      of "staged + unstaged + untracked" (Step 3, lines 330-335).
  - <path>          → that path (file or dir, recursive for dir)
  - <package-name>  → resolve to P:/packages/<name> if it exists (like /review)
  - --diff <file>   → parse the file's changed-file list
"""
```
Key CLI (defined in SKILL.md, implemented in `static_pipeline.py`):
```
/static [target]              # target: empty=dirty tree, path, package, --diff <file>
/static --py314               # only the Python-3.14 detector
/static --security            # add semgrep + bandit
/static --seed-review <dir>   # write findings.json into an existing /review run_dir
/static --format json|md
```
Output contract:
- `P:/.artifacts/<term>/grok-static/<slug>/<ts>/findings.json` (schema-compatible with `/review`)
- `P:/.artifacts/<term>/grok-static/<slug>/<ts>/STATIC.md` (human report; same layout discipline as FINDINGS.md)
- Verdict: `clean` | `needs_fixes` | `critical` (errors only → critical)

### 4.3 Component C — `py314_audit` detector module

**(new)** `P:/.grok/skills/static/__lib/py314_audit.py` — version-aware deterministic checks for the 8 gotchas. All structurally-decidable checks (#1-#4, #6) are **AST-level** via `ast` (no grep/substring matching — see Issue 10: a grep on `get_type_hints` would false-fire on comments/docstrings and train the agent to ignore findings). The module exposes a single `--ast` engine; a `--grep` fast-path is intentionally NOT provided because it would create a two-tier false-positive surface.

```python
"""Python 3.14 predictable-problem detector.

Encodes the 8 gotchas from the research wiki as deterministic checks.
Version-aware: gotcha #5 (GC reversion) gated to >=3.14.5.

Each check returns a list of findings with:
  rule_id, severity, file, line, message, fix, gotcha_number

CLI:
  python py314_audit.py <path...>            # all checks (AST engine)
  python py314_audit.py <path...> --json     # findings.json-compatible
"""
import ast, sys
from pathlib import Path

PATCH = sys.version_info[2]  # 0 for our 3.14.0 build

CHECKS = []  # list of (rule_id, gotcha_n, severity, runner_fn)

# --- Gotcha 2: locals() semantics (PEP 667) ---
def _check_locals(tree, src, path):
    # AST: find `locals()` call whose result is assigned or mutated
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'locals':
            yield ("PY314-667", 2, "risk", path, node.lineno,
                   "locals() now returns a live mapping (PEP 667); "
                   "modifying it or assuming a snapshot breaks on 3.14.",
                   "Audit each call site; do not rely on locals() mutation.")
CHECKS.append(("PY314-667", 2, _check_locals))

# --- Gotcha 3: int() no longer delegates to __trunc__() ---
def _check_trunc(tree, src, path):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '__trunc__':
            yield ("PY314-TRUNC", 3, "bug", path, node.lineno,
                   "int(obj) no longer falls back to __trunc__(); "
                   "implement __int__() or __index__().",
                   "Add __int__ (or __index__) returning the same value.")
CHECKS.append(("PY314-TRUNC", 3, _check_trunc))

# --- Gotcha 4: NotImplemented in boolean context raises TypeError ---
def _check_notimplemented(tree, src, path):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value is NotImplemented:
            # flag if inside If/While/BoolOp/UnaryOp(Not)
            if isinstance(getattr(node, '_parent', None),
                          (ast.If, ast.While, ast.BoolOp, ast.UnaryOp)):
                yield ("PY314-NI", 4, "bug", path, node.lineno,
                       "NotImplemented in boolean context raises TypeError on 3.14.",
                       "Use `is NotImplemented` identity check, not truthiness.")
CHECKS.append(("PY314-NI", 4, _check_notimplemented))

# --- Gotcha 1: deferred annotations (PEP 649) ---
def _check_get_type_hints(tree, src, path):
    # AST-level (consistent with #2/#3/#4/#6): flag Call nodes whose target is
    # typing.get_type_hints or a bare get_type_hints import. A pure substring
    # grep ('get_type_hints' in line) would false-fire on comments, docstrings,
    # and string literals — cry-wolf that trains the agent to ignore findings.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # typing.get_type_hints  OR  from typing import get_type_hints; get_type_hints(...)
        is_qualified = (isinstance(func, ast.Attribute) and func.attr == 'get_type_hints'
                        and getattr(func.value, 'id', '') == 'typing')
        is_bare = isinstance(func, ast.Name) and func.id == 'get_type_hints'
        if is_qualified or is_bare:
            yield ("PY314-649", 1, "risk", path, node.lineno,
                   "typing.get_type_hints() now triggers deferred annotation "
                   "evaluation (PEP 649). Metaclass patterns inspecting annotations "
                   "at class-creation time may behave differently.",
                   "Test get_type_hints() on all models at runtime on 3.14.")
CHECKS.append(("PY314-649", 1, _check_get_type_hints))

# --- Gotcha 6: pickle default protocol 5 ---
def _check_pickle(tree, src, path):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and getattr(node.func, 'attr', '') in ('dumps','load','loads')
                and getattr(node.func.value, 'id', '') == 'pickle'):
            yield ("PY314-PICKLE", 6, "risk", path, getattr(node,'lineno',1),
                   "pickle default protocol changed to 5 on 3.14; "
                   "data exchanged with <=3.7 may fail to unpickle.",
                   "Pin protocol explicitly if exchanging data cross-version.")
CHECKS.append(("PY314-PICKLE", 6, _check_pickle))

# --- Gotcha 5: GC reversion (3.14.5+ only) ---
if PATCH >= 5:
    def _check_gc_note(tree, src, path):
        # informational: no static signal; emit once per package if latency-sensitive
        return iter([])  # placeholder — real check is a benchmark, not static
    CHECKS.append(("PY314-GC", 5, _check_gc_note))
# else: not registered; 3.14.0 does not have the reversion.

# --- Gotcha 7: removed features — delegated to ruff U (pyupgrade) ---
# (handled by Component A/B ruff config; py314_audit just documents the mapping)

# --- Gotcha 8: free-threaded overhead — informational, no static check ---
```
> The `ast` module's parent-link requires a `NodeTransformer` pre-pass to set `_parent` (stdlib `ast` doesn't populate it). The runner does this once per file. This is a known, bounded implementation detail.

### 4.4 Component D — wiring + contract harness

**(edit)** `P:/.grok/skills/check/SKILL.md` — Phase B Step 6. Currently says "Run linters/type-checkers if configured." Change to:

> **6. STATIC ANALYSIS (mandatory when any `.py` file is in `scope_files`).**
> Run `ruff check --select E,F <scope .py files>` and `pyright <scope .py files>`. Any ruff `E`/`F` or pyright `error` finding → emit as an Issue with `severity: bug` (auto-FAIL per Phase B rules). Optionally run `python P:/.grok/skills/static/__lib/py314_audit.py <files> --json` and merge its findings. Record the exact commands and exit codes in "Build & Test Results." Skipping this step when Python files are in scope is a contract violation.

**(edit)** `~/.grok/skills/review/SKILL.md` — insert a new **Step 3.6 — Deterministic static pre-pass** immediately *after* Step 3.5 (depth gate + prior ledger) and *before* Step 4 (specialist pass). *(Verified step order in the live SKILL.md: Step 3 "Collect evidence" → Step 3.5 "Depth gate" → Step 4 "Specialist pass." There is no interval "between Step 3 and Step 3.5" — that was an error in the prior draft.)*

> **Step 3.6 — Static pre-pass (runs after the depth gate, before specialists fan out, when target contains `.py`).**
> Run `P:/.grok/skills/static/__lib/static_pipeline.py <target> --format json` and write the result to `$runDir/packets/_static.json` with `source: "static"`. **Do NOT write into `$runDir/specialists/`** — that directory is reserved by the "Parent must NOT author specialist JSON" invariant (Step 4): every file under `specialists/*.json` must be subagent-authored and counted in `_manifest.json`. Writing a parent-authored static seed there would (a) be mistaken for a specialist output by auditors counting `spawned.length >= 2`, and (b) breach the invariant the rule exists to enforce. The `packets/` location keeps the seed available to specialist prompts (passed by absolute path) without polluting the specialist directory.
>
> These findings seed the specialist pool: specialists **verify** each static finding (confirm/drop) AND hunt for what static analysis misses (logic errors, AI-code patterns from research Part 3). This implements the research's cost-ordered hierarchy: cheap deterministic checks first, expensive LLM review second. The static pre-pass does NOT replace specialists — it focuses them.

**(new)** `P:/.grok/skills/static/__lib/contract_runner.py` — discovers and runs all skill validators against golden inputs:

```python
"""Contract test runner for skill boundaries.

Discovers validate_*.py across skills and runs each against its sibling
fixtures/ directory (canned inputs with expected pass/fail). Reports a
JUnit-style summary. Catches research Pattern 2 (refactor breaks callers)
at the validator layer.

Discovery:
  ~/.grok/skills/*/scripts/validate_*.py
  ~/.grok/skills/*/__lib/validate_*.py
  P:/.grok/skills/*/__lib/validate_*.py

Each validator declares its contract via a module-level CONTRACTS list:
  CONTRACTS = [
    {"name": "proceed_with_open_gap", "input": "...", "expect_exit": 1},
    {"name": "clean_proceed", "input": "...", "expect_exit": 0},
  ]
Validators without CONTRACTS are skipped (back-compat).

CLI:
  python contract_runner.py                    # all skills
  python contract_runner.py --skill close      # one skill
  python contract_runner.py --json             # machine output
Exit: 0 only if all contracts pass.
"""
```
This is run by `/static --contracts` and wired into `/check` Phase B as an optional step when the session touched any `validate_*.py`.

---

## 5. API / Interface Changes

### 5.1 New hooks (Component A)

| File | Event | Matcher | Effect |
|---|---|---|---|
| `static_turn_clear.py` | UserPromptSubmit | (none — always fires) | Truncates `static-<sid>.jsonl` at turn start → makes state per-turn by construction (Issue 15 fix). Non-blocking. |
| `static_nudge.py` | PostToolUse | `search_replace\|write` | Records `.py` edits (file path + mtime) to state JSONL. Non-blocking. |
| `static_gate.py` | Stop | (none — always) | Blocks turn-end on ruff E/F + pyright errors in touched `.py` files. Fail-open. |

Registration: additive entries in `~/.grok/hooks/quality-gate.json` (existing hooks untouched). Per the plugin-mutation checklist analog, after editing the hook JSON the operator runs the active-surface regenerator: `python ~/.grok/hooks/scripts/active_surface_snapshot.py` and verifies via `~/.grok/active-surface.last.md`.

### 5.2 New config

| File | Change |
|---|---|
| `P:/ruff.toml` | **(new)** workspace ruff config; `target-version="py314"`, select E/F/SIM/B/RUF/U. |
| `P:/pyrightconfig.json` | **(edit)** add `typeCheckingMode: standard`, `exclude` worktrees/artifacts. |

### 5.3 New skill: `/static`

| Surface | Value |
|---|---|
| Invocation | `/static`, `/static <pkg>`, `/static --py314`, `/static --security`, `/static --seed-review <dir>` |
| Output | `findings.json` (review-compatible) + `STATIC.md` under `P:/.artifacts/<term>/grok-static/<slug>/<ts>/` |
| Verdict | `clean` / `needs_fixes` / `critical` |

### 5.4 New CLI tools (all under `P:/.grok/skills/static/__lib/`)

| Tool | Purpose |
|---|---|
| `static_pipeline.py` | Orchestrates ruff→pyright→py314→(semgrep/bandit); emits findings.json. |
| `py314_audit.py` | Standalone 8-gotcha detector; usable outside the skill. |
| `runners.py` | Normalized subprocess wrappers. |
| `contract_runner.py` | Discovers + runs skill validators against golden contracts. |

### 5.5 SKILL.md edits (Component D)

| Skill | Edit |
|---|---|
| `/check` Phase B Step 6 | Static analysis becomes **mandatory** (not optional) when `.py` in scope; errors → `severity: bug`. |
| `/review` new Step 3.6 | Deterministic static pre-pass seeds `packets/_static.json` (NOT `specialists/` — that dir is subagent-only per the Step 4 invariant) before specialist fan-out. |

### 5.6 No changes to

- `/check` preprocessor, `/aar`, `/close`, `/tp`, `/red-team` — untouched (additive design).
- Existing `quality_nudge.py`/`quality_gate.py` — untouched.
- AGENTS.md — no rule additions required (the hooks enforce mechanically; AGENTS.md already has the receipt rule and edit-then-verify).

---

## 6. Alternatives

**Hidden anchor (stated up front, per the recommendation rule):** all three alternatives assume (a) the tools are already installed — **verified true**; (b) Python is the primary language of the skills — **verified true**; (c) the workspace is a solo-operator multi-agent host where commit-latency feedback is too slow. The real axis of choice is **where enforcement lives**: the git layer, agent memory, or the session-hook layer.

### Alternative 1 — Git pre-commit hook (standard `pre-commit` framework)

Run ruff+pyright via a `.pre-commit-config.yaml` on `git commit`.
- **Pro:** ecosystem-native; works across Grok/Claude/Codex/editors; survives Grok rebuilds; zero Grok-specific code.
- **Con:** feedback arrives at commit time — minutes after the edit, after the agent has mentally moved on. The research's root cause is precisely that "steps 2–4 vanish" in the AI flow; a commit hook is step 5, still after the fact. On this host the agent **auto-commits per AGENTS.md policy**, so a failing pre-commit would either block auto-commit (friction) or be bypassed (`--no-verify`). Does not help mid-turn debugging.
- **Selection criterion: feedback latency.** Loses to in-session hooks.

### Alternative 2 — Manual `/static` skill only (no hook)

Ship Component B + C, skip the hook (Component A). Agent invokes `/static` when it wants analysis.
- **Pro:** zero hook risk; no fail-open edge cases; fully deterministic and inspectable; no Stop-hook latency.
- **Con:** relies on the agent **choosing** to invoke it — which is exactly the "review harder" anti-pattern the research rejects. The 1.7× defect rate comes from the missing feedback loop, and a manual skill does not close that loop; it gives the agent a tool it will use inconsistently. Verified empirically: `/check` already permits linters and agents skip them.
- **Selection criterion: enforcement reliability.** Loses to mechanical hooks.

### Alternative 3 (RECOMMENDED) — Hybrid: hook gate (A) + on-demand skill (B/C) + integration (D)

Component A gives the per-turn mechanical floor (closes the feedback loop). Component B/C gives depth on demand and feeds `/review`. Component D makes the existing verification pipeline consume static findings so they aren't a parallel path. Reuses the proven `quality_nudge`→`quality_gate` pattern and the proven validator pattern.
- **Pro:** covers all three modes — automatic (hook), deep (skill), integrated (review/check). Matches the research's cost-ordered hierarchy directly. Reuses installed tools and existing hook contract.
- **Con:** most moving parts; hook must be carefully fail-open; `MAX_FILES` cap needed to bound latency; loop bound is the documented 8-continuation cap (relied on by the proven `quality_gate.py`), not a per-hook give-up.
- **Wins on: feedback latency (A) + enforcement reliability (A) + depth (B/C) + composability (D).**

### Alternative 4 — PreToolUse write-gate (REJECTED, named for completeness)

A PreToolUse hook that blocks the `search_replace`/`write` call itself when the *resulting* file content has ruff E/F errors — block at edit time, before the turn continues.
- **Pro:** earliest possible feedback (the file never lands broken).
- **Con / why rejected:** it blocks file authoring mid-flight. An agent building a Python file incrementally writes syntactically-incomplete intermediate states (e.g. a function signature without its body yet, an import added before its use) — every one of those would be blocked by a write-gate, making the tool unusable for normal authoring. Ruff cannot distinguish "deliberately incomplete WIP" from "broken final state" at write time; only at turn-end (Stop) is the change set stable enough to judge. This is the same reason the proven `quality_nudge`/`quality_gate` split uses PostToolUse-record + Stop-gate rather than PreToolUse-block. **Dismissed.**

**Chosen: Alternative 3.** It is the only option that addresses the research's root cause (mechanical verification at turn-end latency) while still providing the depth and integration the existing skills expect. Transition effort is not a selection criterion (operator preference). The fail-open invariant makes the added hook risk acceptable on a multi-agent host.

---

## 7. Key Decisions

### D1. Block on ERRORS only, not warnings/style.
**Decision:** `static_gate.py` blocks only on ruff `E,F` and pyright `severity=error`. Style/warnings are advisory (written to state, surfaced by `/static`).
**Rationale:** a solo operator's worst outcome is a hook that blocks productive turns on noise (E501, naming). Blocking on undefined names (`F821`) and syntax/errors (`E`) catches the highest-severity AI-code defect class (plausible-but-wrong, research Pattern 1) without style friction. This mirrors `/review`'s "cap nits at 5" discipline.

### D2. Record per-edit, analyze per-turn (both ruff AND pyright at Stop).
**Decision:** `static_nudge.py` records only `{file, mtime, tool}` per edit (no tool invocation); `static_gate.py` runs ruff AND pyright together at turn-end on the deduped file set.
**Rationale:** an earlier draft had ruff run in the PostToolUse arm and pyright in the Stop arm. That was dropped (Issue 2): PostToolUse stdout is ignored on Grok (`10-hooks.md:303`), so the per-edit ruff output had no consumer and the Stop arm re-ran ruff from scratch anyway — pure wasted latency (~100ms × N edits). The corrected split keeps the PostToolUse arm at <1ms (file-path append only) and runs both analyzers once at Stop, where the change set is stable and the result actually reaches the agent. This still matches the `quality_nudge`/`quality_gate` precedent: nudge records, gate enforces.

### D3. `target-version = "py314"` in ruff config.
**Decision:** set explicitly, overriding the existing `py312` in `P:/.claude/hooks/pyproject.toml`.
**Rationale:** this single setting makes ruff's `U` (pyupgrade) rules flag every construct removed in 3.10→3.14 — mechanically encoding research gotcha #7 ("removed deprecated features"). It is the highest-leverage line in the whole design.

### D4. `py314_audit` as a standalone AST module, not ruff custom rules.
**Decision:** implement the 8 gotchas as a Python **AST** module rather than authoring ruff custom rules. (Earlier draft said "AST/grep"; the grep path was dropped — see Issue 10. A substring grep on `get_type_hints` would false-fire on comments/docstrings and train the agent to ignore findings.)
**Rationale:** ruff custom rules require Rust + the ruff rule-authoring pipeline — high friction for 8 checks, several of which (PEP 649 deferred annotations, GC) are not statically decidable and need a runtime/audit framing anyway. A Python module composes with `findings.json`, is debuggable on Windows/PowerShell, and can express "risk — needs runtime test" verdicts that ruff's pass/fail model cannot. Trade: we don't get ruff's speed for these 8; acceptable since they run on-demand, not per-edit.

### D5. `findings.json` as the single interchange schema; `source` is an adopted extension.
**Decision:** Component B and C emit the finding-object shape `/review` Step 4 defines, plus a `source` field discriminator (`ruff|pyright|py314|semgrep|bandit`).
**Rationale:** avoids a translation layer; static findings drop straight into `/review`'s specialist pool and FINDINGS.md. **Note (Issue 8):** `source` is an *extension* to `/review`'s documented Step 4 schema (which omits it) — but it is already used ad hoc by the adversarial-critic path (`source: adversarial_critic`, SKILL.md line 673). We adopt the same convention and PR 5 promotes `source` to first-class in the Step 4 schema doc. This is the composability invariant — no parallel artifact path.

### D6. Contract runner reuses existing validators; no new test framework.
**Decision:** `contract_runner.py` discovers and invokes the existing `validate_*.py` scripts against declared `CONTRACTS`; it does not introduce pytest/unittest as a skill-runtime dependency.
**Rationale:** the validators already work and already encode the contracts. The gap was a *runner* and *golden inputs*, not a new framework. Validators without `CONTRACTS` are skipped (back-compat). This is the minimal surface that closes the "no contract testing at skill boundaries" gap.

### D7. Fail-open is non-negotiable for the hook.
**Decision:** every exception path in `static_turn_clear.py`, `static_nudge.py`, and `static_gate.py` exits 0.
**Rationale:** on a 5+ concurrent-session host, a hook that crashes-and-blocks stalls every session. The Grok default is already fail-open for malformed output/timeouts; the scripts extend this to their own internal errors. Blocking happens **only** on explicit, parsed error findings.

### D8. Turn-scoping via UserPromptSubmit clear, not offset tracking.
**Decision:** a dedicated `static_turn_clear.py` UserPromptSubmit hook truncates `static-<sid>.jsonl` at the start of every turn, making the gate's input per-turn by construction. Chosen over offset tracking (a `static-gate-<sid>.pos` file recording the last-consumed line, mirroring `quality_gate.py`'s transcript `last_line` mechanism).
**Rationale:** the Issue 1 fix (state deleted only on allow, preserved on block for within-turn re-verification) opened a cross-turn regression — after an 8-continuation-cap force-stop (`10-hooks.md:265`), the state file survives into the next turn and the gate re-blocks on prior-turn files (Issue 15). Two fixes were viable: (a) UserPromptSubmit clear, (b) offset tracking. **(a) wins on simplicity and correctness-by-construction:** truncating at turn start means the state file *cannot* contain prior-turn entries, so the gate's "files edited this turn" block message is accurate by construction — no offset bookkeeping, no edge cases around offset-reset-vs-preserve. It also preserves the Issue 1 invariant: UserPromptSubmit fires only on a *new user prompt* (`10-hooks.md:89`), NOT between Stop continuations within a turn, so within-turn state still persists for re-verification. Offset tracking (b) is more faithful to `quality_gate.py` but adds a second state file, a read-modify-write on every Stop, and an offset-reset edge case — complexity with no benefit over the truncate approach. The trace log (`static-gate-<sid>.log`) remains append-only across the whole session for observability; only the gate *input* is per-turn.

---

## 8. PR Plan

Ordered; each PR is independently reviewable and independently useful. Each ships behind the fail-open invariant.

### PR 1 — Workspace static-analysis config (foundation, no behavior change)
**Files:** `P:/ruff.toml` (new), `P:/pyrightconfig.json` (additive edit only).
**Deliverable:** a workspace-wide ruff config (`target-version="py314"`, select E/F/SIM/B/RUF/U) + additive pyright edits (`typeCheckingMode`, `exclude`).
**`extraPaths` handling (Issue 5):** the existing `extraPaths: ["../../packages/handoff"]` is a **dead reference** (verified: `P:/packages/handoff` does not exist). PR 1 does NOT touch it — it is a pre-existing latent bug, and silently changing/removing it is a behavioral edit that needs its own justification (see Open Q7). The additive pyright edit preserves `extraPaths` verbatim.
**Verification:** `ruff check P:/.grok/skills/check/__lib/` and `pyright P:/.grok/skills/check/__lib/` run cleanly or report a baseline; record the baseline count.
**Independently useful:** yes — any agent or editor can now run ruff/pyright with sane config.

### PR 2 — `/static` skill skeleton + ruff+pyright pipeline (Component B, no 3.14 detector yet)
**Files:** `P:/.grok/skills/static/SKILL.md`, `__lib/static_pipeline.py`, `__lib/runners.py`, `__lib/findings_schema.json` (new — see Issue 11).
**Deliverable:** `/static <target>` runs ruff+pyright, emits findings.json + STATIC.md.
**Verification:** `/static` on the `/check` skill package; findings.json validates against `__lib/findings_schema.json`. **Note (Issue 11):** no machine-checkable JSON Schema for `/review`'s finding shape exists in the workspace today (`/review` defines the shape in prose only, SKILL.md lines 476-489). PR 2 authors a minimal `findings_schema.json` (JSON Schema draft 2020-12) capturing the documented fields + the `source` extension; both `/static` and (in PR 5) `/review` validate against it. This closes the "validate against the schema" gap with a real artifact rather than prose-conformance.
**Independently useful:** yes — manual deep static analysis is available immediately.

### PR 3 — `py314_audit` detector (Component C)
**Files:** `P:/.grok/skills/static/__lib/py314_audit.py`, plus tests under `P:/.grok/skills/static/tests/`.
**Deliverable:** the 8-gotcha detector, version-aware, **AST-only** (no grep path — see Issue 10); wired into `/static` (default) and as `--py314` standalone.
**Verification:** unit tests with synthetic files exercising each gotcha; confirm gotcha #5 does NOT fire on 3.14.0; confirm #1/#2/#3/#4/#6 fire on canned inputs AND do NOT fire on comments/docstrings mentioning the symbols (the Issue 10 regression case).
**Independently useful:** yes — `python py314_audit.py <path>` works standalone.

### PR 4 — `static_gate` hook trio (Component A) — the mechanical enforcement
**Files:** `static_turn_clear.py`, `static_nudge.py`, `static_gate.py` (new), `quality-gate.json` (edit, additive), `quality_cleanup.py` (edit — see Issue 12).
**Deliverable:** UserPromptSubmit truncates state at turn start (Issue 15 turn-scoping); PostToolUse records `.py` edits; Stop blocks on ruff E/F + pyright errors, **re-blocking on `stopHookActive==true` when errors persist** (Issue 1 fix), with trace logging (Issue 6) and MAX_FILES surfacing (Issue 7).
**Verification:** (a) edit a file with an undefined name → Stop blocks with the finding table; (b) edit a clean file → Stop passes AND state file deleted; (c) kill ruff.exe path → hook fails open (no block); (d) **introduce an error, let Stop block, then edit to a DIFFERENT error (not a fix) → Stop re-blocks with the new error** (this is the Issue 1 acceptance test — confirms the gate re-evaluates on `stopHookActive==true`, not give up); (e) edit to fix all errors → Stop passes AND `static-<sid>.jsonl` is cleaned up (confirm state is NOT deleted on block, only on allow); (f) confirm `static-gate-<sid>.log` trace entries are written for each decision; (g) touch 45 `.py` files → block/allow message includes the MAX_FILES cap note; (h) **CROSS-TURN SCOPING (Issue 15): edit file A with an error, hit the 8-continuation cap to force-stop the turn (state preserved), then start a new user prompt and edit a CLEAN file C → confirm the new turn's Stop does NOT re-block on A** (confirms `static_turn_clear.py` truncated the prior-turn state; the gate checks only C, which passes). Regenerate active-surface snapshot and confirm all three hooks listed.
**Cleanup wiring (Issue 12):** extend `quality_cleanup.py`'s SessionEnd sweep — verified the script uses **explicit per-session filename patterns** (not a glob) for SessionEnd cleanup (`quality_cleanup.py:104-117`). Add `f"static-{session_id}.jsonl"` and `f"static-gate-{session_id}.log"` to both the `summary_ok` and `summary_failed` pattern lists so the new state files are swept alongside the existing `quality-*` ones. (The SessionStart 24h sweep uses a `quality-*` glob prefix and will NOT catch `static-*` — but that sweep is for cross-session staleness only; per-session SessionEnd cleanup is the correct owner.)
**Independently useful:** yes — but depends on PR 1 config. This is the highest-risk PR; review with `/review --focus security` on the hook scripts.
**Rollback:** delete the three JSON entries; hooks stop firing. No state damage (state JSONL/log are disposable).

### PR 5 — `/check` + `/review` integration (Component D, skill edits)
**Files:** `P:/.grok/skills/check/SKILL.md` (Phase B Step 6 edit), `~/.grok/skills/review/SKILL.md` (new Step 3.6 after Step 3.5), `findings_schema.json` (reuse from PR 2; promote `source` to the Step 4 doc).
**Deliverable:** `/check` requires ruff+pyright on Python scope; `/review` runs a static pre-pass writing to `packets/_static.json` (NOT `specialists/` — Issue 4).
**Verification:** run `/check` after a Python edit that introduces `F821` → verifier FAILs with `severity: bug`. Run `/review --local` on a diff → `packets/_static.json` exists (confirm `specialists/` contains NO parent-authored file), and specialists reference it by path.
**Independently useful:** yes — but composes best after PR 2/3.

### PR 6 — `contract_runner` (Component D, contract harness)
**Files:** `P:/.grok/skills/static/__lib/contract_runner.py`; add `CONTRACTS` lists to the three existing validators (`validate_verdict_consistency.py`, `validate_disconfirmation.py`, `validate_close_receipt.py`).
**Deliverable:** `python contract_runner.py` runs all skill validators against golden contracts; exit 0 only if all pass.
**Verification:** runner passes on current validator behavior; introduce a regression in a validator → runner catches it.
**Independently useful:** yes — closes the contract-testing gap independently of the hook.

### PR 7 — Security arm (`/static --security`: semgrep + bandit)
**Files:** `static_pipeline.py` (add stages 4–5), SKILL.md (document `--security`).
**Deliverable:** optional security scan; research notes +2.74× security vuln rate for AI code.
**Verification:** `/static --security` on a package with a known `eval()` → bandit/semgrep flags it.
**Independently useful:** yes; lowest priority (security is already partially covered by the existing narrow ruff `S` config).

---

## 9. Open Questions

1. **Hook latency budget on large turns.** `static_gate.py` caps at `MAX_FILES=40` and pyright `--outputjson` at 60s timeout. Is 60s acceptable for a Stop hook on this host, or should the gate fall back to ruff-only (skip pyright) when the file count exceeds ~15? *Needs the operator's latency tolerance for turn-end blocking.*

2. **`target-version` reconciliation.** The existing `P:/.claude/hooks/pyproject.toml` sets `py312`. The new `P:/ruff.toml` sets `py314`. Ruff resolves config by nearest-file, so the hooks dir keeps `py312` unless we remove/edit that file. Decision needed: leave the hooks dir on py312 (narrow, test-only), or unify to py314 everywhere? *Recommendation: unify to py314; the `py312` setting is stale (we run 3.14.0).*

3. **Should `static_gate` also block on `py314_audit` `bug`-severity findings (gotchas #3/#4), or only on ruff/pyright?** Blocking on the AST detector is higher-signal for the silent-behavior class but adds AST-parse latency to every Stop. *Recommendation: no — keep the hook to ruff+pyright (fast, unambiguous); surface py314 findings via `/static` and `/check` Phase B where the agent can act with context.*

4. **`contract_runner` CONTRACTS declaration convention.** Validators are currently pure functions. Adding a module-level `CONTRACTS = [...]` list to each is a small API change to files other agents maintain. Acceptable, or should contracts live in a sibling `contracts.yaml` to keep validators untouched? *Recommendation: sibling `contracts.yaml` per skill — keeps the validators as-is and makes contracts reviewable in one place.*

5. **Free-threaded build (gotcha #8).** We run standard `python3.14`. If the operator ever switches to `python3.14t`, the 3–8% single-threaded overhead applies. Should `py314_audit` emit an informational finding whenever it detects it's running under a free-threaded interpreter (`sys._is_gil_enabled()`), or is that out of scope? *Recommendation: yes, one-line informational check — near-zero cost, high signal if the switch ever happens.*

6. ~~**State-file cleanup.**~~ **RESOLVED (Issue 12) — converted to a tasked item in PR 4.** Verified `quality_cleanup.py` SessionEnd uses **explicit per-session filename patterns** (`quality_cleanup.py:104-117`), not a glob; the SessionStart 24h sweep uses a `quality-*` glob prefix that would NOT catch `static-*`. PR 4 adds `f"static-{session_id}.jsonl"` and `f"static-gate-{session_id}.log"` to both pattern lists. `quality_cleanup.py` is confirmed the correct single owner.

7. **Dead `extraPaths` in `P:/pyrightconfig.json` (NEW — surfaced by Issue 5).** The existing `extraPaths: ["../../packages/handoff"]` resolves to `P:/packages/handoff`, which **does not exist** (verified `Test-Path = False`; no `handoff` dir under `packages/`). It is a pre-existing dead reference in both the old and the Issue-5-corrected forms. This design's PR 1 preserves it verbatim (additive-only edit). Should a follow-up PR remove the dead entry? *Needs operator input: was `packages/handoff` moved (e.g. into a worktree or `.github_repos`), renamed, or deleted long ago? Removing it is safe (it resolves to nothing today) but is a behavioral change to a config file other tools may read, so it is out of scope for this design unless confirmed.*

---

## Appendix A — Traceability to research findings

| Research finding | Design component | How addressed |
|---|---|---|
| "No single tool catches everything" (§1) | B pipeline + D integration | Cost-ordered multi-tool pipeline; results composed in `/review`. |
| Detection hierarchy: linter→type→test→review (§1) | A (ruff+pyright per-turn at Stop), D (test via /check, review via /review) | Each layer mapped to an existing mechanism. |
| Python 3.14 gotcha #1 (PEP 649) | C `_check_get_type_hints` | AST: flag `Call` to `typing.get_type_hints`/`get_type_hints`; runtime-test advisory. |
| #2 (locals() PEP 667) | C `_check_locals` | AST: flag `locals()` calls. |
| #3 (int/__trunc__) | C `_check_trunc` | AST: flag `__trunc__` defs. |
| #4 (NotImplemented) | C `_check_notimplemented` | AST: flag in boolean context. |
| #5 (GC reversion) | C, gated to ≥3.14.5 | Version check; informational. |
| #6 (pickle proto 5) | C `_check_pickle` | AST: flag pickle calls. |
| #7 (removed features) | A/B ruff `U` rules + `target-version=py314` | Mechanical via ruff. |
| #8 (free-threaded overhead) | Open Q5 | Informational detector. |
| AI Pattern 1 (plausible-but-wrong) | A (F821 undefined names) + D (/check behavior) | Static catches undefined; /check catches behavior. |
| AI Pattern 2 (refactor breaks callers) | D contract_runner + pyright signatures | Contract tests pin boundaries; pyright catches signature drift. |
| AI Pattern 3 (tests test implementation) | D /check Phase B + /review behavioral verify | Existing behavior; static is additive. |
| AI Pattern 4 (copy-paste drift) | B ruff `SIM`/`B` (bugbear) | Bugbear catches several drift classes. |
| AI Pattern 5 (dependency sprawl) | Open — not statically decidable | Document in AGENTS.md (existing convention layer). |
| "Missing feedback loop is root cause" (§3) | A hook gate | Mechanical verification at turn-end latency — the direct structural fix. |

## Appendix B — What this design deliberately does NOT do

- **No CI/CD.** Solo operator; the hook + skills are the CI equivalent.
- **No new test framework.** Reuses validators; `contract_runner` is a runner, not a framework.
- **No ruff custom rules in Rust.** Friction too high for 8 checks (D4).
- **No changes to `/aar`, `/close`, `/tp`, `/red-team`.** Additive design; those skills benefit indirectly via `/static` and the hook.
- **No blocking on style/warnings.** Errors only (D1) — avoids the noise-trap that makes lint gates get disabled.
- **No auto-fix.** The gate blocks and reports; the agent (or operator) fixes. Auto-fix (`ruff check --fix`) is opt-in via `/static`, never automatic in the hook.
