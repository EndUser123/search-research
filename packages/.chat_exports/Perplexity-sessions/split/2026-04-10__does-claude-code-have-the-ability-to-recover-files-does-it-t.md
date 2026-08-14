---
title: "does claude code have the ability to recover files?  Does it take a snapshot before making changes or running tools?"
date: "2026-04-10"
mode: "COPILOT"
uuid: "f4dcb257-3d91-4cc5-be1a-48f14c0cc872"
entry_count: 7
---

## Human

does claude code have the ability to recover files?  Does it take a snapshot before making changes or running tools?

## Assistant

**Yes, Claude Code supports file recovery via built-in snapshots and rollback features.**[1]

1. **File Recovery Capabilities**  
   Claude Code enables recovery of files modified by its **file edit tool** (FileEditTool), **file write tool** (FileWriteTool), or deletions through commands like **/rewind** (aliased as /checkpoint). Users select a prior conversation point, restoring files to pre-edit states from **file-history snapshots** stored in `~/.claude/file-history/{sessionId}/` (hashed filenames with versions like v1, v2). **Esc + Esc** undoes the most recent edit round instantly. Third-party tools like **claude-file-recovery** extract files from session transcripts (`{session-id}.jsonl`). Manual edits, **Bash tool** changes (e.g., `sed`), or external IDE modifications are **not tracked** or recoverable via these mechanisms.[2][3][4][1]

2. **Snapshots Before Changes or Tools**  
   **Yes**, Claude Code automatically creates **file-history snapshots** **before** modifying files during a response: (1) empty snapshot for the message, (2) backup original content to `trackedFileBackups` in session JSONL (`~/.claude/projects/.../{session-id}.jsonl`), (3) apply edits to disk. Snapshots occur **after each Claude response** for changed files (incremental, up to 100 per session, retained 30 days default via `cleanupPeriodDays`). **Bash** or non-official tools lack snapshots; git integration exists but is separate (Claude runs `git` commands on request). Disable via `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING=1` or `fileCheckpointingEnabled: false`.[4][1][2]

3. **Limitations and Risks**  
   Recovery is session-bound and **Claude-tool-specific**—no global/system snapshots. Incidents like unintended deletions (e.g., 202GB archive via Bash) highlight reliance on snapshots/git; hooks can block risky tools. Official docs emphasize **CLAUDE.md**/auto-memory for context, not recovery. Use git for long-term versioning alongside.[5][2]

## Key Takeaways  
- **Core**: Built-in snapshots enable targeted recovery; **/rewind** for granular rollbacks (code, conversation, or both).  
- **Next Step**: Test `/rewind` in a session or check `~/.claude/file-history/` for snapshots. Verify version: `claude --version` (v2.1.59+ for some features).[1][2]
Hope this helps! Let me know if you need setup examples.

## Human

can chat history be used to reconstruct files?

## Assistant

**Yes, Claude Code chat history (JSONL session logs) can reconstruct files.**[1][2]

1. **Mechanism**  
   Sessions store **append-only JSONL files** at `~/.claude/projects/<project_hash>/{session-id}.jsonl`, logging every **tool call** (e.g., **FileWriteTool**, **FileEditTool**) with **full file content**, paths, and timestamps. **grep** for filenames or parse **Write**/**Edit** calls to extract exact prior versions—even across sessions or post-deletion.[3][2][4][1]

2. **Tools and Examples**  
   - **claude-file-recovery** (CLI/TUI): Indexes sessions, extracts files at specific points; recovers **read/edit/write** history without snapshots. `~/.claude/projects/*/sessions/*.jsonl`.[5][1]
   - **Python scripts**: Parse JSONL lines for `{"tool": "FileWrite", "path": "...", "content": "..."}`; users recovered 13+ files via `grep "audit" *.jsonl` then extraction.[2]
   - **/resume <session-id>**: Loads full history (via `sessions-index.json` + JSONL); reconstruct index if corrupted.[6][7][3]
   Limits: **Bash**/**manual edits** absent unless Claude read them first; compacted sessions may truncate (but full logs pre-compaction often exist).[8]

3. **Uncertainty**  
   Official docs prioritize **snapshots** (`file-history/`) over JSONL parsing (community workaround). No built-in "export file from history" command; relies on scripting. Primary: **~/.claude** persists post-crash/OOM if not purged (30-day default).[9]

## Key Takeaways  
- **FACT**: JSONL transcripts log full file contents from tool calls → parseable for reconstruction (high confidence via user reports/tools).  
- **Next Step**: `find ~/.claude/projects -name "*.jsonl" | xargs grep -l "yourfile.txt"` → extract via Python/Recovery tool. Git complements. [2]  
Hope this helps! Let me know if you need a sample script.

## Human

show me the best practice repos that can help with this.

## Assistant

**Top repos for Claude Code file recovery and session reconstruction (prioritized by stars/features/recency).**[1][2]

1. **Primary Recovery Tool**  
   **[hjtenklooster/claude-file-recovery](https://github.com/hjtenklooster/claude-file-recovery)**: CLI/TUI extracts files from **JSONL sessions** (`~/.claude/projects/*/sessions/*.jsonl`)—reads/edits/writes at any point. Install: `pip install claude-recovery` or `uv tool install claude-recovery`. Recovered 100s of files post-deletion; indexes across sessions.[2][3][1]

2. **Rewind/Time Machine**  
   **[holasoymalva/claude-code-rewind](https://github.com/holasoymalva/claude-code-rewind)**: **/rewind** extension with timelines, diffs (`claude-rewind diff latest`), selective rollbacks. Tracks changes incrementally; preserves manual edits. Best for proactive snapshots beyond built-in.[4]

