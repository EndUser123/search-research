# Requirements Analysis: zen-consensus Code Review Extension

**TSK-ID**: TSK-251223-ZenConsensus-Review-2200
**Created**: 2025-12-23
**Status**: Requirements Analysis
**Complexity Tax**: +3 (well under +10 threshold)

---

## Executive Summary

This document analyzes the requirements for extending the existing `/zen-consensus` command to support AI-powered code review using git diff integration. The analysis confirms the architectural decision to leverage the existing zen* multi-LLM infrastructure rather than integrating the single-LLM diffbro tool.

**Key Findings:**
- Existing zen-consensus infrastructure is well-suited for extension
- Provider-agnostic design enables multi-model consensus
- Low implementation complexity (+3 estimated)
- Reuses existing zen-provider-manager, zen-orchestrator, and consensus patterns

---

## 1. Existing zen-consensus Command Structure Analysis

### 1.1 Current Architecture

**File Location**: `P:/__csf.nip/src/zen/zen-consensus.py`

**Current Functionality:**
```python
# Current command-line interface
parser.add_argument("topic", help="Topic for consensus analysis")
parser.add_argument("--models", help="Comma-separated list of models")
parser.add_argument("--mode", help="Consensus mode: debate, discussion, tradeoff, risk, alternatives")
parser.add_argument("--stance", help="Stance assignment: for,against,neutral")
parser.add_argument("--factors", help="Analysis factors to consider")
parser.add_argument("--constraints", help="Constraints and limitations")
parser.add_argument("--temperature", type=float, default=0.7)
parser.add_argument("--max-tokens", type=int, default=1500)
```

**Current Workflow:**
1. Parse command-line arguments
2. Get zen-processor instance
3. Build consensus prompt based on mode
4. Call `processor.process_consensus_structured()`
5. Format and display results
6. Optional export to JSON/markdown

**Processing Layer**: `P:/__csf.nip/src/commands/zen_command_processor.py`
- `process_consensus_structured()` - Main consensus handler
- `_analyze_consensus()` - Agreement level analysis
- `_format_consensus_results()` - Result formatting

### 1.2 Integration Points

**Zen Orchestrator** (`P:/__csf.nip/src/zen_integration/zen_orchestrator.py` - backup):
```python
class ZenRequest:
    prompt: str
    task_type: str = "general"
    models: list[str] | None = None
    context: dict[str, Any] | None = None
    temperature: float | None = None
    max_tokens: int | None = None

async def consensus(self, request: ZenRequest, models: list[str]) -> dict[str, ZenResponse]
```

**Provider Manager** (`P:/__csf.nip/src/zen_integration/api_key_manager.py`):
- ProviderConfig with provider_type, api_key, models, specializations
- Support for: openrouter, gemini, openai, anthropic, xai, groq, mistral
- Cost tracking and performance metrics
- Provider health management

---

## 2. Git Diff Integration Requirements

### 2.1 Git Subprocess Integration

**FR3 Analysis**: Integrate git subprocess to capture diffs

**Implementation Options:**

| Option | Complexity | Pros | Cons |
|--------|-----------|------|------|
| Python subprocess module | Low | No dependencies, simple | Manual parsing required |
| GitPython library | Medium | Pythonic API, robust | External dependency |
| Existing git integration | Low | Reuses codebase patterns | May need adaptation |

**Recommended Approach**: Python subprocess with fallback to GitPython

**Git Diff Capture Requirements:**
```python
# Core diff capture functionality needed
def capture_git_diff(
    ref: str = "HEAD",  # git reference (HEAD, commit hash, branch)
    files: list[str] = None,  # specific files or None for all
    context_lines: int = 5,  # unified diff context
    stat: bool = False,  # include file statistics
) -> dict[str, str]:
    """
    Returns:
    {
        "diff": "unified diff text",
        "stats": "file change statistics",
        "files_changed": ["list.py", "of.py", "files.py"],
        "summary": {"additions": 100, "deletions": 50}
    }
    """
```

