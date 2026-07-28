---
thread_id: dbr-english-only-hook-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T16:10:00Z
closed_at: 2026-07-27T16:45:00Z
status: closed
closed_by_session: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
closed_by_commit: 77c35fd
handoff_type: investigation
accurate_as_of_head: f3ad24c (P:) / 77c35fd (~/.grok)
parent_handoff_path: P:/docs/handoffs/qmd-non-english-20260726/HANDOFF.md
---

## CLOSURE NOTE (2026-07-27)

**RESOLVED.** Commit `77c35fd` shipped both hooks + AGENTS.md rule + 10 detection tests. The hooks are live in `~/.grok/hooks/dbr-language.json`. Detection verified: Chinese, Russian, and mixed-language content triggers; English, code blocks, blockquotes, paths, and YAML frontmatter are exempt. The remaining 273 qmd Chinese docstring lines (from the parent handoff) are the first translation remediation target.

---

# DBR hook: detect non-English output, enforce English-only, translate saved non-English material

## Objective

Build a Grok Build hook that enforces the **DBR (Don't Be Racist)** principle: the agent must use English for all output (prose, comments, logs, docstrings, documentation) unless the original source material is non-English. Non-English output excludes names (proper nouns, variable names, file paths, commands, URLs, API identifiers). When non-English is detected outside names, the hook feeds back "use English only." When saved material is found in non-English, it must be translated.

## The problem (one sentence)

The agent occasionally produces non-English output (Chinese log messages, non-English docstrings, non-English comments) which is a form of linguistic bias — the operator's framing is "it's racist not to use English" — and there is no mechanical enforcement to prevent it.

## Context: the DBR principle

**DBR = Don't Be Racist.** The operator's position (stated 2026-07-26 during the qmd Chinese log translation work): when the agent defaults to non-English for material that could be in English, it creates an accessibility barrier and reflects a linguistic bias. The workspace language is English. All agents, all documentation, all comments, all logs should be in English. The ONLY exception is when the original source material is genuinely non-English (e.g., translating a Chinese research paper, ingesting a non-English webpage).

**This is NOT about suppressing non-English languages.** It's about the agent's default behavior: the agent should default to English, not whatever language the codebase or training data biases it toward. When the agent writes Chinese log messages in a Python script (as happened with qmd — see `qmd-non-english-20260726` handoff), that's the agent imposing its language preference on the operator's workspace.

## Verified facts (with receipts)

- `[FACT]` The qmd package had 288 Chinese-language lines (runtime log messages + docstrings + comments). The operator said "It's racist not to use English" and directed translation. 15 runtime-visible log messages were translated; 273 docstring lines remain (handed off). Receipt: `P:/docs/handoffs/qmd-non-english-20260726/HANDOFF.md`.
- `[FACT]` Grok Build supports `command` and `http` hook types only (not `prompt` or `agent`). Receipt: `P:/AGENTS.md` Host runtime table + `~/.grok/docs/user-guide/10-hooks.md`.
- `[FACT]` Stop hooks can provide feedback via three mechanisms: exit-2+stderr, `decision:block` JSON, `additionalContext` JSON. Receipt: `[[grok-build-stop-hook-patterns-and-feedback-mechanism]]`.
- `[FACT]` Grok Build hook discovery merges from: the global hooks JSON config at `~/.grok/hooks/` (global), the project hooks JSON config (project), plugin hooks, compat sources. Receipt: `P:/AGENTS.md` + `~/.grok/docs/user-guide/10-hooks.md`.
- `[FACT]` The workspace already has quality_gate.py (Stop hook) and mutation_receipt.py (PostToolUse hook) as examples of the hook pattern. Receipt: `C:/Users/brsth/.grok/hooks/scripts/`.

## Requirements

### Functional requirements

1. **Detect non-English text** in agent output (response text, not tool inputs/outputs). Detection should identify Unicode scripts outside ASCII/Latin Extended (CJK, Cyrillic, Arabic, Hebrew, etc.) that appear in PROSE context — not in names.

2. **Exclude names and identifiers.** The following should NOT trigger:
   - Proper nouns (person names, place names, project names) — e.g., "Qwen3", "Zhang", "Beijing"
   - Variable names, function names, class names — e.g., `export_transcripts`, `SkillEntry`
   - File paths and URLs — e.g., `C:/Users/brsth/`, `https://arxiv.org/`
   - Command-line tokens — e.g., `python -m pytest`
   - Code blocks (fenced ``` or inline `) — code should not be language-checked
   - YAML/JSON/TOML keys — structural identifiers, not prose
   - Quoted source material — if citing a non-English source verbatim

3. **Feed back "use English only"** when non-English prose is detected. The feedback mechanism is Stop hook `additionalContext` (advisory — doesn't block, but tells the LLM for next time) or `decision:block` (blocks and requires re-translation).

4. **Translation remediation.** When saved material (files written by the agent) is found in non-English, it must be translated to English. This is a one-time cleanup + ongoing enforcement.

5. **Original-source exception.** If the source material is genuinely non-English (e.g., the agent is translating a Chinese paper, ingesting a Japanese webpage, citing a Russian quote), the non-English text is allowed. The hook should accept a marker or context signal that indicates "this is original-source non-English."

### Non-functional requirements

- **Low latency.** Language detection must be fast (<100ms per response scan). Use Unicode script ranges, not ML-based detection.
- **Low false positive rate.** The operator will disable the hook if it fires on every response due to names/paths/code. The name/identifier exclusion must be robust.
- **Non-blocking by default.** The hook should use `additionalContext` (advisory feedback) for first offense, escalating to `decision:block` only for repeat offenses or large non-English blocks.

## Design considerations

### Hook type: Stop hook (recommended)

A Stop hook fires after the agent's response is complete but before the turn ends. It can:
- Scan the response text for non-Unicode-Latin script characters
- Exclude code blocks, inline code, file paths, URLs
- If non-English prose detected: emit `additionalContext` with "DBR: non-English text detected in response. Use English only for all prose output. Names, paths, and code are exempt."

Alternative: PostToolUse hook on `write`/`search_replace` — fires when the agent writes a file. Scans the written content for non-English. This catches saved material (the qmd case) but not conversational output.

**Recommendation: both.** Stop hook for conversational output; PostToolUse hook for saved files. The PostToolUse hook is the one that would have caught the qmd Chinese log messages before they were committed.

### Language detection approach

Use Unicode script ranges, not ML:
- ASCII (0x00-0x7F): always English-compatible
- Latin Extended (0x80-0x24F, 0x1E00-0x1EFF): accents, diacritics — English-compatible
- CJK Unified (0x4E00-0x9FFF): Chinese/Japanese/Korean — trigger
- Cyrillic (0x0400-0x04FF): Russian etc. — trigger
- Arabic (0x0600-0x06FF): trigger
- Hebrew (0x0590-0x05FF): trigger
- Other non-Latin scripts: trigger

Python's `unicodedata` module can classify characters by script. A simple script-range check is fast and deterministic.

### Name/identifier exclusion

This is the hardest part. Approaches:
1. **Regex-based**: exclude text inside backticks, code fences, file paths (regex: `/[A-Z]:\\|\/`), URLs (`https?://`), quoted strings that look like identifiers.
2. **Context-based**: only check prose paragraphs (not inside code blocks, not inside YAML frontmatter, not inside JSON).
3. **Token-based**: split into tokens; skip tokens that match identifier patterns (`[a-z_][a-z0-9_]*`, `[A-Z][a-z]+[A-Z]`, file extensions, etc.).

**Recommendation:** combine 1 + 2. Strip code blocks and inline code first, then check the remaining prose for non-Latin script characters. This is robust enough for the workspace's use cases.

### Original-source exception

Options:
- **Marker-based**: the agent includes a comment like `<!-- source-language: zh -->` near non-English text. The hook checks for the marker.
- **Context-based**: if the non-English text is inside a blockquote (`>`) or a citation block, it's likely quoted source material.
- **Threshold-based**: small amounts of non-English (<20 chars) are likely names/terms; large blocks (>100 chars) are likely original prose that should be English.

**Recommendation:** start with threshold + context. If the non-English block is large (>50 chars of continuous non-Latin script) AND not inside a blockquote/code block, flag it. Small non-English fragments are likely terms/names.

## Dependencies

- **Requires:** nothing blocking. The Unicode detection is pure Python.
- **Blocks:** nothing critical.
- **Related:** the qmd-non-English handoff (273 remaining docstring lines to translate) is the test case for the saved-material translation.

## Cross-reference couplings

- `P:/docs/handoffs/qmd-non-english-20260726/HANDOFF.md` — the incident that motivated this hook
- `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py` — existing Stop hook pattern to follow
- `C:/Users/brsth/.grok/hooks/scripts/mutation_receipt.py` — existing PostToolUse hook pattern to follow
- `~/.grok/docs/user-guide/10-hooks.md` — hook discovery + event types + feedback mechanisms
- `P:/AGENTS.md` — "Host runtime: Grok Build" section (hook types: command, http only)
- `[[grok-build-stop-hook-patterns-and-feedback-mechanism]]` — Stop hook feedback mechanisms

## Existing AGENTS.md rules to add

The DBR principle should be documented as an AGENTS.md rule alongside the hook:

> **Language: English only.** All output (prose, comments, log messages, docstrings, documentation) must be in English. Non-English is allowed only when: (a) the original source material is non-English and you are translating or quoting it, or (b) the text is a proper noun, variable name, file path, command, or code identifier. Defaulting to non-English when English is available is a form of linguistic bias (DBR principle: Don't Be Racist).

## Recommended fix path

1. **Build the Stop hook** (`dbr_language_check.py`) — scans response text for non-Latin script outside code blocks/names. Uses `additionalContext` for first offense.
2. **Build the PostToolUse hook** (`dbr_file_check.py`) — scans written file content for non-English. Catches saved material before commit.
3. **Register both hooks** in the hooks JSON config at `~/.grok/hooks/dbr-language.json`.
4. **Add the AGENTS.md rule** (text above).
5. **Test on the qmd case** — run the PostToolUse hook against the remaining 273 Chinese docstring lines to verify detection.
6. **Translate the qmd docstrings** (from the qmd-non-English handoff) as the first remediation.

## Next session protocol

1. Read this handoff + the qmd-non-English handoff
2. Read `quality_gate.py` and `mutation_receipt.py` for the hook pattern
3. Read `~/.grok/docs/user-guide/10-hooks.md` for Stop + PostToolUse event contracts
4. Build `dbr_language_check.py` (Stop hook) — Unicode script detection, code-block stripping, name exclusion
5. Build `dbr_file_check.py` (PostToolUse hook) — same detection on file writes
6. Register hooks + add AGENTS.md rule
7. Test on qmd docstrings
8. Run `/check` to verify

## Last user message (verbatim)

> /handoff we need a hook that detects non-English outside of names, and implements DBR actions. DBR is don't be racist. The LLM must be told to use English only, and any material that was saved in non-English must be translated, unless the original source is non-English.

## Provenance

Written from session 019f9f4f after the qmd-non-English translation work (earlier this session: 15 runtime log messages translated, 273 docstring lines deferred). The operator's framing: "It's racist not to use English." The hook is the structural enforcement layer — the AGENTS.md rule is advisory; the hook is mechanical.
