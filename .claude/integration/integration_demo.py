#!/usr/bin/env python3
"""
Universal Command Integration Demo
Demonstrates bidirectional context sharing and smart handoffs
"""

import sys
from pathlib import Path

# Add integration directory to path
sys.path.append(str(Path(__file__).parent))

from command_integration_utils import get_command_integrator
from shared_evidence_manager import evidence_manager
from smart_handoff_manager import handoff_manager


def demo_scenario_1():
    """Demo Scenario 1: User starts with /research, then moves to /cwo12"""
    print("🚀 DEMO SCENARIO 1: Research → CWO12")
    print("=" * 50)

    # Step 1: User starts with /research
    print("\n📚 Step 1: User runs /research")
    research_integrator = get_command_integrator("/research")

    # Initialize execution
    user_input = "research user authentication best practices"
    execution_context = research_integrator.initialize_execution(user_input)

    print(f"   Execution mode: {execution_context['execution_mode']}")
    print(f"   Detected work: {len(execution_context['detected_work'])} items")

    # Adapt execution based on previous work (none in this case)
    adaptation = research_integrator.adapt_execution(user_input, execution_context['detected_work'])
    print(f"   Adaptation: {adaptation['recommended_approach']}")

    # Simulate research execution
    print("   🔍 Executing comprehensive research...")

    # Create evidence
    research_evidence = research_integrator.create_command_evidence(
        execution_context=execution_context,
        results_summary="Comprehensive research on authentication best practices completed",
        quality_metrics={"overall_quality": 0.88, "evidence_depth": 0.90, "relevance": 0.85},
        evidence_paths=["research_findings.md", "security_patterns.md"]
    )

    print(f"   ✅ Research completed with quality score: {research_evidence.quality_metrics['overall_quality']}")

    # Get recommendations
    recommendations = research_integrator.recommend_next_actions(execution_context, research_evidence)
    print(f"   📋 Recommendations: {', '.join(recommendations[:2])}")

    # Step 2: User switches to /cwo12
    print("\n🔄 Step 2: User runs /cwo12")
    cwo12_integrator = get_command_integrator("/cwo12")

    # Initialize CWO12 execution
    user_input_2 = "implement user authentication system"
    execution_context_2 = cwo12_integrator.initialize_execution(user_input_2)

    print(f"   Execution mode: {execution_context_2['execution_mode']}")
    print(f"   Detected work from previous commands: {len(execution_context_2['detected_work'])} items")

    # Adapt CWO12 execution based on previous research
    adaptation_2 = cwo12_integrator.adapt_execution(user_input_2, execution_context_2['detected_work'])
    print(f"   Adaptation: {adaptation_2['recommended_approach']}")
    print(f"   Inherits from: {', '.join(adaptation_2['inherits_from'])}")
    print(f"   Avoids redundant work: {', '.join(adaptation_2['avoids_redundant_work'])}")

    # Simulate CWO12 execution
    print("   🎯 Executing CWO12 workflow with inherited research...")

    # Create evidence
    cwo12_evidence = cwo12_integrator.create_command_evidence(
        execution_context=execution_context_2,
        results_summary="CWO12 Step 3 execution with inherited research context",
        quality_metrics={"overall_quality": 0.92, "workflow_integration": 0.95, "evidence_utilization": 0.90},
        evidence_paths=["cwo12_project.md", "implementation_plan.md"]
    )

    print(f"   ✅ CWO12 execution completed with quality score: {cwo12_evidence.quality_metrics['overall_quality']}")

def demo_scenario_2():
    """Demo Scenario 2: User starts with /cwo12, then needs /exec"""
    print("\n\n🚀 DEMO SCENARIO 2: CWO12 → Exec")
    print("=" * 50)

    # Step 1: User starts with /cwo12
    print("\n📋 Step 1: User runs /cwo12")
    cwo12_integrator = get_command_integrator("/cwo12")

    user_input = "build REST API for user management"
    execution_context = cwo12_integrator.initialize_execution(user_input)

    print(f"   Execution mode: {execution_context['execution_mode']}")

    # Simulate CWO12 planning steps
    adaptation = cwo12_integrator.adapt_execution(user_input, execution_context['detected_work'])
    print(f"   Adaptation: {adaptation['recommended_approach']}")

    print("   🎯 Executing CWO12 Steps 1-3 (planning)...")

    # Create evidence for planning completion
    cwo12_evidence = cwo12_integrator.create_command_evidence(
        execution_context=execution_context,
        results_summary="CWO12 Steps 1-3 completed: Input analysis, research, and strategic planning",
        quality_metrics={"overall_quality": 0.89, "planning_quality": 0.90, "requirements_validation": 0.88},
        evidence_paths=["api_requirements.md", "strategic_plan.md", "task_breakdown.md"]
    )

    print("   ✅ Planning completed, ready for execution")

    # Step 2: User switches to /exec for implementation
    print("\n⚡ Step 2: User runs /exec")
    exec_integrator = get_command_integrator("/exec")

    user_input_2 = "implement the REST API according to plan"
    execution_context_2 = exec_integrator.initialize_execution(user_input_2)

    print(f"   Execution mode: {execution_context_2['execution_mode']}")
    print(f"   Detected work from CWO12: {'yes' if execution_context_2['detected_work'].get('cwo12_active') else 'no'}")

    # Adapt exec execution based on CWO12 planning
    adaptation_2 = exec_integrator.adapt_execution(user_input_2, execution_context_2['detected_work'])
    print(f"   Adaptation: {adaptation_2['recommended_approach']}")
    print(f"   Inherits from: {', '.join(adaptation_2['inherits_from'])}")
    print(f"   Builds upon: {', '.join(adaptation_2['builds_upon'])}")

    # Simulate exec execution
    print("   🔧 Executing enhanced implementation (60% cognitive improvement)...")

    # Create evidence
    exec_evidence = exec_integrator.create_command_evidence(
        execution_context=execution_context_2,
        results_summary="REST API implementation completed with enhanced execution",
        quality_metrics={"overall_quality": 0.91, "code_quality": 0.90, "performance": 0.92},
        evidence_paths=["api_implementation.py", "tests.py", "documentation.md"]
    )

    print(f"   ✅ Implementation completed with quality score: {exec_evidence.quality_metrics['overall_quality']}")

