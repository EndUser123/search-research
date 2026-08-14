---
title: "I'm trying to find a chat we had about improving the quality of our solutions.  It had to do with sdlc best practice ste"
date: "2026-04-02"
mode: "COPILOT"
uuid: "d5dee909-1259-478d-bd7c-d750cdef4d48"
entry_count: 1
---

## Human

I'm trying to find a chat we had about improving the quality of our solutions.  It had to do with sdlc best practice steps and maybe checking api contracts, I think.

## Assistant

We discussed improving solution quality through enhanced SDLC flows, including quality gates like Semgrep + ESLint, contract validation gaps, and Claude Code skills for structured phases.[1]

## Key Past Discussion
Your /quality workflow mixes deterministic tools and LLMs for validation/fixes across domains; we documented orchestration (e.g., SYSTEM_REFERENCE_FOR_LLM.md) and identified contract checks as a missing design/verify gate.[2][3][4]
We covered gaps like data-flow tracing, invariants, edge cases, and drift validation to bulletproof flows in your monorepo/Claude Code setup.[1]
Optimal sequences used skills like /sdlc:init, /ln-500-story-quality-gate, /sdlc:check for explore/design/TDD/verify/validate.

## SDLC Best Practices
Core 2026 practices emphasize AI integration, Agile iteration, CI/CD automation, shift-left security, and quality gates enforcing code coverage/security before phase gates.[5][6][7]
Quality gates block defective code via checkpoints (e.g., test results, vulnerabilities); integrate into hooks like pre-commit or Claude skills.[7][8]

## API Contract Validation
Use tools like Pydantic (your prior gate), Pact, Postman schemas, or OpenAPI validators to ensure producer-consumer alignment and schema conformance.[1][9]
Add to verify phase: static AST traces for data flows, runtime asserts, and version envelopes to catch drift.[9]

## Actionable Next Steps
1. Audit current flow against gaps: Run /sdlc:check + Pydantic on taskssnapshot producers/consumers.[1]
2. Implement 1-2 gates: e.g., pre-commit AST visitor for traces; YAML checklist for design.[6]
3. Test in pilot: Apply to one repo branch; measure coverage/MTTR before scaling.[6]

Confidence: High (95%) on your Claude Code context; SDLC sources align but evolve—verify latest repos like levnikolaevich/claude-code-skills. Which specific gap (e.g., contracts vs. invariants) to prototype first?[10]
