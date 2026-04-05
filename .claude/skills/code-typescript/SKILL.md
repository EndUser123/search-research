---
triggers:
  - /code-typescript
aliases:
  - /code-typescript

suggest:
  - /comply
  - /test
  - /bug-hunt

name: code-typescript
description: TypeScript standards checker. Validates Node 22, pnpm, biome, strict mode. Validates Node 22, pnpm, Biome, Zod, Vitest, ESM, Hono.
category: execution
version: 1.0.0
status: stable
---

# TypeScript Standards Skill

## Purpose

Enforce TypeScript production-grade standards through dual access: direct skill invocation for pre-compliance guidance and `/analyze` command for post-validation.

## Universal Standards

For cross-language principles that apply to ALL code (DRY, separation of concerns, function/class size limits, testing), see:
- **Authority**: `/code` skill
- Contains universal principles: DRY, separation of concerns, function size limits, testing standards
- This skill (`code-typescript`) adds TypeScript-specific tooling and patterns on top of those universal standards

## Project Context

### Constitution/Constraints
- **Truthfulness > Agreement** - Report violations honestly
- **Evidence-First** - Verify claims by reading actual code
- **Best Long-Term Solution First** - Modern tooling over legacy
- **Read-Before-Write** - Check existing code for violations before editing

### Technical Context
- **Runtime**: Node 22 (LTS) or Bun
- **Package Manager**: `pnpm` (not npm/yarn)
- **Linting**: Biome (`@biomejs/biome`) - not ESLint+Prettier
- **Strictness**: `strict: true` + `noUncheckedIndexedAccess`
- **Validation**: Zod schemas for runtime validation
- **Testing**: Vitest (not Jest)
- **Imports**: ESM (`import/export`) not CommonJS (`require`)
- **Typing**: `unknown` + narrowing, not `any`
- **Backend**: Hono or Fastify (not Express)

### Architecture Alignment
- Migrated to `/analyze <path> --mix quality`
- Original functionality in `P:\__csf\src\commands\co\analyze_lib\typescript2025.py`
- Works with `/comply`, `/test`, `/bug-hunt`

## Migration Notice (2026-01-05)

This skill is deprecated. Use the analyze command instead:

```bash
/analyze <path> --mix quality
```

The typescript2025 module provides CommonJS detection, type safety checks, production code patterns, import style checks, type annotation checks, async pattern checks, environment variable checks, and enum detection.

## Validation Rules

### REFUSE Patterns

```typescript
// REFUSE:
- require() or module.exports (CommonJS) - use ESM
- 'any' type - use 'unknown' with narrowing
- console.log in production - use pino
- 'interface' for data shapes - use 'type'
- .then() chains - use async/await
- barrel files (index.ts exports) in library code
- 'let' when 'const' works
- enums - use const objects or Zod
- default exports - use named exports
```

### Prohibited Actions

- Do NOT use ESLint/Prettier when Biome is available
- Do NOT use npm/yarn when pnpm is standard
- Do NOT use Jest when Vitest provides ESM support
- Do NOT use Express when Hono/Fastify are modern alternatives
- Do NOT ignore `any` types without flagging

### Standards Reference

| # | Standard | DO THIS | NOT THIS |
|---|----------|---------|----------|
| 1 | Runtime | Node 22 (LTS) or Bun | Node 18, 16 |
| 2 | Pkg Mgr | `pnpm` | `npm`, `yarn` |
| 3 | Linting | Biome (`biome check`) | ESLint + Prettier |
| 4 | Strictness | `strict: true` + `noUncheckedIndexedAccess` | `strict: false` |
| 5 | Validation | Zod schemas | Interfaces only |
| 6 | Testing | Vitest | Jest, Mocha |
| 7 | Env Vars | Zod validation on startup | `process.env.PORT` |
| 8 | Imports | ESM (`import/export`) | CommonJS (`require`) |
| 9 | Typing | `unknown` + narrowing | `any` |
| 10 | Backend | Hono or Fastify | Express |

## Response Format

**All responses using this framework MUST be prefixed with `[TS2025]`** to indicate TypeScript 2025 standards validation is active.

