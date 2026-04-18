# Competence Layer Architecture v2.0 - Complete Implementation Plan

> **Single message for another LLM to execute as implementation roadmap**

---

## 1. System Understanding

### Current Architecture Analysis

**Your system implements a sophisticated compliance layer through:**

1. **Constitution (CLAUDE.md v9.0)** - 1250+ lines of behavioral rules
2. **Hook enforcement** - 20+ Python hooks across 4 event types
3. **Skill system** - 200+ skills with SKILL.md frontmatter
4. **Evidence store** - SQLite WAL backend with JSONL spooling (`evidence_store.py`)
5. **Contract infrastructure** - `contract_state.py` with terminal-scoped persistence

**How it currently works:**
- UserPromptSubmit → `skill_enforcer.py` detects `/command`, stores intent state
- PreToolUse → `command_intent_gate.py` validates restrictive flags
- PreToolUse → `skill_pattern_gate.py` validates skill execution
- PostToolUse → Various trackers persist to `evidence_store.py`
- Stop → Router runs `safety_gate`, `behavior_audit`, `advisory`, `command_execution_validator`

**How it currently fails (Infrastructure + Behavioral):**

| Category | Specific Failure | Root Cause | Evidence |
|----------|----------------|------------|----------|
| **Over-coupled workflow gate** | TaskUpdate tied to TaskList evidence | TaskList() was never called | /task SKILL.md requires TaskList for "list" sub-command only |
| **Fragile state management** | "TaskList() was never called" even when it was | File-based state without locking | `active_command_{terminal}.json` write-race between concurrent hooks |
| **Noisy error loops** | Spammy duplicate blocks | No dedupe by hash/cooldown | Stop.py runs ALL gates every turn, no "already blocked this turn" tracking |
| **Policy-implementation mismatch** | /task rules applied to everything | Broad DO_NOT patterns | `command_execution_validator.py` DESCRIPTION_PATTERNS catch legitimate summary language |
| **Weak command matching** | /debugRCA vs /rca confusion | No alias normalization | commands.toml has `aliases` but skill_enforcer uses raw SLASH_COMMAND_RE |
| **Next-step suggestion drift** | Archived skills suggested | Stale suggest mappings | commands.toml signals mapping to non-existent commands |
| **Silent write-permission failures** | Behavior degrades silently | No error on write failures | SessionDataDir write failure swallowed by try/except in _store_active_command |

**Behavioral Issues:**

| Issue | Pattern | Why It Happens |
|--------|---------|----------------|
| **Avoids execution** | "I can run that" → produces blog output | No output contract enforcement |
| **Weak research output** | Generic sources, no actionable deltas | /research has no required `actionable_recommendations` field |
| **Language drift** | Random language switches | No user preference tracking |
| **Overclaiming** | "no additional research needed" without evidence | No evidence-tier enforcement for skill outputs |
| **No findings→implementation mapping** | Research findings sit in vacuum | No skill-level contract delivery |
| **Ignores global instructions** | "don't be lazy" missed | Instructions not injected at execution time |

