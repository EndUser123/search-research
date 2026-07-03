# Hook/Plugin Improvement — Phase Prompts for Simpler LLMs (2026-07-02)

Non-blocking phases; run in any order or parallel. Each prompt is self-contained
(cold-start executable). Standard footer is part of every prompt.

**STANDARD FOOTER (append to every phase prompt):**
> Before finishing: run `git -C P:/ status --short` and list every file you
> touched. If any touched file is outside your fence list, revert it and report.
> If you created or modified any hook that prints JSON to stdout: allow = `{}`
> (never `{"decision":"approve"}`), block = `{"decision":"block","reason":...}`.
> Report format: (1) files changed, (2) verification command outputs verbatim,
> (3) anything you could not complete — never claim done on partial work.

---

## Phase 1 — RETIRED (premise refuted)

The double-fire hypothesis was refuted by the official hooks reference:
"identical handlers are deduplicated automatically. Command hooks are
deduplicated by command string and `args`." Dual-scope registrations with
identical command strings fire once. Remaining (Low impact, director-optional):
remove the redundant duplicate lines from ONE scope for readability only.

---

## Phase 2 — Test quarantine sweep (deepseek / glm-4.7)

In P:/.claude/hooks: run `python -m pytest tests/ -q --tb=no` ONCE and save the
full output to a file; this single run defines "failing" (do not re-run to
re-classify). Group FAILED lines by test file. Exemptions — leave in place any
file whose name contains `existence_guard`, `empty_snapshot`, `observe_before_act`,
`arch_first_enforcer`, or `implementation_default_gate` (human triage pending).
For every OTHER file with >=1 failure: move the whole file to
tests/_quarantine/ (create it), preserving filename. IMPORTANT: moving a file
quarantines its passing tests too — that is accepted, but you MUST record it:
create tests/_quarantine/QUARANTINE.md with one row per moved file:
| file | failed | passed | first assertion error (one line) |
Then exclude _quarantine from collection by mirroring how `_legacy` is excluded —
read pytest.ini (`norecursedirs`), conftest.py, and tests/conftest.py
(`collect_ignore`) FIRST and copy that exact mechanism; do not invent a new one.
Verification contract (all three must hold, paste outputs):
1. `python -m pytest tests/ -q --tb=no` → 0 failed outside the exempted files.
2. `python -m pytest tests/_quarantine/ --collect-only -q` → still collects.
3. `git -C P:/ status --short` shows ONLY renames/adds under .claude/hooks/tests/.
Fences: do NOT delete any test, do NOT edit any test's content (config files
pytest.ini/conftest.py are the only permitted edits), do NOT touch anything
outside P:/.claude/hooks/tests/ + pytest.ini + conftest.py.
[STANDARD FOOTER]

## Phase 3 — Dispatch manifest generator (glm-4.7)

Create P:/.claude/hooks/scripts/gen_dispatch_manifest.py (stdlib only, type
hints). Inputs it must read:
(a) hooks sections of P:/.claude/settings.json AND
    C:/Users/brsth/.claude/settings.json;
