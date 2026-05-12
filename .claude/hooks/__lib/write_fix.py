#!/usr/bin/env python3
"""Fix epistemic_applicability.py by rewriting it cleanly"""

import re

# Build the content programmatically to avoid encoding issues
lines = [
    '#!/usr/bin/env python3',
    '"""epistemic_applicability - Turn-mode scoping and simple-answer fast path"""',
    '',
    'from __future__ import annotations',
    '',
    'import re',
    '',
    'from __lib.turn_mode import TurnMode',
    '',
    '_NON_SUBSTANTIVE_MODES: frozenset = frozenset({',
    '    "control",',
    '    "exploration",',
    '    "meta",',
    '    "plan",',
    '    "execution-report",',
    '})',
    '',
    '',
    'def is_substantive_reasoning_turn(mode: TurnMode) -> bool:',
    '    return mode not in _NON_SUBSTANTIVE_MODES',
    '',
    '',
]

# Diagnosis markers
diag_parts = [
    r'\b(?:root\s+cause|because|therefore|evidence\s+that|',
    r'caused\s+by|this\s+is\s+a|investigation|diagnos|',
    r'hypothesis|trace[d]?\s+(the\s+)?(source|cause)|',
    r'find(?:ing)?\s+(the\s+)?(root|underlying)|',
    r'(?:the\s+)?problem\s+is\s+(?:that|caused|located)|',
    r'the\s+(?:issue|bug)\s+originates|reason\s+is|',
    r'from\s+the\s+(?:grep|read|logs?|output|evidence)\b|',
    r'source:\s|as\s+shown|according\s+to\b|',
    r'this\s+suggests|this\s+indicates|this\s+means|',
    r'my\s+hypothesis|it\s+appears|it\s+seems|',
    r"the\s+system\s+(?:is|does|doesn'\x27t|can'\x27t|cannot)\b|",
    r'fixing\s+(?:this|it|the)\s+requires|',
    r'to\s+resolve\s+this|to\s+fix\s+this\b|',
    r'(?:the\s+)?first\s+step|step\s+(?:1|one|two|three|four)\b|',
    r'trace\s+(?:to|back\s+to|from)\b|',
    r'follow(?:ing|s)?\s+the\s+(?:path|chain|stack|import)\b|',
    r'the\s+call\s+chain|the\s+import\s+chain|the\s+stack\s+trace\b)',
]
lines.append('_DIAGNOSIS_MARKERS = (')
for p in diag_parts:
    lines.append(f'    r"{p}"')
lines.append(')')
lines.append('')
lines.append('_DIAGNOSIS_RE = re.compile(_DIAGNOSIS_MARKERS, re.IGNORECASE | re.VERBOSE)')
lines.append('')

# Causal markers
lines.append('_CAUSAL_MARKERS_RE = re.compile(')
lines.append('    r"\\b(?:cause[sd]?|because|therefore|so|hence|thus|"')
lines.append('    r"due\\s+to|result(?:s|ed|ing)?\\s+in|lead(?:s|ing)?\\s+to|"')
lines.append('    r"is\\s+why|is\\s+caused\\s+by|is\\s+driven\\s+by|triggered\\s+by)\\b",')
lines.append('    re.IGNORECASE,')
lines.append(')')
lines.append('')

# Section header
lines.append('_SECTION_HEADER_RE = re.compile(')
lines.append('    r"\\[[\\s]*(?:FACT|INFERENCE|RECOMMENDATION|CONCLUSION|UNKNOWN|RATIONALE|PLAN|STATUS|CHANGES|RESULTS|NEXT)",')
lines.append('    re.IGNORECASE,')
lines.append(')')
lines.append('')

# Delivery markers — the problematic one uses chr() to avoid literal quote issues
apostrophe = chr(0x27)  # straight single quote
right_quote = chr(0xE2) + chr(0x80) + chr(0x99)  # RIGHT SINGLE QUOTATION MARK
wasn_pattern = f"wasn[{apostrophe}{right_quote}]t"

