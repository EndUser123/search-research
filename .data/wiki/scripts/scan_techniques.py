"""
Extract technique indicators from all SKILL.md files.

Mechanically scans for patterns associated with known techniques, then
produces a structured report showing which skills use which techniques.
This is the breadth pass — LLM deep-reads are the depth pass.

Output: P:/tmp/technique-scan.json + P:/tmp/technique-scan.md
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# Technique indicators: (technique_name, [regex_patterns to grep for])
# Each pattern is searched case-insensitively across the full SKILL.md body.
# A skill "exhibits" a technique if ANY pattern matches.
TECHNIQUE_INDICATORS = [
    # Self-improvement
    ("self_improvement", [r"self.improv", r"recursive.*improv", r"optimize.*skill", r"skill.*optim", r"evolve.*skill", r"mutate.*skill", r"graduate.*rule"]),
    ("held_out_validation", [r"held.out", r"held-out", r"validation.*split", r"train.*test.*split", r"baseline.*candidate", r"overfit"]),
    ("skill_authoring", [r"create.*skill", r"write.*SKILL\.md", r"author.*skill", r"scaffold.*skill", r"skill.*from.*doc"]),

    # Evidence and verification
    ("evidence_tiers", [r"tier\s*[0-4]", r"evidence.*tier", r"confidence.*ceiling", r"evidence.*level"]),
    ("fact_inference_classification", [r"\[FACT\]", r"\[INFERENCE\]", r"\[UNKNOWN\]", r"\[RECOMMENDATION\]", r"fact.*inference.*unknown"]),
    ("verification_receipt", [r"receipt", r"verified.*claim", r"claim.*verify", r"unverified.*claim", r"evidence.*receipt"]),
    ("candidate_evidence_not_truth", [r"candidate.*evidence", r"not.*truth", r"not.*ground.*truth", r"treat.*as.*claim"]),
    ("falsifier", [r"falsif", r"would.*prove.*wrong", r"what.*would.*make.*this.*wrong"]),

    # Phase gates
    ("phase_gates", [r"phase.*gate", r"gate.*phase", r"STOP.*between", r"hard.*stop", r"gate.*validation", r"phase.*1.*phase.*2"]),
    ("stop_condition", [r"stop.*condition", r"halt.*condition", r"abort.*gate", r"abort.*condition"]),

    # Conflict detection
    ("conflict_detection", [r"conflict.*detect", r"contradict", r"disagree.*source", r"conflicting.*claim"]),

    # Source quality
    ("source_quality_scoring", [r"source.*quality", r"credib", r"authorit.*score", r"CREDIBLE"]),
    ("source_diversity", [r"source.*diversity", r"diverse.*source", r"mix.*source.*type"]),

    # Progressive disclosure
    ("progressive_disclosure", [r"progressive.*disclosure", r"reference.*loader", r"trigger.*load", r"lean.*core", r"trigger.*reference"]),
    ("context_firewall", [r"context.*firewall", r"evidence.*brief", r"compress.*before.*synth"]),

    # Output discipline
    ("shape_explicit", [r"shape.*explicit", r"output.*shape", r"output.*format.*required", r"required.*section"]),
    ("copyable_checklist", [r"checklist", r"copy.*into.*response", r"tick.*off", r"\- \[ \]"]),
    ("provenance_tags", [r"provenance", r"FACT\(self", r"FACT\(delegated", r"from.file.read", r"from.grep", r"from.bundle"]),
    ("accounting_sentinel", [r"ACCOUNTING", r"account.for.everything", r"bucket.*count", r"tasked.*fixed.*deferred"]),
    ("selection_contract", [r"<selection>", r"parseable.*contract", r"options.*\[0\|1\|2"]),

    # Routing and boundaries
    ("exclusion_clause", [r"do\s+not\s+use\s+for", r"do\s+NOT\s+use\s+for", r"do\s+not\s+trigger", r"when\s+not\s+to\s+use"]),
    ("cross_skill_delegation", [r"use\s+/\w+\s+instead", r"delegate.*to\s+/", r"route.*to\s+/", r"suggest.*\/\w+"]),

    # Retirement and lifecycle
    ("deprecation_stub", [r"disable.model.invocation.*true", r"DEPRECATED", r"stub.*rout", r"absorbed.*into"]),
    ("retirement_check", [r"retire", r"superseded", r"status:\s*supersed"]),
    ("engine_preservation", [r"engine.*preserv", r"source.of.truth.*engine", r"engine.*stays"]),

    # Self-attack and adversarial
    ("self_attack_checklist", [r"attack.*checklist", r"self.*attack", r"attack.*vector", r"theater.*duplication"]),
    ("generator_not_validator", [r"generator.*validator", r"distinct.*LLM.*instance", r"self.validation.*block"]),

    # Failure modes
    ("failure_class_typology", [r"failure.*class", r"failure.*typology", r"distinct.*failure.*type"]),
    ("honest_refusal", [r"cannot.*determine", r"insufficient.*evidence", r"prefer.*honest", r"refuse.*to.*guess"]),

    # Specific named patterns
    ("xstc", [r"cross.skill.*transfer", r"XSTC", r"transfer.*check"]),
    ("cec", [r"completion.*evidence.*contract", r"\bCEC\b", r"claim.type.*enum"]),
    ("cecy", [r"completion.*evidence"]),
    ("opportunity_durability", [r"opportunity.*durab", r"persist.*opportunity", r"durable.*path", r"MONITOR.*INVESTIGATE.*DEFER"]),
    ("research_ledger", [r"research.*ledger", r"incremental.*reuse", r"prior.*research", r"last.researched"]),

    # Cognitive frameworks
    ("cynequin", [r"Cynefin", r"cynequin"]),
    ("chestertons_fence", [r"Chesterton", r"chesterton"]),
    ("deletion_test", [r"deletion.*test", r"imagine.*deleting"]),
    ("surprise_check", [r"surprise.*check", r"why.*this.*answer.*true"]),
    ("absent_evidence", [r"absent.*evidence", r"expect.*to.*find.*but.*didn"]),

    # Pipeline patterns
    ("lifecycle_state_machine", [r"lifecycle.*state", r"state.*machine", r"state.*transition"]),
    ("pipeline_pattern", [r"pipeline.*pattern", r"stage.*1.*stage.*2", r"sequential.*stage"]),
    ("swarm_pattern", [r"swarm", r"parallel.*worker", r"fan.out"]),
    ("debate_pattern", [r"debate.*pattern", r"opposing.*position", r"pro.*con.*agent"]),
    ("supervisor_pattern", [r"supervisor.*pattern", r"coordinator.*agent", r"orchestrat.*subtask"]),

    # Prompting techniques
    ("pushy_description", [r"pushy", r"undertrigger", r"under.trigger", r"make.*sure.*to.*use.*this.*skill"]),
    ("falsifier_section", [r"##\s*Falsifier", r"falsifier.*section", r"wrong.*if.*within.*6.*month"]),
    ("model_disclosure", [r"model.*disclosure", r"parent.inherited", r"fresh.subagent.*model"]),

    # Meta
    ("a_b_loop", [r"A/B.*loop", r"agent.*A.*agent.*B", r"fresh.*instance.*test"]),
    ("recursive_self_invoke", [r"recursive.*self", r"self.invocat", r"run.*on.*itself", r"improve.*own"]),
    ("constitution_list", [r"constitution", r"RBW.001", r"constitutional.*rule"]),
    ("promotion_gate", [r"promotion.*gate", r"WARN.*BLOCK", r"three.legged.*evidence"]),
    ("health_check_executable", [r"health.check.*executable", r"health.check.*script", r"cks_health"]),
]

# Compile patterns once
COMPILED = [(name, [re.compile(p, re.IGNORECASE) for p in patterns]) for name, patterns in TECHNIQUE_INDICATORS]


def scan_skill(skill_md: Path) -> dict:
    """Scan one SKILL.md and return technique hits."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"path": str(skill_md), "techniques": [], "line_count": 0, "error": "read_failed"}

    hits = []
    for tech_name, patterns in COMPILED:
        for pat in patterns:
            if pat.search(text):
                hits.append(tech_name)
                break  # one match per technique is enough

    return {
        "path": str(skill_md).replace("\\", "/"),
        "techniques": hits,
        "technique_count": len(hits),
        "line_count": text.count("\n"),
        "char_count": len(text),
    }


