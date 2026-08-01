---
title: "Conversation Distillation for LLM Review — Filtering & Tool-Call Simplification Techniques"
created: 2026-07-27
source: session-019fa48a (/www research on building a review-packet-export skill)
tags: [transcript, distillation, context-engineering, skill-design, review, grok-sessions]
summary: >
  Techniques and reusable code for exporting a filtered, tool-simplified view of a
  Grok session conversation (chat_history.jsonl) into a review-ready markdown file
  for another LLM. Covers: the reusable AAR transcript parser, relevance-filtering
  strategies (keep wiki/skill turns), tool-call path extraction (collapse tool_use to
  ToolName(path)), and the review-packet output format. Grounded in Anthropic's
  context-engineering principles (tool-result clearing, just-in-time identifiers,
  smallest-set-of-high-signal-tokens) and Sierra's two-tier agent-trace design.
cognitive_load: 3
verification: source-confirmed
host: grok
---

# Conversation Distillation for LLM Review

## Decision context (why this research was needed)

**The real question behind the research:** the operator wants to hand the *full
conversation on a single topic* (e.g. a wiki/skill design discussion) to a *different
LLM* for review — without dumping the entire session (which contains unrelated turns,
giant tool outputs, and system noise). The practical need: a reusable skill that (1)
filters a Grok session down to turns relevant to a topic, (2) simplifies verbose tool
I/O to just the filename/path, and (3) writes a clean markdown file another model can
read cold.

**What the research changed:** the naive approach would be "summarize the conversation."
The research refuted that — Anthropic, Sierra, and multiple compaction-failure sources
agree that summarization *loses subtle but critical context whose importance only
becomes apparent later*. The correct shape is **selection + tool-result clearing** (keep
full prose of relevant turns; collapse only the tool I/O), not summarization. The skill
should be a *filter/collapser*, not a *summarizer*.

---

## The reusable foundation (do NOT reinvent)

The AAR skill already ships a deterministic parser for `chat_history.jsonl`:

- **`~/.grok/skills/aar/__lib/transcript_parser.py`** — `parse_transcript(path) → Transcript`
- **`~/.grok/skills/aar/__lib/event_model.py`** — typed `Event`, `ToolCall`, `Role`,
  `Transcript`, `ParseStats` (frozen dataclasses)

The parser already handles everything the new skill needs:
- All five role types: `system`, `user`, `assistant`, `reasoning`, `tool_result`
- `assistant.tool_calls` → `ToolCall(id, name, arguments(dict), arguments_raw(str))`
- `tool_result.tool_call_id` joined back to the producing `ToolCall.id`
- Distinguishes synthetic user messages (`project_instructions`) from real prompts
- Classifies source completeness (COMPLETE / PARTIAL / UNVERIFIED) via compaction markers
- Forward-slash paths, honest accounting (`ParseStats.reconciles()`)

**Confirmed record shapes** (from session 019fa48a, verified against live JSONL):

```
assistant w/ tools:  {type:"assistant", content:"...", tool_calls:[
                        {id:"call_...", name:"read_file",
                         arguments:"{\"target_file\":\"C:\\\\...\\\\prompt_0.txt\"}"},
                        ...], model_id:"grok-4.5"}
tool_result:         {type:"tool_result", tool_call_id:"call_...",
                        content:"1→<user_query>\n/www ..."}
user:                {type:"user", content:[{type:"text",text:"..."}],
                        synthetic_reason:"project_instructions"}   # or real prompt
```

`arguments` is a **JSON string** with tool-specific keys; the AAR parser already parses
it into `ToolCall.arguments` (dict). The new skill works off the parsed dict — no JSON
parsing needed.

**Skill-design implication:** the new skill imports `transcript_parser` and operates on
the typed `Transcript.events`. It adds two layers the AAR parser does not provide:
(1) a **relevance filter**, (2) a **tool-call simplifier / renderer**. Both are pure
functions over `Event` objects.

---

## The three named techniques (from Anthropic, Sep 2025)

The skill is a concrete application of three techniques Anthropic names explicitly in
*Effective context engineering for AI agents*:

### 1. Tool-result clearing
> "Once a tool has been called deep in the message history, why would the agent need
> to see the raw result again? One of the safest, lightest-touch forms of compaction
> is tool result clearing."

For a *review* packet (not live agent context), go further: collapse the tool **call**
too, keeping only `ToolName(path)`. The reviewer sees *what file was touched*, not the
full argument blob or the returned content. This is the single highest-leverage
compression — tool I/O is 60-90% of session bytes in coding sessions.

