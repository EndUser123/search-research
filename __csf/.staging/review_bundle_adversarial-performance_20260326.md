# Review Bundle: /adversarial-performance Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/adversarial-performance/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: adversarial-performance
- **Description**: Performance analysis with focus on async bottlenecks, cache efficiency, and N+1 patterns
- **Category**: analysis
- **Trigger**: /adversarial-performance
- **Aliases**: /perf-review, /performance

### Domain & Purpose
Analyzes code, architecture, and systems to find performance bottlenecks, N+1 query patterns, cache inefficiencies, and async execution issues.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: AI Distiller, adversarial review framework

---

## 2. PERFORMANCE TARGETS

| Target | Threshold |
|--------|-----------|
| FAST mode latency | <1s |
| COMPREHENSIVE mode | 5-10s |
| Cache lookup | <10ms |
| Backend health detection | 24h |

---

## 3. PERFORMANCE CATEGORIES

### 1. Timeout Detection
Find operations exceeding SLA targets:
- FAST mode: >1s local queries
- COMPREHENSIVE mode: >10s web queries
- Cache lookups: >10ms

### 2. Bottleneck Analysis
Identify blocking operations:
- Synchronous I/O in async functions
- Sequential operations that should be parallel
- CPU-bound work blocking event loop
- Lock contention

### 3. Cache Efficiency
Find cache problems:
- Cache miss rate >50%
- TTL too short (<300s)
- LRU thrashing (size too small)
- No caching for expensive operations

### 4. N+1 Query Detection
Find repeated backend calls:
- Looping over backends sequentially
- Fetching same data multiple times
- Result aggregation triggers re-fetching

### 5. Concurrent Execution Issues
Identify concurrency problems:
- Race conditions in shared state
- Deadlock risks
- Thread pool exhaustion
- Event loop blocking

---

## 4. SELF-VERIFICATION REQUIREMENT

**Before claiming performance issues exist, verify bottleneck is real:**

1. **Located the code** - Read actual implementation
2. **Measured or traced** - Evidence of actual performance impact
3. **Hot path confirmed** - Code is on frequently-executed path

---

## 5. FINDINGS FORMAT

```json
{
  "findings": [
    {
      "id": "PERF-XXX",
      "title": "Descriptive title",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "triage": "nit|fix_before_merge|pre-existing",
      "category": "Timeout|Bottleneck|Cache|N+1|Concurrency",
      "location": "file:line or module description",
      "performance_impact": "What slows down and by how much",
      "evidence": "Code snippet or architectural description",
      "suggested_fix": "How to fix",
      "expected_improvement": "Quantitative improvement"
    }
  ]
}
```

---

## 6. DIRECTOR MODEL CONSTITUTIONAL FILTER

**Prohibited (enterprise bloat):**
- Micro-optimizations with <500ms savings when current perf <1000ms
- Over-engineering for hypothetical scale
- Complex caching for rare queries

**ALLOWED:**
- Actual bottlenecks measured (>500ms impact)
- N+1 query patterns (10-1000x impact)
- Cache misconfiguration (50%+ miss rate)
- Async blocking issues (2-10x slowdown)
- API timeout cascades

---

## 7. OUTPUT FORMAT

```json
{
  "review_metadata": {
    "skill": "target-name",
    "review_type": "adversarial-performance",
    "timestamp": "ISO-8601",
    "performance_targets": {
      "fast_mode_slack": "<1s",
      "comprehensive_mode_slack": "5-10s",
      "cache_lookup_slack": "<10ms"
    }
  },
  "findings": [...]
}
```

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 199-line SKILL.md with detailed patterns |
| Performance Analysis | EXCELLENT | 5-category analysis framework |

### SQA Relevance
- **HIGH** — Performance analysis skill
- Detects N+1 patterns, cache inefficiencies, async bottlenecks
- Self-verification requirement prevents false positives
- Triage categories for prioritization
