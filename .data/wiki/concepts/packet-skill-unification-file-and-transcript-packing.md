---
title: "Packet skill unification — one command for file packing and transcript export"
created: 2026-07-30
source: session-019fb04d (operator-requested refactor after audit review packet)
tags: [skill-consolidation, packet, gitpack, file-packing, transcript-export, command-reduction, cognitive-burden]
summary: >
  /packet and /gitpack were two commands with the same output format (_sig.md +
  _full.md) but different inputs (transcripts vs files). The operator pointed
  out the distinction was invisible to them — "pack this for review" is one
  intent. The unification merges gitpack's AST/regex extraction logic into
  /packet as a file mode, auto-detected from input type. One command, two
  modes, same output. Eliminates /gitpack as a separate mental slot.
cognitive_load: 2
verification: local-only
host: grok
agent: grok
sources:
  - "session-019fb04d operator request: 'why don't you merge them into pack or packet?'"
relations:
  - target: wiki/concepts/conversation-distillation-review-packet-export.md
    type: extends
  - target: wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern.md
    type: related
---

# Packet skill unification

## Decision context

**The problem:** the operator needed to hand 5 source files to a reviewing LLM. I first tried `/packet` (wrong tool — it exports conversation transcripts, not files). Then I hand-wrote a markdown document concatenating the files (wrong approach — manual, not reproducible). Then the operator asked: "why don't you merge them?" — pointing out that `/packet` and `/gitpack` share the same output format but the operator had to know which command handles which input type.

**The cognitive burden:** 45+ user-facing commands already exist (per the improvement-system audit §6). Two commands for the same job ("make something another LLM can read") — one for transcripts, one for files — is one command too many. The distinction between "I want the conversation" and "I want the files" is invisible to the operator at invocation time.

**The triggering incident:** the operator needed to pass 5 source files to a reviewing LLM. I (the agent) tried `/packet` first — wrong, it only handles transcripts. Then I hand-wrote a markdown concatenation — wrong, not reproducible. Then the operator asked "why don't you merge them?" The fact that I, the agent with full skill catalog access, reached for the wrong tool first is the strongest evidence that the split is cognitively expensive. If the agent can't route correctly, the operator certainly can't be expected to.

**What the research says:** the improvement-system audit's cognitive-burden assessment (§6) found that "the mechanisms are individually well-justified. The burden is aggregate — too many parallel paths for the same loop stage." This unification is a narrow instance of that finding: two commands for the same output format is aggregate burden, not individual defect.

## Decision: absorb gitpack's extraction into packet

**Chosen:** `/packet` gains a `--files` mode (and auto-detection from input type). gitpack's AST/regex extraction logic is ported as `file_extractor.py` in packet's `__lib/`. The existing transcript-mode logic stays unchanged.

**Steelman of the rejected alternative (keep them separate):** `/gitpack` is a marketplace plugin we don't own. Keeping it separate preserves the original implementation for the Claude environment. The two skills have different dependencies (packet needs the AAR parser; gitpack is pure stdlib) and different extraction strategies (topic filtering vs AST signatures). Maintaining separate code means each can evolve independently — gitpack could add language support without affecting packet's transcript pipeline.

**Why unification wins:** the operator's mental model is "pack this for review," not "invoke the transcript exporter" or "invoke the file packer." Forcing them to know the input-type distinction is the same class of friction the audit identified as cognitive burden. The extraction logic differences are implementation details — the operator never sees them. And `/gitpack` as a marketplace plugin remains available in the Claude environment; we're porting the logic, not deleting the source. The 674 lines of new code (file_extractor.py + pack.py) is a one-time cost; the ongoing cost is one fewer command to remember for every future session.

## Architecture

```
/packet [session-id | file-paths... | --files <paths>]
```

Auto-routes on input type:
- Existing file/dir path → file mode (AST signatures + full source)
- UUID or session arg → transcript mode (filtered conversation)

Shared output: `_sig.md` (index) + `_full.md` (full content).

