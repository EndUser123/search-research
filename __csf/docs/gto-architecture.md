# GTO v3.5 Architecture

## Component Flow Diagram

```mermaid
flowchart TB
    subgraph INPUT["INPUT / Entry Points"]
        CLI["CLI: gto_orchestrator.py"]
        SESSION["Session Context Detection"]
        AUTO["Auto-detect target from conversation"]
    end

    subgraph LAYER1["Layer 1: Deterministic Detectors (Python)"]
        direction TB
        D1["check_test_presence<br/>test_presence_checker.py"]
        D2["check_docs_presence<br/>docs_presence_checker.py"]
        D3["check_viability<br/>viability_gate.py"]
        D4["check_dependencies<br/>dependency_checker.py"]
        D5["scan_code_markers<br/>code_marker_scanner.py"]
        D6["detect_git_context<br/>git_context.py"]
        D7["detect_session_goal<br/>session_goal_detector.py"]
        D8["detect_unfinished_business<br/>unfinished_business_detector.py"]
        D9["detect_suspicion<br/>suspicion_detector.py"]
        D10["detect_session_outcomes<br/>session_outcome_detector.py"]
        D11["check_entry_points<br/>entry_point_checker.py"]
        D12["check_skill_health<br/>skill_self_health_checker.py"]
        D13["check_gto_self_health<br/>gto_self_health_detector.py"]
        D14["check_chain_integrity<br/>chain_integrity_checker.py"]
    end

    subgraph LAYER2["Layer 2: AI Subagents"]
        direction TB
        S1["gap_finder_subagent.py<br/>Finds gaps via AI reasoning"]
        S2["health_calculator_subagent.py<br/>Calculates composite health"]
    end

    subgraph LAYER3["Layer 3: Orchestration"]
        direction TB
        ORCH["gto_orchestrator.py<br/>Coordinates all layers"]
        RESULTS["results_builder.py<br/>Consolidates detector output"]
        FORMAT["next_steps_formatter.py<br/>Formats findings as markdown"]
        SM["state_manager.py<br/>Persists session state"]
        SD["skill_coverage_detector.py<br/>Maps gaps → skills"]
        SDB["skill_registry_bridge.py<br/>Registry lookups"]
        GAP_MAP["gap_skill_mapper.py<br/>Gap → Skill affinity"]
        GAP_TRACK["gap_resolution_tracker.py<br/>Cross-session gap closure"]
    end

    subgraph OUTPUT["Output / Persistence"]
        JSON["JSON artifact<br/>~/.claude/.evidence/gto-outputs/"]
        MD["Markdown report<br/>stdout"]
    end

    INPUT --> LAYER1
    LAYER1 --> LAYER3
    LAYER2 --> LAYER3
    LAYER3 --> OUTPUT

    style LAYER1 fill:#1a1a2e,stroke:#00d4ff,color:#00d4ff
    style LAYER2 fill:#1a1a2e,stroke:#ff6b6b,color:#ff6b6b
    style LAYER3 fill:#1a1a2e,stroke:#ffd93d,color:#ffd93d
    style INPUT fill:#0d1b2a,stroke:#6c63ff,color:#6c63ff
    style OUTPUT fill:#0d1b2a,stroke:#4ecdc4,color:#4ecdc4
```

## Gap Resolution Tracker (Cross-Session Loop Closure)

```mermaid
flowchart LR
    subgraph Session_N["Session N"]
        PREV["_load_previous_gaps()<br/>Reads gaps from prior session"]
        TRACK["track_gap_resolutions()<br/>Compares prev vs current"]
        VERIFY["_verify_past_resolutions()<br/>Checks if gaps truly resolved"]
    end

    subgraph Session_N1["Session N+1"]
        SAVE["_save_previous_gaps()<br/>Persists current gaps"]
        CREDIT["Resolved gaps credited to skill"]
        DEMOTE["Failed verifications demote skill score"]
    end

    subgraph Persistence["State Files"]
        RES_LOG["resolution.log<br/>gap_ids_resolved per skill"]
        VERIF_LOG["verification.log<br/>Verification records"]
        PREV_GAPS["previous_gaps.json<br/>Snapshot per terminal"]
    end

    PREV --> TRACK
    TRACK --> VERIFY
    VERIFY --> SAVE
    VERIFY --> CREDIT
    VERIFY --> DEMOTE
    TRACK -.-> RES_LOG
    VERIFY -.-> VERIF_LOG
    SAVE -.-> PREV_GAPS

    style Session_N fill:#16213e,stroke:#00d4ff,color:#00d4ff
    style Session_N1 fill:#16213e,stroke:#4ecdc4,color:#4ecdc4
    style Persistence fill:#0d1b2a,stroke:#6c63ff,color:#6c63ff
```

