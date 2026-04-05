#!/usr/bin/env python3
"""
Command Integration Utilities
Provides universal integration functionality for all commands
"""

import logging
from datetime import datetime
from typing import Any

from shared_evidence_manager import CommandEvidence, evidence_manager
from smart_handoff_manager import handoff_manager

logger = logging.getLogger(__name__)

class CommandIntegrator:
    """Universal integration utilities for all commands"""

    def __init__(self, command_name: str):
        self.command_name = command_name
        self.evidence_manager = evidence_manager
        self.handoff_manager = handoff_manager

    def initialize_execution(self, user_input: str) -> dict[str, Any]:
        """Initialize command execution with context detection"""

        # Detect existing project work
        detected_work = self.evidence_manager.detect_previous_work(self.command_name)

        # Determine execution mode
        execution_mode = self._determine_execution_mode(detected_work)

        # Prepare execution context
        execution_context = {
            'command_name': self.command_name,
            'user_input': user_input,
            'execution_mode': execution_mode,
            'detected_work': detected_work,
            'start_time': datetime.now(),
            'project_context': detected_work.get('project_context')
        }

        logger.info(f"Initialized {self.command_name} in {execution_mode} mode")

        return execution_context

    def adapt_execution(self, user_input: str, detected_work: dict[str, Any]) -> dict[str, Any]:
        """Adapt command execution based on previous work"""

        adaptation = {
            'inherits_from': [],
            'avoids_redundant_work': [],
            'builds_upon': [],
            'quality_requirements': 0.85,
            'recommended_approach': 'standard'
        }

        # Analyze what work has been done
        if detected_work.get('ask_completed'):
            adaptation['inherits_from'].append('/ask')
            adaptation['builds_upon'].append('truth-validated analysis')
            adaptation['avoids_redundant_work'].append('duplicate input analysis')

        if detected_work.get('research_completed'):
            adaptation['inherits_from'].append('/research')
            adaptation['builds_upon'].append('comprehensive research findings')
            adaptation['avoids_redundant_work'].append('duplicate research')

        if detected_work.get('planning_done'):
            adaptation['inherits_from'].append('/speckit.plan')
            adaptation['builds_upon'].append('strategic planning')
            adaptation['avoids_redundant_work'].append('re-planning')

        if detected_work.get('execution_started'):
            adaptation['inherits_from'].append('/exec')
            adaptation['builds_upon'].append('implementation work')
            adaptation['avoids_redundant_work'].append('re-implementing')

        # Command-specific adaptations
        if self.command_name == "/cwo12":
            adaptation = self._adapt_cwo12(detected_work, adaptation)
        elif self.command_name == "/ask":
            adaptation = self._adapt_ask(detected_work, adaptation)
        elif self.command_name == "/research":
            adaptation = self._adapt_research(detected_work, adaptation)
        elif self.command_name == "/exec":
            adaptation = self._adapt_exec(detected_work, adaptation)
        elif self.command_name == "/speckit.plan":
            adaptation = self._adapt_speckit_plan(detected_work, adaptation)
        elif self.command_name == "/gw.code-review":
            adaptation = self._adapt_gw_code_review(detected_work, adaptation)

        return adaptation

    def create_command_evidence(self, execution_context: dict[str, Any],
                              results_summary: str, quality_metrics: dict[str, float],
                              evidence_paths: list[str]) -> CommandEvidence:
        """Create evidence for current command execution"""

        # Determine integration capabilities
        integration_points = self._get_integration_points(execution_context)
        can_continue_with = self._get_continuation_capabilities(execution_context)
        prerequisites_satisfied = self._check_prerequisites(execution_context)

        evidence = CommandEvidence(
            command_name=self.command_name,
            execution_time=datetime.now(),
            results_summary=results_summary,
            quality_metrics=quality_metrics,
            evidence_paths=evidence_paths,
            handoff_ready=True,
            integration_points=integration_points,
            can_continue_with=can_continue_with,
            prerequisites_satisfied=prerequisites_satisfied
        )

        # Save evidence
        self.evidence_manager.save_command_evidence(evidence)

        # Update project context
        self._update_project_context(execution_context, evidence)

        return evidence

    def recommend_next_actions(self, execution_context: dict[str, Any],
                            evidence: CommandEvidence) -> list[str]:
        """Recommend next actions based on execution results"""

        recommendations = []

        # Quality-based recommendations
        overall_quality = evidence.quality_metrics.get('overall_quality', 0)
        if overall_quality < 0.85:
            recommendations.append(f"Improve quality score from {overall_quality:.2f} to 0.85")
        else:
            recommendations.append("Quality gates passed - ready for next phase")

        # Command-specific recommendations
        if self.command_name == "/ask":
            if evidence.results_summary and "analysis" in evidence.results_summary.lower():
                recommendations.extend([
                    "Continue with /cwo12 for workflow orchestration",
                    "Or use /speckit.plan for strategic planning",
                    "Or use /research for deeper investigation"
                ])

        elif self.command_name == "/research":
            recommendations.extend([
                "Continue with /cwo12 for implementation planning",
                "Or use /speckit.plan for architecture design",
                "Or use /ask for refined requirements analysis"
            ])

        elif self.command_name == "/speckit.plan":
            recommendations.extend([
                "Continue with /cwo12 for task decomposition",
                "Or use /exec for implementation",
                "Or use /ask for validation of planning approach"
            ])

        elif self.command_name == "/exec":
            recommendations.extend([
                "Continue with /gw.code-review for validation",
                "Or use /cwo12 for complete workflow continuation",
                "Or use /test-fix for specific bug resolution"
            ])

        elif self.command_name == "/gw.code-review":
            recommendations.extend([
                "Continue with /cwo12 for workflow completion",
                "Or use /exec for addressing identified issues",
                "Or use /security-validator for security-specific validation"
            ])

        return recommendations

    def facilitate_handoff(self, target_command: str, user_request: str,
                        execution_context: dict[str, Any]) -> dict[str, Any]:
        """Facilitate handoff to another command"""

        try:
            handoff_result = self.handoff_manager.execute_smart_handoff(
                self.command_name, target_command, user_request
            )

            logger.info(f"Successful handoff from {self.command_name} to {target_command}")

            return handoff_result

        except Exception as e:
            logger.error(f"Handoff failed: {str(e)}")

            return {
                'handoff_successful': False,
                'error': str(e),
                'recommendations': [
                    "Continue with current command",
                    "Try manual command invocation",
                    "Check integration compatibility"
                ]
            }

    def _determine_execution_mode(self, detected_work: dict[str, Any]) -> str:
        """Determine execution mode based on detected work"""

        if not detected_work.get('project_context'):
            return "new_project"

        project_context = detected_work['project_context']

        if self.command_name in project_context.active_commands:
            return "continue_existing"
        elif project_context.completed_phases:
            return "build_upon_existing"
        else:
            return "coordinate_with_existing"

    def _adapt_cwo12(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /cwo12 execution based on previous work"""

        completed_steps = []

        if detected_work.get('ask_completed'):
            completed_steps.extend([1, 2])  # Input analysis and GW.ASK analysis
            adaptation['quality_requirements'] = 0.90

        if detected_work.get('planning_done'):
            completed_steps.append(3)  # Strategic planning
            adaptation['quality_requirements'] = 0.90

        if detected_work.get('execution_started'):
            completed_steps.extend([5, 6])  # Task decomposition and execution
            adaptation['quality_requirements'] = 0.95

        if detected_work.get('validation_done'):
            completed_steps.append(7)  # Code review
            adaptation['quality_requirements'] = 0.95

        if completed_steps:
            adaptation['recommended_approach'] = f"continue_from_step_{max(completed_steps)+1}"
            adaptation['avoids_redundant_work'].extend([
                f"Steps 1-{max(completed_steps)} already completed"
            ])

        return adaptation

    def _adapt_ask(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /ask execution based on previous work"""

        if detected_work.get('research_completed'):
            adaptation['builds_upon'].append('existing research findings')
            adaptation['recommended_approach'] = 'analysis_with_research_context'
            adaptation['quality_requirements'] = 0.90

        if detected_work.get('learn_done'):
            adaptation['builds_upon'].append('captured patterns and knowledge')

        return adaptation

    def _adapt_research(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /research execution based on previous work"""

        if detected_work.get('ask_completed'):
            adaptation['builds_upon'].append('validated requirements and analysis')
            adaptation['avoids_redundant_work'].append('requirements analysis')
            adaptation['recommended_approach'] = 'focused_research'

        if detected_work.get('learn_done'):
            adaptation['builds_upon'].append('existing knowledge patterns')

        return adaptation

    def _adapt_exec(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /exec execution based on previous work"""

        if detected_work.get('planning_done'):
            adaptation['builds_upon'].append('strategic planning and architecture')
            adaptation['quality_requirements'] = 0.90
            adaptation['recommended_approach'] = 'implement_from_plan'

        if detected_work.get('ask_completed'):
            adaptation['builds_upon'].append('truth-validated requirements')

        if detected_work.get('execution_started'):
            adaptation['avoids_redundant_work'].append('re-implementing completed work')
            adaptation['recommended_approach'] = 'continue_implementation'

        return adaptation

    def _adapt_speckit_plan(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /speckit.plan execution based on previous work"""

        if detected_work.get('ask_completed'):
            adaptation['builds_upon'].append('validated requirements')
            adaptation['quality_requirements'] = 0.90

        if detected_work.get('research_completed'):
            adaptation['builds_upon'].append('comprehensive research findings')
            adaptation['recommended_approach'] = 'evidence_based_planning'

        return adaptation

    def _adapt_gw_code_review(self, detected_work: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        """Adapt /gw.code-review execution based on previous work"""

        if detected_work.get('execution_started'):
            adaptation['builds_upon'].append('implementation artifacts')
            adaptation['recommended_approach'] = 'review_implementation'

        if detected_work.get('ask_completed'):
            adaptation['builds_upon'].append('requirements for validation')

        return adaptation

    def _get_integration_points(self, execution_context: dict[str, Any]) -> list[str]:
        """Get integration points for current command"""
        integration_points = {
            "/ask": ["step1", "step2", "requirements_analysis", "truth_validation"],
            "/cwo12": ["all_steps", "project_management", "workflow_orchestration"],
            "/research": ["analysis", "evidence_gathering", "knowledge_integration"],
            "/exec": ["step6", "implementation", "enhanced_execution"],
            "/speckit.plan": ["step3", "architecture_planning", "strategic_design"],
            "/gw.code-review": ["step7", "quality_validation", "specialist_coordination"],
            "/qual-gate": ["all_steps", "quality_orchestration", "validation"]
        }

        return integration_points.get(self.command_name, ["general_integration"])

    def _get_continuation_capabilities(self, execution_context: dict[str, Any]) -> list[str]:
        """Get continuation capabilities for current command"""
        continuation_map = {
            "/ask": ["/cwo12", "/speckit.plan", "/exec", "/research"],
            "/cwo12": ["any_command"],
            "/research": ["/cwo12", "/speckit.plan", "/ask", "/exec"],
            "/exec": ["/cwo12", "/gw.code-review", "/test-fix"],
            "/speckit.plan": ["/cwo12", "/exec", "/ask"],
            "/gw.code-review": ["/cwo12", "/exec", "/security-validator"],
            "/qual-gate": ["any_command"]
        }

        return continuation_map.get(self.command_name, ["/cwo12"])

    def _check_prerequisites(self, execution_context: dict[str, Any]) -> bool:
        """Check if prerequisites are satisfied"""

        # Basic prerequisite checks
        if not execution_context.get('user_input'):
            return False

        detected_work = execution_context.get('detected_work', {})

        # Command-specific prerequisites
        if self.command_name == "/exec":
            return bool(detected_work.get('planning_done') or detected_work.get('ask_completed'))
        elif self.command_name == "/gw.code-review":
            return bool(detected_work.get('execution_started'))
        elif self.command_name == "/speckit.plan":
            return bool(detected_work.get('ask_completed') or detected_work.get('research_completed'))

        return True

    def _update_project_context(self, execution_context: dict[str, Any], evidence: CommandEvidence):
        """Update project context with new evidence"""

        project_context = execution_context.get('project_context')
        if not project_context:
            # Create new project context
            project_context = self.evidence_manager.create_project_context(
                execution_context.get('user_input', ''),
                self.command_name
            )
            execution_context['project_context'] = project_context

        # Update active commands
        if self.command_name not in project_context.active_commands:
            project_context.active_commands.append(self.command_name)

        # Update completed phases based on command
        completed_phases = self._map_command_to_phases(self.command_name)
        for phase in completed_phases:
            if phase not in project_context.completed_phases:
                project_context.completed_phases.append(phase)

        # Update quality scores
        overall_quality = evidence.quality_metrics.get('overall_quality', 0)
        if overall_quality > 0:
            project_context.quality_scores[self.command_name] = overall_quality

        # Save updated context
        self.evidence_manager.save_project_context(project_context)

    def _map_command_to_phases(self, command_name: str) -> list[str]:
        """Map command to completed CWO12 phases"""
        phase_mapping = {
            "/ask": ["input_analysis", "requirements_analysis"],
            "/research": ["requirements_research", "evidence_gathering"],
            "/speckit.plan": ["strategic_planning", "architecture_design"],
            "/exec": ["task_decomposition", "implementation"],
            "/gw.code-review": ["code_validation", "quality_assurance"],
            "/qual-gate": ["quality_validation"]
        }

        return phase_mapping.get(command_name, [])

# Convenience function for commands to use
def get_command_integrator(command_name: str) -> CommandIntegrator:
    """Get command integrator for specified command"""
    return CommandIntegrator(command_name)
