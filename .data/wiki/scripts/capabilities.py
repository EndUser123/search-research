"""
Runtime API for the capability registry.

Loads all capability contracts from P:/.data/wiki/capabilities/ and skill
frontmatter from ~/.grok/skills/. Provides query functions for:
- get_by_domain(domain) -> list of capabilities
- get_by_capability(name) -> list of providing skills
- get_consumers(capability) -> list of skills that use it
- get_all_domains() -> dict of domain -> capabilities
- get_shared_services() -> capabilities + providers used by 3+ skills

Usage:
    from capabilities import CapabilityRegistry
    reg = CapabilityRegistry()
    reg.get_by_domain("discovery")  # all discovery capabilities
    reg.get_consumers("multi-backend-search")  # who uses web search

Skills can import this at runtime to query the registry instead of
hardcoding capability lists or reading the markdown graph.
"""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import re


CAPS_DIR = Path("P:/.data/wiki/capabilities")
SKILLS_DIRS = [
    Path("C:/Users/brsth/.grok/skills"),
    Path("P:/.grok/skills"),
    Path("P:/.agents/skills"),
]
GRAPH_SCRIPT = Path("P:/.data/wiki/scripts/build_skill_graph.py")


class Capability:
    def __init__(self, name: str, domain: str = "", version: str = "1.0"):
        self.name = name
        self.domain = domain
        self.version = version
        self.providers: list[str] = []  # skills that provide this
        self.consumers: list[str] = []  # skills that use this


