# Competence Layer Phase 2: Self-Improvement, Reflection, and Metrics

> **For simpler LLM implementation** - Apply these additions after core competence layer (Phase 1) is implemented.

Assume following from Phase 1 already work:
- `competence_events` table and `CompetenceStateStore` (`competence_state.py`).
- `risk_policy.json`, `skill_output_contracts.json`, and `competence_taxonomy.json`.
- Contracts + enforcement for `/research`, `/debugRCA`, `/task`, `/think`.
- Hook wiring (UserPromptSubmit, PreToolUse, command_execution_validator, Stop).

Do NOT redesign Phase 1. Only extend it.

---

## 1. Golden-path evals and `/run-evals` helper

### 1.1 Golden cases (concept only)

I will maintain a small JSON file manually, for example:

`P:\.claude\hooks\config\golden_evals.json`:

```json
{
  "research": [
    {
      "name": "auth_guide",
      "prompt": "/research \"How do I implement auth in a FastAPI app?\"",
      "notes": "Expect actionable recommendations and multiple sources."
    }
  ],
  "debugRCA": [
    {
      "name": "env_keyerror",
      "prompt": "/debugRCA \"App crashes with KeyError: 'DATABASE_URL'\"",
      "notes": "Expect clear root cause and verification plan."
    }
  ]
}
```

You do NOT need to populate it; just assume it exists and has 5-20 cases per skill.

### 1.2 New script/skill `/run-evals`

Create a script (and wire it as a skill if needed) that:

- Reads `golden_evals.json`.
- For each case, triggers a prompt **through the same hooks** (or describes how I should run them manually).
- Then queries `competence_events` to compute simple metrics.

Define a new Python module:

`P:\.claude\hooks\evals\run_evals.py`:

```python
def run_golden_evals(
    session_id: str,
    terminal_id: str,
    limit_per_skill: int = 20
) -> dict:
    """
    High-level:
    - For now, assume I run prompts myself in that session/terminal.
    - You just read competence_events and aggregate metrics for those golden prompts.

    Returns a dict like:
    {
      "research": {
        "cases": N,
        "complete_contract_rate": 0.0-1.0,
        "avg_block_rate": 0.0-1.0
      },
      "debugRCA": { ... }
    }
    """
```

The function should:
- Use `CompetenceStateStore.get_recent_events()` to find events matching golden prompts (e.g. by `user_prompt_snippet LIKE` or matching on `skill_name` + recent timestamps).
- Count:
  - Number of events with `skill_name == "research"` and `contract_status.status == "complete"`.
  - Number of blocks for that skill.

- Return a summary dict.
```

Also add a simple CLI entry:

```python
if __name__ == "__main__":
    import os, json
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    store = CompetenceStateStore(session_id=session_id, terminal_id="")
    summary = run_golden_evals(session_id, "")
    print(json.dumps(summary, indent=2))
```

I will wire this into a `/run-evals` skill or run it manually.

---

## 2. Stronger self-reflection on selected turns

We only want extra reflection on **important** turns:

- `/research` or `/debugRCA`
- AND either medium/high risk
- OR user gave negative feedback for that turn

### 2.1 Extend `competence_events` to store reflection

In `competence_schema.sql`, ensure `metadata_json` is present (Phase 1 already has it). We will store reflection info there; no new columns needed.

### 2.2 Add a small reflection helper module

Create `P:\.claude\hooks\competence\reflection.py`:

Implement:

```python
from typing import Any, Dict

