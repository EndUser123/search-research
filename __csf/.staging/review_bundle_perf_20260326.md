# Review Bundle: /perf Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/perf/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: perf
- **Description**: Performance tracing wrapper for Python - detects anti-patterns like nested ThreadPoolExecutors
- **Category**: utilities
- **Trigger**: /perf
- **Aliases**: /perf

### Domain & Purpose
Detects performance anti-patterns in Python code execution (nested ThreadPoolExecutors, resource waste).

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: AID, /bug-hunt, /analyze

---

## 2. DIFFERENTIATION

**IMPORTANT:** `/perf` is NOT the same as `/profile`:
- `/perf` - Anti-pattern detection (what's wrong?)
- `/profile` - Performance measurement (how fast? baseline vs comparison)

---

## 3. AID INTEGRATION (v1.1.0)

**Enhanced performance analysis via AI Distiller:**

```bash
aid <path> --ai-action prompt-for-performance-analysis
```

**AID `prompt-for-performance-analysis` provides:**
- **Algorithmic Complexity**: O(n²) → O(n log n) optimization opportunities
- **N+1 Detection**: Database/API query batching opportunities
- **Async Anti-patterns**: Blocking I/O in async functions
- **Profiling Guidance**: What to profile and where
- **Scalability Analysis**: Bottlenecks under load

---

## 4. AUTO-DETECTS

- Nested ThreadPoolExecutors
- ProcessPoolExecutor nesting (expensive IPC overhead)
- Per-worker resource creation patterns
- Thread count vs CPU cores (warns if workers > cores*2)
- Threshold-based alerts (configurable)

---

## 5. USAGE

```bash
# Trace Python scripts
/perf python my_script.py --arg value

# Trace pytest runs
/perf pytest tests/test_parallel.py

# Trace Python modules
/perf python -m mymodule
```

---

## 6. DISABLE TRACING

Set `PERF_TRACE=0` to disable:
```bash
PERF_TRACE=0 /perf python my_script.py
```

---

## 7. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 132-line SKILL.md |
| Performance Detection | EXCELLENT | Anti-pattern detection |

### SQA Relevance
- **HIGH** — Performance anti-pattern detection skill
- Detects nested ThreadPoolExecutors
- Warns on ProcessPoolExecutor nesting
- Thread count vs CPU core analysis
- AID integration for enhanced analysis
