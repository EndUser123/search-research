#!/usr/bin/env python3
"""
Find skills similar to /p --phase=4 across all skills.

/p --phase=4 functionality:
- Make code presentable and deployable
- Generate portfolio artifacts (README, LICENSE, badges, CI/CD, CHANGELOG, demos)
- Clean git history for public consumption
- Verify deploy readiness
- Final secret scan before publishing
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Set, Dict


@dataclass
class SkillInfo:
    """Information about a skill."""
    name: str
    path: Path
    description: str = ""
    category: str = ""
    triggers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    suggest: List[str] = field(default_factory=list)
    keywords: Set[str] = field(default_factory=set)
    content_lines: List[str] = field(default_factory=list)
    similarity_score: float = 0.0
    matched_keywords: Set[str] = field(default_factory=set)


# /p --phase=4 keywords for similarity matching
P4_KEYWORDS = {
    # Core publish/deploy concepts
    "publish", "deploy", "deployment", "release", "ship", "shipping",
    # Portfolio/artifacts
    "portfolio", "artifact", "artifacts", "presentable", "readme", "license",
    # Documentation
    "documentation", "docs", "demo", "example", "changelog", "badge", "badges",
    # Git operations
    "git", "history", "cleanup", "squash", "rebase", "commit", "push",
    # CI/CD
    "ci", "cd", "pipeline", "github", "actions", "workflow",
    # Security/secrets
    "secret", "scan", "credential", "api key", "token", "env", "gitignore",
    # Deploy readiness
    "readiness", "ready", "verify", "verification", "health",
    # Public/publishing
    "public", "publishing", "open source", "github", "repository", "repo",
}

# Skills that are definitely similar (known delegates of /p --phase=4)
KNOWN_P4_DELEGATES = {
    "/portfolio",  # Portfolio artifact generation
    "/ship",  # Deploy readiness and runtime snapshot
}

# Skills that are part of p* pipeline (related but different)
P_PIPELINE_SKILLS = {
    "/p --phase=N, "/p --phase=N, "/p --phase=N, "/p --phase=N, "/p"
}

# Publish/ship related skills
PUBLISH_SKILLS = {
    "/github-public-posting", "/sharing-skills", "/push", "/commit"
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


def extract_keywords_from_content(text: str) -> Set[str]:
    """Extract relevant keywords from skill content."""
    text_lower = text.lower()
    keywords = set()

    # Word boundaries for exact matching
    for keyword in P4_KEYWORDS:
        # Check with word boundary
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            keywords.add(keyword)

    # Additional patterns
    if re.search(r'(portfolio.*artifact|generate.*readme|create.*license)', text_lower):
        keywords.add("artifact_generation")
    if re.search(r'(git.*history|squash.*commit|cleanup.*git)', text_lower):
        keywords.add("git_cleanup")
    if re.search(r'(deploy.*ready|ready.*ship|pre.*deploy)', text_lower):
        keywords.add("deploy_readiness")
    if re.search(r'(secret.*scan|credential.*check|api.*key)', text_lower):
        keywords.add("secret_scan")
    if re.search(r'(ci.*cd|github.*action|workflow.*yml)', text_lower):
        keywords.add("cicd")

    return keywords


def calculate_similarity(skill: SkillInfo) -> float:
    """Calculate similarity score to /p --phase=4."""
    score = 0.0
    reasons = set()

    # Check triggers/aliases (exact match is high similarity)
    all_names = [skill.name.lower()] + [a.lower() for a in skill.aliases]
    if any(name in KNOWN_P4_DELEGATES for name in all_names):
        score += 1.0
        reasons.add("known_p4_delegate")

    # Check other publish-related skills
    if any(name in PUBLISH_SKILLS for name in all_names):
        score += 0.8
        reasons.add("publish_skill")

    # Check if part of p* pipeline
    if skill.name.lower() in P_PIPELINE_SKILLS:
        score += 0.5
        reasons.add("p_pipeline")

    # Keyword matching in description
    desc_lower = skill.description.lower()
    for keyword in P4_KEYWORDS:
        if keyword in desc_lower:
            score += 0.1
            skill.matched_keywords.add(keyword)
            reasons.add(f"desc_{keyword}")

    # Keyword matching in content
    for keyword in skill.keywords:
        if keyword in P4_KEYWORDS:
            score += 0.05
            reasons.add(f"content_{keyword}")

    # Check dependencies on known p4 skills
    for dep in skill.depends_on:
        if dep in KNOWN_P4_DELEGATES or dep in P_PIPELINE_SKILLS:
            score += 0.2
            reasons.add(f"depends_on_{dep}")

    # Check suggestions (if suggests p4 skills, likely related)
    for sugg in skill.suggest:
        if sugg in KNOWN_P4_DELEGATES or sugg in P_PIPELINE_SKILLS:
            score += 0.15
            reasons.add(f"suggests_{sugg}")

    # Category match
    if skill.category in ("publish", "deployment", "documentation", "git"):
        score += 0.1
        reasons.add(f"category_{skill.category}")

    return min(score, 1.0)  # Cap at 1.0


def scan_skills(skills_dir: Path) -> List[SkillInfo]:
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

    print("Scanning skills for similarity to /p --phase=4 (Publish phase)...")
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

    output_file = skills_dir / "p" / "p4_similarity_report.json"
    output_file.write_text(json.dumps(output, indent=2))
    print(f"\n\nFull report exported to: {output_file}")


if __name__ == "__main__":
    main()