**Git Commands to Support:**
- `git diff HEAD` - Current working directory vs last commit
- `git diff --cached` - Staged changes
- `git diff HEAD~N` - Compare with N commits ago
- `git diff branch1...branch2` - Branch comparison
- `git diff --stat` - File statistics

**Error Handling:**
- Not in a git repository
- Invalid git reference
- No changes detected
- Merge conflicts

### 2.2 Diff Format Parsing

**Unified Diff Format:**
```
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -1,5 +1,7 @@
 def old_function():
-    return "old"
+    return "new"
+    # New comment
```

**Parsing Requirements:**
- Extract changed files
- Identify added/removed lines
- Preserve context for LLM understanding
- Handle binary files gracefully
- Support multiple file changes

---

## 3. Code Review Prompt Template Structure

### 3.1 Template Categories (FR2)

**Security Review Template:**
```
Review the following git diff for security vulnerabilities:

**Context**: {context}
**Files Changed**: {files_changed}

**Git Diff**:
```diff
{diff_content}
```

**Security Focus Areas**:
1. Injection vulnerabilities (SQL, command, code)
2. Authentication and authorization issues
3. Sensitive data exposure
4. Cryptographic weaknesses
5. Input validation gaps
6. API security concerns

Provide:
- Critical security findings (with severity)
- Specific code locations and issues
- Remediation recommendations
- Risk assessment (Critical/High/Medium/Low)
```

**Performance Review Template:**
```
Review the following git diff for performance issues:

**Context**: {context}
**Files Changed**: {files_changed}

**Git Diff**:
```diff
{diff_content}
```

**Performance Focus Areas**:
1. Algorithmic complexity (O(n) analysis)
2. Database query efficiency
3. Memory usage patterns
4. Caching opportunities
5. I/O operations
6. Concurrency and parallelization

Provide:
- Performance bottlenecks identified
- Big O complexity analysis
- Optimization recommendations
- Expected performance impact
```

**Bug Detection Template:**
```
Review the following git diff for potential bugs:

**Context**: {context}
**Files Changed**: {files_changed}

**Git Diff**:
```diff
{diff_content}
```

**Bug Detection Focus Areas**:
1. Off-by-one errors
2. Null/None handling
3. Edge cases and boundary conditions
4. Exception handling gaps
5. Logic errors
6. Race conditions

Provide:
- Bugs found (with severity)
- Specific code locations
- Reproduction scenarios
- Fix recommendations
```

**Code Style Template:**
```
Review the following git diff for code style and maintainability:

**Context**: {context}
**Files Changed**: {files_changed}

**Git Diff**:
```diff
{diff_content}
```

**Style Focus Areas**:
1. Naming conventions
2. Code organization and structure
3. Documentation completeness
4. Consistency with project patterns
5. SOLID principles adherence
6. DRY (Don't Repeat Yourself) violations

Provide:
- Style issues found
- Maintainability concerns
- Improvement suggestions
- Best practice recommendations
```

### 3.2 Template Storage

**Location**: `P:/__csf.nip/src/zen/templates/code_review/`
- `security_review.template`
- `performance_review.template`
- `bug_detection.template`
- `style_review.template`
- `comprehensive_review.template` (all categories)

**Template Format**: YAML with embedded markdown
```yaml
name: "Security Code Review"
focus: security
default_temperature: 0.3  # Lower for more focused analysis
system_prompt: |
  You are an expert security reviewer...
user_prompt_template: |
  Review the following git diff for security vulnerabilities...
```

---

## 4. Consensus Aggregation Approach

### 4.1 Current Consensus Mechanism

**Location**: `P:/__csf.nip/src/commands/zen_command_processor.py`

**Existing Method:**
```python
def _analyze_consensus(self, responses: dict[str, Any]) -> dict[str, Any]:
    """Analyze consensus responses for agreement level."""
    # Simple heuristic analysis
    agreement_level = "moderate"
    recommendation = "Consensus requires human review and decision"
    return {
        "agreement_level": agreement_level,
        "response_count": len(response_contents),
        "recommendation": recommendation,
    }
```

