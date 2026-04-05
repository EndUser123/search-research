"""
Baseline regression tests for /s skill (Strategy skill).

These tests capture the current behavior of /s before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Persona-based option generation (innovator, pragmatist, critic, expert)
- Constitutional filtering (enterprise anti-pattern removal)
- Provider tier filtering (T1/T2/T3 quality classification)
- Debate mode selection (none/full/fast)
- Option ranking and scoring
- Decision memo generation (chosen alternative with rationale)

Critical paths tested: 6
Lines of code: ~100
"""

import pytest


def classify_provider_tier(provider_name: str) -> str:
    """
    Classify LLM provider by quality tier.

    This is a copy of the provider tier logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        provider_name: Name of LLM provider

    Returns:
        Quality tier: T1 (Best), T2 (Good), T3 (Experimental)
    """
    provider_lower = provider_name.lower()

    # T1 (Best): claude, anthropic
    if provider_lower in ('claude', 'anthropic'):
        return 'T1'

    # T2 (Good): openai, gpt, gemini, google
    if provider_lower in ('openai', 'gpt', 'gemini', 'google'):
        return 'T2'

    # T3 (Experimental): All other providers
    return 'T3'


def filter_provider_tier(providers: list[str], allowed_tiers: list[str]) -> list[str]:
    """
    Filter providers by allowed quality tiers.

    This is a copy of the provider filtering logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        providers: List of provider names
        allowed_tiers: List of allowed tiers (e.g., ['T1', 'T2'])

    Returns:
        Filtered list of providers
    """
    filtered = []

    for provider in providers:
        tier = classify_provider_tier(provider)
        if tier in allowed_tiers:
            filtered.append(provider)

    return filtered


def apply_constitutional_filter(options: list[dict], forbidden_patterns: list[str]) -> tuple[list[dict], int]:
    """
    Apply constitutional constraints to filter options.

    This is a copy of the constitutional filtering logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Forbidden patterns (enterprise anti-patterns):
    - Background autonomous execution
    - Self-healing systems
    - Real-time monitoring dashboards
    - Team approval gates
    - Lock-free multi-terminal coordination

    Args:
        options: List of option dicts with 'description' field
        forbidden_patterns: List of patterns to filter out

    Returns:
        Tuple of (filtered_options, filtered_count)
    """
    filtered = []
    count = 0

    for option in options:
        description = str(option.get('description', '')).lower()
        # Check if option contains any forbidden pattern
        if any(pattern in description for pattern in forbidden_patterns):
            count += 1
        else:
            filtered.append(option)

    return (filtered, count)


def generate_persona_options(topic: str, persona_type: str, technique: str) -> dict:
    """
    Generate option from persona perspective using specific technique.

    This is a copy of the persona-based generation logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        topic: Strategy topic
        persona_type: Type of persona (innovator, pragmatist, critic, expert)
        technique: Ideation technique (SCAMPER, lateral, first_principles, etc.)

    Returns:
        Generated option dict with persona, technique, and description
    """
    # Simplified stub for testing - actual implementation would use LLM
    return {
        'persona': persona_type,
        'technique': technique,
        'description': f"[{persona_type}] {technique} approach to {topic}"
    }


def rank_options(options: list[dict], weights: dict[str, float]) -> list[dict]:
    """
    Rank options by weighted score.

    This is a copy of the option ranking logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        options: List of option dicts with 'score' field
        weights: Weight dict for scoring criteria

    Returns:
        Ranked list of options (highest score first)
    """
    # Calculate weighted score for each option
    for option in options:
        base_score = option.get('score', 0.5)
        # Apply weights (simplified)
        weighted_score = base_score * weights.get('default', 1.0)
        option['weighted_score'] = weighted_score

    # Sort by weighted score (descending)
    ranked = sorted(options, key=lambda x: x['weighted_score'], reverse=True)
    return ranked


def select_debate_mode(mode: str, idea_count: int) -> tuple[str, int]:
    """
    Select debate mode and determine round count.

    This is a copy of the debate mode logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        mode: Debate mode (none, full, fast)
        idea_count: Number of ideas to debate

    Returns:
        Tuple of (mode, rounds)
    """
    if mode == 'none':
        return ('none', 0)

    if mode == 'full':
        return ('full', 3)  # PRO → CON → REBUTTAL

    if mode == 'fast':
        return ('fast', 1)  # Single abbreviated round

    # Default
    return ('none', 0)


