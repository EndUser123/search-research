# Neural Cache (Self-Learning Memory)

System 1 Reflexes - Always loaded, zero latency. Auto-updated by /retrospective. Manually pruned by Architect.

## Active Constraints (The "Don't Do This" List)

- `[FAIL 2025-12-15]` **Biome Floating Promises**: Biome's `noFloatingPromises` is stricter than ESLint. **Reflex**: Always `await` or `void` every async call.
- `[FAIL 2025-11-20]` **Vitest Mock Hoisting**: `vi.mock` creates hoisted mocks, cannot use closure variables. **Reflex**: Use `vi.doMock` when closure variables are needed.
- `[FAIL 2025-10-12]` **Zod Inference**: Duplicate type definitions cause maintenance issues. **Reflex**: Prefer `z.infer<typeof schema>` over manual interfaces.

## Pattern Links (The "Read This" List - CKS Deep Context)

- **Biome Migration**: `/chs search "eslint to biome migration"` - Full discussion of toolchain switch
- **Vitest Patterns**: `/chs search "vitest mock closure"` - Mock hoisting solutions
- **React Hooks**: `/chs search "react hooks dependency array"` - useEffect patterns

## CKS Integration

When encountering novel problems:
1. Check this Neural Cache first (L1 - reflex)
2. If no reflex exists, query CKS: `/chs search "<topic>"` (L2 - research)
3. After resolving, run `/retrospective typescript` to promote lesson to this cache
