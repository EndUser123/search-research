"""
ReAct Looper - Iterative investigation loop
Uses existing investigation-ledger for confidence tracking
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Import existing ledger
sys.path.insert(0, str(Path(__file__).resolve().parent))
from guidance_generator import generate_guidance
from ledger import calculate_confidence_ceiling

# State file path relative to hook location for portability
_hooks_dir = Path(__file__).resolve().parent.parent
REACT_STATE_FILE = _hooks_dir / ".state" / "react_loop_state.json"


class ReActLooper:
    """Iterative thought-action-observation investigation loop"""

    def __init__(self, error_type: str, initial_description: str):
        # Set default constants (always set regardless of resume or fresh start)
        self.max_iterations = 5
        self.target_confidence = 75

        # Try to resume existing loop
        existing_state = self._load_state()
        if existing_state and existing_state.get("active"):
            self.error_type = existing_state["error_type"]
            self.description = existing_state["error_description"]
            self.iterations = existing_state["iterations"]
            self.hypothesis = existing_state.get("hypothesis")
            self.collected_evidence = existing_state.get("collected_evidence", [])
            self.confidence = existing_state.get("confidence", 0)
            print(f"\n[RESUME] Resuming loop from iteration {self.iterations}")
        else:
            # Start fresh loop
            self.error_type = error_type
            self.description = initial_description
            self.iterations = 0
            self.hypothesis = None
            self.collected_evidence = []
            self.confidence = 0
            self._save_state()  # Persist initial state

    def _load_state(self) -> dict:
        """Load persisted loop state"""
        try:
            if REACT_STATE_FILE.exists():
                with open(REACT_STATE_FILE) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load ReAct state: {e}")
        return {}

    def _save_state(self) -> None:
        """Persist loop state for resume"""
        state = {
            "active": self.iterations < self.max_iterations and self.confidence < self.target_confidence,
            "error_type": self.error_type,
            "error_description": self.description,
            "iterations": self.iterations,
            "hypothesis": self.hypothesis,
            "collected_evidence": self.collected_evidence,
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat()
        }
        try:
            REACT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(REACT_STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to save ReAct state: {e}")

    def _clear_state(self) -> None:
        """
        Clear loop state when done.

        Raises:
            OSError: If state file cannot be deleted due to permissions or locks
        """
        if not REACT_STATE_FILE.exists():
            # Nothing to clear - this is fine
            return

        try:
            REACT_STATE_FILE.unlink()
            print(f"[DEBUG] Cleared ReAct state file: {REACT_STATE_FILE}")
        except PermissionError as e:
            # File is locked or read-only - this is a real problem
            raise OSError(f"Cannot clear ReAct state (permission denied): {e}") from e
        except OSError as e:
            # Other OS errors (file in use, network issue, etc.)
            raise OSError(f"Cannot clear ReAct state (OS error): {e}") from e

    def run(self) -> Dict[str, Any]:
        """
        Run one iteration of ReAct loop.
        Call multiple times to advance iterations.

        Returns:
            {
                "iterations": int,
                "final_confidence": int,
                "ready_for_rca": bool,
                "evidence": list,
                "guidance_history": list
            }
        """
        guidance_history = []

        # Check if already complete (pre-increment)
        # This handles resume scenario: new instance created with existing state at max
        if self.iterations >= self.max_iterations:
            print(f"\n[DONE] Reached max iterations ({self.max_iterations})")
            self._clear_state()
            return self._get_result()

        # Get current confidence
        ceiling_info = calculate_confidence_ceiling()
        current_confidence = ceiling_info["ceiling"]
        self.confidence = current_confidence

        # Check if ready for RCA
        if current_confidence >= self.target_confidence:
            print(f"\n[DONE] Reached target confidence ({current_confidence}%)")
            self._clear_state()
            return self._get_result()

        # Show header for new/first iteration
        if self.iterations == 0:
            print(f"\n{'='*64}")
            print("🔄 REACT INVESTIGATION LOOP")
            print(f"{'='*64}")
            print(f"Error Type: {self.error_type}")
            print(f"Target Confidence: {self.target_confidence}%")
            print(f"Max Iterations: {self.max_iterations}")
            print(f"{'='*64}\n")

        # Increment iteration counter
        self.iterations += 1

        # Show current state
        print(f"[Iteration {self.iterations}/{self.max_iterations}]")
        print(f"  Current Confidence: {current_confidence}%")
        print(f"  Reason: {ceiling_info['reason']}")

        # Generate guidance for this iteration
        guidance = generate_guidance(self.error_type)
        print("\n  💡 Suggested Actions:")
        for i, step in enumerate(guidance, 1):
            print(f"     {i}. {step}")

        # Save state for next iteration
        self._save_state()

        # Check if we've reached max iterations after incrementing (post-increment)
        # This handles "just reached max" scenario: we incremented during run(), now need to clear
        if self.iterations >= self.max_iterations:
            print(f"\n[DONE] Reached max iterations ({self.max_iterations})")
            self._clear_state()
            return self._get_result()

        # Check if ready for RCA after this iteration
        if current_confidence >= self.target_confidence:
            print(f"\n✅ Target confidence reached ({current_confidence}%)")
            self._clear_state()
            return self._get_result()

        # Not ready - prompt for next iteration
        gap = self.target_confidence - current_confidence
        print(f"\n⏳ Need {gap}% more confidence")
        print(f"→ Continue: Run /debug --react again (iteration {self.iterations + 1}/{self.max_iterations})\n")

        return {
            "iterations": self.iterations,
            "final_confidence": current_confidence,
            "ready_for_rca": False,
            "evidence": self.collected_evidence,
            "guidance_history": guidance_history
        }

    def _get_result(self) -> Dict[str, Any]:
        """Get result dictionary"""
        return {
            "iterations": self.iterations,
            "final_confidence": self.confidence,
            "ready_for_rca": self.confidence >= self.target_confidence,
            "evidence": self.collected_evidence,
            "guidance_history": []
        }
