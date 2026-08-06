# Plan: Wiki context injector hook (UserPromptSubmit)

Created: 2026-08-06
Session: 019fd8dc
Plan type: hard plan (multi-file, hook system, reversibility ≥1.75)
Status: ready

## Goal

Build a UserPromptSubmit hook that extracts keywords from the operator's
prompt, searches the wiki concept index, and injects the top 3-5 relevant
concept summaries as `additionalContext` before the agent starts reasoning.
This prevents the failure mode where the agent researches externally without
checking the wiki first.

## Why this plan exists

Session 019fd8dc: the operator asked "can a hook modify tool input?" and the
agent ran a full `/www` research cycle instead of grepping the wiki, which
already had `[[execution-path-based-model-routing-grok-build]]` with the exact
answer. The failure recurs because "query the wiki first" is a prose rule with
~50% compliance. The structural fix is to surface wiki knowledge automatically
at the point of decision.

## Design decisions (resolved before planning)

| Question | Decision | Source |
|---|---|---|
| Mechanism | UserPromptSubmit hook (not MCP server) | Hooks fire automatically; MCP requires agent to call |
| Search backend | SQLite FTS5 over wiki frontmatter | Proven by `retro-knowledge-injector.py` (notque/claude-code-toolkit) |
| Keyword extraction | Stop-word filter, >4 chars | Both reference implementations converge |
| Injection format | `additionalContext` via stdout | Grok Build docs confirm stdout → context for UserPromptSubmit |
| Token budget | 1500 words (~2000 tokens) | retro-knowledge-injector pattern |
| Intent gating | Fire on every prompt; return empty if no hits | Avoids intent-classification model call overhead |
| Max results | 5 concepts | Token budget cap |

### Reference implementations studied

1. **notque/claude-code-toolkit** `retro-knowledge-injector.py` — FTS5 over
   learning.db, work-intent gate, ~2000 token budget, <50ms
2. **nadimtuhin/claude-token-optimizer** `user-prompt-inject-context.sh` —
   keyword scoring over docs/learnings/, 3 files max, 1500 words

### Workspace constraints honored

- **FTS5 query escaping** (`[[fts5-query-syntax-escaping-required]]`): MATCH
  queries must sanitize special characters. The plan uses quoted phrase queries
  for each keyword to avoid the "no such column" error.
- **Multi-terminal isolation** (`[[multi-terminal-isolation-stale-data-immunity]]`):
  the SQLite index is read-only from the hook's perspective; writes happen in
  the index builder, not at query time. No cross-terminal write contention.
- **Hook timeout** (Grok Build docs): default 5s for non-Stop hooks. FTS5
  queries run in <10ms; keyword extraction in <5ms. Well within budget.

## Architecture

```
Operator submits prompt
    │
    ▼
UserPromptSubmit hook fires
    │
    ├── 1. Read prompt from stdin JSON (field: .userPrompt or .prompt)
    ├── 2. Extract keywords (split, filter stop words, >4 chars, max 8)
    ├── 3. Query SQLite FTS5 index (wiki_concepts table)
    │      SELECT title, summary, tags, path
    │      FROM wiki_concepts_fts
    │      WHERE wiki_concepts_fts MATCH :keyword_query
    │      ORDER BY rank
    │      LIMIT 5
    ├── 4. Format results as additionalContext string
    │      "Wiki concepts relevant to your prompt:\n
    │       - [[title]] — summary (path)\n ..."
    ├── 5. Output as hookSpecificOutput.additionalContext via stdout
    │
    ▼
Agent receives prompt + wiki context injected
```

### Files to create

| # | File | Purpose |
|---|------|---------|
| 1 | `~/.grok/hooks/scripts/wiki_context_injector.py` | Hook script: keyword extraction + FTS5 query + context formatting |
| 2 | `~/.grok/hooks/scripts/wiki_index_builder.py` | Index builder: reads wiki frontmatter → writes SQLite FTS5 index |
| 3 | `~/.grok/hooks/UserPromptSubmit_wiki_context.json` | Hook registration JSON |
| 4 | `~/.grok/hooks/tests/test_wiki_context_injector.py` | Unit tests for the hook |

