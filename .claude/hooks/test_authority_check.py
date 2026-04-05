#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


def is_about_existing_code(text: str) -> bool:
    text_lower = text.lower()
    explain_patterns = [r"\bexplain\b", r"\bdescribe\b", r"show\s+me", r"walk\s+through", r"what\s+does", r"how\s+does", r"this\s+(function|code|regex|class|method)", r"line\s+\d+", r"in\s+[\w/]+\.py"]
    return any(re.search(p, text_lower) for p in explain_patterns)

def detect_question(text: str) -> bool:
    text_lower = text.lower().strip()
    if is_about_existing_code(text):
        return False
    if text_lower.endswith("?"):
        return True
    question_words = {"what", "how", "why", "when", "where", "which", "design", "plan", "architecture", "structure", "architect", "outline", "blueprint", "analyze", "review", "examine", "evaluate", "assess", "explore", "should", "would", "could", "might", "best", "recommend", "suggest", "think", "consider", "help"}
    words = set(text_lower.split())
    if any(w in words for w in question_words):
        return True
    question_phrases = [r"how\s+should", r"how\s+would", r"how\s+can", r"how\s+to", r"what.*approach", r"what.*way", r"best\s+way", r"should\s+we", r"would\s+work", r"think\s+about", r"consider\s+using", r"is\s+it\s+possible", r"can\s+we"]
    return any(re.search(p, text_lower) for p in question_phrases)

def has_authorization(text: str) -> bool:
    text_lower = text.lower()
    auth_keywords = {"implement", "create", "write", "build", "generate", "fix", "add", "update", "modify", "refactor", "delete", "remove", "replace", "rename", "deploy", "setup", "install", "initialize", "configure", "yes", "go", "proceed", "start", "begin"}
    words = set(text_lower.split())
    if any(w in words for w in auth_keywords):
        return True
    auth_phrases = [r"go\s+ahead", r"let['']s\s+(go|do)", r"please\s+(write|create|build|implement)", r"can\s+you\s+(create|write|build|implement)", r"would\s+you\s+(create|write|build|implement)", r"do\s+it", r"make\s+it"]
    return any(re.search(p, text_lower) for p in auth_phrases)

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

def print_test_result(name: str, passed: bool, details: str | None = None) -> None:
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{status}] {name}")
    if details:
        print(f"       {details}")

def run_test(name: str, func: Callable[[], bool], expected: bool = True) -> bool:
    try:
        result = func()
        passed = result == expected
        if not passed:
            print_test_result(name, passed, f"Expected: {expected}, Got: {result}")
        else:
            print_test_result(name, passed)
        return passed
    except Exception as e:
        print_test_result(name, False, f"ERROR: {e}")
        return False

def run_hook_test(name: str, prompt_input: str, should_warn: bool = False) -> bool:
    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    signals_dir = Path.home() / ".claude" / "signals"
    try:
        result = subprocess.run([sys.executable, str(hook_path)], input=json.dumps({"prompt": prompt_input}), capture_output=True, text=True, timeout=5)
        signal_files = list(signals_dir.glob("planning_mode_*.json"))
        has_signal = False
        if signal_files:
            with open(signal_files[-1]) as f:
                data = json.load(f)
                has_signal = data.get("action") == "show"
        has_warning = "PLANNING MODE ACTIVE" in result.stdout or has_signal
        passed = has_warning == should_warn
        if not passed:
            details = f"Expected: {should_warn}, Got: {has_warning} (signal={has_signal}, files={len(signal_files)})"
            print_test_result(name, passed, details)
        else:
            print_test_result(name, passed)
        return passed
    except Exception as e:
        print_test_result(name, False, f"ERROR: {e}")
        return False

def main() -> int:
    print("=" * 60)
    print("Authority Check Hook - 15-Test Comprehensive Checklist")
    print("=" * 60)
    results: list[bool] = []
    print(f"\n{YELLOW}SECTION 1: detect_question() - Question Detection{RESET}")
    results.append(run_test("Test 1: Question mark at end", lambda: detect_question("What should I do?"), expected=True))
    results.append(run_test("Test 2: 'what' planning word", lambda: detect_question("What approach works best"), expected=True))
    results.append(run_test("Test 3: 'how' planning word", lambda: detect_question("How should I structure this"), expected=True))
    results.append(run_test("Test 4: 'should' decision word", lambda: detect_question("Should I extract this to a service"), expected=True))
    results.append(run_test("Test 5: Non-question statement", lambda: detect_question("Create a new file"), expected=False))
    print(f"\n{YELLOW}SECTION 2: is_about_existing_code() - False Positive Filter{RESET}")
    results.append(run_test("Test 6: Filters 'explain' questions", lambda: is_about_existing_code("Explain how this regex works"), expected=True))
    results.append(run_test("Test 7: Filters 'show me' questions", lambda: is_about_existing_code("Show me how this function works"), expected=True))
    results.append(run_test("Test 8: Filters 'describe' questions", lambda: is_about_existing_code("Describe the architecture"), expected=True))
    results.append(run_test("Test 9: Filters 'walk through' questions", lambda: is_about_existing_code("Walk through the code"), expected=True))
    results.append(run_test("Test 10: Planning question not filtered", lambda: is_about_existing_code("Should I add a new feature"), expected=False))
    print(f"\n{YELLOW}SECTION 3: has_authorization() - Authorization Detection{RESET}")
    results.append(run_test("Test 11: 'implement' keyword", lambda: has_authorization("Please implement this feature"), expected=True))
    results.append(run_test("Test 12: 'go ahead' phrase", lambda: has_authorization("Yes go ahead and do it"), expected=True))
    results.append(run_test("Test 13: No authorization keywords", lambda: has_authorization("What do you think about this"), expected=False))
    print(f"\n{YELLOW}SECTION 4: End-to-End Hook Behavior{RESET}")
    results.append(run_hook_test("Test 14: Planning + no auth = WARNING", "How should I design this component", should_warn=True))
    results.append(run_hook_test("Test 15: Code explanation = NO WARNING", "Explain how this regex works", should_warn=False))
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    pct = (passed / total) * 100
    if passed == total:
        print(f"{GREEN}ALL {total}/{total} TESTS PASSED ({pct:.0f}%){RESET}")
    else:
        print(f"{RED}TESTS FAILED: {passed}/{total} passed ({pct:.0f}%){RESET}")
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
