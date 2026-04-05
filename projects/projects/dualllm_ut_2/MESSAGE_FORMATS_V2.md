# Enhanced Message Formats V2

**Version**: 2.0.0
**Date**: 2025-01-07
**Type**: Multi-Agent Communication Specification
**Enhancement**: Consensus-ready and framework-integrated formats

---

## OVERVIEW

This document defines enhanced message formats for multi-agent AI coordination, incorporating consensus mechanisms, framework integration patterns, and robust error handling.

## CORE MESSAGE STRUCTURE V2

### **Base Message Format (Enhanced)**
```json
{
  "message_metadata": {
    "message_id": "uuid_v4_unique_identifier",
    "timestamp": "2025-01-07T14:30:45.123456Z",
    "sequence_number": 1001,
    "protocol_version": "2.0.0",
    "checksum": "sha256_integrity_hash",
    "signature": "agent_authentication_signature"
  },

  "agent_information": {
    "sender_id": "agent_uuid_identifier",
    "sender_role": "coordinator|specialist|quality_assessor",
    "sender_specialization": "planner|implementer|tester|inspector|curator",
    "sender_capabilities": ["task_planning", "code_generation", "testing"],
    "sender_status": "active|busy|degraded|offline"
  },

  "routing_information": {
    "target_agents": ["agent_uuid_1", "agent_uuid_2"],
    "target_roles": ["coordinator", "specialist"],
    "routing_strategy": "direct|broadcast|capability_based|consensus_panel",
    "priority": "critical|high|normal|low",
    "delivery_requirements": {
      "acknowledgment_required": true,
      "delivery_timeout_seconds": 30,
      "retry_policy": "exponential_backoff",
      "max_retries": 3
    }
  },

  "message_content": {
    "message_type": "task|coordination|consensus|status|error|result",
    "action": "specific_action_requested",
    "context": "relevant_background_information",
    "parameters": {},
    "expected_outcome": "description_of_expected_result",
    "confidence_level": 0.85,
    "reasoning": "explanation_of_decision_logic",
    "dependencies": ["prerequisite_task_ids"],
    "constraints": ["time_limits", "resource_constraints"]
  },

  "consensus_data": {
    "consensus_required": true,
    "panel_configuration": {
      "minimum_participants": 3,
      "required_roles": ["coordinator", "specialist", "quality_assessor"],
      "decision_threshold": 0.75,
      "timeout_minutes": 10
    },
    "voting_criteria": ["accuracy", "feasibility", "quality", "maintainability"],
    "decision_deadline": "2025-01-07T15:00:00.000Z"
  }
}
```

## SPECIALIZED MESSAGE TYPES

### **Task Assignment Message**
```json
{
  "message_type": "task_assignment",
  "task_details": {
    "task_id": "task_uuid_identifier",
    "task_name": "descriptive_task_name",
    "task_description": "detailed_task_description",
    "task_type": "implementation|testing|review|coordination",
    "complexity_level": "simple|moderate|complex|critical",
    "estimated_duration_minutes": 45,
    "required_capabilities": ["python_coding", "test_generation"],
    "success_criteria": ["specific_measurable_outcomes"],
    "deliverables": ["expected_outputs_and_formats"]
  },

  "assignment_context": {
    "project_context": "overall_project_information",
    "related_tasks": ["dependent_task_ids"],
    "available_resources": ["tools", "documentation", "examples"],
    "constraints": ["time_limits", "quality_requirements"],
    "escalation_path": "fallback_agent_or_human_contact"
  }
}
```

