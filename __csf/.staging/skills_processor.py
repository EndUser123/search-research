#!/usr/bin/env python3
"""Skills taxonomy processor for categorizing 210 skills by domain."""

import json
import re
from pathlib import Path
from typing import List, Tuple

def read_skill_file(file_path: Path) -> Tuple[str, str, List[str]]:
    """Read a SKILL.md file and extract name, description, and triggers."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None, None, []

        frontmatter = frontmatter_match.group(1)

        # Extract name
        name_match = re.search(r'name:\s*(\S+)', frontmatter)
        name = name_match.group(1) if name_match else file_path.stem

        # Extract description
        desc_match = re.search(r'description:\s*(.*?)(?:\n|$)', frontmatter)
        description = desc_match.group(1).strip() if desc_match else ""

        # Extract triggers
        triggers = []
        triggers_match = re.search(r'triggers:\s*\n((?:\s+-\s+.*?\n)+)', frontmatter, re.DOTALL)
        if triggers_match:
            triggers_text = triggers_match.group(1)
            triggers = [line.strip('- ').strip() for line in triggers_text.split('\n') if line.strip()]

        return name, description, triggers

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None, []

def categorize_skill(name: str, description: str) -> str:
    """Categorize a skill based on its name and description."""
    name_lower = name.lower()
    desc_lower = description.lower()

    # Development skills
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'arch', 'tdd', 'rca', 'debug', 'refactor', 'code', 'test', 'build',
        'implement', 'develop', 'construct', 'create', 'write', 'generate',
        'multi-file', 'complexity', 'craft', 'codecraft'
    ]):
        return 'development'

    # Infrastructure & DevOps
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'git', 'worktree', 'hook', 'daemon', 'pipeline', 'deploy', 'config',
        'infrastructure', 'ops', 'system', 'environment', 'setup'
    ]):
        return 'infrastructure'

    # Cognitive & Strategy
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'cognitive', 'strategy', 'decision', 'analysis', 'review', 'rca',
        'architectural', 'framework', 'pattern', 'principle', 'constitution',
        'mental', 'thinking', 'reasoning', 'logic'
    ]):
        return 'cognitive'

    # Documentation & Knowledge
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'doc', 'knowledge', 'learn', 'discover', 'search', 'research',
        'analyze', 'extract', 'summary', 'report', 'study'
    ]):
        return 'documentation'

    # Workflow & Process
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'workflow', 'process', 'task', 'execution', 'flow', 'orchestrator',
        'coordinator', 'manage', 'organize', 'plan', 'schedule'
    ]):
        return 'workflow'

    # Quality & Safety
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'quality', 'safety', 'security', 'comply', 'hardening', 'guard',
        'validation', 'verify', 'audit', 'check', 'monitor'
    ]):
        return 'quality'

    # Data & Processing
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'data', 'processor', 'extract', 'transform', 'analyze', 'compute',
        'calculate', 'table', 'dataset', 'information'
    ]):
        return 'data'

    # AI/ML & External APIs
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'ai', 'ml', 'model', 'llm', 'api', 'external', 'integration',
        'connector', 'client', 'service'
    ]):
        return 'ai-ml'

    # Communication & Collaboration
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'chat', 'message', 'communicate', 'collaborate', 'team', 'share',
        'notification', 'feedback', 'review'
    ]):
        return 'communication'

    # Configuration & Management
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'config', 'setting', 'manage', 'admin', 'control', 'registry',
        'catalog', 'inventory', 'catalog'
    ]):
        return 'configuration'

    # Utility & Helper
    if any(keyword in name_lower or keyword in desc_lower for keyword in [
        'util', 'helper', 'tool', 'command', 'execute', 'run', 'perform',
        'assist', 'support'
    ]):
        return 'utility'

    # Default category
    return 'other'

def main():
    """Main function to process all skills and create taxonomy."""
    # Define skill directories
    skill_dirs = [
        Path(r"P:\.gemini\skills"),
        Path(r"P:\.claude\skills")
    ]

    # Add personal skills directory if it exists
    personal_skills = Path(r"C:\Users\brsth\.claude\skills")
    if personal_skills.exists():
        skill_dirs.append(personal_skills)

    skills_data = {}
    category_counts = {}

    total_skills = 0

    for skill_dir in skill_dirs:
        if not skill_dir.exists():
            continue

        print(f"Scanning {skill_dir}...")

        # Find all SKILL.md files
        for skill_file in skill_dir.rglob("SKILL.md"):
            name, description, triggers = read_skill_file(skill_file)

            if name and description:
                # Determine category
                category = categorize_skill(name, description)

                # Update category counts
                category_counts[category] = category_counts.get(category, 0) + 1

                # Store skill data
                skills_data[name] = {
                    "description": description,
                    "category": category,
                    "triggers": triggers,
                    "path": str(skill_file),
                    "directory": skill_dir.name
                }

                total_skills += 1

                if total_skills % 50 == 0:
                    print(f"Processed {total_skills} skills...")

    # Create taxonomy output
    taxonomy = {
        "metadata": {
            "total_skills": total_skills,
            "generated_at": "2026-03-09",
            "source_directories": [str(d) for d in skill_dirs]
        },
        "categories": category_counts,
        "skills": skills_data,
        "category_details": {
            "development": "Code development, testing, implementation",
            "infrastructure": "Git, hooks, deployment, system setup",
            "cognitive": "Architecture, strategy, decision-making, frameworks",
            "documentation": "Documentation, knowledge management, search",
            "workflow": "Process management, orchestration, coordination",
            "quality": "Quality assurance, safety, validation, security",
            "data": "Data processing, extraction, analysis",
            "ai-ml": "AI/ML models, external APIs, integrations",
            "communication": "Collaboration, messaging, notifications",
            "configuration": "Settings, management, registry",
            "utility": "Helper tools, utilities, execution",
            "other": "Uncategorized or mixed-purpose skills"
        }
    }

    # Write taxonomy file
    output_file = Path(r"P:\__csf\.staging\skills_taxonomy.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(taxonomy, f, indent=2, ensure_ascii=False)

    print(f"\nComplete! Processed {total_skills} skills.")
    print("Category distribution:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")

    print(f"\nTaxonomy saved to: {output_file}")

if __name__ == "__main__":
    main()