### 2. Just-in-time identifiers
> "Agents maintain lightweight identifiers (file paths, stored queries, web links) and
> use these references to dynamically load data at runtime."

A file **path** is the perfect low-token handle. The reviewer (another LLM) can request
the full file if it matters; the path alone tells it *what* was read/written/grepped.
Keep the path, drop the payload.

### 3. Smallest set of high-signal tokens (the governing principle)
> "Find the smallest possible set of high-signal tokens that maximize the likelihood
> of some desired outcome."

For a review packet, "desired outcome" = "the reviewer understands the design
discussion and can critique it." That requires the **prose** (user asks + assistant
reasoning/answers), not the tool payloads. Keep full prose of relevant turns; collapse
everything mechanical.

---

## Code pattern — tool-call path extraction

The `arguments` dict has predictable path keys per tool name. A lookup table is the
optimal long-term solution (DRY, one place to extend when a new tool is added):

```python
from __future__ import annotations
from pathlib import PurePath
from event_model import ToolCall  # from aar/__lib

# tool name -> ordered list of argument keys that carry a path/file identifier.
# First match wins; extend this table as new tools appear.
PATH_KEYS: dict[str, tuple[str, ...]] = {
    "read_file":          ("target_file",),
    "write":              ("file_path",),
    "search_replace":     ("file_path",),
    "list_dir":           ("target_directory",),
    "grep":               ("path",),
    "run_terminal_command": (),  # path is buried in `command`; special-case below
    "spawn_subagent":     ("cwd",),
    "image_gen":          (),
    "image_edit":         (),
}

def _short(path_str: str) -> str:
    """Reduce a verbose absolute path to its filename + immediate parent, if any."""
    if not path_str:
        return ""
    p = PurePath(path_str.replace("\\", "/"))
    parts = p.parts
    if len(parts) >= 3:
        return f".../{parts[-2]}/{parts[-1]}"
    return p.name or path_str

def summarize_tool_call(tc: ToolCall) -> str:
    """Render a tool call as `ToolName(short/path)` — the review-packet form."""
    keys = PATH_KEYS.get(tc.name, ())
    handles: list[str] = []
    for k in keys:
        v = tc.arguments.get(k)
        if isinstance(v, str) and v:
            handles.append(_short(v))
    # Special: extract paths from a shell command (best-effort, regex).
    if tc.name == "run_terminal_command":
        import re
        cmd = tc.arguments.get("command", "")
        paths = re.findall(r'[A-Za-z]:[\\/][^\s\'"]+|P:/[^\s\'"]+|~/[^\s\'"]+', cmd)
        handles += [_short(x) for x in paths[:2]]  # cap at 2 to stay terse
    label = " | ".join(dict.fromkeys(handles))  # dedupe, preserve order
    return f"{tc.name}({label})" if label else f"{tc.name}(...)"
```

**Why a lookup table beats reflection/guessing:** the tool schemas are stable and few
(<20 distinct tools in a coding session). A table is auditable (the reviewer can see
exactly which key is treated as "the path"), extensible (one line per new tool), and
has zero false positives. This satisfies the workspace's "optimal long-term over
minimal-diff" rule — a table is both simpler *and* more correct than heuristic
path-sniffing.

---

## Code pattern — relevance filtering (the design decision)

This is the genuinely uncertain layer. Four strategies, in increasing cost/quality:

| Strategy | Cost | Quality | When |
|---|---|---|---|
| **(a) Semantic term-set on text** | free (orchestrator-side) | high | **default** — orchestrator expands topic → term set |
| **(b) Path-based (tool args)** | free | high | structural signal — paths name what was touched |
| **(c) Context-window expansion** | free | — | keep N turns around each hit (bias toward recall) |
| **(d) Per-turn LLM classification** | 1 call/turn | very high | opt-in only — `--llm-filter` for ambiguous cases |

**Recommended hybrid (default):** orchestrator-LLM expands the topic phrase to a
term set (a), + path-based signal (b), + context-window padding (c). This is
**bias-toward-recall**: better to include a borderline turn than miss a relevant
one. The header reports kept/excluded counts so the operator can widen/narrow.
(d) only when the deterministic pass returns too few/too many turns.

### Why semantic expansion, not regex (operator correction 2026-07-27)

The original proposal used `--topic <regex>`. The operator rejected this:
> "It will be impossible for me to tell you all the patterns. You need to be
> intelligent and adaptive. Maybe use NLP as a pre-pattern expander, or you as
> the orchestrating LLM with perfect understanding expand the requested topic to
> similar meanings so we actually capture a non-brittle result. I'd rather
> capture more info than less without being silly."

