# HANDOFF: Greenfield enforcement layer for Grok Build (LAEFS)

## 1. Objective

Build a greenfield enforcement layer for Grok Build's native hook system, implementing the three-layer LAEFS architecture (Layered Agent Enforcement for Fleet Substrate). Patterns sourced from OAP (broker shape), Earned Authority (authority semantics), and Codex (Windows substrate). **No dependency on Claude Code plugins.** The `cc-aca-authority` plugin source may be studied for design ideas, but the implementation is Grok-native from the first line.

## 2. Status

**IN PROGRESS** — claimed by session `019fcdd2` (host: grok). Created 2026-08-04.
Phase 1 gating tests COMPLETE (all 3 pass). Ready for Phase 0 or Phase 2.

## 3. Background and decision context

A post-mortem of a failed yt-is session found the root cause was "policy described in prompts; controls not active in the live path." Single-pass `/www` research (5 subagents) + deep-research workflow (6 agents) produced a comprehensive landscape of the agent control-plane enforcement field as of August 2026. Key findings:

- The field has crystallized into named frameworks (Futurum ACPF, Microsoft ACS+AGT, OAP, "Earned Authority" paper)
- No single product combines all layers — the assembly is ours to build
- The cc-aca-authority plugin (Claude Code) is DISABLED on Grok Build and should NOT be treated as a starting point
- Operator directive: greenfield IF it results in better development and outcomes (confirmed 2026-08-04)

**Full research wiki concept:** `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md`
**Workflow report (197KB, 6-agent deep research):** key findings have been folded into the wiki concept above; the full report was in session `019fcdd2` scratch directory (now ephemeral — do not rely on finding it)
**Research prompt (design doc):** `P:/tmp/research-prompt-agent-control-plane.md`

## 4. Architecture overview