### **Consensus Vote Message**
```json
{
  "message_type": "consensus_vote",
  "vote_details": {
    "original_message_id": "uuid_of_message_being_voted_on",
    "voter_agent_id": "voting_agent_identifier",
    "vote_decision": "approve|reject|abstain|conditional_approve",
    "confidence_score": 0.90,
    "vote_timestamp": "2025-01-07T14:35:00.000Z"
  },

  "vote_reasoning": {
    "primary_rationale": "main_reason_for_vote_decision",
    "supporting_evidence": ["facts_supporting_the_decision"],
    "concerns_identified": ["potential_issues_or_risks"],
    "alternative_suggestions": ["proposed_modifications_or_alternatives"],
    "conditions_for_approval": ["requirements_that_must_be_met"]
  },

  "quality_assessment": {
    "accuracy_score": 0.85,
    "feasibility_score": 0.90,
    "quality_score": 0.88,
    "maintainability_score": 0.92,
    "overall_recommendation": "approve_with_minor_modifications"
  }
}
```

### **Status Update Message**
```json
{
  "message_type": "status_update",
  "status_information": {
    "agent_status": "active|busy|idle|degraded|offline",
    "current_tasks": ["list_of_active_task_ids"],
    "task_progress": {
      "task_id": "current_task_identifier",
      "completion_percentage": 65,
      "estimated_completion": "2025-01-07T15:30:00.000Z",
      "blockers_identified": ["issues_preventing_progress"],
      "assistance_needed": ["types_of_help_required"]
    },
    "resource_utilization": {
      "cpu_usage_percent": 45,
      "memory_usage_percent": 60,
      "active_connections": 3,
      "queue_depth": 2
    }
  },

  "health_metrics": {
    "response_time_ms": 150,
    "error_rate_percent": 0.5,
    "success_rate_percent": 99.5,
    "last_health_check": "2025-01-07T14:40:00.000Z",
    "performance_trend": "stable|improving|degrading"
  }
}
```

### **Error Report Message**
```json
{
  "message_type": "error_report",
  "error_details": {
    "error_id": "unique_error_identifier",
    "error_type": "system|communication|task|consensus|integration",
    "severity": "critical|high|medium|low",
    "error_message": "human_readable_error_description",
    "error_code": "machine_readable_error_code",
    "timestamp": "2025-01-07T14:45:00.000Z",
    "affected_components": ["list_of_affected_systems"]
  },

  "error_context": {
    "triggering_event": "action_that_caused_the_error",
    "system_state": "relevant_system_state_information",
    "related_messages": ["message_ids_related_to_error"],
    "attempted_recovery": ["recovery_actions_already_tried"],
    "impact_assessment": "description_of_error_impact"
  },

  "recovery_information": {
    "automatic_recovery_possible": true,
    "suggested_recovery_actions": ["recommended_recovery_steps"],
    "escalation_required": false,
    "estimated_recovery_time": "5_minutes",
    "fallback_strategies": ["alternative_approaches"]
  }
}
```

## FRAMEWORK-SPECIFIC EXTENSIONS

### **CANDOR Framework Extensions**
```json
{
  "candor_extensions": {
    "agent_specialization": {
      "primary_role": "initializer|planner|implementer|tester|inspector|curator",
      "secondary_capabilities": ["additional_skills"],
      "expertise_level": "novice|intermediate|expert|master",
      "collaboration_preferences": ["preferred_working_patterns"]
    },

    "panel_discussion_data": {
      "discussion_phase": "independent|structured|consensus|decision",
      "contribution_type": "analysis|opinion|evidence|synthesis",
      "discussion_round": 1,
      "time_allocated_minutes": 5,
      "discussion_focus": "specific_aspect_being_discussed"
    }
  }
}
```

### **Qodo Cover-Agent Extensions**
```json
{
  "qodo_extensions": {
    "testing_context": {
      "test_type": "unit|integration|system|performance|security",
      "coverage_target": "line|branch|function|condition",
      "current_coverage_percent": 75.5,
      "target_coverage_percent": 85.0,
      "test_framework": "pytest|unittest|hypothesis|custom"
    },

    "coverage_analysis": {
      "uncovered_lines": ["file:line_number_ranges"],
      "uncovered_branches": ["branch_identifiers"],
      "uncovered_functions": ["function_names"],
      "complexity_hotspots": ["high_complexity_areas"],
      "recommended_test_types": ["suggested_test_approaches"]
    }
  }
}
```