def demo_handoff():
    """Demo smart handoff between commands"""
    print("\n\n🔄 DEMO: Smart Handoff")
    print("=" * 50)

    # Simulate handoff from /ask to /cwo12
    print("\n📡 Handoff: /ask → /cwo12")

    try:
        handoff_result = handoff_manager.execute_smart_handoff(
            from_command="/ask",
            to_command="/cwo12",
            user_request="continue with workflow implementation"
        )

        if handoff_result['handoff_successful']:
            print("   ✅ Handoff successful!")
            prepared_context = handoff_result['prepared_context']

            print(f"   Target command: {handoff_result['target_command']}")
            print(f"   Quality status: {prepared_context['quality_status']['overall_quality_score']:.2f}")
            print(f"   Next steps: {', '.join(prepared_context['next_steps'][:2])}")
            print(f"   Avoid redundant work: {len(prepared_context['avoid_redunant_work'])} items")

            recommendations = handoff_result['recommendations']
            if recommendations:
                print(f"   Recommendations: {recommendations[0]}")
        else:
            print(f"   ❌ Handoff failed: {handoff_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ⚠️  Handoff demo error: {str(e)}")

def demo_context_preservation():
    """Demo context preservation across commands"""
    print("\n\n💾 DEMO: Context Preservation")
    print("=" * 50)

    # Create project context
    print("\n📁 Creating shared project context...")

    user_input = "microservices authentication system"
    project_context = evidence_manager.create_project_context(user_input, "/ask")

    print(f"   Project ID: {project_context.project_id}")
    print(f"   Current phase: {project_context.current_phase}")
    print(f"   Active commands: {project_context.active_commands}")

    # Simulate work from multiple commands
    print("\n🔄 Simulating work from multiple commands...")

    # Add /ask work
    project_context.completed_phases.append("input_analysis")
    project_context.quality_scores["/ask"] = 0.87
    project_context.active_commands.append("/ask")

    # Add /research work
    project_context.completed_phases.append("requirements_research")
    project_context.quality_scores["/research"] = 0.91
    project_context.active_commands.append("/research")

    # Save context
    evidence_manager.save_project_context(project_context)

    print(f"   Updated completed phases: {', '.join(project_context.completed_phases)}")
    print(f"   Updated quality scores: {project_context.quality_scores}")

    # Test context detection
    print("\n🔍 Testing context detection...")
    detected_work = evidence_manager.detect_previous_work("/cwo12")

    print(f"   Detected project context: {detected_work.get('project_context') is not None}")
    print(f"   Detected /ask work: {detected_work.get('ask_completed') is not None}")
    print(f"   Detected /research work: {detected_work.get('research_completed') is not None}")
    print(f"   Total detected work items: {len([k for k, v in detected_work.items() if v and k != 'project_context'])}")

def main():
    """Run all demos"""
    print("🎯 UNIVERSAL COMMAND INTEGRATION DEMO")
    print("=" * 60)
    print("Demonstrating command-agnostic workflow with bidirectional context sharing")
    print("Users can start with ANY command and seamlessly continue with others")

    # Run all demo scenarios
    demo_scenario_1()
    demo_scenario_2()
    demo_handoff()
    demo_context_preservation()

    print("\n\n✅ DEMO COMPLETE")
    print("=" * 60)
    print("Key Benefits Demonstrated:")
    print("• ✅ Command-agnostic entry points")
    print("• ✅ Bidirectional context detection")
    print("• ✅ Smart redundant work prevention")
    print("• ✅ Seamless handoffs between commands")
    print("• ✅ Quality-aware execution adaptation")
    print("• ✅ Evidence-based decision making")
    print("\nUsers can now start with any command and the system will:")
    print("1. Detect previous work automatically")
    print("2. Adapt execution to build upon existing context")
    print("3. Prevent redundant work intelligently")
    print("4. Provide smooth transitions between commands")
    print("5. Maintain quality consistency across the workflow")

if __name__ == "__main__":
    main()