Regex is the wrong abstraction for natural-language topics. The orchestrating
LLM (the agent running `/packet`) has the session in context and can expand a
topic phrase into a term set far better than any regex. This is the same pattern
qmd uses internally (`QueryExpander().expand(query)` produces lex/vec/hyde
variants via an LLM before search — see `qmd/core/expansion.py`). `/packet`'s
expansion is even richer because the orchestrator knows the session's domain,
not just the query.

**"Without being silly" controls:**
- Cap expansion at ~20-30 terms (generous, bounded)
- Word-boundary matching (no substring false positives like "auth" in "author")
- The expansion is shown in the packet header so the operator can sanity-check
- Domain-aware: the orchestrator expands "auth" differently in a security
  session vs a writing session (it has the session in context)

```python
import re
from event_model import Event, Role

# The term set is built by the orchestrating LLM at invocation time, NOT hardcoded.
# Example: operator runs `/packet auth` -> orchestrator expands to:
#   {"auth", "authentication", "authorization", "login", "session",
#    "token", "credential", "OAuth", "SSO", "JWT", "bearer", "API key",
#    "permission", "identity", "provenance"}
# Example: operator runs `/packet "wiki design"` -> orchestrator expands to:
#   {"wiki", "design", "concept", "schema", "frontmatter", "SCHEMA.md",
#    "/wiki", ".data/wiki/", "[[", "decision context", "falsifier"}
# Example: no --topic -> orchestrator infers from the first real user prompt.
# Fallback: qmd's QueryExpander (less domain-aware, still semantic).

WIKI_PATH_RE   = re.compile(r"/\.data/wiki/|\.data[\\/]wiki", re.I)
SKILL_PATH_RE  = re.compile(r"/\.grok/skills/|/\.agents/skills/|SKILL\.md", re.I)

def _text_of(ev: Event) -> str:
    return (ev.text or "")

def _tools_relevant(ev: Event) -> bool:
    for tc in ev.tool_calls:
        blob = " ".join(str(v) for v in tc.arguments.values())
        if WIKI_PATH_RE.search(blob) or SKILL_PATH_RE.search(blob):
            return True
    return False

def is_relevant(ev: Event) -> bool:
    if ev.role is Role.USER and ev.synthetic_reason:
        return False  # drop injected project_instructions, system noise
    if ev.role is Role.SYSTEM:
        return False
    if _text_of(ev) and _TOPIC_RE.search(_text_of(ev)):
        return True
    if _tools_relevant(ev):
        return True
    return False

def select_with_context(events: list[Event], *, pad_before: int = 1, pad_after: int = 2) -> list[Event]:
    """Keep relevant turns + a window of surrounding turns for conversational flow.

    tool_result events are kept iff their producing tool_call was kept (join on id)."""
    hits = {i for i, ev in enumerate(events) if is_relevant(ev)}
    keep: set[int] = set()
    for i in hits:
        keep.update(range(max(0, i - pad_before), min(len(events), i + pad_after + 1)))
    # propagate: keep tool_results for kept tool_calls
    kept_call_ids = {tc.id for i in keep for tc in events[i].tool_calls}
    for i, ev in enumerate(events):
        if ev.role is Role.TOOL_RESULT and ev.tool_call_id in kept_call_ids:
            keep.add(i)
    return [events[i] for i in sorted(keep)]
```

**Why keep a context window (strategy c):** a relevant turn often references the *prior*
turn ("yes, do that") or the *next* turn (the tool result that confirms it). Dropping
adjacent turns breaks coherence. The `pad_before`/`pad_after` defaults (1/2) are
conservative; tool_results are kept only if their producing call was kept, so no orphan
results leak in.

---

## Output format — the review packet (Sierra two-tier)

Borrow Sierra's *Agent Traces* principle: **scan quickly, drill down if needed.** The
packet has three zones:

```markdown
# Review packet — <topic>
**Source session:** 019fa48a (chat_history.jsonl)
**Filter:** wiki + skill discussions; tool I/O collapsed to path handles
**Scope:** 47 of 312 turns kept (15%). 265 turns excluded (non-topic / system noise).

---
## Conversation

### [user] (turn 4)
I want to add a `/www` validation step...

### [assistant] (turn 5)  *grok-4.5*
Let me check the existing validator...
- read_file(.../www/scripts/validate_disconfirmation.py)
- grep("disconfirm", .../skills/www)

The validator already covers Phase 2...  *(full prose preserved)*

### [tool_result — omitted] (turn 6)
`read_file → 84 lines returned`

### [assistant] (turn 7)  *grok-4.5*
... *(full prose)*

---
## Filter stats
- Kept by keyword: 31 turns
- Kept by path-signal: 9 turns
- Kept by context-window: 7 turns
- Excluded: 265 (system prompts, injected instructions, unrelated tool churn)
```

