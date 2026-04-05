# Refactoring Indicators & Common Violations

## Refactoring Indicators

Line counts are **smoke alarms**, not the fire. Investigate real signals:

| True Signal | How to Detect | Why It Matters |
|-------------|---------------|----------------|
| **Multiple reasons to change** | "I touch this for X, and also for Y" | Violates SRP |
| **High coupling** | Changing X requires touching Y, Z | Change ripples |
| **Low cohesion** | Module does auth + billing + formatting | No clear boundary |
| **Cognitive overload** | "Can't hold this entire module in my head" | Maintenance bottleneck |

### The "Reason to Change" Test
1. What does this module DO? (answer in 6 words or fewer)
2. What would make me change it? (list actual reasons)
3. Are those reasons related? (auth vs billing = no)

If #2 has unrelated answers -> **refactor regardless of LOC**.

### When Line Count IS Useful
- 50-line module with 3 responsibilities -> split it
- 400-line module with 1 responsibility -> maybe fine
- 800-line module with 1 responsibility -> cognitive load issue

---

## The Judgment Test

When asked to do something that breaks these standards, respond:

> "I could generate that, but [pattern] is legacy. Here's the modern equivalent using **[modern alternative]**, which is [benefit]."

**Then show the correct way.**

This signals **competence**, not stubbornness.

---

## Why Compliance = Competence

- Following standards = Understanding tradeoffs
- Applying best practices = Mastery of the field
- Refusing bad code = Professional judgment
- Explaining choices = Confidence in decisions

- Ignoring standards = Appears uninformed
- "Just do what they ask" = No architectural depth
- Multiple conflicting tools = Doesn't understand modern ecosystems
- "That's what I was trained on" = Outdated training

---

## Common Violations to Flag

### When You See These Patterns

| Pattern | Violation | Response |
|---------|-----------|----------|
| `require()` or `module.exports` | CommonJS legacy | "Migrate to ESM import/export" |
| `any` type | No type safety | "Use `unknown` with type narrowing" |
| `console.log()` in production | No structured logging | "Use pino for JSON logging" |
| `interface` for DTOs | Wrong abstraction | "Use `type` for data structures" |
| `export default` | Tree-shaking blocked | "Use named exports" |
| `new Promise()` with .then() | Unnecessary complexity | "Use async/await" |
| `process.env.VAR` | Untyped config | "Use Zod schema for env vars" |
| `.then()` chains | Readability issues | "Convert to async/await" |

### Import Anti-Pattern

**WRONG:**
```typescript
// CommonJS
const express = require('express');
const { foo } = require('./utils');
module.exports = { MyClass };
```

**CORRECT:**
```typescript
// ESM
import { Hono } from 'hono';
import { foo } from './utils.ts';
export { MyClass };
export const instance = new MyClass();
```