class CapabilityRegistry:
    """Queryable registry of all capabilities in the fleet."""

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._skill_domains: dict[str, str] = {}
        self._skill_provides: dict[str, list[str]] = {}
        self._skill_uses_caps: dict[str, list[str]] = {}
        self._skill_consumes: dict[str, list[str]] = {}
        self._load()

    def _load(self):
        """Load all contracts and skill frontmatter."""
        # Load capability contracts
        if CAPS_DIR.exists():
            for cf in CAPS_DIR.glob("*.md"):
                try:
                    body = cf.read_text(encoding="utf-8", errors="replace")
                    parts = body.split("---", 2)
                    if len(parts) < 3:
                        continue
                    fm = parts[1]
                    title_m = re.search(r'title:\s*"([^"]+)"', fm)
                    dom_m = re.search(r"domain:\s*(\S+)", fm)
                    ver_m = re.search(r"version:\s*(\S+)", fm)
                    if title_m:
                        name = title_m.group(1).strip().lower()
                        cap = Capability(
                            name=name,
                            domain=dom_m.group(1).strip().strip("'\"") if dom_m else "uncategorized",
                            version=ver_m.group(1).strip().strip("'\"") if ver_m else "1.0",
                        )
                        self._capabilities[name] = cap
                except Exception:
                    pass

        # Load skill frontmatter
        for skills_dir in SKILLS_DIRS:
            if not skills_dir.exists():
                continue
            for sd in skills_dir.iterdir():
                sf = sd / "SKILL.md"
                if not sf.exists() or not sd.is_dir():
                    continue
                try:
                    body = sf.read_text(encoding="utf-8", errors="replace")
                    parts = body.split("---", 2)
                    if len(parts) < 3:
                        continue
                    fm = parts[1]
                    name = sd.name

                    dom_m = re.search(r"domain:\s*(\S+)", fm)
                    if dom_m:
                        self._skill_domains[name] = dom_m.group(1).strip().strip("'\"")

                    prov_m = re.search(r"provides:\s*\[([^\]]*)\]", fm)
                    if prov_m:
                        caps = [c.strip().strip("'\"").lower() for c in prov_m.group(1).split(",") if c.strip()]
                        self._skill_provides[name] = caps
                        for cap in caps:
                            if cap in self._capabilities:
                                self._capabilities[cap].providers.append(name)
                            else:
                                # Capability without a contract file
                                new_cap = Capability(name=cap)
                                new_cap.providers.append(name)
                                self._capabilities[cap] = new_cap

                    uses_m = re.search(r"uses_capabilities:\s*\[([^\]]*)\]", fm)
                    if uses_m:
                        caps = [c.strip().strip("'\"").lower() for c in uses_m.group(1).split(",") if c.strip()]
                        self._skill_uses_caps[name] = caps
                        for cap in caps:
                            if cap in self._capabilities:
                                self._capabilities[cap].consumers.append(name)

                    con_m = re.search(r"consumes:\s*\[([^\]]*)\]", fm)
                    if con_m:
                        tools = [t.strip().strip("'\"").lower() for t in con_m.group(1).split(",") if t.strip()]
                        self._skill_consumes[name] = tools
                except Exception:
                    pass

    def get_by_domain(self, domain: str) -> list[Capability]:
        """All capabilities in a domain."""
        return sorted(
            [c for c in self._capabilities.values() if c.domain == domain],
            key=lambda c: c.name,
        )

    def get_by_capability(self, name: str) -> list[str]:
        """Skills that provide a capability."""
        cap = self._capabilities.get(name.lower())
        return sorted(set(cap.providers)) if cap else []

    def get_consumers(self, name: str) -> list[str]:
        """Skills that use (not provide) a capability."""
        cap = self._capabilities.get(name.lower())
        return sorted(set(cap.consumers)) if cap else []

    def get_all_domains(self) -> dict[str, list[str]]:
        """Domain -> list of capability names."""
        result = defaultdict(list)
        for cap in self._capabilities.values():
            result[cap.domain or "uncategorized"].append(cap.name)
        return {k: sorted(v) for k, v in sorted(result.items())}

    def get_shared_services(self, min_consumers: int = 3) -> dict[str, list[str]]:
        """Capabilities + high-usage providers used by >=min_consumers skills.

        Merges capability consumers and provider consumers (from tool usage).
        """
        result = {}
        # Capabilities with multiple providers or consumers
        for name, cap in sorted(self._capabilities.items()):
            total = len(set(cap.providers)) + len(set(cap.consumers))
            if total >= min_consumers:
                all_users = sorted(set(cap.providers + cap.consumers))
                result[name] = all_users
        return result

    def list_capabilities(self) -> list[str]:
        """All capability names."""
        return sorted(self._capabilities.keys())

    def _load_depends_on(self) -> dict[str, list[str]]:
        """Load depends_on and composes from all skill frontmatter."""
        depends_on = {}
        composes = {}
        for skills_dir in SKILLS_DIRS:
            if not skills_dir.exists():
                continue
            for sd in skills_dir.iterdir():
                sf = sd / "SKILL.md"
                if not sf.exists() or not sd.is_dir():
                    continue
                try:
                    body = sf.read_text(encoding="utf-8", errors="replace")
                    parts = body.split("---", 2)
                    if len(parts) < 3:
                        continue
                    fm = parts[1]
                    name = sd.name

                    dep_m = re.search(r"depends_on:\s*\[([^\]]*)\]", fm)
                    if dep_m:
                        deps = [d.strip().strip("'\"") for d in dep_m.group(1).split(",") if d.strip()]
                        depends_on[name] = deps

                    comp_m = re.search(r"composes:\s*\[([^\]]*)\]", fm)
                    if comp_m:
                        comps = [c.strip().strip("'\"") for c in comp_m.group(1).split(",") if c.strip()]
                        composes[name] = comps
                except Exception:
                    pass
        return depends_on, composes

    def health_check(self) -> dict:
        """Check skill dependency health: dangling depends_on, missing capabilities.

        Returns dict with:
        - total_skills: count of skills with SKILL.md
        - dangling_deps: {skill: [missing_dep, ...]} — skill depends on something not in catalog
        - skills_without_domain: [skill, ...] — first 20
        - dangling_count: total missing deps across all skills
        """
        depends_on, composes = self._load_depends_on()
        all_skills = set()
        for skills_dir in SKILLS_DIRS:
            if skills_dir.exists():
                all_skills.update(sd.name for sd in skills_dir.iterdir()
                                  if sd.is_dir() and (sd / "SKILL.md").exists())

        # Dangling dependencies
        dangling_deps = {}
        for skill, deps in depends_on.items():
            missing = [d for d in deps if d not in all_skills]
            if missing:
                dangling_deps[skill] = missing

        # Skills without domain
        skills_without_domain = sorted(all_skills - set(self._skill_domains.keys()))

        return {
            "total_skills": len(all_skills),
            "dangling_deps": dangling_deps,
            "skills_without_domain": skills_without_domain[:20],
            "dangling_count": sum(len(v) for v in dangling_deps.values()),
        }

    def verify_consumers(self) -> dict:
        """Verify that declared consumers actually import the provider's code.

        For each skill that depends_on another skill, scan the consumer's
        Python files for an import or reference to the provider's module.
        Flag declared-but-not-wired relationships.

        Returns dict with:
        - verified: [(consumer, provider, capability)]
        - unwired: [(consumer, provider, capability, hint)]
        """
        depends_on, composes = self._load_depends_on()
        verified = []
        unwired = []

        # Build combined dependency list from depends_on + composes
        all_deps = {}
        for consumer, deps in depends_on.items():
            all_deps.setdefault(consumer, []).extend([(d, "depends_on") for d in deps])
        for consumer, comps in composes.items():
            # composes entries may be "skill:function" format — extract skill name
            for c in comps:
                dep_name = c.split(":")[0] if ":" in c else c
                all_deps.setdefault(consumer, []).append((dep_name, "composes"))

        # Check each dependency relationship
        for consumer, dep_list in all_deps.items():
            for dep, cap_type in dep_list:
                # Find the provider's scripts directory
                provider_scripts = None
                for skills_dir in SKILLS_DIRS:
                    candidate = skills_dir / dep / "scripts"
                    if candidate.exists():
                        provider_scripts = candidate
                        break
                    candidate = skills_dir / dep / "__lib"
                    if candidate.exists():
                        provider_scripts = candidate
                        break

                if not provider_scripts:
                    continue  # Provider has no scripts (may be prompt-only skill)

                # Find consumer's script directories (check both scripts/ and __lib/)
                consumer_dirs = []
                for skills_dir in SKILLS_DIRS:
                    for subdir in ("scripts", "__lib"):
                        candidate = skills_dir / consumer / subdir
                        if candidate.exists():
                            consumer_dirs.append(candidate)

                if not consumer_dirs:
                    continue  # Consumer has no scripts

                # Scan consumer's .py files for import-level references to the provider
                found = False
                import_patterns = [
                    f"import {dep}\n",
                    f"import {dep} ",
                    f"from {dep} ",
                    f"from {dep}.",
                    f'"{dep}/',  # path reference in string
                    f"'{dep}/",
                    f"/{dep}/SKILL.md",  # SKILL.md path reference
                ]
                for consumer_dir in consumer_dirs:
                    for pyfile in consumer_dir.rglob("*.py"):
                        if "__pycache__" in str(pyfile):
                            continue
                        try:
                            content = pyfile.read_text(encoding="utf-8", errors="replace")
                            # Check for import-level references only (not bare substring)
                            for pattern in import_patterns:
                                if pattern in content:
                                    found = True
                                    break
                            if found:
                                break
                        except OSError:
                            continue
                    if found:
                        break

                if found:
                    verified.append((consumer, dep, cap_type))
                else:
                    unwired.append((consumer, dep, cap_type,
                                   "no import found — may be prompt-only composition"))

        return {
            "verified": verified,
            "unwired": unwired,
            "verified_count": len(verified),
            "unwired_count": len(unwired),
        }