def main():
    # Reuse the same scope list as index_skills.py
    SCOPES = [
        ("grok-user", Path("C:/Users/brsth/.grok/skills"), None),
        ("grok-bundled", Path("C:/Users/brsth/.grok/bundled/skills"), None),
        ("grok-installed-plugins", Path("C:/Users/brsth/.grok/installed-plugins"), "skills"),
        ("grok-project", Path("P:/.grok/skills"), None),
        ("grok-agents", Path("P:/.agents/skills"), None),
        ("claude-user", Path("C:/Users/brsth/.claude/skills"), None),
        ("claude-project", Path("P:/.claude/skills"), None),
        ("codex-user", Path("C:/Users/brsth/.codex/skills"), None),
        ("claude-cache-antigravity", Path("C:/Users/brsth/.claude/plugins/cache/antigravity-for-claude-code"), "skills"),
        ("claude-cache-official", Path("C:/Users/brsth/.claude/plugins/cache/claude-plugins-official"), "skills"),
        ("claude-cache-karpathy", Path("C:/Users/brsth/.claude/plugins/cache/karpathy-skills"), "skills"),
        ("claude-cache-local", Path("C:/Users/brsth/.claude/plugins/cache/local"), "skills"),
        ("claude-cache-minimax", Path("C:/Users/brsth/.claude/plugins/cache/minimax-skills"), "skills"),
        ("claude-cache-openai-codex", Path("C:/Users/brsth/.claude/plugins/cache/openai-codex"), "skills"),
        ("claude-cache-pi", Path("C:/Users/brsth/.claude/plugins/cache/pi-plugin-cc"), "skills"),
        ("claude-cache-ponytail", Path("C:/Users/brsth/.claude/plugins/cache/ponytail"), "skills"),
        ("claude-cache-superpowers", Path("C:/Users/brsth/.claude/plugins/cache/superpowers-marketplace"), "skills"),
        ("claude-cache-zai", Path("C:/Users/brsth/.claude/plugins/cache/zai-coding-plugins"), "skills"),
        ("claude-mkt-local", Path("C:/Users/brsth/.claude/plugins/marketplaces/local/plugins"), "skills"),
        ("claude-mkt-quickstop", Path("C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins"), "skills"),
        ("claude-mkt-thedotmack", Path("C:/Users/brsth/.claude/plugins/marketplaces/thedotmack"), "skills"),
        ("marketplace", Path("P:/packages/.claude-marketplace/plugins"), "skills"),
    ]

    all_results = []
    for scope, root, _ in SCOPES:
        rp = Path(root)
        if not rp.exists():
            continue
        for skill_md in rp.rglob("SKILL.md"):
            result = scan_skill(skill_md)
            result["scope"] = scope
            all_results.append(result)

    # Write JSON
    out_json = Path("P:/tmp/technique-scan.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    # Aggregate: technique -> [skills that have it]
    tech_to_skills = defaultdict(list)
    for r in all_results:
        for t in r["techniques"]:
            tech_to_skills[t].append(r["path"].split("/")[-2])  # skill dir name

    # Sort by prevalence
    tech_counts = Counter()
    for r in all_results:
        for t in r["techniques"]:
            tech_counts[t] += 1

    # Top skills by technique count
    top_skills = sorted(all_results, key=lambda r: -r["technique_count"])[:50]

    # Write markdown report
    lines = [
        "# Technique scan: all 964 SKILL.md files",
        "",
        f"Generated by `python P:/tmp/scan_techniques.py` on {Path('P:/tmp/technique-scan.json').stat().st_size} bytes of data.",
        f"Total skills scanned: {len(all_results)}",
        f"Total techniques detected: {len(tech_counts)}",
        "",
        "## Technique prevalence (sorted by count)",
        "",
        "| Technique | Skills | Sample skills |",
        "|---|---|---|",
    ]
    for tech, count in tech_counts.most_common():
        samples = sorted(set(tech_to_skills[tech]))[:5]
        sample_str = ", ".join(samples)
        if len(set(tech_to_skills[tech])) > 5:
            sample_str += f" (+{len(set(tech_to_skills[tech]))-5} more)"
        lines.append(f"| `{tech}` | {count} | {sample_str} |")

    lines.extend([
        "",
        "## Top 50 skills by technique density",
        "",
        "| Skill | Scope | Techniques | Line count |",
        "|---|---|---|---|",
    ])
    for r in top_skills:
        name = r["path"].split("/")[-2]
        scope = r["scope"]
        techs = ", ".join(r["techniques"][:8])
        if len(r["techniques"]) > 8:
            techs += f" (+{len(r['techniques'])-8})"
        lines.append(f"| **{name}** | {scope} | {techs} | {r['line_count']} |")

    lines.extend([
        "",
        "## Skills with zero detected techniques",
        "",
        f"Count: {sum(1 for r in all_results if r['technique_count'] == 0)}",
        "",
        "These may still contain novel techniques not covered by the indicator patterns. Manual review recommended for any with high line counts.",
        "",
    ])

    out_md = Path("P:/tmp/technique-scan.md")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Scanned {len(all_results)} skills")
    print(f"Detected {len(tech_counts)} distinct techniques")
    print(f"Top technique: {tech_counts.most_common(1)[0]}")
    print(f"JSON: {out_json}")
    print(f"Markdown: {out_md}")


if __name__ == "__main__":
    main()