### 4.2 Enhanced Aggregation for Code Review

**FR4 Analysis**: Aggregate reviews from multiple LLMs using consensus voting

**Proposed Enhancement:**

```python
def _analyze_code_review_consensus(
    self,
    responses: dict[str, str],
    review_type: str = "security"
) -> dict[str, Any]:
    """
    Analyze code review consensus across multiple LLM responses.

    Aggregation Strategy:
    1. Extract structured findings from each review
    2. Group findings by category and severity
    3. Apply consensus voting:
       - Unanimous: All models mention
       - Strong: 75%+ models mention
       - Moderate: 50%+ models mention
       - Weak: <50% models mention
    4. Prioritize by consensus level and severity
    """
```

**Finding Extraction:**
```python
def extract_findings(review_text: str) -> list[dict]:
    """
    Parse LLM response to extract structured findings.

    Returns:
    [
        {
            "severity": "Critical",
            "category": "SQL Injection",
            "location": "file.py:42",
            "description": "User input not sanitized",
            "recommendation": "Use parameterized query"
        },
        ...
    ]
    """
```

**Consensus Scoring:**
```python
finding_consensus = {
    "file.py:42 - SQL Injection": {
        "models_mentioned": ["claude", "gemini", "gpt4"],  # 3/3 = 100%
        "consensus_level": "unanimous",
        "severity_agreement": "Critical",
        "aggregated_recommendation": "Use parameterized query with prepared statements"
    },
    "file.py:100 - Missing validation": {
        "models_mentioned": ["claude"],  # 1/3 = 33%
        "consensus_level": "weak",
        "severity_agreement": "Medium",
        "aggregated_recommendation": "Add input validation"
    }
}
```

**Priority Ranking:**
1. Unanimous Critical findings
2. Strong High findings
3. Moderate Medium findings
4. Weak Low findings (optional to include)

### 4.3 Synthesis Generation

**Generate aggregated review summary:**
```markdown
# Code Review Consensus Report

## Summary
- **Models**: Claude 3.5, Gemini 1.5, GPT-4
- **Review Type**: Security
- **Consensus Level**: Strong (3/3 models agree on critical findings)

## Critical Findings (Unanimous)

### 1. SQL Injection in user authentication
**Severity**: Critical
**Location**: `src/auth/login.py:42`
**Models**: All (3/3)
**Issue**: User input directly interpolated into SQL query
**Recommendation**: Use parameterized queries with prepared statements

### 2. Missing authentication on API endpoint
**Severity**: Critical
**Location**: `src/api/users.py:15`
**Models**: All (3/3)
**Issue**: Public endpoint returns sensitive user data
**Recommendation**: Add authentication decorator and permission checks

## High Findings (Strong Consensus)

### 1. Hardcoded API key
**Severity**: High
**Location**: `config.py:10`
**Models**: 2/3 (Claude, Gemini)
**Issue**: Production API key in source code
**Recommendation**: Move to environment variables

## Recommendations

### Immediate Actions (Critical)
1. Fix SQL injection vulnerability
2. Add authentication to user endpoint
3. Rotate exposed API key

### Short-term Actions (High)
1. Move secrets to environment variables
2. Add security testing to CI/CD

### Optional Actions (Low/Medium)
1. Add input validation library
2. Implement rate limiting
```

---

## 5. Chill/Mid/Chad Mode Provider Mappings

### 5.1 Mode Definition (FR5)

**Concept**: Pre-configured provider combinations for different use cases

| Mode | Description | Cost | Speed | Quality |
|------|-------------|------|-------|---------|
| **chill** | Fast, cost-effective reviews | Low | Fast | Good |
| **mid** | Balanced speed and quality | Medium | Medium | High |
| **chad** | Maximum quality, no cost concern | High | Slow | Excellent |

### 5.2 Provider Mappings

