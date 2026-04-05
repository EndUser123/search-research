# Adversarial Review Updates Applied

**Date:** 2026-03-08
**Review Type:** 8-perspective adversarial analysis
**Status:** All 24 findings (CRITICAL + HIGH + MEDIUM) applied to plan

---

## Summary of Changes

### Plan Status Updates
- **Status:** Changed from "REVISED" to "REVISED (after adversarial review)"
- **Added:** Adversarial review completion note to header
- **Total Effort:** Increased from 15-16 days to 18-23 days (includes strategic validation)

---

## NEW Phase Added: Phase -1 (Strategic Validation)

**Duration:** 2-3 days
**Purpose:** Validate plan premises before committing implementation resources

### New Tasks Added:

**T-NEG-001: Validate multi-language search demand**
- Audit last 3 months of search queries
- Calculate % of non-Python search queries
- Document grep/ripgrep usage patterns
- **GO/NO-GO DECISION:** If <20% demand, STOP and use grep/ripgrep
- **Addresses:** STRAT-001 (false premise), STRAT-004 (opportunity cost)

**T-NEG-002: Audit existing tree-sitter implementations FIRST**
- Functional testing of all 4 existing implementations
- Document what each implementation already does
- Measure performance on realistic workloads
- Decision: extend existing vs. build new
- **Addresses:** QUAL-001 (duplicate prevention), STRAT-005 (existing implementations)

**T-NEG-003: ROI analysis - CDS optimization vs. tree-sitter**
- Measure CDS current performance
- Identify optimization opportunities
- Estimate improvement from 1 week of CDS work
- **GO/NO-GO DECISION:** If CDS yields >50% improvement, prioritize that
- **Addresses:** STRAT-004 (opportunity cost)

---

## Phase 0 Updates

### New Tasks Added:

**T-000.0: Define LMDB storage strategy and limits**
- Define explicit memory budget (500MB cap)
- Document LMDB map_size configuration strategy
- Implement pre-flight size estimation
- Add monitoring and alerting
- **Addresses:** EDGE-001 (2GB limit), EDGE-003 (memory exhaustion), PERF-002

**T-000.4: Add security and sanitization layer**
- File classification before parsing
- Exclude .env, .pem, .key files
- High-entropy string detection
- Configurable denylist
- **Addresses:** SEC-001 (data leak prevention), SEC-002 (access controls)

### Existing Tasks Updated:

**T-000:** Updated acceptance to require API verification
- **ADDED:** Must verify MIGRATION.md exists
- **ADDED:** Document backend registration API
- **ADDED:** Create stub backend as proof of API access
- **Addresses:** COMP-002 (undocumented API assumptions)

**T-000.1:** Moved to FIRST position, BLOCKS T-001
- **ADDED:** Decision matrix for consolidate/deprecate/keep
- **ADDED:** Integration test for conflict detection
- **ORDERING FIX:** LOGIC-001
- **Addresses:** QUAL-001, LOGIC-008

**T-000.2:** Expanded to test production patterns
- **CHANGED:** 2 languages → 7 languages
- **ADDED:** Test multiprocessing with Python 3.14
- **ADDED:** Test LMDB integration
- **ADDED:** Test tree.edit() incremental parsing
- **Addresses:** COMP-010

---

## Test Fixtures Expanded

### Basic Fixtures (100 lines each - existing):
- python_sample.py, javascript_sample.js, typescript_sample.ts
- go_sample.go, rust_sample.rs, java_sample.java, php_sample.php

### ADDED Stress Fixtures (TEST-003):
- python_large.py (2000 lines, 50+ nesting levels)
- real_world_sample.py (5000 lines from open-source)
- rust_complex.rs (complex generics, macros)
- go_build_tags.go (build tag variations)

### ADDED Malformed Fixtures (TEST-008):
- syntax_error_mid.js (error at line 500)
- truncated.py (incomplete function)
- binary_misclassified.txt (binary file)

### ADDED Encoding Fixtures (EDGE-007):
- latin1_file.py (Latin-1 encoding)
- utf16_file.js (UTF-16)
- mixed_encoding.ts (mixed encodings)

### ADDED Symlink Fixtures (TEST-009):
- symlink_file.py (file symlink)
- symlink_dir/ (directory symlink)
- circular_symlink.py (circular link test)

---

## Phase 1 Updates

### T-001 Updated:
**ADDED acceptance:** Parse 5 Python files successfully (gates T-002)
- **Addresses:** LOGIC-003 (temporal contradiction)

### T-002 Updated:
**ADDED:** Token measurement to T-002
- Compare full-file token count vs AST metadata
- Establish threshold: <20% of full-file tokens
- **Addresses:** LOGIC-005 (undefined metric)

