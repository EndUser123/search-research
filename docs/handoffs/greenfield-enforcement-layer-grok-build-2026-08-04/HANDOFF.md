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

- [ ] **H0.1** UPDATE existing wiki concept `P:/.data/wiki/concepts/agent-control-plane-enforcement-architectures-2026.md` with LAEFS architecture details — do NOT create a new file (the concept already exists, 212 lines)
- [ ] **H0.2** Reconcile three dangling wiki references (`[[earned-authority-fixed-ceiling]]`, `[[codex-windows-sandbox-pattern]]`, `[[open-agent-passport-specification]]`) — either lift sections or close with pointer to the parent concept
- [ ] **H0.3** Study `cc-aca-authority` plugin source at `P:/packages/.claude-marketplace/plugins/cc-aca-authority/` for design patterns (NOT for reuse — for understanding what a production broker looks like)

### Phase 1 — Gating tests (1-2 sessions, MUST pass before any implementation)

**ALL THREE GATING TESTS PASSED (session 019fcdd2, 2026-08-04). Implementation may proceed.**

- [x] **G1.1** NTFS ACL test — **PASS** (100% success, 80/80 operations across 20 iterations). P:\ confirmed NTFS. icacls grant/deny/verify/remove all 100% reliable against both `P:/tmp/` and `P:/worktrees/`. Zero failures.
- [x] **G1.2** PreToolUse hook firing test — **PASS**. Measured via existing hook evidence (new hooks can't be registered mid-session — Grok loads hooks at session start only). Direct-write tools (`search_replace`, `write`): **100% firing rate** (26/26 receipts with `pre_state` populated). `run_terminal_command`: inferred reliable (same hook script/registration; receipts only written when files change). Mid-session hook registration does NOT hot-reload — requires TUI 'r' key or session restart. **Design implication**: the broker must be registered before session start, not dynamically.
- [x] **G1.3** Hook stdin JSON format confirmed. PreToolUse receives JSON on **stdin** with **camelCase** fields: `hookEventName` ("pre_tool_use"), `sessionId`, `cwd`, `workspaceRoot`, `permissionMode`, `toolName`, `toolInput`, `toolUseId`, `toolInputTruncated`, `timestamp`. Output: JSON on **stdout** — `{"decision": "allow"}` or `{"decision": "deny", "reason": "..."}`. Exit codes: 0 = allow, 2 = deny, other = fail-open. Environment vars: `GROK_SESSION_ID`, `GROK_HOOK_EVENT`, `GROK_HOOK_NAME`, `GROK_WORKSPACE_ROOT`. **IMPORTANT**: grok uses camelCase throughout stdin (not Claude's snake_case) — the broker's input parser must use `toolName`/`toolInput`, not `tool_name`/`tool_input`.

### Phase 2 — Layer 0 substrate MVP (4-6 sessions)

**Critical: write cleanup script FIRST, before setup script.**

- [ ] **L0.1** `fleet-sandbox-uninstall.ps1` — removes local users, group, ACL grants, SID registry. Tested against clean host.
- [ ] **L0.2** `fleet-sandbox-setup.ps1` — generates synthetic SIDs per agent, creates local users, adds to `FleetSandboxUsers` group, applies workspace ACLs (worktree + `P:/tmp/` writable, `.git/`/`.agents/`/`.claude/` write-denied)
- [ ] **L0.3** `fleet-command-runner` — restricted token + per-process spawn (Python with `win32security` + `CreateProcessAsUserW`, or Rust/C# binary)
- [ ] **L0.4** Cross-agent isolation test: Agent A cannot write to Agent B's worktree via raw Write, shell command, or subagent
- [ ] **L0.5** Cleanup cycle test: setup → ACL verify → uninstall → ACL verify (idempotent, no orphans)

### Phase 3 — Layer 1 broker MVP (3-5 sessions)

- [ ] **L1.1** Capability manifest schema (YAML per agent) — declares `capabilities`, `limits`, `assurance_level`
- [ ] **L1.2** Policy pack for fleet-critical ops: `git.push`, `file.delete.across_worktree_boundary`, `subagent.spawn`, `hook.script_edit`, `agent.passport_issue`
- [ ] **L1.3** `PreToolUse_oap_broker.py` — implements Algorithm 1 (status → capability → policy → assurance → decision → audit). Register as a `~/.grok/hooks/oap-broker.json` hook (matching existing hook infrastructure — NOT config.toml).
- [ ] **L1.4** Ed25519 key generation per agent, DPAPI-encrypted
- [ ] **L1.5** Signed audit log writer — append-only to `P:/.claude/hooks/.evidence/<session>/audit.jsonl`
- [ ] **L1.6** Fail-closed default for all hook error paths (timeout → deny; exception → deny; malformed output → deny; missing hook → deny + page operator)

### Phase 4 — Layer 2 authority semantics (3-4 sessions)

- [ ] **L2.1** Session-start manifest hasher — SHA-256 of hook scripts in `~/.grok/hooks/`, policy packs, broker Python files (walk import graph). Watchdog re-hashes per tool call.
- [ ] **L2.2** Capability mutation detector — fires on skill load, MCP server enable. Invalidates passport cache.
- [ ] **L2.3** Spawn envelope comparator — records parent's authority scope at session start; refuses child effects outside parent scope. Requires Scope/L_max schema.
- [ ] **L2.4** Wiki concept `source:` field (USER | WEB | SUBAGENT | INFERENCE) + `/wiki` pre-write provenance gate

### Phase 5 — Pilot + iterate (2-4 sessions)

- [ ] **P5.1** 2-week pilot on Grok Build only
- [ ] **P5.2** Track false-positive rate from signed audit logs
- [ ] **P5.3** Track manifest hash drift frequency (if >1/week, enforcement layer being modified outside change-control)
- [ ] **P5.4** Operator feedback gate — if operator disables any layer to ship work, redesign that layer
- [ ] **P5.5** Decide fleet rollout (Codex, Antigravity) based on rejection criteria

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
