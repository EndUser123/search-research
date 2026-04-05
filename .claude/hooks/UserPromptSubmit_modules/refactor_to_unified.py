#!/usr/bin/env python3
"""Refactor cognitive_enhancers.py to use unified detection.

This script modifies cognitive_enhancers.py to integrate with unified_detection module
instead of using internal regex patterns for intent detection.
"""

import re

# Read the file
with open("P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py", encoding="utf-8") as f:
    content = f.read()

# ==============================================================================
# CHANGE 1: Remove unused regex patterns (_IMPL_RE, _MODIFY_RE, _PLAN_RE, _DIAGNOSTIC_RE)
# ==============================================================================

# Remove _IMPL_RE pattern (lines 152-157)
pattern = r'_IMPL_RE = re\.compile\([^)]+\),\s+re\.IGNORECASE,\)\s*\n'
content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Remove _MODIFY_RE pattern (lines 159-164)
pattern = r'_MODIFY_RE = re\.compile\([^)]+\),\s+re\.IGNORECASE,\)\s*\n'
content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Remove _PLAN_RE pattern (lines 166-169)
pattern = r'_PLAN_RE = re\.compile\([^)]+\),\s+re\.IGNORECASE,\)\s*\n'
content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Remove _DIAGNOSTIC_RE pattern (lines 171-176)
pattern = r'_DIAGNOSTIC_RE = re\.compile\([^)]+\),\s+re\.IGNORECASE,\)\s*\n'
content = re.sub(pattern, '', content, flags=re.MULTILINE)

# ==============================================================================
# CHANGE 2: Add new function to select enhancers by framework names
# ==============================================================================

new_function = '''
def _select_enhancers_by_frameworks(
    matched_frameworks: list[str], config: dict
) -> list[Enhancer]:
    """Select enhancers based on detected framework names from unified detection.

    This is the new unified detection path that replaces intent-based selection.
    Frameworks are detected by unified_detection.detect_prompt().

    Args:
        matched_frameworks: List of framework names detected (e.g., ["assumption_surfacing"])
        config: Configuration dict

    Returns:
        List of selected enhancers, limited by max_enhancers_per_prompt
    """
    selected = []

    # Get enabled enhancers from config
    enabled_enhancers = config.get("enhancers", {})

    for enhancer in _ENHANCERS:
        # Skip if enhancer is disabled in config
        if not enabled_enhancers.get(enhancer.name, True):
            continue

        # Check if this enhancer's framework was detected
        if enhancer.name in matched_frameworks:
            selected.append(enhancer)

    # Limit number of enhancers
    max_enhancers = config.get("max_enhancers_per_prompt", 3)
    return selected[:max_enhancers]


'''

# Insert after _select_enhancers function (after line 391)
insert_marker = "    return selected\\[:max_enhancers\\]\n\n\ndef _get_rationale"
content = content.replace(insert_marker, "    return selected[:max_enhancers]" + new_function + "def _get_rationale")

# ==============================================================================
# CHANGE 3: Update cognitive_enhancers() to use unified_detection
# ==============================================================================

# Replace the intent detection section (lines 497-516)
# Old code checks for mode overrides and calls _detect_intent()
# New code should call unified_detection.detect_prompt() and use matched_frameworks

old_intent_logic = '''    # Check for user mode overrides
    mode_match = _MODE_RE.search(prompt)
    if mode_match:
        mode = mode_match.group(1)
        modes = config.get("modes", {})
        if mode in modes:
            mode_config = modes[mode]
            # NOTE: 'disable_all' is no longer handled here - conflict arbiter will manage it
            # Force topic from mode
            forced_topic = mode_config.get("topic")
            if forced_topic:
                # Override intent detection with forced topic
                intent = dict.fromkeys(["implementation", "diagnostic", "meta_rca", "decomposition", "implementation_diagnostic"], False)
                intent[forced_topic] = True
            else:
                intent = _detect_intent(prompt)
        else:
            intent = _detect_intent(prompt)
    else:
        intent = _detect_intent(prompt)

    # Select enhancers based on intent and config
    selected = _select_enhancers(intent, config)'''