## Skill Coverage Detection Flow

```mermaid
flowchart TB
    GAPS["Raw Gaps List"] --> MAP["gap_skill_mapper.py<br/>Calculates gap→skill affinity scores"]
    MAP --> BRIDGE["skill_registry_bridge.py<br/>Looks up skill definitions"]
    BRIDGE --> COVERAGE["skill_coverage_detector.py<br/>Detects coverage per skill"]
    COVERAGE --> RESULTS_B["results_builder.py<br/>Builds ConsolidatedResults"]

    style MAP fill:#2d2d44,stroke:#ff6b6b,color:#ff6b6b
    style BRIDGE fill:#2d2d44,stroke:#ffd93d,color:#ffd93d
    style COVERAGE fill:#2d2d44,stroke:#4ecdc4,color:#4ecdc4
```

## State Manager Schema

```mermaid
erDiagram
    StateManager ||--o{ Gap : contains
    StateManager ||--o{ SkillHealth : tracks
    StateManager ||--o{ SessionContext : holds

    Gap {
        str id
        str type
        str message
        str severity
        str file_path
        int line_number
    }

    SkillHealth {
        str skill_name
        float effectiveness_score
        int total_gaps
        int resolved_gaps
        list resolved_gap_ids
    }

    SessionContext {
        str project_root
        str terminal_id
        str session_id
        list active_gaps
        list detected_skills
    }
```

## File Inventory

| Module | Layer | Responsibility |
|--------|-------|----------------|
| `gto_orchestrator.py` | 3 | Main entry, coordinates all components |
| `lib/state_manager.py` | 3 | State persistence and retrieval |
| `lib/results_builder.py` | 3 | Result consolidation |
| `lib/next_steps_formatter.py` | 3 | Markdown output formatting |
| `lib/gap_resolution_tracker.py` | 3 | Cross-session loop closure |
| `lib/skill_coverage_detector.py` | 3 | Gap→skill coverage mapping |
| `lib/skill_registry_bridge.py` | 3 | Skill registry lookups |
| `lib/gap_skill_mapper.py` | 3 | Gap→skill affinity scoring |
| `lib/viability_gate.py` | 1 | Project viability checks |
| `lib/dependency_checker.py` | 1 | Dependency health |
| `lib/test_presence_checker.py` | 1 | Missing test detection |
| `lib/docs_presence_checker.py` | 1 | Documentation gaps |
| `lib/code_marker_scanner.py` | 1 | TODO/FIXME/BUG markers |
| `lib/git_context.py` | 1 | Git context detection |
| `lib/session_goal_detector.py` | 1 | Session goal detection |
| `lib/unfinished_business_detector.py` | 1 | Unfinished work detection |
| `lib/suspicion_detector.py` | 1 | Suspicious patterns |
| `lib/session_outcome_detector.py` | 1 | Session outcome detection |
| `lib/entry_point_checker.py` | 1 | Entry point validation |
| `lib/skill_self_health_checker.py` | 1 | Skill health checks |
| `lib/gto_self_health_detector.py` | 1 | GTO internal health |
| `lib/chain_integrity_checker.py` | 1 | Chain integrity checks |
| `subagents/gap_finder_subagent.py` | 2 | AI-powered gap finding |
| `subagents/health_calculator_subagent.py` | 2 | AI health calculation |
| `hooks/checklist_gate.py` | Hooks | Pre-execution checklist |
| `hooks/gto_verify_wrapper.py` | Hooks | Verification wrapper |
| `hooks/session_summary.py` | Hooks | Session summary capture |
| `hooks/validate_format.py` | Hooks | Format validation |
| `hooks/gto_failure_capture.py` | Hooks | Failure capture |
