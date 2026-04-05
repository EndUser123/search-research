#!/usr/bin/env python3
"""
Smart Handoff Manager for Universal Command Integration
Handles seamless transitions and context sharing between commands
"""

import json
import logging
from datetime import datetime
from typing import Any

from shared_evidence_manager import (
    IntegrationContext,
    ProjectContext,
    SharedEvidenceManager,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandoffValidationError(Exception):
    """Raised when command handoff validation fails"""
    pass

class SmartHandoffManager:
    """Manages intelligent handoffs between commands"""

    def __init__(self, evidence_manager: SharedEvidenceManager = None):
        self.evidence_manager = evidence_manager or evidence_manager
        self.handoff_history = []

    def validate_command_transition(self, from_command: str, to_command: str,
                                  detected_work: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate if transition between commands is valid and appropriate"""

        validation_issues = []
        is_valid = True

        # Check if transition is supported by command capabilities
        capabilities = self._load_command_capabilities()
        from_cap = capabilities.get(from_command, {})
        to_cap = capabilities.get(to_command, {})

        # Validate handoff support
        if to_command not in from_cap.get('can_handoff_to', []):
            if to_command not in from_cap.get('can_continue_with', []):
                validation_issues.append(f"{from_command} cannot handoff to {to_command}")
                is_valid = False

        # Validate inheritance support
        if from_command not in to_cap.get('can_inherit_from', []):
            if from_command != "any_command":
                validation_issues.append(f"{to_command} cannot inherit from {from_command}")

        # Check for redundant transitions
        if from_command == to_command:
            validation_issues.append("Redundant handoff to same command")
            is_valid = False

        # Validate project state consistency
        project_context = detected_work.get('project_context')
        if project_context:
            if from_command not in project_context.active_commands:
                validation_issues.append(f"{from_command} not in active commands")
                is_valid = False

        return is_valid, validation_issues

    def prepare_context_for_command(self, target_command: str,
                                   current_context: dict[str, Any]) -> dict[str, Any]:
        """Prepare context for target command based on current state"""

        prepared_context = {
            'target_command': target_command,
            'prepared_at': datetime.now().isoformat(),
            'inherited_evidence': {},
            'quality_status': {},
            'next_steps': [],
            'avoid_redunant_work': []
        }

        # Extract relevant evidence based on target command
        relevant_evidence = self._extract_relevant_evidence(target_command, current_context)
        prepared_context['inherited_evidence'] = relevant_evidence

        # Determine quality status and gates
        quality_status = self._assess_quality_status(target_command, current_context)
        prepared_context['quality_status'] = quality_status

        # Generate next steps and work to avoid
        next_steps, avoid_work = self._generate_execution_plan(target_command, current_context)
        prepared_context['next_steps'] = next_steps
        prepared_context['avoid_redunant_work'] = avoid_work

        return prepared_context

    def _extract_relevant_evidence(self, target_command: str,
                                 current_context: dict[str, Any]) -> dict[str, Any]:
        """Extract evidence relevant to target command"""
        relevant_evidence = {}

        # Define evidence relevance mapping
        relevance_map = {
            "/cwo12": {
                "relevant_commands": ["/ask", "/research", "/speckit.plan", "/exec", "/gw.code-review"],
                "required_evidence": ["project_context", "completed_phases", "quality_scores"]
            },
            "/ask": {
                "relevant_commands": ["/research", "/learn", "/truth"],
                "required_evidence": ["previous_analysis", "research_findings", "validation_results"]
            },
            "/research": {
                "relevant_commands": ["/ask", "/learn", "/explore"],
                "required_evidence": ["analysis_requirements", "existing_knowledge", "research_gaps"]
            },
            "/exec": {
                "relevant_commands": ["/speckit.plan", "/ask", "/cwo12"],
                "required_evidence": ["implementation_plan", "requirements_analysis", "architecture_design"]
            },
            "/speckit.plan": {
                "relevant_commands": ["/ask", "/research", "/arch"],
                "required_evidence": ["requirements_analysis", "research_findings", "constraints_analysis"]
            },
            "/gw.code-review": {
                "relevant_commands": ["/exec", "/cwo12", "/test-fix"],
                "required_evidence": ["implementation_artifacts", "test_results", "quality_metrics"]
            }
        }

        target_relevance = relevance_map.get(target_command, {})
        relevant_commands = target_relevance.get("relevant_commands", [])

        # Extract evidence from relevant commands
        for command in relevant_commands:
            evidence_key = f"{command.replace('/', '_')}_completed"
            if evidence_key in current_context:
                evidence = current_context[evidence_key]
                if evidence:
                    relevant_evidence[command] = {
                        'command_name': command,
                        'execution_time': evidence.execution_time.isoformat() if hasattr(evidence, 'execution_time') else None,
                        'results_summary': evidence.results_summary if hasattr(evidence, 'results_summary') else "",
                        'quality_metrics': evidence.quality_metrics if hasattr(evidence, 'quality_metrics') else {},
                        'evidence_paths': evidence.evidence_paths if hasattr(evidence, 'evidence_paths') else [],
                        'handoff_ready': evidence.handoff_ready if hasattr(evidence, 'handoff_ready') else False
                    }

        # Add project context if available
        if current_context.get('project_context'):
            relevant_evidence['project_context'] = {
                'project_id': current_context['project_context'].project_id,
                'current_phase': current_context['project_context'].current_phase,
                'completed_phases': current_context['project_context'].completed_phases,
                'active_commands': current_context['project_context'].active_commands,
                'quality_scores': current_context['project_context'].quality_scores
            }

        return relevant_evidence

    def _assess_quality_status(self, target_command: str,
                             current_context: dict[str, Any]) -> dict[str, Any]:
        """Assess quality status for target command"""
        quality_status = {
            'overall_quality_score': 0.0,
            'quality_gates_passed': [],
            'quality_gates_failed': [],
            'recommended_threshold': 0.85,
            'ready_for_handoff': False
        }

        # Collect quality scores from available evidence
        quality_scores = []
        evidence_items = current_context.values()

        for item in evidence_items:
            if hasattr(item, 'quality_metrics'):
                quality_metrics = item.quality_metrics
                if isinstance(quality_metrics, dict):
                    quality_scores.extend(quality_metrics.values())

        # Calculate overall quality score
        if quality_scores:
            quality_status['overall_quality_score'] = sum(quality_scores) / len(quality_scores)

        # Determine quality gates status
        project_context = current_context.get('project_context')
        if project_context:
            quality_status['quality_gates_passed'] = self._check_quality_gates(project_context)

        # Set recommended threshold based on target command
        thresholds = {
            "/cwo12": 0.90,
            "/gw.code-review": 0.95,
            "/qual-gate": 0.85,
            "/ask": 0.80,
            "/research": 0.85
        }
        quality_status['recommended_threshold'] = thresholds.get(target_command, 0.85)

        # Determine if ready for handoff
        quality_status['ready_for_handoff'] = (
            quality_status['overall_quality_score'] >= quality_status['recommended_threshold'] and
            len(quality_status['quality_gates_passed']) > 0
        )

        return quality_status

    def _generate_execution_plan(self, target_command: str,
                               current_context: dict[str, Any]) -> tuple[list[str], list[str]]:
        """Generate execution plan with next steps and work to avoid"""
        next_steps = []
        avoid_work = []

        project_context = current_context.get('project_context')
        completed_phases = project_context.completed_phases if project_context else []

        # Command-specific execution planning
        if target_command == "/cwo12":
            if not completed_phases:
                next_steps.extend([
                    "Step 1: Input Analysis & Quality Assessment",
                    "Step 2: GW.ASK Enhanced Analysis & Complexity Assessment",
                    "Step 3: Strategic Planning & Resource Allocation"
                ])
            elif "input_analysis" in completed_phases:
                if "requirements_research" not in completed_phases:
                    next_steps.append("Step 2: GW.ASK Enhanced Analysis")
                elif "strategic_planning" not in completed_phases:
                    next_steps.append("Step 3: Strategic Planning & Resource Allocation")
                else:
                    next_steps.append("Continue from Step 4: Multi-Agent Selection")

            # Work to avoid based on completed phases
            if "input_analysis" in completed_phases:
                avoid_work.append("Redundant input quality assessment")
            if "requirements_research" in completed_phases:
                avoid_work.append("Duplicate requirements analysis")
            if "strategic_planning" in completed_phases:
                avoid_work.append("Re-planning already planned work")

        elif target_command == "/exec":
            if "strategic_planning" not in completed_phases:
                next_steps.append("Complete strategic planning first")
            next_steps.append("Execute enhanced implementation with 60% cognitive improvement")

            if current_context.get('execution_started'):
                avoid_work.append("Redundant implementation work")
            if current_context.get('planning_done'):
                avoid_work.append("Re-planning before execution")

        elif target_command == "/research":
            next_steps.append("Conduct comprehensive research with evidence validation")
            if current_context.get('ask_completed'):
                next_steps.append("Build upon existing /ask analysis requirements")
            if current_context.get('research_completed'):
                avoid_work.append("Redundant research on same topics")

        elif target_command == "/gw.code-review":
            next_steps.append("Execute multi-tool specialist code review")
            if current_context.get('execution_started'):
                next_steps.append("Review implemented code for quality and compliance")
            if current_context.get('validation_done'):
                avoid_work.append("Duplicate validation work")

        return next_steps, avoid_work

    def execute_smart_handoff(self, from_command: str, to_command: str,
                            user_request: str) -> dict[str, Any]:
        """Execute smart handoff between commands"""

        # Detect current work
        detected_work = self.evidence_manager.detect_previous_work(from_command)

        # Validate transition
        is_valid, issues = self.validate_command_transition(from_command, to_command, detected_work)
        if not is_valid:
            raise HandoffValidationError(f"Invalid transition: {', '.join(issues)}")

        # Create integration context
        integration_context = self.evidence_manager.create_integration_context(
            from_command, to_command, detected_work
        )

        # Prepare context for target command
        prepared_context = self.prepare_context_for_command(to_command, detected_work)

        # Record handoff in history
        handoff_record = {
            'from_command': from_command,
            'to_command': to_command,
            'timestamp': datetime.now().isoformat(),
            'user_request': user_request,
            'integration_context': integration_context,
            'prepared_context': prepared_context,
            'validation_issues': issues if not is_valid else []
        }

        self.handoff_history.append(handoff_record)
        self._save_handoff_history()

        return {
            'handoff_successful': True,
            'target_command': to_command,
            'prepared_context': prepared_context,
            'integration_context': integration_context,
            'recommendations': self._generate_handoff_recommendations(prepared_context, integration_context)
        }

    def _generate_handoff_recommendations(self, prepared_context: dict[str, Any],
                                        integration_context: IntegrationContext) -> list[str]:
        """Generate recommendations for the handoff"""
        recommendations = []

        if not integration_context.prerequisites_satisfied:
            recommendations.append("Complete prerequisite work before proceeding")

        quality_status = prepared_context['quality_status']
        if not quality_status['ready_for_handoff']:
            recommendations.append(f"Improve quality score from {quality_status['overall_quality_score']:.2f} to {quality_status['recommended_threshold']:.2f}")

        if prepared_context['avoid_redunant_work']:
            recommendations.append(f"Avoid redundant work: {', '.join(prepared_context['avoid_redunant_work'])}")

        if prepared_context['next_steps']:
            recommendations.append(f"Recommended next steps: {', '.join(prepared_context['next_steps'])}")

        return recommendations

    def _check_quality_gates(self, project_context: ProjectContext) -> list[str]:
        """Check which quality gates have been passed"""
        passed_gates = []

        if "input_analysis" in project_context.completed_phases:
            passed_gates.append("input_validation")

        if "requirements_research" in project_context.completed_phases:
            passed_gates.append("research_validation")

        if "strategic_planning" in project_context.completed_phases:
            passed_gates.append("planning_validation")

        if "implementation" in project_context.completed_phases:
            passed_gates.append("implementation_validation")

        if "quality_validation" in project_context.completed_phases:
            passed_gates.append("final_validation")

        return passed_gates

    def _load_command_capabilities(self) -> dict[str, dict[str, Any]]:
        """Load command capability mappings"""
        return {
            "/ask": {
                "can_inherit_from": ["/research", "/learn", "/truth", "/explore", "/nse"],
                "can_handoff_to": ["/cwo12", "/speckit.plan", "/exec", "/research"],
                "can_continue_with": ["/cwo12", "/research", "/learn"]
            },
            "/cwo12": {
                "can_inherit_from": ["any_command"],
                "can_handoff_to": ["any_command"],
                "can_continue_with": ["any_command"]
            },
            "/research": {
                "can_inherit_from": ["/ask", "/learn", "/explore", "/truth"],
                "can_handoff_to": ["/cwo12", "/speckit.plan", "/ask", "/exec"],
                "can_continue_with": ["/ask", "/cwo12", "/speckit.plan"]
            },
            "/exec": {
                "can_inherit_from": ["/cwo12", "/speckit.plan", "/ask", "/task"],
                "can_handoff_to": ["/cwo12", "/gw.code-review", "/test-fix"],
                "can_continue_with": ["/cwo12", "/gw.code-review"]
            },
            "/speckit.plan": {
                "can_inherit_from": ["/ask", "/research", "/arch", "/specify"],
                "can_handoff_to": ["/cwo12", "/exec", "/ask"],
                "can_continue_with": ["/cwo12", "/exec", "/ask"]
            },
            "/gw.code-review": {
                "can_inherit_from": ["/exec", "/cwo12", "/ask", "/test-fix"],
                "can_handoff_to": ["/cwo12", "/exec", "/security-validator"],
                "can_continue_with": ["/cwo12", "/exec", "/security-validator"]
            },
            "/qual-gate": {
                "can_inherit_from": ["any_command"],
                "can_handoff_to": ["any_command"],
                "can_continue_with": ["any_command"]
            }
        }

    def _save_handoff_history(self):
        """Save handoff history to file"""
        history_file = self.evidence_manager.project_root / ".speckit" / "state" / "handoff_history.json"

        with open(history_file, 'w') as f:
            json.dump(self.handoff_history, f, indent=2)

# Global instance for easy access
handoff_manager = SmartHandoffManager()