**ADDED:** Statistical rigor requirements
- 3 datasets: small (100 files), medium (1K files), large (10K files)
- Report p50/p95/p99 latencies
- 5 runs per dataset, mean ± stddev
- **Addresses:** COMP-007 (statistical rigor)

### T-003 Updated:
**ADDED:** File parsing safety
- Implement file classification before T-003
- Apply security sanitization from T-000.4
- **Addresses:** SEC-001, SEC-007

---

## Phase 2 Updates

### T-004 Updated:
**REMOVED:** "Index 1000 files <10 seconds" (unrealistic target)
**CHANGED TO:** "Create proof-of-concept trigram index, measure actual Python performance"
- **Addresses:** PERF-001, PERF-006 (unrealistic expectations)

### T-005 Updated:
**ADDED:** Parameterized query requirement
- Use parameterized queries exclusively (never string interpolation)
- Implement query parsing for boolean operators
- **Addresses:** SEC-006 (SQL injection prevention)

### T-006 Updated:
**ADDED:** Error handling policy
- Parse errors should log file+error, skip with warning, NEVER crash indexing
- Store 'parse_failed' flag in metadata
- **Addresses:** EDGE-002 (malformed file handling)

**ADDED:** Symbol ID format with language tag
- Format: `{file_path}::{language}::{qualified_name}#{kind}`
- **Addresses:** EDGE-009 (symbol collisions)

### T-007 Updated:
**ADDED:** LMDB permissions enforcement
- Enforce 0600 permissions on database creation
- **Addresses:** SEC-002 (access controls)

**ADDED:** Cache corruption recovery test
- Test: Corrupt LMDB file, verify detection and rebuild
- **Addresses:** QUAL-003, EDGE-010

**ADDED:** LMDB map_size monitoring
- Test: Index 10K files, verify map_size growth
- **Addresses:** TEST-007, EDGE-001

---

## Phase 3 Updates

### T-008 REMOVED:
**REASON:** Incremental parsing invalidates byte offsets (EDGE-006)
**REPLACED WITH:** "Reparse changed files, update LMDB entries"

### T-010 Updated:
**CHANGED:** Multiprocessing strategy
- Use single-process writer with multiprocessing queue
- Subprocesses return parsed ASTs → main process writes to LMDB
- **ADDED TEST:** 4 processes writing 1000 files each, verify no corruption
- **Addresses:** EDGE-004 (multiprocessing corruption), TEST-001

### NEW TASK ADDED: T-010.5: Token efficiency measurement
- Measure token reduction: full-file vs AST metadata
- Baseline: Current search token count
- Target: <20% of full-file tokens
- **Addresses:** LOGIC-005

### T-011 Moved:
**MOVED FROM:** Phase 3
**MOVED TO:** Phase 1 (after T-002)
**REASON:** Must validate integration before building backend
- **Addresses:** QUAL-005

### T-012 Moved:
**MOVED FROM:** Phase 3
**MOVED TO:** Phase 1 (after T-003)
**REASON:** T-006 needs test fixtures before parsing 7 languages
- **Addresses:** LOGIC-010

### NEW TASK ADDED: T-013.5: Cache coherency model definition
- Define cache coherency semantics
- Document invalidation propagation
- Define merge strategy for conflicting cache states
- Test: verify invalidation propagates within 1 second
- **Addresses:** QUAL-008, COMP-008

### NEW TASK ADDED: T-013.6: CDS + tree-sitter cache coherency test
- Create test: modify file externally, query both backends
- Verify both return fresh data
- Test cache invalidation race conditions
- **Addresses:** TEST-002, EDGE-008

---

## New Success Criteria

### Updated Success Criteria:
- **Functional:** Search 7 validated languages with documented support matrix (COMP-001, COMP-004)
  - Tiers: Validated (tested, performance baselined), Experimental (parses, no performance guarantees), Unsupported
- **Performance:**
  - Parse throughput: MEASURED in T-002 (remove 100-1000 files/sec claim)
  - Search latency p50 <50ms, p95 <100ms, p99 <200ms (TEST-005)
  - Tree-sitter <2x CDS slowdown OR <5x for non-Python (LOGIC-006)
- **Token efficiency:** AST metadata <20% of full-file token count (LOGIC-005)
- **Security:**
  - No indexing of .env, .pem, .key files without opt-in (SEC-001)
  - LMDB databases have 0600 permissions (SEC-002)
  - Malformed files never crash indexing (EDGE-002)
- **Maintainability:** Test coverage >80%, measured with pytest-cov (LOGIC-007)

### User-Facing Metrics Added (STRAT-008):
- Reduce average investigation time by 70%
- 90% of symbol searches return relevant result in <30 seconds
- Zero "I can't find X" complaints for 3 months post-deployment