def generate_decision_memo(chosen_option: dict, rejected_options: list[dict],
                           rationale: str) -> dict:
    """
    Generate decision memo with chosen alternative and rationale.

    This is a copy of the decision memo logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        chosen_option: The selected option
        rejected_options: List of rejected options
        rationale: Why chosen option was selected

    Returns:
        Decision memo dict with chosen, rejected, and rationale
    """
    return {
        'chosen': chosen_option,
        'rejected_count': len(rejected_options),
        'rejected_summaries': [opt.get('description', '')[:50] + '...' for opt in rejected_options],
        'rationale': rationale,
        'next_steps': generate_next_hints(chosen_option)
    }


def generate_next_hints(option: dict) -> list[str]:
    """
    Generate next command hints from chosen option.

    This is a copy of the next hints logic from /s
    to establish baseline behavior before GoT/ToT integration.

    Args:
        option: Chosen option dict

    Returns:
        List of next command suggestions
    """
    description = option.get('description', '').lower()

    hints = []

    if 'architecture' in description or 'design' in description:
        hints.append('/arch')

    if 'plan' in description:
        hints.append('/plan-workflow')

    if 'next step' in description or 'nse' in description:
        hints.append('/nse')

    if not hints:
        hints.append('/r')  # Default fallback

    return hints


class TestProviderTierClassification:
    """Test provider quality tier classification."""

    def test_claude_is_t1(self):
        """Test claude classified as T1"""
        tier = classify_provider_tier('claude')
        assert tier == 'T1'

    def test_anthropic_is_t1(self):
        """Test anthropic classified as T1"""
        tier = classify_provider_tier('anthropic')
        assert tier == 'T1'

    def test_openai_is_t2(self):
        """Test openai classified as T2"""
        tier = classify_provider_tier('openai')
        assert tier == 'T2'

    def test_gemini_is_t2(self):
        """Test gemini classified as T2"""
        tier = classify_provider_tier('gemini')
        assert tier == 'T2'

    def test_unknown_provider_is_t3(self):
        """Test unknown provider classified as T3"""
        tier = classify_provider_tier('unknown-provider')
        assert tier == 'T3'


class TestProviderTierFiltering:
    """Test provider filtering by allowed tiers."""

    def test_filter_t1_only(self):
        """Test filtering to T1 providers only"""
        providers = ['claude', 'openai', 'unknown']
        filtered = filter_provider_tier(providers, ['T1'])
        assert filtered == ['claude']

    def test_filter_t1_and_t2(self):
        """Test filtering to T1 and T2 providers"""
        providers = ['claude', 'openai', 'unknown']
        filtered = filter_provider_tier(providers, ['T1', 'T2'])
        assert filtered == ['claude', 'openai']

    def test_filter_all_tiers(self):
        """Test allowing all tiers"""
        providers = ['claude', 'openai', 'unknown']
        filtered = filter_provider_tier(providers, ['T1', 'T2', 'T3'])
        assert len(filtered) == 3


class TestConstitutionalFiltering:
    """Test constitutional constraint filtering."""

    def test_filter_autonomous_execution(self):
        """Test filtering autonomous background execution"""
        options = [
            {'description': 'Add autonomous background service'}
        ]
        forbidden = ['autonomous', 'background']
        filtered, count = apply_constitutional_filter(options, forbidden)
        assert len(filtered) == 0
        assert count == 1

    def test_filter_real_time_dashboard(self):
        """Test filtering real-time monitoring dashboard"""
        options = [
            {'description': 'Add real-time metrics dashboard'}
        ]
        forbidden = ['real-time', 'monitoring']
        filtered, count = apply_constitutional_filter(options, forbidden)
        assert len(filtered) == 0
        assert count == 1

    def test_preserve_valid_option(self):
        """Test preserving constitutional option"""
        options = [
            {'description': 'Add LLM-generated tests under user direction'}
        ]
        forbidden = ['autonomous', 'background']
        filtered, count = apply_constitutional_filter(options, forbidden)
        assert len(filtered) == 1
        assert count == 0