delivery_parts = [
    r'^\s*(?:done|complete|finished|implemented|fixed|verified)|',
    r'all\s+(?:tests?\s+)?passed?|',
    r'\d+\s+(?:tests?\s+)?passed|',
    r'[A-Z][a-z]+\s+(?:file|test|module|hook|gate)\s+(?:created|added|updated|fixed|modified)|',
    r'files?\s+created|files?\s+modified|files?\s+added|',
    r'tests?\s+(?:added|wrote|created|written)|',
    r'implementation\s+complete|code\s+complete|',
    r'(?:yes|no|ok|right|wrong|correct)\s*[.,]?\s*$|',
    r'limitations?\s*\.\s*$|',
    r'deliverables?\s*\.\s*$|',
    r'files?\s+(?:modified|created|added)\s*\.\s*$|',
    f'what\\s+(?:was|{wasn_pattern}|could|should)\\s+(?:done|changed|fixed|improved)\\s*\\.\\s*$',
]
lines.append('_DELIVERY_MARKERS = (')
for p in delivery_parts:
    lines.append(f'    r"{p}",')
lines.append(')')
lines.append('')
lines.append('_DELIVERY_RE = re.compile(_DELIVERY_MARKERS, re.IGNORECASE | re.MULTILINE)')
lines.append('')

# Stop hook feedback lines
lines.append('_STOP_HOOK_FEEDBACK_LINES = (')
lines.append('    "LAZY WORKAROUND", "EPISTEMIC FORMAT REPAIR", "EPISTEMIC VIOLATION",')
lines.append('    "pattern matched:", "required approach:", "remember:",')
lines.append('    "this suggests", "this is a", "\\u23fe",')
lines.append('    "stop hook says:", "stop hook:", "stop:", "stop (hook says):",')
lines.append(')')
lines.append('')

# Blockquote and grounded short
lines.append('_BLOCKQUOTE_RE = re.compile(r"^\\s*>")')
lines.append('_GROUNDED_SHORT_RE = re.compile(')
lines.append('    r"^\\s*\\d+\\s+(?:passed|failed|errors?)\\b|"')
lines.append('    r"^\\s*(?:ok|OK|passed|failed|error|true|false)\\s*[.,]?\\s*$",')
lines.append('    re.IGNORECASE,')
lines.append(')')
lines.append('')

# Strip function
lines.append('def _strip_quoted_content(text: str) -> str:')
lines.append('    lines = text.split("\\n")')
lines.append('    result: list[str] = []')
lines.append('    skip = False')
lines.append('')
lines.append('    for line in lines:')
lines.append('        stripped = line.strip()')
lines.append('')
lines.append('        if _BLOCKQUOTE_RE.match(line):')
lines.append('            continue')
lines.append('')
lines.append('        if any(stripped.startswith(artifact) for artifact in _STOP_HOOK_FEEDBACK_LINES):')
lines.append('            skip = True')
lines.append('            continue')
lines.append('')
lines.append('        if skip:')
lines.append('            if not stripped or len(stripped) > 100 or not stripped.startswith(')
lines.append('                ("\\u26a0", "1.", "2.", "3.", "4.", "\\u2713", "\\u2717", "Do NOT", "- ", "* ")')
lines.append('            ):')
lines.append('                skip = False')
lines.append('')
lines.append('        if not skip:')
lines.append('            result.append(line)')
lines.append('')
lines.append('    return "\\n".join(result)')
lines.append('')

# is_simple_epistemic_response
lines.append('def is_simple_epistemic_response(response: str) -> bool:')
lines.append('    if not response:')
lines.append('        return True')
lines.append('')
lines.append('    stripped = response.strip()')
lines.append('')
lines.append('    if _GROUNDED_SHORT_RE.search(stripped):')
lines.append('        return True')
lines.append('')
lines.append('    if _DELIVERY_RE.search(stripped):')
lines.append('        return True')
lines.append('')
lines.append('    if len(stripped) <= 80 and not _DIAGNOSIS_RE.search(stripped):')
lines.append('        return True')
lines.append('')
lines.append('    if len(stripped) <= 150:')
lines.append('        if re.match(r"^(yes|no|correct|incorrect|right|wrong|absolutely|confirm)[,.\s]", stripped.lower()):')
lines.append('            return True')
lines.append('        if re.match(r"^(is|does|can|will|should|would|has|have)\\s+", stripped.lower()):')
lines.append('            if not _DIAGNOSIS_RE.search(stripped):')
lines.append('                return True')
lines.append('')
lines.append('    if _SECTION_HEADER_RE.search(stripped):')
lines.append('        return False')
lines.append('')
lines.append('    causal_count = len(_CAUSAL_MARKERS_RE.findall(stripped))')
lines.append('    if causal_count >= 2:')
lines.append('        return False')
lines.append('')
lines.append('    if _DIAGNOSIS_RE.search(stripped):')
lines.append('        return False')
lines.append('')
lines.append('    if len(stripped) > 300:')
lines.append('        return False')
lines.append('')
lines.append('    return True')
lines.append('')

