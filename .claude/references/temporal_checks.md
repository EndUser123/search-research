## Temporal Freshness Check (MANDATORY - Phase 3 Enhancement)

**All proposed fixes MUST use current APIs, not deprecated ones.**

When you propose a fix, you MUST verify that the solution uses modern, supported APIs rather than deprecated alternatives.

### Prohibited Deprecated APIs

| Language/Framework | Deprecated API | Modern Alternative |
|-------------------|----------------|-------------------|
| **Python** | `os.path.join`, `os.path.exists` | `pathlib.Path` |
| **Python** | `typing.Dict`, `typing.List` | `dict`, `list` (builtin generics) |
| **Python** | `SafeConfigParser` | `ConfigParser` |
| **Python** | `asyncio.run` (requires 3.7+) | Check version, use fallback if needed |
| **JavaScript** | `XMLHttpRequest` | `fetch API` |
| **JavaScript** | `var` keyword | `const`/`let` |
| **TypeScript** | `any` type | Specific type or `unknown` |

### Temporal Check Protocol

**Before proposing any fix involving APIs:**

1. **Check if API is deprecated** - Consult language documentation
2. **Verify version compatibility** - Ensure API exists in target Python/JS version
3. **Propose modern alternative** - Use current best practices
4. **Document version requirements** - Note if API requires minimum version

### Temporal Verdicts

| Verdict | Meaning | Action |
|---------|---------|--------|
| **VALID** | All APIs are current | Proceed with fix |
| **REJECTED** | Deprecated APIs detected | Replace with modern alternative |
| **UNKNOWN** | No APIs mentioned | Additional review needed |

### Example

❌ **INCORRECT:** "Use `os.path.join()` to build the path."
✅ **CORRECT:** "Use `pathlib.Path()` for path operations (modern API)."

❌ **INCORRECT:** "Use `var` to declare the variable."
✅ **CORRECT:** "Use `const` or `let` for variable declarations (ES6+)."

### Enforcement Checklist

Before finalizing any fix, verify:

- [ ] No deprecated Python APIs (`os.path.*`, `typing.Dict`, `SafeConfigParser`)
- [ ] No deprecated JavaScript APIs (`XMLHttpRequest`, `var`)
- [ ] No unsafe TypeScript patterns (`any` type)
- [ ] Proposed API exists in target version
- [ ] Modern alternative is used when available

**If temporal check fails:** Revise fix to use modern APIs before submitting.
---

## CHS/CKS Citation Requirement (MANDATORY - Phase 2 Enhancement)
