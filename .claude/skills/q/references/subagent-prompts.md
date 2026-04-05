# Q2 Subagent Prompts

Reference file for `/q` strategic collection subagents. Launch 4 parallel Task subagents (**sonnet model**).

## Subagent A — Architecture & Structure

```
Analyze architectural soundness of session-touched files:
  - Layer separation (presentation, business, data)
  - Module boundaries and responsibilities
  - Coupling and cohesion
  - Abstraction appropriateness
Report: architectural findings with severity (concerning/critical/sound)
```

## Subagent B — Design Patterns & Domain Best Practices

```
Analyze design patterns and domain practices:
  - Identify patterns in use (Factory, Strategy, Repository, etc.)
  - Check for anti-patterns (God object, Singleton abuse, Cargo cult)
  - Use shared_libs.research_fetcher for domain pattern lookup
  - Compare: implementation vs industry standards
Report: pattern findings with domain comparison gaps
```

## Subagent C — Technology Fit & Engineering Balance

```
Analyze technology choices and engineering balance:
  - Technology fit: Right tool for the problem?
  - Over-engineering signals (unnecessary complexity, YAGNI violations)
  - Under-engineering signals (missing abstractions, technical debt risk)
  - Strategic alignment with project goals
Report: technology and balance findings with recommendations
```

## Subagent D — Library Strategy

```
Analyze library choices and maintenance status:
  - Library freshness: outdated dependencies, CVE vulnerabilities
  - API usage patterns: deprecated APIs, incorrect usage
  - Modern alternatives: newer libraries that replace current choices
  - Maintenance risk: abandoned packages, security issues
Report: library strategy findings with modernization recommendations
```

## Post-Merge Filtering

After merging all 4 subagent results into one `strategic_findings` object:

If `.claude/config/solo-dev-context.yaml` exists, filter out enterprise-style findings (team approval gates, real-time dashboards, self-healing, autonomous execution). Report how many were filtered.