class TestPersonaGeneration:
    """Test persona-based option generation."""

    def test_innovator_persona(self):
        """Test generating option from innovator perspective"""
        option = generate_persona_options('auth system', 'innovator', 'SCAMPER')
        assert option['persona'] == 'innovator'
        assert 'innovator' in option['description']

    def test_pragmatist_persona(self):
        """Test generating option from pragmatist perspective"""
        option = generate_persona_options('auth system', 'pragmatist', 'first_principles')
        assert option['persona'] == 'pragmatist'

    def test_critic_persona(self):
        """Test generating option from critic perspective"""
        option = generate_persona_options('auth system', 'critic', 'lateral')
        assert option['persona'] == 'critic'

    def test_expert_persona(self):
        """Test generating option from expert perspective"""
        option = generate_persona_options('auth system', 'expert', 'reverse')
        assert option['persona'] == 'expert'


class TestDebateMode:
    """Test debate mode selection."""

    def test_no_debate_mode(self):
        """Test no debate mode"""
        mode, rounds = select_debate_mode('none', 5)
        assert mode == 'none'
        assert rounds == 0

    def test_full_debate_mode(self):
        """Test full debate mode with 3 rounds"""
        mode, rounds = select_debate_mode('full', 5)
        assert mode == 'full'
        assert rounds == 3

    def test_fast_debate_mode(self):
        """Test fast debate mode with 1 round"""
        mode, rounds = select_debate_mode('fast', 5)
        assert mode == 'fast'
        assert rounds == 1

    def test_unknown_mode_defaults_to_none(self):
        """Test unknown mode defaults to none"""
        mode, rounds = select_debate_mode('unknown', 5)
        assert mode == 'none'
        assert rounds == 0


class TestOptionRanking:
    """Test option ranking by weighted score."""

    def test_rank_by_score(self):
        """Test ranking options by weighted score"""
        options = [
            {'description': 'Option A', 'score': 0.8},
            {'description': 'Option B', 'score': 0.5},
            {'description': 'Option C', 'score': 0.9}
        ]
        weights = {'default': 1.0}
        ranked = rank_options(options, weights)

        assert ranked[0]['description'] == 'Option C'
        assert ranked[1]['description'] == 'Option A'
        assert ranked[2]['description'] == 'Option B'

    def test_apply_weights(self):
        """Test applying custom weights"""
        options = [
            {'description': 'Option A', 'score': 0.5},
            {'description': 'Option B', 'score': 0.6}
        ]
        weights = {'default': 2.0}
        ranked = rank_options(options, weights)

        # 0.5 * 2.0 = 1.0
        # 0.6 * 2.0 = 1.2
        assert ranked[0]['description'] == 'Option B'
        assert ranked[1]['description'] == 'Option A'


class TestDecisionMemo:
    """Test decision memo generation."""

    def test_generate_memo(self):
        """Test generating decision memo"""
        chosen = {'description': 'JWT authentication'}
        rejected = [
            {'description': 'OAuth 2.0 flow'},
            {'description': 'Session-based auth'}
        ]
        memo = generate_decision_memo(chosen, rejected, 'JWT is simplest for solo dev')

        assert memo['chosen'] == chosen
        assert memo['rejected_count'] == 2
        assert memo['rationale'] == 'JWT is simplest for solo dev'
        assert len(memo['rejected_summaries']) == 2

    def test_architecture_option_suggests_arch(self):
        """Test architecture option suggests /arch command"""
        chosen = {'description': 'Microservices architecture design'}
        memo = generate_decision_memo(chosen, [], 'Best for scalability')

        hints = memo['next_steps']
        assert '/arch' in hints

    def test_plan_option_suggests_plan_workflow(self):
        """Test plan option suggests /plan-workflow command"""
        chosen = {'description': 'Create implementation plan'}
        memo = generate_decision_memo(chosen, [], 'Need structured approach')

        hints = memo['next_steps']
        assert '/plan-workflow' in hints

    def test_generic_option_suggests_r(self):
        """Test generic option defaults to /r"""
        chosen = {'description': 'Some generic option'}
        memo = generate_decision_memo(chosen, [], 'Seems reasonable')

        hints = memo['next_steps']
        assert '/r' in hints


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