def build_reflection_prompt(
    skill_name: str,
    task_type: str,
    user_prompt: str,
    response_text: str
) -> str:
    """
    Build a short meta-prompt asking model to reflect on its own answer.

    This is NOT returned to user; it's used to generate a reflection summary.
    """
    # For now, handle two task types explicitly
    if task_type == "research":
        questions = [
            "Did I fully answer the user's core question?",
            "Are my recommendations specific and actionable, or generic?",
            "What evidence could falsify my main conclusion?",
            "How confident am I (low/medium/high) and why?"
        ]
    elif task_type == "debug_rca":
        questions = [
            "Is the stated root cause strongly supported by evidence?",
            "What alternative causes did I consider and reject?",
            "What evidence would falsify my chosen root cause?",
            "How confident am I (low/medium/high) and why?"
        ]
    else:
        questions = [
            "Did I actually address the user's request?",
            "What is one weakness in this answer?"
        ]

    joined = "\n".join(f"- {q}" for q in questions)
    return (
        "You are reflecting on your own previous answer.\n\n"
        f"User prompt:\n{user_prompt}\n\n"
        f"Your answer:\n{response_text[:2000]}\n\n"
        "Now answer these reflection questions briefly:\n"
        f"{joined}\n"
        "Return a short bullet list."
    )


def should_run_reflection(event: Dict[str, Any]) -> bool:
    """
    Decide whether to trigger reflection for this event.

    event is a record from competence_events or a Stop hook context.
    """
    skill = event.get("skill_name", "")
    risk_level = event.get("risk_level", "low")
    rating = event.get("user_feedback", "unknown")

    if skill not in ("research", "debugRCA"):
        return False

    if risk_level in ("medium", "high"):
        return True

    if rating == "bad":
        return True

    return False
```

You do NOT need to implement actual extra LLM call; just:

- Provide this helper.
- Update comments/hooks where reflection could be called.

### 2.3 Wire reflection into Stop hook (design)

In `Stop.py`:

- After you have final response and contract validation, but before writing final `competence_events` audit entry:

- Build an `event` dict including `skill_name`, `task_type`, `risk_level`, and optionally `user_feedback` if available.
- Call `should_run_reflection(event)`.

- If `True`, then:
  - (Comment/pseudo) "Here we would call model with `build_reflection_prompt(...)` and store result in `metadata_json['reflection']` via `append_audit_event`."

I will later decide whether to add that extra LLM call.

---

## 3. Config-driven adaptation rules

We want a simple place to encode "if metric X, then tweak Y", but for now only in **human-readable form**, not auto-executed code.

Create:

`P:\.claude\hooks\config\adaptation_rules.json`:

```json
{
  "rules": [
    {
      "id": "relax_research_contract_when_often_incomplete",
      "skill": "research",
      "metric": "complete_contract_rate",
      "window": "7d",
      "condition": "<0.7",
      "suggested_action": "Either improve prompts/templates for actionable_recommendations or temporarily treat missing next_step_question as warn instead of block."
    },
    {
      "id": "tighten_debugRCA_when_feedback_bad",
      "skill": "debugRCA",
      "metric": "user_negative_feedback_rate",
      "window": "7d",
      "condition": ">0.2",
      "suggested_action": "Strengthen debug_rca reasoning template; require explicit alternative hypotheses and falsification evidence."
    }
  ]
}
```

No automation yet. This is for `/audit-quality` skill to read and propose changes.

---

## 4. `/audit-quality` v2

Create a new module:

`P:\.claude\hooks\evals\audit_quality.py`:

Implement:

```python
from typing import Any, Dict, List
from competence_state import CompetenceStateStore
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

ADAPTATION_RULES_PATH = Path("P:\\.claude\\hooks\\config\\adaptation_rules.json")


def load_adaptation_rules() -> List[Dict[str, Any]]:
    try:
        if ADAPTATION_RULES_PATH.exists():
            return json.loads(ADAPTATION_RULES_PATH.read_text(encoding="utf-8")).get("rules", [])
    except Exception:
        return []
    return []