### Files to modify

None. This is additive — new hook, new scripts, new index.

## Tasks

### Track A: Index builder (enabling infrastructure)

### Task 1: Write the wiki index builder

Create `~/.grok/hooks/scripts/wiki_index_builder.py`.

**What it does:**
- Walks `P:/.data/wiki/concepts/*.md`
- Parses YAML frontmatter (title, summary, tags, created, verification, relations)
- Creates a SQLite database at `P:/.data/wiki/_state/wiki-concepts-index.db`
- Table: `wiki_concepts (title TEXT, summary TEXT, tags TEXT, path TEXT, created TEXT, verification TEXT)`
- FTS5 virtual table: `wiki_concepts_fts` indexed on (title, summary, tags)
- Idempotent: drops + recreates on each run
- Logs: concept count, index size, build time

**Design notes:**
- Uses `sqlite3` (stdlib, no dependencies)
- Uses `fts5` extension (bundled with Python 3.9+ sqlite3 on Windows)
- Frontmatter parser: reuse the lightweight parser from `epistemic_debt.py`
  (lines 60-90), NOT PyYAML (avoid dependency)
- Path stored as relative to `P:/.data/wiki/concepts/` for portability

**Test:** `test_wiki_index_builder.py`
- Create 3 temp wiki concepts with known frontmatter
- Run the builder
- Query the FTS5 index for a known keyword
- Assert: correct concept returned with correct fields

**Run:**
```bash
python ~/.grok/hooks/scripts/wiki_index_builder.py
```

- [ ] Task 1 complete

### Task 2: Test the index builder against real wiki

**Run:**
```bash
python ~/.grok/hooks/scripts/wiki_index_builder.py
# Verify: index created at P:/.data/wiki/_state/wiki-concepts-index.db
# Verify: concept count > 100 (we have hundreds of wiki concepts)
# Verify: FTS query for "model routing" returns execution-path-based-model-routing-grok-build
```

- [ ] Task 2 complete

### Track B: Hook script

### Task 3: Write the hook script

Create `~/.grok/hooks/scripts/wiki_context_injector.py`.

**What it does:**
1. Reads JSON from stdin (with 3s timeout — fail open)
2. Extracts the user's prompt from `.userPrompt` or `.prompt` field
3. Tokenizes: split on whitespace, lowercase, filter:
   - Remove stop words (built-in set of ~50 common English words)
   - Keep tokens >4 characters
   - Keep max 8 keywords
4. Builds FTS5 query: each keyword wrapped in double quotes (phrase query),
   joined with OR — `("routing" OR "model" OR "hook")`
   This avoids the FTS5 special-char escaping bug documented in
   `[[fts5-query-syntax-escaping-required]]`.
5. Queries `P:/.data/wiki/_state/wiki-concepts-index.db`:
   ```sql
   SELECT title, summary, path
   FROM wiki_concepts_fts
   WHERE wiki_concepts_fts MATCH ?
   ORDER BY rank
   LIMIT 5
   ```
6. Formats results:
   ```
   Wiki concepts relevant to your prompt (check these before researching externally):
   - [[title]] — summary excerpt (file:///P:/.data/wiki/concepts/<path>)
   - [[title]] — summary excerpt (file:///P:/.data/wiki/concepts/<path>)
   ```
   Token budget: truncate summaries to fit within 1500 words total.
   If no results: output nothing (silent — zero noise when wiki has nothing).
7. Outputs as JSON on stdout:
   ```json
   {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
   ```
8. If index DB doesn't exist: output a one-line note suggesting to run the
   index builder. Fail open — never block the prompt.

**Design notes:**
- No external dependencies (stdlib only: json, sqlite3, re, sys)
- Performance target: <50ms total (keyword extraction <5ms, FTS5 query <10ms)
- Fail-open: any exception → exit 0 with no output (prompt proceeds normally)
- Stop-word list: hardcoded set of ~50 words (the, a, an, is, are, was, were,
  how, what, why, when, where, who, can, do, does, did, should, would, could,
  will, this, that, these, those, it, its, for, from, with, and, or, but, not,
  have, has, had, been, being, to, of, in, on, at, by, we, you, they, me)
