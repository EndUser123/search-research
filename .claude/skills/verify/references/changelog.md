# Version History

- **v1.2.0** (2026-03-13): Added post-hoc verification mode
  - **NEW**: Post-hoc verification mode with LLM-as-Judge approach
  - **NEW**: RTM (Requirements Traceability Matrix) generation and validation
  - **NEW**: TSR (Task Success Rate) calculation from evidence ledger
  - **NEW**: `tiers/post_hoc_analyzer.py` module for chat history analysis
  - Post-hoc verification evaluates completed work through artifacts (plan, evidence ledger, transcript)
  - Integrated with /plan-workflow (RTM) and /code (TSR)
  - Updated documentation with post-hoc workflow and examples
  - Enhanced workflow_steps to support both real-time and post-hoc modes

- **v1.1.0** (2026-03-12): Added Tier 0 checklist verification
  - **NEW**: Tier 0 (Checklist) - fast-fail verification before running tests
  - Changed from 3-tier to 4-tier workflow (checklist -> component -> integration -> e2e)
  - Shared checklist library for skill/hook/feature verification
  - Integration tests for complete 4-tier workflow
  - Updated documentation with 4-tier examples

- **v1.0.0** (2026-03-10): Initial release
  - 3-tier verification workflow
  - Evidence-based reporting
  - Integration with TASK-000/002/003 components
