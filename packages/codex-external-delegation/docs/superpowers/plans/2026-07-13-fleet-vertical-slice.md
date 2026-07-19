# Codex Fleet Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a consumed role-first routing and packet-compilation surface for bounded OpenCode execution while representing unproven MMX, agy, PI, and Codex-native lanes without activating them automatically.

**Architecture:** Extend the existing `codex-external-delegation` package with a static lane registry, deterministic task classifier, version-two packet compiler, and CLI `route` command. Reuse the existing OpenCode runner and result artifacts; preserve provider-specific evidence and keep parent verification authoritative.

**Tech Stack:** Node.js ES modules, `node:test`, SHA-256 packet hashes, existing OpenCode/PI runner.

## Global Constraints

- OpenCode is the only automatic execution candidate.
- OpenCode failure halts and never invokes another lane automatically.
- `agy` is advisory/manual because actual model and trajectory identity remain unproven.
- MMX is capability-only until a consumed adapter is proven.
- PI is explicit-only.
- No recursive delegation, commits, pushes, or shared-state mutation by workers.
- Codex independently verifies worker claims before acceptance.

### Task 1: Registry and policy

**Files:**
- Create: `src/registry.mjs`
- Create: `src/policy.mjs`
- Test: `tests/policy.test.mjs`

- [x] Define the five roles and five lane records with eligibility, identity, containment, failure, verification, probe, adapter, and status fields.
- [x] Classify bounded low-ambiguity work only when scope, model, and deterministic verification are present.
- [x] Keep ambiguous, architectural, security, and unverified lanes parent-owned or explicit.
- [x] Run `npm test`.

### Task 2: Version-two packet and result evidence

**Files:**
- Create: `src/packet.mjs`
- Modify: `src/contract.mjs`
- Modify: `src/prompt.mjs`
- Modify: `src/runner.mjs`
- Test: `tests/runner.test.mjs`

- [x] Compile invocation, role, lane, requested identity, scope, restrictions, verification, failure policy, acceptance criteria, and packet hash.
- [x] Preserve lifecycle and raw-evidence paths in version-two results.
- [x] Leave version-one packets compatible with the existing runner.
- [x] Run `npm test`.

### Task 3: Consumed routing command

**Files:**
- Modify: `bin/external-delegation.mjs`
- Modify: `skill/SKILL.md`
- Test: `tests/route.test.mjs`

- [x] Add `route --input` to emit classification and an OpenCode packet only when eligible.
- [x] Represent agy/MMX/PI without producing automatically executable packets.
- [x] Document the no-fallback policy and consumed command surface.
- [x] Run `npm test`.

### Deferred gates

- Automatic activation by Codex itself remains unproven until a live Codex task demonstrates consumption of this command surface.
- `agy` required-review identity, trajectory binding, authentication-failure, timeout-tree, and concurrent-isolation tests remain prerequisites for future activation.
- Isolated write execution remains outside this slice unless containment is independently proven.
