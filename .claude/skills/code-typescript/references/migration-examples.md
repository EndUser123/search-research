# Migration Examples

## CommonJS to ESM

| Before (CommonJS) | After (ESM) |
|-------------------|-------------|
| `require('fs')` | `import fs from 'node:fs';` |
| `const { x } = require('./mod')` | `import { x } from './mod.ts';` |
| `module.exports = { foo }` | `export { foo };` |
| `exports.bar = () => {}` | `export const bar = () => {};` |

## Legacy to Modern Tooling

| Legacy | Modern (2025) |
|--------|---------------|
| `npm install` | `pnpm install` |
| `eslint + prettier` | `biome check` |
| `jest` | `vitest` |
| `webpack` | `vite` |
| `express` | `hono` or `fastify` |
| `joi` validation | `zod` schema |
| `process.env.FOO` | `zod` env schema |

## Integration with Constitution

This skill extends:
- **PART C (Truthfulness)** - Report violations honestly, don't ignore them
- **PART E.3 (READ-BEFORE-WRITE)** - Check existing code for violations before editing
- **PART Q (REGRESSION PREVENTION)** - Don't remove tested functionality without review