# is_grounded_delivery_summary
lines.append('def is_grounded_delivery_summary(response: str) -> bool:')
lines.append('    if not response:')
lines.append('        return False')
lines.append('')
lines.append('    stripped = response.strip()')
lines.append('')
lines.append('    if _GROUNDED_SHORT_RE.search(stripped):')
lines.append('        return True')
lines.append('')
lines.append('    if _DELIVERY_RE.match(stripped):')
lines.append('        return True')
lines.append('')
lines.append('    diag_count = len(_DIAGNOSIS_RE.findall(stripped))')
lines.append('    if diag_count == 0:')
lines.append('        if len(stripped) < 200 and not _CAUSAL_MARKERS_RE.search(stripped):')
lines.append('            return True')
lines.append('')
lines.append('    return False')
lines.append('')

# strip_for_gate_matching
lines.append('def strip_for_gate_matching(response: str) -> str:')
lines.append('    return _strip_quoted_content(response)')
lines.append('')

# Self-test
lines.append('if __name__ == "__main__":')
lines.append('    import sys')
lines.append('    cases = [')
lines.append('        ("Yes, the fix is in.", True, False),')
lines.append('        ("Tests are passing.", True, True),')
lines.append('        ("103 passed, 2 failed.", True, True),')
lines.append("        (\"All tests pass. Done.\", True, True),")
lines.append("        (\"I've fixed the import.\", True, True),")
lines.append('        ("Files modified: Stop.py, test_stop.py\\nTests added: 12 tests", True, True),')
lines.append('        ("Implementation complete. 4 files created, 2 tests written.", True, True),')
lines.append('        ("LIMITATIONS:\\n- No graceful degradation for missing config", True, True),')
lines.append('        ("The root cause is that sys.path does not include the hooks directory.", False, False),')
lines.append('        ("This is a lazy workaround because the real fix would require significant refactoring.", False, False),')
lines.append('        ("The problem originates from the import chain - I traced it to line 42.", False, False),')
lines.append('        ("Because the gate fires on every response, it creates a loop.", False, False),')
lines.append('        ("Therefore, the fix requires adding a turn-mode check.", False, False),')
lines.append('        ("[FACT]\\n- grep shows the import is missing\\n[INFERENCE]\\n- the fix is to add the import", False, False),')
lines.append('        ("> The root cause is X", False, False),')
lines.append('    ]')
lines.append('')
lines.append('    failed = 0')
lines.append('    for resp, exp_simple, exp_delivery in cases:')
lines.append('        actual_simple = is_simple_epistemic_response(resp)')
lines.append('        actual_delivery = is_grounded_delivery_summary(resp)')
lines.append('        s_ok = actual_simple == exp_simple')
lines.append('        d_ok = actual_delivery == exp_delivery')
lines.append('        status = "\\u2713" if (s_ok and d_ok) else "\\u2717"')
lines.append('        if not (s_ok and d_ok):')
lines.append('            failed += 1')
lines.append('            print(f"{status} resp={resp[:40]:40s}  simple: {actual_simple} (exp {exp_simple})  delivery: {actual_delivery} (exp {exp_delivery})")')
lines.append('        else:')
lines.append('            print(f"{status} {resp[:40]:40s} -> simple={actual_simple}, delivery={actual_delivery}")')
lines.append('')
lines.append('    print(f"\\nAll passed" if failed == 0 else f"{failed} FAILED")')
lines.append('    sys.exit(failed)')

content = '\n'.join(lines)
with open('P:/../.claude/hooks/__lib/epistemic_applicability.py'.replace('..', '.'), 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Wrote {len(content)} chars")