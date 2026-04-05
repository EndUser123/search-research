# Specification: diffbro Integration with CSF NIP

**TSK-ID**: TSK-251223-Diffbro-CSFNIP-1423
**Created**: 2025-12-23 14:23:00
**Status**: Draft

## Objective

Integrate [diffbro](https://github.com/disler/diffbro), an AI-powered code review tool using OpenAI GPT models, into the CSF NIP ecosystem to provide semantic diff analysis and contextual code review capabilities.

## Problem Statement

CSF NIP has comprehensive code review commands (`/qual-gate`, `/preview`, `/test_review`, `/ast-analyze`) that provide static analysis, constitutional compliance, and production readiness assessment. However, these tools focus on **what files changed** and **static code quality**, missing the **semantic understanding** of **why changes matter** and **contextual code review** that requires AI comprehension of code changes.

## Proposed Solution

Integrate diffbro through **two complementary approaches**:

1. **`/diffbro` Slash Command** - User-controlled AI code review on demand
2. **CWO12 Plugin** - Optional AI review during Step 7 (Constitutional Quality Validation)

**Explicitly Excluded**: Pre-commit git hook (per user request)

## Key Requirements

### Functional Requirements
- FR1: Create `/diffbro` slash command that wraps diffbro CLI
- FR2: Support diffbro modes: chill, mid, chad
- FR3: Support diffbro features: `--only`, `--ignore`, `--summarize`, `--prompt`
- FR4: Create CWO12 plugin for optional AI review during validation
- FR5: Integrate with existing CSF NIP formatting and error handling
- FR6: Handle graceful degradation when diffbro not installed
- FR7: No duplication of existing quality gate functionality

### Non-Functional Requirements
- NFR1: Optional by default (flag-controlled)
- NFR2: Graceful degradation when unavailable
- NFR3: Low complexity (<+10 complexity tax)
- NFR4: Cost monitoring and limits
- NFR5: Clear boundary (easy to remove/replace)

### Integration Points
- IP1: Slash command in `P:/.claude/commands/`
- IP2: CWO12 plugin in `P:/__csf.nip/src/modules/cwo12/plugins/`
- IP3: Command routing integration

### Out of Scope
- Pre-commit git hook (explicitly excluded)
- Core `/main` integration (adds external dependency)
- Replacing `/qual-gate` functionality
- Modifying existing quality commands

## Constraints

### Technical Constraints
- TC1: Must work with diffbro CLI (external tool)
- TC2: Requires OpenAI API key (user-managed)
- TC3: Subprocess integration (no direct API calls)
- TC4: Must handle diffbro installation failures

### Architecture Constraints
- AC1: Must complement existing tools, not replace them
- AC2: Must follow CSF NIP command patterns
- AC3: Must use existing plugin architecture for CWO12
- AC4: Must maintain backward compatibility

## Success Criteria

- SC1: `/diffbro` command works standalone
- SC2: CWO12 plugin executes during Step 7 when enabled
- SC3: Commands handle errors gracefully when diffbro unavailable
- SC4: No duplication of existing quality gate functionality
- SC5: Complexity tax under +10
- SC6: Developer adoption (team finds useful)

## Deliverables

1. `/diffbro` slash command
2. CWO12 diffbro plugin
3. Documentation for usage and integration
4. Test coverage (TDD approach)
5. Integration with existing command routing

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenAI API down | High | Low | Graceful degradation |
| API costs | Medium | Medium | Usage monitoring, limits |
| Poor quality reviews | Medium | Low | Human review still required |
| Diffbro installation issues | Low | Medium | Clear error messages, docs |
| Duplication of existing tools | Low | Low | Architecture review, testing |

## Dependencies

### External Dependencies
- diffbro CLI tool (`pip install diffbro`)
- OpenAI API key (user-provided)
- Git repository (for diff generation)

### Internal Dependencies
- CSF NIP command routing system
- CWO12 plugin architecture
- OutputFormatter patterns
- TaskMaster integration

## Timeline Estimate

- Phase 1: `/diffbro` command (Week 1)
- Phase 2: CWO12 plugin (Week 2)
- Phase 3: Testing and documentation (Week 2-3)

## Stakeholders

- Primary: CSF NIP development team
- Secondary: CSF NIP users (developers using the system)
- Tertiary: diffbro maintainers (external)

---

**Approval**: Ready for architecture analysis and implementation planning