3. **Session Index Recovery**  
   Script in **[zenn.dev/tjst_t/articles/260220-claude-code-oom-session-recovery](https://zenn.dev/tjst_t/articles/260220-claude-code-oom-session-recovery?locale=en)** (adaptable): Rebuilds `sessions-index.json` from **JSONL** for lost `--resume` sessions (recovered 18+). Use in Claude or Python: scan first lines for IDs/prompts/dates.[5]

4. **Safety/Undo Hooks**  
   **[RonitSachdev/ccundo](https://github.com/RonitSachdev/ccundo)**: Granular undos from session files; integrates as hook. Routes deletes to trash (AI-aware).[6]
   GitHub **claude-code** topic: More hooks/prevention (e.g., trash wrappers).[7]

## Key Takeaways  
- **Best Start**: `claude-file-recovery` for reactive recovery; **claude-code-rewind** for prevention.  
- **Next Step**: Clone/install top repo, run `claude-recovery scan` on `~/.claude/projects`. Combine with git. (Consensus: JSONL=ultimate backup.)[1][4]
Hope this helps! Let me know if you need install/run commands.

## Human

How do these relate to claude-code-log and claude-code-history repos?  I may not have used the exact correct names.

## Assistant

**These "log/history" repos visualize/search **~/.claude JSONL sessions**—**complementary** to recovery tools (e.g., parse for **Write**/**Edit** calls before extracting).**[1][2][3]

1. **daaain/claude-code-log** (likely your **claude-code-log**): CLI/TUI → **HTML timelines** of sessions (`claude-code-log` scans `~/.claude/projects/`; `--open-browser`). Stats (tokens/dates/tools), search/filter. **Relation**: Browse history to **locate** tool calls (e.g., file writes), **then** pipe to **claude-file-recovery** for extraction. No direct recovery—viewing aid.[1]

2. **jhlee0409/claude-code-history-viewer** (likely **claude-code-history**): Desktop app (Electron?) for **chat-style** browsing/search/stats. Syntax highlights diffs/tool outputs; auto-refreshes. **Relation**: Quick-scan sessions for file ops → identify timestamps/JSONL → feed **hjtenklooster/claude-file-recovery** or scripts. Multi-AI (Gemini/Codex).[2]

3. **Relations to Prior Repos**  
   | Repo Category | Examples | Purpose | Use Chain |
   |---------------|----------|---------|-----------|
   | **Recovery** | hjtenklooster/claude-file-recovery, holasoymalva/claude-code-rewind | Extract files from JSONL/snapshots | Parse + restore |
   | **History/Log** | daaain/claude-code-log, jhlee0409/claude-code-history-viewer | Visualize/search/browse | Locate → recovery |
   | **Safety** | RonitSachdev/ccundo | Hooks/undos | Prevention |  
   **Workflow**: `claude-code-log` (find session) → grep JSONL → `claude-file-recovery extract`. All leverage same **JSONL** (logged tool calls with full content). No exact "claude-code-history" repo, but viewers match.[3][4][2][1]

## Key Takeaways  
- **Consensus**: Log viewers **upstream** of recovery—**find → extract**. Install: `pipx install claude-code-log claude-file-recovery`.  
- **Next Step**: `claude-code-log --all-projects` → inspect → `claude-recovery scan`. Git for persistence.[3][1]
Hope this helps! Let me know if you need workflow scripts.

## Human

I don't understand what you mean by complementary.

## Assistant

**"Complementary" means they **work together** in a pipeline: log/history repos **help find** relevant chat data, recovery repos **extract files** from it.**[1][2][3]

1. **Why Complementary (Step-by-Step Workflow)**  
   Claude Code logs **JSONL files** with full **tool calls** (e.g., `{"tool": "FileWrite", "path": "app.py", "content": "full code here"}`).  
   - **Step 1: Locate** (log/history repos): Search/browse 100s of sessions/JSONL lines by date/keyword/project (e.g., "grep app.py" across files).  
   - **Step 2: Extract** (recovery repos): Parse specific lines to output **actual files**.  
   **Without viewers**: Manual `find ~/.claude -name "*.jsonl" | xargs grep` → tedious. **With**: GUI/CLI narrows to 1-2 files → recovery. [1][4][2]

2. **Concrete Example**  
   `claude-code-log scan --project myapp` → lists sessions with "FileWrite: app.py v3" at timestamp X.  
   → `claude-file-recovery extract --session myapp_session123 --path app.py --version before-last` → gets file.  
   **Synergy**: Viewers handle **scale/search** (100+ sessions), recovery handles **parsing/output**. Rewind adds proactive snapshots.[3][1]

## Key Takeaways  
- **Core**: **View/find** (complementary logs) → **recover** (extraction tools). Separate but chained for efficiency.  
- **Next Step**: Run `claude-code-log --help` (if installed) or clone daaain/claude-code-log to test scan.[1]
Hope this clarifies! Let me know for a demo script.

## Human

of the 4 recovery repos, should I use one, or is there a best practice synergy from using parts of each?

## Assistant

**Use **1 primary** (claude-file-recovery) for reactive recovery + **ccundo** for prevention—**synergy via layered workflow**, not all 4 (minimal overlap).**[1][2][3][4]

1. **4 Repos Recap & Strengths**  
   | Repo | Focus | Stars/Use Case | Limits |
   |------|-------|----------------|--------|
   | **hjtenklooster/claude-file-recovery** | **Post-loss JSONL extraction** (CLI/TUI, pip install) | HN-featured, 100s recoveries [2] | Reactive only |
   | **holasoymalva/claude-code-rewind** | **/rewind extension** (timelines/diffs) | Proactive snapshots [5] | Session-bound |
   | **zenn.dev script** (session-index recovery) | Rebuild `--resume` index | OOM/crash fix [6] | Niche, manual |
   | **RonitSachdev/ccundo** | **Hooks/instant undos** (npm, previews) | Pre-delete safety, no tokens [7][1][3] | Prevention-focused |

2. **Best Practice Synergy (From Awesome Lists/Reviews)**  
   - **Primary**: **claude-file-recovery** (gold standard for disasters; "recovered my files" consensus).[8][2]
   - **Layer 1 (Prevention)**: **ccundo** hook → auto-trash/checkpoints before destructive ops.  
   - **Layer 2 (Proactive)**: **claude-code-rewind** for `/checkpoint` during sessions.  
   - **Fallback**: Index script if `--resume` broken.  
   **Workflow**: ccundo (prevent) → rewind (quick undo) → file-recovery (nuclear). Git always. **Not all 4**: 2-3 max (install cost low, ~50MB).[9][10][8]

## Key Takeaways  
- **Recommendation**: Start **file-recovery** (pipx install) + **ccundo** (npm i -g). **Synergy**: Prevention halves recovery needs.  
- **Next Step**: `pipx install claude-recovery; claude-recovery scan` → test on sample session.[2][4]
Hope this helps! Let me know for config examples.

## Human

What limitations does ccundo have compared to /rewind

## Assistant

**ccundo has more **granularity** but requires **setup/manual CLI**; **/rewind** is **instant/native** but **conversation-tied** and excludes non-Claude changes.**[1][2][3]

1. **ccundo Limitations (vs /rewind)**  
   - **Manual CLI**: `ccundo list/undo`—no hotkey (Escx2); external npm install (`npm i -g ccundo`), session parsing overhead.[2][3][4]
   - **Operation-focused**: Undoes **specific ops** (e.g., one FileWrite), but needs user select/preview; misses **conversation state**.[3][5]
   - **Setup/Edge**: Hooks may fail on **Bash/manual edits**; older repo (2025), potential bugs (e.g., list command fixes). No auto-snapshots beyond reads.[6][2]
   - **Tokens**: Zero, but **slower** than native.[4]

2. **/rewind Strengths (Built-in, v2.0+)**  
   - **Hotkey/Seamless**: **Esc Esc** or `/rewind` → pick checkpoint (auto per response), options: **code only/convo only/both**. Persists 30 days.[7][1][3]
   - **Limits**: Tied to **turns** (not arbitrary timestamps); skips **Bash/manual/IDE** changes. Defaults code+convo undo (UX issue).[8][1]

3. **Comparison Table**  
   | Aspect | ccundo | /rewind |
   |--------|--------|---------|
   | **Speed** | CLI steps | Instant hotkey [3] |
   | **Granularity** | Per-op | Per-turn/checkpoint [1] |
   | **Setup** | npm + config | Native |
   | **Convo Restore** | No | Yes |
   | **Bash Coverage** | Partial | No |
   | **Cost** | Free/local | Free |

**Synergy**: ccundo for **precise** post-session; /rewind for **flow**.[3]

## Key Takeaways  
- **ccundo Limits**: **Manual + no convo**—use if /rewind checkpoints insufficient. **Consensus**: /rewind primary (native/fast).[1][3]
- **Next Step**: Test `/rewind` (Esc Esc); if needed, `npm i -g ccundo && ccundo list`.[2]
Hope this helps! Let me know for setup.
