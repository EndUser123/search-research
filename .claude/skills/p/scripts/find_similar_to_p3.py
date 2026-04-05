#!/usr/bin/env python3
"""
Find skills similar to /p --phase=3 across all skills.

/p --phase=3 functionality:
- Prove trustworthiness through gated validation pipeline
- Sequential validation pipeline with halt-on-failure gates (15+ stages)
- Coverage thresholds (default 70%, min 50%)
- CVE scanning, security checks
- Quality checks (pylint, radon, mypy, ruff)
- E2E tests, chaos testing, certification
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillInfo:
    """Information about a skill."""
    name: str
    path: Path
    description: str = ""
    category: str = ""
    triggers: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    suggest: list[str] = field(default_factory=list)
    keywords: set[str] = field(default_factory=set)
    content_lines: list[str] = field(default_factory=list)
    similarity_score: float = 0.0
    matched_keywords: set[str] = field(default_factory=set)


# /p --phase=3 keywords for similarity matching
P3_KEYWORDS = {
    # Core validation concepts
    "validate", "validation", "verify", "verification", "prove", "trustworthy",
    # Pipeline/gate concepts
    "pipeline", "gate", "stage", "halt", "sequential", "blocking",
    # Coverage
    "coverage", "branch", "threshold", "percentage",
    # Security
    "security", "cve", "scan", "bandit", "pip-audit", "vulnerability",
    # Quality
    "quality", "pylint", "radon", "mypy", "ruff", "lint", "formatting",
    # Testing
    "e2e", "end-to-end", "chaos", "integration", "regression", "certification",
    # Syntax/static analysis
    "syntax", "ast", "parse", "static", "analysis",
    # Dead code/duplication
    "dead", "code", "duplication", "vulture",
}

# Skills that are definitely similar (known delegates of /p --phase=3)
KNOWN_P3_DELEGATES = {
    "/v",  # Validation pipeline
    "/p --phase=N,  # QA/certification phase
}

# Skills that are part of p* pipeline (related but different)
P_PIPELINE_SKILLS = {
    "/p --phase=N, "/p --phase=N, "/p --phase=N, "/p --phase=N, "/p"
}

# Validation/verification related skills
# Note: /code-python-2025 and /code-typescript-2025 functionality migrated to commands.p.lib
VALIDATION_SKILLS = {
    "/p --phase=N, "/p --phase=N, "/validate-safety-patterns", "/validate_spec",
    "/comply"
}


def parse_frontmatter_and_content(skill_file: Path) -> dict:
    """Parse YAML frontmatter and content from SKILL.md."""
    content = skill_file.read_text()
    lines = content.split('\n')

    in_frontmatter = False
    frontmatter_lines = []
    content_lines = []

    for line in lines:
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                in_frontmatter = False
                continue
        elif in_frontmatter:
            frontmatter_lines.append(line)
        else:
            content_lines.append(line)

    # Simple YAML parsing for our needs
    data = {
        'description': '',
        'category': '',
        'triggers': [],
        'aliases': [],
        'depends_on_skills': [],
        'suggest': [],
    }

    current_list = None
    for line in frontmatter_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Handle lists
        list_match = re.match(r'^(\w+(?:_\w+)*):\s*\[(.*)\]$', line)
        if list_match:
            key, values = list_match.groups()
            if values.strip():
                data[key] = [v.strip().strip('"\'') for v in values.split(',')]
            continue

        # Handle list start
        if line.endswith(':'):
            current_list = line[:-1]
            if current_list not in data:
                data[current_list] = []
            continue

        # Handle list items with dash
        if current_list and line.startswith('- '):
            value = line[2:].strip().strip('"\'')
            data[current_list].append(value)
            continue

        # Handle key-value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            data[key] = value

    return {
        'frontmatter': data,
        'content': '\n'.join(content_lines),
        'content_lines': content_lines
    }


def extract_keywords_from_content(text: str) -> set[str]:
    """Extract relevant keywords from skill content."""
    text_lower = text.lower()
    keywords = set()

    # Word boundaries for exact matching
    for keyword in P3_KEYWORDS:
        # Check with word boundary
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            keywords.add(keyword)

    # Additional patterns
    if re.search(r'(validation.*pipeline|gate.*pipeline|sequential.*stage)', text_lower):
        keywords.add("validation_pipeline")
    if re.search(r'(halt.*failure|blocking.*gate)', text_lower):
        keywords.add("halt_on_failure")
    if re.search(r'(e2e|end.to.end|playwright)', text_lower):
        keywords.add("e2e_testing")
    if re.search(r'(chaos|hypothesis|schemathesis|locust|load.*test)', text_lower):
        keywords.add("chaos_testing")
    if re.search(r'(cve.*scan|security.*scan|vulnerability.*scan)', text_lower):
        keywords.add("security_scan")

    return keywords


def calculate_similarity(skill: SkillInfo) -> float:
    """Calculate similarity score to /p --phase=3."""
    score = 0.0
    reasons = set()

    # Check triggers/aliases (exact match is high similarity)
    all_names = [skill.name.lower()] + [a.lower() for a in skill.aliases]
    if any(name in KNOWN_P3_DELEGATES for name in all_names):
        score += 1.0
        reasons.add("known_p3_delegate")

    # Check other validation-related skills
    if any(name in VALIDATION_SKILLS for name in all_names):
        score += 0.8
        reasons.add("validation_skill")

    # Check if part of p* pipeline
    if skill.name.lower() in P_PIPELINE_SKILLS:
        score += 0.5
        reasons.add("p_pipeline")

    # Keyword matching in description
    desc_lower = skill.description.lower()
    for keyword in P3_KEYWORDS:
        if keyword in desc_lower:
            score += 0.1
            skill.matched_keywords.add(keyword)
            reasons.add(f"desc_{keyword}")

    # Keyword matching in content
    for keyword in skill.keywords:
        if keyword in P3_KEYWORDS:
            score += 0.05
            reasons.add(f"content_{keyword}")

    # Check dependencies on known p3 skills
    for dep in skill.depends_on:
        if dep in KNOWN_P3_DELEGATES or dep in P_PIPELINE_SKILLS:
            score += 0.2
            reasons.add(f"depends_on_{dep}")

    # Check suggestions (if suggests p3 skills, likely related)
    for sugg in skill.suggest:
        if sugg in KNOWN_P3_DELEGATES or sugg in P_PIPELINE_SKILLS:
            score += 0.15
            reasons.add(f"suggests_{sugg}")

    # Category match
    if skill.category in ("validation", "quality", "testing", "security"):
        score += 0.1
        reasons.add(f"category_{skill.category}")

    return min(score, 1.0)  # Cap at 1.0


def scan_skills(skills_dir: Path) -> list[SkillInfo]:
    """Scan all skills and return parsed information."""
    skills = []

    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            continue

        try:
            parsed = parse_frontmatter_and_content(skill_file)
            fm = parsed['frontmatter']

            skill = SkillInfo(
                name=fm.get('name', skill_path.name),
                path=skill_path,
                description=fm.get('description', ''),
                category=fm.get('category', ''),
                triggers=fm.get('triggers', []),
                aliases=fm.get('aliases', []),
                depends_on=fm.get('depends_on_skills', []),
                suggest=fm.get('suggest', []),
                content_lines=parsed['content_lines']
            )

            # Extract keywords from content
            content = parsed['content']
            skill.keywords = extract_keywords_from_content(content)

            skills.append(skill)
        except Exception as e:
            print(f"Warning: Failed to parse {skill_file}: {e}")

    return skills


def main():
    """Main entry point."""
    skills_dir = Path("P:/.claude/skills")

    if not skills_dir.exists():
        print(f"Error: Skills directory not found: {skills_dir}")
        return

    print("Scanning skills for similarity to /p --phase=3 (Validate phase)...")
    print("=" * 70)

    skills = scan_skills(skills_dir)
    print(f"Found {len(skills)} skills with SKILL.md files\n")

    # Calculate similarity scores
    for skill in skills:
        skill.similarity_score = calculate_similarity(skill)

    # Sort by similarity score
    skills_by_similarity = sorted(
        skills,
        key=lambda s: s.similarity_score,
        reverse=True
    )

    # Group by similarity tiers
    tiers = {
        "HIGH (0.5+)": [],
        "MEDIUM (0.2-0.49)": [],
        "LOW (0.05-0.19)": [],
        "MINIMAL (<0.05)": [],
    }

    for skill in skills_by_similarity:
        if skill.similarity_score >= 0.5:
            tiers["HIGH (0.5+)"].append(skill)
        elif skill.similarity_score >= 0.2:
            tiers["MEDIUM (0.2-0.49)"].append(skill)
        elif skill.similarity_score >= 0.05:
            tiers["LOW (0.05-0.19)"].append(skill)
        else:
            tiers["MINIMAL (<0.05)"].append(skill)

    # Output results
    for tier_name, tier_skills in tiers.items():
        if not tier_skills:
            continue

        print(f"\n{tier_name}")
        print("-" * 70)

        for skill in tier_skills[:10]:  # Limit to top 10 per tier
            print(f"\n  /{skill.name} (score: {skill.similarity_score:.2f})")
            print(f"    Description: {skill.description[:80]}...")
            if skill.matched_keywords:
                print(f"    Keywords: {', '.join(sorted(skill.matched_keywords))}")
            if skill.depends_on:
                print(f"    Depends on: {', '.join(skill.depends_on)}")

    # Export JSON for further analysis
    output = []
    for skill in skills_by_similarity:
        output.append({
            "name": f"/{skill.name}",
            "score": round(skill.similarity_score, 3),
            "description": skill.description,
            "category": skill.category,
            "keywords": sorted(skill.matched_keywords),
            "depends_on": skill.depends_on,
            "suggest": skill.suggest,
        })

    output_file = skills_dir / "p" / "p3_similarity_report.json"
    output_file.write_text(json.dumps(output, indent=2))
    print(f"\n\nFull report exported to: {output_file}")


if __name__ == "__main__":
    main()
