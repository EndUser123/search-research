# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **CKS write-back** (`persistence.py`): After saving an arch decision, ingest it into the CKS database so future `/arch` queries on the same domain benefit from accumulated decisions (closes the learning loop)
- `_find_cks_db()`: Walks up 6 directory levels to locate `__csf/data/cks.db` without hardcoded paths
- `_ingest_into_cks()`: Silent-failure SQLite INSERT with `INSERT OR IGNORE` idempotency; never blocks primary save
- **13 new persistence tests** (`tests/test_persistence.py`): Covers DB discovery, content truncation, title capping, silent-failure contract, duplicate-ID guard, and save_arch_decision integration
- **Urgency column** in all template findings tables (`deep.md`, `fast.md`, `cli.md`, `python.md`, `precedent.md`, `data-pipeline.md`): Separates triage urgency (`Blocking | Address Soon | Defer | Accept`) from severity
- **`deep.md` complete rewrite**: Comprehensive 700+ line template replacing broken 180-line stub; adds ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, and DEFAULT paths with GoT analysis, Cynefin classification, Proportionality Gate, and Value Completeness Gate
- **6-lens Adversarial Self-Review** (`deep.md`, `fast.md`): Failure Mode, Assumptions, Omitted Risks, Multi-Terminal, Contradiction Check, Reversibility — replaces single "weakest assumption" self-critique
- **Blind Spot Meta-Critique** (`deep.md`): Post-review step with four perspective-shifting questions; "nothing comes to mind" is explicitly rejected
- **Confidence Calibration Checklist** (`deep.md`, `fast.md`): Table-based evidence audit capping at 70% for web-only sources and docking per skipped stage
- **SKILL.md routing guide**: Documents `/arch` vs `architect` agent precedence, downstream workflow (`/arch → /prrp → /adversarial-review → /adversarial-rca`)
- **TemplateResult TypedDict chaining**: `detect_domain_chaining()` + `chained_domains` key; 17 new routing tests (73 total)

### Changed
- `fast.md` adversarial self-review upgraded from single "weakest assumption" to 3-lens + Blind Spot format
- `SKILL.md` Philosophy section updated with adversarial self-review and confidence calibration bullets

### Fixed
- Initial bug fixes and stability improvements

## [0.1.0] - 2026-01-11

### Added
- Initial release
- Basic feature set
- Documentation
