# Operational Safety (conditional reference)

**Loaded when:** any of these triggers fire:
- `detect_destructive_write_without_read` any severity
- `detect_tool_result_secret_exposure` any severity (renamed from `detect_secret_exposure` in Phase 2)
- `detect_user_paste_secret_warning` any severity (new in Phase 2)
- `detect_file_edit_reversals` HIGH severity
- Session involves an active incident (user reports data loss, secret exposure, destructive mutation, credential rotation)
- Severity asymmetry applies (Rule 3a in SKILL.md core fires)

**Authority for:** severity asymmetry details, containment vs recovery vs prevention distinction, destructive-write detection interpretation, secret-exposure detection interpretation, incident-response framing.

**Not authority for:** the severity-asymmetry rule itself (1 line in SKILL.md core Rule 3a); the containment distinction (1 line in SKILL.md core Rule 3b); detector implementation (`__lib/detectors.py` owns that).

---

## Severity asymmetry (Rule 3a expansion)

Destructive mutation, data loss, secret exposure, and unsafe recommendations are categorically more severe than CSS defects, variable-count errors, or cosmetic issues. The highest-impact findings must dominate the summary and dispositions.

Use the `destructive_write_without_read`, `tool_result_secret_exposure`, and `user_paste_secret_warning` HIGH-severity signals as forcing functions — if any fires, it is the headline finding until explicitly displaced by evidence.

## Containment vs recovery vs prevention (Rule 3b expansion)

When the session involves an active incident (data loss, secret exposure, destructive mutation), the report must distinguish:

- **Containment**: what must be done RIGHT NOW to limit damage (rotate credential, invalidate dependent output, verify no persistent leak).
- **Recovery**: what must be done to restore lost state (reconstruct .env from backup, restore deleted files).
- **Prevention**: what longer-term improvement should stop recurrence (add read-before-write preflight, add secret-safe diagnostic output).

`ACT_NOW` disposition covers containment and recovery. Do NOT turn an active incident into only a future improvement candidate.

## Destructive-write detection interpretation

For `detect_destructive_write_without_read`:

**What it mechanically proves:** a high-risk path was written without ANY observed prior read of the same path.

**What it only suggests:** that the write was destructive (the file may not have existed; contents may have been known from context).

**High-risk filename list** (`_HIGH_RISK_WRITE_PATHS` in `__lib/detectors.py`) defines a candidate set, not the risk itself. An existing non-empty file outside the list is NOT covered — the detector cannot see "existing non-empty" without a prior read.

**Replace / append / patch / delete semantics are NOT distinguished.** The detector fires on any of them.

**Suggested interpretation in synthesis:**
- Treat the signal as `POTENTIAL_DESTRUCTIVE_WRITE_WITHOUT_OBSERVED_INSPECTION` in the LLM's narrative.
- Only label as actual destructive replacement when independent evidence (file size delta, backup comparison, user report) confirms.

## Secret-exposure detection interpretation

For `detect_tool_result_secret_exposure` (Phase 2 rename of `detect_secret_exposure`) and `detect_user_paste_secret_warning` (new in Phase 2):

**Provenance classification (Phase 2 design):**

| Source path | Meaning |
|---|---|
| `USER_PASTED` | The user pasted a live credential into the conversation |
| `TOOL_RETURNED` | A tool result exposed a credential (e.g. cat .env, echo $TOKEN) |
| `ASSISTANT_REPEATED` | The assistant echoed or repeated a credential in its own text |
| `WRITTEN_TO_FILE` | A credential was written to a file (write tool, diff) |
| `SOURCE_INSUFFICIENT` | Source representation cannot determine exposure path |

**Non-leaking guarantee:** the detector never serializes the matched secret value. The signal carries only:
- a redacted fingerprint (first 4 chars + `…` + last 2 chars + sha256-prefix-8)
- the source classification
- the event index

## Incident-response framing

When an active incident is detected, the report must address in this order:

1. **Containment actions** (URGENT)
2. **Recovery actions**
3. **Exposure assessment** (was the credential newly exposed, already visible, persisted elsewhere?)
4. **Credential rotation decision** (justified when exposure is confirmed and the credential is live)
5. **Future prevention**

Do not let prevention displace containment in the summary.

## Cross-reference

- Severity definitions: see `event_model.py`
- Destructive-write rule in core: see SKILL.md core Rule 3a/3b
- Detector implementation: see `__lib/detectors.py`
- Secret-matching engine (Phase 2): see `__lib/secret_engine.py`
