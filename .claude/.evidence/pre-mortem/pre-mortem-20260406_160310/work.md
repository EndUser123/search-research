Target: P:/.claude/skills/rns/lib/render.py

A new RNS action renderer module. Produces consistent formatted output for RNS action items.
Takes list[CrossSessionAction] and renders:
- Domain sections with emoji headers and domain number prefix (e.g. '1')
- Items numbered within domain (1a, 1b, 2a)
- [UNVERIFIED] markers for heuristic-extracted items
- Carryover section
- '0 — Do ALL' footer

Key exports:
- format_rns_output(actions, carryover, machine_format, **kwargs) -> str
- render_actions(actions, carryover, format_options) -> str  
- render_machine_format(actions, carryover) -> str
- RenderOptions dataclass

Dependencies: lib.chain (CrossSessionAction dataclass)
