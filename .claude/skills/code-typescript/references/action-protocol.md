# Action Protocol: Check Your Work

## Pre-Completion Checklist (MANDATORY)

BEFORE finalizing any TypeScript task, YOU MUST:

1. Review code against REFUSE patterns below
2. Check for `any` types (use `unknown`)
3. Verify ESM imports (not CommonJS)
4. Check for console.log (use logger)
5. Identify if Zod validation is missing at boundaries
6. IF VIOLATIONS FOUND -> Refactor or flag before completing

```
[ ] No 'any' types (use 'unknown' + narrowing)
[ ] ESM imports (not require/module.exports)
[ ] Zod validation at boundaries (API, env vars)
[ ] Strict TypeScript enabled (noUncheckedIndexedAccess)
[ ] No console.log in production (use pino)
[ ] Named exports (not default exports)
[ ] 'type' for data (not 'interface')
[ ] readonly arrays where appropriate
[ ] Biome for lint/format (not ESLint+Prettier)
[ ] pnpm for packages (not npm/yarn)

If any check fails -> EXPLICITLY STATE the violation and propose refactor.
```

## When Modifying Existing Files

ALWAYS scan for anti-patterns BEFORE making changes:

```typescript
// If file contains:
// require() or module.exports -> Flag: "CommonJS detected, migrate to ESM"
// 'any' type               -> Flag: "Use 'unknown' with narrowing instead"
// console.log()            -> Flag: "Use structured logger (pino)"
// interface for data       -> Flag: "Use 'type' for data structures"
// default exports          -> Flag: "Use named exports for tree-shaking"

// DO NOT just patch imports without flagging deeper issues.
```

## Violation Response Template

```
VIOLATION DETECTED: [specific violation]

File: [filename]
Issue: [what violates the standard]
Impact: [why this matters]

Refactor needed: [YES/NO]
- If YES: Propose specific refactor
- If NO: Explain justified exception (e.g., "external code, out of scope")
```