- Keyword deduplication: if "routing" and "router" both appear, keep only the
  first (crude stem dedup)

**Test:** `test_wiki_context_injector.py`
- Mock stdin JSON with a prompt containing "model routing hook"
- Run the hook script
- Assert: output JSON contains `hookSpecificOutput.additionalContext`
- Assert: additionalContext contains "model-routing" or "execution-path" (known wiki concept)
- Mock stdin with a prompt containing "asdf qwerty zxcvbn" (no wiki matches)
- Assert: output is empty (no injection when no hits)
- Mock stdin with index DB missing
- Assert: output is empty or contains suggestion to build index (fail open)

**Run:**
```bash
python ~/.grok/hooks/scripts/wiki_context_injector.py < test_input.json
```

- [ ] Task 3 complete

### Track C: Hook registration + integration

### Task 4: Register the hook

Create `~/.grok/hooks/UserPromptSubmit_wiki_context.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.grok/hooks/scripts/wiki_context_injector.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Note:** Grok Build reads `~/.grok/hooks/*.json` on session start. The hook
will be active next session. To test mid-session, restart the session or
verify via `/hooks`.

- [ ] Task 4 complete

### Task 5: Integration test (manual)

**Steps:**
1. Build the index: `python ~/.grok/hooks/scripts/wiki_index_builder.py`
2. Register the hook (Task 4)
3. Start a new session (or restart)
4. Type a prompt: "can a PreToolUse hook modify tool input?"
5. Verify: the agent's context includes wiki hits about
   `execution-path-based-model-routing-grok-build` before it starts reasoning
6. Type a prompt with no wiki relevance: "what's the weather"
7. Verify: no wiki context injected (silent on no hits)

**Pass criteria:**
- Relevant wiki concepts appear in agent context for relevant prompts
- No injection for irrelevant prompts
- Hook executes in <100ms (no perceptible delay on prompt submission)

- [ ] Task 5 complete

### Task 6: Wiki index auto-refresh (scheduled task)

Add a scheduler entry or SessionStart hook to refresh the index when stale:
- Check if `wiki-concepts-index.db` mtime > 24h old
- If stale, re-run the index builder
- This ensures newly written wiki concepts appear in the index

**Options:**
- A: `scheduler_create` with 1h interval running the builder
- B: SessionStart hook that checks mtime and rebuilds if stale

**Recommendation:** Option B (SessionStart) — no ongoing scheduler overhead,
runs once per session, catches wiki writes from any session.

- [ ] Task 6 complete

## Acceptance criteria

1. `wiki_index_builder.py` creates a valid FTS5 index from wiki frontmatter
2. `wiki_context_injector.py` extracts keywords, queries the index, and outputs results as `additionalContext`
3. Hook fires on every UserPromptSubmit and injects relevant wiki concepts
4. No injection when wiki has no relevant concepts (silent on miss)
5. Hook executes in <100ms (no perceptible delay)
6. Hook fails open on any error (never blocks the prompt)
7. Tests pass: `pytest ~/.grok/hooks/tests/test_wiki_context_injector.py`
8. Index auto-refreshes on session start if stale

## Falsifier

The hook is proven useless if: after deployment, the agent still ignores
injected wiki context and researches from scratch. That would indicate the
problem is "agent doesn't read additionalContext," not "agent doesn't search
wiki" — requiring a different fix (likely a Stop hook checking whether the
answer contradicts injected knowledge).

## Anti-scope (what we are NOT building)

- No MCP server (hook is the right mechanism — fires automatically)
- No intent classification model (fire on every prompt; silent on no hits)
- No semantic/embedding search (FTS5 keyword search is sufficient and 100x faster)
- No modification to existing skills (this is additive infrastructure)
- No blocking gate (nudge only, never blocks the prompt)
