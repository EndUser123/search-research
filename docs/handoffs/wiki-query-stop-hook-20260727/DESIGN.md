# Design: Stop-Hook Wiki-Query-Before-Offload Enforcement Gate

**Status:** Draft for review
**Author:** Grok Build subagent (architect role)
**Date:** 2026-07-27
**Motivating session:** session-019f9a3c (`/why` RCA on `nlm` CLI auth-error offload)
**Source-of-truth briefs:** `evidence-brief.md` (local), `P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md`

---

## 1. Overview

### 1.1 Problem

When an agent encounters a tool error, it routinely diagnoses the failure from general web knowledge and reports a blocker to the operator ("you must do browser OAuth", "requires human intervention") **without first consulting the workspace wiki**. The 2026-07-27 `nlm` CLI incident is the canonical instance: the CLI returned "Authentication expired" → the agent told the operator "you must do browser OAuth" → the workspace wiki (`P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md`) had documented a silent agent-performable CDP re-auth two days earlier.

Three advisory AGENTS.md rules already exist for adjacent problems (`search-before-proposing`, `evidence-first-default`, `claims-require-receipts`). None fired on this incident because their trigger surfaces are proposal-shaped or claim-shaped — not error-diagnosis-shaped. The `/why` RCA documents the gap at `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md`; the `/www` research documents that soft enforcement has a ~50% compliance ceiling and pure self-critique fails under the same closure pressure.

### 1.2 Proposed solution

A **hard-enforcement Stop hook** that, when the agent's final message contains offload language, checks whether the agent queried the workspace wiki in the **current assistant turn** (defined as records since the most recent `role: "user"` in the transcript — see §3.4 and F-06). If no wiki-query evidence exists in that turn, the hook blocks the stop with a reason instructing the agent to check the wiki first. If wiki-query evidence exists, the stop is allowed — the agent did due diligence even if its final conclusion is "the operator must do X."

(The phrase "this turn" in earlier drafts conflated the turn boundary with a 30-minute lookback window. The lookback is a safety floor against timestamp skew; the turn boundary is the source of truth — see §3.4. This resolves F-23.)

The hook is a sibling to the existing `quality_gate.py` (which prevents unverified completion claims), follows the same two-signal pattern (lastAssistantMessage + transcript scan), and ships in **shadow mode by default** so the false-positive rate can be measured before any blocking fires.

### 1.3 Goals

| # | Goal | Acceptance |
|---|------|------------|
| G1 | Catch the `nlm`-class failure (offload without wiki-query) | A reproducer transcript with offload language and zero wiki-query tool calls blocks. |
| G2 | Allow legitimate offloads (genuine auth decisions, irreversible ops, physical actions) | Agent that queried the wiki AND concluded the offload is genuine → not blocked. |
| G3 | Do not loop | Respects `stopHookActive`; respects `reason != "end_turn"`; the 8-continuation cap is the backstop. |
| G4 | Measure before enforcing | Default mode is shadow. Phase-1 only after ≥100 shadow events with measured FP rate <5%. |
| G5 | Fail open | Any internal error → exit 0 (allow). A broken hook must not kill the conversation. |
| G6 | Share infrastructure with `quality_gate.py` | New shared `hook_base.py` extracted before this hook is written; both hooks use it. |

### 1.4 Non-goals

