"""
Lazy Closure Detector - Catches work avoidance and premature task closure.

Detects patterns where the LLM minimizes work or closes tasks without verification:
- "current approach is appropriate" (lazy justification)
- "built-in verification" (assumed mechanism)
- "administrative acknowledgment" (work avoidance framing)
- "agents follow X" (assumed compliance without verification)

PRINCIPLE: The LLM knows if it actually verified or just wants to close the task.
           Work avoidance patterns indicate insufficient effort.

Topic-scoped investigation checking is shared with PreToolUse_user_delegation_gate
via __lib/anti_lazy_policy.py — both modules import from the same canonical source.

Usage:
    from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

    result = detect_lazy_closure(response_text)
    if result:
        print(f"Detected: {result.pattern_type} -> {result.suggestion}")
"""

import json
import os
import re
import time
from pathlib import Path
from typing import NamedTuple

from quote_exemption import is_inside_quoted_content as _is_inside_quoted_content  # shared module
from __lib.anti_lazy_policy import check_investigation_in_ledger, check_topic_relevant_investigation

__all__ = ["detect_lazy_closure", "detect_all_lazy_closure", "LazyClosureMatch"]

# State for sycophancy_capitulation escalation — time-windowed.
# Rationale: the previous consecutive-counter design reset between user
# corrections, so multi-turn challenges never escalated. A 10-minute window
# with threshold 2 captures the actual failure mode: the user pushes back,
# the model agrees without verifying, user pushes back again, model agrees
# again — that second agreement within the window escalates.
_CAPITULATION_STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
_ESCALATION_WINDOW_S = 600  # 10 minutes
_ESCALATION_COUNT = 2       # 2 capitulations in window = escalate


def _get_terminal_id() -> str:
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def _capitulation_state_path() -> Path:
    # Terminal-scoped to prevent cross-terminal contamination (also makes
    # tests independent — each test can use a unique CLAUDE_TERMINAL_ID).
    tid = _get_terminal_id()
    return _CAPITULATION_STATE_DIR / f"lazy_closure_capitulation_{tid}.json"