**Chill Mode (Cost-Optimized):**
```python
CHILL_MODELS = [
    "openrouter/mistralai/mixtral-8x7b",  # Free tier on OpenRouter
    "groq/llama-3.1-70b-versatile",  # Fast, low cost
    "openrouter/google/gemma-2-9b-it:free",  # Free tier
]
# Expected cost: ~$0.001 per review
# Speed: ~10-20 seconds
# Quality: Good for basic issues
```

**Mid Mode (Balanced):**
```python
MID_MODELS = [
    "openrouter/anthropic/claude-3.5-sonnet",  # High quality
    "gemini/gemini-1.5-pro",  # Good quality, fast
    "openrouter/meta-llama/llama-3.1-70b-instruct",  # Balanced
]
# Expected cost: ~$0.01-0.02 per review
# Speed: ~20-40 seconds
# Quality: High, catches most issues
```

**Chad Mode (Maximum Quality):**
```python
CHAD_MODELS = [
    "openrouter/anthropic/claude-3.5-sonnet",  # Best for security
    "openai/gpt-4-turbo",  # Best for reasoning
    "gemini/gemini-1.5-pro",  # Large context, fast
    "openrouter/mistralai/mixtral-8x22b",  # Additional perspective
]
# Expected cost: ~$0.05-0.10 per review
# Speed: ~40-60 seconds
# Quality: Excellent, comprehensive analysis
```

### 5.3 Implementation

**Command-Line Usage:**
```bash
# Chill mode - fast, cheap
/zen-consensus --git-diff --mode chill --review-type security

# Mid mode - balanced
/zen-consensus --git-diff --mode mid --review-type comprehensive

# Chad mode - maximum quality
/zen-consensus --git-diff --mode chad --review-type all

# Custom model selection (override mode)
/zen-consensus --git-diff --models claude,gemini --review-type performance
```

**Configuration Storage:**
```yaml
# P:/__csf.nip/config/zen_modes.yaml
modes:
  chill:
    models:
      - openrouter/mistralai/mixtral-8x7b
      - groq/llama-3.1-70b-versatile
    temperature: 0.5
    max_tokens: 1000
    description: "Fast, cost-effective code review"

  mid:
    models:
      - openrouter/anthropic/claude-3.5-sonnet
      - gemini/gemini-1.5-pro
      - openrouter/meta-llama/llama-3.1-70b-instruct
    temperature: 0.7
    max_tokens: 1500
    description: "Balanced speed and quality"

  chad:
    models:
      - openrouter/anthropic/claude-3.5-sonnet
      - openai/gpt-4-turbo
      - gemini/gemini-1.5-pro
      - openrouter/mistralai/mixtral-8x22b
    temperature: 0.7
    max_tokens: 2000
    description: "Maximum quality review"
```

---

## 6. Backward Compatibility Requirements (FR6)

### 6.1 Compatibility Strategy

**Principle**: All existing zen-consensus functionality must remain unchanged

**Approach**: Additive extension without breaking changes

### 6.2 Implementation Strategy

**Option 1: Flag-Based Mode Switching**
```python
# Existing usage (unchanged)
/zen-consensus "Should we use TypeScript?" --models gemini,claude

# New code review mode (via flag)
/zen-consensus --git-diff --review-type security --mode mid

# Mutually exclusive modes
if args.git_diff:
    # Code review mode
    result = await self.process_code_review(args)
else:
    # Original consensus mode (unchanged)
    result = await self.process_consensus_structured(args)
```

**Option 2: Sub-command Structure**
```bash
# Existing command (unchanged)
/zen-consensus "topic" --models gemini,claude

# New sub-command
/zen-consensus review --git-diff --type security --mode mid

# Implementation: Add new subparser
subparsers = parser.add_subparsers(dest='subcommand')
consensus_parser = subparsers.add_parser('consensus')
review_parser = subparsers.add_parser('review')
```

**Recommended**: Option 1 (flag-based) for simplicity and consistency

### 6.3 Backward Compatibility Checklist

- [x] All existing arguments remain valid
- [x] Default behavior unchanged when --git-diff not present
- [x] Existing prompt templates unaffected
- [x] Existing consensus logic unchanged
- [x] Export formats work for both modes
- [x] Error messages consistent
- [x] Help text updated (not breaking)