**Why CLAUDE.md alone fails:**
- 90% defensive ("what NOT to do")
- 10% offensive guidance ("how to reason well")
- It's a **compliance layer**, not a **competence layer**
- Assumes agent will self-enforce quality (which it doesn't always do)

---

## 2. Task-Type Taxonomy and Output Contracts

### Task Type Definitions

Create `P:\.claude\hooks\config\competence_taxonomy.json`:

```json
{
  "task_types": {
    "research": {
      "name": "research",
      "description": "Investigate and synthesize information from multiple sources",
      "reasoning_template": [
        "What specific question am I answering?",
        "What sources did I consult and how do they support my findings?",
        "What are the key findings ranked by confidence?",
        "What specific actions can be taken based on these findings?",
        "What remains unknown or requires verification?"
      ],
      "output_contract": {
        "required_fields": {
          "sources": "array of {url, title, snippet, accessed_at, relevance_score}",
          "findings": "array of {claim, evidence_sources, confidence_level (0-100)}",
          "actionable_recommendations": "array of {action, priority, estimated_effort, dependencies}",
          "confidence": "number (0-100) overall confidence in findings",
          "next_step_question": "string - what clarification would increase confidence?"
        },
        "optional_fields": {
          "methodology": "string - how research was conducted",
          "limitations": "array of known gaps or weaknesses",
          "related_work": "array of references to prior work"
        }
      }
    },

    "implementation": {
      "name": "implementation",
      "description": "Write or modify code to achieve a specified outcome",
      "reasoning_template": [
        "What exactly am I implementing and for what goal?",
        "What files will be modified/created and why?",
        "What assumptions am I making about current codebase?",
        "What tests will verify this works?",
        "How does this integrate with existing code?"
      ],
      "output_contract": {
        "required_fields": {
          "files_modified": "array of {path, change_summary, line_count}",
          "files_created": "array of {path, purpose, line_count}",
          "tests_written": "array of {path, test_description}",
          "verification_command": "string - command to verify implementation",
          "integration_notes": "string - how this connects to existing system"
        },
        "optional_fields": {
          "alternatives_considered": "array of {approach, why_rejected}",
          "known_limitations": "array of constraints or edge cases"
        }
      }
    },

    "debug_rca": {
      "name": "debug_rca",
      "description": "Systematic root cause analysis with evidence-based hypotheses",
      "reasoning_template": [
        "What exactly failed (error message, stack trace, observed behavior)?",
        "When did this start working (git history, recent changes)?",
        "What are the candidate root causes ranked by likelihood?",
        "What evidence supports or refutes each hypothesis?",
        "What fix is recommended and why will it solve root cause?"
      ],
      "output_contract": {
        "required_fields": {
          "problem_statement": "string - what failed in observable terms",
          "evidence_collected": "array of {source, content, relevance}",
          "hypotheses": "array of {cause, likelihood, supporting_evidence, refuting_evidence}",
          "root_cause": "string - most likely cause with evidence backing",
          "recommended_fix": "string - specific fix with implementation path",
          "verification_plan": "string - how to confirm fix resolves issue"
        },
        "optional_fields": {
          "prevention_strategy": "string - how to prevent similar issues",
          "related_patterns": "array of links to similar resolved issues"
        }
      }
    },

    "planning": {
      "name": "planning",
      "description": "Break down complex work into structured execution plan",
      "reasoning_template": [
        "What is the ultimate objective and success criteria?",
        "What are the major phases and their dependencies?",
        "What risks exist at each phase and how are they mitigated?",
        "What is the estimated effort for each phase?",
        "What prerequisites must be satisfied before starting?"
      ],
      "output_contract": {
        "required_fields": {
          "objective": "string - clear goal statement",
          "phases": "array of {name, description, dependencies, estimated_effort, acceptance_criteria}",
          "risk_assessment": "array of {risk, probability, impact, mitigation}",
          "total_estimated_effort": "string or number",
          "blocking_prerequisites": "array of must-complete items"
        },
        "optional_fields": {
          "rollback_plan": "string - how to undo if needed",
          "alternative_approaches": "array of {approach, tradeoffs}"
        }
      }
    },

    "refactor": {
      "name": "refactor",
      "description": "Restructure existing code without changing behavior",
      "reasoning_template": [
        "What is the current code smell or technical debt?",
        "What is the target design pattern or structure?",
        "What tests ensure behavior doesn't change during refactoring?",
        "What incremental changes achieve target structure?",
        "How is this verified after each change?"
      ],
      "output_contract": {
        "required_fields": {
          "current_problem": "string - what issue is being addressed",
          "target_structure": "string - desired design or pattern",
          "refactoring_steps": "array of {step, files_changed, verification}",
          "behavior_preservation_tests": "array of {test_path, description}",
          "verification_result": "string - test results showing unchanged behavior"
        },
        "optional_fields": {
          "performance_impact": "string - before/after comparison if relevant"
        }
      }
    },

    "audit_review": {
      "name": "audit_review",
      "description": "Examine code, security, or compliance against standards",
      "reasoning_template": [
        "What standard or requirement am I auditing against?",
        "What scope (files, modules, systems) is being examined?",
        "What specific issues were found and at what severity?",
        "What evidence supports each finding?",
        "What are the prioritized remediation steps?"
      ],
      "output_contract": {
        "required_fields": {
          "audit_standard": "string - reference standard or requirement",
          "scope_examined": "string or array of paths/components",
          "findings": "array of {severity, issue, evidence, location, recommendation}",
          "overall_assessment": "string - summary of compliance status",
          "remediation_priority": "array of {priority, action, owner, deadline}"
        },
        "optional_fields": {
          "audit_methodology": "string - how audit was conducted",
          "exclusions": "array of out-of-scope items"
        }
      }
    }
  }
}
```

### Skill-Level Contract Assignments

Create `P:\.claude\hooks\config\skill_output_contracts.json`:

```json
{
  "skill_contracts": {
    "research": {
      "task_type": "research",
      "enforcement_mode": "block",
      "required_fields": ["sources", "findings", "actionable_recommendations", "confidence", "next_step_question"],
      "validation_example": {
        "good": {
          "sources": [
            {"url": "https://example.com/docs", "title": "Official API Docs", "relevance_score": 95}
          ],
          "findings": [
            {"claim": "FastAPI 0.100+ supports async background tasks", "confidence_level": 90, "evidence_sources": ["sources[0]"]}
          ],
          "actionable_recommendations": [
            {"action": "Migrate to FastAPI 0.100+ BackgroundTasks", "priority": "high", "estimated_effort": "2 days"}
          ],
          "confidence": 85,
          "next_step_question": "What is your current FastAPI version?"
        }
      }
    },

    "debugRCA": {
      "task_type": "debug_rca",
      "enforcement_mode": "block",
      "required_fields": ["problem_statement", "evidence_collected", "hypotheses", "root_cause", "recommended_fix", "verification_plan"],
      "validation_example": {
        "good": {
          "problem_statement": "Application crashes on startup with KeyError: 'DATABASE_URL'",
          "evidence_collected": [
            {"source": "stack trace", "content": "File config.py:45 raises KeyError", "relevance": "direct"}
          ],
          "hypotheses": [
            {"cause": "DATABASE_URL missing from env", "likelihood": 85, "supporting_evidence": ["stack trace points to config.py:45"]}
          ],
          "root_cause": "Environment variable DATABASE_URL not set in production config",
          "recommended_fix": "Add DATABASE_URL='postgresql://...' to .env.production",
          "verification_plan": "Run application with new .env file, confirm successful startup"
        }
      }
    },

    "task": {
      "task_type": "planning",
      "enforcement_mode": "warn",
      "required_fields": ["objective", "phases"],
      "validation_example": {
        "good": {
          "objective": "Add user authentication to application",
          "phases": [
            {"name": "Database schema", "dependencies": [], "estimated_effort": "1 day", "acceptance_criteria": "Users table exists"}
          ]
        }
      }
    },

    "think": {
      "task_type": "audit_review",
      "enforcement_mode": "warn",
      "required_fields": ["overall_assessment", "findings"]
    },

    "v": {
      "task_type": "audit_review",
      "enforcement_mode": "block",
      "required_fields": ["overall_assessment"]
    }
  }
}
```

---

## 3. Risk & Confirmation Policy

### Risk Classification Rules

Create `P:\.claude\hooks\config\risk_policy.json`:

```json
{
  "risk_levels": {
    "low": {
      "threshold": 0,
      "description": "Execute directly, no confirmation needed",
      "triggers": []
    },

    "medium": {
      "threshold": 30,
      "description": "One concise confirmation question",
      "triggers": [
        "ambiguous_intent",
        "high_cost_operation",
        "external_side_effects"
      ],
      "confirmation_template": "Confirm: {specific_question} (y/n)"
    },

    "high": {
      "threshold": 70,
      "description": "One structured confirmation with options",
      "triggers": [
        "destructive_operation",
        "intent_mismatch"
      ],
      "confirmation_template": """
⚠️ RISK CHECK REQUIRED

Operation: {operation}
Risk: {risk_factors}

Options:
A) Proceed with {operation}
B) Modify approach
C) Cancel

Choose A/B/C:
      """.strip()
    },

    "critical": {
      "threshold": 90,
      "description": "Always block, no auto-proceed",
      "triggers": [
        "unauthorized_flags",
        "high_risk_missing_contract_fields"
      ],
      "block_reason": "CRITICAL RISK: {reason}. This operation requires manual review."
    }
  },

  "risk_heuristics": {
    "ambiguous_intent": {
      "deterministic_checks": [
        {"pattern": "improve|optimize|better|faster", "score": 20, "reason": "Comparative without baseline"},
        {"pattern": "fix system|make it work", "score": 30, "reason": "Vague problem statement"},
        {"pattern": "refactor.*(?!the)", "score": 25, "reason": "What to refactor unspecified"}
      ],
      "llm_fallback": {
        "enabled": true,
        "threshold": 40,
        "prompt": "Classify user intent clarity (clear/somewhat_ambiguous/very_ambiguous)"
      }
    },

    "destructive_operation": {
      "deterministic_checks": [
        {"pattern": "\\bdelete\\b.*(\\bfolder\\b|directory|schema)", "score": 80, "reason": "Bulk deletion"},
        {"pattern": "\\bdrop\\b.*(\\btable\\b|database)", "score": 90, "reason": "Data loss"},
        {"pattern": "--force|git reset --hard", "score": 70, "reason": "Irreversible history change"}
      ],
      "llm_fallback": {"enabled": false}
    },

    "high_cost_operation": {
      "deterministic_checks": [
        {"pattern": "--large-model|max-tokens.*[5-9][0-9]{3,}", "score": 35, "reason": "Expensive LLM call"},
        {"pattern": "rebuild|reinstall.*dependencies", "score": 40, "reason": "Time-consuming operation"}
      ],
      "llm_fallback": {"enabled": false}
    },

    "external_side_effects": {
      "deterministic_checks": [
        {"pattern": "git push|publish|deploy", "score": 50, "reason": "External changes"},
        {"pattern": "send.*email|post.*webhook", "score": 45, "reason": "External notifications"}
      ],
      "llm_fallback": {"enabled": false}
    },

    "intent_mismatch": {
      "deterministic_checks": [
        {"pattern": "(?i)(?:(use|try) (python -c|Bash.*echo)", "score": 85, "reason": "Skill simulation detected"}
      ],
      "llm_fallback": {
        "enabled": true,
        "threshold": 60,
        "prompt": "Does command '{command}' match user intent '{user_intent}'? (yes/no/partial)"
      }
    }
  },

  "confirmation_rules": {
    "one_question_only": true,
    "no_negotiation_loops": true,
    "max_confirmation_turns": 1,
    "structured_options_for_high_risk": true
  }
}
```

### Pseudo-Code for Risk Assessment

```python
# P:\.claude\hooks\competence\risk_assessor.py
from __future__ import annotations
import re
from typing import Any

def assess_risk(
    user_prompt: str,
    command_name: str | None,
    tool_input: dict[str, Any],
    llm_classifier: Callable | None = None
) -> dict:
    """
    Assess risk level using deterministic heuristics first.
    Falls back to LLM classification only when configured and below confidence threshold.

    Returns:
        {
            "risk_level": "low" | "medium" | "high" | "critical",
            "risk_score": 0-100,
            "triggers": list[str],
            "needs_confirmation": bool,
            "confirmation_text": str | None,
            "block_reason": str | None
        }
    """
    risk_score = 0
    triggers = []

    # 1. Run deterministic checks for each heuristic category
    for category, config in RISK_HEURISTICS.items():
        for check in config.get("deterministic_checks", []):
            pattern = check["pattern"]
            score = check["score"]
            reason = check["reason"]

            if re.search(pattern, user_prompt, re.IGNORECASE):
                risk_score += score
                triggers.append(f"{category}: {reason}")

    # 2. Determine if LLM fallback is needed
    needs_llm = False
    if risk_score >= 30 and risk_score < 70:
        # Check if any trigger has LLM fallback enabled
        for category, config in RISK_HEURISTICS.items():
            if config.get("llm_fallback", {}).get("enabled", False):
                if any(cat in triggers for cat in [category]):
                    needs_llm = True
                    break

    # 3. Optionally use LLM classification
    llm_confidence = 0
    if needs_llm and llm_classifier:
        result = llm_classifier(
            prompt=f"Classify risk level for: {user_prompt}",
            schema={"low": 0, "medium": 40, "high": 70, "critical": 90}
        )
        llm_score = result.get("score", 0)
        llm_confidence = result.get("confidence", 0)

        if llm_confidence >= 70:
            risk_score = max(risk_score, llm_score)
            triggers.append(f"LLM: {result['reason']}")

    # 4. Map score to risk level
    if risk_score >= 90:
        risk_level = "critical"
    elif risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    # 5. Build confirmation or block
    result = {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "triggers": triggers,
        "needs_confirmation": risk_level in ("medium", "high")
    }

    if risk_level == "critical":
        result["block_reason"] = CRITICAL_BLOCK_TEMPLATE.format(
            reason="; ".join(triggers[:3])
        )
    elif risk_level == "high":
        result["confirmation_text"] = HIGH_RISK_TEMPLATE.format(
            operation=command_name or "this operation",
            risk_factors="; ".join(triggers[:3])
        )
    elif risk_level == "medium":
        specific_question = _extract_specific_question(triggers)
        result["confirmation_text"] = f"Confirm: {specific_question} (y/n)"

    return result


def _extract_specific_question(triggers: list[str]) -> str:
    """Convert technical triggers into user-facing questions."""
    if any("comparative" in t for t in triggers):
        return "You used comparative language ('better', 'improve'). What baseline are you comparing to?"
    if any("vague" in t for t in triggers):
        return "You said 'fix system'. What specific problem should I address?"
    return "Proceed with this operation?"
```

---

## 4. State & Audit Design

### SQLite Schema

```sql
-- P:\.claude\hooks\state\competence_schema.sql

-- Session context (already exists, extended)
CREATE TABLE IF NOT EXISTS session_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    terminal_id TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    pid INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

-- Competence layer events
CREATE TABLE IF NOT EXISTS competence_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    terminal_id TEXT NOT NULL DEFAULT '',
    ts TEXT NOT NULL,

    -- Event classification
    event_type TEXT NOT NULL,  -- 'skill_invoked' | 'contract_validated' | 'risk_assessed'
    skill_name TEXT NOT NULL,
    task_type TEXT NOT NULL,

    -- Risk assessment
    risk_level TEXT NOT NULL,  -- 'low' | 'medium' | 'high' | 'critical'
    risk_score INTEGER NOT NULL DEFAULT 0,
    risk_triggers_json TEXT NOT NULL DEFAULT '[]',

    -- Contract validation
    contract_status TEXT NOT NULL,  -- 'missing' | 'partial' | 'complete'
    missing_fields_json TEXT NOT NULL DEFAULT '[]',

    -- Action taken
    action_taken TEXT NOT NULL,  -- 'allowed' | 'blocked' | 'warned'
    block_reason TEXT,
    warning_message TEXT,

    -- Metadata
    user_prompt_snippet TEXT,
    response_snippet TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    FOREIGN KEY (session_id) REFERENCES session_context(session_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_competence_session ON competence_events(session_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_competence_terminal ON competence_events(terminal_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_competence_type ON competence_events(event_type, id DESC);
CREATE INDEX IF NOT EXISTS idx_competence_risk ON competence_events(risk_level, id DESC);

-- User feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    terminal_id TEXT NOT NULL DEFAULT '',
    ts TEXT NOT NULL,
    turn_id INTEGER,
    rating TEXT NOT NULL,    -- 'good' | 'bad'
    note TEXT NOT NULL DEFAULT ''
);
```

### State Store API

```python
# P:\.claude\hooks\state\competence_state.py
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

STATE_DIR = Path("P:\.claude\state")
DB_PATH = STATE_DIR / "competence.db"


class CompetenceStateStore:
    """Unified state API for competence layer with SQLite backend."""

    def __init__(self, session_id: str = "", terminal_id: str = ""):
        self.session_id = session_id or self._resolve_session_id()
        self.terminal_id = terminal_id or ""

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    def get_turn_state(self, turn_id: str | None = None) -> dict:
        """
        Get state for current turn.

        Args:
            turn_id: Optional turn identifier (defaults to current timestamp)

        Returns:
            {
                "session_id": str,
                "terminal_id": str,
                "active_skill": str | None,
                "risk_assessment": dict | None,
                "contract_status": dict | None
            }
        """
        conn = self._connect()
        try:
            # Get most recent state for this session/terminal
            row = conn.execute("""
                SELECT session_id, terminal_id, skill_name, task_type,
                       risk_level, risk_score, risk_triggers_json,
                       contract_status, missing_fields_json
                FROM competence_events
                WHERE session_id = ? AND terminal_id = ?
                ORDER BY id DESC
                LIMIT 1
            """, (self.session_id, self.terminal_id)).fetchone()

            if not row:
                return {"session_id": self.session_id, "terminal_id": self.terminal_id}

            return {
                "session_id": row["session_id"],
                "terminal_id": row["terminal_id"],
                "active_skill": row["skill_name"],
                "risk_assessment": {
                    "level": row["risk_level"],
                    "score": row["risk_score"],
                    "triggers": json.loads(row["risk_triggers_json"])
                } if row["risk_level"] else None,
                "contract_status": {
                    "status": row["contract_status"],
                    "missing_fields": json.loads(row["missing_fields_json"])
                } if row["contract_status"] else None
            }
        finally:
            conn.close()

    def put_turn_state(self, state: dict) -> bool:
        """
        Update state for current turn.

        Args:
            state: {
                "active_skill": str | None,
                "risk_assessment": dict | None,
                "contract_status": dict | None
            }

        Returns:
            True if saved successfully
        """
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO competence_events (
                    session_id, terminal_id, ts,
                    event_type, skill_name, task_type,
                    risk_level, risk_score, risk_triggers_json,
                    contract_status, missing_fields_json,
                    action_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                self.terminal_id,
                datetime.now(timezone.utc).isoformat(),
                "state_update",
                state.get("active_skill"),
                state.get("task_type"),
                state.get("risk_assessment", {}).get("level"),
                state.get("risk_assessment", {}).get("score", 0),
                json.dumps(state.get("risk_assessment", {}).get("triggers", [])),
                state.get("contract_status", {}).get("status"),
                json.dumps(state.get("contract_status", {}).get("missing_fields", [])),
                "recorded"
            ))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Audit Events
    # -------------------------------------------------------------------------

    def append_audit_event(self, event: dict) -> bool:
        """
        Record an audit event with full schema.

        Args:
            event: {
                "intent_label": str,
                "risk_level": str,
                "triggers": list[str],
                "contract_status": dict,
                "block_reason": str | None,
                "suggestions": list[str] | None
            }

        Returns:
            True if saved successfully
        """
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO competence_events (
                    session_id, terminal_id, ts,
                    event_type, skill_name, task_type,
                    risk_level, risk_score, risk_triggers_json,
                    contract_status, missing_fields_json,
                    action_taken, block_reason, warning_message,
                    user_prompt_snippet, response_snippet,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                self.terminal_id,
                datetime.now(timezone.utc).isoformat(),
                "audit_event",
                event.get("skill_name", ""),
                event.get("task_type", ""),
                event.get("risk_level", "low"),
                event.get("risk_score", 0),
                json.dumps(event.get("triggers", [])),
                event.get("contract_status", {}).get("status", "none"),
                json.dumps(event.get("contract_status", {}).get("missing_fields", [])),
                "blocked" if event.get("block_reason") else ("warned" if event.get("warning_message") else "allowed",
                event.get("block_reason"),
                event.get("warning_message"),
                event.get("user_prompt_snippet", "")[:500],
                event.get("response_snippet", "")[:1000],
                json.dumps(event.get("metadata", {}))
            ))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_recent_events(self, limit: int = 50, event_type: str | None = None) -> list[dict]:
        """Get recent audit events for this session."""
        conn = self._connect()
        try:
            query = """
                SELECT id, session_id, terminal_id, ts,
                       event_type, skill_name, task_type,
                       risk_level, action_taken, block_reason
                FROM competence_events
                WHERE session_id = ?
            """
            params = [self.session_id]

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # TTL / Cleanup
    # -------------------------------------------------------------------------

    def cleanup_old_events(self, ttl_days: int = 30) -> int:
        """
        Delete events older than TTL.

        Returns:
            Number of rows deleted
        """
        conn = self._connect()
        try:
            cutoff = (datetime.now(timezone.utc)
                      - timedelta(days=ttl_days)).isoformat()

            cursor = conn.execute("""
                DELETE FROM competence_events
                WHERE ts < ?
            """, (cutoff,))

            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Get database connection with WAL mode."""
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    @staticmethod
    def _resolve_session_id() -> str:
        """Resolve session ID from environment or generate one."""
        import os
        return (
            os.environ.get("CLAUDE_SESSION_ID", "")
            or f"sess_{os.getpid()}_{int(time.time())}"
        )


# -------------------------------------------------------------------------
# Module-level convenience functions
# -------------------------------------------------------------------------

def get_turn_state(session_id: str = "", terminal_id: str = "") -> dict:
    """Convenience function to get turn state."""
    return CompetenceStateStore(session_id, terminal_id).get_turn_state()


def put_turn_state(state: dict, session_id: str = "", terminal_id: str = "") -> bool:
    """Convenience function to update turn state."""
    return CompetenceStateStore(session_id, terminal_id).put_turn_state(state)


def append_audit_event(event: dict, session_id: str = "", terminal_id: str = "") -> bool:
    """Convenience function to record audit event."""
    return CompetenceStateStore(session_id, terminal_id).append_audit_event(event)


# -------------------------------------------------------------------------
# User Feedback Support (Phase 2)
# -------------------------------------------------------------------------

def record_user_feedback(
    rating: str,  # "good" | "bad"
    note: str = "",
    session_id: str = "",
    terminal_id: str = ""
) -> bool:
    """Record user feedback for quality tracking.

    Args:
        rating: User satisfaction rating
        note: Optional short note
        session_id: Session identifier
        terminal_id: Terminal identifier

    Returns:
        True if saved successfully
    """
    store = CompetenceStateStore(session_id, terminal_id)
    conn = store._connect()
    try:
        conn.execute(
            """
            INSERT INTO user_feedback (
                session_id, terminal_id, ts, rating, note
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                store.session_id,
                store.terminal_id,
                datetime.now(timezone.utc).isoformat(),
                rating,
                note[:500],
            ),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
```

### Example Audit Event Flows

**Flow 1: Successful research execution**
```python
# User: /research "FastAPI async patterns"
# Turn 1: Skill invoked
event = {
    "intent_label": "research",
    "risk_level": "low",
    "triggers": [],
    "contract_status": {"status": "none"},
    "suggestions": None
}
# → append_audit_event(event)

# Turn 2: Contract validation passes
event = {
    "intent_label": "research",
    "risk_level": "low",
    "triggers": [],
    "contract_status": {
        "status": "complete",
        "missing_fields": []
    },
    "suggestions": None,
    "metadata": {
        "sources_count": 5,
        "findings_count": 3,
        "recommendations_count": 2
    }
}
# → append_audit_event(event)
```

**Flow 2: Block due to missing contract fields**
```python
# User: /research "How do I implement auth?"
# Turn: Response generated, Stop hook validates
event = {
    "intent_label": "research",
    "risk_level": "low",
    "triggers": [],
    "contract_status": {
        "status": "missing",
        "missing_fields": ["actionable_recommendations", "next_step_question"]
    },
    "block_reason": "Missing required output contract fields for /research. Re-run with structured output including: actionable_recommendations (array of {action, priority, estimated_effort, dependencies}), next_step_question (string - what clarification would increase confidence?)",
    "suggestions": [
        "Re-run /research with enhanced prompt: 'How do I implement auth? Include specific recommendations with priorities and effort estimates.'"
    ],
    "metadata": {
        "response_length": 500,
        "sources_detected": 0
    }
}
# → append_audit_event(event) → Stop hook blocks with block_reason
```

**Flow 3: Risk-based confirmation**
```python
# User: /research "improve my code"
# Turn 1: Intent router detects ambiguity
event = {
    "intent_label": "ambiguous_research",
    "risk_level": "medium",
    "triggers": ["ambiguous_intent: Comparative without baseline"],
    "contract_status": {"status": "none"},
    "suggestions": None
}
# → append_audit_event(event)

# Turn 2: User confirms: "yes, compare to project baseline"
event = {
    "intent_label": "research",
    "risk_level": "low",
    "triggers": [],
    "contract_status": {"status": "none"},
    "suggestions": None,
    "metadata": {
        "clarification_provided": "yes, compare to project baseline"
    }
}
# → append_audit_event(event) → Proceeds with research
```

---

## 5. Hook-Level Patch Plan

### 5.1 UserPromptSubmit/skill_enforcer.py

**Current behavior:**
- Detects `/command` patterns via `SLASH_COMMAND_RE`
- Stores intent to `pending_command_intent_{session_id}.json`
- Stores active command to `active_command_{terminal_id}.json`
- No risk assessment or intent routing
- No competence guidance injection

**Proposed behavior:**
- Add `intent_router()` for deterministic task-type labeling
- Add `risk_assessor()` for confirmation logic
- Inject competence guidance based on task type
- Maintain backward compatibility with existing state storage

**Function-level changes:**

```python
# NEW FUNCTION
def intent_router(user_prompt: str, command_name: str | None) -> dict:
    """
    Route user intent to task type using deterministic heuristics.

    Args:
        user_prompt: Full user input text
        command_name: Detected slash command (if any)

    Returns:
        {
            "task_type": str,
            "confidence": 0-100,
            "reasoning_template": list[str],
            "requires_contract": bool
        }
    """
    if not command_name:
        # No slash command - analyze natural language
        return _route_natural_language(user_prompt)

    # Look up skill's declared task type
    skill_config = _load_skill_contract_config(command_name)
    if skill_config:
        task_type = skill_config.get("task_type", "implementation")
    else:
        # Fallback to command name patterns
        task_type = _classify_command_by_name(command_name)

    reasoning_template = _load_reasoning_template(task_type)

    return {
        "task_type": task_type,
        "confidence": 90 if skill_config else 70,
        "reasoning_template": reasoning_template,
        "requires_contract": task_type in CONTRACT_REQUIRING_TASKS
    }

# NEW FUNCTION
def risk_assessor(
    user_prompt: str,
    intent_result: dict,
    command_name: str | None
) -> dict:
    """
    Assess risk using deterministic heuristics.

    Args:
        user_prompt: Full user input
        intent_result: Result from intent_router()
        command_name: Detected slash command

    Returns:
        {
            "risk_level": "low" | "medium" | "high" | "critical",
            "risk_score": 0-100,
            "triggers": list[str],
            "needs_confirmation": bool,
            "confirmation_text": str | None,
            "block_reason": str | None
        }
    """
    # Load risk policy
    risk_config = _load_risk_policy()

    # Run deterministic checks
    risk_score = 0
    triggers = []

    for category, checks in risk_config["risk_heuristics"].items():
        for check in checks.get("deterministic_checks", []):
            if re.search(check["pattern"], user_prompt, re.IGNORECASE):
                risk_score += check["score"]
                triggers.append(f"{category}: {check['reason']}")

    # Map to risk level
    if risk_score >= 90:
        risk_level = "critical"
    elif risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    result = {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "triggers": triggers,
        "needs_confirmation": risk_level in ("medium", "high")
    }

    # Build confirmation or block
    if risk_level == "critical":
        result["block_reason"] = _format_critical_block(triggers)
    elif risk_level == "high":
        result["confirmation_text"] = _format_high_risk_confirmation(command_name, triggers)
    elif risk_level == "medium":
        specific_question = _extract_specific_question(triggers)
        result["confirmation_text"] = f"Confirm: {specific_question} (y/n)"

    return result

# NEW FUNCTION
def build_competence_context(
    command: str,
    args: str,
    intent_result: dict,
    risk_result: dict | None
) -> str:
    """
    Build competence guidance injection for command execution.

    Args:
        command: Command name
        args: Command arguments
        intent_result: Result from intent_router()
        risk_result: Result from risk_assessor()

    Returns:
        Formatted context injection text
    """
    parts = ["**Detected Command**: /{command}**"]

    if args and args.strip():
        parts.append(f"**Command Args**: {args.strip()}")

    # Add task-type-specific guidance
    task_type = intent_result.get("task_type", "")
    if task_type:
        parts.append(f"**Task Type**: {task_type}")

    # Add reasoning template for first-time visibility
    reasoning_template = intent_result.get("reasoning_template", [])
    if reasoning_template:
        parts.append(f"**Reasoning Template**:")
            for i, question in enumerate(reasoning_template[:5], 1):
                parts.append(f"   {i}. {question}")

    # Add risk confirmation if needed
    if risk_result and risk_result.get("confirmation_text"):
        parts.append(f"**⚠️ Confirmation Required**:")
        parts.append(f"   {risk_result['confirmation_text']}")

    # Add contract reminder for skills with contracts
    if intent_result.get("requires_contract"):
        contract_fields = _get_required_contract_fields(command)
        parts.append(f"**Output Contract Required**:")
        parts.append(f"   Your response must include:")
        for field in contract_fields:
            parts.append(f"   • {field}")

    return "\n\n".join(parts)

# MODIFIED FUNCTION
@register_hook('skill_enforcer', priority=10.0)
def run_skill_enforcer(context: HookContext) -> HookResult | None:
    """Main entry point for skill enforcer."""
    # Check for slash command
    command = extract_command_name(context.prompt)
    if not command:
        return None

    # Check enforcement policy
    if should_block_command(command):
        return HookResult(
            context=f"**Skill Enforcement Skipped**: /{command} is excluded by policy.",
            tokens=50
        )

    # Extract arguments
    match = SLASH_COMMAND_RE.match(context.prompt.strip())
    args = match.group(2) if match and match.group(2) else ''

    # NEW: Route intent and assess risk
    intent_result = intent_router(context.prompt, command)
    risk_result = risk_assessor(context.prompt, intent_result, command)

    # NEW: Check for critical block
    if risk_result.get("block_reason"):
        # Write to state and return block
        _store_blocked_attempt(context, command, risk_result)
        return HookResult(
            context=f"**BLOCKED**: {risk_result['block_reason']}",
            tokens=100
        )

    # NEW: Store intent with task type
    try:
        _store_command_intent(context, command, intent_result)
        _store_active_command(context, command, intent_result)
    except Exception:
        pass

    # NEW: Build enhanced context
    context_text = build_competence_context(command, args, intent_result, risk_result)
    return HookResult(context=context_text, tokens=estimate_tokens(context_text))
```

### 5.2 PreToolUse/command_intent_gate.py

**Current behavior:**
- Validates restrictive flags against user prompt
- Hardcoded `SKILL_COMMAND_PATTERNS` and `RESTRICTIVE_FLAGS`
- No soft warn branch, only allow/deny
- No intent label in output

**Proposed behavior:**
- Keep deny behavior for unauthorized restrictive flags
- Add `intent_label` and `expected_command_scope` to allow/deny reason
- Add soft warn branch for non-critical drift
- Load skill config from centralized file

**Function-level changes:**

```python
# NEW CONFIG STRUCTURE
# Load from P:\.claude\hooks\config\skill_intent_config.json
def load_skill_config() -> dict:
    """Load centralized skill intent configuration."""
    config_path = HOOKS_DIR.parent / "config" / "skill_intent_config.json"
    default_config = {
        "skill_command_patterns": {
            "ask-olymp": ["ask_cli.py", "llm_cli.py"],
            "ask-cli": ["ask_cli.py", "llm_cli.py"],
            # ... existing patterns
        },
        "restrictive_flags": {
            "ask-olymp": ["--qwen-only", "--gemini-only", "--codeex-only"],
            # ... existing flags
        },
        "soft_warn_patterns": {
            "research": ["generic sources", "no specific recommendations"],
            "debugRCA": ["fix without root cause"]
        }
    }

    try:
        if config_path.exists():
            import json
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
            default_config.update(loaded)
    except Exception:
        pass

    return default_config

# MODIFIED FUNCTION
def check_intent_justification(
    user_prompt: str,
    flags: list,
    skill: str,
    config: dict
) -> tuple:
    """
    Check if restrictive flags are justified by user's prompt.

    NEW: Returns (justified, reason, intent_label, expected_scope)
    """
    prompt_lower = user_prompt.lower()
    intent_label = _detect_intent_label(user_prompt, skill)
    expected_scope = _get_expected_command_scope(skill, config)

    # Existing justification patterns
    justifications = {
        "--qwen-only": ["qwen", "use qwen", "just qwen", "only qwen", "with qwen"],
        # ... existing patterns
    }

    unjustified = []
    for flag in flags:
        patterns = justifications.get(flag, [])
        if not any(p in prompt_lower for p in patterns):
            unjustified.append(flag)

    if unjustified:
        reason = f"Unauthorized restrictive flags: {', '.join(unjustified)}"
        return False, reason, intent_label, expected_scope
    return True, "Flags justified by user prompt", intent_label, expected_scope

# NEW FUNCTION
def _detect_intent_label(user_prompt: str, skill: str) -> str:
    """Detect intent label for signaling to Stop."""
    intent_patterns = {
        "research_query": r"(?:how|what).*(?:do|implement|use|work)",
        "debug_request": r"(?:debug|fix|error|broken|crash)",
        "planning_request": r"(?:plan|breakdown|steps|phases)",
        "refactor_request": r"refactor|restructure|clean up"
    }

    import re
    for label, pattern in intent_patterns.items():
        if re.search(pattern, user_prompt, re.IGNORECASE):
            return label

    return f"{skill}_invocation"

# NEW FUNCTION
def _get_expected_command_scope(skill: str, config: dict) -> str:
    """Get expected command scope for this skill."""
    scope_map = {
        "research": "multi_source_investigation",
        "debugRCA": "root_cause_analysis",
        "task": "task_orchestration",
        "think": "analysis_gate"
    }
    return scope_map.get(skill, "general_command")

# MODIFIED MAIN FUNCTION
def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    intent = get_pending_intent()
    if not intent:
        sys.exit(0)

    skill = intent.get("skill", "")
    user_prompt = intent.get("prompt", "")

    # NEW: Load centralized config
    config = load_skill_config()

    if not _is_skill_execution(command, skill, config):
        sys.exit(0)

    restrictive = has_restrictive_flags(command, skill, config)

    if not restrictive:
        clear_intent_state()
        log_decision(skill, user_prompt, command, "allow", "No restrictive flags")
        sys.exit(0)

    # MODIFIED: Get enhanced justification check
    justified, reason, intent_label, expected_scope = check_intent_justification(
        user_prompt, restrictive, skill, config
    )

    if justified:
        clear_intent_state()
        log_decision(skill, user_prompt, command, "allow", reason)
        sys.exit(0)

    # BLOCK: Unjustified restrictive flags
    # NEW: Enhanced output with intent signals
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"""⛔ COMMAND INTENT MISMATCH

User invoked: /{skill} {user_prompt}
Your command: {command}

VIOLATION: {reason}

The user did not authorize these restrictions. Either:
1. Remove unauthorized flags and use skill defaults
2. Or ask user if they want to restrict execution

Re-execute with correct flags.""",
            # NEW: Signals for Stop hook
            "intentLabel": intent_label,
            "expectedCommandScope": expected_scope,
            "softWarn": False
        }
    }

    print(json.dumps(output))
    sys.exit(0)
```

### 5.3 command_execution_validator.py

**Current behavior:**
- Validates response against DESCRIPTION_PATTERNS, SIMULATION_PATTERNS
- Checks COMMAND_SPECIFIC_RULES for cwo12, exec, truth
- Validates against DO_NOT rules from active command state
- No per-skill output contract validation

**Proposed behavior:**
- Keep existing description/simulation checks
- Add per-skill output contract validation
- New validation function: `validate_contract(command_name, response_text, task_type, contract_spec)`
- Warn only for missing contracts when risk is low
- Block with remediation checklist when risk is high

**Function-level changes:**

```python
# NEW MODULE IMPORT
from typing import Any

# NEW CONFIG
CONTRACT_CONFIG_PATH = HOOKS_DIR.parent / "config" / "skill_output_contracts.json"
DEFAULT_CONTRACTS = {
    "research": {
        "task_type": "research",
        "required_fields": ["sources", "findings", "actionable_recommendations", "confidence", "next_step_question"]
    },
    "debugRCA": {
        "task_type": "debug_rca",
        "required_fields": ["problem_statement", "evidence_collected", "hypotheses", "root_cause", "recommended_fix", "verification_plan"]
    }
}

# NEW FUNCTION
def load_skill_contracts() -> dict:
    """Load skill output contract configuration."""
    try:
        import json
        if CONTRACT_CONFIG_PATH.exists():
            return json.loads(CONTRACT_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULT_CONTRACTS

# NEW FUNCTION
def validate_contract(
    command_name: str,
    response_text: str,
    task_type: str | None = None,
    contract_spec: dict | None = None
) -> dict | None:
    """
    Validate response against skill-level output contract.

    Args:
        command_name: Name of skill/command being validated
        response_text: Full response text to validate
        task_type: Task type for this command
        contract_spec: Contract specification for this skill

    Returns:
        None if valid, or {
            "decision": "block" | "warn",
            "reason": str,
            "missing_fields": list[str],
            "remediation_checklist": list[str]
        }
    """
    contracts = load_skill_contracts()
    spec = contract_spec or contracts.get(command_name, {})

    if not spec.get("required_fields"):
        return None  # No contract defined for this skill

    missing_fields = []
    for field in spec["required_fields"]:
        if not _check_field_present(response_text, field, task_type):
            missing_fields.append(field)

    if not missing_fields:
        return None  # All required fields present

    # Determine enforcement mode
    enforcement_mode = spec.get("enforcement_mode", "warn")

    # Build remediation checklist
    remediation = _build_remediation_checklist(command_name, missing_fields, spec)

    result = {
        "missing_fields": missing_fields,
        "remediation_checklist": remediation
    }

    if enforcement_mode == "block":
        result["decision"] = "block"
        result["reason"] = f"""[OUTPUT_CONTRACT_VIOLATION] /{command_name} missing required output fields

Your response is missing these required fields:
{chr(10).join(f'  • {field}' for field in missing_fields)}

Remediation checklist:
{chr(10).join(f'{i}. {item}' for i, item in enumerate(remediation, 1))}

Re-run /{command_name} and produce structured output matching contract."""
    else:  # warn
        result["decision"] = "warn"
        result["reason"] = f"""[OUTPUT_CONTRACT_WARNING] /{command_name} response incomplete

Consider adding these fields for better quality:
{chr(10).join(f'  • {field}' for field in missing_fields)}"""

    return result

# NEW FUNCTION
def _check_field_present(response: str, field: str, task_type: str | None) -> bool:
    """Check if a specific contract field is present in response."""
    import re

    # Field-specific detection patterns
    field_patterns = {
        "sources": [
            r"(?:sources?|citations?)[:]",
            r"\[.*?\](https?://)",  # Markdown link with URL
            r"source:?\s*[:\s]*(?:https?://|file://)",
        ],
        "findings": [
            r"(?:findings?|results?|analysis?)[:]",
            r"(?:found|discovered|identified)\s+(?:that\s+)?\w+",
        ],
        "actionable_recommendations": [
            r"(?:recommendation?s?|suggestion?s?|action\s+items?)[:]",
            r"\d+\.\s*\w+\s*\(",
            r"should\s+(?:implement|add|create|fix)",
        ],
        "confidence": [
            r"\bconfidence[:]\s*(?:level|score)?:?\s*\d+",
            r"(?:\d+%|high|low)\s+confidence",
        ],
        "next_step_question": [
            r"(?:next\s+step|follow.?up|clarif[yi]ing)\s*(?:question|needed)",
            r"what\s+(?:else\s+)?(?:do\s+)?(?:we\s+)?need",
        ],
        "problem_statement": [
            r"(?:problem[:]|issue[:]|error[:]|failure[:])",
            r"crash(?:es)?|fail(?:ure)?",
        ],
        "evidence_collected": [
            r"(?:evidence|data|logs?|traces?)[:]",
            r"stack\s*trace",
        ],
        "hypotheses": [
            r"(?:hypothes[ie]s?|possible\s+causes?)[:]",
            r"likely\s+cause",
        ],
        "root_cause": [
            r"(?:root\s+cause[:]|underlying\s+issue)",
        ],
        "recommended_fix": [
            r"(?:fix[:]|solution[:]|resolution[:])",
        ],
        "verification_plan": [
            r"(?:verif[yi]s?|test\s+plan|validation)",
        ]
    }

    patterns = field_patterns.get(field, [rf"\b{field}\b"])

    for pattern in patterns:
        if re.search(pattern, response, re.IGNORECASE):
            return True

    return False

# NEW FUNCTION
def _build_remediation_checklist(command: str, missing: list[str], spec: dict) -> list[str]:
    """Build specific remediation steps for missing contract fields."""
    checklist = []

    field_examples = {
        "sources": "Include source URLs, file paths, or citations (e.g., 'Sources: [https://example.com]')",
        "findings": "Summarize key discoveries (e.g., 'Findings: [...]')",
        "actionable_recommendations": "List specific next steps with priorities (e.g., 'Recommendations: 1. High: Implement X')",
        "confidence": "State overall confidence level (e.g., 'Confidence: 85%')",
        "next_step_question": "Ask what clarification would help (e.g., 'Next: What is your current environment?')",
        "problem_statement": "State problem in observable terms (e.g., 'Problem: App crashes on startup')",
        "evidence_collected": "List evidence sources (e.g., 'Evidence: [Stack trace, config.py:45]')",
        "hypotheses": "List root cause candidates (e.g., 'Hypotheses: [DATABASE_URL missing (90% likely)]')",
        "root_cause": "State most likely cause with evidence (e.g., 'Root Cause: Env var not set')",
        "recommended_fix": "Specific fix with implementation path (e.g., 'Fix: Add DATABASE_URL to .env')",
        "verification_plan": "How to confirm (e.g., 'Verify: Run app with new .env')"
    }

    for field in missing:
        if field in field_examples:
            checklist.append(field_examples[field])
        else:
            checklist.append(f"Add {field} field to your response")

    return checklist

# MODIFIED VALIDATION FUNCTION
def validate_command_execution(state: dict, response: str) -> dict | None:
    """
    Main validation function with contract checking.
    """
    command_name = state.get("command_name", "unknown")
    do_not_rules = state.get("do_not_rules", [])
    task_type = state.get("task_type")  # NEW: from enhanced state

    all_violations = []

    # Existing checks: description, do_not, specific, simulation
    description_violations = check_description_patterns(response)
    if description_violations:
        all_violations.extend([f"[DESCRIPTION] {v}" for v in description_violations])

    do_not_violations = check_do_not_violations(do_not_rules, response)
    if do_not_violations:
        all_violations.extend([f"[DO_NOT] {v}" for v in do_not_violations])

    specific_violations = check_command_specific_rules(command_name, response)
    if specific_violations:
        all_violations.extend([f"[SPECIFIC] {v}" for v in specific_violations])

    simulation_violations = check_simulation_patterns(response)
    if simulation_violations:
        all_violations.extend([f"[SIMULATION] {v}" for v in simulation_violations])

    # NEW: Contract validation
    contract_result = validate_contract(command_name, response, task_type)
    if contract_result:
        if contract_result.get("decision") == "block":
            all_violations.append("[CONTRACT] Missing required output fields")
        elif contract_result.get("decision") == "warn":
            # Add as non-blocking violation
            pass
        else:
            # Contract validated successfully
            pass

    has_execution_evidence = check_execution_evidence(response)

    if not all_violations:
        return None

    # Simulation always blocks
    if simulation_violations:
        return {
            "decision": "block",
            "reason": """[SIMULATION_DETECTED] /{command_name} was SIMULATED, not executed via Skill tool.

...existing block message..."""
        }

    # Contract violations block
    if contract_result and contract_result.get("decision") == "block":
        return contract_result

    # Serious description violations block
    if description_violations:
        # ...existing block logic...
        pass

    # Other violations
    if len(all_violations) >= 2:
        violation_summary = "; ".join(all_violations[:3])
        return {
            "decision": "block",
            "reason": f"[COMMAND_EXECUTION_VIOLATION] /{command_name}: {violation_summary}. Re-read command directive and execute properly.",
        }

    return None
```

### 5.4 Stop.py

**Current behavior:**
- Router runs gates in sequence: safety_gate, behavior_audit, command_execution_validator, advisory
- Each gate returns `{"decision": "block", "reason": "..."}` or None
- No deduplication of repeated blocks
- No unified quality summary section
- No single block decision path

**Proposed behavior:**
- Add unified "quality summary" section once per turn
- Deduplicate repeated messages by hash/cooldown
- Ensure single block decision path
- Aggregate signals from all gates

**Function-level changes:**

```python
# NEW MODULE-LEVEL STATE
_block_cache: dict[str, dict] = {
    "last_block_hash": None,
    "last_block_time": None,
    "block_cooldown_seconds": 30,
    "turn_blocks": []
}

# NEW FUNCTION
def compute_block_hash(data: dict) -> str:
    """Compute hash for deduplication."""
    import hashlib
    key_content = f"{data.get('response', '')[:500]}{data.get('session_id', '')}"
    return hashlib.md5(key_content.encode()).hexdigest()

# NEW FUNCTION
def should_dedupe_block(block_hash: str, current_time: float) -> bool:
    """Check if this block should be deduped."""
    cache = _block_cache

    # Same hash within cooldown?
    if (cache["last_block_hash"] == block_hash and
        current_time - cache.get("last_block_time", 0) < cache["block_cooldown_seconds"]):
        return True

    # Already blocked this turn with same reason?
    for turn_block in cache.get("turn_blocks", []):
        if turn_block["hash"] == block_hash:
            return True

    return False

# NEW FUNCTION
def build_quality_summary(data: dict, gate_results: list) -> str:
    """
    Build unified quality summary section.

    Args:
        data: Original Stop input data
        gate_results: List of results from all gates

    Returns:
        Formatted quality summary section
    """
    response = data.get("response", "")
    if not response or len(response) < 100:
        return ""

    summary_lines = ["", "---", "**Quality Summary**"]

    # Check assumptions
    assumptions = _check_assumptions_stated(response)
    if assumptions is True:
        summary_lines.append("✓ Assumptions stated explicitly")
    elif assumptions is False:
        summary_lines.append("⚠️ Assumptions not clearly stated")

    # Check actionable output
    command_name = _get_active_command(data)
    if command_name:
        task_type = _get_task_type_for_command(command_name)
        actionable = _check_actionable_output(response, task_type)
        if actionable:
            summary_lines.append(f"✓ Actionable output for /{command_name} ({task_type})")
        else:
            summary_lines.append(f"⚠️ Missing actionable output for /{command_name} ({task_type})")

    # Check confirmation usage
    if _needs_confirmation_was_used(data):
        summary_lines.append("✓ Confirmation used when required")

    # Count blocks this turn
    block_count = sum(1 for r in gate_results if r and r.get("decision") == "block")
    if block_count > 0:
        summary_lines.append(f"⚠️ {block_count} blocking gate(s) triggered")

    return "\n".join(summary_lines)

# NEW FUNCTION
def _check_assumptions_stated(response: str) -> bool | None:
    """Check if assumptions are stated in response."""
    assumption_patterns = [
        r"(?:assum(?:ing|ption)|assuming)",
        r"(?:i\s+(?:assume|presume))"
    ]
    import re
    for pattern in assumption_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    return None  # Couldn't determine

# NEW FUNCTION
def _get_active_command(data: dict) -> str | None:
    """Get active command from state or context."""
    # Check session state for active command
    try:
        from skill_execution_state import read_pending_state
        state = read_pending_state()
        if state:
            return state.get("skill")
    except Exception:
        pass
    return None

# NEW FUNCTION
def _get_task_type_for_command(command: str) -> str:
    """Get task type for a command."""
    try:
        from competence_state import load_skill_contracts
        contracts = load_skill_contracts()
        skill_config = contracts.get(command, {})
        return skill_config.get("task_type", "unknown")
    except Exception:
        return "unknown"

# NEW FUNCTION
def _check_actionable_output(response: str, task_type: str) -> bool:
    """Check if response has actionable output for its task type."""
    import re

    actionable_patterns = {
        "research": [r"recommend", r"should\s+(?:implement|do)", r"next?\s+step"],
        "debug_rca": [r"fix[:]", r"solution[:]", r"apply"],
        "implementation": [r"(?:writ|creat|modif)\w+"],
        "planning": [r"(?:phase|step)\s+\d+"]
    }

    patterns = actionable_patterns.get(task_type, [r"\w+"])

    for pattern in patterns:
        if re.search(pattern, response, re.IGNORECASE):
            return True

    return False

# NEW FUNCTION
def _needs_confirmation_was_used(data: dict) -> bool:
    """Check if confirmation was properly used."""
    # This would be set by UserPromptSubmit hook
    # For now, check for common confirmation patterns
    response = data.get("response", "")
    import re
    return bool(re.search(r"confirm|shall\s+i\s+proceed", response, re.IGNORECASE))

# MODIFIED MAIN FUNCTION
def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}")
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        print("{}")
        sys.exit(0)

    # NEW: Check for deduplication
    block_hash = compute_block_hash(data)
    current_time = time.time()

    if should_dedupe_block(block_hash, current_time):
        # Already blocked this turn, skip
        print("{}")
        sys.exit(0)

    system_messages: list[str] = []
    gate_results: list[dict] = []
    blocks_this_turn: list[str] = []

    # Process Blocking Gates (in-process, fast)
    for name, gate_fn in IN_PROCESS_GATES:
        try:
            res = gate_fn(data)
        except Exception as e:
            print(f"[Stop] gate {name} crashed: {e}", file=sys.stderr)
            continue

        if not res:
            continue

        # NEW: Track blocks for deduplication
        if res.get("decision") == "block":
            blocks_this_turn.append(res.get("reason", "")[:200])

        if res.get("decision") == "block":
            # NEW: Check for duplicate before emitting
            if not should_dedupe_block(block_hash, current_time):
                print(json.dumps(res))
                # NEW: Update cache
                _block_cache["last_block_hash"] = block_hash
                _block_cache["last_block_time"] = current_time
                _block_cache["turn_blocks"].append({
                    "hash": block_hash,
                    "time": current_time,
                    "reason": res.get("reason", "")
                })
            sys.exit(0)

        if "systemMessage" in res:
            system_messages.append(res["systemMessage"])

    # NEW: Build quality summary
    if gate_results:
        quality_summary = build_quality_summary(data, gate_results)
        if quality_summary:
            system_messages.append(quality_summary)

    # Process Side Effects (only if not blocked)
    if SIDE_EFFECTS:
        import concurrent.futures

        input_str = json.dumps(data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SIDE_EFFECTS)) as executor:
            for hook in SIDE_EFFECTS:
                executor.submit(run_side_effect, hook, input_str)

    output = {}
    if system_messages:
        output["systemMessage"] = "\n".join(system_messages)

    print(json.dumps(output))
```

### 5.5 Stop_next_step_suggester.py

**Current behavior:**
- Gets last command from data
- Loads suggestions from commands.toml signals mapping
- Gets suggest-field commands from orchestrator
- Adds task-unresolved when appropriate

**Proposed behavior:**
- Add signals: `needs_confirmation`, `missing_actionable_output`, `assumption_conflict_detected`
- Map signals to concrete commands
- Surface at most top 3 next-step suggestions
- Add contract-based follow-ups

**Function-level changes:**

```python
# NEW SIGNAL PATTERNS
SIGNAL_PATTERNS.update({
    "needs_confirmation": r"confirmation.*required|confirm:",
    "missing_actionable_output": r"missing.*actionable|no.*recommendations",
    "assumption_conflict_detected": r"assumption.*conflict|contradicts.*assumption",
    "contract_missing": r"output.*contract.*missing|required.*fields"
})

# MODIFIED FUNCTION
def get_next_step_options(data: dict[str, Any]) -> list[str]:
    """
    Get next step options with enhanced signal detection.
    """
    response = str(data.get("response", "") or "")
    if not response.strip():
        return []

    registry = suggestion_utils.load_commands_registry()
    signals = suggestion_utils.extract_output_signals(response)
    last_command = _extract_last_command(data)

    options: list[str] = []

    # 1) Signal-based suggestions from registry
    signal_map = registry.get("signals", {})
    for signal in signals:
        mapped = signal_map.get(signal)
        if isinstance(mapped, str) and mapped.strip():
            options.append(mapped.strip())

    # 2) NEW: Contract-based follow-ups
    command_name = _extract_command_name(data)
    if command_name and "contract_missing" in signals:
        contract_followup = _get_contract_followup(command_name)
        if contract_followup:
            options.append(contract_followup)

    # 3) NEW: Actionable output follow-ups
    if "missing_actionable_output" in signals:
        actionable_followup = _get_actionable_followup(last_command, signals)
        if actionable_followup:
            options.append(actionable_followup)

    # 4) Suggest-field graph suggestions from previous command
    for cmd in _get_suggest_field_commands(last_command):
        if not cmd.startswith("/"):
            cmd = f"/{cmd.lstrip('/')}"
        options.append(_format_with_description(cmd, registry))

    # 5) Task unresolved option for task/backlog contexts
    if _should_add_task_unresolved(response, last_command, signals):
        options.append(_format_with_description("/task-unresolved", registry))

    # Dedupe by command token, preserve order
    seen: set[str] = set()
    deduped: list[str] = []
    for opt in options:
        token = opt.split()[0].strip()
        if token and token not in seen:
            seen.add(token)
            deduped.append(opt)

    # NEW: Limit to top 3
    return deduped[:3]

# NEW FUNCTION
def _extract_command_name(data: dict[str, Any]) -> str | None:
    """Extract active command name from context."""
    # Check session state
    try:
        from skill_execution_state import read_pending_state
        state = read_pending_state()
        if state:
            return state.get("skill")
    except Exception:
        pass

    # Fallback to last command pattern
    import re
    prompt = data.get("prompt", "")
    match = re.search(r'/([a-zA-Z][a-zA-Z0-9_-]*)', prompt)
    return match.group(1) if match else None

# NEW FUNCTION
def _get_contract_followup(command: str) -> str:
    """Get contract-based follow-up suggestion."""
    followups = {
        "research": "/research - Re-run with structured output including sources, findings, and actionable recommendations",
        "debugRCA": "/debugRCA - Re-run with full RCA output including hypotheses, root cause, and verification plan",
        "task": "/task list - Check remaining tasks for this work"
    }
    return followups.get(command, "")

# NEW FUNCTION
def _get_actionable_followup(last_command: str | None, signals: list[str]) -> str:
    """Get actionable output follow-up suggestion."""
    if not last_command:
        return ""

    if "research" in last_command.lower():
        return "/research - Request specific recommendations with priorities and effort estimates"
    elif "debug" in last_command.lower() or "rca" in last_command.lower():
        return "/debugRCA - Request specific fix with verification plan"

    return ""
```

### 5.6 registry/commands.toml

**Current state:**
- Basic signal-to-command mappings
- `task_unresolved` alias configuration
- Limited to 5 signal types

**Proposed additions:**
- Add alias normalization for `/debugRCA` → `/rca`
- Add contract-based signals
- Add quality-related suggestions

**Patches:**

```toml
# P:\.claude\registry\commands.toml

[commands]
# Existing entries...
task_unresolved = "/task-unresolved - Scan unresolved items from chat history"

# NEW: Contract-based signals
[commands.contract_followup]
aliases = ["/contract-followup"]
description = "Re-run skill with proper output contract structure"

# NEW: Alias normalization
[commands.rca]
aliases = ["/rca", "/debugRCA", "/debug-rca"]
description = "Root cause analysis with systematic methodology"

# NEW: Signal mappings
[signals]
# Existing signals...
fix_applied = "/commit - Commit applied fix"
tests_passing = "/commit - Commit passing tests"
tests_failing = "/debug - Debug failing tests"
unresolved_items_detected = "/task-unresolved - Scan unresolved items"

# NEW: Competence signals
needs_confirmation = "/task - Add task after confirmation"
missing_actionable_output = "/research - Re-run with structured output"
assumption_conflict = "/think - Analyze conflicting assumptions"
contract_missing = "/contract-followup - Re-run with proper contract"

# NEW: Skill-specific quality signals
[signals.research_quality]
missing_sources = "/research - Re-run including source URLs"
weak_recommendations = "/research - Re-run with specific next steps"
no_confidence = "/research - Re-run including confidence level"

[signals.debugRCA_quality]
missing_root_cause = "/debugRCA - Re-run identifying root cause"
no_fix = "/debugRCA - Re-run with specific fix recommendation"
no_verification = "/debugRCA - Re-run with verification plan"
```

---

## 6. Skill-Level Competence Layer

### 6.1 /research SKILL.md Updates

```markdown
---
name: research
description: Multi-source research with 10+ providers
category: knowledge
triggers:
  - /research
aliases:
  - /research

# NEW: Task type declaration
task_type: research

# NEW: Contract specification
output_contract:
  required_fields:
    - sources: "Array of {url, title, snippet, accessed_at, relevance_score}"
    - findings: "Array of {claim, evidence_sources, confidence_level (0-100)}"
    - actionable_recommendations: "Array of {action, priority (high/medium/low), estimated_effort, dependencies}"
    - confidence: "Number (0-100) overall confidence in findings"
    - next_step_question: "String - what clarification would increase confidence?"
  optional_fields:
    - methodology: "String - how research was conducted"
    - limitations: "Array of known gaps or weaknesses"
    - related_work: "Array of references to prior work"
  validation_example: |
    GOOD: "Sources: [https://fastapi.tiangolo.com/async]"
          Findings: FastAPI 0.100+ supports BackgroundTasks (source 1)"
          Recommendations: 1. High: Migrate to BackgroundTasks (2 days)"
          Confidence: 85%
          Next: What is your current FastAPI version?"
    BAD: "Here's what I found about FastAPI async..."

suggest:
  - /context7
  - /search
  - /cks
---

# Research - Multi-Source Technical Research

## Purpose

Multi-source research with 10+ providers — intelligent auto-selection, HyDE query enhancement, and ML-powered semantic ranking for technical research, web search, internal knowledge bases, and GitHub repositories.

## Competence Layer Integration

This skill declares `task_type: research` and enforces output contracts for quality assurance.

### Phase A: Understand & Restate

When invoked, I will:
1. **State research question** in my own words
2. **Identify constraints** (time, sources, depth)
3. **Clarify assumptions** (what I'm assuming about your environment/context)

Example:
```
Research Question: "FastAPI async patterns"
Assumptions: You're using Python 3.10+, building web API
Constraints: Need production-ready patterns, not just examples
```

### Phase B: Enhancement & Plan

For web searches, I will:
1. **Generate hypothetical document** answering your question comprehensively
2. **Extract 3-5 key phrases** from that document
3. **Enhance your query** with these phrases for better results

### Phase C: Execute & Gather

I will run `research "{enhanced_query}" --mode auto` and collect results.

### Phase D: Contract-Compliant Output

My response MUST include these fields:

| Field | Format | Example |
|-------|--------|---------|
| **sources** | Array with citations | `Sources: [1. https://fastapi.tiangolo.com (FastAPI docs)]` |
| **findings** | Claims with evidence | `Findings: - FastAPI 0.100+ supports BackgroundTasks (source 1)` |
| **actionable_recommendations** | Prioritized actions | `Recommendations: 1. High: Migrate to BackgroundTasks (2 days)` |
| **confidence** | Overall percentage | `Confidence: 85% in FastAPI async best practices` |
| **next_step_question** | Clarifying question | `Next: What is your current FastAPI version?` |

### Phase E: Audit & Log

I will log key events via state API:
- Assumptions stated
- Sources consulted
- Final decision path
```

### 6.2 /task SKILL.md Updates

```markdown
---
name: task
description: Task orchestration - manage Claude Code task list
category: workflow
task_type: planning  # NEW: Task type declaration

# NEW: Lighter contract requirements
output_contract:
  required_fields:
    - objective: "String - clear goal statement"
    - phases: "Array of {name, description, dependencies, estimated_effort, acceptance_criteria}"
  optional_fields:
    - risk_assessment: "Array of {risk, probability, impact, mitigation}"
triggers:
  - /task
aliases:
  - /task
  - /tasks
  - /todo

suggest:
  - /nse
  - /breakdown
  - /session
---

# /task - Task Orchestration

## Purpose

Orchestrator for Claude Code task list operations. Routes sub-commands to built-in TaskCreate/TaskUpdate/TaskList/TaskGet tools.

## Competence Layer Integration

This skill declares `task_type: planning` with lighter contract requirements (guidance, not enforcement).

### Reasoning Template for Planning Work

When planning work, I consider:
1. **What is the objective** - Clear goal statement
2. **What are the major phases** - Dependencies and sequencing
3. **What risks exist** - Probability, impact, mitigation
4. **What is the estimated effort** - Per phase and total
5. **What prerequisites exist** - Must-complete items before starting

... rest of existing skill documentation ...
```

### 6.3 /debugRCA SKILL.md Updates

```markdown
---
name: debugRCA
description: AI-assisted root cause analysis engine
category: analysis
domain: debugging
version: 2.0.0  # UPDATED: Added competence layer
task_type: debug_rca  # NEW: Task type declaration

# NEW: Full RCA contract
output_contract:
  required_fields:
    - problem_statement: "String - what failed in observable terms"
    - evidence_collected: "Array of {source, content, relevance}"
    - hypotheses: "Array of {cause, likelihood (0-100), supporting_evidence, refuting_evidence}"
    - root_cause: "String - most likely cause with evidence backing"
    - recommended_fix: "String - specific fix with implementation path"
    - verification_plan: "String - how to confirm fix resolves issue"
  optional_fields:
    - prevention_strategy: "String - how to prevent similar issues"
    - related_patterns: "Array of links to similar resolved issues"
  validation_example: |
    GOOD: |
      Problem: Application crashes on startup with KeyError: 'DATABASE_URL'
      Evidence: [Stack trace: config.py:45 raises KeyError for DATABASE_URL]
      Hypotheses: [DATABASE_URL missing from env (90% likely)]
      Root Cause: Environment variable not set in production config
      Fix: Add DATABASE_URL='postgresql://...' to .env.production
      Verify: Run with new .env, confirm startup succeeds
    BAD: |
      Problem: Bug in config file
      Fix: You should fix it
triggers:
  - /debugRCA
aliases: []
suggest:
  - /r
  - /verify
  - /fix
governance:
  layer1_enforcement: true
  usage_markers:
    - "Phase 0:"
    - "Phase 1:"
    - "Phase 2:"
    - "Hypothesis"
    - "ROOT CAUSE"
    - "5 Whys"
    - "Data Flow Trace"
    - "INVESTIGATION"
    - "EVIDENCE"
---

# Debug RCA Skill v2.0

## Identity: AI-Assisted Root Cause Analysis

## What Changed in v2.0

### Competence Layer Integration
- **Task type declaration**: `task_type: debug_rca`
- **Output contract**: Required fields for systematic RCA
- **Validation**: Blocked if missing hypothesis evidence, root cause, or fix recommendation

### Phase A: Understand & Restate

When investigating an issue, I will:
1. **State problem** in observable terms (error messages, stack traces)
2. **Identify what changed** (git history, recent modifications)
3. **State my assumptions** (what I'm assuming about environment/context)

Example:
```
Problem: Application crashes on startup with KeyError: 'DATABASE_URL'
Recent Changes: Migrated config loading to environment.py (2 hours ago)
Assumptions: Running in production environment, .env.production should be loaded
```

### Phase B: Generate Hypotheses

I will generate multiple hypotheses ranked by likelihood:
- **Hypothesis 1** (most likely): {cause}, supporting evidence
- **Hypothesis 2** (less likely): {cause}, supporting evidence
- Each hypothesis requires evidence assessment before claiming

### Phase C: Validate Evidence

For each hypothesis, I will:
- **Collect evidence** supporting or refuting
- **Assign likelihood** (0-100%) based on evidence strength
- **Document reasoning** for likelihood assessment

### Phase D: Contract-Compliant Output

My response MUST include:

| Field | Format | Example |
|-------|--------|---------|
| **problem_statement** | Observable failure | `Problem: Application crashes on startup with KeyError: 'DATABASE_URL'` |
| **evidence_collected** | Sources with relevance | `Evidence: [Stack trace: config.py:45 raises KeyError]` |
| **hypotheses** | Ranked causes with evidence | `Hypotheses: [DATABASE_URL missing (90% likely)]` |
| **root_cause** | Most likely + evidence | `Root Cause: Env var not set (evidence: config.py:45 expects it)` |
| **recommended_fix** | Specific + path | `Fix: Add DATABASE_URL to .env.production` |
| **verification_plan** | How to confirm | `Verify: Run app with new .env, confirm startup succeeds` |

### Phase E: Log & Learn

I will log:
- All hypotheses with likelihood scores
- Evidence sources consulted
- Final root cause decision
- Verification steps taken
```

### 6.4 /think SKILL.md Updates

```markdown
---
name: think
description: Lightweight to comprehensive analysis gate
category: meta
task_type: audit_review  # NEW: Task type for analysis gating

# NEW: Light contract for analysis
output_contract:
  required_fields:
    - overall_assessment: "String - summary of analysis conclusion"
  optional_fields:
    - findings: "Array of {issue, severity, recommendation}"
triggers:
  - /think
aliases:
  - /think
suggest:
  - /s
  - /sequential-thinking
  - /nse
  - /analyze
---

# Analysis Gate

**Comprehensive framework for pre-build analysis.**

For routine decisions, focus on sections 1, 3, 5, 11. For architecture decisions, use all 12 sections.

## Competence Layer Integration

This skill declares `task_type: audit_review` with lightweight contract requirements.

### Reasoning Template for Analysis

When analyzing, I consider:
1. **Problem Clarification** - What are we building? (Restate feature/change in your own words)
2. **Constraints** - What are the limitations? (Technical, resource, user)
3. **Assumptions** - What assumptions am I (Claude) making? (Which assumptions, if wrong, would break solution?)
4. **Design Space** - Different approaches: (1) Approach A - Description, (2) Approach B - Description, (3) Approach C - Description
5. **Trade-off Analysis** - (Performance vs. complexity), (Security vs. usability), (Speed vs. correctness), (Short-term vs. long-term)
6. **Failure Analysis** - What can go wrong? | (Failure: Likelihood | Severity | Mitigation)
7. **Boundaries & Invariants** - What must stay constant? | (Invariants: "X must never happen", Boundaries: "Only works when...")
8. **Observability & Control** - How do we monitor and steer? | (Metrics: what to measure, Logging: what to log, Control: how to adjust)
9. **Reversibility** - Can we undo this? | (Reversibility Score: R1-R:4, Rollback plan: How to undo, Entropy control: What side effects persist)
10. **Adversarial Review** - Paranoid staff engineer objections | (Objection 1: "This is fragile and will break because...", Objection 2: "You're solving a tool limitation with a hack...")
11. **AI Delegation** - What's safe to delegate to AI subagents? | (✅ Safe to delegate: Task 1 → specific subagent, Task 2 → specific subagent), ⚠️ Human oversight required, ❌ Human-only)
12. **Decision Summary** - Short-term, Long-term, Remaining unknowns, Follow-up questions, Dependencies

### Output Format

For complex decisions (architecture, multi-component), my response MUST include:
- **Overall Assessment**: Summary conclusion
- **Findings** (optional): Structured issues discovered

For routine decisions, my response follows the 12-section framework internally but outputs distilled recommendations.

---

## 7. Rollout & Safety Plan

### Week-by-Week Rollout

**Week 1: Foundation**
- Create new config files (`competence_taxonomy.json`, `risk_policy.json`, `skill_output_contracts.json`)
- Implement `competence_state.py` with SQLite schema
- Add alias normalization to `commands.toml`
- Safety: Feature flag `COMPETENCE_LAYER_ENABLED=false`

**Week 2: UserPromptSubmit enhancements**
- Add `intent_router()`, `risk_assessor()`, `build_competence_context()` to `skill_enforcer.py`
- Implement task-type guidance injection
- Add block handling for critical risk
- Safety: Only log risk assessments, don't block yet

**Week 3: Stop hook quality summary**
- Add unified quality summary to `Stop.py`
- Implement deduplication by hash
- Add single block decision path
- Safety: Enable in warn mode only

**Week 4: Contract validation**
- Add `validate_contract()` to `command_execution_validator.py`
- Implement field detection patterns
- Add remediation checklists
- Safety: Enable for research skill only

**Week 5: Full rollout**
- Enable all enforcement modes
- Add contract validation to all skills
- Remove feature flag
- Safety: Monitor for over-blocking

### Feature Flags

```bash
# P:\.claude\settings.json
{
  "env": {
    "COMPETENCE_LAYER_ENABLED": "true",
    "CONTRACT_VALIDATION_ENABLED": "true",
    "RISK_ASSESSMENT_ENABLED": "true",
    "QUALITY_SUMMARY_ENABLED": "true",

    # Rollout controls
    "CONTRACT_ENFORCEMENT_MODE": "warn",  # "off" | "warn" | "block"
    "RISK_BLOCK_THRESHOLD": 90,  # 70-100, only block above this score

    # Per-skill overrides
    "CONTRACT_ENFORCEMENT_RESEARCH": "block",
    "CONTRACT_ENFORCEMENT_DEBUGRCA": "block",
    "CONTRACT_ENFORCEMENT_TASK": "warn",
    "CONTRACT_ENFORCEMENT_THINK": "off"
  }
}
```

### Acceptance Tests

```python
# P:\.claude\hooks\tests\test_competence_layer.py
import pytest
from competence_state import CompetenceStateStore, append_audit_event

def test_research_missing_contract_blocked():
    """Test that /research without sources is blocked."""
    state = CompetenceStateStore(session_id="test", terminal_id="test")

    # Simulate /research with no sources
    event = {
        "skill_name": "research",
        "task_type": "research",
        "risk_level": "low",
        "contract_status": {
            "status": "missing",
            "missing_fields": ["sources", "actionable_recommendations"]
        },
        "block_reason": "Missing required fields"
    }

    result = append_audit_event(event, session_id="test", terminal_id="test")
    assert result == True

    # Verify it was stored
    events = state.get_recent_events(limit=1)
    assert len(events) == 1
    assert events[0]["action_taken"] == "blocked"

def test_debugrca_full_contract_allowed():
    """Test that /debugRCA with all fields passes."""
    event = {
        "skill_name": "debugRCA",
        "task_type": "debug_rca",
        "risk_level": "low",
        "contract_status": {
            "status": "complete",
            "missing_fields": []
        },
        "suggestions": None
    }

    result = append_audit_event(event, session_id="test", terminal_id="test")
    assert result == True

def test_task_low_risk_no_confirmation():
    """Test that low-risk /task doesn't require confirmation."""
    # This would be tested via actual hook invocation
    # Verify that /task add "simple task" doesn't trigger confirmation
    pass

def test_deduplication_works():
    """Test that duplicate blocks are deduped."""
    from Stop import should_dedupe_block, compute_block_hash

    data = {"response": "test response", "session_id": "test"}
    block_hash = compute_block_hash(data)

    # First call should not dedupe
    assert not should_dedupe_block(block_hash, 100.0)

    # Second call within cooldown should dedupe
    assert should_dedupe_block(block_hash, 100.0)
```

### Rollback Plan

If issues arise:

1. **Immediate disable** - Set `COMPETENCE_LAYER_ENABLED=false`
2. **Selective rollback** - Disable specific features via env vars:
   - `CONTRACT_VALIDATION_ENABLED=false`
   - `RISK_ASSESSMENT_ENABLED=false`
   - `QUALITY_SUMMARY_ENABLED=false`
3. **Revert hooks** - Keep git history of pre-patch versions
4. **Data preservation** - SQLite database persists for debugging

---

## Summary

This design adds a **competence layer** on top of your existing **compliance layer**:

| Layer | Focus | Mechanism |
|-------|--------|------------|
| **Compliance (existing)** | What NOT to do | CLAUDE.md, hooks block violations |
| **Competence (new)** | How to do it WELL | Task types, output contracts, risk-based confirmation |

**Key improvements:**
1. **Task-type taxonomy** - 6 types with reasoning templates and output contracts
2. **Risk assessment** - Deterministic heuristics before LLM classification
3. **State API** - SQLite with audit events and TTL
4. **Contract validation** - Per-skill required fields with remediation
5. **Quality summary** - Unified view in Stop hook
6. **Deduplication** - No more spammy error loops

This is a **patch-level plan** - each hook file has specific function-level changes, and rollout is staged with safety flags.

---

## GOAL

Make the system:

1. **Measurable**: a few concrete KPIs and evals so we can tell if changes help.
2. **Reflective**: richer self‑checks on important turns (not for everything).
3. **Adaptive**: simple, config‑driven adjustment rules based on logs + feedback.

Deliver code/config I can paste in:

- New/updated Python modules.
- New SQL and JSON.
- Hook/skill changes.
- A small usage/readme section.

Be explicit and mechanical.

***

## 1. Golden-path evals and a `/run-evals` helper

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

You do NOT need to populate it; just assume it exists and has 5–20 cases per skill.

### 1.2 New script/skill `/run-evals`

Create a script (and wire it as a skill if needed) that:

- Reads `golden_evals.json`.
- For each case, triggers a prompt **through the same hooks** (or describes how I should run them manually).
- Then queries `competence_events` to compute simple metrics.

Define a new Python module:

`P:\.claude\hooks\evals\run_evals.py`:

- Functions to implement:

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

***

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

***

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
      "condition": "> 0.2",
      "suggested_action": "Strengthen debug_rca reasoning template; require explicit alternative hypotheses and falsification evidence."
    }
  ]
}
```

No automation yet. This is for `/audit-quality` skill to read and propose changes.

***

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

***

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

***

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
| **Quality audit** | Skill to summarize metrics and apply rules | `/audit-quality` skill |
| **Sensitivity** | Optional env-based risk bump for production | `_env_sensitivity_boost()` |

No auto-execution. All improvements are suggestions for simpler LLM to implement manually.