**Example — file mode (the use case that triggered the unification):**
```bash
python ~/.grok/skills/packet/scripts/pack.py \
    --files check_lifecycle.py write_check_state.py close_accounting.py \
    --name check-receipt-review
```
Produces `check-receipt-review_sig.md` (AST signatures: function names, class names, type annotations) and `check-receipt-review_full.md` (all three files' complete source). The reviewer reads one file instead of opening three.

**Example — transcript mode (unchanged behavior):**
```bash
python ~/.grok/skills/packet/scripts/pack.py 019fb04d-945b-75c0-878a-90c1be2c587f \
    --terms "check_lifecycle,receipt,finalize,close_accounting"
```
Produces `packet-019fb04d_sig.md` (turn index with one-line summaries) and `packet-019fb04d_full.md` (filtered conversation with tool I/O collapsed to path handles).

**Example — auto-detection (the operator-friendly path):**
```bash
python ~/.grok/skills/packet/scripts/pack.py P:/.grok/skills/check/__lib/check_lifecycle.py
```
The positional arg is an existing file → file mode. No `--files` flag needed.

| Component | Module | Origin |
|---|---|---|
| File extractor | `__lib/file_extractor.py` | Ported from gitpack (AST + regex schemas) |
| Transcript extractor | `scripts/pack.py` transcript mode | Existing export.py logic |
| Redaction | `__lib/redact.py` | Existing (applies to both modes) |
| Renderer | `scripts/pack.py` | New unified CLI |

## What stayed unchanged

- `scripts/export.py` — backward-compat entry point still works
- `__lib/filter.py`, `__lib/render.py` — transcript-mode internals
- AAR parser import contract

## Implementation details

The file extractor ports gitpack's proven approach: AST parsing for Python signatures (functions, classes, type annotations), regex schemas for JavaScript/TypeScript/HTML/CSS/SQL/Markdown/YAML/JSON/PowerShell, and directory recursion with component-wise exclusion (no substring false drops). This is the same code-vs-LLM split documented in [[mechanical-enforcement-over-behavioral-reminder]] and [[shell-to-python-orchestration-threshold]] — the extraction is deterministic (pure stdlib), and the only LLM work is mode detection and topic-phrase expansion (transcript mode).

The auto-detection logic is simple: if the positional arg resolves to an existing file or directory, file mode is used; otherwise it's treated as a session ID. This means the operator can type `/packet P:/.grok/skills/check/__lib/check_lifecycle.py` and get a file pack without knowing the `--files` flag exists.

## What this means for our workspace

One fewer command the operator must distinguish. The `/packet` skill now handles the full range of "hand this to another LLM" use cases — whether the input is a conversation transcript or a set of source files. The auto-detection means the operator doesn't even need to specify the mode explicitly.

This is a small instance of the broader pattern documented in [[research-to-execution-ratio-self-reinforcing-pattern]]: the workspace tends to accumulate parallel mechanisms for the same job. Unifying them reduces cognitive load without losing capability. The [[conversation-distillation-review-packet-export]] concept documented the original /packet design; this concept records its evolution into a unified tool.

The unification also addresses a point from the improvement-system audit's cognitive-burden assessment: 45+ commands is a high memorization surface for a single operator with ADHD. Every consolidation reduces that surface by one.

## Falsifier

This unification is wrong if:
- The file extraction logic diverges from gitpack's quality (bugs from porting). Mitigated: the port is line-for-line from gitpack's `gitpack.py` with the same AST walker and regex schemas. Verification: `ruff check` + functional tests confirm both signature extraction and full-source inclusion work correctly.
- The operator actually needs the two modes to be separate commands (they don't — they asked for the merge)
- Transcript-mode backward compat breaks (existing export.py callers fail). Mitigated: `export.py` still exists as a backward-compat entry point; the new `pack.py` calls the same `filter.py` + `render.py` modules.
- The auto-detection misroutes (e.g., a session ID that happens to be a file path). Mitigated: session IDs are UUIDs (contain hyphens, no file extension); file paths have extensions or slashes. The detection is robust for the actual input space.

## Receipts

- `~/.grok/skills/packet/__lib/file_extractor.py` — ported gitpack extraction (AST + regex + directory recursion)
- `~/.grok/skills/packet/scripts/pack.py` — unified CLI with auto-routing
- `~/.grok/skills/packet/SKILL.md` — updated for both modes