### 6.4 Testing Requirements

```python
# Test: Original functionality preserved
async def test_backward_compatibility():
    # Original consensus usage
    result = await processor.process_consensus_structured(
        argparse.Namespace(
            topic="Test topic",
            mode="debate",
            models="gemini,claude",
            # No git-diff flag
        )
    )
    assert result["success"]
    assert "responses" in result

# Test: New git-diff mode works
async def test_git_diff_mode():
    result = await processor.process_code_review(
        argparse.Namespace(
            git_diff=True,
            review_type="security",
            mode="mid",
            ref="HEAD"
        )
    )
    assert result["success"]
    assert "findings" in result
```

---

## 7. Architecture and Design Patterns

### 7.1 Extension Architecture

**Layer Structure:**
```
┌─────────────────────────────────────────┐
│  zen-consensus CLI (zen-consensus.py)  │
│  - Argument parsing                      │
│  - Mode detection (consensus vs review) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  ZenCommandProcessor                     │
│  - process_consensus_structured() [NEW] │
│  - process_code_review() [NEW]          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Code Review Orchestrator [NEW]         │
│  - Git diff capture                     │
│  - Prompt template selection            │
│  - Finding extraction                   │
│  - Consensus aggregation                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Zen Orchestrator (existing)            │
│  - consensus() method                   │
│  - Provider management                  │
│  - API calls                            │
└─────────────────────────────────────────┘
```

### 7.2 Design Patterns

**Strategy Pattern**: Review type selection (security, performance, bugs, style)
**Template Method**: Consensus aggregation workflow
**Factory Pattern**: Prompt template instantiation
**Facade Pattern**: Simplified interface over git operations

### 7.3 Module Organization

```
P:/__csf.nip/src/zen/
├── zen-consensus.py              # Main CLI (modified)
├── templates/
│   └── code_review/
│       ├── security_review.template
│       ├── performance_review.template
│       ├── bug_detection.template
│       ├── style_review.template
│       └── comprehensive_review.template
└── code_review/                  # NEW MODULE
    ├── __init__.py
    ├── git_diff_manager.py      # Git operations
    ├── prompt_template_manager.py # Template loading
    ├── review_orchestrator.py    # Main coordination
    ├── finding_extractor.py      # Structured finding parsing
    ├── consensus_aggregator.py   # Multi-LLM synthesis
    └── mode_config.py            # Chill/mid/chad config
```

---

## 8. Non-Functional Requirements Analysis

### 8.1 Provider Agnostic (NFR1)

**Analysis**: Reuses zen-provider-manager infrastructure

**Evidence**: Existing provider support for:
- OpenRouter (multiple models)
- Groq
- Anthropic (Claude)
- OpenAI (GPT-4)
- Google (Gemini)
- X.AI (Grok)
- Mistral
- Together AI

**Conclusion**: Fully provider-agnostic by design

### 8.2 Graceful Degradation (NFR2)

**Failure Scenarios:**

| Scenario | Current Behavior | Required Enhancement |
|----------|------------------|----------------------|
| Git not available | N/A | Detect and provide clear error |
| Provider API fails | Existing retry logic | Use in zen-consensus |
| Diff too large | N/A | Truncate or chunk diff |
| No changes in git | N/A | Detect and inform user |
| Partial model failure | Continue with available | Existing behavior |

**Implementation**: Leverage existing error handling in provider_wrapper

### 8.3 Low Complexity (NFR3)

**Complexity Analysis:**
- Git integration: +1 (subprocess calls, simple parsing)
- Prompt templates: +1 (template files, string formatting)
- Consensus aggregation: +1 (finding extraction, scoring)
- Total: **+3 complexity tax**

**Verification**: Well under +10 threshold

### 8.4 Documentation (NFR4)

**Required Documentation:**
1. User guide update (`P:/__csf.nip/docs/ZEN_USER_GUIDE.md`)
2. Code review examples
3. Template customization guide
4. Mode selection guide

### 8.5 Cost Tracking (NFR5)

