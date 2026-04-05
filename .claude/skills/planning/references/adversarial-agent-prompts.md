# Adversarial Agent Dispatch Prompts

Reference for Step 4b: Dispatch ALL 6 agents in ONE message (parallel).

## Compaction Resilience -- Idempotent Agents

Each agent prompt prepends a pre-flight check: if its output file already exists and is non-empty, skip execution and return the path immediately. This means:
- Agents that completed before compaction return existing file path instantly (no re-run)
- Agents that didn't run execute normally
- After compaction, re-dispatch the same 6 agents with the same prompts; already-complete agents skip themselves
- The orchestrator only needs to check which output files exist to know what's done

## Agent Prompts

```python
# ALL 6 agents dispatched simultaneously in a single message
# Each writes findings to file and returns ONLY the path
# Each agent checks: if output file exists, skip and return path immediately

# MANDATORY: Each prompt explicitly states the plan path.
# Agents MUST read ONLY the specified plan - no fallback, no other plan.

Task(subagent_type="adversarial-compliance",
     description="Compliance review",
     prompt="""MANDATORY: You MUST review ONLY the plan at this exact path:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/compliance-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

Do NOT assume or infer the plan content. Read the file at <plan_path> first.

1. Review the plan at <plan_path> for specification violations and solo-dev constraints.
   - For stateful/history/provider/multi-terminal plans, explicitly check identity model completeness, source-of-truth declarations, and unresolved implementation-shaping open questions.
2. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/compliance-findings.json
   - Include field: "plan_path": "<plan_path>"
3. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/compliance-findings.json" """)

Task(subagent_type="adversarial-logic",
     description="Logic review",
     prompt="""MANDATORY: You MUST review ONLY the plan at this exact path:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/logic-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

Do NOT assume or infer the plan content. Read the file at <plan_path> first.

1. Review the plan at <plan_path> for pure logic errors, race conditions, and off-by-one bugs.
   - For stateful/history/provider/multi-terminal plans, explicitly compare prose behavior against keys, schema snippets, and contract sections.
   - Flag contradictory ordering rules, dedupe rules, or identity semantics as logic findings.
2. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/logic-findings.json
   - Include field: "plan_path": "<plan_path>"
3. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/logic-findings.json" """)

Task(subagent_type="adversarial-testing",
     description="Testing review",
     prompt="""MANDATORY: You MUST review ONLY the plan at this exact path:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/testing-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

Do NOT assume or infer the plan content. Read the file at <plan_path> first.

1. Review the plan at <plan_path> for coverage gaps and brittle tests.
2. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/testing-findings.json
   - Include field: "plan_path": "<plan_path>"
3. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/testing-findings.json" """)

Task(subagent_type="adversarial-security",
     description="Security review",
     prompt="""MANDATORY: You MUST review ONLY the plan at this exact path:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/security-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

Do NOT assume or infer the plan content. Read the file at <plan_path> first.

1. Review the plan at <plan_path> for data exposure and access control issues.
2. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/security-findings.json
   - Include field: "plan_path": "<plan_path>"
3. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/security-findings.json" """)

Task(subagent_type="adversarial-failure-modes",
     description="Failure modes review",
     prompt="""MANDATORY: You MUST review ONLY the plan at this exact path:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/failure-modes-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

Do NOT assume or infer the plan content. Read the file at <plan_path> first.

1. Review the plan at <plan_path> for domain-aware failure mode discovery.
   - For stateful/history/provider/multi-terminal plans, explicitly check stale-data invalidation, replay triggers, watermark advancement, and cache/archive authority boundaries.
   - Deferred freshness semantics count as blocker/high findings when the plan claims stale-data immunity or durable retention.
2. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/failure-modes-findings.json
   - Include field: "plan_path": "<plan_path>"
3. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/failure-modes-findings.json" """)

Task(subagent_type="adversarial-critic",
     description="Critic review",
     prompt="""MANDATORY: You MUST analyze findings from this specific plan review:
<plan_path>

Validate idempotency before running — skip if valid findings already exist:
python -c "
import sys, json, time, os
fpath = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/critic-findings.json'
if not os.path.exists(fpath):
    sys.exit(1)
try:
    data = json.loads(open(fpath, encoding='utf-8').read())
    age = time.time() - os.path.getmtime(fpath)
    if data.get('plan_path') == r'<plan_path>' and age < 86400:
        print(fpath)
        sys.exit(0)
    # plan_path mismatch or file too old — delete stale file and run agent
    os.remove(fpath)
except (json.JSONDecodeError, KeyError, OSError):
    if os.path.exists(fpath):
        os.remove(fpath)
pass
sys.exit(1)
"
If the above script prints a path, return ONLY that path.

1. Read all adversarial findings files from: P:/.claude/plans/adversarial/{sanitized_plan_name}/
   - SKIP any file whose plan_path field does not match <plan_path>
2. Perform meta-analysis of consensus, blind spots, calibration for the plan at <plan_path>
   - Specifically look for consensus gaps around identity model, ordering, dedupe, invalidation, event source-of-truth, and isolation boundaries.
3. Write JSON findings to: P:/.claude/plans/adversarial/{sanitized_plan_name}/critic-findings.json
   - Include field: "plan_path": "<plan_path>"
4. Return ONLY: "P:/.claude/plans/adversarial/{sanitized_plan_name}/critic-findings.json" """)
```