def summarize_quality(
    session_id: str,
    days: int = 7
) -> Dict[str, Any]:
    """
    Summarize quality over the last N days from competence_events.
    """

    store = CompetenceStateStore(session_id=session_id, terminal_id="")
    conn = store._connect()
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Basic aggregate: by skill_name
        rows = conn.execute(
            """
            SELECT skill_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN contract_status='complete' THEN 1 ELSE 0 END) as complete_contracts,
                   SUM(CASE WHEN action_taken='blocked' THEN 1 ELSE 0 END) as blocked
            FROM competence_events
            WHERE ts >= ?
            GROUP BY skill_name
            """,
            (cutoff,),
        ).fetchall()

        skills = {}
        for r in rows:
            total = r["total"] or 0
            complete = r["complete_contracts"] or 0
            blocked = r["blocked"] or 0
            rate = float(complete) / total if total else 0.0
            block_rate = float(blocked) / total if total else 0.0
            skills[r["skill_name"]] = {
                "total_events": total,
                "complete_contract_rate": rate,
                "block_rate": block_rate,
            }

        return {"skills": skills}
    finally:
        conn.close()


def apply_rules(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate adaptation_rules.json against a summary and return human-readable suggestions.
    No automatic changes are applied.
    """
    rules = load_adaptation_rules()
    skills = summary.get("skills", {})
    suggestions: List[Dict[str, Any]] = []

    for rule in rules:
        skill = rule.get("skill")
        metric = rule.get("metric")
        condition = rule.get("condition", "")
        action = rule.get("suggested_action", "")

        skill_metrics = skills.get(skill)
        if not skill_metrics:
            continue

        value = skill_metrics.get(metric)
        if value is None:
            continue

        try:
            if _condition_matches(value, condition):
                suggestions.append(
                    {
                        "rule_id": rule.get("id"),
                        "skill": skill,
                        "metric": metric,
                        "value": value,
                        "suggested_action": action,
                    }
                )
        except Exception:
            continue

    return suggestions


def _condition_matches(value: float, condition: str) -> bool:
    condition = condition.strip()
    if condition.startswith("<"):
        threshold = float(condition[1:].strip())
        return value < threshold
    if condition.startswith(">"):
        threshold = float(condition[1:].strip())
        return value > threshold
    return False
```

Add a small CLI entry:

```python
if __name__ == "__main__":
    import os
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    summary = summarize_quality(session_id, days=7)
    suggestions = apply_rules(summary)
    print(json.dumps({"summary": summary, "suggestions": suggestions}, indent=2))
```

I will wire this as `/audit-quality`.

---

## 5. Sensitivity and environment-aware risk (minimal)

Add an optional notion of "sensitivity" that can bump risk.

### 5.1 Extend risk heuristics with a simple env-based check

In `risk_assessor.py` (from Phase 1):

- Add:

```python
import os

def _env_sensitivity_boost() -> int:
    """
    Simple heuristic:
    - If CLAUDE_ENV == 'prod', add +20 risk.
    - If CLAUDE_SENSITIVE == '1', add +30 risk.
    """
    boost = 0
    if os.environ.get("CLAUDE_ENV") == "prod":
        boost += 20
    if os.environ.get("CLAUDE_SENSITIVE") == "1":
        boost += 30
    return boost
```

- After computing `risk_score` from text heuristics, do:

```python
risk_score += _env_sensitivity_boost()
```

Leave everything else unchanged.

### 5.2 Clear notes on where to insert this small change

In `risk_assessor.py` function `assess_risk()`:

- After line computing initial `risk_score` from heuristics.
- Before mapping to risk level.

Just add a small function and one-line boost.

---

## 6. README / usage note (short)

At end, please output a short "How to use Phase 2" section summarizing:

- How to run `/run-evals` and `/audit-quality`.
- How to interpret `adaptation_rules.json` suggestions.
- How reflection is triggered (only for `/research` and `/debugRCA` with medium/high risk or bad feedback).

***

Produce:

1. Full code for new modules (`run_evals.py`, `reflection.py`, `audit_quality.py`).
2. The exact JSON and SQL snippets above.
3. Clear notes on where to insert small `risk_assessor.py` change.

---

## Summary

This Phase 2 adds self-improvement and adaptation on top of Phase 1:

| Component | Purpose | Mechanism |
|----------|---------|------------|
| **Golden evals** | Track quality of key skill invocations via manual test cases | `run_evals.py` + `golden_evals.json` |
| **Self-reflection** | Trigger reflection on important turns to catch its own mistakes | `reflection.py` + Stop hook integration |
| **Adaptation rules** | Human-readable config file suggests improvements when metrics drift | `adaptation_rules.json` |
| **Quality audit** | Skill to summarize metrics and apply rules | `/audit-quality` |

No auto-execution. All improvements are suggestions for simpler LLM to implement manually.

---

## Phase 3: Co-Evolving System (Future)

**Note**: Phase 3 is where you stop mainly hard-coding behavior and start **co-evolving** system with data, small models, and limited automation of adaptation loop.

### Phase 3 Goals

- Use **historical data** (competence_events + feedback) to learn better defaults: risk weights, templates, contract fields.
- Automate **safe parts** of adaptation loop (suggest → test → apply) with guardrails.
- Make system **multi-environment aware** (dev/stage/prod terminals, different policies).

### Key Phase 3 Additions

#### 1. Data-driven tuning ("flywheel")

- Export competence_events + user_feedback regularly, and build a small offline script/notebook that:
  - Computes failure patterns by skill/task_type (e.g., which fields are often missing, where blocks are most common).
  - Suggests new contract fields or better templates based on actual transcripts (e.g., add "tradeoffs" to research outputs because they keep showing up ad-hoc).
  - Optionally, fit tiny models (or even rules) to propose **updated risk scores** or trigger patterns instead of hand-tuned regex only.

#### 2. Semi-automatic config evolution

- Introduce a simple "proposal–review–apply" flow:
  - Phase 2's `/audit-quality` produces suggestions.
  - Phase 3 adds a command like `/apply-suggestion <id>` that:
    - Patches `quality_policy.json` or `skill_output_contracts.json`.
    - Runs the golden eval suite.
    - Only writes change if evals stay above thresholds.

This gives you push-button evolution with regression protection, instead of editing JSON by hand every time.

#### 3. Task-type and skill coverage expansion

- Gradually move more skills into the taxonomy, backed by your data:
  - Promote frequently used "implementation-like" skills to full contracts when logs show recurring issues.
  - Add new task_types if patterns emerge (e.g., "meta/audit" or "ux-macro") instead of forcing everything into the original four.

#### 4. Advanced reflection modes (opt-in)

For specific high-value flows (RCA, security, deploy):

- Add **two-stage reflection** patterns on demand:
  - First answer.
  - Second pass that tries to find flaws or propose an alternative plan and logs both.
- Use Phase-2 metrics to decide *where* this is worth extra tokens (e.g., only flows with historically high failure or "bad" feedback rates).

#### 5. Environment-aware behaviors

- Extend risk and contracts based on env:
  - Different policies for `CLAUDE_ENV=dev` vs `prod` (stricter risk, more blocking in prod terminals).
  - Optional "read-only mode" profiles for very sensitive worktrees.

This lets you scale the same system across more contexts without manual reconfiguration.

---

### Phase Summary

| Phase | Focus | Automation Level |
|--------|---------|-------------------|
| **Phase 1** | Design + enforce competence (templates, contracts, risk, state) | Manual configuration |
| **Phase 2** | Add reflection, KPIs, and human-in-the-loop adaptation | Human-supervised metrics |
| **Phase 3** | Make system **self-tuning under your supervision**, using data and light automation | Supervised automation |

---

## Summary (All Phases)

This competence framework adds three progressive capability layers on top of the existing compliance system:

| Component | Phase | Purpose | Mechanism |
|------------|--------|---------|------------|
| **Task types** | 1 | Classify skills into reasoning patterns (research, debug_rca, etc.) | Taxonomy JSON |
| **Output contracts** | 1 | Define required fields per task type | skill_output_contracts.json |
| **Risk policy** | 1 | Score prompts for complexity/sensitivity | risk_assessor.py + heuristics |
| **State store** | 1 | Track outcomes and audit trail | CompetenceStateStore + SQLite |
| **Golden evals** | 2 | Track quality of key skill invocations | run_evals.py + golden_evals.json |
| **Self-reflection** | 2 | Trigger reflection on important turns | reflection.py + Stop hook integration |
| **Adaptation rules** | 2 | Human-readable config suggests improvements | adaptation_rules.json |
| **Quality audit** | 2 | Skill to summarize metrics and apply rules | /audit-quality |
| **Data-driven tuning** | 3 | Learn better defaults from history | Offline analysis + feedback loops |
| **Semi-auto evolution** | 3 | Apply suggestions with regression protection | /apply-suggestion command |
| **Multi-environment** | 3 | Different policies per context | Environment-aware risk/contracts |

---

## Phase 4: Platform & Reusability (Future)

**Note**: Phase 4 is where you stop thinking of this as "a better coding assistant" and treat it as a **personal, multi-environment AI platform** that you can re-target, scale, and partially delegate to other frameworks/agents.

### Phase 4 Goals

- Make the competence stack **portable** across tools (Claude Code, Codex, future IDEs).
- Use it as a **policy/competence nucleus** for other agents or frameworks (LangGraph, AutoGen, etc.).
- Harden it for **long-lived, multi-project use** (strong observability, safety profiles, and "tenant"-style separation).

### Key Phase 4 Moves

#### 1. Abstract competence layer into a "service"

- Wrap contracts, risk policy, and adaptation logic behind a small, stable API (HTTP or local CLI), e.g. `assess_intent`, `assess_risk`, `validate_output`, `log_event`.
- Claude Code hooks, Codex-side scripts, and even external agents call this service instead of re-implementing logic inline.

**Result**: one source of truth for competence and policy, many clients.

#### 2. Cross-framework integration

- Provide thin adapters so **LangGraph graphs** or **AutoGen agents** can:
  - Use your contracts as schemas for their tools/steps.
  - Call your risk/confirmation service before high-impact actions.
- Your system becomes "governor/brainstem" for competence, while orchestration frameworks handle complex workflows.

#### 3. Multi-tenant / multi-context profiles

- Add per-context profiles (e.g., `profile_dev`, `profile_prod`, `profile_experimental`) that:
  - Point to different policy bundles and thresholds.
  - Enforce stricter contracts and risk in prod, looser in scratch environments.

This lets you reuse the same machinery safely across terminals, repos, and projects.

#### 4. Deeper observability and governance

- Build simple dashboards or reports over `competence_events` and feedback: trends, failure clusters, "skills that need attention."
- Add explicit "policy change logs" (who/what changed contracts or risk, and why), so you can audit behavior months later.

#### 5. Optional: small model / fine-tune layer

- If you want to push further, use your logged data and golden paths to:
  - Fine-tune a small local model for **intent/risk classification** or **contract completeness scoring**, replacing some heuristics.
- Keep it strictly in an "advisor" role; hooks still make final decisions based on interpretable signals.

---

### Full Trajectory Summary

| Phase | Focus | Automation Level | Scope |
|--------|--------|-------------------|--------|
| **Phase 1** | Competence + enforcement | Manual configuration | Single-terminal, single-user |
| **Phase 2** | Reflection + metrics + human-guided adaptation | Human-supervised metrics | Single-terminal with quality tracking |
| **Phase 3** | Semi-automatic, data-driven tuning | Supervised automation | Multi-terminal with learning loops |
| **Phase 4** | Portable platform & cross-framework reuse | Multi-environment platform | Multi-tool, multi-framework nucleus |