def _format_help_text(reg: CapabilityRegistry) -> str:
    """Generate formatted help text showing all domains and their capabilities.

    This is the single source of truth for help displays. Skills should call
    `python capabilities.py --help-text` instead of hardcoding capability lists.
    """
    lines = ["## Fleet capabilities (auto-generated from registry)", ""]
    domains = reg.get_all_domains()
    for domain, caps in sorted(domains.items()):
        lines.append(f"### {domain} domain ({len(caps)} capabilities)")
        for cap_name in caps:
            cap = reg._capabilities.get(cap_name)
            providers = ", ".join(sorted(set(cap.providers))) if cap else ""
            consumers = ", ".join(sorted(set(cap.consumers))) if cap else ""
            consumer_note = f" (used by {consumers})" if consumers else ""
            lines.append(f"- **{cap_name}** -- provided by {providers or '(none)'}{consumer_note}")
        lines.append("")
    return "\n".join(lines)


def _format_domain_help(reg: CapabilityRegistry, domain: str) -> str:
    """Show capabilities in a specific domain — for skill help sections."""
    caps = reg.get_by_domain(domain)
    if not caps:
        return f"No capabilities found in domain '{domain}'."
    lines = [f"## {domain} domain ({len(caps)} capabilities)", ""]
    for cap in caps:
        providers = ", ".join(sorted(set(cap.providers)))
        consumers = ", ".join(sorted(set(cap.consumers)))
        lines.append(f"- **{cap.name}** (v{cap.version})")
        if providers:
            lines.append(f"  - Provided by: {providers}")
        if consumers:
            lines.append(f"  - Used by: {consumers}")
    return "\n".join(lines)


