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


if __name__ == "__main__":
    reg = CapabilityRegistry()
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
