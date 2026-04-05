# GoT + ToT Integration

Reference file for Graph-of-Thought and Tree-of-Thought reasoning in `/q`.

## Graph-of-Thought (GoT): Requirement Constraint Analysis in Q3

- Extracts requirement/constraint/idea/risk nodes
- Detects relationships (supports, contradicts, depends)
- Warns about circular dependencies and hidden conflicts
- See [GoT Integration](../docs/got-integration.md)

## Tree-of-Thought (ToT): Question Branching in Q2/Q4

- Explores alternative analysis scenarios (sure/maybe/unlikely)
- Selects output branch based on health level
- Discovers hidden architectural edge cases
- See [ToT Integration](../docs/tot-integration.md)

## Opt-out Flags

```bash
export Q_NO_GOT=true  # Disable Graph-of-Thought
export Q_NO_TOT=true  # Disable Tree-of-Thought
```