**Rules:**
- **Prose is verbatim** — never paraphrase user/assistant text. Reviewers need the
  actual reasoning, not a summary (the disconfirmation finding: summarization loses
  subtle context).
- **Tool calls → one line each**, `ToolName(short/path)`.
- **Tool results → omitted or one-line stub** (`read_file → 84 lines returned`). The
  reviewer does not need the file contents in the packet; the path tells them where to
  look.
- **Reasoning turns**: keep if present and relevant (they show *why* the model chose a
  path — high value for review).
- **Header carries scope stats** so the reviewer knows what was excluded, not just what
  was kept.

---

## Operator-confirmed build decisions (2026-07-27)

Two questions raised by the `/tp` critique that the operator resolved explicitly.
These are **build-spec decisions**, not open options.

### Decision 1: Redaction is ON by default (blocking requirement)

**Question:** "Will packets only ever be handed to LLMs you control?"
**Operator answer:** Intent is internal LLMs, but external web-hosted LLMs will happen sometimes.

**Build spec:** the skill MUST redact by default.
- Default behavior: regex-based secret patterns (`sk-`, `ghp_`, `xoxb-`, `Bearer `,
  `API_KEY=`, `-----BEGIN`, `AKIA...`, `eyJ` JWT prefixes) detected and masked in
  user prompts AND assistant reasoning AND tool arguments before writing the packet.
- Opt-out: `--no-redact` flag for trusted-local cases (the operator accepts the risk).
- SKILL.md warning surfaces the redaction count in the header so the operator knows
  what was masked ("3 secrets redacted in 2 turns").
- Redaction is **preservation, not deletion** — the masked content is replaced with
  `[REDACTED:api-key]`, not removed, so the reviewer sees that *something* was there.

**Why this matters:** packets are exported verbatim. A session that contains an API
key in a `curl` command, a token in a config edit, or credentials in a prompt
inherits that content unchanged. For internal LLMs this is low risk; for external
web-hosted LLMs it's an exfiltration surface. Default-on redaction is the
defense-in-depth fix.

### Decision 2: Two-file output stays (blocking requirement)

**Question:** "One-file output or two-file (`_sig` + `_full`) split?"
**Operator answer:** Two-file split is required.

**Build spec:** the skill produces both files, parallel to `/gitpack`:
- **`<name>_sig.md`** — compact, scannable: packet header (source session, filter
  spec, kept/excluded counts, redaction count), the topic term set used, and a
  **turn index** (one line per kept turn: `[N] role — one-line summary`). No full
  prose. Purpose: the reviewer (or the operator) scans this to decide whether to
  read the full packet.
- **`<name>_full.md`** — same header + turn index + the full verbatim conversation
  (filtered turns, collapsed tool calls, redacted secrets). Purpose: the actual
  review payload.

**Why two files for conversations** (operator-confirmed, not cargo-culted from
`/gitpack`): the `_sig.md` answers "is this packet worth reading?" without making
the reviewer load 50KB of prose. The turn index is the conversation analog of
`/gitpack`'s signature TOC — function/class signatures for code, one-line turn
summaries for conversation. Both let the consumer decide whether to drill in.

**Turn index format (in `_sig.md`):**
```
## Turn index (47 of 312 turns kept)

[4]   user       — "I want to add a /www validation step..."
[5]   assistant  — checks existing validator, proposes Phase 3 gate
[7]   assistant  — implements validator, runs test
[9]   user       — "the gate needs to fire on disconfirmation, not just presence"
...
```

Each line: turn number, role, one-line LLM-generated summary (≤80 chars). The
summaries are produced during the same orchestrator pass that builds the term set
— the orchestrator has the session in context, so summarization is free.

---

## Disconfirmation pass — what could make this wrong

**Confirmed caveat (Anthropic + 4 independent sources):** *"overly aggressive
compaction can result in the loss of subtle but critical context whose importance only
becomes apparent later."* The skill's design counters this by **selecting, not
summarizing** — full prose of relevant turns is preserved verbatim. The risk surface
narrows to two places:

1. **The relevance filter drops a turn that mattered.** Mitigation: (a) keep a context
   window around hits, (b) the header reports the exclusion count so the operator can
   widen the filter, (c) `--no-filter` escape hatch exports the whole session.
