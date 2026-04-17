from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / ".claude" / "docs"
HTML_PATH = DOCS_DIR / "sdlc_tech_tree.html"
COMMANDS_DIR = ROOT / ".claude" / "commands"
SKILLS_DIR = ROOT / ".claude" / "skills"
AGENTS_DIR = ROOT / ".claude" / "agents"

BRANCH_IDS = ["strategy", "execution", "quality", "evolution", "control"]

BRANCH_META = {
    "strategy": {
        "label": "Strategy Branch",
        "icon": "compass",
        "color": "indigo",
        "desc": "The Strategy Pillar. Insight-driven planning and architectural design. Orchestrates Discovery to map the territory before the First Strike.",
    },
    "execution": {
        "label": "Execution Branch",
        "icon": "hammer",
        "color": "blue",
        "desc": "The Action Pillar. Active implementation, coding, and persistent version control. Turning specifications into reality.",
    },
    "quality": {
        "label": "Quality Branch",
        "icon": "shield-check",
        "color": "emerald",
        "desc": "The Certification Pillar. Multi-layered verification, security auditing, and behavioral enforcement Gates.",
    },
    "evolution": {
        "label": "Evolution Branch",
        "icon": "refresh-ccw",
        "color": "amber",
        "desc": "The Modernization Pillar. Addressing technical debt, system-wide refactoring, and documentation longevity.",
    },
    "control": {
        "label": "Control Branch",
        "icon": "cpu",
        "color": "rose",
        "desc": "The Platform Pillar. Multi-agent orchestration, session continuity, and foundational system health.",
    },
}

CATEGORY_TO_BRANCH = {
    "strategy": "strategy",
    "planning": "strategy",
    "architecture": "strategy",
    "specification": "strategy",
    "discovery": "strategy",
    "research": "strategy",
    "research-unified": "strategy",
    "knowledge": "strategy",
    "self-learning": "strategy",
    "framework": "strategy",
    "advisory": "strategy",
    "development": "execution",
    "execution": "execution",
    "generation": "execution",
    "initialization": "execution",
    "deployment": "execution",
    "workflow": "control",
    "orchestration": "control",
    "management": "control",
    "system": "control",
    "command": "control",
    "utilities": "control",
    "utility": "control",
    "taskmaster": "control",
    "framework-management": "control",
    "meta": "control",
    "router": "control",
    "llm": "control",
    "ai-llm": "control",
    "ai/llm": "control",
    "observability": "control",
    "custom": "control",
    "analysis": "quality",
    "investigation": "quality",
    "quality": "quality",
    "validation": "quality",
    "testing": "quality",
    "test": "quality",
    "qa": "quality",
    "review": "quality",
    "code-review": "quality",
    "governance": "quality",
    "standards": "quality",
    "security": "quality",
    "debug": "quality",
    "maintenance": "evolution",
    "documentation": "evolution",
    "refactoring": "evolution",
    "evolution": "evolution",
}

COMMAND_OVERRIDES = {
    "/ddd": "strategy",
    "/sp": "execution",
}

SKILL_OVERRIDES = {
    "csf-nip-integration": "execution",
    "data-safety-vcs": "execution",
    "memory-integration": "control",
    "read-before-write": "control",
    "sharing-skills": "evolution",
}

COMMAND_KEYWORDS = [
    (r"design|specify|arch|plan|prd|triage|brainstorm|constraints|search|research|chs|cks|recent|crawl|discover|think|reflect|ask|problem|cognitive|memory|prompt|query|learn|analytics|investigate|obs|val|standards|wo-advisory|opts|ocpa|oops|prrp|ralph|sar_", "strategy"),
    (r"build|tdd|exec|artifact|git|commit|push|checkpoint|scratchpad|sap|diffbro|write-file|code_python|quadlet|init|restore|cb|main|code_standards|fix", "execution"),
    (r"qa|verify|analy|complexity|test-bisect|bug-hunt|deps|audit|validate|reports|perf|comply|empirical|constitutional|test_bleed", "quality"),
    (r"evolve|cleanup|aid|doc|skills-migrate|update_|refactor", "evolution"),
    (r"cwo|tm|workflow|catchup|retro|timeline|context|hooks|cgate|dgate|cco|bgkill|pwsh|stats|quota|telemetry|llm|check_env|terminal|session|health|lightweight|clear-notifications|create_command|data-processor", "control"),
]