```
Layer 2 — Authority Semantics (Earned Authority framework)
  • Transition envelope per workflow phase (6 mutation classes)
  • Effect ceiling — no runtime evidence may raise it
  • Session-start manifest hash (detects in-session hook edits)
  • Spawn envelope comparator (child authority ⊑ parent authority)
  • Capability mutation detector (skill load, MCP enable)
  • Wiki concept `source:` field + pre-write provenance gate

Layer 1 — Pre-Action Broker (OAP-inspired pattern, greenfield)
  • Agent passport (Ed25519-signed; status + capabilities + limits)
  • Policy packs (declarative YAML, fail-closed)
  • PreToolUse command hook (Grok-native, registered in `~/.grok/hooks/*.json`)
  • Signed audit log entries
  • ESCALATE path (hybrid: model for low-risk, watcher for irreversible)

Layer 0 — Execution Substrate (Codex sandbox primitive, Option C)
  • Synthetic SIDs per agent + WRITE_RESTRICTED token
  • Per-agent workspace ACLs (worktree = writable_roots)
  • Forensic local users (FleetSandboxUsers group)
  • NO WFP/firewall (defer to fleet egress)
  • Cleanup script from day one
```

## 5. Task packets

### Phase 0 — Foundation (1-2 sessions)

- [x] **H0.1** UPDATE existing wiki concept `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md` with LAEFS architecture details — do NOT create a new file (the concept already exists, 212 lines)
- [x] **H0.2** Reconcile three dangling wiki references (`[[earned-authority-fixed-ceiling]]`, `[[codex-windows-sandbox-pattern]]`, `[[open-agent-passport-specification]]`) — all 3 resolved as pointers to parent concept sections (content already covered, no new files needed)
- [x] **H0.3** Study `cc-aca-authority` plugin source at `P:/packages/.claude-marketplace/plugins/cc-aca-authority/` for design patterns (NOT for reuse — for understanding what a production broker looks like)

  **Findings (subagent study, session 019fcdd2):**

  **5 transferable patterns for LAEFS Layer 1 broker:**
  1. **Bootstrap + resolver path architecture** — `_bootstrap.py` + `hooks_resolver.py` decouple hook location from broker location via walk-up path resolution. LAEFS should adopt for `__file__`-relative path resolution.
  2. **Terminal-scoped state with TTL + atomic writes** — delegation state model: `.artifacts/{terminal_id}/hook_state/`, `os.replace()` atomic writes, TTL-based expiration, permission-restricted files. LAEFS should use this as the state management model (with proper concurrency control added).
  3. **Tiered risk classification with pre-compiled patterns** — ADVISORY/CONFIRM/DENY tiers with pre-compiled regex, configurable display modes, session-scoped dedup. LAEFS should adopt for policy evaluation engine.
  4. **Dual-mode hook entry points (CLI + in-process)** — `main()` for subprocess dispatch, `run(data)` for in-process. Essential for testability. LAEFS router should prefer in-process dispatch for performance.
  5. **Structured block logging** — `stop_blocks.jsonl` with structured diagnostic schema (timestamp, event, gate_name, reason, session_id, terminal_id). LAEFS should adopt as audit trail foundation.

  **10 anti-patterns to avoid:**
  1. Claude-specific coupling (CLAUDE_SESSION_ID, agent hook type, settings.json)
  2. Subprocess dispatch per hook (expensive, no shared state, 10s hardcoded timeout)
  3. Hardcoded path assumptions (P:/.claude/ baked in)
  4. Empty hooks.json placeholder (no native registration)
  5. State as flat JSON in shared filesystem (no locking, race conditions)
  6. Monolithic hook files (950-1000+ lines per hook)
  7. No policy versioning or audit trail
  8. Implicit coupling via global __lib/ modules
  9. Orphaned modules (response_intent.py only test-consumed)
  10. **No fail-closed default** — crashed hook = no enforcement (the most critical anti-pattern for LAEFS to fix)

### Phase 1 — Gating tests (1-2 sessions, MUST pass before any implementation)

**ALL THREE GATING TESTS PASSED (session 019fcdd2, 2026-08-04). Implementation may proceed.**

- [x] **G1.1** NTFS ACL test — **PASS** (100% success, 80/80 operations across 20 iterations). P:\ confirmed NTFS. icacls grant/deny/verify/remove all 100% reliable against both `P:/tmp/` and `P:/worktrees/`. Zero failures.
- [x] **G1.2** PreToolUse hook firing test — **PASS**. Measured via existing hook evidence (new hooks can't be registered mid-session — Grok loads hooks at session start only). Direct-write tools (`search_replace`, `write`): **100% firing rate** (26/26 receipts with `pre_state` populated). `run_terminal_command`: inferred reliable (same hook script/registration; receipts only written when files change). Mid-session hook registration does NOT hot-reload — requires TUI 'r' key or session restart. **Design implication**: the broker must be registered before session start, not dynamically.
- [x] **G1.3** Hook stdin JSON format confirmed. PreToolUse receives JSON on **stdin** with **camelCase** fields: `hookEventName` ("pre_tool_use"), `sessionId`, `cwd`, `workspaceRoot`, `permissionMode`, `toolName`, `toolInput`, `toolUseId`, `toolInputTruncated`, `timestamp`. Output: JSON on **stdout** — `{"decision": "allow"}` or `{"decision": "deny", "reason": "..."}`. Exit codes: 0 = allow, 2 = deny, other = fail-open. Environment vars: `GROK_SESSION_ID`, `GROK_HOOK_EVENT`, `GROK_HOOK_NAME`, `GROK_WORKSPACE_ROOT`. **IMPORTANT**: grok uses camelCase throughout stdin (not Claude's snake_case) — the broker's input parser must use `toolName`/`toolInput`, not `tool_name`/`tool_input`.

### Phase 2 — Partial Layer 0 + Layer 1 broker (3-5 sessions, REVISED by /risk assessment 2026-08-04)

**Architecture revision (session 019fcdd2, `/risk` assessment):** the original
phase ordering had full Layer 0 (synthetic SIDs + restricted tokens) as Phase 2
and Layer 1 (broker) as Phase 3. The `/risk` assessment found this was wrong —
the binary framing (full sandbox now vs. deferred entirely) missed a middle
ground: **partial Layer 0** (ACL on hooks/ to prevent hook tampering) combined
with **Layer 1 broker first** (fail-closed from day one). Full synthetic-SID
sandbox is deferred until subprocess-bypass writes are observed in pilot.

**Revised phase ordering:**

#### Phase 2a — Partial Layer 0 (1 session, no admin needed for ACL on user-owned dirs)

- [ ] **L0a.1** Apply ACL on `~/.grok/hooks/` denying write for the agent user (one `icacls` command — G1.1 proved 100% reliable). This prevents hook script tampering (R2, the highest-likelihood structural risk from the `/risk` assessment).
- [ ] **L0a.2** Verify the ACL doesn't break existing hook updates (operator can still modify hooks via elevated session)

#### Phase 2b — Layer 1 broker MVP (3-5 sessions)

- [ ] **L1.1** Capability manifest schema (YAML per agent) — declares `capabilities`, `limits`, `assurance_level`
- [ ] **L1.2** Policy pack for fleet-critical ops: `git.push`, `file.delete.across_worktree_boundary`, `subagent.spawn`, `hook.script_edit`, `agent.passport_issue`
- [ ] **L1.3** `PreToolUse_oap_broker.py` — implements Algorithm 1 (status → capability → policy → assurance → decision → audit). Register as a `~/.grok/hooks/oap-broker.json` hook (matching existing hook infrastructure — NOT config.toml).
- [ ] **L1.4** Ed25519 key generation per agent, DPAPI-encrypted
- [ ] **L1.5** Signed audit log writer — append-only to `~/.grok/hooks/.evidence/<session>/audit.jsonl`
- [ ] **L1.6** **Fail-closed default for ALL hook error paths — this is the FIRST task, not the last.** (timeout → deny; exception → deny; malformed output → deny; missing hook → deny + page operator). Per the `/risk` assessment, fail-open with no backstop is the highest-severity risk (R3).

#### Phase 2c — Layer 2 manifest hash (3-4 sessions)

- [ ] **L2.1** Session-start manifest hasher — SHA-256 of hook scripts in `~/.grok/hooks/`, policy packs, broker Python files (walk import graph). Watchdog re-hashes per tool call (not session-start only — per `/risk` M4 finding about TOCTOU windows).
- [ ] **L2.2** Capability mutation detector — fires on skill load, MCP server enable. Invalidates passport cache.
- [ ] **L2.3** Spawn envelope comparator — records parent's authority scope at session start; refuses child effects outside parent scope. Requires Scope/L_max schema.
- [ ] **L2.4** Wiki concept `source:` field (USER | WEB | SUBAGENT | INFERENCE) + `/wiki` pre-write provenance gate

#### Phase 2d — Full Layer 0 sandbox (DEFERRED — contingent on observing subprocess-bypass threats)

- [ ] **L0.1** `fleet-sandbox-uninstall.ps1` — removes local users, group, ACL grants, SID registry. Tested against clean host. **Write FIRST, before setup.**
- [ ] **L0.2** `fleet-sandbox-setup.ps1` — generates synthetic SIDs per agent, creates local users, adds to `FleetSandboxUsers` group, applies workspace ACLs
- [ ] **L0.3** `fleet-command-runner` — restricted token + per-process spawn
- [ ] **L0.4** Cross-agent isolation test
- [ ] **L0.5** Cleanup cycle test
- **Trigger to activate this phase:** subprocess-bypass writes observed in pilot (an agent writes files via obfuscated subprocess that the broker's pattern matching didn't catch)

### Phase 3 — Pilot + iterate (2-4 sessions, was Phase 5)

- [ ] **P3.1** 2-week pilot on Grok Build only
- [ ] **P3.2** Track false-positive rate from signed audit logs
- [ ] **P3.3** Track manifest hash drift frequency (if >1/week, enforcement layer being modified outside change-control)
- [ ] **P3.4** Operator feedback gate — if operator disables any layer to ship work, redesign that layer
- [ ] **P3.5** Decide fleet rollout (Codex, Antigravity) based on rejection criteria

## 5b. Risk assessment findings (session 019fcdd2, `/risk` run)

The `/risk` assessment produced 10 risks (4 HIGH) and a REVISE verdict. Key
findings that change the architecture:

1. **R3 (fail-open only mode) — HIGHEST+ severity.** During Phase 2b development,
   if the broker crashes, ALL actions are allowed with no backstop. L1.6 (fail-closed
   default) must be the FIRST implementation task, not the last.
2. **R2 (hook tampering) — HIGH/HIGH.** Any agent can edit the broker's own code
   mid-session. Partial Layer 0 (ACL on `~/.grok/hooks/`) is Phase 2a — first task.
3. **M2 (subagent chain bypass) — UNKNOWN.** Does the parent broker's PreToolUse
   fire on subagent tool calls? Needs a G1.2 extension test before pilot.
4. **Binary framing error corrected.** Original phase ordering assumed full Layer 0
   or nothing. Corrected: partial Layer 0 (ACL) + Layer 1 broker first, full sandbox
   deferred until observed threat.
5. **Threat model is unreliable-agent, not adversarial-agent.** The system runs LLM
   agents that make mistakes, not adversaries. Design for accident prevention, not
   attack resistance.

## 6. Critical design constraints (from skeptic review)

These issues MUST be addressed in the implementation, not deferred:

1. **Capabilities must have a separate issuer authority** — agents cannot self-attest their capability manifest. The passport is a request, not a grant. Issued by operator at session start.
2. **Policy packs must be in the manifest hash** — not just hook scripts. The drift detector must walk the Python import graph to find all reachable files.
3. **All hook error paths must fail closed** — timeout, exception, malformed output, missing hook. No silent fail-open.
4. **DPAPI keys must be per-agent** — not shared. Stored where other agents cannot read them.

## 7. Rejection criteria

Stop and re-evaluate if any of these fire:

- J1: Layer 1 p95 latency exceeds 500ms in production (10+ session benchmark)
- J2: ACL setup fails on >10% of test runs against `P:\` (20-run test)
- J3: PreToolUse hooks don't fire on ≥5% of tool calls (5+ session pilot)
- J4: Cleanup success rate <80% (1-month soak test)
- J5: Operator disables any layer to ship work (2-week pilot)
- J6: A simpler architecture covers the same documented threat surface

## 8. Host-specific notes

- This is **Grok Build**, not Claude Code. Hook types are `command` and `http` only (no `agent` hooks). Hook registration is via `~/.grok/hooks/*.json` files (20 active hooks verified 2026-08-04) — NOT in config.toml (which has zero hook registrations). See existing hooks in that directory for the JSON format.
- Hooks fail open on crashes/timeouts — this is documented behavior, not a bug. **During Layer 1 development, the fail-closed default in L1.6 is the ONLY backstop for hook failures.** Layer 2's manifest hash watchdog does not exist yet — do not rely on it during Layer 1 implementation.
- The 18 cc-* control plugins are DISABLED. Verify in `C:\Users\brsth\.grok\active-surface.last.md` under Disabled plugins. Do not assume any Claude Code plugin is active.
- Session ID env var: `$GROK_SESSION_ID` (not `$CLAUDE_SESSION_ID`).
- **P:\ is NTFS** (verified 2026-08-04 via `(Get-Volume P).FileSystem` — NOT ReFS as previously stated in earlier drafts). NTFS is the well-tested case for Codex's sandbox pattern; Codex's documented ACL failures were on ReFS/non-system drives.
- Phase 2 (Layer 0 substrate) requires **admin elevation** for sandbox setup. Confirm admin access is available before starting that phase.
- Codex GitHub issue numbers cited in the wiki concept (#13378, #25162, #28566, #15343, #23912, #14087) are `[UNVERIFIED]` — they came from a blog analysis, not direct verification. Verify before relying on them for design decisions.

## 9. Acceptance criteria

The MVP is complete when:
1. Agent A cannot write to Agent B's worktree (Layer 0 verified)
2. A `git push` during a discovery-phase session is blocked by the broker (Layer 1 verified)
3. Editing a hook script mid-session triggers a manifest hash alert (Layer 2 verified)
4. The cleanup script successfully removes all sandbox artifacts (Layer 0 lifecycle verified)
5. Audit log entries are Ed25519-signed and replayable (Layer 1 audit verified)
6. Layer 1 broker adds <100ms p95 latency per tool call (measured over 20+ calls)

## 10. References

- Research wiki concept: `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md`
- Research prompt: `P:/tmp/research-prompt-agent-control-plane.md`
- Workflow report: key findings folded into the wiki concept above (full 197KB report was in session `019fcdd2` scratch — ephemeral, likely inaccessible)
- OAP paper: https://arxiv.org/abs/2603.20953v1
- Earned Authority paper: https://arxiv.org/abs/2607.23586v1
- Codex sandbox: https://openai.com/index/building-codex-windows-sandbox/
- Grok Build hooks doc: `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md`
- Existing hook examples (registration format): `C:\Users\brsth\.grok\hooks\*.json` (20 files)
- TCB principle: `P:/.data/wiki/concepts/trusted-computing-base-for-agent-enforcement.md`

---

**Assignee:** session 019fcdd2 (grok)
**Session origin:** 2026-08-04 (session 019fcdd2)
**Estimated effort:** 20-30 sessions for greenfield MVP
**Authority level:** Rung 2-3 (implement + verify + review; operator-invoked close for fleet rollout)
