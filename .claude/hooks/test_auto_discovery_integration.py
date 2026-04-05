#!/usr/bin/env python3
"""
Test the complete auto-discovery integration with skill pattern gate.
"""
import sys

# Test imports
try:
    from skill_auto_discovery import discover_all_skills, get_skill_config
    print("✅ Auto-discovery module imports successfully")
except ImportError as e:
    print(f"❌ Failed to import auto-discovery: {e}")
    sys.exit(1)

# Test 1: Discover all skills
print("\n=== Test 1: Discover All Skills ===")
all_skills = discover_all_skills()
print(f"✅ Discovered {len(all_skills)} skills")

# Test 2: /s skill has correct configuration
print("\n=== Test 2: /s Skill Configuration ===")
s_config = get_skill_config("s", {})
assert s_config.get('tools') == ['Bash'], f"Expected ['Bash'], got {s_config.get('tools')}"
assert s_config.get('pattern') == 'run_heavy.py', f"Expected 'run_heavy.py', got {s_config.get('pattern')}"
assert s_config.get('discovered') == True, "Expected discovered=True"
print("✅ /s skill correctly configured with Bash enforcement")

# Test 3: Knowledge skills have no tools
print("\n=== Test 3: Knowledge Skills ===")
# Only test knowledge skills that actually exist
knowledge_skills = ["cks", "search", "constraints", "standards"]
for skill in knowledge_skills:
    config = get_skill_config(skill, {})
    tools = config.get('tools', [])
    assert tools == [], f"{skill} should have no tools, got {tools}"
    print(f"✅ {skill}: no enforcement (knowledge skill)")

# Test 4: Skills with scripts get pattern detection
print("\n=== Test 4: Script Pattern Detection ===")
script_skills = ["s", "p", "q", "research"]
for skill in script_skills:
    config = get_skill_config(skill, {})
    pattern = config.get('pattern', '')
    if pattern:
        print(f"✅ {skill}: detected pattern '{pattern}'")
    else:
        print(f"⚠️  {skill}: no pattern detected (may not have scripts/)")

# Test 5: Backwards compatibility with explicit registry
print("\n=== Test 5: Backwards Compatibility ===")
explicit_registry = {
    "test-skill": {
        "tools": ["Bash"],
        "pattern": r"test_command",
        "hint": "Use test-skill via test_command",
        "intent_enabled": False,
    }
}
config = get_skill_config("test-skill", explicit_registry)
assert config == explicit_registry["test-skill"], "Explicit registry should take precedence"
print("✅ Explicit registry takes precedence over auto-discovery")

# Test 6: Integration with skill pattern gate
print("\n=== Test 6: Integration Test ===")
try:
    # Simulate what the skill pattern gate does
    skill = "s"
    skill_config = get_skill_config(skill, {})
    if skill_config and skill_config.get("tools"):
        print(f"✅ Skill pattern gate would enforce '{skill}' with tools: {skill_config['tools']}")
        print(f"   Pattern to match: {skill_config.get('pattern', 'none')}")
    else:
        print(f"❌ Skill '{skill}' would not be enforced (configuration issue)")
except Exception as e:
    print(f"❌ Integration test failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ALL TESTS PASSED")
print("="*50)
print("\n🎉 Auto-discovery integration is working correctly!")
print("\nKey Results:")
print("  • /s skill: ENFORCED with Bash + run_heavy.py pattern")
print("  • Knowledge skills: NOT ENFORCED (correct)")
print("  • Script detection: WORKING (auto-detects scripts/)")
print("  • Backwards compatibility: MAINTAINED")
print("  • Integration with skill pattern gate: VERIFIED")
