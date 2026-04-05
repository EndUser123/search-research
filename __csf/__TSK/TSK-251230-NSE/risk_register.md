# Risk Register

**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Project**: CSF NIP Observability Enhancement (Weeks 0-7)

---

## Risk Assessment Framework

| Severity | Definition |
|----------|------------|
| **Critical** | Blocks project, requires immediate escalation |
| **High** | Significant impact, requires mitigation plan |
| **Medium** | Manageable impact, monitor closely |
| **Low** | Minor impact, accept or monitor |

| Likelihood | Definition |
|------------|------------|
| **Almost Certain** | >75% probability |
| **Likely** | 50-75% probability |
| **Possible** | 25-50% probability |
| **Unlikely** | <25% probability |

---

## Project Risks

### R001: Instrumentation Breaks Hook Behavior

| Field | Value |
|-------|-------|
| **ID** | R001 |
| **Category** | Technical |
| **Severity** | High |
| **Likelihood** | Possible |
| **Description** | @hook_observable decorator modifies return value or exception handling, causing hooks to fail silently |
| **Impact** | Hook enforcement bypassed, constitutional violations undetected |
| **Mitigation** | - Unit tests for each decorated hook verifying return semantics<br>- TDD workflow enforced via CWO12<br>- Gradual rollout (6 hooks → 20 → remaining)<br>- `TDD_BYPASS=true` for emergency disable |
| **Owner** | Week 1 Implementation |
| **Status** | Open |

---

### R002: Performance Degradation Exceeds 5%

| Field | Value |
|-------|-------|
| **ID** | R002 |
| **Category** | Performance |
| **Severity** | High |
| **Likelihood** | Possible |
| **Description** | Span timing, trace ID generation, and event queuing add >5% overhead to hook execution |
| **Impact** | User-facing latency increases, response time degrades |
| **Mitigation** | - Baseline profiling before instrumentation (Week 0)<br>- Decorator overhead target <1ms per hook<br>- Sampling strategy for high-volume hooks<br>- Performance regression alerts in dashboard |
| **Owner** | Week 1 Implementation |
| **Status** | Open |

---

### R003: SQLite Write Bottleneck

| Field | Value |
|-------|-------|
| **ID** | R003 |
| **Category** | Technical |
| **Severity** | Medium |
| **Likelihood** | Likely |
| **Description** | High event volume exceeds SQLite write capacity, causing event_queue to block or drop events |
| **Impact** | Lost observability data, incomplete metrics |
| **Mitigation** | - event_queue batching (existing, batch_size=10)<br>- On-demand flushing (C.1 compliant)<br>- Fallback logging to JSONL on failure<br>- Monitor queue_depth gauge<br>- Consider PostgreSQL migration if >1000 events/sec |
| **Owner** | Week 2 Infrastructure |
| **Status** | Open |

---

### R004: Metric Cardinality Explosion

| Field | Value |
|-------|-------|
| **ID** | R004 |
| **Category** | Technical |
| **Severity** | Medium |
| **Likelihood** | Possible |
| **Description** | High-cardinality labels (session_id, trace_id) create excessive metric series, exhausting storage/query capacity |
| **Impact** | Dashboard queries slow, storage costs increase |
| **Mitigation** | - ALLOWED_LABELS allowlist enforced in MetricsCollector<br>- session_id, trace_id prohibited in metric labels<br>- Use DB filters instead of labels for high-cardinality values<br>- Alert on cardinality >1000 series per metric |
| **Owner** | Week 1 Schema Design |
| **Status** | Open |

---

### R005: W3C Trace Context Not Propagated

| Field | Value |
|-------|-------|
| **ID** | R005 |
| **Category** | Technical |
| **Severity** | Medium |
| **Likelihood** | Likely |
| **Description** | Claude Code does not propagate traceparent headers between hook invocations, preventing distributed trace linkage |
| **Impact** | Trace waterfall incomplete, cannot follow request across hooks |
| **Mitigation** | - Store trace_id in session_data JSON file<br>- Reconstruct trace context in each hook invocation<br>- Dashboard queries join by session_id + timestamp window<br>- Future: Propose traceparent propagation to upstream |
| **Owner** | Week 1 Integration |
| **Status** | Open |

---

### R006: Dashboard Queries Too Slow

| Field | Value |
|-------|-------|
| **ID** | R006 |
| **Category** | Performance |
| **Severity** | Medium |
| **Likelihood** | Possible |
| **Description** | SQLite queries for dashboard exceed 1 second, degrading user experience |
| **Impact** | Dashboard unusable, observability insights delayed |
| **Mitigation** | - Materialized views for common aggregations<br>- Indexes on trace_id, hook_name, timestamp<br>- 5-minute refresh for dashboard_hook_performance<br>- Pagination for large result sets<br>- Consider read replica if >100 req/sec |
| **Owner** | Week 2 Dashboard |
| **Status** | Open |

---

### R007: JSONL + SQLite Dual-Write Overhead

| Field | Value |
|-------|-------|
| **ID** | R007 |
| **Category** | Technical |
| **Severity** | Low |
| **Likelihood** | Unlikely |
| **Description** | Maintaining both JSONL files (cc_diagnostic_logger) and SQLite inserts doubles write overhead |
| **Impact** | Minor performance impact, storage duplication |
| **Mitigation** | - Phase 1: Dual-write for backward compatibility<br>- Phase 2: Dashboard queries SQLite, JSONL deprecated<br>- Phase 3: JSONL writes become optional/configurable<br>- event_queue is async, on-demand flush minimizes blocking |
| **Owner** | Week 3 Migration |
| **Status** | Open |

