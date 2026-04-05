# ADR 001: Template-Based Architecture Patterns

**Status:** Accepted
**Date:** 2026-03-01
**Context:** arch package architecture advisor

## Context

The `arch` package provides architectural recommendations to users. We needed to decide between:

1. **LLM-generated recommendations**: Query AI models for each architecture request
2. **Template-based patterns**: Pre-defined architectural patterns with matching logic

## Decision

We chose **template-based architecture patterns** with optional LLM fallback for edge cases.

### Rationale

| Factor | Templates | LLM Generation |
|--------|-----------|----------------|
| **Speed** | Instant (< 100ms) | 2-10 seconds |
| **Cost** | $0 (no API calls) | $0.001-0.01 per query |
| **Reproducibility** | Same input → same output | Non-deterministic |
| **Quality** | Proven patterns | Varies by prompt/model |
| **Maintainability** | Version-controlled templates | Prompt engineering overhead |

### Implementation

```python
class TemplateRepository:
    """Stores architectural pattern templates"""
    def get_pattern(self, context: ProjectContext) -> Pattern:
        # Match context to template via rules
        pass

class LLMFallback:
    """Generates custom recommendations for edge cases"""
    def generate(self, context: ProjectContext) -> Pattern:
        # Call LLM API for custom architecture
        pass
```

## Trade-offs

### Pros
- **Instant responses** - No API latency
- **Zero marginal cost** - No per-query API fees
- **Deterministic** - Same requirements → same recommendation
- **Auditable** - Every decision rule is visible in code

### Cons
- **Limited to known patterns** - Can't invent new architectures
- **Template maintenance** - Need to manually add new patterns
- **Less contextual nuance** - Can't adapt to novel situations

## Related Decisions

- ADR 002: Strategy Pattern for Architecture Selection (pending)

## References

- [Software Architecture Patterns Guide](https://refactoring.guru/design-patterns)
- [Template Method Pattern](https://en.wikipedia.org/wiki/Template_method_pattern)