def _load_capitulation_state() -> dict:
    path = _capitulation_state_path()
    if not path.exists():
        return {"timestamps": [], "updated_at": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Back-compat: old format had {"count": N}; treat as no history.
        if "timestamps" not in data:
            return {"timestamps": [], "updated_at": data.get("updated_at", 0)}
        return data
    except (OSError, json.JSONDecodeError):
        return {"timestamps": [], "updated_at": 0}


def _save_capitulation_state(state: dict) -> None:
    path = _capitulation_state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")
    except OSError:
        pass


def _check_capitulation_escalation() -> bool:
    """Return True if sycophancy_capitulation should escalate to block.

    Uses a sliding time window. Records the current capitulation timestamp,
    prunes entries older than _ESCALATION_WINDOW_S, and returns True when
    the count within the window reaches _ESCALATION_COUNT.

    Unlike the previous consecutive-counter design, this survives
    user-correction interleaving — a multi-turn challenge where the user
    pushes back between capitulations still escalates correctly.
    """
    state = _load_capitulation_state()
    now = int(time.time())
    cutoff = now - _ESCALATION_WINDOW_S
    timestamps = [t for t in state.get("timestamps", []) if t > cutoff]
    timestamps.append(now)
    _save_capitulation_state({"timestamps": timestamps, "updated_at": now})
    return len(timestamps) >= _ESCALATION_COUNT


def reset_capitulation_counter() -> None:
    """Clear the capitulation history.

    Kept for back-compat with any external caller. The time-window design
    no longer needs explicit resets — old entries expire naturally — but
    callers that want a hard reset (e.g., new session boundary) can use this.
    """
    try:
        _save_capitulation_state({"timestamps": [], "updated_at": int(time.time())})
    except OSError:
        pass


# _check_investigation_in_ledger() and _check_topic_relevant_investigation() are
# imported from __lib.anti_lazy_policy — canonical source shared with
# PreToolUse_user_delegation_gate.py. The shared module uses importlib.util to
# load the ledger, compatible with both in-process (Stop) and subprocess (PreToolUse)
# contexts. The noise word list, keyword extraction, and scoring logic are identical
# across both enforcement points.


class LazyClosureMatch(NamedTuple):
    """Detection result with remediation guidance."""

    matched: str  # The problematic phrase
    pattern_type: (
        str  # "lazy_justification" | "assumed_mechanism" | "work_avoidance" | "assumed_compliance"
        # | "sycophancy_capitulation"
    )
    suggestion: str  # How to fix it
    severity: str  # "flag" (warn) or "block" (reject)


# === PATTERN CATEGORIES ===

# Lazy justification - claiming something is fine without evidence
LAZY_JUSTIFICATION_PHRASES = [
    r"\bis\s+appropriate\b",
    r"\bis\s+sufficient\b",
    r"\bis\s+adequate\b",
    r"\bworks\s+fine\b",
    r"\bno\s+issues\b",
    r"\bno\s+problems\b",
    r"\bno\s+concerns\b",
    r"\bshould\s+be\s+fine\b",
    r"\blooks\s+good\b",
    r"\bseems\s+correct\b",
    # Premature closure shortcuts
    r"\blgtm\b",
    r"\bshipit\b",
    r"\bship\s+it\b",
    r"\beverything\s+(?:looks?|seems?)\s+(?:fine|good|correct)\b",
    r"\bi\s+don'?t\s+see\s+(?:any\s+)?(?:issues?|problems?)\b",
]

# Exemptions: phrases where "appropriate/sufficient" is properly hedged by context.
# These must appear BEFORE the claim (not after) to exempt.
_LAZY_JUSTIFICATION_EXEMPT = [
    re.compile(r, re.I) for r in [
        # "After [evidence], [claim]" — evidence precedes the evaluation
        r"after\s+(?:testing|review|checking|verifying|inspecting|examining)\b.*\bis\s+appropriate\b",
        r"after\s+(?:testing|review|checking|verifying|inspecting|examining)\b.*\bis\s+sufficient\b",
        r"after\s+(?:testing|review|checking|verifying|inspecting|examining)\b.*\bis\s+adequate\b",
        # "Based on [evidence], [claim]" — evidence precedes the evaluation
        r"based\s+on\s+[^.]*\b(?:testing|review|check|verification|output|result)[^.]*\bis\s+appropriate\b",
        r"based\s+on\s+[^.]*\b(?:testing|review|check|verification|output|result)[^.]*\bis\s+sufficient\b",
        # "Given [evidence], [claim]" — evidence precedes the evaluation
        r"given\s+[^.]*\b(?:testing|review|check|verification|output|result|evidence)[^.]*\bis\s+appropriate\b",
        r"given\s+[^.]*\b(?:testing|review|check|verification|output|result|evidence)[^.]*\bis\s+sufficient\b",
        # "[Claim], which is [evaluation]" — claim first, evaluation is descriptor (not a bare claim)
        r"\bit\s+is\s+appropriate\b.*\bfor\b",
        r"\bit\s+is\s+sufficient\b.*\bfor\b",
    ]
]

# Assumed mechanism - claiming something exists/works without verification
ASSUMED_MECHANISM_PHRASES = [
    r"\bbuilt-in\s+(?:verification|validation|checking|mechanism)\b",
    r"\balready\s+handles\b",
    r"\bautomatically\s+(?:handles|verifies|validates|checks)\b",
    r"\bnatively\s+supports\b",
    r"\bhas\s+built-in\b",
    r"\binherently\s+(?:safe|secure|correct)\b",
]

# Work avoidance - framing closure as minimal/administrative
WORK_AVOIDANCE_PHRASES = [
    r"\badministrative\s+(?:acknowledgment|closure|note|formality)\b",
    r"\bjust\s+a\s+formality\b",
    r"\broutine\s+(?:closure|acknowledgment)\b",
    r"\bnothing\s+(?:more\s+)?(?:to\s+do|needed|required)\b",
    r"\bmy\s+closure\s+is\b",
    r"\bthis\s+(?:completes|concludes|closes)\b(?!\s+(?:the\s+)?(?:implementation|fix|feature))",
]

# Assumed compliance - claiming others follow patterns without verification
ASSUMED_COMPLIANCE_PHRASES = [
    r"\bagents?\s+follow[s]?\b",
    r"\bworkflow[s]?\s+(?:ensure|guarantee|handle)\b",
    r"\bprocess\s+(?:ensures|guarantees|handles)\b",
    r"\bsystem\s+(?:ensures|guarantees|handles)\b",
    r"\bframework\s+(?:ensures|guarantees|handles)\b",
]

# Lazy fix language - proposes superficial fixes over proper solutions
LAZY_FIX_PHRASES = [
    r"\bquick\s+fix\b",
    r"\bsimple\s+(?:fix|patch|edit)\b",
    r"\b\d+-line\s+(?:fix|edit|change)\b",  # "5-line fix"
    r"\b(?:let'?s?\s+|just\s+|simply\s+)?bypass(?:es)?\s+(?:the\s+)?(?:issue|problem|whole\s+\w+)\b",
    r"\bbypassing\s+(?:the\s+)?(?:issue|problem|validation|check)\b",
    r"\b(?:a|the|this|quick|simple)\s+workaround\b",
    r"\bpropose\s+(?:a\s+)?workaround\b",
    r"\buse\s+(?:a\s+)?workaround\b",
    r"\bimplement\s+(?:a\s+)?workaround\b",
    r"\bregardless\s+of\b",  # "regardless of task name" - ignoring design
    # removed: false-positive rate too high when analyzing existing fixes
    # "workaround" patterns already cover the same intent with fewer FP.
    r"\bjust\s+(?:add|patch|fix|use)\b",
    r"\beasier\s+to\s+just\b",
]

# Verifiable state claims — asserting env var / feature flag / config state without checking.
# Pattern: "you likely haven’t set SDLC_MULTI_LLM=1", "X is probably not enabled"
# These are ALWAYS checkable with one Bash/os.environ call. Assert only after verifying.
#
# Two-tier approach (per regex-alternatives-reference.md):
#   - Frozenset for literal anchor phrases: no backtracking, no \b issues, O(n*|phrases|)
#   - Regex only where structure is genuinely needed (variable word in middle, or prefix noun)
#   Dropped: "probably not set/enabled/configured" — too broad, fires on design-discussion prose.

# Tier A: literal substrings — specific enough that they only appear in runtime-state assertions.
# Both straight (U+0027) and curly (U+2019) apostrophe variants; matching runs on lowercased text.
_H = "haven't"   # straight apostrophe U+0027
_HC = "haven’t"  # right single quotation mark U+2019 (common in chat/IDE output)
VERIFIABLE_STATE_CLAIM_ANCHORS = frozenset([
    f"likely {_H} set",          f"likely {_HC} set",
    f"probably {_H} set",        f"probably {_HC} set",
    f"likely {_H} enabled",      f"likely {_HC} enabled",
    f"probably {_H} enabled",    f"probably {_HC} enabled",
    f"likely {_H} configured",   f"likely {_HC} configured",
    f"probably {_H} configured", f"probably {_HC} configured",
    f"likely {_H} activated",    f"likely {_HC} activated",
    f"probably {_H} activated",  f"probably {_HC} activated",
    f"likely {_H} defined",      f"likely {_HC} defined",
    f"probably {_H} defined",    f"probably {_HC} defined",
])

# Tier B: structural regex — variable word in middle or explicit noun prefix required.
VERIFIABLE_STATE_CLAIM_PATTERNS = [
    # "you probably don’t have DEBUG set/enabled" — variable noun between have…set
    r"\b(?:you\s+)?(?:likely|probably)\s+(?:don['‘’]?t|do\s+not)\s+have\s+\w+\s+(?:set|enabled|configured)\b",
    # "the environment variable / feature flag / setting is likely not set"
    r"\b(?:env(?:ironment)?\s+var(?:iable)?|feature\s+flag|setting|config(?:uration)?)\s+(?:is\s+)?(?:likely|probably)\s+(?:not\s+)?(?:set|enabled|configured|active)\b",
]

# User delegation - asking user to fetch info Claude can get with tools
# Pattern: "Can you show me the log output" / "look for lines containing X"
USER_DELEGATION_PHRASES = [
    r"\bcan\s+you\s+(?:show|share|paste|provide)\s+(?:me\s+)?the\s+(?:log|output|file|content|result|error)",
    r"\bcould\s+you\s+(?:show|share|paste|provide)\s+(?:me\s+)?(?:the\s+)?(?:log|output|file|content|error)",
    r"\bplease\s+(?:share|paste|show|provide)\s+(?:the\s+)?(?:log|output|error|result)s?\b",
    r"\bshow\s+me\s+the\s+(?:log|output|error|result|content)s?\b",
    r"\bspecifically.*look\s+for\s+lines?\s+containing\b",
    r"\blook\s+for\s+lines?\s+containing\b",
]

# Premature offer - volunteering to implement before understanding
# Premature offer - volunteering to implement before understanding.
# Distinguishes: "Shall I proceed?" (confirmation-seeking, legitimate) vs
# "Want me to implement?" (offering to start without authorization, problematic).
# Pattern: offer that lacks user authorization signal AND lacks prior Skill() loading.
PREMATURE_OFFER_PHRASES = [
    r"\bwant\s+me\s+to\s+(?:do|implement|fix|try)\s+it\b",
    r"\bshould\s+I\s+(?:implement|do|fix)\s+(?:it|this|that)\b",
    r"\bI\s+can\s+(?:quickly|easily)\s+(?:fix|implement|add)\b",
    r"\blet\s+me\s+(?:just|quickly)\s+(?:fix|implement|add)\b",
    r"\bshall\s+I\s+(?:implement|fix)\b",  # "Shall I implement/fix" — offer, not question
    r"\bdo\s+you\s+want\s+me\s+to\s+(?:implement|do|fix)\b",  # explicit offer
]
# "Shall I proceed?" is confirmation-seeking — NOT premature (legitimate after design complete)

# Literalist framing - model treats the request as a strict, narrow spec and closes
# without volunteering the obvious next step. "That's the extent of what you asked"
# followed by no diagnosis = passive refusal to be useful.
LITERALIST_FRAMING_PHRASES = [
    r"that's\s+the\s+extent\s+of\s+what\s+you\s+asked",
    r"that's\s+all\s+you\s+asked\s+(?:for\s+)?",
    r"that's\s+what\s+you\s+asked\s+(?:for\s+)?",
    r"that's\s+the\s+(?:whole|entire)\s+request",
]

# Status-quo defense — fabricating architectural rationale for why something is the way it is
# without reading design docs, git history, or ADRs. Patterns: "here's why X", "because of Y"
# followed by confident placement justification. Exempted when evidence/verification markers present.
STATUS_QUO_DEFENSE_PHRASES = [
    r"\bthey\s+belong\s+where\s+they\s+are\b",
    r"\b(?:it|they|this|that)\s+belong[s]?\s+(?:here|there|in\s+(?:this|that)\s+(?:directory|folder|location))\b",
    r"\bhere'?s\s+why\s+(?:they'?re|it'?s|that'?s)\s+(?:there|here|in)\b",
    r"\bconvenience\s+and\s+discoverability\b",
    r"\b(?:there|here|placed|kept|put)\s+(?:for|because\s+of)\s+(?:convenience|discoverability|simplicity|historical\s+reasons)\b",
    r"\bthe\s+(?:reason|rationale)\s+(?:is|was)\s+(?:simply|just|because)\b",
    r"\bit\s+(?:makes?\s+sense|is\s+(?:natural|logical|intuitive))\s+(?:to\s+(?:keep|put|place|have)\s+(?:them|it|this|that)\s+(?:here|there|in))\b",
]

# Universal absence claims — asserting X doesn't exist anywhere based on a limited search scope.
# Catches "It's not on disk anywhere" after only searching one directory, or
# "doesn't exist anywhere" when only one source was checked.
# Exempted when VERIFICATION_MARKERS or EVIDENCE_MARKERS are present (meaning the LLM
# actually documented what it searched before making the claim).
UNIVERSAL_ABSENCE_PHRASES = [
    r"\bnot\s+(?:found\s+)?anywhere\b",                      # "not anywhere", "not found anywhere"
    r"\bnot\s+on\s+disk\s+anywhere\b",                       # "not on disk anywhere"
    r"\bdoesn'?t\s+exist\s+anywhere\b",                      # "doesn't exist anywhere"
    r"\bnowhere\s+(?:in|on)\s+(?:disk|the\s+\w+|this\b)",   # "nowhere on disk", "nowhere in the repo"
    r"\bnot\s+(?:tracked|cached|registered|stored)\s+anywhere\b",  # "not cached anywhere"
    r"\bno\s+(?:file|entry|record|match)\s+anywhere\b",      # "no file anywhere"
]

# Declaration without execution patterns - saying "I'll do X" without follow-through
DECLARATION_PATTERNS = [
    r"\bi'll\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bi'd\s+(?:like to|love to|want to|going to)\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bi\s+(?:will|shall|going to)\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\blet\s+me\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bi'm\s+(?:going to|planning to|will)\s+(?:update|edit|modify)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bi\s+should\s+(?:update|edit|modify)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bneed\s+to\s+(?:update|edit|modify)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bhave\s+to\s+(?:update|edit|modify)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
    r"\bmust\s+(?:update|edit|modify)\s+(?:the\s+)?(?:template|arch/|SKILL\.md)",
]

# Explicit debt deferral - "I'll leave that for now" without formal tracking
# Acceptable only when spawn_task or explicit tracking evidence is present.
# frozenset + substring: O(1) lookup, no \b false positives on punctuation.
DEFERRAL_PHRASES = frozenset([
    "i'll leave that for now",
    "i'll leave this for now",
    "i'll leave it for now",
    "i'll leave that for later",
    "i'll leave this for later",
    "leave that for now",
    "leave this for now",
    "leave it for now",
    "leave that for later",
    "leave this for later",
    "defer that",
    "defer this",
    "defer it",
    "deferring the fix",
    "deferring this",
    "deferring that",
    "we can address that later",
    "we can address this later",
    "we can fix that later",
    "we can fix this later",
    "we can handle that later",
    "we can handle this later",
    "can be addressed later",
    "can be fixed later",
    "can be handled later",
    "that can wait",
    "this can wait",
    "leave this as debt",
    "leave that as debt",
    "leave this as technical debt",
    "leave that as technical debt",
])

# Tracking markers that make deferral acceptable (debt formally tracked)
DEFERRAL_TRACKING_MARKERS = frozenset([
    "spawn_task",
    "side task",
    "flagged this",
    "tracked this",
    "todowrite",
    "created a task",
    "filed as",
])

# Sycophantic capitulation - agreeing with user challenge without Bash evidence
# Fires when model says "I see now" / "You're right" after a challenge, then makes
# a confident claim about external behavior — without running the actual command.
# NOTE: Only Bash execution output exempts this pattern (not Skill/Read docs).
SYCOPHANCY_CAPITULATION_PHRASES = [
    r"\bI\s+see\s+now\b",
    r"\bAh[,.]?\s+I\s+see\b",
    r"\bNow\s+I\s+(?:see|understand)\b",
    r"\bSo\s+(?:the\s+|this\s+|it\s+)?\w+\s+simply\b",
    r"\bThat\s+makes\s+sense[.—]\s+[A-Z]",
    # "You're right" with optional intensifier or continuation (not just comma/period)
    r"\bYou(?:'re|\s+are)\s+(?:absolutely\s+|completely\s+|totally\s+)?right\b",
    r"\bYou(?:'re|\s+are)\s+right\s+to\s+\w+",
    r"\bI\s+(?:mis|was\s+mis)understood\b",
    r"\bI\s+(?:was\s+)?wrong\s+about\b",
]

# Self-referential evasion — hedging about own decisions/reasoning without evidence.
# Pattern: model treats its own choices as external phenomena, not commitments it made.
# Scope guard: only flags when tools WERE used — investigation hedging is OK,
# decision evasion (claiming verified when tools exist) is not.
# "I investigated X" (no tools) + "but it might still be Y" = OK (investigation caveat)
# "I verified X" (no tools) + "but Y is also possible" = BLOCK (decision without evidence)
SELF_REFERENTIAL_EVASION_PATTERNS = [
    r"\bROOT\s+CAUSE\s+CANDIDATE\b",
    # Require an actual hedge modal within the same clause (no sentence cross via [^.]).
    # Prevents FP on injected reasoning-contract text ("hypotheses, note what would
    # confirm or falsify each. Test be...") and on "hypothesis" used as a plain
    # technical noun ("single hypothesis, no discriminating test - would now be").
    r"\bhypothes[ei]s\b[^.]{0,40}?(?:yet|still|also|may|might|could)\s+(?:be|apply|explain)\b",
    r"(?:yet|still|also)\s+(?:might|may|could)\s+(?:be|explain|apply)",
    r"(?<!`)(?<!\[)\bhedge[s]?\b(?!`)(?!\])",
    # Exclude structured-field forms (status=unverified, "status":"unverified",
    # status:unverified) and bracket/backtick-wrapped markers ([UNVERIFIED], `unverified`)
    # — these are field values, not a hedged stance claim. Bare prose 'unverified' still fires.
    r"(?<!`)(?<!\[)(?<!=)(?<!:)(?<!\")\bunverified\b(?!`)(?!\])",
    r"\b(?:this|that)\s+(?:still\s+)?(?:might|may|could)\s+(?:be|require)\b",
    r"\bruling\s+out\s+hypotheses\b",
    r"\b(?:candidate|hypothesis)\s+(?:for|of|is)\s+\w+\b",
]

# Bash-only evidence markers — these appear in actual terminal/Bash output,
# not in documentation reads or Skill() calls.
BASH_ONLY_EVIDENCE_MARKERS = frozenset(
    [
        "$ ",  # shell prompt
        "❯ ",  # zsh/fish prompt
        ">>> ",  # Python REPL
        "exit code",
        "exit_code",
        "returncode",
        "stdout:",
        "stderr:",
        "bash:",
        "subprocess",
        "command output",
        "% total",  # curl output
        "traceback (most recent",  # Python traceback = real execution
    ]
)

# Empirical behavior-claim tokens - words asserting how code/system BEHAVES (vs
# design/preference judgments). sycophancy_capitulation fires only when the agreement
# ("you're right") sits near such a claim, restoring the detector's documented design
# ("agreeing ... then makes a confident claim about external behavior"). Bare social or
# preference agreement ("you're right, Option B is cleaner") has no such token.
# Pruned 2026-06-01 (FP-replay over 51 capitulation blocks, second pass).
# Removed pure topic-words that fire on any technical discussion: "the hook",
# "the function", "the script", "the implementation", "the command", "behaves",
# "as intended". In epistemic-analysis sessions these appear as topic words in
# ~all turns within 220 chars of an agreement phrase, causing capitulation to
# fire regardless of whether a real behavioral claim was made.
# Kept: tokens that ASSERT a testable behavioral state.
# Matching uses simple substring (`tok in region`) so multi-word tokens like
# "is working" and "not a bug" require that phrase to appear as a substring.
EMPIRICAL_CLAIM_TOKENS = frozenset([
    # State-change assertions
    "fixed", "not a bug",
    # Runtime behavior assertions
    "works", "working", "is working", "doesn't work", "does not work",
    # Test outcome assertions
    "passes", "passed", "fails", "failing",
    # Function-call behavior descriptions
    "delegates", "displays", "handles",
    # REMOVED 2026-06-01 (second pass): topic words that fire on any analysis turn
    # "bug", "the fix", "behaves", "as intended", "the command", "the hook",
    # "the function", "the script", "the implementation"
])


def _has_empirical_claim_near(text: str, match: "re.Match", window: int = 220) -> bool:
    """True if an empirical behavior-claim token appears near the capitulation match.

    Window starts shortly before the match (to catch claim-then-agreement ordering)
    and runs `window` chars past it. Social/preference agreement with no behavior
    claim returns False and is not flagged.
    """
    start = max(0, match.start() - 40)
    end = min(len(text), match.end() + window)
    region = text[start:end].lower()
    # Word-boundary match: prevents substring bleed where a token is a fragment
    # of an unrelated word ("works" in "frameworks", "correctly" in "incorrectly").
    for tok in EMPIRICAL_CLAIM_TOKENS:
        if re.search(r"(?<![a-z])" + re.escape(tok) + r"(?![a-z])", region):
            return True
    return False


# Template file patterns (for validation)
TEMPLATE_FILE_PATTERNS = [
    r"template",
    r"arch/",
    r"SKILL\.md",
    r"\.md$",
]

# Evidence markers that make claims acceptable
EVIDENCE_MARKERS = frozenset(
    [
        "tier 1",
        "tier 2",
        "tier1",
        "tier2",
        "verified",
        "confirmed",
        "tested",
        "evidence:",
        "[supported]",
        "[verified]",
        "logs show",
        "output shows",
        "test shows",
    ]
)

# Verification markers that indicate actual work was done
VERIFICATION_MARKERS = frozenset(
    [
        "i ran",
        "i executed",
        "i tested",
        "i verified",
        "i read",
        "i checked",
        "running",
        "executing",
        "testing",
        "pytest",
        "test output",
        "test results",
        "checked",
        "inspected",
        "examined",
        "according to",
        "git blame",
        "git log",
        "the commit",
        "the adr",
        "design doc",
    ]
)

# Tool usage markers (Edit/Write indicates actual execution)
TOOL_USAGE_MARKERS = frozenset(
    [
        "edited",
        "updated",
        "wrote",
        "created",
        "modified",
        "edit(",
        "write(",
        "file changed",
        # Bash execution indicators — specific command/tool names that are
        # unambiguous when embedded in text (hard to fake in conversational hedges)
        "ran csf-source",
        "executed csf-source",
        "used csf-source",
        "ran the sync",
        "ran yt-is",
        "executed the command",
        "used bash",
        "csf-source sync",
        "csf-source list",
    ]
)


# Investigation/root-cause bypass phrases — suppress lazy_fix when describing/tracing
# a workaround rather than proposing one as a fix.
INVESTIGATION_BYPASS_PHRASES = [
    r"trace\s+(the\s+)?(source|cause|origin)",
    r"investigate\s+why",
    r"find\s+(the\s+)?(root\s+)?cause",
    r"identify\s+where",
    r"debug\s+(the\s+)?(issue|problem)",
    r"fix\s+(the\s+)?(underlying|root)",
    r"prevent\s+(the\s+)?duplication",
    r"(?:should|will|need to|going to|planning to)\s+(?:trace|investigate|find root|debug|identify)",
    r"(?:let me|let us|i'll|i will)\s+(?:trace|investigate|find|debug|identify)",
    r"(?:tracing|investigating|finding|debugging|identifying)\s+(?:where|why|what|how)",
]


def _has_investigation_intent(text: str) -> bool:
    """Check if text contains root-cause investigation intent (bypass for lazy_fix)."""
    return any(re.search(p, text, re.IGNORECASE) for p in INVESTIGATION_BYPASS_PHRASES)


# Compile patterns for efficiency
_LAZY_JUSTIFICATION = [re.compile(p, re.IGNORECASE) for p in LAZY_JUSTIFICATION_PHRASES]
_ASSUMED_MECHANISM = [re.compile(p, re.IGNORECASE) for p in ASSUMED_MECHANISM_PHRASES]
_WORK_AVOIDANCE = [re.compile(p, re.IGNORECASE) for p in WORK_AVOIDANCE_PHRASES]
_ASSUMED_COMPLIANCE = [re.compile(p, re.IGNORECASE) for p in ASSUMED_COMPLIANCE_PHRASES]
_LAZY_FIX = [re.compile(p, re.IGNORECASE) for p in LAZY_FIX_PHRASES]
_PREMATURE_OFFER = [re.compile(p, re.IGNORECASE) for p in PREMATURE_OFFER_PHRASES]
_LITERALIST_FRAMING = [re.compile(p, re.IGNORECASE) for p in LITERALIST_FRAMING_PHRASES]
_VERIFIABLE_STATE_CLAIM_PATTERNS = [re.compile(p, re.IGNORECASE) for p in VERIFIABLE_STATE_CLAIM_PATTERNS]
_USER_DELEGATION = [re.compile(p, re.IGNORECASE) for p in USER_DELEGATION_PHRASES]
_DECLARATION = [re.compile(p, re.IGNORECASE) for p in DECLARATION_PATTERNS]
_SYCOPHANCY_CAPITULATION = [re.compile(p, re.IGNORECASE) for p in SYCOPHANCY_CAPITULATION_PHRASES]
_SELF_REFERENTIAL_EVASION = [re.compile(p, re.IGNORECASE) for p in SELF_REFERENTIAL_EVASION_PATTERNS]
_UNIVERSAL_ABSENCE = [re.compile(p, re.IGNORECASE) for p in UNIVERSAL_ABSENCE_PHRASES]
_STATUS_QUO_DEFENSE = [re.compile(p, re.IGNORECASE) for p in STATUS_QUO_DEFENSE_PHRASES]


def _find_deferral(text_lower: str) -> str | None:
    """Return the first matched deferral phrase, or None. O(n * |phrases|) worst case
    but avoids regex backtracking and \b false positives on punctuation."""
    return next((p for p in DEFERRAL_PHRASES if p in text_lower), None)


def _has_evidence_marker(text: str) -> bool:
    """Check if text contains evidence tier citation."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in EVIDENCE_MARKERS)


def _has_verification_marker(text: str) -> bool:
    """Check if text indicates actual verification work was done."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in VERIFICATION_MARKERS)


def _has_tool_usage_marker(text: str) -> bool:
    """Check if text indicates Edit/Write tools were actually used."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in TOOL_USAGE_MARKERS)


def _has_deferral_tracking(text_lower: str) -> bool:
    """Check if deferral is acceptable because debt is formally tracked (spawn_task called).
    Expects pre-lowercased input."""
    return any(marker in text_lower for marker in DEFERRAL_TRACKING_MARKERS)


def _find_verifiable_state_claim(text_lower: str, text_original: str) -> str | None:
    """Return the first matched verifiable-state-claim phrase/pattern, or None.

    Two-tier (per regex-alternatives-reference.md):
      Tier A: frozenset literal anchors — O(n*|phrases|), no backtracking.
      Tier B: structural regex — only where a variable word or explicit prefix is needed.
    Expects pre-lowercased text for Tier A; original-case text for Tier B regex.
    """
    hit = next((p for p in VERIFIABLE_STATE_CLAIM_ANCHORS if p in text_lower), None)
    if hit:
        return hit
    for pattern in _VERIFIABLE_STATE_CLAIM_PATTERNS:
        m = pattern.search(text_original)
        if m:
            return m.group(0)
    return None



def _has_bash_evidence(text: str) -> bool:
    """Check if text contains markers from actual Bash/terminal execution.

    Stricter than _has_evidence_marker() — used for sycophancy_capitulation.
    Skill() docs and Read() output do NOT count; only shell-execution artifacts do.
    """
    text_lower = text.lower()
    return any(marker.lower() in text_lower for marker in BASH_ONLY_EVIDENCE_MARKERS)


# Markers indicating the response is a test/summary artifact, not analytical prose.
_TEST_SUMMARY_MARKERS = frozenset([
    "tests added",
    "tests pass",
    "edge cases covered",
    "files modified",
    "| file | change |",
    "test coverage",
    "test description",
    "test_",
    "def test_",
    "passed in",
])


def _is_test_summary_context(text: str) -> bool:
    """Return True if text looks like a test summary or edge-case listing.

    Used to suppress lazy_fix false positives on benign test descriptions
    like 'non-format bypasses repair' in a test coverage summary.
    """
    text_lower = text.lower()
    return any(marker in text_lower for marker in _TEST_SUMMARY_MARKERS)


def _find_pattern(text: str, patterns: list[re.Pattern]) -> re.Match | None:
    """Find first matching pattern in text."""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match
    return None


def detect_lazy_closure(
    response: str, user_prompt: str = "", has_bash_evidence: bool | None = None
) -> LazyClosureMatch | None:
    """
    Detect lazy closure and work avoidance patterns.

    Returns None if clean, LazyClosureMatch if problematic.

    Args:
        response: The assistant's response text to analyze.
        user_prompt: The user prompt (used for topic-scoped ledger check).
        has_bash_evidence: Optional explicit flag for Bash execution evidence.
                          If None, defaults to prose-based detection via _has_bash_evidence().
                          If True/False, overrides prose check for sycophancy_capitulation gate.
    """
    if not response:
        return None

    # Normalize whitespace for matching.
    # Preserve newlines so _is_inside_quoted_content() can detect blockquote/table
    # line prefixes ("> " and "| ") via rfind(newline). Collapse only horizontal whitespace.
    text = re.sub(r"[ 	]+", " ", response)

    # Deferral — "I'll leave that for now" without formal tracking is unacceptable.
    # Exemption: spawn_task was called (debt formally tracked).
    text_lower = text.lower()
    hit = _find_deferral(text_lower)
    if hit and not _has_deferral_tracking(text_lower):
        # Skip if the match phrase is inside quoted/code content — the text is
        # mentioning/explaining the phrase, not making an actual deferral claim.
        _dm = re.search(re.escape(hit), text, re.IGNORECASE)
        if not (_dm and _is_inside_quoted_content(text, _dm)):
            return LazyClosureMatch(
                matched=hit,
                pattern_type="deferral",
                suggestion=(
                    "Untracked debt detected. Either fix it now, or use spawn_task to formally "
                    "track it. 'I'll leave that for now' without tracking creates invisible debt."
                ),
                severity="flag",
            )

    # Verifiable state claims — env vars / flags / settings asserted without checking.
    # Checked unconditionally: having done other verification elsewhere doesn't excuse
    # skipping a one-line runtime check.
    hit = _find_verifiable_state_claim(text_lower, text)
    if hit:
        return LazyClosureMatch(
            matched=hit,
            pattern_type="verifiable_state_claim",
            suggestion=(
                "You asserted runtime/config state (env var, feature flag, setting) without "
                "checking it. These are always verifiable in one tool call: "
                "Bash `echo $VAR` or `python -c \"import os; print(os.environ.get('VAR'))\"`. "
                "Check first, then assert."
            ),
            severity="flag",
        )

    # User delegation is checked unconditionally — "I ran bash" earlier in the
    # response doesn't excuse asking the user to fetch information later.
    # Escalate to block if ledger shows no prior investigation before this delegation.
    match = _find_pattern(text, _USER_DELEGATION)
    if match:
        # Suppress false positives on quoted or negated forms.
        # e.g. "I won't say 'can you show me the log'" or "can't you just read it?"
        before_start = max(0, match.start() - 15)
        prefix = text[before_start:match.start()].lower()
        if any(neg in prefix for neg in ("n't", "not ", "never ", "won't", "can't", '"', "'", "`")):
            return None
        # Check if any investigation was done before this delegation.
        # Use topic-scoped check when user_prompt available to avoid stale activity false-positives.
        had_investigation = (
            check_topic_relevant_investigation(user_prompt)
            if user_prompt
            else check_investigation_in_ledger()
        )
        if not had_investigation:
            return LazyClosureMatch(
                matched=match.group(0),
                pattern_type="user_delegation",
                suggestion=(
                    "Use tools (Bash/Read/Grep/Glob) to get this information yourself. "
                    "Don't ask the user to fetch it. "
                    "No prior investigation detected — use investigative tools before delegating to user."
                ),
                severity="block",
            )
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="user_delegation",
            suggestion="Use tools (Bash/Read/Grep/Glob) to get this information yourself. Don't ask the user to fetch it.",
            severity="block",
        )

    # Sycophancy capitulation — checked before the general evidence exemption,
    # because only Bash execution output (not Skill/Read docs) clears this pattern.
    # Also exempted when the match falls inside quoted content (code blocks,
    # blockquotes) to prevent false positives from cited transcript evidence.
    match = _find_pattern(text, _SYCOPHANCY_CAPITULATION)
    _bash_ok = has_bash_evidence if has_bash_evidence is not None else _has_bash_evidence(text)
    if (
        match
        and not _bash_ok
        and not _is_inside_quoted_content(text, match)
        and _has_empirical_claim_near(text, match)
    ):
        escalated = _check_capitulation_escalation()
        if escalated:
            return LazyClosureMatch(
                matched=match.group(0),
                pattern_type="sycophancy_capitulation",
                suggestion=(
                    "You agreed with a challenge ('I see now', 'you're right') without "
                    "running the actual command. Reading docs or SKILL.md does NOT count as "
                    "evidence. Run the disputed behavior with Bash first, then agree or "
                    "disagree based on real output.\n\n"
                    "This is your 2nd+ capitulation within 10 minutes. You must execute "
                    "Bash verification before conceding any claim."
                ),
                severity="block",
            )
        else:
            return LazyClosureMatch(
                matched=match.group(0),
                pattern_type="sycophancy_capitulation",
                suggestion=(
                    "You agreed with a challenge ('I see now', 'you're right') without "
                    "running the actual command. Reading docs or SKILL.md does NOT count as "
                    "evidence. Run the disputed behavior with Bash first, then agree or "
                    "disagree based on real output."
                ),
                # 2026-07-04: demoted block->flag; measured 80% FP rate on 7-day
                # corpus (P:/__csf/.staging/fp_labels_summary.md). Challenge-active
                # capitulation still blocks via StopHook_unverified_stance escalation.
                severity="flag",
            )

    # Self-referential evasion — model treats its own decisions/reasoning as
    # external phenomena rather than commitments it made.
    # Scope guard: only flags when tools WERE used — this distinguishes:
    #   OK:    "I should investigate X" + no tools used = investigation hedge
    #   BLOCK: "I verified X" + no tools used + "but might still be Y" = decision evasion
    match = _find_pattern(text, _SELF_REFERENTIAL_EVASION)
    if match and _has_tool_usage_marker(text) and not _is_inside_quoted_content(text, match):
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="self_referential_evasion",
            suggestion=(
                "You are hedging about your own reasoning or decisions as if they were "
                "external phenomena. Either: (1) State what you actually verified or "
                "decided — 'I did not verify X' or 'I decided Y based on Z' — or "
                "(2) If you genuinely have not verified something, say so plainly without "
                "framing it as competing hypotheses or unverified candidates."
            ),
            # 2026-07-04: demoted block->flag; 2 FP / 0 TP on 7-day corpus
            # (P:/__csf/.staging/fp_labels_summary.md) — matched bare word
            # 'unverified' inside reported/quoted prose.
            severity="flag",
        )

    # If evidence or verification markers present, other patterns are acceptable
    if _has_evidence_marker(text) or _has_verification_marker(text):
        return None

    # Declaration patterns: Only problematic if NOT followed by actual tool usage
    # "I'll update the template" is OK if Edit/Write tools were actually used
    match = _find_pattern(text, _DECLARATION)
    if match:
        # Allow if tools were used (this is actual execution, not lazy declaration)
        if _has_tool_usage_marker(text):
            return None
        # Block/flag if declaration without tool execution
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="declaration",
            suggestion="You declared an intent to edit a template/file but didn't execute it. "
            "Use Edit or Write tools now to complete the action, or remove the declaration.",
            severity="flag",
        )

    # 1. Check for work avoidance (most severe)
    match = _find_pattern(text, _WORK_AVOIDANCE)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="work_avoidance",
            suggestion="Closure requires verification. What specific checks confirm this is complete?",
            severity="flag",
        )

    # 2. Check for assumed mechanism
    match = _find_pattern(text, _ASSUMED_MECHANISM)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="assumed_mechanism",
            suggestion="Verify the mechanism exists. Where is it implemented? Does it actually work?",
            severity="flag",
        )

    # 3. Check for assumed compliance
    match = _find_pattern(text, _ASSUMED_COMPLIANCE)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="assumed_compliance",
            suggestion="Did you verify compliance or assume it? Check actual behavior, not intended design.",
            severity="flag",
        )

    # 4. Check for lazy justification
    # Exempted: "After testing, X is appropriate" (evidence precedes evaluation)
    match = _find_pattern(text, _LAZY_JUSTIFICATION)
    if match:
        if any(p.search(text) for p in _LAZY_JUSTIFICATION_EXEMPT):
            pass  # Exempted — evidence context precedes the claim
        else:
            return LazyClosureMatch(
                matched=match.group(0),
                pattern_type="lazy_justification",
                suggestion="'Appropriate/sufficient' claims need evidence. What specifically makes it so?",
                severity="flag",
            )

    # 5. Check for lazy fix language (skip in test-summary or investigation context)
    match = _find_pattern(text, _LAZY_FIX)
    if match and not _is_test_summary_context(text) and not _has_investigation_intent(text):
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="lazy_fix",
            suggestion="Lazy fix detected. Does this address root cause or just patch symptoms?",
            severity="flag",
        )

    # 6. Check for premature offer - only premature when NO prior investigation.
    # Offering to implement AFTER investigation is the correct authorization-seeking
    # step (CLAUDE.md: "state what you plan to change and wait for confirmation"), not
    # lazy closure. Reuses the same ledger check as user_delegation.
    match = _find_pattern(text, _PREMATURE_OFFER)
    if match:
        had_investigation = (
            check_topic_relevant_investigation(user_prompt)
            if user_prompt
            else check_investigation_in_ledger()
        )
        if not had_investigation:
            return LazyClosureMatch(
                matched=match.group(0),
                pattern_type="premature_offer",
                suggestion="Offering to implement before understanding. Have you completed Investigation Gate?",
                severity="flag",
            )

    # 7. Check for literalist framing - "that's the extent of what you asked" with no diagnosis
    match = _find_pattern(text, _LITERALIST_FRAMING)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="literalist_framing",
            suggestion=(
                "You framed the request as a strict narrow spec and stopped without "
                "naming the root cause or obvious next step. If you see a diagnosis or "
                "likely follow-up, volunteer it in one line."
            ),
            severity="flag",
        )

    # 8. Check for universal absence claims — "not on disk anywhere", "not found anywhere"
    # These are suspicious when only a subset of locations was searched.
    # Exempted: response contains verification markers (LLM documented what was searched).
    match = _find_pattern(text, _UNIVERSAL_ABSENCE)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="universal_absence",
            suggestion=(
                "Universal absence claim without documented search scope. "
                "Before asserting 'not anywhere', verify you searched ALL relevant locations. "
                "For Claude Code entities: check both the project directory AND ~/.claude/ "
                "(commands/, plugins/, etc.). State which directories were searched."
            ),
            severity="flag",
        )

    # 9. Check for status-quo defense — fabricating rationale for why something exists
    # where it does without reading design docs, git history, or ADRs.
    match = _find_pattern(text, _STATUS_QUO_DEFENSE)
    if match:
        return LazyClosureMatch(
            matched=match.group(0),
            pattern_type="status_quo_defense",
            suggestion=(
                "You fabricated architectural rationale without evidence. "
                "Before explaining WHY something is where it is, read git log/blame, "
                "design docs, or ADRs. If no rationale exists, say so plainly instead "
                "of inventing 'convenience' or 'discoverability' justifications."
            ),
            severity="block",
        )

    return None


def detect_all_lazy_closure(response: str, user_prompt: str = "") -> list[LazyClosureMatch]:
    """
    Detect ALL lazy closure patterns (not just first).

    Useful for comprehensive analysis.

    Args:
        response: The assistant's response text to analyze.
        user_prompt: The user prompt (used for topic-scoped ledger check).
    """
    if not response:
        return []

    results = []
    # Preserve newlines so _is_inside_quoted_content() can detect blockquote/table
    # line prefixes. See detect_lazy_closure() for the same rationale.
    text = re.sub(r"[ 	]+", " ", response)

    # Deferral — untracked debt is always flagged unless spawn_task was called.
    text_lower = text.lower()
    if not _has_deferral_tracking(text_lower):
        for phrase in DEFERRAL_PHRASES:
            if phrase in text_lower:
                results.append(
                    LazyClosureMatch(
                        matched=phrase,
                        pattern_type="deferral",
                        suggestion="Fix it now or use spawn_task to track it. Untracked debt is invisible.",
                        severity="flag",
                    )
                )

    # Verifiable state claims run unconditionally — same rationale as user delegation.
    hit = _find_verifiable_state_claim(text_lower, text)
    if hit:
        results.append(
            LazyClosureMatch(
                matched=hit,
                pattern_type="verifiable_state_claim",
                suggestion="Check runtime state with a tool call before asserting it.",
                severity="flag",
            )
        )

    # User delegation runs unconditionally — verification markers elsewhere don't excuse it.
    # Use topic-scoped check when user_prompt available to avoid stale activity false-positives.
    had_investigation_all = (
        check_topic_relevant_investigation(user_prompt)
        if user_prompt
        else check_investigation_in_ledger()
    )
    for pattern in _USER_DELEGATION:
        for match in pattern.finditer(text):
            if not had_investigation_all:
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type="user_delegation",
                        suggestion=(
                            "Use tools (Bash/Read/Grep/Glob) to get this information yourself. "
                            "Don't ask the user to fetch it. "
                            "No prior investigation detected — use investigative tools before delegating to user."
                        ),
                        severity="block",
                    )
                )
            else:
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type="user_delegation",
                        suggestion="Use tools (Bash/Read/Grep/Glob) to get this information yourself. Don't ask the user to fetch it.",
                        severity="block",
                    )
                )

    # Sycophancy capitulation — only Bash evidence (not Skill/Read docs) exempts this.
    if not _has_bash_evidence(text):
        for pattern in _SYCOPHANCY_CAPITULATION:
            for match in pattern.finditer(text):
                if not _has_empirical_claim_near(text, match):
                    continue
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type="sycophancy_capitulation",
                        suggestion="Run the disputed behavior with Bash before agreeing.",
                        # 2026-07-04: demoted block->flag (see single-detect path)
                        severity="flag",
                    )
                )

    # Self-referential evasion — only when tools were used (scope guard)
    if _has_tool_usage_marker(text):
        for pattern in _SELF_REFERENTIAL_EVASION:
            for match in pattern.finditer(text):
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type="self_referential_evasion",
                        suggestion=(
                            "Frame your own reasoning as your commitment, not an external "
                            "phenomenon. Either state what you verified/didn't verify, or "
                            "say plainly without hedging phrases like 'candidate' or "
                            "'hypothesis'."
                        ),
                        # 2026-07-04: demoted block->flag (see single-detect path)
                        severity="flag",
                    )
                )

    # Other patterns are acceptable if evidence/verification markers are present
    if _has_evidence_marker(text) or _has_verification_marker(text):
        return results

    # Declaration patterns: Check but only flag if NO tool usage markers present
    # "I'll update the template" is OK if Edit/Write tools were actually used
    has_tool_usage = _has_tool_usage_marker(text)
    for pattern in _DECLARATION:
        for match in pattern.finditer(text):
            if not has_tool_usage:  # Only flag if no tools were used
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type="declaration",
                        suggestion="You declared an intent to edit but didn't execute. Use Edit/Write tools now.",
                        severity="flag",
                    )
                )

    pattern_groups = [
        (_WORK_AVOIDANCE, "work_avoidance", "Closure requires verification", "flag"),
        (_ASSUMED_MECHANISM, "assumed_mechanism", "Verify mechanism exists", "flag"),
        (_ASSUMED_COMPLIANCE, "assumed_compliance", "Verify actual compliance", "flag"),
        (_LAZY_JUSTIFICATION, "lazy_justification", "Provide specific evidence", "flag"),
        (_LAZY_FIX, "lazy_fix", "Address root cause, not symptoms", "flag"),
        (_PREMATURE_OFFER, "premature_offer", "Complete Investigation Gate first", "flag"),
        (_LITERALIST_FRAMING, "literalist_framing", "Name the root cause or next step unprompted", "flag"),
        (_UNIVERSAL_ABSENCE, "universal_absence", "State which directories/sources were searched before claiming universal absence", "flag"),
        (_STATUS_QUO_DEFENSE, "status_quo_defense", "Read git log/blame or design docs before explaining WHY something exists where it does", "block"),
    ]

    for patterns, pattern_type, base_suggestion, severity in pattern_groups:
        # Suppress lazy_fix when investigation intent is present (false positive on tracing/root-cause language)
        if pattern_type == "lazy_fix" and _has_investigation_intent(text):
            continue
        for pattern in patterns:
            for match in pattern.finditer(text):
                results.append(
                    LazyClosureMatch(
                        matched=match.group(0),
                        pattern_type=pattern_type,
                        suggestion=base_suggestion,
                        severity=severity,
                    )
                )

    return results


# === Inline tests (run with: python -m anti_sycophancy.lazy_closure_detector) ===
if __name__ == "__main__":
    # Should detect (lazy patterns)
    assert detect_lazy_closure("The current approach is appropriate for this context") is not None
    assert detect_lazy_closure("Agents follow TDD workflow with built-in verification") is not None
    assert detect_lazy_closure("My closure is administrative acknowledgment") is not None
    assert detect_lazy_closure("The system already handles this case") is not None
    assert detect_lazy_closure("This should be fine for production") is not None
    assert detect_lazy_closure("The framework ensures correctness") is not None
    assert detect_lazy_closure("Nothing more to do here") is not None
    # New premature closure patterns
    assert detect_lazy_closure("LGTM") is not None
    assert detect_lazy_closure("shipit") is not None
    assert detect_lazy_closure("ship it") is not None
    assert detect_lazy_closure("Everything looks fine") is not None
    assert detect_lazy_closure("I don't see any issues") is not None
    assert detect_lazy_closure("I dont see any problems") is not None

    # Should pass (has verification or evidence)
    assert (
        detect_lazy_closure("[Tier 1]: The approach is appropriate - test output shows...") is None
    )
    assert detect_lazy_closure("I verified agents follow TDD - checked 5 sessions") is None
    assert detect_lazy_closure("I ran pytest and confirmed the mechanism works") is None
    assert detect_lazy_closure("After testing, this is sufficient for the use case") is None
    assert detect_lazy_closure("") is None

    # Pattern type checks
    lazy = detect_lazy_closure("The approach is appropriate")
    assert lazy and lazy.pattern_type == "lazy_justification"

    mechanism = detect_lazy_closure("It has built-in verification")
    assert mechanism and mechanism.pattern_type == "assumed_mechanism"

    avoidance = detect_lazy_closure("My closure is administrative acknowledgment")
    assert avoidance and avoidance.pattern_type == "work_avoidance"

    compliance = detect_lazy_closure("Agents follow the TDD workflow")
    assert compliance and compliance.pattern_type == "assumed_compliance"

    # Declaration patterns (NEW)
    # Should flag declarations without tool usage
    decl = detect_lazy_closure("I'll update the template")
    assert decl is not None, "Declaration without tools should be detected"
    assert decl.pattern_type == "declaration"

    decl2 = detect_lazy_closure("I'll update arch/ with this pattern")
    assert decl2 is not None, "Declaration to arch/ without tools should be detected"

    decl3 = detect_lazy_closure("I should update SKILL.md with this learning")
    assert decl3 is not None, "Declaration using 'should' without tools should be detected"

    # Declaration WITH tool usage should be allowed
    response_with_tool = "I'll update the template. I edited the file to add the new pattern."
    assert (
        detect_lazy_closure(response_with_tool) is None
    ), "Declaration with Edit tool should be allowed"

    response_with_write = "I'll update arch/. I wrote the changes to fix the issue."
    assert (
        detect_lazy_closure(response_with_write) is None
    ), "Declaration with Write tool should be allowed"

    response_with_updated = "I'll update SKILL.md. The file was updated successfully."
    assert (
        detect_lazy_closure(response_with_updated) is None
    ), "Declaration with 'updated' marker should be allowed"

    # Multi-detection
    multi_text = "The approach is appropriate. Agents follow TDD. My closure is administrative."
    all_matches = detect_all_lazy_closure(multi_text)
    assert len(all_matches) >= 3, f"Expected 3+ matches, got {len(all_matches)}"

    # Sycophancy capitulation patterns (should detect)
    cap1 = detect_lazy_closure("I see now. So the command simply shows documentation, not options.")
    assert cap1 is not None, "sycophancy_capitulation: 'I see now' should be detected"
    assert cap1.pattern_type == "sycophancy_capitulation"

    cap2 = detect_lazy_closure("Ah, I see. You're right that this is working differently.")
    assert cap2 is not None, "sycophancy_capitulation: 'Ah, I see' should be detected"

    cap3 = detect_lazy_closure("You're right. The implementation is already working as intended.")
    assert cap3 is not None, "sycophancy_capitulation: 'You're right' should be detected"

    cap4 = detect_lazy_closure("Now I understand. So /s list simply delegates to the model picker.")
    assert cap4 is not None, "sycophancy_capitulation: 'Now I understand' should be detected"

    # Sycophancy capitulation — should pass with Bash evidence
    cap_bash = detect_lazy_closure(
        "I see now. Looking at the output: $ /openrouter list\n"
        "exit code: 0\nModels: gpt-4, claude-3... The list is working."
    )
    assert cap_bash is None, "sycophancy_capitulation: Bash evidence should exempt this"

    cap_bash2 = detect_lazy_closure(
        "Ah, I see. stdout: Models available: 5\nreturncode: 0 — so the command works."
    )
    assert cap_bash2 is None, "sycophancy_capitulation: stdout/returncode should exempt this"

    # Deferral patterns (should detect)
    d1 = detect_lazy_closure("I'll leave that for now — the script can be updated later.")
    assert d1 is not None, "deferral: 'I'll leave that for now' should be detected"
    assert d1.pattern_type == "deferral"

    d2 = detect_lazy_closure("We can address that later when we have more time.")
    assert d2 is not None, "deferral: 'address that later' should be detected"

    d3 = detect_lazy_closure("Leave that for now, it's lower priority.")
    assert d3 is not None, "deferral: 'leave that for now' should be detected"

    # Deferral with tracking (should pass)
    d4 = detect_lazy_closure("I'll leave that for now — I've used spawn_task to track it.")
    assert d4 is None, "deferral with spawn_task should be exempt"

    d5 = detect_lazy_closure("We can address that later — flagged this as a side task.")
    assert d5 is None, "deferral with 'flagged this' tracking should be exempt"

    # Literalist framing patterns (should detect)
    lf1 = detect_lazy_closure("That's the extent of what you asked.")
    assert lf1 is not None, "literalist_framing: 'that's the extent of what you asked' should be detected"
    assert lf1.pattern_type == "literalist_framing"

    lf2 = detect_lazy_closure("That's all you asked for.")
    assert lf2 is not None, "literalist_framing: 'that's all you asked for' should be detected"

    lf3 = detect_lazy_closure("That's what you asked for.")
    assert lf3 is not None, "literalist_framing: 'that's what you asked for' should be detected"

    lf4 = detect_lazy_closure("No — you said 're-run the adversarial review' and that's what happened. That's the extent of what you asked.")
    assert lf4 is not None, "literalist_framing: 'that's the extent' with diagnosis context should be detected"

    # Literalist framing with diagnosis above should still be caught (only one line follows)
    lf5 = detect_all_lazy_closure("Root cause is X. That's the extent of what you asked.")
    assert any(m.pattern_type == "literalist_framing" for m in lf5), "literalist_framing should fire even with diagnosis above"

    # Universal absence patterns (the go_2.0-skill-03c80e1e incident)
    ua1 = detect_lazy_closure(
        "It's not on disk anywhere — no file, no cache entry, no registry. "
        "The string only exists in the UI's skill list."
    )
    assert ua1 is not None, "universal_absence: 'not on disk anywhere' should be detected"
    assert ua1.pattern_type == "universal_absence"

    ua2 = detect_lazy_closure("The identifier is not found anywhere in the codebase.")
    assert ua2 is not None, "universal_absence: 'not found anywhere' should be detected"

    ua3 = detect_lazy_closure("That file doesn't exist anywhere.")
    assert ua3 is not None, "universal_absence: 'doesn't exist anywhere' should be detected"

    ua4 = detect_lazy_closure("There's no file anywhere matching that pattern.")
    assert ua4 is not None, "universal_absence: 'no file anywhere' should be detected"

    # Universal absence with verification markers should pass
    ua_ok1 = detect_lazy_closure(
        "I checked ~/.claude/commands/ and P:\\ — not found anywhere in those directories."
    )
    assert ua_ok1 is None, "universal_absence: 'checked' exemption should apply"

    ua_ok2 = detect_lazy_closure(
        "I ran Glob across both ~/.claude/ and P:\\ and it's not found anywhere."
    )
    assert ua_ok2 is None, "universal_absence: 'i ran' exemption should apply"

    # Verifiable state claim patterns (the SDLC_MULTI_LLM incident)
    # Tier A — frozenset anchors
    vs1 = detect_lazy_closure("You likely haven't set SDLC_MULTI_LLM=1 in your environment.")
    assert vs1 is not None, "verifiable_state_claim: 'likely haven't set' (Tier A) should be detected"
    assert vs1.pattern_type == "verifiable_state_claim"

    # Tier B — structural regex (variable word in middle)
    vs3 = detect_lazy_closure("You probably don't have DEBUG set in your config.")
    assert vs3 is not None, "verifiable_state_claim: 'probably don't have ... set' (Tier B) should be detected"

    # Tier B — explicit noun prefix
    vs4 = detect_lazy_closure("The environment variable is likely not configured.")
    assert vs4 is not None, "verifiable_state_claim: 'env var likely not configured' (Tier B) should be detected"

    # Should NOT fire — "probably not enabled" alone (dropped: too broad for design-discussion prose)
    vs_no = detect_lazy_closure("The flag is probably not enabled by default.")
    assert vs_no is None, "verifiable_state_claim: bare 'probably not enabled' should NOT fire (dropped pattern)"

    # Should NOT fire — general performance prose, no runtime-state signal
    vs_ok1 = detect_lazy_closure("This approach is probably not the best for large datasets.")
    assert vs_ok1 is None, "verifiable_state_claim: design-discussion prose should NOT fire"

    # Should NOT fire — unhedged direct assertion (no "likely/probably")
    vs_ok2 = detect_lazy_closure(
        "SDLC_MULTI_LLM: NOT SET\n"
        "The variable is not set in your environment."
    )
    assert vs_ok2 is None, "verifiable_state_claim: unhedged assertion after tool output should NOT fire"

    print("✅ All tests passed")