### **Langroid Communication Extensions**
```json
{
  "langroid_extensions": {
    "communication_metadata": {
      "conversation_id": "ongoing_conversation_identifier",
      "conversation_context": "conversation_background",
      "message_chain_position": 5,
      "response_expected": true,
      "response_timeout_seconds": 60
    },

    "routing_intelligence": {
      "capability_requirements": ["required_agent_capabilities"],
      "load_balancing_hint": "prefer_least_loaded|prefer_specialized",
      "geographic_preference": "local|regional|global",
      "cost_optimization": "minimize_latency|minimize_cost|balanced"
    }
  }
}
```

## MESSAGE VALIDATION AND SECURITY

### **Validation Schema**
```json
{
  "validation_requirements": {
    "required_fields": [
      "message_metadata.message_id",
      "message_metadata.timestamp",
      "agent_information.sender_id",
      "message_content.message_type"
    ],

    "field_constraints": {
      "message_id": "uuid_v4_format",
      "timestamp": "iso8601_with_microseconds",
      "confidence_level": "float_between_0_and_1",
      "priority": "enum_critical_high_normal_low"
    },

    "conditional_requirements": {
      "consensus_required_true": ["consensus_data.panel_configuration"],
      "message_type_task": ["task_details"],
      "message_type_error": ["error_details", "recovery_information"]
    }
  }
}
```

### **Security Measures**
```json
{
  "security_configuration": {
    "authentication": {
      "method": "digital_signature_with_certificates",
      "key_rotation_hours": 24,
      "certificate_authority": "internal_ca",
      "signature_algorithm": "RSA_SHA256"
    },

    "encryption": {
      "in_transit": "TLS_1_3",
      "at_rest": "AES_256_GCM",
      "key_management": "hardware_security_module",
      "perfect_forward_secrecy": true
    },

    "access_control": {
      "authorization_model": "role_based_access_control",
      "permission_granularity": "message_type_and_content_level",
      "audit_logging": "comprehensive_with_integrity_protection",
      "session_management": "jwt_with_refresh_tokens"
    }
  }
}
```

## MESSAGE FLOW PATTERNS

### **Consensus Decision Flow**
```yaml
consensus_message_flow:
  1_initiation:
    message_type: "consensus_request"
    sender: "any_agent_requiring_consensus"
    targets: "consensus_panel_members"

  2_independent_analysis:
    message_type: "analysis_submission"
    sender: "each_panel_member"
    targets: "consensus_coordinator"

  3_structured_discussion:
    message_type: "discussion_contribution"
    sender: "panel_members_in_turn"
    targets: "all_panel_members"

  4_consensus_voting:
    message_type: "consensus_vote"
    sender: "each_panel_member"
    targets: "consensus_coordinator"

  5_decision_announcement:
    message_type: "consensus_decision"
    sender: "consensus_coordinator"
    targets: "all_interested_agents"
```

### **Task Coordination Flow**
```yaml
task_coordination_flow:
  1_task_creation:
    message_type: "task_assignment"
    sender: "coordinator_agent"
    targets: "capable_agents"

  2_capability_assessment:
    message_type: "capability_response"
    sender: "candidate_agents"
    targets: "coordinator_agent"

  3_assignment_confirmation:
    message_type: "assignment_confirmation"
    sender: "coordinator_agent"
    targets: "selected_agent"

  4_progress_updates:
    message_type: "status_update"
    sender: "assigned_agent"
    targets: "coordinator_agent"
    frequency: "regular_intervals_or_milestones"

  5_completion_notification:
    message_type: "task_completion"
    sender: "assigned_agent"
    targets: "coordinator_agent_and_stakeholders"
```

---

**These enhanced message formats provide comprehensive, secure, and framework-integrated communication protocols for robust multi-agent AI coordination systems.**