(b) every P:/packages/.claude-marketplace/plugins/*/__lib/router.py — use
    ast.parse to extract module-level list assignments whose name ends with
    `_HOOKS` and the `_DISPATCH` dict keys; if ast fails on a file, record it
    in the manifest under "parse_errors" instead of crashing;
(c) P:/.claude/hooks/SessionStart.py: the module-level list of hook filename
    strings near the top (read the file first to find the exact variable);
    P:/.claude/hooks/PreToolUse.py: entries in the UNIVERSAL and TOOL_HOOKS
    structures (again: read first, then extract with ast where possible).
Output P:/.claude/hooks/dispatch_manifest.json:
{ "generated_at": iso8601, "inputs_hash": sha256 over the sorted bytes of all
  input files, "parse_errors": [...], "events": { "<Event>": [ {"target":
  "<command-or-filename>", "scope": "project|user|router:<plugin>|inprocess"} ] } }
CLI: `--is-live <filename>` prints every dispatch chain entry matching that
filename, or "NOT-LIVE". `--is-live` MUST first recompute inputs_hash and print
"STALE MANIFEST — regenerate" if it differs (manifest may never be hand-edited).
Tests: P:/.claude/hooks/tests/test_gen_dispatch_manifest.py with tmp_path
synthetic settings/router fixtures (no dependence on the real environment).
Acceptance on the real environment: the skill-guard router must appear under
both project and user scope for PreToolUse (known ground truth), and
`--is-live Stop.py` must show the project-settings hook_runner entry.
Fences: net-new files only (script + test); read-only on everything else.
[STANDARD FOOTER]

## Phase 4 — Frozen Stop-payload schema + pilot migration (glm-4.7)

Create P:/.claude/hooks/__lib/stop_payload_schema.py. Module docstring MUST
state: "Field set verified against live Stop payload 2026-07-02 on Claude Code
2.1.199. On CC upgrade, re-verify against the hooks reference (code.claude.com/
docs/en/hooks) before trusting." Contents:
- STOP_PAYLOAD_KEYS = frozenset({"session_id","transcript_path",
  "hook_event_name","stop_hook_active","last_assistant_message","cwd","effort",
  "permission_mode","background_tasks","session_crons","terminal_id",
  "output_text","response"})
- def make_stop_payload(transcript_path: str, **overrides) -> dict — returns
  only real keys with sane defaults; raises ValueError listing any override key
  not in STOP_PAYLOAD_KEYS.
- def make_transcript_line(role: str, text: str, is_meta: bool = False) -> dict
  producing the real nested shape: {"type": role, "message": {"role": role,
  "content": [{"type": "text", "text": text}]}} plus "isMeta": True when set.
- def make_tool_result_line(content: str, tool_use_id: str = "t1") -> dict:
  {"type": "user", "message": {"role": "user", "content": [{"type":
  "tool_result", "tool_use_id": tool_use_id, "content": content}]}}.
Defaults for make_stop_payload: session_id="test-session",
hook_event_name="Stop", stop_hook_active=False, last_assistant_message="",
cwd="P:/", terminal_id="test", output_text="", response="",
permission_mode="default", effort={"level": "high"}, background_tasks=[],
session_crons=[]. ValueError message must list the offending keys.
Pilot migration: rewrite ONLY P:/.claude/hooks/tests/
test_stop_user_prompt_enrichment.py to build its payloads/transcript lines via
these factories. Behavior must not change: all 9 tests pass before AND after
(run both, paste outputs). Also required: `python -m py_compile` on the new
module, and one unit test asserting make_stop_payload(tp, bogus_key=1) raises
ValueError naming "bogus_key". Fences: exactly two files (new module + that
test) plus one new test file test_stop_payload_schema.py if you prefer separate
tests. [STANDARD FOOTER]

## Phase 5 — /why-blocked turn RCA script (glm-4.7)

Read first: P:/.claude/hooks/scripts/why_blocked.py (existing reader — note the
scripts/ subdir) and P:/.claude/hooks/CLAUDE.md "Observability Storage Policy"
section. Sources to join (inspect each schema before writing code):
1. P:/.claude/hooks/logs/diagnostics/stop_blocks.jsonl — fields: timestamp,
   event, gate_name, reason, matched_span, response_hash, session_id,
   terminal_id, transcript_path.
2. diagnostics.db — query the `hooks` table (primary hook-event log) AND
   `importer_diagnostics` (importer failures); read each table's columns via
   PRAGMA table_info first and map what exists; not every row has a
   decision/reason — print "-" for absent fields, never invent them.
3. P:/.claude/hooks/logs/diagnostics/hook_runner_stderr.jsonl — stderr capture;
   has no decision field; report its `error_text`-like payload as the reason
   column.
Open the DB read-only with EXACTLY this form (verified working on this
machine): sqlite3.connect("file:P:/.claude/hooks/logs/diagnostics/"
"diagnostics.db?mode=ro", uri=True).
"--last N" means: take the N most recently modified *.jsonl files in
C:/Users/brsth/.claude/projects/P--/ and use their filename stems as
session_ids. Normalize all timestamps to UTC-aware datetimes before sorting
(some sources are naive — assume naive = UTC). Unavailable/locked sources
appear as one in-report row "SOURCE UNAVAILABLE: <name>: <error>" (stdout, not
stderr; exit 0). Stdlib only. Tests: synthetic jsonl + sqlite fixtures in
tmp_path, including one mixed naive/aware timestamp ordering test; do not read
real logs in tests. Required: `python -m py_compile` on the script.
Acceptance on real data: `--last 1` prints at least one stop_blocks.jsonl row
from 2026-07-02 (several exist). Fences: net-new files only; read-only on logs
and DB. [STANDARD FOOTER]

## Phase 6 — Hook latency profile (agy flash)

Read the PreToolUse hook command lists in P:/.claude/settings.json and
C:/Users/brsth/.claude/settings.json. Deduplicate identical command strings
(Claude Code dedupes them too). For each unique command, run it 3 times via
Python: subprocess.run(shlex.split(cmd, posix=False), input=PAYLOAD,
capture_output=True, text=True, timeout=30) — stdin is always provided and
closed by subprocess.run's input=, so hooks cannot hang on stdin; the timeout
catches everything else. PAYLOAD = '{"session_id":"perf","hook_event_name":
"PreToolUse","tool_name":"Read","tool_input":{"file_path":"x"}}'. Measure
wall-clock ms with time.perf_counter around each run. Record exit codes:
non-zero or timeout rows are marked FAILED and EXCLUDED from medians but shown
in the report. Definitions: per-command latency = median of its 3 runs;
event-total = SUM of per-command medians (models sequential worst case; note
that CC runs hooks in parallel, so also report max(per-command median) as the
parallel estimate). Report format: one markdown table (command, median ms,
exits), then top-3 slowest as table rows, then this caveat verbatim: "Measures
process spawn + import + hook body for a trivial payload; in-conversation
latency may differ." Write to P:/.claude/.artifacts/hook_latency_profile.md and
verify by reading the file back and confirming the caveat string is present.
Fences: read-only; the only file you may write is the report.
[STANDARD FOOTER]

## Phase 7 — RESERVED for frontier model (not simple-LLM safe)

- Semantic-critic discrimination audit (TP/FP on real corpus) → async
  additionalContext or retirement. Depends on nothing above.
- Quality-gate demotion to advisory (Stop.py edits, GATE_CLASSES enforcement).
- PreToolUse dispatcher consolidation (the architectural end-state: one process
  per event instead of ~11) — gated on Phase 6 numbers.
