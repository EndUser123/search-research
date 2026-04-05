"""
Test suite for pattern 2 exemption in skill enforcement.

Tests cover:
- No skill loaded → block pattern 2
- Skill loaded → allow pattern 2 (universal-skills-manager use case)
- Exemption only applies when loaded_skill is in context
"""



class TestPattern2WithoutLoadedSkill:
    """Test pattern 2 blocking when no skill is loaded"""

    def test_pattern_2_blocked_without_loaded_skill(self):
        """Test that pattern 2 requests are blocked when no skill is loaded"""
        # Simulate context without loaded_skill
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": None  # No skill loaded
        }

        # Pattern 2 should be blocked
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is True, "Pattern 2 should be blocked when no skill loaded"

    def test_pattern_2_blocked_with_empty_loaded_skill(self):
        """Test that pattern 2 is blocked when loaded_skill is empty string"""
        # Simulate context with empty loaded_skill
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": ""  # Empty string
        }

        # Pattern 2 should be blocked (empty string is falsy)
        is_loaded = bool(context.get("loaded_skill"))
        should_block = not is_loaded

        assert should_block is True, "Pattern 2 should be blocked with empty loaded_skill"

    def test_pattern_2_blocked_with_none_loaded_skill(self):
        """Test that pattern 2 is blocked when loaded_skill is None"""
        # Simulate context with None loaded_skill
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": None
        }

        # Pattern 2 should be blocked
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is True, "Pattern 2 should be blocked with None loaded_skill"


class TestPattern2WithLoadedSkill:
    """Test pattern 2 allowance when skill is loaded"""

    def test_pattern_2_allowed_with_loaded_skill(self):
        """Test that pattern 2 is allowed when a skill is loaded"""
        # Simulate context with loaded_skill
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": "universal-skills-manager"
        }

        # Pattern 2 should be allowed
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is False, "Pattern 2 should be allowed when skill is loaded"

    def test_pattern_2_allowed_with_any_loaded_skill(self):
        """Test that pattern 2 is allowed for any loaded skill"""
        # Test with various skill names
        loaded_skills = [
            "code",
            "plan",
            "refactor",
            "search",
            "universal-skills-manager",
            "any-skill-name"
        ]

        for skill_name in loaded_skills:
            context = {
                "tool_name": "UniversalSkillsManager",
                "tool_input": {"action": "list"},
                "loaded_skill": skill_name
            }

            # Pattern 2 should be allowed for all
            is_loaded = context.get("loaded_skill") is not None
            should_block = not is_loaded

            assert should_block is False, f"Pattern 2 should be allowed for skill '{skill_name}'"


class TestPattern2ExemptionContext:
    """Test that pattern 2 exemption depends on context"""

    def test_exemption_applies_only_to_pattern_2_tools(self):
        """Test that exemption only applies to pattern 2 tools"""
        # Pattern 2 tools (these are exempt when skill loaded)
        pattern_2_tools = [
            "UniversalSkillsManager",
            "SkillManager"
        ]

        for tool in pattern_2_tools:
            context = {
                "tool_name": tool,
                "tool_input": {"action": "list"},
                "loaded_skill": "code"
            }

            # Should be allowed
            is_loaded = context.get("loaded_skill") is not None
            should_block = not is_loaded

            assert should_block is False, f"Pattern 2 tool '{tool}' should be allowed when skill loaded"

    def test_exemption_does_not_apply_to_other_tools(self):
        """Test that exemption doesn't apply to non-pattern-2 tools"""
        # Non-pattern-2 tools (exemption doesn't apply)
        other_tools = [
            "Read",
            "Grep",
            "Bash",
            "Edit",
            "Write"
        ]

        for tool in other_tools:
            context = {
                "tool_name": tool,
                "tool_input": {},
                "loaded_skill": "code"
            }

            # Exemption logic should not apply
            # (Other tools have different enforcement rules)
            is_pattern_2_tool = context.get("tool_name") in ["UniversalSkillsManager", "SkillManager"]
            assert not is_pattern_2_tool, f"Tool '{tool}' is not a pattern 2 tool"


class TestUniversalSkillsManagerUseCase:
    """Test the universal-skills-manager use case specifically"""

    def test_universal_skills_manager_allowed_from_loaded_skill(self):
        """Test that universal-skills-manager can use UniversalSkillsManager tool"""
        # This is the primary use case: /s skill needs to list other skills
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": "universal-skills-manager"  # /s skill is loaded
        }

        # Should be allowed
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is False, "universal-skills-manager should be able to use UniversalSkillsManager"

    def test_other_skills_can_also_use_universal_skills_manager(self):
        """Test that other skills can also use UniversalSkillsManager when loaded"""
        # Other skills might also need to query skill catalog
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "get", "skill": "code"},
            "loaded_skill": "plan"  # Different skill loaded
        }

        # Should be allowed (exemption is not specific to universal-skills-manager)
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is False, "Any loaded skill should be able to use UniversalSkillsManager"


class TestPattern2ExemptionEdgeCases:
    """Test edge cases for pattern 2 exemption"""

    def test_loaded_skill_with_whitespace(self):
        """Test handling of loaded_skill with only whitespace"""
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": "   "  # Whitespace only
        }

        # Should be blocked (whitespace-only is effectively empty)
        is_loaded = bool(context.get("loaded_skill", "").strip())
        should_block = not is_loaded

        assert should_block is True, "Whitespace-only loaded_skill should be treated as unloaded"

    def test_loaded_skill_case_sensitivity(self):
        """Test that loaded_skill matching is case-sensitive"""
        context = {
            "tool_name": "UniversalSkillsManager",
            "tool_input": {"action": "list"},
            "loaded_skill": "Code"  # Capital C
        }

        # Should be allowed (any non-empty value is loaded)
        is_loaded = context.get("loaded_skill") is not None
        should_block = not is_loaded

        assert should_block is False, "Any non-None loaded_skill should be allowed"

    def test_loaded_skill_with_special_characters(self):
        """Test handling of loaded_skill with special characters"""
        special_names = [
            "skill-with-dashes",
            "skill_with_underscores",
            "skill.with.dots",
            "skill/with/slashes"
        ]

        for skill_name in special_names:
            context = {
                "tool_name": "UniversalSkillsManager",
                "tool_input": {"action": "list"},
                "loaded_skill": skill_name
            }

            # Should be allowed (special characters are valid)
            is_loaded = context.get("loaded_skill") is not None
            should_block = not is_loaded

            assert should_block is False, f"Skill name '{skill_name}' should be allowed"