SKILL_KEYWORDS = [
    (r"design|architecture|plan|specify|research|cks|chs|cognitive|progressive|notebooklm|analytics|recent|library-first|opts", "strategy"),
    (r"build|tdd|exec|code-|web-|git|worktrees|sap|scratchpad|dev", "execution"),
    (r"qa|analysis|audit|logs|profile|constitutional|regression|truth|rca|testing|empirical|debug", "quality"),
    (r"evolve|docs|refactor|update_state|aid|tdd-cycle|cleanup|writing", "evolution"),
    (r"subagent|session|health|orchestration|infrastructure|response-atomicity|execution-clarity|value-maximization|multi-instance|hooks|catchup", "control"),
]

AGENT_OVERRIDES = {
    "@csf-nip-constitution-specialist": "quality",
    "@csf-nip-development": "execution",
    "@csf-nip-knowledge": "strategy",
    "@csf-nip-planning-command": "strategy",
    "@csf-nip-quality": "quality",
    "@csf-sr-architecture-solid-principles": "strategy",
    "@csf-sr-explainable-reasoning": "strategy",
    "@csf-sr-framework-react-hooks": "execution",
    "@csf-sr-multimodal-analysis": "quality",
    "@csf-sr-optimization-strategy": "strategy",
    "@csf-sr-temporal-analysis": "quality",
    "@quant-analyst": "strategy",
}

AGENT_KEYWORDS = [
    (r"architect|strategy|planner|researcher|product-manager|prompt-architect|rag-architect|vector-db-expert|graphql-architect", "strategy"),
    (r"tdd-|python|react|api-builder|ui-ux|development", "execution"),
    (r"qa|critic|rca|risk|security|analysis|verification|quality", "quality"),
    (r"every-style-editor|mlops|ml-engineer|chaos|adaptive-learning", "evolution"),
    (r"orchestration|infrastructure|context-manager|n8n|monitoring|integration|predictive", "control"),
]


def read_frontmatter(path: pathlib.Path) -> Dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def normalize_name(value: str) -> str:
    return value.strip().lstrip("/")


def map_category(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    key = str(category).strip().lower()
    return CATEGORY_TO_BRANCH.get(key)


def map_keywords(name: str, rules: Iterable[Tuple[str, str]]) -> Optional[str]:
    for pattern, branch in rules:
        if re.search(pattern, name, re.IGNORECASE):
            return branch
    return None


def find_matching_brace(text: str, brace_start: int) -> int:
    depth = 0
    in_string: Optional[str] = None
    escape = False
    for i in range(brace_start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
            continue
        if ch in ('"', "'"):
            in_string = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("No matching brace found")


def extract_branch_block(html_text: str, branch_id: str) -> Optional[str]:
    key = f"{branch_id}:"
    key_idx = html_text.find(key)
    if key_idx == -1:
        return None
    brace_start = html_text.find("{", key_idx)
    if brace_start == -1:
        return None
    brace_end = find_matching_brace(html_text, brace_start)
    return html_text[brace_start : brace_end + 1]


def extract_array(block: str, key: str) -> List[str]:
    if not block:
        return []
    match = re.search(rf"{re.escape(key)}\s*:\s*\[(.*?)\]", block, re.S)
    if not match:
        return []
    inner = match.group(1)
    return re.findall(r'"([^"]+)"', inner)


def parse_existing_mappings(html_text: str) -> Dict[str, Dict[str, str]]:
    existing = {"commands": {}, "skills": {}, "agents": {}}
    for branch_id in BRANCH_IDS:
        block = extract_branch_block(html_text, branch_id)
        commands = extract_array(block, "commands")
        skills = extract_array(block, "skills")
        bullets = extract_array(block, "bullets")
        for item in commands:
            existing["commands"][item] = branch_id
        for item in skills:
            existing["skills"][item] = branch_id
        for item in bullets:
            if item.startswith("@"):
                existing["agents"][item] = branch_id
    return existing


def build_items() -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, List[str]], List[str]]:
    html_text = HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    existing = parse_existing_mappings(html_text)

    branches: Dict[str, Dict[str, List[str]]] = {
        b: {"commands": [], "skills": [], "agents": [], "bullets": []}
        for b in BRANCH_IDS
    }
    unmapped = {"commands": [], "skills": [], "agents": []}
    warnings = []

    for path in COMMANDS_DIR.glob("*.md"):
        front = read_frontmatter(path)
        raw_name = front.get("id") or front.get("name") or path.stem
        if front.get("id") and front.get("name") and " " in str(front.get("name")):
            warnings.append(f"command name has spaces with id present: {path.name} -> {front.get("name")}")
        name = normalize_name(str(raw_name))
        item = f"/{name}"
        branch = COMMAND_OVERRIDES.get(item)
        if not branch:
            category = front.get("category") or front.get("domain")
            branch = map_category(category)
        if not branch:
            branch = existing["commands"].get(item)
        if not branch:
            branch = map_keywords(name, COMMAND_KEYWORDS)
        if not branch:
            unmapped["commands"].append(item)
            continue
        branches[branch]["commands"].append(item)

    for path in SKILLS_DIR.rglob("SKILL.md"):
        front = read_frontmatter(path)
        raw_name = front.get("id") or front.get("name") or path.parent.name
        if front.get("id") and front.get("name") and " " in str(front.get("name")):
            warnings.append(f"skill name has spaces with id present: {path} -> {front.get("name")}")
        name = normalize_name(str(raw_name))
        branch = SKILL_OVERRIDES.get(name)
        if not branch:
            category = front.get("category") or front.get("domain")
            branch = map_category(category)
        if not branch:
            branch = existing["skills"].get(name)
        if not branch:
            branch = map_keywords(name, SKILL_KEYWORDS)
        if not branch:
            unmapped["skills"].append(name)
            continue
        branches[branch]["skills"].append(name)

    for path in AGENTS_DIR.glob("*.md"):
        if path.name == "_README.md":
            continue
        name = path.stem
        item = f"@{name}"
        branch = AGENT_OVERRIDES.get(item)
        if not branch:
            branch = existing["agents"].get(item)
        if not branch:
            branch = map_keywords(name, AGENT_KEYWORDS)
        if not branch:
            unmapped["agents"].append(item)
            continue
        branches[branch]["agents"].append(item)

    for branch_id in BRANCH_IDS:
        for key in ("commands", "skills", "agents"):
            branches[branch_id][key] = sorted(set(branches[branch_id][key]))
        bullets = (
            branches[branch_id]["commands"]
            + branches[branch_id]["agents"]
            + [f"skill:{s}" for s in branches[branch_id]["skills"]]
        )
        seen = set()
        deduped = []
        for item in bullets:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        branches[branch_id]["bullets"] = deduped

    return branches, unmapped, warnings