## Rate Limit Retry Protocol (Step 4b-retry)

After agents return from Step 4b, Claude MUST check which agents produced valid findings files. Rate limits (429 errors) are temporary -- retry automatically.

```python
# Retry check: After all agents return, verify findings files exist
# For each agent, check: does {sanitized_dir}/{agent}-findings.json exist and contain valid JSON with matching plan_path?

import json, os, time

ADVERSARIAL_DIR = r'P:/.claude/plans/adversarial/{sanitized_plan_name}/'
PLAN_PATH = r'<plan_path>'

expected_agents = [
    'compliance', 'logic', 'testing',
    'security', 'failure-modes', 'critic'
]

def check_findings():
    """Return list of agents that did NOT produce valid findings."""
    missing = []
    for agent in expected_agents:
        fpath = os.path.join(ADVERSARIAL_DIR, f'{agent}-findings.json')
        if not os.path.exists(fpath):
            missing.append(agent)
            continue
        try:
            data = json.loads(open(fpath, encoding='utf-8').read())
            if data.get('plan_path') != PLAN_PATH:
                missing.append(agent)  # Wrong plan — stale file
        except (json.JSONDecodeError, OSError):
            missing.append(agent)  # Corrupt file
    return missing

missing = check_findings()
if missing:
    print(f"RETRY_NEEDED: {len(missing)} agents need retry: {missing}")
    # Re-dispatch ONLY the missing agents (same prompts, same plan_path)
    # The idempotency check in each prompt ensures completed agents skip themselves
else:
    print("ALL_COMPLETE: All 6 adversarial reviews produced findings")
```

### Retry Procedure

1. **Check**: After all 6 agents return, run the check script above
2. **Retry 1**: Re-dispatch ONLY the failed agents (same prompts, same `plan_path`). The idempotency pre-flight check ensures completed agents skip instantly.
3. **Retry 2**: If agents still fail after Retry 1, wait briefly and re-dispatch failed agents one more time
4. **Give up gracefully**: After 3 total attempts (initial + 2 retries), proceed with whatever findings exist. Write the review summary noting which agents failed: "Rate-limited after 3 attempts: [agent list]"
5. **Never block indefinitely**: Maximum 3 total attempts per agent. Do NOT loop forever.

**Why this works**: The idempotency pre-flight check (already in every agent prompt) means re-dispatching all 6 agents is safe -- completed agents return their existing file path instantly. You can re-dispatch ALL agents for simplicity, or just the failed ones for efficiency.

**Retry dispatch pattern**: Use the exact same prompts from Step 4b. No modifications needed -- the idempotency check handles deduplication.