def _format_skill_caps(reg: CapabilityRegistry, skill_name: str) -> str:
    """Show what a skill provides, consumes, and uses — for skill introspection."""
    provides = reg._skill_provides.get(skill_name, [])
    uses = reg._skill_uses_caps.get(skill_name, [])
    consumes = reg._skill_consumes.get(skill_name, [])
    domain = reg._skill_domains.get(skill_name, "uncategorized")
    lines = [f"## {skill_name} (domain: {domain})", ""]
    if provides:
        lines.append(f"**Provides:** {', '.join(provides)}")
    if uses:
        lines.append(f"**Uses capabilities:** {', '.join(uses)}")
    if consumes:
        lines.append(f"**Consumes tools:** {', '.join(consumes)}")
    if not any([provides, uses, consumes]):
        lines.append("(no capability frontmatter found)")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Capability registry query and help-text generation"
    )
    parser.add_argument(
        "--help-text", action="store_true",
        help="Generate formatted markdown for all domains + capabilities",
    )
    parser.add_argument(
        "--for-domain", metavar="DOMAIN",
        help="Show capabilities in a specific domain",
    )
    parser.add_argument(
        "--for-skill", metavar="SKILL",
        help="Show what a skill provides, consumes, and uses",
    )
    parser.add_argument(
        "--shared", action="store_true",
        help="Show capabilities used by 3+ skills (shared services)",
    )
    parser.add_argument(
        "--consumers", metavar="CAPABILITY",
        help="Show all skills that use a capability",
    )
    parser.add_argument(
        "--health-check", action="store_true",
        help="Check skill dependency health: dangling deps, missing domains",
    )
    parser.add_argument(
        "--verify-consumers", action="store_true",
        help="Verify declared consumers actually import provider code",
    )
    args = parser.parse_args()

    reg = CapabilityRegistry()

    if args.help_text:
        print(_format_help_text(reg))
    elif args.for_domain:
        print(_format_domain_help(reg, args.for_domain))
    elif args.for_skill:
        print(_format_skill_caps(reg, args.for_skill))
    elif args.shared:
        shared = reg.get_shared_services(min_consumers=3)
        print(f"Shared services (3+ skills): {len(shared)}")
        for name, users in sorted(shared.items(), key=lambda x: -len(x[1])):
            print(f"  {name}: {len(users)} skills -- {', '.join(users)}")
    elif args.consumers:
        consumers = reg.get_consumers(args.consumers)
        providers = reg.get_by_capability(args.consumers)
        print(f"Capability: {args.consumers}")
        print(f"  Providers: {', '.join(providers) if providers else '(none)'}")
        print(f"  Consumers: {', '.join(consumers) if consumers else '(none)'}")
    elif args.health_check:
        health = reg.health_check()
        print("=== Skill Graph Health Check ===")
        print(f"Total skills: {health['total_skills']}")
        print(f"Dangling dependencies: {health['dangling_count']}")
        if health["dangling_deps"]:
            print("\nSkills with dangling depends_on:")
            for skill, missing in sorted(health["dangling_deps"].items()):
                print(f"  {skill} → missing: {', '.join(missing)}")
        if health["skills_without_domain"]:
            print(f"\nSkills without domain ({len(health['skills_without_domain'])}):")
            for s in health["skills_without_domain"][:10]:
                print(f"  {s}")
            if len(health["skills_without_domain"]) > 10:
                print(f"  ... and {len(health['skills_without_domain']) - 10} more")
    elif args.verify_consumers:
        result = reg.verify_consumers()
        print("=== Consumer Wiring Verification ===")
        print(f"Verified (import found): {result['verified_count']}")
        print(f"Unwired (no import — may be prompt-only): {result['unwired_count']}")
        if result["unwired"]:
            print("\nPotentially unwired dependencies:")
            for consumer, provider, cap_type, hint in result["unwired"][:20]:
                print(f"  {consumer} → {provider} ({cap_type}) — {hint}")
    else:
        print(f"Capabilities: {len(reg.list_capabilities())}")
        print(f"Domains: {len(reg.get_all_domains())}")
        print()
        for domain, caps in reg.get_all_domains().items():
            print(f"  {domain} ({len(caps)}): {', '.join(caps)}")
        print()
        shared = reg.get_shared_services(min_consumers=3)
        print(f"Shared services (3+ skills): {len(shared)}")
        for name, users in sorted(shared.items(), key=lambda x: -len(x[1])):
            print(f"  {name}: {len(users)} skills")
