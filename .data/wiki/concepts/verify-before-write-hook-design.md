---
title: "Verify-Before-Write Hook Design"
created: 2026-08-02
source: session-2026-08-02
tags: [hook, enforcement, verification, receipt-rule, structural-fix, design-doc]
summary: >
  Design for a PreToolUse hook that structurally enforces the "verify-before-write"
  rule for external-sourced code constants (pool sizes, rate limits, thresholds,
  timeouts from documentation). Targets the decision layer (the write itself)
  rather than post-write reflection. Catches the 2026-08-02 Perplexity incident
  class: writing estimated values without running the authoritative tool.
agent: grok
host: grok
cognitive_load: 3
verification: tested-19-cases-pass
relations:
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: implements
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: related
---

# Verify-Before-Write Hook Design

## 1. Goal in one sentence

Block writes of external-sourced numeric config constants that have no
inline verification receipt, forcing the agent to either verify the value
with a tool call or explicitly label it `ESTIMATED`.

## 2. The failure class this targets

The 2026-08-02 Perplexity incident (`[[inference-in-code-blind-spot]]`): pool
sizes (300/25/25/25) were written into `fleet_quota.py` from a SKILL.md's
"~300/week" estimate without running `pwm usage` — the authoritative CLI that
was available the entire time. Four rounds of operator correction elapsed
before actual research happened. Root cause: the agent treated "I read it in a
document" as equivalent to "I verified it with a tool call." The prose rule did
not fire under closure pressure; the fix must target the **write** (decision
layer), not post-write reflection.

## 3. Detection heuristic (deliverable 1)

The hook fires on a numeric literal that **simultaneously** satisfies the
scope gate AND a config-flavored signal, with no annotation in the window.

### 3a. Scope gate (file pattern) — the primary FP control

The hook only inspects writes to paths matching a config-file pattern:

| Pattern (case-insensitive) | Catches |
|---|---|
| `fleet_quota.py` | the incident file |
| `*_config.py`, `config.py` | app config modules |
| `constants*.py` | constants modules |
| `*quota*`, `*limit*`, `*threshold*`, `*rate_limit*`, `*budget*`, `*cap*`, `*tier*` | external-source-flavored files |

Edit `CONFIG_FILE_PATTERNS` to broaden. The trade-off is explicit:
**broad scope = more coverage but more friction.** v1 is narrow (config files
only) because external-sourced constants live in config files; scanning
`views.py` or `utils.py` would generate noise with no incident history.

### 3b. Config-flavored signal (what distinguishes `pool = 200` from `width = 200`)

A name or dict key is "config-flavored" if it contains one of these vocabulary
tokens (case-insensitive):

`POOL`, `QUOTA`, `LIMIT`, `RATE`, `THRESHOLD`, `TIMEOUT`, `RESET`, `CAP`,
`BUDGET`, `TIER`, `REMAINING`, `ALLOWANCE`.

Two syntactic shapes are detected:

- **Dict value under a config-flavored key** — `"pool": 300`, `"rate": 60`,
  `"limit": 25`. The dict-value position plus the key vocabulary is the
  strongest external-source signal.
- **Single screaming-snake config constant** — `TIMEOUT_SECONDS = 30`,
  `RATE_LIMIT = 100`. Requires the name to be all-caps AND config-flavored.

### 3c. What this does NOT flag (true negatives, verified by tests)

- `width = 200` — lowercase local variable, not config-flavored.
- `for i in range(200)` — loop bound, no config vocabulary.
- `META = {"version": 2, "count": 5}` — dict keys are not config vocabulary.
- `PI_APPROX = 3.14159` — screaming-snake but not config-flavored.
- `pool = 200` (lowercase scalar) — not a screaming-snake module constant.

## 4. Verification mechanism (deliverable 2)

A PreToolUse hook receives **only the current tool input on stdin** — it cannot
read prior tool-call history in-session (confirmed in
`~/.grok/docs/user-guide/10-hooks.md`: the envelope carries `toolName`,
`toolInput`, `sessionId`, `cwd`, but not the conversation transcript).

Therefore "has a receipt" is enforced through an **inline annotation contract**
— the agent's assertion that a receipt exists, made machine-checkable:

| Annotation | Meaning | Result |
|---|---|---|
| `# verified: <source>` | backed by a tool-call receipt | ALLOW |
| `# ESTIMATED ... Verify via: <cmd>` | gap explicitly labeled + upgrade path | ALLOW |
| *(neither)* | unverified | BLOCK |

**Annotation window** (lines checked for an annotation clearing a value at
line *L*): line *L* itself, line *L−1*, and the line where the enclosing config
dict opened (for multi-line dicts). This covers single-line dicts (the
incident), multi-line dicts, and block-comment-above styles.

### Why not scan the session transcript for a matching receipt?

Considered and **rejected for v1**: it would require reading
`~/.grok/sessions/<sessionId>` and fuzzy-matching a numeric value against prior
tool outputs. It is fragile (transcript format coupling, flush timing, the
value may be paraphrased rather than numeric) and the inline annotation already
gives a one-line escape hatch. The annotation IS the receipt contract: if the
agent genuinely verified the value, citing the source is trivial and durably
useful to future readers. Documented as a future enhancement only.

## 5. Block vs warn (deliverable 3)

**Decision: BLOCK (deny, exit 2).**

Rationale:
- On Grok Build, `PreToolUse` is binary — it either allows (exit 0, stdout
  ignored) or denies (exit 2 / `{"decision":"deny","reason":...}`, fed back to
  the model). There is no "allow but inject a message to the model" for
  `PreToolUse`. A pure "warn" (stderr on an allow) does **not** reach the model
  and would not change behavior — useless for the decision-layer target.