**Integration**: Existing zen-provider-manager cost tracking

**Metrics Tracked:**
- Tokens used per review
- Cost per model
- Cost by review type
- Mode cost comparison

---

## 9. Implementation Considerations

### 9.1 Phased Implementation

**Phase 1: Core Git Integration (Day 1)**
- [ ] Git diff capture via subprocess
- [ ] Basic diff parsing
- [ ] Error handling for git operations
- [ ] Unit tests for git operations

**Phase 2: Review Prompts (Day 1)**
- [ ] Create prompt templates
- [ ] Template loading system
- [ ] Basic review generation
- [ ] Single-model testing

**Phase 3: Consensus Aggregation (Day 2)**
- [ ] Finding extraction
- [ ] Consensus scoring
- [ ] Aggregation logic
- [ ] Multi-model testing

**Phase 4: Polish and Documentation (Day 2)**
- [ ] Mode configuration (chill/mid/chad)
- [ ] Error handling refinement
- [ ] Documentation updates
- [ ] Integration tests

### 9.2 Testing Strategy

**Unit Tests:**
- Git diff capture (various scenarios)
- Template loading and rendering
- Finding extraction (mock responses)
- Consensus scoring logic

**Integration Tests:**
- End-to-end review generation
- Multi-model consensus
- Error handling (git failures, provider failures)
- Backward compatibility

**Test Data:**
- Sample git diffs (various sizes)
- Mock LLM responses
- Edge cases (empty diff, merge conflicts)

### 9.3 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Git parsing fails on complex diffs | Low | High | Use mature parsing library |
| LLM responses inconsistent | Medium | Medium | Structured prompts with examples |
| Consensus aggregation too simplistic | Medium | Low | Iterate based on testing |
| Breaking existing functionality | Low | High | Comprehensive backward compat tests |
| Cost higher than expected | Low | Medium | Start with chill mode |

---

## 10. Dependencies and Integration Points

### 10.1 Internal Dependencies

**Existing Components:**
- `zen_command_processor.py` - Extend with code review method
- `zen_orchestrator.py` - Use consensus() method
- `api_key_manager.py` - Provider management
- `provider_wrapper.py` - API calls

**New Components:**
- `code_review/` module
- Template system
- Git integration

### 10.2 External Dependencies

**Potential New Dependencies:**
- GitPython (optional, can use subprocess)
- PyYAML (already in use)

**Recommended**: Start with subprocess, add GitPython if needed

### 10.3 Integration Points

**IP1: zen-consensus command extension**
- Add --git-diff flag
- Add --review-type flag
- Add --mode flag (chill/mid/chad)
- Maintain backward compatibility

**IP2: zen-provider-manager**
- Use existing provider selection
- Leverage cost tracking
- Use health checks

**IP3: zen-orchestrator**
- Use consensus() method
- Pass review-specific prompts
- Aggregate responses

**IP4: Git subprocess**
- `git diff` command
- Error handling
- Output parsing

---

## 11. Success Criteria Mapping

| Success Criterion | Verification Method |
|-------------------|---------------------|
| SC1: `--git-diff` works with multiple LLMs | Integration test: 3+ models |
| SC2: Code review prompts generate high-quality reviews | Manual review of sample outputs |
| SC3: Consensus aggregation provides meaningful synthesis | Test with known issues |
| SC4: Chill/mid/chad modes work as expected | Test each mode configuration |
| SC5: Complexity tax under +5 | Complexity analysis: +3 |
| SC6: Documentation complete and clear | Documentation review checklist |

---

## 12. Open Questions and Decisions Needed

### 12.1 Technical Decisions

1. **Git library**: Subprocess vs GitPython?
   - **Recommendation**: Start with subprocess, add GitPython if parsing becomes complex

2. **Finding extraction**: Regex vs LLM-based parsing?
   - **Recommendation**: Hybrid - regex for structure, LLM for validation

3. **Diff size limits**: What's the maximum diff size?
   - **Recommendation**: Start with 10,000 lines, add chunking if needed