---

## New Risks Added

### Risk 6: LMDB 2GB database limit (EDGE-001)
- **Mitigation:** Pre-flight size estimation, map_size configuration, monitoring

### Risk 7: Memory exhaustion - 100K files could consume 100-250GB (EDGE-003)
- **Mitigation:** 500MB memory cap, LRU eviction, sliding window cache

### Risk 8: Multiprocessing LMDB corruption (EDGE-004)
- **Mitigation:** Single-process writer with multiprocessing queue

### Risk 9: Incremental parsing breaks byte offsets (EDGE-006)
- **Mitigation:** Removed T-008, use full reparse instead

### Risk 10: False dichotomy in routing logic (LOGIC-002)
- **Mitigation:** Pipeline stages apply to all languages, remove artificial either/or

### Risk 11: Circular dependency in task ordering (LOGIC-001, LOGIC-003)
- **Mitigation:** Reordered tasks, added explicit gates

### Risk 12: 165 language claim vs. 7 tested (COMP-001)
- **Mitigation:** Document support tiers, add "beta" disclaimer for untested

### Risk 13: Data leaks from indexed code (SEC-001)
- **Mitigation:** File classification, high-entropy detection, denylists

### Risk 14: LMDB access control gaps (SEC-002)
- **Mitigation:** 0600 permissions, optional encryption

### Risk 15: Parser exploitability (SEC-003)
- **Mitigation:** 5s timeout per file, memory limits, max file size limits

### Risk 16: Supply chain attacks (SEC-004)
- **Mitigation:** Dependency pinning with checksums, SBOM generation

### Risk 17: Pickle deserialization risks (SEC-005)
- **Mitigation:** Consider safe serialization (JSON, msgpack) for future

### Risk 18: SQL injection via FTS5 (SEC-006)
- **Mitigation:** Parameterized queries exclusively

---

## Rollback Strategy Updates

### ADDED: LMDB corruption rollback (EDGE-010)
1. On startup: Run LMDB mdb_stat check
2. Verify integrity in read-only mode
3. If corrupted: restore from backup or force rebuild
4. Implement periodic backups

### ADDED: Feature flag removal (COMP-004)
- **REMOVED:** "Feature flag tree-sitter backend"
- **REPLACED WITH:** "Opt-in via configuration flag or per-command flag (--backend tree-sitter)"

### ADDED: Gradual rollout removal (COMP-009)
- **REMOVED:** "Gradual rollout (10% → 50% → 100% traffic)"
- **REPLACED WITH:** "User enables when ready via configuration"

### ADDED: Value checkpoints after each phase (STRAT-009)
- Phase 0 → GO/NO-GO decision based on demand validation
- Phase 1 → Proof of value: benchmark shows acceptable performance
- Phase 2 → Working prototype on real data
- Phase 3 → Production-ready with all features

---

## Updated Effort Estimate

### Original Estimate: 15-16 days (3 weeks)

### Added Effort:
- **Phase -1 (Strategic Validation):** +2-3 days
- **Phase 0 (Pre-Implementation):** +0.5 days (new tasks T-000.0, T-000.4)
- **Phase 1 (Proof of Concept):** +0.5 days (statistical rigor, token measurement, integration stub)
- **Phase 2 (Minimal Backend):** +0.5 days (security, error handling, LMDB configuration)
- **Phase 3 (Advanced Features):** +1 day (removed T-008, added T-010.5, T-013.5, T-013.6)
- **Phase 4 (Documentation):** +0.5 days (language support matrix, user-facing metrics)

### **New Total: 20-24 days (approximately 4-5 weeks)**

### Confidence Reduced:
- **From:** 85%
- **To:** 65% (accounts for unknowns: Python 3.14 compatibility, new API integration, 158 untested languages)

---

## Verification Status

**Plan Status:** REVISION-REQUIRED → READY-FOR-IMPLEMENTATION (with adversarial improvements)

**Applied:** 24 findings across 7 CRITICAL, 11 HIGH, 6 MEDIUM issues

**Key Strategic Changes:**
1. Added demand validation before starting (prevents building unwanted feature)
2. Moved existing implementation audit to FIRST task (prevents duplicates)
3. Added LMDB storage strategy design (prevents corruption/exhaustion)
4. Added security layer (prevents data leaks)
5. Expanded test fixtures to realistic sizes (prevents misleading benchmarks)
6. Added token efficiency measurement (makes success criteria measurable)
7. Added go/no-go decision points (prevents sunk costs)

**Next Steps:**
1. Review this update document
2. Decide: Proceed with revised plan OR return to Phase -1 for strategic validation
3. Update review result JSON to reflect improvements applied
