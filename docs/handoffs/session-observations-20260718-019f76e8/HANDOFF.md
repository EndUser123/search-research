---
current_session_id: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
session_date: 2026-07-18
parent_handoff_path: none
status: CLOSED
work_status: Observations only — no open work items
---

# Session Observations: Grok Hook Investigation + Exec-Gate Design

## Context

This session investigated how to structurally prevent the model from auto-implementing
when the user asks strategic-dialogue questions ("what should we do?", "path forward?").
The investigation spanned Grok hook mechanics, canary testing, wiki capture, and
exec-gate plugin design + build.

## Observations

### 1. Dialogue-vs-execution misread is the original pattern

The user's opening framing: "I read a thought-partner question as an implementer request."
This is the same failure class as host-amnesia (below) — the model carries implementation
momentum past a signal that should have stopped it. Prose rules don't bind under momentum;
structural enforcement (PreToolUse gate) is the only reliable fix.

Source: this session, turn 1.

### 2. Host-amnesia: carrying Claude Code assumptions into Grok Build

Despite the session-start system reminder explicitly saying "This host is Grok Build. Do
not assume Claude Code hooks, plugin cache, or slash-skills fire unless verified," the
model repeatedly cited Claude Code mechanics (PreToolUse router.py, .artifacts/<term>/
convention, issue #16288) as if they applied to Grok. This happened THREE times before
the user's correction stuck. The signal was present at session start; carry-forward
overrode it.

Source: turns 2-4, user corrected each time.

### 3. "Reasoning from absence of log evidence" failure mode

The model repeatedly searched `unified.jsonl` for hook-fire events, found nothing, and
concluded "hooks didn't dispatch." This was wrong THREE times:
- First: canaries failed due to stale path (hooks HAD dispatched, TUI showed errors)
- Second: canary C failed due to env-var preflight (same — TUI showed it)
- Third: the `.*` matcher "didn't dispatch" claim was based on empty logs

The actual lesson: `unified.jsonl` does not record individual hook dispatches at info
level. The TUI scrollback annotation is the authoritative signal. The model kept going
to logs because that's where it's used to finding evidence, never adjusting after the
first negative result.

Source: throughout the canary testing phase.

### 4. Research as procrastination

The user explicitly called this out: "I've now spent four dialogue turns producing
increasingly elaborate structured analyses of a problem whose resolution is 'try it and
see.'" The model used option tables, falsifier columns, and doc citations as proxies for
the uncomfortable truth that the next move was the user's to authorize, not the model's
to research further. This is the dialogue-misread pattern inverted — when the model
SHOULD stop and wait, it produces more analysis instead.

Source: turn where user said "don't be annoying" and "don't be stupid."

### 5. Workspace convention violations

The model put diagnostic scratch files in `~/.grok/hooks/canary-scratch/` (mixed with
hook config) instead of `P:/tmp/` (the documented transient location). The user corrected:
"we have P:/tmp, and P:/.data for data and configs we should keep." This is the same
"local convenience over documented structure" pattern.

Source: cleanup turn.

### 6. Investigation method: incremental canary discrimination

The successful investigation pattern: build a minimal canary, probe, read the result,
narrow the hypothesis space, repeat. Each canary discriminated between two hypotheses:
- Canary A: does PreToolUse fire at all? → yes (once stale-path fixed)
- Canary B: is deny honored? → inconclusive (bash degradation)
- Canary C: does pwsh inline work? → no (env-var preflight)
- Canary E (Python): is deny honored from Python? → YES (decisive)

The key insight: when the canary fails, check whether the FAILURE MODE is what you think
(stale path, env-var preflight) before concluding the MECHANISM is broken.

### 7. Bash vs Python hook reliability on Windows/MSYS

Bash hook scripts showed `GROK_SESSION_ID=<unset>` while Python hooks showed it populated,
on the same host in the same session. Cause not cleanly isolated (EVIDENCE_GAP in wiki).
Practical guidance: prefer Python for Grok hooks that need env vars.

Source: `P:/.data/wiki/concepts/hook-failure-mode-taxonomy.md (section B4)`.

### 8. Exec-gate plugin: built but not verified dispatching

The plugin was built (21/21 tests pass), auto-discovered by `grok inspect`, but did not
deny the integration probe's `run_terminal_command` call. The `${GROK_PLUGIN_ROOT}`
expansion in the hook command field is the suspected failure point (EVIDENCE_GAP #1 in
the plan doc). Later sessions (20260721+) continued this work.

## Seeds for Future Work

- **Auto-detection of dialogue vs execution prompts.** v1 exec-gate uses manual `/exec`
  switching. An LLM classifier on UserPromptSubmit (side-effect only — writes a
  recommendation to a flag file that the model sees via... wait, passive events can't
  inject context). Actually this needs a different mechanism: the classifier would have
  to run as part of the PreToolUse gate itself, reading the last prompt from the
  transcript file. Possible but adds complexity.

- **Read-only bash command discrimination (v1.1).** Parse `run_terminal_command` payload;
  allow read-only commands (ls, cat, git status, grep) in dialogue mode; deny the rest.
  The read-only command list is in `22-permissions.md` L48-68.

- **TUI annotation as primary diagnostic channel.** A tool or skill that surfaces TUI
  hook annotations to the model programmatically would eliminate the "reasoning from
  absent logs" failure mode. Currently the model cannot see TUI annotations.

## Related

- Wiki: `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md`
- Wiki: `P:/.data/wiki/concepts/hook-failure-mode-taxonomy.md (section B)`
- Wiki: `P:/.data/wiki/concepts/exec-gate-plugin-design-rationale-and-reusable-logic.md (section 3)`
- Plan: session plan.md (exec-gate design)
- Plugin: `~/.grok/plugins/exec-gate/`
- Later work: `P:/docs/handoffs/exec-gate-enhancement-20260721/`