4. **Template storage**: File system vs database?
   - **Recommendation**: File system (YAML files in src/zen/templates/)

### 12.2 User Experience

1. **Default mode**: Which mode should be default?
   - **Recommendation**: `mid` (balanced)

2. **Default review type**: What if user doesn't specify?
   - **Recommendation**: `comprehensive` (all categories)

3. **Output format**: Structured JSON vs readable text?
   - **Recommendation**: Both - text by default, JSON via --export flag

### 12.3 Prioritization

1. **MVP scope**: Which review types for initial release?
   - **Recommendation**: Security and performance (most critical)

2. **Mode availability**: All modes from day 1?
   - **Recommendation**: Yes, all three modes ready at launch

---

## 13. Recommendations

### 13.1 Implementation Priority

1. **Start with Phase 1 + Phase 2** (git integration + prompts)
2. **Test with single model** before adding consensus
3. **Implement aggregation** once single-model works
4. **Add modes** as configuration layer
5. **Polish and document** last

### 13.2 Architecture Recommendations

1. **Keep it simple**: Don't over-engineer finding extraction
2. **Leverage existing**: Maximize reuse of zen* infrastructure
3. **Iterate**: Start with basic aggregation, enhance based on testing
4. **Test early**: Write tests alongside code, not after

### 13.3 Go/No-Go Criteria

**Go Criteria:**
- [ ] Existing zen-consensus tests pass
- [ ] Git diff capture works in target repository
- [ ] At least 2 prompt templates created
- [ ] Basic consensus aggregation logic defined

**No-Go Criteria:**
- Breaking changes to existing zen-consensus
- Complexity tax exceeds +5
- Provider dependencies not available

---

## 14. Next Steps

1. **Approve requirements analysis** - Stakeholder review
2. **Create detailed implementation plan** - Task breakdown with estimates
3. **Set up development environment** - Ensure git access, provider APIs
4. **Begin Phase 1 implementation** - Git diff integration
5. **Continuous testing** - Test each phase before moving to next

---

## Appendix A: Example Usage Scenarios

### A.1 Quick Security Review

```bash
/zen-consensus --git-diff --review-type security --mode chill
```

**Expected Output:**
```markdown
# Security Review Consensus (Chill Mode)

## Models: Mixtral 8x7B, Llama 3.1 70B, Gemma 2 9B
## Files Changed: src/auth.py, config.py

## Critical Findings (Unanimous)
### 1. Hardcoded secret in config.py:10
**Severity**: Critical
**Recommendation**: Move to environment variables

## Summary
- 1 critical issue found
- Review completed in 12 seconds
- Total cost: $0.001
```

### A.2 Comprehensive Review

```bash
/zen-consensus --git-diff --review-type comprehensive --mode chad
```

**Expected Output:**
```markdown
# Comprehensive Code Review Consensus (Chad Mode)

## Models: Claude 3.5, GPT-4 Turbo, Gemini 1.5 Pro, Mixtral 8x22b
## Files Changed: 15 files, +450 lines, -120 lines

## Security Findings
### Critical (2/4 unanimous)
[Detailed findings...]

## Performance Findings
### High (3/4 strong consensus)
[Detailed findings...]

## Bug Detection
### Medium (2/4 moderate consensus)
[Detailed findings...]

## Code Style
### Low (1/4 weak)
[Detailed findings...]

## Aggregated Recommendations
1. [Critical] Fix SQL injection in auth.py
2. [High] Optimize database queries in user_service.py
3. [Medium] Add null checks in data_processor.py
```

### A.3 Custom Model Selection

```bash
/zen-consensus --git-diff --models claude,gemini --review-type performance
```

**Expected Output:**
```markdown
# Performance Review (Custom Models)

## Models: Claude 3.5, Gemini 1.5 Pro
## Review Type: Performance Analysis

## Performance Bottlenecks (2/2 consensus)
[Detailed performance analysis...]
```

---

**End of Requirements Analysis**

---

**Document Version**: 1.0
**Last Updated**: 2025-12-23
**Next Review**: After implementation planning phase