2. **Tool-call path extraction misses a non-standard argument.** Mitigation: the lookup
   table is explicit and auditable; unknown tools render as `ToolName(...)` rather than
   silently dropping.

**Not refuted:** the core shape (selection + tool-clearing, not summarization) held
across every source. No source recommended summarizing prose for a review packet.
This is an instance of the [[reactive-pattern-matching-and-closure-pressure]]
pattern — the first plausible approach (summarize) felt sufficient but would have
lost subtle context.

---

## Skill skeleton — `/packet`

**Name rationale:** parallels `/gitpack` (used in the Claude environment for packaging
git state into a portable form). `/packet` does the same for conversation state —
packages a filtered, tool-simplified view of a session into a portable file another LLM
can read cold. The mnemonic transfers.

**Domain placement:** Domain 8 — Knowledge/Memory (per
[[skill-domain-map]]). Sibling to `/handoff`: both export session state for another
consumer. `/handoff` writes a summary; `/packet` writes a filtered verbatim extract.
Different mechanism, same "export-for-continuation" purpose.

```
~/.grok/skills/packet/
  SKILL.md            # invocation: /packet [session-id|path] [--topic <pat>] [--llm-filter] [--no-filter]
  __lib/
    filter.py         # is_relevant(), select_with_context()  — from this concept
    render.py         # summarize_tool_call(), render_packet() — from this concept
    cli.py            # parse_transcript() reuse → filter → render → write .md
  scripts/
    export.py         # entrypoint: python export.py <session> --topic wiki,skill --out P:/tmp/packet-<topic>.md
```

**Reuse contract:** `sys.path.insert(0, "~/.grok/skills/aar/__lib")` then
`from transcript_parser import parse_transcript`. The AAR parser is the single source
of truth for JSONL → Events; the new skill never re-parses JSONL itself.

**Alternatives considered:**
- (1) extend the AAR skill with an `--export-review` mode → rejected: AAR's purpose is
  retrospective analysis, not export; mixing concerns bloats it.
- (2) extend `/close` → rejected: close is session-close accounting, not topic export.
- (3) name as `/brief` (legal/informational brief) → operator chose `/packet` for the
  `/gitpack` mnemonic. `/brief` is the second-best candidate if `/packet` doesn't stick.
- (4) name as `/distill-review` → rejected: per operator feedback, "doesn't evoke
  anything to remember it."

A standalone skill that *imports* the AAR parser is the optimal long-term shape: single
parser, separate consumers.

---

## Citations

- **Anthropic — Effective context engineering for AI agents** (Sep 29, 2025).
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  — source for "tool result clearing", "just-in-time identifiers", "smallest set of
  high-signal tokens", compaction, structured note-taking, sub-agent architectures.
- **Sierra — Agent Traces: getting to the fix, fast** (Oct 1, 2025).
  https://sierra.ai/blog/agent-traces — source for the two-tier trace design
  (scan quickly / drill down) and "show the decision tree, not raw prompts."
- **Meilisearch — What is context distillation in AI** (Jun 23, 2026).
  https://www.meilisearch.com/blog/context-distillation — the select → filter →
  compress → provide pipeline; technique comparison (prompt-based, synthetic-data,
  on-policy, iterative).
- **Morph — Context Compaction: Delete Noise, Keep Signal** (Mar 13, 2026).
  https://www.morphllm.com/context-compaction — "delete low-signal tokens rather than
  rewriting them" (supports selection-over-summarization).
- **Wang, Y. — Context Compression for LLM Agents: A Survey** (2026).
  https://www.preprints.org/manuscript/202605.2065 — failure-mode survey confirming
  over-aggressive compaction loses critical constraints.
- **Workspace (verified this session):**
  - `~/.grok/skills/aar/__lib/transcript_parser.py` — reusable parser (see [[agentic-sdlc-skill-lifecycle-architecture]] for the skill lifecycle this fits into)
  - `~/.grok/skills/aar/__lib/event_model.py` — typed Event/ToolCall/Transcript
  - `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl` — source format

## Falsifier

This concept is wrong if, within 6 months: (a) the AAR parser is replaced and the new
skill's reuse contract breaks; (b) filtering by keyword+path consistently misses
relevant turns such that reviewers reject packets as incomplete; (c) a future Grok
format change makes `arguments` non-JSON-string (breaking the path-extraction table). If
(c) fires, the AAR parser will catch it first (it sets `ToolCall.parse_error`).
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