- The incident took 4 rounds precisely because nothing forced the decision. A
  warn that doesn't reach the model is the same as no enforcement.
- The escape hatch makes block-mode low-friction: a one-line annotation clears
  any trigger, so there is no frustrating loop where the agent cannot proceed.

The deny reason is prescriptive (shows the offending line, tells the agent
exactly the two ways to proceed, cites the wiki concept).

## 6. False-positive mitigation (deliverable 4)

Four layers, in order of importance:

1. **File-name scope gate** (§3a) — the hook never inspects non-config files.
   This alone removes the bulk of FPs (`count = 0`, `result = []`, loop bounds
   in business logic).
2. **Config-vocabulary signal** (§3b) — within config files, only
   config-flavored keys/names trigger. `MAX`/`VERSION`/`COUNT` are
   intentionally excluded from the vocabulary to avoid developer-default FPs.
3. **Annotation escape hatch** (§4) — even if the heuristic fires on a
   legitimate constant, `# verified: developer default` clears it in one line.
   This is the ultimate FP safety: block is acceptable because dismissal is
   trivial.
4. **Fail-open** — any parse error, unexpected input shape, or crash allows the
   write. The hook only blocks on a *positive* detection, never on ambiguity.

Known residual FP: a config file legitimately defining a developer-chosen
default under a config-flavored key (e.g. `RATE_LIMIT = 100` where 100 is the
developer's own choice). Mitigated by the annotation hatch (annotate once,
durable for future readers). This is acceptable and arguably desirable — it
makes the provenance of every config constant explicit.

## 7. The hook script (deliverable 5)

- **Script:** `~/.grok/hooks/PreToolUse_verify_before_write.py`
- **Registration:** `~/.grok/hooks/verify-before-write.json`
  (matcher `write|search_replace|Write|Edit`, timeout 4s, `command` type)
- **Style:** standalone Python, stdlib-only, follows the existing
  `PreToolUse_spawn_model_gate.py` pattern (read stdin JSON → fail-open on parse
  error → check tool name → inspect input → `{"decision":"deny"}` + exit 2, or
  exit 0).
- **Tested:** `tests/test_verify_before_write.py`, **19 cases pass**
  (3 true positives, 4 escape-hatch, 4 true negatives, 3 FP-mitigation,
  5 end-to-end stdin/exit-code contract including fail-open).

Activation path: the JSON is on disk; run `/hooks` → reload (`r`), or it loads
at next session start. To disable: delete `verify-before-write.json` or toggle
the hook off with `Space` in the Hooks tab.

## 8. Test matrix (deliverable 6)

| Category | Case | Expected | Status |
|---|---|---|---|
| True positive | `POOLS = {"pool": 300}` (incident) | block | PASS |
| True positive | multi-provider `QUOTAS` dict | block | PASS |
| True positive | `TIMEOUT_SECONDS = 30` | block | PASS |
| Escape hatch | `# verified:` on prev line | allow | PASS |
| Escape hatch | `# verified:` same line | allow | PASS |
| Escape hatch | `# ESTIMATED ... Verify via:` | allow | PASS |
| Escape hatch | `# ESTIMATED` on dict-open line | allow | PASS |
| True negative | `width = 200` / `range(200)` | allow | PASS |
| True negative | `META = {"version": 2}` | allow | PASS |
| True negative | `PI_APPROX = 3.14159` | allow | PASS |
| FP mitigation | `MAX_RETRIES = 3 # verified: dev default` | allow | PASS |
| FP mitigation | non-config file path | allow (scope gate) | PASS |
| Contract | block → exit 2 + deny JSON | exit 2 | PASS |
| Contract | non-config file → exit 0 | exit 0 | PASS |
| Contract | verified write → exit 0 | exit 0 | PASS |
| Contract | `search_replace` new_string → block | exit 2 | PASS |
| Contract | garbage stdin → fail-open | exit 0 | PASS |

## 9. Falsifier

This design is wrong if:
- **Friction outweighs benefit** — the block fires so often on legitimate
  developer-chosen constants that operators disable it. Measurable: count of
  deny events per session that were *not* a genuine unverified-external
  constant. If this is high, narrow the vocabulary or tighten the scope gate.
- **The annotation becomes a rubber stamp** — agents add `# ESTIMATED`
  reflexively without ever upgrading to `# verified:`. Measurable: ratio of
  ESTIMATED vs verified annotations in committed config files over time.
- **A better mechanism exists** — e.g. transcript-scan receipt detection
  (§4 future enhancement) proves materially better than inline annotation.
  Upgrade then.

## 10. Limitations & future work

- **Receipt is an assertion, not a proof.** `# verified:` asserts a receipt
  exists; the hook cannot confirm the cited command was actually run. This is a
  deliberate trade-off: perfect verification requires transcript access, which
  is fragile; the inline contract makes provenance visible and auditable.
- **Detection is regex-based, not AST-based.** Sufficient for config dicts and
  module constants; could miss unusual formatting. An AST pass (`ast.parse`)
  would be more precise but slower and more brittle on partial/invalid code
  (writes often contain incomplete snippets). Regex is the right v1 choice.
- **Scope is file-name based.** A `POOLS = {...}` in a non-config file is not
  inspected. Broaden `CONFIG_FILE_PATTERNS` if this proves a gap.
- **Future: transcript-scan receipt.** If `~/.grok/sessions/<id>` parsing
  stabilizes, a secondary check could confirm `# verified:` claims against
  actual prior tool output, catching rubber-stamp annotations.