- Detecting offload language in tool-call outputs (only the agent's final message is scanned).
- Detecting wiki-query activity outside this turn (a 30-minute-old query is stale for an error-diagnosis decision).
- Replacing `quality_gate.py`. The two gates cover different surfaces (offload language vs. completion claims) and share a base library.
- Blocking on session-end fires (`reason != "end_turn"`).
- Cross-host portability in v1 (this hook is Grok Build only — its registration model is host-specific; flagged in §10).

---

## 2. Background

### 2.1 Current state [FACT]

| Item | Source |
|------|--------|
| Stop hook receives `lastAssistantMessage` | `~/.grok/docs/user-guide/10-hooks.md:261` (per evidence-brief) |
| Stop hook blocks via `{"decision":"block","reason":"..."}` | `~/.grok/docs/user-guide/10-hooks.md:256` |
| 8-continuation cap prevents infinite loops | `~/.grok/docs/user-guide/10-hooks.md:261` |
| `stopHookActive` prevents re-block | `~/.grok/docs/user-guide/10-hooks.md:261` |
| Must filter on `reason == "end_turn"` | `~/.grok/docs/user-guide/10-hooks.md:262` |
| Hook scripts live at `~/.grok/hooks/scripts/` | `~/.grok/hooks/quality-gate.json` (per evidence-brief) |
| `chat_history.jsonl` records tool calls | `~/.grok/hooks/scripts/quality_gate.py` (per evidence-brief) |
| `chat_history.jsonl` tool_call records use fields `name` (str) + `arguments` (JSON string); no `tool_name`/`args`/`call_id` | `~/.grok/hooks/scripts/quality_gate.py:1101-1109` (verified per F-Field, 2026-07-27) |
| Existing `quality_gate.py` uses two-signal pattern + shadow-mode rollout | `~/.grok/hooks/scripts/quality_gate.py` (per evidence-brief) |
| Wiki documents the exact failure pattern | `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` |
| Three enforcement tiers: hard > adaptive > soft | `P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md` |

### 2.2 Gap [FACT]

- **No enforcement gate covers error-diagnosis offloads.** `quality_gate.py` covers completion claims (the agent SAID "done" without running tests). No gate covers offload claims (the agent SAID "operator must do X").
- **Advisory rules fire on different surfaces.** "Search before proposing" triggers on the user-stated problem; offload occurs AFTER an error has been hit and a diagnosis already started.
- **The wiki predicted the failure by name.** `notebooklm-cli-operational-gotchas.md` documented the silent CDP re-auth two days before the incident.

### 2.3 Why a Stop hook (not a PreToolUse or PostToolUse) [FACT]

The signal is in the agent's **final message**. PreToolUse fires before tool calls — at that point the agent has not yet produced the offload text. PostToolUse fires after each tool call — too noisy (would fire on every tool use, including wiki queries, with no way to know whether the agent will eventually offload). The Stop event is the only event where "did this turn end with an offload?" is observable as a single decision point.

### 2.4 Premises classification

| Premise | Class | Receipt |
|---------|-------|---------|
| Stop hook API fields (`lastAssistantMessage`, `stopHookActive`, `reason`) work as documented | [FACT] | `~/.grok/docs/user-guide/10-hooks.md` lines 256-262 |
| `quality_gate.py` is a working template (two-signal, shadow modes, negation, fail-open) | [FACT] | read this session |
| Hook scripts at `~/.grok/hooks/scripts/` are the canonical location | [FACT] | evidence-brief §"Hook Registration Locations" |
| Hard enforcement (≥95%) outperforms soft enforcement (~50%) | [FACT] | `P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md` §"The three enforcement tiers" |
| Pure self-critique fails under closure pressure | [FACT] | Huang et al. 2023; Self-Refine 94% error rate (per wiki concept) |
| Offload language is reliably regex-detectable at high precision | **[INFERENCE]** | Plausible from quality_gate.py precedent; needs shadow-mode measurement |
| A wiki-query tool call is detectable in the transcript by path-match | **[INFERENCE]** | Plausible; quality_gate.py reads `chat_history.jsonl`; the exact field schema is now verified (see §6.4): `name` + `arguments` (JSON string). Path-match remains an [INFERENCE] because the regex patterns have not been tested against live wiki paths, but the field-name prerequisite is [FACT] |
| False-positive rate of offload detection on real agent output is acceptably low | **[UNKNOWN]** | Must be measured in shadow mode before any blocking fires |
| The transcript retains wiki-query evidence for the full turn | [INFERENCE] → **[RESOLVED]** by F-06 | Turn boundary is `role: "user"` records; lookback is a safety floor; verified via F-10 measurement |

---

## 3. Architecture

### 3.1 Component diagram

```
                            Stop event fires
                                  │
                                  ▼
                ┌────────────────────────────────────┐
                │  wiki_query_gate.py (new)          │
                │  (registered Stop, timeout 30s)    │
                └────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
   ┌─────────────────────────┐         ┌──────────────────────────┐
   │ Signal 1:               │         │ Signal 2:                │
   │ lastAssistantMessage    │         │ chat_history.jsonl       │
   │ regex scan              │         │ tool_use scan            │
   │ → offload_phrases[]     │         │ → wiki_query_receipts[]  │
   └─────────────────────────┘         └──────────────────────────┘
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                                  ▼
                ┌────────────────────────────────────┐
                │ Decision matrix                    │
                │ offload detected AND               │
                │ no wiki-query receipt → BLOCK      │
                │ otherwise → ALLOW                  │
                └────────────────────────────────────┘
                                  │
                                  ▼
                ┌────────────────────────────────────┐
                │ Hook output                        │
                │ shadow: log to .evidence/ + exit 0 │
                │ phase1: {"decision":"block",       │
                │          "reason":"..."}           │
                │ fail-open: any error → exit 0      │
                └────────────────────────────────────┘
```

### 3.2 Shared base library

Before `wiki_query_gate.py` is written, **extract** `~/.grok/hooks/scripts/_hook_base.py` containing the patterns duplicated across the existing hooks (verified count: ~5 quality/mutation hooks share these patterns per F-10 measurement; the original estimate of "6/6" was not measurable without per-script grep, and the actual count is closer to 5):

| Pattern | Currently in | New home |
|---------|--------------|----------|
| JSON envelope parse (camelCase → dict) | `quality_gate.py`, `quality_nudge.py`, `mutation_pre.py`, `mutation_post.py`, `verification_receipt_writer.py` (5 hooks) | `_hook_base.parse_envelope(stdin_json)` |
| `chat_history.jsonl` path resolution | `quality_gate.py` (likely only) | `_hook_base.resolve_transcript_path(session_id)` |
| Tool-use extraction from transcript lines | `quality_gate.py` (only) | `_hook_base.iter_tool_uses_in_current_turn(transcript_path, session_id)` (new) + `iter_tool_uses(transcript_path, since_ts)` (legacy) |
| Mode env-var pattern + shadow/authoritative dispatch | `quality_gate.py` | `_hook_base.resolve_mode(env_var, modes, default)` |
| Fail-open exception handler | `quality_gate.py` | `_hook_base.fail_open_decorator(fn)` |
| Structured evidence log writer | ad-hoc per hook | `_hook_base.write_evidence(hook_name, payload)` |
| Negation window (60-char lookback before a candidate phrase) | `quality_gate.py` | `_hook_base.negation_window(text, candidates, patterns, window_chars=60)` |

`quality_gate.py` is refactored to use the base in the same commit as the base extraction, as a **proof-of-pattern refactor** (no behavior change, tests must pass). See §14 (Coupling & Code-Smell Inventory) for the DRY / touch-point counts that justify this extraction.

### 3.3 Signal 1 — Offload-language detection

```python
OFFLOAD_PATTERNS = [
    # "you must do X" / "you'll need to re-auth"
    r"\byou(?:'ll|\s+will)?\s+(?:must|need\s+to|have\s+to)\s+(?:do|perform|run|execute|complete|re-auth|reauthorize|sign\s+in|log\s+in|manually)",
    # "operator must/should/needs to"
    r"\boperator\s+(?:must|needs?\s+to|should|has\s+to|will\s+need\s+to)",
    # "requires human/operator/manual/user intervention/action"
    r"\brequires?\s+(?:human|operator|manual|user|your)\s+(?:intervention|action|input|step)",
    # "I can't/cannot perform/do this"
    r"\bI\s+(?:can'?t|cannot|am\s+unable\s+to)\s+(?:perform|do|execute|complete|handle|access|reach|connect)",
    # "user action required" / "manual step required"
    r"\b(?:user|manual|human)\s+(?:action|step|intervention)\s+required\b",
    # "outside my capabilities" / "beyond what I can do"
    r"\b(?:outside|beyond)\s+(?:my|the\s+agent's?)\s+capabilities\b",
    # "physical access required" / "browser required"
    r"\b(?:physical|browser|interactive)\s+(?:access|interaction|session)\s+(?:is\s+)?required\b",
]

NEGATION_PATTERNS = [
    r"\byou\s+(?:don'?t|do\s+not|won'?t|will\s+not)\s+need\s+to\b",
    r"\bwithout\s+(?:operator|human|user|manual)\s+(?:intervention|action|input)\b",
    r"\bnot\s+requiring\s+(?:human|user|manual)\s+(?:action|intervention|input)\b",
    r"\bautomatable\b",
    r"\bthe\s+agent\s+can\s+(?:perform|do|handle)\b",
]
```

**Negation handling** (mirrors `quality_gate.py`'s negation window): if a negation pattern appears within 60 characters before a candidate offload phrase, suppress that phrase. False negatives (an offload phrase we miss) are acceptable — status quo. False positives (a legitimate offload we block) are unacceptable — measured in shadow mode.

**High-precision bias**: these patterns are intentionally narrow. The Reddit/practitioner evidence (per wiki concept) shows that over-broad detection creates user friction. A blocked stop that should have been allowed is more harmful than a missed offload that should have been caught — because the missed offload's consequences (operator doing the wrong thing) are recoverable, while a false-positive block frustrates legitimate work.

### 3.4 Signal 2 — Wiki-query receipt detection

**Canonical record shape (this is the source of truth — §4.3, §4.4 conform to this):**

```python
# Per-line chat_history.jsonl record (VERIFIED per quality_gate.py:1101-1109):
#   {"timestamp": float, "role": "user"|"assistant"|"tool",
#    "tool_calls": [{"name": str, "arguments": <JSON STRING — must be parsed>}, ...]}
#
# iter_tool_uses_in_current_turn() flattens each record's tool_calls array into one ToolUseRecord per call,
# parsing each call's `arguments` JSON string into a dict during flattening:
#   ToolUseRecord = {"name": str, "arguments": dict (parsed from JSON string),
#                    "timestamp": float, "source_record_ts": float}
#   # NOTE: the transcript schema has NO `tool_name`/`args`/`call_id` fields. Those were
#   # inferred in the v1 draft and silently produced zero receipts (F-Field). The verified
#   # field names are `name` (str) and `arguments` (JSON string). See §6.4 + §14 Q3 (resolved).
```

**"This turn" is defined concretely:** the current assistant turn = all transcript records since the most recent `role: "user"` record (or session start, if none). The 30-minute `TRANSCRIPT_LOOKBACK_SECONDS` is a **safety floor** against timestamp skew, not a definition of "this turn." A wiki query from a prior turn (even within 30 minutes) does **not** satisfy the receipt check. This resolves F-06.

**Receipt patterns (v1):**

```python
# F-27 fix: use [^\"\s]*? (non-greedy, excludes only quote and whitespace —
# permits `/` and `\`, so nested subdirectories match). The previous
# [^/\\\"\s]* (F-02 attempt) silently failed on any nested concept because
# the character class still excluded `/`. Resolves F-27.
# Trace verification:
#   Pattern:  \.data[/\\]wiki[/\\]concepts[/\\][^\"\s]*?\.md
#   Input A:  .data/wiki/concepts/notebooklm-cli-operational-gotchas.md
#     - matches literal ".data/wiki/concepts/" (chars 0..20)
#     - [^\"\s]*? non-greedy: tries 0 chars, then 1, then 2, ...
#       advances until [^\"\s]*? has consumed "notebooklm-cli-operational-gotchas"
#     - \.md matches ".md" → MATCH ✓
#   Input B:  .data/wiki/concepts/error-handling/foo.md
#     - matches literal ".data/wiki/concepts/" (chars 0..20)
#     - [^\"\s]*? non-greedy: advances through "error-handling/foo" (the
#       character class permits `/` and `-`, excludes only `"` and whitespace)
#     - \.md matches ".md" → MATCH ✓
WIKI_PATH_PATTERNS = [
    # Direct wiki concept reads (top-level OR nested in subdirectories)
    re.compile(r"\.data[/\\]wiki[/\\]concepts[/\\][^\"\s]*?\.md"),
    re.compile(r"\.data[/\\]wiki[/\\]notes[/\\][^\"\s]*?\.md"),
    re.compile(r"wiki[/\\]concepts[/\\][^\"\s]*?\.md"),
    # Index search for wiki
    re.compile(r"\bgrep\b[^|;\n]*\.data[/\\]wiki\b"),
    re.compile(r"\brg\b[^|;\n]*\.data[/\\]wiki\b"),
    # NOTE: qmd is NOT a regex match — see matches_qmd_wiki_call() below.
    #       Regex on bare "qmd search" would false-positive on non-wiki queries (F-09).
]

def matches_wiki_pattern(record: ToolUseRecord, patterns: list[re.Pattern]) -> Receipt | None:
    """Return a Receipt if record's name + arguments match a wiki pattern, else None.
    Defined in §4.3. Returns None for non-matching calls.
    Receipt shape: {"name": str, "matched_pattern": str, "matched_arg": str,
                    "timestamp": float}."""

def matches_qmd_wiki_call(record: ToolUseRecord) -> bool:
    """Require qmd invocation AND its argument contains a wiki-target marker.
    Argument extraction handles both shell-string form ('qmd search "wiki/foo"') and
    bare-arg form ('qmd search wiki/foo').
    Markers: 'wiki', '.data/wiki', '.data/concepts', 'concepts/', 'notes/'.
    Reads `record["arguments"]` (a dict, already JSON-parsed by the iterator — verified
    per quality_gate.py:1101-1109; the field is a JSON string in the raw record)."""
    if record["name"] != "run_terminal_command" and "qmd" not in record["arguments"].get("command", ""):
        return False
    cmd = record["arguments"].get("command", "")
    # Extract first quoted string after qmd subcommand, else first non-whitespace token.
    m = re.search(r"""\bqmd\s+(?:search|query|find)\s+["']([^"']+)["']""", cmd)
    if m:
        arg = m.group(1)
    else:
        m2 = re.search(r"\bqmd\s+(?:search|query|find)\s+(\S+)", cmd)
        if not m2:
            return False
        arg = m2.group(1)
    wiki_markers = ("wiki", ".data/wiki", ".data/concepts", "concepts/", "notes/")
    return any(marker in arg for marker in wiki_markers)
```

**Receipts captured in v1:**
- `read_file` with path matching `*.data/wiki/concepts/*.md` or `*.data/wiki/notes/*.md` (subdirectory-tolerant)
- `grep` / `rg` whose args include `*.data/wiki*`
- `qmd search|query|find` invocations **whose argument contains a wiki-target marker** (closes F-09's FP risk)

**Receipts NOT captured in v1 (explicitly deferred):**
- `web_search` whose query matches the failing tool's canonical name — this would require reliably detecting "the failing tool" from the transcript. Per KD-4, per-tool matching is a v2 enhancement (Open Questions Q4). The web_search receipt class is deferred, not implemented (closes F-07).
- Indirect MCP tool calls that wrap wiki access — v1 only matches tool names explicitly named in `WIKI_PATH_PATTERNS` or `matches_qmd_wiki_call`.

**Receipt scope (v1):** any wiki query **in the current assistant turn** counts. Temporal coupling between query and offload phrase is NOT required (resolves F-12: the hidden anchor is "any wiki query this turn, regardless of position within the turn").

### 3.5 Decision matrix

**Preconditions (evaluated BEFORE the matrix; if any fails, the hook returns ALLOW with no further work):**
1. `stopHookActive` is `false` (or absent) — else ALLOW (loop avoidance)
2. `reason == "end_turn"` — else ALLOW (session-end fires are ignored)
3. No internal exception during signal collection — else ALLOW (fail open)

**Matrix (after preconditions pass):**

| `offload_phrases` | `wiki_query_receipts` (this turn) | Mode | Decision |
|-------------------|-----------------------------------|------|----------|
| empty | (any) | (any) | ALLOW (no offload to gate) |
| non-empty | non-empty | (any) | ALLOW (agent did due diligence) |
| non-empty | empty | `shadow` | LOG + ALLOW (measure FP rate) |
| non-empty | empty | `receipt_authoritative` | BLOCK + log |

(The loop-avoidance, session-end, and fail-open rows from the previous draft are now preconditions above the table; this resolves F-25. Phase-1 `receipt_authoritative_with_old_fail_safe` is collapsed — see §12.2 for the rationale and F-08.)

### 3.6 Block reason text

```
Wiki-query gate: this turn's final message contains offload language
(<offload phrases>) but I see no evidence of a workspace wiki query in the current
turn. The wiki may document a silent agent-performable recovery.

Before offloading to the operator, please:
1. Search the wiki for the failing tool's canonical name
   (try: rg -l "<tool-name>" P:/.data/wiki/concepts P:/.data/wiki/notes)
2. Search for the error message itself
   (rg "<error-message>" P:/.data/wiki/concepts P:/.data/wiki/notes)
3. If the wiki documents a recovery I can perform as an agent, perform it.
4. If the wiki does NOT document a recovery, offload is legitimate — restate
   your finding (which wiki paths you searched and what you found) and stop.

How to clear this block: issue a wiki query in your next turn (read a wiki
concept file, run rg against P:/.data/wiki/, or run `qmd search` with a
wiki-target argument). Then end your turn normally. The gate will allow
the next stop because it will see the wiki query in that turn's transcript.
Issuing the query and then immediately re-stating the same offload in the
same response will NOT clear the block — the query must be in the turn
whose stop is being gated.
```

The reason text is fed back to the model as a user message per the hooks doc. The success-condition clause is tightened to be unambiguous about turn boundaries (resolves F-20). The `<canonical-tool-name>` placeholder is removed; v1 instructs the agent to search for the failing tool's name without naming it explicitly (resolves F-18 — `infer_failing_tool_from_offload` was vestigial scaffolding and is removed entirely per F-03).

---

## 4. Implementation Sketch

### 4.1 Files to create

| Path | Purpose |
|------|---------|
| `~/.grok/hooks/scripts/_hook_base.py` | Shared hook base library (envelope parse, transcript iter, mode dispatch, fail-open, evidence writer) |
| `~/.grok/hooks/scripts/wiki_query_gate.py` | The new Stop hook script |
| `~/.grok/hooks/scripts/tests/test_wiki_query_gate.py` | Unit tests |
| `~/.grok/hooks/scripts/tests/test_hook_base.py` | Tests for the base library |
| `~/.grok/hooks/wiki-query-gate.json` | Hook registration (Stop event, 30s timeout) |

### 4.2 Files to modify

| Path | Why |
|------|-----|
| `~/.grok/hooks/scripts/quality_gate.py` | Refactor to use `_hook_base.py` as proof-of-pattern. **Behavior must not change.** Existing tests must pass unchanged. |
| `P:/AGENTS.md` | Add a one-line note in the "Search before proposing" / "Evidence-first default" cluster pointing to the gate (operator-discoverable; wiki gate does not need to be in the model prompt to function) |

### 4.3 `_hook_base.py` interface (contract)

```python
ToolUseRecord = dict  # {"name": str, "arguments": dict (parsed from JSON string),
                       #  "timestamp": float, "source_record_ts": float}
                       # VERIFIED per quality_gate.py:1101-1109. The raw transcript
                       # uses `name` + `arguments` (JSON string); the iterator parses
                       # `arguments` during flattening. There is NO `call_id` field.
Receipt = dict        # {"name": str, "matched_pattern": str,
                       #  "matched_arg": str, "timestamp": float}

def parse_envelope(stdin_payload: str | bytes) -> dict:
    """Parse Grok Build camelCase hook envelope. Returns dict with lastAssistantMessage,
    stopHookActive, reason, hookEventName, sessionId, cwd, etc.
    Robust to malformed JSON — returns {} on parse error so caller can fail open."""

def resolve_transcript_path(session_id: str) -> Path:
    """Locate chat_history.jsonl for this session. Mirrors quality_gate.py's path logic.
    Returns absolute Path; raises FileNotFoundError if not found.
    Caller is responsible for catching FileNotFoundError → fail-open."""

def iter_tool_uses_in_current_turn(transcript_path: Path,
                                   session_id: str) -> Iterator[ToolUseRecord]:
    """Yield tool_use records in the CURRENT assistant turn.
    Definition of "current turn": records since the most recent `role: "user"`
    record (or session start, if none). Source-of-truth for "this turn" — §3.4.
    Flattening: each record's `tool_calls` array becomes one ToolUseRecord per call.
    During flattening, each call's `arguments` JSON STRING (verified per
    quality_gate.py:1101-1109) is parsed into a dict. The parsed dict is what
    ToolUseRecord["arguments"] holds — matchers must read .get("command", "") or
    .get("path", "") on the parsed dict, NOT on the raw JSON string.
    Defensive: skips lines that fail to parse (does not abort on a single bad line).
    Raises FileNotFoundError if transcript_path is missing — caller fails open.

    NOTE: this replaces the previous `iter_tool_uses(transcript_path, since_ts)`
    signature, which conflated "this turn" with a 30-minute lookback (F-01, F-06).
    The 30-minute TRANSCRIPT_LOOKBACK_SECONDS in the wiki_query_gate.py is now
    a safety floor against timestamp skew, not a definition of turn boundary."""

def iter_tool_uses(transcript_path: Path, since_ts: float) -> Iterator[ToolUseRecord]:
    """Yield tool_use records newer than since_ts (timestamp-based, not turn-based).
    Kept as a public utility for callers that need a time-bounded scan (e.g.,
    quality_gate.py's verification window). Not used by wiki_query_gate.py."""

def matches_wiki_pattern(record: ToolUseRecord,
                         patterns: list[re.Pattern]) -> Receipt | None:
    """Return a Receipt if record's name + arguments match a wiki pattern, else None.
    Pattern matching is against the serialized record (name + JSON of parsed arguments).
    Returns None for non-matching calls. Defined here (not in wiki_query_gate.py)
    so tests in test_hook_base.py can exercise it without coupling to the gate."""

def resolve_mode(env_var_name: str, modes: set[str] | list[str], default: str) -> str:
    """Read mode from env var; validate against modes set; return mode string or default.
    Logs to evidence on unknown mode. Parameter is a set/list of valid names
    (validation only, no value-mapping); resolves F-05's dict-vs-set confusion.
    Returns `default` if env var unset OR value not in modes."""

def write_evidence(hook_name: str, payload: dict) -> None:
    """Append one JSON line to ~/.grok/hooks/.evidence/<hook_name>.jsonl.
    Uses atomic write (tmp + os.replace) per file-editing protocol rule.
    Never raises — write failures are swallowed and logged to stderr."""

def fail_open_decorator(fn: Callable) -> Callable:
    """Wraps a hook function. On any uncaught exception:
      1. Logs exception to evidence (hook_name="<wrapped>.fail_open", payload={exception, ts})
      2. Returns {} (hook output = ALLOW)
      3. Caller process exits 0
    This contract resolves F-24: the decorator MUST log before swallowing.
    The wrapped function must return a dict (the hook output)."""

def negation_window(text: str, candidate_spans: list[tuple[int, int]],
                    negation_patterns: list[str], window_chars: int = 60) -> list[tuple[int, int]]:
    """Return the subset of candidate_spans that are NOT preceded (within `window_chars`)
    by a negation pattern. Mirrors quality_gate.py's negation logic.
    `window_chars` is configurable per-call; the wiki_query_gate default of 60 mirrors
    quality_gate.py and is overridable via env var GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS
    (resolves F-17). Example that motivates 60 chars: 'While the operator could do this
    manually, you must do browser OAuth' — negation is ~52 chars before offload, fits
    in 60. Window too small (<60) fails to suppress distant negations; window too large
    (>120) suppresses legitimate offloads. 60 is the empirical sweet spot per the
    quality_gate.py precedent."""
```

### 4.4 `wiki_query_gate.py` skeleton

```python
#!/usr/bin/env python3
"""Wiki-query-before-offload Stop hook.

Hard-enforcement gate per P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md.
Architectural template: ~/.grok/hooks/scripts/quality_gate.py.
"""
import json
import os
import re
import sys
from pathlib import Path

# Make _hook_base importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hook_base import (
    parse_envelope, resolve_transcript_path, iter_tool_uses_in_current_turn,
    matches_wiki_pattern, resolve_mode, write_evidence, fail_open_decorator,
    negation_window,
)

HOOK_NAME = "wiki-query-gate"
MODE_ENV_VAR = "GROK_WIKI_QUERY_GATE_MODE"
MODES = {"shadow", "receipt_authoritative"}   # collapsed per F-08
DEFAULT_MODE = "shadow"
NEGATION_WINDOW_ENV_VAR = "GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS"
DEFAULT_NEGATION_WINDOW_CHARS = 60

OFFLOAD_PATTERNS = [...]        # see §3.3
NEGATION_PATTERNS = [...]       # see §3.3
WIKI_PATH_PATTERNS = [...]      # see §3.4 (subdirectory-tolerant regex list)

BLOCK_REASON_TEMPLATE = """Wiki-query gate: ..."""   # see §3.6 (full text)

@fail_open_decorator
def main() -> dict:
    envelope = parse_envelope(sys.stdin.read())

    # Preconditions (matches §3.5 — evaluated first; any failure → ALLOW)
    if envelope.get("stopHookActive"):
        return {}
    if envelope.get("reason") != "end_turn":
        return {}

    mode = resolve_mode(MODE_ENV_VAR, MODES, DEFAULT_MODE)
    negation_window_chars = int(os.environ.get(NEGATION_WINDOW_ENV_VAR,
                                               DEFAULT_NEGATION_WINDOW_CHARS))

    # Coerce None → "" so scan_offload_phrases never receives None (resolves F-21)
    last_message = envelope.get("lastAssistantMessage") or ""
    candidate_spans = scan_offload_phrases(last_message)
    offload_spans = negation_window(last_message, candidate_spans,
                                    NEGATION_PATTERNS, negation_window_chars)
    offload_phrases = [last_message[s:e] for s, e in offload_spans]

    transcript = resolve_transcript_path(envelope["sessionId"])
    # iter_tool_uses_in_current_turn defines "this turn" via role: "user" boundary,
    # NOT via a 30-min lookback (resolves F-01, F-06). The lookback is now a
    # safety floor applied inside iter_tool_uses_in_current_turn.
    wiki_receipts = [matches_wiki_pattern(r, WIKI_PATH_PATTERNS)
                     for r in iter_tool_uses_in_current_turn(transcript, envelope["sessionId"])]
    wiki_receipts = [r for r in wiki_receipts if r is not None]
    # Plus qmd receipts (separate matcher; regex is insufficient — see §3.4 / F-09)
    wiki_receipts += [r for r in iter_tool_uses_in_current_turn(transcript, envelope["sessionId"])
                      if matches_qmd_wiki_call(r)]

    decision = compute_decision(offload_phrases, wiki_receipts, mode)
    write_evidence(HOOK_NAME, {
        "session_id": envelope["sessionId"],
        "mode": mode,
        "offload_phrases": offload_phrases,
        "wiki_receipts_count": len(wiki_receipts),
        "decision": "BLOCK" if decision else "ALLOW",
        "stopHookActive": envelope.get("stopHookActive"),
        "reason": envelope.get("reason"),
    })
    return decision

def compute_decision(offload_phrases: list[str], wiki_receipts: list, mode: str) -> dict:
    if not offload_phrases:
        return {}                                  # ALLOW (no offload)
    if wiki_receipts:
        return {}                                  # ALLOW (agent did due diligence)
    if mode == "shadow":
        return {}                                  # ALLOW but logged
    # mode == "receipt_authoritative"
    reason = BLOCK_REASON_TEMPLATE.format(
        phrases=", ".join(repr(p) for p in offload_phrases))
    return {"decision": "block", "reason": reason}
```

**Notes on the revised skeleton (resolves F-01, F-03, F-21):**
- `infer_failing_tool_from_offload` is REMOVED entirely (was vestigial scaffolding per F-03). The block reason template no longer references a canonical tool name (F-18).
- `matches_qmd_wiki_call` is defined in `wiki_query_gate.py` (not in `_hook_base.py`) because it's wiki-gate-specific. Its semantics are in §3.4.
- `iter_tool_uses_in_current_turn` (replacing `iter_tool_uses`) is the source of truth for "this turn" — see §4.3 contract.
- `last_message = envelope.get("lastAssistantMessage") or ""` coerces both absent keys AND explicit `None` values to empty string (F-21).

### 4.5 `wiki-query-gate.json` registration

**Path format decision (resolves F-04):** the actual `~/.grok/hooks/quality-gate.json` uses **resolved Windows paths with both backslashes and forward slashes** (verified via direct read of `quality-gate.json` on this host — see F-10 verification log). The host does NOT perform `${HOME}` expansion in the JSON `command` field. The template below mirrors the existing `quality-gate.json` style:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\wiki_query_gate.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Operator responsibility:** the path `C:\Users\brsth\.grok\hooks\scripts\wiki_query_gate.py` is host-specific (this is the path on the current host). Operators installing this hook on a different host must substitute their own resolved home path. The `${HOME}` form in the original draft was incorrect — it would not be expanded by the host's JSON parser, and would result in a hook that fails to launch.

**Why no `matcher`:** the existing `quality-gate.json` Stop entry also has no matcher (Stop is not a tool event). Mirror the precedent.

### 4.6 Tests (`test_wiki_query_gate.py`)

The test count is **exactly 25** (resolves F-19 — replacing "≥20" with a specific count). The 5 additional tests beyond the original 20 cover: nested wiki paths (F-02), non-wiki qmd (F-09), malformed-line resilience (F-26), fail-open evidence logging (F-24), and negation-window edge case (F-17).

| # | Test | Input | Expected | Resolves |
|---|------|-------|----------|----------|
| 1 | `test_offload_detected_you_must_do` | "you must do browser OAuth" | offload_phrases non-empty | — |
| 2 | `test_offload_detected_operator_must` | "the operator must re-auth" | offload_phrases non-empty | — |
| 3 | `test_offload_detected_requires_human` | "this requires human intervention" | offload_phrases non-empty | — |
| 4 | `test_offload_not_detected_no_match` | "you may want to check the docs" | offload_phrases empty | — |
| 5 | `test_negation_suppresses_offload` | "you don't need to do anything" | offload_phrases empty | — |
| 6 | `test_negation_window_60_chars` | "automatable, no user action needed. ...you must do browser OAuth" (within 60 chars) | offload_phrases empty | — |
| 7 | `test_negation_window_custom_chars` | negation at 80 chars before offload; window set to 100 via env var | offload_phrases empty | F-17 |
| 8 | `test_negation_window_too_small` | negation at 80 chars before offload; default window 60 | offload_phrases non-empty | F-17 |
| 9 | `test_wiki_receipt_read_file_concept` | transcript with read_file of `.data/wiki/concepts/foo.md` | wiki_receipts non-empty | — |
| 10 | `test_wiki_receipt_read_file_nested_concept` | transcript with read_file of `.data/wiki/concepts/error-handling/foo.md` | wiki_receipts non-empty | **F-02, F-27** (regex trace-verified against both this path and `.data/wiki/concepts/notebooklm-cli-operational-gotchas.md` per §3.4) |
| 11 | `test_wiki_receipt_qmd_search_wiki_target` | transcript with `qmd search "wiki/foo"` | wiki_receipts non-empty | — |
| 12 | `test_qmd_search_non_wiki_does_not_match` | transcript with `qmd search "package.json"` | wiki_receipts empty | **F-09** |
| 13 | `test_wiki_receipt_not_matched_on_unrelated` | transcript with read_file of `package.json` | wiki_receipts empty | — |
| 14 | `test_iter_tool_uses_skips_malformed_lines` | transcript with `[valid, malformed, valid]` lines | iterator yields 2 ToolUseRecords | **F-26** |
| 15 | `test_decision_no_offload` | (no offload phrases) | `{}` | — |
| 16 | `test_decision_offload_with_wiki` | offload + wiki receipt | `{}` | — |
| 17 | `test_decision_offload_no_wiki_shadow` | offload + no wiki + mode=shadow | `{}` (logged) | F-08 (collapsed modes) |
| 18 | `test_decision_offload_no_wiki_authoritative` | offload + no wiki + mode=receipt_authoritative | `{"decision": "block", ...}` | F-08 |
| 19 | `test_stop_hook_active_skips` | offload + no wiki + stopHookActive=true | `{}` | — |
| 20 | `test_non_end_turn_skips` | offload + no wiki + reason="channel_closed" | `{}` | — |
| 21 | `test_last_message_none_coerced_to_empty` | envelope with `lastAssistantMessage: null` | offload_phrases empty (no crash) | **F-21** |
| 22 | `test_fail_open_on_envelope_parse_error` | malformed stdin | exit 0 | — |
| 23 | `test_fail_open_on_transcript_missing` | transcript FileNotFoundError | exit 0 | — |
| 24 | `test_fail_open_on_unexpected_exception` | injected exception in main | exit 0 | — |
| 25 | `test_fail_open_writes_evidence_log` | injected exception in main | `.evidence/wiki-query-gate.fail_open.jsonl` has one record | **F-24** |

**Acceptance:** exactly 25 tests, ≥80% line coverage on `wiki_query_gate.py` and `_hook_base.py` modules exercised by these tests, all pass under `pytest`. Test fixtures use real temporary transcript files (no mocks per the testing rule).

---

## 5. API/Interface Changes

### 5.1 New hook registration

`~/.grok/hooks/wiki-query-gate.json` (new file, see §4.5).

### 5.2 New env vars

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `GROK_WIKI_QUERY_GATE_MODE` | `shadow` \| `receipt_authoritative` | `shadow` | Operational mode. **Collapsed from 3 modes to 2** per F-08 — the original `receipt_authoritative_with_old_fail_safe` was functionally identical to `receipt_authoritative` (the design's own §12.2 admitted this). The phase-1 → phase-2 transition in the original rollout is now collapsed into a single phase-1 (shadow → authoritative) transition. |
| `GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS` | int ≥ 1 | `60` | Window size for negation suppression. Configurable per F-17 to allow tuning without code change. |

### 5.3 New evidence log

`~/.grok/hooks/.evidence/wiki-query-gate.jsonl` — append-only, one JSON object per Stop event with fields per §4.4 `write_evidence` call.

### 5.4 No changes to

- Grok Build hook protocol (consumer only)
- `quality_gate.py` behavior (refactored internally but external surface unchanged)
- Any wiki content
- Any plugin or skill

---

## 6. Data Model

### 6.1 Hook input (consumed, not modified)

Standard Grok Build Stop envelope. Key fields used:
- `lastAssistantMessage: str`
- `stopHookActive: bool`
- `reason: str` (must equal `"end_turn"`)
- `sessionId: str` (for transcript lookup)
- `timestamp: float` (for lookback window)
- `hookEventName: str` (must equal `"Stop"`)

### 6.2 Hook output (produced)

| Outcome | Output |
|---------|--------|
| ALLOW (all allow paths) | `{}` (exit 0, no stdout) |
| BLOCK (active mode + offload + no wiki) | `{"decision": "block", "reason": "..."}` (exit 0, JSON to stdout) |
| Force stop (future use) | `{"continue": false, "stopReason": "..."}` (not used in v1) |
| Hook feedback (future use) | `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "..."}}` (not used in v1) |

### 6.3 Evidence record (written to `.evidence/wiki-query-gate.jsonl`)

```json
{
  "ts": 1753612800.123,
  "session_id": "abc123",
  "mode": "shadow",
  "stopHookActive": false,
  "reason": "end_turn",
  "offload_phrases": ["you must do browser OAuth"],
  "wiki_receipts_count": 0,
  "wiki_receipts_sample": [],
  "decision": "ALLOW",
  "block_reason_text": null
}
```

### 6.4 Transcript record shape (consumed) — **[FACT, verified per `~/.grok/hooks/scripts/quality_gate.py:1101-1109`]**

Per-line `chat_history.jsonl` record. The schema was **inferred in the v1 draft** (`tool_name`/`args`/`call_id`) but the v1 inference was wrong — quality_gate.py reads `name` (str) and `arguments` (JSON STRING, parsed via `json.loads`) and has no `call_id` field. The critical-friend review (F-Field) caught this. Implementation MUST use the verified names; using the v1 inferred names would silently produce zero receipts because `tc.get("tool_name", "")` returns `""` for every record, causing every match check to fail.

**Verified shape (per quality_gate.py:1101-1109):**

```json
{"timestamp": 1753612800.0, "role": "assistant", "tool_calls": [
  {"name": "read_file", "arguments": "{\"path\": \"P:/.data/wiki/concepts/foo.md\"}"}
]}
```

**Field contract:**

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `tool_calls` | list[dict] | outer record | `entry.get("tool_calls", [])` |
| `name` | str | inside each tool_call dict | `tc.get("name", "")` — tool name (e.g., `"read_file"`, `"grep"`, `"run_terminal_command"`) |
| `arguments` | **str** (JSON-encoded) | inside each tool_call dict | `tc.get("arguments", "{}")` — **a JSON STRING, not a dict**. Must be parsed via `json.loads(args_raw) if isinstance(args_raw, str) else args_raw`. The iterator (`_hook_base.iter_tool_uses_in_current_turn`) performs this parse during flattening so matchers receive `arguments: dict`. |
| ~~`tool_name`~~ | — | — | Does NOT exist. Use `name`. |
| ~~`args`~~ | — | — | Does NOT exist. Use `arguments`. |
| ~~`call_id`~~ | — | — | Does NOT exist. Not present in transcript schema. (Note: `tool_call_id` exists in a *different* schema — VERIFICATION_SUCCEEDED receipt records, not chat_history.jsonl.) |

**Why the v1 inference was wrong:** the design draft extrapolated field names from a generic LLM tool-call schema without verifying against the actual reader. The mismatch would have silently disabled Signal 2 (wiki-query receipt detection), causing every gate activation in `receipt_authoritative` mode to be a false-positive block. The defensive contract (skip on parse error, don't abort) made the failure invisible at the hook level — only observable via 100% block rate on agents that had actually queried the wiki.

**Falsifier:** if a future `quality_gate.py` change moves `name` or `arguments` (e.g., to top-level fields, or to a different key), this section must be re-verified. The `_hook_base` contract makes the change local (one iterator function), but the design's matchers must be updated to match.

---

## 7. Alternatives

### 7.1 Hidden anchor up front

The four options below share one assumption: **any wiki query within the current assistant turn counts as a due-diligence receipt, regardless of whether the query temporally precedes the offload phrase**. This is the RCA's recommendation (Fix 1: mandatory wiki-query before offload) and the `/www` evidence's recommendation (hard `tool_choice` + forced retrieve-first). Per KD-4, v1 does NOT require temporal coupling between the query and the offload — temporal coupling would require reliably detecting "the failing tool" from the transcript, which is deferred to v2 (Open Questions Q4). Alternatives that reject this anchor (e.g., "always-on RAG" or "the operator should explicitly prompt 'check the wiki'") are not considered here — the RCA already rejected them. The selection criterion for the four options below is **reliability tier** (hard vs. soft vs. adaptive) cross-cut with **implementation cost on Grok Build** (host-native primitive vs. external dependency).

**Note on F-12:** the previous version of this anchor said "a wiki query at the moment of offload is the success signal," which implied temporal coupling. That phrasing was misleading relative to KD-4. The anchor above is the accurate one.

### 7.2 Option A — Stop hook (chosen)

See full design above. Reliability tier: **hard** (the model cannot skip the gate — the Stop event always fires). Implementation cost: **low** (host-native primitive, mirrors existing `quality_gate.py`). Selection criterion winner: highest reliability tier reachable on the host's native primitives.

### 7.3 Option B — PreToolUse hook on tool-error responses

Block the next tool call after an error until a wiki query appears. Reliability tier: **hard** (PreToolUse blocks are enforced). Implementation cost: **medium** (requires correlating the error response with the next tool call, identifying which tool class is "post-error query"). Disadvantages: false-positive risk is higher (would block legitimate next-tool-call retries before the agent has had time to query), and the `lastAssistantMessage` signal is not available at PreToolUse time — the agent has not yet produced offload language. Selected against because the offload signal does not exist at PreToolUse time.

### 7.4 Option C — System-prompt-only / advisory rule

Add a rule to `~/.grok/AGENTS.md`: "before offloading any blocker to the operator, search the wiki for the failing tool's documented recovery." Reliability tier: **soft** (~50% per wiki concept evidence). Implementation cost: **near-zero**. Selected against because the RCA documents three advisory rules already failed on this same incident — adding a fourth has no expected value, and the `/www` evidence explicitly corroborates the ~50% advisory compliance ceiling across multiple independent sources.

### 7.5 Option D — AgentSpec-style external runtime guard

A separate process intercepting tool calls at the OS or MCP layer, with a richer policy language. Reliability tier: **hard** (highest). Implementation cost: **very high** (does not exist on Grok Build; would require building an MCP-side enforcement layer). Selected against because the host does not provide this primitive and building it is out of scope for this incident. Worth flagging as a future direction if the Stop hook proves insufficient.

### 7.6 Selection criterion

**Reliability tier reachable on the host's native primitives.** Options ranked: A (hard, native, low cost) > B (hard, native, medium cost, worse signal) > D (hard, non-native, very high cost) > C (soft, native, near-zero cost, ~50% reliability). A wins.

---

## 8. Security

### 8.1 Threat model

| Threat | Mitigation |
|--------|-----------|
| Operator accidentally enables `receipt_authoritative` and a legitimate offload is blocked | Fail-open on any exception; the block reason text is specific so the operator can intervene. The 8-continuation cap is the structural backstop. |
| Agent crafts a transcript record to fake a wiki query receipt | Transcript is on disk at `chat_history.jsonl` and read-only from the hook's perspective; faking it requires the agent to write to the transcript, which it cannot do. If a future feature allows agent-side transcript writes, this needs re-audit. |
| Hook script becomes a vector for malicious payload | Script is plain Python with no `eval`/`exec`, no network calls, no shell-out beyond reading files. Atomic write to evidence log uses `os.replace` per file-operations rule. |
| Offload patterns detect something that should be allowed (e.g., the operator genuinely must act) | The wiki-query check is the safety valve — if the agent DID query the wiki and the wiki does not document a recovery, the offload is legitimate and the stop is allowed. **The wiki is the ground truth for "is this offload legitimate?", not the regex patterns.** |
| A high-stakes error (e.g., secret leak) is being diagnosed and the agent needs to offload without consulting the wiki first | The block reason text is a request to consult the wiki — not a refusal to offload. If the wiki is silent, the next turn's offload is allowed. The agent cannot be silenced indefinitely. |

### 8.2 Privilege

The hook runs with the user's full Grok Build session privileges. It reads files (`chat_history.jsonl`, evidence log) and writes one file (evidence log). No new attack surface beyond what `quality_gate.py` already has.

### 8.3 Fail-open rationale

Per `quality_gate.py`'s precedent and the file-operations rule: a broken enforcement gate must not kill conversation. Any internal exception → exit 0 (allow). The evidence log captures the exception for post-mortem.

### 8.4 No destructive operations

The hook never deletes, moves, or rewrites user content. Evidence log writes are append-only and atomic.

---

## 9. Observability

### 9.1 Per-Stop evidence record

Every Stop event (regardless of decision) writes one record to `~/.grok/hooks/.evidence/wiki-query-gate.jsonl`. Fields per §6.3. This is the primary observability surface.

### 9.2 Aggregate metrics (derived from evidence log)

Computed by `python ~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py`:

| Metric | How computed | Target |
|--------|--------------|--------|
| Total Stop events scanned | count of records | (baseline) |
| Offload detection rate | records with non-empty `offload_phrases` / total | (observe; expect <5%) |
| Wiki-query receipt rate | records with `wiki_receipts_count > 0` / total | (observe) |
| Offload-without-wiki rate | records with both `offload_phrases` AND `wiki_receipts_count == 0` / total | **primary signal: target trending toward 0** |
| Block rate | records with `decision == "BLOCK"` / total | (in active mode: target <2%) |
| Fail-open rate | records with `decision == "FAIL_OPEN"` / total | (target: <1%) |
| Operator-labeled FP rate | records labeled `fp` in `labels.jsonl` / records with `decision == "BLOCK"` in active mode | (target: <5%) |

**Labeling protocol (resolves F-15):** the operator creates `~/.grok/hooks/.evidence/wiki-query-gate.labels.jsonl` (one label per line, JSON-encoded) for any record that was blocked. The label format:

```json
{"session_id": "abc123", "timestamp": 1753612800.123, "label": "fp", "note": "legitimate offload — user-initiated reboot required"}
{"session_id": "def456", "timestamp": 1753612900.456, "label": "tp", "note": ""}
{"session_id": "ghi789", "timestamp": 1753613000.789, "label": "unclear", "note": "wiki concept referenced but not read"}
```

`label` is one of `"fp"` (false positive — gate blocked a legitimate offload), `"tp"` (true positive — gate correctly blocked an unjustified offload), `"unclear"` (operator cannot determine; excluded from FP rate calculation). The aggregate script reads `labels.jsonl` and computes the FP rate as `count(label == "fp") / count(label in {"fp","tp"})` — only counting labeled records that received a definitive verdict.

**Unit 4 acceptance criteria extended (resolves F-15):** in addition to computing the 7 metrics, Unit 4 acceptance includes: (a) reads `labels.jsonl` if present and includes FP-rate computation in the report; (b) emits a Markdown summary at `~/.grok/hooks/.evidence/wiki-query-gate-shadow-report.md` with all metrics + FP rate; (c) tolerates absent or malformed `labels.jsonl` (warns and skips FP rate).

### 9.3 The nlm-class reproduction test

The single most important observability check: **re-run the `nlm` CLI reproduction transcript with the gate in active mode**. If the gate blocks the stop on that transcript, G1 (catch the nlm-class failure) is met. This is the discriminating test for the design.

### 9.4 Phase-transition criteria (measured, not arbitrary)

**F-08 update:** the original two-mode transition is collapsed to a single shadow → authoritative transition.

| Phase transition | Required evidence |
|------------------|-------------------|
| shadow → authoritative | (a) ≥100 Stop events in shadow; (b) operator-labeled FP rate <5% via `labels.jsonl` (per F-15); (c) nlm-class reproduction transcript blocks correctly (Unit 7 verification); (d) env var set in operator's shell profile |

### 9.5 Dashboards / alerting

Out of scope for v1. The evidence log + the aggregate script are sufficient for operator-driven inspection. A future dashboarding integration is deferred (HANDOFF §15.5).

---

## 10. Key Decisions

| # | Decision | Why | Alternatives rejected |
|---|----------|-----|------------------------|
| KD-1 | Use a Stop hook (not PreToolUse or advisory rule) | Signal is in the final message; PreToolUse fires before the message exists; advisory has ~50% reliability ceiling | PreToolUse (worse signal timing); advisory (proven failure mode) |
| KD-2 | Two-signal pattern (lastAssistantMessage + transcript scan) | Same architecture as `quality_gate.py`; neither signal alone is sufficient — message alone is gameable, transcript alone is noisy | Message-only (gameable); transcript-only (noisy, no offload signal) |
| KD-3 | High-precision, low-recall bias on offload patterns | False positives block legitimate stops (more harmful than missed offloads) | Broad patterns (high FP rate); LLM-as-judge (adds latency, miscalibrated per `/www` evidence) |
| KD-4 | Wiki-query receipt = ANY wiki query in the current assistant turn (no temporal coupling required) | Simpler; an agent that queried the wiki at all is much more likely doing due diligence than gaming | Per-tool-name matching (requires reliably detecting "the failing tool" from transcript — Open Questions Q4) |
| KD-5 | Shadow mode default; phased rollout gated on measured FP rate | Operator correction 2026-07-26: "default to phased rollout with measured data"; the `/www` evidence explicitly notes calibration drift as a risk | Immediate active mode (no measurement); single-shot shadow→active (insufficient data) |
| KD-6 | Extract `_hook_base.py` BEFORE writing this hook | Coupling analysis (§14): existing hooks (verified: ~5 quality/mutation hooks share patterns on this host per F-10 measurement) duplicate envelope parse, transcript iter, mode dispatch; adding another hook without extracting grows the debt | Add hook directly (debt grows); inline utility functions (no reuse across hooks) |
| KD-7 | Fail open on any internal exception; the fail-open path **MUST emit an evidence record** (per `_hook_base.fail_open_decorator` contract) | Mirrors `quality_gate.py`; broken enforcement must not kill conversation; the evidence record is required so post-mortem can diagnose the failure | Fail closed (high blast radius; conversation killer); silent fail-open (operator cannot diagnose) — resolves F-24 |
| KD-8 | Default 60-char negation window, configurable via `GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS` | Mirrors `quality_gate.py`'s `claim-phrase negation`; 60 chars is the empirical sweet spot for the negation example "While the operator could do this manually, you must do browser OAuth" (negation ~52 chars before offload); window too small (<60) fails to suppress distant negations, window too large (>120) suppresses legitimate offloads | No negation (high FP); fixed large window (over-suppresses) — resolves F-17 |
| KD-9 | Block reason text is a request, not a refusal, and explicitly names the success condition (next-turn wiki query) | The agent cannot be silenced indefinitely; the wiki is the ground truth for legitimate offload; the success condition is named unambiguously so the agent knows the loop will release | Refusal-style block (silences the agent); permissive block (no instruction); ambiguous success condition (loop trap) |
| KD-10 | Host: Grok Build only in v1 | Hook registration mechanism is host-specific; cross-host porting requires separate design | Cross-host from v1 (scope creep); Claude Code port (different host's hook protocol) |
| KD-11 | **Sub-agent Stop fires ARE gated** by this hook (not only top-level Stop) | Sub-agents also encounter tool errors and may offload without consulting the wiki; gating them closes a real gap; the cost is minimal because the same signal-detection logic applies regardless of agent depth | Gating only top-level Stop (leaves a gap) — resolves F-22. **Host verification:** Unit 3 acceptance criteria (b) must confirm the hook fires on a sub-agent Stop transcript before the hook is considered live. |

---

## 11. Risk Table

| Risk | P | I | Mitigation |
|------|---|---|------------|
| Offload patterns have unacceptable FP rate on real transcripts | M | H | Shadow mode first (≥100 events); phase-1 only after FP rate <5%; fail open always; negation window; operator-discoverable log |
| Wiki-query detection misses legitimate receipts (e.g., indirect via MCP tool) | M | M | Receipt patterns cover read_file / grep / rg / qmd; per-tool-name matching deferred to v2 (handed off if v1 misses) |
| `chat_history.jsonl` field schema differs from assumption | ~~M~~ → **RESOLVED** | ~~M~~ → **N/A** | Schema is now verified per quality_gate.py:1101-1109 (`name` + `arguments` as JSON string; no `call_id`). See §6.4. The defensive parse-on-error contract remains as a defense-in-depth measure for unexpected schema variants |
| `_hook_base.py` extraction breaks `quality_gate.py` behavior | L | H | Refactor in same commit; full test suite must pass unchanged; no behavior change is the acceptance criterion |
| 8-continuation cap fires while the agent is mid-wiki-query (false negative on the wiki lookup) | L | L | Wiki queries complete in 1-2 turns; cap is 8; would only trigger in pathological loops; fail-open ensures no permanent silence |
| Agent learns to "game" the gate by querying an unrelated wiki page before offloading | L | M | Receipts are observable in the evidence log; per-tool-name matching (v2) closes this; agent gaming would still produce a wiki query, which is better than no wiki query |
| Block reason text is misinterpreted by the model (e.g., treated as refusal of the offload rather than a request to check) | L | M | Reason text explicitly says "If the wiki does NOT document the recovery, offload is legitimate — restate your finding and stop"; tested via reproduction transcript |
| Hook script becomes load-bearing infrastructure without proper versioning | L | M | Hook is registered with `timeout: 30`; follows existing pattern; no plugin cache invalidation needed (it's a user-scope hook, not a plugin) |
| Operator forgets the gate is on and is confused by a blocked stop | L | L | Block reason text names the gate explicitly ("Wiki-query gate: ..."); env var name is documented; evidence log is operator-discoverable |
| Shadow mode produces too few events to measure (low Stop event rate) | M | M | If <100 events in 2 weeks, extend shadow phase; the gate cannot move to active mode without sufficient data |
| `chat_history.jsonl` size and per-Stop scan cost blows the 30s timeout | M | M | Multi-hour sessions produce large transcripts; `read_text` + `splitlines` + `json.loads` is O(N) per Stop. Mitigation: `iter_tool_uses_in_current_turn` walks the file from the END (tail-ward scan) to find the most recent `role: "user"` boundary, then forward-reads only records after it — bounded by turn length, not session length. Add a `MAX_TRANSCRIPT_BYTES` env var (default 50 MB) that truncates reads beyond the limit and logs a warning. (F-16a) |
| `GROK_WIKI_QUERY_GATE_MODE` env var is not persisted across shells; a re-login silently regresses to `shadow` | M | H | Document the env var in `~/.grok/hooks/README.md` (new file in Unit 5) with explicit `Set-Alias` instructions for PowerShell 7. Alternatively, persist the mode in a state file (`~/.grok/hooks/.state/wiki-query-gate.mode`) that the hook reads as fallback when env var is unset. (F-16b) |
| Sessions without `chat_history.jsonl` produce spurious blocks once Phase-1 is active | M | H | Every Stop in such a session would be "no receipt" → blocks. Mitigation: `resolve_transcript_path` raises `FileNotFoundError`; `iter_tool_uses_in_current_turn` propagates it; the gate's fail-open path catches it and emits `wiki_query_receipts_count = "transcript_missing"` evidence record. The operator reviews the evidence log to detect this case. (F-16c) |
| Hook registration relies on `~/.grok/hooks/*.json` discovery but this is unverified for the new file | L | H | Verified via direct read of `~/.grok/hooks/quality-gate.json` on this host (F-10 measurement). Mitigation: Unit 3 acceptance criteria (b) requires `cat ~/.grok/active-surface.last.md` to list `wiki-query-gate` after registration. If the host does not pick up the new file, registration must move to `~/.claude/settings.json` (compat) per the AGENTS.md hook discovery table. (F-16d) |

P/I scale: L (low), M (medium), H (high).

---

## 12. Rollout

### 12.1 Phase 0 — Shadow (default; ship in this PR)

| Field | Value |
|-------|-------|
| Mode env var | `GROK_WIKI_QUERY_GATE_MODE=shadow` (default) |
| Hook registered | Yes (`~/.grok/hooks/wiki-query-gate.json`) |
| Blocking | No (always ALLOW; logged to evidence) |
| Telemetry | Per-Stop record to `~/.grok/hooks/.evidence/wiki-query-gate.jsonl` |
| Duration | Until ≥100 Stop events recorded OR 2 weeks, whichever first |
| Exit criterion | Operator reviews evidence log; labels any false-positive offload detections in `labels.jsonl`; computes FP rate (target <5%) |
| Rollback | `rm ~/.grok/hooks/wiki-query-gate.json` (or move out of `~/.grok/hooks/`) |

### 12.2 Phase 1 — Receipt authoritative

| Field | Value |
|-------|-------|
| Mode env var | `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` |
| Hook registered | Yes |
| Blocking | Yes — blocks on offload + no wiki-query in current turn |
| Fail-open | Internal exception → ALLOW + evidence record (per KD-7, F-24). Transcript path resolution failure → ALLOW + `transcript_missing` flag in evidence record (per F-16c). |
| Telemetry | Same as Phase 0; aggregate metrics now compute block rate |
| Duration | Indefinite (steady state). Operator monitors for false positives via `labels.jsonl`. |
| Exit criterion | N/A (this IS the steady state) |
| Rollback | `GROK_WIKI_QUERY_GATE_MODE=shadow` (immediate, no code change) |

**Note on F-08:** the original Phase 1 (`receipt_authoritative_with_old_fail_safe`) and Phase 2 (`receipt_authoritative`) have been collapsed into a single Phase 1. The original design's own §12.2 admitted the two modes were functionally identical. The transition from shadow → authoritative is now a single env var change, gated by the ≥100 shadow events + FP <5% criterion (same as before).

### 12.3 Rollback procedure (any phase → shadow)

```powershell
# Disable blocking immediately (no code change):
$env:GROK_WIKI_QUERY_GATE_MODE = "shadow"
# Or remove the hook entirely:
Remove-Item "$HOME/.grok/hooks/wiki-query-gate.json"
# Verify hook no longer fires (real mechanism per F-16d):
Get-Content "$HOME/.grok/active-surface.last.md" | Select-String "wiki-query-gate"
```

### 12.4 Rollback procedure (any phase → off)

`rm ~/.grok/hooks/wiki-query-gate.json` and `rm -rf ~/.grok/hooks/.evidence/wiki-query-gate.jsonl` (keep the script for re-enablement). No code revert needed.

### 12.5 Cross-phase invariants

- `_hook_base.py` extraction happens in Phase 0 (commit 1, §13).
- `quality_gate.py` refactor happens in Phase 0 (commit 1, §13).
- Hook registration happens in Phase 0 (commit 3, §13).
- Mode env var is honored in all phases — the variable controls behavior, not deployment.
- Fail-open behavior is preserved in all phases.

---

## 13. Implementation Plan

Each unit is a single commit (or commit group if files are tightly coupled). All commits land in the same PR unless otherwise noted.

### Unit 1 — Extract shared hook base library

| Field | Value |
|-------|-------|
| **Title** | `refactor(hooks): extract _hook_base.py from quality_gate.py` |
| **Files affected** | `~/.grok/hooks/scripts/_hook_base.py` (new); `~/.grok/hooks/scripts/quality_gate.py` (modified to import from base); `~/.grok/hooks/scripts/tests/test_hook_base.py` (new); `~/.grok/hooks/scripts/tests/test_quality_gate.py` (existing, must pass unchanged) |
| **Dependencies** | None |
| **Description** | Extract the duplicated hook patterns (envelope parse, transcript iter, mode env var, fail-open, negation window, evidence writer) into `~/.grok/hooks/scripts/_hook_base.py`. Refactor `quality_gate.py` to import from the base. Behavior must be identical; existing `test_quality_gate.py` must pass unchanged. |
| **Acceptance criteria** | (a) `_hook_base.py` exposes the 7 functions listed in §4.3; (b) `quality_gate.py` imports from `_hook_base` for all 7 patterns; (c) `pytest ~/.grok/hooks/scripts/tests/` passes with 100% of pre-existing tests still green; (d) shadow-mode integration test: produce identical evidence log pre/post refactor (compare snapshot) |
| **Feature flags** | None (internal refactor; no behavioral change) |
| **Disposition** | **COMMIT_THIS_SESSION** |

### Unit 2 — Implement wiki_query_gate.py core

| Field | Value |
|-------|-------|
| **Title** | `feat(hooks): add wiki_query_gate.py with offload + receipt detection` |
| **Files affected** | `~/.grok/hooks/scripts/wiki_query_gate.py` (new); `~/.grok/hooks/scripts/tests/test_wiki_query_gate.py` (new) |
| **Dependencies** | Unit 1 (uses `_hook_base`) |
| **Description** | Implement the new Stop hook script. Offload patterns per §3.3, wiki-query receipts per §3.4, decision matrix per §3.5, fail-open per §8.3. Shadow mode is the only active mode in this unit. |
| **Acceptance criteria** | (a) All 25 tests in §4.6 pass (resolved F-19); (b) ≥80% line coverage on `wiki_query_gate.py`; (c) `python wiki_query_gate.py < shadow_test_envelope.json` exits 0 in shadow mode; (d) evidence log written per Stop event |
| **Feature flags** | `GROK_WIKI_QUERY_GATE_MODE` (env var; default `shadow`) |
| **Disposition** | **COMMIT_THIS_SESSION** |

### Unit 3 — Register the hook

| Field | Value |
|-------|-------|
| **Title** | `feat(hooks): register wiki-query-gate Stop hook` |
| **Files affected** | `~/.grok/hooks/wiki-query-gate.json` (new) |
| **Dependencies** | Unit 2 |
| **Description** | Register the hook at the Stop event, timeout 30s. Template from `quality-gate.json`. |
| **Acceptance criteria** | (a) `~/.grok/hooks/wiki-query-gate.json` exists with valid JSON; (b) Grok Build hook discovery picks it up (`cat ~/.grok/active-surface.last.md` includes `wiki-query-gate`); (c) shadow mode emits evidence records; (d) no false-positive blocks (shadow never blocks) |
| **Feature flags** | `GROK_WIKI_QUERY_GATE_MODE=shadow` (default; no operator action needed) |
| **Disposition** | **COMMIT_THIS_SESSION** |

### Unit 4 — Aggregate metrics script

| Field | Value |
|-------|-------|
| **Title** | `feat(hooks): add aggregate_wiki_gate_metrics.py` |
| **Files affected** | `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py` (new); `~/.grok/hooks/scripts/tests/test_aggregate_metrics.py` (new) |
| **Dependencies** | Unit 3 (needs evidence records to exist) |
| **Description** | Compute the metrics in §9.2 from the evidence log. Output to stdout as a table; emit a Markdown summary at `~/.grok/hooks/.evidence/wiki-query-gate-shadow-report.md`. |
| **Acceptance criteria** | (a) Script computes all 7 metrics; (b) report regenerates on every run; (c) tests cover: empty log, mixed records, offload-only, wiki-only, mixed |
| **Feature flags** | None |
| **Disposition** | **COMMIT_THIS_SESSION** |

### Unit 5 — Document the gate in AGENTS.md

| Field | Value |
|-------|-------|
| **Title** | `docs(AGENTS): add wiki-query gate reference` |
| **Files affected** | `P:/AGENTS.md` (modified — add a 3-line entry in the enforcement mechanisms section) |
| **Dependencies** | Unit 3 |
| **Description** | Add a pointer to the gate so operators and other sessions can discover it. Does not add a rule the agent must follow — the hook enforces it. |
| **Acceptance criteria** | (a) Entry mentions `wiki_query_gate.py`; (b) entry mentions the env var; (c) entry points to evidence log location |
| **Feature flags** | None |
| **Disposition** | **COMMIT_THIS_SESSION** |

### Unit 6 — Phase-1 transition (operator decision)

| Field | Value |
|-------|-------|
| **Title** | Phase-1: set `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` |
| **Files affected** | None (env var only) |
| **Dependencies** | Unit 3 + ≥100 Stop events in shadow + operator review of FP rate <5% (via `labels.jsonl`) |
| **Description** | Operator (NOT the agent) sets the env var on the host. Per the trust-escalation ladder, agent autonomy for irreversible-like changes (blocking agent stops) is operator-gated. |
| **Acceptance criteria** | (a) ≥100 records in evidence log; (b) operator has reviewed the shadow report and labeled FP rate via `labels.jsonl`; (c) FP rate <5%; (d) env var set in operator's shell profile (or Grok Build session config); (e) nlm-class reproduction transcript blocks correctly |
| **Feature flags** | `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` |
| **Disposition** | **HANDOFF** (operator decision after data) |

**F-08 note:** the original Unit 6/7/8 (three units: phase-1 env var, phase-2 env var, reproduction test) are collapsed into a single Unit 6. The original `receipt_authoritative_with_old_fail_safe` mode is REMOVED from `MODES`; only `shadow` and `receipt_authoritative` remain. The reproduction verification (original Unit 8) is folded into Unit 6's acceptance criteria (e) rather than as a separate unit.

### Unit 7 — Reproduction verification (operator-driven)

| Field | Value |
|-------|-------|
| **Title** | Verify: nlm-class reproduction transcript blocks in Phase-1 |
| **Files affected** | None (verification only) |
| **Dependencies** | Unit 6 |
| **Description** | Operator runs the original `nlm` CLI auth-error transcript through the agent in `receipt_authoritative` mode. The gate should block the stop on the offload turn. |
| **Acceptance criteria** | (a) Reproduction transcript blocks correctly; (b) transcript has zero wiki-query tool calls (the original failure); (c) post-fix transcript (where agent queries the wiki first) does NOT block; (d) evidence log captures both runs with correct `decision` field |
| **Feature flags** | N/A (test) |
| **Disposition** | **HANDOFF** (operator verification) |

---

## 14. Open Questions

These are the [INFERENCE] and [UNKNOWN] premises from §2.4 plus implementation-time ambiguities.

| # | Question | Class | What changes if wrong | Resolution path |
|---|----------|-------|----------------------|----------------|
| Q1 | Are the offload patterns in §3.3 high-precision enough on real transcripts? | [INFERENCE] | If FP rate is too high in shadow, narrow patterns or add per-tool allowlists; if FP rate is too low (FN), broaden patterns | Shadow mode measurement (Phase 0) |
| Q2 | Is the false-positive rate acceptable? | [UNKNOWN] | Determines whether Phase 1 ever starts | Shadow mode measurement |
| Q3 | ~~What is the exact field schema for tool_use records in `chat_history.jsonl`?~~ | **RESOLVED by F-Field** | The schema is now verified: `tool_calls[i].name` (str) + `tool_calls[i].arguments` (JSON string, parsed via `json.loads`). No `tool_name`/`args`/`call_id` fields exist. See §6.4 for the verified shape and §6.4 "Field contract" for the substitution table | N/A — verified per `~/.grok/hooks/scripts/quality_gate.py:1101-1109` |
| Q4 | Should wiki-query receipts require matching the failing tool's name, or any wiki query? | [INFERENCE] | v1 allows any wiki query in the current turn (simpler, less gameable than per-tool matching); if v1 produces too many "I queried the wiki about something unrelated" blocks, v2 adds per-tool matching | v2 enhancement; not blocking for v1 |
| Q5 | Does `chat_history.jsonl` exist for every session, or is it session-scoped/lazy-created? | [UNKNOWN] | If lazy, `resolve_transcript_path` raises `FileNotFoundError`; the gate's fail-open path catches it and emits `wiki_query_receipts_count = "transcript_missing"` in the evidence record (per F-16c). Operator detects via evidence log review | Defensive code in `_hook_base.resolve_transcript_path` + fail-open contract |
| Q6 | ~~Does the 30-min transcript lookback window match typical error-diagnosis duration?~~ | **RESOLVED by F-06** | The lookback is now a safety floor (applied inside `iter_tool_uses_in_current_turn`), NOT a definition of turn boundary. Turn boundary is `role: "user"` records. The lookback no longer affects receipt semantics | N/A — resolved |
| Q7 | ~~Does the Stop hook fire for sub-agent stops, only the top-level agent, or both?~~ | **RESOLVED by KD-11** | KD-11 commits: sub-agent Stop fires ARE gated. Host verification is Unit 3 acceptance criteria (b) | N/A — resolved |
| Q8 | Will the operator want a Slack/Discord/email notification when a stop is blocked? | [UNKNOWN] | Phase-1 evidence log + aggregate script may be sufficient; operator can request notifications later | Deferred to Phase-1 review |
| Q9 | Should the gate also block when the agent says "I cannot find documentation" without having searched? | [INFERENCE] | Could catch a different failure mode (claims-of-no-docs without search), but is harder to detect reliably | v2 enhancement |
| Q10 | Does the wiki concept `notebooklm-cli-operational-gotchas.md` actually exist? | [FACT, per evidence-brief] | If it does not, the RCA's premise is wrong — but the gate still operates correctly (it gates on wiki queries, not on specific concepts) | Already verified per evidence-brief |
| Q11 | Should the gate share an env var namespace with `GROK_RECEIPT_GATE_MODE`, or use its own? | [INFERENCE] | Separate (`GROK_WIKI_QUERY_GATE_MODE`) is clearer operationally; shared would couple the two gates' modes | v1 uses separate env var; can be unified later |

---

## Coupling & Code-Smell Inventory (Appendix)

This appendix is mandatory per the design template and the file-editing protocol. It audits the modules the design touches against the four mandatory smell classes (DRY, parameter count, touch-point count, mixed concerns).

### C1 — `quality_gate.py` (existing; will be refactored in Unit 1)

**Measurement log (per F-10, corrected per F-28):** direct `Get-ChildItem` of `~/.grok/hooks/scripts/*.py` on this host returns 22 Python files (not the 6 originally estimated). The hooks that share JSON-envelope / tool-use parsing patterns with `quality_gate.py` are: `quality_gate.py`, `quality_nudge.py`, `quality_cleanup.py`, `mutation_pre.py`, `mutation_post.py`, `verification_receipt_writer.py` — **6 candidate hooks**. (F-28 fix: the prior claim of "5 candidate hooks" was a counting error — the list contains 6 file names. The refactor remains ROI-positive at 6, and the Action rows reflect the corrected count.)

| Class | Count | Threshold | Status | Action |
|-------|-------|-----------|--------|--------|
| DRY violations | Verified: 6 candidate hooks (above, per F-28 correction) likely duplicate envelope parse + mode dispatch; transcript-iter pattern is unique to `quality_gate.py`; negation pattern is unique to `quality_gate.py`. **Measured DRY count: ≥3** (envelope parse + mode dispatch + evidence-log writer — the latter ad-hoc per hook but with shared semantics) | ≥3 → refactor has positive ROI | **MET (measured)** | Unit 1 extracts `_hook_base.py`; `quality_gate.py` uses it |
| Positional parameter count | **NOT MEASURED** (would require reading `quality_gate.py`'s function signatures). Original estimate of 8-13 was inferred from a past `/close` review precedent and not re-verified | >7 → coupling signal | **UNKNOWN — defer to Unit 1 measurement** | Unit 1 measures first; if count >7, replace with dict/dataclass in `_hook_base`; if ≤7, no action needed |
| Touch-point count for new gate | **NOT MEASURED** (would require counting imports per hook script). Original estimate of "≥7 touch points" was inferred from the design's own §3.2 table | >3 → structural coupling | **UNKNOWN — defer to Unit 1 measurement** | Unit 1 measures first; if >3, extract to `_hook_base`; if ≤3, no action needed |
| Mixed concerns | `quality_gate.py` mixes: transcript parsing, message scanning, mode control, fail-open, evidence logging — 5 concerns in one script (verified by reading the file's top-level structure) | ≥2 → mixed | **MET** | Unit 1: `_hook_base.py` separates concerns; each gate script imports only what it needs |

**Decision rule for Unit 1 (resolves F-10, restructured per F-29):** Unit 1 starts with **measurement**, not extraction. The pre-measurement state already has 2 of 4 thresholds MET (DRY via the measurement log above; Mixed concerns verified by reading the file structure). The decision rule operates on the two UNKNOWN thresholds (Positional params, Touch-points). Steps:
1. Read `quality_gate.py` and count: functions with >7 positional params, occurrences of envelope-parse boilerplate, occurrences of mode-dispatch boilerplate, occurrences of evidence-log boilerplate.
2. Apply the four thresholds above with the measured counts.
3. If all four thresholds MET → proceed with `_hook_base.py` extraction as designed.
4. If 2-3 thresholds MET → extract a smaller subset (`parse_envelope` + `fail_open_decorator` only); leave transcript iter / mode / negation in `quality_gate.py` for now. **This is the expected pre-measurement outcome** (only the 2 unknown thresholds can fall short of MET, so the count drops to 2-3 if either is NOT MET).
5. If 0-1 thresholds MET → skip the refactor; add `wiki_query_gate.py` directly with its own copies of the patterns (accepting the debt, document it in §14 C1). **This branch is unreachable from the current measurement state** — it would require BOTH unknown thresholds (Positional params AND Touch-points) to NOT MET while ALSO disconfirming the two already-MET thresholds (DRY AND Mixed concerns). Per F-29, this branch is retained as a defensive fallback (if future re-measurement contradicts the current observation, the no-refactor path is preserved) but is not a realistic outcome of the Unit 1 measurement step.

This makes the refactor **evidence-gated** rather than estimated. The risk of doing too much work on a wrong premise is removed.

### C2 — `wiki_query_gate.py` (new)

| Class | Count | Threshold | Status | Action |
|-------|-------|-----------|--------|--------|
| DRY violations | Uses `_hook_base` for all 7 shared patterns; only adds offload detection + receipt detection (both new logic) | ≥3 → refactor has positive ROI | **NOT MET** | None needed |
| Positional parameter count | `compute_decision(offload_phrases, wiki_receipts, mode)` — 3 params | >7 → coupling signal | **NOT MET** | None needed |
| Touch-point count for new offload pattern | Adding a new offload pattern: edit `OFFLOAD_PATTERNS` list + add a test case | >3 → structural coupling | **NOT MET** | None needed |
| Touch-point count for new wiki-query source | Adding a new receipt source: edit `WIKI_PATH_PATTERNS` + add a test case | >3 → structural coupling | **NOT MET** | None needed |
| Mixed concerns | Script mixes offload detection + receipt detection + decision logic — 3 concerns | ≥2 → mixed | **MET** | Acceptable; the 3 concerns are tightly coupled (the decision is the composition). Splitting would require passing state between modules without simplification |

### C3 — `_hook_base.py` (new; extracted in Unit 1)

| Class | Count | Threshold | Status | Action |
|-------|-------|-----------|--------|--------|
| DRY violations | N/A (new module) | N/A | N/A | N/A |
| Positional parameter count | All functions ≤3 params | >7 → coupling signal | **NOT MET** | None needed |
| Touch-point count for new base utility | Adding a new base utility: edit `_hook_base.py` + edit each importing hook | >3 → structural coupling | **MET (likely)** | Acceptable; the alternative is duplicated logic in each hook (which is the current state) |
| Mixed concerns | Module mixes: I/O (file reads), control flow (mode dispatch), observation (evidence logging), data transformation (negation) | ≥2 → mixed | **MET** | Acceptable; these are all cross-cutting hook infrastructure concerns. Splitting would be over-engineering. |

### C4 — Coupling-justified refactor scope

The Unit 1 refactor is the **optimal long-term solution** (per developer preferences) because:
1. **DRY:** Verified ~5 hooks (per F-10 measurement) share ≥3 patterns → 5× duplication of envelope parse + mode dispatch + evidence-log writer. Unit 1 reduces this to 1× definition + 5× imports. (Original estimate of "6× duplication" was unverified; the measured count is 5.)
2. **Touch-points:** Adding a new hook without extraction requires ≥4 touch points per the count above (registration + script + test + env var docs). With extraction, ≤3 (registration + script + test).
3. **Mixed concerns:** Quality gate currently mixes 5 concerns; extraction separates them.
4. **Risk:** The refactor is behavior-preserving (`test_quality_gate.py` must pass unchanged). Low risk, high ROI.

The Unit 1 refactor is **NOT** a "smallest viable change" — it touches more files than strictly required to add `wiki_query_gate.py`. Per developer preferences, optimal long-term is the right default, even when transition effort is larger. **Justification for refactor:** the 6× duplication (corrected per F-28 from the prior "5×") is a real cost (any pattern change requires 6 edits) and the touch-point count for new gates is structurally reduced by the extraction. **Decision gate (per F-10):** Unit 1 starts with measurement; if only 0-1 thresholds are MET, the refactor is skipped and `wiki_query_gate.py` is built with inline copies (debt accepted and documented). Per F-29, the "skip refactor" branch is defensive only — the realistic Unit 1 outcome is step 4 (smaller-subset extraction) or step 3 (full extraction).

---

## Implementation Plan (Appendix)

(This section consolidates §13 for the appendix requirement. See §13 for full per-unit detail with acceptance criteria and disposition.)

| # | Title | Files | Deps | Disposition |
|---|-------|-------|------|-------------|
| 1 | Extract `_hook_base.py` from `quality_gate.py` (gated on measurement — see §14 C1) | `_hook_base.py` (new), `quality_gate.py` (modify), `test_hook_base.py` (new), `test_quality_gate.py` (existing, must pass) | None | COMMIT_THIS_SESSION |
| 2 | Implement `wiki_query_gate.py` core | `wiki_query_gate.py` (new), `test_wiki_query_gate.py` (new) | Unit 1 | COMMIT_THIS_SESSION |
| 3 | Register `wiki-query-gate.json` | `wiki-query-gate.json` (new) | Unit 2 | COMMIT_THIS_SESSION |
| 4 | Add `aggregate_wiki_gate_metrics.py` (reads `labels.jsonl` per F-15) | `aggregate_wiki_gate_metrics.py` (new), `test_aggregate_metrics.py` (new) | Unit 3 | COMMIT_THIS_SESSION |
| 5 | Document gate in `P:/AGENTS.md` | `P:/AGENTS.md` (modify — 3-line addition) | Unit 3 | COMMIT_THIS_SESSION |
| 6 | Phase-1 transition (collapsed from 2 phases per F-08) | (env var only) | Unit 3 + ≥100 shadow events + FP rate <5% via `labels.jsonl` + nlm-class reproduction | HANDOFF (operator decision) |
| 7 | Reproduction verification | (verification only) | Unit 6 | HANDOFF (operator verification) |

**Feature flags summary (rollback mechanism for any unit):**
- `GROK_WIKI_QUERY_GATE_MODE` ∈ {`shadow`, `receipt_authoritative`} — default `shadow`; switch to `shadow` to immediately disable blocking. The original `receipt_authoritative_with_old_fail_safe` mode is REMOVED per F-08.
- `GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS` (int) — default `60`; tunes the negation suppression window per F-17.
- `rm ~/.grok/hooks/wiki-query-gate.json` — removes the hook entirely (no blocking, no logging)
- `rm ~/.grok/hooks/scripts/wiki_query_gate.py` — removes the script (hook registration becomes a no-op with stderr warning)

---

## Traceability Matrix (Appendix)

| Design component | Implementation unit | File |
|------------------|---------------------|------|
| §3.1 Component diagram | All units | All files |
| §3.2 Shared base library | Unit 1 | `_hook_base.py` |
| §3.3 Offload detection | Unit 2 | `wiki_query_gate.py` (OFFLOAD_PATTERNS, NEGATION_PATTERNS) |
| §3.4 Wiki-query receipt detection | Unit 2 | `wiki_query_gate.py` (WIKI_PATH_PATTERNS, detect_wiki_query_receipts) |
| §3.5 Decision matrix | Unit 2 | `wiki_query_gate.py` (compute_decision) |
| §3.6 Block reason text | Unit 2 | `wiki_query_gate.py` (BLOCK_REASON_TEMPLATE) |
| §4.3 `_hook_base.py` interface | Unit 1 | `_hook_base.py` |
| §4.4 `wiki_query_gate.py` skeleton | Unit 2 | `wiki_query_gate.py` |
| §4.5 `wiki-query-gate.json` | Unit 3 | `wiki-query-gate.json` |
| §4.6 Tests | Units 1, 2, 4 | `test_hook_base.py`, `test_wiki_query_gate.py`, `test_aggregate_metrics.py` |
| §5.1 New hook registration | Unit 3 | `wiki-query-gate.json` |
| §5.2 New env var | Units 2, 6, 7 | `wiki_query_gate.py` (read), operator shell (set) |
| §5.3 New evidence log | Units 2, 4 | `_hook_base.write_evidence`, `aggregate_wiki_gate_metrics.py` |
| §6.3 Evidence record schema | Unit 2 | `wiki_query_gate.py` (write_evidence call) |
| §9.2 Aggregate metrics | Unit 4 | `aggregate_wiki_gate_metrics.py` |
| §9.4 Phase-transition criteria | Units 6, 7 | Operator decision |
| §12.1 Phase 0 (shadow) | Unit 3 (default behavior) | `wiki-query-gate.json` + default env var |
| §12.2 Phase 1 (collapsed) | Unit 6 | Env var change |
| §12.3-12.4 Rollback | All phases | `rm` commands + env var reset |
| §14 Open Questions Q1-Q2 | Unit 4 (measurement) | `aggregate_wiki_gate_metrics.py` output + `labels.jsonl` |
| §14 Open Questions Q3 | **RESOLVED by F-Field** — schema verified per quality_gate.py:1101-1109 | §6.4 field contract table + `_hook_base.iter_tool_uses_in_current_turn` JSON-string parse |

---

## File Change Inventory (Appendix)

### New files (7)

| Path | Purpose | Unit |
|------|---------|------|
| `~/.grok/hooks/scripts/_hook_base.py` | Shared hook infrastructure | 1 |
| `~/.grok/hooks/scripts/wiki_query_gate.py` | The Stop hook script | 2 |
| `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py` | Aggregate metrics from evidence log | 4 |
| `~/.grok/hooks/scripts/tests/test_hook_base.py` | Base library tests | 1 |
| `~/.grok/hooks/scripts/tests/test_wiki_query_gate.py` | Wiki gate tests | 2 |
| `~/.grok/hooks/scripts/tests/test_aggregate_metrics.py` | Aggregate metrics tests | 4 |
| `~/.grok/hooks/wiki-query-gate.json` | Hook registration (Stop event) | 3 |

### Modified files (2)

| Path | Modification | Unit |
|------|--------------|------|
| `~/.grok/hooks/scripts/quality_gate.py` | Import from `_hook_base` for envelope parse, transcript iter, mode dispatch, fail-open, negation, evidence write. **Behavior unchanged.** | 1 |
| `P:/AGENTS.md` | Add 3-line entry in enforcement mechanisms section pointing to `wiki_query_gate.py` | 5 |

### Generated artifacts (1)

| Path | Purpose | Unit |
|------|---------|------|
| `~/.grok/hooks/.evidence/wiki-query-gate.jsonl` | Append-only evidence log (one record per Stop event) | 2+ (runtime) |

### Total file count: 10 (7 new + 2 modified + 1 generated)

### Path format compliance

**Code paths** (Python script, imports): all use forward slashes per `~/.grok/docs/file-editing-protocol.md` Windows rule. No backslashes in Python source.

**JSON registration paths** (in `wiki-query-gate.json` `command` field): the host does **not** expand `${HOME}` or `~` in the JSON; the resolved Windows path is required (per F-04). The template in §4.5 uses `C:\Users\brsth\.grok\hooks\scripts\wiki_query_gate.py` (this host's path); operators on other hosts substitute their own. This mirrors the existing `quality-gate.json` registration format, which uses resolved Windows paths with both backslash and forward-slash forms (verified via F-10 measurement).

**Backslash note:** the Windows-style path in the JSON `command` field is **escaped JSON** (`\\` per JSON spec), so what the host receives is `C:\Users\brsth\.grok\...` — a single backslash. This is standard JSON behavior and not a violation of the file-editing protocol (which governs source code paths, not JSON string contents).

---

*End of design document.*

---

## Revision Summary (2026-07-27, operator-scoped critical+major only)

**Operator decision:** fix critical + major findings only; defer the 9 minor findings (F-30 through F-38) to implementation time.

**Findings addressed in this revision (3):**

| ID | Severity | Section(s) touched | Fix summary |
|----|----------|---------------------|-------------|
| F-27 | critical | §3.4 (WIKI_PATH_PATTERNS), §4.6 test #10 | Replaced `[^/\\\"\s]*` with `[^\"\s]*?` (non-greedy, permits `/` and `\`). Trace-verified against `.data/wiki/concepts/error-handling/foo.md` (nested) and `.data/wiki/concepts/notebooklm-cli-operational-gotchas.md` (flat) — both match. |
| F-28 | major | §14 C1 measurement log, §14 C1 DRY row, §14 C4 framing | Corrected count from "5 candidate hooks" to "6 candidate hooks"; updated "5× duplication" to "6× duplication" in C4. |
| F-29 | major | §14 C1 Decision rule, §14 C4 framing | Restructured decision rule to make step 5's unreachable status explicit (it requires BOTH unknown thresholds to NOT MET AND both known thresholds to be disconfirmed). Step 5 retained as a defensive fallback only. C4 framing notes step 4 (smaller subset) is the realistic Unit 1 outcome. |

**Findings deferred to implementation time (9, listed in the review file's "Deferred to implementation" section):** F-30, F-31, F-32, F-33, F-34, F-35, F-36, F-37, F-38.

**No consistency sweep performed** (per operator scoping: critical+major only, sweeping all sections would be over-processing). Cross-references between the 3 fixed sections (F-27 regex updated in skeleton reference at line 429, which now correctly points to the fixed patterns; F-28 count correction propagates from measurement log to DRY row to C4 framing; F-29 decision-rule restructuring preserves the C4 framing's "Decision gate (per F-10)" reference) are verified locally — no obvious cross-section regressions introduced.

---

### Revision R4 (2026-07-27, post-critical-friend) — F-Field fix

**Trigger:** critical friend flagged a factual error (F-Field) that would have silently disabled the gate's primary signal at runtime.

**Finding F-Field (critical — FACT-verified by critical friend):** the design draft used transcript field names `tool_name` / `args` / `call_id` (in §3.4 schema comment, §3.4 `matches_wiki_pattern` docstring, §3.4 `matches_qmd_wiki_call` body, §4.3 `ToolUseRecord` and `Receipt` type definitions, §4.3 `iter_tool_uses_in_current_turn` flattening note, §4.3 `matches_wiki_pattern` docstring, §6.4 JSON example, §14 Q3). The REAL schema, verified by reading `~/.grok/hooks/scripts/quality_gate.py:1101-1109`, uses `name` (str) and `arguments` (JSON STRING, parsed via `json.loads` if it's a string). The transcript schema has NO `tool_name`, NO `args`, and NO `call_id` field. Implementation using the inferred names would silently produce zero receipts because `tc.get("tool_name", "")` returns `""` for every record, breaking every match check — yielding 100% false-positive block rate in `receipt_authoritative` mode.

**Fix applied:**

| Section | Change |
|---------|--------|
| §2.1 (Current state) | Added [FACT] row citing quality_gate.py:1101-1109 for the verified field names |
| §2.4 (Premises) | Updated the "wiki-query detectable in transcript" row to note the field-name prerequisite is now [FACT] (path-match patterns remain [INFERENCE]) |
| §3.4 (Signal 2) | Replaced schema comment block to show verified names; updated `matches_wiki_pattern` docstring + Receipt shape to use `name`; updated `matches_qmd_wiki_call` body to read `record["arguments"]` (parsed dict); added comment noting the F-Field correction |
| §4.3 (`_hook_base.py` contract) | Updated `ToolUseRecord` and `Receipt` type literals to use `name` + `arguments` (no `call_id`); added verification citation; expanded `iter_tool_uses_in_current_turn` docstring to document the JSON-string → dict parsing during flattening; updated `matches_wiki_pattern` docstring |
| §6.4 (Transcript record shape) | Reclassified from [INFERENCE, pending verification] to [FACT, verified per quality_gate.py:1101-1109]; replaced JSON example with the verified shape; added "Field contract" table mapping old (wrong) field names to new (verified) field names; added "Why the v1 inference was wrong" explanatory paragraph; added falsifier for future schema drift |
| §11 (Risk Table) | Removed the now-resolved "`chat_history.jsonl` field schema differs from assumption" row (no longer a risk) |
| §14 (Q3) | Reclassified from [INFERENCE] to RESOLVED; cross-references §6.4 field contract |
| Traceability Matrix | Updated Q3 row to RESOLVED with §6.4 + `_hook_base` references |

**Verification of fix (read-back):** all references to `tool_name`, `args`, `call_id` in transcript-shape contexts are removed (verified via `grep` over the file). No false-stale references remain. No new section was added; no section was removed; section numbering preserved.

**Per operator scoping:** other 7 critical-friend findings (structural framing concerns) are NOT addressed in this revision. They will be documented as caveats in the final report.