new_intent_logic = '''    # Call unified detection engine
    detection_result = unified_detection.detect_prompt(prompt)

    # Check for user mode overrides
    mode_match = _MODE_RE.search(prompt)
    if mode_match:
        mode = mode_match.group(1)
        modes = config.get("modes", {})
        if mode in modes:
            mode_config = modes[mode]
            # NOTE: 'disable_all' is no longer handled here - conflict arbiter will manage it
            # Force topic from mode (legacy support - maps to frameworks)
            forced_topic = mode_config.get("topic")
            if forced_topic:
                # Map topic to frameworks for legacy mode support
                topic_to_frameworks = {
                    "implementation": ["assumption_surfacing", "outcome_anchoring", "inversion_prompting", "chestertons_fence", "devils_advocate"],
                    "diagnostic": ["calibrated_confidence", "hanlons_razor"],
                    "meta_rca": ["cynefin_classification"],
                    "decomposition": ["socratic_decomposition"],
                }
                matched_frameworks = topic_to_frameworks.get(forced_topic, [])
            else:
                # Use unified detection results
                matched_frameworks = detection_result.matched_frameworks
        else:
            matched_frameworks = detection_result.matched_frameworks
    else:
        matched_frameworks = detection_result.matched_frameworks

    # Select enhancers based on matched frameworks from unified detection
    selected = _select_enhancers_by_frameworks(matched_frameworks, config)

    # Generate intent dict for rationale generation (backward compatibility)
    # Map frameworks back to intent topics for _get_rationale()
    framework_to_topics = {
        "assumption_surfacing": ["implementation", "implementation_diagnostic"],
        "outcome_anchoring": ["implementation"],
        "inversion_prompting": ["implementation"],
        "chestertons_fence": ["implementation"],
        "calibrated_confidence": ["diagnostic", "implementation_diagnostic"],
        "socratic_decomposition": ["decomposition"],
        "cynefin_classification": ["meta_rca", "diagnostic"],
        "hanlons_razor": ["diagnostic"],
        "devils_advocate": ["implementation"],
    }
    intent = {}
    for framework in matched_frameworks:
        for topic in framework_to_topics.get(framework, []):
            intent[topic] = True'''

content = content.replace(old_intent_logic, new_intent_logic)

# ==============================================================================
# CHANGE 4: Update docstring to reflect unified detection
# ==============================================================================

old_docstring = '''    """Unified cognitive enhancers hook with config-driven routing.

    Replaces 9 separate hooks (assumption_surfacing, outcome_anchoring,
    inversion_prompting, chestertons_fence, calibrated_confidence,
    socratic_decomposition, cynefin_classification, hanlons_razor,
    devils_advocate) with a single config-driven router.

    Topic-based routing:
    - implementation: assumption_surfacing, outcome_anchoring, inversion_prompting, chestertons_fence, devils_advocate
    - diagnostic: calibrated_confidence, hanlons_razor
    - meta_rca: cynefin_classification
    - implementation_diagnostic: assumption_surfacing + calibrated_confidence
    - decomposition: socratic_decomposition (long vague prompts)

    User modes (via #mode in prompt):
    - #rca: Force meta_rca topic
    - #deep: Force implementation topic
    - #fast: Disable all enhancers

    Config-driven enable/disable:
    - topics.{topic_name}: true/false
    - enhancers.{enhancer_name}: true/false
    - max_enhancers_per_prompt: 3
    """'''

new_docstring = '''    """Unified cognitive enhancers hook with config-driven routing.

    Replaces 9 separate hooks (assumption_surfacing, outcome_anchoring,
    inversion_prompting, chestertons_fence, calibrated_confidence,
    socratic_decomposition, cynefin_classification, hanlons_razor,
    devils_advocate) with a single config-driven router.

    Uses unified_detection.detect_prompt() for framework detection:
    - Replaces internal regex patterns with centralized detection engine
    - Framework-based routing: selects enhancers by matched framework names
    - Maintains backward compatibility with mode-based overrides (#rca, #deep, #fast)

    User modes (via #mode in prompt):
    - #rca: Force meta_rca topic (maps to cynefin_classification)
    - #deep: Force implementation topic (maps to implementation frameworks)
    - #fast: Disable all enhancers

    Config-driven enable/disable:
    - topics.{topic_name}: true/false (legacy, for rationale generation)
    - enhancers.{enhancer_name}: true/false
    - max_enhancers_per_prompt: 3
    """'''

content = content.replace(old_docstring, new_docstring)

# ==============================================================================
# CHANGE 5: Remove _detect_intent function (no longer needed)
# ==============================================================================

# Remove the entire _detect_intent function
pattern = r'def _detect_intent\(prompt: str\) -> dict\[str, bool\]:.*?(?=\n\ndef [a-z_])'
content = re.sub(pattern, '', content, flags=re.DOTALL)

# ==============================================================================
# Write the modified content back to the file
# ==============================================================================

with open("P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ cognitive_enhancers.py refactored successfully!")
print("Changes made:")
print("1. Added unified_detection import")
print("2. Removed unused regex patterns (_IMPL_RE, _MODIFY_RE, _PLAN_RE, _DIAGNOSTIC_RE)")
print("3. Added _select_enhancers_by_frameworks() function")
print("4. Updated cognitive_enhancers() to use unified_detection.detect_prompt()")
print("5. Removed _detect_intent() function")
print("6. Updated docstring to reflect unified detection integration")