def build_tech_data(branches: Dict[str, Dict[str, List[str]]]) -> Dict:
    data = {}
    for branch_id in BRANCH_IDS:
        meta = BRANCH_META[branch_id]
        data[branch_id] = {
            "label": meta["label"],
            "icon": meta["icon"],
            "color": meta["color"],
            "commands": branches[branch_id]["commands"],
            "bullets": branches[branch_id]["bullets"],
            "skills": branches[branch_id]["skills"],
            "agents": branches[branch_id]["agents"],
            "desc": meta["desc"],
        }
    return data


def render_tech_data_block(tech_data: Dict) -> str:
    json_text = json.dumps(tech_data, indent=4)
    lines = json_text.splitlines()
    base = "        "
    const_line = base + "const TECH_DATA = " + lines[0].lstrip()
    rest = [base + line for line in lines[1:]]
    if rest:
        rest[-1] = rest[-1] + ";"
    block_lines = [
        base + "// BEGIN AUTO-GENERATED TECH_DATA",
        const_line,
        *rest,
        base + "// END AUTO-GENERATED TECH_DATA",
    ]
    return "\n".join(block_lines)


def replace_tech_data(html_text: str, block: str) -> str:
    start_marker = "// BEGIN AUTO-GENERATED TECH_DATA"
    end_marker = "// END AUTO-GENERATED TECH_DATA"
    if start_marker in html_text and end_marker in html_text:
        start_idx = html_text.index(start_marker)
        end_idx = html_text.index(end_marker) + len(end_marker)
        return html_text[:start_idx] + block + html_text[end_idx:]

    needle = "const TECH_DATA = {"
    start = html_text.find(needle)
    if start == -1:
        raise ValueError("TECH_DATA block not found")
    brace_start = html_text.find("{", start)
    brace_end = find_matching_brace(html_text, brace_start)
    semi = html_text.find(";", brace_end)
    if semi == -1:
        raise ValueError("TECH_DATA block not terminated")
    return html_text[:start] + block + html_text[semi + 1 :]


def main() -> int:
    branches, unmapped, warnings = build_items()
    if warnings:
        print("Naming warnings:")
        for warning in warnings:
            print(f"- {warning}")

    total_unmapped = sum(len(v) for v in unmapped.values())
    if total_unmapped:
        print("Unmapped items detected:")
        for key, values in unmapped.items():
            if values:
                print(f"- {key}: {len(values)}")
                for item in values:
                    print(f"  - {item}")
        return 1

    tech_data = build_tech_data(branches)
    block = render_tech_data_block(tech_data)
    html_text = HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    updated = replace_tech_data(html_text, block)
    if updated != html_text:
        HTML_PATH.write_text(updated, encoding="utf-8")

    print("TECH_DATA updated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
