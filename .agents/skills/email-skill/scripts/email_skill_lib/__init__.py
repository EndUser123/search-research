"""email_skill_lib: library modules for the email-skill CLI.

Modules:
    accounts:  Hardcoded account list + derive_provider() helper.
    schema:    JSON envelope constants and make_envelope().
    cache:     TTL cache for scan results, with cross-platform file lock
               and stale-lock recovery. Lives at P:/.data/email-scan/.
    scoring:   Heuristic 3+3 scoring (importance 0-10 + urgency 0-10) with
               action_type derivation. Loads whitelist from
               ~/.config/email-skill/whitelist.txt.
    himalaya:  Subprocess wrapper around the himalaya CLI email client.
               Gracefully degrades to {"error": "himalaya not found", ...}
               when the binary is not on PATH.
    defer:     Per-thread defer (snooze for N hours) and ignore (suppress
               until thread_id changes) state. Persisted in
               P:/.data/email-scan/state.json.

The CLI entry point (scripts/email_skill.py) composes these modules.
"""