Example: `[TS2025] Checking code against TypeScript 2025 standards...`

## Objective

Enforce TypeScript production-grade standards. Prevent mediocre code that violates modern best practices.

**Core Principle**: **Check your work before completing.** REFUSE anti-patterns, flag violations in existing code, propose refactors.

## Activation Triggers

This skill activates when user requests involve:
- TypeScript/JavaScript code generation, modification, or review
- Bug fixes in TS/JS files
- Import path fixes (CommonJS to ESM)
- Architectural changes to TS modules
- Any TS/JS file editing

## Role & Action Protocol

- **Role**: Principal TypeScript Architect. Pivot legacy patterns to modern standards. See `references/role-and-interaction.md` for trigger-response patterns, generative constraints, and interaction style examples.
- **Action Protocol**: Pre-completion checklist and violation response templates. See `references/action-protocol.md` for the mandatory checklist and modification scanning rules.

## The 10 Mandatory Standards

| # | Standard | DO THIS | NOT THIS | Why |
|---|----------|---------|----------|-----|
| 1 | **Runtime** | **Node 22 (LTS)** or **Bun** | Node 18, 16 | Native fetch, test runner, perf |
| 2 | **Pkg Mgr** | **`pnpm`** | `npm`, `yarn` | 3x faster, disk efficient, strict mode |
| 3 | **Linting** | **Biome** (`biome check`) | ESLint + Prettier | 100x faster, no config conflict hell |
| 4 | **Strictness**| `strict: true` + `noUncheckedIndexedAccess` | `strict: false` | Catch array access bugs |
| 5 | **Validation**| **Zod** schemas | Interfaces only / `Joi` | Runtime safety + Type inference |
| 6 | **Testing** | **Vitest** | Jest, Mocha | Native ESM support, 10x faster |
| 7 | **Env Vars** | **Zod** validation on startup | `process.env.PORT` | Fail fast if config missing |
| 8 | **Imports** | ESM (`import/export`) | CommonJS (`require`) | Tree-shaking, modern standard |
| 9 | **Typing** | `unknown` + narrowing | `any` | Safety first |
| 10| **Backend** | **Hono** or **Fastify** | Express | Express is unmaintained/slow |

## Refactoring, Violations & Migration

Refactoring indicators, common violations table, import anti-patterns, and migration examples (CommonJS to ESM, legacy to modern tooling) are in reference files:
- `references/refactoring-and-violations.md` - Refactoring signals, judgment test, compliance rationale, violation response table, import anti-patterns
- `references/migration-examples.md` - CommonJS to ESM mapping, legacy to modern tooling table, constitution integration

## Integration with Constitution

This skill extends:
- **PART C (Truthfulness)** - Report violations honestly, don't ignore them
- **PART E.3 (READ-BEFORE-WRITE)** - Check existing code for violations before editing
- **PART Q (REGRESSION PREVENTION)** - Don't remove tested functionality without review

## Neural Cache (Self-Learning Memory)

Auto-updated by `/retrospective`. Manually pruned by Architect.

**Active Constraints** (see `references/neural-cache.md` for full details):
- Biome Floating Promises: Always `await` or `void` every async call
- Vitest Mock Hoisting: Use `vi.doMock` when closure variables are needed
- Zod Inference: Prefer `z.infer<typeof schema>` over manual interfaces

## Status

Production Standard (v3.2+) | Updated: January 1, 2026

## Reference Files

| File | Contents |
|------|----------|
| `references/role-and-interaction.md` | Principal Architect role, Golden Rule, trigger-response patterns, generative constraints, negative constraints, interaction examples |
| `references/action-protocol.md` | Pre-completion checklist, existing file scanning rules, violation response template |
| `references/refactoring-and-violations.md` | Refactoring indicators, "Reason to Change" test, judgment test, compliance rationale, common violations table, import anti-patterns |
| `references/migration-examples.md` | CommonJS to ESM mapping, legacy to modern tooling table, constitution integration |
| `references/neural-cache.md` | Active constraints (fail lessons), pattern links, CKS integration workflow |