---

### R008: Test Coverage <50%

| Field | Value |
|-------|-------|
| **ID** | R008 |
| **Category** | Quality |
| **Severity** | Medium |
| **Likelihood** | Likely |
| **Description** | Existing hooks lack comprehensive tests, instrumentation may introduce undetected regressions |
| **Impact** | Bugs in production, constitutional enforcement failures |
| **Mitigation** | - TDD workflow enforced via CWO12 TDD State Guard<br>- pytest fixtures for critical 6 hooks<br>- Mock instrumentationutils for unit tests<br>- Integration tests for trace ID propagation<br>- Coverage threshold enforced in CI |
| **Owner** | Week 1 Testing |
| **Status** | Open |

---

### R009: Hook Registry Dependency Graph Incomplete

| Field | Value |
|-------|-------|
| **ID** | R009 |
| **Category** | Technical |
| **Severity** | Medium |
| **Likelihood** | Possible |
| **Description** | Auto-discovery in hook_registry.py fails to detect all dependencies, topological sort produces incorrect execution order |
| **Impact** | Hooks execute in wrong order, enforcement fails |
| **Mitigation** | - Manual dependency declaration fallback<br>- Validation: compare registry order vs. actual execution<br>- Circuit breaker: disable registry if errors detected<br>- Human review of critical hook order |
| **Owner** | Week 4 Registry |
| **Status** | Open |

---

### R010: Constitution Versioning Rollback Fails

| Field | Value |
|-------|-------|
| **ID** | R010 |
| **Category** | Operational |
| **Severity** | High |
| **Likelihood** | Unlikely |
| **Description** | Git-based constitution versioning rollback fails due to merge conflicts or state mismatch |
| **Impact** | Broken constitution remains deployed, extended outage |
| **Mitigation** | - Pre-merge testing: dry-run on staging<br>- Automated rollback script tested weekly<br>- Constitution snapshot stored in SQLite<br>- Manual rollback procedure documented |
| **Owner** | Week 6 Versioning |
| **Status** | Open |

---

### R011: Context Overflow During Discovery

| Field | Value |
|-------|-------|
| **ID** | R011 |
| **Category** | Process |
| **Severity** | Medium |
| **Likelihood** | Possible |
| **Description** | Week 0 discovery accumulates excessive context, triggering OOM before implementation |
| **Impact** | Session restart, lost work |
| **Mitigation** | - CKS handoff after Step 0.5<br>- On-demand CKS queries instead of accumulation<br>- Context usage monitoring (warn at 70%, block at 85%)<br>- `/compact` recommended before Week 0 start |
| **Owner** | CWO12 Workflow |
| **Status** | Open |

---

### R012: Alert Fatigue from False Positives

| Field | Value |
|-------|-------|
| **ID** | R012 |
| **Category** | Operational |
| **Severity** | Low |
| **Likelihood** | Likely |
| **Description** | Dashboard alert thresholds trigger on normal variance, causing alert fatigue |
| **Impact** | Alerts ignored, real issues missed |
| **Mitigation** | - Tuning period: adjust thresholds for first 2 weeks<br>- Hysteresis: alert must persist for 5 minutes<br>- Severity levels: Critical alerts only for P99<br>- Alert suppression during maintenance windows |
| **Owner** | Week 2 Dashboard |
| **Status** | Open |

---

## Risk Summary

| Severity | Count | Risks |
|----------|-------|-------|
| **Critical** | 0 | None |
| **High** | 3 | R001, R002, R010 |
| **Medium** | 7 | R003, R004, R005, R006, R008, R009, R011 |
| **Low** | 2 | R007, R012 |

**Total Active Risks**: 12

---

## Risk Monitoring

### Weekly Risk Review Agenda

1. **Review HIGH risks**: Status update on R001, R002, R010
2. **Close mitigated risks**: Mark as Closed if mitigation verified
3. **Identify new risks**: Add emerging risks from implementation
4. **Update likelihood/severity**: Adjust based on new data

### Risk Triggers

| Trigger | Action |
|---------|--------|
| Any HIGH risk → Likely | Escalate to project lead, daily standup |
| >5 MEDIUM risks → Likely | Review mitigation capacity, reprioritize |
| New CRITICAL risk | Stop the line, emergency protocol |

---

## Mitigation Status

| Risk | Mitigation Implemented | Verification |
|------|------------------------|--------------|
| R001 | Pending | Unit tests pass for decorated hooks |
| R002 | Pending | Baseline profiling complete |
| R003 | Existing | event_queue batching operational |
| R004 | Pending | ALLOWED_LABELS enforced |
| R005 | Pending | session_data trace_id storage |
| R006 | Pending | Dashboard query <1 second |
| R007 | Pending | Dual-write operational |
| R008 | Pending | pytest fixtures created |
| R009 | Pending | Registry validation |
| R010 | Pending | Rollback script tested |
| R011 | Complete | CKS handoff integrated |
| R012 | Pending | Alert tuning complete |

---

**Document Status**: Draft - 12 risks identified
**Next Review**: Week 1 standup
