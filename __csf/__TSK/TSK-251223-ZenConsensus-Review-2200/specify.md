# Specification: Extend zen-consensus for Code Review

**TSK-ID**: TSK-251223-ZenConsensus-Review-2200
**Created**: 2025-12-23 15:00:00
**Status**: Draft

## Objective

Extend the existing `/zen-consensus` command to support AI-powered code review using multiple independent LLMs, leveraging the existing zen* multi-LLM infrastructure instead of integrating the single-LLM diffbro tool.

## Problem Statement

CSF NIP has comprehensive code review commands (`/qual-gate`, `/preview`, `/test_review`, `/ast-analyze`) that provide static analysis, constitutional compliance, and production readiness assessment. However, these tools focus on **what files changed** and **static code quality**, missing the **semantic understanding** of **why changes matter** and **contextual AI code review** that requires LLM comprehension of code changes.

**Current Limitation**:
- Existing tools: Static analysis (ruff, mypy, bandit)
- Missing: Semantic diff understanding with AI review

**Proposed Solution** (from /arch analysis):
- ❌ Don't integrate diffbro (single LLM, OpenAI lock-in, +7 complexity)
- ✅ Extend `/zen-consensus` (multi-LLM, provider agnostic, +3 complexity)

## Architectural Decision

**[ADF] Assessment**:
- **Complexity Tax**: +3 (well under +10 threshold)
- **Reuses Infrastructure**: zen-provider-manager, zen-consensus voting, zen-synthesize
- **No New Dependencies**: Uses existing provider management
- **Multi-LLM by Default**: More valuable than single-LLM diffbro

## Key Requirements

### Functional Requirements
- FR1: Add `--git-diff` flag to zen-consensus for code review mode
- FR2: Create code review prompt templates for security, performance, bugs, style
- FR3: Integrate git subprocess to capture diffs
- FR4: Aggregate reviews from multiple LLMs using consensus voting
- FR5: Support chill/mid/chad modes as provider combinations
- FR6: Maintain backward compatibility with existing zen-consensus functionality

### Non-Functional Requirements
- NFR1: Provider agnostic (works with any LLM in zen-provider-manager)
- NFR2: Graceful degradation when providers unavailable
- NFR3: Low complexity (<+5 complexity tax)
- NFR4: Clear documentation and usage examples
- NFR5: Cost tracking integration with zen-provider-manager

### Integration Points
- IP1: `/zen-consensus` command extension
- IP2: `/zen-provider-manager` for API calls
- IP3: `/zen-synthesize` for result aggregation
- IP4: Git subprocess for diff capture

### Out of Scope
- Pre-commit git hook (can be added later if needed)
- Replacing existing `/qual-gate` functionality
- Modifying `/zen-code-analyze` (separate command)

## Constraints

### Technical Constraints
- TC1: Must work with git repository (for diff generation)
- TC2: Must use existing zen-provider-manager for API calls
- TC3: Must maintain zen-consensus interface compatibility
- TC4: Must handle git diff format parsing

### Architecture Constraints
- AC1: Must reuse existing zen* infrastructure
- AC2: Must follow zen* command patterns
- AC3: Must maintain backward compatibility
- AC4: Must support multiple LLM providers (not locked to one)

## Success Criteria

- SC1: `/zen-consensus --git-diff` works with multiple LLMs
- SC2: Code review prompts generate high-quality reviews
- SC3: Consensus aggregation provides meaningful synthesis
- SC4: Chill/mid/chad modes work as expected
- SC5: Complexity tax under +5
- SC6: Documentation complete and clear

## Deliverables

1. Extended `/zen-consensus` command with git-diff support
2. Code review prompt templates
3. Git integration for diff capture
4. Consensus aggregation for multiple reviews
5. Documentation and usage examples
6. Test coverage

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Git diff parsing fails | High | Low | Use gitpython library or subprocess |
| Provider API failures | Medium | Medium | Graceful degradation via zen-provider-manager |
| Poor quality reviews | Medium | Low | Multi-LLM consensus improves quality |
| Complexity creep | Low | Medium | Regular ADF reviews |
| Breaking zen-consensus | Medium | Low | Backward compatibility tests |

## Dependencies

### External Dependencies
- Git repository (for diff generation)
- LLM provider APIs (via zen-provider-manager)

### Internal Dependencies
- zen-consensus command infrastructure
- zen-provider-manager for API calls
- zen-synthesize for result aggregation
- TaskMaster integration

## Timeline Estimate

- Phase 1: Core git-diff integration (Day 1)
- Phase 2: Code review prompts (Day 1)
- Phase 3: Consensus aggregation (Day 2)
- Phase 4: Testing and documentation (Day 2)

## Stakeholders

- Primary: CSF NIP development team
- Secondary: CSF NIP users (developers using the system)
- Tertiary: zen* command maintainers

---

**Approval**: Ready for architecture analysis and implementation planning
